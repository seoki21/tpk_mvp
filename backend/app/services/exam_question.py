"""
기출문제/지시문 서비스 모듈
tb_exam_question, tb_exam_instruction 테이블에 대한 CRUD 비즈니스 로직을 처리한다.
psycopg (v3) raw SQL을 사용하며 ORM은 사용하지 않는다.
"""
from app.database import get_connection


def list_questions_and_instructions(exam_key: int) -> dict:
    """
    특정 시험의 문제와 지시문을 모두 조회하여 반환한다.
    CLAUDE.md 정의: tb_exam_question과 tb_exam_instruction을 union all하여 차례로 출력

    Args:
        exam_key: 시험 PK

    Returns:
        questions, instructions를 포함한 딕셔너리
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 문제 목록 조회 (문제 번호 순)
        cursor.execute(
            """
            SELECT exam_key, question_no, section, question_type, struct_type,
                   question_json, score, difficulty, del_yn,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, ins_user,
                   TO_CHAR(upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, upd_user
              FROM tb_exam_question
             WHERE exam_key = %s AND del_yn = 'N'
             ORDER BY question_no ASC
            """,
            (exam_key,),
        )
        questions = cursor.fetchall()

        # 지시문 목록 조회 (지시문 번호 순)
        cursor.execute(
            """
            SELECT exam_key, ins_no, ins_json, del_yn,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, ins_user,
                   TO_CHAR(upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, upd_user
              FROM tb_exam_instruction
             WHERE exam_key = %s AND del_yn = 'N'
             ORDER BY ins_no ASC
            """,
            (exam_key,),
        )
        instructions = cursor.fetchall()

        return {
            "questions": questions,
            "instructions": instructions,
        }
    finally:
        conn.close()


def save_question(exam_key: int, data: dict, user: str = "admin") -> dict:
    """
    문제 단건을 저장한다 (UPSERT — 있으면 UPDATE, 없으면 INSERT).

    Args:
        exam_key: 시험 PK
        data: 문제 데이터 (question_no 필수)
        user: 작업자

    Returns:
        저장된 문제 정보
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        question_no = data["question_no"]

        # 기존 데이터 존재 여부 확인
        cursor.execute(
            "SELECT 1 FROM tb_exam_question WHERE exam_key = %s AND question_no = %s",
            (exam_key, question_no),
        )
        exists = cursor.fetchone()

        if exists:
            # UPDATE
            cursor.execute(
                """
                UPDATE tb_exam_question
                   SET section = %s, question_type = %s, struct_type = %s,
                       question_json = %s, score = %s, difficulty = %s,
                       del_yn = 'N', upd_date = NOW(), upd_user = %s
                 WHERE exam_key = %s AND question_no = %s
                """,
                (
                    data.get("section"),
                    data.get("question_type"),
                    data.get("struct_type"),
                    data.get("question_json"),
                    data.get("score"),
                    data.get("difficulty"),
                    user,
                    exam_key,
                    question_no,
                ),
            )
        else:
            # INSERT
            cursor.execute(
                """
                INSERT INTO tb_exam_question
                       (exam_key, question_no, section, question_type, struct_type,
                        question_json, score, difficulty, del_yn, ins_date, ins_user, upd_date, upd_user)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'N', NOW(), %s, NOW(), %s)
                """,
                (
                    exam_key,
                    question_no,
                    data.get("section"),
                    data.get("question_type"),
                    data.get("struct_type"),
                    data.get("question_json"),
                    data.get("score"),
                    data.get("difficulty"),
                    user,
                    user,
                ),
            )

        conn.commit()

        # 재조회하여 포맷된 결과 반환
        cursor.execute(
            """
            SELECT exam_key, question_no, section, question_type, struct_type,
                   question_json, score, difficulty, del_yn,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, ins_user,
                   TO_CHAR(upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, upd_user
              FROM tb_exam_question
             WHERE exam_key = %s AND question_no = %s
            """,
            (exam_key, question_no),
        )
        return cursor.fetchone()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def save_instruction(exam_key: int, data: dict, user: str = "admin") -> dict:
    """
    지시문 단건을 저장한다 (UPSERT — 있으면 UPDATE, 없으면 INSERT).

    Args:
        exam_key: 시험 PK
        data: 지시문 데이터 (ins_no 필수)
        user: 작업자

    Returns:
        저장된 지시문 정보
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        ins_no = data["ins_no"]

        # 기존 데이터 존재 여부 확인
        cursor.execute(
            "SELECT 1 FROM tb_exam_instruction WHERE exam_key = %s AND ins_no = %s",
            (exam_key, ins_no),
        )
        exists = cursor.fetchone()

        if exists:
            # UPDATE
            cursor.execute(
                """
                UPDATE tb_exam_instruction
                   SET ins_json = %s, del_yn = 'N', upd_date = NOW(), upd_user = %s
                 WHERE exam_key = %s AND ins_no = %s
                """,
                (
                    data.get("ins_json"),
                    user,
                    exam_key,
                    ins_no,
                ),
            )
        else:
            # INSERT
            cursor.execute(
                """
                INSERT INTO tb_exam_instruction
                       (exam_key, ins_no, ins_json, del_yn, ins_date, ins_user, upd_date, upd_user)
                VALUES (%s, %s, %s, 'N', NOW(), %s, NOW(), %s)
                """,
                (
                    exam_key,
                    ins_no,
                    data.get("ins_json"),
                    user,
                    user,
                ),
            )

        conn.commit()

        # 재조회
        cursor.execute(
            """
            SELECT exam_key, ins_no, ins_json, del_yn,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, ins_user,
                   TO_CHAR(upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, upd_user
              FROM tb_exam_instruction
             WHERE exam_key = %s AND ins_no = %s
            """,
            (exam_key, ins_no),
        )
        return cursor.fetchone()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def bulk_save(exam_key: int, questions: list[dict], instructions: list[dict], user: str = "admin") -> dict:
    """
    문제와 지시문을 일괄 저장한다.
    기출문항 변환(JSON) 팝업의 '저장' 버튼에서 호출된다.

    Args:
        exam_key: 시험 PK
        questions: 문제 데이터 리스트
        instructions: 지시문 데이터 리스트
        user: 작업자

    Returns:
        저장 결과 (저장된 건수)
    """
    saved_questions = 0
    saved_instructions = 0

    for q in questions:
        save_question(exam_key, q, user)
        saved_questions += 1

    for ins in instructions:
        save_instruction(exam_key, ins, user)
        saved_instructions += 1

    return {
        "saved_questions": saved_questions,
        "saved_instructions": saved_instructions,
    }
