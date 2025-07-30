import pathlib
import cv2
from Board import Board
from Game import Game
from PieceFactory import PieceFactory
from img import Img
from ScoreManager import ScoreManager
from GameLogger import GameLogger
from SoundManager import SoundManager


def setup_board() -> Board:
    """Create the game board."""
    board_img = Img().read("../board.png", (512, 512))
    
    return Board(
        cell_H_pix=64,      # 512 / 8 = 64 pixels per cell
        cell_W_pix=64,
        cell_H_m=1,         # 1 meter per cell (for physics)
        cell_W_m=1,
        W_cells=8,          # 8x8 chess board
        H_cells=8,
        img=board_img
    )


def setup_pieces_from_csv(board: Board, pieces_root: pathlib.Path, csv_path: pathlib.Path):
    """Create all chess pieces from CSV file."""
    piece_factory = PieceFactory(board, pieces_root)
    pieces = []
    
    # Load piece positions from CSV
    pieces_data = Game.load_board_from_csv(csv_path)
    
    for piece_type, row, col in pieces_data:
        try:
            piece = piece_factory.create_piece(piece_type, (row, col))
            pieces.append(piece)
        except Exception as e:
            pass  # Skip failed pieces
    
    return pieces


def main():
    """Main entry point."""
    # Setup paths
    pieces_root = pathlib.Path("../pieces")
    csv_path = pathlib.Path("../pieces/board.csv")
    
    if not pieces_root.exists():
        return
        
    if not csv_path.exists():
        return
    
    try:
        # Create game components
        board = setup_board()
        pieces = setup_pieces_from_csv(board, pieces_root, csv_path)
        
        if not pieces:
            return
        
        # Create and run game
        game = Game(pieces, board)
        
        # Create managers using event system
        score_manager = ScoreManager(game.event_bus)
        game_logger = GameLogger(game.event_bus)
        sound_effects = SoundManager(game.event_bus)

        game.run()
        
        # Save game log after game ends
        game_logger.save_log()
        
    except FileNotFoundError as e:
        pass
    except Exception as e:
        pass
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()