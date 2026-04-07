"""
시험 이미지 crop API 라우터
PDF에서 이미지를 자동 검출/crop하고 파일명을 최종 형태로 변경하는 엔드포인트를 정의한다.
URL 접두사: /api/v1/exam-list/{exam_key}/images
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.models.common import BaseResponse
from app.services import exam_image as exam_image_service
from app.services import exam_list as exam_list_service
from app.utils.auth import get_current_admin

router = APIRouter(
    prefix="/api/v1/exam-list/{exam_key}/images",
    tags=["시험 이미지"],
)


class CropRequest(BaseModel):
    """이미지 crop 요청 스키마"""
    pdf_key: int


class RenameItem(BaseModel):
    """파일명 변경 항목"""
    old_filename: str
    new_filename: str


class BatchRenameRequest(BaseModel):
    """일괄 파일명 변경 요청 스키마"""
    rename_map: list[RenameItem]


def _check_exam_exists(exam_key: int):
    """시험 존재 여부를 확인하고 없으면 404를 발생시킨다."""
    exam = exam_list_service.get_exam(exam_key)
    if not exam:
        raise HTTPException(status_code=404, detail="해당 시험을 찾을 수 없습니다.")


@router.post("/crop", response_model=BaseResponse, dependencies=[Depends(get_current_admin)])
def crop_images(exam_key: int, body: CropRequest):
    """
    PDF에서 이미지 영역을 자동 검출하여 crop한다.
    crop된 이미지는 uploads/exam/{exam_key}/images/ 하위에 임시 파일명으로 저장된다.
    """
    try:
        _check_exam_exists(exam_key)
        results = exam_image_service.crop_images_from_pdf(exam_key, body.pdf_key)
        return BaseResponse(
            data=results,
            message=f"이미지 {len(results)}개 검출 완료",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 crop 실패: {str(e)}")


@router.post("/rename", response_model=BaseResponse, dependencies=[Depends(get_current_admin)])
def rename_images(exam_key: int, body: BatchRenameRequest):
    """
    crop된 임시 이미지 파일명을 최종 파일명으로 일괄 변경한다.
    프론트엔드에서 문항과 매핑 후 최종 파일명을 결정하여 호출한다.
    """
    try:
        _check_exam_exists(exam_key)
        results = exam_image_service.batch_rename_crop_images(
            exam_key,
            [item.model_dump() for item in body.rename_map],
        )
        return BaseResponse(
            data=results,
            message=f"파일명 {len(results)}개 변경 완료",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일명 변경 실패: {str(e)}")
