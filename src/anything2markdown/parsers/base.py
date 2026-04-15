"""Abstract base class for file parsers."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..schemas.result import ParseResult


class BaseParser(ABC):
    """
    Abstract base class for all file parsers.

    Subclasses must implement:
    - supported_extensions: list of file extensions this parser handles
    - parser_name: unique identifier for this parser
    - parse(): main parsing logic
    - can_handle(): check if parser can handle a file
    """

    # Class-level attributes for routing
    supported_extensions: list[str] = []
    parser_name: str = "base"

    def is_available(self) -> bool:
        """
        Whether this parser is currently usable in the local environment.

        Parsers backed by optional APIs or local tools can override this to
        advertise whether the required configuration is present.
        """
        return True

    @abstractmethod
    def parse(self, file_path: Path, output_dir: Path) -> ParseResult:
        """
        Parse a file and save output.

        Args:
            file_path: Path to the input file
            output_dir: Directory to save output

        Returns:
            ParseResult with status and metadata
        """
        pass

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file.

        Args:
            file_path: Path to check

        Returns:
            True if this parser can handle the file
        """
        pass
