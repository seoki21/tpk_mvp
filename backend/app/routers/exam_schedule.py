"""
시험일정 API 라우터
tb_exam_schedule + tb_exam_location 테이블에 대한 CRUD 엔드포인트를 정의한다.
URL 접두사: /api/v1/exam-schedule
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.models.common import BaseResponse, PaginatedResponse
from app.models.exam_schedule import ExamScheduleCreate, ExamScheduleUpdate
from app.services import exam_schedule as exam_schedule_service
from app.utils.auth import get_current_admin

router = APIRouter(
    prefix="/api/v1/exam-schedule",
    tags=["시험일정 관리"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=PaginatedResponse)
def list_exam_schedules(
    tpk_type: Optional[int] = Query(None, description="시험종류 코드 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
):
    """시험일정 목록을 페이지네이션하여 조회한다."""
    try:
        rows, total = exam_schedule_service.list_exam_schedules(
            tpk_type=tpk_type, page=page, size=size
        )
        return PaginatedResponse(data=rows, total=total, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험일정 목록 조회 실패: {str(e)}")


@router.get("/{exam_key}", response_model=BaseResponse)
def get_exam_schedule(exam_key: int):
    """시험일정 단건을 locations 포함하여 조회한다."""
    try:
        row = exam_schedule_service.get_exam_schedule(exam_key)
        if not row:
            raise HTTPException(status_code=404, detail="해당 시험일정을 찾을 수 없습니다.")
        return BaseResponse(data=row, message="조회 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험일정 조회 실패: {str(e)}")


@router.post("", response_model=BaseResponse, status_code=201)
def create_exam_schedule(body: ExamScheduleCreate, admin=Depends(get_current_admin)):
    """시험일정을 신규 등록한다. locations도 함께 등록된다."""
    try:
        row = exam_schedule_service.create_exam_schedule(
            body.model_dump(), user=admin["admin_id"]
        )
        return BaseResponse(data=row, message="등록 성공")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험일정 등록 실패: {str(e)}")


@router.put("/{exam_key}", response_model=BaseResponse)
def update_exam_schedule(
    exam_key: int,
    body: ExamScheduleUpdate,
    admin=Depends(get_current_admin),
):
    """시험일정의 locations를 전체 교체한다."""
    try:
        existing = exam_schedule_service.get_exam_schedule(exam_key)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 시험일정을 찾을 수 없습니다.")
        row = exam_schedule_service.update_exam_schedule(
            exam_key, body.model_dump(), user=admin["admin_id"]
        )
        return BaseResponse(data=row, message="수정 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험일정 수정 실패: {str(e)}")


@router.delete("/{exam_key}", response_model=BaseResponse)
def delete_exam_schedule(exam_key: int, admin=Depends(get_current_admin)):
    """시험일정을 논리 삭제한다. locations도 함께 삭제된다."""
    try:
        existing = exam_schedule_service.get_exam_schedule(exam_key)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 시험일정을 찾을 수 없습니다.")
        row = exam_schedule_service.delete_exam_schedule(exam_key, user=admin["admin_id"])
        return BaseResponse(data=row, message="삭제 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험일정 삭제 실패: {str(e)}")
