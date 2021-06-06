import os

NUM_HEXA_EDGES = 6

class DorfBoardResult:
    OK = 0
    ENLARGE = -2
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


ILLEGAL_CONNECTIONS = [[TileEdge.RIVER, TileEdge.GRASS],
                       [TileEdge.RIVER, TileEdge.TREES],
                       [TileEdge.RIVER, TileEdge.HOUSE],
                       [TileEdge.RIVER, TileEdge.CROPS],
                       [TileEdge.RIVER, TileEdge.TRAIN],
                       [TileEdge.TRAIN, TileEdge.WATER],
                       [TileEdge.TRAIN, TileEdge.GRASS],
                       [TileEdge.TRAIN, TileEdge.TREES],
                       [TileEdge.TRAIN, TileEdge.HOUSE],
                       [TileEdge.TRAIN, TileEdge.CROPS]]


GOOD_CONNECTIONS = [[TileEdge.GRASS, TileEdge.GRASS],
                    [TileEdge.TREES, TileEdge.TREES],
                    [TileEdge.HOUSE, TileEdge.HOUSE],
                    [TileEdge.CROPS, TileEdge.CROPS],
                    [TileEdge.WATER, TileEdge.WATER],
                    [TileEdge.RIVER, TileEdge.RIVER],
                    [TileEdge.TRAIN, TileEdge.TRAIN],
                    [TileEdge.STATION, TileEdge.STATION],
                    [TileEdge.RIVER, TileEdge.WATER],
                    [TileEdge.WATER, TileEdge.RIVER],
                    [TileEdge.RIVER, TileEdge.STATION],
                    [TileEdge.WATER, TileEdge.STATION],
                    [TileEdge.TRAIN, TileEdge.STATION]]


class TileStatus:
    EMPTY = 0
    GOOD = 1
    PERFECT = 2
    IMPERFECT = 3
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
    IMPERFECT = 'red'
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
                       TileStatus.IMPERFECT:    TileStatusColors.IMPERFECT,
                       TileStatus.VALID:        TileStatusColors.VALID}
    if status in status_to_color.keys():
        return status_to_color[status]
    else:
        raise(Exception("Invalid status: ", status))


PARENT_DIR = os.path.dirname(__file__)
SAVE_DIR = os.path.join(PARENT_DIR, "saves/")
MANUAL_SAVE_FILEPATH = os.path.join(SAVE_DIR, "manual.npz")
AUTO_SAVE_FILEPATH = os.path.join(SAVE_DIR, "auto.npz")