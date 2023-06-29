from os import path
from platform import system
from typing import Optional
from pydantic import BaseSettings

import os


class Settings(BaseSettings):
    BASE_DIR: str = path.dirname((path.abspath(__file__)))
    LOCAL_MODE: bool = (
        True if system().lower().startswith("darwin") or system().lower().startswith("Windows") else False
    )
    app_name: str = "Hello"
    TEST_MODE: bool = False

    ALLOW_SITE = ["127.0.0.1:5173", "*"]
    TRUSTED_HOSTS = ["127.0.0.1:5173","*"]
    JWT_ALGORITHM = "HS256"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET", "hello")
    ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*1
    REFRESH_TOKEN_EXPIRE_MINUTES = 60*24*1
    """ 추가 부분 시작 """
    PAGING_LIMIT = 3
    MIN_CONDITION_BEST = 2
    EXCEPT_PATH_LIST = ["/api/user/login", "/api/user/register", "/api/user/refresh_token"]
    EXCEPT_PATH_REGEX = ""

    RAPID_MLB_BASIC_URL = "https://tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com/"
    RAPID_MLB_AUTH_NAME = "jjoontopia_mlb"
    RAPID_MLB_API_KEY = "75c005dfeamsh89423cd28293c0ep1331c3jsn162b10ffc369"
    RAPID_MLB_HEADERS = {
        "X-RapidAPI-Key": RAPID_MLB_API_KEY,
        "X-RapidAPI-Host": "tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"
    }
    BASEBALL_SCORE_SETTING = {
        "pitching": {
            "BB": -1,
            "H": -1,
            "HR": -1,
            "ER": -1,
            "InningsPitched": 3,
            "SO": 1,
        },
        "hitting": {
            "BB": 1,
            "TB": 1,
            "GIDP": -2,
            "SF": 1,
            "HBP": 1,
            "Outfield_assists": 2,
            "E": -1,
            "CS": -1, # 도루 실패
            "SB": 1, # 도루 성공
            "RBI": 1.5
        } 
    }
    BASEBALL_SCORE_RATIO = [
        1.3, 1.5, 1.5, 1.5, 1.3, 1.3, 1.0, 1.0, 1.0, # 타자 타순대로
        1.5, 1.5, 1.3, 1.3, 1.0 # 투수 순서대로
    ]
    """
        애런저지, 오타니, 김하성, 배지환, 요시다
    """
    MAIN_PLAYER_LIST = ["aaron-judge-592450", "shohei-ohtani-660271", "ha-seong-kim-673490", "ji-hwan-bae-678225", "masataka-yoshida-807799"]

    NOW_SEASON = "2023"
    START_DAY = "20230601"

    GAME_TODAY = "20230606"
    TODAY = "0607"
    from datetime import datetime
    DATETIME_TODAY = datetime(2023, 6, 8)
    """ 추가 부분 끝 """
    DB_URL: str = ""
    DB_POOL_RECYCLE: Optional[int] = 900
    DB_ECHO: Optional[bool] = True
    DB_POOL_SIZE: Optional[int] = 1
    DB_MAX_OVERFLOW: Optional[int] = 1


class DevSettings(Settings):
    DB_URL = "mysql+pymysql://root:1234@localhost:3306/test2?charset=utf8mb4"
    DB_POOL_SIZE = 5
    DB_MAX_OVERFLOW = 10


def get_env():
    cfg_cls = dict(
        dev=DevSettings,
    )
    env = cfg_cls[os.getenv("FASTAPI_ENV", "dev")]()

    return env

settings = get_env()
