# Feature Request: Command-Line Calculator (Python Intern Project)
Nov 2, 2026 · @Bhuvan

## Overview

Build a command-line calculator in Python that runs in an interactive loop, evaluates arithmetic, and keeps a history of results. Target effort is about 1–2 weeks, using only the Python standard library. No database and no third-party packages: all data is saved to a plain file on disk.

The project is a practice exercise. The aim is not a feature-rich calculator, but clean, readable code that uses core Python building blocks correctly.

**By the end, you should be able to show that you can:**

- Design and use **classes** (attributes, methods, `__init__`, `__str__`/`__repr__`)
- Choose the right built-in type: **list**, **dictionary**, **tuple**, plus `int`, `float`, `str`, `bool`
- Write a loop that reads user input, handles errors, and exits cleanly
- Split code into small, single-purpose functions and methods
- Write basic tests for your own code

## Scope

| In scope | Out of scope |
| --- | --- |
| Interactive text menu or command prompt in the terminal | Graphical interface (Tkinter, web, etc.) |
| Two-number operations: add, subtract, multiply, divide, power, modulo | Parsing full expressions like `2 + 3 * (4 - 1)` (stretch goal only) |
| One-number operations: square root, absolute value | Third-party packages; standard library only (no `pip install`) |
| Calculation history and memory, saved to a local JSON file | Any database (SQLite, MySQL, etc.); data is saved only to a file |
| Input validation and friendly error messages | Use of `eval()` or `exec()` (not allowed) |

**Rule:** do not use `eval()` anywhere. The point is to map operations yourself using classes and dictionaries.

## Functional requirements

The calculator must support the commands below. Commands are case-insensitive.

| ID | Command | Example input | Expected behaviour |
| --- | --- | --- | --- |
| FR-1 | `add` | `add 4 5` | Prints `9` |
| FR-2 | `sub` | `sub 10 3.5` | Prints `6.5` |
| FR-3 | `mul` | `mul 3 4` | Prints `12` |
| FR-4 | `div` | `div 7 2` | Prints `3.5`; dividing by 0 shows an error, not a crash |
| FR-5 | `pow` | `pow 2 10` | Prints `1024` |
| FR-6 | `mod` | `mod 10 3` | Prints `1` |
| FR-7 | `sqrt` | `sqrt 16` | Prints `4.0`; negative input shows an error |
| FR-8 | `abs` | `abs -7` | Prints `7` |
| FR-9 | `history` | `history` | Lists every past calculation, numbered, oldest first |
| FR-10 | `last` | `add last 5` | The word `last` can replace any number and uses the previous result |
| FR-11 | `ms` / `mr` / `mc` | `ms`, `mr`, `mc` | Memory store (saves last result), memory recall, memory clear |
| FR-12 | `clear` | `clear` | Empties the history |
| FR-13 | `stats` | `stats` | Shows count, min, max and average of all results so far |
| FR-14 | `help` | `help` | Lists every command with a one-line description |
| FR-15 | `quit` / `exit` | `quit` | Prints a goodbye message and the number of calculations done, then exits |

Additional rules:

- Whole-number results print without a decimal (`9`, not `9.0`), except for `sqrt`.
- Unknown commands print `Unknown command 'xyz'. Type 'help' to see options.`
- Wrong number of arguments prints which arguments the command expects, e.g. `add needs 2 numbers`.

## Saving data to a file

History and memory must survive a restart. Save them to `calculator_data.json` in the program's folder using Python's built-in `json` module. No database of any kind.

| ID | Requirement |
| --- | --- |
| FR-16 | On start, load `calculator_data.json` if it exists. If it does not exist, start empty with no error. |
| FR-17 | Save after every calculation and on `quit`, so nothing is lost if the terminal is closed. |
| FR-18 | Memory changes from `ms` and `mc` are saved too. |
| FR-19 | `clear` also clears the history stored in the file. |
| FR-20 | If the file is not valid JSON, print a warning, rename it to `calculator_data.json.bak`, and start empty. |

