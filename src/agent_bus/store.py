import json
import shutil
from pathlib import Path
from typing import Any

from agent_bus import __version__
from agent_bus.locking import acquire_lock
from agent_bus.repo import atomic_write, ensure_repo_paths, relative_paths
from agent_bus.types import (
    BOOTSTRAP_MUTABLE_FILES,
    MANAGED_STATIC_FILES,
    MANIFEST_SCHEMA_VERSION,
    AckRecord,
    CommandStatus,
    Event,
    Manifest,
    OpsLogEntry,
    Paths,
    Registry,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
TEMPLATES_ROOT = PACKAGE_ROOT / "templates"


def load_events(paths: Paths) -> list[Event]:
    events_path = paths["events_path"]
    if not events_path.exists():
        return []
    events: list[Event] = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


def append_event(paths: Paths, event: Event) -> None:
    paths["agents_dir"].mkdir(parents=True, exist_ok=True)
    with paths["events_path"].open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(event, ensure_ascii=True) + "\n")


def load_registry(paths: Paths) -> Registry:
    registry_path = paths["registry_path"]
    if not registry_path.exists():
        return {
            "version": 1,
            "last_event_id": None,
            "last_updated": None,
            "active_issue": None,
            "active_branch": None,
            "last_handoff": None,
        }
    return json.loads(registry_path.read_text(encoding="utf-8"))


def load_manifest(paths: Paths) -> Manifest | None:
    if not paths["manifest_path"].exists():
        return None
    return json.loads(paths["manifest_path"].read_text(encoding="utf-8"))


def save_registry(paths: Paths, registry: Registry) -> None:
    atomic_write(paths["registry_path"], json.dumps(registry, indent=2) + "\n")


def load_ack(paths: Paths, agent: str) -> AckRecord | None:
    ack_path = paths["inbox_dir"] / f"{agent}.json"
    if not ack_path.exists():
        return None
    return json.loads(ack_path.read_text(encoding="utf-8"))


def save_ack(paths: Paths, agent: str, event_id: str, timestamp: str) -> None:
    paths["inbox_dir"].mkdir(parents=True, exist_ok=True)
    payload: AckRecord = {
        "agent": agent,
        "last_seen_event_id": event_id,
        "acknowledged_at": timestamp,
    }
    atomic_write(paths["inbox_dir"] / f"{agent}.json", json.dumps(payload, indent=2) + "\n")


def rotate_ops_log_if_needed(log_path: Path, max_bytes: int = 262144) -> None:
    if not log_path.exists() or log_path.stat().st_size <= max_bytes:
        return
    lines = log_path.read_text(encoding="utf-8").splitlines()
    tail = lines[len(lines) // 2 :]
    atomic_write(log_path, "\n".join(tail) + ("\n" if tail else ""))


def write_ops_log(paths: Paths, command: str, status: CommandStatus, details: dict[str, Any], timestamp: str) -> None:
    paths["runtime_dir"].mkdir(parents=True, exist_ok=True)
    with acquire_lock(paths["ops_log_path"].with_suffix(".lock")):
        rotate_ops_log_if_needed(paths["ops_log_path"])
        payload: OpsLogEntry = {
            "timestamp": timestamp,
            "command": command,
            "status": status,
            "details": details,
        }
        with paths["ops_log_path"].open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True) + "\n")


def pending_events(paths: Paths, agent: str) -> list[Event]:
    events = load_events(paths)
    ack = load_ack(paths, agent)
    last_seen = ack["last_seen_event_id"] if ack else None

    relevant = [e for e in events if e.get("type") != "ack" and e.get("to") in {agent, "all"}]
    if last_seen is None:
        return relevant

    seen = False
    pending: list[Event] = []
    for event in relevant:
        if seen:
            pending.append(event)
        elif event["id"] == last_seen:
            seen = True

    if not seen:
        return relevant
    return pending


