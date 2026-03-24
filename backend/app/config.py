"""
환경변수 및 설정 관리 모듈
.env 파일에서 환경변수를 로드하여 애플리케이션 설정을 관리한다.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 데이터베이스 접속 정보
DATABASE_URL = os.getenv("DATABASE_URL")

# JWT 인증 설정
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
