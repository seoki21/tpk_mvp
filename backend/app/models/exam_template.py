"""
시험 템플릿 요청/응답 모델 정의
tb_exam_template 테이블에 대한 Pydantic 스키마를 정의한다.
시험종류 + 토픽레벨 + 영역 + 문항번호 복합키로 관리한다.
"""
from typing import Optional
from pydantic import BaseModel, Field


class ExamTemplateCreate(BaseModel):
    """시험 템플릿 등록 요청 모델"""
    tpk_type: int = Field(..., description="시험종류 코드 (tb_code.tpk_type)")
    tpk_level: int = Field(..., description="토픽레벨 코드 (tb_code.tpk_level)")
    section: int = Field(..., description="영역 코드 (tb_code.section)")
    question_no: int = Field(..., description="문항번호")
    passage_type: Optional[int] = Field(None, description="지문유형 코드 (tb_code.passage_type)")
    question_type: Optional[int] = Field(None, description="문항유형 코드 (tb_code.question_type)")


class ExamTemplateUpdate(BaseModel):
    """시험 템플릿 수정 요청 모델 — PK 제외, 수정 가능한 필드만 포함"""
    passage_type: Optional[int] = Field(None, description="지문유형 코드")
    question_type: Optional[int] = Field(None, description="문항유형 코드")
