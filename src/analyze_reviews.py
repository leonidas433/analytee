# analyze_reviews.py — ORM Analyzer 2025-10-19
# Limpieza, análisis de sentimiento, detección de falsos, temas y entidades
# Incluye función completa: run_full_pipeline(csv_path)

import re
import os
import pandas as pd
import numpy as np
from langdetect import detect, DetectorFactory
import unicodedata
from pathlib import Path
import json

DetectorFactory.seed = 0


# =============================================================
# NORMALIZACIÓN DE TEXTO
# =============================================================

class Cleaner:
    """Normaliza texto: minúsculas, sin caracteres especiales ni saltos."""

    def transform(self, X):
        def norm(t):
            t = str(t).lower().strip()
            # Elimina acentos
            t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("utf-8")
            # Reemplaza múltiples espacios
            t = re.sub(r"\s+", " ", t)
            # Mantiene letras, números y espacios
            t = re.sub(r"[^a-z0-9áéíóúüñ\s]", "", t)
            return t.strip()

        return [norm(x) for x in X]


def _safe_detect_lang(text, default="es"):
    """Detecta idioma con fallback seguro."""
    try:
        return detect(text)
    except Exception:
        return default


# =============================================================
# PREPROCESAMIENTO PRINCIPAL
# =============================================================

def preprocess_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Limpieza general: rating, texto y detección de idioma."""
    df = df.copy()

    # --- Limpieza de columna rating ---
    if "rating" in df.columns:
        df["rating_num"] = (
            df["rating"]
            .astype(str)
            .str.extract(r"(\d)")
            .astype(float)
        )
    else:
        raise ValueError("Falta la columna 'rating' en el CSV.")

    df["rating_num"] = df["rating_num"].fillna(0).astype(int)

    # --- Limpieza de texto ---
    if "text" not in df.columns:
        raise ValueError("Falta la columna 'text' en el CSV.")

    df["clean_text"] = Cleaner().transform(df["text"].fillna(""))

    # --- Detección de idioma ---
    disable_lang_cache = str(os.getenv("ORM_DISABLE_LANG_CACHE", "")).strip().lower() in ("1", "true", "yes")
    if disable_lang_cache:
        df["lang"] = df["clean_text"].apply(_safe_detect_lang)
        return df

    lang_cache = {}

    def _detect_cached(t):
        s = "" if t is None else str(t)
        cached = lang_cache.get(s)
        if cached is not None:
            return cached
        v = _safe_detect_lang(s)
        lang_cache[s] = v
        return v

    df["lang"] = df["clean_text"].map(_detect_cached)

    return df


# =============================================================
# DETECCIÓN DE FAKE REVIEWS
# =============================================================

def detect_fake_reviews(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """
    Detecta reseñas potencialmente falsas:
    - Duplicadas
    - Usuarios genéricos
    - Textos demasiado cortos
    """
    df = df.copy()

    dup_text = df.duplicated(subset=["text"], keep=False)

    # ✅ regex=True evita UserWarning
    generic_user = df["user"].str.contains(
        r"^(?:usuario|user|an[oó]nimo)", case=False, na=False, regex=True
    )

    short_text = df["clean_text"].str.len().fillna(0) < 5

    score = (
        dup_text.astype(int) * 0.5
        + generic_user.astype(int) * 0.3
        + short_text.astype(int) * 0.2
    )

    df["fake_prob"] = score.clip(0, 1)
    filtered = df[df["fake_prob"] < threshold].reset_index(drop=True)

    return filtered


# =============================================================
# ANÁLISIS DE SENTIMIENTO
# =============================================================

def analyze_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Asigna categoría de sentimiento según rating."""
    df = df.copy()

    def rule(r):
        if r >= 5:
            return "muy_positivo"
        if r == 4:
            return "positivo"
        if r == 3:
            return "neutro"
        if r == 2:
            return "negativo"
        if r == 1:
            return "muy_negativo"
        return "sin_valor"

    df["sentiment"] = df["rating_num"].apply(rule)
    return df


# =============================================================
# EXTRACCIÓN DE TÓPICOS Y ENTIDADES
# =============================================================

