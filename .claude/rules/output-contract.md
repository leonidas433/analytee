# Contrato de salida y determinismo

- Mismo input ⇒ mismo DOCX/PDF (contenido visible). Determinismo obligatorio.
- No iterar `dict`/`set` sin orden estable (ordenar claves antes de iterar).
- En prod: o se generan DOCX + PDF + `execution_log.json` válidos o el proceso
  termina con exit code ≠ 0.
- `validate_output_contract` debe pasar siempre en prod.
- `run_quality_checks` se ejecuta tras guardar el DOCX.
- Texto prohibido en los informes: `None`, `NO DISPONIBLE`, rutas locales.
- Fallo de QA ⇒ excepción (nunca degradar en silencio).
- El generador es el único responsable de `execution_log.json`.
- El entrypoint (`main_ai.py`) no debe reescribir artefactos del generador.
