import sys
import re
from collections import Counter
from pathlib import Path

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


docx_path = r"RUTA_AL_DOCX"


def iter_block_items(parent):
    body = parent.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def is_heading(paragraph: Paragraph) -> bool:
    style = getattr(paragraph.style, "name", None)
    return isinstance(style, str) and style.startswith("Heading")


def scan_text(violations, idx, where, text):
    t = (text or "").strip()
    if not t:
        return
    if "None" in t:
        violations.append((idx, "TEXT_CONTAINS_NONE", where, t))
    if "NO DISPONIBLE" in t:
        violations.append((idx, "TEXT_CONTAINS_NO_DISPONIBLE", where, t))


def scan_table(violations, idx, table: Table):
    for r_i, row in enumerate(table.rows):
        for c_i, cell in enumerate(row.cells):
            scan_text(violations, idx, f"TABLE_CELL r{r_i}c{c_i}", cell.text)


def audit_docx_structure(path):
    p = Path(path)
    if not p.exists():
        return {
            "docx_path": str(p),
            "exists": False,
            "tables": 0,
            "heading3_count": 0,
            "violations": [("N/A", "DOCX_NOT_FOUND", str(p))],
            "table_titles_in_order": [],
        }

    doc = Document(str(p))

    last_heading3_text = None
    last_heading3_idx = None
    headings3_all = []
    table_titles_in_order = []
    heading3_instances_used_by_tables = []

    tables = 0
    violations = []

    pending_heading = None

    h2_re = re.compile(r"^(?P<num>\d+)\.\s+(?P<title>.+)$")
    h3_re = re.compile(r"^(?P<h2>\d+)\.(?P<h3>\d+)\.\s+(?P<title>.+)$")

    expected_h2 = 1
    current_h2_num = None
    expected_h3 = 1
    seen_h2_titles = set()
    seen_h3_titles_in_current_h2 = set()

    def close_pending_heading_as_empty(next_idx, reason):
        nonlocal pending_heading
        if pending_heading is None:
            return
        h_idx, h_style, h_text = pending_heading
        violations.append((h_idx, reason, h_style, h_text, f"NEXT_BLOCK_IDX={next_idx}"))
        pending_heading = None

    def mark_pending_heading_has_body():
        nonlocal pending_heading
        pending_heading = None

    for idx, block in enumerate(iter_block_items(doc)):
        if isinstance(block, Paragraph):
            text = (block.text or "").strip()
            style = getattr(block.style, "name", None)

            scan_text(violations, idx, "PARAGRAPH", text)

            if text and is_heading(block):
                close_pending_heading_as_empty(idx, "HEADING_WITHOUT_BODY")
                pending_heading = (idx, style, text)

            if text and style == "Heading 2":
                m = h2_re.match(text)
                if not m:
                    violations.append((idx, "INVALID_H2_NUMERATION", style, text))
                else:
                    h2_num = int(m.group("num"))
                    h2_title = m.group("title").strip()
                    if h2_num != expected_h2:
                        violations.append((idx, "H2_NUMERATION_NOT_CONTINUOUS", expected_h2, h2_num, text))
                    expected_h2 = h2_num + 1
                    current_h2_num = h2_num
                    expected_h3 = 1
                    seen_h3_titles_in_current_h2 = set()

                    key = h2_title.lower()
                    if key in seen_h2_titles:
                        violations.append((idx, "DUPLICATE_HEADING_2_TITLE", h2_title))
                    seen_h2_titles.add(key)

            if text and style == "Heading 3":
                m = h3_re.match(text)
                if not m:
                    violations.append((idx, "INVALID_H3_NUMERATION", style, text))
                else:
                    h2_part = int(m.group("h2"))
                    h3_part = int(m.group("h3"))
                    h3_title = m.group("title").strip()

                    if current_h2_num is not None and h2_part != current_h2_num:
                        violations.append((idx, "H3_SECTION_MISMATCH", current_h2_num, h2_part, text))
                    if h3_part != expected_h3:
                        violations.append((idx, "H3_NUMERATION_NOT_CONTINUOUS", f"{current_h2_num}.{expected_h3}", f"{h2_part}.{h3_part}", text))
                    expected_h3 = h3_part + 1

                    key = h3_title.lower()
                    if key in seen_h3_titles_in_current_h2:
                        violations.append((idx, "DUPLICATE_HEADING_3_TITLE_IN_H2", h3_title, f"H2={current_h2_num}"))
                    seen_h3_titles_in_current_h2.add(key)

                last_heading3_text = text
                last_heading3_idx = idx
                headings3_all.append(text)

            if text and (not is_heading(block)):
                mark_pending_heading_has_body()

        elif isinstance(block, Table):
            tables += 1
            scan_table(violations, idx, block)

            if pending_heading is not None:
                mark_pending_heading_has_body()

            if not last_heading3_text:
                violations.append((idx, "TABLE_WITHOUT_PREV_HEADING_3"))
            else:
                if not h3_re.match(last_heading3_text):
                    violations.append((idx, "TABLE_WITHOUT_PREV_NUMBERED_HEADING_3", last_heading3_text))
                table_titles_in_order.append(last_heading3_text)
                heading3_instances_used_by_tables.append((last_heading3_idx, last_heading3_text))

    close_pending_heading_as_empty("EOF", "HEADING_WITHOUT_BODY")

    unique_heading3_instances_used_by_tables = set(heading3_instances_used_by_tables)
    used_heading3_texts = [t for _, t in unique_heading3_instances_used_by_tables]
    heading3_used_counts = Counter(used_heading3_texts)
    duplicates_used_by_tables = sorted([t for t, c in heading3_used_counts.items() if c > 1])

    used_heading3_instance_counts = Counter(heading3_instances_used_by_tables)
    repeated_same_heading_instance = sorted(
        [(i, t, c) for (i, t), c in used_heading3_instance_counts.items() if c > 1],
        key=lambda x: x[0],
    )

    return {
        "docx_path": str(p),
        "exists": True,
        "tables": tables,
        "heading3_count": len(headings3_all),
        "violations": violations,
        "table_titles_in_order": table_titles_in_order,
        "duplicates_used_by_tables": duplicates_used_by_tables,
        "repeated_same_heading_instance": repeated_same_heading_instance,
    }


