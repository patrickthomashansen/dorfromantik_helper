import argparse
import os
from typing import Optional

from tkinter import Tk, Frame, Button, Label

from board import DorfBoard
from board_canvas import DorfBoardCanvas
from tile_canvas import HexTileCanvas

from constants import *


class DorfHelperApp(Tk):
    def __init__(self, save_file, width, height, layout, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        board = DorfBoard(save_file=save_file)

        self.boardview_frame = Frame(self, background=Colors.PASTEL_YELLOW, bd=1, relief="sunken")
        self.tile_frame = Frame(self, background=Colors.PASTEL_BLUE, bd=1, relief="sunken")
        self.control_frame = Frame(self, background=Colors.PASTEL_GREEN, bd=1, relief="sunken")
        self.textlog_frame = Frame(self, background=Colors.PASTEL_RED, bd=1, relief="sunken")

        if layout == 0:
            board_canvas_width = width
            board_canvas_height = int(3/4*height)
            tile_canvas_width = tile_canvas_height = int(1/4*height)
            self.boardview_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=2, pady=2)
            self.tile_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
            self.control_frame.grid(row=1, column=1, rowspan=1, sticky="nsew", padx=2, pady=2)
            self.textlog_frame.grid(row=1, column=2, rowspan=1, sticky="nsew", padx=2, pady=2)
            self.columnconfigure(2, minsize=500)
        elif layout == 1:
            board_canvas_width = int(3/4*width)
            board_canvas_height = height
            tile_canvas_width = tile_canvas_height = int(1/4*width)
            self.boardview_frame.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=2, pady=2)
            self.tile_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            self.control_frame.grid(row=1, column=0, rowspan=1, sticky="nsew", padx=2, pady=2)
            self.textlog_frame.grid(row=2, column=0, rowspan=1, sticky="nsew", padx=2, pady=2)
            self.columnconfigure(0, minsize=500)
            self.rowconfigure(2, minsize=200)

        self.tile_canvas = HexTileCanvas(self.tile_frame, width=tile_canvas_width, height=tile_canvas_height)
        self.tile_canvas.bind('<Button-1>', self.tile_canvas.on_click)
        self.tile_canvas.grid(row=0, column=0, padx=5, pady=5)
        self.tile_canvas.grid(row=0, column=0)

        self.board_canvas = DorfBoardCanvas(self.boardview_frame, board=board, tile_canvas=self.tile_canvas, width=board_canvas_width, height=board_canvas_height)
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
        self.board_canvas.board.save_board(save_file=MANUAL_SAVE_FILEPATH)
        self.log.config(text="Saved board state")


    def undo(self):
        if not self.can_undo:
            self.log.config(text="ERROR: Unable to undo move")
            return
        board = DorfBoard(save_file=AUTO_SAVE_FILEPATH)
        self.board_canvas.board = board
        self.board_canvas.draw_board()
        self.log.config(text="Removed last placed tile")
        self.can_undo = False


    def place_tile(self):
        if self.board_canvas.selected_hex is None:
            self.log.config(text="ERROR: no selected tile")
        xy = self.board_canvas.selected_hex
        if self.board_canvas.board.status[xy] != TileStatus.VALID:
            self.log.config(text="ERROR: Illegal tile placement at {}".format(xy))
            return
        self.board_canvas.board.save_board(save_file=AUTO_SAVE_FILEPATH)
        self.can_undo = True
        tile = self.tile_canvas.get_tile()
        result = self.board_canvas.board.place_tile(xy, tile)
        if result == DorfBoardResult.ERROR:
            self.log.config(text="ERROR: Illegal tile placement at {}".format(xy))
            return
        self.board_canvas.selected_hex = None
        self.board_canvas.set_hint(None)
        self.board_canvas.draw_board()
        self.tile_canvas.set_tile(6 * [TileEdge.GRASS])
        self.tile_canvas.set_connections(None)
        self.log.config(text="Placed tile at {}".format(xy))


    def remove_tile(self):
        if self.board_canvas.selected_hex == None:
            self.log.config(text="ERROR: No selected hex to remove")
            return
        xy = self.board_canvas.selected_hex
        if self.board_canvas.board.status[xy] == TileStatus.VALID:
            self.log.config(text="ERROR: Illegal tile removal at {}".format(xy))
            return
        self.board_canvas.board.save_board(save_file=AUTO_SAVE_FILEPATH)
        self.can_undo = True
        self.board_canvas.board.remove_tile(xy)
        self.board_canvas.selected_hex = None
        self.board_canvas.set_hint(None)
        self.board_canvas.delete('all')
        self.board_canvas.draw_board()
        self.log.config(text="Removed tile at {}".format(xy))


    def sample_tile(self):
        if self.board_canvas.selected_hex == None:
            self.log.config(text="ERROR: No selected hex to sample")
            return
        xy = self.board_canvas.selected_hex
        if self.board_canvas.board.status[xy] == TileStatus.VALID:
            self.log.config(text="ERROR: Illegal tile sample at {}".format(xy))
            return
        tile = self.board_canvas.board.edges[xy]
        self.tile_canvas.set_tile(tile)
        self.log.config(text="Tile sampled at {}".format(xy))


    def display_hint(self):
        tile = self.tile_canvas.get_tile()
        hint = self.board_canvas.board.get_hint(tile, threshold=2, top_k=10)
        if not hint:
            hint = self.board_canvas.board.get_hint(tile, top_k=5)
        text_hint = ["x={}, y={}, {} of {} good connections with {} perfects (score = {})".format(
                            x, y, evaluation['good'], evaluation['good'] + evaluation['bad'], evaluation['perfect'], evaluation['score']) \
                            for ((x, y), _), evaluation in hint]
        text_hint = "\n".join(text_hint)
        self.log.config(text=text_hint)
        self.board_canvas.set_hint(hint)
        self.board_canvas.draw_board()


    def display_stats(self):
        num_good = len(self.board_canvas.board.get_locations_with_status(TileStatus.GOOD))
        num_perfect = len(self.board_canvas.board.get_locations_with_status(TileStatus.PERFECT))
        num_imperfect = len(self.board_canvas.board.get_locations_with_status(TileStatus.IMPERFECT))
        num_valid = len(self.board_canvas.board.get_locations_with_status(TileStatus.VALID))
        text = "{} tiles placed\n".format(num_good+num_perfect+num_imperfect-1)
        text += "{} perfect tiles\n".format(num_perfect)
        text += "{} bad tiles\n".format(num_imperfect)
        text += "{} legal tile locations\n".format(num_valid)
        self.log.config(text=text)


    def correct_quit(self):
        self.destroy()
        self.quit()


def main(save_file:Optional[str], width:int, height:int, layout:int) -> None:
    app = DorfHelperApp(save_file=save_file, width=width, height=height, layout=args.layout)
    app.mainloop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--load', '-l', action='store_true', help="Load data from last manual save")
    parser.add_argument('--height', '-y', type=int, default=1000, help="Pixel height of the board display")
    parser.add_argument('--width', '-x', type=int, default=1500, help="Pixel width of the board display")
    parser.add_argument('--layout', type=int, default=0, help="Layout of the widgets in the window")
    args = parser.parse_args()

    assert(args.layout in [0, 1])

    save_file = MANUAL_SAVE_FILEPATH if args.load else None
    if not os.path.exists(SAVE_DIR):
        os.mkdir(SAVE_DIR)

    main(save_file=save_file, width=args.width, height=args.height, layout=args.layout)

    