import numpy as np
from itertools import product

from tkinter import Canvas
from constants import *


"""
Canvas that displays the full game board
"""
class DorfBoardCanvas(Canvas):
    def __init__(self, master, board, tile_canvas, width=1300, height=1000, *args, **kwargs):
        super().__init__(master, background='white', width=width, height=height, *args, **kwargs)
        
        self.board = board
        self.tile_canvas = tile_canvas
        self.height = height
        self.width  = width

        self.hint_hexes = []
        self.selected_hex = None
        
        self.set_coordinate_transform_parameters()
        self.set_hex_centers()


    def set_coordinate_transform_parameters(self):
        """
        Computes and stores pixel offsets and scaling parameters needed to center the hex grid on the canvas
        Offsets the coordinates if the displayed board is wider or taller than the canvas allows
        """
        # Compute the (x,y) locations in pre-transformed pixel space of all non-empty board tiles
        all_loc_x = []
        all_loc_y = []
        for x in range(self.board.size):
            for y in range(self.board.size):
                if not self.board.get_tile((x,y)).is_empty():
                    loc_x = 1 + 2*x + y
                    loc_y = 1 + 1.5*y
                    all_loc_x.append(loc_x)
                    all_loc_y.append(loc_y)
        # Give pixel offsets that attempt to center the board in the frame
        margin = 4
        loc_x_min = min(all_loc_x) - margin
        loc_y_min = min(all_loc_y) - margin
        loc_x_max = max(all_loc_x) + margin
        loc_y_max = max(all_loc_y) + margin
        loc_x_diff = loc_x_max - loc_x_min
        loc_y_diff = loc_y_max - loc_y_min
        # Compute the scale for a hex tile
        # Add offset if board is too wide or too tall for canvas
        if self.height/loc_y_diff > self.width/loc_x_diff:
            hex_edge_len = 2/3**0.5 * self.width / loc_x_diff
            loc_y_min -= (3**0.5/2 * loc_x_diff/self.width*self.height - loc_y_diff) / 2
        else:
            hex_edge_len = self.height / loc_y_diff
            loc_x_min -= (2/3**0.5 * loc_y_diff/self.height*self.width - loc_x_diff) / 2
        # Store scaling and offset parameters
        self.y_scale = hex_edge_len
        self.x_scale = 3**0.5 / 2 * hex_edge_len
        self.pix_x_offset = self.x_scale * loc_x_min
        self.pix_y_offset = self.y_scale * loc_y_min
        return


    def get_hex_center_pix(self, x, y):
        """
        Returns the (x,y) coordinates in pixel space of a given hex position
        """
        pix_x = self.x_scale * (1 + 2*x + y) - self.pix_x_offset
        pix_y = self.y_scale * (1 + 1.5*y) - self.pix_y_offset
        return pix_x, pix_y


    def set_hex_centers(self):
        """
        Computes and stores the (x,y) coordinates in pixel space of all hex positions
        """
        self.centers = np.zeros((self.board.size, self.board.size, 2))
        for x in range(self.board.size):
            for y in range(self.board.size):
                self.centers[x,y] = self.get_hex_center_pix(x, y)
        return


    def draw_hexagon(self, x, y, border_color=TileOutlineColors.NORMAL, border_width=2, fill_color='blue'):
        """
        Draws a hexagon on the canvas given a hex position
        """
        pix_x, pix_y = self.get_hex_center_pix(x, y)
        # Compute the coordinates of hexagon vertices
        y_size = self.y_scale
        x_size = self.x_scale
        vertices = [(pix_x-x_size, pix_y+y_size/2),
                    (pix_x-x_size, pix_y-y_size/2),
                    (pix_x       , pix_y-y_size  ),
                    (pix_x+x_size, pix_y-y_size/2),
                    (pix_x+x_size, pix_y+y_size/2),
                    (pix_x       , pix_y+y_size  )]
        # Draw hexagon
        if fill_color != None:
            self.create_polygon(vertices[0],
                                vertices[1],
                                vertices[2],
                                vertices[3],
                                vertices[4],
                                vertices[5],
                                fill=fill_color)
        # Draw outline
        if border_color != None:
            for i in range(len(vertices)):
                self.create_line(vertices[i], vertices[(i+1)%len(vertices)], fill=border_color, width=border_width)


    def draw_board(self):
        """
        Draws the full game board on the canvas
        """
        self.set_coordinate_transform_parameters()
        self.set_hex_centers()
        self.delete('all')
        for xy in product(range(self.board.size), range(self.board.size)):
            status = self.board.get_tile(xy).get_status()
            if status == TileStatus.EMPTY:
                # self.draw_hexagon(x, y, fill_color=None, border_color='purple')
                continue
            elif status == TileStatus.VALID and xy in self.hint_hexes:
                fill_color = TileStatusColors.HINT
            else:
                fill_color = get_color_from_status(status)
            x, y = xy
            self.draw_hexagon(x, y, fill_color=fill_color)


    @staticmethod
    def euclidian_distance(x1, y1, x2, y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5


    def get_xy_from_pix(self, pix_x, pix_y):
        """
        Returns the (x,y) position of the hex belonging to the given pixel coordinates
        Approximates the hexagon as a circle with the inner radius of the hexagon
        Gives a 5 percent margin of error to avoid confusing between neighboring hexes
        """
        for x in range(self.board.size):
            for y in range(self.board.size):
                center = self.centers[x,y]
                if self.euclidian_distance(pix_x, pix_y, center[0], center[1]) < self.x_scale * 0.95:
                    return x, y
        return None


    def on_click(self, event):
        """
        Controls behavior of the canvas on a left mouse click
        Used for highlighting a selected hex
        """
        # Remove highlight from previously selected hex tile
        if self.selected_hex:
            x, y = self.selected_hex
            self.draw_hexagon(x, y, border_color=TileOutlineColors.NORMAL, fill_color=None)
            self.selected_hex = None
        # Get location of newly selected hex tile (if any)
        xy = self.get_xy_from_pix(event.x, event.y)
        if xy == None:
            return
        # Highlight newly selected tile if not empty
        x, y = xy
        tile = self.board.get_tile(xy)
        if not tile.is_empty() or tile.is_valid():
            self.selected_hex = xy
            self.draw_hexagon(x, y, border_color=TileOutlineColors.SELECTED, fill_color=None)
        # Set the connecting edges in the slice canvas
        if tile.is_valid():
            connections = self.board.get_connecting_edges(xy)
        else:
            connections = None    
        self.tile_canvas.set_neighbors(connections)
        self.tile_canvas.draw()


    def set_hint(self, hints):
        """
        Set which tiles to highlight given a hint
        """
        self.hint_hexes = []
        if hints is None:
            return
        for (xy, _), _ in hints:
            self.hint_hexes.append(xy)