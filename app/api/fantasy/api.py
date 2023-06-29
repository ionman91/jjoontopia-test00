from fastapi import APIRouter, Depends, HTTPException, status
from app.db.connection import db
from sqlalchemy.orm import Session 
from sqlalchemy import desc, asc
from sqlalchemy.sql.expression import case
from app import schemas
from app.models.fantasy import (
    MLBPlayer, MFLPlayer, MLBTeam, MFLTeam, 
)
from app.models.user import User, FLUser, Event
from config import get_env

import json


fantasy = APIRouter()


# 이벤트 목록 불러오기 (추후에나 가능 - 지금은 의미 없음)

"""
    Event >>> sort 를 Column 을 만들어서 어디 이벤트인지 알수 있어야 한다.
            start_event, end_event 항목을 시간으로 만들어서 기간을 설정해야 한다. 
    Event 가 끝났을 경우 어떤식으로 할지 한번 회사에서 생각해보자.
    상속을 하면 될 듯 하고 mfl user , kfl user 이런식으로 나뉠수 있을거 같다. 

    선수를 클릭하면 선수 한달 간의 스탯과 daily score 가 보여진다. 
"""


# 판타지 메인 화면에 들어가면 메인 로스터 선수들 목록이 보여줌 만일 아무런 정보가 없다면 등록을 시킨다.
@fantasy.get("/find_users_main_roster/{sort}/{event_title}/{user_id}", response_model=schemas.UserMainRoster_OUT)
async def find_users_main_roster_api(sort: schemas.FantasyLeagueSort, event_title: str, user_id: int, session: Session = Depends(db.session)):
    event = session.query(Event).filter_by(title=event_title).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="이벤트가 존재하지 않습니다.")
    
    flgame = session.query(FLUser).filter_by(user_id=user_id, sort=sort, event_id=event.id, season=get_env().NOW_SEASON).first()
    if not flgame:
        flgame = FLUser(
            user_id=user_id, season=get_env().NOW_SEASON, event_id=event.id, sort=sort
        )
        session.add(flgame)
        session.commit()
    else:
        if flgame.is_status:
            flgame.now_lineup_json = json.loads(flgame.now_lineup_json)
    return flgame


"""
    만일 예비 엔트리가 없는 상태에서는 메인 엔트리 선수들 목록을 만들어서 보내줘야 한다. 
    is_modified - NONE > 메인 로스터를 그냥 다 복사 하면 됩니다.
    is_modified - PITCHER > 메인 로스터에서 타자만 복사 하면 됩니다.
    is_modified - ALL > 예비 로스터를 그대로 내보내면 됩니다.
"""
# 판타지 예비 로스터 선수들 보여지는 화면
@fantasy.get("/find_users_preliminary_roster/{sort}/{event_title}/{user_id}", response_model=schemas.UserPreliminaryRoster_OUT)
async def find_users_preliminary_roster_api(sort: schemas.FantasyLeagueSort, event_title: str, user_id: int, session: Session = Depends(db.session)):
    event = session.query(Event).filter_by(title=event_title).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="이벤트가 존재하지 않습니다.")
    flgame = session.query(FLUser).filter_by(user_id=user_id, sort=sort, event_id=event.id, season=get_env().NOW_SEASON).first()
    if not flgame:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="항목을 찾을 수가 없습니다.")
    now_lineup = json.loads(flgame.now_lineup_json)
    modified_lineup = json.loads(flgame.modified_lineup_json)
    
    if flgame.modified_status == "NONE":
        flgame.modified_lineup_json = now_lineup
    elif flgame.modified_status == "PTICHER":
        flgame.modified_lineup_json = now_lineup[:9] + modified_lineup
    else:
        flgame.modified_lineup_json = modified_lineup
    return flgame


# 팀들 리스트를 불러온다. (검색)
@fantasy.get("/find_teams_list/{sort}", response_model=list[schemas.MLBTeams_OUT])
async def find_teams_list_api(sort: schemas.FantasyLeagueSort, session: Session = Depends(db.session)):
    if sort == "MLB":
        sorting_teams = case(
            (MLBTeam.division == "East", 1),
            (MLBTeam.division == "Central", 2),
            (MLBTeam.division == "West", 3),
        )
        teams = session.query(MLBTeam).order_by(asc(MLBTeam.conference), sorting_teams).all()
    return teams


