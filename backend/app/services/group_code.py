"""
그룹코드 서비스 모듈
tb_group_code 테이블에 대한 CRUD 비즈니스 로직을 처리한다.
psycopg (v3) raw SQL을 사용하며 ORM은 사용하지 않는다.
"""
from typing import Optional
from app.database import get_connection
from app.utils.pagination import get_limit_offset


def list_group_codes(
    group_code: Optional[str] = None,
    group_name: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    """
    그룹코드 목록을 페이지네이션하여 조회한다.
    검색 조건(group_code, group_name)은 LIKE 부분 일치로 동적 적용된다.

    Args:
        group_code: 그룹코드 검색어 (부분 일치)
        group_name: 그룹명 검색어 (부분 일치)
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

        if group_code:
            conditions.append("group_code LIKE %s")
            params.append(f"%{group_code}%")
        if group_name:
            conditions.append("group_name LIKE %s")
            params.append(f"%{group_name}%")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # 전체 건수 조회
        count_sql = f"SELECT COUNT(*) AS total FROM tb_group_code {where_clause}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # 페이지네이션 적용하여 목록 조회 (삭제여부 오름차순 → 그룹명 오름차순)
        limit, offset = get_limit_offset(page, size)
        list_sql = f"""
            SELECT group_code, group_name, group_desc, del_yn,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, ins_user,
                   TO_CHAR(upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, upd_user
              FROM tb_group_code
              {where_clause}
             ORDER BY del_yn ASC, group_name ASC
             LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params) + (limit, offset))
        rows = cursor.fetchall()

        return rows, total
    finally:
        conn.close()


def get_all_group_codes() -> list[dict]:
    """
    셀렉트박스용 전체 그룹코드 목록을 조회한다.
    삭제되지 않은(del_yn='N') 항목만 반환한다.

    Returns:
        group_code, group_name만 포함된 딕셔너리 리스트
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 삭제되지 않은 그룹코드만 조회 (셀렉트박스 용도)
        cursor.execute(
            """
            SELECT group_code, group_name
              FROM tb_group_code
             WHERE del_yn = 'N'
             ORDER BY group_code DESC
            """
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_group_code(group_code: str) -> Optional[dict]:
    """
    특정 그룹코드의 상세 정보를 조회한다.

    Args:
        group_code: 조회할 그룹코드

    Returns:
        그룹코드 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 그룹코드 PK로 단건 조회
        cursor.execute(
            """
            SELECT group_code, group_name, group_desc, del_yn,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, ins_user,
                   TO_CHAR(upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, upd_user
              FROM tb_group_code
             WHERE group_code = %s
            """,
            (group_code,),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def create_group_code(data: dict, user: str = "admin") -> dict:
    """
    새로운 그룹코드를 생성한다.

    Args:
        data: group_code, group_name, group_desc를 포함한 딕셔너리
        user: 등록자 (추후 JWT 인증 연동 시 현재 사용자로 대체)

    Returns:
        생성된 그룹코드 정보 딕셔너리
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 그룹코드 신규 등록 (del_yn 기본값 'N', 등록일시 현재시각)
        cursor.execute(
            """
            INSERT INTO tb_group_code (group_code, group_name, group_desc, del_yn, ins_date, ins_user)
            VALUES (%s, %s, %s, 'N', NOW(), %s)
            """,
            (data["group_code"], data["group_name"], data.get("group_desc"), user),
        )
        conn.commit()
        # INSERT 후 포맷된 날짜를 포함한 결과를 조회하여 반환
        return get_group_code(data["group_code"])
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_group_code(group_code: str, data: dict, user: str = "admin") -> Optional[dict]:
    """
    기존 그룹코드 정보를 수정한다.
    전달된 필드 중 None이 아닌 값만 업데이트한다.

    Args:
        group_code: 수정할 그룹코드
        data: 수정할 필드 딕셔너리
        user: 수정자 (추후 JWT 인증 연동 시 현재 사용자로 대체)

    Returns:
        수정된 그룹코드 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # None이 아닌 필드만 SET 절에 추가 (동적 UPDATE 구성)
        set_clauses = []
        params = []
        for field in ["group_name", "group_desc", "del_yn"]:
            if data.get(field) is not None:
                set_clauses.append(f"{field} = %s")
                params.append(data[field])

        if not set_clauses:
            # 수정할 항목이 없으면 기존 데이터 반환
            return get_group_code(group_code)

        # 수정일시, 수정자 자동 설정
        set_clauses.append("upd_date = NOW()")
        set_clauses.append("upd_user = %s")
        params.append(user)
        params.append(group_code)

        update_sql = f"""
            UPDATE tb_group_code
               SET {', '.join(set_clauses)}
             WHERE group_code = %s
        """
        cursor.execute(update_sql, tuple(params))
        conn.commit()
        # UPDATE 후 포맷된 날짜를 포함한 결과를 조회하여 반환
        return get_group_code(group_code)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_group_code(group_code: str, user: str = "admin") -> Optional[dict]:
    """
    그룹코드를 논리 삭제(소프트 딜리트)한다.
    del_yn을 'Y'로 변경하고 수정일시를 갱신한다.

    Args:
        group_code: 삭제할 그룹코드
        user: 수정자 (추후 JWT 인증 연동 시 현재 사용자로 대체)

    Returns:
        삭제 처리된 그룹코드 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 논리 삭제: del_yn='Y'로 변경
        cursor.execute(
            """
            UPDATE tb_group_code
               SET del_yn = 'Y', upd_date = NOW(), upd_user = %s
             WHERE group_code = %s
            """,
            (user, group_code),
        )
        conn.commit()
        # DELETE 후 포맷된 날짜를 포함한 결과를 조회하여 반환
        return get_group_code(group_code)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
