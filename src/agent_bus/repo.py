import re
from pathlib import Path

from agent_bus.types import Paths


def ensure_repo_paths(repo_root: Path) -> Paths:
    return {
        "repo_root": repo_root,
        "agents_dir": repo_root / ".agents",
        "events_path": repo_root / ".agents" / "events.jsonl",
        "registry_path": repo_root / ".agents" / "registry.json",
        "inbox_dir": repo_root / ".agents" / "inbox",
        "runtime_dir": repo_root / ".agents" / "runtime",
        "ops_log_path": repo_root / ".agents" / "runtime" / "ops.jsonl",
        "bus_lock_path": repo_root / ".agents" / "runtime" / "agent-bus.lock",
        "handoff_path": repo_root / "docs" / "coordination" / "session-handoff.md",
        "active_context_path": repo_root / "docs" / "coordination" / "active-context.md",
        "gitignore_path": repo_root / ".gitignore",
        "manifest_path": repo_root / "agent-bus.json",
        "start_doc_path": repo_root / "AGENT_BUS.md",
    }


def parse_repo_root(value: str) -> Path:
    repo_root = Path(value).resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        raise SystemExit(f"Invalid --repo-root: {repo_root}")
    return repo_root


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def validate_agent_name(agent: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", agent):
        raise SystemExit(
            "Invalid agent name. Use only letters, numbers, dot, underscore, or hyphen, max 64 chars."
        )
    return agent


def relative_paths(items: tuple[Path, ...] | list[Path]) -> list[str]:
    return [item.as_posix() for item in items]
