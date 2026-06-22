# ConHugo Adoption Guide

## Purpose

This guide explains how to adopt `ConHugo Agents Flow` in a real repository without confusing it with product runtime code.

`ConHugo` is development-process tooling for human-agent coordination. It helps teams keep durable context, reduce drift, and enforce shared workflow discipline inside a repo.

## What You Get

When you adopt `ConHugo`, you get a repo-local coordination layer with:

- durable handoffs between humans and agents
- active context inside the repo
- machine-readable event history
- unread-update checks
- repo health checks through `doctor`
- upgradeable coordination artifacts

## What You Do Not Get

`ConHugo` is not:

- business logic
- product runtime
- deployment runtime
- customer-facing functionality
- application telemetry

## Recommended Adoption Model

Use this split:

### 1. ConHugo reusable layer

This is the package/tooling itself.

Responsibilities:

- event protocol
- coordination commands
- shared workflow discipline
- reusable checks
- reusable templates

### 2. Repo-local ConHugo instance

This is the footprint created inside the target repo.

Typical files:

- `.agents/`
- `docs/coordination/`
- `agent-bus.json`
- `AGENT_BUS.md`
- `.githooks/`

Responsibilities:

- live coordination state
- active handoffs
- shared working memory
- repo-local workflow enforcement

### 3. Product repo truth

This stays in the target repo and is not part of ConHugo core.

Examples:

- product requirements
- architecture decisions
- domain rules
- issue specs
- business policies

## Installation

Install the package:

```bash
pip install conhugo-agents-flow
```

Bootstrap a repo:

```bash
conhugo-agents-flow install --repo-root /path/to/repo
```

Validate the installation:

```bash
conhugo-agents-flow doctor --repo-root /path/to/repo
```

## First-Time Setup in a Repo

After install, do this:

1. Read `AGENT_BUS.md`
2. Read `agent-bus.json`
3. Read `docs/coordination/active-context.md`
4. Configure an agent name in your shell or environment
5. Run `check` before starting work

Example:

```bash
export AGENT_NAME=codex-a
conhugo-agents-flow check --repo-root /path/to/repo --agent "$AGENT_NAME"
```

## Daily Workflow

Recommended flow:

1. pick an issue
2. read active context and relevant specs
3. run `check`
4. do the work
5. publish a handoff or status update
6. acknowledge processed updates
7. leave the repo in a clear closure state

Example publish:

```bash
conhugo-agents-flow publish \
  --repo-root /path/to/repo \
  --from codex-a \
  --to codex-b \
  --issue 12 \
  --branch feat/12-scope \
  --summary "Discovery notes are ready for review." \
  --next-step "Review assumptions" \
  --next-step "Update issue spec" \
  --action-required
```

## Working Rules That Fit ConHugo Best

ConHugo works best when the target repo follows these disciplines:

- important work maps to an issue
- local specs exist for meaningful tasks
- decisions do not live only in chat
- sessions end as `done`, `blocked`, or `handoff-required`
- architecture-sensitive changes leave durable artifacts in docs/specs/decision logs

## Recommended Repo Docs

ConHugo is stronger when the target repo has:

- product vision
- project requirements
- architecture docs and ADRs
- issue-local specs
- decision log
- handoff log

## Upgrade Guidance

Refresh managed coordination artifacts:

```bash
conhugo-agents-flow install --repo-root /path/to/repo --upgrade
conhugo-agents-flow doctor --repo-root /path/to/repo
```

This upgrades managed static assets while preserving live repo state such as event streams and handoff history.

## When to Use It

Use `ConHugo` when:

- more than one human or agent touches the repo
- handoffs matter
- context is getting lost in chat
- repo-local working memory would reduce mistakes
- you want repeatable workflow discipline

## When It May Be Overkill

It may be unnecessary when:

- one person works alone in a tiny repo
- there are no handoffs
- the work is purely throwaway

## Summary

Adopt `ConHugo` as process infrastructure inside the repo you are building.

Do not treat it as product code.

Let `ConHugo` define how work is coordinated, while the target repo defines what product is being built.
