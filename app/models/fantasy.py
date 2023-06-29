from sqlalchemy import Column, ForeignKey, Integer, JSON, String, Float, Boolean
from app.models.base import Base
from sqlalchemy.orm import relationship
from config import get_env
from datetime import datetime, timedelta
from app.models.match import MLBMatchSchedule

import json


class MLBPlayer(Base):
    __tablename__ = "mlbplayer"
    team_id = Column(ForeignKey("mlbteam.id"), nullable=True)
    kname = Column(String, nullable=True)
    ename = Column(String, nullable=False)
    playerid = Column(String, nullable=False, unique=True)
    mlbid = Column(String, nullable=False)
    bday = Column(String, nullable=False)
    jersey_num = Column(String, nullable=False)
    position = Column(String, nullable=False)
    is_roster = Column(Boolean, nullable=False, default=False)

    mflplayer = relationship("MFLPlayer", back_populates="mlbplayer", cascade="all, delete")
    mlbteam = relationship("MLBTeam", back_populates="roster", foreign_keys=[team_id], uselist=False)
    

class MFLPlayer(Base):
    __tablename__ = "mflplayer"
    player_id = Column(ForeignKey("mlbplayer.id"), nullable=False)
    playerid = Column(String, nullable=False)
    season = Column(String, nullable=False, default=get_env().NOW_SEASON)

    daily_score = Column(Float, nullable=False, default=0)
    weekly_score = Column(Float, nullable=False, default=0)
    monthly_score = Column(Float, nullable=False, default=0)
    total_score = Column(Float, nullable=False, default=0)
    difference_score_this_week = Column(Float, nullable=False, default=0)
    average_score = Column(Float, nullable=False, default=0)

    total_games = Column(Integer, nullable=False, default=0)
    selected_by_user = Column(Integer, nullable=False, default=0)

    stat_json = Column(JSON, nullable=True)
    score_json = Column(JSON, nullable=True)
    now_stat = Column(JSON, nullable=True)

    mlbplayer = relationship("MLBPlayer", back_populates="mflplayer", foreign_keys=[player_id], uselist=False)

    def calculate_pitcher_score(self, data):
        settings = get_env().BASEBALL_SCORE_SETTING["pitching"]
        pitching = data["Pitching"]

        score = int(pitching["BB"]) * settings["BB"] + int(pitching["H"]) * settings["H"] + \
                int(pitching["HR"]) * settings["HR"] + int(pitching["ER"]) * settings["ER"] + \
                round(float(pitching["InningsPitched"]) * settings["InningsPitched"], 1) + int(pitching["SO"]) * settings["SO"]
        return score

    def calculate_hitter_score(self, data):
        settings = get_env().BASEBALL_SCORE_SETTING["hitting"]
        hitting = data["Hitting"]
        fielding = data["Fielding"]
        baserunning = data["BaseRunning"]

        score = int(hitting["BB"]) * settings["BB"] + int(hitting["TB"]) * settings["TB"] + \
                int(hitting["GIDP"]) * settings["GIDP"] + int(hitting["SF"]) * settings["SF"] + \
                int(hitting["HBP"]) * settings["HBP"] + int(hitting["RBI"]) * settings["RBI"] + \
                int(fielding["Outfield assists"]) * settings["Outfield_assists"] + \
                int(fielding["E"]) * settings["E"] + int(baserunning["CS"]) * settings["CS"] + \
                int(baserunning["SB"]) * settings["SB"]
        return score
        
    def add_total_score(self, score):
        score = round(score, 1)
        week_score = 0
        month_score = 0
        """
        추후 활성화
        now = datetime.now()
        today = now.strftime("%m") + now.strftime("%d")
        """
        today = get_env().TODAY
        collect_score = {}
        if self.score_json:
            collect_score = json.loads(self.score_json)
            for i in range(1, 30):
                """
                추후 활성화
                go_past = now + timedelta(days=-i)
                """
                hehe = get_env().DATETIME_TODAY
                go_past = hehe + timedelta(days=-i)
                
                day = go_past.strftime("%m") + go_past.strftime("%d")
                if day in collect_score:
                    if i <= 6:
                        week_score += collect_score[day]
                    month_score += collect_score[day]
            collect_score[today] = score
            self.daily_score = score
            self.weekly_score = week_score + score
            self.monthly_score = month_score + score
            self.total_score += score
            self.total_games += 1
            self.average_score = round(self.total_score / self.total_games, 1)
            self.score_json = json.dumps(collect_score, ensure_ascii=False)
        else:
            collect_score[today] = score
            self.daily_score = score
            self.weekly_score = score
            self.monthly_score = score
            self.total_score = score
            self.total_games = 1
            self.average_score = self.total_score
            self.score_json = json.dumps(collect_score, ensure_ascii=False)

    def add_player_game_stat(self, data, pos: str):
        """
        선수들의 스텟을 전부 저장하는 부분 > 나중에 서버 등의 여유가 많아지면 활성화
        now = datetime.now()
        today = now.strftime("%m") + now.strftime("%d")
        pitcher_stat = {}
        hitter_stat = {}
        """
        insert_now_stat = {"avg":"", "ops":"", "era":""}
        if pos == "pitcher" or pos == "pitcher_hitter":
            pitching = data["Pitching"]
            pitcher_stat = {
                "P_BB": pitching["BB"], "P_H": pitching["H"], "P_HR": pitching["HR"], 
                "ER": pitching["ER"], "ERA": pitching["ERA"], "SO": pitching["SO"],
                "InningsPitched": pitching["InningsPitched"]
            }
            insert_now_stat["era"] = pitching["ERA"]
        if pos == "hitter" or pos == "pitcher_hitter":
            hitting = data["Hitting"]
            fielding = data["Fielding"]
            baserunning = data["BaseRunning"]
            hitter_stat = {
                "AB": hitting["AB"], "H_BB": hitting["BB"], "H_HR": hitting["HR"], "H_H": hitting["H"], 
                "TB": hitting["TB"], "GIDP": hitting["GIDP"], "SF": hitting["SF"], "HBP": hitting["HBP"],
                "AVG": hitting["LOB"], "OPS": hitting["AVG"], "RBI": hitting["RBI"], 
                "Outfield_assists": fielding["Outfield assists"], "E": fielding["E"], "CS": baserunning["CS"], "SB": baserunning["SB"]
            }
            insert_now_stat["avg"] = hitting["LOB"]
            insert_now_stat["ops"] = hitting["AVG"]
        """
        선수들의 스텟을 전부 저장하는 부분 > 나중에 서버 등의 여유가 많아지면 활성화
        collect_stat = {}
        if self.stat_json:
            collect_stat = json.loads(self.stat_json)
        collect_stat[today] = {**pitcher_stat, **hitter_stat}
        self.stat_json = json.dumps(collect_stat, ensure_ascii=False)
        """
        self.now_stat = json.dumps(insert_now_stat, ensure_ascii=False)
    
    def selectedByUser(self, num):
        self.selected_by_user += num


