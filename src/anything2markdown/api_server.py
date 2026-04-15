"""FastAPI HTTP server for Anything2Markdown.

Endpoints:
- POST /convert       : Upload a file, get Markdown text back.
- POST /convert/url   : Submit a URL, get Markdown text back.
- GET  /health        : Health check.

Usage:
    python -m anything2markdown.api_server

Default address: http://127.0.0.1:7861
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import PlainTextResponse

# Ensure project src is on path when run directly via `python -m`.
# Not needed when the package is installed with `pip install -e .`.
_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from anything2markdown.config import settings
from anything2markdown.router import Router
from anything2markdown.utils.file_utils import ensure_directory
from anything2markdown.utils.logging_setup import setup_logging

setup_logging()

app = FastAPI(title="Anything2Markdown API", version="0.1.0")


def _pdf_fallback(router: Router, path: Path, result):
    """Apply the same PDF OCR fallback logic used by the CLI."""
    if (
        path.suffix.lower() == ".pdf"
        and result.parser_name == "markitdown"
        and result.status == "failed"
    ):
        ocr_parser = router.get_ocr_fallback_parser()
        result = ocr_parser.parse(path, settings.output_dir)

    if (
        path.suffix.lower() == ".pdf"
        and result.status == "success"
        and result.parser_name == "markitdown"
        and result.output_path
        and result.output_path.exists()
    ):
        output_content = result.output_path.read_text(encoding="utf-8")
        if router.should_fallback_to_ocr(output_content):
            result.output_path.unlink(missing_ok=True)
            ocr_parser = router.get_ocr_fallback_parser()
            result = ocr_parser.parse(path, settings.output_dir)

    return result


@app.get("/health")
async def health():
    return {"status": "ok", "service": "anything2md"}


@app.post("/convert", response_class=PlainTextResponse)
async def convert_file(
    file: UploadFile = File(...),
    strategy: str = Form("token_efficient"),
):
    """Upload a file and return its Markdown content.

    Form fields:
        file     : The file to convert (required).
        strategy : 'token_efficient' (default) or 'balanced'.
    """
    ensure_directory(settings.output_dir)
    if strategy:
        settings.parsing_strategy = strategy

    suffix = Path(file.filename or "tmp").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        router = Router()
        parser = router.route_file(tmp_path)
        result = parser.parse(tmp_path, settings.output_dir)
        result = _pdf_fallback(router, tmp_path, result)

        if result.status == "success" and result.output_path and result.output_path.exists():
            return result.output_path.read_text(encoding="utf-8")
        return f"Error: {result.error_message or 'Conversion failed'}"
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/convert/url", response_class=PlainTextResponse)
async def convert_url(url: str = Form(...)):
    """Submit a URL and return its Markdown content.

    Form fields:
        url : The URL to convert (required).
    """
    ensure_directory(settings.output_dir)
    router = Router()
    try:
        parser = router.route_url(url)
        result = parser.parse(url, settings.output_dir)

        if result.status == "success" and result.output_path and result.output_path.exists():
            return result.output_path.read_text(encoding="utf-8")
        return f"Error: {result.error_message or 'Conversion failed'}"
    except KeyboardInterrupt:
        raise
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7861)
