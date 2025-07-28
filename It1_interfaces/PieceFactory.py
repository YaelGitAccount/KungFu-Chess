import pathlib
import json
from typing import Dict, Tuple
from Board import Board
from GraphicsFactory import GraphicsFactory
from Moves import Moves
from PhysicsFactory import PhysicsFactory
from Piece import Piece
from State import State
from Physics import Physics

class PieceFactory:
    """Factory for creating chess pieces with state machines."""
    
    def __init__(self, board: Board, pieces_root: pathlib.Path):
        self.board = board
        self.pieces_root = pieces_root
        self.graphics_factory = GraphicsFactory()
        self.physics_factory = PhysicsFactory(board)
        self._piece_counters = {}  # For unique IDs
        self._piece_templates = {}  # Cached templates
    
    def create_piece(self, p_type: str, cell: Tuple[int, int]) -> Piece:
        if p_type not in self._piece_counters:
            self._piece_counters[p_type] = 0
        
        piece_id = f"{p_type}_{self._piece_counters[p_type]}"
        self._piece_counters[p_type] += 1
        
        initial_state = self._get_state_machine(p_type, cell)
        return Piece(piece_id, initial_state)
    
    def _get_state_machine(self, p_type: str, start_cell: Tuple[int, int]) -> State:
        if p_type not in self._piece_templates:
            piece_dir = self.pieces_root / p_type
            if not piece_dir.exists():
                raise FileNotFoundError(f"Missing piece directory: {piece_dir}")
            self._piece_templates[p_type] = self._build_state_machine(piece_dir)
        
        template = self._piece_templates[p_type]
        return self._clone_state_machine(template, start_cell)
    
    def _build_state_machine(self, piece_dir: pathlib.Path) -> Dict[str, State]:
        moves_file = piece_dir / "moves.txt"
        if not moves_file.exists():
            raise FileNotFoundError(f"Missing moves.txt: {moves_file}")
        
        moves = Moves(moves_file, (self.board.H_cells, self.board.W_cells))
        states_dir = piece_dir / "states"
        if not states_dir.exists():
            raise FileNotFoundError(f"Missing states dir: {states_dir}")
        
        states = {}
        state_configs = {}

        for state_dir in states_dir.iterdir():
            if not state_dir.is_dir():
                continue
            
            state_name = state_dir.name
            config_file = state_dir / "config.json"
            if not config_file.exists():
                continue
            
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                state_configs[state_name] = config

                graphics = self.graphics_factory.load(
                    state_dir / "sprites",
                    config.get("graphics", {}),
                    (self.board.cell_W_pix, self.board.cell_H_pix)
                )
                physics = self.physics_factory.create(
                    (0, 0),
                    config.get("physics", {})
                )
                states[state_name] = State(moves, graphics, physics, state_name)
            except Exception:
                continue

        self._setup_transitions(states, state_configs)
        return states
    
    def _setup_transitions(self, states: Dict[str, State], state_configs: Dict[str, dict]):
        for state_name, state in states.items():
            config = state_configs[state_name]
            physics_config = config.get("physics", {})
            next_state_name = physics_config.get("next_state_when_finished")

            if next_state_name and next_state_name in states:
                state.set_next_state(states[next_state_name])
            
            if state_name == "idle":
                if "move" in states:
                    state.set_transition("Move", states["move"])
                if "jump" in states:
                    state.set_transition("Jump", states["jump"])
    
    def _clone_state_machine(self, template: Dict[str, State], start_cell: Tuple[int, int]) -> State:
        if "idle" not in template:
            raise ValueError("Template missing 'idle' state")
        
        cloned_states = {}

        for state_name, template_state in template.items():
            new_physics = Physics(
                start_cell=start_cell,
                board=template_state._physics.board,
                speed_m_s=template_state._physics.speed_m_s,
                next_state_name=template_state._physics.next_state_name
            )
            new_graphics = template_state._graphics.copy()
            new_state = State(
                moves=template_state._moves,
                graphics=new_graphics,
                physics=new_physics,
                state_name=state_name
            )
            cloned_states[state_name] = new_state

        for state_name, template_state in template.items():
            cloned_state = cloned_states[state_name]
            for transition_name, target_template_state in template_state.transitions.items():
                for target_name, target_template in template.items():
                    if target_template is target_template_state:
                        cloned_state.set_transition(transition_name, cloned_states[target_name])
                        break
            
            if hasattr(template_state, '_next_state') and template_state._next_state:
                for target_name, target_template in template.items():
                    if target_template is template_state._next_state:
                        cloned_state.set_next_state(cloned_states[target_name])
                        break
        
        return cloned_states["idle"]
