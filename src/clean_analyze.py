# analyze_reviews.py — Versión optimizada y libre de warnings
# Integra limpieza, detección de idioma, fake reviews y sentimiento
# Autor: ORM Analyzer 2025-10-19

import re
import pandas as pd
import numpy as np
from langdetect import detect
import unicodedata

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
    df["lang"] = df["clean_text"].apply(_safe_detect_lang)

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

    # ✅ Corregido: regex=True para evitar UserWarning
    generic_user = df["user"].str.contains(
        r"^(usuario|user|an[oó]nimo)", case=False, na=False, regex=True
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
