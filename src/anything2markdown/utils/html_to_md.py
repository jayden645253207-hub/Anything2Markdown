"""Strip HTML noise from OCR markdown output to reduce downstream LLM token cost.

PaddleOCR-VL (and similar layout-parsing backends) emit `<table>`, `<div>`,
`<img>` tags inside their markdown. These tags carry little semantic value
for an LLM and inflate token counts 3-5x. This utility converts tables to
markdown syntax and strips the rest.
"""

from __future__ import annotations

import re

_IMG_RE = re.compile(r"<img[^>]*/?>", re.IGNORECASE)
_DIV_OPEN_RE = re.compile(r"<div[^>]*>", re.IGNORECASE)
_DIV_CLOSE_RE = re.compile(r"</div\s*>", re.IGNORECASE)
_TABLE_RE = re.compile(r"<table[^>]*>(.*?)</table>", re.IGNORECASE | re.DOTALL)
_TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
_TD_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.IGNORECASE | re.DOTALL)
_ANY_TAG_RE = re.compile(r"<[^>]+>")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def _table_to_md(html_block: str) -> str:
    rows: list[list[str]] = []
    for tr in _TR_RE.findall(html_block):
        cells = [re.sub(r"\s+", " ", c).strip() for c in _TD_RE.findall(tr)]
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    n_cols = max(len(r) for r in rows)

    # 2-column tables from OCR are almost always key-value (e.g. 考核年度|2023),
    # so flatten them to "key: value" lines — much cleaner for LLMs.
    if n_cols == 2:
        return "\n".join(
            f"{row[0]}: {row[1] if len(row) > 1 else ''}".rstrip(": ").rstrip()
            for row in rows
        )

    # Real tables — render as markdown pipe table.
    lines: list[str] = []
    header = rows[0] + [""] * (n_cols - len(rows[0]))
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * n_cols) + " |")
    for row in rows[1:]:
        padded = row + [""] * (n_cols - len(row))
        lines.append("| " + " | ".join(padded) + " |")
    return "\n".join(lines)


def strip_html_noise(text: str) -> str:
    """
    Convert HTML-laden OCR markdown into clean markdown.

    - `<table>` blocks → markdown pipe table (or key:value lines if 2 columns)
    - `<img>` tags → removed (OCR-cropped image paths aren't useful downstream)
    - `<div>` wrappers → removed, inner content kept
    - any other stray tags → stripped
    - collapses excessive blank lines
    """
    if not text:
        return text

    # Convert tables first, while <tr>/<td> are still present.
    text = _TABLE_RE.sub(lambda m: "\n" + _table_to_md(m.group(1)) + "\n", text)

    text = _IMG_RE.sub("", text)
    text = _DIV_OPEN_RE.sub("", text)
    text = _DIV_CLOSE_RE.sub("", text)

    # Safety net for any stray tags left behind.
    text = _ANY_TAG_RE.sub("", text)

    # Normalize whitespace.
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()
