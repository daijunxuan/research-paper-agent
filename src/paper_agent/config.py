from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PAPERTRAIL_", env_file=".env", extra="ignore")
    provider: Literal["local", "ollama", "evidence"] = "local"
    model_id: str = "Qwen/Qwen3-1.7B"
    model_revision: str = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
    device: Literal["cpu", "mps", "cuda"] = "cpu"
    cpu_quantization: Literal["none", "dynamic-int8"] = "dynamic-int8"
    cpu_threads: int = Field(default=4, ge=1, le=32)
    max_new_tokens: int = Field(default=700, ge=64, le=1500)
    data_dir: Path = Path(".data")
    ollama_url: str = "http://127.0.0.1:11434"
    max_upload_bytes: int = 20 * 1024 * 1024
