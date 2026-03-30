"""
관리자 Pydantic 스키마 정의
tb_admin 테이블에 대한 요청/응답 모델을 정의한다.
"""
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    admin_id: str = Field(..., max_length=50, description="관리자 ID")
    password: str = Field(..., description="비밀번호")


class LoginResponse(BaseModel):
    """로그인 응답 스키마"""
    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    admin_id: str = Field(..., description="관리자 ID")
    roles: list[str] = Field(default=[], description="권한 목록")


class AdminCreate(BaseModel):
    """관리자 생성 요청 스키마"""
    admin_id: str = Field(..., max_length=50, description="관리자 ID")
    password: str = Field(..., min_length=4, description="비밀번호")
    admin_desc: Optional[str] = Field(None, max_length=200, description="설명")
    role_code: str = Field(default="MANAGER", max_length=20, description="권한 코드")


class AdminUpdate(BaseModel):
    """관리자 수정 요청 스키마"""
    password: Optional[str] = Field(None, min_length=4, description="비밀번호 (변경 시)")
    admin_desc: Optional[str] = Field(None, max_length=200, description="설명")
    del_yn: Optional[str] = Field(None, max_length=1, description="삭제여부 (Y/N)")
