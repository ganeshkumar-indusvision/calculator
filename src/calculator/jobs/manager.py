"""Background job manager."""

import json
import logging
import os
import queue
import threading
import time
from pathlib import Path

from src.calculator.core.history import History
from src.calculator.core.models import Calculation
from src.calculator.jobs.models import Job, JobState
from src.calculator.core.scientific import ScientificCalculator
from src.calculator.config import JOBS_FILE
from src.calculator.utils.formatting import Utils
from src.calculator.utils.writer import AtomicWriter
from src.calculator.utils.logging_setup import configure_worker_logger
from src.calculator.jobs.errors import JobNotFoundError
from src.calculator.jobs.views import JobViews

class JobManager(JobViews):
    """Owns jobs, the queue, the lock and saving. Safe to call from any thread."""

    def __init__(self, calculator: ScientificCalculator, history: History, utils: Utils,logger: logging.Logger, jobs_file: Path | None = None,data_file: Path | None = None) -> None:
        self.calculator = calculator
        self.history = history           
        self.jobs: dict[int, Job] = {}
        self.queue: queue.Queue[int] = queue.Queue()
        self.lock = threading.RLock() # Using this because if there is multiple locks aquring by same thread under it is should not cause  deadlock
        self.stop_event = threading.Event()
        self._next_id: int = 1 
        self.jobs_file = jobs_file if jobs_file is not None else JOBS_FILE
        self.utils = utils
        self.logger = self._init_file_logger(logger)
        self.info_logger = logger
        self.data_file = data_file
    def batch_submit(self, jobs: list[tuple[str, tuple]]) -> list[int]:
        """Add multiple jobs to the queue and save once."""
        if not jobs:
            return []
        with self.lock:
            job_ids = [self._enqueue(command, operands).id for command, operands in jobs]
        self.save()
        return job_ids
    def _init_file_logger(self, logger: logging.Logger) -> logging.Logger:
        return configure_worker_logger(logger)

    def submit(self, command: str, operands: tuple) -> int:
        """Add a job in the queue and return it's id."""
        # Here, lock needed because there is Read and write operation
        with self.lock:
            job = self._enqueue(command, operands)
        self.save()
        self.logger.info(f"Job-{job.id} Queued ({command} {operands})")
        return job.id
    def _enqueue(self, command: str, operands: tuple) -> Job:
        job_id = self._next_id
        self._next_id += 1
        job = Job(id=job_id, command=command, operands=tuple(operands))
        self.jobs[job_id] = job
        self.queue.put(job_id)
        return job

    def get(self, job_id: int) -> Job: 
        with self.lock:
            if job_id not in self.jobs:
                raise JobNotFoundError(job_id=job_id)
            return self.jobs[job_id]
    
    def record_calculation(self,op: str,operands: tuple,result: object,data_file: Path | None = None,memory: object = None) -> None:
        with self.lock:
            value = result[0] if op == "primes" else result
            value, _ = self.utils.check_digit(value)
            self.history.add(Calculation(op, tuple(operands), value))

            target_file = data_file or self.data_file
            if target_file:
                mem = self.utils.memory if memory is None else memory
                try:
                    self.history.save(target_file, mem)
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
        formatted = self.utils.formate_msg(job.command, result)
        self.logger.info(f"Job {job_id} Finished ({job.command} {job.operands} = {formatted})")

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
        with self.lock:
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
            try:
                AtomicWriter().write_json(self.jobs_file, data)
            except OSError as e:
                self.logger.warning(f"Could not save jobs: {e}")


    def mark_running(self, job_id: int) -> Job | None:
        with self.lock:
            if self.stop_event.is_set() or job_id not in self.jobs:
                return None
            job = self.jobs[job_id]
            job.state = JobState.RUNNING
            job.started_at = time.time() 
        self.save()
        self.logger.debug(f"Job {job_id} Running ({job.command} {job.operands})")
        return job


    def load(self) -> int:
        """Load jobs from the file and mark unfinished ones as interrupted."""
        if not self.jobs_file.exists():
            return 0
        try:
            with open(self.jobs_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise TypeError("Top-level JSON must be an object")

            loaded: dict[int, Job] = {}
            for item in data.values():
                state = JobState(item["state"])
                error = item.get("error")
                if state in (JobState.QUEUED, JobState.RUNNING):
                    state = JobState.FAILED
                    error = "interrupted"
                job = Job(
                    id=item["id"],
                    command=item["command"],
                    operands=tuple(item["operands"]),
                    state=state,
                    result=item["result"],
                    error=error,
                    started_at=item["started_at"],
                    finished_at=item["finished_at"],
                )
                loaded[job.id] = job
        except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError, AttributeError):
            back_file = self.jobs_file.with_name(self.jobs_file.name + ".bak")
            try:
                os.replace(self.jobs_file, back_file)
                self.info_logger.warning(f"Warning: {self.jobs_file} was invalid. Renamed to {back_file.name}.")
            except OSError:
                self.info_logger.warning(f"Warning: could not read {self.jobs_file}. Starting empty.")
            return 0

        with self.lock:
            self.jobs.update(loaded)
            if self.jobs:
                self._next_id = max(self.jobs.keys()) + 1
            return len(loaded)
