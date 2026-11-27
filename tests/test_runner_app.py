import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.calculator import History, JobManager, ScientificCalculator, TaskRunnerApp, Utils


class _IsolatedTaskRunnerApp(TaskRunnerApp):
    def _load_data(self) -> None: 
        pass

    def _load_manager(self) -> None:
        pass

    def start_worker(self) -> None:
        pass


class TestTaskRunnerApp(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.logger = logging.getLogger("test")
        with patch.object(History, "load", return_value=None), patch("logging.Logger.info"):
            self.app = _IsolatedTaskRunnerApp()
        self.app.history = History()
        self.app.manager = JobManager(
            self.app.calculator,
            self.app.history,
           
            self.app.utils,
             self.logger,
            self.test_dir / "jobs.json",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
    def test_batch_queues_3_valid_skips_2_invalid(self):
        batch_file = self.test_dir / "sums.txt"
        batch_file.write_text(
            "# comment\n"
            "add 4 5\n"
            "mul 2 3\n"
            "div 1 0\n"
            "fly 3\n"
            "fact abc\n",
            encoding="utf-8",
        )

        with self.assertLogs(self.app.logger, level="INFO") as cm:
            self.app._handle_batch((str(batch_file),))

        text = "\n".join(r.getMessage() for r in cm.records)
        self.assertEqual(len(self.app.manager.jobs), 3)
        self.assertIn("Queued 3 jobs (1-3).", text)
        self.assertIn("Skipped 2 invalid lines:", text)
        self.assertIn("line 5:", text)
        self.assertIn("line 6:", text)

    def test_batch_missing_file(self):
        with self.assertLogs(self.app.logger, level="WARNING") as cm:
            self.app._handle_batch((str(self.test_dir / "nope.txt"),))

        text = "\n".join(r.getMessage() for r in cm.records)
        self.assertIn("File not found: nope.txt", text)

    def test_submit_rejects_invalid_and_memory_commands(self):
        bad_inputs = [
            ("fly", "3"),
            ("fact", "abc"),
            ("add", "1"),
            ("ms",),
            ("mr",),
            ("mc",),
        ]
        for args in bad_inputs:
            with self.subTest(args=args):
                self.assertIsNone(self.app._handle_submit(args))

        self.assertEqual(len(self.app.manager.jobs), 0)
    def test_handle_result_states(self):
        jid = self.app.manager.submit("add", (4, 5))

        with self.assertLogs(self.app.logger, level="INFO") as cm:
            self.app._handle_result((str(jid),))
        self.assertEqual(cm.records[-1].getMessage(), "QUEUED")

        self.app.manager.finish(jid, 9)
        with self.assertLogs(self.app.logger, level="INFO") as cm:
            self.app._handle_result((str(jid),))
        self.assertEqual(cm.records[-1].getMessage(), "9")

        fail_id = self.app.manager.submit("div", (1, 0))
        self.app.manager.fail(fail_id, "cannot divide by zero")
        with self.assertLogs(self.app.logger, level="WARNING") as cm:
            self.app._handle_result((str(fail_id),))
        self.assertEqual(cm.records[-1].getMessage(), "FAILED: cannot divide by zero")

    def test_handle_result_unknown_id(self):
        with self.assertLogs(self.app.logger, level="WARNING") as cm:
            self.app._handle_result(("99",))
        self.assertTrue(any("99" in msg for msg in cm.output))
if __name__ == "__main__":
    unittest.main()
    # sci=ScientificCalculator()
    # print(sci.calculate("fact",199999))
    # print(sci.calculate("fact",200000))
    # print(sci.calculate("primes",200000))
