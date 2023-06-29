from fastapi import APIRouter, Depends, HTTPException, Request, status
from config import get_env
from sqlalchemy.orm import Session
from app.db.connection import db
from datetime import datetime, timedelta

from app.models.fantasy import (
    MLBTeam, MLBPlayer, MFLTeam, MFLPlayer, TestTable
)
from app.models.user import FLUser, MPUser
from app.models.match import MLBMatchSchedule, MatchPrediction
from app.utils.call_api_utils import (
    mlb_today_box_score, mlb_daily_schedule_list, mlb_player_list,
    mlb_team_list, mlb_team_schedule_list, mlb_team_roster, 
    mlb_player_find_info
)
from app.utils.utils import check_valid_request, keys_to_remove
from app import schemas

import json


call_api = APIRouter()


"""
    1. 내일 나머지 일자 받아오기(match)
    2. 가장 상위 10명 가장 하위 10명 놔두는거 재미있겠다. (나중에 대회도 가장 높은 거 뽑기, 가장 낮은거 뽑기 하자. 대회 참가 신청을)
    3. team 도 점수로 매겨서 만들기
    4. 선수들이 픽한거 점수 업데이트 하기
    5. 유저들이 넣어뒀던 서브 라인업 적용
    6. 프론트 엔드 쪽 적용

    만일 이후에 반복되는 for 문이 있다면 미리 session 을 불러와서 좀 더 효율적으로 작업 할 수 있게끔 하자.
"""
@call_api.get("/get_fantasy_team_list", response_model=schemas.StatusCode)
async def get_fantasy_team_list_api(request: Request, session: Session = Depends(db.session)):
    # req = check_valid_request(request)
    # if not req.user.is_admin:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="관리자만 할 수 있습니다.")

    mflteams_list = []
    response = mlb_team_list()
    teams = response["body"]
    
    for team in teams:
        team_exists = session.query(MLBTeam).filter_by(team_name=team["teamName"], short_name=team["teamAbv"], teamid=team["teamID"]).scalar() is not None
        if not team_exists:
            mlbteam = MLBTeam(
                team_name=team["teamName"], city_name=team["teamCity"], 
                short_name=team["teamAbv"], teamid=team["teamID"], 
                division=team["division"], conference=team["conferenceAbv"]
            )
            session.add(mlbteam)
            session.commit()

            mflteam = {
                "team_id":mlbteam.id, "season":get_env().NOW_SEASON, "short_name": team["teamAbv"]
            }
            mflteams_list.append(mflteam)
        else:
            mlbteam = session.query(MLBTeam).filter_by(team_name=team["teamName"], short_name=team["teamAbv"], teamid=team["teamID"]).first()
            
            exists_mfl_team = session.query(MFLTeam).filter(MFLTeam.season==get_env().NOW_SEASON, MFLTeam.mlbteam.has(id=mlbteam.id, teamid=team["teamID"])).scalar()
            if not exists_mfl_team:
                mflteam = {
                    "team_id":mlbteam.id, "season":get_env().NOW_SEASON, "short_name": team["teamAbv"]
                }
                mflteams_list.append(mflteam)
    session.bulk_insert_mappings(MFLTeam, mflteams_list)
    session.commit()
    return {"status_code": 200}


@call_api.get("/get_fantasy_player_list", response_model=schemas.StatusCode)
async def get_fantasy_player_list_api(request: Request, session: Session = Depends(db.session)):
    # req = check_valid_request(request)
    # if not req.user.is_admin:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="관리자만 할 수 있습니다.")

    mflplayers = []
    response = mlb_player_list()
    players = response["body"]
    
    for player in players:
        exists = session.query(MLBPlayer).filter_by(ename=player["longName"], playerid=player["playerID"]).scalar() is not None
        if not exists:
            team = session.query(MLBTeam).filter_by(short_name=player["team"]).first().id if player["team"] else None
            # team_id = get_mlb_team_id(player["team"]) if player["team"] else None

            mlbplayer = MLBPlayer(
                team_id=team, ename=player["longName"], playerid=player["playerID"], 
                mlbid=player["mlbID"], bday=player["bDay"], jersey_num=player["jerseyNum"], 
                position=player["pos"]
            )
            session.add(mlbplayer)
            session.commit()

            mflplayer = {
                "player_id":mlbplayer.id, "season":get_env().NOW_SEASON, "playerid":player["playerID"]
            }
            mflplayers.append(mflplayer)
        else:
            mlbplayer = session.query(MLBPlayer).filter_by(ename=player["longName"], playerid=player["playerID"]).first()
            
            exists_mfl_player = session.query(MFLPlayer).filter_by(player_id=mlbplayer.id, playerid=player["playerID"]).scalar()
            if not exists_mfl_player:
                mflplayer = {
                    "player_id":mlbplayer.id, "season":get_env().NOW_SEASON, "playerid":player["playerID"]
                }
                mflplayers.append(mflplayer)
    session.bulk_insert_mappings(MFLPlayer, mflplayers)
    session.commit()
    return {"status_code": 200}


