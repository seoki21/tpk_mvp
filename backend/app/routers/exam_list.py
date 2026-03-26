"""
시험문항 API 라우터
tb_exam_list 테이블에 대한 CRUD 엔드포인트를 정의한다.
URL 접두사: /api/v1/exam-list
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.common import BaseResponse, PaginatedResponse
from app.models.exam_list import ExamListCreate, ExamListUpdate
from app.services import exam_list as exam_list_service

router = APIRouter(
    prefix="/api/v1/exam-list",
    tags=["시험문항"],
)


@router.get("", response_model=PaginatedResponse)
def list_exam_list(
    exam_type: Optional[str] = Query(None, description="시험유형 코드 (정확 일치)"),
    tpk_level: Optional[str] = Query(None, description="토픽레벨 코드 (정확 일치)"),
    round: Optional[int] = Query(None, description="회차 (정수 정확 일치)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
):
    """시험문항 목록을 페이지네이션하여 조회한다."""
    try:
        rows, total = exam_list_service.list_exam_list(
            exam_type=exam_type,
            tpk_level=tpk_level,
            round=round,
            page=page,
            size=size,
        )
        return PaginatedResponse(data=rows, total=total, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험문항 목록 조회 실패: {str(e)}")


@router.get("/{exam_key}", response_model=BaseResponse)
def get_exam(exam_key: int):
    """특정 시험문항의 상세 정보를 조회한다."""
    try:
        row = exam_list_service.get_exam(exam_key)
        if not row:
            raise HTTPException(status_code=404, detail="해당 시험문항을 찾을 수 없습니다.")
        return BaseResponse(data=row, message="조회 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험문항 조회 실패: {str(e)}")


@router.post("", response_model=BaseResponse, status_code=201)
def create_exam(body: ExamListCreate):
    """새로운 시험문항을 생성한다."""
    try:
        row = exam_list_service.create_exam(body.model_dump())
        return BaseResponse(data=row, message="등록 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험문항 등록 실패: {str(e)}")


@router.put("/{exam_key}", response_model=BaseResponse)
def update_exam(exam_key: int, body: ExamListUpdate):
    """기존 시험문항 정보를 수정한다."""
    try:
        # 존재 여부 확인
        existing = exam_list_service.get_exam(exam_key)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 시험문항을 찾을 수 없습니다.")

        row = exam_list_service.update_exam(
            exam_key, body.model_dump(exclude_unset=True)
        )
        return BaseResponse(data=row, message="수정 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험문항 수정 실패: {str(e)}")


@router.delete("/{exam_key}", response_model=BaseResponse)
def delete_exam(exam_key: int):
    """시험문항을 논리 삭제(소프트 딜리트)한다."""
    try:
        existing = exam_list_service.get_exam(exam_key)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 시험문항을 찾을 수 없습니다.")

        row = exam_list_service.delete_exam(exam_key)
        return BaseResponse(data=row, message="삭제 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험문항 삭제 실패: {str(e)}")
