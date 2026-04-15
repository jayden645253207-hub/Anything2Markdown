# Credits & Acknowledgments

Anything2Workspace is a thin orchestration layer over a long list of excellent
upstream projects. This file records what we use, where we use it, and the
license under which we use it.

## Module 1 — Anything2Markdown

| Component                        | Role                                            | License              |
|----------------------------------|-------------------------------------------------|----------------------|
| [MarkItDown](https://github.com/microsoft/markitdown) | Primary parser for PDF / Word / PPT / HTML / EPUB / text / common media | MIT (Microsoft) |
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) text & doc parsing APIs | Low-token OCR for scanned PDFs and images | Apache 2.0 (PaddlePaddle) |
| [PaddleOCR-VL](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5) | Vision-LM OCR fallback (SiliconFlow API or local mlx-vlm) | Apache 2.0 |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) / [pypdf](https://github.com/py-pdf/pypdf) | PDF probing & page rendering for the OCR pipeline | AGPL-3.0 / BSD-3-Clause |
| [pandas](https://github.com/pandas-dev/pandas) + [openpyxl](https://foss.heptapod.net/openpyxl/openpyxl) + [xlrd](https://github.com/python-excel/xlrd) | Excel / CSV → Markdown tables | BSD-3-Clause / MIT / BSD |
| [Firecrawl Python SDK](https://github.com/mendableai/firecrawl) | General web URL crawling | MIT (SDK) |
| [Repomix](https://github.com/yamadashy/repomix) (Node CLI) | Whole GitHub repo → single Markdown | MIT |
| [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) | YouTube subtitle fetch | MIT |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Bilibili audio extraction | Unlicense |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Local audio-to-text when no CC is available | MIT |
| [MinerU](https://mineru.net/) (hosted API) | Optional alternative VLM PDF extractor | Provider ToS |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | MCP server (`anything2markdown.mcp_server`) | MIT (Anthropic) |
| [FastAPI](https://github.com/tiangolo/fastapi) + [Uvicorn](https://github.com/encode/uvicorn) | HTTP server (`anything2markdown.api_server`) | MIT |
| [Gradio](https://github.com/gradio-app/gradio) | Local web UI (`anything2markdown.webui`) | Apache 2.0 |

## Cross-cutting

| Component                        | Role                                            | License              |
|----------------------------------|-------------------------------------------------|----------------------|
| [click](https://github.com/pallets/click) | CLI framework (`anything2md`) | BSD-3-Clause |
| [pydantic](https://github.com/pydantic/pydantic) + [pydantic-settings](https://github.com/pydantic/pydantic-settings) | Schema validation & `.env` loading | MIT |
| [structlog](https://github.com/hynek/structlog) | Dual-format logging (JSON + plain text) | MIT/Apache 2.0 |

## Reporting an attribution gap

If you spot an upstream library or model that should be credited here and isn't,
please open an issue or PR.
