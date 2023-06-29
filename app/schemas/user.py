from pydantic import BaseModel, EmailStr, validator


class APIKeys_OUT(BaseModel):
    id: int
    access_key: str
    whitelist_ips: str | None

    class Config:
        orm_mode = True


class APIKeysExtend_OUT(APIKeys_OUT):
    secret_key: str


class UserNickname_IN(BaseModel):
    nickname: str

    @validator("nickname")
    def not_emtpy_nickname(cls, v):
        if not v or not v.strip():
            raise ValueError("빈 값이 허용되지 않습니다.")
        return v


class UserLogin_IN(BaseModel):
    email: EmailStr
    pw: str

    @validator("email", "pw")
    def not_emtpy(cls, v):
        if not v or not v.strip():
            raise ValueError("빈 값이 허용되지 않습니다.")
        return v


class UserRegist_IN(UserLogin_IN, UserNickname_IN):
    pw2: str

    @validator("pw2")
    def not_empty_pw2(cls, v):
        if not v or not v.strip():
            raise ValueError("빈 값이 허용되지 않습니다.")
        return v
    
    @validator("pw2")
    def match_password(cls, v, values):
        if "pw" in values and v != values["pw"]:
            raise ValueError("비밀번호가 일치 하지 않습니다.")
        return v

    @validator("pw")
    def verify_password_suitablek(cls, v):
        if len(v) < 8 or len(v) > 20:
            raise ValueError("패스워드의 길이는 8자 보다 길고 20자 보다 짧아야 합니다.")
        if not any(char.isdigit() for char in v):
            raise ValueError("패스워드에 최소한 1개 이상의 숫자가 포함되어야 합니다.")
        if not any(char.isupper() for char in v):
            raise ValueError("패스워드에 최소한 1개 이상의 대문자가 포함되어야 합니다.")
        if not any(char.islower() for char in v):
            raise ValueError("패스워드에 최소한 1개 이상의 소문자가 포함되어야 합니다.")
        return v


class User_OUT(BaseModel):
    id: int
    email: EmailStr
    nickname: str
    status: str
    is_admin: int
    # api_keys: List[APIKeys_OUT] = []

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    refresh_token: str | None


class UserInfo(BaseModel):
    ip: str
    user: User_OUT

    class Config:
        orm_mode = True


class Token_OUT(Token):
    nickname: str


class RefreshToken_IN(BaseModel):
    refresh_token: str
