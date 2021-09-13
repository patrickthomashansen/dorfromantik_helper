import numpy as np
import os
from itertools import product
import pickle


from hex_tile import HexTile
from constants import *


class HexGrid:
    """
    A class representing a grid of hexagonal tiles
    """

    def __init__(self, save_file:str=None):
        """Loads a save file or initializes a new game board"""
        if save_file is None:
            self._initialize_new_grid()
        else:
            self.load(save_file)


    @staticmethod
    def _get_neighboring_tile_xys(xy:tuple) -> list:
        """Returns a list of coordinates of all possible neighbors of a tile"""
        x, y = xy
        return [(x-1,y), (x,y-1), (x+1,y-1), (x+1,y), (x,y+1), (x-1,y+1)]


    def _get_empty_tiles(self, size:int=8) -> np.array:
        """Returns an array of empty tile objects"""
        return np.array([[HexTile() for _ in range(size)] for _ in range(size)], dtype=object)


    def _initialize_new_grid(self, size:int=8) -> None:
        """Creates an empty hex grid"""
        self.size = size
        self.tiles = self._get_empty_tiles(size)


    def _get_origin_xy(self) -> tuple:
        """Returns the coordinates of the origin tile"""
        return int(self.size/2 - 1), int(self.size/2 - 1)


    def _is_in_grid(self, xy:tuple) -> bool:
        """Checks if the given coordinates sit within the bounds of the board"""
        x, y = xy
        return x >= 0 and y >= 0 and x < self.size and y < self.size


    def _is_on_border(self, xy:tuple) -> bool:
        """Checks if the given coordinates sit on the border of the game board"""
        assert self._is_in_grid(xy)
        x, y = xy
        return x == 0 or y == 0 or x == self.size-1 or y == self.size-1


    def _is_near_border(self, xy:tuple, threshold:int=1) -> bool:
        """Checks if the given coordinates lay within some distance of the border of the game board"""
        assert self._is_in_grid(xy)
        x, y = xy
        return x <= threshold or y <= threshold or x >= self.size-1-threshold or y >= self.size-1-threshold


    def _enlarge_board(self, pad_size:int=2) -> None:
        """Enlarges the game board by padding the existing board with empty tiles"""
        new_size = self.size + 2*pad_size
        new_tiles = self._get_empty_tiles(new_size)
        x0 = y0 = pad_size
        x1 = y1 = pad_size + self.size
        new_tiles[x0:x1,y0:y1] = self.tiles
        self.tiles = new_tiles
        self.size = new_size


    def _enlarge_and_relocate(self, xy:tuple, pad_size:int=2) -> tuple:
        """Enlarges the game board and returns the new location of the given coordinates"""
        self._enlarge_board(pad_size)
        x, y = xy
        return x+pad_size, y+pad_size


    def _get_opposite_edge_location(self, xy:tuple, index:int) -> tuple:
        """Returns the tile location and edge index of the opposing edge"""
        xy_ = self._get_neighboring_tile_xys(xy)[index]
        index_ = (index + 3) % 6
        return xy_, index_


    def save(self, file_name:str) -> None:
        """Saves a game board to a save file"""
        pickle.dump(self.tiles, open(file_name, "wb"))


    def load(self, file_name:str) -> None:
        """Loads a game board from a save file"""
        self.tiles = pickle.load(open(file_name, "rb"))
        self.size = len(self.tiles)


    def get_tile(self, xy:tuple) -> HexTile:
        assert self._is_in_grid(xy)
        return self.tiles[xy]


    def get_connecting_edges(self, xy:tuple) -> HexTile:
        """Returns a tile representing all opposite edges given a location"""
        connections = []
        for index in range(6):
            xy_, index_ = self._get_opposite_edge_location(xy, index)
            if self._is_in_grid(xy_) and not self.get_tile(xy_).is_empty():
                connections.append(self.get_tile(xy_).get_edge(index_))
            else:
                connections.append(TileEdge.EMPTY)
        return HexTile(connections)


    def get_locations_with_status(self, status:int) -> list:
        """Returns a list of all tile locations with a given status"""
        result = []
        for xy in product(range(self.size), range(self.size)):
            if self.get_tile(xy).get_status() == status:
                result.append(xy)
        return result


    def place_tile(self, xy:tuple, tile:HexTile) -> None:
        """Places a tile at a given location"""
        assert self._is_in_grid(xy)
        if self._is_near_border(xy, threshold=1):
            xy = self._enlarge_and_relocate(xy)
        self.get_tile(xy).set_edges(tile.edges)
        self.get_tile(xy).set_status(tile.status)


    def remove_tile(self, xy:tuple) -> None:
        """Attempts to remove a tile from a given location"""
        assert self._is_in_grid(xy)
        self.get_tile(xy).clear_edges()
        self.get_tile(xy).clear_status()