Example file contents:

```json
{
  "memory": 27,
  "history": [
    {"op": "add", "operands": [4, 5], "result": 9},
    {"op": "mul", "operands": [9, 3], "result": 27}
  ]
}
```

File-handling rules:

- **TR-21:** Only these standard library modules are allowed: `json`, `pathlib`, `math`, `collections`, `unittest`, `tempfile`. Ask before using anything else.
- **TR-22:** Open files with `with open(path, "r", encoding="utf-8")` so they always close, even on errors.
- **TR-23:** JSON has no tuple type. Convert operand tuples to lists when saving and back to tuples when loading. Explain this in a comment.
- **TR-24:** Saving and loading live in `History` (or a small `Storage` class). `CalculatorApp` decides when to save; it does not touch the file itself.
- **TR-25:** Tests use `tempfile` for a throwaway file, so running tests never overwrites real data.

## Technical requirements

Each requirement below exists to exercise a specific Python skill. Reviewers will check these directly.

### Classes

- **TR-1:** At least three classes: `Calculator` (does the maths), `History` (stores past calculations) and `CalculatorApp` (runs the input loop and prints output).
- **TR-2:** Every class has an `__init__` that sets up its own attributes. No global variables, except constants in UPPER\_CASE.
- **TR-3:** `History` implements `__len__` so `len(history)` works, and `__str__` so `print(history)` shows a readable list.
- **TR-4:** A `Calculation` record has a `__repr__` that shows its contents, e.g. `Calculation(op='add', operands=(4, 5), result=9)`.
- **TR-5:** Input reading and printing live only in `CalculatorApp`. `Calculator` and `History` never call `input()` or `print()`, so they can be tested on their own.

### Dictionaries

- **TR-6:** Map command names to methods with a dictionary, e.g. `{"add": self.add, "sub": self.subtract}`. Do not use a long `if/elif` chain to pick the operation.
- **TR-7:** Store each command's expected argument count and help text in a dictionary, e.g. `{"add": (2, "Add two numbers")}`. The `help` command and argument checks both read from it.
- **TR-8:** `stats` returns its result as a dictionary: `{"count": ..., "min": ..., "max": ..., "average": ...}`.

### Lists

- **TR-9:** `History` keeps calculations in a list, in the order they were made.
- **TR-10:** `clear` empties that list; `history` loops over it with `enumerate()` to number entries from 1.
- **TR-11:** Use at least one list comprehension, e.g. to collect all results for `stats`.

### Tuples

- **TR-12:** Store a calculation's operands as a tuple, e.g. `(4, 5)`, because they should not change after the calculation.
- **TR-13:** Each history entry is a tuple `(operation, operands, result)` or a `namedtuple` called `Calculation`. Explain your choice in a code comment.
- **TR-14:** Use tuple unpacking at least once, e.g. `op, operands, result = entry`.

### Other basic types

- **TR-15:** Convert input strings with `float()`, and return `int` when the result is a whole number.
- **TR-16:** Use a `bool` attribute or flag to control the main loop (e.g. `self.running = True`).
- **TR-17:** Memory is `None` when empty; check for it with `is None`.

### Code quality

- **TR-18:** Follow PEP 8 naming: `snake_case` for functions and variables, `PascalCase` for classes.
- **TR-19:** Every class and public method has a one-line docstring.
- **TR-20:** Use type hints on method signatures, e.g. `def add(self, a: float, b: float) -> float:`.

## Suggested design

This is a starting skeleton, not a final answer. You may rename things or add classes if you can explain why.

