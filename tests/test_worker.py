import logging
import tempfile
import threading
import unittest
from pathlib import Path

from src.calculator import JobManager, ScientificCalculator, Utils, JobState, Worker, History
from tests.data import JobManagerData


class TestWorker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data = JobManagerData()
        self.test_dir = Path(self.temp_dir.name)
        
        self.jobs_file, self.history_file = (
            self.data.create_initial_files(self.test_dir)
        )
        self.logger = logging.getLogger("test")
        self.calc = ScientificCalculator()
        self.utils = Utils(self.calc)
        self.history = History()
        self.memory = self.history.load(self.history_file)

        self.manager = JobManager(
            self.calc,
            self.history,
            self.utils,
             self.logger,
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

    def tearDown(self):
        self.stop_workers()
        self.temp_dir.cleanup()

    def test_worker_survives_failed_job(self):
        single_worker = Worker("worker-1", self.manager)
        fail_id = self.manager.submit("div", (10, 0))
        ok_id = self.manager.submit("add", (2, 3))

        single_worker.thread.start()
        try:
            self.manager.queue.join()
        finally:
            self.manager.stop_event.set()
            single_worker.thread.join(timeout=2)

        self.assertEqual(self.manager.get(fail_id).state, JobState.FAILED)
        self.assertEqual(self.manager.get(ok_id).state, JobState.DONE)
        self.assertEqual(self.manager.get(ok_id).result, 5)

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
