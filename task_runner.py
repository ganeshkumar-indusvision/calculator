import json
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass
from decimal import Decimal, getcontext
from enum import Enum
from pathlib import Path

from calculator import Calculation, Calculator, CalculatorApp, History

JOBS_FILE = Path("output/jobs.json")
NUM_WORKERS = 3
WORKER_LOG = Path("logs/runner.log")
DEFAULT_DIGIT_LIMIT= 50

class ScientificCalculator(Calculator):
    """Calculator with slow operations that suit background jobs."""

    def __init__(self) -> None:
        super().__init__()
        getcontext().prec = 1_000_000
        self.operations.update({"fact": (1,self.factorial),
                                "primes": (1,self.count_primes),
                                "fib": (1,self.fibonacci)})
        self.scientific_operations = {"fact","primes", "fib"}
        self.validation.update({
            "fact":self._check_fact,
            "primes": self._check_primes,
            "fib": self._check_fib
        })
        
    def _check_fact(self, n: int) -> None:
        if n < 0:
            raise ValueError("fact requires a non-negative number")
        if n > 200000:
            raise ValueError("fact is limited to n ≤ 200000")
    
    def factorial(self, num: int) -> Decimal:
        fact = Decimal(str(1))
        value = Decimal(str(2))
        while(value <= num):
            fact *= value
            value +=1  
        return fact

    def _check_primes(self, n: int) -> None:
        if n < 2:
            raise ValueError("primes requires a non-negative number and should be greater than 2")
    def _check_fib(self, n: int) -> None:
        if n < 0:
            raise ValueError("fib requires a non-negative number")

    def fibonacci(self, num: int) -> Decimal:
        num = int(num)
        result = Decimal(str(0))
        value = Decimal(str(1))
        for _ in range(num):
            result, value = value, result + value
        return result


    def count_primes(self, num: Decimal) -> tuple[Decimal, Decimal]:  # (count, largest)

        num = int(num)
        prime = [True] * int(num+1)
        p = 2
        length = 0
        while (p*p<=num):
            if prime[p]:

                for i in range(p*p,num+1,p):
                    prime[i]=False

            p+=1
        for i in range(2,num+1,1):
            if prime[i]:
                last = i
                length +=1 

        return  Decimal(str(length)),Decimal(str(last))

    def _validate_output(self, op: str, *results: Decimal):
        if op in self.scientific_operations:
            if op == "primes":
                results = results[0]

            converted = tuple(int(value) for value in results)
            return converted[0] if len(converted) == 1 else converted

        return super()._validate_output(op, *results)

    def _validate_number(self, number: object, op: str) -> None:
        if op in {"fact", "fib"}:
            if not isinstance(number, int) or isinstance(number, bool):
                raise ValueError(f"{number!r} is not a valid integer")
            return

        super()._validate_number(number,op)

    def check_digit(self, value: int | Decimal) -> tuple[int, bool]:
        length = value.adjusted() + 1
        return length, length > DEFAULT_DIGIT_LIMIT
    

