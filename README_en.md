# Anything2Markdown

[中文](./README.md) | [English](./README_en.md)

> **Universal file and URL parser for LLM pipelines.**  
> Turn any document, URL, or repo into clean Markdown that AI can read.

---

## Basic Info

| Property | Content |
|:---|:---|
| **License** | MIT |
| **Language** | Python 3.10+ |
| **Deployment** | Local pip install or Docker |
| **Positioning** | Universal parsing layer for LLM pipelines — converts any file, URL, or repo into clean Markdown/JSON |

---

## Project Overview

Anything2Markdown is the **robust parsing layer** extracted from the Anything2Workspace pipeline. If all you need is "convert anything to clean Markdown," this is it.

The core idea is a **unified entry point**: whether the input is PDF, Excel, image, web page, YouTube video, or GitHub repo, the output is always structured text that LLMs can read.

---

## Core Capabilities

| Icon | Capability | Description |
|:---|:---|:---|
| 📄 | Document Parsing | PDF, Word, PowerPoint, EPUB, HTML → Markdown (via MarkItDown) |
| 🔍 | OCR Fallback | Auto-detect scanned PDFs and fall back to OCR (PaddleOCR / Manner OCR) |
| 📊 | Spreadsheet Conversion | Excel (.xlsx/.xls), CSV → Pandas Markdown tables |
| 🖼️ | Image Recognition | PNG, JPG, TIFF, etc. → OCR text extraction |
| 🌐 | Web Scraping | General sites → FireCrawl extracts main content |
| 🎬 | Video Transcription | YouTube, Bilibili → subtitles/transcript text |
| 📦 | Code Repos | GitHub repos → Repomix structured output |
| ⚡ | Parallel Processing | ThreadPoolExecutor for batch file parsing |
| 🔄 | Resume Support | Skip already-processed files on restart |
| 🔌 | Multiple Interfaces | CLI / HTTP API / MCP Server / Web UI / Python API |

---

## System Architecture

```
+------------------+
| Input Layer      |
| File / URL / Repo|
+--------+---------+
         |
+--------v---------+
| Router Layer     |
| Dispatch by type |
+--------+---------+
         |
+--------+---------+
| Preprocessing    |
| PDF probe / Retry|
+--------+---------+
         |
+--------------+--------------+--------------+
|              |              |              |
+--------v---------+ +--------v---------+ +--------v---------+
| Document Parsers  | | Media Parsers     | | Web Parsers       |
| MarkItDown        | | PaddleOCR-VL     | | FireCrawl        |
| Pandas (tables)   | | Manner OCR       | | YouTube API      |
| PyMuPDF (probe)   | | yt-dlp           | | Bilibili Parser  |
+------------------+ +------------------+ +------------------+
|              |              |
+--------------+--------------+
              |
+--------v---------+
| Output Layer     |
| Markdown / JSON  |
+------------------+
```

### Five Interfaces

| Interface | Command | Use Case |
|:---|:---|:---|
| CLI | `anything2md run` | Local batch processing |
| Python API | `from anything2markdown.pipeline import ...` | Embed in other Python projects |
| HTTP API | `python -m anything2markdown.api_server` | Service-oriented calls |
| MCP Server | `python -m anything2markdown.mcp_server` | Claude Code / Cursor and other MCP clients |
| Web UI | `anything2md web` | Gradio visual interface |

---

## Tech Stack

| Layer | Technology | Version |
|:---|:---|:---|
| **Core Parsing** | MarkItDown | 0.1.x |
| | PaddleOCR | VL 1.5 / Doc |
| | PyMuPDF | 1.24+ |
| | pypdf | 4.0+ |
| **Data Processing** | Pandas | 2.0+ |
| | openpyxl / xlrd | 3.1+ / 2.0+ |
| **Web/URL** | FireCrawl | 1.0+ |
| | youtube-transcript-api | 1.0+ |
| | yt-dlp | 2024+ |
| **Web Services** | FastAPI | 0.110+ |
| | Uvicorn | 0.29+ |
| | Gradio | 4.0+ |
| **Config** | Pydantic / pydantic-settings | 2.0+ |
| | Click | 8.1+ |
| | python-dotenv | 1.0+ |
| **Logging** | structlog | 24.0+ |
| **Testing** | pytest / pytest-cov | 8.0+ |
| **Linting** | ruff | 0.3+ |

---

## Installation

### Local Install (Recommended)

Requirements: Python 3.10+

```bash
git clone https://github.com/yourusername/anything2markdown.git
cd anything2markdown

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -e ".[dev]"

# If you need GitHub repo parsing, also install repomix
npm install -g repomix
```

### Docker Deployment

```bash
docker build -t anything2markdown .
docker run --rm -it \
  -v ./input:/app/input \
  -v ./output:/app/output \
  -v ./logs:/app/logs \
  anything2markdown anything2md run
```

---

## Quick Start

### 1. Initialize Directories

```bash
anything2md init
```

This creates three folders:
- `input/` — put files to process here
- `output/` — results will appear here
- `logs/` — execution logs

### 2. Drop Files In

Copy PDFs, Word docs, images, etc. into the `input/` folder.

You can also create `input/urls.txt` with one URL per line:

```
https://example.com
https://www.bilibili.com/video/BV1xx411c7mD
```

### 3. Run

```bash
anything2md run
```

When finished, check `output/` for results. **Already-processed files are automatically skipped** — safe to rerun.

### Single File / Single URL

```bash
# Parse a single file
anything2md parse-file ./input/my-document.pdf

# Parse a single URL
anything2md parse-url https://example.com
```

### Python API

```python
from anything2markdown.pipeline import Anything2MarkdownPipeline

pipeline = Anything2MarkdownPipeline()
results = pipeline.run()

for r in results:
    print(r.source_path, r.status, r.parser_used)
```

