from __future__ import annotations
import os
import textwrap
from typing import List, Optional

import streamlit as st

from core.cover_letter import analyze_cover_letter
from core.coding_tutor import TestCase, tutor
from core.interview_assistant import analyze_script, analyze_audio_wav, optional_transcribe


st.set_page_config(page_title="취업 준비 튜터", page_icon="🎯", layout="wide")

st.sidebar.title("설정")
api_key_input = st.sidebar.text_input("OpenAI API Key (선택)", type="password", help="입력 시 LLM 기반 보강 피드백 제공")
if api_key_input:
    os.environ["OPENAI_API_KEY"] = api_key_input

st.title("취업 준비 튜터")
st.caption("자소서 첨삭 · 코딩테스트 튜터 · 면접 도우미")


tab1, tab2, tab3 = st.tabs(["자기소개서 첨삭", "코딩테스트 튜터", "면접 도우미"])


with tab1:
    st.subheader("자기소개서 첨삭 및 피드백")
    job_title = st.text_input("지원 직무 (선택)")
    text_input = st.text_area("자기소개서 문항+답변", height=240, placeholder="문항과 답변을 함께 붙여넣어 주세요", label_visibility="collapsed")
    uploaded = st.file_uploader("또는 .txt 파일 업로드", type=["txt"])

    content = text_input
    if uploaded is not None:
        content = uploaded.read().decode("utf-8", errors="replace")

    col1, col2 = st.columns([1, 1])
    with col1:
        run = st.button("첨삭 실행", use_container_width=True)
    with col2:
        use_llm = st.toggle("LLM 보강 사용", value=False, help="API Key 설정 시 심화 피드백")

    if run and (content or "").strip():
        fb = analyze_cover_letter(content, job_title=job_title or None, enable_llm=use_llm)
        st.markdown("**기초 지표**")
        st.write({
            "문자수": fb.metrics.num_chars,
            "단어수(대략)": fb.metrics.num_words,
            "문장수": fb.metrics.num_sentences,
            "평균 문장 길이": fb.metrics.avg_sentence_len,
            "긴 문장(40자↑)": fb.metrics.long_sentence_count,
        })

        if fb.issues:
            st.markdown("**발견된 이슈**")
            for it in fb.issues:
                st.error(it)
        if fb.suggestions:
            st.markdown("**개선 제안**")
            for sg in fb.suggestions:
                st.info("- " + sg)

        st.markdown("**STAR 요소 커버리지**")
        st.write({
            "S": fb.star_coverage.get("S"),
            "T": fb.star_coverage.get("T"),
            "A": fb.star_coverage.get("A"),
            "R": fb.star_coverage.get("R"),
        })

        if use_llm and fb.llm_feedback:
            st.markdown("**LLM 보강 피드백**")
            st.write(fb.llm_feedback)


