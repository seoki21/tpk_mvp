"""
공통 응답 모델 정의
모든 API 응답에서 사용하는 표준 응답 스키마를 정의한다.
"""
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel):
    """
    기본 API 응답 모델
    단건 데이터 또는 처리 결과를 반환할 때 사용한다.
    """
    data: Any = None
    message: str = ""


class PaginatedResponse(BaseModel):
    """
    페이지네이션 API 응답 모델
    목록 조회 시 페이지 정보와 함께 데이터를 반환한다.
    """
    data: List[Any] = []
    total: int = 0
    page: int = 1
    size: int = 20
