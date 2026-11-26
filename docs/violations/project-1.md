# Project Decisions, Violations and Explanations

Here I am documenting all the violations and changes made in calculator.py compared to the original [Project-1](docs/requirements/project-1.md) requirements. 

Most of these changes I discussed and took approval during the first level review itself, because while building the calculator I faced some practical issues with normal python floats and terminal inputs. The remaining things were cleaned up so the code looks simple and works properly without any bugs.


## Deviated from Spec (Taken Approval in First Review)

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

### 3. Direct Decimal input conversion
- Spec rule (TR-15): Convert input strings using float().
- What I did: Converted directly using Decimal(str(text)) in `_detect_numeric_type`.
- Reason: 
  - If I convert string to float first and then to Decimal, the precision is already lost in float step (`Decimal(float("0.1"))` gives `0.1000000000000000055...`). 
  - So converting directly string to Decimal keeps exact value user entered.

### 4. Using Lambdas with Arity tuple instead of separate methods
- Spec rule (TR-6): Map command names to methods like `{"add": self.add, "sub": self.subtract}` and suggested writing separate def add(), def sub() etc.
- In first reviwe i was asked to reduce the method creation and instead use common way to perform operation.
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


### 5. Rounding of Decimal Value to 3 and Converting into int datatype


1. This was done based on first review done to have meaningfull information to anyone reading result.
2. This was doen Against `FR-7`
3. Currently I am rounding off to 3 if there is any decimal value and if the value has too much `0` (ex : 4.000 or 4.0) I am ronding of to 4.



## Usage Of AI And Google(Summary)


Majorly First iteration of Code I wrote which had multiple error handling and test case.


⁠1. `Calculator()` and It's initial test case I wrote which took almost 3-4 hours on because there were many drawbacks I faced with maths calculation in python (even with before I just created bowler plate with AI but it was not good).
2. Later Once basic manually wrote Initialising `Calculator()` in `CalculatorApp()`. Made basic `ctr + c`, `operation` cmd work correctly. 
3. `History()` methods manually wrote which and made basic history read and write on file.
4. Created Test function for both `CalculatorApp()` and `History()` with AI again it was not good just made sure all test case example writen manaully and tried to call those function and test it out.
5. Took First review with sai. He pointed out many issues (example: code writing is not good it can be optimised further). 
6. Fixed it with writing manually and again took small review with him.
7. Final review was to use logger, some more small fixes with error handling was done with AI just to replace most of print statement present in `CalculatorApp()`.


### AI 

1. Refactor and simple code refactor like changing print() to logger formate which was used on suggestion to move prints to logger formate.
2. Writting few test case calling function `CalculatorApp()` and `History()` with adding test data with correct intent.
3. Refactor for creating `self.command_info` content for help command (Basicaly first 3,4 operation I manualy wrote)
4. Asked multiple doubts with ai to clearly understand specific concepts and it was implemented in seperate directory and verified the correct recommendation.