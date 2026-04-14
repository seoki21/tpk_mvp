"""
시험일정 요청/응답 모델 정의
tb_exam_schedule + tb_exam_location 테이블에 대한 Pydantic 스키마를 정의한다.
location은 schedule API에서 배열로 함께 처리한다.
"""
from typing import Optional
from pydantic import BaseModel, Field


class ExamLocationItem(BaseModel):
    """지역별 시험일 항목 모델 (schedule 요청 body에 배열로 포함)"""
    exam_region: int = Field(..., description="지역 코드 (tb_code.exam_region)")
    test_date: Optional[str] = Field(None, description="시험일 (YYYY-MM-DD)")


class ExamScheduleCreate(BaseModel):
    """시험일정 등록 요청 모델"""
    tpk_type: int = Field(..., description="시험종류 코드 (tb_code.topik_type)")
    round: int = Field(..., description="회차")
    locations: list[ExamLocationItem] = Field(default=[], description="지역별 시험일 목록")


class ExamScheduleUpdate(BaseModel):
    """시험일정 수정 요청 모델 — locations 전체 교체"""
    locations: list[ExamLocationItem] = Field(default=[], description="지역별 시험일 목록 (전체 교체)")
