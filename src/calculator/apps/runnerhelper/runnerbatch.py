"""Batch submission mixin."""

from pathlib import Path

from src.calculator.jobs.errors import InvalidJobError


class BatchSubmission:
    """Submit batches of calculations from files."""
    def _read_batch_file(self, path: Path) -> list[str] | None:
        try:
            return path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            self.logger.warning(f"File not found: {path.name}")
        except OSError as e:
            self.logger.warning(f"Could not read {path.name}: {e}")
        return None
    def _handle_batch(self, args: tuple) -> None:
        if len(args) != 1:
            self.logger.warning("Usage: batch <filename>")
            return

        lines = self._read_batch_file(Path(args[0]))
        if lines is None:
            return

        valid_jobs, invalid = [], []
        for line_no, line in enumerate(lines, start=1):
            parts = tuple(line.split())
            if not parts or parts[0].startswith("#"):
                continue
            try:
                valid_jobs.append(self._validate_submit(parts))
            except (ValueError,InvalidJobError, TypeError) as e:
                invalid.append((line_no, str(e)))

        queued_ids = self.manager.batch_submit(valid_jobs)

        if queued_ids:
            rng = f"{queued_ids[0]}-{queued_ids[-1]}" if len(queued_ids) > 1 else str(queued_ids[0])
            msg = f"Queued {len(queued_ids)} jobs ({rng})."
        else:
            msg = "Queued 0 jobs."

        if invalid:
            suffix = "line" if len(invalid) == 1 else "lines"
            self.logger.warning(f"{msg} Skipped {len(invalid)} invalid {suffix}:")
            for lno, err in invalid:
                self.logger.warning(f"  line {lno}: {err}")
        else:
            self.logger.info(msg)
