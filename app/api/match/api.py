from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.db.connection import db
from app.models.match import MLBMatchSchedule, MatchPrediction
from app.models.fantasy import MLBPlayer
from app import schemas

import json


match = APIRouter()


"""
    request 넣어야 한다. 생각해보니 안넣었음.....
"""
# 특정 날짜에 맞춰서 스케쥴을 불러온다.
@match.get("/asd/{sort}", response_model=list[schemas.ScheduleMatch_OUT])
async def call_match_schedule_api(sort: schemas.FantasyLeagueSort, date: str, session: Session = Depends(db.session)):
    if sort == "MLB":
        schedule_list = session.query(MLBMatchSchedule).filter_by(game_date=date).all()
        if not schedule_list:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="잘못된 요청입니다.")
        
        for match in schedule_list:
            if match.pitching_start_json["home"]:
                home_player = session.query(MLBPlayer).filter_by(playerid=match.pitching_start_json["home"]).first()
                away_player = session.query(MLBPlayer).filter_by(playerid=match.pitching_start_json["away"]).first()
                match.pitching_start_json = {
                    "home": home_player,
                    "away": away_player
                }
            else:
                match.pitching_start_json = None
    schedule_list = sorted(schedule_list, key=lambda x: (x.game_time_epoch))            
    return schedule_list


# 승부 예측한 결과가 넘어온다.(등록)
@match.post("/regist_match_prediction/{sort}", response_model=schemas.StatusCode)
async def regist_match_prediction_api(user_id: int, sort: schemas.FantasyLeagueSort, d: schemas.MatchPrediction_IN, session: Session = Depends(db.session)):
    if sort == "MLB":
        games = session.query(MLBMatchSchedule).filter_by(game_date=d.game_date).all()
        if len(games) != len(d.match_prediction):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="승부 예측은 그날 모든 경기를 예측 하셔야 합니다.")
        for predict_game in d.match_prediction:
            exists = session.query(MLBMatchSchedule).filter_by(game_date=d.game_date, gameid=predict_game.gameid).scalar() is not None
            if not exists:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="승부 예측은 그날 모든 경기를 예측 하셔야 합니다.")
    object_to_json = jsonable_encoder(d.match_prediction)
    object_to_json["result"] = ""
    u = MatchPrediction(
        user_id=user_id,
        sort=sort,
        game_date=d.game_date,
        predict_json=json.dumps(object_to_json, ensure_ascii=False)
    )
    session.add(u)
    session.commit()
    return {"status_code": 200}
