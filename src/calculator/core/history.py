"""Calculation history with JSON persistence."""

import json
import threading
from pathlib import Path

from src.calculator.core.models import Calculation
from src.calculator.utils.writer import AtomicWriter

class History:
    """Stores past calculations in order."""

    def __init__(self) -> None:
        """Start with an empty entry list."""
        self._entries: list[Calculation] = []
        self._lock= threading.RLock()

    def add(self, calc: Calculation) -> None:
        """Append a calculation to the history ensuring operands are an immutable tuple."""
        with self._lock:
            entry = Calculation(calc.op, tuple(calc.operands), calc.result)
            self._entries.append(entry)

    def last_result(self) -> int | float | None:
        """Return the most recent result, or None if history is empty."""
        with self._lock:
            if not self._entries:
                return None
            return self._entries[-1].result

    def stats(self) -> dict:
        """Return count, min, max, and average of all results."""
        with self._lock:
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
        with self._lock:
            data = {
                "memory": memory,
                # JSON has no tuple type, so operand tuples are converted to
                # lists here. load() converts them back to tuples.
                "history": [
                    {"op": c.op, "operands": list(c.operands), "result": c.result}
                    for c in self._entries
                ],
            }
            AtomicWriter().write_json(path, data)

    def load(self, path: Path, on_warning: object = None) -> int | float | None:
        """Load history from a JSON file and return the saved memory value."""
        with self._lock:
            if not path.exists():
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise TypeError("Top-level JSON must be an object")
                entries = [
                    Calculation(item["op"], tuple(item["operands"]), item["result"])
                    for item in data.get("history", [])
                ]
                memory = data.get("memory")
            except (json.JSONDecodeError, OSError, KeyError, TypeError, AttributeError, ValueError):
                backup = path.with_name(path.name + ".bak")
                try:
                    path.rename(backup)
                    msg = f"Warning: {path} was invalid. Renamed to {backup.name}."
                except OSError:
                    msg = f"Warning: could not read {path}. Starting empty."
                if callable(on_warning):
                    on_warning(msg)
                self._entries = []
                return None

            self._entries = entries
            return memory
    def clear(self) -> None:
        """Remove all entries from history."""
        with self._lock:
            self._entries = []

    def __len__(self) -> int:
        """Return the number of entries."""
        with self._lock:
            return len(self._entries)

    def __str__(self) -> str:
        """Return a numbered, multi-line view of the history."""
        with self._lock:
            if not self._entries:
                return "No calculations yet"
            return "\n".join(
                f"{i}. {op} {operands} = {result}"
                for i, (op, operands, result) in enumerate(self._entries, start=1)
            )
