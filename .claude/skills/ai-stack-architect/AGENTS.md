# Auditoría individual de agentes (.claude/agents/*.md)

Complemento de la capa 8 de [STACK.md](STACK.md): esa capa comprueba que el
proyecto tenga agentes; esta checklist audita **cada agente uno a uno**.
También sirve como plantilla al crear un agente nuevo.

## Plantilla canónica

```md
---
name: nombre-del-agente
description: Qué hace + cuándo usarlo ("Usar cuando…"). Es lo único que ve el
  modelo para decidir invocarlo.
tools: Read, Grep, Glob, Bash   # opcional: restringe herramientas
model: haiku                    # opcional: modelo específico
---

System prompt del agente: rol, restricciones, pasos concretos y formato de
salida esperado.
```

No existe otra plantilla: todos los agentes usan esta estructura; lo que
cambia es el contenido del prompt.

## Checklist de auditoría (por agente)

Evaluar cada criterio como ✅ / ⚠️ / ❌ con evidencia (línea o campo concreto):

1. **Frontmatter completo**: `name` en kebab-case y `description` presente.
2. **Description con trigger**: dice qué hace Y cuándo invocarlo ("usar
   cuando…", "usar proactivamente tras…"). Una description vaga ("ayuda con
   informes") es ❌ aunque el prompt sea bueno: el agente nunca se invocará
   bien.
3. **Rol y restricciones explícitos en la primera frase** del prompt: qué es
   y qué NUNCA hace (p. ej. "solo lectura: nunca modificas ni borras").
4. **Pasos concretos y verificables**: instrucciones con comandos, rutas o
   patrones exactos, no "revisa que todo esté bien".
5. **Formato de salida definido**: el prompt dice qué devuelve (tabla,
   veredicto ✅/❌, JSON…) para que el agente principal pueda encadenarlo.
6. **Coherencia herramientas ↔ rol**: un agente "de solo lectura" con `Bash`
   o `Write` es ⚠️ — la garantía depende del prompt, no del harness. Si la
   restricción importa, blindar con reglas `deny` en `settings.json`.
7. **Modelo proporcionado a la tarea**: tareas mecánicas (auditorías,
   greps, validaciones) → fijar un modelo pequeño (`haiku`) abarata sin
   perder calidad; omitir `model` (heredar) solo si la tarea exige el modelo
   de la sesión.
8. **Sin duplicidad**: el agente no repite lo que ya hace un skill o comando
   existente; si se solapan, uno debe referenciar al otro (como
   `report-auditor` → skill `diagnose-report-failure`).
9. **Sin información volátil**: nada de fechas, versiones de modelos de pago
   o rutas de máquina personal dentro del prompt.

## Formato del informe

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1-9 | … | ✅/⚠️/❌ | línea o campo concreto |

Cerrar con: veredicto global (apto / apto con mejoras / rehacer) y, para
cada ⚠️/❌, el arreglo concreto en una línea.
