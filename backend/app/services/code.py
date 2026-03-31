"""
코드 서비스 모듈
tb_code 테이블에 대한 CRUD 비즈니스 로직을 처리한다.
tb_group_code와 JOIN하여 그룹명을 함께 조회한다.
psycopg (v3) raw SQL을 사용하며 ORM은 사용하지 않는다.
"""
from typing import Optional
from app.database import get_connection
from app.utils.pagination import get_limit_offset


def list_codes(
    group_code: Optional[str] = None,
    code_name: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    """
    코드 목록을 페이지네이션하여 조회한다.
    tb_group_code와 JOIN하여 그룹명을 함께 반환한다.

    Args:
        group_code: 그룹코드 검색어 (완전 일치)
        code_name: 코드명 검색어 (부분 일치)
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
            conditions.append("c.group_code = %s")
            params.append(group_code)
        if code_name:
            conditions.append("c.code_name LIKE %s")
            params.append(f"%{code_name}%")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # 전체 건수 조회
        count_sql = f"""
            SELECT COUNT(*) AS total
              FROM tb_code c
              {where_clause}
        """
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # 페이지네이션 적용하여 목록 조회
        # tb_group_code와 LEFT JOIN하여 그룹명 포함
        # 삭제여부 오름차순 → 정렬순서 오름차순
        limit, offset = get_limit_offset(page, size)
        list_sql = f"""
            SELECT c.group_code, c.code, c.code_name, c.code_desc,
                   c.sort_order, c.del_yn,
                   TO_CHAR(c.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, c.ins_user,
                   TO_CHAR(c.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, c.upd_user,
                   g.group_name
              FROM tb_code c
              LEFT JOIN tb_group_code g ON c.group_code = g.group_code
              {where_clause}
             ORDER BY c.del_yn ASC, c.group_code ASC, c.sort_order ASC
             LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params) + (limit, offset))
        rows = cursor.fetchall()

        return rows, total
    finally:
        conn.close()


def list_codes_by_group(group_code: str) -> list[dict]:
    """
    특정 그룹코드에 속하는 활성 코드 목록을 조회한다 (del_yn='N').
    셀렉트박스, 체크박스 등 UI에서 동적으로 코드 목록을 표시할 때 사용한다.

    Args:
        group_code: 그룹코드

    Returns:
        코드 목록 (code, code_name, code_desc, sort_order)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT code, code_name, code_desc, sort_order
              FROM tb_code
             WHERE group_code = %s AND del_yn = 'N'
             ORDER BY sort_order ASC
            """,
            (group_code,),
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_code(group_code: str, code: str) -> Optional[dict]:
    """
    특정 코드의 상세 정보를 조회한다.
    tb_group_code와 JOIN하여 그룹명을 함께 반환한다.

    Args:
        group_code: 코드그룹
        code: 코드

    Returns:
        코드 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 코드그룹 + 코드 복합 PK로 단건 조회 (그룹명 JOIN)
        cursor.execute(
            """
            SELECT c.group_code, c.code, c.code_name, c.code_desc,
                   c.sort_order, c.del_yn,
                   TO_CHAR(c.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, c.ins_user,
                   TO_CHAR(c.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, c.upd_user,
                   g.group_name
              FROM tb_code c
              LEFT JOIN tb_group_code g ON c.group_code = g.group_code
             WHERE c.group_code = %s AND c.code = %s
            """,
            (group_code, code),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def create_code(data: dict, user: str = "admin") -> dict:
    """
    새로운 코드를 생성한다.
    code 값이 없으면 해당 그룹코드 내 max(code)+1로 자동채번한다.
    (삭제된 코드 포함하여 max 계산 — PK 충돌 방지)

    Args:
        data: group_code, code(Optional), code_name, code_desc, sort_order를 포함한 딕셔너리
        user: 등록자 (추후 JWT 인증 연동 시 현재 사용자로 대체)

    Returns:
        생성된 코드 정보 딕셔너리
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # code 값이 없으면 해당 그룹코드 내 최대 code + 1로 자동채번
        code_value = data.get("code")
        if code_value is None:
            cursor.execute(
                """
                SELECT COALESCE(MAX(code), 0) + 1 AS next_code
                  FROM tb_code
                 WHERE group_code = %s
                """,
                (data["group_code"],),
            )
            code_value = cursor.fetchone()["next_code"]

        # 코드 신규 등록 (del_yn 기본값 'N', 등록일시 현재시각)
        cursor.execute(
            """
            INSERT INTO tb_code (group_code, code, code_name, code_desc, sort_order, del_yn, ins_date, ins_user)
            VALUES (%s, %s, %s, %s, %s, 'N', NOW(), %s)
            """,
            (
                data["group_code"],
                code_value,
                data["code_name"],
                data.get("code_desc"),
                data.get("sort_order", 0),
                user,
            ),
        )
        conn.commit()
        # INSERT 후 포맷된 날짜를 포함한 결과를 조회하여 반환
        return get_code(data["group_code"], code_value)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_code(group_code: str, code: str, data: dict, user: str = "admin") -> Optional[dict]:
    """
    기존 코드 정보를 수정한다.
    전달된 필드 중 None이 아닌 값만 업데이트한다.

    Args:
        group_code: 코드그룹
        code: 코드
        data: 수정할 필드 딕셔너리
        user: 수정자 (추후 JWT 인증 연동 시 현재 사용자로 대체)

    Returns:
        수정된 코드 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # None이 아닌 필드만 SET 절에 추가 (동적 UPDATE 구성)
        set_clauses = []
        params = []
        for field in ["code_name", "code_desc", "sort_order", "del_yn"]:
            if data.get(field) is not None:
                set_clauses.append(f"{field} = %s")
                params.append(data[field])

        if not set_clauses:
            # 수정할 항목이 없으면 기존 데이터 반환
            return get_code(group_code, code)

        # 수정일시, 수정자 자동 설정
        set_clauses.append("upd_date = NOW()")
        set_clauses.append("upd_user = %s")
        params.append(user)
        params.extend([group_code, code])

        update_sql = f"""
            UPDATE tb_code
               SET {', '.join(set_clauses)}
             WHERE group_code = %s AND code = %s
        """
        cursor.execute(update_sql, tuple(params))
        conn.commit()
        # UPDATE 후 포맷된 날짜를 포함한 결과를 조회하여 반환
        return get_code(group_code, code)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_code(group_code: str, code: str, user: str = "admin") -> Optional[dict]:
    """
    코드를 논리 삭제(소프트 딜리트)한다.
    del_yn을 'Y'로 변경하고 수정일시를 갱신한다.

    Args:
        group_code: 코드그룹
        code: 코드
        user: 수정자 (추후 JWT 인증 연동 시 현재 사용자로 대체)

    Returns:
        삭제 처리된 코드 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 논리 삭제: del_yn='Y'로 변경
        cursor.execute(
            """
            UPDATE tb_code
               SET del_yn = 'Y', upd_date = NOW(), upd_user = %s
             WHERE group_code = %s AND code = %s
            """,
            (user, group_code, code),
        )
        conn.commit()
        # DELETE 후 포맷된 날짜를 포함한 결과를 조회하여 반환
        return get_code(group_code, code)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
