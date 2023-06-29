from sqlalchemy import Column, ForeignKey, Boolean, BIGINT, String, Integer, Text
from app.models.base import Base
from sqlalchemy.orm import relationship, Session


class Best(Base):
    __tablename__ = "best"
    post_id = Column(ForeignKey("post.id", ondelete="CASCADE"), nullable=False) # 등록된 게시글
    is_status = Column(Boolean, nullable=False, default=True) # 관리자의 차단 여부

    post = relationship("Post", back_populates="best", foreign_keys=[post_id], uselist=False)


# 대표 이미지 넣는 곳 있어야 한다. (선택 가능)
class Series(Base):
    __tablename__ = "series"
    name = Column(String(100), nullable=False) # 제목
    user_id = Column(ForeignKey("users.id"), nullable=False) # 만든 사람
    is_shown = Column(Boolean, nullable=False, default=True) # 공개 여부(공개 시 게시판에 등록이 됨)
    is_status = Column(Boolean, nullable=False, default=False) # 연재 게시판 공개 여부
    recommend_count = Column(Integer, nullable=False, default=0)

    writer = relationship("User", back_populates="series_list", foreign_keys=[user_id])
    posts = relationship("Post", back_populates="series", order_by="Post.created_at.desc()")


class Board(Base):
    __tablename__ = "board"
    name = Column(String(100), nullable=False) # 게시판 이름
    is_status = Column(Boolean, nullable=False, default=True) # 게시판 차단 여부

    posts = relationship("Post", back_populates="board")


"""
    add_commnet - relationship 추가 해줌
    check_best - post_up 과 post_down 을 계산해서 현재 게시물이 best 에 포함될지 말지를 결정한다.
"""
class Post(Base):
    __tablename__ = "post"
    title = Column(String(255), nullable=False) # 제목
    body = Column(Text, nullable=False)

    user_id = Column(ForeignKey("users.id"), nullable=False) # 만든 사람
    series_id = Column(ForeignKey("series.id"), nullable=True)
    board_id = Column(ForeignKey("board.id"), nullable=False)

    post_up = Column(Integer, nullable=False, default=0)
    post_down = Column(Integer, nullable=False, default=0)
    
    read_count = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)
    recommend_count = Column(Integer, nullable=False, default=0)

    is_status = Column(Boolean, nullable=False, default=True) # 관리자의 차단 여부
    is_admin = Column(Boolean, nullable=False, default=False) # 공지사항 여부

    writer = relationship("User", back_populates="posts", foreign_keys=[user_id], uselist=False)
    board = relationship("Board", back_populates="posts", foreign_keys=[board_id], uselist=False)
    series = relationship("Series", back_populates="posts", foreign_keys=[series_id], uselist=False)
    recommends = relationship("Recommend", back_populates="post", cascade="all, delete") # 연결된 추천
    comments = relationship("Comment", back_populates="post", cascade="all, delete") # 연결된 댓글
    best = relationship("Best", back_populates="post", uselist=False, cascade="all, delete")

    def check_best(self):
        return
    

class Recommend(Base):
    __tablename__ = "recommend"
    post_id = Column(ForeignKey("post.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    is_recommend = Column(Boolean, nullable=False, default=True)

    post = relationship("Post", back_populates="recommends", foreign_keys=[post_id])
    writer = relationship("User", back_populates="recommends", foreign_keys=[user_id])


class Comment(Base):
    __tablename__ = "comment"
    id = Column(BIGINT, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    post_id = Column(ForeignKey("post.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    parent_id = Column(ForeignKey("comment.id"), nullable=True)
    comment_by_user_id = Column(ForeignKey("users.id"), nullable=True)

    is_delete = Column(Boolean, nullable=False, default=False)
    is_status = Column(Boolean, nullable=False, default=True)

    writer = relationship("User", back_populates="comments", foreign_keys=[user_id], uselist=False)
    post = relationship("Post", back_populates="comments", foreign_keys=[post_id], uselist=False)
    comment_by = relationship("User", foreign_keys=[comment_by_user_id], uselist=False)
    children = relationship("Comment", back_populates="parent")
    parent = relationship("Comment", back_populates="children", foreign_keys=[parent_id], uselist=False, remote_side=[id])
