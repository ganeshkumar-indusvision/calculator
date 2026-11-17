import time
from calculator import History
from task_runner import JobManager, Worker, ScientificCalculator

# 1. Build the pieces
calc    = ScientificCalculator()      # has add, sub, ..., fact, primes, fib
history = History()                    # shared history
manager = JobManager(calc, history)    # the "kitchen counter"

# 2. Build ONE worker and START it
worker = Worker("worker-1", manager)   # creates a Thread object — NOT running yet
worker.thread.start()                  # NOW the _loop() begins running in the background

# 3. Submit a job (main thread)
job_id = manager.submit("add", (4, 5))
print(f"main: submitted job {job_id}")     # id = 1

# 4. Wait for the worker to actually process it
#    queue.join() blocks until every task_done() has been called
manager.queue.join()
print("main: all jobs processed")

# 5. Read the result
job = manager.get(job_id)
print(f"main: state    = {job.state}")
print(f"main: result   = {job.result}")
print(f"main: duration = {job.duration:.4f}s")
print(f"main: history  = {len(history)} entries, last={history.last_result()}")

# 6. Shut the worker down (2-step: signal, then join)
manager.stop_event.set()               # worker's while-loop sees this on next pass
worker.thread.join(timeout=2.0)        # wait for the thread to finish
print("main: worker stopped, bye")