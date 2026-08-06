---
name: ai-stack-architect
description: Crea la estructura del "$0 AI Architecture Stack" (frontend, orquestador de agentes, RAG, LLM local, MCP, memoria/caché, guardrails/evals, observabilidad, deployment con herramientas gratuitas u open source) o audita un proyecto existente contra esas 12 capas generando un informe de gaps priorizado. Usar cuando el usuario diga "crea el stack de IA", "monta la arquitectura de IA", "audita nuestra arquitectura de IA", "qué capas de IA nos faltan", "compara nuestro stack con el $0 stack", o pida scaffolding o gap analysis de una app de IA.
---

# AI Stack Architect ($0 AI Architecture Stack)

Dos modos. Decidir por la petición del usuario; si es ambigua y ya existe
código en el proyecto, usar **Auditar**.

La referencia canónica de las 12 capas (herramientas gratuitas, heurísticas
de detección y preguntas de auditoría) está en [STACK.md](STACK.md).
Para auditar o crear agentes individuales (`.claude/agents/*.md`), usar la
plantilla y checklist de [AGENTS.md](AGENTS.md).

## Modo Auditar (proyecto existente)

1. **Inventariar sin modificar nada**: leer `requirements.txt`/`package.json`,
   imports, Dockerfiles, configs y CLAUDE.md. Identificar qué es el proyecto
   (CLI, API, web app) — eso determina qué capas aplican.
2. **Mapear cada capa** de STACK.md contra la evidencia encontrada, usando
   sus heurísticas de detección. Asignar estado:
   - ✅ Cubierta (nombrar el componente concreto encontrado)
   - ⚠️ Parcial (existe algo pero con hueco claro; decir cuál)
   - ❌ Ausente y relevante para este proyecto
   - N/A No aplica a este tipo de proyecto (justificar en una frase)
3. **No inflar**: un CLI batch no necesita frontend ni orquestador multi-agente.
   Marcar N/A es un resultado válido; recomendar tecnología innecesaria es un
   fallo de la auditoría.
4. **Informe final** con: tabla de las 12 capas (capa, estado, evidencia),
   los 3-5 gaps más importantes priorizados por impacto/esfuerzo, y para cada
   uno la opción gratuita concreta de STACK.md con el primer paso accionable.
5. No tocar código en este modo salvo que el usuario pida aplicar mejoras.

## Modo Crear (proyecto nuevo o capa nueva)

1. **Alcance primero**: preguntar (o inferir del contexto) qué tipo de app es
   y qué capas necesita de verdad. Proponer el subconjunto mínimo, no las 12.
2. **Scaffolding por capa** siguiendo el orden de dependencias:
   LLM/RAG → orquestador → memoria → guardrails → observabilidad → frontend
   → deployment. Para cada capa elegida, usar la opción por defecto de
   STACK.md salvo preferencia explícita del usuario.
3. Generar estructura de carpetas, configs mínimos (`docker-compose.yml`,
   `.env.example`, config del orquestador) y un README con cómo arrancar
   cada pieza. Dependencias en `requirements.txt`/`package.json`, versiones
   sin fijar salvo petición.
4. **Verificar**: cada pieza scaffoldeada debe arrancar en local o tener un
   smoke test documentado; no entregar configs sin probar su sintaxis
   (p. ej. `docker compose config`, `python -c "import ..."`).

## Reglas comunes

- Solo herramientas gratuitas u open source; si una capa exige pago para el
  caso de uso real, decirlo explícitamente en vez de ocultarlo.
- "Gratis" no incluye el hardware: avisar de requisitos de GPU/VRAM al
  proponer LLM local (p. ej. Llama 70B no corre en un portátil normal).
- Respetar las reglas del proyecto anfitrión (en este repo:
  `.claude/rules/code-style.md` — cambios mínimos, nada fuera de lo pedido).
