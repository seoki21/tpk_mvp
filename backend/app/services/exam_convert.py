"""
기출문항 PDF → JSON 변환 서비스 모듈
Anthropic Claude API의 PDF 분석 기능을 사용하여 기출문제 PDF를 JSON으로 변환한다.
anthropic Python SDK의 AsyncAnthropic 클라이언트와 스트리밍 API를 사용한다.
SSE(Server-Sent Events) 형식으로 변환 결과를 실시간 전달한다.
"""
import os
import json
import base64
import asyncio
from typing import Optional, AsyncGenerator
import anthropic
from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, UPLOAD_DIR
from app.services.exam_file import get_file


# Anthropic 비동기 클라이언트 싱글턴
_async_client: Optional[anthropic.AsyncAnthropic] = None


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


def _read_pdf_as_base64(file_path: str) -> str:
    """PDF 파일을 읽어 base64 문자열로 반환한다. (동기 I/O)"""
    with open(file_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def _format_sse(event: str, data: dict) -> str:
    """SSE 이벤트 문자열을 생성한다."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# PDF 분석 프롬프트 (CLAUDE.md에 정의된 프롬프트)
_PDF_CONVERT_PROMPT = """첨부의 기출문제를 분석하고 json으로 변환해줘
 - 읽기 유형만 진행
 - 결과가 100 line 이상되면 종료할 것

1. 아래 유형의 지시문
   * 유형
      * ※ [1~2] ( )에 들어갈 말로 가장 알맞은 것을 고르십시오. (각 2점)
      * 지시문 하단에 문단이 제시되어 있으면 paragraph key 값에 추가
   * json key 값
      * item_type : 'I'
      * full_sentence : ex. ※ [1~2] ( )에 들어갈 말로 가장 알맞은 것을 고르십시오. (각 2점)
      * paragraph : full_sentence 아래 문단 내용
      * no_list : 번호 목록, ex. [1, 2]
      * instruction : ex. ( )에 들어갈 말로 가장 알맞은 것을 고르십시오.
      * score : 점수, ex. 2

2. 문제 유형
   * json key 값
      * item_type : 'Q'
      * no : 문제 번호
      * score : 점수
      * section : 읽기, 쓰기, ...
      * type : 문제 유형
      * question_text : 문제
      * choices : 선택 옵션
         * 선택 옵션의 번호는 아래와 같이 동그라미 형식으로 해줄 것
         * "choices": ["① 식당", "② 은행", "③ 공원", "④ 서점"]
      * correct_answer : 정답 (동그라미 형식이 아닌 숫자 형식으로 출력)
      * feedback : 피드백
         * 선택 옵션 번호별 피드백
         * 번호별 정답여부와 피드백내용이 추가
         * 정답여부에서 정답이면 'T', 오답이면 'F'
         * 피드백내용은 한글로 정답이면 정답 피드백, 오답이면 오답피드백
         * 피드백내용은 간결하고 읽기 좋게 20~40자 내외로 정리하고 한글의 경우 존대어를 사용한다.
         * "feedback": ["①:정답여부_피드백내용", "②:정답여부_피드백내용", "③:정답여부_피드백내용", "④:정답여부_피드백내용"]

3. 기타 사항
   * json 순서는 번호 순서
   * json의 지시문 위치는 no_list의 번호 앞에 위치
   * 문항 중 json 파싱이 불가능한 문제는 위 예시가 아닌 notes 필드에 별도 정리
      * notes : 파싱이 불가능한 번호와 불가능한 이유를 별도로 정리
   * notes 필드는 번호와 불가능한 이유를 알기 쉽게 요약해서 정리
   * notes 필드는 맨 아래 별도 json 형식으로 정리

반드시 JSON 배열만 출력해줘. 마크다운 코드블록(```)으로 감싸지 말고, 순수 JSON만 응답해줘."""


async def convert_pdf_to_json_stream(exam_key: int, pdf_key: int) -> AsyncGenerator[str, None]:
    """
    PDF 파일을 Claude API 스트리밍으로 분석하여 SSE 이벤트를 생성한다.

    Args:
        exam_key: 시험 PK
        pdf_key: PDF 파일 PK

    Yields:
        SSE 형식 문자열 (event: type\ndata: {...}\n\n)

    Raises:
        ValueError: API 키 미설정 또는 파일을 찾을 수 없음
    """
    client = _get_async_client()

    # PDF 파일 정보 조회
    file_info = get_file(pdf_key)
    if not file_info:
        raise ValueError(f"PDF 파일을 찾을 수 없습니다 (pdf_key={pdf_key})")

    # PDF 파일 경로 구성 및 존재 확인
    file_path = os.path.join(UPLOAD_DIR, file_info["file_path"])
    if not os.path.exists(file_path):
        raise ValueError(f"PDF 파일이 존재하지 않습니다: {file_info['file_name']}")

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
    except anthropic.APIError as e:
        yield _format_sse("error", {"detail": f"PDF 변환 실패: {str(e)}"})