with tab2:
    st.subheader("코딩테스트 튜터")
    problem = st.text_area("문제 설명", height=160, placeholder="문제 설명을 입력하세요")

    st.markdown("코드 (Python)")
    code = st.text_area("코드 입력", height=220, placeholder="여기에 Python 코드를 붙여넣으세요", label_visibility="collapsed")

    st.markdown("샘플 테스트케이스")
    tc_input = st.text_area(
        "입력과 기대 출력 (옵션)",
        height=160,
        placeholder=textwrap.dedent(
            """
            각 테스트케이스는 --- 으로 구분합니다.
            입력과 기대출력은 INPUT:, EXPECTED: 라인을 사용합니다.

            예)
            INPUT:
            3 4
            1 2 3 4
            EXPECTED:
            10
            ---
            INPUT:
            5\n6
            EXPECTED:
            11
            """
        ).strip(),
    )

    def parse_testcases(raw: str) -> List[TestCase]:
        if not raw.strip():
            return []
        parts = [p for p in raw.split("---") if p.strip()]
        tcs: List[TestCase] = []
        for idx, part in enumerate(parts, start=1):
            inp = ""
            exp: Optional[str] = None
            block = []
            mode = None
            for line in part.splitlines():
                if line.strip().upper().startswith("INPUT:"):
                    mode = "IN"
                    continue
                if line.strip().upper().startswith("EXPECTED:"):
                    mode = "EX"
                    continue
                if mode == "IN":
                    block.append(line)
                elif mode == "EX":
                    exp = (exp or "") + ("\n" if exp else "") + line
            inp = "\n".join(block)
            tcs.append(TestCase(name=f"TC{idx}", stdin=inp, expected_stdout=exp))
        return tcs

    tcs = parse_testcases(tc_input or "")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        run_tests = st.button("테스트 실행", use_container_width=True)
    with col2:
        ask_llm = st.toggle("LLM 힌트 요청", value=False)
    with col3:
        include_ref = st.toggle("정답 포함", value=False, help="LLM 사용 시 레퍼런스 정답 코드 포함")

    if run_tests and (code or "").strip():
        resp = tutor(code=code, problem=problem or "", testcases=tcs, ask_llm_solution=ask_llm, include_reference=include_ref)
        st.markdown("**정적 분석**")
        st.write({
            "문법 정상": resp.static.syntax_ok,
            "문법 오류": resp.static.syntax_error,
            "복잡도 추정": resp.static.complexity_estimate,
            "패턴": resp.static.detected_patterns,
            "경고": resp.static.warnings,
        })

        if resp.results:
            st.markdown("**테스트 결과**")
            for r in resp.results:
                box = st.container(border=True)
                with box:
                    st.write({"이름": r.name, "통과": r.passed, "종료코드": r.exit_code})
                    with st.expander("stdout"):
                        st.code(r.stdout or "", language="text")
                    if r.stderr:
                        with st.expander("stderr"):
                            st.code(r.stderr, language="text")
                    if r.hint:
                        st.info(r.hint)

        if ask_llm and resp.llm_hint:
            st.markdown("**LLM 힌트**")
            st.write(resp.llm_hint)


with tab3:
    st.subheader("면접 도우미")
    script = st.text_area("답변 스크립트 (텍스트)", height=200, placeholder="면접 답변 스크립트를 붙여넣으세요. 오디오 업로드와 함께 사용하면 길이/속도 지표도 확인 가능합니다.")
    audio = st.file_uploader("오디오 업로드 (.wav)", type=["wav"])

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        run_interview = st.button("분석 실행", use_container_width=True)
    with col2:
        use_llm_iv = st.toggle("LLM 보강 사용", value=False)
    with col3:
        use_stt = st.toggle("STT 시도", value=False, help="오디오에서 텍스트를 자동 전사합니다")

    if run_interview and ((script or "").strip() or audio is not None):
        if (script or "").strip():
            fb = analyze_script(script, enable_llm=use_llm_iv)
            st.markdown("**STAR 커버리지**")
            st.write(fb.star_coverage)
            if fb.strengths:
                st.markdown("**강점**")
                for s in fb.strengths:
                    st.success("- " + s)
            if fb.improvements:
                st.markdown("**개선점**")
                for imp in fb.improvements:
                    st.info("- " + imp)
            st.markdown("**꼬리질문**")
            for q in fb.follow_ups:
                st.write("- " + q)
            if use_llm_iv and fb.llm_feedback:
                st.markdown("**LLM 보강 피드백**")
                st.write(fb.llm_feedback)

        if audio is not None:
            with st.spinner("오디오 분석 중..."):
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio.getbuffer())
                    tmp_path = tmp.name
                aa = analyze_audio_wav(tmp_path, approx_text_length_chars=len(script or ""))
                st.markdown("**오디오 지표**")
                st.write({
                    "길이(초)": aa.duration_sec,
                    "샘플레이트": aa.sample_rate,
                    "채널": aa.channels,
                    "분당 문자수(대략)": aa.approx_chars_per_min,
                    "비고": aa.note,
                })
                if use_stt:
                    st.markdown("**전사(STT) 텍스트**")
                    tx = optional_transcribe(tmp_path)
                    if tx:
                        st.write(tx)
                        st.markdown("**전사 텍스트 기반 피드백**")
                        fb2 = analyze_script(tx, enable_llm=use_llm_iv)
                        st.write(fb2.star_coverage)
                        for s in fb2.strengths:
                            st.success("- " + s)
                        for imp in fb2.improvements:
                            st.info("- " + imp)
                    else:
                        st.warning("전사에 실패했거나 사용 가능한 STT가 없습니다.")
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

st.caption("Made with ❤️  | 로컬에서 안전하게 실행됩니다. API Key 미설정 시에도 기본 기능이 동작합니다.") 