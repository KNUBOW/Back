from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, HTTPException

from exception.auth_exception import UnauthorizedException

#jwt 토큰이 있는지 없는지 체크

def get_access_token(
        auth_header: HTTPAuthorizationCredentials | None = Depends(
            HTTPBearer(auto_error=False))
) -> str:
    if auth_header is None:
        raise UnauthorizedException()
    return auth_header.credentials # access_token

