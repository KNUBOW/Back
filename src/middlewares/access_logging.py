#백엔드 서버에 접근한 IP 로그

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from time import time
from core.logging import loggers

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time()
        response: Response = await call_next(request)
        duration = round(time() - start_time, 4)

        loggers["access"].info(
            f"{request.client.host} {request.method} {request.url.path} "
            f"-> {response.status_code} [{duration}s]"
        )

        return response
