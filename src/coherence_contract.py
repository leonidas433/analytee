import hashlib
import re
from typing import Dict, Any


def _hash_text(text: str) -> str:
    """
    Calcular SHA256 hex de un texto.
    Si text es None, se usa cadena vacía.
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        text = str(text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _contains_forbidden_tokens(text: str) -> Dict[str, bool]:
    """
    Detectar presencia de elementos prohibidos en texto cliente.
    - Dígitos
    - Palabras asociadas a scores/ratios/alertas
    - Tablas Markdown (líneas con '|' repetido)
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        text = str(text)

    has_digits = bool(re.search(r"\d", text))

    lower_text = text.lower()
    score_words = [
        "score",
        "dcs",
        "ofs",
        "severity",
        "alert",
        "ratio",
        "percent",
        "%",
    ]
    has_score_words = any(word in lower_text for word in score_words)

    has_tables = False
    for line in text.splitlines():
        if line.count("|") >= 2:
            has_tables = True
            break

    return {
        "has_digits": has_digits,
        "has_score_words": has_score_words,
        "has_tables": has_tables,
    }


def build_contract(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construir contrato de coherencia AUDIT vs CLIENTE.
    No modifica cfg, solo lee los campos necesarios.
    """
    metrics_version = str(cfg.get("metrics_version", "v1"))
    audit_text = cfg.get("audit_text") or ""
    client_text = cfg.get("client_derived_text")

    audit_hash = _hash_text(audit_text)
    client_hash = _hash_text(client_text) if client_text is not None else _hash_text("")

    if not client_text:
        client_checks = {
            "has_digits": False,
            "has_score_words": False,
            "has_tables": False,
        }
        status = "PASS"
    else:
        client_checks = _contains_forbidden_tokens(client_text)
        if (
            client_checks.get("has_digits")
            or client_checks.get("has_score_words")
            or client_checks.get("has_tables")
        ):
            status = "FAIL"
        else:
            status = "PASS"

    return {
        "metrics_version": metrics_version,
        "audit_hash": audit_hash,
        "client_hash": client_hash,
        "client_checks": client_checks,
        "status": status,
    }

