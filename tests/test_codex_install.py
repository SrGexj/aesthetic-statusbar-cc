"""Tests for the Codex install: the shell wrapper and the tmux block."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aesthetic_statusbar import cli


class RcCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        self.rc = self.home / ".zshrc"
        orig = cli.shell_rc
        cli.shell_rc = lambda: self.rc
        self.addCleanup(setattr, cli, "shell_rc", orig)


class TestShellRc(unittest.TestCase):
    def test_bash_gets_bashrc(self):
        old = os.environ.get("SHELL")
        os.environ["SHELL"] = "/bin/bash"
        self.addCleanup(lambda: os.environ.pop("SHELL") if old is None else os.environ.update({"SHELL": old}))
        self.assertEqual(cli.shell_rc().name, ".bashrc")

    def test_anything_else_gets_zshrc(self):
        old = os.environ.get("SHELL")
        os.environ["SHELL"] = "/bin/zsh"
        self.addCleanup(lambda: os.environ.pop("SHELL") if old is None else os.environ.update({"SHELL": old}))
        self.assertEqual(cli.shell_rc().name, ".zshrc")


class TestShellFunction(RcCase):
    def test_wrapper_is_delimited_and_calls_the_real_codex(self):
        fn = cli.shell_function()
        self.assertTrue(fn.startswith(cli.SHELL_MARKER))
        self.assertIn(cli.SHELL_END, fn)
        self.assertIn('command codex "$@"', fn)
        self.assertIn(f"{cli.CODEX_COMMAND} --watch &", fn)

    def test_an_existing_tmux_session_is_left_alone(self):
        self.assertIn('if [ -n "$TMUX" ]; then', cli.shell_function())

    def test_tmux_runs_codex_under_the_bar_config(self):
        fn = cli.shell_function()
        self.assertIn("command -v tmux", fn)
        self.assertIn(f'tmux -f "{cli.TMUX_SESSION_CONF}" new-session -- codex "$@"', fn)

    def test_warp_gets_no_title_watcher(self):
        # Warp paints its own title at the top of the window.
        fn = cli.shell_function()
        warp = fn.index('"$TERM_PROGRAM" = "WarpTerminal"')
        watcher = fn.index(f"{cli.CODEX_COMMAND} --watch")
        self.assertLess(warp, watcher)


class TestTmuxSessionConf(unittest.TestCase):
    def test_carries_the_bar_on_the_left(self):
        conf = cli.tmux_session_conf()
        self.assertIn(f'set -g status-left "#({cli.CODEX_COMMAND} --tmux)"', conf)
        self.assertIn('set -g status-right ""', conf)

    def test_hides_every_other_piece_of_tmux_chrome(self):
        conf = cli.tmux_session_conf()
        self.assertIn('set -g window-status-format ""', conf)
        self.assertIn('set -g window-status-current-format ""', conf)
        self.assertIn("set -g status-position bottom", conf)

    def test_write_then_remove_leaves_the_file_as_it_was(self):
        self.rc.write_text("export EDITOR=vim\n", encoding="utf-8")
        cli.write_shell_function()
        self.assertIn(cli.SHELL_MARKER, self.rc.read_text(encoding="utf-8"))
        cli.remove_shell_function()
        self.assertEqual(self.rc.read_text(encoding="utf-8"), "export EDITOR=vim\n")

    def test_writing_twice_does_not_duplicate(self):
        cli.write_shell_function()
        cli.write_shell_function()
        self.assertEqual(self.rc.read_text(encoding="utf-8").count(cli.SHELL_MARKER), 1)

    def test_removing_from_an_untouched_rc_is_a_noop(self):
        self.rc.write_text("alias ll='ls -l'\n", encoding="utf-8")
        cli.remove_shell_function()
        self.assertEqual(self.rc.read_text(encoding="utf-8"), "alias ll='ls -l'\n")


class TestTmuxSessionConf(unittest.TestCase):
    def test_carries_the_bar_on_the_left(self):
        conf = cli.tmux_session_conf()
        self.assertIn(f'set -g status-left "#({cli.CODEX_COMMAND} --tmux)"', conf)
        self.assertIn('set -g status-right ""', conf)

    def test_hides_every_other_piece_of_tmux_chrome(self):
        conf = cli.tmux_session_conf()
        self.assertIn('set -g window-status-format ""', conf)
        self.assertIn('set -g window-status-current-format ""', conf)
        self.assertIn("set -g status-position bottom", conf)


class TestTmuxBlock(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.conf = Path(tmp.name) / ".tmux.conf"
        orig = cli.TMUX_CONF
        cli.TMUX_CONF = self.conf
        self.addCleanup(setattr, cli, "TMUX_CONF", orig)

    def test_block_renders_the_bar_as_tmux_markup(self):
        self.assertIn("--tmux", cli.tmux_line())

    def test_write_then_remove_roundtrip(self):
        self.conf.write_text("set -g mouse on\n", encoding="utf-8")
        cli.write_tmux_config()
        self.assertIn(cli.TMUX_MARKER, self.conf.read_text(encoding="utf-8"))
        cli.remove_tmux_config()
        self.assertEqual(self.conf.read_text(encoding="utf-8"), "set -g mouse on\n")

    def test_writing_twice_does_not_duplicate(self):
        cli.write_tmux_config()
        cli.write_tmux_config()
        self.assertEqual(self.conf.read_text(encoding="utf-8").count(cli.TMUX_MARKER), 1)


if __name__ == "__main__":
    unittest.main()
