# Project Decisions, Violations and Explanations

Here I am documenting all the violations and changes made in calculator.py compared to the original cli-cal.md requirements. 

Most of these changes I discussed and took approval during the first level review itself, because while building the calculator I faced some practical issues with normal python floats and terminal inputs. The remaining things were cleaned up so the code looks simple and works properly without any bugs.

---

## 1. Things Deviated from Spec (Taken Approval in First Review)

### 1. Using decimal module instead of normal float
- Spec rule (TR-21): Only use json, pathlib, math, collections, unittest, tempfile.
- What I did: imported Decimal, ROUND_FLOOR, InvalidOperation from decimal.
- Reason: 
  - In python normal float has precision issue because of IEEE 754 standard. If you do `0.1 + 0.2` in python terminal it gives `0.30000000000000004` instead of `0.3`. Because of this `0.1 + 0.2 == 0.3` becomes False and test cases were failing.
  - Also for modulo operation with floats, normal python `%` operator gives weird rounding numbers like `0.4999999999999998` instead of exact remainder. So I used Decimal with ROUND_FLOOR so modulo calculates accurately.
  - Since this is calculator app, getting wrong decimal value looks bad. So I took approval in first level review to use Decimal.

### 2. Using readline module
- Spec rule (TR-21): readline not in allowed modules list.
- What I did: imported readline at the top.
- Reason: 
  - When running calculator.py in terminal, whenever I pressed left arrow, right arrow or up arrow to fix typo or check previous command, it was printing weird gibberish characters like `^[[A`, `^[[B`, `^[[D` into the input. 
  - Because of this the command gets corrupted and throws error like unknown command or not a valid number.
  - By importing readline, python automatically handles arrow keys so user can move cursor and edit input cleanly. Took approval for this also.

### 3. Sqrt returning integer for whole numbers
- Spec rule (FR-7 & TR-15): Spec says whole number results should print without decimal (like 9), but specifically for `sqrt 16` it should print `4.0`.
- What I did: In my code `sqrt 16` gives 4 (int) instead of 4.0.
- Reason:
  - I wrote one common helper function `_validate_output` which checks if decimal number is whole number (`result == result.to_integral_value()`). If it is whole it converts to int, else float.
  - If I make sqrt always return float, I had to put special `if op == "sqrt"` check inside common output logic which felt like hack. So kept common logic for all operations. Took approval for this.

### 4. Direct Decimal input conversion
- Spec rule (TR-15): Convert input strings using float().
- What I did: Converted directly using Decimal(text) in `_detect_numeric_type`.
- Reason: 
  - If I convert string to float first and then to Decimal, the precision is already lost in float step (`Decimal(float("0.1"))` gives `0.1000000000000000055...`). 
  - So converting directly string to Decimal keeps exact value user entered.

### 5. Using Lambdas with Arity tuple instead of separate methods
- Spec rule (TR-6): Map command names to methods like `{"add": self.add, "sub": self.subtract}` and suggested writing separate def add(), def sub() etc.
- What I did: Kept operations as lambda inside dictionary paired with argument count:
  ```python
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
  ```
- Reason:
  - Writing 8 separate methods just to do single line `return a + b` was creating around 35 lines of useless boilerplate code. None of these functions use self at all.
  - Having (arity, lambda) in single dictionary makes it very clean and easy to read in one place, exactly like how command_info is done in CalculatorApp.
  - Also this completely avoids needing any bytecode inspection tricks. Took approval to use lambdas.

---

## 2. Code Cleanups and Fixes Done

### 1. Removed __code__.co_argcount bytecode check
- Earlier I was doing `n = self.operations[op].__code__.co_argcount` to find how many arguments function expects.
- But inspecting `__code__` is internal cpython implementation detail. If function is wrapped or built-in c function it can fail or give wrong count.
- Now by storing arity directly in tuple `(2, lambda ...)`, we just do `n, _ = self.operations[op]` which is O(1) and never breaks.

### 2. Fixed warning print in History.load
- Spec TR-5 says History and Calculator should never call print() directly so they can be tested without terminal noise.
- But FR-20 says if json file is corrupted it should print warning and rename to .bak.
- To fix this conflict without breaking TR-5, I added `on_warning=None` parameter to `History.load()`. In `CalculatorApp.run()` I pass `on_warning=print`, so CalculatorApp does the printing. When running unit tests no callback is passed so it stays clean.

### 3. Kept save and load in History class directly
- TR-24 mentions saving and loading can live in History or small Storage class.
- I decided to keep it directly in History itself so we don't create unnecessary extra classes when not needed. Keeps project strictly to 3 main classes (Calculator, History, CalculatorApp) as per TR-1.

### 4. Fixed set comprehension print in help
- In `_help()` earlier there was `{print(key, ":", value[1]) for key, value in self.command_info.items()}`.
- Set comprehension is meant for creating a set, not for running side effect like print. It was creating useless `{None}` set in memory.
- Changed it to simple clean for loop.

### 5. Fixed *args type annotation
- In calculate method it was written `def calculate(self, *arg: tuple)`.
- In python typing `*args: T` means type of each argument passed, not the whole tuple. So changed it to `def calculate(self, *args: object)`.

---

## 3. Python Memory & Variable Storage Concept (From Bhuvan's Video)

After watching the video on variable storage in python, here is how it relates to this calculator implementation:

### Variables are references (pointers), not storage boxes
- In python, variables don't hold the actual data directly like in C. Variable is just a label/name that points to an object in heap memory (PyObject).
- If you do `a = [1, 2]` and `b = a`, both point to the same memory address. If you change `b.append(3)`, `a` also changes.

### Why operands must be tuple and not list
- In `Calculation = namedtuple("Calculation", ["op", "operands", "result"])`, we store operands as tuple e.g. `(4, 5)`.
- Because tuple is immutable, once created its items cannot be changed or appended.
- If operands was a mutable list `[4, 5]`, then if someone modifies that list outside, our calculation history would also get silently modified in memory.
- To make sure this never happens, in `History.add()` I explicitly do `tuple(calc.operands)` before saving into `_entries`.

### Handling JSON tuple to list issue
- JSON format does not have any tuple datatype, it only has array `[]`.
- So when `json.dump` saves history to file, python converts tuple `(4, 5)` into json list `[4, 5]`.
- When we load it back using `json.load()`, python gives it back as list, not tuple.
- So in `History.load()` I explicitly convert it back using `tuple(item["operands"])` when creating Calculation object. That way in-memory entries and file-loaded entries both always use immutable tuples consistently.
