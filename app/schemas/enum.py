from enum import Enum


class MLBTeamList(str, Enum):
    LAA: str = "LAA"
    LAD: str = "LAD"
    PIT: str = "PIT"
    NYM: str = "NYM"
    MIL: str = "MIL"
    ATL: str = "ATL"
    CLE: str = "CLE"
    COL: str = "COL"
    ARI: str = "ARI"
    CHW: str = "CHW"
    TEX: str = "TEX"
    WAS: str = "WAS"
    SF: str = "SF"
    TB: str = "TB"
    CHC: str = "CHC"
    BOS: str = "BOS"
    SD: str = "SD"
    NYY: str = "NYY"
    STL: str = "STL"
    CIN: str = "CIN"
    HOU: str = "HOU"
    BAL: str = "BAL"
    OAK: str = "OAK"
    TOR: str = "TOR"
    PHI: str = "PHI"
    SEA: str = "SEA"
    KC: str = "KC"
    MIN: str = "MIN"
    DET: str = "DET"
    MIA: str = "MIA"


class PlayerPosition(str, Enum):
    DH: str = "DH"
    Base1: str = "1B"
    Base2: str = "2B"
    Base3: str = "3B"
    SS: str = "SS"
    RF: str = "RF"
    CF: str = "CF"
    LF: str = "LF"
    C: str = "C"
    P: str = "P"


class FantasyLeagueSort(str, Enum):
    MLB: str = "MLB"
    KBO: str = "KBO"


class SelectedMatchResult(str, Enum):
    W: str = "W"
    D: str = "D"
    L: str = "L"