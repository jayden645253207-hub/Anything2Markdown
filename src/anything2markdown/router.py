"""Front desk routing logic - determines which parser handles each file/URL."""

import re
from pathlib import Path
from urllib.parse import urlparse

import structlog

from .config import settings
from .parsers import (
    MannerOCRParser,
    MarkItDownParser,
    MinerUParser,
    PaddleOCRDocParser,
    PaddleOCRTextParser,
    PaddleOCRVLParser,
    TabularParser,
)
from .parsers.base import BaseParser
from .url_parsers import BilibiliParser, FireCrawlParser, RepomixParser, YouTubeParser
from .url_parsers.base import BaseURLParser
from .utils.file_utils import get_file_size_mb
from .utils.pdf_probe import PDFProbeResult, probe_pdf

logger = structlog.get_logger(__name__)

# Pre-compiled pattern for OCR fallback quality check
_VALID_CHARS_PATTERN = re.compile(r"[\w\s.,!?;:'\"-]")


class Router:
    """
    Front desk script that routes files/URLs to appropriate parsers.
    Routing logic based on file extension, size, and URL patterns.
    """

    # File extension to parser mapping
    EXTENSION_MAP = {
        # MarkItDown handles these
        ".pdf": "markitdown",  # May fallback to MinerU
        ".ppt": "markitdown",
        ".pptx": "markitdown",
        ".doc": "markitdown",
        ".docx": "markitdown",
        ".html": "markitdown",
        ".htm": "markitdown",
        ".epub": "markitdown",
        ".md": "markitdown",
        ".txt": "markitdown",
        # Tabular data
        ".xlsx": "tabular",
        ".xls": "tabular",
        ".csv": "tabular",
    }

    IMAGE_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif",
    }

    # Extensions to silently skip (no useful text content)
    SKIP_EXTENSIONS = {
        ".svg", ".ico",
        ".mp3", ".mp4", ".wav", ".avi", ".mov", ".flv", ".wmv",
        ".css", ".js", ".hhc", ".hhk",
    }

    # URL patterns for auto-detection
    YOUTUBE_PATTERNS = [
        r"youtube\.com/watch",
        r"youtu\.be/",
        r"youtube\.com/embed/",
    ]

    BILIBILI_PATTERNS = [
        r"bilibili\.com/video/",
        r"b23\.tv/",
        r"bilibili\.com/bangumi/",
    ]

    GITHUB_REPO_PATTERNS = [
        r"github\.com/[\w-]+/[\w-]+/?$",
        r"github\.com/[\w-]+/[\w-]+\.git$",
    ]

    def __init__(self):
        """Initialize all parsers."""
        # File parsers
        self.parsers: dict[str, BaseParser] = {
            "markitdown": MarkItDownParser(),
            "mineru": MinerUParser(),
            "manner": MannerOCRParser(),
            "paddle_doc": PaddleOCRDocParser(),
            "paddle_text": PaddleOCRTextParser(),
            "paddleocr_vl": PaddleOCRVLParser(),
            "tabular": TabularParser(),
        }

        # URL parsers
        self.url_parsers: dict[str, BaseURLParser] = {
            "firecrawl": FireCrawlParser(),
            "youtube": YouTubeParser(),
            "bilibili": BilibiliParser(),
            "repomix": RepomixParser(),
        }

    def route_file(self, file_path: Path) -> BaseParser:
        """
        Determine which parser to use for a file.

        Routing rules:
        1. Route by extension (MinerU disabled due to network issues)

        Args:
            file_path: Path to the file

        Returns:
            Appropriate parser instance

        Raises:
            ValueError: If file type is not supported
        """
        extension = file_path.suffix.lower()

        # Skip known non-text extensions silently
        if extension in self.SKIP_EXTENSIONS:
            logger.debug("Skipping non-text file", extension=extension, file=file_path.name)
            raise ValueError(f"Skipped non-text file: {extension}")

        if extension in self.IMAGE_EXTENSIONS:
            return self._resolve_parser(
                [settings.image_ocr_parser, "paddle_text", "paddle_doc", "manner"],
                file_path=file_path,
                reason="image OCR",
            )

        if extension == ".pdf":
            return self._route_pdf(file_path)

        # Get initial parser based on extension
        parser_key = self.EXTENSION_MAP.get(extension)

        if parser_key is None:
            logger.warning("No parser for extension", extension=extension, file=file_path.name)
            raise ValueError(f"Unsupported file type: {extension}")

        # NOTE: MinerU routing disabled due to network connectivity issues
        # to Alibaba Cloud Shanghai. Using MarkItDown for all PDFs.
        # To re-enable, uncomment the following:
        # if extension == ".pdf" and self._should_use_mineru_for_size(file_path):
        #     logger.info("Routing to MinerU (size threshold)", file=file_path.name)
        #     return self.parsers["mineru"]

        return self._resolve_parser([parser_key], file_path=file_path, reason="extension match")

    _ALLOWED_SCHEMES = {"http", "https"}

    def route_url(self, url: str) -> BaseURLParser:
        """
        Determine which URL parser to use based on URL pattern.

        Routing rules:
        1. YouTube URLs -> YouTubeParser
        2. GitHub repo URLs -> RepomixParser
        3. Other URLs -> FireCrawlParser

        Args:
            url: URL to parse

        Returns:
            Appropriate URL parser instance

        Raises:
            ValueError: If URL scheme is not allowed.
        """
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme.lower() not in self._ALLOWED_SCHEMES:
            raise ValueError(
                f"Unsupported URL scheme: {parsed.scheme!r}. Only http/https allowed."
            )

        url_lower = url.lower()

        # Check YouTube patterns
        for pattern in self.YOUTUBE_PATTERNS:
            if re.search(pattern, url_lower):
                logger.info("Routing URL to YouTube parser", url=url)
                return self.url_parsers["youtube"]

        # Check Bilibili patterns
        for pattern in self.BILIBILI_PATTERNS:
            if re.search(pattern, url_lower):
                logger.info("Routing URL to Bilibili parser", url=url)
                return self.url_parsers["bilibili"]

        # Check GitHub repo patterns
        for pattern in self.GITHUB_REPO_PATTERNS:
            if re.search(pattern, url_lower):
                # Make sure it's not a specific page (issues, PRs, etc.)
                excluded = ["/issues", "/pull", "/blob/", "/tree/", "/releases", "/actions"]
                if not any(ex in url_lower for ex in excluded):
                    logger.info("Routing URL to Repomix parser", url=url)
                    return self.url_parsers["repomix"]

        # Default to FireCrawl for general websites
        logger.info("Routing URL to FireCrawl parser", url=url)
        return self.url_parsers["firecrawl"]

    def _should_use_mineru_for_size(self, file_path: Path) -> bool:
        """
        Check if PDF should be routed to MinerU based on file size.

        Args:
            file_path: Path to the PDF file

        Returns:
            True if file exceeds size threshold
        """
        size_mb = get_file_size_mb(file_path)
        if size_mb > settings.max_pdf_size_mb:
            logger.info(
                "PDF exceeds size threshold",
                file=file_path.name,
                size_mb=f"{size_mb:.2f}",
                threshold_mb=settings.max_pdf_size_mb,
            )
            return True
        return False

    def should_fallback_to_ocr(self, text_content: str) -> bool:
        """
        Check if MarkItDown result should fallback to OCR.
        Called after MarkItDown parsing to check content quality.

        Args:
            text_content: Extracted text content from MarkItDown

        Returns:
            True if content quality is too low
        """
        # Count valid characters (alphanumeric + common punctuation)
        valid_chars = sum(1 for _ in _VALID_CHARS_PATTERN.finditer(text_content))

        if valid_chars < settings.min_valid_chars:
            logger.info(
                "Low valid chars, fallback to OCR",
                valid_chars=valid_chars,
                threshold=settings.min_valid_chars,
            )
            return True

        return False

    def get_ocr_fallback_parser(self) -> BaseParser:
        """Get the preferred OCR fallback parser for scanned or low-quality PDFs."""
        return self._resolve_parser(
            [
                settings.pdf_ocr_fallback_parser,
                settings.scanned_pdf_parser,
                "paddle_text",
                "paddle_doc",
                "manner",
                "paddleocr_vl",
                "mineru",
            ],
            reason="PDF OCR fallback",
        )

    def _route_pdf(self, file_path: Path) -> BaseParser:
        if settings.parsing_strategy != "token_efficient":
            return self._resolve_parser(["markitdown"], file_path=file_path, reason="balanced PDF")

        pdf_probe = self._probe_pdf(file_path)
        if pdf_probe and pdf_probe.has_text_layer:
            logger.info(
                "Routing PDF to MarkItDown",
                file=file_path.name,
                sampled_pages=pdf_probe.sampled_pages,
                average_text_length=pdf_probe.average_text_length,
            )
            return self._resolve_parser(["markitdown"], file_path=file_path, reason="PDF text layer")

        preferred = [settings.scanned_pdf_parser]
        if (
            pdf_probe
            and pdf_probe.page_count > settings.paddle_doc_max_pdf_pages
            and settings.scanned_pdf_parser == "paddle_doc"
        ):
            preferred = ["manner", "mineru", "paddle_text", "paddleocr_vl"]

        return self._resolve_parser(
            preferred + ["paddle_text", "paddle_doc", "manner", "paddleocr_vl", "mineru"],
            file_path=file_path,
            reason="scanned PDF",
        )

    def _probe_pdf(self, file_path: Path) -> PDFProbeResult | None:
        try:
            return probe_pdf(
                file_path,
                sample_pages=settings.pdf_probe_pages,
                min_chars_per_page=settings.pdf_text_layer_min_chars,
            )
        except (OSError, RuntimeError) as e:
            logger.warning("PDF probe failed, falling back to MarkItDown-first", file=file_path.name, error=str(e))
            return None

    def _resolve_parser(
        self,
        parser_keys: list[str],
        *,
        file_path: Path | None = None,
        reason: str,
    ) -> BaseParser:
        seen: set[str] = set()
        for parser_key in parser_keys:
            if not parser_key or parser_key in seen:
                continue
            seen.add(parser_key)
            parser = self.parsers.get(parser_key)
            if parser is None:
                continue
            if file_path and not parser.can_handle(file_path):
                continue
            if not parser.is_available():
                continue
            logger.debug("Routing file", file=file_path.name if file_path else None, parser=parser_key, reason=reason)
            return parser

        raise ValueError(f"No available parser for {reason}")
