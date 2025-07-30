import pathlib
from typing import Tuple, List
from Graphics import Graphics
from Board import Board


class GraphicsFactory:
    """Factory for creating Graphics objects from sprite directories."""
    
    def __init__(self):
        """Initialize the graphics factory."""
        pass
    
    def load(self,
             sprites_dir: pathlib.Path,
             cfg: dict,
             cell_size: Tuple[int, int]) -> Graphics:
        """Load graphics from sprites directory with configuration."""
        if not sprites_dir.exists():
            raise FileNotFoundError(f"Sprites directory not found: {sprites_dir}")
        
        # Extract configuration with defaults
        fps = cfg.get("frames_per_sec", 6.0)
        loop = cfg.get("is_loop", True)
        
        # Validate sprites directory has content
        sprite_files = self._get_sprite_files(sprites_dir)
        
        # Create a dummy board for Graphics constructor
        dummy_board = self._create_dummy_board(cell_size)
        
        return Graphics(
            sprites_folder=sprites_dir,
            board=dummy_board,
            loop=loop,
            fps=fps
        )
    
    def _get_sprite_files(self, sprites_dir: pathlib.Path) -> List[pathlib.Path]:
        """Get all valid sprite files from directory."""
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        sprite_files = []
        
        for file_path in sprites_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
                sprite_files.append(file_path)
        
        # Sort files for consistent animation order
        sprite_files.sort(key=lambda x: x.name)
        
        return sprite_files
    
    def _create_dummy_board(self, cell_size: Tuple[int, int]) -> Board:
        """Create a minimal board for Graphics constructor."""
        from img import Img
        
        cell_w, cell_h = cell_size
        
        # Create a small dummy image
        dummy_img = Img()
        
        return Board(
            cell_H_pix=cell_h,
            cell_W_pix=cell_w,
            cell_H_m=1,
            cell_W_m=1,
            W_cells=8,
            H_cells=8,
            img=dummy_img
        )