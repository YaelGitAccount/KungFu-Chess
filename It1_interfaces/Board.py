from dataclasses import dataclass, field
import copy
import cv2
import numpy as np
from img import Img
from typing import Tuple
from copy import deepcopy
from MovesLog import MovesLog
from ColorScheme import Colors


@dataclass
class Board:
    cell_H_pix: int
    cell_W_pix: int
    cell_H_m: int
    cell_W_m: int
    W_cells: int
    H_cells: int
    img: Img
    left_sidebar_width: int = field(default=350)
    right_sidebar_width: int = field(default=350)
    white_log: MovesLog = field(default=None)
    black_log: MovesLog = field(default=None)

    def __post_init__(self):
        self.board_width_pix = self.W_cells * self.cell_W_pix
        self.board_height_pix = self.H_cells * self.cell_H_pix

        self.bottom_margin = 30  # Space for column labels
        self.top_margin = 30     # Space for column labels
        self._margin = 20        # Space for row numbers

        # Total dimensions
        self.total_height_pix = self.top_margin + self.board_height_pix + self.bottom_margin
        self.total_width_pix = self.left_sidebar_width + self.board_width_pix + self.right_sidebar_width + self._margin * 2
        
        self._add_sidebars_to_image()
        self._draw_board_labels()
    
    def get_board_offset(self) -> Tuple[int, int]:
        """Return board start position within the image (x,y)"""
        return self.left_sidebar_width + self._margin, self.top_margin

    def _add_sidebars_to_image(self):
        if self.img.img is None:
            self._create_default_board_with_sidebars()
            return

        current_img = self.img.img
        if current_img.shape[-1] == 4:
            current_img = cv2.cvtColor(current_img, cv2.COLOR_BGRA2BGR)

        # Resize to board dimensions
        current_img = cv2.resize(current_img, (self.board_width_pix, self.board_height_pix))

        # Create extended image with sidebars
        extended_img = np.zeros((self.total_height_pix, self.total_width_pix, 3), dtype=np.uint8)
        extended_img[:, :] = Colors.BACKGROUND_MAIN

        start_x = self.left_sidebar_width + self._margin
        start_y = self.top_margin

        extended_img[start_y:start_y + self.board_height_pix, start_x:start_x + self.board_width_pix] = current_img

        # Left separator line
        cv2.line(extended_img,
                 (start_x - 1, 0),
                 (start_x - 1, self.total_height_pix),
                 Colors.BACKGROUND_SEPARATOR, Colors.SEPARATOR_THICKNESS)

        # Right separator line
        cv2.line(extended_img,
                 (start_x + self.board_width_pix - 1, 0),
                 (start_x + self.board_width_pix - 1, self.total_height_pix),
                 Colors.BACKGROUND_SEPARATOR, Colors.SEPARATOR_THICKNESS)

        self.img.img = extended_img

    def _create_default_board_with_sidebars(self):
        total_img = np.zeros((self.total_height_pix, self.total_width_pix, 3), dtype=np.uint8)

        # Classic chess board colors
        light_color = Colors.BOARD_LIGHT
        dark_color = Colors.BOARD_DARK

        # Draw board squares
        for row in range(self.H_cells):
            for col in range(self.W_cells):
                x1 = self.left_sidebar_width + col * self.cell_W_pix + self._margin
                y1 = row * self.cell_H_pix + self.top_margin
                x2 = x1 + self.cell_W_pix
                y2 = y1 + self.cell_H_pix
                color = light_color if (row + col) % 2 == 0 else dark_color
                cv2.rectangle(total_img, (x1, y1), (x2 - 1, y2 - 1), color, -1)

        # Fill sidebars
        total_img[:, :self.left_sidebar_width] = Colors.BACKGROUND_MAIN
        right_start = self.left_sidebar_width + self._margin + self.board_width_pix
        total_img[:, right_start:] = Colors.BACKGROUND_MAIN

        # Separator lines
        x_start = self.left_sidebar_width + self._margin
        cv2.line(total_img,
                 (x_start - 1, 0),
                 (x_start - 1, self.total_height_pix),
                 Colors.BACKGROUND_SEPARATOR, Colors.SEPARATOR_THICKNESS)

        cv2.line(total_img,
                 (x_start + self.board_width_pix - 1, 0),
                 (x_start + self.board_width_pix - 1, self.total_height_pix),
                 Colors.BACKGROUND_SEPARATOR, Colors.SEPARATOR_THICKNESS)

        self.img.img = total_img

    def clone(self) -> "Board":
        cloned = deepcopy(self)
        if not hasattr(cloned, 'board_width_pix'):
            cloned.__post_init__()
        return cloned

    def cell_to_pixels(self, row: int, col: int) -> Tuple[int, int]:
        x = self.left_sidebar_width + col * self.cell_W_pix + self._margin
        y = row * self.cell_H_pix + self.top_margin
        return (x, y)

    def pixels_to_cell(self, x: int, y: int) -> Tuple[int, int]:
        x -= self.left_sidebar_width
        if x < 0 or x >= self.board_width_pix:
            return (-1, -1)
        col = min(x // self.cell_W_pix, self.W_cells - 1)
        row = min(y // self.cell_H_pix, self.H_cells - 1)
        return (row, col)

    def is_in_board_area(self, x: int, y: int) -> bool:
        return self.left_sidebar_width <= x < self.left_sidebar_width + self.board_width_pix and \
               0 <= y < self.board_height_pix

    def get_left_sidebar_area(self) -> Tuple[int, int, int, int]:
        return (0, 0, self.left_sidebar_width, self.total_height_pix)

    def get_right_sidebar_area(self) -> Tuple[int, int, int, int]:
        x = self.left_sidebar_width + self.board_width_pix + self._margin * 2
        return (x, 0, self.right_sidebar_width, self.total_height_pix)

    @property
    def dimensions(self) -> Tuple[int, int]:
        return (self.H_cells, self.W_cells)

    @property
    def total_dimensions(self) -> Tuple[int, int]:
        return (self.total_height_pix, self.total_width_pix)

    def _draw_board_labels(self):
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        color = Colors.LABEL_TEXT_COLOR

        # Column letters (A-H)
        for col in range(self.W_cells):
            letter = chr(ord('A') + col)
            x = self.left_sidebar_width + col * self.cell_W_pix + self.cell_W_pix // 2 + self._margin
            # Top
            cv2.putText(self.img.img, letter, (x - 5, 20), font, font_scale, color, thickness, cv2.LINE_AA)
            # Bottom
            y_bottom = self.top_margin + self.board_height_pix + 20
            cv2.putText(self.img.img, letter, (x - 5, y_bottom), font, font_scale, color, thickness, cv2.LINE_AA)

        # Row numbers (1-8)
        for row in range(self.H_cells):
            number = str(self.H_cells - row)
            y = self.top_margin + row * self.cell_H_pix + self.cell_H_pix // 2 + 5
            # Left
            cv2.putText(self.img.img, number, (self.left_sidebar_width - 20 + self._margin, y), font, font_scale, color, thickness, cv2.LINE_AA)
            # Right
            x_right = self.left_sidebar_width + self.board_width_pix + 10 + self._margin 
            cv2.putText(self.img.img, number, (x_right, y), font, font_scale, color, thickness, cv2.LINE_AA)