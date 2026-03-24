"""
코드 Pydantic 스키마 정의
tb_code 테이블에 대한 요청/응답 모델을 정의한다.
실제 DB 컬럼: group_code(varchar), code(integer), code_name, code_desc, sort_order, del_yn 등
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CodeSearch(BaseModel):
    """코드 목록 검색 조건"""
    group_code: Optional[str] = Field(None, description="그룹코드 (부분 일치 검색)")
    code_name: Optional[str] = Field(None, description="코드명 (부분 일치 검색)")
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(20, ge=1, le=100, description="페이지당 항목 수")


class CodeCreate(BaseModel):
    """코드 생성 요청 스키마"""
    group_code: str = Field(..., max_length=20, description="그룹코드 (FK → tb_group_code)")
    code: int = Field(..., description="코드 (integer)")
    code_name: str = Field(..., max_length=100, description="코드명")
    code_desc: Optional[str] = Field(None, max_length=500, description="코드 설명")
    sort_order: Optional[int] = Field(0, description="정렬순서")


class CodeUpdate(BaseModel):
    """코드 수정 요청 스키마"""
    code_name: Optional[str] = Field(None, max_length=100, description="코드명")
    code_desc: Optional[str] = Field(None, max_length=500, description="코드 설명")
    sort_order: Optional[int] = Field(None, description="정렬순서")
    del_yn: Optional[str] = Field(None, max_length=1, description="삭제여부 (Y/N)")


class CodeResponse(BaseModel):
    """코드 응답 스키마 — tb_code 테이블의 모든 필드 + 그룹명"""
    group_code: str
    code: int
    code_name: Optional[str] = None
    code_desc: Optional[str] = None
    sort_order: Optional[int] = None
    del_yn: Optional[str] = None
    ins_date: Optional[datetime] = None
    ins_user: Optional[str] = None
    upd_date: Optional[datetime] = None
    upd_user: Optional[str] = None
    group_name: Optional[str] = None  # JOIN으로 가져오는 그룹명
