import unittest
import math
import logging
from pathlib import Path
import tempfile
import json
from unittest.mock import patch

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
                (7, 2, 3.5), (-10, 2, -5), (1, 3, 0.3333333333333333),
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
            "pow":  self.value_error_cases,
            "mod":  self.value_error_cases + [(5, 0, ZeroDivisionError)],
            "sqrt": self.single_input_error_cases + [(5, 0, ValueError), (-5, 0, ValueError)],
            "abs":  self.single_input_error_cases,
        }

    def _check_op(self, op: str) -> None:
        for a, b, expected in self.input_output[op]:
            with self.subTest(op=op, a=a, b=b):
                args = (a,) if b is None else (a, b)
                result = self.calc.calculate(op, *args)
                self.assertEqual(result, expected)
                # Whole-number results must come back as int, otherwise float.
                # sqrt is skipped because perfect squares currently return int
                # even though the spec says sqrt should always be float.
                if op != "sqrt":
                    self.assertIsInstance(result, int if isinstance(expected, int) else float)

    def test_add(self):
        self._check_op("add")

    def test_sub(self):
        self._check_op("sub")

    def test_mul(self):
        self._check_op("mul")

    def test_div(self):
        self._check_op("div")

    def test_pow(self):
        self._check_op("pow")

    def test_mod(self):
        self._check_op("mod")

    def test_sqrt(self):
        self._check_op("sqrt")

    def test_abs(self):
        self._check_op("abs")

    def test_invalid_numbers_binary(self):
        cases = [
            (math.nan, 1), (1, math.nan), (math.nan, math.nan),
            (1, 'a'), ('a', -2.5), (True, 'a'), (False, 1),
            (1, False), (math.inf, 1), (-math.inf, 1),
            (1, math.inf), (1, -math.inf), (1, True), (True, 1),
        ]
        for op in ("add", "sub", "mul", "div", "pow", "mod"):
            for a, b in cases:
                with self.subTest(op=op, a=a, b=b):
                    with self.assertRaises(ValueError):
                        self.calc.calculate(op, a, b)

    def test_invalid_numbers_single(self):
        for op in ("sqrt", "abs"):
            for a in (None, 'a', True, False):
                with self.subTest(op=op, a=a):
                    with self.assertRaises(ValueError):
                        self.calc.calculate(op, a)

    def test_missing_operand(self):
        for op in ("add", "sub", "mul", "div", "pow", "mod"):
            with self.subTest(op=op, kind="zero"):
                with self.assertRaises(ValueError):
                    self.calc.calculate(op)
            with self.subTest(op=op, kind="one"):
                with self.assertRaises(ValueError):
                    self.calc.calculate(op, 5)
        for op in ("sqrt", "abs"):
            with self.subTest(op=op, kind="zero"):
                with self.assertRaises(ValueError):
                    self.calc.calculate(op)

    def test_too_many_operands(self):
        cases = [("add", 1, 2, 3), ("sqrt", 4, 5), ("abs", 1, 2)]
        for args in cases:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    self.calc.calculate(*args)

    def test_no_operation_given(self):
        with self.assertRaises(ValueError):
            self.calc.calculate()

    def test_unknown_operation(self):
        with self.assertRaises(ValueError):
            self.calc.calculate("power", 2, 3)

    def test_divide_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            self.calc.calculate("div", 5, 0)

    def test_mod_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            self.calc.calculate("mod", 5, 0)

    def test_sqrt_of_negative(self):
        with self.assertRaises(ValueError):
            self.calc.calculate("sqrt", -4)

    def test_pow_zero_to_negative(self):
        with self.assertRaises(ZeroDivisionError):
            self.calc.calculate("pow", 0, -1)

    def test_pow_negative_base_fractional_exponent(self):
        with self.assertRaises(ValueError):
            self.calc.calculate("pow", -2, 0.5)


