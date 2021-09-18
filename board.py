from enum import Flag, auto
import numpy as np
import os
from typing import Optional, List, Tuple, Callable

from edge import Edge, EdgeIndex, Connection
from tile import HexTile, TileStatus
from grid import HexGrid, Coordinate


class DorfBoardResultFlag(Flag):
    OK = auto()
    ILLEGAL = auto()
    ERROR = auto()


class PlacementEvaluator:
    def __init__(self, tile: HexTile, xy: Coordinate, neighborTiles: List[Optional[HexTile]]) -> None:
        self.tile = tile
        self.xy = xy
        self.neighborTiles = neighborTiles


    def get_num_good_connections(self) -> int:
        count = 0
        for index, neighborTile in enumerate(self.neighborTiles):
            index_ = (index + 3) % 6
            edge = self.tile.get_edge(index)
            edge_ = neighborTile.get_edge(index_)
            if Connection(edge, edge_).is_good():
                count += 1
        return count


    def get_num_bad_connections(self) -> int:
        count = 0
        for index, neighborTile in enumerate(self.neighborTiles):
            index_ = (index + 3) % 6
            edge = self.tile.get_edge(index)
            edge_ = neighborTile.get_edge(index_)
            if not Connection(edge, edge_).is_good() and not edge_ == Edge.EMPTY:
                count += 1
        return count

    def get_num_neighbors_perfected(self) -> int:
        count = 0
        for index, neighborTile in enumerate(self.neighborTiles):
            if neighborTile is None or neighborTile.status == TileStatus.EMPTY:
                continue
            index_ = (index + 3) % 6
            edge = self.tile.get_edge(index)
            edge_ = neighborTile.get_edge(index_)
            if Connection(edge, edge_).is_good() and neighborTile.num_good_connections == 5:
                count += 1
        return count


    def get_num_neighbors_ruined(self) -> int:
        count = 0
        for index, neighborTile in enumerate(self.neighborTiles):
            if neighborTile is None or neighborTile.status == TileStatus.EMPTY:
                continue
            index_ = (index + 3) % 6
            edge = self.tile.get_edge(index)
            edge_ = neighborTile.get_edge(index_)
            if not Connection(edge, edge_).is_good() and neighborTile.num_bad_connections == 0:
                count += 1
        return count


    def get_score(self) -> float:
        num_good_connections = self.get_num_good_connections()
        num_bad_connections = self.get_num_bad_connections()
        num_perfects = self.get_num_neighbors_perfected() + (num_good_connections == 6)
        num_neighbors_ruined = self.get_num_neighbors_ruined()
        return 0.5*num_perfects + num_good_connections - num_neighbors_ruined - 0.5*num_bad_connections
        


class DorfBoard(HexGrid):
    """
    A class representing the board state of a Dorfromantik game
    """

    def _initialize_new_grid(self) -> None:
        """Creates a game board with only the origin tile"""
        super()._initialize_new_grid()
        xy = self._get_origin_xy()
        origin_tile = self.get_tile(xy)
        origin_tile.set_edges(6*[Edge.GRASS])
        origin_tile.update_status(neighborTiles=6*[None])
        self.update_neighbors_status(xy)


    def is_legal_connection(self, xy: Coordinate, index: EdgeIndex, tile: HexTile) -> bool:
        """Checks if the connection along one edge would be legal if the tile is placed"""
        edge = tile.get_edge(index)
        xy_, index_ = self._get_opposite_edge_location(xy, index)
        if not self._is_in_grid(xy_):
            return True # Connection with a neighbor outside the board is legal
        edge_ = self.get_tile(xy_).get_edge(index_)
        return Connection(edge, edge_).is_legal()


    def is_legal_placement(self, xy: Coordinate, tile: HexTile) -> bool:
        """Checks if the given tile placement is legal"""
        for index in range(6):
            if not self.is_legal_connection(xy, index, tile):
                return False
        return True


    def get_legal_placements(self, tile: HexTile) -> List[Tuple[Coordinate, HexTile]]:
        """Returns a list of all legal placements of a tile"""
        rotations = tile.get_all_rotations()
        valid_locations = self.get_locations_with_status(TileStatus.VALID)
        legal_placements = []
        for xy in valid_locations:
            for rotation in rotations:
                if self.is_legal_placement(xy, rotation):
                    legal_placements.append((xy, rotation))
        return legal_placements


    def update_tile_status(self, xy: Coordinate) -> None:
        """Updates the status of a tile"""
        neighborTiles = self._get_neighbor_tiles(xy)
        self.get_tile(xy).update_status(neighborTiles)


    def update_neighbors_status(self, xy: Coordinate) -> None:
        """Updates the status of all neighbors to a tile"""
        for xy_ in self._get_neighboring_tile_xys(xy):
            self.update_tile_status(xy_)


    def place_tile(self, xy: Coordinate, tile: HexTile) -> DorfBoardResultFlag:
        """Attempts to place a tile at a given location and updates the status of neighbors"""
        if not self._is_in_grid(xy) or (xy, tile) not in self.get_legal_placements(tile):
            print("Illegal placement: {}: ".format(xy), tile)
            return DorfBoardResultFlag.ERROR
        if self._is_near_border(xy, threshold=1):
            xy = self._enlarge_and_relocate(xy)
        self.get_tile(xy).set_edges(tile.edges)
        self.update_tile_status(xy)
        self.update_neighbors_status(xy)
        return DorfBoardResultFlag.OK


    def remove_tile(self, xy:tuple) -> DorfBoardResultFlag:
        """Attempts to remove a tile from a given location and updates the status of neighbors"""
        if not self._is_in_grid(xy) or self.get_tile(xy).is_empty():
            print("Illegal removal: {}: ".format(xy))
            return DorfBoardResultFlag.ERROR
        super().remove_tile(xy)
        self.update_tile_status(xy)
        self.update_neighbors_status(xy)
        return DorfBoardResultFlag.OK


    def rank_all_placements(self, tile:HexTile) -> list:
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