"""
    22시 40분 - 하루에 한번씩 팀 로스터를 불러와야 한다. (바뀌는 경우가 있음)
    팀 로스터를 저장한다.
"""
@call_api.get("/get_fantasy_team_roster", response_model=schemas.StatusCode)
async def get_fantasy_team_roster_api(request: Request, session: Session = Depends(db.session)):
    # req = check_valid_request(request)
    # if not req.user.is_admin:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="관리자만 할 수 있습니다.")

    insert_players = []
    update_players = []
    teams = session.query(MLBTeam).all()
    for team in teams:
        team_roster_playersID_list = []

        response = mlb_team_roster(team.short_name)
        roster_players = response["body"]["roster"]
        for roster_player in roster_players:
            team_roster_playersID_list.append(roster_player["playerID"])
            player = session.query(MLBPlayer).filter_by(playerid=roster_player["playerID"]).first()
            if not player:
                mlbplayer = MLBPlayer(
                    team_id=team.id, ename=roster_player["longName"], playerid=roster_player["playerID"], 
                    mlbid=roster_player["mlbID"], bday=roster_player["bDay"], jersey_num=roster_player["jerseyNum"], 
                    position=roster_player["pos"]
                )
                session.add(mlbplayer)
                session.commit()

                mflplayer = {
                    "player_id":mlbplayer.id, "season":get_env().NOW_SEASON, "playerid":roster_player["playerID"]
                }
                insert_players.append(mflplayer)
            else:
                if player.team_id != team.id:
                    update_mlb_player = {
                        "id": player.id,
                        "team_id": team.id,
                        "is_roster": True,
                        "updated_at": datetime.now()
                    }
                    update_players.append(update_mlb_player)
                elif not player.is_roster:
                    update_mlb_player = {
                        "id": player.id,
                        "is_roster": True,
                        "updated_at": datetime.now()
                    }
                    update_players.append(update_mlb_player)         
        not_exists_team_roster = session.query(MLBPlayer).filter(~MLBPlayer.playerid.in_(team_roster_playersID_list), MLBPlayer.is_roster==True, MLBPlayer.team_id==team.id).all()
        for player in not_exists_team_roster:
            update_mlb_player = {
                "id": player.id,
                "is_roster": False,
                "updated_at": datetime.now()
            }
            update_players.append(update_mlb_player)
    session.bulk_insert_mappings(MFLPlayer, insert_players)
    session.bulk_update_mappings(MLBPlayer, update_players)
    session.commit()
    return {"status_code": 200}


"""
    팀 스케쥴을 찾아서 가지고 온다. (모든 경기)
"""
@call_api.get("/get_fantasy_team_schedule", response_model=schemas.StatusCode)
async def get_fantasy_team_schedule_api(request: Request, session: Session = Depends(db.session)):
    # req = check_valid_request(request)
    # if not req.user.is_admin:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="관리자만 할 수 있습니다.")

    teams = session.query(MLBTeam).all()
    for team in teams:
        team_name = team.short_name
        response = mlb_team_schedule_list(team_name)
        schedule_list = response["body"]["schedule"]

        for data in schedule_list:
            exists = session.query(MLBMatchSchedule).filter_by(gameid=data["gameID"]).scalar() is not None
            if not exists:
                if data["home"] == team_name:
                    home_team = team
                else:
                    home_team = session.query(MLBTeam).filter_by(short_name=data["home"]).first()
                    # home_team_id = get_mlb_team_id(data["home"])
                
                if data["away"] == team_name:
                    away_team = team
                else:
                    away_team = session.query(MLBTeam).filter_by(short_name=data["away"]).first()
                    # away_team_id = get_mlb_team_id(data["away"])
                pitching_start = data["probableStartingPitchers"] if "probableStartingPitchers" in data else {"away":"","home":""}

                match = MLBMatchSchedule(
                    home_id=home_team.id, away_id=away_team.id, gameid=data["gameID"], 
                    game_date=data["gameDate"], venue=home_team.estadium,
                    game_time=data["gameTime"], game_time_epoch=data["gameTime_epoch"],
                    pitching_start_json=pitching_start, game_status=data["gameStatus"]
                )
                session.add(match)
                session.commit()
    return {"status_code": 200}


