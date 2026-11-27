"""Calculator domain operations."""

from decimal import Decimal, ROUND_FLOOR

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
        self.validation = {
            "div":self._check_divisor,
            "mod":self._check_divisor,
            "sqrt":self._check_sqrt,
            "pow":self._check_pow,
        }
        
    def _check_divisor(self,a:float,b=int|float) -> None:
        if b == 0 :
            raise ZeroDivisionError("Error: cannot divide by zero")
    def _check_sqrt(self, a:int|float) -> None:
        if a < 0:
            raise ValueError("Error: cannot take square root of a negative number")
    def _check_pow(self, a: int|float, b: int|float) -> None:
        if a == 0 and b < 0:
            raise ZeroDivisionError("Error: cannot raise 0 to a negative power")
        if a < 0 and Decimal(str(b)) != Decimal(str(b)).to_integral_value():
            raise ValueError("Error: cannot raise a negative number to a fractional power")
        
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
            self._validate_number(v,op)
        validator = self.validation.get(op)
        if validator is not None:
            validator(*operands)

    def _validate_number(self, number: object, op: str) -> None:
        if not isinstance(number, (int, float, Decimal)) or isinstance(number, bool):
            raise ValueError(f"{number!r} is not a valid number")
        if not Decimal(str(number)).is_finite():
            raise ValueError(f"{number!r} is not a finite number")
    
    
    def _validate_output(self, op: str, *results: Decimal) -> int | float | tuple:
        """Convert whole Decimals to int, otherwise return float."""
        converted = tuple(
            int(result) if result == result.to_integral_value()
            else round(float(result), 3)
            for result in results
        )

        return converted[0] if len(converted) == 1 else converted

    def calculate(self, *args: object) -> int | float:
        """Validate the request, run the operation, and return a clean result."""
        self._validate_input(*args)
        op = str(args[0])
        operands = [Decimal(str(v)) for v in args[1:] if v is not None]
        return self._validate_output(op, self.operations[op][1](*operands))
