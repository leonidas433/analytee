from copy import deepcopy


def is_audit_mode(cfg: dict) -> bool:
    return str(cfg.get("report_mode", "client")).lower() == "audit"


def redact_for_client(cfg: dict) -> dict:
    sanitized = deepcopy(cfg)

    sanitized["alerts"] = {"alerts": []}

    dcs = sanitized.get("artifact_contradiction_score")
    if isinstance(dcs, dict):
        level = dcs.get("level")
        sanitized["artifact_contradiction_score"] = {"level": level} if level is not None else {}

    ofs = sanitized.get("artifact_fatigue_score")
    if isinstance(ofs, dict):
        level = ofs.get("level")
        sanitized["artifact_fatigue_score"] = {"level": level} if level is not None else {}

    contradictions = sanitized.get("artifact_contradictions")
    if isinstance(contradictions, dict):
        contradictions = contradictions.copy()
        contradictions["examples"] = []
        sanitized["artifact_contradictions"] = contradictions

    fatigue = sanitized.get("artifact_operational_fatigue")
    if isinstance(fatigue, dict):
        fatigue = fatigue.copy()
        fatigue["repeated_complaints"] = []
        sanitized["artifact_operational_fatigue"] = fatigue

    return sanitized

