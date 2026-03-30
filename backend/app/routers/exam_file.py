"""
시험 파일 API 라우터
tb_exam_file 테이블에 대한 업로드/조회/삭제/다운로드 엔드포인트를 정의한다.
URL 접두사: /api/v1/exam-list/{exam_key}/files
"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from typing import List, Optional

from app.models.common import BaseResponse
from app.services import exam_file as exam_file_service
from app.services import exam_list as exam_list_service
from app.config import UPLOAD_DIR
from app.utils.auth import get_current_admin

router = APIRouter(
    prefix="/api/v1/exam-list/{exam_key}/files",
    tags=["시험 파일"],
)


def _check_exam_exists(exam_key: int):
    """시험 존재 여부를 확인하고 없으면 404를 발생시킨다."""
    exam = exam_list_service.get_exam(exam_key)
    if not exam:
        raise HTTPException(status_code=404, detail="해당 시험을 찾을 수 없습니다.")


@router.get("", response_model=BaseResponse, dependencies=[Depends(get_current_admin)])
def list_files(exam_key: int):
    """특정 시험의 파일 목록을 조회한다."""
    try:
        _check_exam_exists(exam_key)
        rows = exam_file_service.list_files(exam_key)
        return BaseResponse(data=rows, message="조회 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 목록 조회 실패: {str(e)}")


@router.post("", response_model=BaseResponse, status_code=201, dependencies=[Depends(get_current_admin)])
async def upload_files(
    exam_key: int,
    files: List[UploadFile] = File(...),
    file_type: Optional[str] = Form("pdf"),
):
    """
    파일을 업로드한다. (여러 파일 동시 업로드 가능)
    - file_type='pdf': PDF 파일만 허용
    - file_type='json': JSON 파일만 허용
    - file_type='mp3': MP3 파일만 허용
    """
    try:
        _check_exam_exists(exam_key)

        # file_type에 따른 파일 유효성 검증 (json은 확장자 체크 없음)
        for file in files:
            fname = file.filename.lower()
            if file_type == "json":
                pass  # JSON 영역은 확장자 체크하지 않음
            elif file_type == "mp3":
                if not fname.endswith(".mp3"):
                    raise HTTPException(
                        status_code=400,
                        detail="듣기 파일 형식이 MP3가 아닌 것 같으니 확인 바랍니다."
                    )
            else:
                # 기본: PDF 검증
                if not fname.endswith(".pdf"):
                    raise HTTPException(
                        status_code=400,
                        detail="기출문제 파일 형식이 PDF가 아닌 것 같으니 확인 바랍니다."
                    )
                if file.content_type and file.content_type != "application/pdf":
                    raise HTTPException(
                        status_code=400,
                        detail="기출문제 파일 형식이 PDF가 아닌 것 같으니 확인 바랍니다."
                    )

        rows = await exam_file_service.upload_files(exam_key, files, file_type=file_type or "pdf")
        return BaseResponse(data=rows, message="업로드 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")


@router.delete("/{pdf_key}", response_model=BaseResponse, dependencies=[Depends(get_current_admin)])
def delete_file(exam_key: int, pdf_key: int):
    """파일을 삭제한다. (소프트 삭제 + 파일 삭제)"""
    try:
        _check_exam_exists(exam_key)

        result = exam_file_service.delete_file(pdf_key)
        if not result:
            raise HTTPException(status_code=404, detail="해당 파일을 찾을 수 없습니다.")

        return BaseResponse(data=result, message="삭제 성공")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 삭제 실패: {str(e)}")


@router.get("/{pdf_key}/download")
def download_file(exam_key: int, pdf_key: int, inline: bool = False):
    """
    파일을 다운로드한다.
    - inline=True: 브라우저에서 인라인으로 표시 (PDF 뷰어용)
    - inline=False(기본): 다운로드 첨부 파일로 응답
    """
    try:
        _check_exam_exists(exam_key)

        file_info = exam_file_service.get_file(pdf_key)
        if not file_info:
            raise HTTPException(status_code=404, detail="해당 파일을 찾을 수 없습니다.")

        # 파일 경로 구성
        full_path = os.path.join(UPLOAD_DIR, file_info["file_path"])
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

        # 파일 유형에 따른 media_type 결정
        file_type_val = file_info.get("file_type")
        if file_type_val == "json":
            media = "application/json"
        elif file_type_val == "mp3":
            media = "audio/mpeg"
        else:
            media = "application/pdf"

        # 원본 파일명으로 응답 (inline 여부에 따라 Content-Disposition 결정)
        return FileResponse(
            path=full_path,
            filename=file_info["file_name"],
            media_type=media,
            content_disposition_type="inline" if inline else "attachment",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 다운로드 실패: {str(e)}")
