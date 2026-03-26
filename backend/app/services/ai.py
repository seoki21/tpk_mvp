"""
AI 피드백 서비스 모듈
Anthropic Claude API를 사용하여 TOPIK 학습 피드백을 생성한다.
anthropic Python SDK를 사용하며 HTTP 직접 호출은 하지 않는다.
"""
from typing import Optional
import anthropic
from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


# Anthropic 클라이언트 싱글턴
_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    """
    Anthropic 클라이언트 싱글턴을 반환한다.
    API 키가 설정되지 않은 경우 명확한 에러를 발생시킨다.
    """
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


# 언어 코드 → 언어명 매핑 (시스템 프롬프트에서 사용)
_LANGUAGE_MAP = {
    "ko": "한국어",
    "en": "English",
    "ja": "日本語",
}

# TOPIK 튜터 시스템 프롬프트 템플릿
_SYSTEM_PROMPT_TEMPLATE = """당신은 TOPIK(한국어능력시험) 전문 튜터입니다.
학생이 TOPIK 문제를 풀고 답을 제출하면, 다음을 수행합니다:
1. 학생의 답이 맞는지 틀렸는지 판단합니다.
2. 정답에 대한 상세한 해설을 제공합니다.
3. 틀린 경우, 왜 틀렸는지 설명하고 올바른 이해를 돕습니다.
4. 관련 문법이나 어휘가 있다면 추가 설명을 제공합니다.

반드시 {language_name}(으)로 응답하십시오."""


def generate_feedback(
    question_text: str,
    choices: Optional[list[str]],
    correct_answer: str,
    user_answer: str,
    question_type: Optional[str] = None,
    tpk_level: Optional[str] = None,
    language: str = "ko",
) -> dict:
    """
    TOPIK 문제에 대한 AI 피드백을 생성한다.

    Args:
        question_text: 문제 본문
        choices: 선택지 목록 (객관식)
        correct_answer: 정답
        user_answer: 사용자 답변
        question_type: 문제 유형 (읽기, 듣기, 쓰기 등)
        tpk_level: 토픽 레벨 (TOPIK I, TOPIK II 등)
        language: 응답 언어 (ko/en/ja)

    Returns:
        feedback, is_correct, model, token_usage를 포함한 딕셔너리

    Raises:
        ValueError: API 키 미설정
        anthropic.APIError: API 호출 실패
    """
    client = _get_client()

    # 언어명 결정 (미지원 언어는 한국어로 폴백)
    language_name = _LANGUAGE_MAP.get(language, "한국어")

    # 시스템 프롬프트 생성
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(language_name=language_name)

    # 사용자 메시지 조합 — 문제 정보를 구조화하여 전달
    user_message_parts = []

    if tpk_level:
        user_message_parts.append(f"[토픽 레벨] {tpk_level}")
    if question_type:
        user_message_parts.append(f"[문제 유형] {question_type}")

    user_message_parts.append(f"[문제]\n{question_text}")

    if choices:
        choices_text = "\n".join(f"  {i + 1}. {choice}" for i, choice in enumerate(choices))
        user_message_parts.append(f"[선택지]\n{choices_text}")

    user_message_parts.append(f"[정답] {correct_answer}")
    user_message_parts.append(f"[학생의 답] {user_answer}")

    user_message = "\n\n".join(user_message_parts)

    # Claude API 호출
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ],
    )

    # 응답 텍스트 추출
    feedback_text = ""
    for block in response.content:
        if block.type == "text":
            feedback_text += block.text

    # 정답 여부는 로컬에서 비교 (AI 판단에 의존하지 않음)
    is_correct = user_answer.strip() == correct_answer.strip()

    return {
        "feedback": feedback_text,
        "is_correct": is_correct,
        "model": response.model,
        "token_usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }
