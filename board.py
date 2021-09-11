import numpy as np
import os


from tile import Tile
from constants import *


class DorfBoard:
    """
    A class representing the board state of a Dorfromantik game
    """

    def __init__(self, save_file:str=None):
        """Loads a save file or initializes a new game board"""
        if save_file is None:
            self.initialize_new_board()
        else:
            self.load_board(save_file)


    @staticmethod
    def get_empty_edges(size:int) -> np.array:
        """Return an array representing edges of an empty board of a given size"""
        return np.ones([size, size, 6], dtype=np.uint8) * TileEdge.EMPTY


    @staticmethod
    def get_empty_status(size:int) -> np.array:
        """Return an array representing status of each tile of an empty board of a given size"""
        return np.ones([size, size], dtype=np.uint8) * TileStatus.EMPTY


    def initialize_new_board(self) -> None:
        """Creates a game board with only the origin tile"""
        # Create a board with empty tiles
        self.size = 8
        self.edges = self.get_empty_edges(self.size)
        self.status = self.get_empty_status(self.size)
        # Place the origin tile and update neighbors
        xy = self.get_origin_xy()
        self.edges[xy] = ORIGIN_TILE
        self.status[xy] = TileStatus.GOOD
        for xy_ in self.get_neighboring_tile_xys(xy):
            self.update_tile_status(xy_)


    def load_board(self, save_file:str) -> None:
        """Loads a game board from a npz save file"""
        assert os.path.exists(save_file)
        data = np.load(save_file)
        self.edges = data['edges']
        self.status = data['status']
        self.size = len(self.edges)


    def save_board(self, save_file:str) -> None:
        """Saves a game board to a npz save file"""
        np.savez(save_file, edges=self.edges, status=self.status)


    def get_origin_xy(self) -> tuple:
        """Returns the (x,y) coordinates of the origin tile"""
        return int(self.size/2 - 1), int(self.size/2 - 1)


    def is_in_grid(self, xy:tuple) -> bool:
        """Checks if the given coordinates lay within the bounds of the board"""
        x, y = xy
        return x >= 0 and y >= 0 and x < self.size and y < self.size


    def is_on_border(self, xy:tuple) -> bool:
        """Checks if the given coordinates lay on the border of the game board"""
        x, y = xy
        return x == 0 or y == 0 or x == self.size-1 or y == self.size-1


    def is_near_border(self, xy:tuple, distance_threshold:int=1) -> bool:
        """Checks if the given coordinates lay within some distance of the border of the game board"""
        if not self.is_in_grid(xy):
            return DorfBoardResult.ERROR
        x, y = xy
        k = distance_threshold
        return x <= k or y <= k or x >= self.size-1-k or y >= self.size-1-k


    def enlarge_board(self, pad_size:int=2) -> None:
        """Enlarges the game board by padding the existing board with empty tiles"""
        new_size = self.size + 2*pad_size
        new_edges = self.get_empty_edges(new_size)
        new_status = self.get_empty_status(new_size)
        x0 = y0 = pad_size
        x1 = y1 = pad_size + self.size
        new_edges[x0:x1,y0:y1] = self.edges
        new_status[x0:x1,y0:y1] = self.status
        self.edges = new_edges
        self.status = new_status
        self.size = new_size


    def enlarge_and_relocate(self, xy:tuple, pad_size:int=2) -> tuple:
        """Enlarges the game board and returns the new loacation of the given coordinates"""
        self.enlarge_board(pad_size)
        x, y = xy
        return x+pad_size, y+pad_size


    def get_edge(self, xy:tuple, edge_index:int) -> int:
        """Returns the edge at the given location"""
        x, y = xy
        return self.edges[x,y,edge_index]


    @staticmethod
    def get_neighboring_tile_xys(xy:tuple) -> list:
        """Returns a list of coordinates of all possible neighbors of a tile"""
        x, y = xy
        return [(x-1,y), (x,y-1), (x+1,y-1), (x+1,y), (x,y+1), (x-1,y+1)]


    def is_empty_tile(self, xy:tuple) -> bool:
        """Checks if the given tile location is empty"""
        return (self.edges[xy] == TileEdge.EMPTY).all()


    def get_opposite_edge_location(self, xy:tuple, edge_index:int) -> tuple:
        """Returns the tile location and edge index of the opposing edge"""
        x, y = xy
        if edge_index == 0:
            return (x-1, y), 3
        elif edge_index == 1:
            return (x, y-1), 4
        elif edge_index == 2:
            return (x+1, y-1), 5
        elif edge_index == 3:
            return (x+1, y), 0
        elif edge_index == 4:
            return (x, y+1), 1
        elif edge_index == 5:
            return (x-1, y+1), 2


    def is_legal_connection(self, xy:tuple, edge_index:int, tile:Tile) -> bool:
        """Checks if the connection along one edge would be legal if the tile is placed"""
        edge1 = tile.edges[edge_index]
        xy_, edge_index_ = self.get_opposite_edge_location(xy, edge_index)
        if not self.is_in_grid(xy_):
            return True
        edge2 = self.get_edge(xy_, edge_index_)
        return not (edge1, edge2) in ILLEGAL_CONNECTIONS and not (edge2, edge1) in ILLEGAL_CONNECTIONS

    
    def is_good_connection(self, xy:tuple, edge_index:int, tile:Tile) -> bool:
        """Checks if the connection along one edge would be good if the tile is placed"""
        if not self.is_legal_connection(xy, edge_index, tile):
            return False
        edge1 = tile.edges[edge_index]
        xy_, edge_index_ = self.get_opposite_edge_location(xy, edge_index)
        edge2 = self.get_edge(xy_, edge_index_)
        return (edge1, edge2) in GOOD_CONNECTIONS or (edge2, edge1) in GOOD_CONNECTIONS


    def get_valid_locations(self) -> list:
        """Returns a list of all valid tile locations"""
        return zip(*np.where(self.status==TileStatus.VALID))


    def is_legal_placement(self, xy:tuple, tile:Tile) -> bool:
        """Checks if the given tile placement is legal"""
        for edge_index in range(6):
            if not self.is_legal_connection(xy, edge_index, tile):
                return False
        return True

    def get_legal_placements(self, tile:Tile) -> list:
        """Returns a list of all legal placements of a tile"""
        rotations = tile.get_rotations()
        valid_locations = self.get_valid_locations()
        legal_placements = []
        for xy in valid_locations:
            for rotation in rotations:
                if self.is_legal_placement(xy, rotation):
                    legal_placements.append([xy, rotation])
        return legal_placements


    def get_connecting_edges(self, xy:tuple) -> Tile:
        """Returns a tile representing all opposite edges given a location"""
        connections = []
        for edge_index in range(6):
            xy_, opposite_edge_index = self.get_opposite_edge_location(xy, edge_index)
            if self.is_in_grid(xy_) and not self.is_empty_tile(xy_):
                connections.append(self.get_edge(xy_, opposite_edge_index))
            else:
                connections.append(TileEdge.EMPTY)
        return Tile(connections)


    def get_num_good_and_bad_connections(self, xy:tuple, tile:Tile=None) -> tuple:
        """Returns the number of good and bad connections a tile has or will have if it is placed"""
        if tile is None:
            tile = Tile(list(self.edges[xy]))    # Use existing edges
        neighbors = self.get_neighboring_tile_xys(xy)
        num_good_connections = num_bad_connections = 0
        for edge_index, xy_ in enumerate(neighbors):
            if self.is_in_grid(xy_) and not self.is_empty_tile(xy_):
                if self.is_good_connection(xy, edge_index, tile):
                    num_good_connections += 1
                else:
                    num_bad_connections += 1
        return num_good_connections, num_bad_connections


    def get_status_from_connections(self, xy:tuple) -> int:
        """Returns the status of a tile location from the connections with its neighbors"""
        if self.is_empty_tile(xy):
            for xy_ in self.get_neighboring_tile_xys(xy):
                if self.is_in_grid(xy_) and not self.is_empty_tile(xy_):
                        return TileStatus.VALID
            return TileStatus.EMPTY
        else:
            num_good_connections, num_bad_connections = self.get_num_good_and_bad_connections(xy)
            if num_good_connections == 6:
                return TileStatus.PERFECT
            elif num_bad_connections > 0:
                return TileStatus.IMPERFECT
            else:
                return TileStatus.GOOD


    def update_tile_status(self, xy:tuple) -> None:
        """Updates the status of a tile location"""
        self.status[xy] = self.get_status_from_connections(xy)


    def place_tile(self, xy:tuple, tile:Tile) -> int:
        """Attempts to place a tile at a given location"""
        if not self.is_in_grid(xy) or [xy, tile] not in self.get_legal_placements(tile):
            print("Illegal placement: {}: ".format(xy), tile)
            return DorfBoardResult.ERROR
        if self.is_near_border(xy, distance_threshold=1):
            xy = self.enlarge_and_relocate(xy)
        self.edges[xy] = tile.edges
        self.status[xy] = self.get_status_from_connections(xy)
        for xy_ in self.get_neighboring_tile_xys(xy):
            self.update_tile_status(xy_)
        return DorfBoardResult.OK


    def remove_tile(self, xy:tuple) -> int:
        """Attempts to remove a tile from a given location"""
        if not self.is_in_grid(xy) or self.is_empty_tile(xy):
            print("Illegal removal: {}: ".format(xy))
            return DorfBoardResult.ERROR
        self.edges[xy] = 6 * [TileEdge.EMPTY]
        self.status[xy] = self.get_status_from_connections(xy)
        for xy_ in self.get_neighboring_tile_xys(xy):
            self.update_tile_status(xy_)
        return DorfBoardResult.OK


    def evaluate_placement(self, xy:tuple, tile:Tile) -> dict:
        """Evaluates how well a tile fits in a given location"""
        for edge_index in range(6):
            if not self.is_legal_connection(xy, edge_index, tile):
                return DorfBoardResult.ILLEGAL
        # Compute the number of adjecent tiles that would become perfects
        num_perfects = 0
        num_meh_connections = 0
        neighbors = self.get_neighboring_tile_xys(xy)
        for edge_index, (xy_) in enumerate(neighbors):
            if not self.is_empty_tile(xy_):
                num_good_connections, num_bad_connections = self.get_num_good_and_bad_connections(xy_)
                is_good = self.is_good_connection(xy, edge_index, tile)
                if num_good_connections == 6-1 and is_good:
                    num_perfects += 1
                elif num_bad_connections > 0 and not is_good:
                    num_meh_connections += 1
        # Compute the number of good and bad connections
        num_good_connections, num_bad_connections = self.get_num_good_and_bad_connections(xy, tile)
        if num_good_connections == 6:
            num_perfects += 1
        # Give a proxy score
        score = 0.5*num_perfects + num_good_connections - (1.5*num_bad_connections - num_meh_connections)
        evaluation = {'score': score,
                      'perfect': num_perfects,
                      'good': num_good_connections,
                      'bad': num_bad_connections,
                      'meh': num_meh_connections}
        return evaluation


    def rank_all_placements(self, tile:Tile) -> list:
        """Ranks every legal placement of a tile based on the evaluations of those placements"""
        placements = self.get_legal_placements(tile)
        evaluations = []
        for placement in placements:
            xy_, tile_ = placement
            evaluation = self.evaluate_placement(xy_, tile_)
            if not evaluation == DorfBoardResult.ILLEGAL:
                evaluations.append((placement, evaluation))
        ranked_evaluations = sorted(evaluations, key=lambda x: x[1]['score'], reverse=True)
        return ranked_evaluations


    def get_hint(self, tile:Tile, top_k=None, threshold=None) -> list:
        """Returns the evaluations of the best placements of a tile"""
        ranked_evaluations = self.rank_all_placements(tile)
        num_evals = len(ranked_evaluations)
        if not threshold is None:
            above_threshold = [evaluation['score'] >= threshold for _, evaluation in ranked_evaluations]
            num_evals = above_threshold.index(False)
        if not top_k is None:
            num_evals = min(top_k, num_evals)
        return ranked_evaluations[0:num_evals]


    def get_num_tiles_with_status(self, status) -> int:
        """Returns the number of tiles on the board with the given status"""
        if isinstance(status, list):
            match = np.zeros(shape=self.status.shape, dtype=bool)
            for s in status:
                match |= (self.status ==  s)
        else:
            match = (self.status == status)
        return np.count_nonzero(match)




