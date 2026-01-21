def compute_alerts(cfg: dict) -> dict:
    """
    Genera alertas deterministas basadas en scores.
    """
    alerts = []

    dcs = cfg.get("artifact_contradiction_score", {})
    ofs = cfg.get("artifact_fatigue_score", {})

    dcs_score = dcs.get("score")
    ofs_score = ofs.get("score")

    if isinstance(dcs_score, (int, float)):
        if dcs_score < 65:
            alerts.append({
                "code": "DISCOURSE_INCONSISTENCY",
                "metric": "DCS",
                "value": dcs_score,
                "severity": "HIGH",
                "message": "Alto nivel de contradicciones entre puntuación y discurso"
            })
        elif dcs_score < 80:
            alerts.append({
                "code": "DISCOURSE_INCONSISTENCY",
                "metric": "DCS",
                "value": dcs_score,
                "severity": "MEDIUM",
                "message": "Inconsistencias detectadas entre puntuación y discurso"
            })

    if isinstance(ofs_score, (int, float)):
        if ofs_score < 60:
            alerts.append({
                "code": "OPERATIONAL_FATIGUE",
                "metric": "OFS",
                "value": ofs_score,
                "severity": "HIGH",
                "message": "Señales claras de fatiga operativa"
            })
        elif ofs_score < 75:
            alerts.append({
                "code": "OPERATIONAL_FATIGUE",
                "metric": "OFS",
                "value": ofs_score,
                "severity": "MEDIUM",
                "message": "Señales de fatiga operativa moderada"
            })

    return {
        "alerts": alerts
    }

