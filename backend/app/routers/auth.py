"""
인증 API 라우터
로그인, 현재 관리자 조회 엔드포인트를 정의한다.
URL 접두사: /api/v1/auth
"""
from fastapi import APIRouter, HTTPException, Depends

from app.models.common import BaseResponse
from app.models.admin import LoginRequest, LoginResponse
from app.services import admin as admin_service
from app.utils.auth import verify_password, create_access_token, get_current_admin

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["인증"],
)


@router.post("/login", response_model=BaseResponse)
def login(body: LoginRequest):
    """
    관리자 로그인 — ID/비밀번호를 검증하고 JWT 토큰을 발급한다.
    삭제된 관리자(del_yn='Y')는 로그인 불가.
    """
    # 관리자 조회
    admin = admin_service.get_admin(body.admin_id)
    if not admin:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    # 삭제 여부 확인
    if admin.get("del_yn") == "Y":
        raise HTTPException(status_code=401, detail="비활성화된 계정입니다.")

    # 비밀번호 검증
    if not verify_password(body.password, admin["password"]):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    # 권한 조회
    roles = admin_service.get_admin_roles(body.admin_id)

    # JWT 토큰 생성
    token = create_access_token(body.admin_id, roles)

    return BaseResponse(
        data=LoginResponse(
            access_token=token,
            admin_id=body.admin_id,
            roles=roles,
        ).model_dump(),
        message="로그인 성공",
    )


@router.get("/me", response_model=BaseResponse)
def get_me(current_admin: dict = Depends(get_current_admin)):
    """현재 로그인한 관리자 정보를 반환한다."""
    admin = admin_service.get_admin_safe(current_admin["admin_id"])
    if not admin:
        raise HTTPException(status_code=404, detail="관리자 정보를 찾을 수 없습니다.")
    return BaseResponse(data=admin, message="조회 성공")
