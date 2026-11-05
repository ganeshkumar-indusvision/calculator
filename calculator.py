# calculator.py
import json
import readline
from collections import namedtuple
from pathlib import Path
import math
from decimal import Decimal, ROUND_FLOOR  , InvalidOperation

DATA_FILE = Path("calculator_data.json")

Calculation = namedtuple("Calculation", ["op", "operands", "result"])


class Calculator:
    """Performs arithmetic operations."""

    def __init__(self) -> None:
        """Set up the operation table."""
        self.operations = {
            "add": lambda a, b: a + b,
            "sub": lambda a, b: a - b,
            "mul": lambda a, b: a * b,
            "div": lambda a, b: a / b,
            "pow": lambda a, b: a ** b,
            "mod": lambda a, b: a - (a / b).to_integral_value(rounding=ROUND_FLOOR) * b,
            "sqrt": lambda a: a.sqrt(),
            "abs": lambda a: abs(a),
        }

    def calculate(self, op: str, a: int | float | Decimal,
                  b: int | float | Decimal = None) -> int | float:
        """Validate the request, run the operation, and return a clean result."""
        self._validate_input(op, a, b)
        a = Decimal(str(a))
        if b is not None:
            b = Decimal(str(b))

        if b is None:
            result = self.operations[op](a)
        else:
            result = self.operations[op](a, b)

        return self._validate_output(result)

    def _validate_output(self, result: Decimal | int | float) -> int | float:
        """Convert a whole Decimal to int, otherwise return float."""
        if result == result.to_integral_value():
            return int(result)
        return float(result)

    def _validate_input(self, op: str, a: int | float | Decimal,
                  b: int | float | Decimal | None) -> None:
        """Validate an input request before running the operation."""
        # print(op,a,b)
        # print(type(op),type(a),type(b))
        if op not in self.operations:
            raise ValueError(f"Unknown operation: {op}")

        # bool is subclass of int so dealing with it seperately as well 
        # a should be int,decimal and float only and it should not be NaN,Inf, None, True, 
        # Allow only Data type int, float,decimal 
        if not isinstance(a, (int, float, Decimal)) or isinstance(a, bool):
            raise ValueError(f"{a!r} is not a valid number")

        # bool is subclass of int so dealing with it seperately as well 
        # a should be int,decimal, float and None only and it should not be NaN,Inf, None, True, 
        # Allow only Data type int, float,decimal 
        if b is not None and (isinstance(b, bool)
                              or not isinstance(b, (int, float, Decimal))):
            raise ValueError(f"{b!r} is not a valid number")

        if not Decimal(str(a)).is_finite():
            raise ValueError(f"{a!r} is not a finite number")
        if b is not None and not Decimal(str(b)).is_finite():
            raise ValueError(f"{b!r} is not a finite number")

        if op in ("sqrt", "abs"):
            if b is not None:
                raise ValueError(f"{op} takes exactly 1 argument")
            if op == "sqrt" and a < 0:
                raise ValueError("Error: cannot take square root of a negative number")
        else:
            if b is None:
                raise ValueError(f"{op} needs 2 numbers")
            if op in ("div", "mod") and b == 0:
                raise ZeroDivisionError("Error: cannot divide by zero")
            if op == "pow" and a == 0 and b < 0:
                raise ZeroDivisionError("Error: cannot raise 0 to a negative power")
            # Decimal ** Decimal raises InvalidOperation for (-x) ** fraction.
            if op == "pow" and a < 0 and Decimal(str(b)) != Decimal(str(b)).to_integral_value():
                raise ValueError("Error: cannot raise a negative number to a fractional power")


class History:
    """Stores past calculations in order."""

    def __init__(self) -> None:
        """Start with an empty entry list."""
        self._entries: list[Calculation] = []

    def add(self, calc: Calculation) -> None:
        """Append a calculation to the history."""
        self._entries.append(calc)

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
            "history": [
                {"op": c.op, "operands": list(c.operands), "result": c.result}
                for c in self._entries
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, path: Path) -> int | float | None:
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
                print(f"Warning: {path} was not valid JSON. Renamed to {backup.name}.")
            except OSError:
                print(f"Warning: could not read {path}. Starting empty.")
            self._entries = []
            return None
        self._entries = [
            Calculation(item["op"], tuple(item["operands"]), item["result"])
            for item in data.get("history", [])
        ]
        return data.get("memory")

    def clear(self) -> None:
        """Remove all entries from history."""
        self._entries = []

    def __len__(self) -> int:
        return len(self._entries)

    def __str__(self) -> str:
        if not self._entries:
            return "No calculations yet"
        # TR-14: tuple unpacking inside the comprehension
        return "\n".join(
            f"{i}. {op} {operands} = {result}"
            for i, (op, operands, result) in enumerate(self._entries, start=1)
        )


