from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String)

    game_sessions = relationship("GameSession", back_populates="user")


class GameType(Base):
    __tablename__ = "game_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String, nullable=True)


class GameRoom(Base):
    __tablename__ = "game_rooms"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    game_type_id = Column(Integer, ForeignKey("game_types.id"))
    is_active = Column(Boolean, default=True)

    game_type = relationship("GameType")
    sessions = relationship("GameSession", back_populates="room")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GameSession(Base):
    __tablename__ = "game_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("game_rooms.id"))
    result = Column(String)
    score = Column(Integer)
    duration_seconds = Column(Integer)
    
    user = relationship("User", back_populates="game_sessions")
    room = relationship("GameRoom", back_populates="sessions")


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_type_id = Column(Integer, ForeignKey("game_types.id"))
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)

    user = relationship("User")
    game_type = relationship("GameType")

