from dataclasses import dataclass
from enum import Enum


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
