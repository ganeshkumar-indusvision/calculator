import unittest
import time
import tempfile

from pathlib import Path
from calculator import History
from task_runner import (
    ScientificCalculator,
    JobManager,
    Worker,
    JobState,
)
from test_data import ScientificCalculatorData, JobManagerData
class TestJobManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data = JobManagerData()
        self.test_dir = Path(self.temp_dir.name)
    
        self.jobs_file, self.history_file = (
            self.data.create_initial_files(self.test_dir)
        )
    
        self.calc = ScientificCalculator()
        self.history = History()
    
        self.memory = self.history.load(self.history_file)
    
        self.manager = JobManager(
            self.calc,
            self.history,
            self.jobs_file
        )
    
        self.manager.load()
    
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initial_history_loaded(self):
        self.assertEqual(len(self.history), 1)
        self.assertEqual(self.history.last_result(), 12)
        self.assertEqual(self.memory, 7.5)
    def test_submit_get_jobs(self):
        job_id = self.manager.submit("add", (4, 5))
        job = self.manager.get(job_id)

        self.assertEqual(job.id, job_id)
        self.assertEqual(job.command, "add")
        self.assertEqual(job.operands, (4, 5))
        self.assertEqual(job.state, JobState.QUEUED)
    def test_unique_job_ids(self):
        first_id = self.manager.submit("add", (1, 2))
        second_id = self.manager.submit("add", (3, 4))
        self.assertNotEqual(first_id, second_id)
    def test_finish_job(self):
        job_id = self.manager.submit("add", (4, 5))

        self.manager.finish(job_id, 9)

        job = self.manager.get(job_id)
        self.assertEqual(job.state, JobState.DONE)
        self.assertEqual(job.result, 9)
    def test_failed_job(self):
        job_id = self.manager.submit("div", (10, 0))

        self.manager.fail(job_id, "Cannot divide by zero")
    
        job = self.manager.get(job_id)
        self.assertEqual(job.state, JobState.FAILED)
        self.assertEqual(job.error, "Cannot divide by zero")
     
class TestCalculator(unittest.TestCase):

    def setUp(self):
        self.calc = ScientificCalculator()
        self.data = ScientificCalculatorData()
        self.input_output = self.data.input_output
        self.value_error_cases = self.data.value_error_cases
        self.single_input_error_cases= self.data.single_input_error_cases
        self.error_cases= self.data.error_cases
        self.bad_call_cases= self.data.bad_call_cases

    def test_operations(self):
        for op, cases in self.input_output.items():
            for a, b, expected in cases:
                with self.subTest(op=op, a=a, b=b):
                    args = (a,) if b is None else (a, b)
                    result = self.calc.calculate(op, *args)
                    self.assertEqual(result, expected)
                    if op != "sqrt"  and isinstance(expected, (int, float)):
                        self.assertIsInstance(
                            result, int if isinstance(expected, int) else float)

    def test_errors(self):
        for op, cases in self.error_cases.items():
            for a, b, exc in cases:
                with self.subTest(op=op, a=a, b=b):
                    args = (a,) if b is None else (a, b)
                    with self.assertRaises(exc):
                        self.calc.calculate(op, *args)

    def test_bad_calls(self):
        for args, exc in self.bad_call_cases:
            with self.subTest(args=args), self.assertRaises(exc):
                self.calc.calculate(*args)
   

if __name__ == "__main__":
    unittest.main()
    # sci=ScientificCalculator()
    # print(sci.calculate("fact",199999))
    # print(sci.calculate("fact",200000))
    # print(sci.calculate("primes",200000))