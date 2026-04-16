"""MCP server for Anything2Markdown.

Exposes tools:
- parse_file : Convert local files (PDF/Word/PPT/Excel/image/etc.) to Markdown.
- parse_url  : Convert URLs (web pages, YouTube, Bilibili, GitHub, etc.) to Markdown.
- list_supported_extensions : Return supported file extensions.

Usage (stdio transport):
    python -m anything2markdown.mcp_server
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project src is on path when run directly via `python -m`.
# Not needed when the package is installed with `pip install -e .`.
_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from mcp.server.fastmcp import FastMCP

from anything2markdown.config import settings
from anything2markdown.router import Router
from anything2markdown.utils.file_utils import ensure_directory

mcp = FastMCP("anything2md")


def _pdf_fallback(router: Router, path: Path, result):
    """Apply the same PDF OCR fallback logic used by the CLI."""
    if (
        path.suffix.lower() == ".pdf"
        and result.parser_used == "markitdown"
        and result.status == "failed"
    ):
        ocr_parser = router.get_ocr_fallback_parser()
        result = ocr_parser.parse(path, settings.output_dir)

    if (
        path.suffix.lower() == ".pdf"
        and result.status == "success"
        and result.parser_used == "markitdown"
        and result.output_path
        and result.output_path.exists()
    ):
        output_content = result.output_path.read_text(encoding="utf-8")
        if router.should_fallback_to_ocr(output_content):
            result.output_path.unlink(missing_ok=True)
            ocr_parser = router.get_ocr_fallback_parser()
            result = ocr_parser.parse(path, settings.output_dir)

    return result


@mcp.tool()
async def parse_file(file_path: str, strategy: str = "token_efficient") -> str:
    """Parse a local file into clean Markdown.

    Supports PDF, Word, PPT, Excel, images, HTML, EPUB, CSV, JSON, TXT, MD, etc.

    Args:
        file_path: Absolute path to the file.
        strategy: 'token_efficient' (default, faster/cheaper) or 'balanced'.
    """
    path = Path(file_path)
    if not path.exists():
        return f"Error: file not found: {file_path}"

    ensure_directory(settings.output_dir)
    if strategy:
        settings.parsing_strategy = strategy

    router = Router()
    try:
        parser = router.route_file(path)
        result = parser.parse(path, settings.output_dir)
        result = _pdf_fallback(router, path, result)

        if result.status == "success" and result.output_path and result.output_path.exists():
            text = result.output_path.read_text(encoding="utf-8")
            return (
                f"Status: success\n"
                f"Parser: {result.parser_used}\n"
                f"Characters: {result.character_count}\n\n"
                f"{text}"
            )
        return f"Status: {result.status}\nError: {result.error_message or 'Unknown error'}"
    except KeyboardInterrupt:
        raise
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def parse_url(url: str) -> str:
    """Parse a URL into clean Markdown.

    Supports web pages (via Firecrawl), YouTube transcripts, Bilibili, GitHub repos, etc.

    Args:
        url: The URL to parse.
    """
    ensure_directory(settings.output_dir)
    router = Router()
    try:
        parser = router.route_url(url)
        result = parser.parse(url, settings.output_dir)

        if result.status == "success" and result.output_path and result.output_path.exists():
            text = result.output_path.read_text(encoding="utf-8")
            return (
                f"Status: success\n"
                f"Parser: {result.parser_used}\n"
                f"Characters: {result.character_count}\n\n"
                f"{text}"
            )
        return f"Status: {result.status}\nError: {result.error_message or 'Unknown error'}"
    except KeyboardInterrupt:
        raise
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def list_supported_extensions() -> list[str]:
    """Return the list of file extensions supported by Anything2Markdown."""
    return [
        ".pdf",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        ".csv",
        ".html",
        ".htm",
        ".epub",
        ".txt",
        ".md",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".tiff",
        ".webp",
    ]


if __name__ == "__main__":
    mcp.run(transport="stdio")
