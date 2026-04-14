"""
시험일정 서비스 모듈
tb_exam_schedule + tb_exam_location 테이블에 대한 CRUD 비즈니스 로직을 처리한다.
tb_code와 JOIN하여 시험종류/지역 명칭을 함께 반환한다.
location은 schedule 단건 조회 시 배열로 포함하여 반환한다.
psycopg (v3) raw SQL을 사용하며 ORM은 사용하지 않는다.
"""
from typing import Optional
from app.database import get_connection
from app.utils.pagination import get_limit_offset


def list_exam_schedules(
    tpk_type: Optional[int] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    """
    시험일정 목록을 페이지네이션하여 조회한다.
    각 회차별 지역 수와 지역 명칭 요약을 함께 반환한다.

    Args:
        tpk_type: 시험종류 코드 필터
        page: 페이지 번호
        size: 페이지당 항목 수

    Returns:
        (조회 결과 리스트, 전체 건수) 튜플
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        conditions = ["s.del_yn = 'N'"]
        params = []

        if tpk_type is not None:
            conditions.append("s.tpk_type = %s")
            params.append(tpk_type)

        where_clause = "WHERE " + " AND ".join(conditions)

        # 전체 건수 조회
        count_sql = f"SELECT COUNT(*) AS total FROM tb_exam_schedule s {where_clause}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # 목록 조회 — location 건수 및 지역명 요약을 서브쿼리로 포함
        limit, offset = get_limit_offset(page, size)
        list_sql = f"""
            SELECT
                s.exam_key,
                s.tpk_type,
                c_type.code_name                    AS tpk_type_name,
                s.round,
                s.del_yn,
                TO_CHAR(s.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date,
                s.ins_user,
                TO_CHAR(s.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date,
                s.upd_user,
                -- 지역명 목록 (줄바꿈 구분)
                (
                    SELECT STRING_AGG(c_r.code_name, E'\n' ORDER BY l2.exam_region)
                      FROM tb_exam_location l2
                      LEFT JOIN tb_code c_r ON c_r.group_code = 'exam_region'
                                           AND c_r.code = l2.exam_region
                     WHERE l2.exam_key = s.exam_key AND l2.del_yn = 'N'
                )                                   AS region_names,
                -- 시험일 목록 (줄바꿈 구분, 지역과 동일 순서)
                (
                    SELECT STRING_AGG(COALESCE(TO_CHAR(l3.test_date, 'YYYY-MM-DD'), '-'), E'\n' ORDER BY l3.exam_region)
                      FROM tb_exam_location l3
                     WHERE l3.exam_key = s.exam_key AND l3.del_yn = 'N'
                )                                   AS test_dates
              FROM tb_exam_schedule s
              LEFT JOIN tb_code c_type ON c_type.group_code = 'topik_type'
                                      AND c_type.code = s.tpk_type
              {where_clause}
             ORDER BY s.tpk_type ASC, s.round DESC
             LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params) + (limit, offset))
        return cursor.fetchall(), total
    finally:
        conn.close()


def get_exam_schedule(exam_key: int) -> Optional[dict]:
    """
    시험일정 단건을 조회한다. locations 배열을 포함하여 반환한다.

    Args:
        exam_key: 시험일정 키

    Returns:
        시험일정 딕셔너리 (locations 포함) 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # schedule 단건 조회
        cursor.execute(
            """
            SELECT
                s.exam_key,
                s.tpk_type,
                c_type.code_name  AS tpk_type_name,
                s.round,
                s.del_yn,
                TO_CHAR(s.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date,
                s.ins_user,
                TO_CHAR(s.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date,
                s.upd_user
              FROM tb_exam_schedule s
              LEFT JOIN tb_code c_type ON c_type.group_code = 'topik_type'
                                      AND c_type.code = s.tpk_type
             WHERE s.exam_key = %s
            """,
            (exam_key,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        # location 목록 조회 — 지역명 포함
        cursor.execute(
            """
            SELECT
                l.loc_key,
                l.exam_region,
                c_r.code_name  AS exam_region_name,
                TO_CHAR(l.test_date, 'YYYY-MM-DD') AS test_date,
                l.del_yn
              FROM tb_exam_location l
              LEFT JOIN tb_code c_r ON c_r.group_code = 'exam_region'
                                   AND c_r.code = l.exam_region
             WHERE l.exam_key = %s AND l.del_yn = 'N'
             ORDER BY l.exam_region ASC
            """,
            (exam_key,),
        )
        locations = cursor.fetchall()

        # schedule 딕셔너리에 locations 배열 추가
        result = dict(row)
        result["locations"] = locations
        return result
    finally:
        conn.close()


def create_exam_schedule(data: dict, user: str = "admin") -> dict:
    """
    시험일정을 신규 등록한다. locations도 함께 일괄 INSERT한다.

    Args:
        data: tpk_type, round, locations([{exam_region, test_date}])
        user: 등록자

    Returns:
        등록된 시험일정 딕셔너리 (locations 포함)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 동일 시험종류 + 회차 중복 확인
        cursor.execute(
            "SELECT 1 FROM tb_exam_schedule WHERE tpk_type = %s AND round = %s AND del_yn = 'N'",
            (data["tpk_type"], data["round"]),
        )
        if cursor.fetchone():
            raise ValueError("이미 존재하는 시험일정입니다. (동일한 시험종류/회차)")

        # tb_exam_schedule INSERT — RETURNING으로 exam_key 획득
        cursor.execute(
            """
            INSERT INTO tb_exam_schedule
                (tpk_type, round, del_yn, ins_date, ins_user, upd_date, upd_user)
            VALUES (%s, %s, 'N', NOW(), %s, NOW(), %s)
            RETURNING exam_key
            """,
            (data["tpk_type"], data["round"], user, user),
        )
        exam_key = cursor.fetchone()["exam_key"]

        # tb_exam_location 일괄 INSERT
        for loc in data.get("locations", []):
            cursor.execute(
                """
                INSERT INTO tb_exam_location
                    (exam_key, exam_region, test_date, del_yn, ins_date, ins_user, upd_date, upd_user)
                VALUES (%s, %s, %s, 'N', NOW(), %s, NOW(), %s)
                """,
                (exam_key, loc["exam_region"], loc.get("test_date"), user, user),
            )

        conn.commit()
        return get_exam_schedule(exam_key)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_exam_schedule(exam_key: int, data: dict, user: str = "admin") -> Optional[dict]:
    """
    시험일정의 locations를 전체 교체한다.
    기존 location을 논리 삭제 후 새 목록을 INSERT한다.

    Args:
        exam_key: 시험일정 키
        data: locations([{exam_region, test_date}])
        user: 수정자

    Returns:
        수정된 시험일정 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 기존 location 논리 삭제
        cursor.execute(
            "UPDATE tb_exam_location SET del_yn = 'Y', upd_date = NOW(), upd_user = %s WHERE exam_key = %s",
            (user, exam_key),
        )

        # 새 location 일괄 INSERT
        for loc in data.get("locations", []):
            cursor.execute(
                """
                INSERT INTO tb_exam_location
                    (exam_key, exam_region, test_date, del_yn, ins_date, ins_user, upd_date, upd_user)
                VALUES (%s, %s, %s, 'N', NOW(), %s, NOW(), %s)
                """,
                (exam_key, loc["exam_region"], loc.get("test_date"), user, user),
            )

        # schedule 수정일시 갱신
        cursor.execute(
            "UPDATE tb_exam_schedule SET upd_date = NOW(), upd_user = %s WHERE exam_key = %s",
            (user, exam_key),
        )

        conn.commit()
        return get_exam_schedule(exam_key)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_exam_schedule(exam_key: int, user: str = "admin") -> Optional[dict]:
    """
    시험일정을 논리 삭제(del_yn='Y')한다. location도 함께 논리 삭제한다.

    Args:
        exam_key: 시험일정 키
        user: 수정자

    Returns:
        삭제 처리된 시험일정 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # location 논리 삭제
        cursor.execute(
            "UPDATE tb_exam_location SET del_yn = 'Y', upd_date = NOW(), upd_user = %s WHERE exam_key = %s",
            (user, exam_key),
        )
        # schedule 논리 삭제
        cursor.execute(
            "UPDATE tb_exam_schedule SET del_yn = 'Y', upd_date = NOW(), upd_user = %s WHERE exam_key = %s",
            (user, exam_key),
        )

        conn.commit()
        return get_exam_schedule(exam_key)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
