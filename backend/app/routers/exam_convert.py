"""
기출문항 PDF → JSON 변환 API 라우터
Claude API를 활용한 PDF 분석 → JSON 변환 엔드포인트를 정의한다.
SSE(Server-Sent Events) 스트리밍으로 변환 결과를 실시간 전달한다.
URL 접두사: /api/v1/exam-list/{exam_key}/convert
"""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.exam_question import PdfConvertRequest
from app.services import exam_convert as convert_service

router = APIRouter(
    prefix="/api/v1/exam-list/{exam_key}/convert",
    tags=["기출문항 변환"],
)


@router.post("")
async def convert_pdf_to_json(exam_key: int, body: PdfConvertRequest):
    """
    PDF 파일을 Claude API로 분석하여 JSON으로 변환한다.
    SSE 스트리밍으로 변환 결과를 실시간 전달한다.

    이벤트 종류:
    - start: 변환 시작 (파일명, 모델 정보)
    - text_delta: JSON 텍스트 청크
    - done: 변환 완료 (토큰 사용량)
    - error: 에러 발생
    """

    async def event_generator():
        """
        서비스의 async generator를 감싸서 예외를 SSE error 이벤트로 변환한다.
        스트리밍 시작 후에는 HTTP 상태 코드를 변경할 수 없으므로
        모든 에러를 SSE 이벤트로 전달한다.
        """
        try:
            async for event in convert_service.convert_pdf_to_json_stream(
                exam_key=exam_key,
                pdf_key=body.pdf_key,
                ai_provider=body.ai_provider,
            ):
                yield event
        except ValueError as e:
            # 파일 미존재, API 키 미설정 등 사전 검증 에러
            yield f"event: error\ndata: {json.dumps({'detail': str(e)}, ensure_ascii=False)}\n\n"
        except Exception as e:
            # 예상치 못한 에러
            yield f"event: error\ndata: {json.dumps({'detail': f'서버 오류: {str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
