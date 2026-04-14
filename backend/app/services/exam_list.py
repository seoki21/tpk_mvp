"""
시험문항 서비스 모듈
tb_exam_list 테이블에 대한 CRUD 비즈니스 로직을 처리한다.
psycopg (v3) raw SQL을 사용하며 ORM은 사용하지 않는다.
"""
from typing import Optional
from app.database import get_connection
from app.utils.pagination import get_limit_offset


# 시험문항 목록/상세 조회에서 사용하는 공통 SELECT 절 (코드명 LEFT JOIN 포함)
_BASE_SELECT = """
    SELECT e.exam_key, e.exam_year, e.exam_type, e.tpk_type, e.round, e.tpk_level, e.section,
           e.del_yn,
           TO_CHAR(e.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, e.ins_user,
           TO_CHAR(e.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, e.upd_user,
           et.code_name AS exam_type_name,
           tt.code_name AS tpk_type_name,
           tl.code_name AS tpk_level_name,
           sc.code_name AS section_name,
           (SELECT CASE WHEN COUNT(*) > 0 THEN 'Y' ELSE '' END
              FROM tb_exam_file ef WHERE ef.exam_key = e.exam_key AND ef.del_yn = 'N' AND (ef.file_type = 'pdf' OR ef.file_type IS NULL)) AS has_pdf,
           (SELECT CASE WHEN COUNT(*) > 0 THEN 'Y' ELSE '' END
              FROM tb_exam_file ef WHERE ef.exam_key = e.exam_key AND ef.del_yn = 'N' AND ef.file_type = 'json') AS has_json,
           (SELECT COUNT(*)
              FROM tb_exam_file ef WHERE ef.exam_key = e.exam_key AND ef.del_yn = 'N' AND ef.file_type = 'mp3') AS mp3_count
      FROM tb_exam_list e
      LEFT JOIN tb_code et ON et.group_code = 'exam_type' AND et.code = CAST(NULLIF(e.exam_type, '') AS INTEGER)
      LEFT JOIN tb_code tt ON tt.group_code = 'topik_type' AND tt.code = e.tpk_type
      LEFT JOIN tb_code tl ON tl.group_code = 'tpk_level' AND tl.code = CAST(NULLIF(e.tpk_level, '') AS INTEGER)
      LEFT JOIN tb_code sc ON sc.group_code = 'section' AND sc.code = CAST(NULLIF(e.section, '') AS INTEGER)
"""


def list_exam_list(
    exam_type: Optional[str] = None,
    tpk_level: Optional[str] = None,
    section: Optional[str] = None,
    round: Optional[int] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    """
    시험문항 목록을 페이지네이션하여 조회한다.
    검색 조건(exam_type, tpk_level, section, round)은 정확 일치로 동적 적용된다.

    Args:
        exam_type: 시험유형 코드 (정확 일치)
        tpk_level: 토픽레벨 코드 (정확 일치)
        section: 영역 코드 (정확 일치)
        round: 회차 (정수 정확 일치)
        page: 페이지 번호
        size: 페이지당 항목 수

    Returns:
        (조회 결과 리스트, 전체 건수) 튜플
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 동적 WHERE 조건 구성 (삭제된 항목은 항상 제외)
        conditions = ["e.del_yn = 'N'"]
        params = []

        if exam_type:
            conditions.append("e.exam_type = %s")
            params.append(exam_type)
        if tpk_level:
            conditions.append("e.tpk_level = %s")
            params.append(tpk_level)
        if section:
            conditions.append("e.section = %s")
            params.append(section)
        if round is not None:
            conditions.append("e.round = %s")
            params.append(round)

        where_clause = "WHERE " + " AND ".join(conditions)

        # 전체 건수 조회
        count_sql = f"SELECT COUNT(*) AS total FROM tb_exam_list e {where_clause}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # 페이지네이션 적용하여 목록 조회 (삭제여부 오름차순 → 생성시간 내림차순)
        limit, offset = get_limit_offset(page, size)
        list_sql = f"""
            {_BASE_SELECT}
            {where_clause}
            ORDER BY e.del_yn ASC, e.ins_date DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params) + (limit, offset))
        rows = cursor.fetchall()

        return rows, total
    finally:
        conn.close()


