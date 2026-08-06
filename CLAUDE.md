# Analytee Analytics — ORM Analyzer IA PRO

Pipeline en Python que analiza reseñas de clientes (JSON exportado de Google Maps)
y genera informes profesionales en DOCX + PDF con ayuda de OpenAI.

## Stack

- Python 3 (sin framework web; se ejecuta como CLI)
- OpenAI API (`gpt-4o-mini` por defecto, configurable en `config.yaml`)
- `python-docx` + `docx2pdf` / `reportlab` para los informes
- `pandas`, `numpy`, `matplotlib` para el análisis
- Dependencias: `src/requirements.txt` es la lista completa (incluye `openai`,
  `pyyaml`, `reportlab`); el `requirements.txt` de la raíz es un subconjunto.

## Comandos

```bash
pip install -r src/requirements.txt

# Modo dev (pide la ruta del JSON o acepta --input)
python main_ai.py --mode dev --input ruta/al/cliente.json

# Modo prod (requiere OPENAI_API_KEY y --input; exit code ≠ 0 si algo falla)
python main_ai.py --mode prod --input ruta/al/cliente.json

# Prueba de los formatos modernos con datos sintéticos (sin API key)
python src/test_modern_reports.py

# Auditar la estructura de un DOCX generado
python audit_docx_structure.py
```

## Estructura

- `main_ai.py` — entrypoint: carga `.env` y `config.yaml`, ejecuta el pipeline
  y escribe `execution_log.json`. No reescribe artefactos del generador.
- `src/analyze_reviews.py` — limpieza + análisis (`run_full_pipeline`).
- `src/report_generator_professional.py` — generador principal (formato
  profesional), dueño de `execution_log.json`, QA y contrato de salida.
- `src/report_generator_modern.py` / `src/pdf_generator_modern.py` — formatos
  modernos DOCX/PDF. `src/report_generator_ai_pro.py` — formato clásico.
- `src/metrics_invisibles*.py`, `src/analysis_*.py` — métricas y análisis IA.
- `ai_models/` — prompts de IA (markdown). `analisis/` — notas de arquitectura.
- Salida: `data/reports/<cliente>/v<PIPELINE_VERSION>/` (ignorada por git).

## Contrato de salida en prod

En `--mode prod` la ejecución **o** produce DOCX + PDF + `execution_log.json`
válidos **o** termina con exit code ≠ 0 (10 QA, 11 contrato, 12 entrada/error,
13 falta API key). `validate_output_contract` y `run_quality_checks` deben
pasar siempre; un fallo de QA lanza excepción, nunca se degrada en silencio.

## Configuración

- `.env` (no versionado; ver `.env.example`): `OPENAI_API_KEY`. El proyecto
  la carga automáticamente si existe — nunca asumir export manual.
- `config.yaml` (no versionado): modelo, temperatura, formato, `output_dir`,
  `output_mode` (CLIENT/AUDIT), umbral de reseñas falsas, versión de métricas.

## Reglas del proyecto

Ver reglas completas (obligatorias) en:

@.claude/rules/output-contract.md
@.claude/rules/code-style.md
