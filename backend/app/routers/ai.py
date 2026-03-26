"""
AI 피드백 API 라우터
Claude API를 활용한 TOPIK 학습 피드백 엔드포인트를 정의한다.
URL 접두사: /api/v1/ai
"""
import anthropic
from fastapi import APIRouter, HTTPException
from app.models.common import BaseResponse
from app.models.ai import AIFeedbackRequest
from app.services import ai as ai_service

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI 피드백"],
)


@router.post("/feedback", response_model=BaseResponse)
def generate_feedback(body: AIFeedbackRequest):
    """TOPIK 문제에 대한 AI 피드백을 생성한다."""
    try:
        result = ai_service.generate_feedback(
            question_text=body.question_text,
            choices=body.choices,
            correct_answer=body.correct_answer,
            user_answer=body.user_answer,
            question_type=body.question_type,
            topic_level=body.topic_level,
            language=body.language,
        )
        return BaseResponse(data=result, message="피드백 생성 성공")
    except ValueError as e:
        # API 키 미설정 등 설정 오류
        raise HTTPException(status_code=500, detail=f"AI 서비스 설정 오류: {str(e)}")
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="AI API 요청 한도 초과. 잠시 후 다시 시도해 주세요.")
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=500, detail="AI API 인증 실패. 관리자에게 문의하세요.")
    except anthropic.APIError as e:
        raise HTTPException(status_code=500, detail=f"AI 피드백 생성 실패: {str(e)}")
