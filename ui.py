import argparse

from tkinter import *
from board import *
from constants import *


"""
Canvas that displays the full game board
"""
class DorfBoardCanvas(Canvas):
    def __init__(self, master, board, tile_canvas, pix_width=1300, pix_height=1000, *args, **kwargs):
        Canvas.__init__(self, master, background='white', width=pix_width, height=pix_height, *args, **kwargs)
        
        self.board = board
        self.tile_canvas = tile_canvas
        self.pix_height = pix_height
        self.pix_width  = pix_width

        self.hint_hexes = []
        self.selected_hex = None
        
        self.set_coordinate_transform_parameters()
        self.set_hex_centers()


    def set_coordinate_transform_parameters(self):
        """
        Computes and stores pixel offsets and scaling parameters needed to center the hex grid on the canvas
        Offsets the coordinates if the displayed board is wider or taller than the canvas allows
        """
        # Compute the (x,y) locations in pre-transformed pixel space of all non-empty board tiles
        all_loc_x = []
        all_loc_y = []
        for x in range(self.board.size):
            for y in range(self.board.size):
                if not self.board.is_empty_tile(x, y):
                    loc_x = 1 + 2*x + y
                    loc_y = 1 + 1.5*y
                    all_loc_x.append(loc_x)
                    all_loc_y.append(loc_y)
        # Give pixel offsets that attempt to center the board in the frame
        margin = 4
        loc_x_min = min(all_loc_x) - margin
        loc_y_min = min(all_loc_y) - margin
        loc_x_max = max(all_loc_x) + margin
        loc_y_max = max(all_loc_y) + margin
        loc_x_diff = loc_x_max - loc_x_min
        loc_y_diff = loc_y_max - loc_y_min
        # Compute the scale for a hex tile
        # Add offset if board is too wide or too tall for canvas
        if self.pix_height/loc_y_diff > self.pix_width/loc_x_diff:
            hex_edge_len = 2/3**0.5 * self.pix_width / loc_x_diff
            loc_y_min -= (3**0.5/2 * loc_x_diff/self.pix_width*self.pix_height - loc_y_diff) / 2
        else:
            hex_edge_len = self.pix_height / loc_y_diff
            loc_x_min -= (2/3**0.5 * loc_y_diff/self.pix_height*self.pix_width - loc_x_diff) / 2
        # Store scaling and offset parameters
        self.y_scale = hex_edge_len
        self.x_scale = 3**0.5 / 2 * hex_edge_len
        self.pix_x_offset = self.x_scale * loc_x_min
        self.pix_y_offset = self.y_scale * loc_y_min
        return


    def get_hex_center_pix(self, x, y):
        """
        Returns the (x,y) coordinates in pixel space of a given hex position
        """
        pix_x = self.x_scale * (1 + 2*x + y) - self.pix_x_offset
        pix_y = self.y_scale * (1 + 1.5*y) - self.pix_y_offset
        return pix_x, pix_y


    def set_hex_centers(self):
        """
        Computes and stores the (x,y) coordinates in pixel space of all hex positions
        """
        self.centers = np.zeros((self.board.size, self.board.size, 2))
        for x in range(self.board.size):
            for y in range(self.board.size):
                self.centers[x,y] = self.get_hex_center_pix(x, y)
        return


    def draw_hexagon(self, x, y, border_color=TileOutlineColors.NORMAL, border_width=2, fill_color='blue'):
        """
        Draws a hexagon on the canvas given a hex position
        """
        pix_x, pix_y = self.get_hex_center_pix(x, y)
        # Compute the coordinates of hexagon vertices
        y_size = self.y_scale
        x_size = self.x_scale
        vertices = [(pix_x-x_size, pix_y+y_size/2),
                    (pix_x-x_size, pix_y-y_size/2),
                    (pix_x       , pix_y-y_size  ),
                    (pix_x+x_size, pix_y-y_size/2),
                    (pix_x+x_size, pix_y+y_size/2),
                    (pix_x       , pix_y+y_size  )]
        # Draw hexagon
        if fill_color != None:
            self.create_polygon(vertices[0],
                                vertices[1],
                                vertices[2],
                                vertices[3],
                                vertices[4],
                                vertices[5],
                                fill=fill_color)
        # Draw outline
        if border_color != None:
            for i in range(len(vertices)):
                self.create_line(vertices[i], vertices[(i+1)%len(vertices)], fill=border_color, width=border_width)


    def draw_board(self):
        """
        Draws the full game board on the canvas
        """
        for x, row in enumerate(self.board.status):
            for y, status in enumerate(row):
                if status == TileStatus.EMPTY:
                    # self.draw_hexagon(x, y, fill_color=None, border_color='purple')
                    continue
                elif status == TileStatus.VALID and (x,y) in self.hint_hexes:
                    fill_color = TileStatusColors.HINT
                else:
                    fill_color = get_color_from_status(status)
                self.draw_hexagon(x, y, fill_color=fill_color)


    @staticmethod
    def euclidian_distance(x1, y1, x2, y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5


    def get_xy_from_pix(self, pix_x, pix_y):
        """
        Returns the (x,y) position of the hex belonging to the given pixel coordinates
        Approximates the hexagon as a circle with the inner radius of the hexagon
        Gives a 5 percent margin of error to avoid confusing between neighboring hexes
        """
        for x in range(self.board.size):
            for y in range(self.board.size):
                center = self.centers[x,y]
                if self.euclidian_distance(pix_x, pix_y, center[0], center[1]) < self.x_scale * 0.95:
                    return x, y
        return None


    def on_click(self, event):
        """
        Controls behavior of the canvas on a left mouse click
        Used for highlighting a selected hex
        Sets the location of the selected hex and a tile that represents the surrounding connect
        """
        # Remove highlight from previously selected hex tile
        if self.selected_hex:
            x, y = self.selected_hex
            self.draw_hexagon(x, y, border_color=TileOutlineColors.NORMAL, fill_color=None)
            self.selected_hex = None
        # Get location of newly selected hex tile (if any)
        loc = self.get_xy_from_pix(event.x, event.y)
        if loc == None:
            return
        # Highlight newly selected tile if not empty
        x, y = loc
        if self.board.status[x,y] != TileStatus.EMPTY:
            self.selected_hex = loc
            self.draw_hexagon(x, y, border_color=TileOutlineColors.SELECTED, fill_color=None)
        # Set the connecting edges in the slice canvas
        if self.board.status[x,y] == TileStatus.VALID:
            connections = self.board.get_connecting_edges(x, y)
        else:
            connections = None    
        self.tile_canvas.set_connections(connections)


    def set_hint(self, hints):
        """
        Set which tiles to highlight given a hint
        """
        self.hint_hexes = []
        if hints is None:
            return
        for (x, y, _), _ in hints:
            self.hint_hexes.append((x,y))


class HexTileCanvas(Canvas):
    def __init__(self, master, scale, *args, **kwargs):
        self.x_scale = (scale**2 - (scale/2.0)**2)**0.5     # hexagon width
        self.y_scale = scale                                # half hexagon height
        self.pix_height = 3 * self.y_scale
        self.pix_width  = 3 * self.x_scale
        
        Canvas.__init__(self, master, background='white', width=self.pix_width, height=self.pix_height, *args, **kwargs)
        
        self.selected_slice = None
        self.edges = 6 * [None]
        self.select_slice(0)
        self.set_tile(6 * [TileEdge.GRASS])


    def get_tile(self):
        return self.edges


    def get_triangle_vertices(self, index, scale=1):
        y_size = self.y_scale
        x_size = self.x_scale
        x_offset = 1/2*self.pix_width - x_size
        y_offset = 1/2*self.pix_height - y_size
        origin = [(x_size, y_size)] # origin
        outside_vertices = [((1-scale)*x_size, (2+scale)/2*y_size),
                            ((1-scale)*x_size, (2-scale)/2*y_size),
                            (1*x_size,         (1-scale)*y_size),
                            ((1+scale)*x_size, (2-scale)/2*y_size),
                            ((1+scale)*x_size, (2+scale)/2*y_size),
                            (1*x_size,         (1+scale)*y_size)]
        if index == 5:
            vertices = origin + [outside_vertices[5], outside_vertices[0]]
        else:
            vertices = origin + outside_vertices[index:index+2]
        vertices = [(x+x_offset, y+y_offset) for (x,y) in vertices]
        return vertices


    def draw_slice(self, index, border_color='black', border_width=2, fill_color='blue'):
        vertices = self.get_triangle_vertices(index)
        if fill_color != None:
            self.create_polygon(vertices[0], vertices[1], vertices[2], fill=fill_color)
        if border_color != None:
            for i in range(len(vertices)):
                self.create_line(vertices[i], vertices[(i+1)%len(vertices)], fill=border_color, width=border_width)


    def draw_connection(self, index, border_color=None, border_width=2, fill_color='blue'):
        _, a, b = self.get_triangle_vertices(index, scale=1.1)
        _, d, c = self.get_triangle_vertices(index, scale=1.2)
        if fill_color != None:
            self.create_polygon(a, b, c, d, fill=fill_color)
        if border_color != None:
            self.create_line(a, b, fill=border_color, width=border_width)
            self.create_line(b, c, fill=border_color, width=border_width)
            self.create_line(c, d, fill=border_color, width=border_width)
            self.create_line(d, a, fill=border_color, width=border_width)


    def set_edge(self, index, feature):
        self.edges[index] = feature
        if self.selected_slice == index or self.selected_slice == -1:
            border_color = TileOutlineColors.SELECTED
        else:
            border_color = TileOutlineColors.NORMAL
        self.draw_slice(index, fill_color=get_color_from_feature(feature), border_color=border_color)


    def set_tile(self, tile):
        for index, feature in enumerate(tile):
            self.set_edge(index, feature)
        self.draw_slice(self.selected_slice, border_color=TileOutlineColors.SELECTED, fill_color=None)


    def set_connections(self, connections):
        for index in range(6):
            self.draw_connection(index, fill_color=TileFeatureColors.EMPTY, border_color=TileOutlineColors.EMPTY)
        if not connections:
            return
        for index, feature in enumerate(connections):
            if feature != TileEdge.EMPTY:
                self.draw_connection(index, fill_color=get_color_from_feature(feature), border_color=TileOutlineColors.NORMAL)


    def select_slice(self, index):
        # remove any existing highlights
        for i in range(6):
            self.draw_slice(i, border_color=TileOutlineColors.NORMAL, fill_color=None)
        # highlight newly selected slice
        self.draw_slice(index, border_color=TileOutlineColors.SELECTED, fill_color=None)
        self.selected_slice = index

    def select_all(self):
        print("Selected slice: ALL")
        self.selected_slice = -1
        for i in range(6):
            self.draw_slice(i, border_color=TileOutlineColors.SELECTED, fill_color=None)

    def set_selected_edge(self, feature, auto_advance=True):
        if self.selected_slice == -1:
            for i in range(6):
                self.set_edge(i, feature)
        else:
            self.set_edge(self.selected_slice, feature)
            if auto_advance:
                self.select_slice((self.selected_slice+1)%6)


    def rotate(self, reverse=False):
        if reverse:
            new_edges = self.edges[1:] + self.edges[:1]
            new_selected_slice = (self.selected_slice - 1) % 6
        else:
            new_edges = self.edges[5:] + self.edges[:5]
            new_selected_slice = (self.selected_slice + 1) % 6
        for index, feature in enumerate(new_edges):
            self.set_edge(index, feature)
        if self.selected_slice != -1:
            self.select_slice(new_selected_slice)


    @staticmethod
    def half_plane_test(p1, p2, p3):
         return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])


    def is_inside_triangle(self, point, vertices):
        d1 = self.half_plane_test(point, vertices[0], vertices[1])
        d2 = self.half_plane_test(point, vertices[1], vertices[2])
        d3 = self.half_plane_test(point, vertices[2], vertices[0])
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (has_neg and has_pos)

    def get_index_from_pix(self, x, y):
        all_triangle_vertices = [self.get_triangle_vertices(i) for i in range(6)]
        for i, vertices in enumerate(all_triangle_vertices):
            if self.is_inside_triangle((x,y), vertices):
                return i
        return None
        

    def on_click(self, event):
        # Get location of newly selected hex tile (if any)
        index = self.get_index_from_pix(event.x, event.y)
        print("Selected slice: ", index)
        if index == None:
            return
        # Highlight newly selected tile if valid
        self.select_slice(index)



