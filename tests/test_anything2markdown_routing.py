from pathlib import Path

import fitz

from anything2markdown.parsers.tabular_parser import TabularParser
from anything2markdown.router import Router


class StubParser:
    def __init__(self, name: str, supported_extensions: set[str], available: bool = True):
        self.parser_name = name
        self.supported_extensions = supported_extensions
        self._available = available

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    def is_available(self) -> bool:
        return self._available


def test_probe_routes_digital_pdf_to_markitdown(tmp_path, monkeypatch):
    pdf_path = tmp_path / "digital.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "This is embedded text inside the PDF. It has enough characters to exceed the minimum threshold for a text layer.")
    doc.save(pdf_path)
    doc.close()

    router = Router()
    router.parsers["markitdown"] = StubParser("markitdown", {".pdf"})

    parser = router.route_file(pdf_path)
    assert parser.parser_name == "markitdown"


def test_probe_routes_scanned_pdf_to_paddle_text(tmp_path, monkeypatch):
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%stub")

    monkeypatch.setattr(
        "anything2markdown.router.probe_pdf",
        lambda *_args, **_kwargs: type(
            "Probe",
            (),
            {
                "page_count": 2,
                "sampled_pages": [1, 2],
                "average_text_length": 0.0,
                "has_text_layer": False,
            },
        )(),
    )

    router = Router()
    router.parsers["paddle_text"] = StubParser("paddle_text", {".pdf"})
    router.parsers["markitdown"] = StubParser("markitdown", {".pdf"})
    router.parsers["paddle_doc"] = StubParser("paddle_doc", {".pdf"}, available=False)
    router.parsers["manner"] = StubParser("manner", {".pdf"}, available=False)
    router.parsers["paddleocr_vl"] = StubParser("paddleocr_vl", {".pdf"}, available=False)
    router.parsers["mineru"] = StubParser("mineru", {".pdf"}, available=False)

    parser = router.route_file(pdf_path)
    assert parser.parser_name == "paddle_text"


def test_route_image_to_paddle_text(tmp_path):
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"fakepng")

    router = Router()
    router.parsers["paddle_text"] = StubParser("paddle_text", {".png"})
    router.parsers["paddle_doc"] = StubParser("paddle_doc", {".png"}, available=False)
    router.parsers["manner"] = StubParser("manner", {".png"}, available=False)

    parser = router.route_file(image_path)
    assert parser.parser_name == "paddle_text"


def test_tabular_parser_outputs_markdown(tmp_path):
    csv_path = tmp_path / "table.csv"
    csv_path.write_text("name,score\nalice,10\nbob,20\n", encoding="utf-8")
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    parser = TabularParser()
    result = parser.parse(csv_path, output_dir)

    assert result.status == "success"
    assert result.output_path.suffix == ".md"
    content = result.output_path.read_text(encoding="utf-8")
    assert "| name | score |" in content
    assert "| alice | 10 |" in content
