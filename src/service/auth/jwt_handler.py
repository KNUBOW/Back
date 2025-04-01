#jwt 토큰이 있는지 없는지 체크

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, HTTPException

def get_access_token(
        auth_header: HTTPAuthorizationCredentials | None = Depends(
            HTTPBearer(auto_error=False))
) -> str:
    if auth_header is None:
        raise HTTPException(
            status_code=401,
            detail="jwt 토큰 없음",    #인증 안된 상태
        )
    return auth_header.credentials # access_token

