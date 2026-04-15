<h1 align="center">Anything2Markdown</h1>

<p align="center">
  <b>Universal file and URL parser for LLM pipelines.</b><br>
  把任意文件、网页、视频转成 Markdown，让 AI 读得懂。
</p>

<p align="center">
  <a href="./README.md">中文</a> | <a href="./README_en.md">English</a>
</p>

<p align="center">
  <img src="assets/wechat-qr.jpg" width="200" alt="微信二维码" />
  &nbsp;&nbsp;
  <img src="assets/mp-qr.jpg" width="200" alt="公众号二维码" />
</p>
<p align="center">
  <b>💬 微信：周杰 律师</b> &nbsp;|&nbsp; <b>📰 公众号：扫码关注</b>
</p>

---

> **Anything2Markdown** 是从 Anything2Workspace 管道中提取出的**鲁棒解析层**。  
> 核心理念是**统一入口**：无论输入是 PDF、Excel、图片、网页、YouTube 视频还是 GitHub 仓库，都输出为 LLM 可读的结构化文本。

<p align="center">
  <a href="#项目简介">项目简介</a> ·
  <a href="#核心能力">核心能力</a> ·
  <a href="#快速开始">快速开始</a> ·
  <a href="#系统架构">系统架构</a> ·
  <a href="#技术栈">技术栈</a> ·
  <a href="#外部依赖">外部依赖</a> ·
  <a href="#许可">许可</a>
</p>

---

## 项目简介

| 属性 | 内容 |
|:---|:---|
| **协议** | MIT |
| **语言** | Python 3.10+ |
| **部署方式** | 本地 pip 安装 或 Docker 部署 |
| **定位** | LLM 管道的通用解析层 — 将任意文件、URL 或代码仓库转换为干净的 Markdown/JSON |

---

## 核心能力

| 图标 | 能力 | 说明 |
|:---|:---|:---|
| 📄 | 文档解析 | PDF、Word、PowerPoint、EPUB、HTML → Markdown（MarkItDown） |
| 🔍 | OCR 兜底 | 扫描版 PDF 自动探测并回退到 OCR（PaddleOCR / Manner OCR） |
| 📊 | 表格转换 | Excel（.xlsx/.xls）、CSV → Pandas Markdown 表格 |
| 🖼️ | 图片识别 | PNG、JPG、TIFF 等 → OCR 提取文本 |
| 🌐 | 网页抓取 | 通用站点 → FireCrawl 提取正文 |
| 🎬 | 视频转录 | YouTube、Bilibili → 字幕/转录文本 |
| 📦 | 代码仓库 | GitHub 仓库 → Repomix 结构化输出 |
| ⚡ | 并发处理 | ThreadPoolExecutor 并行解析批量文件 |
| 🔄 | 断点续跑 | 自动跳过已处理文件，支持幂等重跑 |
| 🔌 | 多接口暴露 | CLI / HTTP API / MCP Server / Web UI / Python API |

---

## 快速开始

### 第一步：安装

要求 Python 3.10+

```bash
git clone https://github.com/jayden645253207-hub/Anything2Markdown.git
cd Anything2Markdown

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

### 第二步：初始化

```bash
anything2md init
```

这会创建三个文件夹：
- `input/` — 放你要处理的文件
- `output/` — 处理结果会出现在这里
- `logs/` — 运行日志

### 第三步：丢文件进去，一键运行

把 PDF、Word、图片等文件复制到 `input/`，然后：

```bash
anything2md run
```

等它跑完，去 `output/` 里看结果。**已经处理过的文件会自动跳过**，不用担心重复跑。

### 其他用法

```bash
# 解析单个文件
anything2md parse-file ./input/我的文档.pdf

# 解析单个网址
anything2md parse-url https://example.com

# 启动网页界面
anything2md web

# 启动 HTTP API
python -m anything2markdown.api_server