class MLBTeam(Base):
    __tablename__ = "mlbteam"
    kname = Column(String, nullable=True)
    team_name = Column(String, nullable=False)
    city_name = Column(String, nullable=False)
    short_name = Column(String, nullable=False, unique=True)
    division = Column(String, nullable=False)
    conference = Column(String, nullable=False)
    teamid = Column(String, nullable=False)
    kstadium = Column(String, nullable=True)
    estadium = Column(String, nullable=True)

    roster = relationship("MLBPlayer", back_populates="mlbteam")
    mflteam = relationship("MFLTeam", back_populates="mlbteam", cascade="all, delete")
    home_match = relationship("MLBMatchSchedule", back_populates="home_team", foreign_keys=[MLBMatchSchedule.home_id])
    away_match = relationship("MLBMatchSchedule", back_populates="away_team", foreign_keys=[MLBMatchSchedule.away_id])


class MFLTeam(Base):
    __tablename__ = "mflteam"
    team_id = Column(ForeignKey("mlbteam.id"), nullable=False)
    short_name = Column(String, nullable=False)
    season = Column(String, nullable=False, default=get_env().NOW_SEASON)
    team_betting = Column(JSON, nullable=True)
    team_pitching = Column(JSON, nullable=True)

    mlbteam = relationship("MLBTeam", back_populates="mflteam", uselist=False)


class TestTable(Base):
    __tablename__ = "testtable"
    user_id = Column(Integer, nullable=False, unique=True)
    title = Column(String, nullable=False)
    hello = Column(JSON, nullable=False)

    def score(self, str):
        self.title = str