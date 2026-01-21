import pandas as pd
from datetime import datetime


def compute_rating_by_timeband(df: pd.DataFrame) -> dict:
    if df is None or len(df) == 0 or "date" not in df.columns or "rating_num" not in df.columns:
        return {}

    def _parse_hour(value):
        try:
            s = str(value)
            if not s:
                return None
            return datetime.fromisoformat(s.replace("Z", "")[:19]).hour
        except Exception:
            return None

    hours = df["date"].apply(_parse_hour)
    bands = []
    for h in hours:
        if h is None:
            bands.append(None)
        elif 0 <= h < 6:
            bands.append("madrugada")
        elif 6 <= h < 12:
            bands.append("mañana")
        elif 12 <= h < 16:
            bands.append("comida")
        elif 16 <= h < 20:
            bands.append("tarde")
        elif 20 <= h < 24:
            bands.append("noche")
        else:
            bands.append(None)

    working = df.copy()
    working["timeband"] = bands
    working = working.dropna(subset=["timeband"])

    if len(working) == 0:
        return {}

    result = {}
    grouped = working.groupby(["rating_num", "timeband"]).size().reset_index(name="count")
    for _, row in grouped.iterrows():
        rating = str(int(row["rating_num"]))
        band = row["timeband"]
        count = int(row["count"])
        if rating not in result:
            result[rating] = {}
        result[rating][band] = result[rating].get(band, 0) + count

    return result


def compute_rating_by_language(df: pd.DataFrame) -> dict:
    if df is None or len(df) == 0 or "lang" not in df.columns or "rating_num" not in df.columns:
        return {}

    working = df.copy()
    grouped = working.groupby("lang")["rating_num"].agg(["mean", "count"]).reset_index()

    result = {}
    for _, row in grouped.iterrows():
        lang = str(row["lang"])
        avg = float(row["mean"]) if row["count"] > 0 else 0.0
        cnt = int(row["count"])
        result[lang] = {
            "avg_rating": round(avg, 2),
            "count": cnt,
        }

    return result


def compute_rating_by_local_guide(df: pd.DataFrame) -> dict:
    if df is None or len(df) == 0 or "rating_num" not in df.columns:
        return {}

    col = None
    if "isLocalGuide" in df.columns:
        col = df["isLocalGuide"]
    elif "is_local_guide" in df.columns:
        col = df["is_local_guide"]

    if col is None:
        local_mask = pd.Series([False] * len(df), index=df.index)
    else:
        series = col
        if series.dtype == bool:
            local_mask = series
        else:
            s = series.fillna("").astype(str).str.lower().str.strip()
            local_mask = s.isin(["true", "1", "yes", "y", "si", "sí"])

    working = df.copy()
    working["is_local_guide_flag"] = local_mask

    local = working[working["is_local_guide_flag"]]
    non_local = working[~working["is_local_guide_flag"]]

    def _stats(sub):
        if len(sub) == 0:
            return {"avg_rating": 0.0, "count": 0}
        return {
            "avg_rating": round(float(sub["rating_num"].mean()), 2),
            "count": int(len(sub)),
        }

    return {
        "local_guide": _stats(local),
        "non_local_guide": _stats(non_local),
    }


def compute_rating_by_images(df: pd.DataFrame) -> dict:
    if df is None or len(df) == 0 or "rating_num" not in df.columns:
        return {}

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

    working = df.copy()
    if has_images is None:
        working["has_images_flag"] = False
    else:
        working["has_images_flag"] = has_images

    with_images = working[working["has_images_flag"]]
    without_images = working[~working["has_images_flag"]]

    def _stats(sub):
        if len(sub) == 0:
            return {"avg_rating": 0.0, "count": 0}
        return {
            "avg_rating": round(float(sub["rating_num"].mean()), 2),
            "count": int(len(sub)),
        }

    return {
        "with_images": _stats(with_images),
        "without_images": _stats(without_images),
    }

