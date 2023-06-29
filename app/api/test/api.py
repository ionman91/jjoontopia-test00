from fastapi import APIRouter, Depends
from app import schemas
from sqlalchemy.orm import Session
from app.db.connection import db
from app.models.fantasy import MLBPlayer, MFLPlayer
from app.models.user import User, FLUser, MPUser
from app.models.match import MatchPrediction, MLBMatchSchedule
from config import get_env
from sqlalchemy import asc, not_, desc
from app.utils.utils import (
    date_to_previous_day
)

import random
import json


test = APIRouter()


"""
    fantasy league
    랜덤하게 선택된 플레이어를 만든다.
"""
@test.get("/create_mflplayers", response_model=schemas.RegistMFLPlayer_IN)
async def create_mflplayers_api(session: Session = Depends(db.session)):
    import random
    players_list = {}
    batting_positions = ["RF", "LF", "CF", "SS", "2B", "1B", "3B", "DH", "C"]
    random.shuffle(batting_positions)
    for index, pos in enumerate(batting_positions):
        players = session.query(MLBPlayer).filter_by(position=pos, is_roster=True).all()
        random.shuffle(players)
        player = players[0]
        order = f"B_Order_{index+1}"
        players_list[order] = {
            "position": player.position,
            "playerID": player.playerid
        }
    for index in range(5):
        players = session.query(MLBPlayer).filter_by(position="P", is_roster=True).all()
        random.shuffle(players)
        player = players[0]
        order = f"P_Order_{index+1}"
        players_list[order] = {
            "position": player.position,
            "playerID": player.playerid
        }
    create_players = {
        "is_preliminary_roster": False,
        "regist_order": players_list
    }
    return create_players


"""
    fantasy league
    모든 유저가 랜덤하게 플레이어를 등록한다. 
"""
@test.get("/create_all_users_lineup")
async def create_all_users_lineup_api(session: Session = Depends(db.session)):
    users = session.query(User).filter_by(status="ACTIVE").all()
    update_users_data = []
    update_players_data = []
    
    for user in users:
        fluser = session.query(FLUser).filter_by(user_id=user.id).first()
        insert_players_data = []
        total_selected_player = {}
        batting_positions = ["RF", "LF", "CF", "SS", "2B", "1B", "3B", "DH", "C"]
        random.shuffle(batting_positions)
        for index, pos in enumerate(batting_positions):
            players = session.query(MLBPlayer).filter_by(position=pos, is_roster=True).all()
            random.shuffle(players)
            player = players[0]
            insert_batting_player = {
                "position": player.position, "playerID": player.playerid,
                "ename": player.ename, "kname": player.kname if player.kname else None, "daily_score": 0.0
            }

            # total_selected_player[player.playerid] = 1
            #  for player in player.mflplayer:
            #      if player.season == get_env().NOW_SEASON:
            #          update_player = {
            #              "id": player.id,
            #              "selected_by_user": 1
            #         }
            #         update_players_data.append(update_player) 

            insert_players_data.append(insert_batting_player)
        for index in range(5):
            players = session.query(MLBPlayer).filter_by(position="P", is_roster=True).all()
            random.shuffle(players)
            player = players[0]
            insert_pitching_player = {
                "position": player.position, "playerID": player.playerid,
                "ename": player.ename, "kname": player.kname if player.kname else None, "average_score": 0.0
            }

            # total_selected_player[player.playerid] = 1
            # for player in player.mflplayer:
            #     if player.season == get_env().NOW_SEASON:
            #         update_player = {
            #             "id": player.id,
            #             "selected_by_user": 1
            #         }
            #         update_players_data.append(update_player) 

            insert_players_data.append(insert_pitching_player)
        update_user = {
            "id": fluser.id,
            "now_lineup": json.dumps(insert_players_data, ensure_ascii=False),
            "total_selected_lineup": json.dumps(total_selected_player, ensure_ascii=False),
            "is_status": True
        }
        update_users_data.append(update_user)
    session.bulk_update_mappings(FLUser, update_users_data)
    session.bulk_update_mappings(MFLPlayer, update_players_data)
    session.commit()
    return {"status_code": 200}


"""
    모든 유저에게 mpuser 와 fluser 를 만들어 준다. - 적용 해야 함
"""
@test.get("/create_fluser_mpuser")
async def create_fluser_mpuser_api(session: Session = Depends(db.session)):
    users = session.query(User).filter_by(status="ACTIVE").all()
    for user in users:
        fluser_check = session.query(FLUser).filter_by(user_id=user.id).scalar()
        mpuser_check = session.query(MPUser).filter_by(user_id=user.id).scalar()
        if not fluser_check:
            u = FLUser(
                user_id=user.id, season=get_env().NOW_SEASON, event_id=1, sort="MLB"
            )
            session.add(u)
            session.commit()
        if not mpuser_check:
            u = MPUser(
                user_id=user.id, season=get_env().NOW_SEASON, sort="MLB"
            )
            session.add(u)
            session.commit()
    return {"status_code": 200}


