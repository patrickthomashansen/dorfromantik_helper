import numpy as np
import os


from hex_tile import HexTile
from constants import *


class HexGrid:
    """
    A class representing a grid of hexagonal tiles
    """


    def __init__(self, save_file:str=None):
        """Loads a save file or initializes a new game board"""
        if save_file is None:
            self._initialize_new_board()
        else:
            self.load_board(save_file)


    def _initialize_new_board(self) -> None:
        """Creates an empty hex grid"""
        # Create a board with empty tiles
        self.size = 8
        self.tiles = np.empty([size, size], dtype=object)


    def save_board(self, save_file:str) -> None:
        """Saves a game board to a npz save file"""
        pass
        np.savez(save_file, edges=self.edges, status=self.status)


    def load_board(self, save_file:str) -> None:
        """Loads a game board from a npz save file"""
        pass
        assert os.path.exists(save_file)
        data = np.load(save_file)
        self.edges = data['edges']
        self.status = data['status']
        self.size = len(self.edges)


    def _get_origin_xy(self) -> tuple:
        """Returns the (x,y) coordinates of the origin tile"""
        return int(self.size/2 - 1), int(self.size/2 - 1)


    def _is_in_grid(self, xy:tuple) -> bool:
        """Checks if the given coordinates lay within the bounds of the board"""
        x, y = xy
        return x >= 0 and y >= 0 and x < self.size and y < self.size


    def _is_on_border(self, xy:tuple) -> bool:
        """Checks if the given coordinates lay on the border of the game board"""
        x, y = xy
        return x == 0 or y == 0 or x == self.size-1 or y == self.size-1


    def _is_near_border(self, xy:tuple, distance_threshold:int=1) -> bool:
        """Checks if the given coordinates lay within some distance of the border of the game board"""
        if not self._is_in_grid(xy):
            return DorfBoardResult.ERROR
        x, y = xy
        k = distance_threshold
        return x <= k or y <= k or x >= self.size-1-k or y >= self.size-1-k


    def _enlarge_board(self, pad_size:int=2) -> None:
        """Enlarges the game board by padding the existing board with empty tiles"""
        new_size = self.size + 2*pad_size
        new_edges = self._get_empty_edges(new_size)
        new_status = self._get_empty_status(new_size)
        x0 = y0 = pad_size
        x1 = y1 = pad_size + self.size
        new_edges[x0:x1,y0:y1] = self.edges
        new_status[x0:x1,y0:y1] = self.status
        self.edges = new_edges
        self.status = new_status
        self.size = new_size


    def _enlarge_and_relocate(self, xy:tuple, pad_size:int=2) -> tuple:
        """Enlarges the game board and returns the new location of the given coordinates"""
        self._enlarge_board(pad_size)
        x, y = xy
        return x+pad_size, y+pad_size


    def _get_edge(self, xy:tuple, edge_index:int) -> int:
        """Returns the edge at the given location"""
        x, y = xy
        return self.tiles[x,y].edges[edge_index]


    @staticmethod
    def _get_neighboring_tile_xys(xy:tuple) -> list:
        """Returns a list of coordinates of all possible neighbors of a tile"""
        x, y = xy
        return [(x-1,y), (x,y-1), (x+1,y-1), (x+1,y), (x,y+1), (x-1,y+1)]


    def _get_opposite_edge_location(self, xy:tuple, edge_index:int) -> tuple:
        """Returns the tile location and edge index of the opposing edge"""
        x, y = xy
        if edge_index == 0:
            return (x-1, y), 3
        elif edge_index == 1:
            return (x, y-1), 4
        elif edge_index == 2:
            return (x+1, y-1), 5
        elif edge_index == 3:
            return (x+1, y), 0
        elif edge_index == 4:
            return (x, y+1), 1
        elif edge_index == 5:
            return (x-1, y+1), 2


    def is_empty_tile(self, xy:tuple) -> bool:
        """Checks if the given tile location is empty"""
        return self.tiles[xy].is_empty()


    def get_connecting_edges(self, xy:tuple) -> HexTile:
        """Returns a tile representing all opposite edges given a location"""
        connections = []
        for edge_index in range(6):
            xy_, opposite_edge_index = self._get_opposite_edge_location(xy, edge_index)
            if self._is_in_grid(xy_) and not self.is_empty_tile(xy_):
                connections.append(self._get_edge(xy_, opposite_edge_index))
            else:
                connections.append(TileEdge.EMPTY)
        return HexTile(connections)


    def update_tile_status(self, xy:tuple) -> None:
        """Updates the status of a tile location"""
        self.tile[xy].set_status(self.get_status_from_connections(xy))


    def place_tile(self, xy:tuple, tile:HexTile) -> int:
        """Attempts to place a tile at a given location"""
        if not self._is_in_grid(xy) or [xy, tile] not in self.get_legal_placements(tile):
            print("Illegal placement: {}: ".format(xy), tile)
            return DorfBoardResult.ERROR
        if self._is_near_border(xy, distance_threshold=1):
            xy = self._enlarge_and_relocate(xy)
        self.edges[xy] = tile.edges
        self.status[xy] = self.get_status_from_connections(xy)
        for xy_ in self._get_neighboring_tile_xys(xy):
            self.update_tile_status(xy_)
        return DorfBoardResult.OK


    def remove_tile(self, xy:tuple) -> int:
        """Attempts to remove a tile from a given location"""
        if not self._is_in_grid(xy) or self.is_empty_tile(xy):
            print("Illegal removal: {}: ".format(xy))
            return DorfBoardResult.ERROR
        self.edges[xy] = 6 * [TileEdge.EMPTY]
        self.status[xy] = self.get_status_from_connections(xy)
        for xy_ in self._get_neighboring_tile_xys(xy):
            self.update_tile_status(xy_)
        return DorfBoardResult.OK


    def get_locations_with_status(self, status:int) -> list:
        """Returns a list of all valid tile locations"""
        return zip(*np.where(self.status==status))