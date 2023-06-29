from fastapi import HTTPException
from config import get_env
from typing import Optional
from app.api import crud as c
from sqlalchemy.orm import Session

from app.models.board import Comment, Post

import math


def comments_sort(
    comments: list[Comment], page: int = 0, size: int = get_env().PAGING_LIMIT, 
    created_comment_id: Optional[int] = None
):
    comments_list = []
    for comment in comments:
        if not comment.parent_id:
            comments_list.append(comment)
            if created_comment_id and comment.id == created_comment_id:
                page = math.ceil(len(comments_list) / size)
            if comment.children:
                for child in comment.children:
                    comments_list.append(child)
                    if created_comment_id and child.id == created_comment_id:
                        page = math.ceil(len(comments_list) / size)
    if created_comment_id:
        return page - 1
    else:
        return comments_list[(page * size) : ((page + 1) * size)]


def verify_location_this_post(session: Session, board_name: str, post_id: int, user_id: int=None):
    if board_name == "best":
        best_post = c.get_best_post(session, id=post_id)
        if not best_post:
            raise HTTPException(status_code=404, detail="없음")
        post = best_post.post
    else:
        board = c.get_board(session, board_name)
        if not board:
            raise HTTPException(status_code=404, detail="없음")
        if user_id:
            post = c.get_post(session, post_id, board_id=board.id, user_id=user_id)
        else:
            post = c.get_post(session, post_id, board_id=board.id)
        if not post:
            raise HTTPException(status_code=404, detail="없음")
    return post


def post_up(post: Post, exist_recommend: bool):
    post.post_up += 1
    if exist_recommend:
        post.post_down -= 1
    post.recommend_count = post.post_up - post.post_down
    return post

    
def post_down(post: Post, exist_recommend: bool):
    post.post_down += 1
    if exist_recommend:
        post.post_up -= 1
    post.recommend_count = post.post_up - post.post_down
    return post
