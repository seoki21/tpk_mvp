"""
기출문항 피드백 생성 서비스 모듈
Claude API 또는 Google Gemini API를 사용하여 question_json 기반으로 다국어 피드백(feedback_json)을 생성한다.
각 문제별로 AI API를 호출하고, 결과를 row 단위로 DB에 UPDATE한다.
선택된 locale 목록에 따라 프롬프트에 언어 목록을 동적으로 주입한다.
"""
import json
from typing import Optional
import anthropic
from google import genai
from app.config import (
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    GOOGLE_AI_API_KEY, GOOGLE_AI_MODEL,
)
from app.database import get_connection
from app.services.api_usage import save_usage


# Anthropic 클라이언트 싱글턴
_anthropic_client: Optional[anthropic.Anthropic] = None

# Google AI 클라이언트 싱글턴
_google_client: Optional[genai.Client] = None


def _get_anthropic_client() -> anthropic.Anthropic:
    """
    Anthropic 클라이언트 싱글턴을 반환한다.
    API 키가 설정되지 않은 경우 명확한 에러를 발생시킨다.
    """
    global _anthropic_client
    if _anthropic_client is None:
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _anthropic_client


def _get_google_client() -> genai.Client:
    """
    Google AI 클라이언트 싱글턴을 반환한다.
    API 키가 설정되지 않은 경우 명확한 에러를 발생시킨다.
    """
    global _google_client
    if _google_client is None:
        if not GOOGLE_AI_API_KEY:
            raise ValueError("GOOGLE_AI_API_KEY 환경변수가 설정되지 않았습니다.")
        _google_client = genai.Client(api_key=GOOGLE_AI_API_KEY)
    return _google_client


# 피드백 생성 프롬프트 (외부 파일에서 로드)
from app.utils.prompt_loader import load_prompt
_FEEDBACK_PROMPT_TEMPLATE = load_prompt("feedback_generate")
_FEEDBACK_LISTENING_PROMPT_TEMPLATE = load_prompt("feedback_generate_listening")


def _build_languages_text(locales: list[str]) -> str:
    """
    선택된 locale 코드 목록을 프롬프트에 삽입할 언어 목록 텍스트로 변환한다.
    한국어(ko)는 기본 피드백 작성 언어이므로 번역 목록에서 제외한다.

    Args:
        locales: locale 코드 목록 (예: ['ko', 'en', 'ja', 'zh'])

    Returns:
        프롬프트에 삽입할 언어 목록 텍스트 (예: "1. 영어 en\n2. 일본어 ja\n3. 중국어 zh")
    """
    # locale 코드 → 언어명 매핑 (tb_code의 code_desc 대신 고정 매핑 사용 — 프롬프트 일관성)
    locale_names = {
        "en": "영어", "vi": "베트남어", "zh": "중국어", "zh-TW": "대만어",
        "th": "태국어", "id": "인도네시아어", "uz": "우즈베키스탄어", "ru": "러시아어",
        "ja": "일본어", "mn": "몽골어", "ne": "네팔어", "my": "미얀마어",
    }
    # ko 제외, 번역 대상 언어만 번호 매겨서 목록 생성
    lines = []
    idx = 1
    for loc in locales:
        if loc == "ko":
            continue
        name = locale_names.get(loc, loc)
        lines.append(f"{idx}. {name} {loc}")
        idx += 1
    return "\n".join(lines)


def _get_prompt_template(section: str = None) -> str:
    """
    영역에 따라 적절한 피드백 프롬프트 템플릿을 반환한다.

    Args:
        section: 영역명 ('듣기', '읽기' 등). None이면 기본(읽기) 프롬프트.

    Returns:
        프롬프트 템플릿 문자열
    """
    if section == "듣기":
        return _FEEDBACK_LISTENING_PROMPT_TEMPLATE
    return _FEEDBACK_PROMPT_TEMPLATE


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


def _get_section_name_by_exam(exam_key: int) -> Optional[str]:
    """
    시험키로 영역명(section_name)을 조회한다.

    Args:
        exam_key: 시험 PK

    Returns:
        영역명 (예: '듣기', '읽기') 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.code_name AS section_name
              FROM tb_exam_list e
              LEFT JOIN tb_code c ON c.group_code = 'section' AND c.code = e.section
             WHERE e.exam_key = %s
            """,
            (exam_key,),
        )
        row = cursor.fetchone()
        return row["section_name"] if row else None
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


def save_feedback_single(exam_key: int, question_no: int, feedback_json: str) -> None:
    """
    단건 피드백 JSON을 DB에 저장한다.

    Args:
        exam_key: 시험 PK
        question_no: 문제 번호
        feedback_json: 피드백 JSON 문자열
    """
    _update_feedback_json(exam_key, question_no, feedback_json)


