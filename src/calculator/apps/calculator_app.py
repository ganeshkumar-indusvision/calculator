"""Interactive calculator application."""

import logging
import readline

from src.calculator.apps.calculatorhelper import CalculatorHelper
from src.calculator.apps.calculatorhelper.commands import CALCULATOR_COMMANDS
from src.calculator.apps.parsing import OperandParser
from src.calculator.core.history import History
from src.calculator.core.models import Calculation
from src.calculator.core.calculator import Calculator
from src.calculator.config import DATA_FILE, LOG_FILE
from src.calculator.utils.logging_setup import JsonFormatter, configure_app_logger

class CalculatorApp(OperandParser, CalculatorHelper):
    """Reads commands from the user and prints results."""

    def __init__(self, data_file=None, log_file=None) -> None:
        """Set up the calculator, history, memory, and command tables."""
        # added this becuase once i initalise the CalculatorApp class it fill be initiating calcualtor.
        self.calculator = self._make_calculator()
        self.data_file = data_file if data_file is not None else DATA_FILE
        self.log_file = log_file if log_file is not None else LOG_FILE
        self.history = History()
        self.memory = None
        self.running = True

        # 1. Create a UNIQUE logger just for this object

        self.command_info: dict[str, tuple[int, str, str]] = dict(CALCULATOR_COMMANDS)
        self.app_handlers = {
            "help": self._help,
            "history": self._print_history,
            "stats": self._print_stats,
            "clear": self._clear_history,
            "ms": self._memory_store,
            "mr": self._memory_recall,
            "mc": self._memory_clear,
            "exit": self._exit,
            "quit": self._exit,
        }
        self._calculator_logger_init()
        self._load_history()
        

    def _display_result(self,op, operands, result):
        self.logger.debug(f"{op} {operands} {result}")
        self.logger.info("%s", result)

    def _record_result(self, op, operands, result):
        self.history.add(Calculation(op, operands, result))
        try:
            self.history.save(self.data_file, self.memory)
        except OSError as e:
            self.logger.warning(f"Warning: could not save history: {e}")
    def _make_calculator(self) -> Calculator:
        """Factory for the calculator instance. Override to use a subclass."""
        return Calculator()

    def _calculator_logger_init(self) -> None:
        self.logger = configure_app_logger(name=__name__, log_file=self.log_file, instance=self)

    def _load_history(self) -> None:
        self.memory = self.history.load(self.data_file, on_warning=self.logger.warning)
        self.logger.info(f"Loaded {len(self.history)} past calculations from {self.data_file}")

    def _exit(self) -> None:
        """Save state and stop the loop."""
        try:
            self.history.save(self.data_file, self.memory)
            self.logger.info(f"\nSaved {len(self.history)} calculations to {self.data_file}. Goodbye!")
        except OSError as e:
            self.logger.warning(f"\nCould not save to {self.data_file}: {e}. Goodbye!")
        self.running = False

    def handle_command(self, command: str) -> None:
        """Parse and execute a single command."""
        if not command:
            self._help()
            return

        tokens = tuple(command.split())
        if not self._validate_input(tokens):
            return

        self._process_command(tokens)


    def _process_command(self, tokens: tuple) -> None:
        """Process a validated command."""
        op = tokens[0].lower()
        args = tokens[1:]

        # help accepts 0 or 1 argument (help / help <command>). Since
        # command_info says 0, handle it before the generic arg-count check.
        if op == "help":
            if len(args) > 1:
                self.logger.warning("help takes 0 or 1 arguments")
                return
            self._help(args[0].lower() if args else None)
            return

        expected = self.command_info[op][0]

        # Check argument count against command_info
        if len(args) != expected:
            if expected == 0:
                self.logger.warning(f"{op} takes no arguments")
            else:
                suffix = "number" if expected == 1 else "numbers"
                self.logger.warning(f"{op} needs {expected} {suffix}")
            return

        # Non-arithmetic commands: help, history, stats, clear,
        # ms, mr, mc, exit, quit
        if op in self.app_handlers:
            self.app_handlers[op]()
            return

        # Arithmetic commands
        converted = self._convert_args(args)
        if converted is None:
            return

        # Execute calculation.
        result = self.calculator.calculate(op, *converted)

        # I changed result to differetn fromate for reporting to user so i want to isolate someparts.
        self._display_result(op, converted, result)
        self._record_result(op, converted, result)

    def run(self) -> None:
        """Run the interactive input loop."""
        self.logger.info("Python Calculator — type 'help' for commands")
        try:
            while self.running:
                try:
                    command = input("> ").strip()
                    self.handle_command(command)
                except ValueError as e:
                    self.logger.warning("%s", e)
                    continue
                except ZeroDivisionError as e:
                    self.logger.warning("%s", e)
                    continue
        except (KeyboardInterrupt, EOFError):
            self._exit()

    def __del__(self):
        """Clean up logger handlers to prevent file descriptor leaks."""
        if hasattr(self, 'logger'):
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
                handler.close()
