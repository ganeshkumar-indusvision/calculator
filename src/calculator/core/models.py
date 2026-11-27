"""Domain models."""

from collections import namedtuple
from dataclasses import dataclass
from enum import Enum

Calculation = namedtuple("Calculation", ["op", "operands", "result"])
