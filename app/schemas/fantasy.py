from app.models.fantasy import (
    MLBPlayer, MFLPlayer, MLBTeam, MFLTeam
)
from pydantic import BaseModel, validator
from typing import Optional
from config import get_env
from app.schemas.enum import (
    PlayerPosition
)

import json


class UserSelectedMFLPlayerInfo(BaseModel):
    position: PlayerPosition
    playerID: str


class UserSelectedMFLPlayerForm(BaseModel):
    B_Order_1: UserSelectedMFLPlayerInfo
    B_Order_2: UserSelectedMFLPlayerInfo
    B_Order_3: UserSelectedMFLPlayerInfo
    B_Order_4: UserSelectedMFLPlayerInfo
    B_Order_5: UserSelectedMFLPlayerInfo
    B_Order_6: UserSelectedMFLPlayerInfo
    B_Order_7: UserSelectedMFLPlayerInfo
    B_Order_8: UserSelectedMFLPlayerInfo
    B_Order_9: UserSelectedMFLPlayerInfo
    P_Order_1: UserSelectedMFLPlayerInfo
    P_Order_2: UserSelectedMFLPlayerInfo
    P_Order_3: UserSelectedMFLPlayerInfo
    P_Order_4: UserSelectedMFLPlayerInfo
    P_Order_5: UserSelectedMFLPlayerInfo
    

class RegistMFLPlayer_IN(BaseModel):
    is_preliminary_roster: bool
    regist_order: UserSelectedMFLPlayerForm


class SelectedMFLPlayer(BaseModel):
    position: PlayerPosition
    playerID: str
    daily_score: float
    ename: str
    kname: str = None

    class Config:
        orm_mode=True


class EventTitleForm(BaseModel):
    title: str

    class Config:
        orm_mode=True


class UserMainRoster_OUT(BaseModel):
    daily_score: float
    weekly_score: float
    monthly_score: float
    total_score: float
    average_score: float
    total_games: int
    now_lineup_json: list[SelectedMFLPlayer] = None
    event: EventTitleForm

    class Config:
        orm_mode=True


class UserPreliminaryRoster_OUT(BaseModel):
    daily_score: float
    weekly_score: float
    monthly_score: float
    total_score: float
    average_score: float
    total_games: int
    modified_lineup_json: list[SelectedMFLPlayer] = None
    event: EventTitleForm

    class Config:
        orm_mode=True   


class MLBTeamName(BaseModel):
    short_name: str

    class Config:
        orm_mode=True


class MFLPlayerStat(BaseModel):
    weekly_score: float = 0
    now_stat: dict = None

    def json_decode(self):
        return json.loads(self.now_stat)

    class Config:
        orm_mode=True


class MLBPlayers_OUT(BaseModel):
    kname: str = None
    ename: str
    jersey_num: str = None
    position: str
    playerid: str
    mlbteam: MLBTeamName
    mflplayer: list[MFLPlayerStat]

    def get_mflplayer(self):
        return [player for player in self.mflplayer if player.season == get_env().NOW_SEASON]
    
    class Config:
        orm_mode=True


class MLBTeams_OUT(BaseModel):
    short_name: str
    kname: str = None
    division: str
    conference: str

    class Config:
        orm_mode=True

