# Guia de Adopcion de ConHugo

## Proposito

Esta guia explica como adoptar `ConHugo Agents Flow` dentro de un repositorio real sin confundirlo con codigo de producto.

`ConHugo` es tooling del proceso de desarrollo para coordinacion entre humanos y agentes. Su objetivo es dejar contexto durable dentro del repo, reducir drift y hacer mas disciplinado el trabajo compartido.

## Que te da ConHugo

Cuando adoptas `ConHugo`, agregas una capa local de coordinacion al repo con:

- handoffs durables entre humanos y agentes
- contexto activo dentro del repo
- historial de eventos maquina-legible
- chequeo de mensajes pendientes
- validacion de salud con `doctor`
- artefactos de coordinacion actualizables

## Que no te da

`ConHugo` no es:

- logica de negocio
- runtime de la aplicacion
- runtime de despliegue
- funcionalidad para clientes finales
- telemetria del producto

## Modelo recomendado de adopcion

Piensalo en tres capas:

### 1. Capa reusable de ConHugo

Es el paquete o tooling reusable.

Responsabilidades:

- protocolo de eventos
- comandos de coordinacion
- disciplina de trabajo reusable
- checks reusables
- templates reusables

### 2. Instancia local de ConHugo en el repo

Es la huella que ConHugo deja dentro del repo destino.

Archivos tipicos:

- `.agents/`
- `docs/coordination/`
- `agent-bus.json`
- `AGENT_BUS.md`
- `.githooks/`

Responsabilidades:

- estado vivo de coordinacion
- handoffs activos
- memoria de trabajo compartida
- enforcement local del flujo

### 3. Verdad del repo de producto

Esto se queda en el repo destino y no pertenece al core de ConHugo.

Ejemplos:

- requerimientos del producto
- decisiones de arquitectura
- reglas del dominio
- specs por issue
- politicas del negocio

## Instalacion

Instala el paquete:

```bash
pip install conhugo-agents-flow
```

Inicializa un repo:

```bash
conhugo-agents-flow install --repo-root /ruta/al/repo
```

Valida la instalacion:

```bash
conhugo-agents-flow doctor --repo-root /ruta/al/repo
```

## Primer uso dentro de un repo

Despues de instalar:

1. leer `AGENT_BUS.md`
2. leer `agent-bus.json`
3. leer `docs/coordination/active-context.md`
4. definir nombre de agente en el shell o entorno
5. ejecutar `check` antes de empezar

Ejemplo:

```bash
export AGENT_NAME=codex-a
conhugo-agents-flow check --repo-root /ruta/al/repo --agent "$AGENT_NAME"
```

## Flujo diario recomendado

1. elegir un issue
2. leer contexto activo y specs relevantes
3. ejecutar `check`
4. hacer el trabajo
5. publicar handoff o status
6. hacer `ack` de lo procesado
7. dejar el repo en un estado de cierre claro

Ejemplo de `publish`:

```bash
conhugo-agents-flow publish \
  --repo-root /ruta/al/repo \
  --from codex-a \
  --to codex-b \
  --issue 12 \
  --branch feat/12-scope \
  --summary "Las notas de discovery quedaron listas para revision." \
  --next-step "Revisar supuestos" \
  --next-step "Actualizar spec del issue" \
  --action-required
```

## Reglas de trabajo que encajan bien con ConHugo

ConHugo funciona mejor cuando el repo sigue estas disciplinas:

- el trabajo importante mapea a issues
- existen specs locales para tareas relevantes
- las decisiones no viven solo en chat
- cada sesion termina como `done`, `blocked` o `handoff-required`
- los cambios sensibles dejan artefactos durables en docs, specs o decision logs

## Documentos recomendados en el repo destino

ConHugo se vuelve mucho mas fuerte cuando el repo tiene:

- vision de producto
- requerimientos del proyecto
- docs de arquitectura y ADRs
- specs por issue
- decision log
- handoff log

## Actualizaciones

Para refrescar los artefactos administrados:

```bash
conhugo-agents-flow install --repo-root /ruta/al/repo --upgrade
conhugo-agents-flow doctor --repo-root /ruta/al/repo
```

Eso actualiza archivos estaticos administrados sin borrar el estado vivo del repo, como eventos o handoffs.

## Cuando conviene adoptarlo

Usa `ConHugo` cuando:

- mas de un humano o agente toca el repo
- los handoffs importan
- el contexto se esta perdiendo en chat
- una memoria local en el repo reduciria errores
- quieres disciplina de trabajo repetible

## Cuando puede ser demasiado

Puede ser innecesario cuando:

- una sola persona trabaja sola en un repo muy pequeno
- no hay handoffs
- el trabajo es desechable

## Glosario

Ver [glosario-es.md](C:/dev/conhugo-agents-flow/docs/glosario-es.md).

## Resumen

Adopta `ConHugo` como infraestructura de proceso dentro del repo que estas construyendo.

No lo trates como codigo de producto.

Deja que `ConHugo` defina como se coordina el trabajo, mientras el repo destino define que producto se esta construyendo.
