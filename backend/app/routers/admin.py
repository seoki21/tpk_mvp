"""
관리자 관리 API 라우터
tb_admin 테이블에 대한 CRUD 엔드포인트를 정의한다.
SUPER 권한이 있는 관리자만 접근 가능하다.
URL 접두사: /api/v1/admins
"""
from fastapi import APIRouter, HTTPException, Query, Depends

from app.models.common import BaseResponse, PaginatedResponse
from app.models.admin import AdminCreate, AdminUpdate
from app.services import admin as admin_service
from app.utils.auth import require_super

router = APIRouter(
    prefix="/api/v1/admins",
    tags=["관리자 관리"],
)


@router.get("", response_model=PaginatedResponse)
def list_admins(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    _current_admin: dict = Depends(require_super),
):
    """관리자 목록을 페이지네이션하여 조회한다. (SUPER 권한 필요)"""
    try:
        rows, total = admin_service.list_admins(page=page, size=size)
        return PaginatedResponse(data=rows, total=total, page=page, size=size)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"관리자 목록 조회 실패: {str(e)}")


@router.post("", response_model=BaseResponse, status_code=201)
def create_admin(
    body: AdminCreate,
    current_admin: dict = Depends(require_super),
):
    """새로운 관리자를 생성한다. (SUPER 권한 필요)"""
    try:
        row = admin_service.create_admin(body.model_dump(), ins_user=current_admin["admin_id"])
        return BaseResponse(data=row, message="등록 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"관리자 등록 실패: {str(e)}")


@router.put("/{admin_id}", response_model=BaseResponse)
def update_admin(
    admin_id: str,
    body: AdminUpdate,
    current_admin: dict = Depends(require_super),
):
    """기존 관리자 정보를 수정한다. (SUPER 권한 필요)"""
    try:
        existing = admin_service.get_admin_safe(admin_id)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 관리자를 찾을 수 없습니다.")

        row = admin_service.update_admin(
            admin_id, body.model_dump(exclude_unset=True), upd_user=current_admin["admin_id"]
        )
        return BaseResponse(data=row, message="수정 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"관리자 수정 실패: {str(e)}")


@router.delete("/{admin_id}", response_model=BaseResponse)
def delete_admin(
    admin_id: str,
    current_admin: dict = Depends(require_super),
):
    """관리자를 논리 삭제(소프트 딜리트)한다. (SUPER 권한 필요)"""
    try:
        if admin_id == "admin":
            raise HTTPException(status_code=400, detail="최고 관리자(admin)는 삭제할 수 없습니다.")

        existing = admin_service.get_admin_safe(admin_id)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 관리자를 찾을 수 없습니다.")

        row = admin_service.delete_admin(admin_id, upd_user=current_admin["admin_id"])
        return BaseResponse(data=row, message="삭제 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"관리자 삭제 실패: {str(e)}")
