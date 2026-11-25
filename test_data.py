import math
import json
from pathlib import Path


class TestCalculatorData:
    def __init__(self):
        self.input_output: dict[str, list[tuple[float | int, float | None | int, float | int]]] = {
            "add": [
                (5, 6, 11), (-3, 3, 0), (0.1, 0.2, 0.3),
                (0, 0, 0), (1.5, 2.5, 4),
                (-1.5, -2.5, -4), (1e10, 1e10, 20000000000)],
            "sub": [
                (10, 3, 7), (-5, -3, -2),
                (0, 0, 0), (1.5, 0.5, 1),
                (-1.5, -0.5, -1), (1e10, 5e9, 5000000000)],
            "mul": [
                (3, 4, 12), (-2, 5, -10),
                (0, 10, 0), (1.5, 2.0, 3),
                (-1.5, -2.0, 3), (1e5, 1e5, 10000000000)],
            "div": [
                (7, 2, 3.5), (-10, 2, -5), (1, 3, 0.333),
                (1.5, 0.5, 3), (-1.5, -0.5, 3),
                (1e10, 1e5, 100000)],
            "pow": [
                (2, 3, 8), (2, 10, 1024), (2, 0, 1), (0, 5, 0),
                (5, 1, 5), (-2, 4, 16),
                (1.5, 2, 2.25), (-2, 3, -8),
                (1e2, 3, 1000000)],
            "mod": [
                (10, 3, 1), (-10, 3, 2), (-10, -3, -1), (10, -3, -2),
                (9, -4, -3),
                (10, -3, -2), (-10, -3, -1),
                (1.5, 1, 0.5)],
            "sqrt": [
                (25, None, 5), (0, None, 0),
                (2.25, None, 1.5), (1e4, None, 100)],
            "abs": [
                (-7, None, 7), (0, None, 0),
                (3.5, None, 3.5), (-3.5, None, 3.5)],
        }
        self.value_error_cases: list[
            tuple[float | int | bool | None,
                  float | int | bool | None,
                  type[Exception]]
        ] = [
            (1, None, ValueError), (None, None, ValueError),
            (math.nan, 1, ValueError), (1, math.nan, ValueError),
            (math.nan, math.nan, ValueError),
            (None, 1, ValueError), (1, 'a', ValueError),
            ('a', -2.5, ValueError), (True, 'a', ValueError),
            (False, 1, ValueError), (1, False, ValueError),
            (math.inf, 1, ValueError), (-math.inf, 1, ValueError),
            (1, math.inf, ValueError), (1, -math.inf, ValueError),
            (1, True, ValueError), (True, 1, ValueError),
        ]

        self.single_input_error_cases: list[
            tuple[float | int | bool | None,
                  float | int | bool | None,
                  type[Exception]]
        ] = [
            (None, None, ValueError), ('a', None, ValueError),
            (True, None, ValueError), (False, None, ValueError),
        ]

        self.error_cases: dict[
            str,
            list[tuple[float | int | bool | None,
                       float | int | bool | None,
                       type[Exception]]]
        ] = {
            "add":  self.value_error_cases,
            "sub":  self.value_error_cases,
            "mul":  self.value_error_cases,
            "div":  self.value_error_cases + [(5, 0, ZeroDivisionError)],
            "pow":  self.value_error_cases + [(0, -1, ZeroDivisionError),
                                              (-2, 0.5, ValueError)],
            "mod":  self.value_error_cases + [(5, 0, ZeroDivisionError)],
            "sqrt": self.single_input_error_cases + [(-5, None, ValueError)],
            "abs":  self.single_input_error_cases,
        }

        # Calls that don't fit the (op, a, b) shape: arity and unknown-op errors.
        self.bad_call_cases: list[tuple[tuple, type[Exception]]] = [
            ((),                ValueError),   # no operation
            (("power", 2, 3),   ValueError),   # unknown operation
            (("add",),          ValueError),   # binary op, missing operand
            (("add", 5),        ValueError),
            (("sqrt",),         ValueError),   # unary op, missing operand
            (("abs",),          ValueError),
            (("add", 1, 2, 3),  ValueError),   # too many operands
            (("sqrt", 4, 5),    ValueError),
            (("abs", 1, 2),     ValueError),
        ]


class ScientificCalculatorData(TestCalculatorData):
    def __init__(self):
        super().__init__()
        self.input_output.update({
"fact": [
    (0, None, 1),
    (5, None, 120),
    (41, None, 33452526613163807108170062053440751665152000000000),
    (50, None, 30414093201713378043612608166064768844377641568960512000000000000),
],
    "primes": [
        (10, None, (4,7)),
        (200_000, None, ( 17984,199999)),
        (5.0,None , (3,5))
    ],
    "fib": [
        (0, None, 0),
        (6, None, 8),
        (10, None, 55),
        (20, None, 6765),
    ],
})
        self.error_cases.update({
            "fact": [
                (-1,       None, ValueError),   # negative
                (True,     None, ValueError),   # bool
                (5.0,      None, ValueError),   # float (only int accepted)
                (None,     None, ValueError),   # None filtered → 0 operands → arity
                ('a',      None, ValueError),   # str
                (200_001,  None, ValueError),   # > limit
            ],
            "primes": [
                (-1,       None, ValueError),
                (True,     None, ValueError),
                (None,     None, ValueError),
                ('a',      None, ValueError),
                (1, None, ValueError),
                (0, None, ValueError)
            ],
            "fib": [
                (-1,       None, ValueError),
                (True,     None, ValueError),
                (5.0,      None, ValueError),
                (None,     None, ValueError),
                ('a',      None, ValueError),
            ],
        })
        
        self.bad_call_cases.extend([
            (("fact",),         ValueError),   # missing operand
            (("fact", 5, 6),    ValueError),   # too many operands
            (("primes",),       ValueError),
            (("primes", 10, 20), ValueError),
            (("fib",),          ValueError),
            (("fib", 6, 7),     ValueError),
        ])
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