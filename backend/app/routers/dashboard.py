"""
대시보드 통계 API 라우터
관리자 대시보드에 표시할 요약/상세 통계를 제공한다.
URL 접두사: /api/v1/dashboard
"""
from fastapi import APIRouter, HTTPException, Query, Depends

from app.models.common import BaseResponse
from app.services import api_usage as api_usage_service
from app.utils.auth import get_current_admin
from app.config import AI_CONSOLE_URLS

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["대시보드"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/summary", response_model=BaseResponse)
def get_summary():
    """상단 요약 카드 데이터 (총 사용자, 시험, 문항, 금월 API 호출)"""
    try:
        data = api_usage_service.get_summary_stats()
        return BaseResponse(data=data, message="조회 성공")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 통계 조회 실패: {str(e)}")


@router.get("/exam-stats", response_model=BaseResponse)
def get_exam_stats():
    """시험/문제 현황 (레벨별, 영역별 분포, 피드백 생성률)"""
    try:
        data = api_usage_service.get_exam_stats()
        return BaseResponse(data=data, message="조회 성공")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시험 통계 조회 실패: {str(e)}")


@router.get("/api-usage", response_model=BaseResponse)
def get_api_usage(
    period: str = Query("daily", description="기간 ('daily', 'weekly', 'monthly')"),
):
    """API 토큰 사용 이력 (차트 데이터 + 프로바이더 합계 + 최근 호출 목록)"""
    try:
        data = api_usage_service.get_api_usage_stats(period=period)
        # 외부 관리 콘솔 링크 추가
        data["console_links"] = AI_CONSOLE_URLS
        return BaseResponse(data=data, message="조회 성공")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API 사용량 조회 실패: {str(e)}")