def write_human_context(paths: Paths, event: Event) -> None:
    next_steps = event.get("next_steps") or []
    next_steps_md = "\n".join(f"1. {step}" for step in next_steps) if next_steps else "1. None."
    handoff = f"""# Session Handoff

## Latest Handoff

- Date: {event["timestamp"]}
- From: {event["from"]}
- To: {event["to"]}
- Issue: {event["issue"]}
- Branch: {event["branch"]}
- Type: {event["type"]}
- Action required: {str(event["action_required"]).lower()}

## Summary

{event["summary"]}

## Next Recommended Action

{next_steps_md}

## Validation

- Event published to `.agents/events.jsonl`
- Registry updated in `.agents/registry.json`
"""
    paths["handoff_path"].parent.mkdir(parents=True, exist_ok=True)
    atomic_write(paths["handoff_path"], handoff)

    active_context = f"""# Active Context

## Current Focus

- Active issue: {event["issue"]}
- Active branch: {event["branch"]}
- Current owner: {event["from"]}
- Status: {event["type"]}
- Last update: {event["timestamp"]}

## Latest Summary

- {event["summary"]}

## Immediate Next Steps

{next_steps_md}
"""
    atomic_write(paths["active_context_path"], active_context)


def ensure_gitignore_entries(paths: Paths) -> None:
    gitignore_path = paths["gitignore_path"]
    entries = [".agents/inbox/", ".agents/runtime/"]
    if gitignore_path.exists():
        current = gitignore_path.read_text(encoding="utf-8").splitlines()
    else:
        current = []
    missing = [entry for entry in entries if entry not in current]
    if missing:
        updated = current + missing
        atomic_write(gitignore_path, "\n".join(updated) + "\n")


def merge_template_tree(name: str, destination: Path, overwrite: bool = False) -> None:
    source = TEMPLATES_ROOT / name
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if overwrite or not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def copy_template_file(template_relative: Path, destination: Path, overwrite: bool = False) -> None:
    source = TEMPLATES_ROOT / template_relative
    if overwrite or not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def bootstrap_repo(repo_root: Path, upgrade: bool = False) -> None:
    paths = ensure_repo_paths(repo_root)
    paths["agents_dir"].mkdir(parents=True, exist_ok=True)
    paths["inbox_dir"].mkdir(parents=True, exist_ok=True)
    paths["runtime_dir"].mkdir(parents=True, exist_ok=True)

    merge_template_tree("agents", paths["agents_dir"], overwrite=upgrade)
    merge_template_tree("docs_coordination", repo_root / "docs" / "coordination", overwrite=False)
    merge_template_tree("githooks", repo_root / ".githooks", overwrite=True)
    copy_template_file(
        Path("docs_coordination/README.md"),
        repo_root / "docs" / "coordination" / "README.md",
        overwrite=upgrade,
    )
    ensure_gitignore_entries(paths)

    if not paths["events_path"].exists():
        seed_event: Event = {
            "id": "seed-0001",
            "timestamp": "2026-06-22T00:00:00Z",
            "type": "status",
            "from": "system",
            "to": "all",
            "issue": "bootstrap",
            "branch": "bootstrap/agent-bus",
            "summary": "Agent communication bus initialized.",
            "next_steps": ["Configure git hooks.", "Publish first real handoff event."],
            "action_required": False,
        }
        append_event(paths, seed_event)

    if not paths["registry_path"].exists():
        registry: Registry = {
            "version": 1,
            "last_event_id": "seed-0001",
            "last_updated": "2026-06-22T00:00:00Z",
            "active_issue": "bootstrap",
            "active_branch": "bootstrap/agent-bus",
            "last_handoff": {
                "from": "system",
                "to": "all",
                "summary": "Agent communication bus initialized.",
            },
        }
        save_registry(paths, registry)


