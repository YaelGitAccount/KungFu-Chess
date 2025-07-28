from EventBus import EventBus
from datetime import datetime

class GameLogger:
    """Logs game events using event subscription."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.game_log = []
        
        # Subscribe to all game events
        self.event_bus.subscribe("game_started", self._on_game_started)
        self.event_bus.subscribe("game_ended", self._on_game_ended)
        self.event_bus.subscribe("piece_moved", self._on_piece_moved)
        self.event_bus.subscribe("piece_captured", self._on_piece_captured)
        self.event_bus.subscribe("score_updated", self._on_score_updated)
        self.event_bus.subscribe("game_result", self._on_game_result)
    
    def _log(self, event_type: str, message: str):
        """Add entry to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {event_type}: {message}"
        self.game_log.append(log_entry)
    
    def _on_game_started(self, data):
        """Log game start."""
        self._log("GAME_START", "New game started")
    
    def _on_game_ended(self, data):
        """Log game end."""
        self._log("GAME_END", "Game ended")
    
    def _on_piece_moved(self, data):
        """Log piece movement."""
        player = data['player']
        piece = data['piece_id']
        from_pos = data['from']
        to_pos = data['to']
        
        message = f"Player {player} moved {piece} from {from_pos} to {to_pos}"
        if data.get('captured'):
            message += f" (captured {data['captured']})"
        
        self._log("MOVE", message)
    
    def _on_piece_captured(self, data):
        """Log piece capture."""
        player = data['player']
        capturing = data['capturing_piece']
        captured = data['captured_piece']
        position = data['position']
        
        message = f"Player {player}: {capturing} captured {captured} at {position}"
        self._log("CAPTURE", message)
    
    def _on_score_updated(self, data):
        """Log score update."""
        message = f"Scores updated - P1: {data['player1_score']}, P2: {data['player2_score']}"
        self._log("SCORE", message)
    
    def _on_game_result(self, data):
        """Log game result."""
        winner = data.get('winner')
        p1_score = data['player1_score']
        p2_score = data['player2_score']
        
        if winner:
            message = f"Player {winner} wins! Final scores: P1={p1_score}, P2={p2_score}"
        else:
            message = f"Game tied! Final scores: P1={p1_score}, P2={p2_score}"
        
        self._log("RESULT", message)
    
    def save_log(self, filename: str = "game_log.txt"):
        """Save log to file."""
        with open(filename, 'w') as f:
            for entry in self.game_log:
                f.write(entry + '\n')
    
    def get_log(self):
        """Get current log."""
        return self.game_log.copy()