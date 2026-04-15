"""Pluggable external OCR parser for local tools such as Manner OCR."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

import structlog

from ..config import settings
from ..schemas.result import ParseResult
from ..utils.file_utils import flatten_path
from .base import BaseParser

logger = structlog.get_logger(__name__)

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")


class MannerOCRParser(BaseParser):
    """
    Generic external-command OCR parser.

    Configure `MANNER_OCR_COMMAND` as a shell template. Supported placeholders:
    - `{input}`  absolute input path
    - `{output}` absolute markdown output path

    If the command writes to stdout instead of `{output}`, stdout is persisted as
    the markdown result.
    """

    supported_extensions = [".pdf", *IMAGE_EXTENSIONS]
    parser_name = "manner"

    def is_available(self) -> bool:
        return bool(settings.manner_ocr_command.strip())

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    def parse(self, file_path: Path, output_dir: Path) -> ParseResult:
        started_at = datetime.now()
        output_name = flatten_path(file_path, settings.input_dir) + ".md"
        output_path = output_dir / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            template = settings.manner_ocr_command.strip()
            if not template:
                raise RuntimeError("MANNER_OCR_COMMAND not configured")

            command = template.format(input=str(file_path.resolve()), output=str(output_path.resolve()))
            proc = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True,
                timeout=settings.manner_ocr_timeout,
            )
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "Manner OCR failed")

            if output_path.exists() and output_path.stat().st_size > 0:
                content = output_path.read_text(encoding="utf-8")
            else:
                content = proc.stdout.strip()
                if not content:
                    raise RuntimeError("Manner OCR command produced no markdown output")
                output_path.write_text(content, encoding="utf-8")

            completed_at = datetime.now()
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
                metadata={"ocr_backend": "manner"},
            )
        except Exception as e:
            completed_at = datetime.now()
            logger.error("Manner OCR failed", file=file_path.name, error=str(e))
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
