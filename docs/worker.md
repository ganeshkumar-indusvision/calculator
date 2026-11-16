# Feature Request: Calculator Task Runner, a Multi-Threaded Add-on (Python Intern Project 2)

Nov 11, 2026 · @Bhuvan

## Overview

Extend the finished command-line calculator so users can **submit calculations as background jobs**. A pool of worker threads runs them while the user keeps typing. Normal commands like `add 4 5` still work instantly as before; `submit add 4 5` runs the same calculation on a worker thread instead. Target effort is about 1 week, using only the Python standard library, with no database.

**Prerequisite:** Project 1 (the calculator) is complete and all its tests pass. This project builds on that code. The existing tests must keep passing at the end.

To make threading worthwhile, the add-on also introduces slow operations (large factorials, prime counting, Fibonacci) that take seconds to run.

**By the end, you should be able to show that you can:**

- Extend existing code without breaking it, using inheritance (`ScientificCalculator(Calculator)`, `TaskRunnerApp(CalculatorApp)`)
- Start, run and cleanly stop threads with `threading.Thread`
- Pass work between threads with `queue.Queue` (the producer–consumer pattern)
- Protect shared data with `threading.Lock` and explain what a race condition is
- Use `enum`, `dataclasses`, custom exceptions and `logging`
- Test code that runs in more than one thread

## Scope

| In scope | Out of scope |
| --- | --- |
| Submitting any existing calculator command as a background job | Rewriting the calculator from scratch |
| Three new slow operations: `fact`, `primes`, `fib` | Expression parsing or new basic operations |
| Submitting many calculations at once from a text file (`batch`) | Network, GUI or web interface |
| A pool of 3 worker threads (configurable at start) | `multiprocessing` or `asyncio` (stretch goal only) |
| Jobs saved to `jobs.json`; finished jobs also added to the calculator's history | Any database (SQLite, MySQL, etc.) |
| Log file `runner.log` written with the `logging` module | Third-party packages; standard library only |

**Rules:** no `eval()` or `exec()`, never kill a thread forcefully, and keep changes to Project 1's files small. New behaviour goes in new classes that inherit from the old ones.

## Functional requirements

Start with `python task_runner.py`. It loads the calculator's saved data, starts 3 worker threads, and shows the usual `>` prompt. Every Project 1 command keeps working exactly as before. The prompt must stay responsive while jobs run.

### New slow operations

These are added in a `ScientificCalculator` subclass. They work both directly (`fact 10`) and as jobs (`submit fact 50000`).

| Command | Example | Result |
| --- | --- | --- |
| `fact` | `fact 50000` | Factorial of n. For results over 50 digits, show the digit count instead (e.g. `213237 digits`) |
| `primes` | `primes 2000000` | How many primes are ≤ n, and the largest one |
| `fib` | `fib 100000` | The nth Fibonacci number (digit count if over 50 digits) |

### New commands

| ID | Command | Example | Expected behaviour |
| --- | --- | --- | --- |
| FR-1 | `submit` | `submit primes 2000000` | Validates the calculator command, queues it, and prints `Job 3 queued` at once without waiting |
| FR-2 | `batch` | `batch sums.txt` | Reads a text file with one calculator command per line and submits each as a job. Prints how many were queued and lists invalid lines |
| FR-3 | `jobs` | `jobs` | Lists every job: id, command, state, and duration if finished |
| FR-4 | `result` | `result 3` | Prints the job's result, or its current state if not finished |
| FR-5 | `workers` | `workers` | Shows each worker thread's name and the job it is running, or `idle` |
| FR-6 | `help` | `help` | Lists the old and new commands together |
| FR-7 | `quit` | `quit` | Stops taking new jobs, waits for running jobs to finish, saves everything, then exits |

Job states, in order: `QUEUED` → `RUNNING` → `DONE` or `FAILED`.

### Linking with Project 1 features

| ID | Requirement |
| --- | --- |
| FR-8 | When a job finishes, its calculation is added to the existing `History`, so `history` and `stats` include background results |
| FR-9 | `last` in a submitted command uses the last result at the moment you submit, not when the job runs. E.g. `submit mul last 2` stores the real number in the job |
| FR-10 | Memory commands (`ms`, `mr`, `mc`) are not allowed in `submit`; print `ms can't be run as a job` |

### Saving data

