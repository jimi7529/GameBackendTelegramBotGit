# game_engines/rock_paper_scissors.py

from typing import Dict, Optional

CHOICES = ["rock", "paper", "scissors"]

# Regole: cosa batte cosa
WIN_MAP = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock"
}

def play(p1_choice: str, p2_choice: str) -> Dict[str, Optional[str]]:
    """
    Determina il risultato tra due giocatori.
    Restituisce un dizionario con il risultato.
    """
    p1 = p1_choice.lower()
    p2 = p2_choice.lower()

    if p1 not in CHOICES or p2 not in CHOICES:
        return {"error": "Invalid choice"}

    if p1 == p2:
        return {"result": "draw"}

    if WIN_MAP[p1] == p2:
        return {"result": "p1"}
    else:
        return {"result": "p2"}
