from pydantic import BaseModel
from typing import List, Optional

class UserSync(BaseModel):
    telegram_id: int
    username: Optional[str]
    

class RoomRequest(BaseModel):
    game_type: str
    telegram_id: int


class GameResultPlayer(BaseModel):
    telegram_id: int
    result: str  # "win", "loss", "draw"
    score: Optional[int] = 0


class GameReport(BaseModel):
    game_type: str
    room_code: str
    duration_seconds: Optional[int]
    players: List[GameResultPlayer]


class LeaderboardEntryOut(BaseModel):
    telegram_id: int
    username: str
    wins: int
    losses: int
    draws: int


class UserStatsOut(BaseModel):
    total_games: int
    wins: int
    losses: int
    draws: int
    average_score: float
    
    
class RpsMoveRequest(BaseModel):
    room_code: str
    telegram_id: int
    move: str
