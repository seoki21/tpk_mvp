"""
기출문항 PDF → JSON 변환 서비스 모듈
Anthropic Claude API 또는 Google Gemini API의 PDF 분석 기능을 사용하여 기출문제 PDF를 JSON으로 변환한다.
SSE(Server-Sent Events) 형식으로 변환 결과를 실시간 전달한다.
"""
import os
import json
import base64
import asyncio
from typing import Optional, AsyncGenerator
import anthropic
from google import genai
from app.config import (
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    GOOGLE_AI_API_KEY, GOOGLE_AI_MODEL,
)
from app.services.exam_file import get_file
from app.services.api_usage import save_usage
from app.services import r2_storage


# Anthropic 비동기 클라이언트 싱글턴
_async_client: Optional[anthropic.AsyncAnthropic] = None

# Google AI 클라이언트 싱글턴 (비동기)
_google_client: Optional[genai.Client] = None


def _get_async_client() -> anthropic.AsyncAnthropic:
    """
    Anthropic 비동기 클라이언트 싱글턴을 반환한다.
    API 키가 설정되지 않은 경우 명확한 에러를 발생시킨다.
    """
    global _async_client
    if _async_client is None:
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        _async_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    return _async_client


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


def _read_pdf_as_base64(r2_key: str) -> str:
    """R2에서 PDF 파일을 다운로드하여 base64 문자열로 반환한다. (동기 I/O)"""
    data = r2_storage.download_bytes(r2_key)
    return base64.standard_b64encode(data).decode("utf-8")


def _read_pdf_bytes(r2_key: str) -> bytes:
    """R2에서 PDF 파일을 다운로드하여 바이트 데이터로 반환한다. (동기 I/O)"""
    return r2_storage.download_bytes(r2_key)


def _format_sse(event: str, data: dict) -> str:
    """SSE 이벤트 문자열을 생성한다."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# PDF 분석 프롬프트 (외부 파일에서 로드, 영역별 분기)
from app.utils.prompt_loader import load_prompt
from app.database import get_connection

_PDF_CONVERT_PROMPT = load_prompt("pdf_convert")
_PDF_CONVERT_LISTENING_PROMPT = load_prompt("pdf_convert_listening")

# 영역 code_name → 프롬프트 매핑 (매핑에 없는 영역은 기본 프롬프트 사용)
_SECTION_PROMPT_MAP = {
    "듣기": _PDF_CONVERT_LISTENING_PROMPT,
}


def _get_section_name(section_code: str) -> Optional[str]:
    """
    영역 코드 값으로 tb_code에서 code_name을 조회하여 반환한다.

    Args:
        section_code: 영역 코드 (예: "1", "2")

    Returns:
        코드명 (예: "듣기", "읽기") 또는 None
    """
    if not section_code:
        return None
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT code_name
              FROM tb_code
             WHERE group_code = 'section'
               AND code = %s
            """,
            (int(section_code),),
        )
        row = cursor.fetchone()
        return row["code_name"] if row else None
    finally:
        conn.close()


