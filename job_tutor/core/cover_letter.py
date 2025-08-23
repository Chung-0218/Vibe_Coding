from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from .llm import LLMProvider


@dataclass
class CoverLetterMetrics:
    num_chars: int
    num_words: int
    num_sentences: int
    avg_sentence_len: float
    long_sentence_count: int


@dataclass
class CoverLetterFeedback:
    metrics: CoverLetterMetrics
    issues: List[str]
    suggestions: List[str]
    star_coverage: Dict[str, bool]
    llm_feedback: Optional[str]


STAR_KEYWORDS = {
    "S": ["상황", "배경", "문제 상황", "계기"],
    "T": ["과제", "문제", "목표", "도전"],
    "A": ["행동", "실행", "역할", "조치"],
    "R": ["결과", "성과", "지표", "배운 점", "회고"],
}

FILLER_WORDS = [
    "열심히", "성실", "책임감", "꼼꼼", "노력", "최선을", "소통", "협업", "정직", "도전",
]

PASSIVE_PATTERNS = [
    r"되었[다습]\b", r"하게 되었습니다", r"되어\b", r"되었습니다", r"되기도",
]

NUMBER_PATTERN = re.compile(r"\d+([.,]\d+)?(%|퍼센트|배|건|명|원|만원|시간|일|주|달|개|회)?")


def _split_sentences_kr(text: str) -> List[str]:
    # Very simple Korean sentence splitter (avoid variable-width lookbehind)
    candidates = re.split(
        r"(?<=\.)\s+|(?<=!)\s+|(?<=\?)\s+|(?<=\uC694\.)\s+|(?<=\uB2E4\.)\s+",
        text.strip(),
    )
    sentences = [s.strip() for s in candidates if s.strip()]
    return sentences


def _count_words_kr(text: str) -> int:
    tokens = re.findall(r"[\w\u3131-\u3163\uAC00-\uD7A3]+", text)
    return len(tokens)


def _detect_star(text: str) -> Dict[str, bool]:
    coverage: Dict[str, bool] = {k: False for k in ["S", "T", "A", "R"]}
    for key, kws in STAR_KEYWORDS.items():
        if any(kw in text for kw in kws):
            coverage[key] = True
    return coverage


def _find_passives(text: str) -> List[str]:
    found = []
    for p in PASSIVE_PATTERNS:
        if re.search(p, text):
            found.append(p)
    return found


def analyze_cover_letter(text: str, job_title: Optional[str] = None, enable_llm: bool = True) -> CoverLetterFeedback:
    text = (text or "").strip()
    sentences = _split_sentences_kr(text)
    num_sentences = len(sentences)
    num_chars = len(text)
    num_words = _count_words_kr(text)
    long_count = sum(1 for s in sentences if len(s) >= 40)
    avg_sentence_len = (sum(len(s) for s in sentences) / num_sentences) if num_sentences else 0.0

    metrics = CoverLetterMetrics(
        num_chars=num_chars,
        num_words=num_words,
        num_sentences=num_sentences,
        avg_sentence_len=round(avg_sentence_len, 2),
        long_sentence_count=long_count,
    )

    issues: List[str] = []
    suggestions: List[str] = []

    if num_chars < 300:
        issues.append("내용이 너무 짧아 설득력이 약할 수 있습니다 (300자 미만).")
        suggestions.append("경험의 배경과 구체적 행동, 수치화된 결과를 추가해 주세요.")
    if long_count > 0:
        issues.append(f"긴 문장이 {long_count}개 있습니다 (40자 이상). 가독성을 위해 분리해 보세요.")
        suggestions.append("각 문장당 하나의 메시지를 담고 불필요한 수식어를 줄여 주세요.")

    # Filler words density
    filler_hits = [w for w in FILLER_WORDS if w in text]
    if len(filler_hits) >= 3:
        issues.append("일반적 미사여구가 많습니다: " + ", ".join(sorted(set(filler_hits))))
        suggestions.append("정성 표현 대신 숫자/지표로 성과를 제시해 주세요.")

    # Passive voice
    passive_found = _find_passives(text)
    if passive_found:
        issues.append("수동적 표현이 감지되었습니다. 보다 능동태로 바꿔 보세요.")
        suggestions.append("예: '배우게 되었습니다' → '학습하고 적용했습니다'")

    # Numbers
    numbers = NUMBER_PATTERN.findall(text)
    if not numbers:
        suggestions.append("성과를 %/숫자로 구체화해 주세요 (예: 전환율 18%p 상승, 리드 120건 확보).")

    star_coverage = _detect_star(text)
    if not all(star_coverage.values()):
        missing = [k for k, v in star_coverage.items() if not v]
        issues.append("STAR 구조의 일부가 약합니다: " + ", ".join(missing))
        suggestions.append("상황-과제-행동-결과가 한 사이클로 보이도록 단락을 구성하세요.")

    llm_feedback: Optional[str] = None
    if enable_llm:
        provider = LLMProvider()
        if provider.enabled:
            prompt_parts = [
                "다음 자기소개서 문항과 답변에 대해 1) 핵심요약(한 문장), 2) 강점, 3) 개선점 3가지, 4) 한 단락 샘플 리라이팅(200자 내외)을 한국어로 간결히 제시하세요.",
            ]
            if job_title:
                prompt_parts.append(f"직무: {job_title}")
            prompt_parts.append("답변:\n" + text)
            llm_feedback = provider.cover_letter_feedback("\n\n".join(prompt_parts))

    return CoverLetterFeedback(
        metrics=metrics,
        issues=issues,
        suggestions=suggestions,
        star_coverage=star_coverage,
        llm_feedback=llm_feedback,
    ) 