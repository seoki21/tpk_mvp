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
    UPLOAD_DIR,
)
from app.services.exam_file import get_file


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


def _read_pdf_as_base64(file_path: str) -> str:
    """PDF 파일을 읽어 base64 문자열로 반환한다. (동기 I/O)"""
    with open(file_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def _read_pdf_bytes(file_path: str) -> bytes:
    """PDF 파일을 읽어 바이트 데이터로 반환한다. (동기 I/O)"""
    with open(file_path, "rb") as f:
        return f.read()


def _format_sse(event: str, data: dict) -> str:
    """SSE 이벤트 문자열을 생성한다."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# PDF 분석 프롬프트 (외부 파일에서 로드)
from app.utils.prompt_loader import load_prompt
_PDF_CONVERT_PROMPT = load_prompt("pdf_convert")


def _get_pdf_file_info(pdf_key: int):
    """
    PDF 파일 정보를 조회하고 경로를 확인한다.

    Args:
        pdf_key: PDF 파일 PK

    Returns:
        (file_info, file_path) 튜플

    Raises:
        ValueError: 파일을 찾을 수 없는 경우
    """
    file_info = get_file(pdf_key)
    if not file_info:
        raise ValueError(f"PDF 파일을 찾을 수 없습니다 (pdf_key={pdf_key})")

    file_path = os.path.join(UPLOAD_DIR, file_info["file_path"])
    if not os.path.exists(file_path):
        raise ValueError(f"PDF 파일이 존재하지 않습니다: {file_info['file_name']}")

    return file_info, file_path


async def _convert_with_claude(file_info: dict, file_path: str) -> AsyncGenerator[str, None]:
    """
    Claude API 스트리밍으로 PDF를 JSON으로 변환한다.

    Args:
        file_info: 파일 메타데이터
        file_path: PDF 파일 경로

    Yields:
        SSE 형식 문자열
    """
    client = _get_async_client()

    # PDF 파일을 base64로 인코딩 (블로킹 I/O → 별도 스레드)
    pdf_data = await asyncio.to_thread(_read_pdf_as_base64, file_path)

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
                            "text": _PDF_CONVERT_PROMPT,
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
            yield _format_sse("done", {
                "stop_reason": response.stop_reason,
                "token_usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            })

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


async def _convert_with_gemini(file_info: dict, file_path: str) -> AsyncGenerator[str, None]:
    """
    Google Gemini API 스트리밍으로 PDF를 JSON으로 변환한다.

    Args:
        file_info: 파일 메타데이터
        file_path: PDF 파일 경로

    Yields:
        SSE 형식 문자열
    """
    client = _get_google_client()

    # PDF 파일을 바이트로 읽기 (블로킹 I/O → 별도 스레드)
    pdf_bytes = await asyncio.to_thread(_read_pdf_bytes, file_path)

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
                _PDF_CONVERT_PROMPT,
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

    except Exception as e:
        yield _format_sse("error", {"detail": f"PDF 변환 실패: {str(e)}"})


async def convert_pdf_to_json_stream(
    exam_key: int, pdf_key: int, ai_provider: str = "claude"
) -> AsyncGenerator[str, None]:
    """
    PDF 파일을 AI API 스트리밍으로 분석하여 SSE 이벤트를 생성한다.
    ai_provider에 따라 Claude 또는 Gemini를 사용한다.

    Args:
        exam_key: 시험 PK
        pdf_key: PDF 파일 PK
        ai_provider: AI 제공자 ("claude" 또는 "gemini")

    Yields:
        SSE 형식 문자열 (event: type\ndata: {...}\n\n)

    Raises:
        ValueError: API 키 미설정, 파일 미존재, 지원하지 않는 제공자
    """
    # 공통: PDF 파일 정보 조회 및 경로 확인
    file_info, file_path = _get_pdf_file_info(pdf_key)

    if ai_provider == "gemini":
        async for event in _convert_with_gemini(file_info, file_path):
            yield event
    elif ai_provider == "claude":
        async for event in _convert_with_claude(file_info, file_path):
            yield event
    else:
        raise ValueError(f"지원하지 않는 AI 제공자입니다: {ai_provider}")
