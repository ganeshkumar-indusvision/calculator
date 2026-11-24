import time
from pathlib import Path
from calculator import History
from task_runner import JobManager, Worker, ScientificCalculator



def run(worker,jobs,n):
    sci_cal = ScientificCalculator()
    manager = JobManager(sci_cal,History(),jobs_file=Path("/tmp/bench.json"))
    workers = [Worker(f"worker-{i}",manager) for i in range(worker)]
    [manager.submit("primes",(n,))for _ in range(jobs)]
    t0  =time.perf_counter()
    [worker.thread.start() for worker in workers]
    manager.queue.join()
    manager.stop_event.set()
    print(f"Total time taken {time.perf_counter() - t0}")
    [worker.thread.join() for worker in workers]
    return

run(4,100,1_000_000)
# run(4,100,100000000)


# def run(num_workers, jobs, n):
#     calc = ScientificCalculator()
#     mgr = JobManager(calc, History(), jobs_file=Path("/tmp/bench.json"))
#     ws = [Worker(f"w-{i}", mgr) for i in range(1, num_workers + 1)]
#     for w in ws:
#         w.thread.start()
#     t0 = time.perf_counter()
#     for _ in range(jobs):
#         mgr.submit("primes", (n, None))
#     mgr.queue.join()
#     elapsed = time.perf_counter() - t0
#     mgr.stop_event.set()
#     for w in ws:
#         w.thread.join(timeout=2.0)
#     return elapsed

# n = 11_000_000
# print(f"1 worker, 4 jobs:  {run(1, 4, n):.3f}s")   # expect ~0.30s
# print(f"4 workers, 4 jobs: {run(4, 4, n):.3f}s")   # see below