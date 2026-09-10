"""Tests for the Codex adapter: rollout parsing, window labels, cache ratio."""

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aesthetic_statusbar import codex
from aesthetic_statusbar.renderer import render_snapshot

ANSI = re.compile(r"\033\[[\d;]*m")


def plain(text: str) -> str:
    return ANSI.sub("", text)


def token_count(primary=None, secondary=None, **usage) -> dict:
    last = {
        "input_tokens": 20000,
        "cached_input_tokens": 15000,
        "output_tokens": 500,
        "total_tokens": 20500,
    }
    last.update(usage)
    return {
        "type": "token_count",
        "info": {
            "total_token_usage": last,
            "last_token_usage": last,
            "model_context_window": 258400,
        },
        "rate_limits": {"primary": primary, "secondary": secondary},
    }


def write_rollout(path: Path, events: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for entry in events:
            f.write(json.dumps(entry) + "\n")


class TestWindowLabel(unittest.TestCase):
    def test_hours(self):
        self.assertEqual(codex.window_label(300), "5h")

    def test_days(self):
        self.assertEqual(codex.window_label(10080), "7d")
        self.assertEqual(codex.window_label(43200), "30d")

    def test_minutes(self):
        self.assertEqual(codex.window_label(30), "30m")

    def test_missing_window(self):
        self.assertEqual(codex.window_label(None), "")


class TestRateData(unittest.TestCase):
    def test_shorter_window_goes_first(self):
        rate = codex.get_rate_data(
            token_count(
                primary={"used_percent": 12.0, "window_minutes": 10080, "resets_at": 100},
                secondary={"used_percent": 60.0, "window_minutes": 300, "resets_at": 50},
            )
        )
        self.assertEqual((rate["label_5h"], rate["pct_5h"]), ("5h", 60.0))
        self.assertEqual((rate["label_7d"], rate["pct_7d"]), ("7d", 12.0))

    def test_single_window_leaves_the_second_bar_empty(self):
        rate = codex.get_rate_data(
            token_count(primary={"used_percent": 1.0, "window_minutes": 43200, "resets_at": 7})
        )
        self.assertEqual(rate["label_5h"], "30d")
        self.assertIsNone(rate["pct_7d"])

    def test_no_limits_reported(self):
        rate = codex.get_rate_data({})
        self.assertIsNone(rate["pct_5h"])
        self.assertIsNone(rate["pct_7d"])


class TestUsageSegments(unittest.TestCase):
    def test_context_suffix_counts_the_last_turn(self):
        self.assertEqual(codex.get_context_suffix(token_count()), "(20.5k/258.4k)")

    def test_context_suffix_without_a_window(self):
        tc = token_count()
        tc["info"]["model_context_window"] = 0
        self.assertEqual(codex.get_context_suffix(tc), "")

    def test_cache_ratio_from_cached_input_tokens(self):
        cache = codex.get_cache_data(token_count())
        self.assertTrue(cache["warm"])
        self.assertAlmostEqual(cache["hit_ratio"], 0.75)
        self.assertEqual(cache["misses"], 0)

    def test_cache_cold_when_nothing_was_cached(self):
        cache = codex.get_cache_data(token_count(cached_input_tokens=0))
        self.assertFalse(cache["warm"])

    def test_no_cache_segment_before_the_first_turn(self):
        self.assertEqual(codex.get_cache_data(token_count(input_tokens=0)), {})


class TestEffort(unittest.TestCase):
    def test_turn_context_wins(self):
        turn = {"collaboration_mode": {"settings": {"reasoning_effort": "high"}}}
        thread = {"reasoning_effort": "low"}
        self.assertEqual(codex.get_effort(thread, turn, {"model_reasoning_effort": "medium"}), "high")

    def test_falls_back_to_the_thread_store(self):
        self.assertEqual(codex.get_effort({"reasoning_effort": "low"}, {}, {}), "low")

    def test_falls_back_to_config_toml(self):
        self.assertEqual(codex.get_effort({}, {}, {"model_reasoning_effort": "medium"}), "medium")

    def test_unknown_when_nothing_reports(self):
        self.assertEqual(codex.get_effort({}, {}, {}), "?")


class TestRollout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "rollout.jsonl"

    def test_reads_the_last_events(self):
        write_rollout(
            self.path,
            [
                {"type": "turn_context", "payload": {"model": "gpt-5-old"}},
                {"type": "event_msg", "payload": token_count(primary={"used_percent": 5.0, "window_minutes": 300})},
                {"type": "turn_context", "payload": {"model": "gpt-5.6-terra"}},
                {
                    "type": "event_msg",
                    "payload": token_count(
                        primary={"used_percent": 9.0, "window_minutes": 300}, input_tokens=30000
                    ),
                },
            ],
        )
        out = codex.read_rollout(str(self.path))
        self.assertEqual(out["turn_context"]["model"], "gpt-5.6-terra")
        self.assertEqual(out["token_count"]["rate_limits"]["primary"]["used_percent"], 9.0)

    def test_survives_a_truncated_tail(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "event_msg", "payload": token_count()}) + "\n")
            f.write('{"type": "event_msg", "payload": {"type": "token_c')
        self.assertIn("token_count", codex.read_rollout(str(self.path)))

    def test_missing_file(self):
        self.assertEqual(codex.read_rollout(str(self.path / "nope")), {})
        self.assertEqual(codex.read_rollout(""), {})


