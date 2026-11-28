"""Background worker threads."""

from src.calculator.worker import Job, JobManager, queue, threading

class Worker:
    def __init__(self, name: str, manager: JobManager) -> None:
        self.manager = manager
        self.current_job: Job | None = None
        self.thread = threading.Thread(target=self._loop, name=name)

    def _loop(self) -> None:
        while not self.manager.stop_event.is_set():
            try:
                # 0.5s timeout lets thread regularly check stop_event so quit doesn't block forever
                job_id = self.manager.queue.get(timeout=0.5)
                if self.manager.stop_event.is_set():
                    self.manager.queue.task_done()
                    break
            except queue.Empty:
                continue

            job = self.manager.mark_running(job_id)
            if job is None:
                self.manager.queue.task_done()
                continue

            self.current_job = job
            try:
                result = self.manager.calculator.calculate(job.command, *job.operands)
                self.manager.finish(job_id, result)
            except (ArithmeticError, LookupError, TypeError, ValueError) as e:
                self.manager.fail(job_id, str(e))
            finally:
                self.current_job = None
                self.manager.queue.task_done()

    def status(self) -> str:
        job = self.current_job
        if job is None:
            return f"{self.thread.name}: idle"
        ops_str = " ".join(str(o) for o in job.operands)
        return f"{self.thread.name}: running job {job.id} ({job.command} {ops_str})"
