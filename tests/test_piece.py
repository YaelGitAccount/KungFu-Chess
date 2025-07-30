import sys
import pathlib
# הוספת הנתיב של It1_interfaces לנתיב החיפוש
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent / "It1_interfaces"))

import pytest
from unittest.mock import Mock
from Piece import Piece
from State import State
from Command import Command
from Board import Board


class TestPiece:
    """Test suite for Piece class."""
    
    @pytest.fixture
    def mock_state(self):
        """Create a mock State object."""
        state = Mock(spec=State)
        state.reset = Mock()
        state.update = Mock(return_value=state)  # Returns self by default
        state.process_command = Mock(return_value=state)
        state._physics = Mock()
        state._physics.current_cell = (2, 3)
        state._physics.board = Mock()
        state._physics.get_pos = Mock(return_value=(2.0, 3.0))  # ✓ Fixed: return tuple
        state._graphics = Mock()
        state._graphics.get_img = Mock(return_value=Mock())
        state._moves = Mock()
        state._moves.get_moves = Mock(return_value=[(3, 3), (1, 3), (2, 4)])
        state.transitions = {"Move": Mock(), "Jump": Mock()}
        return state
    
    @pytest.fixture
    def piece(self, mock_state):
        """Create a Piece with mock state."""
        return Piece("test_piece_1", mock_state)
    
    @pytest.fixture
    def mock_board(self):
        """Create a mock Board object."""
        board = Mock(spec=Board)
        board.cell_W_pix = 64
        board.cell_H_pix = 64
        board.cell_W_m = 1.0
        board.cell_H_m = 1.0
        board.img = Mock()
        return board
    
    @pytest.fixture
    def move_command(self):
        """Create a Move command for testing."""
        return Command(
            timestamp=1000,
            piece_id="test_piece_1",
            type="Move",
            params=["3", "4"]
        )
    
    @pytest.fixture
    def jump_command(self):
        """Create a Jump command for testing."""
        return Command(
            timestamp=1500,
            piece_id="test_piece_1",
            type="Jump",
            params=[]
        )
    
    @pytest.fixture
    def invalid_move_command(self):
        """Create an invalid Move command for testing."""
        return Command(
            timestamp=2000,
            piece_id="test_piece_1",
            type="Move",
            params=["9", "9"]  # Outside board
        )

    def test_initialization(self, mock_state):
        """Test proper initialization of Piece."""
        piece_id = "knight_1"
        piece = Piece(piece_id, mock_state)
        
        assert piece.piece_id == piece_id
        assert piece._state == mock_state

    def test_get_piece_id(self, piece):
        """Test getting piece ID."""
        result = piece.get_piece_id()
        assert result == "test_piece_1"

    def test_get_current_cell(self, piece, mock_state):
        """Test getting current cell position."""
        mock_state._physics.current_cell = (4, 5)
        
        result = piece.get_current_cell()
        
        assert result == (4, 5)

    def test_reset(self, piece, move_command, mock_state):
        """Test resetting the piece."""
        piece.reset(move_command)
        
        # Should delegate to state.reset
        mock_state.reset.assert_called_once_with(move_command)

    def test_update(self, piece, mock_state):
        """Test updating the piece."""
        now_ms = 5000
        new_state = Mock()
        mock_state.update.return_value = new_state
        
        piece.update(now_ms)
        
        # Should update state and potentially transition
        mock_state.update.assert_called_once_with(now_ms)
        assert piece._state == new_state

    def test_update_no_state_change(self, piece, mock_state):
        """Test update when state doesn't change."""
        now_ms = 3000
        mock_state.update.return_value = mock_state  # Same state
        
        piece.update(now_ms)
        
        mock_state.update.assert_called_once_with(now_ms)
        assert piece._state == mock_state  # Should remain same

    def test_on_command_valid_move(self, piece, move_command, mock_state):
        """Test processing valid move command."""
        # Mock valid move
        mock_state._moves.get_moves.return_value = [(3, 4), (1, 3)]
        mock_state.transitions = {"Move": Mock()}
        mock_state._physics.board.H_cells = 8
        mock_state._physics.board.W_cells = 8
        
        piece.on_command(move_command, 1000)
        
        # Should process the command
        mock_state.process_command.assert_called_once_with(move_command, 1000)

    def test_on_command_invalid_move_outside_board(self, piece, mock_state):
        """Test processing move command to position outside board."""
        invalid_command = Command(1000, "test", "Move", ["8", "8"])  # Outside 8x8 board
        mock_state._physics.board.H_cells = 8
        mock_state._physics.board.W_cells = 8
        mock_state.transitions = {"Move": Mock()}
        
        piece.on_command(invalid_command, 1000)
        
        # Should not process invalid command
        mock_state.process_command.assert_not_called()

    def test_on_command_invalid_move_not_legal(self, piece, move_command, mock_state):
        """Test processing move command to illegal position."""
        # Mock that target position is not in legal moves
        mock_state._moves.get_moves.return_value = [(1, 3), (2, 4)]  # (3,4) not included
        mock_state.transitions = {"Move": Mock()}
        mock_state._physics.board.H_cells = 8
        mock_state._physics.board.W_cells = 8
        
        piece.on_command(move_command, 1000)
        
        # Should not process illegal move
        mock_state.process_command.assert_not_called()

    def test_on_command_unsupported_command_type(self, piece, mock_state):
        """Test processing unsupported command type."""
        unsupported_command = Command(1000, "test", "Teleport", [])
        mock_state.transitions = {"Move": Mock(), "Jump": Mock()}  # No "Teleport"
        
        piece.on_command(unsupported_command, 1000)
        
        # Should not process unsupported command
        mock_state.process_command.assert_not_called()

    def test_is_command_possible_valid_move(self, piece, move_command, mock_state):
        """Test validation of valid move command."""
        mock_state._moves.get_moves.return_value = [(3, 4), (1, 3)]
        mock_state.transitions = {"Move": Mock()}
        mock_state._physics.board.H_cells = 8
        mock_state._physics.board.W_cells = 8
        
        result = piece.is_command_possible(move_command)
        
        assert result == True

    def test_is_command_possible_invalid_params(self, piece, mock_state):
        """Test validation of move command with invalid parameters."""
        invalid_command = Command(1000, "test", "Move", ["invalid", "params"])
        mock_state.transitions = {"Move": Mock()}
        
        result = piece.is_command_possible(invalid_command)
        
        assert result == False

    def test_is_command_possible_insufficient_params(self, piece, mock_state):
        """Test validation of move command with insufficient parameters."""
        invalid_command = Command(1000, "test", "Move", ["3"])  # Only one param
        mock_state.transitions = {"Move": Mock()}
        
        result = piece.is_command_possible(invalid_command)
        
        assert result == False

    def test_is_command_possible_outside_board(self, piece, mock_state):
        """Test validation of move command outside board boundaries."""
        invalid_command = Command(1000, "test", "Move", ["10", "10"])
        mock_state.transitions = {"Move": Mock()}
        mock_state._physics.board.H_cells = 8
        mock_state._physics.board.W_cells = 8
        
        result = piece.is_command_possible(invalid_command)
        
        assert result == False

    def test_is_command_possible_illegal_move(self, piece, move_command, mock_state):
        """Test validation of illegal move according to piece rules."""
        mock_state._moves.get_moves.return_value = [(1, 3), (2, 4)]  # (3,4) not legal
        mock_state.transitions = {"Move": Mock()}
        mock_state._physics.board.H_cells = 8
        mock_state._physics.board.W_cells = 8
        
        result = piece.is_command_possible(move_command)
        
        assert result == False

    def test_is_command_possible_no_transition(self, piece, mock_state):
        """Test validation when command type has no transition."""
        unsupported_command = Command(1000, "test", "Fly", [])
        mock_state.transitions = {"Move": Mock(), "Jump": Mock()}  # No "Fly"
        
        result = piece.is_command_possible(unsupported_command)
        
        assert result == False

    def test_is_command_possible_non_move_command(self, piece, jump_command, mock_state):
        """Test validation of non-Move command."""
        mock_state.transitions = {"Jump": Mock()}
        
        result = piece.is_command_possible(jump_command)
        
        assert result == True

    def test_draw_on_board_with_sprite(self, piece, mock_board, mock_state):
        """Test drawing piece on board with valid sprite."""
        now_ms = 2000
        
        # Mock sprite
        mock_sprite = Mock()
        mock_sprite.img = Mock()  # Not None
        mock_sprite.draw_on = Mock()
        mock_state._graphics.get_img.return_value = mock_sprite
        
        # Mock position
        mock_state._physics.get_pos.return_value = (2.5, 3.7)  # meters
        
        piece.draw_on_board(mock_board, now_ms)
        
        # Should call draw_on with correct pixel position
        expected_x = int(2.5 * 64 / 1.0)  # Convert to pixels
        expected_y = int(3.7 * 64 / 1.0)
        mock_sprite.draw_on.assert_called_once_with(mock_board.img, expected_x, expected_y)

    def test_draw_on_board_no_sprite(self, piece, mock_board, mock_state):
        """Test drawing piece when no sprite is available."""
        now_ms = 2000
        mock_state._graphics.get_img.return_value = None
        mock_state._physics.get_pos.return_value = (1.0, 2.0)  # ✓ Added position
        
        # Should not crash
        piece.draw_on_board(mock_board, now_ms)
        
        # No drawing should occur, but no exception should be raised

    def test_draw_on_board_sprite_no_image(self, piece, mock_board, mock_state):
        """Test drawing piece when sprite has no image."""
        now_ms = 2000
        
        mock_sprite = Mock()
        mock_sprite.img = None  # No image
        mock_state._graphics.get_img.return_value = mock_sprite
        mock_state._physics.get_pos.return_value = (1.5, 2.5)  # ✓ Added position
        
        # Should not crash and not attempt to draw
        piece.draw_on_board(mock_board, now_ms)

    def test_position_conversion_calculation(self, piece, mock_board, mock_state):
        """Test pixel position calculation from meters."""
        now_ms = 1000
        
        # Mock sprite
        mock_sprite = Mock()
        mock_sprite.img = Mock()
        mock_sprite.draw_on = Mock()
        mock_state._graphics.get_img.return_value = mock_sprite
        
        # Test specific position conversion
        mock_state._physics.get_pos.return_value = (1.5, 2.3)  # 1.5m x, 2.3m y
        
        piece.draw_on_board(mock_board, now_ms)
        
        # Expected conversion: meters * pixels_per_meter
        expected_x = int(1.5 * 64 / 1.0)  # = 96 pixels
        expected_y = int(2.3 * 64 / 1.0)  # = 147 pixels
        
        mock_sprite.draw_on.assert_called_once_with(mock_board.img, expected_x, expected_y)

    def test_state_transitions_during_update(self, piece, mock_state):
        """Test state transitions during piece update."""
        now_ms = 4000
        new_state = Mock()
        mock_state.update.return_value = new_state
        
        # Verify initial state
        assert piece._state == mock_state
        
        piece.update(now_ms)
        
        # Should transition to new state
        assert piece._state == new_state
        mock_state.update.assert_called_once_with(now_ms)

    def test_command_processing_flow(self, piece, move_command, mock_state):
        """Test complete command processing flow."""
        # Setup valid command scenario
        mock_state._moves.get_moves.return_value = [(3, 4)]
        mock_state.transitions = {"Move": Mock()}
        mock_state._physics.board.H_cells = 8
        mock_state._physics.board.W_cells = 8
        
        new_state = Mock()
        mock_state.process_command.return_value = new_state
        
        # Process command
        piece.on_command(move_command, 1000)
        
        # Should validate, then process, then transition
        mock_state._moves.get_moves.assert_called_once()
        mock_state.process_command.assert_called_once_with(move_command, 1000)
        assert piece._state == new_state

    def test_piece_identity_persistence(self, piece, mock_state):
        """Test that piece ID persists through state changes."""
        original_id = piece.get_piece_id()
        
        # Simulate state change
        new_state = Mock()
        mock_state.update.return_value = new_state
        piece.update(1000)
        
        # ID should remain the same
        assert piece.get_piece_id() == original_id

    def test_multiple_command_processing(self, piece, mock_state):
        """Test processing multiple commands in sequence."""
        # Setup
        mock_state.transitions = {"Move": Mock(), "Jump": Mock()}
        mock_state._physics.board.H_cells = 8
        mock_state._physics.board.W_cells = 8
        mock_state._moves.get_moves.return_value = [(3, 4), (5, 6)]
        
        commands = [
            Command(1000, "test", "Move", ["3", "4"]),
            Command(2000, "test", "Jump", []),
            Command(3000, "test", "Move", ["5", "6"])
        ]
        
        for i, cmd in enumerate(commands):
            piece.on_command(cmd, cmd.timestamp)
        
        # Should process all valid commands
        assert mock_state.process_command.call_count == 3