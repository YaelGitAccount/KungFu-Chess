import pathlib
from typing import List, Optional
import copy
from img import Img
from Command import Command
from Board import Board


class Graphics:
    def __init__(self,
                 sprites_folder: pathlib.Path,
                 board: Board,
                 loop: bool = True,
                 fps: float = 6.0):
        """Initialize graphics with sprites folder, cell size, loop setting, and FPS."""
        self.sprites_folder = sprites_folder
        self.board = board
        self.loop = loop
        self.fps = fps
        
        # All sprite images
        self.sprites: List[Img] = []
        
        # Animation state
        self.current_frame = 0
        self.start_time_ms = 0
        self.frame_duration_ms = int(1000 / fps) if fps > 0 else 1000
        self.is_finished = False
        
        self._load_sprites()

    def _load_sprites(self):
        """Load all sprite images from folder."""
        if not self.sprites_folder.exists():
            return
            
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        sprite_files = []
        
        # Collect all image files
        for file_path in self.sprites_folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
                sprite_files.append(file_path)
        
        # Sort by name for consistent order
        sprite_files.sort(key=lambda x: x.name)
        
        # Load images
        cell_size = (self.board.cell_W_pix, self.board.cell_H_pix)
        for sprite_file in sprite_files:
            try:
                img = Img().read(sprite_file, cell_size)
                self.sprites.append(img)
            except Exception as e:
                # Skip unloadable images
                continue
        
        # Create default empty image if no sprites loaded
        if not self.sprites:
            default_img = Img()
            self.sprites.append(default_img)

    def copy(self):
        """Create a shallow copy of the graphics object."""
        new_graphics = Graphics(
            self.sprites_folder,
            self.board,
            self.loop,
            self.fps
        )
        # Copy current state
        new_graphics.current_frame = self.current_frame
        new_graphics.start_time_ms = self.start_time_ms
        new_graphics.is_finished = self.is_finished
        return new_graphics

    def reset(self, start_time_ms: int):
        """Reset the animation with a new start time."""
        self.start_time_ms = start_time_ms
        self.current_frame = 0
        self.is_finished = False

    def update(self, now_ms: int):
        """Advance animation frame based on game-loop time."""
        if not self.sprites or self.is_finished:
            return
            
        if self.start_time_ms == 0:
            self.start_time_ms = now_ms
            return
        
        # Calculate elapsed time since animation start
        elapsed_ms = now_ms - self.start_time_ms
        
        # Calculate target frame
        target_frame = elapsed_ms // self.frame_duration_ms
        
        if self.loop:
            # Looping animation - return to start
            if len(self.sprites) > 0:
                self.current_frame = target_frame % len(self.sprites)
        else:
            # One-time animation
            if target_frame >= len(self.sprites):
                self.current_frame = len(self.sprites) - 1  # Stay on last frame
                self.is_finished = True
            else:
                self.current_frame = target_frame

    def get_img(self) -> Optional[Img]:
        """Get the current frame image."""
        if not self.sprites:
            return None
            
        # Ensure valid index
        if 0 <= self.current_frame < len(self.sprites):
            return self.sprites[self.current_frame]
        
        return self.sprites[0] if self.sprites else None
    
    def is_animation_finished(self) -> bool:
        """Check if animation is finished (relevant only for loop=False)."""
        return self.is_finished
    
    def get_frame_count(self) -> int:
        """Return number of frames in animation."""
        return len(self.sprites)
    
    def set_frame(self, frame_index: int):
        """Set specific frame (for testing or special cases)."""
        if 0 <= frame_index < len(self.sprites):
            self.current_frame = frame_index