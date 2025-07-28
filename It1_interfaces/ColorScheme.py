"""
Game color definitions - central color settings for the entire game
All colors in BGR format (Blue, Green, Red) for OpenCV
"""

class Colors:
    # Chess board colors
    BOARD_LIGHT = (215, 235, 245)  # Light cream
    BOARD_DARK = (65, 105, 139)    # Chocolate brown
    
    # Background colors
    BACKGROUND_MAIN = (125, 170, 205)  # Light wood brown
    BACKGROUND_SEPARATOR = (80, 110, 140)  # Dark brown for borders
    SEPARATOR_THICKNESS = 2
    
    # Move table colors - white player
    WHITE_TABLE_BG = (225, 240, 250)
    WHITE_TABLE_HEADER = (190, 210, 225)
    WHITE_TABLE_TEXT = (20, 30, 40)
    WHITE_TABLE_ALT_ROW = (210, 225, 235)
    WHITE_TABLE_BORDER = (100, 120, 140)
    
    # Move table colors - black player
    BLACK_TABLE_BG = (40, 50, 60)
    BLACK_TABLE_HEADER = (30, 40, 50)
    BLACK_TABLE_TEXT = (230, 230, 230)
    BLACK_TABLE_ALT_ROW = (50, 60, 70)
    BLACK_TABLE_BORDER = (80, 90, 100)
    
    # Player cursor colors
    PLAYER1_CURSOR = (0, 0, 255)  # Red
    PLAYER2_CURSOR = (255, 0, 0)  # Blue
    PLAYER1_SELECTION_BG = (150, 150, 255)  # Light red for selection
    PLAYER2_SELECTION_BG = (255, 150, 150)  # Light blue for selection
    
    # General text colors
    SCORE_TEXT_COLOR = (0, 0, 0)  # Black
    LABEL_TEXT_COLOR = (0, 0, 0)  # Black
    
    # Text sizes
    SCORE_FONT_SIZE = 0.7
    SCORE_FONT_THICKNESS = 2
    TABLE_TITLE_FONT_SIZE = 0.7
    TABLE_HEADER_FONT_SIZE = 0.5
    TABLE_ROW_FONT_SIZE = 0.45
    
    @classmethod
    def get_table_colors(cls, player_color: str):
        """Return table colors based on player color (W/B)"""
        if player_color == "W":
            return (
                cls.WHITE_TABLE_BG,
                cls.WHITE_TABLE_HEADER,
                cls.WHITE_TABLE_TEXT,
                cls.WHITE_TABLE_ALT_ROW,
                cls.WHITE_TABLE_BORDER
            )
        else:
            return (
                cls.BLACK_TABLE_BG,
                cls.BLACK_TABLE_HEADER,
                cls.BLACK_TABLE_TEXT,
                cls.BLACK_TABLE_ALT_ROW,
                cls.BLACK_TABLE_BORDER
            )
    
    @classmethod
    def get_player_colors(cls, player: int):
        """Return player colors (cursor and selection background)"""
        if player == 1:
            return (cls.PLAYER1_CURSOR, cls.PLAYER1_SELECTION_BG)
        else:
            return (cls.PLAYER2_CURSOR, cls.PLAYER2_SELECTION_BG)