from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse

from schema.request import SignUpRequest, LogInRequest
from service.user_service import UserService
from service.auth.social.naver import NaverAuthService
from service.di import ServiceProvider

router = APIRouter(prefix="/users")

@router.post("/sign-up", status_code=201)
async def user_sign_up(
    request: SignUpRequest,
    user_service: UserService = Depends(ServiceProvider.user_service),
):
    return await user_service.sign_up(request)


@router.post("/log-in")
async def user_log_in(
    request: LogInRequest,
    user_service: UserService = Depends(ServiceProvider.user_service),
):
    return await user_service.log_in(request)


# ---------------- 네이버 로그인 ----------------
@router.get("/naver")
async def naver_login(
    naver_auth_service: NaverAuthService = Depends(ServiceProvider.naver_auth_service)
):
    auth_url = await naver_auth_service.get_auth_url()
    return JSONResponse(content={"auth_url": auth_url})


@router.get("/naver/callback")
async def naver_callback(
    request: Request,
    naver_auth_service: NaverAuthService = Depends(ServiceProvider.naver_auth_service),
):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    redirect_url = await naver_auth_service.handle_naver_callback(code, state)
    return RedirectResponse(url=redirect_url)

# ---------------- 구글 로그인(예정) ----------------
