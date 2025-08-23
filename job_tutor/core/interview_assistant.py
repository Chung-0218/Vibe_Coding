from __future__ import annotations
import contextlib
import os
import random
import wave
from dataclasses import dataclass
from typing import Dict, List, Optional

from .llm import LLMProvider


FOLLOW_UPS = [
    "그 경험에서 본인이 한 가장 구체적인 행동은 무엇이었나요?",
    "성과를 수치로 표현하면 어느 정도였나요? 기준과 비교해 설명해 주세요.",
    "동료/이해관계자와의 갈등은 어떻게 조율했나요?",
    "같은 상황이 온다면 무엇을 다르게 하실 건가요?",
    "그 경험이 지원 직무의 어떤 역량과 연결되나요?",
]

STAR_CLUES = {
    "S": ["상황", "배경", "문제"],
    "T": ["목표", "과제", "역할"],
    "A": ["행동", "시도", "실행"],
    "R": ["결과", "성과", "학습"],
}


@dataclass
class TextInterviewFeedback:
    star_coverage: Dict[str, bool]
    strengths: List[str]
    improvements: List[str]
    follow_ups: List[str]
    llm_feedback: Optional[str]


@dataclass
class AudioAnalysis:
    duration_sec: float
    sample_rate: int
    channels: int
    approx_chars_per_min: Optional[float]
    note: Optional[str]


def analyze_script(text: str, enable_llm: bool = True) -> TextInterviewFeedback:
    text = (text or "").strip()

    coverage = {k: any(any(w in text for w in ws) for ws in [v]) for k, v in STAR_CLUES.items()}

    strengths: List[str] = []
    improvements: List[str] = []

    if len(text) >= 300:
        strengths.append("충분한 분량으로 상황 설명이 가능합니다.")
    else:
        improvements.append("분량이 다소 짧습니다. 배경→행동→결과의 흐름을 보강하세요.")

    has_number = any(ch.isdigit() for ch in text)
    if has_number:
        strengths.append("수치/지표 제시가 있습니다. 구체성을 유지하세요.")
    else:
        improvements.append("성과를 숫자로 제시하면 설득력이 높아집니다.")

    for k, covered in coverage.items():
        if not covered:
            improvements.append(f"STAR 중 '{k}' 요소가 약합니다.")

    follow_ups = random.sample(FOLLOW_UPS, k=min(3, len(FOLLOW_UPS)))

    llm_feedback: Optional[str] = None
    if enable_llm:
        provider = LLMProvider()
        if provider.enabled:
            prompt = (
                "면접관처럼 다음 스크립트를 읽고 1) 날카로운 꼬리질문 3개, 2) 강점 2개, 3) 개선점 3개를 한국어로 간결히 제시하세요.\n\n"
                + text
            )
            llm_feedback = provider.interview_feedback(prompt)

    return TextInterviewFeedback(
        star_coverage=coverage,
        strengths=strengths,
        improvements=improvements,
        follow_ups=follow_ups,
        llm_feedback=llm_feedback,
    )


def analyze_audio_wav(file_path: str, approx_text_length_chars: Optional[int] = None) -> AudioAnalysis:
    # Basic WAV stats using stdlib wave (no external deps)
    if not os.path.exists(file_path):
        return AudioAnalysis(0.0, 0, 0, None, note="파일을 찾을 수 없습니다")

    try:
        with contextlib.closing(wave.open(file_path, "rb")) as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            channels = wf.getnchannels()
            duration = frames / float(rate) if rate else 0.0
    except wave.Error:
        return AudioAnalysis(0.0, 0, 0, None, note="WAV 형식이 아닙니다. .wav 파일을 올려주세요")

    cpm: Optional[float] = None
    if approx_text_length_chars and duration > 0:
        cpm = (approx_text_length_chars / duration) * 60.0

    return AudioAnalysis(
        duration_sec=round(duration, 2),
        sample_rate=rate,
        channels=channels,
        approx_chars_per_min=round(cpm, 1) if cpm else None,
        note=None,
    )


def optional_transcribe(file_path: str) -> Optional[str]:
    """Try to transcribe using OpenAI (if key set) or local whisper/faster-whisper if installed.
    Returns None if unavailable or on error.
    """
    # 1) Try OpenAI via LLMProvider
    provider = LLMProvider()
    if provider.enabled:
        text = provider.transcribe_audio(file_path)
        if text:
            return text

    # 2) Try local whisper
    try:
        import whisper  # type: ignore

        model = whisper.load_model("base")
        result = model.transcribe(file_path, fp16=False, language="ko")
        txt = result.get("text") if isinstance(result, dict) else None
        if txt:
            return txt.strip()
    except Exception:
        pass

    # 3) Try faster-whisper
    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel("base")
        segments, info = model.transcribe(file_path, language="ko")
        txt_parts: List[str] = []
        for seg in segments:
            txt_parts.append(seg.text)
        if txt_parts:
            return " ".join(txt_parts).strip()
    except Exception:
        pass

    return None 