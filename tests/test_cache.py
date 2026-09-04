"""Tests for the prompt-cache segment: cause precedence and rendering."""

import os
import pathlib
import re
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aesthetic_statusbar import data
from aesthetic_statusbar.colors import get_palette
from aesthetic_statusbar.data import get_cache_data
from aesthetic_statusbar.formatters import cache_cause_label, pick_cache_cause
from aesthetic_statusbar.renderer import render_cache

ANSI = re.compile(r"\033\[[\d;]*m")


def plain(text: str) -> str:
    return ANSI.sub("", text)


def stdin_with(**prompt_cache) -> dict:
    pc = {
        "warm": True,
        "caching_observed": True,
        "ttl": "1h",
        "expires_at": int(time.time()) + 1800,
        "hit_ratio": 0.9,
        "misses": 0,
        "last_miss_cause": None,
        "miss_causes": {},
    }
    pc.update(prompt_cache)
    return {"prompt_cache": pc}


class PickCause(unittest.TestCase):
    def test_structural_beats_temporal(self):
        self.assertEqual(
            pick_cache_cause(["ttl_expired_1h", "tools_changed"]), "tools_changed"
        )
        self.assertEqual(
            pick_cache_cause(["ttl_expired_5m", "system_prompt_changed"]),
            "system_prompt_changed",
        )

    def test_system_beats_tools(self):
        self.assertEqual(
            pick_cache_cause(["tools_changed", "system_prompt_changed"]),
            "system_prompt_changed",
        )

    def test_diagnosed_beats_vague(self):
        self.assertEqual(
            pick_cache_cause(["unknown", "likely_server_side", "ttl_expired_1h"]),
            "ttl_expired_1h",
        )
        self.assertEqual(
            pick_cache_cause(["unknown", "likely_server_side"]), "likely_server_side"
        )

    def test_empty_and_unknown_names(self):
        self.assertEqual(pick_cache_cause([]), "")
        self.assertEqual(pick_cache_cause(None), "")
        # A cause added by a future Claude Code version must not crash or
        # outrank the ones we know about.
        self.assertEqual(
            pick_cache_cause(["brand_new_cause", "tools_changed"]), "tools_changed"
        )
        self.assertEqual(pick_cache_cause(["brand_new_cause"]), "brand_new_cause")


class Labels(unittest.TestCase):
    def test_vague_causes_are_flagged(self):
        self.assertEqual(cache_cause_label("likely_server_side"), "⚠ server")
        self.assertEqual(cache_cause_label("unknown"), "⚠ unknown")

    def test_known_causes_are_bare(self):
        self.assertEqual(cache_cause_label("tools_changed"), "tools")
        self.assertEqual(cache_cause_label("ttl_expired_5m"), "ttl 5m")

    def test_unrecognized_cause_is_humanized(self):
        self.assertEqual(cache_cause_label("brand_new_cause"), "brand new cause")


class GetCacheData(unittest.TestCase):
    def setUp(self):
        # get_cache_data falls back to the on-disk stdin cache; point it at a
        # path that cannot exist so the tests do not read this machine's state.
        self._real_cache = data.CACHE_FILE
        data.CACHE_FILE = pathlib.Path(tempfile.gettempdir()) / "aesthetic-statusbar-absent.json"

    def tearDown(self):
        data.CACHE_FILE = self._real_cache

    def test_absent_field(self):
        self.assertEqual(get_cache_data({"prompt_cache": {}}), {})

    def test_caching_off(self):
        self.assertEqual(get_cache_data(stdin_with(caching_observed=False)), {})

    def test_composite_cause_is_prioritized(self):
        data = get_cache_data(
            stdin_with(
                warm=False,
                misses=1,
                last_miss_cause={"causes": ["ttl_expired_1h", "tools_changed"]},
            )
        )
        self.assertEqual(data["last_cause"], "tools_changed")

    def test_expired_prefix_reported_cold(self):
        # Stale data out of the on-disk stdin cache claims to be warm.
        data = get_cache_data(
            stdin_with(warm=True, expires_at=int(time.time()) - 5, ttl="5m")
        )
        self.assertFalse(data["warm"])
        self.assertEqual(data["last_cause"], "ttl_expired_5m")


class RenderCache(unittest.TestCase):
    def setUp(self):
        self.pal = get_palette("default")

    def render(self, **prompt_cache):
        return plain(render_cache(get_cache_data(stdin_with(**prompt_cache)), self.pal))

    def test_warm(self):
        self.assertRegex(self.render(hit_ratio=0.9), r"^⚡ 90% \d+m$")

    def test_warm_with_misses(self):
        out = self.render(
            hit_ratio=0.44,
            misses=2,
            last_miss_cause={"causes": ["ttl_expired_1h"]},
        )
        self.assertIn("✗2 ttl 1h", out)

    def test_cold_with_cause(self):
        out = self.render(warm=False, misses=1, last_miss_cause={"causes": ["tools_changed"]})
        self.assertEqual(out, "⚡ cold: tools")

    def test_cold_without_cause(self):
        self.assertEqual(self.render(warm=False, expires_at=None), "⚡ cold")

    def test_cold_server_side(self):
        out = self.render(
            warm=False, misses=1, last_miss_cause={"causes": ["likely_server_side"]}
        )
        self.assertEqual(out, "⚡ cold: ⚠ server")

    def test_missing_hit_ratio(self):
        self.assertRegex(self.render(hit_ratio=None), r"^⚡ warm \d+m$")


if __name__ == "__main__":
    unittest.main()