def get_exam(exam_key: int) -> Optional[dict]:
    """
    특정 시험문항의 상세 정보를 코드명 JOIN과 함께 조회한다.

    Args:
        exam_key: 조회할 시험문항 PK

    Returns:
        시험문항 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 시험문항 PK로 단건 조회 (코드명 LEFT JOIN 포함)
        sql = f"""
            {_BASE_SELECT}
            WHERE e.exam_key = %s
        """
        cursor.execute(sql, (exam_key,))
        return cursor.fetchone()
    finally:
        conn.close()


def create_exam(data: dict, user: str = "admin") -> dict:
    """
    새로운 시험문항을 생성한다.

    Args:
        data: exam_year, exam_type, round, tpk_level, section을 포함한 딕셔너리
        user: 등록/수정자 (추후 JWT 인증 연동 시 현재 사용자로 대체)

    Returns:
        생성된 시험문항 정보 딕셔너리
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 시험문항 신규 등록 (del_yn 기본값 'N', 등록일시 현재시각)
        # RETURNING으로 생성된 PK를 안전하게 조회 (lastval() 대비 동시성 안전)
        cursor.execute(
            """
            INSERT INTO tb_exam_list (exam_year, exam_type, tpk_type, round, tpk_level, section,
                                      del_yn, ins_date, ins_user, upd_date, upd_user)
            VALUES (%s, %s, %s, %s, %s, %s, 'N', NOW(), %s, NOW(), %s)
            RETURNING exam_key
            """,
            (
                data["exam_year"],
                data["exam_type"],
                data.get("tpk_type"),
                data.get("round"),
                data.get("tpk_level"),
                data["section"],
                user,
                user,
            ),
        )
        new_key = cursor.fetchone()["exam_key"]
        conn.commit()

        # INSERT 후 포맷된 날짜를 포함한 결과를 조회하여 반환
        return get_exam(new_key)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_exam(exam_key: int, data: dict, user: str = "admin") -> Optional[dict]:
    """
    기존 시험문항 정보를 수정한다.
    전달된 필드 중 None이 아닌 값만 업데이트한다.

    Args:
        exam_key: 수정할 시험문항 PK
        data: 수정할 필드 딕셔너리
        user: 수정자 (추후 JWT 인증 연동 시 현재 사용자로 대체)

    Returns:
        수정된 시험문항 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # None이 아닌 필드만 SET 절에 추가 (동적 UPDATE 구성)
        set_clauses = []
        params = []
        for field in ["exam_year", "exam_type", "tpk_type", "round", "tpk_level", "section", "del_yn"]:
            if data.get(field) is not None:
                set_clauses.append(f"{field} = %s")
                params.append(data[field])

        if not set_clauses:
            # 수정할 항목이 없으면 기존 데이터 반환
            return get_exam(exam_key)

        # 수정일시, 수정자 자동 설정
        set_clauses.append("upd_date = NOW()")
        set_clauses.append("upd_user = %s")
        params.append(user)
        params.append(exam_key)

        update_sql = f"""
            UPDATE tb_exam_list
               SET {', '.join(set_clauses)}
             WHERE exam_key = %s
        """
        cursor.execute(update_sql, tuple(params))
        conn.commit()
        # UPDATE 후 포맷된 날짜를 포함한 결과를 조회하여 반환
        return get_exam(exam_key)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_exam(exam_key: int, user: str = "admin") -> Optional[dict]:
    """
    시험문항을 논리 삭제(소프트 딜리트)한다.
    del_yn을 'Y'로 변경하고 수정일시를 갱신한다.

    Args:
        exam_key: 삭제할 시험문항 PK
        user: 수정자 (추후 JWT 인증 연동 시 현재 사용자로 대체)

    Returns:
        삭제 처리된 시험문항 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 논리 삭제: del_yn='Y'로 변경
        cursor.execute(
            """
            UPDATE tb_exam_list
               SET del_yn = 'Y', upd_date = NOW(), upd_user = %s
             WHERE exam_key = %s
            """,
            (user, exam_key),
        )
        conn.commit()
        # DELETE 후 포맷된 날짜를 포함한 결과를 조회하여 반환
        return get_exam(exam_key)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
