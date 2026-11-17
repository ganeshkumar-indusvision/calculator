import time
from pathlib import Path
from calculator import History
from task_runner import JobManager, Worker, ScientificCalculator



# def run(worker,jobs,n):
#     sci_cal = ScientificCalculator()
#     job_manager = JobManager()
#     workers = [Worker(f"worker{i}")for i in range(2)]
#     [worker.thread.start() for worker in workers]
#     t0  =time.perf_counter()




def run(num_workers, jobs, n):
    calc = ScientificCalculator()
    mgr = JobManager(calc, History(), jobs_file=Path("/tmp/bench.json"))
    ws = [Worker(f"w-{i}", mgr) for i in range(1, num_workers + 1)]
    for w in ws:
        w.thread.start()
    t0 = time.perf_counter()
    for _ in range(jobs):
        mgr.submit("primes", (n, None))
    mgr.queue.join()
    elapsed = time.perf_counter() - t0
    mgr.stop_event.set()
    for w in ws:
        w.thread.join(timeout=2.0)
    return elapsed

n = 1_000_000
print(f"1 worker, 4 jobs:  {run(1, 4, n):.3f}s")   # expect ~0.30s
print(f"4 workers, 4 jobs: {run(4, 4, n):.3f}s")   # see below