# 启动 MCP Server
python -m anything2markdown.mcp_server
```

### Python API

```python
from anything2markdown.pipeline import Anything2MarkdownPipeline

pipeline = Anything2MarkdownPipeline()
results = pipeline.run()

for r in results:
    print(r.source_path, r.status, r.parser_used)
```

---

## 系统架构

```
+------------------+
| 输入层            |
| 文件 / URL / 仓库 |
+--------+---------+
         |
+--------v---------+
| 路由层            |
| 按类型分发 Parser |
+--------+---------+
         |
+--------v---------+
| 预处理            |
| PDF 探测 / 重试   |
+--------+---------+
         |
+--------------+--------------+--------------+
|              |              |              |
+--------v---------+ +--------v---------+ +--------v---------+
| 文档 Parser       | | 媒体 Parser       | | 网络 Parser       |
| MarkItDown        | | PaddleOCR-VL     | | FireCrawl        |
| Pandas (表格)     | | Manner OCR       | | YouTube API      |
| PyMuPDF (探测)    | | yt-dlp           | | Bilibili Parser  |
+------------------+ +------------------+ +------------------+
|              |              |
+--------------+--------------+
              |
+--------v---------+
| 输出层            |
| Markdown / JSON   |
+------------------+
```

### 五种使用接口

| 接口 | 启动方式 | 用途 |
|:---|:---|:---|
| CLI | `anything2md run` | 本地批量处理 |
| Python API | `from anything2markdown.pipeline import ...` | 嵌入其他 Python 项目 |
| HTTP API | `python -m anything2markdown.api_server` | 服务化调用 |
| MCP Server | `python -m anything2markdown.mcp_server` | Claude Code / Cursor 等 MCP 客户端 |
| Web UI | `anything2md web` | Gradio 可视化界面 |

---

## 技术栈

| 层级 | 技术 | 版本 |
|:---|:---|:---|
| **核心解析** | MarkItDown | 0.1.x |
| | PaddleOCR | VL 1.5 / Doc |
| | PyMuPDF | 1.24+ |
| | pypdf | 4.0+ |
| **数据处理** | Pandas | 2.0+ |
| | openpyxl / xlrd | 3.1+ / 2.0+ |
| **网络/URL** | FireCrawl | 1.0+ |
| | youtube-transcript-api | 1.0+ |
| | yt-dlp | 2024+ |
| **Web 服务** | FastAPI | 0.110+ |
| | Uvicorn | 0.29+ |
| | Gradio | 4.0+ |
| **协议/配置** | Pydantic / pydantic-settings | 2.0+ |
| | Click | 8.1+ |
| | python-dotenv | 1.0+ |
| **日志** | structlog | 24.0+ |
| **测试** | pytest / pytest-cov | 8.0+ |
| **代码规范** | ruff | 0.3+ |

---

## 外部依赖与 API 说明

**所有 API Key 都是可选的。** 默认配置下，大部分常见格式无需任何外部服务即可本地解析。

### 零配置即可使用（无需 API Key）

| 功能 | 说明 |
|:---|:---|
| 常规 PDF / Word / PPT / EPUB / HTML | MarkItDown 纯本地解析 |
| Excel / CSV 表格 | Pandas 纯本地转换 |
| YouTube 字幕 | `youtube-transcript-api` 直接请求公开 API |
| Bilibili 视频 | `yt-dlp` 抓取公开页面 |
| GitHub 仓库 | `repomix` 本地克隆打包（需本地安装 Node.js 包） |

### 需要外部 API Key 的功能

| 功能 | 依赖服务 | 是否必需 | 申请地址 |
|:---|:---|:---|:---|
| **通用网页解析** | FireCrawl | 仅 `parse-url` 处理普通网页时需要 | [firecrawl.dev](https://www.firecrawl.dev/) |
| **扫描版 PDF / 图片 OCR 回退** | SiliconFlow (PaddleOCR-VL) | 仅当扫描件/图片 MarkItDown 解析失败且未部署本地 OCR 时需要 | [siliconflow.cn](https://siliconflow.cn/) |
| **复杂 PDF 替代解析** | MinerU | 可选（默认关闭） | [mineru.net](https://mineru.net/) |
| **生产级 OCR (文字/文档)** | PaddleOCR API | 可选 | [PaddleOCR 云服务](https://www.paddlepaddle.org.cn/) 或自行部署本地服务 |
| **自定义 OCR 脚本** | Manner OCR / 本地命令 | 可选 | 配置本地可执行命令 `MANNER_OCR_COMMAND` |

### 部署建议

- **最小化部署（无 GPU、无外部 API）**：只处理常规文档和公开视频，直接 `pip install` 后运行，不填任何 Key。
- **增加网页解析**：申请 [FireCrawl](https://www.firecrawl.dev/) API Key，填入 `.env`。
- **增加扫描件/图片 OCR**：
  - 方案 A（简单）：申请 [SiliconFlow](https://siliconflow.cn/) API Key，使用云端 PaddleOCR-VL。
  - 方案 B（本地）：自行部署 PaddleOCR 服务，填写 `OCR_BASE_URL` 和 `PADDLEOCR_*` 相关配置。
- **高质量复杂 PDF**：申请 [MinerU](https://mineru.net/) API Key，修改 `SCANNED_PDF_PARSER=mineru`。

---

## 环境变量

项目里有个 `.env.example`，复制一份改名叫 `.env`：

```bash
cp .env.example .env
```

### 通用配置

| 变量 | 默认值 | 说明 |
|:---|:---|:---|
| `INPUT_DIR` | `./input` | 输入文件目录 |
| `OUTPUT_DIR` | `./output` | 输出结果目录 |
| `LOG_DIR` | `./logs` | 日志目录 |
| `LANGUAGE` | `en` | 默认语言 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `LOG_FORMAT` | `both` | 日志格式：console / file / both |
| `MAX_WORKERS` | `4` | 并行解析最大线程数 |

### API Key 配置

| 变量 | 默认值 | 说明 |
|:---|:---|:---|
| `SILICONFLOW_API_KEY` | — | [SiliconFlow](https://siliconflow.cn/) PaddleOCR-VL 云端 OCR |
| `FIRECRAWL_API_KEY` | — | [FireCrawl](https://www.firecrawl.dev/) 网页解析 |
| `MINERU_API_KEY` | — | [MinerU](https://mineru.net/) 复杂 PDF 解析 |
| `PADDLEOCR_ACCESS_TOKEN` | — | 自建/第三方 PaddleOCR 服务认证 |
| `PADDLEOCR_DOC_PARSING_API_URL` | — | 自建/第三方 PaddleOCR Doc 解析地址 |

---

## 项目结构

```
Anything2Markdown/
├── src/anything2markdown/
│   ├── __init__.py
│   ├── api_server.py        # FastAPI HTTP 服务
│   ├── cli.py               # Click CLI
│   ├── config.py            # 配置与设置
│   ├── mcp_server.py        # MCP 协议服务
│   ├── pipeline.py          # 核心管道逻辑
│   ├── router.py            # Parser 路由
│   ├── webui.py             # Gradio Web UI
│   ├── _internal/           # 内部工具（重试、日志、异常）
│   ├── parsers/             # 文件解析器集合
│   ├── schemas/             # Pydantic 数据模型
│   ├── url_parsers/         # URL 解析器集合
│   └── utils/               # 通用工具函数
├── tests/
│   └── test_anything2markdown_routing.py
├── assets/                   # 二维码等静态资源
├── Dockerfile
├── pyproject.toml
├── README.md
├── README_en.md
├── LICENSE
├── .env.example
└── .gitignore
```

---

## 开发

```bash
# 运行测试
pytest tests/ -q

# 代码检查
ruff check src/
ruff format src/
```

---

## 许可

MIT License — 详见 [LICENSE](./LICENSE)。
