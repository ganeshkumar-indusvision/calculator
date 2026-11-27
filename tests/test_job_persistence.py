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

    def test_load_missing_file(self):
        manager = JobManager(
            self.calc, History(), self.utils, self.logger, self.test_dir / "missing.json"
        )
        manager.load()
        self.assertEqual(manager.jobs, {})

    def test_load_corrupted_json(self):
        bad_file = self.test_dir / "corrupt.json"
        bad_file.write_text("{not valid json", encoding="utf-8")

        manager = JobManager(self.calc, History(), self.utils,self.logger, bad_file)
        manager.load()

        self.assertEqual(manager.jobs, {})
        self.assertTrue(bad_file.with_name("corrupt.json.bak").exists())

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
            self.utils,self.logger,
            self.jobs_file
        )
        new_manager.load()

        job = new_manager.get(job_id)

        self.assertEqual(job.command, "add")
        self.assertEqual(job.operands, (5, 6))
        self.assertEqual(job.state, JobState.FAILED)
        self.assertEqual(job.error, "interrupted")
