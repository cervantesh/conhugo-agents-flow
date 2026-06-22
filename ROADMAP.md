# Roadmap

ConHugo Agents Flow is still in an early alpha stage. The project already has a functioning install/bootstrap flow, a durable event stream, repo-local coordination artifacts, basic locking, a doctor command, tests, PyPI publishing, and release automation. The next job is not "add random features." The next job is to turn the current alpha into a disciplined, extensible coordination platform that teams can trust across multiple repositories and multiple agents.

This roadmap is intentionally opinionated:

- prioritize reliability before feature breadth
- keep the boundary clear between development-process tooling and product/runtime code
- optimize for low-drift multi-agent collaboration inside real repositories
- avoid repo-specific hacks in the reusable core
- treat upgradeability and operability as first-class concerns

## Current State

What already exists in `0.1.1`:

- repo bootstrap and upgrade flow
- local manifest and doctrinal boundary documents
- machine-readable event stream in `.agents/events.jsonl`
- ack and unread detection flow
- pre-commit unread gate
- repo-local docs updates for handoffs and active context
- atomic writes for several core files
- basic file locking for mutations and ops-log writes
- unit tests for bootstrap, install, publish/check/ack, doctor, upgrade, and lock contention
- GitHub release automation
- PyPI publishing via trusted publishing

What is still missing or underpowered:

- no explicit protocol version negotiation beyond a manifest schema integer
- no migration framework for installed repos across breaking footprint changes
- no stale-lock detection or lock recovery strategy
- append-only events are not protected against concurrent writers with stronger durability semantics
- no structured "status" or "list" command for machine consumption
- no JSON schema or documented contract for events, registry, acks, and manifest
- no config layer for team defaults, conventions, or policy tuning
- no plugin/extension model for repo-specific enforcement
- no integration-test matrix across Windows, macOS, and Linux behaviors
- no onboarding path for GitHub Issues, Projects, or PR workflows as first-class coordination surfaces

## Roadmap Structure

The roadmap is split into four delivery tracks:

1. Core reliability and protocol integrity
2. Operator ergonomics and team workflow integration
3. Ecosystem and automation surfaces
4. Release maturity toward `1.0`

Each phase below is meant to produce a materially stronger public artifact, not just more code.

## Phase 0.2 - Reliability and Protocol Hardening

Goal: make the current alpha trustworthy under repeated real-world use.

Backlog anchors:

