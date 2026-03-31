"""
연습문제 생성 요청 Pydantic 스키마 정의
tb_practice_request 테이블에 대한 요청/응답 모델을 정의한다.
"""
from pydantic import BaseModel, Field


class PracticeRequestCreate(BaseModel):
    """연습문제 생성 요청 등록 스키마"""
    exam_type: str = Field(..., max_length=20, description="시험유형 코드")
    tpk_level: str = Field(..., max_length=10, description="토픽레벨 코드")
    section: str = Field(..., max_length=20, description="영역 코드")
    difficulty: str | None = Field(None, max_length=10, description="난이도 코드")
    question_count: int = Field(..., ge=1, description="문항수")
    gen_method: str = Field(..., max_length=10, description="생성방법 (realtime/batch)")
