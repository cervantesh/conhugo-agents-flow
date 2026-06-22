# Decision Log

## D-0001

- Date: 2026-06-22
- Status: accepted
- Context: The project will be worked on by more than one agent and at least two humans.
- Decision: Use Git issues as external requirement records and local Markdown artifacts as durable agent memory.
- Consequences:
  - Every meaningful task should map to an issue.
  - Each issue should have a local spec mirror under `docs/specs/`.
  - Handoffs and architectural decisions must be written to the repo.
