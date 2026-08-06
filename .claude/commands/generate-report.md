---
description: Genera y valida un informe ORM/CX a partir de un JSON de reseñas
---

Genera un informe para el cliente indicado en $ARGUMENTS (ruta a un JSON de
reseñas). Pasos:

1. Verifica que el archivo JSON existe y que `OPENAI_API_KEY` está disponible
   (`.env` o entorno). Si falta la clave, detente e indícalo — no inventes una.
2. Ejecuta: `python main_ai.py --mode prod --input <ruta-del-json>`
3. Si el exit code es ≠ 0, interpreta el código (10 = QA, 11 = contrato de
   salida, 12 = entrada/error, 13 = falta API key), lee la salida y diagnostica
   antes de tocar código.
4. Si es 0, localiza la carpeta de salida en `data/reports/<cliente>/v<versión>/`
   y confirma que existen los tres artefactos: `*_informe_PROFESIONAL.docx`,
   `*_informe_PROFESIONAL.pdf` y `execution_log.json`.
5. Resume al usuario: estado, rutas de los artefactos y hashes del
   `execution_log.json`.

Respeta siempre `.claude/rules/output-contract.md`.
