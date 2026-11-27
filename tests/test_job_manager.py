import json
import logging
import tempfile
import threading
import unittest
from pathlib import Path

from src.calculator import Job, JobManager, JobNotFoundError, JobState, ScientificCalculator, Utils, History
from tests.data import JobManagerData


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
        self.logger = logging.getLogger("test")
        self.manager = JobManager(
            self.calc,
            self.history,
            self.utils,
             self.logger,
            self.jobs_file
        )

        self.manager.load()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_batch_submit(self):
        ids = self.manager.batch_submit([("add", (1, 2)), ("mul", (3, 4))])

        self.assertEqual(len(ids), 2)
        self.assertEqual(len(set(ids)), 2)
        self.assertEqual(self.manager.get(ids[0]).state, JobState.QUEUED)
        self.assertEqual(self.manager.get(ids[1]).command, "mul")

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

    def test_record_calculation(self):
        self.manager.record_calculation("add", (2, 3), 5)

        self.assertEqual(len(self.history), 2)
        self.assertEqual(self.history.last_result(), 5)

    def test_job_duration_not_started(self):
        job = Job(id=1, command="add", operands=(4, 5))

        self.assertIsNone(job.duration)

    def test_show_jobs(self):
        expected = (
            " 1  add 4 5          DONE    1.00s\n"
            " 2  primes 10        FAILED  interrupted\n"
            " 3  fib 10           FAILED  interrupted\n"
            " 4  div 10 0         FAILED  Error: cannot divide by zero"
        )
        self.assertEqual(self.manager.show_jobs(), expected)

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
            self.logger,
            self.test_dir / "empty.json",
        )
        self.assertEqual(manager.show_jobs(), "No jobs yet")

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