"""
    22시 50분
    앞으로 있을 일주일 경기를 가지고 온다. 
    (경기 취소로 인한 더블 헤더 추가와 예상 투수 라인업이 바뀌었는지 확인한다.)
"""
@call_api.get("/get_fantasy_weekly_schedule", response_model=schemas.StatusCode)
async def get_fantasy_weekly_schedule_api(session: Session = Depends(db.session)):
    update_matchs_data = []
    insert_matchs_data = []
    today = datetime.now()
    for i in range(7):
        day = datetime(2023, 6, 14) + timedelta(days=i)
        response = mlb_daily_schedule_list(f"{day.strftime('%m')}{day.strftime('%d')}")
        schedule_list = response["body"]
        for match in schedule_list:
            game = session.query(MLBMatchSchedule).filter_by(gameid=match["gameID"]).first()

            pitching_start = match["probableStartingPitchers"] if "probableStartingPitchers" in match else {"away":"","home":""}
            if game:
                update_match = {"id": game.id}
                if game.game_time_epoch != match["gameTime_epoch"]:
                    update_match["game_time"] = match["gameTime"]
                    update_match["game_time_epoch"] = match["gameTime_epoch"]
                if game.pitching_start_json["home"] != pitching_start["home"] or game.pitching_start_json["away"] != pitching_start["away"]:
                    pitching_start = {
                        "home": pitching_start["home"],
                        "away": pitching_start["away"]
                    }
                    update_match["pitching_start_json"] = pitching_start
                if ("game_time" in update_match) or ("pitching_start" in update_match): 
                    update_match["updated_at"] = datetime.now()
                    update_matchs_data.append(update_match)
            else:
                home_team = session.query(MLBTeam).filter_by(short_name=match["home"]).first()
                away_team = session.query(MLBTeam).filter_by(short_name=match["away"]).first()
                # home_team_id = get_mlb_team_id(match["home"])
                # away_team_id = get_mlb_team_id(match["away"])
                
                new_match = {
                    "home_id":home_team.id, "away_id":away_team.id, 
                    "gameid":match["gameID"], "game_date":match["gameDate"], 
                    "game_time":match["gameTime"], "game_time_epoch":match["gameTime_epoch"], 
                    "venue":home_team.estadium, "pitching_start_json":pitching_start,
                }
                insert_matchs_data.append(new_match)
    if update_matchs_data:            
        session.bulk_update_mappings(MLBMatchSchedule, update_matchs_data)
    if insert_matchs_data:
        session.bulk_insert_mappings(MLBMatchSchedule, insert_matchs_data)
    session.commit()    
    return {"status_code": 200}