class JobState(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    id: int
    command: str
    operands: tuple
    state: JobState = JobState.QUEUED # By default we will be storing value as queued until worker marks it as running, fialed
    result: object = None
    error: str | None = None
    started_at: float | None = None
    finished_at: float | None = None

    @property
    def duration(self) -> float | None:
        if self.started_at is not None and self.finished_at is not None:
            return self.finished_at - self.started_at


class JobManager:
    """Owns jobs, the queue, the lock and saving. Safe to call from any thread."""

    def __init__(self, calculator: ScientificCalculator, history: History, jobs_file: Path= JOBS_FILE) -> None:
        self.calculator = calculator
        self.history = history           
        self.jobs: dict[int, Job] = {}
        self.queue: queue.Queue[int] = queue.Queue()
        self.lock = threading.RLock() # Using this because if there is multiple locks aquring by same thread under it is should not cause  deadlock
        self.stop_event = threading.Event()
        self._next_id: int = 1 
        self.jobs_file = jobs_file
        self._worker_logger_init()
        
    
    def _worker_logger_init(self) -> None:
        self.logger = logging.getLogger("runner")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        if not self.logger.handlers:
            WORKER_LOG.parent.mkdir(parents= True, exist_ok=True)
            file_handler = logging.FileHandler(WORKER_LOG,mode="a",encoding="utf-8")
            file_handler.setFormatter(logging.Formatter(
                fmt="%(asctime)s [%(threadName)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            self.logger.addHandler(file_handler)

    def submit(self, command: str, operands: tuple) -> int:
        """Add a job in the queue and return it's id."""
        # Here, lock needed because there is Read and write operation
        with self.lock:
            job_id = self._next_id
            self._next_id +=1
            job = Job(id=job_id,command=command,operands=tuple(operands))
            self.jobs[job_id]= job
            self.queue.put(job_id)# Queue adding (publisher point)
            self.save()
            self.logger.info(f"Job-{job_id} Queued ({command} {operands})")
            return job_id 

    def get(self, job_id: int) -> Job: 
        with self.lock:
            if job_id not in self.jobs:
                self.logger.error(f"No Jobs with id {job_id}")
                raise ValueError(f"No Jobs with id{job_id}")
            return self.jobs[job_id]

    def record_calculation(self, op: str, operands: tuple, result: object, data_file: Path | None = None, memory: object = None) -> None:
        # central place for history recording so both main thread and workers use it under the lock
        with self.lock:
            self.history.add(Calculation(op, tuple(operands), result))
            if data_file:
                try:
                    self.history.save(data_file, memory)
                except OSError as e:
                    self.logger.warning(f"Could not save history: {e}")

    def finish(self, job_id: int, result: object) -> None:
        with self.lock:
            if job_id not in self.jobs:
                return
            job = self.jobs[job_id]
            job.finished_at = time.time()
            job.result = result
            self.record_calculation(job.command, job.operands, result)
            job.state = JobState.DONE
            self.save()
            self.logger.info(f"Job {job_id} Finished ({job.command} {job.operands} = {result})")

    def fail(self, job_id: int, error: str) -> None: 
        with self.lock:
            if job_id not in self.jobs:
                return      
            job = self.jobs[job_id]
            job.finished_at = time.time()
            job.error = error
            job.state = JobState.FAILED
            self.save()
            self.logger.error(f"Job {job_id} Failed ({job.command} {job.operands} Error = {error})")

    def save(self) -> None: 
        # Currenty this i feel need iteration we can improve this problem.
        data = {str(job_id):{
            "id": job.id,
            "command": job.command,
            "operands":tuple(job.operands),
            "state":job.state.value,
            "result":job.result,
            "error":job.error,
            "started_at":job.started_at,
            "finished_at":job.finished_at,}
          for job_id,job in self.jobs.items()
        }
        self.jobs_file.parent.mkdir(parents= True,exist_ok=True)
        temp_file = self.jobs_file.with_name(self.jobs_file.name + ".tmp")
        with open(temp_file ,"w",encoding="utf-8") as f:
            json.dump(data,f,indent=2)
        os.replace(temp_file,self.jobs_file)


    def mark_running(self, job_id: int) -> Job | None:
        with self.lock:
            if job_id not in self.jobs:
                return None
            job = self.jobs[job_id]
            job.state = JobState.RUNNING
            job.started_at = time.time()
            self.save()
            self.logger.info(f"Job {job_id} Running ({job.command} {job.operands})")
            return job


    def load(self) -> None: 
        """Load jobs from the file and mark unfinished one as interrupted."""
        if not self.jobs_file.exists():
            return
        try:
            with open(self.jobs_file,"r",encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            back_file = self.jobs_file.with_name(self.jobs_file.name + ".bak")
            try:
                os.replace(self.jobs_file, back_file)
            except OSError:
                raise OSError(f"Warning: could not read {self.jobs_file}. Starting empty.")
                data = {} # Need to make sure empty data is created.
        with self.lock:
            for item in data.values():
                state = JobState(item["state"])
                error = item.get("error")
                if state in (JobState.QUEUED, JobState.RUNNING):
                    state = JobState.FAILED
                    error = "interrupted"
                job = Job(
                    id = item["id"],
                    command= item["command"],
                    operands= tuple(item["operands"]),
                    state= state,
                    result= item["result"],
                    error = error,
                    started_at=item["started_at"],
                    finished_at=item["finished_at"],
                )
                self.jobs[job.id] = job
            if self.jobs:                             
                self._next_id = max(self.jobs.keys()) + 1    

    def show_jobs(self) -> None:
        """Print all jobs with there state and duration."""
        with self.lock:
            jobs = sorted(self.jobs.values(), key=lambda j: j.id)
        if not jobs:
            print("No jobs yet")
            return
        for job in jobs:
            ops_str = " ".join(str(o) for o in job.operands)
            cmd_str = f"{job.command} {ops_str}".strip()
            if job.state == JobState.DONE:
                dur = f"{job.duration:.2f}s" if job.duration is not None else "0.00s"
                print(f" {job.id:<2} {cmd_str:<16} DONE    {dur}")
            elif job.state == JobState.FAILED:
                print(f" {job.id:<2} {cmd_str:<16} FAILED  {job.error or ''}")
            elif job.state == JobState.RUNNING:
                print(f" {job.id:<2} {cmd_str:<16} RUNNING")
            else:
                print(f" {job.id:<2} {cmd_str:<16} QUEUED")    


class Worker:
    """One background thread that runs calculator jobs from the queue."""

    def __init__(self, name: str, manager: JobManager) -> None:
        self.manager = manager
        self.current_job: int | None = None
        self.thread = threading.Thread(target=self._loop, name=name)
    def _loop(self) -> None:
        while not self.manager.stop_event.is_set():
            try:
                # 0.5s timeout lets thread regularly check stop_event so quit doesn't block forever
                job_id = self.manager.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            job = self.manager.mark_running(job_id)
            if job is None:
                self.manager.queue.task_done()
                continue
            self.current_job = job_id
            # print(f"[{self.thread.name}] running job {job_id}")
            try:
                # calc has no shared state so no lock needed here
                result = self.manager.calculator.calculate(job.command, *job.operands)
                self.manager.finish(job_id, result)
            except Exception as e:
                self.manager.fail(job_id, str(e))
            finally:
                with self.manager.lock:
                    self.current_job = None
                self.manager.queue.task_done()



class TaskRunnerApp(CalculatorApp):
    """The calculator app plus background job commands."""

    def __init__(self) -> None:
        super().__init__()
        self.manager = JobManager(self.calculator, self.history)
        self.workers = [Worker(f"worker-{i}", self.manager) for i in range(1, NUM_WORKERS + 1)]

        self.command_info.update({
            "fact": (1, "Calculate factorial of n", "\nExample: \n> fact 5 \n> 120"),
            "primes": (1, "Count primes <= n and largest prime", "\nExample: \n> primes 10 \n> 4 primes, largest 7"),
            "fib": (1, "Calculate nth Fibonacci number", "\nExample: \n> fib 10 \n> 55"),
            "submit": (2, "Submit a calculation as background job", "\nExample: \n> submit primes 2000000 \n> Job 1 queued"),
            "batch": (1, "Submit calculations from a file", "\nExample: \n> batch sums.txt \n> Queued 4 jobs"),
            "jobs": (0, "List all background jobs", "\nExample: \n> jobs \n> Displays all jobs"),
            "result": (1, "Show the result of a background job", "\nExample: \n> result 1 \n> Shows job result"),
            "workers": (0, "Show status of worker threads", "\nExample: \n> workers \n> Displays worker status"),
        })

        self.app_handlers.update({
            "jobs": self._show_jobs,
            "workers": self._show_workers,
        })

        self.manager.load(self.logger.warning)
        self.task_handlers = {
            "submit": self._handle_submit,
            "batch": self._handle_batch,
            "result": self._handle_result,
        }
        self._workers_started = False

    def _ensure_workers_started(self) -> None:
        if self._workers_started:
            return
        [w.thread.start() for w in self.workers]
        self._workers_started = True
    def _make_calculator(self) -> Calculator:
        return ScientificCalculator()

    def format_result(self, result):
        """Format the result so it look nice in the terminal."""
        if isinstance(result, (tuple, list)) and result and isinstance(result[0], str):
            op = result[0]
            if op in ("fact", "fib"):
                val, is_digits = result[1]
                return f"{val} digits" if is_digits else str(val)
            if op == "primes":
                (largest, _), (count, _) = result[1], result[2]
                return f"{count} primes, largest {largest}" if count else "0 primes"
        return str(result)

    def _display_result(self, result):
        print(self.format_result(result))

    def _record_result(self, op, operands, result):
        self.manager.record_calculation(op, operands, result, self.data_file, self.memory)
    
    def validate_request(self, op: str, *args: object) -> None:
        if op not in self.calculator.operations:
            raise ValueError(f"Unknown operation: {op}")

        expected, _ = self.calculator.operations[op]

        if len(args) != expected:
            raise ValueError(f"{op} requires {expected} argument(s)")

    def _process_task_command(self, tokens: tuple) -> None:
        op = tokens[0].lower()
        args = tokens[1:]
    
        handler = self.task_handlers.get(op)
        if handler:
            handler(args)

    def _handle_submit(self, args: tuple) -> None:
        self._ensure_workers_started() 
        if len(args) < 2:
            self.logger.warning("Usage: submit <operation> <arguments>")
            return

        op = args[0].lower()
        operands = args[1:]

        if op in ("ms", "mr", "mc"):
            self.logger.warning(f"{op} can't be run as a job")
            return

        if op not in self.calculator.operations:
            self.logger.warning(f"{op} is not a valid calculator operation")
            return

        expected = self.command_info[op][0]
        if len(operands) != expected:
            self.logger.warning(f"{op} requires {expected} argument(s)")
            return

        try:
            converted = self._convert_args(operands)
            if converted is None:
                return

            self.validate_request(op, *converted)

            job_id = self.manager.submit(op, converted)
            print(f"Job {job_id} queued")

        except (ValueError, TypeError) as e:
            self.logger.warning(str(e))

    def _handle_batch(self, args: tuple) -> None:
        if len(args) != 1:
            self.logger.warning("Usage: batch <filename>")
            return

        path = Path(args[0])
        if not path.exists():
            print(f"File not found: {path.name}")
            return

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as e:
            print(f"Could not read {path.name}: {e}")
            return

        queued_ids = []
        invalid = []

        for line_no, line in enumerate(lines, start=1):
            parts = line.split()
            if not parts or parts[0].startswith("#"):
                continue
            cmd, raw = parts[0].lower(), parts[1:]

            if cmd in ("ms", "mr", "mc"):
                invalid.append((line_no, f"{cmd} can't be run as a job"))
            elif cmd not in self.calculator.operations:
                invalid.append((line_no, f"Unknown command '{cmd}'"))
            elif len(raw) != self.calculator.operations[cmd][0]:
                exp = self.calculator.operations[cmd][0]
                invalid.append((line_no, f"{cmd} needs {exp} {'number' if exp == 1 else 'numbers'}"))
            elif any(s.lower() == "last" for s in raw):
                invalid.append((line_no, "'last' is not allowed in batch files"))
            else:
                nums = [self._detect_numeric_type(s) for s in raw]
                if None in nums:
                    invalid.append((line_no, f"'{raw[nums.index(None)]}' is not a valid number"))
                else:
                    queued_ids.append(self.manager.submit(cmd, tuple(nums)))

        if queued_ids:
            self._ensure_workers_started()
            rng = f"{queued_ids[0]}-{queued_ids[-1]}" if len(queued_ids) > 1 else str(queued_ids[0])
            msg = f"Queued {len(queued_ids)} jobs ({rng})."
        else:
            msg = "Queued 0 jobs."

        if invalid:
            suffix = "line" if len(invalid) == 1 else "lines"
            print(f"{msg} Skipped {len(invalid)} invalid {suffix}:")
            for lno, err in invalid:
                print(f"  line {lno}: {err}")
        else:
            print(msg)

    def _handle_result(self, args: tuple) -> None:
        if len(args) != 1:
            self.logger.warning("Usage: result <job_id>")
            return

        try:
            job_id = int(args[0])
            job = self.manager.get(job_id)
        except (ValueError) as e:
            self.logger.warning(str(e))
            return

        if job.state == JobState.DONE:
            print(self.format_result(job.result))
        elif job.state == JobState.FAILED:
            print(f"FAILED: {job.error}")
        else:
            print(job.state.value.upper())

    def _show_jobs(self) -> None:
        self.manager.show_jobs()

    def _show_workers(self) -> None:
        if not self._workers_started:
            print("(workers not started — submit a job first)")
            return
        for worker in self.workers:
            if worker.current_job is None:
                print(f"{worker.thread.name}: idle")
                continue
            with self.manager.lock:
                job = self.manager.jobs.get(worker.current_job)
            if job:
                ops_str = " ".join(str(o) for o in job.operands)
                print(f"{worker.thread.name}: running job {job.id} ({job.command} {ops_str})")
            else:
                print(f"{worker.thread.name}: running job {worker.current_job}")

    def _exit(self) -> None:
        self.manager.queue.join()
        self.manager.stop_event.set()
        if self._workers_started:
            [worker.thread.join() for worker in self.workers]
        super()._exit()

    def handle_command(self, command: str) -> None:
        tokens = tuple(command.split())

        if tokens and tokens[0].lower() in self.task_handlers:
            self._process_task_command(tokens)
            return

        super().handle_command(command)

if __name__ == "__main__":
    TaskRunnerApp().run()
    # print("Go Home")