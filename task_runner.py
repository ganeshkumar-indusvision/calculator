import threading
import queue
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from calculator import Calculator, History, Calculation, CalculatorApp
from decimal import Decimal, getcontext, MAX_EMAX, MIN_EMIN

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
        return fact,None


    def count_primes(self, num: int) -> tuple[int, int]:  # (count, largest)
        if num <= 1:
            return 0,None
        # threshold = num.sqrt().quantize(Decimal('1'), rounding=ROUND_DOWN)
        # prime.append(2)
        prime = [True] * int(num+1)
        p = 2
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
        result = Decimal(str(0))
        value = Decimal(str(0))
        while(value <= num):
            result += value
            value +=1  
        return result,None

    def _validate_digit_count(self,value: int|Decimal) -> tuple[int,bool] :
        lenght =  value.adjusted()+ 1
        result = lenght,True if lenght >= 50 else value,False
        return result

    def _validate_scintific_output(self, op: str,*args: object) -> tuple:
        """Convert a whole Decimal to int, otherwise return float."""
        result = tuple()
        result = result + (op,)
        if op=="prime":
            for arg in args:
                value = self._validate_digit_count(arg)
                
                result = result+(value,)
            return result
        value = self._validate_digit_count(arg[0])

        return result+(value,)

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
        
    def calculate(self, *args: object) -> int | float:
        """Validate the request, run the operation, and return a clean result."""
        if not self._validate_scintific_input(*args):
            return super().calculate(*args)
        op = str(args[0])
        operands = [Decimal(str(v)) for v in args[1:] if v is not None]
        return self._validate_scintific_output(op,self.operations[op][1](*operands))
    

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
    state: JobState = JobState.QUEUED
    result: object = None
    error: str | None = None


class JobManager:
    """Owns jobs, the queue, the lock and saving. Safe to call from any thread."""

    def __init__(self, calculator: ScientificCalculator, history) -> None:
        self.calculator = calculator
        self.history = history           # Project 1's History, now shared
        self.jobs: dict[int, Job] = {}
        self.queue: queue.Queue[int] = queue.Queue()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

    def submit(self, command: str, operands: tuple) -> int: ...
    def get(self, job_id: int) -> Job: ...
    def finish(self, job_id: int, result: object) -> None: ...  # also adds to history
    def fail(self, job_id: int, error: str) -> None: ...
    def save(self) -> None: ...
    def load(self) -> None: ...


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