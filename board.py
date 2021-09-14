import numpy as np
import os
from typing import Optional

from hex_grid import HexGrid
from hex_tile import HexTile
from constants import *


class DorfBoard(HexGrid):
    """
    A class representing the board state of a Dorfromantik game
    """

    def _initialize_new_grid(self) -> None:
        """Creates a game board with only the origin tile"""
        super()._initialize_new_grid()
        xy = self._get_origin_xy()
        origin_tile = self.get_tile(xy)
        origin_tile.set_edges(ORIGIN_EDGES)
        origin_tile.set_status(TileStatus.GOOD)
        self.update_neighbors_status(xy)


    def is_legal_connection(self, xy:tuple, index:int, tile:HexTile) -> bool:
        """Checks if the connection along one edge would be legal if the tile is placed"""
        edge = tile.get_edge(index)
        xy_, index_ = self._get_opposite_edge_location(xy, index)
        if not self._is_in_grid(xy_):
            return True # Connection with a neighbor outside the board is legal
        edge_ = self.get_tile(xy_).get_edge(index_)
        return not set([edge, edge_]) in ILLEGAL_CONNECTIONS

    
    def is_good_connection(self, xy:tuple, index:int, tile:HexTile) -> bool:
        """Checks if the connection along one edge would be good if the tile is placed"""
        if not self.is_legal_connection(xy, index, tile):
            return False
        edge = tile.get_edge(index)
        xy_, index_ = self._get_opposite_edge_location(xy, index)
        edge_ = self.get_tile(xy_).get_edge(index_)
        return set([edge, edge_]) in GOOD_CONNECTIONS


    def is_legal_placement(self, xy:tuple, tile:HexTile) -> bool:
        """Checks if the given tile placement is legal"""
        for index in range(6):
            if not self.is_legal_connection(xy, index, tile):
                return False
        return True


    def get_legal_placements(self, tile:HexTile) -> list:
        """Returns a list of all legal placements of a tile"""
        rotations = tile.get_all_rotations()
        valid_locations = self.get_locations_with_status(TileStatus.VALID)
        legal_placements = []
        for xy in valid_locations:
            for rotation in rotations:
                if self.is_legal_placement(xy, rotation):
                    legal_placements.append((xy, rotation))
        return legal_placements


    def get_num_good_and_bad_connections(self, xy:tuple, tile:Optional[HexTile]=None) -> tuple:
        """Returns the number of good and bad connections a tile has (or will have if it is placed)"""
        if tile is None:
            tile = self.get_tile(xy)
        neighbors = self._get_neighboring_tile_xys(xy)
        num_good_connections = num_bad_connections = 0
        for index, xy_ in enumerate(neighbors):
            if self._is_in_grid(xy_) and not self.get_tile(xy_).is_empty():
                if self.is_good_connection(xy, index, tile):
                    num_good_connections += 1
                else:
                    num_bad_connections += 1
        return num_good_connections, num_bad_connections


    def get_status_from_connections(self, xy:tuple) -> int:
        """Returns the status of a tile location from the connections with its neighbors"""
        if self.get_tile(xy).is_empty():
            for xy_ in self._get_neighboring_tile_xys(xy):
                if self._is_in_grid(xy_) and not self.get_tile(xy_).is_empty():
                    return TileStatus.VALID
            return TileStatus.EMPTY
        else:
            num_good_connections, num_bad_connections = self.get_num_good_and_bad_connections(xy)
            if num_good_connections == 6:
                return TileStatus.PERFECT
            elif num_bad_connections > 0:
                return TileStatus.BAD
            else:
                return TileStatus.GOOD


    def update_tile_status(self, xy:tuple) -> None:
        """Updates the status of a tile"""
        self.get_tile(xy).set_status(self.get_status_from_connections(xy))


    def update_neighbors_status(self, xy:tuple) -> None:
        """Updates the status of all neighbors to a tile"""
        for xy_ in self._get_neighboring_tile_xys(xy):
            self.update_tile_status(xy_)


    def place_tile(self, xy:tuple, tile:list) -> int:
        """Attempts to place a tile at a given location and updates the status of neighbors"""
        if not self._is_in_grid(xy) or (xy, tile) not in self.get_legal_placements(tile):
            print("Illegal placement: {}: ".format(xy), tile)
            return DorfBoardResult.ERROR
        if self._is_near_border(xy, threshold=1):
            xy = self._enlarge_and_relocate(xy)
        self.get_tile(xy).set_edges(tile.edges)
        self.get_tile(xy).set_status(tile.status)
        self.update_tile_status(xy)
        self.update_neighbors_status(xy)
        return DorfBoardResult.OK


    def remove_tile(self, xy:tuple) -> int:
        """Attempts to remove a tile from a given location and updates the status of neighbors"""
        if not self._is_in_grid(xy) or self.get_tile(xy).is_empty():
            print("Illegal removal: {}: ".format(xy))
            return DorfBoardResult.ERROR
        super().remove_tile(xy)
        self.update_tile_status(xy)
        self.update_neighbors_status(xy)
        return DorfBoardResult.OK


    # TODO: make an evaluation class
    def evaluate_placement(self, xy:tuple, tile:HexTile) -> dict:
        """Evaluates how well a tile fits in a given location"""
        assert self.is_legal_placement(xy, tile)
        # Compute the number of adjecent tiles that would become perfects
        num_perfects = 0
        num_meh_connections = 0
        neighbors = self._get_neighboring_tile_xys(xy)
        for index, xy_ in enumerate(neighbors):
            if not self.get_tile(xy_).is_empty():
                num_good_connections, num_bad_connections = self.get_num_good_and_bad_connections(xy_)
                if num_good_connections == 6-1 and self.is_good_connection(xy, index, tile):
                    num_perfects += 1
                elif num_bad_connections > 0 and not self.is_good_connection(xy, index, tile):
                    num_meh_connections += 1
        # Compute the number of good and bad connections
        num_good_connections, num_bad_connections = self.get_num_good_and_bad_connections(xy, tile)
        if num_good_connections == 6:
            num_perfects += 1
        # Give a proxy score
        score = 0.5*num_perfects + num_good_connections - (1.5*num_bad_connections - num_meh_connections)
        evaluation = {'score': score,
                      'perfect': num_perfects,
                      'good': num_good_connections,
                      'bad': num_bad_connections,
                      'meh': num_meh_connections}
        return evaluation


    def rank_all_placements(self, tile:HexTile) -> list:
        """Ranks every legal placement of a tile based on the evaluations of those placements"""
        placements = self.get_legal_placements(tile)
        evaluations = []
        for placement in placements:
            xy_, tile_ = placement
            evaluation = self.evaluate_placement(xy_, tile_)
        ranked_evaluations = sorted(evaluations, key=lambda x: x[1]['score'], reverse=True)
        return ranked_evaluations


    # TODO: clean up API
    def get_hint(self, tile:HexTile, top_k=None, threshold=None) -> list:
        """Returns the evaluations of the best placements of a tile"""
        ranked_evaluations = self.rank_all_placements(tile)
        num_evals = len(ranked_evaluations)
        if not threshold is None:
            above_threshold = [evaluation['score'] >= threshold for _, evaluation in ranked_evaluations]
            num_evals = above_threshold.index(False)
        if not top_k is None:
            num_evals = min(top_k, num_evals)
        return ranked_evaluations[0:num_evals]