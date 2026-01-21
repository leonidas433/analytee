import pandas as pd
from datetime import datetime
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Optional


def compute_owner_response_rate(df: pd.DataFrame) -> dict:
    """
    Calcula el % de respuesta del propietario a reseñas.
    Usa solo columnas existentes.
    """
    total = int(len(df))
    if total == 0:
        return {
            "metric": "Owner Response Rate",
            "version": "v1",
            "total_reviews": 0,
            "responded_reviews": 0,
            "response_rate_pct": 0.0,
        }

    responded = int(df["owner_response"].notna().sum()) if "owner_response" in df.columns else 0
    rate = round((responded / total) * 100, 1) if total > 0 else 0.0

    return {
        "metric": "Owner Response Rate",
        "version": "v1",
        "total_reviews": total,
        "responded_reviews": responded,
        "response_rate_pct": rate,
    }


def compute_review_languages_distribution(df: pd.DataFrame) -> dict:
    """
    Calcula distribución de idiomas de reseñas (conteo + %).
    Usa exclusivamente la columna existente 'lang'.
    """
    total = int(len(df))

    if total == 0 or "lang" not in df.columns:
        return {
            "metric": "Review Language Distribution",
            "version": "v1",
            "total_reviews": 0,
            "languages": [],
        }

    counts = (
        df["lang"]
        .fillna("unknown")
        .value_counts()
    )

    languages = []
    for lang, count in counts.items():
        pct = round((count / total) * 100, 1)
        languages.append({
            "lang": lang,
            "count": int(count),
            "pct": pct,
        })

    return {
        "metric": "Review Language Distribution",
        "version": "v1",
        "total_reviews": total,
        "languages": languages,
    }


def compute_rating_time_distribution(df: pd.DataFrame) -> dict:
    """
    Distribución de reseñas por franja horaria y rating.
    """
    total = int(len(df))

    FRANJAS = {
        "MADRUGADA": range(0, 8),
        "MAÑANA": range(8, 12),
        "MEDIODÍA": range(12, 16),
        "TARDE": range(16, 20),
        "NOCHE": range(20, 24),
    }

    if total == 0 or "rating_num" not in df.columns or "date" not in df.columns:
        return {
            "metric": "Rating Time Distribution",
            "version": "v1",
            "total_reviews": 0,
            "distribution": {},
        }

    distribution = {}

    for rating in sorted(df["rating_num"].dropna().unique(), reverse=True):
        rating_key = str(int(rating))
        distribution[rating_key] = {k: 0 for k in FRANJAS.keys()}

        subset = df[df["rating_num"] == rating]

        for _, row in subset.iterrows():
            try:
                hour = datetime.fromisoformat(str(row["date"])[:19]).hour
            except Exception:
                continue

            for franja, hours in FRANJAS.items():
                if hour in hours:
                    distribution[rating_key][franja] += 1
                    break

    return {
        "metric": "Rating Time Distribution",
        "version": "v1",
        "total_reviews": total,
        "distribution": distribution,
    }


def compute_local_guide_participation(df: pd.DataFrame) -> dict:
    """
    Conteo y porcentaje de reseñas de Local Guides vs no Local Guides.
    """
    total = int(len(df))

    if total == 0:
        return {
            "metric": "Local Guide Participation",
            "version": "v1",
            "total_reviews": 0,
            "local_guide": {"count": 0, "percent": 0.0},
            "non_local_guide": {"count": 0, "percent": 0.0},
        }

    if "isLocalGuide" in df.columns:
        series = df["isLocalGuide"]
    elif "user.isLocalGuide" in df.columns:
        series = df["user.isLocalGuide"]
    else:
        return {
            "metric": "Local Guide Participation",
            "version": "v1",
            "total_reviews": total,
            "local_guide": {"count": 0, "percent": 0.0},
            "non_local_guide": {"count": total, "percent": 100.0},
        }

    local_count = int(series.fillna(False).astype(bool).sum())
    non_local_count = total - local_count

    return {
        "metric": "Local Guide Participation",
        "version": "v1",
        "total_reviews": total,
        "local_guide": {
            "count": local_count,
            "percent": round((local_count / total) * 100, 1),
        },
        "non_local_guide": {
            "count": non_local_count,
            "percent": round((non_local_count / total) * 100, 1),
        },
    }


