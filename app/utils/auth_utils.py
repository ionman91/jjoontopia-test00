from datetime import timedelta, datetime
from datetime import datetime
from config import get_env

import bcrypt
import jwt
import random
import string
import base64
import hmac


def create_token(data: dict, delta: int):
    conf = get_env()
    expire = datetime.utcnow() + timedelta(minutes=delta)
    payload = dict(exp=expire, **data)
    payload["iat"] = datetime.utcnow()
    payload["iss"] = "imizi api"

    return jwt.encode(payload, conf.JWT_SECRET_KEY, algorithm=conf.JWT_ALGORITHM)


def decode_token(token: str):
    conf = get_env()
    try:
        payload = jwt.decode(token, conf.JWT_SECRET_KEY, algorithms=conf.JWT_ALGORITHM)
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
        raise Exception("토큰이 유효하지 않습니다.")


def hash_password(password: str):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def check_password(password: str, existed_password: str):
    return bcrypt.checkpw(password.encode("utf-8"), existed_password.encode("utf-8"))


def is_valid_password(password: str, hashed_password: str):
    try:
        is_verified = bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
        return is_verified
    except Exception:
        return False


def generate_random_string(length: int = 32):
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for i in range(length))


def parse_params_to_str(params: dict):
    url = "?"
    for key, value in params.items():
        url = url + str(key) + "=" + str(value) + "&"
    return url[1:-1]


def hash_string(params: dict, secret_key: str):
    mac = hmac.new(
        bytes(secret_key, encoding="utf8"), bytes(parse_params_to_str(params), encoding="utf-8"), digestmod="sha256"
    )
    digest = mac.digest()
    validating_secret = str(base64.b64encode(digest).decode("utf-8"))
    return validating_secret


def get_current_timestamp():
    return int(datetime.utcnow().timestamp())
