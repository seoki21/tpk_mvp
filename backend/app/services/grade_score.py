"""
토픽 등급 체계 서비스 모듈
tb_grade_score 테이블에 대한 CRUD 비즈니스 로직을 처리한다.
tb_code와 JOIN하여 시험종류/레벨 명칭을 함께 반환한다.
psycopg (v3) raw SQL을 사용하며 ORM은 사용하지 않는다.
"""
from typing import Optional
from app.database import get_connection


def list_grade_scores(tpk_type: Optional[int] = None) -> list[dict]:
    """
    등급 체계 전체 목록을 조회한다.
    tb_code와 LEFT JOIN하여 시험종류/레벨 명칭을 함께 반환한다.
    데이터 건수가 적으므로 페이징 없이 전체 반환한다.

    Args:
        tpk_type: 시험종류 코드 필터 (None이면 전체)

    Returns:
        등급 목록 리스트
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 동적 WHERE 조건 구성
        conditions = ["g.del_yn = 'N'"]
        params = []

        if tpk_type is not None:
            conditions.append("g.tpk_type = %s")
            params.append(tpk_type)

        where_clause = "WHERE " + " AND ".join(conditions)

        # tb_code와 LEFT JOIN하여 시험종류/레벨/등급 명칭 포함 조회
        # 시험종류 → 토픽레벨 → 등급 오름차순 정렬
        list_sql = f"""
            SELECT
                g.tpk_type,
                c_type.code_name        AS tpk_type_name,
                g.tpk_level,
                c_level.code_name       AS tpk_level_name,
                g.tpk_grade,
                c_grade.code_name       AS tpk_grade_name,
                g.min_score,
                g.max_score,
                g.total_score,
                g.del_yn,
                TO_CHAR(g.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date,
                g.ins_user,
                TO_CHAR(g.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date,
                g.upd_user
              FROM tb_grade_score g
              LEFT JOIN tb_code c_type  ON c_type.group_code  = 'topik_type'
                                       AND c_type.code        = g.tpk_type
              LEFT JOIN tb_code c_level ON c_level.group_code = 'tpk_level'
                                       AND c_level.code       = g.tpk_level
              LEFT JOIN tb_code c_grade ON c_grade.group_code = 'tpk_grade'
                                       AND c_grade.code       = g.tpk_grade
              {where_clause}
             ORDER BY g.tpk_type ASC, g.tpk_level ASC, g.tpk_grade ASC
        """
        cursor.execute(list_sql, tuple(params))
        return cursor.fetchall()
    finally:
        conn.close()


def get_grade_score(tpk_type: int, tpk_level: int, tpk_grade: int) -> Optional[dict]:
    """
    복합 PK로 등급 단건을 조회한다.

    Args:
        tpk_type: 시험종류 코드
        tpk_level: 토픽레벨 코드
        tpk_grade: 등급

    Returns:
        등급 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                g.tpk_type,
                c_type.code_name        AS tpk_type_name,
                g.tpk_level,
                c_level.code_name       AS tpk_level_name,
                g.tpk_grade,
                c_grade.code_name       AS tpk_grade_name,
                g.min_score,
                g.max_score,
                g.total_score,
                g.del_yn,
                TO_CHAR(g.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date,
                g.ins_user,
                TO_CHAR(g.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date,
                g.upd_user
              FROM tb_grade_score g
              LEFT JOIN tb_code c_type  ON c_type.group_code  = 'topik_type'
                                       AND c_type.code        = g.tpk_type
              LEFT JOIN tb_code c_level ON c_level.group_code = 'tpk_level'
                                       AND c_level.code       = g.tpk_level
              LEFT JOIN tb_code c_grade ON c_grade.group_code = 'tpk_grade'
                                       AND c_grade.code       = g.tpk_grade
             WHERE g.tpk_type = %s AND g.tpk_level = %s AND g.tpk_grade = %s
            """,
            (tpk_type, tpk_level, tpk_grade),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def create_grade_score(data: dict, user: str = "admin") -> dict:
    """
    등급 체계를 신규 등록한다.

    Args:
        data: tpk_type, tpk_level, tpk_grade, min_score, max_score, total_score
        user: 등록자

    Returns:
        등록된 등급 정보 딕셔너리
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 복합 PK 중복 확인
        cursor.execute(
            """
            SELECT 1 FROM tb_grade_score
             WHERE tpk_type = %s AND tpk_level = %s AND tpk_grade = %s
            """,
            (data["tpk_type"], data["tpk_level"], data["tpk_grade"]),
        )
        if cursor.fetchone():
            raise ValueError("이미 존재하는 등급입니다. (동일한 시험종류/레벨/등급)")

        # 등급 신규 등록
        cursor.execute(
            """
            INSERT INTO tb_grade_score
                (tpk_type, tpk_level, tpk_grade, min_score, max_score, total_score,
                 del_yn, ins_date, ins_user, upd_date, upd_user)
            VALUES (%s, %s, %s, %s, %s, %s, 'N', NOW(), %s, NOW(), %s)
            """,
            (
                data["tpk_type"],
                data["tpk_level"],
                data["tpk_grade"],
                data["min_score"],
                data["max_score"],
                data["total_score"],
                user,
                user,
            ),
        )
        conn.commit()
        # INSERT 후 재조회하여 반환
        return get_grade_score(data["tpk_type"], data["tpk_level"], data["tpk_grade"])
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_grade_score(
    tpk_type: int,
    tpk_level: int,
    tpk_grade: int,
    data: dict,
    user: str = "admin",
) -> Optional[dict]:
    """
    등급의 점수 범위/총점을 수정한다. PK 컬럼은 수정 불가.

    Args:
        tpk_type: 시험종류 코드
        tpk_level: 토픽레벨 코드
        tpk_grade: 등급
        data: 수정할 필드 (min_score, max_score, total_score)
        user: 수정자

    Returns:
        수정된 등급 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # None이 아닌 필드만 SET 절에 추가 (동적 UPDATE 구성)
        set_clauses = []
        params = []
        for field in ["min_score", "max_score", "total_score"]:
            if field in data and data[field] is not None:
                set_clauses.append(f"{field} = %s")
                params.append(data[field])

        if not set_clauses:
            return get_grade_score(tpk_type, tpk_level, tpk_grade)

        # 수정일시, 수정자 자동 설정
        set_clauses.append("upd_date = NOW()")
        set_clauses.append("upd_user = %s")
        params.append(user)
        params.extend([tpk_type, tpk_level, tpk_grade])

        update_sql = f"""
            UPDATE tb_grade_score
               SET {', '.join(set_clauses)}
             WHERE tpk_type = %s AND tpk_level = %s AND tpk_grade = %s
        """
        cursor.execute(update_sql, tuple(params))
        conn.commit()
        return get_grade_score(tpk_type, tpk_level, tpk_grade)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_grade_score(
    tpk_type: int,
    tpk_level: int,
    tpk_grade: int,
    user: str = "admin",
) -> Optional[dict]:
    """
    등급을 논리 삭제(del_yn='Y')한다.

    Args:
        tpk_type: 시험종류 코드
        tpk_level: 토픽레벨 코드
        tpk_grade: 등급
        user: 수정자

    Returns:
        삭제 처리된 등급 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tb_grade_score
               SET del_yn = 'Y', upd_date = NOW(), upd_user = %s
             WHERE tpk_type = %s AND tpk_level = %s AND tpk_grade = %s
            """,
            (user, tpk_type, tpk_level, tpk_grade),
        )
        conn.commit()
        return get_grade_score(tpk_type, tpk_level, tpk_grade)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
