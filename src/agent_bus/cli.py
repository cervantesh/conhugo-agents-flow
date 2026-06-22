import argparse
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

from agent_bus import __version__
from agent_bus.locking import acquire_lock
from agent_bus.repo import ensure_repo_paths, parse_repo_root, validate_agent_name
from agent_bus.store import (
    append_event,
    bootstrap_repo,
    detect_repo_issues,
    load_registry,
    pending_events,
    rotate_ops_log_if_needed,
    save_ack,
    save_registry,
    write_human_context,
    write_manifest,
    write_ops_log,
    write_start_doc,
)
from agent_bus.types import Event, MANIFEST_SCHEMA_VERSION, Paths


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_mutation_with_lock(paths, operation_name: str, callback):
    try:
        with acquire_lock(paths["bus_lock_path"]):
            return callback()
    except TimeoutError as exc:
        print(f"{operation_name} failed: {exc}", file=sys.stderr)
        return 1


def cmd_install(args: argparse.Namespace) -> int:
    repo_root = parse_repo_root(args.repo_root)
    paths = ensure_repo_paths(repo_root)

    def mutation() -> int:
        bootstrap_repo(repo_root, upgrade=args.upgrade)
        write_manifest(paths)
        write_start_doc(paths)
        try:
            subprocess.run(["git", "-C", str(repo_root), "config", "core.hooksPath", ".githooks"], check=True)
        except subprocess.CalledProcessError as exc:
            print(f"Installed agent-bus assets into {repo_root}")
            print("Warning: assets were installed, but git hooks were not configured yet.")
            print(f"Git reported: {exc}", file=sys.stderr)
            print("Run this command again after `git init` or inside a valid Git repository.")
            write_ops_log(
                paths,
                "install",
                "warning",
                {"repo_root": str(repo_root), "git_configured": False, "upgrade": args.upgrade},
                utc_now(),
            )
            return 0
        print(f"Installed agent-bus assets into {repo_root}")
        print("Configured git hooks path to .githooks")
        write_ops_log(
            paths,
            "install",
            "ok",
            {"repo_root": str(repo_root), "git_configured": True, "upgrade": args.upgrade},
            utc_now(),
        )
        return 0

    return run_mutation_with_lock(paths, "install", mutation)


def cmd_publish(args: argparse.Namespace) -> int:
    paths = ensure_repo_paths(parse_repo_root(args.repo_root))
    validate_agent_name(args.from_agent)
    if args.to != "all":
        validate_agent_name(args.to)

    def mutation() -> int:
        event: Event = {
            "id": str(uuid.uuid4()),
            "timestamp": utc_now(),
            "type": args.type,
            "from": args.from_agent,
            "to": args.to,
            "issue": args.issue,
            "branch": args.branch,
            "summary": args.summary,
            "next_steps": args.next_steps or [],
            "action_required": args.action_required,
        }
        append_event(paths, event)

        registry = load_registry(paths)
        registry["last_event_id"] = event["id"]
        registry["last_updated"] = event["timestamp"]
        registry["active_issue"] = event["issue"]
        registry["active_branch"] = event["branch"]
        registry["last_handoff"] = {
            "from": event["from"],
            "to": event["to"],
            "summary": event["summary"],
        }
        save_registry(paths, registry)
        write_human_context(paths, event)
        write_ops_log(
            paths,
            "publish",
            "ok",
            {
                "event_id": event["id"],
                "from": event["from"],
                "to": event["to"],
                "issue": event["issue"],
                "action_required": event["action_required"],
            },
            utc_now(),
        )
        print(f'Published event {event["id"]} for {event["to"]}')
        return 0

    return run_mutation_with_lock(paths, "publish", mutation)


def cmd_check(args: argparse.Namespace) -> int:
    paths = ensure_repo_paths(parse_repo_root(args.repo_root))
    validate_agent_name(args.agent)
    pending = pending_events(paths, args.agent)
    if not pending:
        write_ops_log(paths, "check", "ok", {"agent": args.agent, "pending_count": 0}, utc_now())
        print(f"No pending updates for {args.agent}")
        return 0

    print(f"Pending updates for {args.agent}:")
    for event in pending:
        print(
            f'- [{event["type"]}] {event["id"]} from {event["from"]} '
            f'issue={event["issue"]} action_required={event["action_required"]}'
        )
        print(f'  {event["summary"]}')

    if args.fail_on_pending and any(event["action_required"] for event in pending):
        write_ops_log(paths, "check", "blocked", {"agent": args.agent, "pending_count": len(pending)}, utc_now())
        print(f"There are action-required updates pending for {args.agent}.", file=sys.stderr)
        return 1
    write_ops_log(paths, "check", "ok", {"agent": args.agent, "pending_count": len(pending)}, utc_now())
    return 0


