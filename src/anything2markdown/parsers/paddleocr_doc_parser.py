"""Parser using PaddleOCR document-parsing API for structured markdown output."""

from __future__ import annotations

import base64
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import httpx
import structlog
from pypdf import PdfReader, PdfWriter

from ..config import settings
from ..schemas.result import ParseResult
from ..utils.file_utils import flatten_path
from ..utils.html_to_md import strip_html_noise
from ..utils.ocr_config import get_paddle_doc_skill_config, resolve_config_value
from .base import BaseParser

logger = structlog.get_logger(__name__)

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")


class PaddleOCRDocParser(BaseParser):
    """Structured document parser backed by PaddleOCR layout parsing API."""

    supported_extensions = [".pdf", *IMAGE_EXTENSIONS]
    parser_name = "paddle_doc"

    def __init__(self):
        self.skill_config = get_paddle_doc_skill_config()

    def is_available(self) -> bool:
        return bool(self._get_api_url() and self._get_token())

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    def parse(self, file_path: Path, output_dir: Path) -> ParseResult:
        started_at = datetime.now()
        logger.info("Paddle doc parsing", file=file_path.name)

        try:
            content, metadata = self._parse_file(file_path)
            output_name = flatten_path(file_path, settings.input_dir) + ".md"
            output_path = output_dir / output_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")

            completed_at = datetime.now()
            metadata["ocr_backend"] = "paddle_doc"
            return ParseResult(
                source_path=file_path,
                output_path=output_path,
                source_type="file",
                parser_used=self.parser_name,
                status="success",
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=(completed_at - started_at).total_seconds(),
                output_format="markdown",
                character_count=len(content),
                metadata=metadata,
            )
        except Exception as e:
            completed_at = datetime.now()
            logger.error("Paddle doc parsing failed", file=file_path.name, error=str(e))
            return ParseResult(
                source_path=file_path,
                output_path=Path(""),
                source_type="file",
                parser_used=self.parser_name,
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=(completed_at - started_at).total_seconds(),
                output_format="markdown",
                error_message=str(e),
            )

    def _parse_file(self, file_path: Path) -> tuple[str, dict[str, object]]:
        if file_path.suffix.lower() != ".pdf":
            result = self._request(file_path)
            return result["text"], {"page_count": 1}

        page_count = len(PdfReader(file_path).pages)
        if page_count <= settings.paddle_doc_max_pdf_pages:
            result = self._request(file_path)
            return result["text"], {"page_count": page_count}

        temp_dir = Path(tempfile.mkdtemp(prefix="paddle_doc_splits_"))
        try:
            parts = self._split_pdf(file_path, temp_dir, settings.paddle_doc_max_pdf_pages)
            texts: list[str] = []
            for part in parts:
                result = self._request(part)
                texts.append(result["text"])
            return "\n\n---\n\n".join(texts), {
                "page_count": page_count,
                "split_parts": len(parts),
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _split_pdf(self, file_path: Path, temp_dir: Path, pages_per_split: int) -> list[Path]:
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        parts: list[Path] = []

        for start in range(0, total_pages, pages_per_split):
            end = min(start + pages_per_split, total_pages)
            writer = PdfWriter()
            for page_num in range(start, end):
                writer.add_page(reader.pages[page_num])
            part_path = temp_dir / f"{file_path.stem}_part_{start + 1}_{end}.pdf"
            with open(part_path, "wb") as fh:
                writer.write(fh)
            parts.append(part_path)

        return parts

    def _request(self, file_path: Path) -> dict[str, str]:
        api_url = self._get_api_url()
        token = self._get_token()
        if not api_url or not token:
            raise RuntimeError("PaddleOCR document parsing API not configured")

        params: dict[str, object] = {
            "file": self._load_file_payload(file_path),
            "fileType": 0 if file_path.suffix.lower() == ".pdf" else 1,
            "useDocUnwarping": False,
            "useDocOrientationClassify": False,
            "useChartRecognition": False,
            "visualize": False,
        }
        headers = {
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
            "Client-Platform": "anything2markdown",
        }
        timeout = float(
            settings.paddleocr_doc_parsing_timeout
            or resolve_config_value(
                "PADDLEOCR_DOC_PARSING_TIMEOUT",
                file_config=self.skill_config,
            )
            or 600
        )

        with httpx.Client(timeout=timeout) as client:
            resp = client.post(api_url, json=params, headers=headers)
        resp.raise_for_status()
        raw = resp.json()
        if raw.get("errorCode", 0) != 0:
            raise RuntimeError(raw.get("errorMsg", "Unknown PaddleOCR document parsing error"))

        pages = raw.get("result", {}).get("layoutParsingResults", [])
        texts = []
        for page in pages:
            page_text = page.get("markdown", {}).get("text", "")
            page_text = strip_html_noise(page_text)
            if page_text:
                texts.append(page_text)

        return {"text": "\n\n".join(texts), "raw": raw}

    def _get_api_url(self) -> str:
        value = settings.paddleocr_doc_parsing_api_url or resolve_config_value(
            "PADDLEOCR_DOC_PARSING_API_URL",
            file_config=self.skill_config,
        )
        if value and not value.startswith(("http://", "https://")):
            value = f"https://{value}"
        return value

    def _get_token(self) -> str:
        return settings.paddleocr_access_token or resolve_config_value(
            "PADDLEOCR_ACCESS_TOKEN",
            file_config=self.skill_config,
        )

    @staticmethod
    def _load_file_payload(file_path: Path) -> str:
        return base64.b64encode(file_path.read_bytes()).decode("utf-8")
