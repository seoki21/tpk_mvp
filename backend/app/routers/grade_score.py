"""
토픽 등급 체계 API 라우터
tb_grade_score 테이블에 대한 CRUD 엔드포인트를 정의한다.
URL 접두사: /api/v1/grade-score
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.models.common import BaseResponse
from app.models.grade_score import GradeScoreCreate, GradeScoreUpdate
from app.services import grade_score as grade_score_service
from app.utils.auth import get_current_admin

router = APIRouter(
    prefix="/api/v1/grade-score",
    tags=["등급 관리"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=BaseResponse)
def list_grade_scores(
    tpk_type: Optional[int] = Query(None, description="시험종류 코드 필터"),
):
    """등급 체계 전체 목록을 조회한다. 페이징 없이 전체 반환."""
    try:
        rows = grade_score_service.list_grade_scores(tpk_type=tpk_type)
        return BaseResponse(data=rows, message="조회 성공")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"등급 목록 조회 실패: {str(e)}")


@router.get("/{tpk_type}/{tpk_level}/{tpk_grade}", response_model=BaseResponse)
def get_grade_score(tpk_type: int, tpk_level: int, tpk_grade: int):
    """복합 PK로 등급 단건을 조회한다."""
    try:
        row = grade_score_service.get_grade_score(tpk_type, tpk_level, tpk_grade)
        if not row:
            raise HTTPException(status_code=404, detail="해당 등급을 찾을 수 없습니다.")
        return BaseResponse(data=row, message="조회 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"등급 조회 실패: {str(e)}")


@router.post("", response_model=BaseResponse, status_code=201)
def create_grade_score(body: GradeScoreCreate, admin=Depends(get_current_admin)):
    """등급 체계를 신규 등록한다."""
    try:
        row = grade_score_service.create_grade_score(body.model_dump(), user=admin["admin_id"])
        return BaseResponse(data=row, message="등록 성공")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"등급 등록 실패: {str(e)}")


@router.put("/{tpk_type}/{tpk_level}/{tpk_grade}", response_model=BaseResponse)
def update_grade_score(
    tpk_type: int,
    tpk_level: int,
    tpk_grade: int,
    body: GradeScoreUpdate,
    admin=Depends(get_current_admin),
):
    """등급의 점수 범위/총점을 수정한다."""
    try:
        existing = grade_score_service.get_grade_score(tpk_type, tpk_level, tpk_grade)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 등급을 찾을 수 없습니다.")
        row = grade_score_service.update_grade_score(
            tpk_type, tpk_level, tpk_grade,
            body.model_dump(exclude_unset=True),
            user=admin["admin_id"],
        )
        return BaseResponse(data=row, message="수정 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"등급 수정 실패: {str(e)}")


@router.delete("/{tpk_type}/{tpk_level}/{tpk_grade}", response_model=BaseResponse)
def delete_grade_score(
    tpk_type: int,
    tpk_level: int,
    tpk_grade: int,
    admin=Depends(get_current_admin),
):
    """등급을 논리 삭제한다."""
    try:
        existing = grade_score_service.get_grade_score(tpk_type, tpk_level, tpk_grade)
        if not existing:
            raise HTTPException(status_code=404, detail="해당 등급을 찾을 수 없습니다.")
        row = grade_score_service.delete_grade_score(
            tpk_type, tpk_level, tpk_grade,
            user=admin["admin_id"],
        )
        return BaseResponse(data=row, message="삭제 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"등급 삭제 실패: {str(e)}")
