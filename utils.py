import os
from typing import Tuple, List
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


GridCoordinate = Tuple[int, int]
PixelCoordinate = Tuple[float, float]


def is_point_inside_polygon(point: PixelCoordinate, polygon: List[PixelCoordinate]) -> bool:
    return Polygon(polygon).contains(Point(point))


class Color:
    PASTEL_YELLOW = "#FFF0C1"
    PASTEL_BLUE = "#D2E2FB"
    PASTEL_GREEN = "#CCE4CA"
    PASTEL_RED = "#F5C2C1"
    WHITE = 'white'
    GREEN = 'green'
    BLACK = 'black'
    LIGHT_GREEN = 'lawn green'
    DARK_GREEN = 'forest green'
    RED = 'red'
    YELLOW = 'yellow'
    PINK = 'pink'
    PLUM = 'plum1'
    GOLD = 'gold'
    BLUE = 'blue'
    CYAN = 'cyan'
    LIGHT_GRAY = 'light gray'
    PURPLE = 'purple'


PARENT_DIR = os.path.dirname(__file__)
SAVE_DIR = os.path.join(PARENT_DIR, "saves/")
MANUAL_SAVE_FILEPATH = os.path.join(SAVE_DIR, "manual.p")
AUTO_SAVE_FILEPATH = os.path.join(SAVE_DIR, "auto.p")