class App(Tk):
    def __init__(self, from_npz, pix_height, pix_width, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        board = DorfBoard(from_npz=from_npz)

        self.boardview_frame = Frame(self, background="#FFF0C1", bd=1, relief="sunken")
        self.tile_frame = Frame(self, background="#D2E2FB", bd=1, relief="sunken")
        self.control_frame = Frame(self, background="#CCE4CA", bd=1, relief="sunken")
        self.textlog_frame = Frame(self, background="#F5C2C1", bd=1, relief="sunken")

        self.boardview_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=2, pady=2)
        self.tile_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.control_frame.grid(row=1, column=1, rowspan=1, sticky="nsew", padx=2, pady=2)
        self.textlog_frame.grid(row=1, column=2, rowspan=1, sticky="nsew", padx=2, pady=2)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=100000)

        self.tile_canvas = HexTileCanvas(self.tile_frame, scale=100)
        self.tile_canvas.bind('<Button-1>', self.tile_canvas.on_click)
        self.tile_canvas.grid(row=0, column=0, padx=5, pady=5)
        self.tile_canvas.grid(row=0, column=0)

        self.board_canvas = DorfBoardCanvas(self.boardview_frame, board=board, tile_canvas=self.tile_canvas)
        self.board_canvas.bind('<Button-1>', self.board_canvas.on_click)
        self.board_canvas.grid(row=0, column=0, padx=5, pady=5)
        self.board_canvas.draw_board()

        board_controls = []
        frame = self.control_frame
        board_controls.append(Button(frame, text="Place",  command=self.place_tile))
        board_controls.append(Button(frame, text="Hint",   command=self.display_hint))
        board_controls.append(Button(frame, text="Sample", command=self.sample_tile))
        board_controls.append(Button(frame, text="Remove", command=self.remove_tile))
        board_controls.append(Button(frame, text="Undo",   command=self.undo))
        board_controls.append(Button(frame, text="Stats",  command=self.display_stats))
        board_controls.append(Button(frame, text="Save",   command=self.manual_save))
        board_controls.append(Button(frame, text="Quit",   command=self.correct_quit))
        for i, button in enumerate(board_controls):
            button.grid(row=i, column=0)

        tile_controls = []
        frame = self.control_frame
        fn = self.tile_canvas.set_selected_edge
        tile_controls.append(Button(frame, text="ALL", command=self.tile_canvas.select_all))
        tile_controls.append(Button(frame, text="Grass",   command=lambda: fn(TileEdge.GRASS)))
        tile_controls.append(Button(frame, text="Trees",   command=lambda: fn(TileEdge.TREES)))
        tile_controls.append(Button(frame, text="House",   command=lambda: fn(TileEdge.HOUSE)))
        tile_controls.append(Button(frame, text="Crops",   command=lambda: fn(TileEdge.CROPS)))
        tile_controls.append(Button(frame, text="River",   command=lambda: fn(TileEdge.RIVER)))
        tile_controls.append(Button(frame, text="Train",   command=lambda: fn(TileEdge.TRAIN)))
        tile_controls.append(Button(frame, text="Water",   command=lambda: fn(TileEdge.WATER)))
        tile_controls.append(Button(frame, text="Station", command=lambda: fn(TileEdge.STATION)))
        for i, button in enumerate(tile_controls):
            button.grid(row=i, column=1)
        
        rotate_controls = []
        frame = self.control_frame
        rotate_controls.append(Button(frame, text="Rotate CW",  command=lambda: self.tile_canvas.rotate(reverse=False)))
        rotate_controls.append(Button(frame, text="Rotate CCW", command=lambda: self.tile_canvas.rotate(reverse=True)))
        for i, button in enumerate(rotate_controls):
            button.grid(row=i, column=2)

        self.log = Label(self.textlog_frame, text="")
        self.log.pack()

        self.can_undo = False


    def manual_save(self):
        self.grid.board.save(to_npz=MANUAL_SAVE_FILEPATH)
        self.log.config(text="Saved board state")


    def undo(self):
        if self.can_undo:
            board = DorfBoard(from_npz=AUTO_SAVE_FILEPATH)
            self.board_canvas = DorfBoardCanvas(self.boardview_frame, board=board, tile_canvas=self.tile_canvas)
            self.board_canvas.bind('<Button-1>', self.board_canvas.on_click)
            self.board_canvas.grid(row=0, column=0, padx=5, pady=5)
            self.board_canvas.draw_board()
            self.log.config(text="Removed last placed tile")
            self.can_undo = False
        else:
            self.log.config(text="ERROR: Unable to undo move")


    def place_tile(self):
        x, y = self.board_canvas.selected_hex
        if self.board_canvas.board.status[x,y] != TileStatus.VALID:
            self.log.config(text="ERROR: Illegal tile placement at ({},{})".format(x, y))
            return
        self.board_canvas.board.save(to_npz=AUTO_SAVE_FILEPATH)
        self.can_undo = True
        tile = self.tile_canvas.get_tile()
        self.board_canvas.board.place_tile(x, y, tile)
        self.board_canvas.set_coordinate_transform_parameters()
        self.board_canvas.set_hex_centers()
        self.board_canvas.delete('all')
        self.board_canvas.selected_hex = None
        self.board_canvas.set_hint(None)
        self.board_canvas.draw_board()
        self.tile_canvas.set_tile(6 * [TileEdge.GRASS])
        self.tile_canvas.set_connections(None)
        self.log.config(text="Placed tile at ({},{})".format(x, y))


    def remove_tile(self):
        if self.board_canvas.selected_hex == None:
            self.log.config(text="ERROR: No selected hex to remove")
            return
        x, y = self.board_canvas.selected_hex
        if self.board_canvas.board.status[x,y] == TileStatus.VALID:
            self.log.config(text="ERROR: Illegal tile removal at ({},{})".format(x, y))
            return
        self.board_canvas.board.save(to_npz=AUTO_SAVE_FILEPATH)
        self.can_undo = True
        self.board_canvas.board.remove_tile(x, y)
        self.board_canvas.set_hint(None)
        self.board_canvas.draw_board()
        self.log.config(text="Removed tile at ({},{})".format(x, y))


    def sample_tile(self):
        if self.board_canvas.selected_hex == None:
            self.log.config(text="ERROR: No selected hex to sample")
            return
        x, y = self.board_canvas.selected_hex
        if self.board_canvas.board.status[x,y] == TileStatus.VALID:
            self.log.config(text="ERROR: Illegal tile sample at ({},{})".format(x, y))
            return
        tile = self.board_canvas.board.edges[x,y]
        self.tile_canvas.set_tile(tile)
        self.log.config(text="Tile sampled at ({},{})".format(x, y))


    def display_hint(self):
        tile = self.tile_canvas.get_tile()
        hint = self.board_canvas.board.get_hint(tile, threshold=2, top_k=10)
        if not hint:
            hint = self.board_canvas.board.get_hint(tile, top_k=5)
        text_hint = ["x={}, y={}, {} of {} good connections with {} perfects (score = {}), {}".format(
                            x, y, evaluation['good'], evaluation['good'] + evaluation['bad'], evaluation['perfect'], evaluation['score']) \
                            for (x, y, _), evaluation in hint]
        text_hint = "\n".join(text_hint)
        self.log.config(text=text_hint)
        self.board_canvas.set_hint(hint)
        self.board_canvas.draw_board()


    def display_stats(self):
        text = "{} tiles placed\n".format(self.board_canvas.board.get_num_tiles_with_status([TileStatus.GOOD, TileStatus.PERFECT, TileStatus.IMPERFECT]) - 1)
        text += "{} perfect tiles\n".format(self.board_canvas.board.get_num_tiles_with_status(TileStatus.PERFECT))
        text += "{} bad tiles\n".format(self.board_canvas.board.get_num_tiles_with_status(TileStatus.IMPERFECT))
        text += "{} legal tile locations\n".format(self.board_canvas.board.get_num_tiles_with_status(TileStatus.VALID))
        self.log.config(text=text)


    def correct_quit(self):
        self.destroy()
        self.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--load', '-l', action='store_true', help="Load data from last manual save")
    parser.add_argument('--height', '-y', type=int, help="Pixel height of the board display")
    parser.add_argument('--width', '-x', type=int, help="Pixel width of the board display")
    args = parser.parse_args()

    from_npz = MANUAL_SAVE_FILEPATH if args.load else None

    app = App(from_npz=from_npz, pix_height=args.height, pix_width=args.width)
    app.mainloop()