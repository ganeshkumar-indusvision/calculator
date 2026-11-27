from tests.data.calculator_cases import TestCalculatorData


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
        (100,None,(25, 97)),
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
