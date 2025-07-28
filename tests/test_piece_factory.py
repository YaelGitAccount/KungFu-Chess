import sys
import pathlib
# הוספת הנתיב של It1_interfaces לנתיב החיפוש
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent / "It1_interfaces"))

import pytest
import tempfile
import shutil
import json
from unittest.mock import Mock, patch

from PieceFactory import PieceFactory
from Board import Board


class TestPieceFactory:
    """Test suite for PieceFactory class."""
    
    @pytest.fixture
    def mock_board(self):
        """Create a mock board for testing."""
        board = Mock(spec=Board)
        board.cell_W_pix = 64
        board.cell_H_pix = 64
        board.cell_W_m = 1.0
        board.cell_H_m = 1.0
        board.H_cells = 8
        board.W_cells = 8
        return board
    
    @pytest.fixture
    def temp_pieces_dir(self):
        """Create a temporary pieces directory structure."""
        temp_dir = pathlib.Path(tempfile.mkdtemp())
        
        # Create knight piece structure
        knight_dir = temp_dir / "knight"
        knight_dir.mkdir()
        
        # Create moves.txt
        (knight_dir / "moves.txt").write_text("L-shape moves for knight")
        
        # Create states directory
        states_dir = knight_dir / "states"
        states_dir.mkdir()
        
        # Create idle state
        idle_dir = states_dir / "idle"
        idle_dir.mkdir()
        (idle_dir / "config.json").write_text(json.dumps({
            "physics": {
                "speed_m_per_sec": 0.0,
                "next_state_when_finished": "idle"
            },
            "graphics": {
                "frames_per_sec": 6,
                "is_loop": True
            }
        }))
        (idle_dir / "sprites").mkdir()
        (idle_dir / "sprites" / "idle.png").touch()
        
        # Create move state
        move_dir = states_dir / "move"
        move_dir.mkdir()
        (move_dir / "config.json").write_text(json.dumps({
            "physics": {
                "speed_m_per_sec": 2.0,
                "next_state_when_finished": "idle"
            },
            "graphics": {
                "frames_per_sec": 8,
                "is_loop": False
            }
        }))
        (move_dir / "sprites").mkdir()
        (move_dir / "sprites" / "move1.png").touch()
        (move_dir / "sprites" / "move2.png").touch()
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def piece_factory(self, mock_board, temp_pieces_dir):
        """Create a PieceFactory with mock dependencies."""
        return PieceFactory(mock_board, temp_pieces_dir)

    def test_initialization(self, mock_board, temp_pieces_dir):
        """Test proper initialization of PieceFactory."""
        factory = PieceFactory(mock_board, temp_pieces_dir)
        
        assert factory.board == mock_board
        assert factory.pieces_root == temp_pieces_dir
        assert hasattr(factory, 'graphics_factory')
        assert hasattr(factory, 'physics_factory')
        assert factory._piece_counters == {}
        assert factory._piece_templates == {}

    def test_create_piece_first_of_type(self, piece_factory):
        """Test creating first piece of a specific type."""
        with patch.object(piece_factory, '_get_state_machine') as mock_get_state:
            mock_state = Mock()
            mock_get_state.return_value = mock_state
            
            with patch('PieceFactory.Piece') as mock_piece_class:
                mock_piece_instance = Mock()
                mock_piece_class.return_value = mock_piece_instance
                
                result = piece_factory.create_piece("knight", (3, 4))
                
                # Should create piece with ID knight_0
                mock_piece_class.assert_called_once_with("knight_0", mock_state)
                mock_get_state.assert_called_once_with("knight", (3, 4))
                assert result == mock_piece_instance

    def test_create_multiple_pieces_same_type(self, piece_factory):
        """Test creating multiple pieces of the same type with incremented IDs."""
        with patch.object(piece_factory, '_get_state_machine') as mock_get_state:
            mock_states = [Mock(), Mock(), Mock()]
            mock_get_state.side_effect = mock_states
            
            with patch('PieceFactory.Piece') as mock_piece_class:
                mock_pieces = [Mock(), Mock(), Mock()]
                mock_piece_class.side_effect = mock_pieces
                
                # Create three knights
                results = []
                for i in range(3):
                    result = piece_factory.create_piece("knight", (i, i))
                    results.append(result)
                
                # Should have incremented IDs
                expected_calls = [
                    (("knight_0", mock_states[0]),),
                    (("knight_1", mock_states[1]),),
                    (("knight_2", mock_states[2]),)
                ]
                
                assert mock_piece_class.call_count == 3
                for i, expected_call in enumerate(expected_calls):
                    assert mock_piece_class.call_args_list[i].args == expected_call[0]

    def test_create_pieces_different_types(self, piece_factory):
        """Test creating pieces of different types."""
        with patch.object(piece_factory, '_get_state_machine') as mock_get_state:
            mock_states = [Mock(), Mock()]
            mock_get_state.side_effect = mock_states
            
            with patch('PieceFactory.Piece') as mock_piece_class:
                mock_pieces = [Mock(), Mock()]
                mock_piece_class.side_effect = mock_pieces
                
                # Create knight and pawn
                knight = piece_factory.create_piece("knight", (0, 1))
                pawn = piece_factory.create_piece("pawn", (1, 1))
                
                # Should have separate counters
                expected_calls = [
                    (("knight_0", mock_states[0]),),
                    (("pawn_0", mock_states[1]),)
                ]
                
                for i, expected_call in enumerate(expected_calls):
                    assert mock_piece_class.call_args_list[i].args == expected_call[0]

    @patch('PieceFactory.Moves')
    @patch('PieceFactory.State')
    def test_build_state_machine(self, mock_state_class, mock_moves_class, piece_factory, temp_pieces_dir):
        """Test building state machine from piece directory."""
        # Mock dependencies
        mock_moves = Mock()
        mock_moves_class.return_value = mock_moves
        
        mock_states = [Mock(), Mock()]
        mock_state_class.side_effect = mock_states
        
        with patch.object(piece_factory.graphics_factory, 'load') as mock_graphics_load:
            mock_graphics = [Mock(), Mock()]
            mock_graphics_load.side_effect = mock_graphics
            
            with patch.object(piece_factory.physics_factory, 'create') as mock_physics_create:
                mock_physics = [Mock(), Mock()]
                mock_physics_create.side_effect = mock_physics
                
                # Test the method
                result = piece_factory._build_state_machine(temp_pieces_dir / "knight")
                
                # Should create moves
                mock_moves_class.assert_called_once()
                moves_call_args = mock_moves_class.call_args
                assert str(moves_call_args[0][0]).endswith("moves.txt")
                
                # Should create states
                assert mock_state_class.call_count == 2  # idle and move states
                
                # Should load graphics for both states
                assert mock_graphics_load.call_count == 2
                
                # Should create physics for both states
                assert mock_physics_create.call_count == 2
                
                # Should return dict with state names
                assert isinstance(result, dict)
                assert "idle" in result
                assert "move" in result

    def test_build_state_machine_missing_directory(self, piece_factory):
        """Test error handling when piece directory doesn't exist."""
        fake_dir = pathlib.Path("/nonexistent/piece/dir")
        
        with pytest.raises(FileNotFoundError):
            piece_factory._build_state_machine(fake_dir)

    def test_build_state_machine_missing_moves_file(self, piece_factory, temp_pieces_dir):
        """Test error handling when moves.txt is missing."""
        # Remove moves.txt
        (temp_pieces_dir / "knight" / "moves.txt").unlink()
        
        with pytest.raises(FileNotFoundError):
            piece_factory._build_state_machine(temp_pieces_dir / "knight")

    def test_build_state_machine_missing_states_directory(self, piece_factory, temp_pieces_dir):
        """Test error handling when states directory is missing."""
        # Remove states directory
        shutil.rmtree(temp_pieces_dir / "knight" / "states")
        
        with pytest.raises(FileNotFoundError):
            piece_factory._build_state_machine(temp_pieces_dir / "knight")

    @patch('PieceFactory.json.load')
    def test_build_state_machine_invalid_json(self, mock_json_load, piece_factory, temp_pieces_dir):
        """Test handling of invalid JSON in config files."""
        # Mock JSON parsing error
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        with patch('PieceFactory.Moves'):
            with patch.object(piece_factory.graphics_factory, 'load'):
                with patch.object(piece_factory.physics_factory, 'create'):
                    # Should handle gracefully and skip invalid states
                    result = piece_factory._build_state_machine(temp_pieces_dir / "knight")
                    
                    # Should return empty dict or dict without invalid states
                    assert isinstance(result, dict)

    def test_setup_transitions(self, piece_factory):
        """Test setting up transitions between states."""
        # Create mock states
        idle_state = Mock()
        move_state = Mock()
        idle_state.set_transition = Mock()
        move_state.set_next_state = Mock()
        
        states = {"idle": idle_state, "move": move_state}
        
        # Create state configs
        state_configs = {
            "idle": {
                "physics": {}
            },
            "move": {
                "physics": {
                    "next_state_when_finished": "idle"
                }
            }
        }
        
        piece_factory._setup_transitions(states, state_configs)
        
        # Should set up automatic transition from move to idle
        move_state.set_next_state.assert_called_once_with(idle_state)
        
        # Should set up user command transitions for idle
        idle_state.set_transition.assert_called()

    def test_clone_state_machine(self, piece_factory):
        """Test cloning state machine for specific piece instance."""
        # Create mock template
        mock_idle_state = Mock()
        template = {"idle": mock_idle_state}
        
        result = piece_factory._clone_state_machine(template, (2, 3))
        
        # Should return the idle state (current implementation)
        assert result == mock_idle_state

    def test_clone_state_machine_missing_idle(self, piece_factory):
        """Test error when template doesn't have idle state."""
        template = {"move": Mock(), "jump": Mock()}  # No idle
        
        with pytest.raises(ValueError, match="State machine must have an 'idle' state"):
            piece_factory._clone_state_machine(template, (0, 0))

    def test_caching_state_machines(self, piece_factory):
        """Test that state machines are cached and reused."""
        with patch.object(piece_factory, '_build_state_machine') as mock_build:
            mock_template = {"idle": Mock()}
            mock_build.return_value = mock_template
            
            with patch.object(piece_factory, '_clone_state_machine') as mock_clone:
                mock_states = [Mock(), Mock()]
                mock_clone.side_effect = mock_states
                
                with patch('PieceFactory.Piece') as mock_piece_class:
                    mock_pieces = [Mock(), Mock()]
                    mock_piece_class.side_effect = mock_pieces
                    
                    # Create two pieces of same type
                    piece1 = piece_factory.create_piece("knight", (0, 0))
                    piece2 = piece_factory.create_piece("knight", (1, 1))
                    
                    # Should build state machine only once
                    assert mock_build.call_count == 1
                    
                    # Should clone twice
                    assert mock_clone.call_count == 2

    def test_factory_integration(self, piece_factory):
        """Test complete integration of piece creation."""
        with patch('PieceFactory.Moves') as mock_moves_class:
            mock_moves = Mock()
            mock_moves_class.return_value = mock_moves
            
            with patch('PieceFactory.State') as mock_state_class:
                mock_states = [Mock(), Mock()]
                mock_state_class.side_effect = mock_states
                
                with patch.object(piece_factory.graphics_factory, 'load') as mock_graphics_load:
                    mock_graphics = [Mock(), Mock()]
                    mock_graphics_load.side_effect = mock_graphics
                    
                    with patch.object(piece_factory.physics_factory, 'create') as mock_physics_create:
                        mock_physics = [Mock(), Mock()]
                        mock_physics_create.side_effect = mock_physics
                        
                        with patch('PieceFactory.Piece') as mock_piece_class:
                            mock_piece = Mock()
                            mock_piece_class.return_value = mock_piece
                            
                            # Create a piece - this should work end-to-end
                            result = piece_factory.create_piece("knight", (4, 4))
                            
                            # Verify complete flow
                            assert mock_moves_class.called
                            assert mock_state_class.called
                            assert mock_graphics_load.called
                            assert mock_physics_create.called
                            assert mock_piece_class.called
                            assert result == mock_piece

    def test_error_handling_nonexistent_piece_type(self, piece_factory):
        """Test error handling for non-existent piece type."""
        with pytest.raises(FileNotFoundError):
            piece_factory.create_piece("nonexistent_piece", (0, 0))

    def test_piece_counter_persistence(self, piece_factory):
        """Test that piece counters persist across multiple creations."""
        with patch.object(piece_factory, '_get_state_machine') as mock_get_state:
            mock_states = [Mock() for _ in range(5)]
            mock_get_state.side_effect = mock_states
            
            with patch('PieceFactory.Piece') as mock_piece_class:
                mock_pieces = [Mock() for _ in range(5)]
                mock_piece_class.side_effect = mock_pieces
                
                # Create multiple pieces
                for i in range(3):
                    piece_factory.create_piece("knight", (i, 0))
                
                for i in range(2):
                    piece_factory.create_piece("pawn", (i, 1))
                
                # Check piece IDs were incremented correctly
                expected_ids = ["knight_0", "knight_1", "knight_2", "pawn_0", "pawn_1"]
                actual_ids = [call.args[0] for call in mock_piece_class.call_args_list]
                
                assert actual_ids == expected_ids

    def test_graphics_factory_integration(self, piece_factory, temp_pieces_dir):
        """Test integration with GraphicsFactory."""
        with patch('PieceFactory.Moves'):
            with patch('PieceFactory.State'):
                with patch.object(piece_factory.physics_factory, 'create'):
                    with patch.object(piece_factory.graphics_factory, 'load') as mock_graphics_load:
                        mock_graphics = Mock()
                        mock_graphics_load.return_value = mock_graphics
                        
                        with patch('PieceFactory.Piece'):
                            piece_factory.create_piece("knight", (0, 0))
                            
                            # Should call graphics factory for each state
                            assert mock_graphics_load.call_count >= 1
                            
                            # Check that correct parameters were passed
                            for call in mock_graphics_load.call_args_list:
                                sprites_dir, config, cell_size = call[0]
                                assert isinstance(sprites_dir, pathlib.Path)
                                assert isinstance(config, dict)
                                assert cell_size == (64, 64)  # From mock_board

    def test_physics_factory_integration(self, piece_factory, temp_pieces_dir):
        """Test integration with PhysicsFactory."""
        with patch('PieceFactory.Moves'):
            with patch('PieceFactory.State'):
                with patch.object(piece_factory.graphics_factory, 'load'):
                    with patch.object(piece_factory.physics_factory, 'create') as mock_physics_create:
                        mock_physics = Mock()
                        mock_physics_create.return_value = mock_physics
                        
                        with patch('PieceFactory.Piece'):
                            piece_factory.create_piece("knight", (2, 3))
                            
                            # Should call physics factory for each state
                            assert mock_physics_create.call_count >= 1
                            
                            # Check that physics factory was called with correct config
                            # Note: start_cell in template creation uses (0,0) by default
                            # The actual piece position is set later during cloning/initialization
                            for call in mock_physics_create.call_args_list:
                                start_cell, config = call[0]
                                # Physics factory is called during template creation with default position
                                assert isinstance(start_cell, tuple)
                                assert len(start_cell) == 2
                                assert isinstance(config, dict)