"""
    모든 유저의 데이터를 초기화 시킨다.
"""
@test.get("/delete_fluser_data")
async def delete_fluser_data_api(session: Session = Depends(db.session)):
    update_users_data = []
    users = session.query(FLUser).all()
    for user in users:
        update_user = {
            "id": user.id,
            "daily_score": 0,
            "weekly_score": 0,
            "monthly_score": 0,
            "total_score": 0,
            "daily_scores_json": None,
            "now_lineup_json": None,
            "modified_lineup_json": None,
            "total_selected_lineup": None,
            "average_score": 0,
            "total_games": 0,
            "is_status": 0
        }
        update_users_data.append(update_user)
    session.bulk_update_mappings(FLUser, update_users_data)
    session.commit()
    return {"status_code": 200}


"""
    모든 선수들의 데이터를 초기화 시킨다.
"""
@test.get("/delete_mflplayer_data")
async def delete_mflpalyer_data_api(session: Session = Depends(db.session)):
    update_players_data = []
    players = session.query(MFLPlayer).all()
    for player in players:
        update_player = {
            "id": player.id,
            "daily_score": 0,
            "weekly_score": 0,
            "monthly_score": 0,
            "total_score": 0,
            "score_json": None,
            "stat_json": None,
            "now_stat": None,
            "selected_by_user": 0,
            "difference_score_this_week": 0
        }
        update_players_data.append(update_player)
    session.bulk_update_mappings(MFLPlayer, update_players_data)
    session.commit()
    return {"status_code": 200}


"""
    모든 스케쥴의 데이터를 초기화 시킨다.
"""
@test.get("/delete_schedule_data")
async def delete_schedule_data_api(session: Session = Depends(db.session)):
    update_schedule_list_data = []
    schedule_list = session.query(MLBMatchSchedule).all()
    for schedule in schedule_list:
        update_schedule = {
            "id": schedule.id,
            "home_batting_stat": None,
            "home_pitching_stat": None,
            "home_score_json": None,
            "home_result": None,
            "away_batting_stat": None,
            "away_pitching_stat": None,
            "away_score_json": None,
            "pitching_result": None,
            "home_score": 0,
            "away_0core": 0,
            "game_status": "scheduled",
            "venue": None
        }
        update_schedule_list_data.append(update_schedule)
    session.bulk_update_mappings(MLBMatchSchedule, update_schedule_list_data)
    session.commit()
    return {"status_code": 200}


"""
    match
    해당 date 를 치면 해당 date 에 해당하는 모든 경기의 예상을 랜덤으로 작성해서 내뱉게 된다. 
"""
@test.get("/make_match_prediction_dict/{game_date}")
async def make_match_prediction_dict_api(now_date: str, session: Session = Depends(db.session)):
    update_users_data = []
    game_date = date_to_previous_day(now_date)
    games = session.query(MLBMatchSchedule).filter_by(game_date=game_date).order_by(asc(MLBMatchSchedule.game_time_epoch)).all()
    users = session.query(User).filter_by(status="ACTIVE").all()
    for user in users:
        predict_games = []
        for game in games:
            prediction = {
                "gameid": game.gameid,
                "predict": random.choice(["W", "L"]),
                "result": ""
            }
            predict_games.append(prediction)
        insertUser = {
            "user_id": user.id, 
            "game_date": now_date,
            "predict_json": json.dumps(predict_games, ensure_ascii=False),
            "sort": "MLB"
        }
        update_users_data.append(insertUser)
    session.bulk_insert_mappings(MatchPrediction, update_users_data)
    session.commit()
    
    return {"status_code": 200}


"""
    call_api 에서 test 해보기
"""
@test.get("/asdasdasdasdasd")
async def get_fantasy_weekqergqergqergly_schedule(session: Session = Depends(db.session)):
    from app.models.fantasy import TestTable
    sess_mlb_teams = session.query(TestTable)
    for index in range(7):
        index = 9
        test = sess_mlb_teams.filter_by(id=index).first() is not None
        if not test:
            u = TestTable(
                user_id=13, title="안녕하세요", hello=json.dumps({"0606":"hello"})
            )
            session.add(u)
            session.commit()
    # teams = session.query(MLBTeam).all()
    # for team in teams:
    #     players = session.query(MLBPlayer).filter_by(team_id=team.id, is_roster=True).all()
    #     with open(f"app/api/call_api_data/asd.json", "a") as file:
    #         file.write(f"{team.short_name}의 모든 로스터 선수의 숫자는 {len(players)}명 입니다.\n")
    return {"status_code": 200}

