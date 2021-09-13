import os



class Colors:
    PASTEL_YELLOW = "#FFF0C1"
    PASTEL_BLUE = "#D2E2FB"
    PASTEL_GREEN = "#CCE4CA"
    PASTEL_RED = "#F5C2C1"


class DorfBoardResult:
    OK = 0
    ILLEGAL = -3
    ERROR = -1

class TileEdge:
    EMPTY = 0
    GRASS = 1
    TREES = 2
    HOUSE = 3
    CROPS = 4
    WATER = 5
    RIVER = 6
    TRAIN = 7
    STATION = 8


ORIGIN_EDGES = 6 * [TileEdge.GRASS]


ILLEGAL_CONNECTIONS = [set([TileEdge.RIVER, TileEdge.GRASS]),
                       set([TileEdge.RIVER, TileEdge.TREES]),
                       set([TileEdge.RIVER, TileEdge.HOUSE]),
                       set([TileEdge.RIVER, TileEdge.CROPS]),
                       set([TileEdge.RIVER, TileEdge.TRAIN]),
                       set([TileEdge.TRAIN, TileEdge.WATER]),
                       set([TileEdge.TRAIN, TileEdge.GRASS]),
                       set([TileEdge.TRAIN, TileEdge.TREES]),
                       set([TileEdge.TRAIN, TileEdge.HOUSE]),
                       set([TileEdge.TRAIN, TileEdge.CROPS])]


GOOD_CONNECTIONS = [set([TileEdge.GRASS, TileEdge.GRASS]),
                    set([TileEdge.TREES, TileEdge.TREES]),
                    set([TileEdge.HOUSE, TileEdge.HOUSE]),
                    set([TileEdge.CROPS, TileEdge.CROPS]),
                    set([TileEdge.WATER, TileEdge.WATER]),
                    set([TileEdge.RIVER, TileEdge.RIVER]),
                    set([TileEdge.TRAIN, TileEdge.TRAIN]),
                    set([TileEdge.STATION, TileEdge.STATION]),
                    set([TileEdge.RIVER, TileEdge.WATER]),
                    set([TileEdge.WATER, TileEdge.GRASS]),
                    set([TileEdge.GRASS, TileEdge.STATION]),
                    set([TileEdge.RIVER, TileEdge.STATION]),
                    set([TileEdge.WATER, TileEdge.STATION]),
                    set([TileEdge.TRAIN, TileEdge.STATION])]


class TileStatus:
    EMPTY = 0
    GOOD = 1
    PERFECT = 2
    BAD = 3
    VALID = 4


class TileFeatureColors:
    EMPTY = 'white'
    GRASS = 'lawn green'
    TREES = 'forest green'
    HOUSE = 'red'
    CROPS = 'gold'
    WATER = 'blue'
    RIVER = 'cyan'
    TRAIN = 'light gray'
    STATION = 'purple'


class TileFeatureNames:
    EMPTY = "Empty"
    GRASS = "Grass"
    TREES = "TREES"
    HOUSE = "House"
    CROPS = "Crops"
    WATER = "Water"
    RIVER = "River"
    TRAIN = "Train"
    STATION = "Station"


class TileStatusColors:
    EMPTY = None
    GOOD = 'green'
    PERFECT = 'blue'
    BAD = 'red'
    VALID = 'white'
    HINT = 'plum1'


class TileOutlineColors:
    EMPTY = 'white'
    NORMAL = 'black'
    SELECTED = 'yellow'


def get_color_from_feature(feature):
    feature_to_color = {TileEdge.EMPTY:     TileFeatureColors.EMPTY,
                        TileEdge.GRASS:     TileFeatureColors.GRASS,
                        TileEdge.TREES:     TileFeatureColors.TREES,
                        TileEdge.HOUSE:     TileFeatureColors.HOUSE,
                        TileEdge.CROPS:     TileFeatureColors.CROPS,
                        TileEdge.WATER:     TileFeatureColors.WATER,
                        TileEdge.RIVER:     TileFeatureColors.RIVER,
                        TileEdge.TRAIN:     TileFeatureColors.TRAIN,
                        TileEdge.STATION:   TileFeatureColors.STATION}
    if feature in feature_to_color.keys():
        return feature_to_color[feature]
    else:
        raise(Exception("Invalid feature: ", feature))


def get_name_from_feature(feature):
    feature_to_name = {TileEdge.EMPTY:     TileFeatureNames.EMPTY,
                       TileEdge.GRASS:     TileFeatureNames.GRASS,
                       TileEdge.TREES:     TileFeatureNames.TREES,
                       TileEdge.HOUSE:     TileFeatureNames.HOUSE,
                       TileEdge.CROPS:     TileFeatureNames.CROPS,
                       TileEdge.WATER:     TileFeatureNames.WATER,
                       TileEdge.RIVER:     TileFeatureNames.RIVER,
                       TileEdge.TRAIN:     TileFeatureNames.TRAIN,
                       TileEdge.STATION:   TileFeatureNames.STATION}
    if feature in feature_to_name.keys():
        return feature_to_name[feature]
    else:
        raise(Exception("Invalid feature: ", feature))



def get_color_from_status(status):
    status_to_color = {TileStatus.EMPTY:        TileStatusColors.EMPTY,
                       TileStatus.GOOD:         TileStatusColors.GOOD,
                       TileStatus.PERFECT:      TileStatusColors.PERFECT,
                       TileStatus.BAD:    TileStatusColors.BAD,
                       TileStatus.VALID:        TileStatusColors.VALID}
    if status in status_to_color.keys():
        return status_to_color[status]
    else:
        raise(Exception("Invalid status: ", status))


PARENT_DIR = os.path.dirname(__file__)
SAVE_DIR = os.path.join(PARENT_DIR, "saves/")
MANUAL_SAVE_FILEPATH = os.path.join(SAVE_DIR, "manual.p")
AUTO_SAVE_FILEPATH = os.path.join(SAVE_DIR, "auto.p")