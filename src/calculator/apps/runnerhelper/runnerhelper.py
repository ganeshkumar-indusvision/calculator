"""Runner command handlers mixin."""

from src.calculator.core.calculator import Calculator
from src.calculator.jobs.errors import InvalidJobError, JobNotFoundError
from src.calculator.jobs.models import JobState


class RunnerHelper:
    """Background-job command handlers."""
    def validate_request(self, op: str, *args: object) -> None:
        if op not in self.calculator.operations:
            raise ValueError(f"Unknown operation: {op}")

        expected, _ = self.calculator.operations[op]

        if len(args) != expected:
            raise ValueError(f"{op} requires {expected} argument(s)")
    def _validate_submit(self, args: tuple, allow_last: bool = False) -> tuple[str, tuple]:
        if not args:
            raise InvalidJobError("", "Usage: submit <operation> <arguments>")

        op, operands = args[0].lower(), args[1:]

        if op not in self.command_info:
            raise InvalidJobError(op, f"Unknown command '{op}'")

        job_commands = self.command_info.keys() - self.app_handlers.keys() - self.task_handlers.keys()
        if op not in job_commands:
            raise InvalidJobError(op, f"{op} can't be run as a job")

        expected = self.command_info[op][0]
        if len(operands) != expected:
            raise InvalidJobError(op, f"{op} requires {expected} argument(s)")

        converted_list = []
        for s in operands:
            if s.lower() == "last":
                if not allow_last:
                    raise InvalidJobError(op, "'last' is not allowed in batch files")
                with self.manager.lock:
                    last_val = self.history.last_result()
                if last_val is None:
                    raise InvalidJobError(op, "No previous result for 'last'")
                converted_list.append(last_val)
            else:
                val = self._detect_numeric_type(s)
                if val is None:
                    raise InvalidJobError(op, f"'{s}' is not a valid number")
                converted_list.append(val)

        converted = tuple(converted_list)
        try:
            self.validate_request(op, *converted)
            if op in self.calculator.scientific_operations:
                for val in converted:
                    self.calculator._validate_number(val, op)
                self.calculator.validation[op](*converted)
        except ValueError as e:
            raise InvalidJobError(op, str(e)) from e

        return op, converted
    def _handle_submit(self, args: tuple) -> int | None:
        try:
            op, converted = self._validate_submit(args, allow_last=True)
        except (ValueError,InvalidJobError )as e:
            if str(e):
                self.logger.warning(str(e))
            return None

        job_id = self.manager.submit(op, converted)
        last_idx = next((i for i, s in enumerate(args[1:]) if s.lower() == "last"), None)
        if last_idx is not None:
            self.logger.info(f"Job {job_id} queued   (last = {converted[last_idx]})")
        else:
            self.logger.info(f"Job {job_id} queued")
        return job_id
    def _handle_result(self, args: tuple) -> None:
        if len(args) != 1:
            self.logger.warning("Usage: result <job_id>")
            return

        try:
            job_id = int(args[0])

        except ValueError:
            self.logger.warning(f"'{args[0]}' is not a valid job id")
            return
        try:
            job = self.manager.get(job_id)
        except JobNotFoundError as e:
            self.logger.warning(str(e))
            return

        if job.state == JobState.DONE:
            self.logger.info("%s", self.utils.formate_msg(job.command, job.result))
        elif job.state == JobState.FAILED:
            self.logger.warning(f"FAILED: {job.error}")
        else:
            self.logger.info("%s", job.state.value.upper())
    def _show_jobs(self) -> None:
        self.logger.info("%s", self.manager.show_jobs())
    def _show_workers(self) -> None:
        if not self._workers_started:
            self.logger.info("(workers not started — submit a job first)")
            return
        for worker in self.workers:
            self.logger.info(worker.status())
