"""
사용자 서비스 모듈
tb_user 테이블에 대한 조회 비즈니스 로직을 처리한다.
"""
from typing import Optional
from app.database import get_connection
from app.utils.pagination import get_limit_offset


def list_users(
    email: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    """
    사용자 목록을 페이지네이션하여 조회한다.

    Args:
        email: 이메일 검색어 (부분 일치)
        page: 페이지 번호
        size: 페이지당 항목 수

    Returns:
        (조회 결과 리스트, 전체 건수) 튜플
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 동적 WHERE 조건 구성
        conditions = []
        params = []

        if email:
            conditions.append("email LIKE %s")
            params.append(f"%{email}%")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # 전체 건수 조회
        count_sql = f"SELECT COUNT(*) AS total FROM tb_user {where_clause}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # 페이지네이션 적용하여 목록 조회
        limit, offset = get_limit_offset(page, size)
        list_sql = f"""
            SELECT user_key, email, provider_id, provider_type, del_yn,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, ins_user,
                   TO_CHAR(upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, upd_user
              FROM tb_user
              {where_clause}
             ORDER BY del_yn ASC, user_key ASC
             LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params) + (limit, offset))
        rows = cursor.fetchall()

        return rows, total
    finally:
        conn.close()