def cmd_ack(args: argparse.Namespace) -> int:
    paths = ensure_repo_paths(parse_repo_root(args.repo_root))
    validate_agent_name(args.agent)

    def mutation() -> int:
        pending = pending_events(paths, args.agent)
        if not pending:
            write_ops_log(paths, "ack", "ok", {"agent": args.agent, "acked": None}, utc_now())
            print(f"No pending updates to acknowledge for {args.agent}")
            return 0

        last_event_id = pending[-1]["id"]
        timestamp = utc_now()
        save_ack(paths, args.agent, last_event_id, timestamp)
        write_ops_log(paths, "ack", "ok", {"agent": args.agent, "acked": last_event_id}, timestamp)
        print(f"{args.agent} acknowledged {last_event_id}")
        return 0

    return run_mutation_with_lock(paths, "ack", mutation)


def cmd_watch(args: argparse.Namespace) -> int:
    paths = ensure_repo_paths(parse_repo_root(args.repo_root))
    validate_agent_name(args.agent)
    print(f"Watching for updates for {args.agent} every {args.poll_seconds} seconds. Press Ctrl+C to stop.")
    write_ops_log(paths, "watch", "ok", {"agent": args.agent, "poll_seconds": args.poll_seconds}, utc_now())
    last_output = None
    while True:
        pending = pending_events(paths, args.agent)
        if pending:
            lines = [f"Pending updates for {args.agent}:"]
            for event in pending:
                lines.append(
                    f'- [{event["type"]}] {event["id"]} from {event["from"]} '
                    f'issue={event["issue"]} action_required={event["action_required"]}'
                )
                lines.append(f'  {event["summary"]}')
            output = "\n".join(lines)
        else:
            output = f"No pending updates for {args.agent}"

        if output != last_output:
            last_output = output
            print()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            print(output)

        time.sleep(args.poll_seconds)


def cmd_pre_commit_check(args: argparse.Namespace) -> int:
    agent = os.environ.get("AGENT_NAME", "").strip()
    if not agent:
        print("AGENT_NAME is not set. Skipping unread-update gate.")
        return 0
    validate_agent_name(agent)
    check_args = argparse.Namespace(repo_root=args.repo_root, agent=agent, fail_on_pending=True)
    return cmd_check(check_args)


def cmd_doctor(args: argparse.Namespace) -> int:
    paths = ensure_repo_paths(parse_repo_root(args.repo_root))
    issues = detect_repo_issues(paths)
    if not issues:
        print(f"agent-bus doctor: OK ({__version__})")
        write_ops_log(paths, "doctor", "ok", {"issue_count": 0, "version": __version__}, utc_now())
        return 0

    print("agent-bus doctor found issues:")
    for issue in issues:
        print(f"- {issue}")
    write_ops_log(paths, "doctor", "blocked", {"issue_count": len(issues), "version": __version__}, utc_now())
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent communication bus")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install = subparsers.add_parser("install", help="Install bus assets into a repo")
    install.add_argument("--repo-root", default=".")
    install.add_argument("--upgrade", action="store_true", help="Refresh managed static assets to current version")
    install.set_defaults(func=cmd_install)

    publish = subparsers.add_parser("publish", help="Publish a handoff or status event")
    publish.add_argument("--repo-root", default=".")
    publish.add_argument("--from", dest="from_agent", required=True)
    publish.add_argument("--to", required=True)
    publish.add_argument("--issue", required=True)
    publish.add_argument("--branch", required=True)
    publish.add_argument("--summary", required=True)
    publish.add_argument(
        "--type",
        default="handoff",
        choices=["handoff", "status", "decision", "blocker", "request-review"],
    )
    publish.add_argument("--next-step", dest="next_steps", action="append", default=[])
    publish.add_argument("--action-required", action="store_true")
    publish.set_defaults(func=cmd_publish)

    check = subparsers.add_parser("check", help="Check for unread events")
    check.add_argument("--repo-root", default=".")
    check.add_argument("--agent", required=True)
    check.add_argument("--fail-on-pending", action="store_true")
    check.set_defaults(func=cmd_check)

    ack = subparsers.add_parser("ack", help="Acknowledge latest unread event")
    ack.add_argument("--repo-root", default=".")
    ack.add_argument("--agent", required=True)
    ack.set_defaults(func=cmd_ack)

    watch = subparsers.add_parser("watch", help="Poll for updates")
    watch.add_argument("--repo-root", default=".")
    watch.add_argument("--agent", required=True)
    watch.add_argument("--poll-seconds", type=int, default=10)
    watch.set_defaults(func=cmd_watch)

    pre_commit = subparsers.add_parser("pre-commit-check", help="Git hook entrypoint")
    pre_commit.add_argument("--repo-root", default=".")
    pre_commit.set_defaults(func=cmd_pre_commit_check)

    doctor = subparsers.add_parser("doctor", help="Validate installation health and version alignment")
    doctor.add_argument("--repo-root", default=".")
    doctor.set_defaults(func=cmd_doctor)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
