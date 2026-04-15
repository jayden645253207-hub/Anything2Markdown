"""File parsers for Anything2Markdown."""

from .base import BaseParser
from .markitdown_parser import MarkItDownParser
from .manner_ocr_parser import MannerOCRParser
from .mineru_parser import MinerUParser
from .paddleocr_doc_parser import PaddleOCRDocParser
from .paddleocr_text_parser import PaddleOCRTextParser
from .paddleocr_vl_parser import PaddleOCRVLParser
from .tabular_parser import TabularParser

__all__ = [
    "BaseParser",
    "MarkItDownParser",
    "MannerOCRParser",
    "MinerUParser",
    "PaddleOCRDocParser",
    "PaddleOCRTextParser",
    "PaddleOCRVLParser",
    "TabularParser",
]
