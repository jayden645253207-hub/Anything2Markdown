"""Parser using PaddleOCR text-recognition API for low-token OCR."""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

import httpx
import structlog

from ..config import settings
from ..schemas.result import ParseResult
from ..utils.file_utils import flatten_path
from ..utils.html_to_md import strip_html_noise
from ..utils.ocr_config import get_paddle_text_skill_config, resolve_config_value
from .base import BaseParser

logger = structlog.get_logger(__name__)

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")


class PaddleOCRTextParser(BaseParser):
    """OCR parser backed by PaddleOCR text-recognition API."""

    supported_extensions = [".pdf", *IMAGE_EXTENSIONS]
    parser_name = "paddle_text"

    def __init__(self):
        self.skill_config = get_paddle_text_skill_config()

    def is_available(self) -> bool:
        return bool(self._get_api_url() and self._get_token())

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    def parse(self, file_path: Path, output_dir: Path) -> ParseResult:
        started_at = datetime.now()
        logger.info("Paddle text OCR parsing", file=file_path.name)

        try:
            result = self._ocr(file_path)
            if not result.get("ok"):
                raise RuntimeError(result.get("error", {}).get("message", "OCR failed"))

            content = result.get("text", "").strip()
            output_name = flatten_path(file_path, settings.input_dir) + ".md"
            output_path = output_dir / output_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")

            completed_at = datetime.now()
            raw_result = result.get("result", {})
            page_count = len(raw_result.get("result", {}).get("ocrResults", []))
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
                metadata={
                    "page_count": page_count,
                    "ocr_backend": "paddle_text",
                },
            )
        except Exception as e:
            completed_at = datetime.now()
            logger.error("Paddle text OCR failed", file=file_path.name, error=str(e))
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

    def _ocr(self, file_path: Path) -> dict:
        api_url = self._get_api_url()
        token = self._get_token()
        if not api_url or not token:
            return {"ok": False, "error": {"message": "PaddleOCR text API not configured"}}

        params: dict[str, object] = {
            "file": self._load_file_payload(file_path),
            "visualize": False,
            "fileType": 0 if file_path.suffix.lower() == ".pdf" else 1,
            "useDocUnwarping": False,
            "useDocOrientationClassify": False,
        }

        headers = {
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
            "Client-Platform": "anything2markdown",
        }

        timeout = float(
            settings.paddleocr_ocr_timeout
            or resolve_config_value(
                "PADDLEOCR_OCR_TIMEOUT",
                file_config=self.skill_config,
            )
            or 120
        )

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(api_url, json=params, headers=headers)
            resp.raise_for_status()
            raw = resp.json()
        except Exception as e:
            return {"ok": False, "error": {"message": str(e)}}

        if raw.get("errorCode", 0) != 0:
            return {
                "ok": False,
                "error": {"message": raw.get("errorMsg", "Unknown PaddleOCR error")},
            }

        all_text: list[str] = []
        result_payload = raw.get("result", {})
        # The AI Studio endpoint returns layoutParsingResults (same shape as paddle_doc);
        # fall back to ocrResults for older/alternate endpoints.
        pages = result_payload.get("layoutParsingResults") or result_payload.get("ocrResults") or []
        for page in pages:
            md = page.get("markdown")
            if isinstance(md, dict):
                page_text = str(md.get("text", "")).strip()
            else:
                texts = page.get("prunedResult", {}).get("rec_texts", [])
                page_text = "\n".join(str(text) for text in texts if str(text).strip())
            page_text = strip_html_noise(page_text)
            if page_text:
                all_text.append(page_text)

        combined = "\n\n---\n\n".join(all_text).strip()
        if not combined:
            return {
                "ok": False,
                "error": {"message": "PaddleOCR returned empty text"},
            }

        return {
            "ok": True,
            "text": combined,
            "result": raw,
            "error": None,
        }

    def _get_api_url(self) -> str:
        value = settings.paddleocr_ocr_api_url or resolve_config_value(
            "PADDLEOCR_OCR_API_URL",
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
