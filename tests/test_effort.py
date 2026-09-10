"""Tests for the effort segment: stdin wins over settings.json."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aesthetic_statusbar.data import get_effort


class TestEffort(unittest.TestCase):
    def test_live_level_from_stdin(self):
        self.assertEqual(get_effort({"effort": {"level": "high"}}, {}), "high")

    def test_stdin_beats_stale_settings(self):
        stdin_data = {"effort": {"level": "low"}}
        self.assertEqual(get_effort(stdin_data, {"effortLevel": "high"}), "low")

    def test_falls_back_to_settings(self):
        self.assertEqual(get_effort({}, {"effortLevel": "medium"}), "medium")

    def test_unknown_when_nothing_reports(self):
        self.assertEqual(get_effort({}, {}), "?")

    def test_survives_malformed_effort(self):
        self.assertEqual(get_effort({"effort": "high"}, {}), "?")


if __name__ == "__main__":
    unittest.main()
