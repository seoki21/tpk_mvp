"""
사용자 Pydantic 스키마 정의
tb_user 테이블에 대한 응답 모델을 정의한다. (조회 전용)
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    user_key: int
    email: str
    provider_id: Optional[str] = None
    provider_type: Optional[str] = None
    del_yn: Optional[str] = None
    ins_date: Optional[str] = None
    ins_user: Optional[str] = None
    upd_date: Optional[str] = None
    upd_user: Optional[str] = None