| ID | Requirement |
| --- | --- |
| FR-11 | Save all jobs to `jobs.json` every time a job changes state. Calculator history keeps saving to `calculator_data.json` as before |
| FR-12 | On start, load past jobs. If the file is missing, start empty |
| FR-13 | Jobs left `QUEUED` or `RUNNING` when the program last stopped are marked `FAILED` with reason `interrupted` |
| FR-14 | New job ids continue from the highest saved id, never reusing one |

## Technical requirements

Each requirement exists to exercise a specific skill. Reviewers will check these directly.

### Reusing Project 1

- **TR-1:** Import `Calculator`, `History` and `CalculatorApp` from `calculator.py`. Do not copy and paste their code.
- **TR-2:** `ScientificCalculator(Calculator)` adds `fact`, `primes` and `fib`, and registers them in the inherited operations dictionary in its `__init__` (call `super().__init__()` first).
- **TR-3:** `TaskRunnerApp(CalculatorApp)` adds the new commands by extending the inherited command dictionary, not with `if/elif`. Override `run()` only if you must, and explain why in a comment.
- **TR-4:** Running `python calculator.py` on its own must still work, and Project 1's tests must still pass unchanged.

### Threading and concurrency

- **TR-5:** Workers are `threading.Thread` objects named `worker-1`, `worker-2`, and so on.
- **TR-6:** The input loop puts job ids on a `queue.Queue`; workers take them with `queue.get()`. Workers never read input or print.
- **TR-7:** Each worker calls the shared `ScientificCalculator` to do the maths. The calculator has no shared mutable state, so it needs no lock. Explain in a comment why that is safe.
- **TR-8:** The jobs dictionary, the `History` object and both JSON files are shared. Protect all of them with one `threading.Lock`, always used as `with self.lock:`.
- **TR-9:** Never run a calculation while holding the lock. Lock only to read or update shared data.
- **TR-10:** Shutdown uses a `threading.Event`. On `quit` or Ctrl+C, set the event, let workers finish their current job, then `join()` every thread.

### Classes and data types

- **TR-11:** Each job is a `@dataclass` called `Job` with: `id` (int), `command` (str), `operands` (tuple, as in Project 1), `state`, `result`, `error`, `started_at`, `finished_at`.
- **TR-12:** Job states are an `enum.Enum` called `JobState`.
- **TR-13:** All jobs live in a dictionary keyed by id: `{1: Job(...), 2: Job(...)}`. A `JobManager` class owns it, along with the queue, the lock and saving.
- **TR-14:** Custom exceptions `JobNotFoundError` and `InvalidJobError`.
- **TR-15:** `jobs` builds its output with `sorted()` and a `key`, and `batch` collects invalid lines into a list of `(line_number, text)` tuples.

### Files, big numbers and logging

- **TR-16:** Save `jobs.json` with `json` and `pathlib`. Write to a temporary file first, then rename it over the real one, so a crash never leaves a half-written file.
- **TR-17:** Convert tuples, enums and datetimes to JSON-safe values on save, and back on load.
- **TR-18:** Very large results (e.g. `fact 50000`) can't be turned into a string by default in Python 3.11+. Store and show the digit count instead, and explain in the README how you calculated it.
- **TR-19:** Use `logging` to write `runner.log`, with the time and thread name on each line, e.g. `2026-11-11 10:02:15 [worker-2] Job 3 DONE in 1.84s`.

### Allowed modules

- **TR-20:** Only these standard library modules: `threading`, `queue`, `dataclasses`, `enum`, `json`, `pathlib`, `logging`, `math`, `time`, `datetime`, `os`, `sys`, `unittest`, `tempfile`. Ask before using anything else.
- **TR-21:** PEP 8 naming, a docstring on every class and public method, and type hints on method signatures.

## Suggested design

The input loop is the **producer**: it validates a calculator command, creates a `Job` and puts its id on the queue. Workers are **consumers**: each takes a job, calls the calculator, then records the result and adds it to `History` under the lock. This skeleton is a starting point; you may change it if you can explain why.

```python
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
```

Example `sums.txt` for `batch`:

```
add 4 5
primes 1000000
fact 20000
div 1 0
fly 3
```

### Sample session

