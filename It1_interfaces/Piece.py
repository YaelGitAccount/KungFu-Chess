from Board import Board
from Command import Command
from State import State


class Piece:
    def __init__(self, piece_id: str, init_state: State):
        self.piece_id = piece_id
        self._state: State = init_state
        self.event_bus = None  # יוגדר על ידי Game

    def on_command(self, cmd: Command, now_ms: int):
        """Process a new command from game input."""
        # Debug info removed for cleaner output
        if self.is_command_possible(cmd):
            old_state_name = getattr(self._state, "_state_name", "unknown")
            self._state = self._state.process_command(cmd, now_ms)
            new_state_name = getattr(self._state, "_state_name", "unknown")
            # Optional: notify about state change
        else:
            # Command rejected; could log if needed
            pass

    def is_command_possible(self, cmd: Command) -> bool:
        """Basic validation hook - בדיקה אם הפקודה אפשרית."""
        # Only allow Move/Jump from idle state
        if cmd.type in ["Move", "Jump"] and not self.is_idle():
            return False

        if cmd.type not in self._state.transitions:
            return False

        if cmd.type == "Move":
            if len(cmd.params) != 2:
                return False

            try:
                to_row, to_col = int(cmd.params[0]), int(cmd.params[1])
            except ValueError:
                return False

            board = self._state._physics.board
            if not (0 <= to_row < board.H_cells and 0 <= to_col < board.W_cells):
                return False

            current_cell = self._state._physics.current_cell
            current_row, current_col = int(round(current_cell[0])), int(round(current_cell[1]))

            legal_moves = self._state._moves.get_moves(current_row, current_col)
            if (to_row, to_col) not in legal_moves:
                return False

        return True

    def reset(self, cmd: Command):
        """Reset the piece to a specific command (usually idle)."""
        self._state.reset(cmd)

    def update(self, now_ms: int):
        """Advance the state machine and apply transitions."""
        old_state = self._state
        self._state = self._state.update(now_ms)

        if old_state != self._state:
            old_state_name = getattr(old_state, "_state_name", "unknown")
            new_state_name = getattr(self._state, "_state_name", "unknown")
            if self.event_bus:
                self.event_bus.publish("piece_state_changed", {
                    "piece_id": self.piece_id,
                    "state": new_state_name
                })

    def draw_on_board(self, board: Board, now_ms: int):
        """Draw the piece's current image on the board."""
        pos_m = self._state._physics.get_pos()
        pos_pix = (
            int(pos_m[0] * board.cell_W_pix / board.cell_W_m),
            int(pos_m[1] * board.cell_H_pix / board.cell_H_m)
        )

        draw_x = board.left_sidebar_width + pos_pix[0] + board._margin
        draw_y = board.top_margin + pos_pix[1]

        sprite = self._state._graphics.get_img()
        if sprite and sprite.img is not None:
            sprite.draw_on(board.img, draw_x, draw_y)

    def get_current_cell(self) -> tuple[int, int]:
        """Return the current cell of the piece on the board."""
        current_pos = self._state._physics.current_cell
        return (int(round(current_pos[0])), int(round(current_pos[1])))

    def get_piece_id(self) -> str:
        """Return the piece ID."""
        return self.piece_id

    def is_idle(self) -> bool:
        """Check if the piece is in idle state - only then selectable."""
        return (
            self._state._physics.speed_m_s == 0.0 and 
            self._state._graphics.loop == True and
            self._state._physics.next_state_name == "idle"
        )
