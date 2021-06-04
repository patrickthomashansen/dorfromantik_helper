from collections import namedtuple
import numpy as np
from constants import *


class DorfBoard:

    EDGE_ZERO_INDEX = 'left'
    DIRECTION = 'clockwise'
    ORIGIN_TILE = NUM_HEXA_EDGES * [TileEdge.GRASS]


    def __init__(self, starting_size=8, edges=None, status=None):
        
        if not edges is None and not status is None:
            self.edges = edges
            self.status = status
            self.size = len(edges)
        else:
            self.size = starting_size
            self.edges = np.zeros([self.size, self.size, NUM_HEXA_EDGES], dtype=np.uint8)
            self.status = np.zeros([self.size, self.size], dtype=np.uint8)
            x, y = self.get_origin_xy()
            self.edges[x,y] = self.ORIGIN_TILE
            self.status[x,y] = TileStatus.GOOD
            for x_, y_ in self.get_neighboring_tiles(x,y):
                self.update_tile_status(x_, y_)
        self.height = self.size
        self.width = self.size


    def get_origin_xy(self):
        return int(self.size/2 - 1), int(self.size/2 - 1)


    def is_in_grid(self, x, y):
        return x >= 0 and y >= 0 and x < self.size and y < self.size


    def is_on_border(self, x, y):
        return x == 0 or y == 0 or x == self.size-1 or y == self.size-1


    def is_near_border(self, x, y, distance=1):
        if not self.is_in_grid(x, y):
            return DorfBoardResult.ERROR
        return x <= distance or y <= distance or x >= self.size-1-distance or y >= self.size-1-distance


    def enlarge(self, pad_size=2):
        new_size = self.size + 2*pad_size
        x0 = y0 = pad_size
        x1 = y1 = pad_size + self.size
        new_edges =  np.zeros([new_size, new_size, NUM_HEXA_EDGES], dtype=np.uint8)
        new_status =  np.zeros([new_size, new_size], dtype=np.uint8)
        new_edges[x0:x1,y0:y1] = self.edges
        new_status[x0:x1,y0:y1] = self.status
        self.edges = new_edges
        self.status = new_status
        self.size = new_size
        self.height = new_size
        self.width = new_size


    def enlarge_and_relocate(self, x, y, pad_size=2):
        self.enlarge(pad_size)
        return x+pad_size, y+pad_size


    @staticmethod
    def get_neighboring_tiles(x, y):
        return [(x-1,y), (x,y-1), (x+1,y-1), (x+1,y), (x,y+1), (x-1,y+1)]


    def get_tile_rotations(self, tile):
        rotations = []
        for i in range(NUM_HEXA_EDGES):
            rotations.append(tuple(tile[i:] + tile[:i]))
        rotations = list(set(rotations))
        rotations = [list(r) for r in rotations]
        return rotations


    def is_empty_tile(self, x, y):
        return (self.edges[x, y] == TileEdge.EMPTY).all()


    def get_opposite_edge(self, x, y, edge_index):
        if edge_index == 0:
            return x-1, y, 3
        elif edge_index == 1:
            return x, y-1, 4
        elif edge_index == 2:
            return x+1, y-1, 5
        elif edge_index == 3:
            return x+1, y, 0
        elif edge_index == 4:
            return x, y+1, 1
        elif edge_index == 5:
            return x-1, y+1, 2


    def is_legal_connection(self, x, y, edge_index, tile):
        edge1 = tile[edge_index]
        x_, y_, edge_index_ = self.get_opposite_edge(x, y, edge_index)
        if not self.is_in_grid(x_, y_):
            return True
        edge2 = self.edges[x_,y_,edge_index_]
        if [edge1, edge2] in ILLEGAL_CONNECTIONS:
            return False
        elif [edge2, edge1] in ILLEGAL_CONNECTIONS:
            return False
        else:
            return True

    
    def is_good_connection(self, x, y, edge_index, tile=None):
        if tile is None:
            tile = self.edges[x,y]
        if not self.is_legal_connection(x, y, edge_index, tile):
            return False
        edge1 = tile[edge_index]
        x_, y_, edge_index_ = self.get_opposite_edge(x, y, edge_index)
        edge2 = self.edges[x_,y_,edge_index_]
        if [edge1, edge2] in GOOD_CONNECTIONS:
            return True
        elif [edge2, edge1] in GOOD_CONNECTIONS:
            return True
        else:
            return False

    def get_valid_locations(self, tile):
        return zip(*np.where(self.status==TileStatus.VALID))


    def get_legal_placements(self, tile):
        rotations = self.get_tile_rotations(tile)
        valid_locations = self.get_valid_locations(tile)
        legal_placements = []
        for (x,y) in valid_locations:
            for rotation in rotations:
                is_legal = True
                for edge_index in range(NUM_HEXA_EDGES):
                    if not self.is_legal_connection(x, y, edge_index, rotation):
                        is_legal = False
                        break
                if is_legal:
                    legal_placements.append([x, y, rotation])
        return legal_placements


    def get_connecting_edges(self, x, y):
        connections = []
        for edge_index in range(NUM_HEXA_EDGES):
            x_, y_, opposite_edge_index = self.get_opposite_edge(x, y, edge_index)
            if self.is_in_grid(x_, y_) and not self.is_empty_tile(x_, y_):
                connections.append(self.edges[x_,y_,opposite_edge_index])
            else:
                connections.append(TileEdge.EMPTY)
        return connections


    def get_num_good_and_bad_connections(self, x, y, tile=None):
        if tile is None:
            tile = self.edges[x,y]
        neighbors = self.get_neighboring_tiles(x, y)
        num_good_connections = num_bad_connections = 0
        for edge_index, (x_, y_) in enumerate(neighbors):
            if self.is_in_grid(x_, y_) and not self.is_empty_tile(x_, y_):
                if self.is_good_connection(x, y, edge_index, tile):
                    num_good_connections += 1
                else:
                    num_bad_connections += 1
        return num_good_connections, num_bad_connections


    def get_tile_status_from_connections(self, x, y):
        if self.is_empty_tile(x, y):
            for x_, y_ in self.get_neighboring_tiles(x, y):
                if self.is_in_grid(x_, y_) and not self.is_empty_tile(x_, y_):
                        return TileStatus.VALID
            return TileStatus.EMPTY
        else:
            num_good_connections, num_bad_connections = self.get_num_good_and_bad_connections(x, y)
            if num_good_connections == NUM_HEXA_EDGES:
                return TileStatus.PERFECT
            elif num_bad_connections > 0:
                return TileStatus.IMPERFECT
            else:
                return TileStatus.GOOD


    def update_tile_status(self, x, y):
        self.status[x,y] = self.get_tile_status_from_connections(x, y)


    def place_tile(self, x, y, tile):
        if not self.is_in_grid(x, y) or [x, y, tile] not in self.get_legal_placements(tile):
            print("Illegal placement: ({},{}): ".format(x, y), tile)
            return DorfBoardResult.ERROR
        if self.is_near_border(x, y, distance=1):
            x, y = self.enlarge_and_relocate(x, y)
            result = DorfBoardResult.ENLARGE
        else:
            result = DorfBoardResult.OK
        self.edges[x,y] = tile
        self.status[x,y] = self.get_tile_status_from_connections(x, y)
        for x_, y_ in self.get_neighboring_tiles(x, y):
            self.update_tile_status(x_, y_)
        return result


    def remove_tile(self, x, y):
        if not self.is_in_grid(x, y) or self.is_empty_tile(x, y):
            print("Illegal removal: ({},{}): ".format(x, y))
            return DorfBoardResult.ERROR
        self.edges[x,y] = NUM_HEXA_EDGES * [TileEdge.EMPTY]
        self.status[x,y] = self.get_tile_status_from_connections(x, y)
        for x_, y_ in self.get_neighboring_tiles(x, y):
            self.update_tile_status(x_, y_)
        return DorfBoardResult.OK


    def evaluate_placement(self, x, y, tile):
        for edge_index in range(NUM_HEXA_EDGES):
            if not self.is_legal_connection(x, y, edge_index, tile):
                return DorfBoardResult.ILLEGAL
        # Compute the number of adjecent tiles that would become perfects
        num_perfects = 0
        neighbors = self.get_neighboring_tiles(x, y)
        for x_, y_ in neighbors:
            num_good_connections, _ = self.get_num_good_and_bad_connections(x_, y_)
            if num_good_connections == NUM_HEXA_EDGES-1:
                num_perfects += 1
        # Compute the number of good and bad connections
        num_good_connections, num_bad_connections = self.get_num_good_and_bad_connections(x, y, tile)
        if num_good_connections == NUM_HEXA_EDGES:
            num_perfects += 1
        # Give a proxy score
        score = 0.5*num_perfects + num_good_connections - 2*num_bad_connections
        return score, num_perfects, num_good_connections, num_bad_connections


    def rank_all_placements(self, tile):
        placements = self.get_legal_placements(tile)
        evaluations = []
        for placement in placements:
            x_, y_, tile_ = placement
            evaluation = self.evaluate_placement(x_, y_, tile_)
            if not evaluation == DorfBoardResult.ILLEGAL:
                evaluations.append((placement, evaluation))
        ranked_evaluations = sorted(evaluations, key=lambda x: x[1][0], reverse=True)
        return ranked_evaluations


    def get_hint(self, tile, top_k=None, threshold=None):
        ranked_evaluations = self.rank_all_placements(tile)
        num_evals = len(ranked_evaluations)
        if not threshold is None:
            above_threshold = [score >= threshold for _, (score, _, _, _) in ranked_evaluations]
            num_evals = above_threshold.index(False)
        if not top_k is None:
            num_evals = min(top_k, num_evals)
        return ranked_evaluations[0:num_evals]


    def save(self, auto=False):
        if auto:
            fpath = AUTO_SAVE_FILEPATH
        else:
            fpath = MANUAL_SAVE_FILEPATH
        np.savez(fpath, edges=self.edges, status=self.status)




