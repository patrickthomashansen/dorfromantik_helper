from typing import Optional

from constants import *


class HexTile:

    def __init__(self, edges:Optional[list]=None, status:Optional[int]=None):
        self.edges = 6*[TileEdge.EMPTY] if edges is None else edges
        self.status = TileStatus.EMPTY if status is None else status


    def __iter__(self):
        return iter(self.edges)


    def __eq__(self, other):
        if (isinstance(other, HexTile)):
            return self.edges == other.edges


    def __str__(self):
        return "<HexTile: {}>".format(self.edges)


    def __repr__(self):
        return str(self)


    def get_edges(self) -> list:
        return self.edges.copy()


    def get_edge(self, index:int) -> list:
        return self.edges[index]


    def set_edges(self, edges:list) -> None:
        self.edges = edges.copy()


    def set_edge(self, edge:int, index:int) -> None:
        self.edges[index] = edge


    def clear_edges(self) -> None:
        self.edges = 6*[TileEdge.EMPTY]


    def get_status(self) -> int:
        return self.status


    def set_status(self, status:int) -> None:
        self.status = status


    def clear_status(self) -> None:
        self.status = TileStatus.EMPTY


    def is_empty(self) -> bool:
        return all([edge == TileEdge.EMPTY for edge in self.edges])


    def is_valid(self) -> bool:
        return self.status == TileStatus.VALID


    def get_rotations(self) -> list:
        """Generates a list of all posible rotations of the tile"""
        rotations = []
        for i in range(6):
            rotations.append(tuple(self.edges[i:] + self.edges[:i]))
        rotations = list(set(rotations)) # Remove duplicate rotations
        return [HexTile(list(edges)) for edges in rotations]
