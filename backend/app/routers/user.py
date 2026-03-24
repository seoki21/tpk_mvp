"""
사용자 API 라우터
tb_user 테이블에 대한 조회 엔드포인트를 정의한다.
URL 접두사: /api/v1/users
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.common import PaginatedResponse
from app.services import user as user_service

router = APIRouter(
    prefix="/api/v1/users",
    tags=["사용자"],
)


@router.get("", response_model=PaginatedResponse)
def list_users(
    email: Optional[str] = Query(None, description="이메일 검색어 (부분 일치)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
):
    """사용자 목록을 페이지네이션하여 조회한다."""
    try:
        rows, total = user_service.list_users(
            email=email,
            page=page,
            size=size,
        )
        return PaginatedResponse(data=rows, total=total, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 목록 조회 실패: {str(e)}")
