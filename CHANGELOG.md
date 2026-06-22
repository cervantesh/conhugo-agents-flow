# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and this project follows Semantic Versioning.

## [0.1.1] - 2026-06-22

### Added

- live PyPI publication for `conhugo-agents-flow` under the `cervantesh` maintainer account
- trusted-publishing documentation for the repo release discipline

### Fixed

- removed the deprecated MIT license classifier that broke package builds in GitHub Actions
- changed the publish workflow so tag pushes build and validate artifacts without failing on unconfigured PyPI publishing
- gated the `testpypi` publish path so it skips cleanly unless that environment is explicitly enabled

### Changed

- version tags now publish to live PyPI automatically through the configured trusted publisher
- manual publish dispatch remains available for `pypi` reruns and optional `testpypi` usage
- package metadata now declares `license-files = ["LICENSE"]`

## [0.1.0] - 2026-06-22

### Added

- initial open source release of ConHugo Agents Flow
- durable agent event bus and repo-local coordination artifacts
- install, upgrade, doctor, publish, check, ack, watch, and pre-commit flows
- atomic writes for managed state and generated docs
- lock-file based protection for mutating operations and ops log writes
- managed static file inventory and version recording in `agent-bus.json`
- unit tests for bootstrap, publish/check/ack, doctor, upgrade behavior, and lock contention