class TestSnapshotRendering(unittest.TestCase):
    def setUp(self):
        # The renderer reads the user's own config, which may hide segments.
        from aesthetic_statusbar import config, renderer

        cfg = dict(config.DEFAULT_CONFIG)
        cfg["show"] = dict(config.DEFAULT_CONFIG["show"])
        cfg["show"]["update"] = False
        cfg["order"] = list(config.DEFAULT_CONFIG["order"])
        orig = renderer.load_config
        renderer.load_config = lambda: cfg
        self.addCleanup(setattr, renderer, "load_config", orig)

    def test_bar_paints_a_codex_snapshot(self):
        snap = {
            "model": "gpt-5.6-terra",
            "ctx_suffix": "(20.5k/258.4k)",
            "effort": "high",
            "rate": {
                "pct_5h": 60.0,
                "reset_5h": None,
                "label_5h": "5h",
                "pct_7d": 12.0,
                "reset_7d": None,
                "label_7d": "7d",
            },
            "cache": codex.get_cache_data(token_count()),
        }
        line = plain(render_snapshot(snap))
        self.assertIn("5h ", line)
        self.assertIn("7d ", line)
        self.assertIn("gpt-5.6-terra(20.5k/258.4k)", line)
        self.assertIn("effort: high", line)
        self.assertIn("75%", line)


class TestFindThread(unittest.TestCase):
    """No thread store: the adapter falls back to the rollout files on disk."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        self.day = self.home / "sessions" / "2026" / "09" / "10"
        self.day.mkdir(parents=True)
        old = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = str(self.home)
        self.addCleanup(lambda: os.environ.pop("CODEX_HOME") if old is None else os.environ.update({"CODEX_HOME": old}))

    def add_session(self, name: str, cwd: str, mtime: float) -> Path:
        path = self.day / f"rollout-{name}.jsonl"
        write_rollout(path, [{"type": "session_meta", "payload": {"cwd": cwd}}])
        os.utime(path, (mtime, mtime))
        return path

    def test_prefers_a_session_started_in_this_directory(self):
        self.add_session("newest", "/elsewhere", 2000)
        mine = self.add_session("mine", "/work/repo", 1000)
        self.assertEqual(codex.find_thread("/work/repo")["rollout_path"], str(mine))

    def test_falls_back_to_the_newest_session(self):
        newest = self.add_session("newest", "/elsewhere", 2000)
        self.add_session("older", "/other", 1000)
        self.assertEqual(codex.find_thread("/work/repo")["rollout_path"], str(newest))

    def test_no_sessions_at_all(self):
        self.assertEqual(codex.find_thread("/work/repo"), {})

    def test_snapshot_without_a_session_still_renders(self):
        snap = codex.codex_snapshot("/work/repo")
        self.assertEqual(snap["model"], "?")
        self.assertEqual(snap["cache"], {})
        self.assertIsNone(snap["rate"]["pct_5h"])


class TestCodexConfig(unittest.TestCase):
    def test_stops_at_the_first_table_header(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        home = Path(tmp.name)
        (home / "config.toml").write_text(
            'model = "gpt-5.6-terra"\n'
            'model_reasoning_effort = "high"\n'
            "\n"
            "[mcp_servers.pencil]\n"
            'model = "not-the-session-model"\n',
            encoding="utf-8",
        )
        old = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = str(home)
        self.addCleanup(lambda: os.environ.pop("CODEX_HOME") if old is None else os.environ.update({"CODEX_HOME": old}))

        cfg = codex.read_codex_config()
        self.assertEqual(cfg["model"], "gpt-5.6-terra")
        self.assertEqual(cfg["model_reasoning_effort"], "high")

    def test_missing_config(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        old = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = tmp.name
        self.addCleanup(lambda: os.environ.pop("CODEX_HOME") if old is None else os.environ.update({"CODEX_HOME": old}))
        self.assertEqual(codex.read_codex_config(), {})


if __name__ == "__main__":
    unittest.main()
