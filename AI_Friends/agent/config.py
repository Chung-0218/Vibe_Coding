from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class AppConfig:
    openai_api_key: str
    tts_voice: str = "alloy"
    chat_model: str = "gpt-4o-mini"
    tts_model: str = "gpt-4o-mini-tts"
    moderation_model: str = "omni-moderation-latest"
    max_history_messages: int = 12


def load_config() -> AppConfig:
    # 프로젝트 폴더의 .env를 우선 로드 (이 파일 기준 상위 폴더)
    project_env = Path(__file__).resolve().parents[1] / ".env"
    try:
        if project_env.exists():
            load_dotenv(dotenv_path=project_env, override=False)
        else:
            load_dotenv(override=False)
    except Exception:
        load_dotenv(override=False)

    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")

    # 키가 없어도 앱은 기동되도록 하되, 실제 API 호출 시 오류가 발생할 수 있습니다.
    return AppConfig(openai_api_key=api_key or "")


