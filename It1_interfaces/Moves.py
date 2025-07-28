import pathlib
from typing import List, Tuple, Dict, Optional


class Moves:
    def __init__(self, txt_path: pathlib.Path, dims: Tuple[int, int]):
        """Initialize moves with rules from text file and board dimensions."""
        self.moves: List[Tuple[int, int]] = []
        self.rows, self.cols = dims
        
        with open(txt_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                try:
                    parts = line.split(',')
                    if len(parts) != 2:
                        continue
                    
                    dr = int(parts[0].strip().split(':')[0])
                    dc = int(parts[1].strip().split(':')[0])
                    
                    self.moves.append((dr, dc))
                    
                except (ValueError, IndexError):
                    continue

    def get_moves(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Return list of legal moves from position (r, c) within board limits."""
        legal_moves = []

        for dr, dc in self.moves:
            new_r = r + dr
            new_c = c + dc

            if 0 <= new_r < self.rows and 0 <= new_c < self.cols:
                legal_moves.append((new_r, new_c))

        return legal_moves