from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request

from config import get_env
from datetime import datetime
from enum import Enum

from app.db.connection import db
from app.models.board import Post, Comment, Best, Series, Recommend
from app.api import crud as c
from app import schemas
from app.utils import (
    board_utils as b_ut,
    utils as ut
)


board = APIRouter()


"""
    1. 나중에 로그인 만들고 나서 middleware 에서 request.state.id 를 받아 온다면 
    post, comment 수정 삭제 등은 검색할 때 user_id 를 같이 검색해야 한다.

    2. 나중에 board_name, post_id 오면 일일이 다 검색하지 말고 post_id 를 검색하고 나서 그냥 연결해서 
    post.board.name == board_name 이런식으로 연결해서 하자. 그게 훨씬 데이터 상으로 이득일거 같다.

    ### cascade 의 연결된 것들을 다 지우기 위해서는 relationship("Best", back_populates="post", uselist=False, cascade="all, delete") 가 되야함

    3. 게시글 읽기 - 조회수 중복 막기 (session id 를 이용하여 redis 로 하자. - 나중에)
    4. relationship order_by 를 이용해서 하는것을 한번 찾아보자.
"""

"""
    enum
"""
class RecommendType(str, Enum):
    like: str = "like"
    dislike: str = "dislike"


"""
    게시판 관련
"""
# 모든 게시판 불러오기
@board.get("/", response_model=list[schemas.Board_OUT])
async def get_boards_api(session: Session = Depends(db.session)):
    boards = c.get_boards(session)
    return boards


# 베스트 게시판 들어가기
@board.get("/best", response_model=schemas.Best_OUT)
async def get_best_list_api(page: int = 0, size: int = get_env().PAGING_LIMIT, session: Session = Depends(db.session)):
    _best_list = session.query(Best).filter_by(is_status=True).order_by(Best.created_at.desc())
    
    total = _best_list.count()
    posts = _best_list.offset(page*size).limit(size).all()

    return {
        "total": total,
        "posts": posts
    }


"""
    연재 관련
"""
# 연재 가지고 오기
@board.get("/series/lists", response_model=schemas.Series_OUT)
async def get_series_list_api(page: int = 0, size: int = get_env().PAGING_LIMIT, session: Session = Depends(db.session)):
    _series_list = session.query(Series).filter_by(is_shown=True, is_status=True).order_by(Series.created_at.desc())

    total = _series_list.count()
    series_list = _series_list.offset(page*size).limit(size).all()

    return {
        "total": total,
        "series_list": series_list
    }


# 시리즈 불러오기 - 자기 자신이 불러올대랑 다른 사람이 불러올때랑 다르다.
@board.get("/series/{series_id}", response_model=schemas.SeriesDetail_OUT)
async def get_series_api(request: Request, series_id: int, page: int = 0, size: int = get_env().PAGING_LIMIT, session: Session = Depends(db.session)):
    current_user = request.state.user
    if current_user:
        series = c.get_series(session, series_id, user_id=current_user.id)
    else:
        series = c.get_series(session, series_id, is_shown=True, is_status=True)
    if not series:
        raise HTTPException(status_code=404, detail="존재하지 않는 연재입니다.")
    
    posts = series.posts
    val = jsonable_encoder(series)
    val["writer"] = series.writer
    val["total"] = len(posts)
    val["posts"] = posts[page*size:(page+1)*size]
    return val


# 등록 - request 필요
@board.post("/series/write", response_model=list[schemas.Series_OUT])
async def create_series_api(request: Request, d: schemas.Series_IN, user_id: int, session: Session = Depends(db.session)):
    # req = ut.check_valid_request(request)

    user = c.get_user(session, user_id)

    for series in user.series_list:
        if d.name == series.name:
            raise HTTPException(status_code=404, detail="유저가 이전에 만든 연재 이름과 같습니다.")
    u = Series(name=d.name, user_id=user.id)
    session.add(u)
    session.commit()

    return user.series_list


# 삭제 - request 필요
@board.delete("/series/delete/{series_id}", response_model=schemas.StatusCode)
async def delete_series_api(request: Request, series_id: int, user_id: int, session: Session = Depends(db.session)):
    # req = ut.check_valid_request(request)

    series = c.get_series(session, series_id, user_id=user_id)

    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="읎엄")
    if series.posts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="시리즈에 연재 되어있는 게시글을 연동 해제 하셔야 합니다.")
    session.delete(series)
    session.commit()

    return {
        "status_code": status.HTTP_200_OK
    }


