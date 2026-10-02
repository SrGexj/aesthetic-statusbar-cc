"""Tests for running two Claude accounts at once: who is who, and no shared usage cache."""

import io
import json
import os
import pathlib
import re
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aesthetic_statusbar import data
from aesthetic_statusbar.renderer import render_account

ANSI = re.compile(r"\033\[[\d;]*m")

WORK = {"accountUuid": "a3a34f67-1111", "emailAddress": "me@work.com", "displayName": "Me Work"}
HOME = {"accountUuid": "a7251946-2222", "emailAddress": "me@gmail.com", "displayName": ""}


def payload(pct):
    return json.dumps({"rate_limits": {"five_hour": {"used_percentage": pct, "resets_at": 0}}})


class TwoAccounts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.home = root / "home"
        self.personal = root / "personal"
        self.personal.mkdir(parents=True)
        self.home.mkdir()
        # The default account lives in ~/.claude.json, the other next to its config dir.
        (self.home / ".claude.json").write_text(json.dumps({"oauthAccount": WORK}))
        (self.personal / ".claude.json").write_text(json.dumps({"oauthAccount": HOME}))

        self.patches = [
            mock.patch.object(data.Path, "home", return_value=self.home),
            mock.patch.object(data, "CACHE_DIR", root / "cache"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def account(self, config_dir):
        env = {"CLAUDE_CONFIG_DIR": str(config_dir)} if config_dir else {}
        with mock.patch.dict(os.environ, env, clear=False):
            if not config_dir:
                os.environ.pop("CLAUDE_CONFIG_DIR", None)
            return data.get_account()

    def feed(self, account, raw):
        with mock.patch.object(sys, "stdin", io.StringIO(raw)):
            return data.read_stdin(account)

    def test_default_dir_reads_home_claude_json(self):
        self.assertEqual(self.account(None)["email"], "me@work.com")

    def test_config_dir_reads_its_own_claude_json(self):
        acct = self.account(self.personal)
        self.assertEqual(acct["email"], "me@gmail.com")
        # No display name: fall back to the email's local part.
        self.assertEqual(acct["name"], "me")

    def test_no_login_means_no_account(self):
        self.assertEqual(self.account(self.home / "nowhere"), {})

    def test_each_account_keeps_its_own_slot(self):
        self.assertEqual(self.account(self.personal)["slot"], 0)
        self.assertEqual(self.account(None)["slot"], 1)
        self.assertEqual(self.account(self.personal)["slot"], 0)

    def test_usage_cache_is_not_shared(self):
        work, personal = self.account(None), self.account(self.personal)
        self.feed(work, payload(80))
        # The personal terminal before its first turn has no limits of its own yet.
        stdin = self.feed(personal, "{}")
        self.assertIsNone(data.get_rate_data(stdin, personal)["pct_5h"])
        self.assertEqual(data.get_rate_data({}, work)["pct_5h"], 80)

        self.feed(personal, payload(10))
        self.assertEqual(data.get_rate_data({}, personal)["pct_5h"], 10)
        self.assertEqual(data.get_rate_data({}, work)["pct_5h"], 80)


class RenderAccount(unittest.TestCase):
    work = {"uuid": WORK["accountUuid"], "email": WORK["emailAddress"], "name": "Me Work", "slot": 0}
    home = {"uuid": HOME["accountUuid"], "email": HOME["emailAddress"], "name": "me", "slot": 1}

    def test_display_name(self):
        self.assertEqual(ANSI.sub("", render_account(self.work, {})), "◆ Me Work")

    def test_label_override_by_email(self):
        out = render_account(self.home, {"me@gmail.com": "personal"})
        self.assertEqual(ANSI.sub("", out), "◆ personal")

    def test_accounts_get_different_tints(self):
        tint = lambda a: ANSI.match(render_account(a, {})).group()
        self.assertNotEqual(tint(self.work), tint(self.home))


if __name__ == "__main__":
    unittest.main()
