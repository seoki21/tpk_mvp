"""
관리자 서비스 모듈
tb_admin, tb_admin_role 테이블에 대한 CRUD 비즈니스 로직을 처리한다.
psycopg (v3) raw SQL을 사용하며 ORM은 사용하지 않는다.
"""
from typing import Optional
from app.database import get_connection
from app.utils.auth import hash_password
from app.utils.pagination import get_limit_offset


def get_admin(admin_id: str) -> Optional[dict]:
    """
    관리자 상세 조회 (비밀번호 포함 — 로그인 검증용).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.admin_id, a.password, a.admin_desc, a.del_yn,
                   TO_CHAR(a.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, a.ins_user,
                   TO_CHAR(a.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, a.upd_user
              FROM tb_admin a
             WHERE a.admin_id = %s
            """,
            (admin_id,),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def get_admin_roles(admin_id: str) -> list[str]:
    """관리자의 권한 코드 목록을 조회한다."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role_code FROM tb_admin_role WHERE admin_id = %s",
            (admin_id,),
        )
        return [row["role_code"] for row in cursor.fetchall()]
    finally:
        conn.close()


def list_admins(page: int = 1, size: int = 20) -> tuple[list[dict], int]:
    """
    관리자 목록을 페이지네이션하여 조회한다.
    비밀번호 컬럼은 제외한다.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 전체 건수 조회
        cursor.execute("SELECT COUNT(*) AS total FROM tb_admin")
        total = cursor.fetchone()["total"]

        # 목록 조회 (비밀번호 제외, 권한 코드 서브쿼리)
        limit, offset = get_limit_offset(page, size)
        cursor.execute(
            """
            SELECT a.admin_id, a.admin_desc, a.del_yn,
                   TO_CHAR(a.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, a.ins_user,
                   TO_CHAR(a.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, a.upd_user,
                   (SELECT STRING_AGG(r.role_code, ',') FROM tb_admin_role r WHERE r.admin_id = a.admin_id) AS roles
              FROM tb_admin a
             ORDER BY a.del_yn ASC, a.ins_date ASC
             LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        return cursor.fetchall(), total
    finally:
        conn.close()


def create_admin(data: dict, ins_user: str = "admin") -> dict:
    """
    관리자를 생성한다.
    비밀번호는 bcrypt 해시로 저장하고, 권한도 함께 등록한다.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 중복 체크
        cursor.execute("SELECT 1 FROM tb_admin WHERE admin_id = %s", (data["admin_id"],))
        if cursor.fetchone():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="이미 존재하는 관리자 ID입니다.")

        # 관리자 INSERT
        hashed = hash_password(data["password"])
        cursor.execute(
            """
            INSERT INTO tb_admin (admin_id, password, admin_desc, ins_user)
            VALUES (%s, %s, %s, %s)
            """,
            (data["admin_id"], hashed, data.get("admin_desc"), ins_user),
        )

        # 권한 INSERT
        role_code = data.get("role_code", "MANAGER")
        cursor.execute(
            "INSERT INTO tb_admin_role (admin_id, role_code) VALUES (%s, %s)",
            (data["admin_id"], role_code),
        )

        conn.commit()
        return get_admin_safe(data["admin_id"])
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_admin(admin_id: str, data: dict, upd_user: str = "admin") -> Optional[dict]:
    """
    관리자 정보를 수정한다.
    비밀번호가 포함된 경우 bcrypt 해시로 변환하여 저장한다.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        set_parts = []
        params = []

        if "password" in data and data["password"]:
            set_parts.append("password = %s")
            params.append(hash_password(data["password"]))
        if "admin_desc" in data:
            set_parts.append("admin_desc = %s")
            params.append(data["admin_desc"])
        if "del_yn" in data and data["del_yn"]:
            set_parts.append("del_yn = %s")
            params.append(data["del_yn"])

        if not set_parts:
            return get_admin_safe(admin_id)

        set_parts.append("upd_date = NOW()")
        set_parts.append("upd_user = %s")
        params.append(upd_user)
        params.append(admin_id)

        cursor.execute(
            f"UPDATE tb_admin SET {', '.join(set_parts)} WHERE admin_id = %s",
            tuple(params),
        )
        conn.commit()
        return get_admin_safe(admin_id)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_admin(admin_id: str, upd_user: str = "admin") -> Optional[dict]:
    """관리자를 논리 삭제(소프트 딜리트)한다."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tb_admin SET del_yn = 'Y', upd_date = NOW(), upd_user = %s WHERE admin_id = %s",
            (upd_user, admin_id),
        )
        conn.commit()
        return get_admin_safe(admin_id)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_admin_safe(admin_id: str) -> Optional[dict]:
    """관리자 상세 조회 (비밀번호 제외 — 응답용)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.admin_id, a.admin_desc, a.del_yn,
                   TO_CHAR(a.ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date, a.ins_user,
                   TO_CHAR(a.upd_date, 'YYYY-MM-DD HH24:MI:SS') AS upd_date, a.upd_user,
                   (SELECT STRING_AGG(r.role_code, ',') FROM tb_admin_role r WHERE r.admin_id = a.admin_id) AS roles
              FROM tb_admin a
             WHERE a.admin_id = %s
            """,
            (admin_id,),
        )
        return cursor.fetchone()
    finally:
        conn.close()
