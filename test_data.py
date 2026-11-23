import math



class TestCalculatorData():
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
        
        
        