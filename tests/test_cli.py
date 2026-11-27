import unittest

from src.cli import build_parser, default_worker_count


class TestCli(unittest.TestCase):
    def test_no_flag(self):
        args = build_parser().parse_args([])
        self.assertIsNone(args.worker)

    def test_worker_default(self):
        args = build_parser().parse_args(["--worker"])
        self.assertEqual(args.worker, default_worker_count())

    def test_worker_two(self):
        args = build_parser().parse_args(["--worker", "2"])
        self.assertEqual(args.worker, 2)

    def test_worker_zero_rejected(self):
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["--worker", "0"])

    def test_default_worker_count(self):
        self.assertGreaterEqual(default_worker_count(), 1)


class TestMain(unittest.TestCase):
    def test_main_no_flag_runs_calculator_app(self):
        from unittest.mock import patch
        with patch("src.calculator.apps.calculator_app.CalculatorApp") as app:
            from src.cli import main
            main([])
            app.assert_called_once_with()
            app.return_value.run.assert_called_once_with()

    def test_main_worker_runs_task_runner_app(self):
        from unittest.mock import patch
        with patch("src.calculator.apps.runner_app.TaskRunnerApp") as app:
            from src.cli import main
            main(["--worker", "2"])
            app.assert_called_once_with(num_workers=2)
            app.return_value.run.assert_called_once_with()
