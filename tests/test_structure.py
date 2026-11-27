"""Structural checks: 200-line rule, no root shims, import surface."""

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

PUBLIC_NAMES = [
    "Calculator", "History", "Calculation", "CalculatorApp", "ScientificCalculator",
    "TaskRunnerApp", "JobManager", "Worker", "JobState", "Job", "Utils",
    "JobNotFoundError", "DEFAULT_DIGIT_LIMIT", "NUM_WORKERS", "JOBS_FILE",
    "DATA_FILE", "LOG_FILE", "InvalidJobError", "ResultFormatter",
]


class TestStructure(unittest.TestCase):
    def test_every_module_under_200_lines(self):
        for base in ("src", "tests"):
            for path in (REPO / base).rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue
                n = len(path.read_text(encoding="utf-8").splitlines())
                self.assertLessEqual(n, 200, f"{path} has {n} lines")

    def test_no_root_calculator_task_runner_or_tests(self):
        self.assertFalse((REPO / "calculator.py").exists())
        self.assertFalse((REPO / "task_runner.py").exists())
        self.assertEqual(list(REPO.glob("test_*.py")), [])

    def test_import_surface_exists(self):
        import src.calculator as calc
        for name in PUBLIC_NAMES:
            self.assertTrue(hasattr(calc, name), name)


if __name__ == "__main__":
    unittest.main()