```python
# calculator.py
import json
from collections import namedtuple
from pathlib import Path

DATA_FILE = Path("calculator_data.json")

Calculation = namedtuple("Calculation", ["op", "operands", "result"])


class Calculator:
    """Performs arithmetic operations."""

    def __init__(self) -> None:
        self.operations = {}   # TODO: map command name -> method (TR-6)

    def add(self, a: float, b: float) -> float: ...
    def divide(self, a: float, b: float) -> float: ...
    # ... other operations


class History:
    """Stores past calculations in order."""

    def __init__(self) -> None:
        self._entries: list[Calculation] = []

    def add(self, calc: Calculation) -> None: ...
    def last_result(self) -> float | None: ...
    def stats(self) -> dict: ...
    def save(self, path: Path, memory: float | None) -> None: ...
    def load(self, path: Path) -> float | None: ...  # returns saved memory
    def __len__(self) -> int: ...
    def __str__(self) -> str: ...


class CalculatorApp:
    """Reads commands from the user and prints results."""

    def __init__(self) -> None:
        self.calculator = Calculator()
        self.history = History()
        self.memory = None
        self.running = True

    def run(self) -> None: ...


if __name__ == "__main__":
    CalculatorApp().run()
```

### Sample session

```
Loaded 0 past calculations from calculator_data.json
Python Calculator — type 'help' for commands
> add 4 5
9
> mul last 3
27
> div 10 0
Error: cannot divide by zero
> ms
Stored 27 in memory
> sqrt 16
4.0
> history
1. add (4, 5) = 9
2. mul (9, 3) = 27
3. sqrt (16,) = 4.0
> stats
count: 3, min: 4.0, max: 27, average: 13.33
> power 2 3
Unknown command 'power'. Type 'help' to see options.
> quit
Saved 3 calculations to calculator_data.json. Goodbye!
```

## Error handling

The program must never crash on bad input. Handle at least these cases with `try/except`:

| Situation | Example | Message shown |
| --- | --- | --- |
| Not a number | `add 4 abc` | `'abc' is not a valid number` |
| Divide or modulo by zero | `div 5 0` | `Error: cannot divide by zero` |
| Square root of a negative | `sqrt -4` | `Error: cannot take square root of a negative number` |
| `last` with empty history | `add last 1` | `No previous result yet` |
| `mr` with empty memory | `mr` | `Memory is empty` |
| Ctrl+C or Ctrl+D | — | Exit cleanly with the goodbye message |

Raise errors inside `Calculator` (e.g. `ValueError`, `ZeroDivisionError`) and catch them in `CalculatorApp`.

## Testing

- Write tests in `test_calculator.py` using `unittest` or `pytest`.
- Cover every operation, at least 3 error cases, and the `History` methods (`add`, `last_result`, `stats`, `len`).
- Aim for at least 15 test cases. All must pass before review.

## Acceptance criteria

- [ ] All 20 functional requirements work, including saving and reloading from the file
- [ ] At least 3 classes, each with a clear single responsibility
- [ ] A dictionary drives operation lookup; no long `if/elif` chain
- [ ] History is a list; operands and history entries are tuples
- [ ] No `eval()`, no database, no global mutable state
- [ ] No crash on any input listed under Error handling
- [ ] At least 15 passing tests
- [ ] README explains how to run the program and the tests

## Deliverables

- `calculator.py` — the program
- `test_calculator.py` — the tests
- `README.md` — how to run it, plus 3–5 sentences on your design choices (why a tuple here, why a dict there)
- Code pushed to a Git repository with small, meaningful commits

## Milestones

1. `Calculator` class with the 8 operations, plus tests for each.
2. `CalculatorApp` input loop, command dictionary, `help` and `quit`.
3. `History` class, `history`, `last`, `clear`, `stats`, memory commands, saving and loading the JSON file.
4. Error handling, remaining tests, README. Submit for code review.

## Stretch goals (optional)

- Let the user choose the save file with a \`--file\` argument using the built-in \`argparse\` module.
- Evaluate full expressions like `2 + 3 * 4` without `eval()`, respecting operator precedence.
- Add a `Operation` base class with one subclass per operation, to practise inheritance.
- Undo the last calculation with an `undo` command.
