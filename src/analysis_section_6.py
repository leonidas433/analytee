import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List


def compute_contradictions(df: pd.DataFrame) -> Dict:
    """
    Detecta contradicciones entre rating y texto.
    Ejemplo: rating >=4 con texto negativo o rating <=2 con texto positivo.
    """
    if df is None or len(df) == 0:
        return {
            "total_reviews": 0,
            "contradiction_count": 0,
            "contradiction_ratio": 0.0,
            "examples": [],
        }

    working = df.copy()

    def _sentiment_from_text(text: str) -> int:
        t = str(text).lower()
        negative_patterns = [
            "horrible",
            "terrible",
            "pésimo",
            "pesimo",
            "malo",
            "muy mal",
            "no volver",
            "no lo recomiendo",
            "decepcionante",
            "fatal",
        ]
        positive_patterns = [
            "excelente",
            "fantástico",
            "fantastico",
            "increíble",
            "increible",
            "muy bueno",
            "genial",
            "perfecto",
            "lo recomiendo",
            "volveré",
            "volvere",
        ]

        score = 0
        for p in negative_patterns:
            if p in t:
                score -= 1
        for p in positive_patterns:
            if p in t:
                score += 1
        return score

    working["rating_num"] = working.get("rating_num", 0)
    working["text"] = working.get("text", "")

    working["text_polarity"] = working["text"].fillna("").apply(_sentiment_from_text)

    mask_high_rating_neg_text = (working["rating_num"] >= 4) & (
        working["text_polarity"] < 0
    )
    mask_low_rating_pos_text = (working["rating_num"] <= 2) & (
        working["text_polarity"] > 0
    )
    contradictions = working[mask_high_rating_neg_text | mask_low_rating_pos_text]

    total_reviews = int(len(working))
    contradiction_count = int(len(contradictions))
    contradiction_ratio = (
        float(contradiction_count / total_reviews) if total_reviews > 0 else 0.0
    )

    examples: List[str] = []
    for _, row in contradictions.head(5).iterrows():
        date = str(row.get("date", "") or "")
        rating = int(row.get("rating_num", 0))
        text = str(row.get("text", "") or "").strip()
        if not text:
            continue
        examples.append(f"[{date}] {rating}★: {text}")

    return {
        "total_reviews": total_reviews,
        "contradiction_count": contradiction_count,
        "contradiction_ratio": round(contradiction_ratio, 4),
        "examples": examples,
    }


def compute_local_vs_tourist(df: pd.DataFrame) -> Dict:
    """
    Segmenta reseñas usando:
    - Idioma
    - Referencias semánticas (visit, vacation, local, barrio, etc.)
    """
    if df is None or len(df) == 0:
        return {
            "local_count": 0,
            "tourist_count": 0,
            "local_avg_rating": 0.0,
            "tourist_avg_rating": 0.0,
            "key_differences": "Sin datos suficientes para segmentar entre locales y turistas.",
        }

    working = df.copy()
    working["lang"] = working.get("lang", "")
    working["text"] = working.get("text", "")

    def _is_tourist_row(row) -> bool:
        text = str(row.get("text", "") or "").lower()
        lang = str(row.get("lang", "") or "").lower()

        tourist_keywords = [
            "vacation",
            "holidays",
            "holiday",
            "trip",
            "tourist",
            "tourists",
            "turista",
            "turistas",
            "viaje",
            "visita",
            "visitamos",
            "estábamos de paso",
            "estabamos de paso",
        ]
        local_keywords = [
            "soy de",
            "somos de",
            "vivimos",
            "vecino",
            "vecinos",
            "del barrio",
            "del barrio",
            "cliente habitual",
            "cliente frecuente",
            "somos clientes",
        ]

        if any(k in text for k in tourist_keywords):
            return True
        if any(k in text for k in local_keywords):
            return False

        if lang not in ("es", "ca", "eu", "gl", ""):
            return True

        return False

    def _is_local_row(row) -> bool:
        text = str(row.get("text", "") or "").lower()
        lang = str(row.get("lang", "") or "").lower()

        local_keywords = [
            "soy de",
            "somos de",
            "vivimos",
            "vecino",
            "vecinos",
            "del barrio",
            "cliente habitual",
            "cliente frecuente",
            "somos clientes",
        ]

        if any(k in text for k in local_keywords):
            return True

        if lang in ("es", "ca", "eu", "gl"):
            return True

        return False

    working["is_tourist"] = working.apply(_is_tourist_row, axis=1)
    working["is_local"] = working.apply(_is_local_row, axis=1) & ~working["is_tourist"]

    local_df = working[working["is_local"]]
    tourist_df = working[working["is_tourist"]]

    local_count = int(len(local_df))
    tourist_count = int(len(tourist_df))

    local_avg_rating = float(local_df["rating_num"].mean()) if local_count > 0 else 0.0
    tourist_avg_rating = (
        float(tourist_df["rating_num"].mean()) if tourist_count > 0 else 0.0
    )

    if local_count == 0 and tourist_count == 0:
        key_differences = (
            "No se han identificado patrones claros para diferenciar clientes locales y turistas."
        )
    else:
        if abs(local_avg_rating - tourist_avg_rating) < 0.2:
            key_differences = (
                "Locales y turistas valoran de forma muy similar la experiencia."
            )
        elif local_avg_rating > tourist_avg_rating:
            key_differences = (
                "Los clientes locales valoran mejor la experiencia que los turistas."
            )
        else:
            key_differences = (
                "Los turistas valoran mejor la experiencia que los clientes locales."
            )

    return {
        "local_count": local_count,
        "tourist_count": tourist_count,
        "local_avg_rating": round(local_avg_rating, 2),
        "tourist_avg_rating": round(tourist_avg_rating, 2),
        "key_differences": key_differences,
    }


