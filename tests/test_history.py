import json
import tempfile
import unittest
from pathlib import Path

from src.calculator import Calculation, History


class TestHistory(unittest.TestCase):

    def setUp(self):
        # Entry data reused by several cases.
        add_4_5      = Calculation("add", (4, 5), 9)
        mul_9_3      = Calculation("mul", (9, 3), 27)
        div_7_2      = Calculation("div", (7, 2), 3.5)
        sqrt_16      = Calculation("sqrt", (16,), 4)
        sub_0_5      = Calculation("sub", (0, 5), -5)
        sub_0_5_alt  = Calculation("sub", (0, 5), -5)
        add_10_5     = Calculation("add", (10, 5), 15)
        add_1_2      = Calculation("add", (1, 2), 3)

        self.last_result_cases: list[tuple[list[Calculation], int | float | None]] = [
            ([], None),
            ([add_4_5], 9),
            ([add_4_5, mul_9_3], 27),
            ([div_7_2], 3.5),
            ([sqrt_16], 4),
            ([sub_0_5], -5),
        ]

        self.stats_cases: list[tuple[list[Calculation], dict]] = [
            ([], {"count": 0, "min": None, "max": None, "average": None}),
            ([add_4_5],
             {"count": 1, "min": 9, "max": 9, "average": 9.0}),
            ([add_4_5, mul_9_3],
             {"count": 2, "min": 9, "max": 27, "average": 18.0}),
            ([sub_0_5_alt, add_10_5],
             {"count": 2, "min": -5, "max": 15, "average": 5.0}),
        ]

        self.len_cases: list[tuple[list[Calculation], int]] = [
            ([], 0),
            ([add_1_2], 1),
            ([add_1_2] * 5, 5),
        ]

        self.str_cases: list[tuple[list[Calculation], str]] = [
            ([], "No calculations yet"),
            ([add_4_5], "1. add (4, 5) = 9"),
            ([add_4_5, mul_9_3],
             "1. add (4, 5) = 9\n2. mul (9, 3) = 27"),
        ]

        self.save_load_cases: list[tuple[list[Calculation], int | float | None]] = (
            self.last_result_cases + [([], 0)]
        )

        self.bad_json_cases: list[str] = [
            "{not valid json",
            "",
            "[1, 2, 3",
            "not json at all",
        ]

        self.clear_cases: list[list[Calculation]] = [
            [],
            [add_1_2],
        ]

        self.missing_file_name = "nope.json"
        self.data_file_name    = "data.json"

    def _build(self, entries: list[Calculation]) -> History:
        h = History()
        for c in entries:
            h.add(c)
        return h

    def test_last_result(self):
        for entries, expected in self.last_result_cases:
            with self.subTest(entries=entries):
                self.assertEqual(self._build(entries).last_result(), expected)

    def test_stats(self):
        for entries, expected in self.stats_cases:
            with self.subTest(entries=entries):
                self.assertEqual(self._build(entries).stats(), expected)

    def test_len(self):
        for entries, expected in self.len_cases:
            with self.subTest(entries=entries):
                self.assertEqual(len(self._build(entries)), expected)

    def test_str(self):
        for entries, expected in self.str_cases:
            with self.subTest(entries=entries):
                self.assertEqual(str(self._build(entries)), expected)

    def test_clear(self):
        for entries in self.clear_cases:
            with self.subTest(entries=entries):
                h = self._build(entries)
                h.clear()
                self.assertEqual(len(h), 0)
                self.assertIsNone(h.last_result())

    def test_save_load_roundtrip(self):
        for entries, memory in self.save_load_cases:
            with self.subTest(entries=entries, memory=memory):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / self.data_file_name
                    h = self._build(entries)
                    h.save(path, memory)
                    h2 = History()
                    loaded_mem = h2.load(path)
                    self.assertEqual(loaded_mem, memory)
                    self.assertEqual(str(h2), str(h))
                    for entry in h2._entries:
                        self.assertIsInstance(entry.operands, tuple)

    def test_load_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / self.missing_file_name
            h = History()
            self.assertIsNone(h.load(path))
            self.assertEqual(len(h), 0)

    def test_load_bad_json(self):
        for bad_content in self.bad_json_cases:
            with self.subTest(bad=bad_content):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / self.data_file_name
                    path.write_text(bad_content, encoding="utf-8")
                    h = History()
                    self.assertIsNone(h.load(path))
                    self.assertEqual(len(h), 0)
                    self.assertTrue(path.with_name(path.name + ".bak").exists())
                    self.assertFalse(path.exists())
