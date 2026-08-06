# Las 12 capas del $0 AI Architecture Stack (edición 2026)

Referencia por capa: qué resuelve, opciones gratuitas (la primera es la
opción por defecto del skill), cómo detectarla en un proyecto existente y
qué pregunta responde la auditoría.

## 1. Entrada del usuario

- **Qué es**: por dónde llega la petición — web, móvil o CLI.
- **Detección**: argparse/click/typer (CLI), rutas HTTP, app móvil.
- **Auditoría**: ¿está claro el punto de entrada único? ¿Valida su input?

## 2. Frontend

- **Qué resuelve**: capturar input y mostrar respuestas (streaming si hay chat).
- **Opciones**: Streamlit (Python, prototipos), Next.js + Vercel free tier
  (producción web).
- **Detección**: `streamlit` en requirements, carpeta `pages/`/`app/` de
  Next.js, `package.json` con react.
- **Auditoría**: ¿aplica? Un pipeline batch/CLI → N/A. Si hay chat, ¿hay
  streaming de tokens o el usuario espera en blanco?

## 3. Orquestador de agentes

- **Qué resuelve**: planificar tareas y enrutar a herramientas, RAG o LLM.
- **Opciones**: LangGraph (grafos de estado, control fino), CrewAI (equipos
  de agentes con roles).
- **Detección**: `langgraph`/`crewai` en dependencias; o un "orquestador
  artesanal" (cadena de ifs que decide qué prompt llamar) — eso cuenta como
  ⚠️ parcial si ya tiene complejidad de enrutado real.
- **Auditoría**: ¿hay más de un flujo de decisión IA? Con un solo paso LLM
  secuencial, un orquestador es sobreingeniería → N/A.

## 4. Enrutado: ¿necesita conocimiento externo?

- **Qué resuelve**: decidir por petición si hace falta RAG o basta el modelo.
- **Detección**: lógica condicional antes de la llamada al LLM.
- **Auditoría**: ¿se inyecta siempre todo el contexto (caro, ruidoso) o se
  decide? En pipelines batch la "decisión" puede estar fija en el diseño — OK.

## 5. RAG Pipeline

- **Qué resuelve**: responder con contexto de documentos propios.
- **Opciones**: ingesta/chunking con Docling; embeddings BGE-M3 (multilingüe,
  local); vector store ChromaDB (local, cero infra); rerank BGE-Reranker-v2.
- **Detección**: `chromadb`, `qdrant`, `faiss`, `sentence-transformers`,
  código de chunking/embeddings.
- **Auditoría**: si los prompts llevan los datos completos en contexto y caben,
  RAG es N/A. Es ❌ cuando hay corpus que no cabe en contexto o se re-envía
  entero en cada llamada pagando tokens.

## 6. Capa LLM

- **Qué resuelve**: el modelo. La versión $0 = open-weight local.
- **Opciones**: Ollama como runtime; modelos según hardware — Llama 3.3 70B
  (necesita ~40 GB VRAM), Mistral Small 3, Qwen 3, Gemma 3, Phi-4 (corren en
  GPU de consumo o CPU con cuantización), DeepSeek-R1 (razonamiento).
- **Detección**: `ollama`, `llama-cpp-python`, `vllm`; o cliente de API de
  pago (`openai`, `anthropic`) → cubierta pero no a coste cero.
- **Auditoría**: ¿el modelo y parámetros están en config (no hardcodeados)?
  ¿Hay estimación de coste por ejecución? ¿Un modelo local cuantizado daría
  calidad suficiente para abaratar? Avisar siempre del coste hardware real.

## 7. Herramientas vía MCP

- **Qué resuelve**: conectar el agente a sistemas externos (GitHub, Slack,
  BBDD, ficheros) con un protocolo estándar en vez de integraciones ad hoc.
- **Opciones**: servidores MCP oficiales/comunitarios; SDK MCP para exponer
  herramientas propias.
