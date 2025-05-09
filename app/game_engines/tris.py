def validate_move(game_state, move):
    # Validazione del movimento per il gioco del tris
    return True

def check_winner(game_state):
    # Logica per verificare se qualcuno ha vinto
    return "X" if game_state['board'] == ['X', 'X', 'X'] else None
