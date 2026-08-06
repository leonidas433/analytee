# Estilo de cambios y entorno

- Cambios mínimos y localizados. No refactors cosméticos ni cambios de formato
  no solicitados.
- No cambiar rutas, nombres de archivos ni firmas públicas sin indicación
  explícita.
- El proyecto debe cargar automáticamente variables desde `.env` si existe
  (ver `_load_env_once()` en `main_ai.py`). Nunca asumir que el usuario
  exportó variables manualmente.
- En modo `prod`, las variables críticas (p. ej. `OPENAI_API_KEY`) deben
  validarse al inicio y fallar explícitamente si faltan.
- Nunca commitear credenciales: `.env`, `config.yaml` y `secrets.*` están en
  `.gitignore` y deben seguir estándolo.