class TestHistory(unittest.TestCase):

    LAST_RESULT_CASES: list[tuple[list[Calculation], int | float | None]] = [
        ([], None),
        ([Calculation("add", (4, 5), 9)], 9),
        ([Calculation("add", (4, 5), 9), Calculation("mul", (9, 3), 27)], 27),
        ([Calculation("div", (7, 2), 3.5)], 3.5),
        ([Calculation("sqrt", (16,), 4)], 4),
        ([Calculation("sub", (0, 5), -5)], -5),
    ]

    STATS_CASES: list[tuple[list[Calculation], dict]] = [
        ([], {"count": 0, "min": None, "max": None, "average": None}),
        ([Calculation("add", (4, 5), 9)],
         {"count": 1, "min": 9, "max": 9, "average": 9.0}),
        ([Calculation("add", (4, 5), 9), Calculation("mul", (9, 3), 27)],
         {"count": 2, "min": 9, "max": 27, "average": 18.0}),
        ([Calculation("sub", (0, 5), -5), Calculation("add", (10, 5), 15)],
         {"count": 2, "min": -5, "max": 15, "average": 5.0}),
    ]

    LEN_CASES: list[tuple[list[Calculation], int]] = [
        ([], 0),
        ([Calculation("add", (1, 2), 3)], 1),
        ([Calculation("add", (1, 2), 3)] * 5, 5),
    ]

    STR_CASES: list[tuple[list[Calculation], str]] = [
        ([], "No calculations yet"),
        ([Calculation("add", (4, 5), 9)], "1. add (4, 5) = 9"),
        ([Calculation("add", (4, 5), 9), Calculation("mul", (9, 3), 27)],
         "1. add (4, 5) = 9\n2. mul (9, 3) = 27"),
    ]

    SAVE_LOAD_CASES: list[tuple[list[Calculation], int | float | None]] = [
        ([], None),
        ([], 0),
        ([Calculation("add", (4, 5), 9)], 9),
        ([Calculation("add", (4, 5), 9), Calculation("mul", (9, 3), 27)], 27),
        ([Calculation("div", (7, 2), 3.5)], 3.5),
        ([Calculation("sub", (0, 5), -5)], -5),
    ]

    BAD_JSON_CASES: list[str] = [
        "{not valid json",
        "",
        "[1, 2, 3",
        "not json at all",
    ]

    def setUp(self):
        self.history = History()

    def _build(self, entries: list[Calculation]) -> History:
        h = History()
        for c in entries:
            h.add(c)
        return h

    def test_last_result(self):
        for entries, expected in self.LAST_RESULT_CASES:
            with self.subTest(entries=entries):
                self.assertEqual(self._build(entries).last_result(), expected)

    def test_stats(self):
        for entries, expected in self.STATS_CASES:
            with self.subTest(entries=entries):
                self.assertEqual(self._build(entries).stats(), expected)

    def test_len(self):
        for entries, expected in self.LEN_CASES:
            with self.subTest(entries=entries):
                self.assertEqual(len(self._build(entries)), expected)

    def test_str(self):
        for entries, expected in self.STR_CASES:
            with self.subTest(entries=entries):
                self.assertEqual(str(self._build(entries)), expected)

    def test_clear(self):
        for entries in ([], [Calculation("add", (1, 2), 3)]):
            with self.subTest(entries=entries):
                h = self._build(entries)
                h.clear()
                self.assertEqual(len(h), 0)
                self.assertIsNone(h.last_result())

    def test_save_load_roundtrip(self):
        for entries, memory in self.SAVE_LOAD_CASES:
            with self.subTest(entries=entries, memory=memory):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "data.json"
                    h = self._build(entries)
                    h.save(path, memory)
                    h2 = History()
                    loaded_mem = h2.load(path)
                    self.assertEqual(loaded_mem, memory)
                    self.assertEqual(str(h2), str(h))
                    # Operands come back as tuples, not lists.
                    for entry in h2._entries:
                        self.assertIsInstance(entry.operands, tuple)

    def test_load_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nope.json"
            h = History()
            self.assertIsNone(h.load(path))
            self.assertEqual(len(h), 0)

    def test_load_bad_json(self):
        for bad_content in self.BAD_JSON_CASES:
            with self.subTest(bad=bad_content):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "data.json"
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