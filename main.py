from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer
from config import get_env
from app.db.connection import db
from app.api import (
    board, user, fantasy, match, call_api_data, test, ranking, main
)
from app.middlewares.trusted_hosts import TrustedHostMiddleware
from app.middlewares.access_control import AccessControl
from starlette.middleware.cors import CORSMiddleware

import uvicorn


# HTTP_BEARER = HTTPBearer(auto_error=False)


def start_app():
    app = FastAPI(debug=True)
    env = get_env()
    db.init_db(app=app, **env.dict())

    origins = env.ORIGINS

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AccessControl)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=env.TRUSTED_HOSTS, except_path=["/"])
    app.include_router(user.user, prefix="/api/user", tags=["User"])
    app.include_router(board.board, prefix="/api/board", tags=["Board"])
    app.include_router(fantasy.fantasy, prefix="/api/fantasy", tags=["Fantasy"])
    app.include_router(match.match, prefix="/api/match", tags=["Match"])
    app.include_router(call_api_data.call_api, prefix="/api/data", tags=["CallAPI"])
    app.include_router(ranking.ranking, prefix="/api/ranking", tags=["Ranking"])
    app.include_router(main, prefix="/api/main", tags=["Main"])

    app.include_router(test.test, prefix="/api/test", tags=["Test"])

    return app


app = start_app()


if __name__ == "__main__":
    uvicorn.run("main:start_app", host="0.0.0.0", port=8000, reload=True, factory=True)