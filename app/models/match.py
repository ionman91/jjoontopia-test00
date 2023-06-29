from sqlalchemy import Column, ForeignKey, String, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base


class MLBMatchSchedule(Base):
    __tablename__ = "mlb_match_schedule"
    home_id = Column(ForeignKey("mlbteam.id"), nullable=False)
    away_id = Column(ForeignKey("mlbteam.id"), nullable=False)
    gameid = Column(String(32), nullable=False, unique=True)
    game_date = Column(String(8), nullable=False)
    game_time = Column(String(6), nullable=False)
    game_time_epoch = Column(String(15), nullable=True)
    venue = Column(String(40), nullable=False)

    home_score = Column(String(2), nullable=False, default="0")
    away_score = Column(String(2), nullable=False, default="0")
    home_result = Column(Enum("W", "L", "P"), nullable=True)

    pitching_start_json = Column(JSON, nullable=True)
    pitching_result_json = Column(JSON, nullable=True)
    home_batting_stat_json = Column(JSON, nullable=True)
    away_batting_stat_json = Column(JSON, nullable=True)
    home_pitching_stat_json = Column(JSON, nullable=True)
    away_pitching_stat_json = Column(JSON, nullable=True)
    home_score_json = Column(JSON, nullable=True)
    away_score_json = Column(JSON, nullable=True)

    game_status = Column(Enum("Completed", "scheduled", "Postponed", "Suspended"), nullable=False, default="scheduled")
    is_application = Column(Boolean, nullable=False, default=False) # 승부 예측 결과가 적용 되었는지 여부

    home_team = relationship("MLBTeam", back_populates="home_match", foreign_keys=[home_id], uselist=False)
    away_team = relationship("MLBTeam", back_populates="away_match", foreign_keys=[away_id], uselist=False)


class MatchPrediction(Base):
    __tablename__ = "match_prediction"
    user_id = Column(ForeignKey("users.id"), nullable=False)
    sort = Column(Enum("KBO", "MLB"), nullable=False)
    game_date = Column(String(8), nullable=False)
    predict_json = Column(JSON, nullable=False)
    is_status = Column(Boolean, nullable=False, default=False)

    writer = relationship("User", back_populates="match_predict", uselist=False)
