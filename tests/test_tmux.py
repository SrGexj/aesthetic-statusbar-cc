"""Tests for the tmux markup conversion."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aesthetic_statusbar.tmux import ansi_to_tmux


class TestAnsiToTmux(unittest.TestCase):
    def test_foreground_color(self):
        self.assertEqual(ansi_to_tmux("\033[38;5;220mmodel"), "#[fg=colour220]model#[default]")

    def test_background_color(self):
        self.assertEqual(ansi_to_tmux("\033[48;5;236m "), "#[bg=colour236] #[default]")

    def test_reset(self):
        self.assertEqual(ansi_to_tmux("a\033[0mb"), "a#[default]b#[default]")

    def test_combined_sequence(self):
        self.assertEqual(
            ansi_to_tmux("\033[48;5;236m\033[38;5;244m7%"),
            "#[bg=colour236]#[fg=colour244]7%#[default]",
        )

    def test_hash_is_escaped_so_tmux_does_not_read_it_as_markup(self):
        self.assertEqual(ansi_to_tmux("PR #12"), "PR ##12#[default]")

    def test_plain_text_still_ends_reset(self):
        self.assertEqual(ansi_to_tmux("ok"), "ok#[default]")

    def test_no_ansi_left_behind(self):
        from aesthetic_statusbar.colors import get_palette
        from aesthetic_statusbar.bars import progress_bar

        out = ansi_to_tmux(progress_bar(42, get_palette("default"), width=10))
        self.assertNotIn("\033", out)


if __name__ == "__main__":
    unittest.main()
