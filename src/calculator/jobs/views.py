"""Job rendering views."""

from src.calculator.jobs.models import JobState


class JobViews:
    """Render job listings."""

    def show_jobs(self) -> str:
        with self.lock:
            snapshot = {
                job_id: {
                    "command": job.command,
                    "operands": job.operands,
                    "state": job.state,
                    "duration": job.duration,
                    "error": job.error,
                }
                for job_id, job in self.jobs.items()
            }

        if not snapshot:
            return "No jobs yet"

        lines = []
        for job_id in sorted(snapshot):
            job = snapshot[job_id]
            ops_str = " ".join(str(o) for o in job["operands"])
            cmd_str = f"{job['command']} {ops_str}".strip()
            if job["state"] == JobState.DONE:
                dur = f"{job['duration']:.2f}s" if job["duration"] is not None else "0.00s"
                lines.append(f" {job_id:<2} {cmd_str:<16} DONE    {dur}")
            elif job["state"] == JobState.FAILED:
                lines.append(f" {job_id:<2} {cmd_str:<16} FAILED  {job['error'] or ''}")
            elif job["state"] == JobState.RUNNING:
                lines.append(f" {job_id:<2} {cmd_str:<16} RUNNING")
            else:
                lines.append(f" {job_id:<2} {cmd_str:<16} QUEUED")
        return "\n".join(lines)
