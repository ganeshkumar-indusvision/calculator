import unittest
import math
import logging
from pathlib import Path
import tempfile
import json

import calculator
from calculator import Calculator, History, Calculation, CalculatorApp

class TestCalculator(unittest.TestCase):

    def setUp(self):
        self.calc = Calculator()
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
class TestHistory(unittest.TestCase):

    def setUp(self):
        # Entry data reused by several cases.
        add_4_5      = Calculation("add", (4, 5), 9)
        mul_9_3      = Calculation("mul", (9, 3), 27)
        div_7_2      = Calculation("div", (7, 2), 3.5)
        sqrt_16      = Calculation("sqrt", (16,), 4)
        sub_0_5      = Calculation("sub", (0, 5), -5)
        sub_0_5_alt  = Calculation("sub", (0, 5), -5)
        add_10_5     = Calculation("add", (10, 5), 15)
        add_1_2      = Calculation("add", (1, 2), 3)

        self.last_result_cases: list[tuple[list[Calculation], int | float | None]] = [
            ([], None),
            ([add_4_5], 9),
            ([add_4_5, mul_9_3], 27),
            ([div_7_2], 3.5),
            ([sqrt_16], 4),
            ([sub_0_5], -5),
        ]

        self.stats_cases: list[tuple[list[Calculation], dict]] = [
            ([], {"count": 0, "min": None, "max": None, "average": None}),
            ([add_4_5],
             {"count": 1, "min": 9, "max": 9, "average": 9.0}),
            ([add_4_5, mul_9_3],
             {"count": 2, "min": 9, "max": 27, "average": 18.0}),
            ([sub_0_5_alt, add_10_5],
             {"count": 2, "min": -5, "max": 15, "average": 5.0}),
        ]

        self.len_cases: list[tuple[list[Calculation], int]] = [
            ([], 0),
            ([add_1_2], 1),
            ([add_1_2] * 5, 5),
        ]

        self.str_cases: list[tuple[list[Calculation], str]] = [
            ([], "No calculations yet"),
            ([add_4_5], "1. add (4, 5) = 9"),
            ([add_4_5, mul_9_3],
             "1. add (4, 5) = 9\n2. mul (9, 3) = 27"),
        ]

        self.save_load_cases: list[tuple[list[Calculation], int | float | None]] = (
            self.last_result_cases + [([], 0)]
        )

        self.bad_json_cases: list[str] = [
            "{not valid json",
            "",
            "[1, 2, 3",
            "not json at all",
        ]

        self.clear_cases: list[list[Calculation]] = [
            [],
            [add_1_2],
        ]

        self.missing_file_name = "nope.json"
        self.data_file_name    = "data.json"

    def _build(self, entries: list[Calculation]) -> History:
        h = History()
        for c in entries:
            h.add(c)
        return h

    def test_last_result(self):
        for entries, expected in self.last_result_cases:
            with self.subTest(entries=entries):
                self.assertEqual(self._build(entries).last_result(), expected)

    def test_stats(self):
        for entries, expected in self.stats_cases:
            with self.subTest(entries=entries):
                self.assertEqual(self._build(entries).stats(), expected)

    def test_len(self):
        for entries, expected in self.len_cases:
            with self.subTest(entries=entries):
                self.assertEqual(len(self._build(entries)), expected)

    def test_str(self):
        for entries, expected in self.str_cases:
            with self.subTest(entries=entries):
                self.assertEqual(str(self._build(entries)), expected)

    def test_clear(self):
        for entries in self.clear_cases:
            with self.subTest(entries=entries):
                h = self._build(entries)
                h.clear()
                self.assertEqual(len(h), 0)
                self.assertIsNone(h.last_result())

    def test_save_load_roundtrip(self):
        for entries, memory in self.save_load_cases:
            with self.subTest(entries=entries, memory=memory):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / self.data_file_name
                    h = self._build(entries)
                    h.save(path, memory)
                    h2 = History()
                    loaded_mem = h2.load(path)
                    self.assertEqual(loaded_mem, memory)
                    self.assertEqual(str(h2), str(h))
                    for entry in h2._entries:
                        self.assertIsInstance(entry.operands, tuple)

    def test_load_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / self.missing_file_name
            h = History()
            self.assertIsNone(h.load(path))
            self.assertEqual(len(h), 0)

    def test_load_bad_json(self):
        for bad_content in self.bad_json_cases:
            with self.subTest(bad=bad_content):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / self.data_file_name
                    path.write_text(bad_content, encoding="utf-8")
                    h = History()
                    self.assertIsNone(h.load(path))
                    self.assertEqual(len(h), 0)
                    self.assertTrue(path.with_name(path.name + ".bak").exists())
                    self.assertFalse(path.exists())


class TestCalculatorApp(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.data_path = Path(self.tmpdir.name) / "test_data.json"
        self.log_path = Path(self.tmpdir.name) / "test.log"

        self._orig_data_file = calculator.DATA_FILE
        self._orig_log_file = calculator.LOG_FILE
        calculator.DATA_FILE = self.data_path
        calculator.LOG_FILE = self.log_path

        # Remove existing handlers so __init__ re-creates them using our temp LOG_FILE
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
        calculator.DATA_FILE = self._orig_data_file
        calculator.LOG_FILE = self._orig_log_file
        self.tmpdir.cleanup()

    def _fresh_app(self) -> CalculatorApp:
        """Create a new app on a clean data file."""
        if self.data_path.exists():
            self.data_path.unlink()
        return CalculatorApp()

    def _run(self, cmd: str) -> str:
        """Run one command and capture its logged output as a single string."""
        with self.assertLogs(logger=self.app.logger, level="DEBUG") as cm:
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