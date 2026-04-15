"""Local web UI for Anything2Markdown — 一切先转MD."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Gradio may fail self-health-check behind proxies on macOS
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr

from .config import settings

# Project root = two levels up from this file (src/anything2markdown/webui.py)
PROJECT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = (PROJECT_DIR / "output").resolve()


def _run_parse(file_path: str, strategy: str) -> tuple[str, str]:
    """Call CLI and return (markdown_text, status)."""
    path = Path(file_path)
    # Invoke the CLI via `python -m` so this works regardless of where the
    # package/venv lives (no hard-coded .venv path).
    cmd = [
        sys.executable,
        "-m",
        "anything2markdown.cli",
        "parse-file",
        str(path),
        "-o",
        str(OUTPUT_DIR),
        "--strategy",
        strategy,
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return "", f"❌ 失败：{result.stderr.strip() or '未知错误'}"

        # Determine output filename
        from .utils.file_utils import flatten_path

        out_name = flatten_path(path, settings.input_dir) + ".md"
        out_path = OUTPUT_DIR / out_name
        if not out_path.exists():
            return "", "❌ 未找到输出文件"
        text = out_path.read_text(encoding="utf-8")
        return text, f"✅ 完成 | {len(text)} 字符 | 输出：{out_path.name}"
    except KeyboardInterrupt:
        raise
    except Exception as e:
        return "", f"❌ 异常：{e}"


def convert_files(files: list[str] | None, strategy: str) -> str:
    if not files:
        return "请先上传文件"
    parts: list[str] = []
    for f in files:
        text, status = _run_parse(f, strategy)
        parts.append(f"---\n**{status}**\n\n{text}")
    return "\n\n".join(parts)


def launch(host: str = "127.0.0.1", port: int = 7860) -> None:
    with gr.Blocks(title="一切先转MD") as demo:
        gr.Markdown("# 一切先转MD")
        gr.Markdown("拖拽文件到下方，点击转换，即可批量生成 Markdown。")

        with gr.Row():
            strategy = gr.Radio(
                choices=["token_efficient", "balanced"],
                value="token_efficient",
                label="转换策略",
            )

        file_input = gr.Files(
            label="拖放文件到这里（支持批量）",
            file_count="multiple",
        )

        btn = gr.Button("开始转换", variant="primary")
        output = gr.Markdown(label="结果")

        btn.click(
            fn=convert_files,
            inputs=[file_input, strategy],
            outputs=output,
        )

    print(f"🌐 一切先转MD 已开启：http://{host}:{port}")
    demo.launch(server_name=host, server_port=port, show_error=True)


if __name__ == "__main__":
    launch()
