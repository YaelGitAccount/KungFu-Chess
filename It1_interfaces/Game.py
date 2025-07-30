import pathlib
import time, cv2
import csv
from typing import List, Tuple, Optional
from Board   import Board
from Command import Command
from Piece   import Piece
from MovesLog import MovesLog
from EventBus import EventBus
from KeyboardController import KeyboardController
from ColorScheme import Colors
from UIManager import UIManager


class InvalidBoard(Exception): ...


class Game:
    def __init__(self, pieces: List[Piece], board: Board):
        """Initialize the game with pieces, board, and two-player support."""
        self.pieces = {p.piece_id: p for p in pieces}
        self.board = board
        self.start_time = None
        self.event_bus = EventBus()
        
        # Pass event_bus to all pieces
        for piece in self.pieces.values():
            piece.event_bus = self.event_bus

        # Player 1 (arrows) state - Black pieces, starts at top-left (0,0)
        self.p1_cursor_pos = [0, 0]
        self.p1_selected_piece_id = None
        self.p1_ui_state = "selecting"  # "selecting" or "moving"
        
        # Player 2 (WASD) state - White pieces, starts at bottom-left (7,0)
        self.p2_cursor_pos = [7, 0]
        self.p2_selected_piece_id = None
        self.p2_ui_state = "selecting"  # "selecting" or "moving"
        
        self.keyboard = KeyboardController()
        self.running = True

        # Move logs for both players
        self.player1_moves = MovesLog("Player 1", "B")  # Black
        self.player2_moves = MovesLog("Player 2", "W")  # White
        
        # Scores - handled by ScoreManager
        self.player1_score = 0
        self.player2_score = 0
        
        self.ui_manager = UIManager(self.event_bus)
        self.ui_manager.set_game_reference(self)

    def game_time_ms(self) -> int:
        """Return the current game time in milliseconds."""
        if self.start_time is None:
            self.start_time = time.time()
            return 0
        return int((time.time() - self.start_time) * 1000)

    def clone_board(self) -> Board:
        """Return a copy of the board for drawing."""
        return self.board.clone()

    def _get_piece_owner(self, piece_id: str) -> Optional[int]:
        """Determine which player owns a piece based on piece_id."""
        piece_lower = piece_id.lower()
        
        # Black pieces (Player 1) - pieces containing 'b'
        if 'b' in piece_lower and 'w' not in piece_lower:
            return 1
        # White pieces (Player 2) - pieces containing 'w'
        elif 'w' in piece_lower:
            return 2
        
        return None

    def _can_player_control_piece(self, player: int, piece_id: str) -> bool:
        """Check if a player can control a specific piece."""
        return self._get_piece_owner(piece_id) == player

    def _is_move_valid(self, piece_id: str, target_row: int, target_col: int) -> bool:
        """Check if a move is valid for the given piece to the target position."""
        if piece_id not in self.pieces:
            return False
            
        piece = self.pieces[piece_id]
        current_pos = piece.get_current_cell()
        current_row = int(round(current_pos[0]))
        current_col = int(round(current_pos[1]))
        
        # Check path for sliding pieces (rook, bishop, queen)
        piece_type = piece_id[:2]
        if piece_type[0] in ['R', 'B', 'Q']:
            if not self._is_path_clear(current_row, current_col, target_row, target_col):
                return False
        
        # Special rules for pawns
        if piece_type in ['PW', 'PB']:
            return self._is_pawn_move_valid(piece_id, current_row, current_col, target_row, target_col)
        
        # Check if there's a piece at target
        piece_at_target = self._get_piece_at_position(target_row, target_col)
        if piece_at_target:
            owner_moving = self._get_piece_owner(piece_id)
            owner_target = self._get_piece_owner(piece_at_target.piece_id)
            
            if owner_moving == owner_target:
                return False
        
        test_cmd = Command(
            timestamp=self.game_time_ms(),
            piece_id=piece_id,
            type="Move",
            params=[str(target_row), str(target_col)]
        )
        
        return piece.is_command_possible(test_cmd)

    def _get_piece_at_position(self, row: int, col: int) -> Optional[Piece]:
        """Find piece at given board position."""
        for piece in self.pieces.values():
            piece_pos = piece.get_current_cell()
            piece_row = int(round(piece_pos[0]))
            piece_col = int(round(piece_pos[1]))
            if piece_row == row and piece_col == col:
                return piece
        return None

    def start_user_input_thread(self):
        """Initialize control system."""
        pass

    def _handle_keyboard_input(self) -> bool:
        """Handle keyboard input for both players."""
        action = self.keyboard.get_action()
        if not action:
            return True

        now_ms = self.game_time_ms()

        # General controls
        if action == "QUIT":
            self.running = False
            return False
        elif action == "ESC":
            self._handle_escape()
            return True

        # Player 1 controls (Arrow keys + Space + Enter)
        if action == "MOVE_UP":
            self._move_cursor(1, -1, 0)
        elif action == "MOVE_DOWN":
            self._move_cursor(1, 1, 0)
        elif action == "MOVE_LEFT":
            self._move_cursor(1, 0, -1)
        elif action == "MOVE_RIGHT":
            self._move_cursor(1, 0, 1)
        elif action == "SPACE":
            self._handle_action_key(1, now_ms)
        elif action == "ENTER":
            self._handle_jump_key(1, now_ms)

        # Player 2 controls (WASD + Tab + Shift)
        elif action == "W":
            self._move_cursor(2, -1, 0)
        elif action == "S":
            self._move_cursor(2, 1, 0)
        elif action == "A":
            self._move_cursor(2, 0, -1)
        elif action == "D":
            self._move_cursor(2, 0, 1)
        elif action == "SHIFT":
            self._handle_action_key(2, now_ms)
        elif action == "TAB":
            self._handle_jump_key(2, now_ms)

        return True

    def _move_cursor(self, player: int, dr: int, dc: int):
        """Move cursor within board bounds for specified player."""
        if player == 1:
            cursor_pos = self.p1_cursor_pos
        else:
            cursor_pos = self.p2_cursor_pos
            
        new_row = max(0, min(self.board.H_cells - 1, cursor_pos[0] + dr))
        new_col = max(0, min(self.board.W_cells - 1, cursor_pos[1] + dc))
        
        if new_row != cursor_pos[0] or new_col != cursor_pos[1]:
            if player == 1:
                self.p1_cursor_pos = [new_row, new_col]
            else:
                self.p2_cursor_pos = [new_row, new_col]

    def _handle_action_key(self, player: int, now_ms: int):
        """Handle single button toggle - select/move/deselect."""
        if player == 1:
            cursor_pos = self.p1_cursor_pos
            ui_state = self.p1_ui_state
            selected_piece_id = self.p1_selected_piece_id
        else:
            cursor_pos = self.p2_cursor_pos
            ui_state = self.p2_ui_state
            selected_piece_id = self.p2_selected_piece_id
        
        piece_at_cursor = self._get_piece_at_position(cursor_pos[0], cursor_pos[1])
        
        if ui_state == "selecting":
            # Try to select a piece
            if piece_at_cursor and self._can_player_control_piece(player, piece_at_cursor.piece_id):
                # Check if piece is in idle state
                if piece_at_cursor.is_idle():
                    if player == 1:
                        self.p1_selected_piece_id = piece_at_cursor.piece_id
                        self.p1_ui_state = "moving"
                    else:
                        self.p2_selected_piece_id = piece_at_cursor.piece_id
                        self.p2_ui_state = "moving"
        
        elif ui_state == "moving" and selected_piece_id:
            # Check if cursor is on the selected piece (deselect)
            selected_piece = self.pieces[selected_piece_id]
            selected_pos = selected_piece.get_current_cell()
            selected_row = int(round(selected_pos[0]))
            selected_col = int(round(selected_pos[1]))
            
            if cursor_pos[0] == selected_row and cursor_pos[1] == selected_col:
                # Deselect the piece
                if player == 1:
                    self.p1_selected_piece_id = None
                    self.p1_ui_state = "selecting"
                else:
                    self.p2_selected_piece_id = None
                    self.p2_ui_state = "selecting"
            else:
                # Try to move the piece
                if self._is_move_valid(selected_piece_id, cursor_pos[0], cursor_pos[1]):
                    from_pos = selected_piece.get_current_cell()
                    from_pos_tuple = (int(round(from_pos[0])), int(round(from_pos[1])))
                    
                    piece_at_target = self._get_piece_at_position(cursor_pos[0], cursor_pos[1])
                    captured_piece_id = None
                    
                    if piece_at_target:
                        # Can only capture piece if it's in idle state
                        if not piece_at_target.is_idle():
                            return
                            
                        captured_piece_id = piece_at_target.piece_id
                        
                        # Check if captured piece is a king
                        if captured_piece_id.startswith('K'):
                            # King captured - game over
                            winner = player
                            loser = 2 if player == 1 else 1
                            
                            self.game_over_info = {
                                "winner": winner,
                                "loser": loser,
                                "reason": "king_captured",
                                "timestamp": self.game_time_ms()
                            }
                            
                            self.event_bus.publish("game_over", {
                                "winner": winner,
                                "loser": loser,
                                "reason": "king_captured"
                            })
                        
                        del self.pieces[captured_piece_id]
                        
                        self.event_bus.publish("piece_captured", {
                            "player": player,
                            "capturing_piece": selected_piece_id,
                            "captured_piece": captured_piece_id,
                            "position": tuple(cursor_pos)
                        })
                    
                    cmd = Command(
                        timestamp=now_ms,
                        piece_id=selected_piece_id,
                        type="Move",
                        params=[str(cursor_pos[0]), str(cursor_pos[1])]
                    )
                    
                    self.event_bus.publish("piece_moved", {
                        "player": player,
                        "piece_id": selected_piece_id,
                        "from": from_pos_tuple,
                        "to": tuple(cursor_pos),
                        "captured": captured_piece_id
                    })
                    
                    self._process_input(cmd)
                    
                    if player == 1:
                        self.player1_moves.add_move(selected_piece_id, from_pos_tuple, tuple(cursor_pos))
                    else:
                        self.player2_moves.add_move(selected_piece_id, from_pos_tuple, tuple(cursor_pos))
                    
                    if player == 1:
                        self.p1_selected_piece_id = None
                        self.p1_ui_state = "selecting"
                    else:
                        self.p2_selected_piece_id = None
                        self.p2_ui_state = "selecting"

    def _handle_escape(self):
        """Handle ESC key - cancel selections."""
        if self.p1_ui_state == "moving":
            self.p1_selected_piece_id = None
            self.p1_ui_state = "selecting"
        if self.p2_ui_state == "moving":
            self.p2_selected_piece_id = None
            self.p2_ui_state = "selecting"
    
    def _handle_jump_key(self, player: int, now_ms: int):
        """Handle jump command for selected piece or piece at cursor."""
        # First check if player has a selected piece
        if player == 1:
            selected_piece_id = self.p1_selected_piece_id
            cursor_pos = self.p1_cursor_pos
        else:
            selected_piece_id = self.p2_selected_piece_id
            cursor_pos = self.p2_cursor_pos
        
        # Use selected piece if available, otherwise piece at cursor
        if selected_piece_id and selected_piece_id in self.pieces:
            piece_to_jump = self.pieces[selected_piece_id]
            piece_id = selected_piece_id
        else:
            piece_at_cursor = self._get_piece_at_position(cursor_pos[0], cursor_pos[1])
            if piece_at_cursor and self._can_player_control_piece(player, piece_at_cursor.piece_id):
                piece_to_jump = piece_at_cursor
                piece_id = piece_at_cursor.piece_id
            else:
                return
        
        # Check if piece can jump
        cmd = Command(
            timestamp=now_ms,
            piece_id=piece_id,
            type="Jump",
            params=[]
        )
        
        if piece_to_jump.is_command_possible(cmd):
            # Get current position before jump
            current_pos = piece_to_jump.get_current_cell()
            from_pos_tuple = (int(round(current_pos[0])), int(round(current_pos[1])))
            
            self._process_input(cmd)
            
            # Publish jump event
            self.event_bus.publish("piece_jumped", {
                "piece_id": piece_id,
                "player": player,
                "position": from_pos_tuple
            })
            
            # Record jump as a move (same position)
            if player == 1:
                self.player1_moves.add_move(piece_id, from_pos_tuple, from_pos_tuple, move_type="Jump")
            else:
                self.player2_moves.add_move(piece_id, from_pos_tuple, from_pos_tuple, move_type="Jump")

    def _process_input(self, cmd: Command):
        """Process input command for specific piece."""
        if cmd.piece_id in self.pieces:
            piece = self.pieces[cmd.piece_id]
            if piece.is_command_possible(cmd):
                piece.on_command(cmd, cmd.timestamp)

    def _draw(self):
        """Draw the current game state."""
        current_board = self.clone_board()
        
        # Draw all pieces
        now = self.game_time_ms()
        for piece in self.pieces.values():
            piece.draw_on_board(current_board, now)
            
        # Use UIManager to draw all UI elements
        self.ui_manager.draw_all_ui_elements(current_board)
        
        self.rendered_board = current_board

    def _show(self) -> bool:
        """Display the current frame."""
        if hasattr(self, 'rendered_board'):
            cv2.imshow("Two-Player Chess Game", self.rendered_board.img.img)
            cv2.waitKey(1)

            try:
                if cv2.getWindowProperty("Two-Player Chess Game", cv2.WND_PROP_VISIBLE) < 1:
                    self.running = False
                    return False
            except cv2.error:
                self.running = False
                return False

        return True

    def run(self):
        """Main game loop."""
        self.start_user_input_thread()
        self.event_bus.publish("game_started")

        start_ms = self.game_time_ms()
        for piece in self.pieces.values():
            idle_cmd = Command(start_ms, piece.piece_id, "idle", [])
            piece.reset(idle_cmd)

        while self.running and not self._is_win():
            now = self.game_time_ms()

            # Update pieces
            for piece in self.pieces.values():
                piece.update(now)

            # Handle input
            if not self._handle_keyboard_input():
                break

            # Draw and display
            self._draw()
            if not self._show():
                break
                
            # Check if game should end after move animation completes
            if hasattr(self, 'game_over_info') and self.game_over_info:
                game_over_time = self.game_over_info.get('timestamp', 0)
                if now - game_over_time > 1500:  # 1.5 seconds after king capture
                    self.running = False

            time.sleep(0.016)  # ~60 FPS
            
        # After game ends, show final state for a moment
        if hasattr(self, 'game_over_info'):
            # Draw the final board with game over message
            self._draw()
            cv2.imshow("Two-Player Chess Game", self.rendered_board.img.img)
            cv2.waitKey(0)  # Wait for any key press
            
        self.event_bus.publish("game_ended")
        self.keyboard.stop()
        cv2.destroyAllWindows()

    def _is_win(self) -> bool:
        """Check if the game has ended."""
        return not self.running
    
    def _is_pawn_move_valid(self, piece_id: str, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Check if pawn move is valid with special pawn rules."""
        piece_type = piece_id[:2]
        is_white = piece_type == 'PW'
        
        # Calculate movement direction
        row_diff = to_row - from_row
        col_diff = to_col - from_col
        
        # Check direction (white goes up, black goes down)
        if is_white and row_diff >= 0:  # White must move up (negative row)
            return False
        if not is_white and row_diff <= 0:  # Black must move down (positive row)
            return False
        
        # Get piece at target position
        piece_at_target = self._get_piece_at_position(to_row, to_col)
        
        # Check if it's a capture move (diagonal)
        if abs(col_diff) == 1 and abs(row_diff) == 1:
            # Diagonal move - must capture enemy piece
            if not piece_at_target:
                return False  # No piece to capture
            
            # Check if it's enemy piece
            owner_moving = self._get_piece_owner(piece_id)
            owner_target = self._get_piece_owner(piece_at_target.piece_id)
            
            return owner_moving != owner_target  # Can only capture enemy
        
        # Forward move (not diagonal)
        elif col_diff == 0:
            # Cannot capture when moving forward
            if piece_at_target:
                return False
            
            # Check if it's first move (can move 2 squares)
            if abs(row_diff) == 2:
                # White pawns start at row 6, black pawns at row 1
                if is_white and from_row != 6:
                    return False
                if not is_white and from_row != 1:
                    return False
                
                # Check if path is clear
                middle_row = from_row + (1 if not is_white else -1)
                if self._get_piece_at_position(middle_row, from_col):
                    return False
            
            # Normal move - one square forward
            elif abs(row_diff) != 1:
                return False
        
        else:
            # Invalid move (not forward or diagonal)
            return False
        
        return True
    
    def _is_path_clear(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Check if path is clear between two positions (for sliding pieces)."""
        # Calculate direction
        dr = 0 if from_row == to_row else (1 if to_row > from_row else -1)
        dc = 0 if from_col == to_col else (1 if to_col > from_col else -1)
        
        # Check each position along the path
        curr_row, curr_col = from_row + dr, from_col + dc
        
        while (curr_row, curr_col) != (to_row, to_col):
            if self._get_piece_at_position(curr_row, curr_col):
                return False
            curr_row += dr
            curr_col += dc
        
        return True

    @staticmethod
    def load_board_from_csv(csv_path: pathlib.Path) -> List[Tuple[str, int, int]]:
        """Load initial piece positions from CSV file."""
        pieces_data = []
        
        try:
            with open(csv_path, 'r') as file:
                csv_reader = csv.reader(file)
                for row_idx, row in enumerate(csv_reader):
                    for col_idx, cell in enumerate(row):
                        cell = cell.strip()
                        if cell:
                            pieces_data.append((cell, row_idx, col_idx))
                            
        except FileNotFoundError:
            raise FileNotFoundError(f"Board CSV file not found: {csv_path}")
        except Exception as e:
            raise InvalidBoard(f"Error loading board from CSV: {e}")
        
        return pieces_data