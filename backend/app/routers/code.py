"""
코드 API 라우터
tb_code 테이블에 대한 CRUD 엔드포인트를 정의한다.
URL 접두사: /api/v1/codes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.common import BaseResponse, PaginatedResponse
from app.models.code import CodeCreate, CodeUpdate
from app.services import code as code_service

router = APIRouter(
    prefix="/api/v1/codes",
    tags=["코드"],
)


@router.get("", response_model=PaginatedResponse)
def list_codes(
    group_code: Optional[str] = Query(None, description="그룹코드 검색어"),
    code_name: Optional[str] = Query(None, description="코드명 검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
):
    """코드 목록을 페이지네이션하여 조회한다 (그룹명 JOIN 포함)."""
    try:
        rows, total = code_service.list_codes(
            group_code=group_code,
            code_name=code_name,
            page=page,
            size=size,
        )
        return PaginatedResponse(data=rows, total=total, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코드 목록 조회 실패: {str(e)}")


@router.get("/{group_code}/{code}", response_model=BaseResponse)
def get_code(group_code: str, code: int):
    """특정 코드의 상세 정보를 조회한다."""
    try:
        row = code_service.get_code(group_code, code)
        if not row:
            raise HTTPException(status_code=404, detail="해당 코드를 찾을 수 없습니다.")
        return BaseResponse(data=row, message="조회 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코드 조회 실패: {str(e)}")


@router.post("", response_model=BaseResponse, status_code=201)
def create_code(body: CodeCreate):
    """새로운 코드를 생성한다."""
    try:
        # 중복 체크 (group_code + code 복합 PK)
        existing = code_service.get_code(body.group_code, body.code)
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 코드입니다.")

        row = code_service.create_code(body.model_dump())
        return BaseResponse(data=row, message="등록 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코드 등록 실패: {str(e)}")


@router.put("/{group_code}/{code}", response_model=BaseResponse)
def update_code(group_code: str, code: int, body: CodeUpdate):
    """기존 코드 정보를 수정한다."""
    try:
        existing = code_service.get_code(group_code, code)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 코드를 찾을 수 없습니다.")

        row = code_service.update_code(
            group_code, code, body.model_dump(exclude_unset=True)
        )
        return BaseResponse(data=row, message="수정 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코드 수정 실패: {str(e)}")


@router.delete("/{group_code}/{code}", response_model=BaseResponse)
def delete_code(group_code: str, code: int):
    """코드를 논리 삭제(소프트 딜리트)한다."""
    try:
        existing = code_service.get_code(group_code, code)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 코드를 찾을 수 없습니다.")

        row = code_service.delete_code(group_code, code)
        return BaseResponse(data=row, message="삭제 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코드 삭제 실패: {str(e)}")
