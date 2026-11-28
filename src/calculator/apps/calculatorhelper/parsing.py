"""Operand parsing mixin."""

from decimal import Decimal, InvalidOperation


class OperandParser:
    """Parse and validate numeric operands."""

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
