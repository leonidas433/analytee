from __future__ import annotations

import os
from pathlib import Path

from docx import Document


def _iter_container_text(container):
    for p in getattr(container, "paragraphs", []) or []:
        yield p.text
    for table in getattr(container, "tables", []) or []:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p.text


def _collect_doc_text(doc: Document) -> str:
    chunks = []

    for t in _iter_container_text(doc):
        if t:
            chunks.append(t)

    for section in getattr(doc, "sections", []) or []:
        for t in _iter_container_text(section.header):
            if t:
                chunks.append(t)
        for t in _iter_container_text(section.footer):
            if t:
                chunks.append(t)

    return "\n".join(chunks)


def validate_docx_no_ai_text(docx_path: Path) -> None:
    docx_path = Path(docx_path)
    doc = Document(str(docx_path))
    text = _collect_doc_text(doc)
    lower = text.lower()

    signals = [
        "🤖",
        "Análisis Inteligente",
        "Plan de Acción Estratégico",
        "Lectura estratégica",
        "Métricas Invisibles — Capa Cliente",
    ]

    for token in signals:
        if token == "🤖":
            if token in text:
                raise RuntimeError(f"Guardrails: texto IA detectado en DOCX ({docx_path}): {token}")
        else:
            if token.lower() in lower:
                raise RuntimeError(f"Guardrails: texto IA detectado en DOCX ({docx_path}): {token}")

    audit_mode = False
    if str(os.environ.get("AUDIT_MODE", "")).strip() in ("1", "true", "True", "TRUE", "yes", "YES"):
        audit_mode = True
    if str(os.environ.get("REPORT_MODE", "")).strip().upper() == "AUDIT":
        audit_mode = True

    if audit_mode:
        audit_tokens = [
            "recomendación",
            "recomendacion",
            "oportunidad",
            "estratégic",
            "estrategic",
        ]
        for token in audit_tokens:
            if token in lower:
                raise RuntimeError(f"Guardrails: texto IA detectado en DOCX ({docx_path}): {token}")
