# calculator.py
import json
import logging
import readline
from collections import namedtuple
from pathlib import Path
from decimal import Decimal, ROUND_FLOOR, InvalidOperation

DATA_FILE = Path("calculator_data.json")
LOG_FILE = Path("calculator.log")

# Chosen because namedtuple gives us a free __repr__ that matches the
# required format (Calculation(op='add', operands=(4, 5), result=9)),
# plus field access (c.op, c.result) and tuple unpacking
# (op, operands, result = c).
Calculation = namedtuple("Calculation", ["op", "operands", "result"])


class Calculator:
    """Performs arithmetic operations."""

    def __init__(self) -> None:
        """Set up the operation table mapping operation names to (arity, lambda)."""
        self.operations = {
            "add": (2, lambda a, b: a + b),
            "sub": (2, lambda a, b: a - b),
            "mul": (2, lambda a, b: a * b),
            "div": (2, lambda a, b: a / b),
            "pow": (2, lambda a, b: a ** b),
            "mod": (2, lambda a, b: a - (a / b).to_integral_value(rounding=ROUND_FLOOR) * b),
            "sqrt": (1, lambda a: a.sqrt()),
            "abs": (1, lambda a: abs(a)),
        }

    def calculate(self, *args: object) -> int | float:
        """Validate the request, run the operation, and return a clean result."""
        self._validate_input(*args)
        op = str(args[0])
        operands = [Decimal(str(v)) for v in args[1:] if v is not None]
        return self._validate_output(self.operations[op][1](*operands))
    
    def _validate_output(self, result: Decimal) -> int | float:
        """Convert a whole Decimal to int, otherwise return float."""
        return int(result) if result == result.to_integral_value() else float(result)

    def _validate_number(self, number: object) -> None:
        """Raise if number is not a finite int/float/Decimal (bool is rejected)."""
        if not isinstance(number, (int, float, Decimal)) or isinstance(number, bool):
            raise ValueError(f"{number!r} is not a valid number")
        if not Decimal(str(number)).is_finite():
            raise ValueError(f"{number!r} is not a finite number")

    def _validate_input(self, *args: object) -> None:
        """Validate an input request before running the operation."""
        if not args:
            raise ValueError("No operation given")

        op = args[0]
        if not isinstance(op, str) or op not in self.operations:
            raise ValueError(f"Unknown operation: {op}")

        operands = [v for v in args[1:] if v is not None]
        n, _ = self.operations[op]
        if len(operands) != n:
            raise ValueError(f"{op} takes exactly {n} argument{'s' if n != 1 else ''}")

        for v in operands:
            self._validate_number(v)

        # operation-specific rules
        if op in ("div", "mod") and operands[1] == 0:
            raise ZeroDivisionError("Error: cannot divide by zero")
        if op == "sqrt" and operands[0] < 0:
            raise ValueError("Error: cannot take square root of a negative number")
        if op == "pow" and operands[0] == 0 and operands[1] < 0:
            raise ZeroDivisionError("Error: cannot raise 0 to a negative power")
        if op == "pow" and operands[0] < 0 and Decimal(str(operands[1])) != Decimal(str(operands[1])).to_integral_value():
            raise ValueError("Error: cannot raise a negative number to a fractional power")


