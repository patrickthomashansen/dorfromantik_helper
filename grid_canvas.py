import numpy as np
from itertools import product
from math import sin, cos, pi, dist
from typing import Optional, List, Tuple

from tkinter import Canvas

from tile import HexTile, TileStatus
from evaluator import PlacementEvaluator
from grid import HexGrid
from utils import Color, EdgeIndex, GridCoordinate, PixelCoordinate, is_point_inside_polygon


"""
Canvas that displays the full game board
"""
class HexGridCanvas(Canvas):
    def __init__(self, master, width: int = 1300, height: int = 1000, *args, **kwargs) -> None:
        super().__init__(master, background='white', width=width, height=height, *args, **kwargs)
        self.width  = width
        self.height = height
        self.hint_hexes = []
        self.selected_hex = None
        self.view_edges = False
        self.hex_ratio = abs(cos(self._get_vertex_angle(0))) # Ratio of a hexagon's height to its width


    def _get_vertex_angle(self, index: EdgeIndex) -> float:
        """Returns the angle (in radians) from positive x of the vertex indicated by index"""
        return pi * (7/6 - index/3)


    def _get_tile_position_bounds(self, board: HexGrid, margin: float = 0) -> Tuple[float, float, float, float]:
        """Computes the bounds of tile positions spacially"""
        left = top = float("inf")
        right = bottom = -float("inf")
        for xy in product(range(board.size), range(board.size)):
            if not board.get_tile(xy).is_empty():
                x, y = xy
                pos_x = 2*x + y
                pos_y = 1.5*y
                left = min(left, pos_x-margin)
                right = max(right, pos_x+margin)
                top = min(top, pos_y-margin)
                bottom = max(bottom, pos_y+margin)
        return left, right, top, bottom


    def _set_coordinate_transform_parameters(self, board: HexGrid) -> None:
        """Computes pixel offsets and scaling parameters needed to center the hex grid on the canvas"""
        self.size = board.size
        left, right, top, bottom = self._get_tile_position_bounds(board, margin=4)
        board_width = right - left
        board_height = bottom - top
        # Offset in either x or y direction depending on the relative shapes of the board and canvas
        if self.height/self.width > board_height/board_width:
            self.tile_radius = self.width / board_width / self.hex_ratio
            top -= (self.height*board_width/self.width - board_height) * self.hex_ratio / 2
        else:
            self.tile_radius = self.height / board_height
            left -= (self.width*board_height/self.height - board_width) / self.hex_ratio / 2
        self.pixel_offset_xy = (self.tile_radius * self.hex_ratio * left, self.tile_radius * top)


    def _get_tile_center_pixel(self, xy: GridCoordinate) -> PixelCoordinate:
        """Returns the pixel coordinate of the center of a given tile position"""
        x, y = xy
        pixel_offset_x, pixel_offset_y = self.pixel_offset_xy
        pixel_x = self.tile_radius * self.hex_ratio * (2*x + y) - pixel_offset_x
        pixel_y = self.tile_radius * (1.5*y) - pixel_offset_y
        return pixel_x, pixel_y


    def _get_tile_vertices(self, xy: GridCoordinate) -> List[PixelCoordinate]:
        """Returns the vertices of a tile"""
        pixel_x, pixel_y = self._get_tile_center_pixel(xy)
        v_x = [pixel_x+self.tile_radius*cos(self._get_vertex_angle(index)) for index in range(6)]
        v_y = [pixel_y-self.tile_radius*sin(self._get_vertex_angle(index)) for index in range(6)]
        return list(zip(v_x, v_y))


    def draw_tile(
        self,
        xy: GridCoordinate,
        fill_color: Optional[str] = None,
        border_color: Optional[str] = None,
        border_width: float = 2
    ) -> None:
        """Draws a tile on the canvas at a given position"""
        vertices = self._get_tile_vertices(xy)
        if not fill_color is None:
            self.create_polygon(vertices, fill=fill_color)
        if not border_color is None:
                self.create_line(vertices, vertices[0], fill=border_color, width=border_width)
    

    def draw_edges(
        self,
        xy: GridCoordinate,
        fill_colors: Optional[List[str]] = None,
        border_color: Optional[str] = None,
        border_width: float = 2
    ) -> None:
        """Draws a tile on the canvas at a given position"""
        center = self._get_tile_center_pixel(xy)
        vertices = self._get_tile_vertices(xy)
        if not fill_colors is None:
            for i in range(6):
                self.create_polygon([center, vertices[i], vertices[(i+1)%6]], fill=fill_colors[i])
        if not border_color is None:
                self.create_line(vertices, vertices[0], fill=border_color, width=border_width)


    def draw(self, board: HexGrid) -> None:
        """Draws the full game board on the canvas"""
        self._set_coordinate_transform_parameters(board)
        self.delete('all')
        for xy in product(range(board.size), range(board.size)):
            status = board.get_tile(xy).get_status()
            if status == TileStatus.EMPTY:
                # self.draw_tile(x, y, fill_color=None, border_color='purple')
                continue
            if self.view_edges:
                fill_colors = [edge.to_color() for edge in board.get_tile(xy).get_edges()]
                self.draw_edges(xy, fill_colors=fill_colors, border_color=Color.BLACK)
            else:
                if status == TileStatus.VALID and xy in self.hint_hexes:
                    fill_color = Color.PLUM
                else:
                    fill_color = status.to_color()
                self.draw_tile(xy, fill_color=fill_color, border_color=Color.BLACK)
        if self.selected_hex is not None:
            self.draw_tile(self.selected_hex, border_color=Color.YELLOW)
    

    def toggle_view(self) -> None:
        self.view_edges = not self.view_edges


    def get_xy_from_pix(self, pixel_xy: PixelCoordinate) -> None:
        """Returns the grid coordinates of the hex belonging to the given pixel coordinates"""
        for xy in product(range(self.size), range(self.size)):
            vertices = self._get_tile_vertices(xy)
            if is_point_inside_polygon(pixel_xy, vertices):
                return xy
        return None


    def set_selected_hex(self, xy: GridCoordinate) -> None:
        self.selected_hex = xy


    def set_hint(self, hint: List[PlacementEvaluator]):
        """Set which tiles to highlight given a hint"""
        self.hint_hexes = []
        if hint is None:
            return
        for evaluator in hint:
            self.hint_hexes.append(evaluator.xy)