"""
    23시 00분
    오늘 경기를 결과를 불러와서 저장을 한다.
    - 경기 결과를 업데이트 한다. 
    - mflplayer 에 오늘 경기 스켓 결과를 점수화 해서 업데이트 한다.
"""
@call_api.get("/get_fantasy_box_score", response_model=schemas.StatusCode)
async def get_fantasy_box_score_api(session: Session = Depends(db.session)):
    matchs = []
    players = []
    
    day = datetime.now() + timedelta(days=-1)
    game_date = f"{get_env().NOW_SEASON}{day.strftime('%m')}{day.strftime('%d')}"
    game_date = get_env().GAME_TODAY
    today_games = session.query(MLBMatchSchedule).filter_by(game_date=game_date).all()

    for game in today_games:
        home_batting_stat = []
        home_pitching_stat = []
        away_batting_stat = []
        away_pitching_stat = []

        response = mlb_today_box_score(game.gameid)
        match_data = response["body"]

        if match_data["gameStatus"] == "Completed":
            players_data = match_data["playerStats"]
            home_team = game.home_team.short_name

            for player_id, player_data in players_data.items():
                player = session.query(MFLPlayer).filter_by(playerid=player_id).first()
                if not player:
                    response = mlb_player_find_info(player_id)
                    info = response["body"]
                    player_team = session.query(MLBTeam).filter_by(short_name=info["team"]).first()
                    u = MLBPlayer(
                        team_id=player_team.id, ename=info["longName"], playerid=info["playerID"], 
                        mlbid=info["mlbID"], bday=info["bDay"], jersey_num=info["jerseyNum"], 
                        position=info["pos"], is_roster=True
                    )
                    session.add(u)
                    session.commit()

                    player = MFLPlayer(
                        player_id=u.id, season=get_env().NOW_SEASON, playerid=u.playerid
                    )
                    session.add(player)
                    session.commit()

                player_name = {"playerNameE": player.mlbplayer.ename, "playerNameK": player.mlbplayer.kname}
                player_pos = player_data["allPositionsPlayed"]
                divide_player_pos = player_pos.split("-")

                if len(divide_player_pos) >= 2 and "P" in divide_player_pos:
                    make_player_stat = {player_id: {**player_data, **player_name}}

                    p_score = player.calculate_hitter_score(player_data)
                    h_score = player.calculate_pitcher_score(player_data)
                    player.add_total_score(p_score + h_score)
                    player.add_player_game_stat(player_data, "pitcher_hitter")

                    if player_data["team"] == home_team:
                        home_pitching_stat.append(make_player_stat)
                        home_batting_stat.append(make_player_stat)
                    else:
                        away_pitching_stat.append(make_player_stat)
                        away_batting_stat.append(make_player_stat)
                
                elif player_pos == "P":
                    keys_to_remove(player_data, ["Hitting", "Baserunning", "Fielding"])
                    make_player_stat = {player_id: {**player_data, **player_name}}
                    
                    p_score = player.calculate_pitcher_score(player_data)
                    player.add_total_score(p_score)
                    player.add_player_game_stat(player_data, "pitcher")

                    if player_data["team"] == home_team:
                        home_pitching_stat.append(make_player_stat)
                    else:
                        away_pitching_stat.append(make_player_stat)
                
                else:
                    keys_to_remove(player_data, ["Pitching"])
                    make_player_stat = {player_id: {**player_data, **player_name}}

                    h_score = player.calculate_hitter_score(player_data)
                    player.add_total_score(h_score)
                    player.add_player_game_stat(player_data, "hitter")

                    if player_data["team"] == home_team:
                        home_batting_stat.append(make_player_stat)
                    else:
                        away_batting_stat.append(make_player_stat)

                player_update_data = {
                    "id": player.id
                }
                players.append(player_update_data)

            home_batting_stat = sorted(home_batting_stat, key=lambda x: (list(x.values())[0]["Hitting"]["battingOrder"], list(x.values())[0]["Hitting"]["substitutionOrder"]))
            home_pitching_stat = sorted(home_pitching_stat, key=lambda x: (list(x.values())[0]["Pitching"]["pitchingOrder"]))
            away_batting_stat = sorted(away_batting_stat, key=lambda x: (list(x.values())[0]["Hitting"]["battingOrder"], list(x.values())[0]["Hitting"]["substitutionOrder"]))
            away_pitching_stat = sorted(away_pitching_stat, key=lambda x: (list(x.values())[0]["Pitching"]["pitchingOrder"]))
            
            match_update_data = {
                "id": game.id,
                "home_result": match_data["homeResult"],
                "home_batting_stat_json": json.dumps(home_batting_stat),
                "home_pitching_stat_json": json.dumps(home_pitching_stat),
                "away_batting_stat_json": json.dumps(away_batting_stat),
                "away_pitching_stat_json": json.dumps(away_pitching_stat),
                "home_score_json": json.dumps(match_data["lineScore"]["home"]),
                "home_score": match_data["lineScore"]["home"]["R"],
                "away_score_json": json.dumps(match_data["lineScore"]["away"]),
                "away_score": match_data["lineScore"]["away"]["R"],
                "game_status": match_data["gameStatus"],
                "pitching_result_json": json.dumps(match_data["decisions"]),
                "venue": match_data["Venue"]
            }
            matchs.append(match_update_data)
        else:
            match_update_data = {
                "id": game.id,
                "home_result": match_data["homeResult"],
                "game_status": match_data["gameStatus"]
            }
            matchs.append(match_update_data)
    session.bulk_update_mappings(MFLPlayer, players)
    session.bulk_update_mappings(MLBMatchSchedule, matchs)
    session.commit()
    return {"status_code": 200}
    

