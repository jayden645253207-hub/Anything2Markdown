"""Configuration management using Pydantic Settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field

from anything2markdown._internal.config import BaseModuleConfig


class Settings(BaseModuleConfig):
    """Application configuration loaded from environment variables."""

    # API Keys
    mineru_api_key: str = Field(default="")
    firecrawl_api_key: str = Field(default="")

    # MinerU Configuration
    mineru_api_endpoint: str = Field(default="https://mineru.net/api/v4/extract/task")
    max_pdf_size_mb: int = Field(default=10)
    min_valid_chars: int = Field(default=500)
    mineru_pages_per_split: int = Field(default=400)

    # Routing / token efficiency
    parsing_strategy: Literal["token_efficient", "balanced"] = Field(default="token_efficient")
    pdf_probe_pages: int = Field(default=3)
    pdf_text_layer_min_chars: int = Field(default=80)
    scanned_pdf_parser: Literal[
        "paddle_text", "paddle_doc", "manner", "mineru", "paddle_vl"
    ] = Field(default="paddle_text")
    image_ocr_parser: Literal["paddle_text", "paddle_doc", "manner", "paddle_vl"] = Field(
        default="paddle_text"
    )
    pdf_ocr_fallback_parser: Literal[
        "paddle_text", "paddle_doc", "manner", "mineru", "paddle_vl"
    ] = Field(default="paddle_text")
    paddle_doc_max_pdf_pages: int = Field(default=100)

    # PaddleOCR-VL Configuration
    paddleocr_model: str = Field(default="PaddlePaddle/PaddleOCR-VL-1.5")
    ocr_dpi: int = Field(default=150)
    ocr_page_timeout: int = Field(default=60)
    ocr_base_url: str = Field(default="")  # Empty = use siliconflow_base_url; set to e.g. http://localhost:8080/v1 for local

    # PaddleOCR API Configuration
    paddleocr_access_token: str = Field(default="")
    paddleocr_ocr_api_url: str = Field(default="")
    paddleocr_ocr_timeout: int = Field(default=120)
    paddleocr_doc_parsing_api_url: str = Field(default="")
    paddleocr_doc_parsing_timeout: int = Field(default=600)

    # External OCR command (for custom backends like Manner OCR)
    manner_ocr_command: str = Field(default="")
    manner_ocr_timeout: int = Field(default=600)

    # Bilibili Configuration
    bilibili_cookies_file: str = Field(default="")  # Path to Netscape cookie file
    bilibili_cookies_from_browser: str = Field(default="")  # Browser to extract cookies from (chrome/firefox/safari/edge); empty to disable
    whisperx_model: str = Field(default="large-v2")  # WhisperX model size


def get_settings() -> Settings:
    """Get settings instance. Creates new instance each time to pick up env changes."""
    return Settings()


# Default singleton for convenience
settings = Settings()
