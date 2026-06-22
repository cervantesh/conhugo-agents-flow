# Agent Bus

Este directorio implementa un bus simple de comunicacion entre agentes.

## Objetivo

Permitir que varios agentes:

- publiquen actualizaciones durables
- detecten si hay mensajes nuevos
- reconozcan que ya leyeron
- bloqueen commits si hay mensajes pendientes

## Archivos

- `events.jsonl`: stream maquina-legible de eventos entre agentes
- `registry.json`: estado agregado actual
- `protocol.md`: reglas operativas
- `templates/message-template.json`: ejemplo de payload
- `inbox/`: acuses de lectura por agente, no se versiona
- `runtime/`: archivos temporales locales, no se versionan

## Flujo

1. Un agente publica una actualizacion con `agent-bus publish`.
2. El evento se agrega a `events.jsonl` y actualiza `registry.json`.
3. Otro agente ejecuta `agent-bus check` o `agent-bus watch`.
4. Cuando procesa el mensaje, ejecuta `agent-bus ack`.
5. Si existen mensajes pendientes, el hook `pre-commit` puede bloquear el commit.
