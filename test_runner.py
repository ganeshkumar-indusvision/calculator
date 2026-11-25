import unittest
import time
import tempfile
import io
from contextlib import redirect_stdout
from pathlib import Path
from calculator import History
from task_runner import (
    ScientificCalculator,
    JobManager,
    Worker,
    JobState,Job,Utils,JobNotFoundError,DEFAULT_DIGIT_LIMIT
)
import threading
from test_data import ScientificCalculatorData, JobManagerData,UtilsData



class TestUtils(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = ScientificCalculator()
        self.utils = Utils(self.calculator)
        self.utils_data = UtilsData(DEFAULT_DIGIT_LIMIT)
        self.check_digit_cases = self.utils_data.check_digit_cases
        self.check_digit_passthrough_cases = self.utils_data.check_digit_passthrough_cases
        self.add_digit_words_cases = self.utils_data.add_digit_words_cases
        self.formate_msg_cases = self.utils_data.formate_msg_cases

    def test_check_digit(self) -> None:
        for value, expected_val, expected_flag in self.check_digit_cases:
            with self.subTest(expected=(expected_val, expected_flag)):
                self.assertEqual(
                    self.utils._check_digit(value),
                    (expected_val, expected_flag),
                )

    def test_check_digit_passthrough(self) -> None:
        for value, expected_val, expected_flag in self.check_digit_passthrough_cases:
            with self.subTest(value=value):
                self.assertEqual(
                    self.utils._check_digit(value),
                    (expected_val, expected_flag),
                )

    def test_add_digit_words(self) -> None:
        for msg, expected in self.add_digit_words_cases:
            with self.subTest(msg=msg):
                self.assertEqual(self.utils.add_digit_words(msg), expected)

    def test_formate_msg(self) -> None:
        for op, result, expected in self.formate_msg_cases:
            with self.subTest(op=op, expected=expected):
                self.assertEqual(self.utils.formate_msg(op, result), expected)

class TestWorker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data = JobManagerData()
        self.test_dir = Path(self.temp_dir.name)
        
        self.jobs_file, self.history_file = (
            self.data.create_initial_files(self.test_dir)
        )

        self.calc = ScientificCalculator()
        self.utils = Utils(self.calc)
        self.history = History()
        self.memory = self.history.load(self.history_file)

        self.manager = JobManager(
            self.calc,
            self.history,
            self.utils,
            self.jobs_file
        )
        self.manager.load()

        self.workers = [
            Worker(f"Worker-{i}", self.manager)
            for i in range(1, 4)
        ]
    def start_workers(self):
        for worker in self.workers:
            worker.thread.start()
            
    def stop_workers(self):
        self.manager.stop_event.set()
        for worker in self.workers:
            if worker.thread.is_alive():
                worker.thread.join(timeout=2)


    def test_worker_handles_calculation_error(self):
        job_id = self.manager.submit("div", (10, 0))
        self.start_workers()

        self.manager.queue.join()

        job = self.manager.get(job_id)
        self.assertEqual(job.state, JobState.FAILED)
        self.assertIsNotNone(job.error)

    def test_worker_processes_multiple_jobs(self):
        job_ids = [
            self.manager.submit("add", (i, 10))
            for i in range(5)
        ]

        self.start_workers()
        self.manager.queue.join()
        i = 0
        for job_id in job_ids:

            self.assertEqual(
                self.manager.get(job_id).state,
                JobState.DONE
            )
            self.assertEqual(
                self.manager.get(job_id).result,
                (i+10)
            )
            i = i +1

    def test_three_workers_process_jobs(self):
        job_ids = [
            self.manager.submit("mul", (i, 2))
            for i in range(1, 11)
        ]

        self.start_workers()
        self.manager.queue.join()
        i = 1
        for job_id in job_ids:
            self.assertEqual(
                self.manager.get(job_id).state,
                JobState.DONE
            )
            self.assertEqual(
                self.manager.get(job_id).result,
                (i*2)
            )
            i = i +1

    def test_no_duplicate_job_execution(self):
        job_ids = [
            self.manager.submit("add", (i, 1))
            for i in range(20)
        ]

        self.start_workers()
        self.manager.queue.join()

        completed = [
            job_id for job_id in job_ids
            if self.manager.get(job_id).state == JobState.DONE
        ]

        self.assertEqual(len(completed), len(job_ids))
    def test_worker_shutdown_when_idle(self):
        self.start_workers()
        self.stop_workers()

        for worker in self.workers:
            self.assertFalse(worker.thread.is_alive())

    def test_worker_shutdown_after_job(self):
        job_id = self.manager.submit("add", (5, 5))
        self.start_workers()

        self.manager.queue.join()
        self.stop_workers()

        self.assertEqual(
            self.manager.get(job_id).state,
            JobState.DONE
        )

    def test_shutdown_with_empty_queue(self):
        self.start_workers()
        self.stop_workers()

        self.assertTrue(
            all(not worker.thread.is_alive() for worker in self.workers)
        )
    def tearDown(self):
        self.stop_workers()
        self.temp_dir.cleanup()
    def test_worker_initialization(self):
        worker = self.workers[0]
        self.assertIs(worker.manager, self.manager)
        self.assertIsNone(worker.current_job)
        self.assertEqual(worker.thread.name, "Worker-1")
        self.assertFalse(worker.thread.is_alive())

    def test_worker_executes_job(self):
        job_id = self.manager.submit("add", (4, 5))
        self.start_workers()

        self.manager.queue.join()

        job = self.manager.get(job_id)
        self.assertEqual(job.state, JobState.DONE)
        self.assertEqual(job.result, 9)


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
        self.utils = Utils(self.calc)
        self.memory = self.history.load(self.history_file)

        self.manager = JobManager(
            self.calc,
            self.history,
            self.utils,
            self.jobs_file
        )

        self.manager.load()

    def tearDown(self):
        self.temp_dir.cleanup()
    def test_submit_adds_job_to_queue(self):
        job_id = self.manager.submit("add", (4, 5))
        queued_id = self.manager.queue.get_nowait()
        self.assertEqual(queued_id, job_id)
        
    def test_get_invalid_job(self):
        with self.assertRaises(JobNotFoundError):
            self.manager.get(999)
    def test_mark_running(self):
        job_id = self.manager.submit("add", (4, 5))
    
        job = self.manager.mark_running(job_id)

        self.assertEqual(job.state, JobState.RUNNING)
        self.assertIsNotNone(job.started_at)
    # this should change running to failed and makr error as intruped (this should be ideally start with again makring it queue ideally)
    def test_interrupted_jobs(self):
        queued_job = self.manager.get(2)
        running_job = self.manager.get(3)

        self.assertEqual(queued_job.state, JobState.FAILED)
        self.assertEqual(queued_job.error, "interrupted")

        self.assertEqual(running_job.state, JobState.FAILED)
        self.assertEqual(running_job.error, "interrupted")
    
    # test next id value should be 5 as we wrote 1-4 jobs
    def test_next_id_after_loading(self):
        job_id = self.manager.submit("add", (10, 20))
        self.assertEqual(job_id, 5)
    def test_save_and_load_jobs(self):
        job_id = self.manager.submit("add", (5, 6))

        new_manager = JobManager(
            self.calc,
            self.history,
            self.utils,
            self.jobs_file
        )
        new_manager.load()

        job = new_manager.get(job_id)

        self.assertEqual(job.command, "add")
        self.assertEqual(job.operands, (5, 6))
        self.assertEqual(job.state, JobState.FAILED)
        self.assertEqual(job.error, "interrupted")
    def test_record_calculation(self):
        self.manager.record_calculation("add", (2, 3), 5)

        self.assertEqual(len(self.history), 2)
        self.assertEqual(self.history.last_result(), 5)
    def test_job_duration_not_started(self):
        job = Job(id=1, command="add", operands=(4, 5))

        self.assertIsNone(job.duration)
    def test_show_jobs(self):
        output = io.StringIO()

        with redirect_stdout(output):
            self.manager.show_jobs()

        expected = (
            " 1  add 4 5          DONE    1.00s\n"
            " 2  primes 10        FAILED  interrupted\n"
            " 3  fib 10           FAILED  interrupted\n"
            " 4  div 10 0         FAILED  Error: cannot divide by zero\n"
        )

        self.assertEqual(output.getvalue(), expected)
    def test_finish_invalid_job(self):
        self.manager.finish(999, 100)

        self.assertNotIn(999, self.manager.jobs)

    def test_fail_invalid_job(self):
        self.manager.fail(999, "Some error")

        self.assertNotIn(999, self.manager.jobs)
    def test_show_empty_jobs(self):
        manager = JobManager(
            self.calc,
            self.history,
            self.utils,
            self.test_dir / "empty.json"
        )

        output = io.StringIO()
    
        with redirect_stdout(output):
            manager.show_jobs()
    
        self.assertIn("No jobs yet", output.getvalue())
    def test_concurrent_submissions(self):
        

        job_ids = []
        result_lock = threading.Lock()

        def submit_jobs():
            for _ in range(20):
                job_id = self.manager.submit("add", (1, 2))

                with result_lock:
                    job_ids.append(job_id)

        threads = [
            threading.Thread(target=submit_jobs)
            for _ in range(5)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(job_ids), 100)
        self.assertEqual(len(set(job_ids)), 100)
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
    def test_job_duration(self):
        job = Job(
            id=1,
            command="add",
            operands=(4, 5),
            started_at=100.0,
            finished_at=102.5,
        )
    
        self.assertEqual(job.duration, 2.5)
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