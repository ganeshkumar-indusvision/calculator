import threading
import queue
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging
from calculator import Calculator, History, Calculation, CalculatorApp
from decimal import Decimal, getcontext, MAX_EMAX, MIN_EMIN
import json
import time
import os

JOBS_FILE = Path("output/jobs.json")
NUM_WORKERS = 3
WORKER_LOG = Path("logs/worer.log")




class ScientificCalculator(Calculator):
    """Calculator with slow operations that suit background jobs."""

    def __init__(self) -> None:
        super().__init__()
        self.operations.update({"fact": (1,self.factorial),
                                "primes": (1,self.count_primes),
                                "fib": (1,self.fibonacci)})
        self.scientific_operations = {"fact","primes", "fib"}

        # Decimal datatype functions to keep precision.
        getcontext().prec = 50
        getcontext().Emax = MAX_EMAX
        getcontext().Emin = MIN_EMIN



    def factorial(self, num: int) -> tuple[Decimal,None]: # Result, None
        if num < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        fact = Decimal(str(1))
        value = Decimal(str(2))
        while(value <= num):
            fact *= value
            value +=1  
        return (fact,None,)


    def count_primes(self, num: Decimal) -> tuple[Decimal, Decimal]:  # (count, largest)
        if num <= 1:
            return Decimal('0'), Decimal('0')  
        # threshold = num.sqrt().quantize(Decimal('1'), rounding=ROUND_DOWN)
        # prime.append(2)
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

        return Decimal(str(last)), Decimal(str(length))

    def fibonacci(self, num: int) -> tuple[Decimal,None]: # Result, None
        if num < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        num = int(num)
        result = Decimal(str(0))
        value = Decimal(str(1))
        for _ in range(num):
            result, value = value, result + value
        return result,None

    def _validate_digit_count(self,value: int|Decimal) -> tuple[int,bool] :
        lenght =  value.adjusted()+ 1
        result = (lenght,True,) if lenght >= 50 else (int(value),False,)
        return result

    def _validate_scintific_output(self, op: str,*args: object) -> tuple:
        """Convert a whole Decimal to int, otherwise return float."""
        raw = args[0]
        if op=="primes":
            # for arg in args:
            return (op, *(self._validate_digit_count(value) for value in raw))
        return (op, self._validate_digit_count(raw[0] ))

    def _validate_scintific_number(self, number: object) -> None:
        """Raise if number is not a finite int/float/Decimal (bool is rejected)."""
        if not isinstance(number, int) or isinstance(number, bool):
            raise ValueError(f"{number!r} is not a valid number")
        if not Decimal(str(number)).is_finite():
            raise ValueError(f"{number!r} is not a finite number")


    def _validate_scintific_input(self, *args: object) -> bool:
        """Validate an input request before running the operation."""
        if not args:
            raise ValueError("No operation given")

        op = args[0]
        if not isinstance(op, str) or op not in self.scientific_operations:
            if op not in self.operations:
                raise ValueError(f"Unknown operation: {op}")
            return False

        operands = [v for v in args[1:] if v is not None]
        n, _ = self.operations[op]
        if len(operands) != n:
            raise ValueError(f"{op} takes exactly {n} argument{'s' if n != 1 else ''}")

        for v in operands:
            self._validate_scintific_number(v)

        if operands[0] <0:
            raise ValueError(f"Value should be <= 0")
        if op == "fact":
            if operands[0]>= 200000:
                raise ValueError(f"fact is limited to n ≤ 200000")
        return True
        
    def calculate(self, *args: object) -> int | float:
        """Validate the request, run the operation, and return a clean result."""
        if self._validate_scintific_input(*args):
            op = str(args[0])
            operands = [Decimal(str(v)) for v in args[1:] if v is not None]
            return self._validate_scintific_output(op,self.operations[op][1](*operands))
        return super().calculate(*args)
    

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

class JobNotFoundError(Exception):
    """Raised when querying a job id that does not exist."""
    pass