# 수정 - request 필요
@board.patch("/series/update/{series_id}", response_model=schemas.StatusCode)
async def update_series_api(request: Request, d: schemas.SeriesUpdate_IN, series_id: int, user_id: int, session: Session = Depends(db.session)):
    # req = ut.check_valid_request(request)

    series = c.get_series(session, series_id, user_id=user_id)

    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="읎엄")
    
    series.name = d.name
    series.is_shown = d.is_shown
    session.add(series)
    session.commit()

    return {
        "status_code": status.HTTP_200_OK
    }


# 유저의 시리즈 불러오기 - 자기 자신이 불러올때는 다 불러오고, 다른 유저가 불러올때는 공개 된것만 불러온다.
@board.get("/user_series/{user_id}", response_model=list[schemas.Series_OUT])
async def get_user_series_list_api(request: Request, user_id: int, session: Session = Depends(db.session)):
    # req = ut.check_valid_request(request)
    # if (req.user.id == user_id):
    # lists = c.get_user_series_list(session, user_id)
    # else:
    lists = c.get_user_series_list(session, user_id, is_shown=True)
    return lists


"""
    post 관련
"""
# 일반 게시판 들어가기
@board.get("/{board_name}", response_model=schemas.Posts_OUT)
async def get_posts_api(board_name: str, page: int = 0, size: int = get_env().PAGING_LIMIT, session: Session = Depends(db.session)):  
    board = c.get_board(session, board_name)
    if not board:
        raise HTTPException(status_code=404, detail="존재하지 않는 게시판입니다.")
    elif not board.is_status:
        raise HTTPException(status_code=404, detail="삭제된 게시판입니다.")
    
    _posts_list = session.query(Post).filter_by(is_status=True).order_by(Post.created_at.desc())
    total = _posts_list.count()
    posts = _posts_list.offset(page*size).limit(size).all()

    return {
        "total": total, 
        "posts": posts
    }


# 상세 페이지 ㅇ  
@board.get("/post/{post_id}", response_model=schemas.PostDetail_OUT)
async def get_post_api(post_id: int, session: Session = Depends(db.session)):
    post = c.get_post(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="못찾았음")

    post_dict = jsonable_encoder(post)
    post_dict["writer"] = post.writer
    post_dict["board"] = post.board
    post_dict["series"] = post.series
    post_dict["series_list"] = post.series.posts if post.series else []
        
    return post_dict


# 등록 ㅇ
@board.post("/post/write", response_model=schemas.StatusCode)
async def create_post_api(request: Request, d: schemas.Post_IN, session: Session = Depends(db.session)):
    req = ut.check_valid_request(request)
    
    board = c.get_board(session, d.board_name)
    if not board:
        raise HTTPException(status_code=404, detail="존재하지 않는 게시판입니다.")
    u = Post(title=d.title, body=d.body, user_id=req.user.id, series_id=d.series_id, board_id=board.id)
    session.add(u)
    session.commit()

    return {
        "status_code": status.HTTP_200_OK
    }


# 삭제
@board.delete("/post/delete/{post_id}", response_model=schemas.StatusCode)
async def delete_post_api(request: Request, post_id: int, session: Session = Depends(db.session)):
    req = ut.check_valid_request(request)
    
    post = c.get_post(session, post_id, user_id=req.user.id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="못찾았음")

    session.delete(post)
    session.commit()

    return {
        "status_code": status.HTTP_200_OK
    }


# 수정
@board.patch("/post/update/{post_id}", response_model=schemas.StatusCode)
async def update_post_api(request: Request, d: schemas.Post_IN, post_id: int, session: Session = Depends(db.session)):
    req = ut.check_valid_request(request)

    post = c.get_post(session, post_id, user_id=req.user.id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="못찾았음")
    if post.title == d.title and post.body == d.body and post.series_id == d.series_id:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="내용이 변한게 없습니다.")

    post.title = d.title
    post.body = d.body
    post.series_id = d.series_id
    post.updated_at = datetime.now()

    session.add(post)
    session.commit()

    return {
        "status_code": status.HTTP_200_OK
    }


