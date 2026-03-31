"""
연습문제 생성 요청 API 라우터
tb_practice_request 테이블에 대한 CRUD 엔드포인트를 정의한다.
URL 접두사: /api/v1/practice-request
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.common import BaseResponse, PaginatedResponse
from app.models.practice_request import PracticeRequestCreate
from app.services import practice_request as practice_request_service
from app.utils.auth import get_current_admin

router = APIRouter(
    prefix="/api/v1/practice-request",
    tags=["연습문제 생성 요청"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=PaginatedResponse)
def list_requests(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 행 수"),
    exam_type: Optional[str] = Query(None, description="시험유형 코드"),
    tpk_level: Optional[str] = Query(None, description="토픽레벨 코드"),
    section: Optional[str] = Query(None, description="영역 코드"),
    gen_method: Optional[str] = Query(None, description="생성방법"),
    status: Optional[str] = Query(None, description="상태 코드"),
):
    """연습문제 생성 요청 목록을 조회한다."""
    try:
        result = practice_request_service.list_requests(
            page=page,
            size=size,
            exam_type=exam_type,
            tpk_level=tpk_level,
            section=section,
            gen_method=gen_method,
            status=status,
        )
        return PaginatedResponse(data=result["list"], total=result["total"], page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.post("", response_model=BaseResponse)
def create_request(body: PracticeRequestCreate, admin=Depends(get_current_admin)):
    """연습문제 생성 요청을 등록한다."""
    try:
        result = practice_request_service.create_request(
            data=body.model_dump(),
            user=admin.get("admin_id", "admin"),
        )
        return BaseResponse(data=result, message="등록 성공")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"등록 실패: {str(e)}")


@router.put("/{request_key}", response_model=BaseResponse)
def update_request(request_key: int, body: PracticeRequestCreate, admin=Depends(get_current_admin)):
    """연습문제 생성 요청을 수정한다."""
    try:
        result = practice_request_service.update_request(
            request_key=request_key,
            data=body.model_dump(),
            user=admin.get("admin_id", "admin"),
        )
        return BaseResponse(data=result, message="수정 성공")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수정 실패: {str(e)}")


@router.delete("/{request_key}", response_model=BaseResponse)
def delete_request(request_key: int, admin=Depends(get_current_admin)):
    """연습문제 생성 요청을 삭제한다."""
    try:
        practice_request_service.delete_request(
            request_key=request_key,
            user=admin.get("admin_id", "admin"),
        )
        return BaseResponse(message="삭제 성공")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")
