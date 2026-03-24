"""
그룹코드 API 라우터
tb_group_code 테이블에 대한 CRUD 엔드포인트를 정의한다.
URL 접두사: /api/v1/group-codes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.common import BaseResponse, PaginatedResponse
from app.models.group_code import GroupCodeCreate, GroupCodeUpdate
from app.services import group_code as group_code_service

router = APIRouter(
    prefix="/api/v1/group-codes",
    tags=["그룹코드"],
)


@router.get("", response_model=PaginatedResponse)
def list_group_codes(
    group_code: Optional[str] = Query(None, description="그룹코드 검색어"),
    group_name: Optional[str] = Query(None, description="그룹명 검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
):
    """그룹코드 목록을 페이지네이션하여 조회한다."""
    try:
        rows, total = group_code_service.list_group_codes(
            group_code=group_code,
            group_name=group_name,
            page=page,
            size=size,
        )
        return PaginatedResponse(data=rows, total=total, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"그룹코드 목록 조회 실패: {str(e)}")


@router.get("/all", response_model=BaseResponse)
def get_all_group_codes():
    """셀렉트박스용 전체 그룹코드 목록을 조회한다 (삭제되지 않은 항목만)."""
    try:
        rows = group_code_service.get_all_group_codes()
        return BaseResponse(data=rows, message="조회 성공")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"그룹코드 전체 목록 조회 실패: {str(e)}")


@router.get("/{group_code}", response_model=BaseResponse)
def get_group_code(group_code: str):
    """특정 그룹코드의 상세 정보를 조회한다."""
    try:
        row = group_code_service.get_group_code(group_code)
        if not row:
            raise HTTPException(status_code=404, detail="해당 그룹코드를 찾을 수 없습니다.")
        return BaseResponse(data=row, message="조회 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"그룹코드 조회 실패: {str(e)}")


@router.post("", response_model=BaseResponse, status_code=201)
def create_group_code(body: GroupCodeCreate):
    """새로운 그룹코드를 생성한다."""
    try:
        # 중복 체크
        existing = group_code_service.get_group_code(body.group_code)
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 그룹코드입니다.")

        row = group_code_service.create_group_code(body.model_dump())
        return BaseResponse(data=row, message="등록 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"그룹코드 등록 실패: {str(e)}")


@router.put("/{group_code}", response_model=BaseResponse)
def update_group_code(group_code: str, body: GroupCodeUpdate):
    """기존 그룹코드 정보를 수정한다."""
    try:
        # 존재 여부 확인
        existing = group_code_service.get_group_code(group_code)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 그룹코드를 찾을 수 없습니다.")

        row = group_code_service.update_group_code(
            group_code, body.model_dump(exclude_unset=True)
        )
        return BaseResponse(data=row, message="수정 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"그룹코드 수정 실패: {str(e)}")


@router.delete("/{group_code}", response_model=BaseResponse)
def delete_group_code(group_code: str):
    """그룹코드를 논리 삭제(소프트 딜리트)한다."""
    try:
        existing = group_code_service.get_group_code(group_code)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 그룹코드를 찾을 수 없습니다.")

        row = group_code_service.delete_group_code(group_code)
        return BaseResponse(data=row, message="삭제 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"그룹코드 삭제 실패: {str(e)}")
