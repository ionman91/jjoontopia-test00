"""
    lineup 등록하는 template
"""
"""
승부 예측 IN
data = {
    game_date: "20230613",
    match_prediction: [
        {
            "gameid": "20230613_PIT@CHC",
            "predict": "W",
        },
            "gameid": "20230613_MIL@MIN",
            "predict": "W"
        },
        {
            "gameid": "20230613_ATL@DET",
            "predict": "W"
        }
    ]
}

승부 예측 저장시
data = {
    game_date: "20230613",
    match_prediction: [
        {
            "gameid": "20230613_PIT@CHC",
            "predict": "W",
            "result": "W"
        },
            "gameid": "20230613_MIL@MIN",
            "predict": "W",
            "result": "L"
        },
        {
            "gameid": "20230613_ATL@DET",
            "predict": "W",
            "result": "P"
        }
    ]
}
"""
"""
[
    {
        "position": "RF", "playerID": 630123, 
        "ename": "Holding", "kname": "에르난데스", "daily_score": 0.0
    }
]
"""
"""
유저가 fluser 안에서 모든 선수들을 선택한 횟수를 저장한다.
fluser.total_selected_lineup
data = {
    "623132" : 12, "602314": 12
}
"""