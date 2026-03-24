"""
데이터베이스 연결 관리 모듈
psycopg2를 사용하여 PostgreSQL에 직접 연결한다. (ORM 미사용)
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import DATABASE_URL


def get_connection():
    """
    데이터베이스 커넥션을 반환한다.
    사용 후 반드시 close() 호출 필요.
    """
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
