"""Command-line interface."""

import argparse
import os


def default_worker_count() -> int:
    """Default number of workers: one less than CPU count, at least 1."""
    return max(1, (os.cpu_count() or 1) - 1)


def positive_int(value: str) -> int:
    """argparse type for integers >= 1."""
    try:
        n = int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"invalid int value: {value!r}") from e
    if n < 1:
        raise argparse.ArgumentTypeError(f"value must be >= 1, got {n}")
    return n


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(prog="main.py")
    parser.add_argument(
        "--worker",
        nargs="?",
        const=default_worker_count(),
        type=positive_int,
        default=None,
        metavar="N",
        help="run as background-task runner with N workers (default: CPUs-1)",
    )
    return parser


def main(argv=None) -> int:
    """Dispatch: no flag -> CalculatorApp; --worker [N] -> TaskRunnerApp."""
    args = build_parser().parse_args(argv)
    if args.worker is None:
        from src.calculator.apps.calculator_app import CalculatorApp
        CalculatorApp().run()
    else:
        from src.calculator.apps.runner_app import TaskRunnerApp
        TaskRunnerApp(num_workers=args.worker).run()
    return 0
