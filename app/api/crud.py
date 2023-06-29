from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models as md


def get_user(db: Session, id: int, **kwargs):
    user = db.query(md.User).filter_by(id=id, status="ACTIVE", **kwargs).first()
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 유저입니다.")
    return user


def get_boards(db: Session, **kwargs):
    return db.query(md.Board).filter_by(**kwargs).all()


def get_best_board(db: Session, **kwargs):
    return db.query(md.Best).filter_by(is_status=True, **kwargs).all()


def get_board(db: Session, name: str, **kwargs):
    return db.query(md.Board).filter_by(name=name, is_status=True, **kwargs).first()


def get_posts(db: Session, **kwargs):
    return db.query(md.Post).filter_by(is_status=True, **kwargs).order_by(md.Post.created_at.desc()).all()


def get_post(db: Session, id: int, **kwargs):
    return db.query(md.Post).filter_by(id=id, is_status=True, **kwargs).first()


def get_best_post(db: Session, **kwargs):
    return db.query(md.Best).filter_by(**kwargs).first()


def get_comments(db: Session, post_id: int, **kwargs):
    return db.query(md.Comment).filter_by(post_id=post_id, parent_id=None, comment_by_user_id=None, **kwargs).all()


def get_comment(db: Session, id: int, **kwargs):
    return db.query(md.Comment).filter_by(id=id, **kwargs).first()


def get_series_list(db: Session, **kwargs):
    return db.query(md.Series).filter_by(**kwargs).all()


def get_series(db: Session, id: int, **kwargs):
    return db.query(md.Series).filter_by(id=id, **kwargs).first()


def get_user_series_list(db: Session, user_id: int, **kwargs):
    return db.query(md.Series).filter_by(user_id=user_id, **kwargs).all()


def get_recommend(db: Session, post_id: int, user_id: int, **kwargs):
    return db.query(md.Recommend).filter_by(post_id=post_id, user_id=user_id, **kwargs).first()


