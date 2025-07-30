import sys
import pathlib
# הוספת הנתיב של It1_interfaces לנתיב החיפוש
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent / "It1_interfaces"))

import pytest
from unittest.mock import Mock, MagicMock
from State import State
from Command import Command
from Moves import Moves
from Graphics import Graphics
from Physics import Physics


class TestState:
    """Test suite for State class."""
    
    @pytest.fixture
    def mock_moves(self):
        """Create a mock Moves object."""
        return Mock(spec=Moves)
    
    @pytest.fixture
    def mock_graphics(self):
        """Create a mock Graphics object."""
        graphics = Mock(spec=Graphics)
        graphics.reset = Mock()
        graphics.update = Mock()
        return graphics
    
    @pytest.fixture
    def mock_physics(self):
        """Create a mock Physics object."""
        physics = Mock(spec=Physics)
        physics.reset = Mock()
        physics.update = Mock(return_value=None)  # Default: no state change
        physics.set_target = Mock()
        return physics
    
    @pytest.fixture
    def state(self, mock_moves, mock_graphics, mock_physics):
        """Create a State object with mocked dependencies."""
        return State(mock_moves, mock_graphics, mock_physics)
    
    @pytest.fixture
    def move_command(self):
        """Create a Move command for testing."""
        return Command(
            timestamp=1000,
            piece_id="test_piece",
            type="Move",
            params=["3", "4"]
        )
    
    @pytest.fixture
    def jump_command(self):
        """Create a Jump command for testing."""
        return Command(
            timestamp=1500,
            piece_id="test_piece",
            type="Jump",
            params=[]
        )
    
    @pytest.fixture
    def reset_command(self):
        """Create a reset command for testing."""
        return Command(
            timestamp=2000,
            piece_id="test_piece",
            type="reset",
            params=[]
        )

    def test_initialization(self, mock_moves, mock_graphics, mock_physics):
        """Test proper initialization of State object."""
        state = State(mock_moves, mock_graphics, mock_physics)
        
        assert state._moves == mock_moves
        assert state._graphics == mock_graphics
        assert state._physics == mock_physics
        assert state.transitions == {}

    def test_set_transition(self, state, mock_moves, mock_graphics, mock_physics):
        """Test setting transitions between states."""
        # Create a target state
        target_state = State(mock_moves, mock_graphics, mock_physics)
        
        # Set transition
        state.set_transition("Move", target_state)
        
        assert "Move" in state.transitions
        assert state.transitions["Move"] == target_state

    def test_set_multiple_transitions(self, state, mock_moves, mock_graphics, mock_physics):
        """Test setting multiple transitions."""
        target_state1 = State(mock_moves, mock_graphics, mock_physics)
        target_state2 = State(mock_moves, mock_graphics, mock_physics)
        
        state.set_transition("Move", target_state1)
        state.set_transition("Jump", target_state2)
        
        assert len(state.transitions) == 2
        assert state.transitions["Move"] == target_state1
        assert state.transitions["Jump"] == target_state2

    def test_reset_with_move_command(self, state, move_command):
        """Test reset with Move command."""
        state.reset(move_command)
        
        # Should set target in physics for Move command
        state._physics.set_target.assert_called_once_with((3, 4))
        
        # Should reset graphics and physics with timestamp
        state._graphics.reset.assert_called_once_with(1000)  # cmd.timestamp
        state._physics.reset.assert_called_once_with(1000)   # cmd.timestamp

    def test_reset_with_invalid_move_params(self, state, mock_physics):
        """Test reset with Move command having invalid parameters."""
        invalid_move = Command(
            timestamp=1000,
            piece_id="test",
            type="Move",
            params=["invalid", "params"]  # Non-numeric
        )
        
        state.reset(invalid_move)
        
        # Should not call set_target due to ValueError
        state._physics.set_target.assert_not_called()
        
        # But should still reset graphics and physics with timestamp
        state._graphics.reset.assert_called_once_with(1000)  # cmd.timestamp
        state._physics.reset.assert_called_once_with(1000)   # cmd.timestamp

    def test_reset_with_non_move_command(self, state, jump_command):
        """Test reset with non-Move command."""
        state.reset(jump_command)
        
        # Should not set target for non-Move commands
        state._physics.set_target.assert_not_called()
        
        # Should reset graphics and physics with timestamp
        state._graphics.reset.assert_called_once_with(1500)  # cmd.timestamp
        state._physics.reset.assert_called_once_with(1500)   # cmd.timestamp

    def test_reset_with_incomplete_move_params(self, state):
        """Test reset with Move command having insufficient parameters."""
        incomplete_move = Command(
            timestamp=1000,
            piece_id="test",
            type="Move",
            params=["3"]  # Only one parameter
        )
        
        state.reset(incomplete_move)
        
        # Should not set target due to insufficient params
        state._physics.set_target.assert_not_called()

    def test_update_no_state_change(self, state):
        """Test update when physics doesn't request state change."""
        state._physics.update.return_value = None
        
        result = state.update(2000)
        
        # Should update both graphics and physics
        state._graphics.update.assert_called_once_with(2000)
        state._physics.update.assert_called_once_with(2000)
        
        # Should return self (no state change)
        assert result == state

    def test_update_with_state_change_no_transition(self, state):
        """Test update when physics requests state change but no transition exists."""
        state._physics.update.return_value = "nonexistent_state"
        
        result = state.update(2000)
        
        # Should update both components
        state._graphics.update.assert_called_once_with(2000)
        state._physics.update.assert_called_once_with(2000)
        
        # Should return self (no valid transition)
        assert result == state

    def test_update_with_valid_state_change(self, state, mock_moves, mock_graphics, mock_physics):
        """Test update when physics requests valid state change."""
        # Create target state
        target_state = State(mock_moves, mock_graphics, mock_physics)
        target_state.reset = Mock()
        
        # Set up transition
        state.set_transition("idle", target_state)
        state._physics.update.return_value = "idle"
        
        result = state.update(2500)
        
        # Should update components
        state._graphics.update.assert_called_once_with(2500)
        state._physics.update.assert_called_once_with(2500)
        
        # Should reset target state with auto-generated reset command
        target_state.reset.assert_called_once()
        reset_call_args = target_state.reset.call_args[0][0]
        assert reset_call_args.timestamp == 2500
        assert reset_call_args.type == "reset"
        
        # Should return target state
        assert result == target_state

    def test_process_command_no_transition(self, state, move_command):
        """Test processing command when no transition exists."""
        result = state.process_command(move_command, 3000)
        
        # Should return self (no transition)
        assert result == state

    def test_process_command_with_transition(self, state, move_command, mock_moves, mock_graphics, mock_physics):
        """Test processing command with valid transition."""
        # Create target state
        target_state = State(mock_moves, mock_graphics, mock_physics)
        target_state.reset = Mock()
        
        # Set up transition
        state.set_transition("Move", target_state)
        
        result = state.process_command(move_command, 3000)
        
        # Should reset target state with the command
        target_state.reset.assert_called_once_with(move_command)
        
        # Should return target state
        assert result == target_state

    def test_process_multiple_different_commands(self, state, move_command, jump_command, mock_moves, mock_graphics, mock_physics):
        """Test processing different types of commands."""
        # Create target states
        move_state = State(mock_moves, mock_graphics, mock_physics)
        jump_state = State(mock_moves, mock_graphics, mock_physics)
        move_state.reset = Mock()
        jump_state.reset = Mock()
        
        # Set up transitions
        state.set_transition("Move", move_state)
        state.set_transition("Jump", jump_state)
        
        # Test Move command
        result1 = state.process_command(move_command, 3000)
        assert result1 == move_state
        move_state.reset.assert_called_once_with(move_command)
        
        # Test Jump command
        result2 = state.process_command(jump_command, 3500)
        assert result2 == jump_state
        jump_state.reset.assert_called_once_with(jump_command)

    def test_can_transition_default_implementation(self, state):
        """Test default can_transition implementation."""
        result = state.can_transition(4000)
        
        # Default implementation should always return True
        assert result == True

    def test_get_command_default_implementation(self, state):
        """Test default get_command implementation."""
        result = state.get_command()
        
        # Default implementation should return None
        assert result is None

    def test_state_transitions_are_independent(self, mock_moves, mock_graphics, mock_physics):
        """Test that different state instances have independent transitions."""
        state1 = State(mock_moves, mock_graphics, mock_physics)
        state2 = State(mock_moves, mock_graphics, mock_physics)
        
        target_state = State(mock_moves, mock_graphics, mock_physics)
        
        # Set transition only on state1
        state1.set_transition("Move", target_state)
        
        # state2 should not have the transition
        assert "Move" in state1.transitions
        assert "Move" not in state2.transitions
        assert len(state2.transitions) == 0

    def test_complex_state_machine_flow(self, mock_moves, mock_graphics, mock_physics):
        """Test a complex flow through multiple states."""
        # Create states: idle -> move -> idle
        idle_state = State(mock_moves, mock_graphics, mock_physics)
        move_state = State(mock_moves, mock_graphics, mock_physics)
        
        # Mock reset methods
        idle_state.reset = Mock()
        move_state.reset = Mock()
        
        # Set up transitions
        idle_state.set_transition("Move", move_state)
        move_state.set_transition("idle", idle_state)
        
        # Configure physics to simulate movement completion
        move_state._physics.update.return_value = "idle"  # Movement finished
        
        # Start in idle state
        current_state = idle_state
        
        # Process Move command (idle -> move)
        move_cmd = Command(1000, "piece1", "Move", ["2", "3"])
        current_state = current_state.process_command(move_cmd, 1000)
        assert current_state == move_state
        move_state.reset.assert_called_once_with(move_cmd)
        
        # Update move state (move -> idle automatically)
        current_state = current_state.update(2000)
        assert current_state == idle_state
        
        # Verify idle state was reset with auto-generated command
        idle_state.reset.assert_called_once()

    def test_update_components_called_in_correct_order(self, state):
        """Test that graphics and physics are updated in correct order."""
        call_order = []
        
        def track_graphics_update(time_ms):
            call_order.append(f"graphics_{time_ms}")
        
        def track_physics_update(time_ms):
            call_order.append(f"physics_{time_ms}")
            return None
        
        state._graphics.update.side_effect = track_graphics_update
        state._physics.update.side_effect = track_physics_update
        
        state.update(5000)
        
        # Graphics should be updated before physics
        assert call_order == ["graphics_5000", "physics_5000"]