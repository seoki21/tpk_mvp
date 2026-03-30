"""
환경변수 및 설정 관리 모듈
.env 파일에서 환경변수를 로드하여 애플리케이션 설정을 관리한다.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 데이터베이스 접속 정보 — 개별 환경변수로부터 접속 문자열 조합
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tpk_db")
DB_USER = os.getenv("DB_USER", "tpk")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_SCHEMA = os.getenv("DB_SCHEMA", "public")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 파일 업로드 경로
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))

# JWT 인증 설정
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# 초기 관리자 계정 (DB 시딩용 — 실제 비밀번호는 DB에 bcrypt 해시로 저장됨)
SUPER_ADMIN_ID = "admin"
SUPER_ADMIN_PASSWORD = "dear#405"

# AI (Anthropic Claude) 설정
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# AI (Google Gemini) 설정
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")
GOOGLE_AI_MODEL = os.getenv("GOOGLE_AI_MODEL", "gemini-2.5-flash")

# AI 모델별 토큰 단가 (USD per 1M tokens) — 비용 추적용
AI_TOKEN_PRICING = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
}

# 외부 AI 관리 콘솔 URL
AI_CONSOLE_URLS = {
    "claude": "https://console.anthropic.com",
    "gemini": "https://aistudio.google.com",
}
