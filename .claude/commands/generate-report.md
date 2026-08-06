---
description: Generar y validar un informe a partir de un JSON de reseñas
---

Genera un informe para el JSON de reseñas indicado en `$ARGUMENTS` (ruta al
archivo del cliente) y valida el resultado:

1. Comprueba que las dependencias están instaladas
   (`pip install -r src/requirements.txt` si falta alguna).
2. Si no hay `OPENAI_API_KEY` en el entorno ni en `.env`, ejecuta en modo dev
   sin IA o avisa; en prod es obligatoria.
3. Ejecuta: `python main_ai.py --mode prod --input $ARGUMENTS`
   (usa `--mode dev` si el usuario lo pide o falta la API key).
4. Verifica el contrato de salida en `data/reports/<cliente>/v<versión>/`:
   - existe exactamente un `*_informe_PROFESIONAL.docx` y un `.pdf`,
   - existe `execution_log.json` con `status: "OK"` y `exit_code: 0`,
   - los hashes `docx_hash`/`pdf_hash` no son null.
5. Si el exit code es ≠ 0, informa del código (10 QA, 11 contrato, 12 entrada,
   13 API key) y del error, sin reintentar a ciegas.
