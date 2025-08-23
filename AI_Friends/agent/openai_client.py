from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
import io

from openai import OpenAI

from .config import load_config


class OpenAIClient:
    """OpenAI 클라이언트 래퍼.

    - 텍스트 채팅
    - 이미지 분석 보조 (vision)
    - TTS 오디오 생성
    - 모더레이션
    """

    def __init__(self) -> None:
        cfg = load_config()
        self._client = OpenAI(api_key=cfg.openai_api_key)
        self._chat_model = cfg.chat_model
        self._tts_model = cfg.tts_model
        self._moderation_model = cfg.moderation_model
        self._tts_voice = cfg.tts_voice

    # ---------- Moderation ----------
    def check_policy(self, input_text: str) -> Dict[str, Any]:
        result = self._client.moderations.create(
            model=self._moderation_model,
            input=input_text,
        )
        return result.model_dump()

    # ---------- Chat (text + optional image tool) ----------
    def chat(self, messages: List[Dict[str, Any]], temperature: float = 0.8) -> str:
        """일반 텍스트/이미지 혼합 메시지로 답변 텍스트를 생성"""
        response = self._client.chat.completions.create(
            model=self._chat_model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    # ---------- TTS ----------
    def tts_to_audio_bytes(self, text: str, voice: Optional[str] = None) -> bytes:
        """텍스트를 mp3 바이트로 변환"""
        model = self._tts_model
        voice_name = voice or self._tts_voice
        # New-style Audio generation API (Responses with audio)
        resp = self._client.audio.speech.create(
            model=model,
            voice=voice_name,
            input=text,
            format="mp3",
        )
        return resp.read()

    # ---------- STT ----------
    def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        """오디오 바이트를 텍스트로 전사"""
        bio = io.BytesIO(audio_bytes)
        bio.name = filename
        transcript = self._client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=bio,
        )
        # transcript.text exists for whisper-like models
        return getattr(transcript, "text", "").strip()


