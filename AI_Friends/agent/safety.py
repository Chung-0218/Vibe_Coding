from __future__ import annotations

import re
from typing import Tuple


POSITIVE_PREFIX = (
    "나는 너를 지지해. 네 이야기를 진심으로 듣고 있어. "
    "힘든 마음을 공감하고, 동시에 작은 희망을 찾을 수 있도록 도와줄게. "
)


def sanitize_user_text(text: str) -> str:
    """간단한 입력 정화: 과도한 공백, 제어문자 제거"""
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def empathetic_prefix() -> str:
    return POSITIVE_PREFIX


def safe_and_empathetic_system_prompt() -> str:
    return (
        "너는 사용자의 좋은 친구 같은 AI다. 공감, 위로, 긍정, 실용적 조언을 균형 있게 제공한다. "
        "민감한 주제(자해, 폭력, 혐오, 불법, 의학/법률 상담)에는 안전 가이드라인을 지켜 정보를 일반화하고 지원 리소스를 안내한다. "
        "말투는 따뜻하고 편안하게, 존중하는 반말로 대화한다. 과장하거나 단정하지 않는다. "
        "사용자의 감정 이름붙이기 → 공감 → 확인 질문 → 부드러운 제안 → 선택지 제시 흐름을 추구한다."
    )


def build_chat_messages(user_text: str, image_url: str | None = None) -> list[dict]:
    system = safe_and_empathetic_system_prompt()
    content: list[dict] = [{"type": "text", "text": empathetic_prefix() + " " + user_text}]
    if image_url:
        content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ]