# 좋아요, 싫어요
@board.post("/recommend/{post_id}/{like_sort}")
async def recommend_post_api(request: Request, post_id: int, like_sort: RecommendType, session: Session = Depends(db.session)):
    req = ut.check_valid_request(request)
    
    post = c.get_post(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="못찾았음")
    if post.user_id == req.user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="본인 게시물에는 추천을 할 수 없습니다.")

    like_status = True if like_sort == "like" else False
    is_recommend = c.get_recommend(session, post_id, req.user.id)

    if is_recommend:
        exist_comment = True
        if is_recommend.is_recommend == like_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 선택한 상태입니다.")
        else:
            is_recommend.is_recommend = like_status
            is_recommend.updated_at = datetime.now()
            session.add(is_recommend)
    else:
        exist_comment = False
        u = Recommend(post_id=post.id, user_id=req.user.id, is_recommend=like_status)
        session.add(u)
    session.commit()
    
    if like_status:
        post = b_ut.post_up(post, exist_comment)
    else:
        post = b_ut.post_down(post, exist_comment)
    session.add(post)
    session.commit()

    # 해당 post 가 series 에 연결되어있다면 해당 series 의 좋아요도 다시 합산해서 적용한다.
    if post.series:
        series = post.series
        series.recommend_count = sum(post.recommend_count for post in series.posts)
        session.add(series)
        session.commit()

    # 좋아요를 확인해서 베스트로 보낼지 말지 결정한다.
    if not post.best and post.recommend_count >= get_env().MIN_CONDITION_BEST:
        u = Best(post_id=post.id)
        session.add(u)
        session.commit()
    elif post.best and post.best.is_status and post.recommend_count < get_env().MIN_CONDITION_BEST:
        # best = c.get_best_post(session, post_id=post.id)
        post.best.is_status = False
        session.add(post.best)
        session.commit()
    return {
        "status_code": status.HTTP_200_OK
    }
    
    

"""
    댓글 관련
"""
# 불러오기
@board.get("/{post_id}/comments", status_code=status.HTTP_200_OK, response_model=schemas.Comments_OUT)
async def get_comments_api(post_id: int, page: int = 0, size: int = get_env().PAGING_LIMIT, session: Session = Depends(db.session)):
    post = c.get_post(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="못찾았음")
    
    comments = b_ut.comments_sort(post.comments, page, size)

    return {
        "comments": comments, 
        "total": post.comment_count
    }


# 등록
@board.post("/{post_id}/write_comment", status_code=status.HTTP_201_CREATED, response_model=schemas.CommentNowPage_OUT)
async def create_comment_api(request: Request, post_id: int, d: schemas.Comments_IN, session: Session = Depends(db.session)):
    req = ut.check_valid_request(request)

    post = c.get_post(session, post_id, user_id=req.user.id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="못찾았음")
    
    if d.parent_id:
        parent_comment = c.get_comment(session, d.parent_id, post_id=post_id, is_status=True, is_delete=False)
        comment_by_user = c.get_user(session, d.comment_by_user_id)
        if not parent_comment or not comment_by_user:
            raise HTTPException(status_code=404, detail="오류가 발생하였습니다. 다시 한번 댓글을 입력해 주시기 바랍니다.")
        
    u = Comment(content=d.content.strip(), user_id=req.user.id, post_id=post.id, parent_id=d.parent_id, comment_by_user_id=d.comment_by_user_id)
    session.add(u)
    session.commit()

    post.comment_count += 1
    session.add(post)
    session.commit()
    page = b_ut.comments_sort(post.comments, created_comment_id=u.id)

    return {"page": page}


# 삭제
@board.delete("/{post_id}/delete_comment/{comment_id}", response_model=schemas.StatusCode)
async def delete_comment_api(request: Request, post_id: int, comment_id: int, session: Session = Depends(db.session)):
    req = ut.check_valid_request(request)

    post = c.get_post(session, post_id, user_id=req.user.id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="못찾았음")
    
    comment = c.get_comment(session, comment_id, user_id=req.user.id, post_id=post.id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="못 찾았음")
    if comment.children:
        comment.is_delete = True
        session.add(comment)
        session.commit()
    else:
        comment.post.comment_count -= 1
        session.add(comment.post)
        session.commit()
        
        session.delete(comment)
        session.commit()

    return {
        "status_code": status.HTTP_200_OK
    }


# 수정 
@board.patch("/{post_id}/update_comment/{comment_id}", response_model=schemas.StatusCode)
async def update_comment_api(request: Request, post_id: int, comment_id: int, d: schemas.CommentUpdate_IN, session: Session = Depends(db.session)):
    req = ut.check_valid_request(request)
    
    post = c.get_post(session, post_id, user_id=req.user.id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="못찾았음")
    
    comment = c.get_comment(session, comment_id, user_id=req.user.id, post_id=post.id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="못 찾았음")
    if comment.content == d.content.strip():
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="내용이 변한게 없습니다.")
    
    comment.content = d.content
    comment.updated_at = datetime.now()
    session.add(comment)
    session.commit()

    return {"status_code": status.HTTP_200_OK}
