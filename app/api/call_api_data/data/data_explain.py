"""
    >>> Pitching
    BB: 볼넷(투수가 공을 넷볼로 친 경우)의 수를 나타냅니다.
    Balk: 볼커밋(투수의 반칙)의 수를 나타냅니다.
    Wild Pitch: 와일드 피치(투수가 공을 제대로 조절하지 못한 경우)의 수를 나타냅니다.
    decision: 투수의 경기 결과를 나타냅니다 (L: 패배).
    Flyouts: 뜬공 아웃의 수를 나타냅니다.
    Inherited Runners: 상대 팀에서 상속받은 주자의 수를 나타냅니다.
    H: 피안타 허용 수를 나타냅니다.
    HR: 피홈런 허용 수를 나타냅니다.
    ER: 자책점 수를 나타냅니다.
    Strikes: 스트라이크(정확한 공 스트라이크)의 수를 나타냅니다.
    Inherited Runners Scored: 상대 팀에서 상속받은 주자들 중 득점한 주자의 수를 나타냅니다.
    Groundouts: 땅볼 아웃의 수를 나타냅니다.
    R: 실점 수를 나타냅니다.
    pitchingOrder: 투구 순서를 나타냅니다.
    ERA: 평균자책점을 나타냅니다.
    InningsPitched: 투구 이닝 수를 나타냅니다.
    Batters Faced: 상대 타자에 대한 투구 수를 나타냅니다.
    SO: 삼진(타자를 삼진으로 잡은 경우)의 수를 나타냅니다.
    Pitches: 투구 수를 나타냅니다.

    >>> Fielding
    Passed Ball: 패스트볼이나 커브볼을 잡을 때 실수로 공을 놓친 경우를 나타냅니다. 값은 해당 경기에서의 Passed Ball 수를 나타냅니다.
    Outfield assists: 외야수가 공을 받은 후 잡는 주자를 아웃시키는 경우를 나타냅니다. 값은 해당 경기에서의 Outfield Assists 수를 나타냅니다.
    E: 에러(수비 오류)를 나타냅니다. 값은 해당 경기에서의 에러 수를 나타냅니다.
    Pickoffs: 투수가 베이스 주자를 픽오프하여 잡는 경우를 나타냅니다. 값은 해당 경기에서의 Pickoffs 수를 나타냅니다.

    >>> Hitting
    BB: 볼넷(베이스 온 볼)을 받은 횟수를 나타냅니다.
    AB: 타수(타석에 들어간 횟수)를 나타냅니다.
    battingOrder: 타순을 나타냅니다.
    H: 안타(타석에서 베이스에 도달하는 성공적인 타격)를 기록한 횟수를 나타냅니다.
    IBB: 고의 사구(계획적으로 투수가 타자에게 고의로 볼을 던지는 것)를 받은 횟수를 나타냅니다.
    substitutionOrder: 교체 순서를 나타냅니다.
    HR: 홈런(볼을 장타하여 홈 베이스까지 달리는 타격)을 기록한 횟수를 나타냅니다.
    TB: 총 루타(타격으로 얻은 베이스 수)를 나타냅니다.
    3B: 3루타(타구가 외야를 돌아 세 베이스까지 달리는 타격)를 기록한 횟수를 나타냅니다.
    GIDP: 병살타(타자가 살아있는 주자를 아웃시키는 타격)를 기록한 횟수를 나타냅니다.
    2B: 2루타(타구가 외야를 돌아 두 베이스까지 달리는 타격)를 기록한 횟수를 나타냅니다.
    R: 득점(주자가 홈 베이스까지 도착하여 득점하는 것)을 기록한 횟수를 나타냅니다.
    AVG: 타율(타자의 안타 비율)을 나타냅니다.
    SF: 희생 플라이(타자가 공을 치지 않고 볼을 상대로 잡아 희생하는 것)를 기록한 횟수를 나타냅니다.
    SAC: 희생 번트(타자가 공을 치지 않고 볼을 상대로 내는 것)를 기록한 횟수를 나타냅니다.
    HBP: 사구(투수가 공을 던져 타자를 몸에 맞히는 것)를 받은 횟수를 나타냅니다.
    RBI: 타점(주자를 홈 베이스로 이끌어들이는 타격)를 기록한 횟수를 나타냅니다.
    SO: 삼진(타자가 스트라이크 아웃되는 것)을 당한 횟수를 나타냅니다.
    LOB: 타자 타율을 뜻함 (여기서는 그것을 뜻하는거 같음)

    >>> BaseRunning
    CS: 도루를 시도했으나 태그 아웃당한 횟수를 나타냅니다 (Caught Stealing).
    SB: 성공적으로 도루를 성공한 횟수를 나타냅니다 (Stolen Bases).
    PO: 상대팀의 수비수에 의해 아웃당한 횟수를 나타냅니다 (Pickoffs).
"""
{
    "Pitching": {
        "BB": "2",
        "Balk": "0",
        "Wild Pitch": "0",
        "decision": "L",
        "Flyouts": "2",
        "Inherited Runners": "0",
        "H": "6",
        "HR": "0",
        "ER": "6",
        "Strikes": "58",
        "Inherited Runners Scored": "0",
        "Groundouts": "6",
        "R": "6",
        "pitchingOrder": "1",
        "ERA": "5.47",
        "InningsPitched": "4.0",
        "Batters Faced": "19",
        "SO": "3",
        "Pitches": "86"
    },
    "Fielding": {
        "Passed Ball": "0",
        "Outfield assists": "0",
        "E": "0",
        "Pickoffs": "0"
    },
    "Hitting": {
        "BB": "1",
        "AB": "2",
        "battingOrder": "7",
        "H": "0",
        "IBB": "0",
        "substitutionOrder": "0",
        "HR": "0",
        "TB": "0",
        "3B": "0",
        "GIDP": "0",
        "2B": "0",
        "R": "0",
        "AVG": ".717",
        "SF": "1",
        "SAC": "0",
        "HBP": "0",
        "RBI": "1",
        "SO": "1",
        "LOB": ".306"
    },
    "BaseRunning": {
        "CS": "0",
        "SB": "0",
        "PO": "0"
    },
}