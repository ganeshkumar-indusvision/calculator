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

    def test_100_concurrent_jobs_and_history(self):
        initial_history = len(self.history)
        job_ids = []
        id_lock = threading.Lock()

        def submit_many():
            for i in range(20):
                jid = self.manager.submit("add", (i, 1))
                with id_lock:
                    job_ids.append(jid)

        self.start_workers()
        producers = [threading.Thread(target=submit_many) for _ in range(5)]
        for t in producers:
            t.start()
        for t in producers:
            t.join()

        self.manager.queue.join()
        self.stop_workers()

        self.assertEqual(len(job_ids), 100)
        self.assertEqual(len(set(job_ids)), 100)
        self.assertTrue(
            all(self.manager.get(jid).state == JobState.DONE for jid in job_ids)
        )
        self.assertEqual(len(self.history), initial_history + 100)
