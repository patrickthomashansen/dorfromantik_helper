import argparse

from tkinter import *
from board import *
from constants import *


class HexaGridCanvas(Canvas):
    def __init__(self, master, board, slices, pix_width=1300, pix_height=1000, *args, **kwargs):
        Canvas.__init__(self, master, background='white', width=pix_width, height=pix_height, *args, **kwargs)
        
        self.board = board
        self.slices = slices
        
        self.pix_height = pix_height
        self.pix_width  = pix_width

        self.tile_loc_borders = self.get_tile_location_borders()
        self.loc_x_min = self.tile_loc_borders[0]
        self.loc_y_min = self.tile_loc_borders[1]
        self.loc_x_max = self.tile_loc_borders[2]
        self.loc_y_max = self.tile_loc_borders[3]
        self.loc_x_diff = self.loc_x_max - self.loc_x_min
        self.loc_y_diff = self.loc_y_max - self.loc_y_min


        if pix_height/self.loc_y_diff > pix_width/self.loc_x_diff:
            edge_len = 2/3**0.5*pix_width/self.loc_x_diff
        else:
            edge_len = pix_height/self.loc_y_diff
        self.y_scale = edge_len
        self.x_scale = 3**0.5/2*edge_len
        
        self.hint_hexes = []
        self.selected_hex = None
        self.click_radius = self.x_scale * 0.95             # 5 percent margin of error on hex click
        # Compute all tile locations
        self.centers = np.zeros((board.size, board.size, 2))
        for x in range(board.size):
            for y in range(board.size):
                self.centers[x,y] = self.get_hex_center_pix(x, y)


    def get_tile_location_borders(self, margin=4):
        # Give pixel offsets that attempt to center the board in the frame
        all_loc_x = []
        all_loc_y = []
        for x in range(self.board.size):
            for y in range(self.board.size):
                if not self.board.is_empty_tile(x, y):
                    loc_x = 1 + 2*x + y
                    loc_y = 1 + 1.5*y
                    all_loc_x.append(loc_x)
                    all_loc_y.append(loc_y)
        loc_x_min = min(all_loc_x) - margin
        loc_y_min = min(all_loc_y) - margin
        loc_x_max = max(all_loc_x) + margin
        loc_y_max = max(all_loc_y) + margin
        print(loc_x_min, loc_y_min, loc_x_max, loc_y_max)
        return loc_x_min, loc_y_min, loc_x_max, loc_y_max 


    def get_hex_center_pix(self, x, y):
        pix_x = self.x_scale * ((1 + 2*x + y) - self.loc_x_min)
        pix_y = self.y_scale * ((1 + 1.5*y) - self.loc_y_min)
        # Center the board in the frame
        if self.pix_height/self.loc_y_diff > self.pix_width/self.loc_x_diff:
            pix_y += self.y_scale * (3**0.5/2*self.loc_x_diff/self.pix_width*self.pix_height - self.loc_y_diff) / 2
        else:
            pix_x += self.x_scale * (2/3**0.5*self.loc_y_diff/self.pix_height*self.pix_width - self.loc_x_diff) / 2
        return pix_x, pix_y


    def draw_hexagon(self, x, y, border_color=TileOutlineColors.NORMAL, border_width=2, fill_color='blue'):
        pix_x, pix_y = self.get_hex_center_pix(x, y)
        y_size = self.y_scale
        x_size = self.x_scale
        vertices = [(pix_x-x_size, pix_y+y_size/2),
                    (pix_x-x_size, pix_y-y_size/2),
                    (pix_x       , pix_y-y_size  ),
                    (pix_x+x_size, pix_y-y_size/2),
                    (pix_x+x_size, pix_y+y_size/2),
                    (pix_x       , pix_y+y_size  )]

        if fill_color != None:
            self.create_polygon(vertices[0],
                                vertices[1],
                                vertices[2],
                                vertices[3],
                                vertices[4],
                                vertices[5],
                                fill=fill_color)

        if border_color != None:
            for i in range(len(vertices)):
                self.create_line(vertices[i], vertices[(i+1)%len(vertices)], fill=border_color, width=border_width)


    def draw_board(self):
        for x, row in enumerate(self.board.status):
            for y, ele in enumerate(row):
                if ele == TileStatus.EMPTY:
                    # self.draw_hexagon(x, y, fill_color=None, border_color='gray')
                    continue
                elif ele == TileStatus.VALID and (x,y) in self.hint_hexes:
                    fill_color = TileStatusColors.HINT
                else:
                    fill_color = get_color_from_status(ele)
                self.draw_hexagon(x, y, fill_color=fill_color)


    @staticmethod
    def euclidian_distance(x1, y1, x2, y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5


    def get_xy_from_pix(self, pix_x, pix_y):
        for x in range(self.board.height):
            for y in range(self.board.width):
                center = self.centers[x,y]
                if self.euclidian_distance(pix_x, pix_y, center[0], center[1]) < self.click_radius:
                    return x, y
        return None


    def on_click(self, event):
        # Remove highlight from previously selected hex tile
        if self.selected_hex:
            x, y = self.selected_hex
            self.draw_hexagon(x, y, border_color=TileOutlineColors.NORMAL, fill_color=None)
            self.selected_hex = None

        # Get location of newly selected hex tile (if any)
        loc = self.get_xy_from_pix(event.x, event.y)
        if loc == None:
            print("Selected hex: ", loc)
            return

        # Highlight newly selected tile if not empty
        x, y = loc
        if self.board.status[x,y] != TileStatus.EMPTY:
            print("Selected hex: ", loc)
            self.selected_hex = loc
            self.draw_hexagon(x, y, border_color=TileOutlineColors.SELECTED, fill_color=None)
        else:
            print("Selected hex: ", None)

        if self.board.status[x,y] == TileStatus.VALID:
            connections = self.board.get_connecting_edges(x, y)
        else:
            connections = None    
        self.slices.set_connections(connections)


    def set_hint(self, hints):
        self.hint_hexes = []
        if hints is None:
            return
        for (x, y, _), _ in hints:
            self.hint_hexes.append((x,y))



class HexaSliceCanvas(Canvas):
    def __init__(self, master, scale, *args, **kwargs):
        self.x_scale = (scale**2 - (scale/2.0)**2)**0.5     # hexagon width
        self.y_scale = scale                                # half hexagon height
        self.pix_height = 3 * self.y_scale
        self.pix_width  = 3 * self.x_scale
        
        Canvas.__init__(self, master, background='white', width=self.pix_width, height=self.pix_height, *args, **kwargs)
        
        self.selected_slice = None
        self.edges = NUM_HEXA_EDGES * [None]
        self.select_slice(0)
        self.set_tile(NUM_HEXA_EDGES * [TileEdge.GRASS])


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
        for index in range(NUM_HEXA_EDGES):
            self.draw_connection(index, fill_color=TileFeatureColors.EMPTY, border_color=TileOutlineColors.EMPTY)
        if not connections:
            return
        for index, feature in enumerate(connections):
            if feature != TileEdge.EMPTY:
                self.draw_connection(index, fill_color=get_color_from_feature(feature), border_color=TileOutlineColors.NORMAL)


    def select_slice(self, index):
        # remove any existing highlights
        for i in range(NUM_HEXA_EDGES):
            self.draw_slice(i, border_color=TileOutlineColors.NORMAL, fill_color=None)
        # highlight newly selected slice
        self.draw_slice(index, border_color=TileOutlineColors.SELECTED, fill_color=None)
        self.selected_slice = index

    def select_all(self):
        print("Selected slice: ALL")
        self.selected_slice = -1
        for i in range(NUM_HEXA_EDGES):
            self.draw_slice(i, border_color=TileOutlineColors.SELECTED, fill_color=None)

    def set_selected_edge(self, feature, auto_advance=True):
        if self.selected_slice == -1:
            for i in range(NUM_HEXA_EDGES):
                self.set_edge(i, feature)
        else:
            self.set_edge(self.selected_slice, feature)
            if auto_advance:
                self.select_slice((self.selected_slice+1)%NUM_HEXA_EDGES)


    def rotate(self, reverse=False):
        if reverse:
            new_edges = self.edges[1:] + self.edges[:1]
            new_selected_slice = (self.selected_slice - 1) % NUM_HEXA_EDGES
        else:
            new_edges = self.edges[5:] + self.edges[:5]
            new_selected_slice = (self.selected_slice + 1) % NUM_HEXA_EDGES
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
        all_triangle_vertices = [self.get_triangle_vertices(i) for i in range(NUM_HEXA_EDGES)]
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
    def __init__(self, from_npz, height, width *args, **kwargs):
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

        slices = HexaSliceCanvas(self.tile_frame, scale=100)
        self.slices = slices
        slices.bind('<Button-1>', slices.on_click)
        slices.grid(row=0, column=0, padx=5, pady=5)
        slices.grid(row=0, column=0)

        grid = HexaGridCanvas(boardview_frame, board=board, slices=slices)
        self.grid = grid
        grid.bind('<Button-1>', grid.on_click)
        grid.grid(row=0, column=0, padx=5, pady=5)
        grid.draw_board()

        grid_buttons = []
        f = self. control_frame
        grid_buttons.append(Button(f, text="Place",  command=self.place_tile))
        grid_buttons.append(Button(f, text="Hint",   command=self.display_hint))
        grid_buttons.append(Button(f, text="Sample", command=self.sample_tile))
        grid_buttons.append(Button(f, text="Remove", command=self.remove_tile))
        grid_buttons.append(Button(f, text="Undo",   command=self.undo))
        grid_buttons.append(Button(f, text="Stats",  command=self.display_stats))
        grid_buttons.append(Button(f, text="Save",   command=self.manual_save))
        grid_buttons.append(Button(f, text="Quit",   command=self.correct_quit))
        for i, button in enumerate(grid_buttons):
            button.grid(row=i, column=0)

        slices_buttons = []
        f = self.control_frame
        slices_buttons.append(Button(f, text="ALL", command=slices.select_all))
        slices_buttons.append(Button(f, text="Grass",   command=lambda: slices.set_selected_edge(TileEdge.GRASS)))
        slices_buttons.append(Button(f, text="Trees",   command=lambda: slices.set_selected_edge(TileEdge.TREES)))
        slices_buttons.append(Button(f, text="House",   command=lambda: slices.set_selected_edge(TileEdge.HOUSE)))
        slices_buttons.append(Button(f, text="Crops",   command=lambda: slices.set_selected_edge(TileEdge.CROPS)))
        slices_buttons.append(Button(f, text="River",   command=lambda: slices.set_selected_edge(TileEdge.RIVER)))
        slices_buttons.append(Button(f, text="Train",   command=lambda: slices.set_selected_edge(TileEdge.TRAIN)))
        slices_buttons.append(Button(f, text="Water",   command=lambda: slices.set_selected_edge(TileEdge.WATER)))
        slices_buttons.append(Button(f, text="Station", command=lambda: slices.set_selected_edge(TileEdge.STATION)))
        for i, button in enumerate(slices_buttons):
            button.grid(row=i, column=1)
        
        rotate_buttons = []
        f = self.control_frame
        rotate_buttons.append(Button(f, text="Rotate CW",  command=lambda: slices.rotate(reverse=False)))
        rotate_buttons.append(Button(f, text="Rotate CCW", command=lambda: slices.rotate(reverse=True)))
        for i, button in enumerate(rotate_buttons):
            button.grid(row=i, column=2)

        self.log = Label(textlog_frame, text="")
        self.log.pack()

        self.can_undo = False


    def manual_save(self):
        self.grid.board.save(to_npz=MANUAL_SAVE_FILEPATH)
        self.log.config(text="Saved board state")


    def undo(self):
        if self.can_undo:
            board = DorfBoard(from_npz=AUTO_SAVE_FILEPATH)
            self.grid = HexaGridCanvas(self.boardview_frame, board=board, slices=self.slices)
            self.grid.bind('<Button-1>', self.grid.on_click)
            self.grid.grid(row=0, column=0, padx=5, pady=5)
            self.grid.draw_board()
            self.log.config(text="Removed last placed tile")
            self.can_undo = False
        else:
            self.log.config(text="ERROR: Unable to undo move")


    def place_tile(self):
        x, y = self.grid.selected_hex
        if self.grid.board.status[x,y] != TileStatus.VALID:
            self.log.config(text="ERROR: Illegal tile placement at ({},{})".format(x, y))
            return
        self.grid.board.save(to_npz=AUTO_SAVE_FILEPATH)
        self.can_undo = True
        tile = self.slices.get_tile()
        self.grid.board.place_tile(x, y, tile)
        if self.grid.tile_loc_borders != self.grid.get_tile_location_borders():
            # self.boardview_frame.grid_forget()
            self.grid = HexaGridCanvas(self.boardview_frame, board=self.grid.board, slices=self.slices)
            self.grid.bind('<Button-1>', self.grid.on_click)
            self.grid.grid(row=0, column=0, padx=5, pady=5)
        self.grid.selected_hex = None
        self.grid.set_hint(None)
        self.grid.draw_board()
        self.slices.set_tile(NUM_HEXA_EDGES * [TileEdge.GRASS])
        self.slices.set_connections(None)
        self.log.config(text="Placed tile at ({},{})".format(x, y))


    def remove_tile(self):
        if self.grid.selected_hex == None:
            self.log.config(text="ERROR: No selected hex to remove")
            return
        x, y = self.grid.selected_hex
        if self.grid.board.status[x,y] == TileStatus.VALID:
            self.log.config(text="ERROR: Illegal tile removal at ({},{})".format(x, y))
            return
        self.grid.board.save(to_npz=AUTO_SAVE_FILEPATH)
        self.can_undo = True
        self.grid.board.remove_tile(x, y)
        self.grid.set_hint(None)
        self.grid.draw_board()
        self.log.config(text="Removed tile at ({},{})".format(x, y))


    def sample_tile(self):
        if self.grid.selected_hex == None:
            self.log.config(text="ERROR: No selected hex to sample")
            return
        x, y = self.grid.selected_hex
        if self.grid.board.status[x,y] == TileStatus.VALID:
            self.log.config(text="ERROR: Illegal tile sample at ({},{})".format(x, y))
            return
        tile = self.grid.board.edges[x,y]
        self.slices.set_tile(tile)
        self.log.config(text="Tile sampled at ({},{})".format(x, y))


    def display_hint(self):
        tile = self.slices.get_tile()
        hint = self.grid.board.get_hint(tile, threshold=2, top_k=10)
        if not hint:
            hint = self.grid.board.get_hint(tile, top_k=5)
        text_hint = ["x={}, y={}, {} of {} good connections with {} perfects".format(
                            x, y, num_good_connections, num_good_connections + num_bad_connections, num_perfects) \
                            for (x, y, _), (_, num_perfects, num_good_connections, num_bad_connections) in hint]
        text_hint = "\n".join(text_hint)
        self.log.config(text=text_hint)
        self.grid.set_hint(hint)
        self.grid.draw_board()


    def display_stats(self):
        text = "{} tiles placed\n".format(self.grid.board.get_num_tiles() - 1)
        text += "{} perfect tiles\n".format(self.grid.board.get_num_perfects())
        self.log.config(text=text)


    def correct_quit(self):
        self.destroy()
        self.quit()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--load', '-l', action='store_true', help="Load data from last manual save")
    parser.add_argument('--height', '-h', type=int, help="Pixel height of the hex grid display")
    parser.add_argument('--width', '-w', type=int, help="Pixel width of the hex grid display")
    args = parser.parse_args()

    from_npz = MANUAL_SAVE_FILEPATH if args.load else None

    app = App(from_npz=from_npz, height=args.height, width=args.width)
    app.mainloop()