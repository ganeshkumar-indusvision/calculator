import threading
import queue
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from calculator import Calculator, History, Calculation, CalculatorApp
from decimal import Decimal, getcontext, MAX_EMAX, MIN_EMIN
import json
import time
import os

JOBS_FILE = Path("output/jobs.json")
NUM_WORKERS = 3


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
            return 0,None
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

    def submit(self, command: str, operands: tuple) -> int:
        # Here, lock needed because there is Read and write operation
        with self.lock:
            job_id = self._next_id
            self._next_id +=1
            job = Job(id=job_id,command=command,operands=tuple(operands))
            self.jobs[job_id]= job
            self.queue.put(job_id)# Queue adding (publisher point)
            self.save()
            return job_id 

    def get(self, job_id: int) -> Job: 
        with self.lock:
            if job_id not in self.jobs:
                raise JobNotFoundError(f"No Jobs with id{job_id}")
            return self.jobs[job_id]
    def finish(self, job_id: int, result: object) -> None:
        with self.lock:
            if job_id not in self.jobs:
                return
            job = self.job[job_id]
            job.state = JobState.DONE
            job.finished_at = time.time()

            self.history.add(Calculation(job.command,job.operands, result))
            self.save()

    def fail(self, job_id: int, error: str) -> None: 
        with self.lock:
            if job_id not in self.jobs:
                return      
            job = self.jobs[job_id]
            job.state = JobState.FAILED
            job.finished_at = time.time()
            job.error = error
            self.save()
    def save(self) -> None: 

    #     class Job:
    # id: int
    # command: str
    # operands: tuple
    # state: JobState = JobState.QUEUED # By default we will be storing value as queued until worker marks it as running, fialed
    # result: object = None
    # error: str | None = None
    # started_at: float | None = None
    # finished_at: float | None = None

        data = {str(jid):{
            "id": j.id,
            "command": j.command,
            "operands":j.operands,
            "state":j.state,
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
            for _,item in data.items():
                state = JobState(item["state"])
                error = item.get("error")
                if state in (JobState.QUEUED, JobState.RUNNING):
                    state = JobState.FAILED
                    error = "Interuped"
                    # id: int
    # command: str
    # operands: tuple
    # state: JobState = JobState.QUEUED # By default we will be storing value as queued until worker marks it as running, fialed
    # result: object = None
    # error: str | None = None
    # started_at: float | None = None
    # finished_at: float | None = None

                job = Job(
                    id = item["id"],
                    command= item["command"],
                    operands= item["operands"],
                    state= state,
                    result= item["result"],
                    error = error,
                    started_at=item["started_at"],
                    finished_at=item["finished_at"],
                )
                self.jobs[job.id] = job
                if self.jobs:
                    self._next_id=max(self.jobs.keys())+1


class Worker:
    """One background thread that runs calculator jobs from the queue."""

    def __init__(self, name: str, manager: JobManager) -> None:
        self.manager = manager
        self.current_job: int | None = None
        self.thread = threading.Thread(target=self._loop, name=name)

    def _loop(self) -> None:
        # Hint: queue.get(timeout=0.5) lets the thread check
        # stop_event regularly instead of blocking forever.
        ...
        while not self.manager.stop_event.is_set():
            try:
                job_id = self.manager.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            with self.manager.lock:
                if job_id not in self.manager.jobs:
                    self.manager.queue.task_done()
                    continue
                job=self.manager.jobs[job_id]
                job.state=JobState.RUNNING
                job.started_at = time.time()
                self.current_job = job_id
                self.manager.save()
            try:
                result = self.manager.calculator.calculate(job.command, *job.operands)
                self.manager.finish(job_id, result)
                duration = job.duration or 0.0
                # print("Total Duration: {duration}")
            finally:
                with self.manager.lock:
                    self.current_job = None
                self.manager.queue.task_done()



class TaskRunnerApp(CalculatorApp):
    """The calculator app plus background job commands."""

    def __init__(self) -> None:
        super().__init__()
        self.calculator = ScientificCalculator()
        self.manager = JobManager(self.calculator, self.history)
        self.workers = [Worker(f"worker-{i}", self.manager)
                        for i in range(1, NUM_WORKERS + 1)]
        # TODO: add submit, batch, jobs, result, workers to the command dict


if __name__ == "__main__":
    TaskRunnerApp().run()