def compute_operational_fatigue(df: pd.DataFrame) -> Dict:
    """
    Detecta:
    - Aumento de negatividad en el tiempo
    - Repetición de quejas
    - Caída de rating reciente vs histórico
    """
    SENTIMENT_SCORE_MAP = {
        "muy_positivo": 2,
        "positivo": 1,
        "neutro": 0,
        "negativo": -1,
        "muy_negativo": -2,
    }

    def _mean_sentiment_score(frame: pd.DataFrame) -> float:
        if frame.empty or "sentiment" not in frame.columns:
            return 0.0

        scores = frame["sentiment"].map(SENTIMENT_SCORE_MAP).dropna()

        return float(scores.mean()) if len(scores) > 0 else 0.0

    if df is None or len(df) == 0:
        return {
            "trend_rating_last_6m": 0.0,
            "trend_sentiment_last_6m": 0.0,
            "repeated_complaints": [],
            "fatigue_signal": "LOW",
        }

    working = df.copy()
    working["rating_num"] = working.get("rating_num", 0)
    working["sentiment"] = working.get("sentiment", "")
    working["text"] = working.get("text", "")

    def _parse_date_safe(value):
        try:
            return datetime.fromisoformat(str(value)[:10])
        except Exception:
            return None

    working["parsed_date"] = working.get("date", "").apply(_parse_date_safe)
    working = working.dropna(subset=["parsed_date"]).sort_values("parsed_date")

    if len(working) == 0:
        return {
            "trend_rating_last_6m": 0.0,
            "trend_sentiment_last_6m": 0.0,
            "repeated_complaints": [],
            "fatigue_signal": "LOW",
        }

    max_date = working["parsed_date"].max()
    six_months_ago = max_date.replace(
        year=max_date.year if max_date.month > 6 else max_date.year - 1,
        month=((max_date.month - 6 - 1) % 12) + 1,
    )

    recent = working[working["parsed_date"] >= six_months_ago]
    past = working[working["parsed_date"] < six_months_ago]

    overall_rating = float(working["rating_num"].mean()) if len(working) > 0 else 0.0
    recent_rating = float(recent["rating_num"].mean()) if len(recent) > 0 else 0.0
    past_rating = float(past["rating_num"].mean()) if len(past) > 0 else overall_rating

    trend_rating_last_6m = recent_rating - past_rating

    recent_sentiment = _mean_sentiment_score(recent)
    past_sentiment = _mean_sentiment_score(past)
    trend_sentiment_last_6m = recent_sentiment - past_sentiment

    words = (
        working["text"]
        .fillna("")
        .str.lower()
        .str.replace(r"[^\w\sáéíóúñ]", " ", regex=True)
        .str.split()
    )

    from collections import Counter

    all_words = [w for row in words for w in row if len(w) > 4]
    word_counts = Counter(all_words)
    repeated = [w for w, c in word_counts.most_common(20) if c >= 5]

    repeated_complaints = repeated[:10]

    fatigue_score = 0

    if trend_rating_last_6m <= -0.3:
        fatigue_score += 2
    elif trend_rating_last_6m <= -0.1:
        fatigue_score += 1

    if trend_sentiment_last_6m <= -0.5:
        fatigue_score += 2
    elif trend_sentiment_last_6m <= -0.2:
        fatigue_score += 1

    if len(repeated_complaints) >= 5:
        fatigue_score += 2
    elif len(repeated_complaints) >= 3:
        fatigue_score += 1

    if fatigue_score >= 4:
        fatigue_signal = "HIGH"
    elif fatigue_score >= 2:
        fatigue_signal = "MEDIUM"
    else:
        fatigue_signal = "LOW"

    return {
        "trend_rating_last_6m": round(trend_rating_last_6m, 3),
        "trend_sentiment_last_6m": round(trend_sentiment_last_6m, 3),
        "repeated_complaints": repeated_complaints,
        "fatigue_signal": fatigue_signal,
    }


