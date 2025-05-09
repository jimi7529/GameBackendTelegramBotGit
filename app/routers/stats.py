from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter(prefix="/api", tags=["game"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users/sync")
def sync_user(user: schemas.UserSync, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter_by(telegram_id=user.telegram_id).first()
    
    if not db_user:
        db_user = models.User(
            telegram_id=user.telegram_id,
            username=user.username or "unknown"
        )
        db.add(db_user)
    else:
        db_user.username = user.username or db_user.username  # Don't overwrite with None
    
    try:
        db.commit()
        db.refresh(db_user)  # Ensure user data is refreshed, so `db_user.id` is updated.
        print(f"User {db_user.id} successfully committed!")
    except Exception as e:
        db.rollback()
        print(f"Failed to commit user: {str(e)}")
        return {"status": "error", "details": str(e)}
    
    return {"status": "synced", "user_id": db_user.id}


@router.post("/games/report")
def report_game(report: schemas.GameReport, db: Session = Depends(get_db)):
    game_type = db.query(models.GameType).filter_by(name=report.game_type).first()
    if not game_type:
        game_type = models.GameType(name=report.game_type)
        db.add(game_type)
        db.commit()
        db.refresh(game_type)

    room = db.query(models.GameRoom).filter_by(code=report.room_code).first()
    if not room:
        room = models.GameRoom(code=report.room_code, game_type_id=game_type.id)
        db.add(room)
        db.commit()
        db.refresh(room)

    for p in report.players:
        user = db.query(models.User).filter_by(telegram_id=p.telegram_id).first()
        if not user:
            user = models.User(telegram_id=p.telegram_id, username="unknown")
            db.add(user)
            db.commit()
            db.refresh(user)

        session = models.GameSession(
            user_id=user.id,
            room_id=room.id,
            result=p.result,
            score=p.score,
            duration_seconds=report.duration_seconds
        )
        db.add(session)

        lb = db.query(models.LeaderboardEntry).filter_by(user_id=user.id, game_type_id=game_type.id).first()
        if not lb:
            lb = models.LeaderboardEntry(user_id=user.id, game_type_id=game_type.id)
            db.add(lb)
        if p.result == "win":
            lb.wins += 1
        elif p.result == "loss":
            lb.losses += 1
        elif p.result == "draw":
            lb.draws += 1

    db.commit()
    return {"status": "recorded"}


@router.get("/leaderboard", response_model=List[schemas.LeaderboardEntryOut])
def get_leaderboard(game_type: str, db: Session = Depends(get_db)):
    game = db.query(models.GameType).filter_by(name=game_type).first()
    if not game:
        return []

    entries = (
        db.query(models.LeaderboardEntry)
        .filter_by(game_type_id=game.id)
        .join(models.User)
        .order_by(models.LeaderboardEntry.wins.desc())
        .all()
    )

    return [
        schemas.LeaderboardEntryOut(
            telegram_id=e.user.telegram_id,
            username=e.user.username,
            wins=e.wins,
            losses=e.losses,
            draws=e.draws
        )
        for e in entries
    ]
    
@router.get("/debug/users")
def debug_users(db: Session = Depends(get_db)):
        users = db.query(models.User).all()
        return [{"id": u.id, "telegram_id": u.telegram_id, "username": u.username} for u in users]


@router.get("/users/{telegram_id}/stats", response_model=schemas.UserStatsOut)
def user_stats(telegram_id: str, game_type: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(telegram_id=telegram_id).first()
    if not user:
        return {"error": "User not found"}

    game = db.query(models.GameType).filter_by(name=game_type).first()
    if not game:
        return {"error": "Game not found"}

    sessions = (
        db.query(models.GameSession)
        .join(models.GameRoom)
        .filter(models.GameSession.user_id == user.id, models.GameRoom.game_type_id == game.id)
        .all()
    )

    wins = sum(1 for s in sessions if s.result == "win")
    losses = sum(1 for s in sessions if s.result == "loss")
    draws = sum(1 for s in sessions if s.result == "draw")
    total_score = sum(s.score or 0 for s in sessions)
    avg_score = total_score / len(sessions) if sessions else 0

    return schemas.UserStatsOut(
        total_games=len(sessions),
        wins=wins,
        losses=losses,
        draws=draws,
        average_score=avg_score
    )
    


