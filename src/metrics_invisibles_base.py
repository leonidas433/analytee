import pandas as pd


def compute_owner_response_rate(df: pd.DataFrame) -> dict:
    total_reviews = int(len(df)) if df is not None else 0
    if df is None or total_reviews == 0:
        return {
            "total_reviews": 0,
            "owner_responses": 0,
            "response_rate_pct": 0.0,
        }

    if "owner_response" in df.columns:
        responses = df["owner_response"].fillna("").astype(str).str.strip() != ""
        owner_responses = int(responses.sum())
    else:
        owner_responses = 0

    rate = (owner_responses / total_reviews * 100) if total_reviews > 0 else 0.0

    return {
        "total_reviews": total_reviews,
        "owner_responses": owner_responses,
        "response_rate_pct": round(float(rate), 2),
    }


def compute_languages_distribution(df: pd.DataFrame) -> dict:
    total_reviews = int(len(df)) if df is not None else 0
    if df is None or total_reviews == 0 or "lang" not in df.columns:
        return {
            "total_reviews": total_reviews,
            "languages": [],
        }

    counts = df["lang"].fillna("").astype(str).value_counts()
    languages = []
    for lang_code, count in counts.items():
        pct = (count / total_reviews * 100) if total_reviews > 0 else 0.0
        languages.append(
            {
                "lang": lang_code,
                "count": int(count),
                "pct": round(float(pct), 2),
            }
        )

    return {
        "total_reviews": total_reviews,
        "languages": languages,
    }


def compute_images_rate(df: pd.DataFrame) -> dict:
    total_reviews = int(len(df)) if df is not None else 0
    if df is None or total_reviews == 0:
        return {
            "total_reviews": 0,
            "reviews_with_images": 0,
            "image_rate_pct": 0.0,
        }

    has_images = None

    if "review_photos" in df.columns:
        has_images = df["review_photos"].fillna(0).astype(float) > 0
    elif "photos" in df.columns:
        has_images = df["photos"].fillna(0).astype(float) > 0
    elif "hasImages" in df.columns:
        col = df["hasImages"]
        if col.dtype == bool:
            has_images = col
        else:
            has_images = col.fillna(False).astype(bool)

    if has_images is None:
        reviews_with_images = 0
    else:
        reviews_with_images = int(has_images.sum())

    rate = (reviews_with_images / total_reviews * 100) if total_reviews > 0 else 0.0

    return {
        "total_reviews": total_reviews,
        "reviews_with_images": reviews_with_images,
        "image_rate_pct": round(float(rate), 2),
    }


def compute_local_guides_ratio(df: pd.DataFrame) -> dict:
    total_reviews = int(len(df)) if df is not None else 0
    if df is None or total_reviews == 0:
        return {
            "total_reviews": 0,
            "local_guides": 0,
            "non_local_guides": 0,
            "local_guides_pct": 0.0,
        }

    col = None
    if "isLocalGuide" in df.columns:
        col = df["isLocalGuide"]
    elif "is_local_guide" in df.columns:
        col = df["is_local_guide"]

    if col is None:
        local_guides = 0
    else:
        series = col
        if series.dtype == bool:
            mask = series
        else:
            s = series.fillna("").astype(str).str.lower().str.strip()
            mask = s.isin(["true", "1", "yes", "y", "si", "sí"])
        local_guides = int(mask.sum())

    non_local_guides = max(total_reviews - local_guides, 0)
    pct = (local_guides / total_reviews * 100) if total_reviews > 0 else 0.0

    return {
        "total_reviews": total_reviews,
        "local_guides": local_guides,
        "non_local_guides": non_local_guides,
        "local_guides_pct": round(float(pct), 2),
    }

