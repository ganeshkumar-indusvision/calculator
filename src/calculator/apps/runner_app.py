"""Task runner application."""

import logging

from src.calculator.apps.calculator_app import CalculatorApp
from src.calculator.apps.runnerhelper.runnerbatch import BatchSubmission
from src.calculator.apps.runnerhelper import RunnerHelper
from src.calculator.jobs.jobhelper import JobState
from src.calculator.core.calculator import Calculator
from src.calculator.core.scientific import ScientificCalculator
from src.calculator.config import NUM_WORKERS
from src.calculator.utils.formatting import Utils
from src.calculator.jobs.jobhelper import JobManager
from src.calculator.jobs.jobhelper import Worker

class TaskRunnerApp(CalculatorApp, RunnerHelper, BatchSubmission):
    """The calculator app plus background job commands."""

    def __init__(self, data_file=None, log_file=None, jobs_file=None, num_workers: int | None = None) -> None:
        super().__init__(data_file=data_file, log_file=log_file)
        num_workers = num_workers if num_workers is not None else NUM_WORKERS
        if num_workers < 1:
            raise ValueError(f"num_workers must be >= 1, got {num_workers}")
        self.utils = Utils(self.calculator)
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
        self.utils.memory = self.memory
        self.app_handlers.update({
            "jobs": self._show_jobs,
            "workers": self._show_workers,
        })

        self.task_handlers = {
            "submit": self._handle_submit,
            "batch": self._handle_batch,
            "result": self._handle_result,
        }
        
        self._workers_started = False
        self.manager = JobManager(
                        self.calculator,
                        self.history,
                        self.utils,
                        logger=self.logger,
                        data_file=self.data_file,
                        jobs_file=jobs_file,
                    )
        
        self.workers = [Worker(f"worker-{i}", self.manager) for i in range(1, num_workers + 1)]
        self.start_worker()
        self._load_manager()

    def _load_manager(self) -> None:
        jobs = self.manager.load()
        self.logger.info(f"Loaded {jobs} past jobs from {self.manager.jobs_file}")


    def start_worker(self) -> None:
        for w in self.workers:
            w.thread.start()
        self._workers_started = True     


    def _make_calculator(self) -> Calculator:
        return ScientificCalculator()


    def _display_result(self,op, operands, result):
        msg = self.utils.formate_msg(op,result)
        self.logger.debug(f"{op} {operands} {msg}")
        self.logger.info("%s", msg)

        
    def _process_task_command(self, tokens: tuple) -> None:
        op = tokens[0].lower()
        args = tokens[1:]
    
        handler = self.task_handlers.get(op)
        if handler:
            handler(args)


    def _exit(self) -> None:
        self.manager.stop_event.set()
        if self._workers_started:
            running = sum(1 for w in self.workers if w.current_job is not None)
            if running:
                word = "job" if running == 1 else "jobs"
                self.logger.info(f"Waiting for {running} {word} to finish...")
            for worker in self.workers:
                worker.thread.join()

        total = len(self.manager.jobs)
        self.logger.info("Saving jobs, please wait...")
        self.manager.save()

        word = "job" if total == 1 else "jobs"
        self.logger.info(f"Saved {total} {word} to {self.manager.jobs_file.name}.")
        super()._exit()

    def handle_command(self, command: str) -> None:
        tokens = tuple(command.split())

        if tokens and tokens[0].lower() in self.task_handlers:
            self._process_task_command(tokens)
            return

        super().handle_command(command)
        self.utils.memory = self.memory
    def __del__(self) -> None:
        if hasattr(self, "manager"):
            self.manager.logger.handlers.clear()
        super().__del__()
