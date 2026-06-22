# ConHugo Agents Flow

Open source tooling for coordinating humans and agents while they work inside Git repositories.

[PyPI package](https://pypi.org/project/conhugo-agents-flow/) | [GitHub repository](https://github.com/cervantesh/conhugo-agents-flow) | [GitHub releases](https://github.com/cervantesh/conhugo-agents-flow/releases)

See [ROADMAP.md](C:/dev/conhugo-agents-flow/ROADMAP.md) for the phased improvement plan and linked GitHub backlog.
See [ADOPTION_GUIDE.md](C:/dev/conhugo-agents-flow/ADOPTION_GUIDE.md) for how to roll ConHugo into a real target repository.

`ConHugo Agents Flow` is not product runtime code. It is development-process tooling: durable handoffs, shared working memory, anti-drift checks, and upgradeable repo-local coordination artifacts.

## What It Does

- publishes durable machine-readable events between agents
- keeps repo-local coordination state under `.agents/` and `docs/coordination/`
- blocks commits when action-required updates are unread
- installs and upgrades managed repo artifacts
- validates installation health and version drift with `doctor`

## What It Is Not

- not business logic
- not application runtime
- not deployment runtime
- not customer-facing functionality
- not product telemetry

## Installation

```bash
pip install conhugo-agents-flow
```

Published package:

- PyPI: `conhugo-agents-flow`
- Maintainer account: `cervantesh`

## Basic Usage

Bootstrap a target repository:

```bash
conhugo-agents-flow install --repo-root /path/to/repo
```

Upgrade a target repository to the current version:

```bash
conhugo-agents-flow install --repo-root /path/to/repo --upgrade
conhugo-agents-flow doctor --repo-root /path/to/repo
```

Core commands:

```bash
conhugo-agents-flow publish --repo-root /path/to/repo --from codex-a --to codex-b --issue 12 --branch feat/12-x --summary "Ready for review" --action-required
conhugo-agents-flow check --repo-root /path/to/repo --agent codex-b
conhugo-agents-flow ack --repo-root /path/to/repo --agent codex-b
conhugo-agents-flow doctor --repo-root /path/to/repo
```

The legacy alias `agent-bus` is also exposed as a CLI entrypoint.

## Repo Footprint

A target repository may contain a local coordination instance with:

- `.agents/`
- `docs/coordination/`
- `agent-bus.json`
- `AGENT_BUS.md`
- `.githooks/`
- a thin wrapper script

That footprint is process infrastructure only. It is not shipped product code.

## Versioning and Upgrades

- package version comes from `src/agent_bus/__init__.py`
- installed repos record the current package version in `agent-bus.json`
- `doctor` detects version drift and missing managed files
- `install --upgrade` refreshes only managed static files and preserves live repo state like event streams and active handoffs

## Current Hardening

- atomic writes for registry, acks, manifest, and generated docs
- lock files for mutating operations and ops-log writes
- managed static file inventory in the manifest
- installation health checks through `doctor`
- unit tests for bootstrap, publish/check/ack, upgrade behavior, doctor, and lock contention

## Development

Run tests:

```bash
python -m unittest discover -s tests -v
```

Build artifacts:

```bash
python -m pip install build
python -m build
```

## Release

- update `src/agent_bus/__init__.py`
- update `CHANGELOG.md`
- push a tag like `v0.1.1`
- GitHub automatically creates a GitHub Release with generated notes for every `v*` tag
- GitHub Actions will build, validate, and publish to PyPI automatically on version tags
- PyPI production publishing is active for `cervantesh/conhugo-agents-flow` via `publish.yml` and environment `pypi`
- manual dispatch of the publish workflow remains available for `target=pypi`
- the `testpypi` target is gated and skips cleanly unless `TEST_PYPI_PUBLISHING_ENABLED=true` is configured after registering a trusted publisher for the `testpypi` environment

See [CONTRIBUTING.md](C:/dev/conhugo-agents-flow/CONTRIBUTING.md) for the development and release flow.

## License

MIT