def _print_audit_report(result):
    p = result.get("docx_path")
    tables = int(result.get("tables", 0) or 0)
    heading3_count = int(result.get("heading3_count", 0) or 0)
    violations = result.get("violations") or []
    table_titles_in_order = result.get("table_titles_in_order") or []
    duplicates_used_by_tables = result.get("duplicates_used_by_tables") or []
    repeated_same_heading_instance = result.get("repeated_same_heading_instance") or []

    print(f"DOCX: {p}")
    print(f"Tables found: {tables}")
    print(f"Heading 3 titles (non-empty): {heading3_count}")

    if violations:
        print("\nVIOLATIONS:")
        for v in violations:
            print("-", v)
    else:
        print("\nOK: Sin violaciones detectadas.")

    print("\nTable titles in order:")
    for i, title in enumerate(table_titles_in_order, 1):
        print(f"{i:02d}. {title}")

    if duplicates_used_by_tables:
        print("\nDUPLICATE Heading 3 titles used by tables (distinct titles repeated):")
        for t in duplicates_used_by_tables:
            print("-", t)

    if repeated_same_heading_instance:
        print("\nINFO: Multiple tables under the same Heading 3 instance:")
        for i, t, c in repeated_same_heading_instance:
            print(f"- IDX={i} TITLE={t} TABLES={c}")


def main():
    path = docx_path
    if len(sys.argv) > 1 and sys.argv[1].strip():
        path = sys.argv[1].strip().strip('"')

    result = audit_docx_structure(path)
    if not result.get("exists", False):
        print(f"❌ DOCX no encontrado: {result.get('docx_path')}")
        return 1

    _print_audit_report(result)
    return 1 if (result.get("violations") or []) else 0


if __name__ == "__main__":
    raise SystemExit(main())

