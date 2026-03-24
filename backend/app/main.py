"""
TOPIK MVP API 서버 진입점
FastAPI 애플리케이션 인스턴스를 생성하고 라우터를 등록한다.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import group_code, code, exam_list, user

app = FastAPI(
    title="TOPIK MVP API",
    description="TOPIK 한국어능력시험 학습 플랫폼 API",
    version="0.1.0",
)

# CORS 설정 - 개발 환경에서 프론트엔드 접근 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 — 도메인별 API 엔드포인트
app.include_router(group_code.router)  # 그룹코드 관리
app.include_router(code.router)        # 코드 관리
app.include_router(exam_list.router)   # 시험문항 관리
app.include_router(user.router)        # 사용자 관리


@app.get("/health")
def health_check():
    """서버 상태 확인 엔드포인트"""
    return {"status": "ok"}
