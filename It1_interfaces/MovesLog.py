from typing import List, Tuple
import time
from datetime import datetime
import cv2
import numpy as np
from img import Img
from ColorScheme import Colors

class MovesLog:
    """Player moves log management with visual table creation."""
    
    def __init__(self, player_name: str, player_color: str):
        """Initialize moves log for a player."""
        self.player_name = player_name
        self.player_color = player_color  # "B" or "W"
        self.moves: List[dict] = []
        self.move_counter = 0
    
    def add_move(self, piece_id: str, from_pos: Tuple[int, int], to_pos: Tuple[int, int], move_type: str = "Move"):
        """Add a move to the player's log."""
        # Extract piece type (first letter)
        piece_type_code = piece_id[0] if len(piece_id) > 0 else "?"
        piece_full_name = self._get_piece_full_name(piece_type_code)
        
        # Create move record with timestamp
        if move_type == "Jump":
            notation = self._create_jump_notation(piece_full_name, from_pos)
        else:
            notation = self._create_chess_notation(piece_full_name, from_pos, to_pos)
            
        move_record = {
            "move_number": self.move_counter + 1,
            "piece_id": piece_id,
            "piece_type_code": piece_type_code,
            "piece_full_name": piece_full_name,
            "from_pos": from_pos,
            "to_pos": to_pos,
            "move_type": move_type,
            "notation": notation,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
        self.moves.append(move_record)
        self.move_counter += 1
        
    def _get_piece_full_name(self, piece_type_code: str) -> str:
        """Return full piece name by code."""
        piece_names = {
            "P": "Pawn",
            "R": "Rook",
            "N": "Knight",
            "B": "Bishop",
            "Q": "Queen",
            "K": "King"
        }
        return piece_names.get(piece_type_code, "?")
    
    def _get_piece_symbol(self, piece_name: str) -> str:
        """Get chess symbol for piece name."""
        piece_symbols = {
            "Pawn": "",       # No symbol for pawn
            "Rook": "R",
            "Knight": "N",
            "Bishop": "B",
            "Queen": "Q",
            "King": "K"
        }
        return piece_symbols.get(piece_name, "?")
        
    def _create_jump_notation(self, piece_name: str, pos: Tuple[int, int]) -> str:
        """Create notation for a jump."""
        def pos_to_chess(pos):
            """Convert (row, col) to chess notation"""
            row, col = pos
            file = chr(ord('a') + col)
            rank = str(8 - row)
            return f"{file}{rank}"
        
        piece_symbol = self._get_piece_symbol(piece_name)
        return f"{piece_symbol}{pos_to_chess(pos)} jumps"
    
    def _create_chess_notation(self, piece_name: str, from_pos: Tuple[int, int], 
                              to_pos: Tuple[int, int]) -> str:
        """Create chess notation for the move."""
        def pos_to_chess(pos):
            """Convert (row, col) to chess notation"""
            row, col = pos
            file = chr(ord('a') + col)
            rank = str(8 - row)
            return f"{file}{rank}"
        
        from_notation = pos_to_chess(from_pos)
        to_notation = pos_to_chess(to_pos)
        
        return f"{from_notation} -> {to_notation}"
    
    def create_visual_table(self, width: int = 300, max_height: int = 500, fixed_height: int = None) -> Img:
        """Create visual moves table."""
        # Design settings
        row_height = 35
        header_height = 40
        padding = 10
        
        # Get colors from central file
        bg_color, header_color, text_color, alt_row_color, border_color = Colors.get_table_colors(self.player_color)
        
        # How many moves to show to fit height
        available_height = max_height - (header_height + padding*2)
        max_moves = available_height // row_height
        
        # Show all moves from start (or as many as fit)
        moves_to_show = self.moves[:max_moves] if len(self.moves) > max_moves else self.moves
        
        # Use fixed height if provided
        if fixed_height:
            height = fixed_height
        else:
            # Calculate height based on number of moves to show
            if len(moves_to_show) == 0:
                # If no moves, create table with minimum height of 200
                height = max(200, header_height + row_height * 3 + padding * 2)
            else:
                height = header_height + len(moves_to_show) * row_height + padding * 2
            # Don't exceed max height
            height = min(height, max_height)

        # Create image with 3 channels instead of 4
        img_array = np.full((height, width, 3), bg_color, dtype=np.uint8)
        visual_img = Img()
        visual_img.img = img_array
        
        # Title
        title = f"{self.player_name} Moves"
        visual_img.put_text(title, padding, 25, Colors.TABLE_TITLE_FONT_SIZE, text_color, 2)
        
        # Separator line
        cv2.line(visual_img.img, (padding, header_height-5), 
                (width-padding, header_height-5), header_color, 2)
        
        # Column headers
        y_pos = header_height + 20
        visual_img.put_text("#", padding, y_pos, 0.5, text_color, 1)
        visual_img.put_text("Piece", padding + 30, y_pos, 0.5, text_color, 1)
        visual_img.put_text("Move", padding + 100, y_pos, 0.5, text_color, 1)
        visual_img.put_text("Time", padding + 200, y_pos, 0.5, text_color, 1)
        
        # Moves
        for i, move in enumerate(moves_to_show):
            y_pos = header_height + (i + 1) * row_height + 20
            
            # Alternating row background
            if i % 2 == 1:
                cv2.rectangle(visual_img.img, 
                            (5, header_height + (i + 1) * row_height - 5),
                            (width - 5, header_height + (i + 2) * row_height - 5),
                            alt_row_color, -1)
            
            # Move number
            visual_img.put_text(f"{move['move_number']}", padding, y_pos, 0.45, text_color, 1)
            
            # Piece symbol
            visual_img.put_text(move['piece_full_name'], padding + 30, y_pos, 0.6, text_color, 1)
            
            # Move
            visual_img.put_text(move['notation'], padding + 100, y_pos, 0.45, text_color, 1)
            
            # Time
            visual_img.put_text(move['timestamp'], padding + 200, y_pos, 0.4, text_color, 1)
        
        # If no moves, show message
        if len(self.moves) == 0:
            visual_img.put_text("No moves yet", padding + 50, header_height + 35, 0.5, text_color, 1)
        
        # Subtle border
        cv2.rectangle(visual_img.img, (2, 2), (width-3, height-3), border_color, 2)
        
        return visual_img
    
    def get_moves_count(self) -> int:
        """Return number of moves made by player."""
        return len(self.moves)
    
    def get_last_move(self) -> dict:
        """Return last move (or None if no moves)."""
        return self.moves[-1] if self.moves else None
    
    def get_all_moves(self) -> List[dict]:
        """Return all player moves."""
        return self.moves.copy()
    
    def get_piece_moves(self, piece_type_code: str) -> List[dict]:
        """Return all moves of specific piece type."""
        return [move for move in self.moves if move['piece_type_code'] == piece_type_code]
    
    def save_to_file(self, filename: str):
        """Save moves to file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"{self.player_name} ({self.player_color}) Move History\n")
                f.write("=" * 50 + "\n\n")
                
                for move in self.moves:
                    f.write(f"{move['move_number']:2d}. {move['notation']} "
                           f"({move['from_pos']} -> {move['to_pos']}) at {move['timestamp']}\n")
                           
        except Exception as e:
            pass
    
    def clear_history(self):
        """Clear move history."""
        self.moves.clear()
        self.move_counter = 0
    
    def undo_last_move(self) -> dict:
        """Undo last move."""
        if self.moves:
            last_move = self.moves.pop()
            self.move_counter -= 1
            return last_move
        else:
            return None
        
    def on_piece_moved(self, data):
        """Handle piece moved event."""
        if data["player"] == 1 and self.player_color == "W":
            self.add_move(data["piece_id"], data["from"], data["to"])
        elif data["player"] == 2 and self.player_color == "B":
            self.add_move(data["piece_id"], data["from"], data["to"])