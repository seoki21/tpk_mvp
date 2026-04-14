"""
토픽 등급 체계 요청/응답 모델 정의
tb_grade_score 테이블에 대한 Pydantic 스키마를 정의한다.
시험종류 + 토픽레벨 + 등급 복합키로 관리한다.
"""
from typing import Optional
from pydantic import BaseModel, Field


class GradeScoreCreate(BaseModel):
    """등급 등록 요청 모델"""
    tpk_type: int = Field(..., description="시험종류 코드 (tb_code.topik_type)")
    tpk_level: int = Field(..., description="토픽레벨 코드 (tb_code.tpk_level)")
    tpk_grade: int = Field(..., description="토픽 등급")
    min_score: int = Field(..., description="최소 점수")
    max_score: int = Field(..., description="최대 점수")
    total_score: int = Field(..., description="총점")


class GradeScoreUpdate(BaseModel):
    """등급 수정 요청 모델 — PK 제외, 수정 가능한 필드만 포함"""
    min_score: Optional[int] = Field(None, description="최소 점수")
    max_score: Optional[int] = Field(None, description="최대 점수")
    total_score: Optional[int] = Field(None, description="총점")
