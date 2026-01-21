import os
from pathlib import Path
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

def build_owner_response_pairs(df, max_pairs=40):
    """
    Extrae pares reseña–respuesta de forma controlada.
    Requiere columnas: text, sentiment, owner_response
    """
    pairs = []

    # Solo reseñas con respuesta
    df_r = df[df["owner_response"].notna() & (df["owner_response"].str.strip() != "")]

    if df_r.empty:
        return []

    # Balance por sentimiento
    buckets = {
        "negativo": df_r[df_r["sentiment"].isin(["negativo", "muy_negativo"])],
        "neutro": df_r[df_r["sentiment"] == "neutro"],
        "positivo": df_r[df_r["sentiment"].isin(["positivo", "muy_positivo"])]
    }

    per_bucket = max_pairs // 3

    neg_count = len(buckets["negativo"])
    neu_count = len(buckets["neutro"])
    pos_count = len(buckets["positivo"])
    logger.info(f"OWNER_BUCKETS_COUNTS neg={neg_count} neu={neu_count} pos={pos_count}")

    for bucket in buckets.values():
        for _, r in bucket.head(per_bucket).iterrows():
            pairs.append({
                "review": str(r.get("text", "")).strip(),
                "response": str(r.get("owner_response", "")).strip()
            })

    return pairs[:max_pairs]


def build_prompt_owner_analysis(pairs):
    blocks = []
    for p in pairs:
        blocks.append(
            f'Reseña del cliente:\n"{p["review"]}"\n\n'
            f'Respuesta del propietario:\n"{p["response"]}"\n\n---'
        )

    context = "\n".join(blocks)

    prompt = f"""
ROL
Actúas como auditor senior en Online Reputation Management (ORM).

OBJETIVO
Analizar de forma agregada la calidad, coherencia y naturaleza
de las respuestas del propietario a reseñas públicas.

REGLAS
- No analizar casos individuales.
- No generar tablas.
- No usar Markdown.
- No repetir textos literales largos.

DIMENSIONES
1. Origen probable de las respuestas (humano / IA / mixto)
2. Alineación conceptual con el cliente
3. Alineación emocional
4. Calidad ORM percibida
5. Riesgos reputacionales
6. Recomendaciones accionables

FORMATO
Texto narrativo con secciones numeradas.

DATOS A ANALIZAR
{context}
"""
    return prompt.strip()


def run_owner_response_ai_analysis(df, cfg):
    pairs = build_owner_response_pairs(df)
    logger.info(f"OWNER_PAIRS_COUNT={len(pairs)}")
    if not pairs:
        return None

    prompt = build_prompt_owner_analysis(pairs)
    try:
        from report_generator_professional import _apply_sector_profile_to_prompt
        prompt = _apply_sector_profile_to_prompt(prompt, cfg)
    except Exception:
        pass
    if not prompt:
        logger.warning("OWNER_PROMPT_EMPTY")
    else:
        logger.info(f"OWNER_PROMPT_LEN={len(prompt)}")

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        r = client.chat.completions.create(
            model=cfg.get("openai_model_owner", "gpt-4o-mini"),
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        text = r.choices[0].message.content.strip()
        return text
    except Exception as e:
        logger.error(f"OWNER_AI_OPENAI_ERROR: {e}")
        return None
