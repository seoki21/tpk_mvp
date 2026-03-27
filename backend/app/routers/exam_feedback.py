"""
기출문항 피드백 생성 API 라우터
Claude API를 사용하여 question_json 기반으로 다국어 feedback_json을 생성한다.
URL 접두사: /api/v1/exam-list/{exam_key}/feedback
"""
from fastapi import APIRouter, HTTPException
from app.models.common import BaseResponse
from app.services import exam_feedback as exam_feedback_service

router = APIRouter(
    prefix="/api/v1/exam-feedback",
    tags=["기출문항 피드백 생성"],
)


@router.post("/{exam_key}/generate", response_model=BaseResponse)
def generate_feedback(exam_key: int):
    """
    특정 시험의 모든 문제에 대해 다국어 피드백을 일괄 생성한다.
    각 문제의 question_json을 Claude API로 분석하여 feedback_json을 생성 및 저장한다.
    """
    try:
        result = exam_feedback_service.generate_feedback_batch(exam_key)
        return BaseResponse(data=result, message="피드백 생성 완료")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 생성 실패: {str(e)}")
