from Command import Command
from Moves import Moves
from Graphics import Graphics
from Physics import Physics
from typing import Dict, Tuple, Optional

class State:
    def __init__(self, moves: Moves, graphics: Graphics, physics: Physics, state_name: str = "unknown"):
        """Initialize state with moves, graphics, and physics."""
        self._moves = moves
        self._graphics = graphics
        self._physics = physics
        self.transitions = {}
        self._next_state = None
        self._state_name = state_name

    def set_transition(self, event: str, target: "State"):
        """Define a transition for a given event."""
        self.transitions[event] = target

    def set_next_state(self, next_state: "State"):
        """Set auto-transition target state."""
        self._next_state = next_state

    def reset(self, cmd: Command):
        """Reset state with a new command."""
        if cmd.type == "Move" and len(cmd.params) == 2:
            try:
                target_row, target_col = int(cmd.params[0]), int(cmd.params[1])
                self._physics.set_target((target_row, target_col))
            except ValueError:
                pass  # Invalid move parameters

        self._graphics.reset(cmd.timestamp)
        self._physics.reset(cmd.timestamp)

    def update(self, now_ms: int) -> "State":
        """Update state and handle automatic transitions."""
        self._graphics.update(now_ms)
        next_state_name = self._physics.update(now_ms)

        if not next_state_name and not self._graphics.loop and self._graphics.is_finished:
            next_state_name = self._physics.next_state_name

        if next_state_name:
            if self._next_state:
                self._next_state._graphics.reset(now_ms)
                current_pos = self._physics.current_cell
                self._next_state._physics.current_cell = current_pos
                self._next_state._physics.start_cell = current_pos
                self._next_state._physics.target_cell = current_pos
                self._next_state._physics.is_moving = False
                self._next_state.transitions = self.transitions.copy()
                return self._next_state

            elif next_state_name in self.transitions:
                next_state = self.transitions[next_state_name]
                current_pos = self._physics.current_cell
                next_state._physics.current_cell = current_pos
                next_state._physics.start_cell = current_pos
                next_state._physics.target_cell = current_pos
                next_state._physics.is_moving = False
                next_state.transitions = self.transitions.copy()
                next_state._graphics.reset(now_ms)
                return next_state

        return self

    def process_command(self, cmd: Command, now_ms: int) -> "State":
        """Process a command and return the next state."""
        if cmd.type not in self.transitions:
            return self

        next_state = self.transitions[cmd.type]
        next_state.transitions = self.transitions.copy()

        if cmd.type == "Jump":
            current_pos = self._physics.current_cell
            next_state._physics.current_cell = current_pos
            next_state._physics.start_cell = current_pos
            next_state._physics.target_cell = current_pos
            next_state._physics.is_moving = False

        next_state.reset(cmd)
        return next_state

    def can_transition(self, now_ms: int) -> bool:
        """Determine if this state can transition."""
        return True

    def get_command(self) -> Command:
        """Return the current command (if any)."""
        return None
