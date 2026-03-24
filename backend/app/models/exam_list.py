"""
시험문항 Pydantic 스키마 정의
tb_exam_list 테이블에 대한 요청/응답 모델을 정의한다.
"""
from typing import Optional
from pydantic import BaseModel, Field


class ExamListCreate(BaseModel):
    """시험문항 생성 요청 스키마"""
    exam_year: str = Field(..., max_length=4, description="시험연도")
    exam_type: str = Field(..., max_length=20, description="시험유형 코드")
    round: Optional[int] = Field(None, description="회차")
    topic_level: Optional[str] = Field(None, max_length=10, description="토픽레벨 코드")
    section: str = Field(..., max_length=20, description="영역 코드")


class ExamListUpdate(BaseModel):
    """시험문항 수정 요청 스키마"""
    exam_year: Optional[str] = Field(None, max_length=4, description="시험연도")
    exam_type: Optional[str] = Field(None, max_length=20, description="시험유형 코드")
    round: Optional[int] = Field(None, description="회차")
    topic_level: Optional[str] = Field(None, max_length=10, description="토픽레벨 코드")
    section: Optional[str] = Field(None, max_length=20, description="영역 코드")
    del_yn: Optional[str] = Field(None, max_length=1, description="삭제여부 (Y/N)")
