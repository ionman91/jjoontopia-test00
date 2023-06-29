from fastapi import Request, HTTPException
from datetime import datetime, timedelta


def check_valid_request(request: Request):
    error = request.state.exceptions
    print("request.state.user === ", request.state.user)
    if error:
        raise HTTPException(status_code=error["status_code"], detail=error["msg"])
    return request.state


def keys_to_remove(dict, keys):
    for key in keys:
        dict.pop(key, None)


"""
    일반 date 정보가 넘어왔을 때 하루 전날 date 로 변환한다. 
"""
def date_to_previous_day(date: str):
    now_date = datetime.strptime(date, "%Y%m%d")
    previous_day = now_date - timedelta(days=1)

    previous_day_str = previous_day.strftime("%Y%m%d")
    return previous_day_str