def compute_review_media_participation(df: pd.DataFrame) -> dict:
    """
    Porcentaje de reseñas con imágenes y su distribución por rating.
    """
    total = int(len(df))

    if total == 0:
        return {
            "metric": "Review Media Participation",
            "version": "v1",
            "total_reviews": 0,
            "with_images": {"count": 0, "percent": 0.0},
            "without_images": {"count": 0, "percent": 0.0},
            "rating_distribution_with_images": {},
        }

    image_col = None
    for col in ["reviewImages", "images", "photos"]:
        if col in df.columns:
            image_col = col
            break

    if image_col is None:
        return {
            "metric": "Review Media Participation",
            "version": "v1",
            "total_reviews": total,
            "with_images": {"count": 0, "percent": 0.0},
            "without_images": {"count": total, "percent": 100.0},
            "rating_distribution_with_images": {},
        }

    has_images = df[image_col].apply(
        lambda x: isinstance(x, (list, tuple)) and len(x) > 0
    )

    with_images_count = int(has_images.sum())
    without_images_count = total - with_images_count

    distribution = {}
    subset = df[has_images & df["rating_num"].notna()]

    for rating in sorted(subset["rating_num"].unique(), reverse=True):
        distribution[str(int(rating))] = int(
            (subset["rating_num"] == rating).sum()
        )

    return {
        "metric": "Review Media Participation",
        "version": "v1",
        "total_reviews": total,
        "with_images": {
            "count": with_images_count,
            "percent": round((with_images_count / total) * 100, 1),
        },
        "without_images": {
            "count": without_images_count,
            "percent": round((without_images_count / total) * 100, 1),
        },
        "rating_distribution_with_images": distribution,
    }


def compute_popular_times_profile(raw_json: dict) -> dict:
    """
    Perfil horario de afluencia por día, basado en popularTimes.
    """
    if not isinstance(raw_json, dict):
        return {
            "metric": "Popular Times Profile",
            "version": "v1",
            "days": {},
        }

    popular_times = raw_json.get("popularTimes")

    if not isinstance(popular_times, list):
        return {
            "metric": "Popular Times Profile",
            "version": "v1",
            "days": {},
        }

    days = {}

    for day in popular_times:
        name = day.get("name")
        data = day.get("data")

        if not name or not isinstance(data, list):
            continue

        hours = {}
        for hour, value in enumerate(data):
            try:
                hours[str(hour)] = int(value)
            except Exception:
                continue

        days[name] = hours

    return {
        "metric": "Popular Times Profile",
        "version": "v1",
        "days": days,
    }


def _extract_reviews_list(raw_json: dict) -> list:
    if not isinstance(raw_json, dict):
        return []
    reviews = raw_json.get("reviews")
    if isinstance(reviews, list):
        return reviews
    return []


