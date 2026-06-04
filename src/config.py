from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")


def _resolve_path(value: str | None, default: Path) -> Path:
    if value:
        candidate = Path(value).expanduser()
        return candidate if candidate.is_absolute() else ROOT_DIR / candidate
    return default


@dataclass(frozen=True)
class Settings:
    root_dir: Path = ROOT_DIR
    data_dir: Path = _resolve_path(os.getenv("DATA_PATH"), ROOT_DIR / "data")
    vector_db_dir: Path = _resolve_path(os.getenv("VECTOR_DB_PATH"), ROOT_DIR / "vector_db")
    db_path: Path = _resolve_path(os.getenv("DB_PATH"), data_dir / "meridian_wealth.db")
    policy_dir: Path = _resolve_path(os.getenv("POLICY_DIR"), data_dir / "policy_documents")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    tavily_api_key: str | None = os.getenv("TAVILY_API_KEY")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-5-mini")
    tavily_max_results: int = int(os.getenv("TAVILY_MAX_RESULTS", "3"))
    tavily_topic: str = os.getenv("TAVILY_TOPIC", "news")

    def validate(self) -> None:
        if not self.db_path.exists():
            raise FileNotFoundError(f"SQLite database not found at {self.db_path}")
        if not self.policy_dir.exists():
            raise FileNotFoundError(f"Policy documents directory not found at {self.policy_dir}")
        if not self.openai_api_key:
            raise EnvironmentError("OPENAI_API_KEY is required")
        if not self.tavily_api_key:
            raise EnvironmentError("TAVILY_API_KEY is required")


def get_settings() -> Settings:
    settings = Settings()
    settings.validate()
    return settings
