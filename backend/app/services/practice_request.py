"""
연습문제 생성 요청 서비스 모듈
tb_practice_request 테이블에 대한 CRUD 비즈니스 로직을 처리한다.
psycopg (v3) raw SQL을 사용하며 ORM은 사용하지 않는다.
"""
from app.database import get_connection


def list_requests(
    page: int = 1,
    size: int = 20,
    exam_type: str | None = None,
    tpk_level: str | None = None,
    section: str | None = None,
    gen_method: str | None = None,
    status: str | None = None,
) -> dict:
    """
    연습문제 생성 요청 목록을 페이징하여 조회한다.
    코드명은 tb_code를 LEFT JOIN하여 함께 반환한다.

    Args:
        page: 페이지 번호 (1부터)
        size: 페이지당 행 수
        exam_type: 시험유형 코드 필터
        tpk_level: 토픽레벨 코드 필터
        section: 영역 코드 필터
        gen_method: 생성방법 필터
        status: 상태 필터

    Returns:
        list, total을 포함한 딕셔너리
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 동적 WHERE 조건 조립
        conditions = ["r.del_yn = 'N'"]
        params = []

        if exam_type:
            conditions.append("r.exam_type = %s")
            params.append(exam_type)
        if tpk_level:
            conditions.append("r.tpk_level = %s")
            params.append(tpk_level)
        if section:
            conditions.append("r.section = %s")
            params.append(section)
        if gen_method:
            conditions.append("r.gen_method = %s")
            params.append(gen_method)
        if status:
            conditions.append("r.status = %s")
            params.append(status)

        where_clause = " AND ".join(conditions)

        # 전체 건수 조회
        cursor.execute(
            f"SELECT COUNT(*) FROM tb_practice_request r WHERE {where_clause}",
            tuple(params),
        )
        total = cursor.fetchone()["count"]

        # 목록 조회 — 코드명 LEFT JOIN
        offset = (page - 1) * size
        cursor.execute(
            f"""
            SELECT r.request_key,
                   r.exam_type,
                   c_et.code_name AS exam_type_name,
                   r.tpk_level,
                   c_tl.code_name AS tpk_level_name,
                   r.section,
                   c_sc.code_name AS section_name,
                   r.difficulty,
                   c_df.code_name AS difficulty_name,
                   r.question_count,
                   r.gen_method,
                   c_gm.code_name AS gen_method_name,
                   r.status,
                   c_st.code_name AS status_name,
                   r.del_yn,
                   TO_CHAR(r.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date,
                   r.ins_user,
                   TO_CHAR(r.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date,
                   r.upd_user
              FROM tb_practice_request r
              LEFT JOIN tb_code c_et ON c_et.group_code = 'exam_type'       AND c_et.code = CAST(r.exam_type AS INTEGER)
              LEFT JOIN tb_code c_tl ON c_tl.group_code = 'tpk_level'       AND c_tl.code = CAST(r.tpk_level AS INTEGER)
              LEFT JOIN tb_code c_sc ON c_sc.group_code = 'section'         AND c_sc.code = CAST(r.section AS INTEGER)
              LEFT JOIN tb_code c_df ON c_df.group_code = 'difficulty'        AND c_df.code = CAST(r.difficulty AS INTEGER)
              LEFT JOIN tb_code c_gm ON c_gm.group_code = 'exam_req_method' AND c_gm.code = CAST(r.gen_method AS INTEGER)
              LEFT JOIN tb_code c_st ON c_st.group_code = 'exam_req_status'  AND c_st.code = CAST(r.status AS INTEGER)
             WHERE {where_clause}
             ORDER BY r.request_key DESC
             LIMIT %s OFFSET %s
            """,
            tuple(params) + (size, offset),
        )
        rows = cursor.fetchall()

        return {"list": rows, "total": total}
    finally:
        conn.close()


def create_request(data: dict, user: str = "admin") -> dict:
    """
    연습문제 생성 요청을 등록한다.

    Args:
        data: 요청 데이터
        user: 등록자

    Returns:
        등록된 요청 정보
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO tb_practice_request
                   (exam_type, tpk_level, section, difficulty,
                    question_count, gen_method, status,
                    del_yn, ins_date, ins_user, upd_date, upd_user)
            VALUES (%s, %s, %s, %s, %s, %s, '1', 'N', NOW(), %s, NOW(), %s)
            RETURNING request_key
            """,
            (
                data["exam_type"],
                data["tpk_level"],
                data["section"],
                data.get("difficulty"),
                data["question_count"],
                data["gen_method"],
                user,
                user,
            ),
        )
        request_key = cursor.fetchone()["request_key"]
        conn.commit()

        # 등록된 데이터 재조회
        return get_request(request_key)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_request(request_key: int) -> dict | None:
    """
    연습문제 생성 요청 단건을 조회한다.

    Args:
        request_key: 요청 PK

    Returns:
        요청 정보 딕셔너리 (없으면 None)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT request_key, exam_type, tpk_level, section, difficulty,
                   question_count, gen_method, status, del_yn,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, ins_user,
                   TO_CHAR(upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, upd_user
              FROM tb_practice_request
             WHERE request_key = %s
            """,
            (request_key,),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def update_request(request_key: int, data: dict, user: str = "admin") -> dict:
    """
    연습문제 생성 요청을 수정한다.

    Args:
        request_key: 요청 PK
        data: 수정 데이터
        user: 수정자

    Returns:
        수정된 요청 정보
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tb_practice_request
               SET exam_type = %s, tpk_level = %s, section = %s, difficulty = %s,
                   question_count = %s, gen_method = %s,
                   upd_date = NOW(), upd_user = %s
             WHERE request_key = %s
            """,
            (
                data["exam_type"],
                data["tpk_level"],
                data["section"],
                data.get("difficulty"),
                data["question_count"],
                data["gen_method"],
                user,
                request_key,
            ),
        )
        conn.commit()
        return get_request(request_key)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_request(request_key: int, user: str = "admin") -> None:
    """
    연습문제 생성 요청을 소프트 삭제한다.

    Args:
        request_key: 요청 PK
        user: 수정자
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tb_practice_request
               SET del_yn = 'Y', upd_date = NOW(), upd_user = %s
             WHERE request_key = %s
            """,
            (user, request_key),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