# 각 포지션에 맞는 선수들 검색
@fantasy.get("/find_pos_mflplayer/{sort}/{position}/{team}", response_model=list[schemas.MLBPlayers_OUT])
async def find_pos_mflplayer_api(sort: schemas.FantasyLeagueSort, position: schemas.PlayerPosition, team: schemas.MLBTeamList, session: Session = Depends(db.session)):
    if sort == "MLB":
        team = session.query(MLBTeam).filter_by(short_name=team).first()
        players = session.query(MLBPlayer).filter(
            MLBPlayer.team_id == team.id,
            MLBPlayer.is_roster == True
        ).order_by(asc(MLBPlayer.ename))
    if position == "DH":
        players = players.filter(
            MLBPlayer.position != "P"
        )
    elif position in ["RF", "CF", "LF"]:
        players = players.filter(
            MLBPlayer.position.in_(["RF", "CF", "LF", "OF"])
        )
    elif position == "P":
        players = players.filter(
            MLBPlayer.position.in_(["P", "TWP"])
        )
    else:
        players = players.filter(
            MLBPlayer.position == position
        )
    players = players.all()
    return players


# 유저들이 설정한 선수들을 등록한다. 
@fantasy.post("/regist_roster/{sort}/{event_title}/{user_id}")
async def registe_roster_api(sort: schemas.FantasyLeagueSort, event_title: str, user_id: int, d: schemas.RegistMFLPlayer_IN, session: Session = Depends(db.session)):
    regist_players = []
    total_selected_lineup = {}
    is_preliminary_roster = d.is_preliminary_roster

    event = session.query(Event).filter_by(title=event_title).first()
    fluser = session.query(FLUser).filter_by(user_id=user_id, sort=sort, event_id=event.id, season=get_env().NOW_SEASON).first()
    if not fluser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="못찾았어요")
    if fluser and fluser.is_status != is_preliminary_roster:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="메인과 예비 로스터의 관계가 맞지 않습니다. 다시 한번 확인 부탁드립니다.")
    
    batting_positions = ["RF", "LF", "CF", "SS", "2B", "1B", "3B", "DH", "C"]

    for order, data in d.regist_order:
        pos = data.position
        player = session.query(MLBPlayer).filter_by(playerid=data.playerID, is_roster=True).first()
        if not player:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="플레이어가 존재하지 않습니다.")
        
        if pos == "DH":
            if player.position == "P":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="선수 선택이 잘못되었습니다. 다시 한번 확인 부탁드립니다.")
        elif pos in ["RF", "LF", "CF"]:
            if not player.position in ["RF", "LF", "CF", "OF"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="선수 선택이 잘못되었습니다. 다시 한번 확인 부탁드립니다.")
        elif pos == "p":
            if not player.position in ["P", "TWP"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="선수 선택이 잘못되었습니다. 다시 한번 확인 부탁드립니다.")
        elif pos != player.position:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="선수 선택이 잘못되었습니다. 다시 한번 확인 부탁드립니다.")
        
        order_split = order.split("_")[0]
        if order_split == "B":
            if pos in batting_positions:
                batting_positions.remove(pos)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="선수 선택이 잘못되었습니다. 다시 한번 확인 부탁드립니다.")
        
        order_player = {
            "position": pos, "playerID": data.playerID, 
            "ename": player.ename, "kname": player.kname, "average_score": 0.0
        }
        regist_players.append(order_player)

    if not is_preliminary_roster:
        fluser.now_lineup_json = json.dumps(regist_players, ensure_ascii=False)
        fluser.is_status = True
        fluser.selected_players_json = json.dumps(total_selected_lineup, ensure_ascii=False)
    else:
        fluser.modified_lineup_json = json.dumps(regist_players, ensure_ascii=False)
        fluser.modified_status = 'ALL'
    session.add(fluser)
    session.commit()
    return {"status_code": 200}