class JobManager:
    """Owns jobs, the queue, the lock and saving. Safe to call from any thread."""

    def __init__(self, calculator: ScientificCalculator, history: History, jobs_file: Path= JOBS_FILE) -> None:
        self.calculator = calculator
        self.history = history           # Project 1's History, now shared
        self.jobs: dict[int, Job] = {}
        self.queue: queue.Queue[int] = queue.Queue()
        self.lock = threading.Lock()
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
                raise JobNotFoundError(f"No Jobs with id{job_id}")
            return self.jobs[job_id]
    def finish(self, job_id: int, result: object) -> None:
        with self.lock:
            if job_id not in self.jobs:
                return
            job = self.jobs[job_id]
            job.state = JobState.DONE
            job.finished_at = time.time()
            job.result = result
            self.history.add(Calculation(job.command,job.operands, result))
            self.save()
            self.logger.info(f"Job {job_id} Finished ({job.command} {job.operands} = {result})")

    def fail(self, job_id: int, error: str) -> None: 
        with self.lock:
            if job_id not in self.jobs:
                return      
            job = self.jobs[job_id]
            job.state = JobState.FAILED
            job.finished_at = time.time()
            job.error = error
            self.save()
            self.logger.error(f"Job {job_id} Failed ({job.command} {job.operands} Error = {error})")
    def save(self) -> None: 
        data = {str(jid):{
            "id": j.id,
            "command": j.command,
            "operands":j.operands,
            "state":j.state.value,
            "result":j.result,
            "error":j.error,
            "started_at":j.started_at,
            "finished_at":j.finished_at,
          }
          for jid,j in self.jobs.items()
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

        
    def load(self,on_warning: object = None) -> None: 
        if not self.jobs_file.exists():
            return
        try:
            with open(self.jobs_file,"r",encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            back_file = self.jobs_file.with_name(self.jobs_file.name + ".bak")
            try:
                os.replace(self.jobs_file,back_file)
                msg = f"Warning: {self.jobs_file} was not valid JSON. Renamed to {back_file.name}."
            except OSError:
                msg = f"Warning: could not read {self.jobs_file}. Starting empty."
                if callable(on_warning):
                    on_warning(msg)
                return
        with self.lock:
            for _, item in data.items():
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
            if self.jobs:                               # ← OUTSIDE the loop
                self._next_id = max(self.jobs.keys()) + 1    

    def __del__(self):
        """Clean up logger handlers to prevent file descriptor leaks."""
        if hasattr(self, 'logger'):
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
                handler.close()


class Worker:
    """One background thread that runs calculator jobs from the queue."""

    def __init__(self, name: str, manager: JobManager) -> None:
        self.manager = manager
        self.current_job: int | None = None
        self.thread = threading.Thread(target=self._loop, name=name)
    def _loop(self) -> None:
        while not self.manager.stop_event.is_set():
            try:
                job_id = self.manager.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            job = self.manager.mark_running(job_id)
            if job is None:
                self.manager.queue.task_done()
                continue
            self.current_job = job_id
            try:
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
            "submit": ((2,3), "Submit a calculation as background job", "\nExample: \n> submit primes 2000000 \n> Job 1 queued"),
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

    def _make_calculator(self) -> Calculator:
        return ScientificCalculator()
    
    def _exit(self) -> None:
        """Save state and stop the loop."""
        try:
            self.history.save(self.data_file, self.memory)
            self.logger.info(f"\nSaved {len(self.history)} calculations to {self.data_file}. Goodbye!")
        except OSError as e:
            self.logger.warning(f"\nCould not save to {self.data_file}: {e}. Goodbye!")
        self.running = False

    def handle_command(self, command: str) -> None:
        """Intercept task-runner commands and delegate other commands."""
        tokens = tuple(command.split())

        if tokens and tokens[0].lower() in ("submit", "batch", "result"):
            self._process_task_command(tokens)
            return

        super().handle_command(command)


    def _process_task_command(self, tokens: tuple) -> None:
        """Process commands specific to the task runner."""
        op = tokens[0].lower()
        args = tokens[1:]

        if op == "submit":
            self._handle_submit(args)

        elif op == "batch":
            self._handle_batch(args)

        elif op == "result":
            self._handle_result(args)

    def _handle_submit(self,args: tuple) -> None:

if __name__ == "__main__":
    # TaskRunnerApp().run()
    print("Go Home")