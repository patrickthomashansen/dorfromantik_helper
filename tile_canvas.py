from tkinter import Canvas
from math import sin, cos, pi
from typing import Optional, List, Tuple

from edge import Edge
from tile import HexTile

from utils import Color, is_point_inside_polygon, PixelCoordinate, EdgeIndex


class HexTileCanvas(Canvas):
    """Class to draw the preview of the hex tile to be placed onto the Dorfromantik board"""

    def __init__(self, master, size: int, *args, **kwargs) -> None:
        super().__init__(master, background='white', width=size, height=size, *args, **kwargs)
        self.size = size
        self.selected_slice = None
        self.tile = HexTile()
        self.tile.set_edges(HexTile.ORIGIN_EDGES)
        self.neighbors = HexTile()
        self.select_slice(0)
        self.draw()


    def _get_vertex_angle(self, index: EdgeIndex) -> float:
        """Returns the angle (in radians) from positive x of the vertex indicated by index"""
        return pi * (7/6 - index/3)


    def _get_slice_vertices(self, index: EdgeIndex, scale: float = 1) -> List[PixelCoordinate]:
        """Returns the vertices of a triangular slice of a hexagon"""
        r = scale * self.size / 3 # radius
        offset = self.size / 2
        angle1 = self._get_vertex_angle(index)
        angle2 = self._get_vertex_angle(index+1)
        return [(offset, offset),
                (offset+r*cos(angle1), offset-r*sin(angle1)),
                (offset+r*cos(angle2), offset-r*sin(angle2))]


    def _get_slice_index_from_xy(self, xy: PixelCoordinate) -> Optional[EdgeIndex]:
        """Returns the index of the slice containing a point on the canvas, if any"""
        for index in range(6):
            vertices = self._get_slice_vertices(index)
            if is_point_inside_polygon(xy, vertices):
                return index
        return None
    

    def _draw_slice(
        self,
        index: EdgeIndex,
        fill_color: Optional[str] = None,
        border_color: Optional[str] = None,
        border_width: float = 2
    ) -> None:
        """Draw a triangular slice of a hexagon on the canvas"""
        vertices = self._get_slice_vertices(index)
        if fill_color != None:
            self.create_polygon(vertices, fill=fill_color)
        if border_color != None:
            self.create_line(vertices, vertices[0], fill=border_color, width=border_width)


    def _draw_neighbor_edge(
        self,
        index: EdgeIndex,
        fill_color: Optional[str] = None,
        border_color: Optional[str] = None,
        border_width: float = 2
    ) -> None:
        """Draw an indicator for a neighboring edge of the currently selected hex"""
        _, a, b = self._get_slice_vertices(index, scale=1.1)
        _, d, c = self._get_slice_vertices(index, scale=1.2)
        if fill_color != None:
            self.create_polygon(a, b, c, d, fill=fill_color)
        if border_color != None:
            self.create_line(a, b, c, d, a, fill=border_color, width=border_width)


    def draw(self) -> None:
        """Draws the tile and its neighboring edges on the canvas"""
        self.delete('all')
        for index, edge in enumerate(self.tile.get_edges()):
            self._draw_slice(index, fill_color=edge.to_color(), border_color=Color.BLACK)
        for index, edge in enumerate(self.neighbors.get_edges()):
            if edge != Edge.EMPTY:
                self._draw_neighbor_edge(index, fill_color=edge.to_color(), border_color=Color.BLACK)
        if self.selected_slice == -1:
            for index in range(6):
                self._draw_slice(index, border_color=Color.YELLOW)
        else:
            self._draw_slice(self.selected_slice, border_color=Color.YELLOW)


    def get_tile(self) -> HexTile:
        return self.tile


    def select_slice(self, index: EdgeIndex) -> None:
        self.selected_slice = index


    def select_next(self) -> None:
        self.selected_slice = (self.selected_slice + 1)%6


    def select_prev(self) -> None:
        self.selected_slice = (self.selected_slice - 1)%6


    def select_all(self) -> None:
        self.selected_slice = -1
        self.draw()


    def set_selected_edge(self, edge: Edge, auto_advance = True) -> None:
        """Sets the currently selected edge (or all edges)"""
        if self.selected_slice == -1:
            self.tile.set_edges(6*[edge])
        else:
            self.tile.set_edge(edge, self.selected_slice)
            if auto_advance:
                self.select_next()
        self.draw()


    def set_neighbors(self, neighbors: HexTile) -> None:
        self.neighbors = neighbors
        self.draw()


    def rotate(self, clockwise = True) -> None:
        """Rotates the edges on the tile, as well as the selected tile"""
        self.tile.rotate(clockwise)
        if not self.selected_slice == -1:
            self.select_next() if clockwise else self.select_prev()
        self.draw()
        

    def on_click(self, event) -> None:
        """Checks if a slice has been selected"""
        index = self._get_slice_index_from_xy((event.x, event.y))
        if index == None:
            return
        # print("Selected slice: ", index)
        self.select_slice(index)
        self.draw()
