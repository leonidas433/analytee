import pandas as pd


def compute_participation_bias(df: pd.DataFrame) -> dict:
    """
    Cálculo determinista de la métrica:
    Participation Bias Metric (PBM).
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "metric": "Participation Bias Metric",
            "version": "v1",
            "dominant_reviewer_type": "UNKNOWN",
            "contribution_ratio": 0.0,
            "bias_risk": "LOW",
            "notes": "Métrica calculada a partir de recuentos de reseñas por tipo de revisor.",
        }

    work_df = df.copy()

    if "is_local_guide" not in work_df.columns:
        work_df["is_local_guide"] = False

    if "has_images" not in work_df.columns:
        work_df["has_images"] = False

    lg = work_df["is_local_guide"].fillna(False).astype(bool)
    has_img = work_df["has_images"].fillna(False).astype(bool)

    segments = {
        "LOCAL_GUIDE_WITH_IMAGES": int((lg & has_img).sum()),
        "LOCAL_GUIDE_NO_IMAGES": int((lg & ~has_img).sum()),
        "NON_LOCAL_GUIDE_WITH_IMAGES": int((~lg & has_img).sum()),
        "NON_LOCAL_GUIDE_NO_IMAGES": int((~lg & ~has_img).sum()),
    }

    total_reviews = sum(segments.values())
    if total_reviews <= 0:
        return {
            "metric": "Participation Bias Metric",
            "version": "v1",
            "dominant_reviewer_type": "UNKNOWN",
            "contribution_ratio": 0.0,
            "bias_risk": "LOW",
            "notes": "Métrica calculada a partir de recuentos de reseñas por tipo de revisor.",
        }

    dominant_reviewer_type, dominant_count = max(
        segments.items(),
        key=lambda item: item[1],
    )

    contribution_ratio = dominant_count / float(total_reviews)

    if contribution_ratio >= 0.45:
        bias_risk = "HIGH"
    elif contribution_ratio >= 0.30:
        bias_risk = "MEDIUM"
    else:
        bias_risk = "LOW"

    return {
        "metric": "Participation Bias Metric",
        "version": "v1",
        "dominant_reviewer_type": dominant_reviewer_type,
        "contribution_ratio": float(contribution_ratio),
        "bias_risk": bias_risk,
        "notes": "Métrica calculada a partir de recuentos de reseñas por tipo de revisor.",
    }

