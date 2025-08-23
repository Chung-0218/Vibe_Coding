from __future__ import annotations
import ast
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .llm import LLMProvider


@dataclass
class TestCase:
    name: str
    stdin: str
    expected_stdout: Optional[str] = None


@dataclass
class TestResult:
    name: str
    passed: bool
    stdout: str
    stderr: str
    exit_code: int
    hint: Optional[str]


@dataclass
class StaticAnalysis:
    syntax_ok: bool
    syntax_error: Optional[str]
    complexity_estimate: str
    detected_patterns: List[str]
    warnings: List[str]


@dataclass
class TutorResponse:
    static: StaticAnalysis
    results: List[TestResult]
    llm_hint: Optional[str]


COMMON_HINTS = [
    ("IndexError", "인덱스 범위를 확인하세요. off-by-one 오류(<= vs <)를 점검해 보세요."),
    ("KeyError", "dict 키 존재 여부 확인 또는 .get 사용을 고려하세요."),
    ("ValueError", "입력 파싱 시 공백/개행/형 변환(int/float) 부분을 점검하세요."),
    ("RecursionError", "재귀 깊이를 줄이거나 반복문으로 전환을 고려하세요."),
    ("Timeout", "시간 제한에 걸렸습니다. 알고리즘 복잡도를 낮추거나 I/O를 최적화하세요."),
]


def _estimate_complexity(tree: ast.AST) -> Tuple[str, List[str]]:
    total_loops = 0
    detected: List[str] = []
    function_stack: List[str] = []

    def visit(node: ast.AST, loop_depth: int = 0) -> None:
        nonlocal total_loops
        if isinstance(node, (ast.For, ast.While)):
            total_loops += 1
            if loop_depth >= 1:
                detected.append("중첩 루프 감지")
            for child in ast.iter_child_nodes(node):
                visit(child, loop_depth + 1)
            return

        if isinstance(node, ast.FunctionDef):
            function_stack.append(node.name)
            for child in ast.iter_child_nodes(node):
                visit(child, loop_depth)
            function_stack.pop()
            return

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id.lower() in {"bfs", "dfs"}:
                    detected.append(f"{func.id.upper()} 호출 감지")
                if function_stack and func.id == function_stack[-1]:
                    detected.append("재귀 사용")

        for child in ast.iter_child_nodes(node):
            visit(child, loop_depth)

    visit(tree)

    if total_loops >= 2:
        estimate = "O(n^2) 이상 가능성"
    elif total_loops == 1:
        estimate = "O(n)~O(n log n) 가능성"
    else:
        estimate = "O(n) 또는 더 낮음"

    return estimate, detected


def _static_analysis(code: str) -> StaticAnalysis:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return StaticAnalysis(
            syntax_ok=False,
            syntax_error=f"SyntaxError: {e.msg} (line {e.lineno}, col {e.offset})",
            complexity_estimate="N/A",
            detected_patterns=[],
            warnings=["문법 오류를 먼저 해결하세요"],
        )

    complexity, detected = _estimate_complexity(tree)

    warnings: List[str] = []
    source_lower = code.lower()
    if "input(" in source_lower and "print(" not in source_lower:
        warnings.append("입력을 받지만 출력을 하지 않을 수 있습니다. 출력 로직을 확인하세요.")
    if "while true" in source_lower:
        warnings.append("무한 루프 가능성: 종료 조건을 확인하세요.")

    return StaticAnalysis(
        syntax_ok=True,
        syntax_error=None,
        complexity_estimate=complexity,
        detected_patterns=detected,
        warnings=warnings,
    )


def _run_single(code: str, tc: TestCase, timeout_sec: int = 2) -> TestResult:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
        user_script = f.name

    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-S", "-B", user_script],
            input=tc.stdin.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_sec,
        )
        stdout = proc.stdout.decode("utf-8", errors="replace").strip()
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        return TestResult(
            name=tc.name,
            passed=False,
            stdout="",
            stderr="Timeout",
            exit_code=124,
            hint=_hint_from_error("Timeout"),
        )

    passed = True
    hint: Optional[str] = None
    if tc.expected_stdout is not None:
        expected = (tc.expected_stdout or "").strip()
        passed = (stdout == expected)
        if not passed:
            hint = _diff_hint(stdout, expected)

    if not passed and not hint:
        hint = _hint_from_error(stderr)

    return TestResult(
        name=tc.name,
        passed=passed,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        hint=hint,
    )


def _diff_hint(actual: str, expected: str) -> str:
    def norm(s: str) -> List[str]:
        return [line.rstrip() for line in s.splitlines()]

    a, e = norm(actual), norm(expected)
    return (
        "출력이 기대값과 다릅니다.\n"
        f"- 기대 출력 라인수: {len(e)}, 실제: {len(a)}\n"
        "- 공백/개행/대소문자/형 변환(int/str) 문제를 점검하세요."
    )


def _hint_from_error(stderr: str) -> Optional[str]:
    if not stderr:
        return None
    for key, hint in COMMON_HINTS:
        if key.lower() in stderr.lower():
            return hint
    return "실패 원인을 출력 로그에서 확인하세요. 입력 파싱/자료구조/복잡도 문제를 우선 점검하세요."


def tutor(
    code: str,
    problem: str,
    testcases: List[TestCase],
    ask_llm_solution: bool = False,
    include_reference: bool = False,
) -> TutorResponse:
    static = _static_analysis(code)

    results: List[TestResult] = []
    if static.syntax_ok:
        for tc in testcases:
            results.append(_run_single(code, tc))

    llm_hint: Optional[str] = None
    if ask_llm_solution:
        provider = LLMProvider()
        if provider.enabled:
            extra = "\n4) 가능하면 파이썬 레퍼런스 정답 코드를 맨 아래 하나의 코드블록으로 제시하세요." if include_reference else ""
            prompt = (
                "다음 코딩테스트 문제와 사용자가 제출한 Python 코드가 있습니다. "
                "1) 실패 가능성이 높은 부분을 짚고, 2) 테스트 설계 힌트, 3) 필요시 시간복잡도 개선 아이디어를 간결히 제시하세요."
                + extra
                + "\n\n[문제]\n" + problem + "\n\n[코드]\n" + code
            )
            llm_hint = provider.coding_hint(prompt)

    return TutorResponse(static=static, results=results, llm_hint=llm_hint) 