def update_question_single(
    exam_key: int, question_no: int,
    question_json: Optional[str] = None, feedback_json: Optional[str] = None
) -> bool:
    """
    단건 문제의 question_json, feedback_json을 업데이트한다.
    기존 row가 없으면 False를 반환한다 (INSERT 하지 않음).

    Args:
        exam_key: 시험 PK
        question_no: 문제 번호
        question_json: 문제 JSON 문자열 (None이면 업데이트 안 함)
        feedback_json: 피드백 JSON 문자열 (None이면 업데이트 안 함)

    Returns:
        True: 업데이트 성공, False: 해당 row가 존재하지 않음
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 해당 row 존재 여부 확인
        cursor.execute(
            "SELECT 1 FROM tb_exam_question WHERE exam_key = %s AND question_no = %s",
            (exam_key, question_no),
        )
        if not cursor.fetchone():
            return False

        # SET 절 동적 구성
        set_parts = ["upd_date = NOW()", "upd_user = 'admin'"]
        params = []
        if question_json is not None:
            set_parts.append("question_json = %s")
            params.append(question_json)
        if feedback_json is not None:
            set_parts.append("feedback_json = %s")
            params.append(feedback_json)

        params.extend([exam_key, question_no])

        cursor.execute(
            f"""
            UPDATE tb_exam_question
               SET {', '.join(set_parts)}
             WHERE exam_key = %s AND question_no = %s
            """,
            tuple(params),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _extract_json_from_response(result_text: str) -> str:
    """
    AI 응답 텍스트에서 JSON 객체를 추출하고 유효성을 검증한다.
    마크다운 코드블록, 앞뒤 설명 텍스트를 자동 제거한다.

    Args:
        result_text: AI 응답 텍스트

    Returns:
        minified JSON 문자열

    Raises:
        ValueError: JSON 객체를 찾을 수 없거나 유효하지 않은 경우
    """
    result_text = result_text.strip()

    # 마크다운 코드블록 제거 (```json ... ``` 형태)
    if result_text.startswith("```"):
        lines = result_text.split("\n")
        # 첫 줄(```json)과 마지막 줄(```) 제거
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        result_text = "\n".join(lines).strip()

    # 응답에 설명 텍스트가 포함된 경우 JSON 객체 부분만 추출
    if not result_text.startswith("{"):
        start_idx = result_text.find("{")
        if start_idx == -1:
            raise ValueError("응답에서 JSON 객체를 찾을 수 없습니다.")
        end_idx = result_text.rfind("}")
        if end_idx == -1:
            raise ValueError("응답에서 JSON 객체의 끝을 찾을 수 없습니다.")
        result_text = result_text[start_idx:end_idx + 1]

    # JSON 유효성 검증 후 minify하여 반환
    import re
    try:
        parsed = json.loads(result_text)
    except json.JSONDecodeError:
        # AI가 trailing comma, 줄임표(...) 등 비표준 JSON을 반환하는 경우 보정 시도
        cleaned = result_text
        # 줄임표 항목 제거: "...", ... , "①:..." 등
        cleaned = re.sub(r',\s*"[^"]*\.\.\.[^"]*"', '', cleaned)
        cleaned = re.sub(r',\s*\.\.\.', '', cleaned)
        # trailing comma 제거: ,] 또는 ,}
        cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # 보정 실패 — 다국어 문자를 포함하지 않는 안전한 에러 메시지 생성
            raise ValueError(
                f"AI 응답 JSON 파싱 실패 (응답 길이: {len(result_text)}자). "
                "max_tokens 부족으로 응답이 잘렸을 수 있습니다. 언어 수를 줄여서 다시 시도하세요."
            )
    return json.dumps(parsed, ensure_ascii=False)


def _calc_max_tokens(locales: list[str] = None) -> int:
    """
    선택된 locale 수에 비례하여 적절한 max_tokens를 계산한다.
    언어 1개당 약 500토큰, 기본(ko) 1000토큰 + 여유 500토큰.
    """
    lang_count = len(locales) if locales else 1
    return min(1000 + lang_count * 500 + 500, 16000)


def _generate_feedback_claude(question_json: str, locales: list[str] = None, section: str = None) -> str:
    """
    Claude API를 호출하여 단일 문제에 대한 다국어 피드백을 생성한다.

    Args:
        question_json: 문제 JSON 문자열
        locales: 생성할 locale 코드 목록 (None이면 ko만)
        section: 영역명 (프롬프트 분기용)

    Returns:
        피드백 JSON 문자열 (minified)
    """
    client = _get_anthropic_client()
    template = _get_prompt_template(section)
    languages_text = _build_languages_text(locales) if locales else ""
    prompt = template.replace("{languages}", languages_text).replace("{question_json}", question_json)
    max_tokens = _calc_max_tokens(locales)

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    # API 사용 이력 저장
    try:
        save_usage("admin", "feedback_generate", "claude", ANTHROPIC_MODEL,
                   response.usage.input_tokens, response.usage.output_tokens)
    except Exception:
        pass

    # 응답 텍스트 추출
    result_text = ""
    for block in response.content:
        if block.type == "text":
            result_text += block.text

    return _extract_json_from_response(result_text)


def _generate_feedback_gemini(question_json: str, locales: list[str] = None, section: str = None) -> str:
    """
    Google Gemini API를 호출하여 단일 문제에 대한 다국어 피드백을 생성한다.

    Args:
        question_json: 문제 JSON 문자열
        locales: 생성할 locale 코드 목록 (None이면 ko만)
        section: 영역명 (프롬프트 분기용)

    Returns:
        피드백 JSON 문자열 (minified)
    """
    client = _get_google_client()
    template = _get_prompt_template(section)
    languages_text = _build_languages_text(locales) if locales else ""
    prompt = template.replace("{languages}", languages_text).replace("{question_json}", question_json)

    response = client.models.generate_content(
        model=GOOGLE_AI_MODEL,
        contents=prompt,
    )

    # API 사용 이력 저장
    try:
        in_tok = response.usage_metadata.prompt_token_count or 0
        out_tok = response.usage_metadata.candidates_token_count or 0
        save_usage("admin", "feedback_generate", "gemini", GOOGLE_AI_MODEL, in_tok, out_tok)
    except Exception:
        pass

    return _extract_json_from_response(response.text)


def _generate_feedback_for_question(
    question_json: str, ai_provider: str = "claude",
    locales: list[str] = None, section: str = None
) -> str:
    """
    AI API를 호출하여 단일 문제에 대한 다국어 피드백을 생성한다.
    ai_provider에 따라 Claude 또는 Gemini를 사용한다.

    Args:
        question_json: 문제 JSON 문자열
        ai_provider: AI 제공자 ("claude" 또는 "gemini")
        locales: 생성할 locale 코드 목록
        section: 영역명 (프롬프트 분기용)

    Returns:
        피드백 JSON 문자열 (minified)

    Raises:
        ValueError: 지원하지 않는 AI 제공자인 경우
    """
    if ai_provider == "gemini":
        return _generate_feedback_gemini(question_json, locales, section)
    elif ai_provider == "claude":
        return _generate_feedback_claude(question_json, locales, section)
    else:
        raise ValueError(f"지원하지 않는 AI 제공자입니다: {ai_provider}")


def generate_feedback_single(
    question_json: str, ai_provider: str = "claude",
    locales: list[str] = None, section: str = None
) -> str:
    """
    단일 문제의 question_json을 받아 AI API로 다국어 피드백을 생성한다.
    DB 저장 없이 결과만 반환한다 (프론트에서 편집 상태에 반영).

    Args:
        question_json: 문제 JSON 문자열
        ai_provider: AI 제공자 ("claude" 또는 "gemini")
        locales: 생성할 locale 코드 목록
        section: 영역명 (프롬프트 분기용)

    Returns:
        피드백 JSON 문자열 (minified, 플랫 구조)
    """
    return _generate_feedback_for_question(question_json, ai_provider, locales, section)


def generate_feedback_batch(
    exam_key: int, ai_provider: str = "claude", locales: list[str] = None
) -> dict:
    """
    특정 시험의 모든 문제에 대해 피드백을 일괄 생성한다.
    각 문제별로 AI API를 호출하고, 결과를 row 단위로 DB에 UPDATE한다.

    Args:
        exam_key: 시험 PK
        ai_provider: AI 제공자 ("claude" 또는 "gemini")
        locales: 생성할 locale 코드 목록

    Returns:
        처리 결과 (total, success, failed, errors 등)
    """
    questions = _list_questions_for_feedback(exam_key)

    if not questions:
        return {
            "total": 0,
            "success": 0,
            "failed": 0,
            "errors": [],
        }

    # 시험의 영역명 조회 (프롬프트 분기용)
    section = _get_section_name_by_exam(exam_key)

    success = 0
    failed = 0
    errors = []

    for q in questions:
        question_no = q["question_no"]
        question_json = q["question_json"]

        try:
            # AI API로 피드백 생성
            feedback_json = _generate_feedback_for_question(
                question_json, ai_provider, locales, section
            )

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
        except anthropic.APIStatusError as e:
            failed += 1
            if e.status_code == 529:
                errors.append({
                    "question_no": question_no,
                    "error": "AI 서버 과부하. 잠시 후 다시 시도해 주세요."
                })
                break  # 과부하 상태에서는 나머지 호출도 실패하므로 중단
            else:
                errors.append({
                    "question_no": question_no,
                    "error": f"API 오류: {e.message}"
                })
        except anthropic.APIError as e:
            failed += 1
            errors.append({
                "question_no": question_no,
                "error": f"API 오류: {e.message}"
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