def _extract_owner_response_text(review: dict):
    if not isinstance(review, dict):
        return None
    candidates = [
        review.get("ownerResponse"),
        review.get("reply"),
        review.get("response"),
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
        if isinstance(c, dict):
            for k in ("text", "content", "replyText", "response"):
                v = c.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()
    return None


def owner_response_field_available(raw_json: dict) -> bool:
    reviews = _extract_reviews_list(raw_json or {})
    for r in reviews:
        if not isinstance(r, dict):
            continue
        for k in ("ownerResponse", "response", "reply"):
            if k in r:
                return True
    return False


def local_guides_field_available(raw_json: dict) -> bool:
    reviews = _extract_reviews_list(raw_json or {})
    for r in reviews:
        if not isinstance(r, dict):
            continue
        for k in ("isLocalGuide", "localGuide"):
            if isinstance(r.get(k), bool):
                return True
        for sub in (r.get("authorProfile"), r.get("author")):
            if isinstance(sub, dict) and isinstance(sub.get("isLocalGuide"), bool):
                return True
            if isinstance(sub, dict):
                badges = sub.get("badges")
                if badges is not None and "local guide" in str(badges).lower():
                    return True
                user_level = sub.get("userLevel")
                if user_level is not None and "local guide" in str(user_level).lower():
                    return True
        for k in ("badges", "userLevel"):
            if k in r and "local guide" in str(r.get(k)).lower():
                return True
        if "local guide" in str(r).lower():
            return True
    return False


def _coerce_rating(value):
    if value is None:
        return None
    if isinstance(value, (int, float)) and not pd.isna(value):
        try:
            r = int(round(float(value)))
        except Exception:
            return None
        return r if 1 <= r <= 5 else None
    s = str(value).strip()
    if not s:
        return None
    m = pd.to_numeric(pd.Series([s]).astype(str).str.extract(r"(\d)")[0], errors="coerce").iloc[0]
    if pd.isna(m):
        return None
    r = int(m)
    return r if 1 <= r <= 5 else None


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    if isinstance(value, (int, float)):
        return bool(int(value))
    s = str(value).strip().lower()
    if s in ("true", "1", "yes", "y", "si", "sí"):
        return True
    if s in ("false", "0", "no", "n"):
        return False
    return False


def compute_invisible_owner_response_rate(df: pd.DataFrame, raw_json: Optional[dict] = None) -> dict:
    if not owner_response_field_available(raw_json or {}):
        return {"available": False}

    total = int(len(df)) if isinstance(df, pd.DataFrame) else 0
    if total == 0 or "owner_response" not in df.columns:
        return {"available": True, "total": total, "responded": 0, "pct": 0.0}

    responded = int(df["owner_response"].fillna("").astype(str).str.strip().ne("").sum())
    pct = round((responded / total) * 100, 1) if total else 0.0
    return {"available": True, "total": total, "responded": responded, "pct": pct}


def compute_invisible_review_languages(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or len(df) == 0 or "lang" not in df.columns:
        return pd.DataFrame(columns=["Idioma", "Cantidad", "%"])
    total = int(len(df))
    counts = df["lang"].fillna("unknown").astype(str).value_counts()
    out = pd.DataFrame({"Idioma": counts.index, "Cantidad": counts.values})
    out["%"] = (out["Cantidad"] / total * 100).round(1)
    return out.reset_index(drop=True)


def compute_invisible_hour_rating_matrix(df: pd.DataFrame) -> pd.DataFrame:
    hours = list(range(24))
    cols = [1, 2, 3, 4, 5]
    base = pd.DataFrame(0, index=hours, columns=cols, dtype=int)

    if not isinstance(df, pd.DataFrame) or len(df) == 0:
        base.index.name = "Hora"
        return base
    if "date" not in df.columns or "rating_num" not in df.columns:
        base.index.name = "Hora"
        return base

    dt = pd.to_datetime(df["date"], errors="coerce", utc=False)
    hr = dt.dt.hour
    rt = pd.to_numeric(df["rating_num"], errors="coerce").astype("Int64")
    valid = hr.notna() & rt.notna() & rt.between(1, 5)
    if valid.any():
        tmp = pd.DataFrame({"hour": hr[valid].astype(int), "rating": rt[valid].astype(int)})
        pivot = tmp.groupby(["hour", "rating"]).size().unstack(fill_value=0)
        for c in cols:
            if c not in pivot.columns:
                pivot[c] = 0
        pivot = pivot[cols]
        base.loc[pivot.index, cols] = pivot.astype(int)

    base.index.name = "Hora"
    return base


def compute_invisible_local_guides(raw_json: dict) -> dict:
    if not local_guides_field_available(raw_json or {}):
        return {"available": False}
    reviews = _extract_reviews_list(raw_json or {})
    total = int(len(reviews))
    local = 0
    non_local = 0
    ratings_local = []
    ratings_non_local = []

    for r in reviews:
        if not isinstance(r, dict):
            continue
        is_lg = None
        if "isLocalGuide" in r:
            is_lg = _coerce_bool(r.get("isLocalGuide"))
        elif "localGuide" in r:
            is_lg = _coerce_bool(r.get("localGuide"))
        elif isinstance(r.get("author"), dict) and "isLocalGuide" in r["author"]:
            is_lg = _coerce_bool(r["author"].get("isLocalGuide"))
        elif isinstance(r.get("authorProfile"), dict) and "isLocalGuide" in r["authorProfile"]:
            is_lg = _coerce_bool(r["authorProfile"].get("isLocalGuide"))
        if is_lg is None:
            is_lg = False

        rating = _coerce_rating(r.get("rating"))
        if is_lg:
            local += 1
            if rating is not None:
                ratings_local.append(rating)
        else:
            non_local += 1
            if rating is not None:
                ratings_non_local.append(rating)

    pct_local = round((local / total) * 100, 1) if total else 0.0
    pct_non_local = round((non_local / total) * 100, 1) if total else 0.0
    avg_local = round(float(np.mean(ratings_local)), 2) if ratings_local else None
    avg_non_local = round(float(np.mean(ratings_non_local)), 2) if ratings_non_local else None

    return {
        "available": True,
        "total": total,
        "local_guides": {"count": local, "pct": pct_local, "avg_rating": avg_local},
        "non_local_guides": {"count": non_local, "pct": pct_non_local, "avg_rating": avg_non_local},
    }


def compute_invisible_reviews_with_images(df: pd.DataFrame, raw_json: Optional[dict] = None) -> dict:
    if isinstance(df, pd.DataFrame) and len(df) > 0 and "review_photos" in df.columns and "rating_num" in df.columns:
        photos = pd.to_numeric(df["review_photos"], errors="coerce").fillna(0)
        has = photos.gt(0)
        total = int(len(df))
        with_count = int(has.sum())
        without_count = total - with_count
        pct_with = round((with_count / total) * 100, 1) if total else 0.0
        pct_without = round((without_count / total) * 100, 1) if total else 0.0
        r = pd.to_numeric(df["rating_num"], errors="coerce")
        avg_with = round(float(r[has].mean()), 2) if has.any() else None
        avg_without = round(float(r[~has].mean()), 2) if (~has).any() else None
        return {
            "total": total,
            "with_images": {"count": with_count, "pct": pct_with, "avg_rating": avg_with},
            "without_images": {"count": without_count, "pct": pct_without, "avg_rating": avg_without},
        }

    reviews = _extract_reviews_list(raw_json or {})
    total = int(len(reviews))
    with_images = 0
    without_images = 0
    ratings_with = []
    ratings_without = []
    for r in reviews:
        if not isinstance(r, dict):
            continue
        photos = r.get("photos")
        images = r.get("images")
        num_photos = r.get("num_photos")
        has = False
        if isinstance(photos, list):
            has = len(photos) > 0
        elif isinstance(images, list):
            has = len(images) > 0
        elif num_photos is not None:
            try:
                has = int(num_photos) > 0
            except Exception:
                has = False
        rating = _coerce_rating(r.get("rating"))
        if has:
            with_images += 1
            if rating is not None:
                ratings_with.append(rating)
        else:
            without_images += 1
            if rating is not None:
                ratings_without.append(rating)

    pct_with = round((with_images / total) * 100, 1) if total else 0.0
    pct_without = round((without_images / total) * 100, 1) if total else 0.0
    avg_with = round(float(np.mean(ratings_with)), 2) if ratings_with else None
    avg_without = round(float(np.mean(ratings_without)), 2) if ratings_without else None
    return {
        "total": total,
        "with_images": {"count": with_images, "pct": pct_with, "avg_rating": avg_with},
        "without_images": {"count": without_images, "pct": pct_without, "avg_rating": avg_without},
    }


def compute_invisible_popular_times(raw_json: dict) -> pd.DataFrame:
    popular_times = None
    if isinstance(raw_json, dict):
        popular_times = raw_json.get("popularTimes")
    if isinstance(popular_times, dict):
        rows = {}
        for day, entries in popular_times.items():
            if not isinstance(entries, list):
                continue
            vals = [0] * 24
            for item in entries:
                if not isinstance(item, dict):
                    continue
                hour_raw = item.get("hour")
                occ = item.get("occupancy", 0)
                try:
                    hour = int(str(hour_raw).split(":")[0].strip())
                except Exception:
                    continue
                if 0 <= hour <= 23:
                    try:
                        vals[hour] = int(occ)
                    except Exception:
                        vals[hour] = 0
            rows[str(day)] = vals
        if not rows:
            return pd.DataFrame(columns=[str(h) for h in range(24)])
        df = pd.DataFrame.from_dict(rows, orient="index", columns=[str(h) for h in range(24)])
        order = ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes", "sábado", "sabado", "sábados", "sabados", "domingo", "domingos"]
        idx_lower = {str(i).lower(): str(i) for i in df.index}
        ordered = [idx_lower[d] for d in order if d in idx_lower]
        rest = [i for i in df.index if i not in ordered]
        return df.loc[ordered + rest]

    if not isinstance(popular_times, list):
        return pd.DataFrame(columns=[str(h) for h in range(24)])

    rows = {}
    for day in popular_times:
        if not isinstance(day, dict):
            continue
        name = day.get("name")
        data = day.get("data")
        if not isinstance(name, str) or not isinstance(data, list):
            continue
        vals = []
        for h in range(24):
            v = data[h] if h < len(data) else 0
            try:
                vals.append(int(v))
            except Exception:
                vals.append(0)
        rows[name] = vals

    if not rows:
        return pd.DataFrame(columns=[str(h) for h in range(24)])

    df = pd.DataFrame.from_dict(rows, orient="index", columns=[str(h) for h in range(24)])
    order = ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes", "sábado", "sabado", "sábados", "sabados", "domingo", "domingos"]
    idx_lower = {str(i).lower(): str(i) for i in df.index}
    ordered = [idx_lower[d] for d in order if d in idx_lower]
    rest = [i for i in df.index if i not in ordered]
    df = df.loc[ordered + rest]
    return df


def compute_invisible_sample_cleaning(df_clean: pd.DataFrame, raw_json: dict) -> dict:
    raw_total = int(len(_extract_reviews_list(raw_json or {})))
    clean_total = int(len(df_clean)) if isinstance(df_clean, pd.DataFrame) else 0
    discarded = max(raw_total - clean_total, 0)
    pct_discarded = round((discarded / raw_total) * 100, 1) if raw_total else 0.0
    return {
        "raw_total": raw_total,
        "clean_total": clean_total,
        "discarded": discarded,
        "pct_discarded": pct_discarded,
    }


def _fmt_int_es(value) -> str:
    try:
        return f"{int(round(float(value))):,}".replace(",", ".")
    except Exception:
        return str(value)


def _is_popular_times_matrix(matrix) -> bool:
    if not isinstance(matrix, pd.DataFrame):
        return False
    cols = [str(c) for c in matrix.columns]
    if len(cols) != 24:
        return False
    if not all(c.isdigit() for c in cols):
        return False
    if sorted(int(c) for c in cols) != list(range(24)):
        return False
    data = pd.to_numeric(matrix.stack(), errors="coerce").dropna()
    if data.empty:
        return False
    return float(data.min()) >= 0 and float(data.max()) <= 100


def _best_text_color(facecolor) -> str:
    try:
        r, g, b, _ = mcolors.to_rgba(facecolor)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        return "black" if lum >= 0.62 else "white"
    except Exception:
        return "black"


def plot_donut(values, labels, output_path: str, colors=None, title: Optional[str] = None):
    output_path = str(output_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.5, 4.0), dpi=150)
    if colors is None:
        colors = ["#1E88E5", "#E0E0E0", "#43A047", "#FB8C00", "#E53935"]
    vals = [float(v) for v in values]
    total = float(np.sum(vals)) if len(vals) else 0.0
    legend_labels = []
    for name, v in zip(labels, vals):
        pct = (float(v) / total * 100.0) if total else 0.0
        legend_labels.append(f"{name}: {_fmt_int_es(v)} ({pct:.1f}%)")
    if len(vals) <= 6:
        idx = {"i": 0}

        def _autopct(pct):
            i = idx["i"]
            idx["i"] += 1
            v = vals[i] if i < len(vals) else 0.0
            return f"{_fmt_int_es(v)}\n({pct:.1f}%)"

        wedges, _, autotexts = ax.pie(
            vals,
            labels=None,
            startangle=90,
            colors=colors[: len(vals)],
            wedgeprops={"width": 0.45},
            autopct=_autopct,
            pctdistance=0.78,
        )
        for w, t in zip(wedges, autotexts):
            t.set_color(_best_text_color(w.get_facecolor()))
            t.set_fontsize(9)
            t.set_fontweight("bold")
        ax.legend(legend_labels, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
    else:
        ax.pie(vals, labels=None, startangle=90, colors=colors[: len(vals)], wedgeprops={"width": 0.45})
        ax.legend(legend_labels, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
    ax.axis("equal")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_bar_counts(labels, counts, output_path: str, title: Optional[str] = None):
    output_path = str(output_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=150)
    x = np.arange(len(labels))
    bars = ax.bar(x, counts, color="#1E88E5")
    ax.set_xticks(x, labels, rotation=0)
    ax.set_ylabel("Cantidad")
    if len(labels) <= 6:
        total = float(np.sum([float(c) for c in counts])) if len(counts) else 0.0
        y_max = max([float(b.get_height()) for b in bars], default=0.0)
        y_pad = max(y_max * 0.02, 0.5)
        for i, bar in enumerate(bars):
            v = float(bar.get_height())
            pct = (v / total * 100.0) if total else 0.0
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                v + y_pad,
                f"{_fmt_int_es(v)} ({pct:.1f}%)",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )
    if title:
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_heatmap(matrix: pd.DataFrame, output_path: str, title: Optional[str] = None, cmap: str = "Blues"):
    output_path = str(output_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    data = matrix.values.astype(float) if isinstance(matrix, pd.DataFrame) else np.array(matrix, dtype=float)
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=150)
    im = ax.imshow(data, aspect="auto", cmap=cmap)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    if isinstance(matrix, pd.DataFrame):
        ax.set_yticks(np.arange(matrix.shape[0]), [str(i) for i in matrix.index])
        ax.set_xticks(np.arange(matrix.shape[1]), [str(c) for c in matrix.columns])
    if title:
        ax.set_title(title)
    ax.set_xlabel("Hora" if (isinstance(matrix, pd.DataFrame) and all(str(c).isdigit() for c in matrix.columns)) else "")
    if int(data.size) <= 36:
        max_val = float(np.nanmax(data)) if data.size else 0.0
        if _is_popular_times_matrix(matrix):
            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    v = float(data[i, j])
                    color = "white" if max_val and v >= max_val * 0.6 else "black"
                    ax.text(j, i, f"{v:.0f} ({v:.0f}%)", ha="center", va="center", fontsize=7, color=color)
        else:
            total = float(np.nansum(data)) if data.size else 0.0
            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    v = float(data[i, j])
                    pct = (v / total * 100.0) if total else 0.0
                    color = "white" if max_val and v >= max_val * 0.6 else "black"
                    ax.text(j, i, f"{_fmt_int_es(v)} ({pct:.1f}%)", ha="center", va="center", fontsize=7, color=color)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


