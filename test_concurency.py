# test_concurrency.py
import shutil
import threading
import time
from pathlib import Path

import calculator
from task_runner import TaskRunnerApp, JobState 
import sys
sys.setswitchinterval(1e-6)  
TEST_DIR = Path("tests")


class NoLock:
    """Does nothing. Used to simulate removing the lock."""
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fresh_test_dir():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir()


def wait_for_all_jobs(app, n_jobs, timeout=30):
    """Block until every job is DONE or FAILED, or until timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with app.manager.lock:
            states = [job.state for job in app.manager.jobs.values()]
        finished = sum(1 for s in states if s in (JobState.DONE, JobState.FAILED))
        if len(states) == n_jobs and finished == n_jobs:
            return True
        time.sleep(0.05)
    return False


def run(use_lock: bool, n_jobs: int = 100):
    fresh_test_dir()
    calculator.DATA_FILE = TEST_DIR / "calc.json"

    app = TaskRunnerApp()
    app.manager.jobs_file = TEST_DIR / "jobs.json"
    # workers are already started by TaskRunnerApp.__init__ — don't stop them,
    # we need them running so jobs actually reach DONE/FAILED

    if not use_lock:
        app.manager.lock = NoLock()
        app.history._lock = NoLock()

    threads = [
        threading.Thread(target=app.manager.submit, args=("fact", (4000,)))
        for _ in range(n_jobs)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    all_finished = wait_for_all_jobs(app, n_jobs)

    ids = list(app.manager.jobs.keys())
    duplicate_ids = len(ids) - len(set(ids))
    done = sum(1 for j in app.manager.jobs.values() if j.state == JobState.DONE)
    failed = sum(1 for j in app.manager.jobs.values() if j.state == JobState.FAILED)
    stuck = sum(1 for j in app.manager.jobs.values() if j.state in (JobState.QUEUED, JobState.RUNNING))

    print(f"jobs stored: {len(app.manager.jobs)}/{n_jobs}, duplicate ids: {duplicate_ids}, "
          f"done: {done}, failed: {failed}, stuck: {stuck}, history: {len(app.history)}, "
          f"all_finished_in_time: {all_finished}")

    app._exit()


if __name__ == "__main__":
    import sys
    use_lock = "--nolock" not in sys.argv
    print(f"=== running {'WITH' if use_lock else 'WITHOUT'} lock ===")
    for i in range(1, 11):
        print(f"run {i}:", end=" ")
        run(use_lock=use_lock)