"""
기출문제/지시문 API 라우터
tb_exam_question, tb_exam_instruction 테이블에 대한 CRUD 엔드포인트를 정의한다.
URL 접두사: /api/v1/exam-list/{exam_key}/questions
"""
from fastapi import APIRouter, HTTPException
from app.models.common import BaseResponse
from app.models.exam_question import ExamQuestionBulkSave
from app.services import exam_question as exam_question_service

router = APIRouter(
    prefix="/api/v1/exam-list/{exam_key}/questions",
    tags=["기출문제 관리"],
)


@router.get("", response_model=BaseResponse)
def get_questions_and_instructions(exam_key: int):
    """특정 시험의 문제와 지시문 목록을 조회한다."""
    try:
        result = exam_question_service.list_questions_and_instructions(exam_key)
        return BaseResponse(data=result, message="조회 성공")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기출문제 조회 실패: {str(e)}")


@router.post("/bulk-save", response_model=BaseResponse)
def bulk_save_questions(exam_key: int, body: ExamQuestionBulkSave):
    """문제와 지시문을 일괄 저장한다."""
    try:
        # Pydantic 모델을 dict로 변환
        questions = [q.model_dump() for q in body.questions]
        instructions = [ins.model_dump() for ins in body.instructions]

        result = exam_question_service.bulk_save(
            exam_key=exam_key,
            questions=questions,
            instructions=instructions,
        )
        return BaseResponse(data=result, message="저장 성공")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기출문제 저장 실패: {str(e)}")
