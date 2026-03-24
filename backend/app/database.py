"""
데이터베이스 연결 관리 모듈
psycopg (v3)를 사용하여 PostgreSQL에 직접 연결한다. (ORM 미사용)
dict 형태로 결과를 반환하기 위해 row_factory=dict_row를 사용한다.
"""
import psycopg
from psycopg.rows import dict_row
from app.config import DATABASE_URL


def get_connection():
    """
    데이터베이스 커넥션을 반환한다.
    사용 후 반드시 close() 호출 필요.
    psycopg v3의 dict_row를 사용하여 결과를 dict 형태로 반환한다.
    """
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)
