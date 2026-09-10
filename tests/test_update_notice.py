"""Tests for the update notice: it must name a command that exists here."""

import os
import pathlib
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aesthetic_statusbar import version_check
from aesthetic_statusbar.version_check import UPDATE_URL, git_checkout, update_command

ANSI = re.compile(r"\033\[[\d;]*m")


class TestUpdateCommand(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fake_install = pathlib.Path(self.tmp.name).resolve() / "aesthetic-statusbar"
        self.fake_install.mkdir()

        self.orig_dir = version_check.CURL_INSTALL_DIR
        self.orig_which = version_check.shutil.which
        self.orig_checkout = version_check.git_checkout
        self.addCleanup(self._restore)
        version_check.CURL_INSTALL_DIR = self.fake_install
        version_check.shutil.which = lambda name: None
        # The tests themselves run inside a checkout; opt into that case
        # explicitly instead of having every assertion see it.
        version_check.git_checkout = lambda start: None

    def _restore(self):
        version_check.CURL_INSTALL_DIR = self.orig_dir
        version_check.shutil.which = self.orig_which
        version_check.git_checkout = self.orig_checkout

    def test_editable_checkout_pulls_instead_of_overwriting(self):
        repo = pathlib.Path(self.tmp.name).resolve() / "repo"
        version_check.git_checkout = lambda start: repo
        version_check.shutil.which = lambda name: "/usr/local/bin/" + name
        self.assertEqual(update_command(), f"git -C {repo} pull")

    def test_checkout_needs_both_git_and_pyproject(self):
        repo = pathlib.Path(self.tmp.name).resolve() / "half-a-repo"
        (repo / ".git").mkdir(parents=True)
        self.assertIsNone(git_checkout(repo / "src" / "aesthetic_statusbar"))
        (repo / "pyproject.toml").write_text("")
        self.assertEqual(git_checkout(repo / "src" / "aesthetic_statusbar"), repo)

    def test_curl_install_points_at_its_own_script(self):
        (self.fake_install / "run.py").write_text("")
        script = self.fake_install / "update.sh"
        script.write_text("")
        self.assertEqual(update_command(), f"bash {script}")

    def test_paths_with_spaces_stay_pasteable(self):
        spaced = pathlib.Path(self.tmp.name).resolve() / "my projects" / "statusbar"
        spaced.mkdir(parents=True)
        version_check.CURL_INSTALL_DIR = spaced
        (spaced / "run.py").write_text("")
        (spaced / "update.sh").write_text("")
        self.assertEqual(update_command(), f"bash '{spaced / 'update.sh'}'")

    def test_console_script_install_uses_the_cli(self):
        version_check.shutil.which = lambda name: "/usr/local/bin/" + name
        self.assertEqual(update_command(), "aesthetic-statusbar setup update")

    def test_falls_back_to_the_remote_one_liner(self):
        self.assertEqual(update_command(), f"curl -fsSL {UPDATE_URL} | bash")

    def test_curl_dir_without_script_does_not_name_a_missing_file(self):
        (self.fake_install / "run.py").write_text("")
        self.assertEqual(update_command(), f"curl -fsSL {UPDATE_URL} | bash")


class TestNoticeRendering(unittest.TestCase):
    def test_segment_carries_version_and_command(self):
        from aesthetic_statusbar import config, renderer

        cfg = dict(config.DEFAULT_CONFIG)
        cfg["show"] = {k: False for k in config.DEFAULT_CONFIG["show"]}
        cfg["show"]["update"] = True
        cfg["order"] = list(config.DEFAULT_CONFIG["order"])

        patches = {
            "read_stdin": lambda: {},
            "read_settings": lambda: {},
            "load_config": lambda: cfg,
            "get_update": lambda: "1.2.0",
            "update_command": lambda: "do-the-thing",
        }
        for name, stub in patches.items():
            orig = getattr(renderer, name)
            setattr(renderer, name, stub)
            self.addCleanup(setattr, renderer, name, orig)

        plain = ANSI.sub("", renderer.render())
        self.assertEqual(plain, "\u21911.2.0 do-the-thing")


if __name__ == "__main__":
    unittest.main()