"""
    23시 20분
    매치의 결과를 가지고 와서 승부 예측한 것을 반영한다.
    추후에 더블 헤더로 인해서 승부 예측 못한 경기가 있을 수 있으므로 해당 경기에 대한 예외도 처리 해야 한다.
"""
@call_api.get("/update_mpuser_score", response_model=schemas.StatusCode)
async def update_mpuser_score_api(session: Session = Depends(db.session)):
    update_predictGames_data = []
    update_mpusers_data = []
    """
    추후 활성화 해야 함
    today = datetime.now()
    game_date = today - timedelta(days=1)
    today_str = today.strftime("%m") + today.strftime("%d")
    game_date_str = game_date.strftime("%m") + game_date.strftime("%d")
    """
    today_str = get_env().NOW_SEASON + get_env().TODAY
    game_date_str = get_env().GAME_TODAY

    predict_games = session.query(MatchPrediction).filter_by(game_date=today_str, is_status=False).all()

    sess_match_games = session.query(MLBMatchSchedule).filter_by(game_date=game_date_str)
    sess_mpuser_list = session.query(MPUser).filter_by(season=get_env().NOW_SEASON)

    for predict_game in predict_games:
        update_match = []
        win_num = 0
        predict_games_list = json.loads(predict_game.predict_json)

        # 유저가 승부 예측한 승 패를 확인해서 matchprediction 에 저장한다.
        for game in predict_games_list:
            match = sess_match_games.filter_by(gameid=game["gameid"]).first()
            if match.game_status != "Completed":
                game["result"] = "P"
            elif match.home_result == game["predict"]:
                win_num += 1
                game["result"] = "W"
            else:
                game["result"] = "L"
            update_match.append(game)
        update_predict_game = {
            "id": predict_game.id,
            "predict_json": json.dumps(update_match, ensure_ascii=False),
            "is_status": True,
            "updated_at": datetime.now()
        }
        update_predictGames_data.append(update_predict_game)

        # 유저가 승부 예측한 통계를 mpuser 에 저장한다.
        mpuser = sess_mpuser_list.filter_by(user_id=predict_game.user_id).first()
        total_matchs_num = len(sess_match_games.filter_by(game_status="Completed").all())
        win_ratio = round(win_num / total_matchs_num * 100  ,1)

        if mpuser.predict_history_json:
            predict_history = json.loads(mpuser.predict_history_json)
        else:
            predict_history = {}

        update_total_games = mpuser.total_games + total_matchs_num
        update_total_win = mpuser.total_win + win_num
        predict_history[today_str] = f"{win_num}/{total_matchs_num}/{win_ratio}"
        
        update_mpuser = {
            "id": mpuser.id,
            "total_games": update_total_games,
            "total_win": update_total_win,
            "total_win_rate": round(update_total_win / update_total_games * 100, 1),
            "predict_history_json": json.dumps(predict_history, ensure_ascii=False)
        }
        update_mpusers_data.append(update_mpuser)
    session.bulk_update_mappings(MatchPrediction, update_predictGames_data)
    session.bulk_update_mappings(MPUser, update_mpusers_data)
    session.commit()
    return {"status_code": 200}


