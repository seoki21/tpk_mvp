"""
기출문항 피드백 생성 API 라우터
Claude API 또는 Google Gemini API를 사용하여 question_json 기반으로 다국어 feedback_json을 생성한다.
URL 접두사: /api/v1/exam-feedback
"""
import anthropic
from fastapi import APIRouter, HTTPException, Depends
from app.models.common import BaseResponse
from app.models.exam_question import FeedbackGenerateRequest, FeedbackBatchRequest, FeedbackSaveRequest, QuestionSingleSaveRequest
from app.services import exam_feedback as exam_feedback_service
from app.utils.auth import get_current_admin

router = APIRouter(
    prefix="/api/v1/exam-feedback",
    tags=["기출문항 피드백 생성"],
    dependencies=[Depends(get_current_admin)],
)


@router.post("/generate-single", response_model=BaseResponse)
def generate_feedback_single(body: FeedbackGenerateRequest):
    """
    단일 문제의 question_json을 받아 다국어 피드백을 생성한다.
    DB 저장 없이 결과만 반환한다.
    ai_provider로 Claude 또는 Gemini를 선택할 수 있다.
    """
    try:
        feedback_json = exam_feedback_service.generate_feedback_single(
            body.question_json, body.ai_provider
        )
        return BaseResponse(data={"feedback_json": feedback_json}, message="피드백 생성 완료")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except anthropic.APIStatusError as e:
        if e.status_code == 529:
            raise HTTPException(status_code=503, detail="AI 서버가 일시적으로 과부하 상태입니다. 잠시 후 다시 시도해 주세요.")
        raise HTTPException(status_code=500, detail=f"피드백 생성 실패: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 생성 실패: {str(e)}")


@router.post("/{exam_key}/save-single", response_model=BaseResponse)
def save_feedback_single(exam_key: int, body: FeedbackSaveRequest):
    """
    단건 피드백 JSON을 DB에 저장한다.
    """
    try:
        exam_feedback_service.save_feedback_single(
            exam_key, body.question_no, body.feedback_json
        )
        return BaseResponse(message="피드백 저장 완료")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 저장 실패: {str(e)}")


@router.post("/{exam_key}/update-single", response_model=BaseResponse)
def update_question_single(exam_key: int, body: QuestionSingleSaveRequest):
    """
    단건 문제의 question_json과 feedback_json을 업데이트한다.
    기존 row가 없으면 에러를 반환한다 (INSERT 하지 않음).
    """
    try:
        updated = exam_feedback_service.update_question_single(
            exam_key, body.question_no, body.question_json, body.feedback_json
        )
        if not updated:
            raise HTTPException(
                status_code=400,
                detail="해당 문제가 존재하지 않습니다. '전체 저장' 후 수정만 가능합니다."
            )
        return BaseResponse(message="저장 완료")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장 실패: {str(e)}")


@router.post("/{exam_key}/generate", response_model=BaseResponse)
def generate_feedback(exam_key: int, body: FeedbackBatchRequest = None):
    """
    특정 시험의 모든 문제에 대해 다국어 피드백을 일괄 생성한다.
    각 문제의 question_json을 AI API로 분석하여 feedback_json을 생성 및 저장한다.
    ai_provider로 Claude 또는 Gemini를 선택할 수 있다.
    """
    ai_provider = body.ai_provider if body else "claude"
    try:
        result = exam_feedback_service.generate_feedback_batch(exam_key, ai_provider)
        return BaseResponse(data=result, message="피드백 생성 완료")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 생성 실패: {str(e)}")
