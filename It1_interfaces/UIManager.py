from EventBus import EventBus
import cv2
import numpy as np
from ColorScheme import Colors
from Board import Board

class UIManager:
    """Handles UI rendering for the chess game."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.player1_score = 0
        self.player2_score = 0
        self.game = None
        self.event_bus.subscribe("score_updated", self._on_score_updated)
    
    def set_game_reference(self, game):
        """Attach reference to game object."""
        self.game = game
    
    def _on_score_updated(self, data):
        """Update player scores."""
        self.player1_score = data['player1_score']
        self.player2_score = data['player2_score']
    
    def draw_all_ui_elements(self, board: Board):
        """Draw all UI components."""
        if not self.game:
            return
        self.draw_cursors_and_selections(board)
        self.draw_moves_tables(board)
        self.draw_scores(board)
        if hasattr(self.game, 'game_over_info'):
            self.draw_game_over_message(board)
    
    def draw_cursors_and_selections(self, board: Board):
        """Draw player cursors and selected piece highlights."""
        if not self.game:
            return

        self._draw_selection_backgrounds(board)

        # Player 1 cursor
        p1_x, p1_y = board.cell_to_pixels(*self.game.p1_cursor_pos)
        p1_color, p1_thickness = self._get_cursor_color_and_thickness(1)
        cv2.rectangle(board.img.img, (p1_x, p1_y),
                      (p1_x + board.cell_W_pix - 1, p1_y + board.cell_H_pix - 1),
                      p1_color, p1_thickness)
        cv2.putText(board.img.img, "P1", (p1_x + 2, p1_y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, p1_color, 1)

        # Player 2 cursor
        p2_x, p2_y = board.cell_to_pixels(*self.game.p2_cursor_pos)
        p2_color, p2_thickness = self._get_cursor_color_and_thickness(2)
        cv2.rectangle(board.img.img, (p2_x, p2_y),
                      (p2_x + board.cell_W_pix - 1, p2_y + board.cell_H_pix - 1),
                      p2_color, p2_thickness)
        cv2.putText(board.img.img, "P2", (p2_x + 2, p2_y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, p2_color, 1)
    
    def _get_cursor_color_and_thickness(self, player: int):
        """Return cursor color and thickness for a player."""
        if not self.game:
            return (Colors.PLAYER1_CURSOR if player == 1 else Colors.PLAYER2_CURSOR), 3

        if player == 1:
            color = Colors.PLAYER1_CURSOR
            if self.game.p1_ui_state == "moving" and self.game.p1_selected_piece_id:
                is_valid = self.game._is_move_valid(self.game.p1_selected_piece_id, *self.game.p1_cursor_pos)
                return color, 3 if is_valid else 2
            return color, 3
        else:
            color = Colors.PLAYER2_CURSOR
            if self.game.p2_ui_state == "moving" and self.game.p2_selected_piece_id:
                is_valid = self.game._is_move_valid(self.game.p2_selected_piece_id, *self.game.p2_cursor_pos)
                return color, 3 if is_valid else 2
            return color, 3

    def _draw_selection_backgrounds(self, board: Board):
        """Draw selection background under selected pieces."""
        if not self.game:
            return

        def draw_selection(piece_id, color):
            piece = self.game.pieces[piece_id]
            pos = piece.get_current_cell()
            x, y = board.cell_to_pixels(int(round(pos[0])), int(round(pos[1])))
            overlay = board.img.img.copy()
            cv2.rectangle(overlay, (x, y),
                          (x + board.cell_W_pix - 1, y + board.cell_H_pix - 1),
                          color, -1)
            cv2.addWeighted(board.img.img, 0.4, overlay, 0.6, 0, board.img.img)

        if self.game.p1_selected_piece_id and self.game.p1_ui_state == "moving":
            draw_selection(self.game.p1_selected_piece_id, Colors.PLAYER1_SELECTION_BG)
        if self.game.p2_selected_piece_id and self.game.p2_ui_state == "moving":
            draw_selection(self.game.p2_selected_piece_id, Colors.PLAYER2_SELECTION_BG)
    
    def draw_moves_tables(self, board: Board):
        """Draw move tables and scores for both players."""
        if not self.game:
            return

        window_height = board.total_height_pix
        table_height = int(window_height * 0.75)
        vertical_center_y = (window_height - table_height) // 2

        player1_table = self.game.player1_moves.create_visual_table(width=300, fixed_height=table_height)
        player2_table = self.game.player2_moves.create_visual_table(width=300, fixed_height=table_height)

        left_x = board.get_left_sidebar_area()[0] + 20
        right_x = board.get_right_sidebar_area()[0] + 30
        score_y = max(30, vertical_center_y - 20)

        # Draw scores above tables
        cv2.putText(board.img.img, f"Score: {self.player1_score}",
                    (left_x, score_y), cv2.FONT_HERSHEY_SIMPLEX, Colors.SCORE_FONT_SIZE,
                    Colors.SCORE_TEXT_COLOR, Colors.SCORE_FONT_THICKNESS)
        cv2.putText(board.img.img, f"Score: {self.player2_score}",
                    (right_x, score_y), cv2.FONT_HERSHEY_SIMPLEX, Colors.SCORE_FONT_SIZE,
                    Colors.SCORE_TEXT_COLOR, Colors.SCORE_FONT_THICKNESS)

        try:
            if player1_table and player1_table.img is not None:
                player1_table.draw_on(board.img, left_x, vertical_center_y)
            if player2_table and player2_table.img is not None:
                player2_table.draw_on(board.img, right_x, vertical_center_y)
        except:
            pass  # Fail gracefully if drawing fails
    
    def draw_scores(self, board: Board):
        """Scores now drawn inside draw_moves_tables."""
        pass
    
    def draw_game_over_message(self, board: Board):
        """Display game over screen."""
        if not self.game or not hasattr(self.game, 'game_over_info'):
            return

        game_over_time = self.game.game_over_info.get('timestamp', 0)
        if self.game.game_time_ms() - game_over_time < 1000:
            return

        winner = self.game.game_over_info['winner']
        loser = self.game.game_over_info['loser']

        window_width = board.total_width_pix
        window_height = board.total_height_pix

        overlay = board.img.img.copy()
        cv2.rectangle(overlay, (0, 0), (window_width, window_height), (0, 0, 0), -1)
        cv2.addWeighted(board.img.img, 0.3, overlay, 0.7, 0, board.img.img)

        text1 = "GAME OVER!"
        text2 = f"Player {winner} Wins!"
        text3 = f"Player {winner} captured Player {loser}'s King!"

        center_x = window_width // 2
        center_y = window_height // 2
        base_scale = min(window_width, window_height) / 400
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = max(2, int(base_scale))

        def draw_centered_text(text, offset_y, scale, thickness_adj=0):
            (tw, th), _ = cv2.getTextSize(text, font, base_scale * scale, thickness)
            x = center_x - tw // 2
            y = center_y + offset_y
            cv2.putText(board.img.img, text, (x, y), font, base_scale * scale, (0, 0, 0), thickness + thickness_adj)
            cv2.putText(board.img.img, text, (x, y), font, base_scale * scale, (255, 255, 255), thickness)

        draw_centered_text(text1, -80, 1.2, 2)
        draw_centered_text(text2, 0, 1.0, 2)
        draw_centered_text(text3, 60, 0.7, 1)
    
    def get_scores(self):
        """Return current scores."""
        return self.player1_score, self.player2_score
