import unittest
import math
import logging
from pathlib import Path
import tempfile
import json

import src.calculator as calculator
from src.calculator import Calculator, History, Calculation, CalculatorApp
from tests.data import TestCalculatorData


class TestCalculatorApp(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.data_path = Path(self.tmpdir.name) / "test_data.json"
        self.log_path = Path(self.tmpdir.name) / "test.log"

        # Remove existing handlers so __init__ re-creates them using our temp log file
        logger = logging.getLogger("calculator")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

        self.output_cases: dict[str, str] = {
            "add 4 5": "9",
            "ADD 4 5": "9",
            "sub 10 3.5": "6.5",
            "mul 3 4": "12",
            "div 7 2": "3.5",
            "pow 2 10": "1024",
            "mod 10 3": "1",
            "sqrt 16": "4",
            "abs -7": "7",
            "add 0.1 0.2": "0.3",
            "add -1 -1": "-2",
            "add 4": "add needs 2 numbers",
            "add 4 5 6": "add needs 2 numbers",
            "sqrt": "sqrt needs 1 number",
            "add 4 abc": "'abc' is not a valid number",
            "add abc 5": "'abc' is not a valid number",
            "add last 5": "No previous result yet",
            "ms": "No previous result yet",
            "history": "No calculations yet",
            "stats": "No calculations yet",
            "mr": "Memory is empty",
            "mc": "Memory cleared",
            "clear": "History cleared",
        }

        self.raised_cases: dict[str, type] = {
            "div 5 0": ZeroDivisionError,
            "mod 5 0": ZeroDivisionError,
            "sqrt -4": ValueError,
            "pow 0 -1": ZeroDivisionError,
            "pow -2 0.5": ValueError,
        }

        self.history_cases: list[tuple[list[str], int]] = [
            ([], 0),
            (["add 4 5"], 1),
            (["add 4 5", "mul 3 4"], 2),
            (["add 4 5", "clear"], 0),
            (["add 4 5", "mul 3 4", "clear", "sub 10 3"], 1),
        ]

        self.memory_cases: list[tuple[list[str], int | float | None]] = [
            ([], None),
            (["ms"], None),
            (["add 4 5"], None),
            (["add 4 5", "ms"], 9),
            (["add 4 5", "ms", "mc"], None),
            (["add 4 5", "ms", "add 10 20", "ms"], 30),
            (["div 7 2", "ms"], 3.5),
        ]

        self.last_sub_cases: list[tuple[list[str], int | float | None]] = [
            (["add 4 5", "add last 5"], 14),
            (["add 4 5", "mul last 3"], 27),
            (["add 4 5", "sub last 20"], -11),
            (["add 4 5", "add 10 last"], 19),
            (["add 4 5", "mul 2 3", "add last 100"], 106),
        ]

    def tearDown(self):
        self.tmpdir.cleanup()

    def _fresh_app(self) -> CalculatorApp:
        """Create a new app on a clean data file."""
        if self.data_path.exists():
            self.data_path.unlink()
        return CalculatorApp(data_file=self.data_path, log_file=self.log_path)

    def _run(self, cmd: str) -> str:
        """Run one command and capture its logged output as a single string."""
        with self.assertLogs(logger=self.app.logger, level="INFO") as cm:
            self.app.handle_command(cmd)
        return "\n".join(record.getMessage() for record in cm.records)

    def test_output(self):
        for cmd, expected in self.output_cases.items():
            with self.subTest(cmd=cmd):
                self.app = self._fresh_app()
                self.assertEqual(self._run(cmd), expected)

    def test_raises(self):
        for cmd, exc in self.raised_cases.items():
            with self.subTest(cmd=cmd):
                self.app = self._fresh_app()
                with self.assertRaises(exc):
                    self._run(cmd)

    def test_history_accumulates(self):
        for commands, expected_len in self.history_cases:
            with self.subTest(commands=commands):
                self.app = self._fresh_app()
                for cmd in commands:
                    self._run(cmd)
                self.assertEqual(len(self.app.history), expected_len)

    def test_memory_flow(self):
        for commands, expected in self.memory_cases:
            with self.subTest(commands=commands):
                self.app = self._fresh_app()
                for cmd in commands:
                    self._run(cmd)
                self.assertEqual(self.app.memory, expected)

    def test_last_substitution(self):
        for commands, expected in self.last_sub_cases:
            with self.subTest(commands=commands):
                self.app = self._fresh_app()
                for cmd in commands:
                    self._run(cmd)
                self.assertEqual(self.app.history.last_result(), expected)

    def test_exit_sets_running_false(self):
        for cmd in ["exit", "quit", "EXIT", "QUIT"]:
            with self.subTest(cmd=cmd):
                self.app = self._fresh_app()
                self.assertTrue(self.app.running)
                self._run(cmd)
                self.assertFalse(self.app.running)

    def test_saves_to_disk(self):
        self.app = self._fresh_app()
        self.assertFalse(self.data_path.exists())
        self._run("add 4 5")
        self.assertTrue(self.data_path.exists())
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data["history"]), 1)
        self.assertEqual(data["history"][0]["operands"], [4, 5])


if __name__ == "__main__":
    unittest.main()