def extract_topics(df: pd.DataFrame, top_k: int = 10) -> dict:
    """Identifica los términos más frecuentes mediante TF-IDF."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    if len(df) == 0 or df["clean_text"].str.strip().eq("").all():
        return {"top_terms": []}

    vec = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
    X = vec.fit_transform(df["clean_text"])
    terms = vec.get_feature_names_out()
    sums = np.asarray(X.sum(axis=0)).ravel()
    order = np.argsort(-sums)[:top_k]

    return {"top_terms": [terms[i] for i in order]}


def extract_entities(df: pd.DataFrame) -> dict:
    """Extrae nombres propios (empleados mencionados, lugares, etc.)."""
    names = []
    pattern = re.compile(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b")

    for t in df["text"].dropna().tolist():
        names += pattern.findall(str(t))

    from collections import Counter
    cnt = Counter(names)

    return {"employees": cnt.most_common(10)}


def extract_language_distribution(df: pd.DataFrame) -> dict:
    """Extrae distribución de idiomas de las reseñas."""
    if "lang" not in df.columns:
        return {"languages": []}

    lang_counts = df["lang"].value_counts()
    total = len(df)

    languages = []
    for lang_code, count in lang_counts.items():
        percentage = (count / total * 100) if total > 0 else 0
        # Mapear códigos de idioma a nombres legibles
        lang_names = {
            "es": "Español",
            "en": "Inglés",
            "fr": "Francés",
            "de": "Alemán",
            "it": "Italiano",
            "pt": "Portugués",
            "ca": "Catalán",
            "eu": "Euskera",
            "gl": "Gallego",
            "nl": "Holandés",
            "ru": "Ruso",
            "zh": "Chino",
            "ja": "Japonés",
            "ko": "Coreano",
            "ar": "Árabe"
        }
        lang_name = lang_names.get(lang_code, lang_code.upper())
        languages.append({
            "code": lang_code,
            "name": lang_name,
            "count": int(count),
            "percentage": round(percentage, 1)
        })

    return {"languages": languages}


def analyze_engagement(df: pd.DataFrame) -> dict:
    """Analiza métricas de engagement de las reseñas."""
    engagement_stats = {
        "total_reviews_with_likes": 0,
        "avg_likes_per_review": 0,
        "total_photos": 0,
        "reviews_with_photos": 0,
        "response_rate": 0,
        "avg_response_time": "N/A"
    }

    if len(df) == 0:
        return engagement_stats

    # Análisis de likes
    if "review_likes" in df.columns:
        df_likes = df["review_likes"].fillna("0").astype(str)
        likes_numeric = pd.to_numeric(df_likes.str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
        engagement_stats["total_reviews_with_likes"] = (likes_numeric > 0).sum()
        engagement_stats["avg_likes_per_review"] = likes_numeric.mean()

    # Análisis de fotos
    if "review_photos" in df.columns:
        df_photos = df["review_photos"].fillna("0").astype(str)
        photos_numeric = pd.to_numeric(df_photos.str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
        engagement_stats["total_photos"] = photos_numeric.sum()
        engagement_stats["reviews_with_photos"] = (photos_numeric > 0).sum()

    # Análisis de respuestas del propietario
    if "owner_response" in df.columns:
        responses = df["owner_response"].notna() & (df["owner_response"].str.strip() != "")
        engagement_stats["response_rate"] = (responses.sum() / len(df) * 100) if len(df) > 0 else 0

    return engagement_stats


# =============================================================
# PIPELINE COMPLETO
# =============================================================

def run_full_pipeline(csv_path: str, fake_threshold: float = 0.5) -> dict:
    """
    Ejecuta el flujo completo:
    1. Carga CSV
    2. Limpieza y preprocesamiento
    3. Detección de fake reviews
    4. Análisis de sentimiento
    5. Extracción de tópicos y entidades
    Devuelve: dict con resultados + DataFrame limpio
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo CSV: {csv_path}")

    print(f"🔍 Procesando archivo: {csv_path.name}")
    with open(csv_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    reviews = data.get("reviews", [])
    rows = []
    for r in reviews:
        photos = r.get("photos") or []
        rows.append(
            {
                "user": r.get("author", ""),
                "rating": r.get("rating", ""),
                "date": r.get("date", ""),
                "text": r.get("text", ""),
                "owner_response": r.get("responseFromOwnerText", None),
                "review_likes": r.get("likes", 0),
                "review_photos": len(photos),
            }
        )

    df = pd.DataFrame(rows)

    # Paso 1: Preprocesamiento
    df = preprocess_reviews(df)

    # Paso 2: Filtrado de reseñas falsas
    df_filtered = detect_fake_reviews(df, threshold=fake_threshold)

    # Paso 3: Análisis de sentimiento
    df_final = analyze_sentiment(df_filtered)

    # Paso 4: Tópicos, entidades e idiomas
    topics = extract_topics(df_final)
    entities = extract_entities(df_final)
    languages = extract_language_distribution(df_final)

    # Análisis adicional de engagement
    engagement_stats = analyze_engagement(df_final)

    place_metadata = {
        "address": data.get("address"),
        "category": data.get("category"),
        "totalScore": data.get("totalScore"),
        "reviewsCount": data.get("reviewsCount"),
        "website": data.get("website"),
        "phoneNumber": data.get("phoneNumber"),
    }

    # Resultado estructurado
    results = {
        "source_file": str(csv_path),
        "total_reviews": len(df),
        "clean_reviews": len(df_final),
        "topics": topics["top_terms"],
        "employees": entities["employees"],
        "languages": languages["languages"],
        "engagement": engagement_stats,
        "dataframe": df_final,
        "place_metadata": place_metadata,
    }

    print(f"✅ Procesadas {len(df_final)} reseñas limpias de {len(df)} totales.")
    return results


# =============================================================
# USO DIRECTO
# =============================================================

if __name__ == "__main__":
    csv_example = r"D:\proyecto_a\clientes\Bar_Restaurant_La_Carpa_ChIJo44OQEe9pBIRfQ9MxOuuKvQ\Bar_Restaurant_La_Carpa_ChIJo44OQEe9pBIRfQ9MxOuuKvQ.csv"
    results = run_full_pipeline(csv_example)
    print("\n--- Resumen ---")
    print(f"Tópicos: {results['topics']}")
    print(f"Empleados más mencionados: {results['employees']}")
