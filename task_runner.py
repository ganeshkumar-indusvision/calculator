from calculator import Calculator, History, Calculation, CalculatorApp


# task_runner.py
import threading
import queue
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from calculator import Calculator, CalculatorApp, Calculation  # Project 1

JOBS_FILE = Path("jobs.json")
NUM_WORKERS = 3


class ScientificCalculator(Calculator):
    """Calculator with slow operations that suit background jobs."""

    def __init__(self) -> None:
        super().__init__()
        self.operations.update({"fact": self.factorial,
                                "primes": self.count_primes,
                                "fib": self.fibonacci})

    def factorial(self, n: int) -> int: ...
    def count_primes(self, n: int) -> tuple[int, int]: ...  # (count, largest)
    def fibonacci(self, n: int) -> int: ...


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