def compute_operational_fatigue_score(fatigue: dict) -> dict:
    """
    Convierte señales de fatiga operativa en score 0–100.
    """
    score = 100.0

    rating_trend = fatigue.get("trend_rating_last_6m", 0.0)
    sentiment_trend = fatigue.get("trend_sentiment_last_6m", 0.0)
    complaints = fatigue.get("repeated_complaints", [])
    signal = fatigue.get("fatigue_signal", "LOW")

    # Penalizaciones deterministas
    if rating_trend <= -0.3:
        score -= 25
    elif rating_trend <= -0.1:
        score -= 15

    if sentiment_trend <= -0.5:
        score -= 25
    elif sentiment_trend <= -0.2:
        score -= 15

    if len(complaints) >= 5:
        score -= 20
    elif len(complaints) >= 3:
        score -= 10

    if signal == "HIGH":
        score -= 10
    elif signal == "MEDIUM":
        score -= 5

    score = max(round(score, 1), 0.0)

    if score >= 85:
        level = "ESTABLE"
    elif score >= 65:
        level = "RIESGO MODERADO"
    else:
        level = "RIESGO ALTO"

    return {
        "metric": "Operational Fatigue Score",
        "version": METRICS_VERSION,
        "score": score,
        "level": level
    }


METRICS_VERSION = "v1"
ALERT_RULES_VERSION = "v1"


def get_metrics_version() -> dict:
    return {
        "metrics_version": METRICS_VERSION,
        "alert_rules_version": ALERT_RULES_VERSION,
    }


def compute_alerts_by_score(
    contradiction_score: dict,
    fatigue_score: dict,
    mode: str = "CLIENT",
) -> dict:
    """
    Genera alertas deterministas SOLO por score.
    """
    normalized_mode = str(mode or "CLIENT").upper()
    if normalized_mode not in ("CLIENT", "AUDIT"):
        normalized_mode = "CLIENT"

    def _dcs_severity(score_value):
        if score_value is None:
            return None
        if score_value >= 90:
            return "OK"
        if score_value >= 80:
            return "WATCH"
        if score_value >= 65:
            return "WARN"
        return "ALERT"

    def _ofs_severity(score_value):
        if score_value is None:
            return None
        if score_value >= 85:
            return "OK"
        if score_value >= 65:
            return "WATCH"
        return "ALERT"

    def _severity_rank(level):
        ordering = {"OK": 0, "WATCH": 1, "WARN": 2, "ALERT": 3}
        return ordering.get(level, 0)

    alerts = []

    dcs_score_value = None
    if isinstance(contradiction_score, dict):
        dcs_score_value = contradiction_score.get("score")

    ofs_score_value = None
    if isinstance(fatigue_score, dict):
        ofs_score_value = fatigue_score.get("score")

    if isinstance(dcs_score_value, (int, float)):
        dcs_sev = _dcs_severity(dcs_score_value)
        if dcs_sev == "OK":
            msg = "Coherencia del discurso estable."
        elif dcs_sev == "WATCH":
            msg = "Vigilar posibles desviaciones en la coherencia del discurso."
        elif dcs_sev == "WARN":
            msg = "Inconsistencias relevantes entre puntuación y discurso."
        else:
            msg = "Coherencia del discurso en nivel crítico."
    else:
        dcs_sev = "WATCH"
        if normalized_mode == "AUDIT":
            msg = "Score de coherencia no disponible; revisar artefactos y pipeline técnico."
        else:
            msg = "Score de coherencia no disponible; se recomienda revisión manual."

    alerts.append(
        {
            "id": "DCS",
            "severity": dcs_sev,
            "title": "Coherencia del discurso",
            "message": msg,
        }
    )

    if isinstance(ofs_score_value, (int, float)):
        ofs_sev = _ofs_severity(ofs_score_value)
        if ofs_sev == "OK":
            msg = "Fatiga operativa dentro de parámetros aceptables."
        elif ofs_sev == "WATCH":
            msg = "Señales moderadas de fatiga operativa; conviene seguimiento."
        else:
            msg = "Riesgo elevado de fatiga operativa; requiere atención prioritaria."
    else:
        ofs_sev = "WATCH"
        if normalized_mode == "AUDIT":
            msg = "Score de fatiga operativa no disponible; comprobar artefactos y reglas."
        else:
            msg = "Score de fatiga operativa no disponible; revisar operación de forma preventiva."

    alerts.append(
        {
            "id": "OFS",
            "severity": ofs_sev,
            "title": "Fatiga operativa",
            "message": msg,
        }
    )

    overall = max((alert["severity"] for alert in alerts), key=_severity_rank)

    return {
        "mode": normalized_mode,
        "alert_rules_version": ALERT_RULES_VERSION,
        "alerts": alerts,
        "overall": overall,
    }



def compute_contradiction_score(contradictions: dict) -> dict:
    """
    Convierte contradicciones en un score 0–100.
    """
    total = contradictions.get("total_reviews", 0)
    ratio = contradictions.get("contradiction_ratio", 0.0)

    if total == 0:
        return {
            "metric": "Discourse Consistency Score",
            "version": METRICS_VERSION,
            "score": 100.0,
            "level": "NO DATA",
            "contradiction_ratio": 0.0
        }

    score = round(100 * (1 - ratio), 1)

    if score >= 90:
        level = "EXCELENTE"
    elif score >= 80:
        level = "BUENA"
    elif score >= 65:
        level = "INCONSISTENTE"
    else:
        level = "CRÍTICA"

    return {
        "metric": "Discourse Consistency Score",
        "version": METRICS_VERSION,
        "score": score,
        "level": level,
        "contradiction_ratio": ratio
    }

