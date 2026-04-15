"""Helpers for resolving OCR configuration from env and local skill configs."""

from __future__ import annotations

import os
from pathlib import Path

PADDLE_TEXT_SKILL_ROOT = Path.home() / ".codex" / "skills" / "paddleocr-text-recognition"
PADDLE_DOC_SKILL_ROOT = Path.home() / ".codex" / "skills" / "paddleocr-doc-parsing"


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _load_skill_env(skill_root: Path) -> dict[str, str]:
    config: dict[str, str] = {}
    for candidate in (skill_root / "config" / ".env", skill_root / "scripts" / ".env"):
        config.update(_load_env_file(candidate))
    return config


def _read_aistudio_token_file() -> str:
    cache_home = Path(os.getenv("AISTUDIO_CACHE_HOME", str(Path.home()))).expanduser()
    token_path = cache_home / ".cache" / "aistudio" / ".auth" / "token"
    if not token_path.exists():
        return ""
    return token_path.read_text(encoding="utf-8").strip()


def resolve_config_value(*keys: str, file_config: dict[str, str] | None = None) -> str:
    """
    Resolve a config value with this precedence:
    1. process env
    2. supplied file config
    3. AI Studio token fallback for Paddle token
    """
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value

    if file_config:
        for key in keys:
            value = file_config.get(key, "").strip()
            if value:
                return value

    if "PADDLEOCR_ACCESS_TOKEN" in keys:
        aistudio_token = os.getenv("AISTUDIO_ACCESS_TOKEN", "").strip()
        if aistudio_token:
            return aistudio_token
        return _read_aistudio_token_file()

    return ""


def get_paddle_text_skill_config() -> dict[str, str]:
    return _load_skill_env(PADDLE_TEXT_SKILL_ROOT)


def get_paddle_doc_skill_config() -> dict[str, str]:
    return _load_skill_env(PADDLE_DOC_SKILL_ROOT)
