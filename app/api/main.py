from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.connection import db


main = APIRouter()

@main.get("/call_main_player")
async def call_main_player_api(session: Session = Depends(db.session)):
    return 