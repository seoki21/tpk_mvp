"""
기출문항 피드백 생성 서비스 모듈
Claude API를 사용하여 question_json 기반으로 다국어 피드백(feedback_json)을 생성한다.
각 문제별로 Claude API를 호출하고, 결과를 row 단위로 DB에 UPDATE한다.
"""
import json
from typing import Optional
import anthropic
from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from app.database import get_connection


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


# 피드백 생성 프롬프트 템플릿
_FEEDBACK_PROMPT_TEMPLATE = """당신은 TOPIK(한국어능력시험) 전문 튜터입니다.
아래 TOPIK 문제의 JSON 데이터를 분석하여, 각 선택지별 피드백을 5개 언어(ko, en, ja, zh, vi)로 생성해주세요.

[문제 JSON]
{question_json}

반환 형식 (순수 JSON만, 마크다운 코드블록 없이):
{{
  "correct_answer": 정답번호(숫자),
  "feedback": {{
    "ko": ["①:정답여부_피드백내용", "②:정답여부_피드백내용", ...],
    "en": ["①:정답여부_피드백내용(영어)", ...],
    "ja": ["①:정답여부_피드백내용(일본어)", ...],
    "zh": ["①:정답여부_피드백내용(중국어)", ...],
    "vi": ["①:정답여부_피드백내용(베트남어)", ...]
  }}
}}

규칙:
- 정답여부: 정답이면 'T', 오답이면 'F'
- 피드백내용: 간결하고 읽기 좋게 20~40자 내외, 한국어는 존대어 사용
- 선택지 번호는 동그라미 형식 사용 (①, ②, ③, ④)
- correct_answer는 숫자 형식 (동그라미 아님)
- 반드시 순수 JSON 객체만 출력"""


def _list_questions_for_feedback(exam_key: int) -> list[dict]:
    """
    피드백 생성 대상 문제 목록을 조회한다.
    question_json이 존재하는 문제만 반환한다.

    Args:
        exam_key: 시험 PK

    Returns:
        문제 목록 (question_no, question_json 포함)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT question_no, question_json, feedback_json
              FROM tb_exam_question
             WHERE exam_key = %s AND del_yn = 'N'
               AND question_json IS NOT NULL
             ORDER BY question_no ASC
            """,
            (exam_key,),
        )
        return cursor.fetchall()
    finally:
        conn.close()


def _update_feedback_json(exam_key: int, question_no: int, feedback_json: str) -> None:
    """
    특정 문제의 feedback_json을 업데이트한다.

    Args:
        exam_key: 시험 PK
        question_no: 문제 번호
        feedback_json: 생성된 피드백 JSON 문자열
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tb_exam_question
               SET feedback_json = %s, upd_date = NOW(), upd_user = 'ai'
             WHERE exam_key = %s AND question_no = %s
            """,
            (feedback_json, exam_key, question_no),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _generate_feedback_for_question(question_json: str) -> str:
    """
    Claude API를 호출하여 단일 문제에 대한 다국어 피드백을 생성한다.

    Args:
        question_json: 문제 JSON 문자열

    Returns:
        피드백 JSON 문자열 (minified)

    Raises:
        ValueError: API 응답이 유효한 JSON이 아닌 경우
    """
    client = _get_client()

    prompt = _FEEDBACK_PROMPT_TEMPLATE.format(question_json=question_json)

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    # 응답 텍스트 추출
    result_text = ""
    for block in response.content:
        if block.type == "text":
            result_text += block.text

    # 마크다운 코드블록 제거 (```json ... ``` 형태)
    result_text = result_text.strip()
    if result_text.startswith("```"):
        lines = result_text.split("\n")
        # 첫 줄(```json)과 마지막 줄(```) 제거
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        result_text = "\n".join(lines)

    # JSON 유효성 검증 후 minify하여 반환
    parsed = json.loads(result_text)
    return json.dumps(parsed, ensure_ascii=False)


def generate_feedback_batch(exam_key: int) -> dict:
    """
    특정 시험의 모든 문제에 대해 피드백을 일괄 생성한다.
    각 문제별로 Claude API를 호출하고, 결과를 row 단위로 DB에 UPDATE한다.

    Args:
        exam_key: 시험 PK

    Returns:
        처리 결과 (total, success, failed, errors, token_usage 등)
    """
    questions = _list_questions_for_feedback(exam_key)

    if not questions:
        return {
            "total": 0,
            "success": 0,
            "failed": 0,
            "errors": [],
        }

    success = 0
    failed = 0
    errors = []

    for q in questions:
        question_no = q["question_no"]
        question_json = q["question_json"]

        try:
            # Claude API로 피드백 생성
            feedback_json = _generate_feedback_for_question(question_json)

            # DB 업데이트 (row 단위)
            _update_feedback_json(exam_key, question_no, feedback_json)
            success += 1

        except json.JSONDecodeError as e:
            failed += 1
            errors.append({
                "question_no": question_no,
                "error": f"JSON 파싱 실패: {str(e)}"
            })
        except anthropic.RateLimitError:
            failed += 1
            errors.append({
                "question_no": question_no,
                "error": "API 요청 한도 초과"
            })
        except anthropic.AuthenticationError:
            failed += 1
            errors.append({
                "question_no": question_no,
                "error": "API 인증 실패"
            })
        except anthropic.APIError as e:
            failed += 1
            errors.append({
                "question_no": question_no,
                "error": f"API 오류: {str(e)}"
            })
        except Exception as e:
            failed += 1
            errors.append({
                "question_no": question_no,
                "error": str(e)
            })

    return {
        "total": len(questions),
        "success": success,
        "failed": failed,
        "errors": errors,
    }
