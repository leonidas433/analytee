# Estilo de código y alcance de cambios

- Cambios mínimos y localizados; nada fuera de lo pedido.
- No cambiar rutas, nombres de archivos ni firmas públicas sin indicación
  explícita.
- No refactors cosméticos ni cambios de formato no solicitados.
- El proyecto debe cargar automáticamente variables desde `.env` si existe.
- Nunca asumir que el usuario exportó variables manualmente.
- En modo `prod`, las variables críticas (p. ej. `OPENAI_API_KEY`) deben
  validarse y fallar explícitamente si faltan.
