# Contrato de salida y calidad

- Mismo input ⇒ mismo DOCX/PDF (contenido visible). Determinismo obligatorio.
- No iterar `dict`/`set` sin orden estable (ordenar claves antes de iterar).
- En modo `prod`: o se generan DOCX + PDF + `execution_log.json` válidos, o el
  proceso termina con exit code ≠ 0.
- `validate_output_contract` debe pasar siempre en prod.
- `run_quality_checks` se ejecuta tras guardar el DOCX.
- Texto prohibido en los informes: `None`, `NO DISPONIBLE`, rutas locales.
- Fallo de QA ⇒ excepción (`QualityCheckError` / `OutputContractError`), nunca
  degradar en silencio.
- El generador (`report_generator_professional.py`) es el único responsable de
  escribir `execution_log.json`; el entrypoint no debe reescribir artefactos.
