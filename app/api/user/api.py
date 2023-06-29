from fastapi import APIRouter, Depends, HTTPException, Request
from app.db.connection import db
from sqlalchemy.orm import Session
from app.utils.auth_utils import check_password
from app import schemas, models
from app.utils.auth_utils import (
    decode_token,
    create_token,
)
from starlette import status
from datetime import datetime
from config import get_env


user = APIRouter()


# 유저 닉네임 중복 검사
@user.post("/check-duplicate", response_model=schemas.StatusCode)
async def check_duplicate_nickname_api(d: schemas.UserNickname_IN, session: Session = Depends(db.session)):
    if models.User.get(session, nickname=d.nickname):
        raise HTTPException(status_code=404, detail="이미 존재하는 닉네임 입니다.")
    return {"status_code": 204}


# 유저 등록하기
@user.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.Token_OUT)
async def register_user_api(d: schemas.UserRegist_IN, session: Session = Depends(db.session)):
    if models.User.get(session, email=d.email):
        raise HTTPException(status_code=404, detail="이미 존재하는 이메일 입니다.")
    elif models.User.get(session, nickname=d.nickname):
        raise HTTPException(status_code=404, detail="이미 존재하는 닉네임 입니다.")
    u = models.User(email=d.email, nickname=d.nickname, pw=d.pw)
    session.add(u)
    session.commit()

    return u.get_token()


# 유저 로그인 하기
@user.post("/login", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.Token_OUT)
async def login_user_api(d: schemas.UserLogin_IN, session: Session = Depends(db.session)):
    user = models.User.get(session, email=d.email)
    if not user:
        raise HTTPException(status_code=404, detail="이메일 혹은 비밀번호가 맞지 않습니다.")
    
    is_verified = check_password(d.pw, user.pw)
    if not is_verified:
        raise HTTPException(status_code=404, detail="이메일 혹은 비밀번호가 맞지 않습니다.")

    return user.get_token()


# token refresh
@user.post("/refresh_token", response_model=schemas.Token_OUT)
async def refresh_token_api(d: schemas.RefreshToken_IN, session: Session = Depends(db.session)):
    refresh_payload = decode_token(d.refresh_token)
    exist_user = models.User.get(session, refresh_payload.get("id"))
    if not exist_user:
        raise HTTPException(status_code=404, detail="올바르지 못한 요청입니다.")

    now = int(datetime.utcnow().timestamp())
    if now - refresh_payload["iat"] < get_env().REFRESH_TOKEN_EXPIRE_MINUTES * 60 / 2:
        return {
            "access_token": create_token(
                data=dict(id=exist_user.id, email=exist_user.email, staff=exist_user.is_admin),
                delta=get_env().ACCESS_TOKEN_EXPIRE_MINUTES
            ),
            "refresh_token": d.refresh_token,
            "nickname": exist_user.nickname
        }
    else:
        return exist_user.get_token()


# 유저 구하기
@user.get("/user_info", response_model=schemas.User_OUT)
async def get_user_api(request: Request, session: Session = Depends(db.session)):
    user = models.User.get(session, id=request.state.id)
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 유저입니다.")
    return user