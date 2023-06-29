from app.models.base import Base
from app.models.board import Comment, Post, Series, Recommend
from sqlalchemy import (
    Column, String, ForeignKey, Enum, Boolean, Integer, 
    DateTime, Float, JSON, DECIMAL
)
from sqlalchemy.orm import relationship, Session
from app.utils.auth_utils import (
    generate_random_string, 
    hash_password, 
    create_token,
)
from config import get_env
from datetime import datetime, timedelta

import enum
import json


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    STOP = "STOP"
    DELETED = "DELETED"


class UserGrade(str, enum.Enum):
    USER0 = "normal"


class LineupStatus(str, enum.Enum):
    ALL = "ALL"
    PITCHER = "PITCHER"
    NONE = "NONE"


class Event(Base):
    __tablename__ = "event"
    user_id = Column(ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    info = Column(String, nullable=True)
    period = Column(String, nullable=True)
    is_status = Column(Boolean, nullable=False, default=True)

    participant = relationship("FLUser", back_populates="event")


class User(Base):
    __tablename__ = "users"
    email = Column(String(64), nullable=False, unique=True)
    nickname = Column(String(64), nullable=False, unique=True)
    pw = Column(String(256), nullable=False)
    total_point = Column(Integer, nullable=False, default=0)
    now_point = Column(Integer, nullable=False, default=0)
    grade = Column(Enum(UserGrade, native_enum=False, length=50), nullable=False, default=UserGrade.USER0)
    
    status = Column(Enum(UserStatus, native_enum=False, length=50), nullable=False, default=UserStatus.ACTIVE) # 유저 상태
    is_admin = Column(Boolean, nullable=False, default=False)

    api_keys = relationship("APIKeys", back_populates="user")
    posts = relationship("Post", back_populates="writer", foreign_keys=[Post.user_id])
    comments = relationship("Comment", back_populates="writer", foreign_keys=[Comment.user_id])
    series_list = relationship("Series", back_populates="writer", foreign_keys=[Series.user_id])
    recommends = relationship("Recommend", back_populates="writer", foreign_keys=[Recommend.user_id])
    flgame = relationship("FLUser", back_populates="writer")
    mpgame = relationship("MPUser", back_populates="writer")
    match_predict = relationship("MatchPrediction", back_populates="writer")

    def __init__(self, email, nickname, pw):
        print("email==", email, "nickname==", nickname, "pw==", pw)
        self.email = email
        self.nickname = nickname
        self.pw = hash_password(pw)

    @classmethod
    def get(cls, session: Session, id: int = None, **kwargs):
        if id:
            return session.query(cls).filter_by(id=id, **kwargs).first()
        return session.query(cls).filter_by(**kwargs).first()
    
    @classmethod
    def update(cls, session: Session, id: int, **kwargs):
        session.query(cls).filter_by(id=id).update(**kwargs)
        session.commit()

    def get_token(self):
        return {
            "access_token": create_token(
                data=dict(id=self.id, email=self.email, staff=self.is_admin),
                delta=get_env().ACCESS_TOKEN_EXPIRE_MINUTES,
            ),
            "refresh_token": create_token(
                data=dict(id=self.id),
                delta=get_env().REFRESH_TOKEN_EXPIRE_MINUTES,
            ),
            "nickname": self.nickname
        }

    def add_points(self, point):
        self.now_point += point
    
    def subtract_points(self, point):
        self.now_point -= point


# fantasy league user
class FLUser(Base):
    __tablename__ = "users_fantasy_league"
    user_id = Column(ForeignKey("users.id"), nullable=False)
    event_id = Column(ForeignKey("event.id"), nullable=False)
    sort = Column(Enum("MLB", "KBO"), nullable=False) # string(10)
    season = Column(String(4), nullable=False, default=get_env().NOW_SEASON)

    daily_score = Column(DECIMAL(4,1), nullable=False, default=0.0)
    weekly_score = Column(DECIMAL(4,1), nullable=False, default=0.0)
    monthly_score = Column(DECIMAL(5,1), nullable=False, default=0.0)
    total_score = Column(DECIMAL(5,1), nullable=False, default=0.0)
    average_score = Column(DECIMAL(4,1), nullable=False, default=0.0)
    total_games = Column(Integer, nullable=False, default=0)

    daily_scores_json = Column(JSON, nullable=True)
    now_lineup_json = Column(JSON, nullable=True)
    modified_lineup_json = Column(JSON, nullable=True)
    selected_players_json = Column(JSON, nullable=True)
    
    is_status = Column(Boolean, nullable=False, default=False)
    modified_status = Column(Enum(LineupStatus, native_enum=False, length=50), nullable=False, default=LineupStatus.NONE) # 유저 상태

    writer = relationship("User", back_populates="flgame", foreign_keys=[user_id], uselist=False)
    event = relationship("Event", back_populates="participant", foreign_keys=[event_id], uselist=False)

    def add_total_score(self, today_score):
        today_score = round(today_score, 1)
        week_score = 0
        month_score = 0
        # now = datetime.now()
        # today = now.strftime("%m") + now.strftime("%d")
        today = get_env().TODAY
        collect_score = {}
        if self.daily_scores_json:
            collect_score = json.loads(self.daily_scores_json)
            for i in range(1, 30):
                # go_past = now + timedelta(days=-i)
                hehe = get_env().DATETIME_TODAY
                go_past = hehe + timedelta(days=-i)
                day = go_past.strftime("%m") + go_past.strftime("%d")
                if day in collect_score:
                    if i <= 6:
                        week_score += collect_score[day]
                    month_score += collect_score[day]
            collect_score[today] = today_score
            self.daily_score = today_score
            self.weekly_score = week_score + today_score
            self.monthly_score = month_score + today_score
            self.total_score += today_score
            self.total_games += 1
            self.average_score = round(self.total_score / self.total_games, 1)
            self.daily_scores_json = json.dumps(collect_score, ensure_ascii=False)
        else:
            collect_score[today] = today_score
            self.daily_score = today_score
            self.weekly_score = today_score
            self.monthly_score = today_score
            self.total_score = today_score
            self.average_score = today_score
            self.total_games = 1
            self.daily_scores_json = json.dumps(collect_score, ensure_ascii=False)


# match prediction match user
class MPUser(Base):
    __tablename__ = "users_match_prediction"
    user_id = Column(ForeignKey("users.id"), nullable=False)
    sort = Column(Enum("KBO", "MLB"), nullable=False)
    season = Column(String, nullable=False, default=get_env().NOW_SEASON)
    
    total_games = Column(Integer, nullable=False, default=0)
    total_win = Column(Integer, nullable=False, default=0)
    total_win_rate = Column(DECIMAL(3,1), nullable=False, default=0.0)

    predict_history_json = Column(JSON, nullable=True)
    is_status = Column(Boolean, nullable=False, default=True)

    writer = relationship("User", back_populates="mpgame", foreign_keys=[user_id], uselist=False)


class APIKeys(Base):
    __tablename__ = "users_api_keys"
    user_id = Column(ForeignKey("users.id"), nullable=False)
    access_key = Column(String(64), nullable=False)
    secret_key = Column(String(64), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="api_keys")
    whitelist = relationship("APIKeysWhitelist", back_populates="api_keys")

    def __init__(self, user_id):
        self.user_id = user_id
        self.access_key = generate_random_string(24)
        self.secret_key = generate_random_string()

    def add(self, session: Session):
        prev_issued = session.query(APIKeys).filter_by(user_id=self.user_id, deleted_at=None).all()
        if len(prev_issued) >= 3:
            return False
        session.add(self)
        session.commit()
        return self

    @classmethod
    def get_api_key(cls, access_key: str, session: Session):
        get_api_key = session.query(cls).filter_by(access_key=access_key, deleted_at=None).first()
        return get_api_key



class APIKeysWhitelist(Base):
    __tablename__ = "users_api_keys_whitelist"
    api_key_id = Column(ForeignKey("users_api_keys.id"), nullable=False)
    ip = Column(String(64), nullable=False)

    api_keys = relationship("APIKeys", back_populates="whitelist")

    @classmethod
    def has_up(cls, api_key_id: int, ip: str, session: Session) -> bool:
        if not session.query(cls).filter_by(api_key_id=api_key_id).first():
            return True
        return session.query(cls).filter_by(ip=ip, api_key_id=api_key_id).first() is not None
