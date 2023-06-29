from pydantic import BaseModel
from app.schemas.enum import SelectedMatchResult

"""
    추후에 venue 는 무조건 채워야 하기 때문에 나중에 = None 을 없애줘야 한다. = kname 은 혹시 모르니 냅두자.
"""
class TeamInfo(BaseModel):
    short_name: str
    
    class Config:
        orm_mode=True


class MLBPlayerInfo(BaseModel):
    kname: str = None
    ename: str
    jersey_num: str
    playerid: str
    position: str
    
    class Config:
        orm_mode=True


class PitchingStartForm(BaseModel):
    home: MLBPlayerInfo = None
    away: MLBPlayerInfo = None


class ScheduleMatch_OUT(BaseModel):
    home_team: TeamInfo
    away_team: TeamInfo
    game_date: str
    game_time: str
    home_score: str
    away_score: str
    venue: str = None
    game_status: str
    home_result: str = None
    gameid: str
    pitching_start_json: PitchingStartForm = None

    class Config:
        orm_mode=True


class MatchPredictionForm(BaseModel):
    gameid: str
    predict: SelectedMatchResult

    class Config:
        orm_mode=True


class MatchPrediction_IN(BaseModel):
    game_date: str
    match_prediction: list[MatchPredictionForm]

    class Config:
        orm_mode=True
    
