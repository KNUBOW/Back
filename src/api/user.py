#유저 관리
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from schema.request import SignUpRequest, LogInRequest
from database.orm import User
from service.user import UserService, NaverAuthService
from schema.response import UserSchema, JWTResponse
from database.repository import UserRepository
from sqlalchemy.exc import OperationalError


router = APIRouter(prefix="/users")

@router.post("/sign-up", status_code=201)
def user_sign_up_handler(
    request: SignUpRequest,
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    try:
        hashed_password: str = user_service.hash_password(
            plain_password=request.password
        )

        user: User = User.create(
            email=request.email,
            hashed_password=hashed_password,
            name=request.name,
            nickname = request.nickname,
            birth=request.birth,
            gender=request.gender,
        )

        user: User = user_repo.save_user(user=user)

        return UserSchema.model_validate(user)

    except OperationalError as e:
        # 컨테이너 또는 데이터베이스 관련 에러 발생
        raise HTTPException(status_code=500, detail="컨테이너 또는 데이터베이스 관련 오류 발생(docker, mysql 등 확인)")


@router.post("/log-in")
def user_log_in_handler(
        request: LogInRequest,
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
):
    user: User | None = user_repo.get_user_by_email(email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="해당하는 이메일 존재X")

    verified: bool = user_service.verify_password(
        plain_password=request.password,
        hashed_password=user.password,
    )
    if not verified:
        raise HTTPException(status_code=401, detail="인증 실패")

    access_token: str = user_service.create_jwt(email=user.email)

    return JWTResponse(access_token=access_token)

#-------------------------- 네이버 회원가입 / 로그인 --------------------------
@router.get("/naver")
async def naver_login():
    auth_url = await NaverAuthService.get_auth_url()
    return JSONResponse(content={"auth_url": auth_url})  # Redirect에서 JSON으로 해야함. Front에서 정상적으로 전달안됨.

@router.get("/naver/callback")
async def callback(
        request: Request,
        user_repo: UserRepository = Depends(),
        user_service: UserService = Depends(),
):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    #state값 검증
    await NaverAuthService.validate_state(state)

    # 네이버에서 액세스 토큰 요청
    token_response = await NaverAuthService.get_token(code, state)
    access_token = token_response.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="토큰 발급 실패")

    # 액세스 토큰으로 사용자 정보 추출
    user_info = await NaverAuthService.get_user_info(access_token)

    email = user_info.get("response", {}).get("email")
    name = user_info.get("response", {}).get("name")
    nickname = user_info.get("response", {}).get("id")
    gender = user_info.get("response", {}).get("gender")
    birthday = user_info.get("response", {}).get("birthday")
    birthyear = user_info.get("response", {}).get("birthyear")

    # 정보 없을 시 에러 발생
    info_fields = [email, name, nickname, gender, birthday, birthyear]
    if any(field is None for field in info_fields):
        raise HTTPException(status_code=400, detail="사용자 정보 가져오기 실패")

    # 생년월일 형식 보정 (한 자리 숫자 보정)
    birthday = "-".join(part.zfill(2) for part in birthday.split("-"))  # "5-5" → "05-05"
    birth = f"{birthyear}-{birthday}"  # YYYY-MM-DD 형식으로 조합

    # 기존 유저 확인
    user: User | None = user_repo.get_user_by_email(email=email)

    if user:
        # 기존 유저 → 로그인 처리
        token = user_service.create_jwt(email=user.email)  # JWT 토큰 발급
        redirect_url = f"http://프론트엔드서버/auth/success?token={token}" # 파라미터로 token값 전송할 예정        return RedirectResponse(url=redirect_url)

    else:
        # 신규 유저 → 회원가입 처리
        try:
            # 비밀번호는 네이버에서 제공하지 않으므로, 직접 비밀번호를 설정할 수 있거나 생략
            password = secrets.token_urlsafe(12)# 기본 비밀번호 혹은 패스워드 설정 로직 필요
            hashed_password = user_service.hash_password(password)  # 비밀번호 해싱
            # 유저 정보 생성
            user = User(
                email=email,
                hashed_password=hashed_password,  # 기본 비밀번호 사용
                name=name,
                nickname=f"naver_{nickname}",
                birth=birth,
                gender=gender,
                social_auth="N",
            )
            # DB에 저장
            user = user_repo.save_user(user=user)

            # JWT 토큰 발급
            token = user_service.create_jwt(email=user.email)

            # 프론트엔드로 리다이렉트
            redirect_url = f"http://프론트엔드서버/auth/signup?token={token}"
            return RedirectResponse(url=redirect_url)

        except Exception as e:
            raise HTTPException(status_code=500, detail="회원가입 중 오류 발생")

#------------------------------------------------------------------------