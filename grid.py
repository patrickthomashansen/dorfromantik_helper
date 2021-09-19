from enum import Flag, auto
from typing import Optional, Tuple, List
import numpy as np
from itertools import product
import pickle


from edge import Edge, Connection
from tile import HexTile, TileStatus
from evaluator import PlacementEvaluator
from utils import GridCoordinate, EdgeIndex


class HexGridResultFlag(Flag):
    OK = auto()
    ILLEGAL = auto()
    ERROR = auto()


class HexGrid:
    """
    A class representing a grid of hexagonal tiles
    """

    def __init__(self, save_file: Optional[str] = None) -> None:
        """Loads a save file or initializes a new game board"""
        if save_file is None:
            self._initialize_new_grid()
        else:
            self.load(save_file)


    @staticmethod
    def _get_neighboring_tile_xys(xy: GridCoordinate) -> List[GridCoordinate]:
        """Returns a list of coordinates of all possible neighbors of a tile"""
        x, y = xy
        return [(x-1,y), (x,y-1), (x+1,y-1), (x+1,y), (x,y+1), (x-1,y+1)]


    def _get_neighbor_tiles(self, xy: GridCoordinate) -> List[HexTile]:
        """Returns a list of tiles that surround the given loaction"""
        return [self.get_tile(xy_) for xy_ in self._get_neighboring_tile_xys(xy)]


    def _get_empty_tiles(self, size: int = 8) -> np.ndarray:
        """Returns an array of empty tile objects"""
        return np.array([[HexTile() for _ in range(size)] for _ in range(size)], dtype=object)


    def _initialize_new_grid(self, size: int = 8) -> None:
        """Creates a game board with only the origin tile"""
        self.size = size
        self.tiles = self._get_empty_tiles(size)
        xy = self._get_origin_xy()
        origin_tile = self.get_tile(xy)
        origin_tile.set_edges(HexTile.ORIGIN_EDGES)
        self.update_tile_status(xy)
        self.update_neighbors_status(xy)


    def _get_origin_xy(self) -> GridCoordinate:
        """Returns the coordinates of the origin tile"""
        return int(self.size/2 - 1), int(self.size/2 - 1)


    def _is_in_grid(self, xy: GridCoordinate) -> bool:
        """Checks if the given coordinates sit within the bounds of the board"""
        x, y = xy
        return x >= 0 and y >= 0 and x < self.size and y < self.size


    def _is_on_border(self, xy: GridCoordinate) -> bool:
        """Checks if the given coordinates sit on the border of the game board"""
        assert self._is_in_grid(xy)
        x, y = xy
        return x == 0 or y == 0 or x == self.size-1 or y == self.size-1


    def _is_near_border(self, xy: GridCoordinate, threshold: int = 1) -> bool:
        """Checks if the given coordinates lay within some distance of the border of the game board"""
        assert self._is_in_grid(xy)
        x, y = xy
        return x <= threshold or y <= threshold or x >= self.size-1-threshold or y >= self.size-1-threshold


    def _enlarge_board(self, pad_size: int = 2) -> None:
        """Enlarges the game board by padding the existing board with empty tiles"""
        new_size = self.size + 2*pad_size
        new_tiles = self._get_empty_tiles(new_size)
        x0 = y0 = pad_size
        x1 = y1 = pad_size + self.size
        new_tiles[x0:x1,y0:y1] = self.tiles
        self.tiles = new_tiles
        self.size = new_size


    def _enlarge_and_relocate(self, xy: GridCoordinate, pad_size: int = 2) -> GridCoordinate:
        """Enlarges the game board and returns the new location of the given coordinates"""
        self._enlarge_board(pad_size)
        x, y = xy
        return x+pad_size, y+pad_size


    def _get_opposite_edge_location(self, xy: GridCoordinate, index: EdgeIndex) -> Tuple[GridCoordinate, EdgeIndex]:
        """Returns the tile location and edge index of the opposing edge"""
        xy_ = self._get_neighboring_tile_xys(xy)[index]
        index_ = (index + 3) % 6
        return xy_, index_


    def save(self, file_name: str) -> None:
        """Saves a game board to a save file"""
        pickle.dump(self.tiles, open(file_name, "wb"))


    def load(self, file_name: str) -> None:
        """Loads a game board from a save file"""
        self.tiles = pickle.load(open(file_name, "rb"))
        self.size = len(self.tiles)


    def get_tile(self, xy: GridCoordinate) -> HexTile:
        assert self._is_in_grid(xy)
        return self.tiles[xy]


    def get_connecting_edges(self, xy: GridCoordinate) -> HexTile:
        """Returns a tile representing all opposite edges given a location"""
        connections = []
        for index in range(6):
            xy_, index_ = self._get_opposite_edge_location(xy, index)
            if self._is_in_grid(xy_) and not self.get_tile(xy_).is_empty():
                connections.append(self.get_tile(xy_).get_edge(index_))
            else:
                connections.append(Edge.EMPTY)
        return HexTile(connections)


    def get_locations_with_status(self, status: TileStatus) -> List[GridCoordinate]:
        """Returns a list of all tile locations with a given status"""
        result = []
        for xy in product(range(self.size), range(self.size)):
            if self.get_tile(xy).get_status() == status:
                result.append(xy)
        return result


    def is_legal_placement(self, xy: GridCoordinate, tile: HexTile) -> bool:
        """Checks if the given tile placement is legal"""
        for index in range(6):
            edge = tile.get_edge(index)
            xy_, index_ = self._get_opposite_edge_location(xy, index)
            if not self._is_in_grid(xy_):
                continue # Connection with a neighbor outside the board is legal
            edge_ = self.get_tile(xy_).get_edge(index_)
            if not Connection(edge, edge_).is_legal():
                return False
        return True


    def get_legal_placements(self, tile: HexTile) -> List[Tuple[GridCoordinate, HexTile]]:
        """Returns a list of all legal placements of a tile"""
        rotations = tile.get_all_rotations()
        valid_locations = self.get_locations_with_status(TileStatus.VALID)
        legal_placements = []
        for xy in valid_locations:
            for rotation in rotations:
                if self.is_legal_placement(xy, rotation):
                    legal_placements.append((xy, rotation))
        return legal_placements


    def update_tile_status(self, xy: GridCoordinate) -> None:
        """Updates the status of a tile"""
        neighborTiles = self._get_neighbor_tiles(xy)
        self.get_tile(xy).update_status(neighborTiles)


    def update_neighbors_status(self, xy: GridCoordinate) -> None:
        """Updates the status of all neighbors to a tile"""
        for xy_ in self._get_neighboring_tile_xys(xy):
            self.update_tile_status(xy_)


    def place_tile(self, xy: GridCoordinate, tile: HexTile) -> HexGridResultFlag:
        """Attempts to place a tile at a given location and updates the status of neighbors"""
        if not self._is_in_grid(xy) or (xy, tile) not in self.get_legal_placements(tile):
            print("Illegal placement: {}: ".format(xy), tile)
            return HexGridResultFlag.ERROR
        if self._is_near_border(xy, threshold=1):
            xy = self._enlarge_and_relocate(xy)
        self.get_tile(xy).set_edges(tile.edges)
        self.update_tile_status(xy)
        self.update_neighbors_status(xy)
        return HexGridResultFlag.OK


    def remove_tile(self, xy:tuple) -> HexGridResultFlag:
        """Attempts to remove a tile from a given location and updates the status of neighbors"""
        if not self._is_in_grid(xy) or self.get_tile(xy).is_empty():
            print("Illegal removal: {}: ".format(xy))
            return HexGridResultFlag.ERROR
        self.get_tile(xy).clear_edges()
        self.update_tile_status(xy)
        self.update_neighbors_status(xy)
        return HexGridResultFlag.OK


    def rank_all_placements(self, tile:HexTile) -> List[PlacementEvaluator]:
        """Ranks every legal placement of a tile based on the evaluations of those placements"""
        placements = self.get_legal_placements(tile)
        evaluators = []
        for placement in placements:
            xy, tile_ = placement
            neighborTiles = self._get_neighbor_tiles(xy)
            evaluator = PlacementEvaluator(tile_, xy, neighborTiles)
            evaluators.append(evaluator)
        ranked_evaluators = sorted(evaluators, key=lambda x: x.get_score(), reverse=True)
        return ranked_evaluators


    # TODO: clean up API
    def get_hint(self, tile:HexTile, top_k=None, threshold=None) -> list:
        """Returns the evaluations of the best placements of a tile"""
        ranked_evaluators = self.rank_all_placements(tile)
        num_evals = len(ranked_evaluators)
        if not threshold is None:
            above_threshold = [evaluator.get_score() >= threshold for evaluator in ranked_evaluators]
            num_evals = above_threshold.index(False)
        if not top_k is None:
            num_evals = min(top_k, num_evals)
        return ranked_evaluators[0:num_evals]


    