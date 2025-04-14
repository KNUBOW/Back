from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse

from schema.request import SignUpRequest, LogInRequest, PasswordChangeRequest
from service.auth.jwt_handler import get_access_token
from service.auth.social.google import GoogleAuthService
from service.user_service import UserService
from service.auth.social.naver import NaverAuthService
from dependencies.di import (
    get_user_service,
    get_google_auth_service,
    get_naver_auth_service
)

#유저 관련 라우터

router = APIRouter(prefix="/users", tags=["User"])

@router.post("/sign-up", status_code=201)
async def user_sign_up(
    request: SignUpRequest,
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.sign_up(request)

@router.post("/log-in")
async def user_log_in(
    request: LogInRequest,
    req: Request,
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.log_in(request, req)

@router.patch("/change-password", status_code=204)
async def change_password(
    request: PasswordChangeRequest,
    access_token: str = Depends(get_access_token),
    req: Request = None,
    user_service: UserService = Depends(get_user_service),
):
    current_user = await user_service.get_user_by_token(access_token, req)

    await user_service.change_password(
        user=current_user,
        current_password=request.current_password,
        new_password=request.new_password,
        confirm_new_password=request.confirm_new_password
    )
# ---------------- 네이버 로그인 ----------------
@router.get("/naver")
async def naver_login(
    naver_auth_service: NaverAuthService = Depends(get_naver_auth_service),
):
    auth_url = await naver_auth_service.get_auth_url()
    return JSONResponse(content={"auth_url": auth_url})

@router.get("/google")
async def google_login(
    google_auth_service: GoogleAuthService = Depends(get_google_auth_service),
):
    auth_url = await google_auth_service.get_auth_url()
    return JSONResponse(content={"auth_url": auth_url})

@router.get("/naver/callback")
async def naver_callback(
    request: Request,
    code: str = None,
    state: str = None,
    naver_auth_service: NaverAuthService = Depends(get_naver_auth_service),
):
    redirect_url = await naver_auth_service.handle_naver_callback(code, state, request)
    return RedirectResponse(url=redirect_url)
# ---------------- 구글 로그인 ----------------

@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = None,
    state: str = None,
    google_auth_service: GoogleAuthService = Depends(get_google_auth_service)
):

    redirect_url = await google_auth_service.handle_google_callback(code, state, request)
    return RedirectResponse(url=redirect_url)