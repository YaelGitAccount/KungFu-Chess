from typing import Tuple, Optional
from Board import Board
import math


class Physics:
    """Basic physics engine for movement."""

    def __init__(self, start_cell: Tuple[int, int], board: Board, speed_m_s: float, next_state_name: str):
        self.start_cell = start_cell
        self.current_cell = start_cell
        self.target_cell = start_cell
        self.board = board
        self.speed_m_s = speed_m_s
        self.next_state_name = next_state_name
        self.start_time_ms = 0
        self.total_distance_m = 0
        self.traveled_distance_m = 0
        self.is_moving = False

    def set_target(self, target_cell: Tuple[int, int]):
        """Set new movement target."""
        self.start_cell = self.current_cell
        self.target_cell = target_cell
        self.is_moving = True

        dx = target_cell[1] - self.current_cell[1]
        dy = target_cell[0] - self.current_cell[0]
        self.total_distance_m = math.sqrt(dx * dx + dy * dy) * self.board.cell_W_m
        self.traveled_distance_m = 0

    def reset(self, start_time_ms: int):
        """Reset timing and distance tracking."""
        self.start_time_ms = start_time_ms
        self.traveled_distance_m = 0

    def update(self, now_ms: int) -> Optional[str]:
        """Update movement. Returns next state if target reached."""
        if self.start_time_ms == 0:
            return None

        if self.speed_m_s == 0.0:
            return None

        if not self.is_moving:
            return None

        elapsed_time_s = (now_ms - self.start_time_ms) / 1000.0
        self.traveled_distance_m = self.speed_m_s * elapsed_time_s

        if self.traveled_distance_m >= self.total_distance_m:
            self.current_cell = self.target_cell
            self.start_cell = self.target_cell
            self.is_moving = False
            return self.next_state_name

        if self.total_distance_m > 0:
            progress = self.traveled_distance_m / self.total_distance_m
            start_row, start_col = self.start_cell
            target_row, target_col = self.target_cell

            current_row = start_row + (target_row - start_row) * progress
            current_col = start_col + (target_col - start_col) * progress
            self.current_cell = (current_row, current_col)

        return None

    def get_pos(self) -> Tuple[float, float]:
        """Return current position in meters."""
        pos_m_x = self.current_cell[1] * self.board.cell_W_m
        pos_m_y = self.current_cell[0] * self.board.cell_H_m
        return (pos_m_x, pos_m_y)
