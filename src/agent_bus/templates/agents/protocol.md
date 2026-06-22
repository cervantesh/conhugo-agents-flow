# Agent Communication Protocol

## Principle

Los agentes no deben depender de memoria de chat compartida.

La comunicacion oficial entre agentes ocurre por:

1. `.agents/events.jsonl`
2. `.agents/registry.json`
3. `docs/coordination/session-handoff.md`
4. `docs/coordination/active-context.md`

## Event Types

- `handoff`: transferencia de contexto
- `status`: progreso intermedio
- `decision`: cambio de decision o supuesto
- `blocker`: impedimento que requiere atencion
- `request-review`: solicitud explicita a otro agente
- `ack`: acuse de lectura

## Required Fields

- `id`
- `timestamp`
- `type`
- `from`
- `to`
- `issue`
- `branch`
- `summary`
- `next_steps`
- `action_required`

## Rules

1. Si un agente cambia el contexto de trabajo, debe publicar un evento.
2. Si `action_required` es `true`, el destinatario debe releer antes de seguir.
3. Ningun agente debe commitear si tiene eventos pendientes con `action_required=true`.
4. Toda decision duradera debe reflejarse tambien en `docs/coordination/decision-log.md` cuando aplique.
5. El handoff humano en Markdown debe resumir el ultimo evento importante.

## Startup Contract

Al comenzar una sesion, el agente debe:

1. verificar eventos pendientes
2. leer `active-context.md`
3. leer `session-handoff.md`
4. leer el spec del issue activo

## Automation Contract

Para minimizar drift:

- configurar `core.hooksPath` a `.githooks`
- usar `agent-bus watch` en una terminal separada
- usar `pre-commit` para bloquear commits con mensajes pendientes
