from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "gemini-1.5-flash")
    figma_token: str = os.getenv("FIGMA_TOKEN", "")
    figma_file_id: str = os.getenv("FIGMA_FILE_ID", "")
    http_timeout: int = int(os.getenv("HTTP_TIMEOUT", "30"))

    @classmethod
    def validate(cls) -> "Settings":
        s = cls()
        if not s.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required")
        return s