def _get_template_data(exam_key: int, section_code: str) -> str:
    """
    tb_exam_template에서 해당 시험의 문제번호별 passage_type/question_type을 조회하여
    프롬프트에 삽입할 참조 텍스트를 생성한다.

    Args:
        exam_key: 시험 PK
        section_code: 영역 코드 (예: "15", "16")

    Returns:
        포맷된 참조 텍스트 (빈 문자열이면 템플릿 데이터 없음)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # tb_exam_list에서 tpk_type, tpk_level 조회
        cursor.execute(
            "SELECT tpk_type, tpk_level FROM tb_exam_list WHERE exam_key = %s",
            (exam_key,),
        )
        exam = cursor.fetchone()
        if not exam or not exam["tpk_type"] or not exam["tpk_level"]:
            return ""

        tpk_type = int(exam["tpk_type"])
        tpk_level = int(exam["tpk_level"])
        section = int(section_code) if section_code else None
        if section is None:
            return ""

        # tb_exam_template에서 문제번호별 passage_type/question_type 조회
        cursor.execute(
            """
            SELECT t.question_no, t.passage_type, t.question_type,
                   cp.code_name AS passage_type_name,
                   cq.code_name AS question_type_name
              FROM tb_exam_template t
              LEFT JOIN tb_code cp ON cp.group_code = 'passage_type' AND cp.code = t.passage_type
              LEFT JOIN tb_code cq ON cq.group_code = 'question_type' AND cq.code = t.question_type
             WHERE t.tpk_type = %s AND t.tpk_level = %s AND t.section = %s
               AND t.del_yn = 'N'
             ORDER BY t.question_no
            """,
            (tpk_type, tpk_level, section),
        )
        rows = cursor.fetchall()
        if not rows:
            return ""

        # "  1번: passage_type=1(짧은 대화), question_type=1(맞는 대답 고르기)" 형식으로 포맷
        lines = []
        for row in rows:
            pt_label = f"{row['passage_type']}({row['passage_type_name']})" if row["passage_type_name"] else str(row["passage_type"] or "")
            qt_label = f"{row['question_type']}({row['question_type_name']})" if row["question_type_name"] else str(row["question_type"] or "")
            lines.append(f"  {row['question_no']}번: passage_type={pt_label}, question_type={qt_label}")

        return "\n".join(lines)
    except Exception:
        return ""
    finally:
        conn.close()


def _get_prompt_by_section(exam_key: int, section_code: str) -> str:
    """
    영역 코드로 적절한 PDF 변환 프롬프트를 반환한다.
    tb_code에서 code_name을 조회한 뒤 매핑 테이블에서 프롬프트를 찾는다.
    매핑에 없는 영역은 기본 프롬프트(pdf_convert)를 사용한다.
    프롬프트 내 {{TEMPLATE_DATA}} 플레이스홀더를 tb_exam_template 데이터로 치환한다.

    Args:
        exam_key: 시험 PK
        section_code: 영역 코드 (예: "15", "16")

    Returns:
        프롬프트 텍스트
    """
    section_name = _get_section_name(section_code)
    prompt = _SECTION_PROMPT_MAP.get(section_name, _PDF_CONVERT_PROMPT)

    # tb_exam_template 데이터로 프롬프트 치환
    template_data = _get_template_data(exam_key, section_code)
    if template_data:
        prompt = prompt.replace("{{TEMPLATE_DATA}}", template_data)
    else:
        prompt = prompt.replace("{{TEMPLATE_DATA}}", "  (템플릿 데이터 없음 — AI가 지문/문제를 분석하여 직접 판단)")

    return prompt


def _get_pdf_file_info(pdf_key: int):
    """
    PDF 파일 정보를 조회하고 R2 키를 확인한다.

    Args:
        pdf_key: PDF 파일 PK

    Returns:
        (file_info, r2_key) 튜플 — r2_key는 R2 오브젝트 키(= file_path 컬럼 값)

    Raises:
        ValueError: 파일을 찾을 수 없는 경우
    """
    file_info = get_file(pdf_key)
    if not file_info:
        raise ValueError(f"PDF 파일을 찾을 수 없습니다 (pdf_key={pdf_key})")

    r2_key = file_info["file_path"]
    if not r2_storage.exists(r2_key):
        raise ValueError(f"PDF 파일이 R2에 존재하지 않습니다: {file_info['file_name']}")

    return file_info, r2_key


async def _convert_with_claude(file_info: dict, r2_key: str, exam_key: int = None, section: str = None) -> AsyncGenerator[str, None]:
    """
    Claude API 스트리밍으로 PDF를 JSON으로 변환한다.

    Args:
        file_info: 파일 메타데이터
        r2_key: R2 오브젝트 키
        exam_key: 시험 PK (tb_exam_template 조회용)
        section: 영역 (듣기/읽기) — 프롬프트 분기용

    Yields:
        SSE 형식 문자열
    """
    client = _get_async_client()

    # R2에서 PDF를 다운로드하여 base64 인코딩 (블로킹 I/O → 별도 스레드)
    pdf_data = await asyncio.to_thread(_read_pdf_as_base64, r2_key)

    # 영역 코드로 적절한 프롬프트 조회 (tb_exam_template 데이터 포함)
    prompt = _get_prompt_by_section(exam_key, section)

    # start 이벤트 전송 — 변환 시작 알림
    yield _format_sse("start", {
        "file_name": file_info["file_name"],
        "model": ANTHROPIC_MODEL,
    })

    # Claude API 스트리밍 호출
    try:
        async with client.messages.stream(
            model=ANTHROPIC_MODEL,
            max_tokens=64000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        ) as stream:
            # 텍스트 델타를 실시간 전송
            async for text in stream.text_stream:
                yield _format_sse("text_delta", {"text": text})

            # 최종 메시지에서 토큰 사용량 및 중단 사유 추출
            response = await stream.get_final_message()
            in_tok = response.usage.input_tokens
            out_tok = response.usage.output_tokens
            yield _format_sse("done", {
                "stop_reason": response.stop_reason,
                "token_usage": {"input_tokens": in_tok, "output_tokens": out_tok},
            })
            # API 사용 이력 저장
            try:
                save_usage("admin", "pdf_convert", "claude", ANTHROPIC_MODEL, in_tok, out_tok)
            except Exception:
                pass  # 이력 저장 실패가 변환 결과에 영향을 주지 않도록 무시

    except anthropic.RateLimitError:
        yield _format_sse("error", {"detail": "AI API 요청 한도 초과. 잠시 후 다시 시도해 주세요."})
    except anthropic.AuthenticationError:
        yield _format_sse("error", {"detail": "AI API 인증 실패. 관리자에게 문의하세요."})
    except anthropic.APIStatusError as e:
        if e.status_code == 529:
            yield _format_sse("error", {"detail": "AI 서버가 일시적으로 과부하 상태입니다. 잠시 후 다시 시도해 주세요."})
        else:
            yield _format_sse("error", {"detail": f"PDF 변환 실패: {e.message}"})
    except anthropic.APIError as e:
        yield _format_sse("error", {"detail": f"PDF 변환 실패: {e.message}"})


async def _convert_with_gemini(file_info: dict, r2_key: str, exam_key: int = None, section: str = None) -> AsyncGenerator[str, None]:
    """
    Google Gemini API 스트리밍으로 PDF를 JSON으로 변환한다.

    Args:
        file_info: 파일 메타데이터
        r2_key: R2 오브젝트 키
        exam_key: 시험 PK (tb_exam_template 조회용)
        section: 영역 (듣기/읽기) — 프롬프트 분기용

    Yields:
        SSE 형식 문자열
    """
    client = _get_google_client()

    # R2에서 PDF를 다운로드하여 바이트로 읽기 (블로킹 I/O → 별도 스레드)
    pdf_bytes = await asyncio.to_thread(_read_pdf_bytes, r2_key)

    # 영역 코드로 적절한 프롬프트 조회 (tb_exam_template 데이터 포함)
    prompt = _get_prompt_by_section(exam_key, section)

    # start 이벤트 전송
    yield _format_sse("start", {
        "file_name": file_info["file_name"],
        "model": GOOGLE_AI_MODEL,
    })

    try:
        # Gemini API 스트리밍 호출
        response_stream = client.models.generate_content_stream(
            model=GOOGLE_AI_MODEL,
            contents=[
                genai.types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                prompt,
            ],
        )

        # 텍스트 델타를 실시간 전송
        input_tokens = 0
        output_tokens = 0
        for chunk in response_stream:
            if chunk.text:
                yield _format_sse("text_delta", {"text": chunk.text})
            # 토큰 사용량 누적
            if chunk.usage_metadata:
                if chunk.usage_metadata.prompt_token_count:
                    input_tokens = chunk.usage_metadata.prompt_token_count
                if chunk.usage_metadata.candidates_token_count:
                    output_tokens = chunk.usage_metadata.candidates_token_count

        # 완료 이벤트 전송
        yield _format_sse("done", {
            "stop_reason": "end_turn",
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        })
        # API 사용 이력 저장
        try:
            save_usage("admin", "pdf_convert", "gemini", GOOGLE_AI_MODEL, input_tokens, output_tokens)
        except Exception:
            pass

    except Exception as e:
        yield _format_sse("error", {"detail": f"PDF 변환 실패: {str(e)}"})


async def convert_pdf_to_json_stream(
    exam_key: int, pdf_key: int, ai_provider: str = "claude", section: str = None
) -> AsyncGenerator[str, None]:
    """
    PDF 파일을 AI API 스트리밍으로 분석하여 SSE 이벤트를 생성한다.
    ai_provider에 따라 Claude 또는 Gemini를 사용한다.
    section에 따라 듣기/읽기 전용 프롬프트를 분기한다.

    Args:
        exam_key: 시험 PK
        pdf_key: PDF 파일 PK
        ai_provider: AI 제공자 ("claude" 또는 "gemini")
        section: 영역 (듣기/읽기) — 프롬프트 분기용

    Yields:
        SSE 형식 문자열 (event: type\ndata: {...}\n\n)

    Raises:
        ValueError: API 키 미설정, 파일 미존재, 지원하지 않는 제공자
    """
    # 공통: PDF 파일 정보 조회 및 R2 키 확인
    file_info, r2_key = _get_pdf_file_info(pdf_key)

    if ai_provider == "gemini":
        async for event in _convert_with_gemini(file_info, r2_key, exam_key, section):
            yield event
    elif ai_provider == "claude":
        async for event in _convert_with_claude(file_info, r2_key, exam_key, section):
            yield event
    else:
        raise ValueError(f"지원하지 않는 AI 제공자입니다: {ai_provider}")
