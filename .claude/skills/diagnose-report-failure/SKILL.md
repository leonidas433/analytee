---
name: diagnose-report-failure
description: Diagnostica fallos del pipeline de informes ORM (exit codes 10-13, QualityCheckError, OutputContractError, artefactos ausentes). Usar cuando python main_ai.py termina con exit code distinto de 0, cuando falta el DOCX/PDF/execution_log.json esperado, o cuando el usuario dice "el informe falla", "no se genera el PDF", "error de QA" o similar.
---

# Diagnóstico de fallos del pipeline de informes

## Paso 1 — Identificar el exit code

| Código | Significado | Dónde mirar |
|--------|-------------|-------------|
| 10 | Fallo de QA (`QualityCheckError`) | `run_quality_checks` en `src/report_generator_professional.py`; texto prohibido (`None`, `NO DISPONIBLE`, rutas locales) en el DOCX |
| 11 | Contrato de salida (`OutputContractError`) | `validate_output_contract`; falta alguno de los tres artefactos o no son válidos |
| 12 | Entrada inválida o error no controlado | Ruta del `--input`, formato del JSON de reseñas, traceback en la salida |
| 13 | Falta `OPENAI_API_KEY` | `.env` en la raíz del proyecto o variable de entorno |

## Paso 2 — Leer el execution_log.json

Está en `data/reports/<cliente>/v<PIPELINE_VERSION>/execution_log.json`.
Campos clave: `status`, `exit_code`, `input_hash`, `docx_hash`, `pdf_hash`.
Un hash a `null` significa que ese artefacto no se generó o hay más de un
candidato en la carpeta (el glob exige exactamente un `*_informe_PROFESIONAL.docx`).

## Paso 3 — Reproducir en dev antes de tocar código

```bash
python main_ai.py --mode dev --input <mismo-json>
```

En dev los fallos devuelven exit 1 pero con el mismo traceback, sin exigir
API key para diagnóstico de fases previas a la IA.

## Reglas al arreglar

- Respetar `.claude/rules/output-contract.md`: nunca degradar en silencio,
  nunca hacer que un fallo de QA "pase" relajando el check.
- Cambios mínimos: arreglar la causa, no reescribir el generador.
- Mismo input debe seguir produciendo el mismo DOCX/PDF tras el arreglo.
