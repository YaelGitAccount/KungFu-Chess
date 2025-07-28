import sys
import pathlib
# הוספת הנתיב של It1_interfaces לנתיב החיפוש
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent / "It1_interfaces"))

import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch

from GraphicsFactory import GraphicsFactory


class TestGraphicsFactory:
    """Test suite for GraphicsFactory class."""
    
    @pytest.fixture
    def graphics_factory(self):
        """Create a GraphicsFactory for testing."""
        return GraphicsFactory()
    
    @pytest.fixture
    def temp_sprites_dir(self):
        """Create a temporary directory with mock sprite files."""
        temp_dir = pathlib.Path(tempfile.mkdtemp())
        
        # Create some mock sprite files with realistic names
        (temp_dir / "frame_01.png").touch()
        (temp_dir / "frame_02.png").touch()
        (temp_dir / "frame_03.png").touch()
        (temp_dir / "idle_sprite.jpg").touch()
        (temp_dir / "invalid_file.txt").touch()  # Non-image file
        (temp_dir / "another.bmp").touch()
        
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
    def cell_size(self):
        """Standard cell size for testing."""
        return (64, 64)

    def test_initialization(self):
        """Test proper initialization of GraphicsFactory."""
        factory = GraphicsFactory()
        
        # Factory should initialize without errors
        assert factory is not None

    def test_load_with_complete_config(self, graphics_factory, temp_sprites_dir, cell_size):
        """Test loading graphics with complete configuration."""
        config = {
            "frames_per_sec": 8,
            "is_loop": False
        }
        
        with patch('GraphicsFactory.Graphics') as mock_graphics_class:
            mock_graphics_instance = Mock()
            mock_graphics_class.return_value = mock_graphics_instance
            
            result = graphics_factory.load(temp_sprites_dir, config, cell_size)
            
            # Should create Graphics with config values
            mock_graphics_class.assert_called_once()
            call_args = mock_graphics_class.call_args
            
            assert call_args.kwargs['sprites_folder'] == temp_sprites_dir
            assert call_args.kwargs['fps'] == 8
            assert call_args.kwargs['loop'] == False
            assert result == mock_graphics_instance

    def test_load_with_default_config(self, graphics_factory, temp_sprites_dir, cell_size):
        """Test loading graphics with empty configuration (uses defaults)."""
        config = {}
        
        with patch('GraphicsFactory.Graphics') as mock_graphics_class:
            mock_graphics_instance = Mock()
            mock_graphics_class.return_value = mock_graphics_instance
            
            result = graphics_factory.load(temp_sprites_dir, config, cell_size)
            
            # Should create Graphics with default values
            mock_graphics_class.assert_called_once()
            call_args = mock_graphics_class.call_args
            
            assert call_args.kwargs['fps'] == 6.0      # Default
            assert call_args.kwargs['loop'] == True    # Default
            assert result == mock_graphics_instance

    def test_load_with_partial_config_fps_only(self, graphics_factory, temp_sprites_dir, cell_size):
        """Test loading graphics with only FPS configuration."""
        config = {
            "frames_per_sec": 12
            # Missing is_loop
        }
        
        with patch('GraphicsFactory.Graphics') as mock_graphics_class:
            mock_graphics_instance = Mock()
            mock_graphics_class.return_value = mock_graphics_instance
            
            result = graphics_factory.load(temp_sprites_dir, config, cell_size)
            
            # Should use FPS from config, default for loop
            mock_graphics_class.assert_called_once()
            call_args = mock_graphics_class.call_args
            
            assert call_args.kwargs['fps'] == 12
            assert call_args.kwargs['loop'] == True    # Default
            assert result == mock_graphics_instance

    def test_load_with_partial_config_loop_only(self, graphics_factory, temp_sprites_dir, cell_size):
        """Test loading graphics with only loop configuration."""
        config = {
            "is_loop": False
            # Missing frames_per_sec
        }
        
        with patch('GraphicsFactory.Graphics') as mock_graphics_class:
            mock_graphics_instance = Mock()
            mock_graphics_class.return_value = mock_graphics_instance
            
            result = graphics_factory.load(temp_sprites_dir, config, cell_size)
            
            # Should use default FPS, loop from config
            mock_graphics_class.assert_called_once()
            call_args = mock_graphics_class.call_args
            
            assert call_args.kwargs['fps'] == 6.0      # Default
            assert call_args.kwargs['loop'] == False
            assert result == mock_graphics_instance

    def test_load_with_realistic_config(self, graphics_factory, temp_sprites_dir, cell_size):
        """Test loading graphics with realistic config matching JSON example."""
        config = {
            "frames_per_sec": 8,
            "is_loop": False
        }
        
        with patch('GraphicsFactory.Graphics') as mock_graphics_class:
            mock_graphics_instance = Mock()
            mock_graphics_class.return_value = mock_graphics_instance
            
            result = graphics_factory.load(temp_sprites_dir, config, cell_size)
            
            # Should match the JSON config example exactly
            mock_graphics_class.assert_called_once()
            call_args = mock_graphics_class.call_args
            
            assert call_args.kwargs['fps'] == 8
            assert call_args.kwargs['loop'] == False
            assert result == mock_graphics_instance

    def test_load_nonexistent_directory(self, graphics_factory, cell_size):
        """Test loading from non-existent sprites directory."""
        fake_dir = pathlib.Path("/nonexistent/sprites/directory")
        config = {"frames_per_sec": 6.0, "is_loop": True}
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Sprites directory not found"):
            graphics_factory.load(fake_dir, config, cell_size)

    def test_load_empty_sprites_directory(self, graphics_factory, empty_sprites_dir, cell_size):
        """Test loading from empty sprites directory."""
        config = {"frames_per_sec": 6.0, "is_loop": True}
        
        with patch('GraphicsFactory.Graphics') as mock_graphics_class:
            mock_graphics_instance = Mock()
            mock_graphics_class.return_value = mock_graphics_instance
            
            # Should not raise error, but print warning
            result = graphics_factory.load(empty_sprites_dir, config, cell_size)
            
            # Should still create Graphics object
            mock_graphics_class.assert_called_once()
            assert result == mock_graphics_instance

    def test_get_sprite_files_filtering(self, graphics_factory, temp_sprites_dir):
        """Test that _get_sprite_files correctly filters image files."""
        sprite_files = graphics_factory._get_sprite_files(temp_sprites_dir)
        
        # Should find image files but not .txt files
        file_names = [f.name for f in sprite_files]
        
        # Should include image files
        assert "frame_01.png" in file_names
        assert "frame_02.png" in file_names
        assert "frame_03.png" in file_names
        assert "idle_sprite.jpg" in file_names
        assert "another.bmp" in file_names
        
        # Should exclude non-image files
        assert "invalid_file.txt" not in file_names
        
        # Should be sorted alphabetically
        sorted_names = sorted(file_names)
        assert file_names == sorted_names

    def test_get_sprite_files_empty_directory(self, graphics_factory, empty_sprites_dir):
        """Test _get_sprite_files with empty directory."""
        sprite_files = graphics_factory._get_sprite_files(empty_sprites_dir)
        
        assert sprite_files == []

    def test_get_sprite_files_supported_extensions(self, graphics_factory):
        """Test that _get_sprite_files supports all expected image formats."""
        temp_dir = pathlib.Path(tempfile.mkdtemp())
        
        # Create files with different extensions
        test_files = [
            "image.png", "image.jpg", "image.jpeg", 
            "image.bmp", "image.tiff", "image.PNG",
            "image.JPG", "not_image.txt", "no_extension"
        ]
        
        for filename in test_files:
            (temp_dir / filename).touch()
        
        try:
            sprite_files = graphics_factory._get_sprite_files(temp_dir)
            file_names = [f.name for f in sprite_files]
            
            # Should include lowercase image formats
            expected_lowercase = [
                "image.png", "image.jpg", "image.jpeg", 
                "image.bmp", "image.tiff"
            ]
            
            for expected in expected_lowercase:
                assert expected in file_names
            
            # Check if uppercase extensions are supported (depends on implementation)
            # The current implementation handles case-insensitive extensions
            total_image_files = len([f for f in file_names if not f.endswith('.txt')])
            assert total_image_files >= 5  # At least the lowercase ones
                
            # Should exclude non-images
            assert "not_image.txt" not in file_names
            assert "no_extension" not in file_names
            
        finally:
            shutil.rmtree(temp_dir)

    def test_create_dummy_board(self, graphics_factory, cell_size):
        """Test _create_dummy_board creates proper Board object."""
        # The _create_dummy_board method imports Img locally, so we need to patch it there
        with patch('img.Img') as mock_img_class:
            mock_img_instance = Mock()
            mock_img_class.return_value = mock_img_instance
            
            board = graphics_factory._create_dummy_board(cell_size)
            
            # Should create Board with correct cell sizes
            assert board.cell_W_pix == 64
            assert board.cell_H_pix == 64
            assert board.cell_W_m == 1
            assert board.cell_H_m == 1
            assert board.W_cells == 8
            assert board.H_cells == 8
            assert board.img == mock_img_instance

    def test_create_dummy_board_different_sizes(self, graphics_factory):
        """Test _create_dummy_board with different cell sizes."""
        test_sizes = [(32, 48), (128, 96), (16, 16)]
        
        for width, height in test_sizes:
            with patch('img.Img'):
                board = graphics_factory._create_dummy_board((width, height))
                
                assert board.cell_W_pix == width
                assert board.cell_H_pix == height

    def test_load_multiple_graphics_objects(self, graphics_factory, cell_size):
        """Test loading multiple graphics objects with different configurations."""
        temp_dirs = []
        try:
            # Create multiple sprite directories
            for i in range(3):
                temp_dir = pathlib.Path(tempfile.mkdtemp())
                temp_dirs.append(temp_dir)
                (temp_dir / f"sprite_{i}.png").touch()
            
            configs = [
                {"frames_per_sec": 6, "is_loop": True},
                {"frames_per_sec": 12, "is_loop": False},
                {"frames_per_sec": 4, "is_loop": True}
            ]
            
            with patch('GraphicsFactory.Graphics') as mock_graphics_class:
                mock_instances = [Mock(), Mock(), Mock()]
                mock_graphics_class.side_effect = mock_instances
                
                results = []
                for i, (temp_dir, config) in enumerate(zip(temp_dirs, configs)):
                    result = graphics_factory.load(temp_dir, config, cell_size)
                    results.append(result)
                
                # Should create three different Graphics objects
                assert len(results) == 3
                assert mock_graphics_class.call_count == 3
                
                # Check each was called with correct config
                for i, call in enumerate(mock_graphics_class.call_args_list):
                    expected_fps = configs[i]["frames_per_sec"]
                    expected_loop = configs[i]["is_loop"]
                    
                    assert call.kwargs['fps'] == expected_fps
                    assert call.kwargs['loop'] == expected_loop
                    assert call.kwargs['sprites_folder'] == temp_dirs[i]
        
        finally:
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

    def test_load_with_invalid_config_types(self, graphics_factory, temp_sprites_dir, cell_size):
        """Test loading with invalid configuration value types."""
        config = {
            "frames_per_sec": "invalid_string",  # Should be number
            "is_loop": "not_boolean"             # Should be boolean
        }
        
        with patch('GraphicsFactory.Graphics') as mock_graphics_class:
            mock_graphics_instance = Mock()
            mock_graphics_class.return_value = mock_graphics_instance
            
            # Should handle gracefully by using defaults or passed values
            result = graphics_factory.load(temp_sprites_dir, config, cell_size)
            
            # Should not crash and create Graphics object
            mock_graphics_class.assert_called_once()
            assert result == mock_graphics_instance

    def test_load_board_passed_to_graphics(self, graphics_factory, temp_sprites_dir, cell_size):
        """Test that created dummy board is passed to Graphics constructor."""
        config = {"frames_per_sec": 8, "is_loop": False}
        
        with patch('GraphicsFactory.Graphics') as mock_graphics_class:
            mock_graphics_instance = Mock()
            mock_graphics_class.return_value = mock_graphics_instance
            
            result = graphics_factory.load(temp_sprites_dir, config, cell_size)
            
            # Should pass board to Graphics
            mock_graphics_class.assert_called_once()
            call_args = mock_graphics_class.call_args
            
            board_arg = call_args.kwargs['board']
            assert board_arg is not None
            assert hasattr(board_arg, 'cell_W_pix')
            assert hasattr(board_arg, 'cell_H_pix')
            assert board_arg.cell_W_pix == 64
            assert board_arg.cell_H_pix == 64

    def test_factory_reusability(self, graphics_factory, cell_size):
        """Test that factory can be reused to load multiple graphics."""
        temp_dirs = []
        try:
            # Create two sprite directories
            for i in range(2):
                temp_dir = pathlib.Path(tempfile.mkdtemp())
                temp_dirs.append(temp_dir)
                (temp_dir / f"sprite_{i}.png").touch()
            
            config1 = {"frames_per_sec": 6, "is_loop": True}
            config2 = {"frames_per_sec": 10, "is_loop": False}
            
            with patch('GraphicsFactory.Graphics') as mock_graphics_class:
                mock_instances = [Mock(), Mock()]
                mock_graphics_class.side_effect = mock_instances
                
                # Load first graphics
                result1 = graphics_factory.load(temp_dirs[0], config1, cell_size)
                
                # Load second graphics with same factory
                result2 = graphics_factory.load(temp_dirs[1], config2, cell_size)
                
                # Should create two different objects
                assert result1 != result2
                assert result1 == mock_instances[0]
                assert result2 == mock_instances[1]
                assert mock_graphics_class.call_count == 2
        
        finally:
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)