class History:
    """Stores past calculations in order."""

    def __init__(self) -> None:
        """Start with an empty entry list."""
        self._entries: list[Calculation] = []

    def add(self, calc: Calculation) -> None:
        """Append a calculation to the history ensuring operands are an immutable tuple."""
        entry = Calculation(calc.op, tuple(calc.operands), calc.result)
        self._entries.append(entry)

    def last_result(self) -> int | float | None:
        """Return the most recent result, or None if history is empty."""
        if not self._entries:
            return None
        return self._entries[-1].result

    def stats(self) -> dict:
        """Return count, min, max, and average of all results."""
        results = [entry.result for entry in self._entries]
        if not results:
            return {"count": 0, "min": None, "max": None, "average": None}
        return {
            "count": len(results),
            "min": min(results),
            "max": max(results),
            "average": sum(results) / len(results),
        }

    def save(self, path: Path, memory: int | float | None) -> None:
        """Save history and memory to a JSON file."""
        data = {
            "memory": memory,
            # JSON has no tuple type, so operand tuples are converted to
            # lists here. load() converts them back to tuples.
            "history": [
                {"op": c.op, "operands": list(c.operands), "result": c.result}
                for c in self._entries
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, path: Path, on_warning: object = None) -> int | float | None:
        """Load history from a JSON file and return the saved memory value."""
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            backup = path.with_name(path.name + ".bak")
            try:
                path.rename(backup)
                msg = f"Warning: {path} was not valid JSON. Renamed to {backup.name}."
            except OSError:
                msg = f"Warning: could not read {path}. Starting empty."
            if callable(on_warning):
                on_warning(msg)
            self._entries = []
            return None

        # Convert operand lists back to tuples for immutability and memory consistency.
        self._entries = [
            Calculation(item["op"], tuple(item["operands"]), item["result"])
            for item in data.get("history", [])
        ]
        return data.get("memory")

    def clear(self) -> None:
        """Remove all entries from history."""
        self._entries = []

    def __len__(self) -> int:
        """Return the number of entries."""
        return len(self._entries)

    def __str__(self) -> str:
        """Return a numbered, multi-line view of the history."""
        if not self._entries:
            return "No calculations yet"
        return "\n".join(
            f"{i}. {op} {operands} = {result}"
            for i, (op, operands, result) in enumerate(self._entries, start=1)
        )


class CalculatorApp:
    """Reads commands from the user and prints results."""

    def __init__(self) -> None:
        """Set up the calculator, history, memory, and command tables."""
        self.calculator = Calculator()
        self.history = History()
        self.memory = None
        self.running = True

        # logger setup — created per-instance, handlers added only once
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(message)s"))
            file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")

            class JsonFormatter(logging.Formatter):
                def format(self, record: logging.LogRecord) -> str:
                    return json.dumps({
                        "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
                        "level": record.levelname,
                        "name": record.name,
                        "message": record.getMessage(),
                    })

            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

        self.command_info: dict[str, tuple[int, str, str]] = {
            "add": (2, "Add two numbers","\nExample: \n> add 1 3 \n> 4"),
            "sub": (2, "Subtract two numbers ","\nExample: \n> sub 5 2 \n> 3"),
            "mul": (2, "Multiply two numbers ","\nExample: \n> mul 5 2 \n> 10"),
            "div": (2, "Divide two numbers ","\nExample: \n> div 10 2 \n> 5"),
            "pow": (2, "Raise a number to a power ","\nExample: \n> pow 2 3 \n> 8"),
            "mod": (2, "Find the remainder of a division ","\nExample: \n> mod 10 3 \n> 1"),
            "sqrt": (1, "Calculate the square root of a number ","\nExample: \n> sqrt 25 \n> 5"),
            "abs": (1, "Calculate the absolute value of a number ","\nExample: \n> abs -10 \n> 10"),
            "help": (0, "Show this help message ","\nExample: \n> help \n> Displays all available commands",),
            "exit": (0, "Exit the calculator ","\nExample: \n> exit \n> Exits the calculator"),
            "ms": (0, "Store the last result in memory ","\nExample: \n> ms \n> Result stored in memory"),
            "mr": (0, "Recall the value from memory ","\nExample: \n> mr \n> 10"),
            "mc": (0, "Clear the memory ","\nExample: \n> mc \n> Memory cleared"),
            "history": (0, "Show the history of calculations ","\nExample: \n> history \n> Displays calculation history"),
            "stats": (0, "Show statistics about the history ","\nExample: \n> stats \n> Displays calculation statistics"),
            "clear": (0, "Clear the history of calculations ","\nExample: \n> clear \n> History cleared"),
            "quit": (0, "Exit the calculator ","\nExample: \n> quit \n> Exits the calculator"),
        }
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

        self.memory = self.history.load(DATA_FILE, on_warning=self.logger.warning)
        self.logger.info(f"Loaded {len(self.history)} past calculations from {DATA_FILE}")
        self.logger.info("Python Calculator — type 'help' for commands")

    def handle_command(self, command: str) -> None:
        """Parse and execute a single command."""
        if not command:
            self._help()
            return

        tokens = tuple(command.split())
        if not self._validate_input(tokens):
            return

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

        result = self.calculator.calculate(op, *converted)
        self.logger.info("%s", result)

        self.history.add(Calculation(op, converted, result))
        try:
            self.history.save(DATA_FILE, self.memory)
        except OSError as e:
            self.logger.warning(f"Warning: could not save history: {e}")

    def _exit(self) -> None:
        """Save state and stop the loop."""
        try:
            self.history.save(DATA_FILE, self.memory)
            self.logger.info(f"\nSaved {len(self.history)} calculations to {DATA_FILE}. Goodbye!")
        except OSError as e:
            self.logger.warning(f"\nCould not save to {DATA_FILE}: {e}. Goodbye!")
        self.running = False

    def _help(self, op: str | None = None) -> None:
        """Show all commands, or details for one command."""
        if op is None:
            for key, value in self.command_info.items():
                self.logger.info("%s : %s", key, value[1])
        elif op in self.command_info:
            self._command_help(op)
        else:
            self.logger.warning(f"Unknown command '{op}'. Type 'help' to see options.")

    def _command_help(self, op: str) -> None:
        """Show description and example for one command."""
        self.logger.info("%s : %s %s", op, self.command_info[op][1], self.command_info[op][2])

    def _validate_input(self, command: tuple) -> bool:
        """Return True if the command exists, otherwise print an error and return False."""
        if command[0].lower() not in self.command_info:
            self.logger.warning(f"Unknown command '{command[0]}'. Type 'help' to see options.")
            return False
        return True

    def _convert_one(self, arg: str) -> int | float:
        """Convert one argument string to a number (or resolve 'last'). Raises ValueError."""
        if arg.lower() == "last":
            last = self.history.last_result()
            if last is None:
                raise ValueError("No previous result yet")
            return last
        value = self._detect_numeric_type(arg)
        if value is None:
            raise ValueError(f"'{arg}' is not a valid number")
        return value

    def _convert_args(self, args: tuple) -> tuple | None:
        """Convert argument strings to numbers; return None on error (after printing)."""
        try:
            return tuple(self._convert_one(arg) for arg in args)
        except ValueError as e:
            self.logger.warning("%s", e)
            return None

    def _detect_numeric_type(self, text: str) -> int | float | None:
        """Convert text to a finite int/float, or None if not a number."""
        try:
            d = Decimal(text)
        except InvalidOperation:
            return None
        if not d.is_finite():
            return None
        if d == d.to_integral_value():
            return int(d)
        return float(d)

    def _print_history(self) -> None:
        """Print every past calculation."""
        self.logger.info("%s", self.history)

    def _print_stats(self) -> None:
        """Print count, min, max, and average of results."""
        stats = self.history.stats()
        if stats["count"] == 0:
            self.logger.info("No calculations yet")
            return
        self.logger.info(f"count: {stats['count']}, min: {stats['min']}, "
                         f"max: {stats['max']}, average: {stats['average']:.2f}")

    def _clear_history(self) -> None:
        """Clear the history and persist it."""
        self.history.clear()
        try:
            self.history.save(DATA_FILE, self.memory)
        except OSError as e:
            self.logger.warning(f"Warning: could not save history: {e}")
        self.logger.info("History cleared")

    def _memory_store(self) -> None:
        """Store the last result in memory."""
        last = self.history.last_result()
        if last is None:
            self.logger.info("No previous result yet")
            return
        self.memory = last
        try:
            self.history.save(DATA_FILE, self.memory)
        except OSError as e:
            self.logger.warning(f"Warning: could not save memory: {e}")
        self.logger.info(f"Stored {last} in memory")

    def _memory_recall(self) -> None:
        """Print the stored memory value."""
        if self.memory is None:
            self.logger.info("Memory is empty")
            return
        self.logger.info("%s", self.memory)

    def _memory_clear(self) -> None:
        """Clear memory and persist it."""
        self.memory = None
        try:
            self.history.save(DATA_FILE, self.memory)
        except OSError as e:
            self.logger.warning(f"Warning: could not save memory: {e}")
        self.logger.info("Memory cleared")

    def run(self) -> None:
        """Run the interactive input loop."""
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


if __name__ == "__main__":
    CalculatorApp().run()