- [#1](https://github.com/cervantesh/conhugo-agents-flow/issues/1) Harden event-store durability and corruption handling
- [#2](https://github.com/cervantesh/conhugo-agents-flow/issues/2) Harden lock lifecycle and stale-lock recovery
- [#3](https://github.com/cervantesh/conhugo-agents-flow/issues/3) Add schema validation and a migration framework for installed repos

### Outcomes

- safer concurrent access to mutable state
- better recovery from partial failures
- clearer protocol guarantees
- a stronger verification story for upgrades and installs

### Workstreams

#### 1. Event-store durability hardening

The current event stream appends JSON lines without a dedicated event-store abstraction or stronger write guarantees. That is acceptable for a small alpha, but it remains a risk area for concurrent or interrupted writes.

Targets:

- extract event-stream operations into a more explicit store abstraction
- define append invariants and corruption detection rules
- add event validation before writes
- add repair and recovery guidance for malformed log tails
- evaluate whether event appends should also use a dedicated lock

#### 2. Locking model hardening

The current lock is simple and useful, but it does not distinguish between healthy contention and abandoned lock files.

Targets:

- add stale-lock detection using age and process metadata
- add explicit lock-owner diagnostics
- add a safe `doctor` signal for abandoned locks
- add optional force-unlock flow with guardrails
- document concurrency boundaries per command

#### 3. Manifest and schema discipline

The project already records a manifest and schema version, but it still needs clearer guarantees around forward compatibility and migrations.

Targets:

- formalize schema evolution rules
- define what is breaking vs non-breaking in the repo footprint
- add manifest validation beyond presence checks
- version event, registry, and ack contracts more explicitly
- add machine-readable schema assets or contract docs

#### 4. Upgrade and migration discipline

`install --upgrade` is already useful, but it needs a migration story before the footprint evolves more aggressively.

Targets:

- classify files into immutable templates, generated mutable artifacts, and live state
- add explicit migration hooks for future breaking changes
- add upgrade safety checks and clearer upgrade output
- produce a compatibility matrix between package versions and repo schema versions

### Exit Criteria

- stronger corruption and lock diagnostics
- no known silent-failure paths in mutable state handling
- clearly documented compatibility rules
- upgrade path documented and tested for non-trivial changes

## Phase 0.3 - CLI Ergonomics and Workflow Depth

Goal: make the tool easier to consume quickly by both humans and agents.

Backlog anchors:

- [#4](https://github.com/cervantesh/conhugo-agents-flow/issues/4) Add machine-readable CLI output and repo status commands
- [#5](https://github.com/cervantesh/conhugo-agents-flow/issues/5) Deepen onboarding, upgrade, and recovery documentation

### Outcomes

- better discoverability
- more machine-friendly command outputs
- less need to read source code to use the tool correctly

### Workstreams

#### 1. Machine-readable command outputs

Right now the CLI is primarily human-oriented. Agents benefit from stable structured output.

Targets:

- add `--json` support to key commands
- standardize exit codes across normal, warning, and blocked states
- add compact structured summaries for `check`, `doctor`, and `install`
- keep human output readable while making machine parsing stable

#### 2. Missing operational commands

There are notable gaps in the operator surface.

Targets:

- add `status` command for repo coordination summary
- add `history` command for recent events and handoffs
- add `tail` or `watch --once` style mode for automation compatibility
- add `validate` or `lint` command for manifests and docs footprint

#### 3. Better bootstrap ergonomics

Bootstrap should be faster for new users and more deterministic for agents.

Targets:

- improve install output with next-step guidance
- expose repo boundary warnings earlier
- support non-default wrapper generation patterns where needed
- document zero-to-first-handoff in a concise public example

#### 4. Documentation depth

The current docs are clear, but still minimal.

Targets:

- add protocol reference docs
- add upgrade/migration docs
- add examples for solo-agent, pair-agent, and swarm-lite workflows
- add a "consume quickly as an agent" section with exact expected reading order

### Exit Criteria

- agents can operate against the tool with less inferred behavior
- core commands have structured output modes
- operator docs cover first-run, day-2, and failure recovery paths

## Phase 0.4 - Team Integration and GitHub Workflow Surfaces

Goal: make the bus feel native inside issue-driven development rather than adjacent to it.

Backlog anchors:

- [#6](https://github.com/cervantesh/conhugo-agents-flow/issues/6) Define GitHub issue and project workflow integration

### Outcomes

- stronger alignment with Issues, PRs, and backlog flow
- lower coordination drift between repo state and GitHub state
- easier adoption across multiple repositories

### Workstreams

#### 1. GitHub issue integration

Issues are already the obvious planning surface for this project and for target repos.

Targets:

- document an issue-first workflow
- add optional issue metadata references in commands
- support richer issue context propagation into handoff docs
- consider templates for handoff-ready issue descriptions

#### 2. GitHub Projects integration

Projects should become a first-class coordination plane for planning and release discipline.

Targets:

- define a canonical GitHub Project structure for roadmap tracking
- map phases, epics, and backlog items to project status fields
- document how a repo owner should create and wire the project
- optionally add helper commands or scripts for project bootstrap in the future

#### 3. PR and review workflow integration

The current bus can hand off context, but it does not yet close the loop with PR review discipline.

Targets:

- define PR-ready handoff conventions
- support request-review events more deeply
- add docs for using bus events to drive review queues
- consider PR comment or status export helpers later

#### 4. Multi-repo adoption model

This tool exists to be reused. The adoption surface should be explicit.

Targets:

- add a target-repo adoption guide
- define minimal footprint vs full workflow modes
- document update cadence expectations for downstream repos
- provide stronger examples for monorepo and multi-repo environments

### Exit Criteria

- roadmap and backlog are tracked as first-class GitHub work items
- issue-first workflow is documented and operational
- teams can adopt the tool without reverse-engineering the intended process

## Phase 0.5 - Extensibility and Policy Surfaces

Goal: make the tool reusable across teams with different collaboration policies without forking the core.

Backlog anchors:

- [#7](https://github.com/cervantesh/conhugo-agents-flow/issues/7) Add repo-local config and policy extension surfaces

### Outcomes

- configurable team conventions
- less need for downstream patching
- clearer separation between protocol and policy

### Workstreams

#### 1. Config model

Targets:

- define repo-local config file semantics
- support defaults for agent names, branch conventions, issue conventions, and enforcement toggles
- allow teams to tune gating behavior without modifying package code

#### 2. Policy hooks

Targets:

- separate core coordination protocol from optional policy rules
- allow opt-in enforcement modules such as required issue IDs or required next steps
- keep extension points explicit and documented

#### 3. Template customization

Targets:

- support managed overrides for selected templates
- define safe customization boundaries
- keep upgrades predictable even when template overrides exist

### Exit Criteria

- downstream repos can adopt team-specific policy without forking the package
- customization does not destroy upgradeability

## Phase 0.6 - Cross-Platform and Integration Testing Depth

Goal: prove this works outside the happy path.

Backlog anchors:

- [#8](https://github.com/cervantesh/conhugo-agents-flow/issues/8) Expand cross-platform CI and integration fixture coverage

### Outcomes

- stronger public confidence
- lower risk of regressions across platforms
- better release confidence for PyPI consumers

### Workstreams

#### 1. Test matrix expansion

Targets:

- run tests across Windows, Linux, and macOS
- cover Python `3.11` and `3.12` consistently
- add tests for newline behavior and path handling

#### 2. Integration and fixture testing

Targets:

- add repo-fixture based integration tests
- test install-to-upgrade-to-doctor flows end-to-end
- test Git hook behavior more directly
- test corruption and stale-lock scenarios

#### 3. Release verification

Targets:

- add smoke-install tests from built artifacts
- validate console entrypoints from wheel installs
- consider TestPyPI publish path once explicitly enabled

### Exit Criteria

- broader CI matrix is green
- end-to-end scenarios cover the public contract, not only internal functions

## Phase 1.0 - General Availability Discipline

Goal: graduate from alpha tooling into a stable reusable coordination package.

Backlog anchors:

- [#9](https://github.com/cervantesh/conhugo-agents-flow/issues/9) Define the 1.0 stability and compatibility checklist

### Outcomes

- public contract clarity
- documented compatibility and migration rules
- release discipline strong enough for external adopters

### Requirements for 1.0

- stable protocol and schema rules
- migration story for repo footprints
- mature doctor/validation surface
- strong docs for install, operate, upgrade, and recover
- tested cross-platform behavior
- GitHub planning model documented and reproducible
- a clear support boundary for what the tool does and does not own

## Success Metrics

The roadmap should be judged by operational outcomes, not just merged code.

Suggested metrics:

- time from install to first valid handoff in a fresh repo
- number of ambiguous or undocumented failure states
- number of commands with stable machine-readable output
- number of downstream repos upgraded without manual repair
- number of CI failures caused by tool packaging/release friction
- amount of repo-specific customization required by adopters

## Backlog Discipline

The backlog should stay disciplined:

- use issues for epics and scoped deliverables
- link issues to roadmap phases explicitly
- keep one issue focused on one outcome
- avoid mixing protocol, policy, and packaging concerns in a single ticket
- close issues only when the public operator surface actually improves

## GitHub Project Tracking

This roadmap is designed to be tracked in a GitHub Project with:

- status columns or a status field such as `Backlog`, `Ready`, `In Progress`, `Done`
- roadmap phase fields such as `0.2`, `0.3`, `0.4`, `0.5`, `0.6`, `1.0`
- item type grouping such as `Epic`, `Feature`, `Hardening`, `Docs`, `Release`

If the GitHub auth context available to the maintainer lacks `project` scope, issue creation should still proceed first and the Project can be bootstrapped immediately after the token is refreshed.
