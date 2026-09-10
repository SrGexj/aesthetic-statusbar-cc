"""Tests for the terminal-title watcher used when there is no tmux."""

import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aesthetic_statusbar import watch
from aesthetic_statusbar.bars import text_bar


class TestTextBar(unittest.TestCase):
    def test_survives_losing_its_colors(self):
        bar = text_bar(50, width=10)
        self.assertEqual(bar, "█████░░░░░ 50%")

    def test_empty_and_full(self):
        self.assertEqual(text_bar(0, width=4), "░░░░ 0%")
        self.assertEqual(text_bar(100, width=4), "████ 100%")


class TestTitleLoop(unittest.TestCase):
    def setUp(self):
        self.out = io.StringIO()
        orig_writer, orig_title = watch._writer, watch.title_text
        watch._writer = lambda: self.out
        watch.title_text = lambda: "bar contents"
        self.addCleanup(setattr, watch, "_writer", orig_writer)
        self.addCleanup(setattr, watch, "title_text", orig_title)

    def test_writes_the_title_escape_once(self):
        watch.title_loop(once=True)
        self.assertEqual(self.out.getvalue(), "\033]2;bar contents\007")

    def test_a_closed_terminal_does_not_raise(self):
        class Closed(io.StringIO):
            def write(self, _):
                raise OSError("gone")

        watch._writer = Closed
        watch.title_loop(once=True)


class TestPlain(unittest.TestCase):
    def test_strips_ansi(self):
        self.assertEqual(watch.plain("\033[38;5;220mmodel\033[0m"), "model")

    def test_title_has_no_escape_sequences(self):
        self.assertNotIn("\033", watch.title_text())


if __name__ == "__main__":
    unittest.main()
