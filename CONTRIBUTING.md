# Contributing

## Scope

ConHugo Agents Flow is development-process tooling for human and agent coordination.

Contributions should preserve that boundary:

- do not turn this into product runtime middleware
- do not mix domain-specific logic into the reusable core
- prefer repo-agnostic workflow primitives over project-specific policy

## Local Setup

```bash
python -m venv .venv
. .venv/Scripts/activate
python -m pip install --upgrade pip build
```

Tests:

```bash
python -m unittest discover -s tests -v
```

Optional build check:

```bash
python -m build
```

## Development Rules

- keep the reusable implementation under `src/agent_bus/`
- treat templates as part of the public upgrade surface
- avoid breaking installed repo footprints without an explicit migration story
- preserve live repo state during `install --upgrade`
- keep new commands and manifest fields covered by tests

## Versioning

- package version is sourced from `src/agent_bus/__init__.py`
- use SemVer
- update `CHANGELOG.md` for every release-worthy change
- if a change affects installed repos, document the expected upgrade path
- keep roadmap-significant work linked to `ROADMAP.md` and the matching GitHub issue

## Release Flow

1. Update `src/agent_bus/__init__.py`
2. Update `CHANGELOG.md`
3. Merge to `main`
4. Create and push a tag like `v0.1.1`
5. GitHub Actions will create a GitHub Release with generated notes for that tag
6. GitHub Actions will run CI, build artifacts, and publish to the live PyPI project on the tag
7. Confirm the package page shows the new version at `https://pypi.org/project/conhugo-agents-flow/`
8. Use manual dispatch only when you need an out-of-band publish run, such as re-running `target=pypi`

## Publishing Configuration

- production publishing is active through PyPI trusted publishing
- current trusted publisher owner: `cervantesh`
- current trusted publisher repository: `conhugo-agents-flow`
- current trusted publisher workflow: `publish.yml`
- current trusted publisher environment: `pypi`
- TestPyPI publishing is disabled by default to avoid false CI/CD failures on unconfigured environments
- to enable TestPyPI, register a trusted publisher for the `testpypi` environment and set repository variable `TEST_PYPI_PUBLISHING_ENABLED=true`
