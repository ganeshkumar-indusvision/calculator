Free threaded
4 workers
```
(ml) gk@jarvis:~/indus/calculator$ uv run --python 3.14t task_runner.py 
Loaded 19 past calculations from output/calculator_data.json
Loaded 0 past jobs from output/jobs.json
Python Calculator — type 'help' for commands
> batch batch.txt
Queued 10 jobs (1-10).
> jobs
 1  primes 2000000   DONE    0.64s
 2  primes 2000000   DONE    0.66s
 3  primes 2000000   DONE    0.62s
 4  primes 2000000   DONE    0.61s
 5  primes 2000000   DONE    0.60s
 6  primes 2000000   DONE    0.63s
 7  primes 2000000   DONE    0.78s
 8  primes 2000000   DONE    0.69s
 9  primes 2000000   DONE    0.64s
 10 primes 2000000   DONE    0.57s
> 
```

4 workers
```
(ml) gk@jarvis:~/indus/calculator$ uv run --python 3.11 task_runner.py 
Loaded 29 past calculations from output/calculator_data.json
Loaded 10 past jobs from output/jobs.json
Python Calculator — type 'help' for commands
> batch batch.txt
Queued 10 jobs (11-20).
> jobs
 1  primes 2000000   DONE    0.64s
 2  primes 2000000   DONE    0.66s
 3  primes 2000000   DONE    0.62s
 4  primes 2000000   DONE    0.61s
 5  primes 2000000   DONE    0.60s
 6  primes 2000000   DONE    0.63s
 7  primes 2000000   DONE    0.78s
 8  primes 2000000   DONE    0.69s
 9  primes 2000000   DONE    0.64s
 10 primes 2000000   DONE    0.57s
 11 primes 2000000   DONE    2.85s
 12 primes 2000000   DONE    1.59s
 13 primes 2000000   DONE    1.41s
 14 primes 2000000   DONE    1.65s
 15 primes 2000000   DONE    1.56s
 16 primes 2000000   DONE    2.44s
 17 primes 2000000   DONE    1.82s
 18 primes 2000000   DONE    1.43s
 19 primes 2000000   DONE    1.57s
 20 primes 2000000   DONE    1.40s
```