class CalculatorApp:
    """Reads commands from the user and prints results."""

    def __init__(self) -> None:
        self.calculator = Calculator()
        self.history = History()
        self.memory = None
        self.running = True
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
    def run(self) -> None:
        memory = self.history.load(DATA_FILE)
        if memory is not None:
            self.memory = memory
        print(f"Loaded {len(self.history)} past calculations from {DATA_FILE}")
        print("Python Calculator — type 'help' for commands")
        try:
            while self.running:
                try:
                    command = input("> ").strip()
                    self.handle_command(command)
                except ValueError as e:
                    print(e)
                    continue
                except ZeroDivisionError as e:
                    print(e)
                    continue
        except (KeyboardInterrupt, EOFError):
            self._exit()

    def handle_command(self, command: str) -> None:
        if not command:
            self._help()
            return

        tokens = tuple(command.split())
        if not self._validate_input(tokens, len(tokens)):
            return

        op = tokens[0].lower()
        args = tokens[1:]

        # help is special-cased: it takes 0 or 1 argument (help / help <command>),
        # but command_info says 0, so the generic arg-count check below would
        # reject "help add". Handle it before that check.
        if op == "help":
            if len(args) > 1:
                print("help takes 0 or 1 arguments")
                return
            self._help(args[0].lower() if args else None)
            return

        expected = self.command_info[op][0]

        # Check argument count against command_info
        if len(args) != expected:
            if expected == 0:
                print(f"{op} takes no arguments")
            else:
                suffix = "number" if expected == 1 else "numbers"
                print(f"{op} needs {expected} {suffix}")
            return
        ## Other than calculate operation this will handle i
        if op in self.app_handlers:
            self.app_handlers[op]()
            return

        # Arithmetic commands
        converted = self._convert_args(args)
        if converted is None:
            return

        result = self.calculator.calculate(op, *converted)
        print(result)

        self.history.add(Calculation(op, converted, result))
        try:
            self.history.save(DATA_FILE, self.memory)
        except OSError as e:
            print(f"Warning: could not save history: {e}")

    def _exit(self) -> None:
        try:
            self.history.save(DATA_FILE, self.memory)
            print(f"\nSaved {len(self.history)} calculations to {DATA_FILE}. Goodbye!")
        except OSError as e:
            print(f"\nCould not save to {DATA_FILE}: {e}. Goodbye!")
        self.running = False

    def _help(self, op: str | None = None) -> None:
        """Show all commands, or details for one command."""
        if op is None:
            {print(key,":", value[1]) for key,value in self.command_info.items()}
        elif op in self.command_info:
            self._command_help(op)
        else:
            print(f"Unknown command '{op}'. Type 'help' to see options.")

    def _command_help(self, op: str) -> None:
        print(op, ":", self.command_info[op][1], self.command_info[op][2])

    def _validate_input(self, command: tuple, input_lenght: int) -> bool:
        # check with valid values are there from opertor selection to value checker.
        if command[0].lower() not in self.command_info:
            print("Unknown command '", command[0], "'. Type 'help' to see options.")
            return False
        return True

    def _convert_one(self, arg: str) -> int | float:
        """Convert one argument string to a number (or resolve 'last'). Raises ValueError."""
        if arg.lower() == "last":
            # 'last' means: use the previous result from history
            last = self.history.last_result()
            if last is None:
                raise ValueError("No previous result yet")
            return last
        # normal number: try int, then float
        value = self._detect_numeric_type(arg)
        if value is None:
            # not a number and not 'last' -> error
            raise ValueError(f"'{arg}' is not a valid number")
        return value

    def _convert_args(self, args: tuple) -> tuple | None:
        """Convert argument strings to numbers; return None on error (after printing)."""
        # Input:  args = ('4', '5')  or  ('last', '5')  or  ('4', 'abc')
        # Output: (4, 5)  or  (previous_result, 5)  or  None (on error)
        try:
            return tuple(self._convert_one(arg) for arg in args)  # e.g. (4, 5) -- tuple of numbers
        except ValueError as e:
            print(e)
            return None


    def _detect_numeric_type(self, text: str) -> int | float | None:
        try:
            d = Decimal(text)
        except InvalidOperation:
            return None
        if not d.is_finite():        # rejects NaN, Inf, -Inf
            return None
        if d == d.to_integral_value():
            return int(d)
        return float(d)

    def _print_history(self) -> None:
        print(self.history)

    def _print_stats(self) -> None:
        stats = self.history.stats()
        if stats["count"] == 0:
            print("No calculations yet")
            return
        print(f"count: {stats['count']}, min: {stats['min']}, "
              f"max: {stats['max']}, average: {stats['average']:.2f}")

    def _clear_history(self) -> None:
        self.history.clear()
        try:
            self.history.save(DATA_FILE, self.memory)
        except OSError as e:
            print(f"Warning: could not save history: {e}")
        print("History cleared")

    def _memory_store(self) -> None:
        last = self.history.last_result()
        if last is None:
            print("No previous result yet")
            return
        self.memory = last
        try:
            self.history.save(DATA_FILE, self.memory)
        except OSError as e:
            print(f"Warning: could not save memory: {e}")
        print(f"Stored {last} in memory")

    def _memory_recall(self) -> None:
        if self.memory is None:
            print("Memory is empty")
            return
        print(self.memory)

    def _memory_clear(self) -> None:
        self.memory = None
        try:
            self.history.save(DATA_FILE, self.memory)
        except OSError as e:
            print(f"Warning: could not save memory: {e}")
        print("Memory cleared")


if __name__ == "__main__":
    CalculatorApp().run()