from __future__ import annotations

from enum import Enum, auto
from typing import Optional, List, Iterator

from edge import Edge, EdgeIndex, Connection
from constants import Color


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
    edges: List[Edge]
    num_good_connections: int
    num_bad_connections: int
    num_empty_neighbors: int
    status: TileStatus


    def __init__(self, edges: Optional[List[Edge]] = None) -> None:
        self.edges = 6 * [Edge.EMPTY] if edges is None else edges.copy()
        self.update_status(neighborTiles=6*[None])


    def __iter__(self) -> Iterator[Edge]:
        return iter(self.edges)


    def __eq__(self, other: HexTile) -> bool:
        if (isinstance(other, HexTile)):
            return self.edges == other.edges
        return False


    def __str__(self) -> str:
        return "<HexTile: {}>".format(self.edges)


    def __repr__(self) -> str:
        return str(self)


    def get_edges(self) -> List[Edge]:
        return self.edges.copy()


    def get_edge(self, index: EdgeIndex) -> Edge:
        return self.edges[index]


    def set_edges(self, edges: List[Edge]) -> None:
        self.edges = edges.copy()


    def set_edge(self, edge: Edge, index: EdgeIndex) -> None:
        self.edges[index] = edge


    def clear_edges(self) -> None:
        self.edges = 6*[Edge.EMPTY]


    def update_status(self, neighborTiles: List[Optional[HexTile]]) -> None:
        """Computes the status of the tile given the edges of the neighboring tiles"""
        # Gather statistics
        self.num_good_connections = 0
        self.num_bad_connections = 0
        self.num_empty_neighbors = 0
        for index, neighborTile in enumerate(neighborTiles):
            if neighborTile is None:
                self.num_empty_neighbors += 1
                continue
            index_ = (index + 3) % 6
            edge = self.edges[index]
            edge_ = neighborTile.edges[index_]
            if neighborTile.is_empty():
                self.num_empty_neighbors += 1
            elif Connection(edge, edge_).is_good():
                self.num_good_connections += 1
            else:
                self.num_bad_connections += 1
        # Determine tile status
        if self.edges == 6*[Edge.EMPTY] and self.num_empty_neighbors == 6:
            self.status = TileStatus.EMPTY
        elif self.edges == 6*[Edge.EMPTY] and self.num_empty_neighbors < 6:
            self.status = TileStatus.VALID
        elif self.num_good_connections == 6:
            self.status = TileStatus.PERFECT
        elif self.num_bad_connections > 0:
            self.status = TileStatus.BAD
        else:
            self.status = TileStatus.GOOD


    def get_status(self) -> TileStatus:
        return self.status


    def is_empty(self) -> bool:
        return self.get_edges() == 6*[Edge.EMPTY]


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