"""
    23시 30분
    fluser 의 now_lineup 에 저장되어 있는 선수들의 점수를 업데이트 한다.
    - total_selected_lineup 에 유저가 now_lineup 에 선택된 선수들의 숫자를 하나씩 늘려줍니다.
    - 선택된 mflplayer 의 selected_by_user 의 숫자도 하나씩 늘려줍니다.
"""
@call_api.get("/update_fluser_score", response_model=schemas.StatusCode)
async def update_fluser_score_api(session: Session = Depends(db.session)):
    update_users_list = []
    update_players_list = []
    selected_players = {}
    """
    추후 활성화 해야 함
    date_now = datetime.now()
    today = date_now.strftime("%m") + date_now.strftime("%d")
    """
    today = get_env().TODAY

    users = session.query(FLUser).filter_by(is_status=True).all()
    for user in users:
        daily_score = 0
        mlbplayers = []
        call_lineup = json.loads(user.now_lineup_json)
        if user.selected_players_json:
            user_selected_players = json.loads(user.selected_players_json)
        else:
            user_selected_players = {}

        for index, info in enumerate(call_lineup):
            player = session.query(MFLPlayer).join(MFLPlayer.mlbplayer).\
                filter(MLBPlayer.position==info["position"], MLBPlayer.playerid==info["playerID"], MFLPlayer.season==get_env().NOW_SEASON).first()
            
            player_score_json = json.loads(player.score_json)
            if today in player_score_json:
                player_daily_score = round(player.daily_score * get_env().BASEBALL_SCORE_RATIO[index], 1)
            else:
                player_daily_score = 0
            daily_score += player_daily_score
            
            info["average_score"] = player.average_score
            mlbplayers.append(info)
            # 유저가 해당 선수들을 얼마나 선택했었는지에 대한 횟수를 추가한다.
            if player.playerid in user_selected_players:
                user_selected_players[player.playerid] += 1
            else:
                user_selected_players[player.playerid] = 1
            # 유저에 의해 선택되어진 선수들의 횟수를 추가한다.
            if player.playerid in selected_players:
                selected_players[player.playerid] += 1
            else:
                selected_players[player.playerid] = 1
        else:
            user.add_total_score(round(daily_score, 1))
            update_user_data = {
                "id": user.id,
                "selected_players_json": json.dumps(user_selected_players, ensure_ascii=False),
                "now_lineup_json": json.dumps(mlbplayers, ensure_ascii=False)
            }
            update_users_list.append(update_user_data)
    # 모든 유저들에 의해서 선택되어진 선수들의 선택된 횟수를 플레이어마다 저장을 한다.
    for player_id, num in selected_players.items():
        player = session.query(MFLPlayer).filter_by(playerid=player_id).first()
        player.selectedByUser(num)
        update_player = {
            "id": player.id
        }
        update_players_list.append(update_player)

    session.bulk_update_mappings(FLUser, update_users_list)
    session.bulk_update_mappings(MFLPlayer, update_players_list)
    session.commit()
    return {"status_code": 200}


"""
    23시 40분
    mflplayer 중에 모든 선수들의 difference score this week 를 업데이트 시켜 준다.
"""
@call_api.get("update_difference_score_this_week")
async def update_difference_score_this_week_api(session: Session = Depends(db.session)):
    return


"""
    23시 50분
    modified_lineup 에 저장되어 있는 엔트리를 적용 시킨다.
"""
@call_api.get("/update_fluser_preliminary_roster/{sort}", response_model=schemas.StatusCode)
async def update_fluser_preliminary_roster_api(sort: schemas.FantasyLeagueSort, session: Session = Depends(db.session)):
    update_users_list = []
    is_weekday = datetime.now().weekday()
    
    users = session.query(FLUser).filter(FLUser.sort==sort, FLUser.season==get_env().NOW_SEASON)
    if is_weekday == 0:
        users = users.filter(FLUser.modified_status.in_(["ALL", "PITCHER"])).all()
    else:
        users = users.filter(FLUser.modified_status=="ALL").all()
    
    for user in users:
        now_lineup = json.loads(user.now_lineup_json)
        modified_lineup = json.loads(user.modified_lineup_json)
        if is_weekday == 0:
            if user.modified_status == "PITCHER":
                now_lineup = now_lineup[:9] + modified_lineup
                user.now_lineup_json = json.dumps(now_lineup, ensure_ascii=False)
            else:
                user.now_lineup_json = user.modified_lineup_json
            user.modified_lineup_json = None
            user.modified_status = "NONE"
        else:
            now_lineup = modified_lineup[:9] + now_lineup[9:]
            modified_lineup = modified_lineup[9:]

            user.now_lineup_json = json.dumps(now_lineup, ensure_ascii=False)
            user.modified_lineup_json = json.dumps(modified_lineup, ensure_ascii=False)
            user.modified_status = "PITCHER"
        update_user = {
            "id": user.id
        }
        update_users_list.append(update_user)
    session.bulk_update_mappings(FLUser, update_users_list)
    session.commit()
    return {"status_code": 200}



