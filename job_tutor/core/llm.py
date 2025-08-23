from __future__ import annotations
import os
from typing import Any, Optional


class LLMProvider:
    """Optional LLM provider. Uses OpenAI if OPENAI_API_KEY is set and SDK is available.

    Methods return None when provider is unavailable, so callers can safely fall back.
    """

    def __init__(self) -> None:
        self._enabled = bool(os.environ.get("OPENAI_API_KEY"))
        self._client: Any = None
        if self._enabled:
            try:
                from openai import OpenAI  # type: ignore

                self._client = OpenAI()
            except Exception:
                # OpenAI SDK missing or misconfigured. Disable provider.
                self._enabled = False
                self._client = None

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    def cover_letter_feedback(self, prompt: str) -> Optional[str]:
        if not self.enabled or self._client is None:
            return None
        try:
            completion = self._client.chat.completions.create(  # type: ignore[attr-defined]
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert Korean career coach. Provide concise, actionable feedback."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
            )
            return completion.choices[0].message.content or None
        except Exception:
            return None

    def coding_hint(self, prompt: str) -> Optional[str]:
        if not self.enabled or self._client is None:
            return None
        try:
            completion = self._client.chat.completions.create(  # type: ignore[attr-defined]
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful coding interview tutor. Respond in Korean with hints first, then a reference answer only if asked."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            return completion.choices[0].message.content or None
        except Exception:
            return None

    def interview_feedback(self, prompt: str) -> Optional[str]:
        if not self.enabled or self._client is None:
            return None
        try:
            completion = self._client.chat.completions.create(  # type: ignore[attr-defined]
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a tough but fair interviewer. Respond in Korean with realistic follow-ups and targeted feedback."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
            )
            return completion.choices[0].message.content or None
        except Exception:
            return None

    def transcribe_audio(self, file_path: str) -> Optional[str]:
        """Optional audio transcription via OpenAI if enabled.
        Returns text on success or None on failure/unavailable.
        """
        if not self.enabled or self._client is None:
            return None
        try:
            with open(file_path, "rb") as f:
                try:
                    resp = self._client.audio.transcriptions.create(  # type: ignore[attr-defined]
                        model="gpt-4o-mini-transcribe",
                        file=f,
                    )
                    text = getattr(resp, "text", None)
                    if text:
                        return text
                except Exception:
                    pass
            with open(file_path, "rb") as f2:
                try:
                    resp = self._client.audio.transcriptions.create(  # type: ignore[attr-defined]
                        model="whisper-1",
                        file=f2,
                    )
                    text = getattr(resp, "text", None)
                    return text
                except Exception:
                    return None
        except Exception:
            return None 