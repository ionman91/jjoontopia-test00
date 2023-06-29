from config import get_env
from typing import Optional
from app import schemas

import requests


env = get_env()
headers = env.RAPID_MLB_HEADERS


def mlb_player_find_info(player_id: int):
    url = env.RAPID_MLB_BASIC_URL + "getMLBPlayerInfo"
    querystring = {"playerID": player_id}
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"에러가 발생하였습니다.: {err}")
    return response.json()

def mlb_player_list():
    url = env.RAPID_MLB_BASIC_URL + "getMLBPlayerList"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"에러가 발생하였습니다.: {err}")
    return response.json()


def mlb_team_list():
    url = env.RAPID_MLB_BASIC_URL + "getMLBTeams"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"에러가 발생하였습니다.: {err}")
    return response.json()


def mlb_team_roster(team: schemas.MLBTeamList):
    url = env.RAPID_MLB_BASIC_URL + "getMLBTeamRoster"
    querystring = {"teamAbv": team}
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"에러가 발생하였습니다.: {err}")
    return response.json()


def mlb_team_schedule_list(team: schemas.MLBTeamList, season: Optional[str] = env.NOW_SEASON):
    url = env.RAPID_MLB_BASIC_URL + "getMLBTeamSchedule"
    querystring = {"teamAbv" : team, "season" : season}
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"에러가 발생하였습니다.: {err}")
    return response.json()


def mlb_daily_schedule_list(date: str = "20230529"):
    url = env.RAPID_MLB_BASIC_URL + "getMLBGamesForDate"
    querystring = {"gameDate" : env.NOW_SEASON + date}
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"에러가 발생하였습니다.: {err}")
    return response.json()


def mlb_today_box_score(gameID: str):
    url = env.RAPID_MLB_BASIC_URL + "getMLBBoxScore"    
    querystring = {"gameID":gameID}
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"에러가 발생하였습니다.: {err}")
    return response.json()


def get_mlb_team_id(team: schemas.MLBTeamList):
    MLBTeamID = {
        "PIT": 5, "NYM": 6, "MIL": 7, "ATL": 8, "LAA": 9, "CLE": 10, "COL": 11, "ARI": 12, 
        "CHW": 13, "TEX": 14, "WAS": 15, "SF": 16, "TB": 17, "CHC": 18, "BOS": 19, "SD": 20, 
        "NYY": 21, "STL": 22, "CIN": 23, "HOU": 24, "BAL": 25, "OAK": 26, "TOR": 27, "PHI": 28, 
        "SEA": 29, "KC": 30, "MIN": 31, "DET": 32, "MIA": 33, "LAD": 34, 
    }
    return MLBTeamID[team]
