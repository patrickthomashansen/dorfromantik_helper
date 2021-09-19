from enum import Enum, auto
from typing import List

from utils import Color


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

    __GOOD_CONNECTIONS__ = [set([Edge.EMPTY]),
                            set([Edge.GRASS]),
                            set([Edge.TREES]),
                            set([Edge.HOUSE]),
                            set([Edge.CROPS]),
                            set([Edge.WATER]),
                            set([Edge.RIVER]),
                            set([Edge.TRAIN]),
                            set([Edge.STATION]),
                            set([Edge.RIVER, Edge.WATER]),
                            set([Edge.WATER, Edge.GRASS]),
                            set([Edge.GRASS, Edge.STATION]),
                            set([Edge.RIVER, Edge.STATION]),
                            set([Edge.WATER, Edge.STATION]),
                            set([Edge.TRAIN, Edge.STATION])]


    def __init__(self, edgeA: Edge, edgeB: Edge) -> None:
        self.edges = [edgeA, edgeB]


    def get_edges(self) -> List[Edge]:
        return self.edges


    def is_legal(self) -> bool:
        return not set(self.edges) in self.__ILLEGAL_CONNECTIONS__


    def is_good(self) -> bool:
        return set(self.edges) in self.__GOOD_CONNECTIONS__