### HTTP API

```bash
python -m anything2markdown.api_server
# POST /parse/file   upload file for parsing
# POST /parse/url    submit URL for parsing
```

### MCP Server

```bash
python -m anything2markdown.mcp_server
# Exposes: parse_file, parse_url, list_supported_extensions
```

### Web UI

```bash
anything2md web
# Launches Gradio at http://127.0.0.1:7860
```

---

## External Dependencies & APIs

**All API Keys are optional.** Under default settings, most common formats can be parsed locally without any external service.

### Zero-Config Features (No API Key Required)

| Feature | Description |
|:---|:---|
| Regular PDF / Word / PPT / EPUB / HTML | Pure local parsing via MarkItDown |
| Excel / CSV Tables | Pure local conversion via Pandas |
| YouTube Subtitles | `youtube-transcript-api` calls public API |
| Bilibili Videos | `yt-dlp` scrapes public pages |
| GitHub Repos | `repomix` clones and packs locally (requires Node.js package) |

### Features Requiring External API Keys

| Feature | Service | Required? | Sign-up / Deployment |
|:---|:---|:---|:---|
| **General web page parsing** | FireCrawl | Only for `parse-url` on regular web pages | [firecrawl.dev](https://www.firecrawl.dev/) |
| **Scanned PDF / image OCR fallback** | SiliconFlow (PaddleOCR-VL) | Only when scanned docs/images fail MarkItDown and no local OCR is deployed | [siliconflow.cn](https://siliconflow.cn/) |
| **Complex PDF alternative parsing** | MinerU | Optional (disabled by default) | [mineru.net](https://mineru.net/) |
| **Production OCR (text/doc)** | PaddleOCR API | Optional | [PaddleOCR Cloud](https://www.paddlepaddle.org.cn/) or self-hosted |
| **Custom OCR script** | Manner OCR / local command | Optional | Configure local executable `MANNER_OCR_COMMAND` |

### Deployment Recommendations

- **Minimal deployment (no GPU, no external APIs)**: Handle regular documents and public videos only. Just `pip install` and run — no keys needed.
- **Add web page parsing**: Sign up for [FireCrawl](https://www.firecrawl.dev/) and add the API key to `.env`.
- **Add scanned PDF / image OCR**:
  - Option A (easy): Get a [SiliconFlow](https://siliconflow.cn/) API key and use cloud PaddleOCR-VL.
  - Option B (local): Self-host PaddleOCR and set `OCR_BASE_URL` and `PADDLEOCR_*` configs.
- **High-quality complex PDFs**: Get a [MinerU](https://mineru.net/) API key and set `SCANNED_PDF_PARSER=mineru`.

---

## Environment Variables (`.env.example`)

The project includes `.env.example`. Copy it to `.env`:

```bash
cp .env.example .env
```

Then fill in any keys you need.

### General Config

| Variable | Default | Description |
|:---|:---|:---|
| `INPUT_DIR` | `./input` | Input files directory |
| `OUTPUT_DIR` | `./output` | Output results directory |
| `LOG_DIR` | `./logs` | Logs directory |
| `LANGUAGE` | `en` | Default language |
| `LOG_LEVEL` | `INFO` | Log level |
| `LOG_FORMAT` | `both` | Log format: console / file / both |
| `MAX_WORKERS` | `4` | Max parallel parsing threads |

### API Key Config

| Variable | Default | Description |
|:---|:---|:---|
| `SILICONFLOW_API_KEY` | — | [SiliconFlow](https://siliconflow.cn/) cloud PaddleOCR-VL OCR |
| `FIRECRAWL_API_KEY` | — | [FireCrawl](https://www.firecrawl.dev/) web page parsing |
| `MINERU_API_KEY` | — | [MinerU](https://mineru.net/) complex PDF parsing |
| `PADDLEOCR_ACCESS_TOKEN` | — | Self-hosted / third-party PaddleOCR service auth |
| `PADDLEOCR_DOC_PARSING_API_URL` | — | Self-hosted / third-party PaddleOCR Doc parsing endpoint |

---

## Architecture Highlights

- **Parser chain with fallback** — MarkItDown first, auto-fallback to OCR if quality is too low
- **PDF probing** — Samples a few pages to decide whether a PDF has a text layer or needs OCR
- **Retry decorator** — Transient failures (network, API rate limits) are retried automatically
- **Parallel processing** — Files are parsed concurrently via `ThreadPoolExecutor`
- **Resume support** — Skips already-processed files on restart

---

## Project Structure

```
Anything2Markdown/
├── src/anything2markdown/
│   ├── __init__.py
│   ├── api_server.py        # FastAPI HTTP service
│   ├── cli.py               # Click CLI
│   ├── config.py            # Configuration & settings
│   ├── mcp_server.py        # MCP protocol service
│   ├── pipeline.py          # Core pipeline logic
│   ├── router.py            # Parser router
│   ├── webui.py             # Gradio Web UI
│   ├── _internal/           # Internal utils (retry, logging, exceptions)
│   ├── parsers/             # File parsers
│   ├── schemas/             # Pydantic data models
│   ├── url_parsers/         # URL parsers
│   └── utils/               # General utilities
├── tests/
│   └── test_anything2markdown_routing.py
├── Dockerfile
├── pyproject.toml
├── README.md
├── README_en.md
├── LICENSE
├── .env.example
└── .gitignore
```

---

## Development

```bash
# Run tests
pytest tests/ -q

# Lint
ruff check src/
ruff format src/
```

---

## Test Coverage

- Parser routing & availability checks
- PDF text-layer probing logic
- Multi-format extension matching
- Pipeline batch execution flow

---

## License

MIT License — see [LICENSE](./LICENSE) for details.
