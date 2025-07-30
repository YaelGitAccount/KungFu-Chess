import sys
import pathlib
# הוספת הנתיב של It1_interfaces לנתיב החיפוש
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent / "It1_interfaces"))

import pytest
from unittest.mock import Mock, patch
from PhysicsFactory import PhysicsFactory
from Physics import Physics
from Board import Board


class TestPhysicsFactory:
    """Test suite for PhysicsFactory class."""
    
    @pytest.fixture
    def mock_board(self):
        """Create a mock board for testing."""
        board = Mock(spec=Board)
        board.cell_W_m = 1.0
        board.cell_H_m = 1.0
        board.W_cells = 8
        board.H_cells = 8
        return board
    
    @pytest.fixture
    def physics_factory(self, mock_board):
        """Create a PhysicsFactory with mock board."""
        return PhysicsFactory(mock_board)

    def test_initialization(self, mock_board):
        """Test proper initialization of PhysicsFactory."""
        factory = PhysicsFactory(mock_board)
        
        # Factory should store the board reference
        assert factory.board == mock_board

    def test_create_with_empty_config(self, physics_factory):
        """Test creating physics with empty configuration."""
        start_cell = (2, 3)
        config = {}
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_physics_instance = Mock()
            mock_physics_class.return_value = mock_physics_instance
            
            result = physics_factory.create(start_cell, config)
            
            # Should create Physics with default values
            mock_physics_class.assert_called_once_with(
                start_cell=(2, 3),
                board=physics_factory.board,
                speed_m_s=0.0,  # Default speed
                next_state_name="idle"  # Default next state
            )
            assert result == mock_physics_instance

    def test_create_with_complete_config(self, physics_factory):
        """Test creating physics with complete configuration."""
        start_cell = (1, 4)
        config = {
            "speed_m_per_sec": 3.0,
            "next_state_when_finished": "short_rest"
        }
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_physics_instance = Mock()
            mock_physics_class.return_value = mock_physics_instance
            
            result = physics_factory.create(start_cell, config)
            
            # Should create Physics with config values
            mock_physics_class.assert_called_once_with(
                start_cell=(1, 4),
                board=physics_factory.board,
                speed_m_s=3.0,
                next_state_name="short_rest"
            )
            assert result == mock_physics_instance

    def test_create_with_partial_config_speed_only(self, physics_factory):
        """Test creating physics with only speed configuration."""
        start_cell = (0, 0)
        config = {
            "speed_m_per_sec": 2.5
            # Missing next_state_when_finished
        }
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_physics_instance = Mock()
            mock_physics_class.return_value = mock_physics_instance
            
            result = physics_factory.create(start_cell, config)
            
            # Should use speed from config, default for next_state
            mock_physics_class.assert_called_once_with(
                start_cell=(0, 0),
                board=physics_factory.board,
                speed_m_s=2.5,
                next_state_name="idle"  # Default
            )
            assert result == mock_physics_instance

    def test_create_with_partial_config_state_only(self, physics_factory):
        """Test creating physics with only next_state configuration."""
        start_cell = (5, 2)
        config = {
            "next_state_when_finished": "move_complete"
            # Missing speed_m_per_sec
        }
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_physics_instance = Mock()
            mock_physics_class.return_value = mock_physics_instance
            
            result = physics_factory.create(start_cell, config)
            
            # Should use default speed, state from config
            mock_physics_class.assert_called_once_with(
                start_cell=(5, 2),
                board=physics_factory.board,
                speed_m_s=0.0,  # Default
                next_state_name="move_complete"
            )
            assert result == mock_physics_instance

    def test_create_with_zero_speed(self, physics_factory):
        """Test creating physics for stationary states (speed = 0)."""
        start_cell = (3, 3)
        config = {
            "speed_m_per_sec": 0.0,
            "next_state_when_finished": "idle"
        }
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_physics_instance = Mock()
            mock_physics_class.return_value = mock_physics_instance
            
            result = physics_factory.create(start_cell, config)
            
            # Should create Physics for idle/stationary state
            mock_physics_class.assert_called_once_with(
                start_cell=(3, 3),
                board=physics_factory.board,
                speed_m_s=0.0,
                next_state_name="idle"
            )
            assert result == mock_physics_instance

    def test_create_with_high_speed_movement(self, physics_factory):
        """Test creating physics for fast movement states."""
        start_cell = (7, 1)
        config = {
            "speed_m_per_sec": 5.0,
            "next_state_when_finished": "jump_complete"
        }
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_physics_instance = Mock()
            mock_physics_class.return_value = mock_physics_instance
            
            result = physics_factory.create(start_cell, config)
            
            # Should create Physics for fast movement
            mock_physics_class.assert_called_once_with(
                start_cell=(7, 1),
                board=physics_factory.board,
                speed_m_s=5.0,
                next_state_name="jump_complete"
            )
            assert result == mock_physics_instance

    def test_create_multiple_different_physics(self, physics_factory):
        """Test creating multiple physics objects with different configs."""
        configs_and_cells = [
            ((0, 0), {"speed_m_per_sec": 1.0, "next_state_when_finished": "idle"}),
            ((1, 1), {"speed_m_per_sec": 3.0, "next_state_when_finished": "short_rest"}),
            ((2, 2), {"speed_m_per_sec": 0.0, "next_state_when_finished": "long_rest"})
        ]
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_instances = [Mock(), Mock(), Mock()]
            mock_physics_class.side_effect = mock_instances
            
            results = []
            for (cell, config) in configs_and_cells:
                result = physics_factory.create(cell, config)
                results.append(result)
            
            # Should create three different Physics objects
            assert len(results) == 3
            assert mock_physics_class.call_count == 3
            
            # Check each call had correct parameters
            expected_calls = [
                ((0, 0), 1.0, "idle"),
                ((1, 1), 3.0, "short_rest"),
                ((2, 2), 0.0, "long_rest")
            ]
            
            for i, (expected_cell, expected_speed, expected_state) in enumerate(expected_calls):
                call_args = mock_physics_class.call_args_list[i]
                
                assert call_args.kwargs['start_cell'] == expected_cell
                assert call_args.kwargs['speed_m_s'] == expected_speed
                assert call_args.kwargs['next_state_name'] == expected_state

    def test_create_with_negative_speed(self, physics_factory):
        """Test creating physics with negative speed (edge case)."""
        start_cell = (2, 2)
        config = {
            "speed_m_per_sec": -1.5,
            "next_state_when_finished": "error_state"
        }
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_physics_instance = Mock()
            mock_physics_class.return_value = mock_physics_instance
            
            result = physics_factory.create(start_cell, config)
            
            # Should pass negative speed to Physics (let Physics handle validation)
            mock_physics_class.assert_called_once_with(
                start_cell=(2, 2),
                board=physics_factory.board,
                speed_m_s=-1.5,
                next_state_name="error_state"
            )
            assert result == mock_physics_instance

    def test_create_with_very_high_speed(self, physics_factory):
        """Test creating physics with very high speed."""
        start_cell = (4, 4)
        config = {
            "speed_m_per_sec": 100.0,
            "next_state_when_finished": "teleport"
        }
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_physics_instance = Mock()
            mock_physics_class.return_value = mock_physics_instance
            
            result = physics_factory.create(start_cell, config)
            
            # Should create Physics with very high speed
            mock_physics_class.assert_called_once_with(
                start_cell=(4, 4),
                board=physics_factory.board,
                speed_m_s=100.0,
                next_state_name="teleport"
            )
            assert result == mock_physics_instance

    def test_board_reference_passed_correctly(self, physics_factory, mock_board):
        """Test that the correct board reference is passed to Physics."""
        start_cell = (5, 6)
        config = {"speed_m_per_sec": 1.0, "next_state_when_finished": "idle"}
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_physics_instance = Mock()
            mock_physics_class.return_value = mock_physics_instance
            
            result = physics_factory.create(start_cell, config)
            
            # Should pass the exact board reference
            mock_physics_class.assert_called_once()
            call_args = mock_physics_class.call_args
            
            assert call_args.kwargs['board'] == mock_board

    def test_edge_case_start_positions(self, physics_factory):
        """Test creating physics with edge case start cell positions."""
        edge_cases = [
            (0, 0),      # Top-left corner
            (7, 7),      # Bottom-right corner (8x8 board)
            (0, 7),      # Top-right corner
            (7, 0),      # Bottom-left corner
        ]
        
        config = {"speed_m_per_sec": 2.0, "next_state_when_finished": "idle"}
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_instances = [Mock() for _ in edge_cases]
            mock_physics_class.side_effect = mock_instances
            
            results = []
            for start_cell in edge_cases:
                result = physics_factory.create(start_cell, config)
                results.append(result)
            
            # Should create physics for all edge positions
            assert len(results) == len(edge_cases)
            assert mock_physics_class.call_count == len(edge_cases)
            
            # Check that correct start cells were passed
            for i, expected_cell in enumerate(edge_cases):
                call_args = mock_physics_class.call_args_list[i]
                assert call_args.kwargs['start_cell'] == expected_cell

    def test_factory_reusability(self, physics_factory):
        """Test that factory can be reused multiple times."""
        config1 = {"speed_m_per_sec": 1.0, "next_state_when_finished": "idle"}
        config2 = {"speed_m_per_sec": 4.0, "next_state_when_finished": "move"}
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_instances = [Mock(), Mock()]
            mock_physics_class.side_effect = mock_instances
            
            # Create first physics
            result1 = physics_factory.create((0, 0), config1)
            
            # Create second physics with same factory
            result2 = physics_factory.create((1, 1), config2)
            
            # Should create two different objects
            assert result1 != result2
            assert result1 == mock_instances[0]
            assert result2 == mock_instances[1]
            assert mock_physics_class.call_count == 2

    def test_config_with_realistic_values(self, physics_factory):
        """Test with realistic game values matching the JSON config example."""
        start_cell = (3, 2)
        config = {
            "speed_m_per_sec": 3.0,
            "next_state_when_finished": "short_rest"
        }
        
        with patch('PhysicsFactory.Physics') as mock_physics_class:
            mock_physics_instance = Mock()
            mock_physics_class.return_value = mock_physics_instance
            
            result = physics_factory.create(start_cell, config)
            
            # Should match the JSON config example exactly
            mock_physics_class.assert_called_once_with(
                start_cell=(3, 2),
                board=physics_factory.board,
                speed_m_s=3.0,
                next_state_name="short_rest"
            )
            assert result == mock_physics_instance