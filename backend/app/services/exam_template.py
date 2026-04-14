"""
시험 템플릿 서비스 모듈
tb_exam_template 테이블에 대한 CRUD 비즈니스 로직을 처리한다.
tb_code와 JOIN하여 시험종류/레벨/영역/지문유형/문항유형 명칭을 함께 반환한다.
psycopg (v3) raw SQL을 사용하며 ORM은 사용하지 않는다.
"""
from typing import Optional
from app.database import get_connection
from app.utils.pagination import get_limit_offset


def list_exam_templates(
    tpk_type: Optional[int] = None,
    tpk_level: Optional[int] = None,
    section: Optional[int] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    """
    시험 템플릿 목록을 페이지네이션하여 조회한다.
    tb_code와 LEFT JOIN하여 각 코드의 명칭을 함께 반환한다.

    Args:
        tpk_type: 시험종류 코드 필터
        tpk_level: 토픽레벨 코드 필터
        section: 영역 코드 필터
        page: 페이지 번호
        size: 페이지당 항목 수

    Returns:
        (조회 결과 리스트, 전체 건수) 튜플
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 동적 WHERE 조건 구성
        conditions = ["t.del_yn = 'N'"]
        params = []

        if tpk_type is not None:
            conditions.append("t.tpk_type = %s")
            params.append(tpk_type)
        if tpk_level is not None:
            conditions.append("t.tpk_level = %s")
            params.append(tpk_level)
        if section is not None:
            conditions.append("t.section = %s")
            params.append(section)

        where_clause = "WHERE " + " AND ".join(conditions)

        # 전체 건수 조회
        count_sql = f"""
            SELECT COUNT(*) AS total
              FROM tb_exam_template t
              {where_clause}
        """
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # tb_code와 LEFT JOIN하여 각 코드명 포함 목록 조회
        # 문항번호 오름차순 정렬
        limit, offset = get_limit_offset(page, size)
        list_sql = f"""
            SELECT
                t.tpk_type,
                c_tpk_type.code_name   AS tpk_type_name,
                t.tpk_level,
                c_level.code_name      AS tpk_level_name,
                t.section,
                c_section.code_name    AS section_name,
                t.question_no,
                t.passage_type,
                c_passage.code_name    AS passage_type_name,
                t.question_type,
                c_question.code_name   AS question_type_name,
                t.del_yn,
                TO_CHAR(t.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date,
                t.ins_user,
                TO_CHAR(t.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date,
                t.upd_user
              FROM tb_exam_template t
              LEFT JOIN tb_code c_tpk_type ON c_tpk_type.group_code = 'topik_type'
                                          AND c_tpk_type.code = t.tpk_type
              LEFT JOIN tb_code c_level    ON c_level.group_code = 'tpk_level'
                                          AND c_level.code = t.tpk_level
              LEFT JOIN tb_code c_section  ON c_section.group_code = 'section'
                                          AND c_section.code = t.section
              LEFT JOIN tb_code c_passage  ON c_passage.group_code = 'passage_type'
                                          AND c_passage.code = t.passage_type
              LEFT JOIN tb_code c_question ON c_question.group_code = 'question_type'
                                          AND c_question.code = t.question_type
              {where_clause}
             ORDER BY t.tpk_type ASC, t.tpk_level ASC, t.question_no ASC
             LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params) + (limit, offset))
        rows = cursor.fetchall()

        return rows, total
    finally:
        conn.close()


def get_exam_template(
    tpk_type: int,
    tpk_level: int,
    section: int,
    question_no: int,
) -> Optional[dict]:
    """
    복합 PK로 시험 템플릿 단건을 조회한다.
    tb_code와 JOIN하여 각 코드명을 함께 반환한다.

    Args:
        tpk_type: 시험종류 코드
        tpk_level: 토픽레벨 코드
        section: 영역 코드
        question_no: 문항번호

    Returns:
        템플릿 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                t.tpk_type,
                c_tpk_type.code_name   AS tpk_type_name,
                t.tpk_level,
                c_level.code_name      AS tpk_level_name,
                t.section,
                c_section.code_name    AS section_name,
                t.question_no,
                t.passage_type,
                c_passage.code_name    AS passage_type_name,
                t.question_type,
                c_question.code_name   AS question_type_name,
                t.del_yn,
                TO_CHAR(t.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date,
                t.ins_user,
                TO_CHAR(t.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date,
                t.upd_user
              FROM tb_exam_template t
              LEFT JOIN tb_code c_tpk_type ON c_tpk_type.group_code = 'topik_type'
                                          AND c_tpk_type.code = t.tpk_type
              LEFT JOIN tb_code c_level    ON c_level.group_code = 'tpk_level'
                                          AND c_level.code = t.tpk_level
              LEFT JOIN tb_code c_section  ON c_section.group_code = 'section'
                                          AND c_section.code = t.section
              LEFT JOIN tb_code c_passage  ON c_passage.group_code = 'passage_type'
                                          AND c_passage.code = t.passage_type
              LEFT JOIN tb_code c_question ON c_question.group_code = 'question_type'
                                          AND c_question.code = t.question_type
             WHERE t.tpk_type = %s
               AND t.tpk_level = %s
               AND t.section = %s
               AND t.question_no = %s
            """,
            (tpk_type, tpk_level, section, question_no),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def create_exam_template(data: dict, user: str = "admin") -> dict:
    """
    시험 템플릿을 신규 등록한다.

    Args:
        data: tpk_type, tpk_level, section, question_no, passage_type, question_type
        user: 등록자

    Returns:
        등록된 템플릿 정보 딕셔너리
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 복합 PK 중복 확인
        cursor.execute(
            """
            SELECT 1 FROM tb_exam_template
             WHERE tpk_type = %s AND tpk_level = %s
               AND section = %s AND question_no = %s
            """,
            (data["tpk_type"], data["tpk_level"], data["section"], data["question_no"]),
        )
        if cursor.fetchone():
            raise ValueError("이미 존재하는 템플릿입니다. (동일한 시험종류/레벨/영역/문항번호)")

        # 시험 템플릿 신규 등록
        cursor.execute(
            """
            INSERT INTO tb_exam_template
                (tpk_type, tpk_level, section, question_no,
                 passage_type, question_type, del_yn, ins_date, ins_user, upd_date, upd_user)
            VALUES (%s, %s, %s, %s, %s, %s, 'N', NOW(), %s, NOW(), %s)
            """,
            (
                data["tpk_type"],
                data["tpk_level"],
                data["section"],
                data["question_no"],
                data.get("passage_type"),
                data.get("question_type"),
                user,
                user,
            ),
        )
        conn.commit()
        # INSERT 후 포맷된 날짜 포함 결과 재조회하여 반환
        return get_exam_template(
            data["tpk_type"], data["tpk_level"], data["section"], data["question_no"]
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_exam_template(
    tpk_type: int,
    tpk_level: int,
    section: int,
    question_no: int,
    data: dict,
    user: str = "admin",
) -> Optional[dict]:
    """
    시험 템플릿의 지문유형/문항유형을 수정한다. PK 컬럼은 수정 불가.

    Args:
        tpk_type: 시험종류 코드
        tpk_level: 토픽레벨 코드
        section: 영역 코드
        question_no: 문항번호
        data: 수정할 필드 (passage_type, question_type)
        user: 수정자

    Returns:
        수정된 템플릿 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # None이 아닌 필드만 SET 절에 추가 (동적 UPDATE 구성)
        set_clauses = []
        params = []
        for field in ["passage_type", "question_type"]:
            if field in data and data[field] is not None:
                set_clauses.append(f"{field} = %s")
                params.append(data[field])

        if not set_clauses:
            return get_exam_template(tpk_type, tpk_level, section, question_no)

        # 수정일시, 수정자 자동 설정
        set_clauses.append("upd_date = NOW()")
        set_clauses.append("upd_user = %s")
        params.append(user)
        params.extend([tpk_type, tpk_level, section, question_no])

        update_sql = f"""
            UPDATE tb_exam_template
               SET {', '.join(set_clauses)}
             WHERE tpk_type = %s AND tpk_level = %s
               AND section = %s AND question_no = %s
        """
        cursor.execute(update_sql, tuple(params))
        conn.commit()
        return get_exam_template(tpk_type, tpk_level, section, question_no)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_exam_template(
    tpk_type: int,
    tpk_level: int,
    section: int,
    question_no: int,
    user: str = "admin",
) -> Optional[dict]:
    """
    시험 템플릿을 논리 삭제(del_yn='Y')한다.

    Args:
        tpk_type: 시험종류 코드
        tpk_level: 토픽레벨 코드
        section: 영역 코드
        question_no: 문항번호
        user: 수정자

    Returns:
        삭제 처리된 템플릿 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tb_exam_template
               SET del_yn = 'Y', upd_date = NOW(), upd_user = %s
             WHERE tpk_type = %s AND tpk_level = %s
               AND section = %s AND question_no = %s
            """,
            (user, tpk_type, tpk_level, section, question_no),
        )
        conn.commit()
        return get_exam_template(tpk_type, tpk_level, section, question_no)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
