import unittest
import time
import tempfile
import io
from contextlib import redirect_stdout
from pathlib import Path
from src.calculator import History
from src.calculator import (
    ScientificCalculator,
    JobManager,
    Worker,
    JobState,
    Job,
    Utils,
    JobNotFoundError,
    DEFAULT_DIGIT_LIMIT,
    TaskRunnerApp,
)
import logging
import threading
from tests.data import ScientificCalculatorData, JobManagerData,UtilsData
from unittest.mock import patch







