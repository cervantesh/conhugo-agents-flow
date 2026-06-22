import json
import os
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from agent_bus import cli
from agent_bus.locking import acquire_lock


class AgentBusCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def paths(self) -> cli.Paths:
        return cli.ensure_repo_paths(self.repo_root)

    def read_json_lines(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def call_quiet(self, func, *args):
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = func(*args)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_bootstrap_repo_creates_seed_files_and_templates(self) -> None:
        cli.bootstrap_repo(self.repo_root)
        paths = self.paths()

        self.assertTrue(paths["events_path"].exists())
        self.assertTrue(paths["registry_path"].exists())
        self.assertTrue((self.repo_root / ".githooks" / "pre-commit").exists())
        self.assertTrue((self.repo_root / "docs" / "coordination" / "decision-log.md").exists())

        events = self.read_json_lines(paths["events_path"])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["id"], "seed-0001")

        registry = json.loads(paths["registry_path"].read_text(encoding="utf-8"))
        self.assertEqual(registry["last_event_id"], "seed-0001")

    def test_install_writes_manifest_and_start_doc_even_when_git_config_fails(self) -> None:
        with patch("agent_bus.cli.subprocess.run", side_effect=cli.subprocess.CalledProcessError(128, "git")):
            result, _, _ = self.call_quiet(cli.cmd_install, Namespace(repo_root=str(self.repo_root), upgrade=False))

        self.assertEqual(result, 0)
        self.assertTrue((self.repo_root / "agent-bus.json").exists())
        self.assertTrue((self.repo_root / "AGENT_BUS.md").exists())

        ops = self.read_json_lines(self.repo_root / ".agents" / "runtime" / "ops.jsonl")
        self.assertEqual(ops[-1]["command"], "install")
        self.assertEqual(ops[-1]["status"], "warning")
        manifest = json.loads((self.repo_root / "agent-bus.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], cli.__version__)
        self.assertEqual(manifest["schema_version"], cli.MANIFEST_SCHEMA_VERSION)

    def test_publish_updates_registry_context_and_log(self) -> None:
        cli.bootstrap_repo(self.repo_root)

        result, _, _ = self.call_quiet(
            cli.cmd_publish,
            Namespace(
                repo_root=str(self.repo_root),
                from_agent="codex-a",
                to="codex-b",
                issue="12",
                branch="feat/12-test",
                summary="Published from test",
                type="handoff",
                next_steps=["Review", "Merge"],
                action_required=True,
            ),
        )

        self.assertEqual(result, 0)
        paths = self.paths()
        events = self.read_json_lines(paths["events_path"])
        self.assertEqual(len(events), 2)
        self.assertEqual(events[-1]["to"], "codex-b")
        self.assertTrue(events[-1]["action_required"])

        registry = json.loads(paths["registry_path"].read_text(encoding="utf-8"))
        self.assertEqual(registry["active_issue"], "12")

        handoff = paths["handoff_path"].read_text(encoding="utf-8")
        self.assertIn("codex-a", handoff)
        self.assertIn("Review", handoff)

        ops = self.read_json_lines(paths["ops_log_path"])
        self.assertEqual(ops[-1]["command"], "publish")
        self.assertEqual(ops[-1]["status"], "ok")

    def test_check_and_ack_flow(self) -> None:
        cli.bootstrap_repo(self.repo_root)
        self.call_quiet(
            cli.cmd_publish,
            Namespace(
                repo_root=str(self.repo_root),
                from_agent="codex-a",
                to="codex-b",
                issue="15",
                branch="feat/15-check",
                summary="Need review",
                type="handoff",
                next_steps=["Review"],
                action_required=True,
            ),
        )

        blocked, _, _ = self.call_quiet(
            cli.cmd_check, Namespace(repo_root=str(self.repo_root), agent="codex-b", fail_on_pending=True)
        )
        self.assertEqual(blocked, 1)

        acked, _, _ = self.call_quiet(cli.cmd_ack, Namespace(repo_root=str(self.repo_root), agent="codex-b"))
        self.assertEqual(acked, 0)

        clear, _, _ = self.call_quiet(
            cli.cmd_check, Namespace(repo_root=str(self.repo_root), agent="codex-b", fail_on_pending=True)
        )
        self.assertEqual(clear, 0)

        ack = json.loads((self.repo_root / ".agents" / "inbox" / "codex-b.json").read_text(encoding="utf-8"))
        self.assertEqual(ack["agent"], "codex-b")

    def test_validate_agent_name_rejects_invalid_values(self) -> None:
        with self.assertRaises(SystemExit):
            cli.validate_agent_name("bad name with spaces")

    def test_pre_commit_check_uses_environment_agent(self) -> None:
        cli.bootstrap_repo(self.repo_root)
        self.call_quiet(
            cli.cmd_publish,
            Namespace(
                repo_root=str(self.repo_root),
                from_agent="codex-a",
                to="codex-c",
                issue="18",
                branch="feat/18-gate",
                summary="Pending action",
                type="handoff",
                next_steps=[],
                action_required=True,
            ),
        )

        with patch.dict(os.environ, {"AGENT_NAME": "codex-c"}, clear=False):
            blocked, _, _ = self.call_quiet(cli.cmd_pre_commit_check, Namespace(repo_root=str(self.repo_root)))
        self.assertEqual(blocked, 1)

        self.call_quiet(cli.cmd_ack, Namespace(repo_root=str(self.repo_root), agent="codex-c"))
        with patch.dict(os.environ, {"AGENT_NAME": "codex-c"}, clear=False):
            clear, _, _ = self.call_quiet(cli.cmd_pre_commit_check, Namespace(repo_root=str(self.repo_root)))
        self.assertEqual(clear, 0)

    def test_rotate_ops_log_trims_large_files(self) -> None:
        cli.bootstrap_repo(self.repo_root)
        paths = self.paths()
        lines = [json.dumps({"n": index}) for index in range(200)]
        paths["ops_log_path"].parent.mkdir(parents=True, exist_ok=True)
        paths["ops_log_path"].write_text("\n".join(lines) + "\n", encoding="utf-8")

        cli.rotate_ops_log_if_needed(paths["ops_log_path"], max_bytes=100)

        trimmed = paths["ops_log_path"].read_text(encoding="utf-8").splitlines()
        self.assertLess(len(trimmed), len(lines))
        self.assertGreater(len(trimmed), 0)

    def test_install_upgrade_refreshes_managed_static_files_only(self) -> None:
        cli.bootstrap_repo(self.repo_root)
        paths = self.paths()
        cli.write_manifest(paths)
        cli.write_start_doc(paths)

        (self.repo_root / "AGENT_BUS.md").write_text("OLD DOC\n", encoding="utf-8")
        decision_log_path = self.repo_root / "docs" / "coordination" / "decision-log.md"
        decision_log_path.write_text("KEEP DECISION LOG\n", encoding="utf-8")
        old_event = {"id": "custom", "timestamp": "x", "type": "status", "from": "a", "to": "all", "issue": "1", "branch": "b", "summary": "keep", "next_steps": [], "action_required": False}
        paths["events_path"].write_text(json.dumps(old_event) + "\n", encoding="utf-8")

        with patch("agent_bus.cli.subprocess.run", side_effect=cli.subprocess.CalledProcessError(128, "git")):
            result, _, _ = self.call_quiet(cli.cmd_install, Namespace(repo_root=str(self.repo_root), upgrade=True))

        self.assertEqual(result, 0)
        self.assertIn("development-process coordination tooling only", (self.repo_root / "AGENT_BUS.md").read_text(encoding="utf-8"))
        self.assertEqual(decision_log_path.read_text(encoding="utf-8"), "KEEP DECISION LOG\n")
        events = self.read_json_lines(paths["events_path"])
        self.assertEqual(events, [old_event])

    def test_doctor_detects_version_drift_and_missing_files(self) -> None:
        cli.bootstrap_repo(self.repo_root)
        paths = self.paths()
        cli.write_manifest(paths)
        cli.write_start_doc(paths)
        manifest = json.loads(paths["manifest_path"].read_text(encoding="utf-8"))
        manifest["version"] = "0.0.1"
        paths["manifest_path"].write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (self.repo_root / "AGENT_BUS.md").unlink()

        result, stdout, _ = self.call_quiet(cli.cmd_doctor, Namespace(repo_root=str(self.repo_root)))
        self.assertEqual(result, 1)
        self.assertIn("agent-bus doctor found issues", stdout)

        ops = self.read_json_lines(paths["ops_log_path"])
        self.assertEqual(ops[-1]["command"], "doctor")
        self.assertEqual(ops[-1]["status"], "blocked")

    def test_publish_fails_when_repo_lock_is_held(self) -> None:
        cli.bootstrap_repo(self.repo_root)
        paths = self.paths()

        with acquire_lock(paths["bus_lock_path"], timeout_seconds=0.1):
            result, _, stderr = self.call_quiet(
                cli.cmd_publish,
                Namespace(
                    repo_root=str(self.repo_root),
                    from_agent="codex-a",
                    to="codex-b",
                    issue="22",
                    branch="feat/22-lock",
                    summary="Should fail on lock",
                    type="handoff",
                    next_steps=[],
                    action_required=False,
                ),
            )

        self.assertEqual(result, 1)
        self.assertIn("Timed out waiting for lock", stderr)


if __name__ == "__main__":
    unittest.main()
