"""
그룹코드 Pydantic 스키마 정의
tb_group_code 테이블에 대한 요청/응답 모델을 정의한다.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GroupCodeSearch(BaseModel):
    """그룹코드 목록 검색 조건"""
    group_code: Optional[str] = Field(None, description="그룹코드 (부분 일치 검색)")
    group_name: Optional[str] = Field(None, description="그룹명 (부분 일치 검색)")
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(20, ge=1, le=100, description="페이지당 항목 수")


class GroupCodeCreate(BaseModel):
    """그룹코드 생성 요청 스키마"""
    group_code: str = Field(..., max_length=20, description="그룹코드")
    group_name: str = Field(..., max_length=100, description="그룹명")
    group_desc: Optional[str] = Field(None, max_length=500, description="그룹 설명")


class GroupCodeUpdate(BaseModel):
    """그룹코드 수정 요청 스키마"""
    group_name: Optional[str] = Field(None, max_length=100, description="그룹명")
    group_desc: Optional[str] = Field(None, max_length=500, description="그룹 설명")
    del_yn: Optional[str] = Field(None, max_length=1, description="삭제여부 (Y/N)")


class GroupCodeResponse(BaseModel):
    """그룹코드 응답 스키마 — tb_group_code 테이블의 모든 필드"""
    group_code: str
    group_name: Optional[str] = None
    group_desc: Optional[str] = None
    del_yn: Optional[str] = None
    ins_date: Optional[datetime] = None
    ins_user: Optional[str] = None
    upd_date: Optional[datetime] = None
    upd_user: Optional[str] = None
