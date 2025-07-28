from Board import Board
from Physics import Physics


class PhysicsFactory:
    def __init__(self, board: Board):
        """Initialize with board."""
        self.board = board

    def create(self, start_cell, cfg) -> Physics:
        """Create a Physics object based on config."""
        speed = cfg.get("speed_m_per_sec", 0.0)
        next_state = cfg.get("next_state_when_finished", "idle")

        physics = Physics(
            start_cell=start_cell,
            board=self.board,
            speed_m_s=speed,
            next_state_name=next_state
        )

        return physics
