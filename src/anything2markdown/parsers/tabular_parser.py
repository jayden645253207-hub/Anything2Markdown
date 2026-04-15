"""Parser for tabular data (xlsx, xls, csv) -> Markdown."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import structlog

from ..config import settings
from ..schemas.result import ParseResult
from ..utils.file_utils import flatten_path
from .base import BaseParser

logger = structlog.get_logger(__name__)


class TabularParser(BaseParser):
    """
    Parser for tabular data (xlsx, xls, csv).
    Converts to compact Markdown tables to keep downstream token usage low.
    """

    supported_extensions = [".xlsx", ".xls", ".csv"]
    parser_name = "tabular"

    def can_handle(self, file_path: Path) -> bool:
        """Check if file extension is supported."""
        return file_path.suffix.lower() in self.supported_extensions

    def parse(self, file_path: Path, output_dir: Path) -> ParseResult:
        """
        Convert tabular data to Markdown.

        Args:
            file_path: Path to the input file
            output_dir: Directory to save output

        Returns:
            ParseResult with conversion details
        """
        started_at = datetime.now()

        logger.info("Tabular parsing", file=file_path.name)

        try:
            extension = file_path.suffix.lower()
            metadata = {}

            if extension == ".csv":
                # CSV: single sheet
                df = self._normalize_dataframe(pd.read_csv(file_path))
                markdown_content = self._render_sheet(file_path.stem, df)
                metadata["row_count"] = len(df)
                metadata["column_count"] = len(df.columns) if not df.empty else 0
            else:
                # Excel: may have multiple sheets
                xlsx = pd.ExcelFile(file_path)
                sheet_sections: list[str] = []
                row_counts: dict[str, int] = {}

                for sheet_name in xlsx.sheet_names:
                    df = self._normalize_dataframe(pd.read_excel(xlsx, sheet_name=sheet_name))
                    row_counts[sheet_name] = len(df)
                    sheet_sections.append(self._render_sheet(sheet_name, df))

                markdown_content = "\n\n".join(sheet_sections)
                if len(row_counts) == 1:
                    metadata["row_count"] = next(iter(row_counts.values()))
                else:
                    metadata["sheet_count"] = len(row_counts)
                    metadata["row_counts"] = row_counts

            # Generate flattened output filename
            output_name = flatten_path(file_path, settings.input_dir) + ".md"
            output_path = output_dir / output_name

            # Ensure parent directory exists (for grouped outputs)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write output
            output_path.write_text(markdown_content, encoding="utf-8")

            completed_at = datetime.now()

            logger.info(
                "Tabular parsing success",
                file=file_path.name,
                output=output_path.name,
                chars=len(markdown_content),
            )

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
                character_count=len(markdown_content),
                metadata=metadata,
            )

        except Exception as e:
            completed_at = datetime.now()
            logger.error("Tabular parsing failed", file=file_path.name, error=str(e))

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

    @staticmethod
    def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        cleaned = df.copy()
        cleaned = cleaned.dropna(axis=0, how="all").dropna(axis=1, how="all")
        cleaned = cleaned.fillna("")
        return cleaned

    def _render_sheet(self, sheet_name: str, df: pd.DataFrame) -> str:
        title = f"## {sheet_name}"
        if df.empty:
            return f"{title}\n\n_Empty sheet_"

        header = "| " + " | ".join(self._escape_cell(col) for col in df.columns) + " |"
        separator = "| " + " | ".join("---" for _ in df.columns) + " |"
        rows = [
            "| " + " | ".join(self._escape_cell(value) for value in row) + " |"
            for row in df.itertuples(index=False, name=None)
        ]
        return "\n".join([title, "", header, separator, *rows])

    @staticmethod
    def _escape_cell(value: object) -> str:
        text = str(value).strip()
        text = text.replace("|", "\\|")
        text = text.replace("\r\n", "<br>")
        text = text.replace("\n", "<br>")
        return text
