import logging
import unittest

from src.calculator import ScientificCalculator, Utils, DEFAULT_DIGIT_LIMIT
from tests.data import UtilsData


class TestUtils(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = ScientificCalculator()
        self.utils = Utils(self.calculator)
        self.utils_data = UtilsData(DEFAULT_DIGIT_LIMIT)
        self.logger = logging.getLogger("test")
        self.check_digit_cases = self.utils_data.check_digit_cases
        self.check_digit_passthrough_cases = self.utils_data.check_digit_passthrough_cases
        self.add_digit_words_cases = self.utils_data.add_digit_words_cases
        self.formate_msg_cases = self.utils_data.formate_msg_cases

    def test_check_digit(self) -> None:
        for value, expected_val, expected_flag in self.check_digit_cases:
            with self.subTest(expected=(expected_val, expected_flag)):
                self.assertEqual(
                    self.utils.check_digit(value),
                    (expected_val, expected_flag),
                )

    def test_check_digit_passthrough(self) -> None:
        for value, expected_val, expected_flag in self.check_digit_passthrough_cases:
            with self.subTest(value=value):
                self.assertEqual(
                    self.utils.check_digit(value),
                    (expected_val, expected_flag),
                )

    def test_add_digit_words(self) -> None:
        for msg, expected in self.add_digit_words_cases:
            with self.subTest(msg=msg):
                self.assertEqual(self.utils.add_digit_words(msg), expected)

    def test_formate_msg(self) -> None:
        for op, result, expected in self.formate_msg_cases:
            with self.subTest(op=op, expected=expected):
                self.assertEqual(self.utils.formate_msg(op, result), expected)
