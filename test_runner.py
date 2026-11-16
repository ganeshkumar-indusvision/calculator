import unittest
import math
import logging
from pathlib import Path
import tempfile
import json

import calculator
from task_runner import ScientificCalculator

from test_calculator import TestCalculator as BaseTestCalculator

from test_data import TestCalculatorData
class TestCalculator(unittest.TestCase):

    def setUp(self):
        self.calc = ScientificCalculator()
        self.data = TestCalculatorData()
        self.input_output = self.data.input_output
        self.value_error_cases = self.data.value_error_cases
        self.single_input_error_cases= self.data.single_input_error_cases
        self.error_cases= self.data.error_cases
        self.bad_call_cases= self.data.bad_call_cases

    def test_operations(self):
        for op, cases in self.input_output.items():
            for a, b, expected in cases:
                with self.subTest(op=op, a=a, b=b):
                    args = (a,) if b is None else (a, b)
                    result = self.calc.calculate(op, *args)
                    self.assertEqual(result, expected)
                    if op != "sqrt":
                        self.assertIsInstance(
                            result, int if isinstance(expected, int) else float)

    def test_errors(self):
        for op, cases in self.error_cases.items():
            for a, b, exc in cases:
                with self.subTest(op=op, a=a, b=b):
                    args = (a,) if b is None else (a, b)
                    with self.assertRaises(exc):
                        self.calc.calculate(op, *args)

    def test_bad_calls(self):
        for args, exc in self.bad_call_cases:
            with self.subTest(args=args):
                with self.assertRaises(exc):
                    self.calc.calculate(*args)

if __name__ == "__main__":
    unittest.main()