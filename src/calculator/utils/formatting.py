"""Logging and output formatting helpers."""

import json
import logging

from src.calculator.core.scientific import ScientificCalculator
from src.calculator.config import DEFAULT_DIGIT_LIMIT

class ResultFormatter:

    def __init__(self,calculator: ScientificCalculator):
        self.calculator = calculator
        self.memory = None
    def check_digit(self, value: int ) -> tuple[int, bool]:
        if isinstance(value, int) and not isinstance(value, bool):
            length = len(str(value))
            if length > DEFAULT_DIGIT_LIMIT:
               return length , True
        return value, False

    def add_digit_words(self, msg):
        return msg + " digits" 

    def formate_msg(self, op: str, result) -> str:
        if op not in self.calculator.scientific_operations:
            return str(result)

        if op == "primes":
            count, largest = result
            value, is_digit = self.check_digit(count)
            msg = f"{value} primes"
            if is_digit:
                msg = self.add_digit_words(msg)
            value, is_digit = self.check_digit(largest)
            msg = msg + f", largest {value}"
            if is_digit:
                msg = self.add_digit_words(msg)
            return msg

        value, is_digit = self.check_digit(result)
        msg = f"{value}"
        if is_digit:
            msg = self.add_digit_words(msg)
        return msg


Utils = ResultFormatter


from src.calculator.utils.logging_setup import JsonFormatter  # re-exported for compatibility
