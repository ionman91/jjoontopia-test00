from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from fastapi.encoders import jsonable_encoder
from app import models
from app.db.connection import db
from config import get_env
from starlette import status

import jwt


class AccessControl(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        conf = get_env()

        request.state.user = None
        request.state.exceptions = None
        ip = request.headers["x-forwarded-for"] if "x-forwarded-for" in request.headers.keys() else request.client.host
        request.state.ip = ip.split(",")[0] if "," in ip else ip
        access_token = request.headers.get("Authorization")

        if request.url.path in get_env().EXCEPT_PATH_LIST:
            print("미들웨어를 패스 하고 넘어갑니다.")
            response = await call_next(request)
            return response
        
        if request.url.path.startswith("/api"):
            print("미들웨어를 거칩니다.")
            if access_token:
                access_token = request.headers.get("Authorization").replace("Bearer ", "")
                session = next(db.session())
                print("access_token === ", access_token)
                try:
                    user = jwt.decode(access_token, conf.JWT_SECRET_KEY, algorithms=conf.JWT_ALGORITHM)
                except jwt.ExpiredSignatureError:
                    request.state.exceptions = {"status_code": 900, "msg": "토큰이 만료되었습니다."}
                    return await call_next(request)
                except jwt.InvalidTokenError:
                    request.state.exceptions = {"status_code": status.HTTP_401_UNAUTHORIZED, "msg": "토큰이 유효하지 않습니다."}
                    return await call_next(request)
                print("user ======= ", user)
                if user:
                    exist_user = models.User.get(session, user.get("id"))
                    if not exist_user:
                        request.state.exceptions = {"status_code": status.HTTP_401_UNAUTHORIZED, "msg": "존재하지 않는 유저 입니다."}
                        return await call_next(request)
                    request.state.user = exist_user
                    print("exist_user === ", exist_user)
            else:
                request.state.exceptions = {"status_code": status.HTTP_401_UNAUTHORIZED, "msg": "로그인을 하셔야 합니다."}
        print("user의 마지막 것은 === ", request.state.user)
        response = await call_next(request)
        return response
