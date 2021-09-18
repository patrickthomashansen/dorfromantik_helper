import numpy as np
from itertools import product
from math import sin, cos, pi

from tkinter import Canvas

from tile import HexTile, TileStatus

from constants import *


def euclidian_distance(xy, xy_):
    x1, y1 = xy
    x2, y2 = xy_
    return ((x2-x1)**2 + (y2-y1)**2)**0.5


"""
Canvas that displays the full game board
"""
class DorfBoardCanvas(Canvas):
    def __init__(self, master, board,  width=1300, height=1000, *args, **kwargs):
        super().__init__(master, background='white', width=width, height=height, *args, **kwargs)
        self.width  = width
        self.height = height
        self.hint_hexes = []
        self.selected_hex = None

        self.hex_ratio = abs(cos(self._get_vertex_angle(0))) # Ratio of a hexagon's height to its width
        self._set_coordinate_transform_parameters(board)
        self._set_tile_centers(board.size)


    def _get_vertex_angle(self, index:int) -> float:
        """Returns the angle (in radians) from positive x of the vertex indicated by index"""
        return pi * (7/6 - index/3)


    def _get_tile_position_bounds(self, board, margin:float=0) -> tuple:
        """Computes the bounds of tile positions spacially"""
        left = top = float("inf")
        right = bottom = 0
        for xy in product(range(board.size), range(board.size)):
            if not board.get_tile(xy).is_empty():
                x, y = xy
                pos_x = 1 + 2*x + y
                pos_y = 1 + 1.5*y
                left = min(left, pos_x-margin)
                right = max(right, pos_x+margin)
                top = min(top, pos_y-margin)
                bottom = max(bottom, pos_y+margin)
        return left, right, top, bottom


    def _set_coordinate_transform_parameters(self, board) -> None:
        """Computes and stores pixel offsets and scaling parameters needed to center the hex grid on the canvas"""
        left, right, top, bottom = self._get_tile_position_bounds(board, margin=4)
        board_width = right - left
        board_height = bottom - top
        # Offsets in either x or y direction depending on the relative shapes of the board and the canvas
        if self.height/self.width > board_height/board_width:
            self.tile_radius = self.width / board_width / self.hex_ratio
            top -= (self.height*board_width/self.width - board_height) * self.hex_ratio / 2
        else:
            self.tile_radius = self.height / board_height
            left -= (self.width*board_height/self.height - board_width) / self.hex_ratio / 2
        self.pixel_offset_xy = (self.tile_radius * left, self.tile_radius * self.hex_ratio * top)


    def _get_tile_center_pixel(self, xy:tuple) -> tuple:
        """Returns the pixel coordinate of the center of a given tile position"""
        x, y = xy
        pixel_offset_x, pixel_offset_y = self.pixel_offset_xy
        pixel_x = self.tile_radius * self.hex_ratio * (1 + 2*x + y) - pixel_offset_x
        pixel_y = self.tile_radius * (1 + 1.5*y) - pixel_offset_y
        return pixel_x, pixel_y


    def _set_tile_centers(self, size) -> None:
        """Computes and stores the pixel coordinates of all tiles"""
        self.centers = np.zeros((size, size, 2))
        for xy in product(range(size), range(size)):
            self.centers[xy] = self._get_tile_center_pixel(xy)


    def _get_tile_vertices(self, xy:tuple) -> list:
        """Returns the vertices of a tile"""
        pixel_x, pixel_y = self._get_tile_center_pixel(xy)
        v_x = [pixel_x+self.tile_radius*cos(self._get_vertex_angle(index)) for index in range(6)]
        v_y = [pixel_y-self.tile_radius*sin(self._get_vertex_angle(index)) for index in range(6)]
        return list(zip(v_x, v_y))


    def draw_tile(self, xy, border_color=Color.BLACK, border_width=2, fill_color='blue'):
        """Draws a tile on the canvas at a given position"""
        vertices = self._get_tile_vertices(xy)
        if fill_color != None:
            self.create_polygon(vertices, fill=fill_color)
        if border_color != None:
                self.create_line(vertices, vertices[0], fill=border_color, width=border_width)


    def draw(self, board):
        """Draws the full game board on the canvas"""
        self._set_coordinate_transform_parameters(board)
        self._set_tile_centers(board.size)
        self.delete('all')
        for xy in product(range(board.size), range(board.size)):
            status = board.get_tile(xy).get_status()
            if status == TileStatus.EMPTY:
                # self.draw_tile(x, y, fill_color=None, border_color='purple')
                continue
            elif status == TileStatus.VALID and xy in self.hint_hexes:
                fill_color = Color.PLUM
            else:
                fill_color = status.to_color()
            self.draw_tile(xy, fill_color=fill_color)
        if self.selected_hex is not None:
            self.draw_tile(self.selected_hex, border_color=Color.YELLOW, fill_color=None)


    def get_xy_from_pix(self, pixel_xy):
        """
        Returns the (x,y) position of the hex belonging to the given pixel coordinates
        Approximates the hexagon as a circle with the inner radius of the hexagon
        Gives a 5 percent margin of error to avoid confusing between neighboring hexes
        """
        for x, row in enumerate(self.centers):
            for y, center in enumerate(row):
                if euclidian_distance(pixel_xy, center) < self.tile_radius * 0.95:
                    return x, y
        return None


    def set_selected_hex(self, xy:tuple) -> None:
        self.selected_hex = xy


    def set_hint(self, hints):
        """Set which tiles to highlight given a hint"""
        self.hint_hexes = []
        if hints is None:
            return
        for evaluator in hints:
            self.hint_hexes.append(evaluator.xy)