```
Loaded 12 past calculations from calculator_data.json
Loaded 0 past jobs from jobs.json
Calculator with 3 background workers. Type 'help' for commands.
> add 4 5
9
> submit primes 2000000
Job 1 queued
> submit fact 50000
Job 2 queued
> submit mul last 2
Job 3 queued   (last = 9)
> workers
worker-1: running job 1 (primes 2000000)
worker-2: running job 2 (fact 50000)
worker-3: idle
> result 3
18
> batch sums.txt
Queued 4 jobs (4-7). Skipped 1 invalid line:
  line 5: Unknown command 'fly'
> jobs
 1  primes 2000000   DONE    1.84s
 2  fact 50000       DONE    0.92s
 3  mul 9 2          DONE    0.00s
 4  add 4 5          DONE    0.00s
 5  primes 1000000   RUNNING
 6  fact 20000       QUEUED
 7  div 1 0          FAILED  cannot divide by zero
> result 1
148933 primes, largest 1999993
> result 2
213237 digits
> history
...
13. add (4, 5) = 9
14. mul (9, 2) = 18
...
> quit
Waiting for 2 jobs to finish...
Saved 7 jobs to jobs.json. Goodbye!
```

## Error handling

Check what you can **before** queuing (bad command, wrong number of operands, not a number). Errors that only happen while running (divide by zero, negative square root) are caught inside the worker: mark the job `FAILED`, store the message, and keep the worker running.

| Situation | Example | Behaviour |
| --- | --- | --- |
| Unknown command | `submit fly 3` | `Unknown command 'fly'`; nothing queued |
| Bad operand | `submit fact abc` | `'abc' is not a valid number`; nothing queued |
| Too large | `submit fact 10000000` | `fact is limited to n ≤ 200000`; nothing queued |
| Fails while running | `submit div 1 0` | Job queued, then `FAILED: cannot divide by zero` |
| Memory command | `submit ms` | `ms can't be run as a job` |
| Batch file missing | `batch nope.txt` | `File not found: nope.txt` |
| Unknown job id | `result 99` | `No job with id 99` |
| Corrupted `jobs.json` | — | Warning, rename to `jobs.json.bak`, start empty |
| Ctrl+C | — | Same clean shutdown as `quit` |

## Testing

- Add `test_task_runner.py` using `unittest`. Project 1's `test_calculator.py` must still pass unchanged.
- Test `fact`, `primes` and `fib` directly on `ScientificCalculator`, with no threads (e.g. `count_primes(100)` returns `(25, 97)`).
- **Concurrency test:** submit 100 `add` jobs, wait for all to finish, and check there are exactly 100 `DONE` jobs with unique ids and 100 new `History` entries.
- **Shutdown test:** start workers, signal stop, and check every thread has ended (`is_alive()` is `False`) within 2 seconds.
- **Batch test:** a temporary file with 3 valid and 2 invalid lines queues exactly 3 jobs.
- Use `tempfile` so tests never touch the real `jobs.json` or `calculator_data.json`.
- Aim for at least 15 new test cases. All must pass before review.

## Race condition exercise

Before the final review, temporarily remove the lock around `History` and the job id counter. Run the 100-job concurrency test 10 times. In the README, write 3–5 sentences on what went wrong (lost history entries, duplicate ids) or why it didn't show up. Then put the lock back. This is graded on the explanation, not the result.

## Acceptance criteria

- [ ] All Project 1 commands and tests still work unchanged
- [ ] All 14 functional requirements work as shown in the sample session
- [ ] The prompt stays responsive while `primes 2000000` runs
- [ ] `ScientificCalculator` and `TaskRunnerApp` inherit from Project 1 classes; no copied code
- [ ] Finished jobs appear in `history` and `stats`
- [ ] Shared data is only touched inside `with self.lock:`, and no calculation runs while holding it
- [ ] `quit` and Ctrl+C both shut down cleanly with no lost jobs
- [ ] A failing job never crashes a worker
- [ ] Jobs survive a restart via `jobs.json`; no database, no third-party packages
- [ ] At least 15 new passing tests, including concurrency, shutdown and batch tests
- [ ] README includes the race condition write-up

## Deliverables

- `task_runner.py` — the add-on, in the same repository as the calculator
- `test_task_runner.py` — the new tests
- `README.md` — updated with how to run the task runner, a short design explanation, and the race condition write-up
- `sums.txt` — an example batch file
- Small, meaningful commits on a new branch, merged after review

## Stretch goals (optional)

- `cancel <id>` for jobs still `QUEUED`.
- Job priorities with `queue.PriorityQueue` (`submit --high fact 50000`).
- A `@timed` decorator that records each job's duration.
- Run `batch` with 10 `primes 2000000` lines using 1 worker, then 4 workers. Time both and explain why threads barely help CPU-heavy work in Python (the GIL). Then try `concurrent.futures.ProcessPoolExecutor`.
