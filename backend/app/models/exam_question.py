"""
기출문제/지시문 Pydantic 스키마 정의
tb_exam_question, tb_exam_instruction 테이블에 대한 요청/응답 모델을 정의한다.
"""
from typing import Optional
from pydantic import BaseModel, Field


class ExamQuestionSave(BaseModel):
    """기출문제 저장 요청 스키마 (단건)"""
    question_no: int = Field(..., description="문제 번호")
    section: Optional[str] = Field(None, description="영역 (읽기, 쓰기 등)")
    question_type: Optional[str] = Field(None, description="문제 유형")
    struct_type: Optional[str] = Field(None, description="구조 유형")
    question_json: Optional[str] = Field(None, description="문제 JSON 데이터")
    feedback_json: Optional[str] = Field(None, description="피드백 JSON 데이터 (다국어 해설)")
    score: Optional[int] = Field(None, description="배점")
    difficulty: Optional[str] = Field(None, description="난이도")


class ExamInstructionSave(BaseModel):
    """지시문 저장 요청 스키마 (단건)"""
    ins_no: int = Field(..., description="지시문 번호")
    ins_json: Optional[str] = Field(None, description="지시문 JSON 데이터")


class ExamQuestionBulkSave(BaseModel):
    """기출문제 + 지시문 일괄 저장 요청 스키마"""
    questions: list[ExamQuestionSave] = Field(default=[], description="문제 목록")
    instructions: list[ExamInstructionSave] = Field(default=[], description="지시문 목록")


class PdfConvertRequest(BaseModel):
    """PDF → JSON 변환 요청 스키마"""
    pdf_key: int = Field(..., description="변환할 PDF 파일 키")
    ai_provider: str = Field("claude", description="AI 제공자 (claude 또는 gemini)")


class FeedbackGenerateRequest(BaseModel):
    """단건 피드백 생성 요청 스키마"""
    question_json: str = Field(..., description="문제 JSON 데이터")
    ai_provider: str = Field("claude", description="AI 제공자 (claude 또는 gemini)")


class FeedbackBatchRequest(BaseModel):
    """일괄 피드백 생성 요청 스키마"""
    ai_provider: str = Field("claude", description="AI 제공자 (claude 또는 gemini)")


class FeedbackSaveRequest(BaseModel):
    """단건 피드백 저장 요청 스키마"""
    question_no: int = Field(..., description="문제 번호")
    feedback_json: str = Field(..., description="피드백 JSON 데이터")


class QuestionSingleSaveRequest(BaseModel):
    """단건 문제+피드백 저장 요청 스키마"""
    question_no: int = Field(..., description="문제 번호")
    question_json: Optional[str] = Field(None, description="문제 JSON 데이터")
    feedback_json: Optional[str] = Field(None, description="피드백 JSON 데이터")
