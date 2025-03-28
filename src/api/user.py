#유저 관리
import requests

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from core.config import Settings
from schema.request import SignUpRequest, LogInRequest
from service.user import UserService, NaverAuthService
from database.repository import UserRepository


router = APIRouter(prefix="/users")

@router.post("/sign-up", status_code=201)
async def user_sign_up_handler(
    request: SignUpRequest,
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    return await user_service.sign_up(request, user_repo)


@router.post("/log-in")
async def user_log_in_handler(
    request: LogInRequest,
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    return await user_service.log_in(request, user_repo)

#-------------------------- 네이버 회원가입 / 로그인 --------------------------
@router.get("/naver")
async def naver_login():
    auth_url = await NaverAuthService.get_auth_url()
    return JSONResponse(content={"auth_url": auth_url})  # Redirect에서 JSON으로 해야함. Front에서 정상적으로 전달안됨.

@router.get("/naver/callback")
async def callback(
    request: Request,
    naver_auth_service: NaverAuthService = Depends(),
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    redirect_url = await naver_auth_service.handle_naver_callback(code, state, user_service, user_repo)

    return RedirectResponse(url=redirect_url)
#------------------------------------------------------------------------

#-------------------------- 구글 회원가입 / 로그인 ---------------------------
@router.get("/google/callback")
def google_callback(code: str):
    token_endpoint = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": Settings.GOOGLE_CLIENT_ID,
        "client_secret": Settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": Settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    r = requests.post(url=token_endpoint, data=data)
#------------------------------------------------------------------------

#-------------------------- 카카오 회원가입 / 로그인 --------------------------

#------------------------------------------------------------------------