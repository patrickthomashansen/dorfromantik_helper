from __future__ import annotations

from enum import Enum, auto
from typing import Optional, List, Iterator

from constants import Color


EdgeIndex = int


class Edge(Enum):
    EMPTY = auto()
    GRASS = auto()
    TREES = auto()
    HOUSE = auto()
    CROPS = auto()
    WATER = auto()
    RIVER = auto()
    TRAIN = auto()
    STATION = auto()

    __COLORS__ = {EMPTY: Color.WHITE,
                  GRASS: Color.LIGHT_GREEN,
                  TREES: Color.DARK_GREEN,
                  HOUSE: Color.RED,
                  CROPS: Color.GOLD,
                  WATER: Color.BLUE,
                  RIVER: Color.CYAN,
                  TRAIN: Color.LIGHT_GRAY,
                  STATION: Color.PURPLE}


    def to_color(self) -> Color:
        return self.__COLORS__[self.value]



class Connection:
    __ILLEGAL_CONNECTIONS__ = [set([Edge.RIVER, Edge.GRASS]),
                               set([Edge.RIVER, Edge.TREES]),
                               set([Edge.RIVER, Edge.HOUSE]),
                               set([Edge.RIVER, Edge.CROPS]),
                               set([Edge.RIVER, Edge.TRAIN]),
                               set([Edge.TRAIN, Edge.WATER]),
                               set([Edge.TRAIN, Edge.GRASS]),
                               set([Edge.TRAIN, Edge.TREES]),
                               set([Edge.TRAIN, Edge.HOUSE]),
                               set([Edge.TRAIN, Edge.CROPS])]

    __GOOD_CONNECTIONS__ = [set([Edge.RIVER, Edge.WATER]),
                            set([Edge.WATER, Edge.GRASS]),
                            set([Edge.GRASS, Edge.STATION]),
                            set([Edge.RIVER, Edge.STATION]),
                            set([Edge.WATER, Edge.STATION]),
                            set([Edge.TRAIN, Edge.STATION])]


    def __init__(self, edgeA, edgeB) -> None:
        self.edgeA = edgeA
        self.edgeB = edgeB


    def is_legal(self) -> bool:
        connection = set([self.edgeA, self.edgeB])
        return not connection in self.__ILLEGAL_CONNECTIONS__


    def is_good(self) -> bool:
        connection = set([self.edgeA, self.edgeB])
        return len(connection) == 1 or connection in self.__GOOD_CONNECTIONS__
