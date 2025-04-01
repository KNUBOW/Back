# Redis(비동기 세션 관리 미들웨어)

import json
import redis.asyncio as aioredis

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from itsdangerous import Signer

from core.config import Settings

# Redis 연결
REDIS_URL = f"redis://{Settings.REDIS_HOST}:{Settings.REDIS_PORT}"
redis = None

async def get_redis():
    global redis
    if redis is None:
        redis = await aioredis.from_url(REDIS_URL)
    return redis

class RedisSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str, session_cookie: str = "session_id"):
        super().__init__(app)
        self.signer = Signer(secret_key)
        self.session_cookie = session_cookie

    async def dispatch(self, request: Request, call_next):
        redis = await get_redis()
        session_id = request.cookies.get(self.session_cookie)

        if session_id:
            session_id = self.signer.unsign(session_id).decode()
            session_data = await redis.get(f"session:{session_id}")
            request.state.session = json.loads(session_data) if session_data else {}
        else:
            request.state.session = {}

        response = await call_next(request)

        if request.state.session:
            new_session_id = self.signer.sign(session_id or request.client.host).decode()
            await redis.set(f"session:{new_session_id}", json.dumps(request.state.session), ex=3600)
            response.set_cookie(self.session_cookie, new_session_id, httponly=True, secure=True)

        return response