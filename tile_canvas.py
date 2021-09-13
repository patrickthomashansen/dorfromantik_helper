from tkinter import Canvas

from hex_tile import HexTile

from constants import *


class HexTileCanvas(Canvas):
    def __init__(self, master, width, height, *args, **kwargs):
        size = height
        scale = size / 3
        self.x_scale = (scale**2 - (scale/2.0)**2)**0.5     # hexagon width
        self.y_scale = scale                                # half hexagon height
        self.pix_height = 3 * self.y_scale
        self.pix_width  = 3 * self.x_scale
        
        Canvas.__init__(self, master, background='white', width=self.pix_width, height=self.pix_height, *args, **kwargs)
        
        self.selected_slice = None
        self.tile = HexTile(6 * [TileEdge.EMPTY])
        self.select_slice(0)
        self.set_tile(6 * [TileEdge.GRASS])


    def get_tile(self):
        return self.tile


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
        self.tile.edges[index] = feature
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
            new_edges = self.tile.edges[1:] + self.tile.edges[:1]
            new_selected_slice = (self.selected_slice - 1) % 6
        else:
            new_edges = self.tile.edges[5:] + self.tile.edges[:5]
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
