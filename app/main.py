from fastapi import FastAPI
from .routers import game, auth, debug  # ← NEW
from .routers import stats  # ← NEW
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to the bot host if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(game.router)
app.include_router(stats.router)
app.include_router(debug.router)  # ← NEW
