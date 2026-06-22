# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and this project follows Semantic Versioning.

## [0.1.0] - 2026-06-22

### Added

- initial open source release of ConHugo Agents Flow
- durable agent event bus and repo-local coordination artifacts
- install, upgrade, doctor, publish, check, ack, watch, and pre-commit flows
- atomic writes for managed state and generated docs
- lock-file based protection for mutating operations and ops log writes
- managed static file inventory and version recording in `agent-bus.json`
- unit tests for bootstrap, publish/check/ack, doctor, upgrade behavior, and lock contention
