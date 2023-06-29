from typing import Optional
from pydantic import BaseModel, validator
from app.schemas.user import User_OUT
from datetime import datetime


class Board_OUT(BaseModel):
    id: int
    name: str

    class Config: 
        orm_mode = True


class Series_IN(BaseModel):
    name: str

    @validator("name")
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("빈 값이 허용되지 않습니다.")
        return v


class SeriesUpdate_IN(Series_IN):
    is_shown: bool


class Post_IN(BaseModel):
    title: str
    board_name: str
    body: str
    series_id: Optional[int] = None

    @validator("title", "board_name", "body")
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("빈 값이 허용되지 않습니다.")
        return v


class CommentUpdate_IN(BaseModel):
    content: str

    @validator("content")
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("빈 값이 허용되지 않습니다.")
        return v


class Comments_IN(CommentUpdate_IN):
    parent_id: Optional[int] = None
    comment_by_user_id: Optional[int] = None


class CommentsForm(Comments_IN):
    id: int
    writer: User_OUT
    comment_by: Optional[User_OUT] = None
    is_delete: bool
    is_status: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Comments_OUT(BaseModel):
    total: int = 0
    comments: list[CommentsForm] = []

    class Config:
        orm_mode = True


class CommentNowPage_OUT(BaseModel):
    page: int = 0


class SeriesForm(Series_IN):
    id: int
    user_id: int
    writer: User_OUT
    is_shown: bool
    is_status: bool
    recommend_count: int

    class Config:
        orm_mode = True


class Series_OUT(BaseModel):
    total: int = 0
    series_list: list[SeriesForm] = []

    class Config:
        orm_mode = True


class PostForm(BaseModel):
    id: int
    title: str
    user_id: int
    writer: User_OUT
    total: Optional[int] = 0
    series: Optional[Series_OUT] = None
    board: Board_OUT

    recommend_count: int
    read_count: int
    comment_count: int

    is_status: bool
    is_admin: bool
    
    class Config:
        orm_mode = True


class BestForm(BaseModel):
    id: int
    post: PostForm

    class Config:
        orm_mode = True


class Posts_OUT(BaseModel):
    total: int = 0
    posts: list[PostForm] = []

    class Config:
        orm_mode = True


class Best_OUT(BaseModel):
    total: int = 0
    posts: list[BestForm] = []

    class Config: 
        orm_mode = True


class PostDetail_OUT(PostForm):
    body: str
    post_up: int
    post_down: int
    series_list: list[PostForm] = []
    
    class Config:
        orm_mode = True


class SeriesDetail_OUT(SeriesForm):
    total: int
    posts: list[PostForm] = []

    class Config:
        orm_mode = True


class StatusCode(BaseModel):
    status_code: int
