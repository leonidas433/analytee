# Analytee Analytics (ORM Analyzer IA PRO)

## Overview

Pipeline en Python que analiza reseñas de clientes (JSON exportado de Google)
y genera un informe ORM/CX profesional en
DOCX + PDF con análisis asistido por IA (OpenAI). El flujo completo es:
limpieza → análisis (métricas, idiomas, engagement, detección de reseñas
falsas) → generación de informe → validación de calidad → `execution_log.json`.

## Stack tecnológico

- Python 3.10+ (usa `str | None`, f-strings, `pathlib`)
- OpenAI API (`gpt-4o-mini` por defecto; requiere `OPENAI_API_KEY` en `.env`)
- pandas / numpy / matplotlib para análisis y gráficas
- python-docx (DOCX), docx2pdf y generador propio de PDF (`src/pdf_generator_modern.py`)
- langdetect, python-dateutil, python-dotenv, PyYAML

## Comandos

```bash
# Instalar dependencias
pip install -r requirements.txt          # raíz
pip install -r src/requirements.txt      # dependencias adicionales de src/

# Ejecutar en desarrollo (pide la ruta del JSON o acepta --input)
python main_ai.py --mode dev --input ruta/al/cliente.json

# Ejecutar en producción (exige --input y OPENAI_API_KEY; exit code ≠ 0 si falla)
python main_ai.py --mode prod --input ruta/al/cliente.json

# Tests de generación de informes
python src/test_modern_reports.py
```

Configuración opcional en `config.yaml` (no versionado): secciones `openai`,
`report`, `paths`, `analysis`, `metrics`. Los valores por defecto están en
`DEFAULT_CONFIG` de `main_ai.py`.

## Estructura

- `main_ai.py` — entrypoint: carga `.env`, config y orquesta el pipeline
- `src/analyze_reviews.py` — limpieza + análisis (`run_full_pipeline`)
- `src/report_generator_professional.py` — informe profesional, contrato de
  salida (`PIPELINE_VERSION`, `validate_output_contract`, `run_quality_checks`)
- `src/report_generator_ai_pro.py` / `report_generator_modern.py` — otros formatos
- `src/pdf_generator_modern.py` — PDF
- `ai_models/` — prompts de las fases de análisis
- `data/reports/` — salida (no versionada)

## Reglas del proyecto

Las reglas obligatorias están en `.claude/rules/`:

- `output-contract.md` — determinismo, contrato de salida prod y QA
- `code-style.md` — estilo de cambios y manejo de variables de entorno

Exit codes en prod: 10 = fallo QA, 11 = contrato de salida, 12 = error de
entrada/no controlado, 13 = falta `OPENAI_API_KEY`.
