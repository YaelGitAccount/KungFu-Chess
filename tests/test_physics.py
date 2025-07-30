import sys
import pathlib
import pytest
import math
from unittest.mock import Mock

# הוספת הנתיב של It1_interfaces לנתיב החיפוש
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent / "It1_interfaces"))

from Physics import Physics
from Board import Board


class TestPhysics:
    """Test suite for Physics class."""
    
    @pytest.fixture
    def mock_board(self):
        """Create a mock board for testing."""
        board = Mock(spec=Board)
        board.cell_W_m = 1.0  # 1 meter per cell width
        board.cell_H_m = 1.0  # 1 meter per cell height
        board.cell_W_pix = 64  # 64 pixels per cell width
        board.cell_H_pix = 64  # 64 pixels per cell height
        return board
    
    @pytest.fixture
    def physics_moving(self, mock_board):
        """Create a physics object for movement testing."""
        return Physics(
            start_cell=(2, 3),
            board=mock_board,
            speed_m_s=2.0,  # 2 meters per second
            next_state_name="idle"
        )
    
    @pytest.fixture
    def physics_idle(self, mock_board):
        """Create a physics object for idle state testing."""
        return Physics(
            start_cell=(1, 1),
            board=mock_board,
            speed_m_s=0.0,  # No movement
            next_state_name="idle"
        )
    
    @pytest.fixture
    def physics_rest(self, mock_board):
        """Create a physics object for rest state testing."""
        return Physics(
            start_cell=(0, 0),
            board=mock_board,
            speed_m_s=0.0,  # No movement
            next_state_name="idle"  # Will return to idle after 2 seconds
        )

    def test_initialization(self, mock_board):
        """Test proper initialization of Physics object."""
        start_cell = (2, 3)
        speed = 1.5
        next_state = "move"
        
        physics = Physics(start_cell, mock_board, speed, next_state)
        
        assert physics.start_cell == start_cell
        assert physics.current_cell == start_cell
        assert physics.target_cell == start_cell
        assert physics.board == mock_board
        assert physics.speed_m_s == speed
        assert physics.next_state_name == next_state
        assert physics.start_time_ms == 0
        assert physics.total_distance_m == 0
        assert physics.traveled_distance_m == 0

    def test_set_target(self, physics_moving):
        """Test target setting and distance calculation."""
        # Test setting target from (2,3) to (5,7)
        target = (5, 7)
        physics_moving.set_target(target)
        
        assert physics_moving.target_cell == target
        
        # Calculate expected distance: sqrt((5-2)² + (7-3)²) * 1.0m
        expected_distance = math.sqrt(3*3 + 4*4) * 1.0  # = 5.0 meters
        assert physics_moving.total_distance_m == pytest.approx(expected_distance)

    def test_reset(self, physics_moving):
        """Test physics reset functionality."""
        start_time = 1000
        physics_moving.traveled_distance_m = 10.0  # Set some travel distance
        
        physics_moving.reset(start_time)
        
        assert physics_moving.start_time_ms == start_time
        assert physics_moving.traveled_distance_m == 0

    def test_update_before_reset(self, physics_moving):
        """Test update returns None when start_time_ms is 0."""
        result = physics_moving.update(1000)
        assert result is None

    def test_idle_state_no_movement(self, physics_idle):
        """Test idle state (speed=0, next_state='idle') stays in place."""
        physics_idle.reset(1000)
        
        # Update after some time
        result = physics_idle.update(3000)
        
        assert result is None  # Should not transition
        assert physics_idle.current_cell == physics_idle.start_cell

    def test_rest_state_transition(self, mock_board):
        """Test rest state (speed=0, next_state != 'idle') transitions after 2 seconds."""
        physics = Physics(
            start_cell=(1, 1),
            board=mock_board,
            speed_m_s=0.0,
            next_state_name="move"  # Not idle
        )
        
        physics.reset(1000)
        
        # Update before 2 seconds - should not transition
        result = physics.update(2500)  # 1.5 seconds elapsed
        assert result is None
        
        # Update after 2 seconds - should transition
        result = physics.update(3000)  # 2 seconds elapsed
        assert result == "move"

    def test_movement_in_progress(self, physics_moving):
        """Test movement calculation during travel."""
        physics_moving.set_target((2, 6))  # Move 3 cells right (3 meters)
        physics_moving.reset(1000)
        
        # After 1 second at 2 m/s, should travel 2 meters
        result = physics_moving.update(2000)
        
        assert result is None  # Movement not finished
        assert physics_moving.traveled_distance_m == pytest.approx(2.0)
        
        # Check interpolated position
        # Start: (2,3), Target: (2,6), Progress: 2/3 = 0.667
        expected_col = 3 + (6 - 3) * (2.0 / 3.0)  # 3 + 3 * 0.667 = 5
        assert physics_moving.current_cell[0] == pytest.approx(2.0)
        assert physics_moving.current_cell[1] == pytest.approx(expected_col)

    def test_movement_completion(self, physics_moving):
        """Test movement completion and state transition."""
        physics_moving.set_target((2, 5))  # Move 2 cells right (2 meters)
        physics_moving.reset(1000)
        
        # After 1 second at 2 m/s, should complete the 2-meter journey
        result = physics_moving.update(2000)
        
        assert result == "idle"  # Should transition to next state
        assert physics_moving.current_cell == (2, 5)  # Should be at target

    def test_movement_overshoot(self, physics_moving):
        """Test movement when traveled distance exceeds total distance."""
        physics_moving.set_target((2, 4))  # Move 1 cell right (1 meter)
        physics_moving.reset(1000)
        
        # After 1 second at 2 m/s, should travel 2 meters (overshooting 1 meter target)
        result = physics_moving.update(2000)
        
        assert result == "idle"  # Should complete and transition
        assert physics_moving.current_cell == (2, 4)  # Should be exactly at target

    def test_zero_distance_movement(self, physics_moving):
        """Test movement when target is same as current position."""
        physics_moving.set_target(physics_moving.current_cell)  # Same position
        physics_moving.reset(1000)
        
        result = physics_moving.update(2000)
        
        assert result == "idle"  # Should immediately complete
        assert physics_moving.current_cell == physics_moving.start_cell

    def test_get_pos_meters(self, physics_moving):
        """Test position conversion to meters for drawing."""
        # Set position to (2, 3)
        physics_moving.current_cell = (2.5, 3.7)
        
        pos_m = physics_moving.get_pos()
        
        # Expected: x = col * cell_W_m, y = row * cell_H_m
        expected_x = 3.7 * 1.0  # = 3.7 meters
        expected_y = 2.5 * 1.0  # = 2.5 meters
        
        assert pos_m[0] == pytest.approx(expected_x)
        assert pos_m[1] == pytest.approx(expected_y)

    def test_diagonal_movement(self, physics_moving):
        """Test diagonal movement calculation."""
        physics_moving.set_target((5, 6))  # From (2,3) to (5,6) - diagonal move
        
        # Expected distance: sqrt((5-2)² + (6-3)²) = sqrt(9+9) = sqrt(18) ≈ 4.24 meters
        expected_distance = math.sqrt(18)
        assert physics_moving.total_distance_m == pytest.approx(expected_distance)
        
        physics_moving.reset(1000)
        
        # After 2 seconds at 2 m/s = 4 meters traveled
        # Progress = 4/4.24 ≈ 0.943
        physics_moving.update(3000)
        
        progress = 4.0 / expected_distance
        expected_row = 2 + (5 - 2) * progress
        expected_col = 3 + (6 - 3) * progress
        
        assert physics_moving.current_cell[0] == pytest.approx(expected_row, abs=0.01)
        assert physics_moving.current_cell[1] == pytest.approx(expected_col, abs=0.01)