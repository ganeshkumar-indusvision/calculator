import json
import math
from pathlib import Path


class JobManagerData:
    def create_initial_files(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)

        jobs_file = directory / "jobs.json"
        history_file = directory / "calculator_data.json"

        jobs = {
            "1": {
                "id": 1,
                "command": "add",
                "operands": [4, 5],
                "state": "done",
                "result": 9,
                "error": None,
                "started_at": 1000.0,
                "finished_at": 1001.0
            },
            "2": {
                "id": 2,
                "command": "primes",
                "operands": [10],
                "state": "queued",
                "result": None,
                "error": None,
                "started_at": None,
                "finished_at": None
            },
            "3": {
                "id": 3,
                "command": "fib",
                "operands": [10],
                "state": "running",
                "result": None,
                "error": None,
                "started_at": 1002.0,
                "finished_at": None
            },
            "4": {
                "id": 4,
                "command": "div",
                "operands": [10, 0],
                "state": "failed",
                "result": None,
                "error": "Error: cannot divide by zero",
                "started_at": 1003.0,
                "finished_at": 1004.0
            }
        }

        history = {
            "memory": 7.5,
            "history": [
                {
                    "op": "mul",
                    "operands": [3, 4],
                    "result": 12
                }
            ]
        }

        with open(jobs_file, "w", encoding="utf-8") as file:
            json.dump(jobs, file, indent=2)

        with open(history_file, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=2)

        return jobs_file, history_file

class UtilsData:
    def __init__(self, digit_limit=50):
        at_limit = 10 ** (digit_limit - 1)
        over_limit = 10 ** digit_limit
        fact_100 = math.factorial(100)
        fact_5000 = math.factorial(5000)
        fib_1000 = self._fib(1000)
        huge_count = 10 ** 60

        self.check_digit_cases = [
            (42,         42,              False),
            (0,          0,               False),
            (-123,       -123,            False),
            (at_limit,   at_limit,        False),
            (over_limit, digit_limit + 1, True),
            (fact_100,   158,             True),
            (fact_5000,  16326,           True),
        ]

        self.check_digit_passthrough_cases = [
            (True,    True,    False),
            (False,   False,   False),
            ("hello", "hello", False),
            (3.14,    3.14,    False),
        ]
        self.add_digit_words_cases = [
            ("213237", "213237 digits"),
        ]
        self.formate_msg_cases = [
            ("add",    9,                 "9"),
            ("sub",    -5,                "-5"),
            ("div",    2.5,               "2.5"),
            ("mul",    42,                "42"),
            ("fact",   120,               "120"),
            ("fact",   at_limit,          str(at_limit)),
            ("fact",   fact_100,          "158 digits"),
            ("fact",   fact_5000,         "16326 digits"),
            ("fib",    55,                "55"),
            ("fib",    fib_1000,          "209 digits"),
            ("primes", (148933, 1999993), "148933 primes, largest 1999993"),
            ("primes", (25, 97),          "25 primes, largest 97"),
            ("primes", (4, 7),            "4 primes, largest 7"),
            ("primes", (huge_count, 97),  "61 primes digits, largest 97"),
        ]

    @staticmethod
    def _fib(n):
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a