def write_manifest(paths: Paths) -> None:
    manifest: Manifest = {
        "name": "agent-bus",
        "version": __version__,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "classification": "development-process-tooling",
        "runtime_role": "non-product",
        "distribution_role": "not-shipped",
        "repo_footprint": "local-instance-only",
        "purpose": "human-agent coordination during development",
        "entrypoint": "scripts/agent_bus.py",
        "managed_static_files": relative_paths(list(MANAGED_STATIC_FILES)),
        "protocol_files": [
            ".agents/events.jsonl",
            ".agents/registry.json",
            "docs/coordination/active-context.md",
            "docs/coordination/session-handoff.md",
        ],
        "startup_command": "python scripts/agent_bus.py check --repo-root . --agent <agent>",
        "publish_command": "python scripts/agent_bus.py publish --repo-root . --from <agent> --to <agent> --issue <id> --branch <branch> --summary <text>",
        "ack_command": "python scripts/agent_bus.py ack --repo-root . --agent <agent>",
        "watch_command": "python scripts/agent_bus.py watch --repo-root . --agent <agent>",
        "pre_commit_command": "python scripts/agent_bus.py pre-commit-check --repo-root .",
        "doctor_command": "python scripts/agent_bus.py doctor --repo-root .",
        "logs": {"ops": ".agents/runtime/ops.jsonl"},
    }
    atomic_write(paths["manifest_path"], json.dumps(manifest, indent=2) + "\n")


def write_start_doc(paths: Paths) -> None:
    content = """# AGENT_BUS

This file describes development-process coordination tooling only.
It does not describe application runtime behavior.
Treat `agent-bus` as process infrastructure, not product implementation.

## Purpose

Fast entrypoint for agents consuming the agent-bus protocol in this repo.

## Read First

1. `agent-bus.json`
2. `docs/coordination/active-context.md`
3. `docs/coordination/session-handoff.md`

## Boundary

- Do not treat `.agents/` as application data.
- Do not treat `agent-bus.json` as product configuration.
- Do not treat `AGENT_BUS.md` as end-user documentation.
- Do not move coordination artifacts into business-logic folders.
- Do not assume `agent-bus` participates in production deploy/runtime unless the repo explicitly says so.

## Commands

```bash
python scripts/agent_bus.py check --repo-root . --agent <agent>
python scripts/agent_bus.py publish --repo-root . --from <agent> --to <agent> --issue <id> --branch <branch> --summary "<text>"
python scripts/agent_bus.py ack --repo-root . --agent <agent>
python scripts/agent_bus.py watch --repo-root . --agent <agent>
python scripts/agent_bus.py doctor --repo-root .
```

## Required Startup Sequence

1. Run `check`
2. Read `active-context.md`
3. Read `session-handoff.md`
4. Work only after pending `action_required=true` messages are understood

## Required Shutdown Sequence

1. Publish a handoff if context changed
2. Ack messages you processed
3. Leave next steps explicit

## Small Logs

- Local ops log: `.agents/runtime/ops.jsonl`
- This log is intentionally small and ignored by Git
"""
    atomic_write(paths["start_doc_path"], content)


def detect_manifest_issues(paths: Paths) -> list[str]:
    issues: list[str] = []
    manifest = load_manifest(paths)
    if manifest is None:
        issues.append("Missing agent-bus.json manifest.")
        return issues

    if manifest.get("name") != "agent-bus":
        issues.append("Manifest name is not `agent-bus`.")
    if manifest.get("version") != __version__:
        issues.append(
            f"Installed manifest version `{manifest.get('version')}` does not match package version `{__version__}`."
        )
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        issues.append(
            f"Manifest schema version `{manifest.get('schema_version')}` does not match expected `{MANIFEST_SCHEMA_VERSION}`."
        )
    expected_static = set(relative_paths(list(MANAGED_STATIC_FILES)))
    actual_static = set(manifest.get("managed_static_files", []))
    missing_static = sorted(expected_static - actual_static)
    if missing_static:
        issues.append(f"Manifest is missing managed static file declarations: {', '.join(missing_static)}.")
    return issues


def detect_repo_issues(paths: Paths) -> list[str]:
    issues = detect_manifest_issues(paths)
    for relative in MANAGED_STATIC_FILES:
        if not (paths["repo_root"] / relative).exists():
            issues.append(f"Missing managed static file `{relative.as_posix()}`.")
    for relative in BOOTSTRAP_MUTABLE_FILES:
        if not (paths["repo_root"] / relative).exists():
            issues.append(f"Missing bootstrap file `{relative.as_posix()}`.")
    return issues
