from EventBus import EventBus

class ScoreManager:
    """Handles game scoring via event subscriptions."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.player1_score = 0
        self.player2_score = 0

        # Piece score values
        self.piece_values = {
            "P": 1,  # Pawn
            "N": 3,  # Knight
            "B": 3,  # Bishop
            "R": 5,  # Rook
            "Q": 9   # Queen
        }

        # Subscribe to relevant events
        self.event_bus.subscribe("piece_captured", self._on_piece_captured)
        self.event_bus.subscribe("game_started", self._on_game_started)
        self.event_bus.subscribe("game_ended", self._on_game_ended)
    
    def _on_piece_captured(self, data):
        # Update score when a piece is captured
        player = data['player']
        captured_piece = data['captured_piece']
        piece_type = captured_piece[0]
        points = self.piece_values.get(piece_type, 0)

        if player == 1:
            self.player1_score += points
        else:
            self.player2_score += points

        self.event_bus.publish("score_updated", {
            "player": player,
            "new_score": self.player1_score if player == 1 else self.player2_score,
            "player1_score": self.player1_score,
            "player2_score": self.player2_score
        })
    
    def _on_game_started(self, data):
        # Reset scores at game start
        self.player1_score = 0
        self.player2_score = 0
    
    def _on_game_ended(self, data):
        # Publish final scores and winner
        if self.player1_score > self.player2_score:
            winner = 1
        elif self.player2_score > self.player1_score:
            winner = 2
        else:
            winner = None

        self.event_bus.publish("game_result", {
            "winner": winner,
            "player1_score": self.player1_score,
            "player2_score": self.player2_score
        })
    
    def get_scores(self):
        # Return current scores
        return {
            "player1": self.player1_score,
            "player2": self.player2_score
        }
