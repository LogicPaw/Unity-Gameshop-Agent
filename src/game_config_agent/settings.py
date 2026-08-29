"""Environment-backed runtime settings without exposing secrets."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SettingsError(ValueError):
    """Raised when required model configuration is missing."""


@dataclass(frozen=True)
class ModelSettings:
    api_key: str
    base_url: str
    model: str

    @classmethod
    def from_env(cls, env_path: str | Path | None = None) -> "ModelSettings":
        load_dotenv(Path(env_path) if env_path else PROJECT_ROOT / ".env")
        api_key = os.getenv("OPENCODEGO_API_KEY", "").strip()
        base_url = os.getenv("OPENCODEGO_BASE_URL", "").strip()
        model = os.getenv("OPENCODEGO_MODEL", "").strip()

        missing = [
            name
            for name, value in (
                ("OPENCODEGO_API_KEY", api_key),
                ("OPENCODEGO_BASE_URL", base_url),
                ("OPENCODEGO_MODEL", model),
            )
            if not value
        ]
        if missing:
            raise SettingsError(f"缺少模型配置：{', '.join(missing)}")
        return cls(api_key=api_key, base_url=base_url.rstrip("/"), model=model)
