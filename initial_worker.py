import time
from pathlib import Path
from calculator import History
from task_runner import JobManager, Worker, ScientificCalculator, JobState

calc    = ScientificCalculator()
history = History()
manager = JobManager(calc, history, jobs_file=Path("/tmp/jobs_diag.json"))

# worker = Worker("worker-1", manager)
workers =[Worker(f"worker-{i}",manager)for i in range(1,5)]

[worker.thread.start() for worker in workers]
valeu =401
start = time.perf_counter()
for i in range(valeu):
    manager.submit("primes", (i, None))
print("main: 5 jobs submitted")

manager.queue.join()
print("main: all jobs processed\n")

# for jid in range(1, valeu):
#     j = manager.get(jid)
    # dur = f"{j.duration:.4f}s" if j.duration is not None else "None"
    # print(f"job {jid}  {j.command:7} {str(j.operands):12}  "
    #       f"state={j.state.value:8}  "
    #       f"result={j.result}  "
    #       f"error={j.error!r}  "
    #       f"duration={dur}")

print(f"\nhistory: {len(history)} entries")
print(f"last_result: {history.last_result()}")

manager.stop_event.set()
[worker.thread.join(timeout=2.0) for worker in workers]
print("\nmain: worker stopped, bye")

end = time.perf_counter()
print(f"Total runtime of the program in simple is {end - start} seconds")