"""Tests for the Codex hook: the bar printed inside Codex after every turn."""

import io
import json
import os
import sys
import re
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aesthetic_statusbar import cli, codex

ANSI = re.compile(r"\033\[[\d;]*m")


def plain(text: str) -> str:
    return ANSI.sub("", text)


class CodexHomeCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        old = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = str(self.home)
        self.addCleanup(
            lambda: os.environ.pop("CODEX_HOME") if old is None else os.environ.update({"CODEX_HOME": old})
        )
        self.hooks = self.home / "hooks.json"

    def hooks_json(self) -> dict:
        return json.loads(self.hooks.read_text(encoding="utf-8"))


class TestHooksFile(CodexHomeCase):
    def test_registers_the_stop_event(self):
        cli.write_codex_hook()
        events = self.hooks_json()["hooks"]
        self.assertEqual(sorted(events), ["Stop"])
        self.assertEqual(events["Stop"][0]["hooks"][0]["command"], cli.HOOK_COMMAND)

    def test_codex_only_accepts_the_nested_shape(self):
        # A bare event map at the root makes Codex reject the whole file with
        # `unknown field \`Stop\``, so anything found there is folded inside.
        self.hooks.write_text(json.dumps({"Stop": [{"hooks": [{"type": "command", "command": "theirs"}]}]}), encoding="utf-8")
        cli.write_codex_hook()
        data = self.hooks_json()
        self.assertNotIn("Stop", set(data) - {"hooks"})
        commands = [h["command"] for e in data["hooks"]["Stop"] for h in e["hooks"]]
        self.assertIn("theirs", commands)
        self.assertIn(cli.HOOK_COMMAND, commands)

    def test_writing_twice_registers_once(self):
        cli.write_codex_hook()
        cli.write_codex_hook()
        entries = self.hooks_json()["hooks"]["Stop"]
        commands = [h["command"] for e in entries for h in e.get("hooks", [])]
        self.assertEqual(commands.count(cli.HOOK_COMMAND), 1)

    def test_uninstall_keeps_other_peoples_hooks(self):
        self.hooks.write_text(
            json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "lint.sh"}]}]}}),
            encoding="utf-8",
        )
        cli.write_codex_hook()
        cli.remove_codex_hook()
        data = self.hooks_json()
        commands = [h["command"] for e in data["hooks"]["Stop"] for h in e["hooks"]]
        self.assertEqual(commands, ["lint.sh"])

    def test_removing_when_nothing_is_registered(self):
        self.hooks.write_text(json.dumps({"hooks": {}}), encoding="utf-8")
        cli.remove_codex_hook()
        self.assertEqual(self.hooks_json(), {"hooks": {}})


class TestHookOutput(CodexHomeCase):
    def payload(self, **over) -> dict:
        data = {
            "hook_event_name": "Stop",
            "cwd": str(self.home),
            "model": "gpt-6-astra",
            "transcript_path": None,
        }
        data.update(over)
        return data

    def run_hook(self, raw: str) -> str:
        out, err = io.StringIO(), io.StringIO()
        stdin, stdout = sys.stdin, sys.stdout
        sys.stdin, sys.stdout = io.StringIO(raw), out
        try:
            with self.assertRaises(SystemExit) as exit_code:
                codex.hook_main()
        finally:
            sys.stdin, sys.stdout = stdin, stdout
        self.assertEqual(exit_code.exception.code, 0, err.getvalue())
        return out.getvalue()

    def test_emits_a_system_message(self):
        body = json.loads(self.run_hook(json.dumps(self.payload())))
        self.assertIn("systemMessage", body)
        self.assertIn("\u25cf", body["systemMessage"])  # the git segment

    def test_leaves_out_what_codex_already_prints(self):
        message = json.loads(self.run_hook(json.dumps(self.payload())))["systemMessage"]
        self.assertNotIn("gpt-6-astra", message)
        self.assertNotIn("effort:", message)

    def test_reads_the_rollout_the_payload_points_at(self):
        rollout = self.home / "rollout.jsonl"
        events = [
            {"type": "turn_context", "payload": {"model": "gpt-5.6-terra"}},
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "last_token_usage": {"input_tokens": 1000, "cached_input_tokens": 900, "output_tokens": 24},
                        "model_context_window": 200000,
                    },
                    "rate_limits": {"primary": {"used_percent": 7.0, "window_minutes": 300, "resets_at": None}},
                },
            },
        ]
        rollout.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

        message = json.loads(self.run_hook(json.dumps(self.payload(transcript_path=str(rollout)))))["systemMessage"]
        self.assertIn("1.0k/200k", plain(message))  # this session's own numbers
        self.assertIn("7%", plain(message))

    def test_junk_on_stdin_is_not_the_session_s_problem(self):
        self.assertIn("systemMessage", self.run_hook("not json at all"))

    def test_empty_stdin(self):
        self.assertIn("systemMessage", self.run_hook(""))


if __name__ == "__main__":
    unittest.main()
