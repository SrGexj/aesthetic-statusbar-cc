"""Tests for the Windows-specific paths, runnable from any platform."""

import json
import os
import subprocess
import sys
import time
import unittest
from unittest import mock

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, SRC)

from aesthetic_statusbar import version_check

STDIN_SAMPLE = {
    "model": {"display_name": "Opus 5"},
    "context_window": {"context_window_size": 200000, "used_percentage": 12},
    "rate_limits": {
        "five_hour": {"used_percentage": 40, "resets_at": 4102444800},
        "seven_day": {"used_percentage": 30, "resets_at": 4102444800},
    },
    "prompt_cache": {
        "warm": False,
        "caching_observed": True,
        "ttl": "1h",
        "expires_at": None,
        "hit_ratio": 0.5,
        "misses": 1,
        "last_miss_cause": {"causes": ["likely_server_side"]},
        "miss_causes": {"likely_server_side": 1},
    },
}


class LegacyCodePage(unittest.TestCase):
    def test_render_survives_cp1252_stdout(self):
        """A Windows console on a legacy code page must not crash the bar.

        The pets, the bar blocks, ⚡ and ⚠ are all outside cp1252, so without
        reconfiguring stdout this raises UnicodeEncodeError.
        """
        env = dict(os.environ)
        env["PYTHONPATH"] = os.path.abspath(SRC)
        env["PYTHONIOENCODING"] = "cp1252"
        proc = subprocess.run(
            [sys.executable, "-c", "from aesthetic_statusbar.renderer import main; main()"],
            input=json.dumps(STDIN_SAMPLE),
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("UnicodeEncodeError", proc.stderr)
        self.assertIn("⚡", proc.stdout)


class DetachKwargs(unittest.TestCase):
    def test_posix_uses_new_session(self):
        kwargs = version_check.detach_kwargs("posix")
        self.assertTrue(kwargs["start_new_session"])
        self.assertNotIn("creationflags", kwargs)

    def test_windows_uses_creationflags(self):
        kwargs = version_check.detach_kwargs("nt")
        # start_new_session is POSIX-only and must not reach Popen on Windows.
        self.assertNotIn("start_new_session", kwargs)
        self.assertEqual(kwargs["creationflags"], 0x00000008 | 0x08000000)


class SpawnRefresh(unittest.TestCase):
    def test_child_is_detached_and_gets_the_package_on_its_path(self):
        with mock.patch.object(version_check.subprocess, "Popen") as popen:
            version_check.spawn_refresh()
        self.assertEqual(popen.call_count, 1)
        kwargs = popen.call_args.kwargs
        self.assertEqual(
            {k: v for k, v in kwargs.items() if k in ("start_new_session", "creationflags")},
            version_check.detach_kwargs(),
        )
        first = kwargs["env"]["PYTHONPATH"].split(os.pathsep)[0]
        self.assertTrue(os.path.isdir(os.path.join(first, "aesthetic_statusbar")))


class RefreshWithoutNetwork(unittest.TestCase):
    def test_failed_fetch_still_stamps_checked_at(self):
        """An offline machine must not spawn a child on every single render."""
        with mock.patch.object(version_check, "fetch_latest", side_effect=OSError("offline")):
            with mock.patch.object(version_check, "read_cache", return_value={}):
                with mock.patch.object(version_check, "write_cache") as write:
                    version_check.refresh()
        written = write.call_args.args[0]
        self.assertIsNone(written["latest"])
        self.assertAlmostEqual(written["checked_at"], time.time(), delta=5)


if __name__ == "__main__":
    unittest.main()
