"""
시험 파일 Pydantic 스키마 정의
tb_exam_file 테이블에 대한 응답 모델을 정의한다.
"""
from pydantic import BaseModel, Field


class ExamFileResponse(BaseModel):
    """시험 파일 응답 스키마"""
    pdf_key: int = Field(..., description="파일 Key")
    exam_key: int = Field(..., description="시험 Key")
    file_name: str = Field(..., description="원본 파일명")
    file_path: str = Field(..., description="서버 저장 경로")
    file_size: int | None = Field(None, description="파일 크기 (bytes)")
    sort_order: int = Field(0, description="정렬 순서")
    del_yn: str = Field("N", description="삭제여부")
    ins_date: str | None = Field(None, description="등록일시")
    ins_user: str | None = Field(None, description="등록자")
