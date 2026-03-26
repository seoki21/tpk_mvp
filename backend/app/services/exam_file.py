"""
시험 파일 서비스 모듈
tb_exam_file 테이블에 대한 CRUD 비즈니스 로직을 처리한다.
파일 저장/삭제는 로컬 파일시스템을 사용한다.
psycopg (v3) raw SQL을 사용하며 ORM은 사용하지 않는다.
"""
import os
import uuid
from typing import Optional
from fastapi import UploadFile

from app.database import get_connection
from app.config import UPLOAD_DIR


def _ensure_upload_dir(exam_key: int) -> str:
    """
    시험별 업로드 디렉토리를 생성하고 경로를 반환한다.
    구조: {UPLOAD_DIR}/exam/{exam_key}/

    Args:
        exam_key: 시험 PK

    Returns:
        업로드 디렉토리 절대 경로
    """
    dir_path = os.path.join(UPLOAD_DIR, "exam", str(exam_key))
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def list_files(exam_key: int) -> list[dict]:
    """
    특정 시험의 파일 목록을 조회한다. (삭제되지 않은 것만)

    Args:
        exam_key: 시험 PK

    Returns:
        파일 정보 딕셔너리 리스트
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 시험 PK로 파일 목록 조회 (정렬순서 → 등록일 순)
        cursor.execute(
            """
            SELECT pdf_key, exam_key, file_name, file_path, file_size, sort_order,
                   del_yn,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, ins_user
              FROM tb_exam_file
             WHERE exam_key = %s AND del_yn = 'N'
             ORDER BY sort_order ASC, ins_date ASC
            """,
            (exam_key,),
        )
        return cursor.fetchall()
    finally:
        conn.close()


async def upload_files(
    exam_key: int, files: list[UploadFile], user: str = "admin"
) -> list[dict]:
    """
    파일을 서버에 저장하고 DB에 메타데이터를 등록한다.
    파일명 충돌 방지를 위해 UUID 기반 저장명을 사용한다.

    Args:
        exam_key: 시험 PK
        files: 업로드된 파일 리스트
        user: 등록자

    Returns:
        등록된 파일 정보 딕셔너리 리스트
    """
    upload_dir = _ensure_upload_dir(exam_key)

    # 현재 최대 sort_order를 조회하여 이어서 번호 부여
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(MAX(sort_order), 0) AS max_order FROM tb_exam_file WHERE exam_key = %s AND del_yn = 'N'",
            (exam_key,),
        )
        current_max = cursor.fetchone()["max_order"]
    finally:
        conn.close()

    saved_keys = []

    for idx, file in enumerate(files):
        # UUID 기반 저장 파일명 생성 (확장자 유지)
        ext = os.path.splitext(file.filename)[1] or ".pdf"
        stored_name = f"{uuid.uuid4().hex}{ext}"
        stored_path = os.path.join(upload_dir, stored_name)

        # 파일 저장
        content = await file.read()
        file_size = len(content)
        with open(stored_path, "wb") as f:
            f.write(content)

        # DB에 상대 경로로 저장 (UPLOAD_DIR 기준)
        relative_path = os.path.join("exam", str(exam_key), stored_name).replace("\\", "/")

        conn = get_connection()
        try:
            cursor = conn.cursor()
            # 파일 메타데이터 INSERT
            cursor.execute(
                """
                INSERT INTO tb_exam_file (exam_key, file_name, file_path, file_size, sort_order,
                                          del_yn, ins_date, ins_user)
                VALUES (%s, %s, %s, %s, %s, 'N', NOW(), %s)
                RETURNING pdf_key
                """,
                (
                    exam_key,
                    file.filename,
                    relative_path,
                    file_size,
                    current_max + idx + 1,
                    user,
                ),
            )
            new_key = cursor.fetchone()["pdf_key"]
            saved_keys.append(new_key)
            conn.commit()
        except Exception:
            conn.rollback()
            # 저장된 파일 정리
            if os.path.exists(stored_path):
                os.remove(stored_path)
            raise
        finally:
            conn.close()

    return list_files(exam_key)


def delete_file(pdf_key: int, user: str = "admin") -> Optional[dict]:
    """
    파일을 소프트 삭제하고 실제 파일도 삭제한다.

    Args:
        pdf_key: 삭제할 파일 PK
        user: 삭제 처리자

    Returns:
        삭제된 파일 정보 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 파일 정보 조회 (파일 경로 확인용)
        cursor.execute(
            """
            SELECT pdf_key, exam_key, file_name, file_path, file_size, sort_order,
                   del_yn,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, ins_user
              FROM tb_exam_file
             WHERE pdf_key = %s
            """,
            (pdf_key,),
        )
        file_info = cursor.fetchone()
        if not file_info:
            return None

        # 소프트 삭제 처리
        cursor.execute(
            "UPDATE tb_exam_file SET del_yn = 'Y' WHERE pdf_key = %s",
            (pdf_key,),
        )
        conn.commit()

        # 실제 파일 삭제
        full_path = os.path.join(UPLOAD_DIR, file_info["file_path"])
        if os.path.exists(full_path):
            os.remove(full_path)

        return file_info
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_file(pdf_key: int) -> Optional[dict]:
    """
    특정 파일의 상세 정보를 조회한다.

    Args:
        pdf_key: 조회할 파일 PK

    Returns:
        파일 정보 딕셔너리 또는 None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pdf_key, exam_key, file_name, file_path, file_size, sort_order,
                   del_yn,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, ins_user
              FROM tb_exam_file
             WHERE pdf_key = %s AND del_yn = 'N'
            """,
            (pdf_key,),
        )
        return cursor.fetchone()
    finally:
        conn.close()
