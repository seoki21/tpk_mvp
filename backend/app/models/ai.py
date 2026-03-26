"""
AI 피드백 Pydantic 스키마 정의
Claude API 기반 학습 피드백 요청/응답 모델을 정의한다.
"""
from typing import Optional
from pydantic import BaseModel, Field


class AIFeedbackRequest(BaseModel):
    """AI 피드백 생성 요청 스키마"""
    question_text: str = Field(..., description="문제 본문 텍스트")
    choices: Optional[list[str]] = Field(None, description="선택지 목록 (객관식인 경우)")
    correct_answer: str = Field(..., description="정답")
    user_answer: str = Field(..., description="사용자가 선택/입력한 답")
    question_type: Optional[str] = Field(None, description="문제 유형 (예: 읽기, 듣기, 쓰기)")
    topic_level: Optional[str] = Field(None, description="토픽 레벨 (예: TOPIK I, TOPIK II)")
    language: str = Field("ko", description="응답 언어 (ko/en/ja)")


class TokenUsage(BaseModel):
    """토큰 사용량 스키마"""
    input_tokens: int = Field(0, description="입력 토큰 수")
    output_tokens: int = Field(0, description="출력 토큰 수")


class AIFeedbackResult(BaseModel):
    """AI 피드백 결과 스키마 (BaseResponse.data에 포함)"""
    feedback: str = Field(..., description="AI가 생성한 피드백 텍스트")
    is_correct: bool = Field(..., description="사용자 답변의 정답 여부")
    model: str = Field(..., description="사용된 AI 모델명")
    token_usage: TokenUsage = Field(..., description="토큰 사용량")
