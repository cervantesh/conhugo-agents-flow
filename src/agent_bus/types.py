from pathlib import Path
from typing import Any, Literal, TypedDict


EventType = Literal["handoff", "status", "decision", "blocker", "request-review", "ack"]
CommandStatus = Literal["ok", "warning", "blocked"]
MANIFEST_SCHEMA_VERSION = 1
MANAGED_STATIC_FILES = (
    Path("agent-bus.json"),
    Path("AGENT_BUS.md"),
    Path(".githooks/pre-commit"),
    Path(".agents/README.md"),
    Path(".agents/protocol.md"),
    Path(".agents/templates/message-template.json"),
    Path("docs/coordination/README.md"),
)
BOOTSTRAP_MUTABLE_FILES = (
    Path(".agents/events.jsonl"),
    Path(".agents/registry.json"),
    Path("docs/coordination/active-context.md"),
    Path("docs/coordination/decision-log.md"),
    Path("docs/coordination/session-handoff.md"),
)


class Paths(TypedDict):
    repo_root: Path
    agents_dir: Path
    events_path: Path
    registry_path: Path
    inbox_dir: Path
    runtime_dir: Path
    ops_log_path: Path
    bus_lock_path: Path
    handoff_path: Path
    active_context_path: Path
    gitignore_path: Path
    manifest_path: Path
    start_doc_path: Path


Event = TypedDict(
    "Event",
    {
        "id": str,
        "timestamp": str,
        "type": EventType,
        "from": str,
        "to": str,
        "issue": str,
        "branch": str,
        "summary": str,
        "next_steps": list[str],
        "action_required": bool,
    },
)


HandoffSummary = TypedDict(
    "HandoffSummary",
    {
        "from": str,
        "to": str,
        "summary": str,
    },
)


class Registry(TypedDict):
    version: int
    last_event_id: str | None
    last_updated: str | None
    active_issue: str | None
    active_branch: str | None
    last_handoff: HandoffSummary | None


class AckRecord(TypedDict):
    agent: str
    last_seen_event_id: str
    acknowledged_at: str


class OpsLogEntry(TypedDict):
    timestamp: str
    command: str
    status: CommandStatus
    details: dict[str, Any]


class ManifestLogs(TypedDict):
    ops: str


class Manifest(TypedDict):
    name: str
    version: str
    schema_version: int
    classification: str
    runtime_role: str
    distribution_role: str
    repo_footprint: str
    purpose: str
    entrypoint: str
    managed_static_files: list[str]
    protocol_files: list[str]
    startup_command: str
    publish_command: str
    ack_command: str
    watch_command: str
    pre_commit_command: str
    doctor_command: str
    logs: ManifestLogs
