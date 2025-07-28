from enum import Enum

class PieceType(Enum):
    PAWN = "P"
    KNIGHT = "N"
    BISHOP = "B"
    ROOK = "R"
    QUEEN = "Q"
    KING = "K"


    class PieceColor(Enum):
        WHITE = "W"
        BLACK = "B"