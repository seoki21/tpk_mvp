"""
시험 템플릿 API 라우터
tb_exam_template 테이블에 대한 CRUD 엔드포인트를 정의한다.
URL 접두사: /api/v1/exam-template
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.models.common import BaseResponse, PaginatedResponse
from app.models.exam_template import ExamTemplateCreate, ExamTemplateUpdate
from app.services import exam_template as exam_template_service
from app.utils.auth import get_current_admin

router = APIRouter(
    prefix="/api/v1/exam-template",
    tags=["시험 템플릿"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=PaginatedResponse)
def list_exam_templates(
    tpk_type: Optional[int] = Query(None, description="시험종류 코드 필터"),
    tpk_level: Optional[int] = Query(None, description="토픽레벨 코드 필터"),
    section: Optional[int] = Query(None, description="영역 코드 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
):
    """시험 템플릿 목록을 페이지네이션하여 조회한다."""
    try:
        rows, total = exam_template_service.list_exam_templates(
            tpk_type=tpk_type,
            tpk_level=tpk_level,
            section=section,
            page=page,
            size=size,
        )
        return PaginatedResponse(data=rows, total=total, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험 템플릿 목록 조회 실패: {str(e)}")


@router.get("/{tpk_type}/{tpk_level}/{section}/{question_no}", response_model=BaseResponse)
def get_exam_template(tpk_type: int, tpk_level: int, section: int, question_no: int):
    """복합 PK로 시험 템플릿 단건을 조회한다."""
    try:
        row = exam_template_service.get_exam_template(tpk_type, tpk_level, section, question_no)
        if not row:
            raise HTTPException(status_code=404, detail="해당 템플릿을 찾을 수 없습니다.")
        return BaseResponse(data=row, message="조회 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험 템플릿 조회 실패: {str(e)}")


@router.post("", response_model=BaseResponse, status_code=201)
def create_exam_template(body: ExamTemplateCreate, admin=Depends(get_current_admin)):
    """시험 템플릿을 신규 등록한다."""
    try:
        row = exam_template_service.create_exam_template(body.model_dump(), user=admin["admin_id"])
        return BaseResponse(data=row, message="등록 성공")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험 템플릿 등록 실패: {str(e)}")


@router.put("/{tpk_type}/{tpk_level}/{section}/{question_no}", response_model=BaseResponse)
def update_exam_template(
    tpk_type: int,
    tpk_level: int,
    section: int,
    question_no: int,
    body: ExamTemplateUpdate,
    admin=Depends(get_current_admin),
):
    """시험 템플릿의 지문유형/문항유형을 수정한다."""
    try:
        existing = exam_template_service.get_exam_template(tpk_type, tpk_level, section, question_no)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 템플릿을 찾을 수 없습니다.")
        row = exam_template_service.update_exam_template(
            tpk_type, tpk_level, section, question_no,
            body.model_dump(exclude_unset=True),
            user=admin["admin_id"],
        )
        return BaseResponse(data=row, message="수정 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험 템플릿 수정 실패: {str(e)}")


@router.delete("/{tpk_type}/{tpk_level}/{section}/{question_no}", response_model=BaseResponse)
def delete_exam_template(
    tpk_type: int,
    tpk_level: int,
    section: int,
    question_no: int,
    admin=Depends(get_current_admin),
):
    """시험 템플릿을 논리 삭제한다."""
    try:
        existing = exam_template_service.get_exam_template(tpk_type, tpk_level, section, question_no)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 템플릿을 찾을 수 없습니다.")
        row = exam_template_service.delete_exam_template(
            tpk_type, tpk_level, section, question_no,
            user=admin["admin_id"],
        )
        return BaseResponse(data=row, message="삭제 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험 템플릿 삭제 실패: {str(e)}")