- **Detección**: `mcp` en dependencias, `.mcp.json`, config de servidores.
- **Auditoría**: ¿cuántas integraciones ad hoc hay que ya existen como
  servidor MCP? Con 0-1 integraciones simples → N/A.

## 8. Agente de código

- **Qué resuelve**: escribir, editar y probar código del propio proyecto.
- **Opciones**: Claude Code, Aider (open source, cualquier LLM), OpenHands.
- **Detección**: `.claude/` (CLAUDE.md, skills, rules), `.aider*`.
- **Auditoría**: ¿hay CLAUDE.md con comandos y reglas? ¿Los flujos repetidos
  están capturados como skills/comandos?

## 9. Memoria, datos y caché

- **Qué resuelve**: estado, persistencia y no repetir trabajo caro (llamadas
  LLM idénticas → caché).
- **Opciones**: SQLite (persistencia simple), DuckDB (analítica local), Redis
  (caché), LangGraph Store (memoria de agentes), Supabase free tier (si hace
  falta Postgres gestionado).
- **Detección**: `sqlite3`, `duckdb`, `redis`, ORMs, ficheros de estado JSON.
- **Auditoría**: ¿se cachean respuestas LLM repetibles? ¿El estado sobrevive a
  un reinicio? Ficheros JSON como registro de ejecución cuentan como ⚠️/✅
  según necesidad real.

## 10. Guardrails y evals

- **Qué resuelve**: calidad y seguridad de las salidas antes de entregarlas,
  y regresiones medibles al cambiar prompts o modelo.
- **Opciones**: validación propia con excepciones (patrón QA de este repo),
  Guardrails AI (validación estructurada), Promptfoo (evals de prompts en CI),
  Ragas (evals de RAG).
- **Detección**: checks post-generación que lanzan excepción, textos
  prohibidos, contratos de salida, tests de prompts.
- **Auditoría**: ¿un output malo puede llegar al usuario en silencio? ¿Cambiar
  un prompt tiene eval automática o se mira a ojo? Esta capa casi nunca es N/A
  en un proyecto con LLM en producción.

## 11. Observabilidad

- **Qué resuelve**: trazar cada ejecución (prompts, tokens, latencia, coste)
  y depurar cadenas de llamadas.
- **Opciones**: Langfuse (self-hosted, trazas LLM), Phoenix (Arize, evals +
  trazas), OpenTelemetry (estándar general).
- **Detección**: `langfuse`, `arize-phoenix`, `opentelemetry-*`, logging
  estructurado de llamadas LLM con tokens/coste.
- **Auditoría**: ¿se puede responder "cuánto costó y cuánto tardó la ejecución
  de ayer y qué prompts usó"? Un log de ejecución propio es ⚠️ si no registra
  tokens/coste por llamada.

## 12. Deployment

- **Qué resuelve**: ejecutar el sistema fuera del portátil, gratis.
- **Opciones**: Docker (empaquetado base), Hugging Face Spaces (demos
  Streamlit/Gradio), Cloudflare Workers (edge, JS), Oracle Cloud Always Free
  (VM 4 OCPU/24 GB ARM — la opción para servicios Python persistentes).
- **Detección**: `Dockerfile`, `docker-compose.yml`, CI de deploy, systemd.
- **Auditoría**: ¿el entorno es reproducible (¿corre en una máquina limpia con
  N pasos documentados?) aunque el proyecto sea CLI local?

## Formato del informe de auditoría

| # | Capa | Estado | Evidencia / justificación |
|---|------|--------|---------------------------|
| 1-12 | … | ✅ / ⚠️ / ❌ / N/A | componente concreto o motivo del N/A |

Después de la tabla: top 3-5 gaps ordenados por (impacto en fiabilidad o
coste) / esfuerzo, cada uno con la herramienta gratuita propuesta y un primer
paso concreto (comando o fichero a crear).
