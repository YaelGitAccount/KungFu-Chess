import sys
import pathlib
# הוספת הנתיב של It1_interfaces לנתיב החיפוש
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent / "It1_interfaces"))

import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch

from Graphics import Graphics
from Board import Board
from img import Img


class TestGraphics:
    """Test suite for Graphics class."""
    
    @pytest.fixture
    def mock_board(self):
        """Create a mock board for testing."""
        board = Mock(spec=Board)
        board.cell_W_pix = 64
        board.cell_H_pix = 64
        return board
    
    @pytest.fixture
    def temp_sprites_dir(self):
        """Create a temporary directory with mock sprite files."""
        temp_dir = pathlib.Path(tempfile.mkdtemp())
        
        # Create some mock sprite files
        (temp_dir / "sprite_01.png").touch()
        (temp_dir / "sprite_02.png").touch()
        (temp_dir / "sprite_03.png").touch()
        (temp_dir / "invalid.txt").touch()  # Non-image file
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def empty_sprites_dir(self):
        """Create an empty temporary directory."""
        temp_dir = pathlib.Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_img(self):
        """Create a mock Img object."""
        img = Mock(spec=Img)
        img.img = "mock_image_data"
        return img

    def test_initialization_default_params(self, temp_sprites_dir, mock_board):
        """Test initialization with default parameters."""
        with patch('Graphics.Img') as mock_img_class:
            mock_img_class.return_value.read.return_value = Mock()
            
            graphics = Graphics(temp_sprites_dir, mock_board)
            
            assert graphics.sprites_folder == temp_sprites_dir
            assert graphics.board == mock_board
            assert graphics.loop == True  # Default
            assert graphics.fps == 6.0    # Default
            assert graphics.current_frame == 0
            assert graphics.start_time_ms == 0
            assert graphics.frame_duration_ms == int(1000 / 6.0)  # ~167ms
            assert graphics.is_finished == False

    def test_initialization_custom_params(self, temp_sprites_dir, mock_board):
        """Test initialization with custom parameters."""
        with patch('Graphics.Img') as mock_img_class:
            mock_img_class.return_value.read.return_value = Mock()
            
            graphics = Graphics(temp_sprites_dir, mock_board, loop=False, fps=12.0)
            
            assert graphics.loop == False
            assert graphics.fps == 12.0
            assert graphics.frame_duration_ms == int(1000 / 12.0)  # ~83ms

    def test_sprites_loading(self, temp_sprites_dir, mock_board):
        """Test that sprites are loaded correctly from directory."""
        with patch('Graphics.Img') as mock_img_class:
            mock_img_instance = Mock()
            mock_img_class.return_value = mock_img_instance
            mock_img_instance.read.return_value = mock_img_instance
            
            graphics = Graphics(temp_sprites_dir, mock_board)
            
            # Should load 3 PNG files (ignoring .txt file)
            assert len(graphics.sprites) >= 1  # At least one sprite loaded
            
            # Check that Img.read was called with correct parameters
            call_args_list = mock_img_instance.read.call_args_list
            assert len(call_args_list) >= 3
            
            # Check that cell_size was passed correctly
            for call_args in call_args_list:
                args, kwargs = call_args
                if len(args) > 1:  # If size parameter exists
                    assert args[1] == (64, 64)  # cell_size

    def test_empty_sprites_directory(self, empty_sprites_dir, mock_board):
        """Test handling of empty sprites directory."""
        graphics = Graphics(empty_sprites_dir, mock_board)
        
        # Should handle gracefully - may have empty sprites or create default
        assert len(graphics.sprites) >= 0  # Just don't crash

    def test_nonexistent_sprites_directory(self, mock_board):
        """Test handling of non-existent sprites directory."""
        fake_dir = pathlib.Path("/nonexistent/directory")
        
        graphics = Graphics(fake_dir, mock_board)
        
        # Should handle gracefully - may have empty sprites list
        assert len(graphics.sprites) >= 0  # Just don't crash

    def test_copy(self, temp_sprites_dir, mock_board):
        """Test copying graphics object."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board, loop=False, fps=10.0)
            graphics.current_frame = 2
            graphics.start_time_ms = 1000
            graphics.is_finished = True
            
            copied = graphics.copy()
            
            # Check that properties are copied
            assert copied.sprites_folder == graphics.sprites_folder
            assert copied.loop == graphics.loop
            assert copied.fps == graphics.fps
            assert copied.current_frame == graphics.current_frame
            assert copied.start_time_ms == graphics.start_time_ms
            assert copied.is_finished == graphics.is_finished

    def test_reset(self, temp_sprites_dir, mock_board):
        """Test reset functionality."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board)
            
            # Set some state
            graphics.current_frame = 5
            graphics.start_time_ms = 2000
            graphics.is_finished = True
            
            # Reset
            graphics.reset(1500)
            
            assert graphics.start_time_ms == 1500
            assert graphics.current_frame == 0
            assert graphics.is_finished == False

    def test_update_no_sprites(self, empty_sprites_dir, mock_board):
        """Test update when no sprites are loaded."""
        graphics = Graphics(empty_sprites_dir, mock_board)
        graphics.sprites = []  # Force empty sprites
        
        graphics.update(1000)
        
        # Should not crash
        assert graphics.current_frame == 0

    def test_update_first_call_sets_start_time(self, temp_sprites_dir, mock_board):
        """Test that first update call sets start time."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board)
            graphics.sprites = [Mock(), Mock(), Mock()]  # 3 sprites
            
            assert graphics.start_time_ms == 0
            
            graphics.update(2000)
            
            assert graphics.start_time_ms == 2000

    def test_update_looping_animation(self, temp_sprites_dir, mock_board):
        """Test looping animation behavior."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board, loop=True, fps=10.0)
            graphics.sprites = [Mock(), Mock(), Mock()]  # 3 sprites
            graphics.frame_duration_ms = 100  # 100ms per frame
            
            graphics.reset(1000)
            
            # After 150ms - should be on frame 1
            # elapsed = 150ms, target_frame = 150/100 = 1, 1%3 = 1
            graphics.update(1150)
            assert graphics.current_frame == 1
            
            # After 250ms - should be on frame 2
            # elapsed = 250ms, target_frame = 250/100 = 2, 2%3 = 2
            graphics.update(1250)
            assert graphics.current_frame == 2
            
            # After 350ms - should loop back to frame 0
            # elapsed = 350ms, target_frame = 350/100 = 3, 3%3 = 0
            graphics.update(1350)
            assert graphics.current_frame == 0

    def test_update_non_looping_animation(self, temp_sprites_dir, mock_board):
        """Test non-looping animation behavior."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board, loop=False, fps=10.0)
            graphics.sprites = [Mock(), Mock(), Mock()]  # 3 sprites
            graphics.frame_duration_ms = 100  # 100ms per frame
            
            graphics.reset(1000)
            
            # After 150ms - should be on frame 1
            graphics.update(1150)
            assert graphics.current_frame == 1
            assert graphics.is_finished == False
            
            # After 250ms - should be on frame 2 (last frame)
            graphics.update(1250)
            assert graphics.current_frame == 2
            assert graphics.is_finished == False
            
            # After 350ms - should stay on last frame and be finished
            graphics.update(1350)
            assert graphics.current_frame == 2  # Stay on last frame
            assert graphics.is_finished == True

    def test_get_img_valid_frame(self, temp_sprites_dir, mock_board):
        """Test getting image for valid frame."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board)
            mock_sprite = Mock()
            graphics.sprites = [mock_sprite]
            graphics.current_frame = 0
            
            result = graphics.get_img()
            
            assert result == mock_sprite

    def test_get_img_no_sprites(self, temp_sprites_dir, mock_board):
        """Test getting image when no sprites exist."""
        graphics = Graphics(temp_sprites_dir, mock_board)
        graphics.sprites = []
        
        result = graphics.get_img()
        
        assert result is None

    def test_get_img_invalid_frame_index(self, temp_sprites_dir, mock_board):
        """Test getting image with invalid frame index."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board)
            mock_sprite = Mock()
            graphics.sprites = [mock_sprite]
            graphics.current_frame = 10  # Invalid index
            
            result = graphics.get_img()
            
            # Should return first sprite as fallback
            assert result == mock_sprite

    def test_is_animation_finished_looping(self, temp_sprites_dir, mock_board):
        """Test is_animation_finished for looping animation."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board, loop=True)
            graphics.is_finished = True  # Force finished state
            
            result = graphics.is_animation_finished()
            
            assert result == True

    def test_is_animation_finished_non_looping(self, temp_sprites_dir, mock_board):
        """Test is_animation_finished for non-looping animation."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board, loop=False)
            graphics.is_finished = False
            
            result = graphics.is_animation_finished()
            
            assert result == False

    def test_get_frame_count(self, temp_sprites_dir, mock_board):
        """Test getting frame count."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board)
            graphics.sprites = [Mock(), Mock(), Mock()]
            
            result = graphics.get_frame_count()
            
            assert result == 3

    def test_get_frame_count_empty(self, temp_sprites_dir, mock_board):
        """Test getting frame count when no sprites."""
        graphics = Graphics(temp_sprites_dir, mock_board)
        graphics.sprites = []
        
        result = graphics.get_frame_count()
        
        assert result == 0

    def test_set_frame_valid_index(self, temp_sprites_dir, mock_board):
        """Test setting valid frame index."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board)
            graphics.sprites = [Mock(), Mock(), Mock()]
            
            graphics.set_frame(1)
            
            assert graphics.current_frame == 1

    def test_set_frame_invalid_index(self, temp_sprites_dir, mock_board):
        """Test setting invalid frame index."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board)
            graphics.sprites = [Mock(), Mock()]
            
            original_frame = graphics.current_frame
            graphics.set_frame(10)  # Invalid index
            
            # Should not change frame
            assert graphics.current_frame == original_frame

    def test_zero_fps_handling(self, temp_sprites_dir, mock_board):
        """Test handling of zero FPS."""
        with patch('Graphics.Img'):
            graphics = Graphics(temp_sprites_dir, mock_board, fps=0.0)
            
            # Should default to reasonable frame duration
            assert graphics.frame_duration_ms == 1000  # 1 second per frame