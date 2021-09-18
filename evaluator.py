from enum import Flag, auto
import numpy as np
import os
from typing import Optional, List, Tuple, Callable

from edge import Edge, Connection
from tile import HexTile, TileStatus


Coordinate = Tuple[int, int]


class PlacementEvaluator:
    def __init__(self, tile: HexTile, xy: Coordinate, neighborTiles: List[HexTile]) -> None:
        self.tile = tile
        self.xy = xy
        self.neighborTiles = neighborTiles


    def zip_neighbor_tiles_and_connections(self) -> List[Tuple[HexTile, Connection]]:
        result = []
        for index, neighborTile in enumerate(self.neighborTiles):
            index_ = (index + 3) % 6
            edge = self.tile.get_edge(index)
            edge_ = neighborTile.get_edge(index_)
            result.append((neighborTile, Connection(edge, edge_)))
        return result


    def get_num_good_connections(self) -> int:
        return sum([connection.is_good() \
                        for _, connection in self.zip_neighbor_tiles_and_connections()])


    def get_num_bad_connections(self) -> int:
        return sum([not connection.is_good() and not Edge.EMPTY in connection.get_edges() \
                        for _, connection in self.zip_neighbor_tiles_and_connections()])


    def get_num_neighbors_perfected(self) -> int:
        return sum([connection.is_good() and neighborTile.num_good_connections == 5 \
                        for neighborTile, connection in self.zip_neighbor_tiles_and_connections()])


    def get_num_neighbors_ruined(self) -> int:
        return sum([not connection.is_good() and neighborTile.get_status() == TileStatus.GOOD \
                        for neighborTile, connection in self.zip_neighbor_tiles_and_connections()])


    def get_score(self) -> float:
        num_good_connections = self.get_num_good_connections()
        num_bad_connections = self.get_num_bad_connections()
        num_perfects = self.get_num_neighbors_perfected() + (num_good_connections == 6)
        num_neighbors_ruined = self.get_num_neighbors_ruined()
        return 0.5*num_perfects + num_good_connections - num_neighbors_ruined - 0.5*num_bad_connections
        