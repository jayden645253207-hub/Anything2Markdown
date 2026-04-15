"""Shared base configuration for all pipeline modules."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseModuleConfig(BaseSettings):
    """Base configuration shared across all pipeline modules."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # I/O Paths
    input_dir: Path = Field(default=Path("./input"))
    output_dir: Path = Field(default=Path("./output"))
    log_dir: Path = Field(default=Path("./logs"))

    # Language
    language: Literal["en", "zh"] = Field(default="en")

    # Logging
    log_level: str = Field(default="INFO")
    log_format: Literal["json", "text", "both"] = Field(default="both")

    # LLM Configuration (SiliconFlow)
    siliconflow_api_key: str = Field(default="")
    siliconflow_base_url: str = Field(default="https://api.siliconflow.cn/v1")

    # Processing parallelism
    max_workers: int = Field(default=4, description="Max worker threads for I/O-bound pipeline stages")

    # Retry defaults
    retry_count: int = Field(default=1)
    retry_delay_seconds: int = Field(default=2)
