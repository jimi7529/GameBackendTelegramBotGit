import logging, random, string
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas, database
from ..game_engines import rps
from ..schemas import RpsMoveRequest, RoomRequest
from fastapi import HTTPException

# Logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/game", tags=["game"])

# In-memory move store
rps_move_store = {}

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check
@router.get("/health")
def health_check():
    return {"status": "OK"}

# Add RPS game type (once)
@router.post("/add-rps-game-type")
def add_rps_game_type(db: Session = Depends(get_db)):
    if db.query(models.GameType).filter_by(name="rps").first():
        return {"message": "'rps' game type already exists."}
    db.add(models.GameType(name="rps"))
    db.commit()
    return {"message": "'rps' game type added successfully"}

# Room creation
@router.post("/create-room")
def create_game_room(data: RoomRequest, db: Session = Depends(get_db)):
    if not db.query(models.GameType).filter_by(name=data.game_type).first():
        return {"error": "Invalid game type"}

    print(data.telegram_id)
    if not db.query(models.User).filter_by(telegram_id=data.telegram_id).first():
        return {"error": "User not found"}

    # Clean up inactive rooms
    db.query(models.GameRoom).filter_by(is_active=False).delete()

    # Unique room code
    while True:
        room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not db.query(models.GameRoom).filter_by(code=room_code).first():
            break

    room = models.GameRoom(code=room_code, game_type_id=1, is_active=True)  # assuming "rps" has ID 1
    db.add(room)
    db.commit()
    return {"room_code": room.code}

# Register RPS move
@router.post("/rps/move")
def play_rps_move(data: RpsMoveRequest, db: Session = Depends(get_db)):
    room = db.query(models.GameRoom).filter_by(code=data.room_code).first()
    if not room:
        logger.error(f"Room {data.room_code} not found")
        raise HTTPException(status_code=404, detail="Room not found")

    if not room.is_active:
        logger.error(f"Room {data.room_code} is not active")
        raise HTTPException(status_code=400, detail="Room is not active")

    moves = rps_move_store.setdefault(data.room_code, {})
    moves[data.telegram_id] = data.move

    if len(moves) < 2:
        return {"status": "Move registered, waiting for opponent"}

    return {"status": "Ready to end session", "players": list(moves.keys())}

# End RPS session
@router.post("/end-rps-session")
def end_rps_session(room_code: str, db: Session = Depends(get_db)):
    # Check if the room exists
    room = db.query(models.GameRoom).filter_by(code=room_code).first()
    if not room:
        logger.error(f"Room {room_code} not found")
        return {"error": "Room not found"}

    # Ensure the room is active
    if not room.is_active:
        logger.error(f"Room {room_code} is not active")
        return {"error": "Room is not active"}

    # Retrieve moves for the room from the in-memory store
    moves = rps_move_store.get(room_code)
    if not moves or len(moves) < 2:
        logger.error(f"Not enough moves for room {room_code}. Moves: {moves}")
        return {"error": "Not enough moves"}

    # Extract player IDs and moves
    players = list(moves.items())
    player1_id, move1 = players[0]
    player2_id, move2 = players[1]

    # Determine winner using the game logic
    result = rps.play(move1, move2)

    # Fetch user details from the database
    user1 = db.query(models.User).filter_by(telegram_id=player1_id).first()
    user2 = db.query(models.User).filter_by(telegram_id=player2_id).first()

    if not user1 or not user2:
        logger.error(f"User1 (ID: {player1_id}) or User2 (ID: {player2_id}) not found in DB")
        return {"error": "One or both players not found in DB"}

    # Function to map game result to leaderboard update
    def map_result(player, winner):
        if winner == player:
            return "win", 1
        elif winner == "draw":
            return "draw", 0
        return "loss", 0

    # Map results for both players
    winner = result.get("result")
    outcome1, score1 = map_result("p1", winner)
    outcome2, score2 = map_result("p2", winner)


    # Save game session results
    db.add(models.GameSession(user_id=user1.id, result=outcome1, score=score1))
    db.add(models.GameSession(user_id=user2.id, result=outcome2, score=score2))

    # Update leaderboard for both players
    def update_leaderboard(user_id: int, outcome: str):
        lb = db.query(models.LeaderboardEntry).filter_by(user_id=user_id).first()
        if not lb:
            lb = models.LeaderboardEntry(user_id=user_id, wins=0, losses=0, draws=0)
            db.add(lb)
        if outcome == "win":
            lb.wins += 1
        elif outcome == "loss":
            lb.losses += 1
        elif outcome == "draw":
            lb.draws += 1

    update_leaderboard(user1.id, outcome1)
    update_leaderboard(user2.id, outcome2)

    # Mark the room as inactive (game over)
    room.is_active = False

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database commit failed: {e}")
        return {"error": f"Database error: {e}"}

    # Clear the temporary moves from the in-memory store
    del rps_move_store[room_code]

    return {
        "message": "Game session ended",
        "player_1": player1_id,
        "move_1": move1,
        "player_2": player2_id,
        "move_2": move2,
        "result": result
    }