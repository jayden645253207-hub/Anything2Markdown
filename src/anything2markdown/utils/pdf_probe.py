"""Lightweight PDF inspection for token-efficient routing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass
class PDFProbeResult:
    page_count: int
    sampled_pages: list[int]
    sample_text_lengths: list[int]
    average_text_length: float
    pages_with_text: int
    has_text_layer: bool


def _sample_page_indices(page_count: int, sample_pages: int) -> list[int]:
    if page_count <= 0:
        return []
    if page_count <= sample_pages:
        return list(range(page_count))

    candidates = {0, page_count - 1, page_count // 2}
    step = max(1, page_count // sample_pages)
    for idx in range(0, page_count, step):
        candidates.add(idx)
        if len(candidates) >= sample_pages:
            break
    return sorted(candidates)[:sample_pages]


def probe_pdf(
    file_path: Path,
    sample_pages: int = 3,
    min_chars_per_page: int = 80,
) -> PDFProbeResult:
    doc = fitz.open(file_path)
    try:
        page_count = len(doc)
        indices = _sample_page_indices(page_count, sample_pages)
        text_lengths: list[int] = []
        for index in indices:
            text = doc[index].get_text("text").strip()
            text_lengths.append(len(text))

        pages_with_text = sum(1 for value in text_lengths if value > 0)
        average_text_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0.0
        has_text_layer = any(value >= min_chars_per_page for value in text_lengths)

        return PDFProbeResult(
            page_count=page_count,
            sampled_pages=[index + 1 for index in indices],
            sample_text_lengths=text_lengths,
            average_text_length=average_text_length,
            pages_with_text=pages_with_text,
            has_text_layer=has_text_layer,
        )
    finally:
        doc.close()
