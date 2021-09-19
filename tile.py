from __future__ import annotations

from enum import Enum, auto
from typing import Optional, List, Iterator

from edge import Edge, Connection
from utils import Color, EdgeIndex


class TileStatus(Enum):
    EMPTY = auto()
    GOOD = auto()
    PERFECT = auto()
    BAD = auto()
    VALID = auto()

    __COLORS__ = {EMPTY: Color.WHITE,
                  GOOD: Color.GREEN,
                  PERFECT: Color.BLUE,
                  BAD: Color.RED,
                  VALID: Color.WHITE}


    def to_color(self) -> Color:
        return self.__COLORS__[self.value]


class HexTile:
    EMPTY_EDGES = 6 * [Edge.EMPTY]
    ORIGIN_EDGES = 6 * [Edge.GRASS]


    def __init__(self, edges: Optional[List[Edge]] = None) -> None:
        if edges is None:
            self.clear_edges()
        else:
            self.edges = edges.copy()
        self.clear_status()


    def __eq__(self, other: HexTile) -> bool:
        if (isinstance(other, HexTile)):
            return self.edges == other.edges
        return False


    def get_edges(self) -> List[Edge]:
        return self.edges.copy()


    def get_edge(self, index: EdgeIndex) -> Edge:
        return self.edges[index]


    def set_edges(self, edges: List[Edge]) -> None:
        self.edges = edges.copy()


    def set_edge(self, edge: Edge, index: EdgeIndex) -> None:
        self.edges[index] = edge


    def clear_edges(self) -> None:
        self.edges = HexTile.EMPTY_EDGES


    def update_status(self, neighborTiles: Optional[List[HexTile]]) -> None:
        """Computes the status of the tile given the edges of the neighboring tiles"""
        self.num_good_connections = 0
        self.num_bad_connections = 0
        self.num_empty_neighbors = 0
        if neighborTiles is None:
            self.status = TileStatus.EMPTY if self.is_empty() else TileStatus.GOOD
            return
        # Gather statistics
        for index, neighborTile in enumerate(neighborTiles):
            index_ = (index + 3) % 6
            edge = self.edges[index]
            edge_ = neighborTile.edges[index_]
            if neighborTile.is_empty():
                self.num_empty_neighbors += 1
            elif not Connection(edge, edge_).is_good() and not edge_ == Edge.EMPTY:
                self.num_bad_connections += 1
            else:
                self.num_good_connections += 1
        # Determine tile status
        if self.is_empty() and self.num_empty_neighbors == 6:
            self.status = TileStatus.EMPTY
        elif self.is_empty():
            self.status = TileStatus.VALID
        elif self.num_good_connections == 6:
            self.status = TileStatus.PERFECT
        elif self.num_bad_connections > 0:
            self.status = TileStatus.BAD
        else:
            self.status = TileStatus.GOOD


    def clear_status(self) -> None:
        self.update_status(None)


    def get_status(self) -> TileStatus:
        return self.status


    def is_empty(self) -> bool:
        return self.get_edges() == HexTile.EMPTY_EDGES


    def rotate(self, clockwise: bool = True) -> None:
        edges = self.get_edges()
        if clockwise:
            self.set_edges(edges[5:] + edges[:5])
        else:
            self.set_edges(edges[1:] + edges[:1])


    def get_all_rotations(self) -> List[HexTile]:
        """Generates a list of all posible rotations of the tile"""
        rotations = []
        for i in range(6):
            rotations.append(tuple(self.edges[i:] + self.edges[:i]))
        rotations = list(set(rotations)) # Remove duplicate rotations
        return [HexTile(list(edges)) for edges in rotations]
