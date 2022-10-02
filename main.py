import tkinter as tk
from tkinter import font

from time import time
from math import sqrt, floor, ceil

from os import path, mkdir

from enum import Enum
from types import SimpleNamespace


# Configurations ##############################################################

class State(Enum):
    IDLE = 0
    EDIT_START = 1
    EDIT_END = 2
    EDIT_MAP = 3

class Color(SimpleNamespace):
    START   = '#16a34a'
    END     = '#dc2626'
    GRID    = '#d4d4d4'
    CURSOR  = '#000000'
    LINE    = '#facc15'
    MAP     = '#2563eb'
    PREVIEW = '#475569'

WIDTH      = 800
HEIGHT     = 600
PADDING    = 2.5
DOT_RADIUS = 5
TILE_SIZE  = 40
FONT_SIZE  = 10
LINE_WIDTH = 3

MAP_WIDTH  = WIDTH // TILE_SIZE
MAP_HEIGHT = HEIGHT // TILE_SIZE

# Mutable states ##############################################################

start_pos = ()
end_pos = ()
result_path = []
map = [] 

state = State.IDLE


# Tkinter widgets #############################################################

def build_widgets():
    window = tk.Tk(className="pathfinding")
    window.wm_title("Pathfinding")
    window.wm_resizable(False, False)

    global NORMAL_FONT, BOLD_FONT
    NORMAL_FONT = font.Font(size=FONT_SIZE, weight='normal')
    BOLD_FONT   = font.Font(size=FONT_SIZE, weight='bold')

    root = tk.Frame(window)
    root.pack(padx=PADDING, pady=PADDING)

    config_menu = tk.Frame(root)
    config_menu.pack(padx=PADDING, pady=PADDING, fill='x')

    map_menu = tk.Frame(config_menu)
    map_menu.pack(side=tk.LEFT, expand=1, anchor='w')

    global map_name
    map_name = tk.Entry(map_menu)
    map_name.pack(side=tk.LEFT, padx=PADDING)

    global map_save
    map_save = tk.Button(map_menu, text='Save', font=NORMAL_FONT)
    map_save.pack(side=tk.LEFT, padx=PADDING)

    global map_load
    map_load = tk.Button(map_menu, text='Load', font=NORMAL_FONT)
    map_load.pack(side=tk.LEFT, padx=PADDING)

    global map_edit
    map_edit = tk.Button(map_menu, text='Edit', font=NORMAL_FONT)
    map_edit.pack(side=tk.LEFT, padx=PADDING)

    points_menu = tk.Frame(config_menu)
    points_menu.pack(side=tk.LEFT, expand=1, anchor='e')

    global points_edit
    points_edit = tk.Button(points_menu, text="Edit", font=NORMAL_FONT)
    points_edit.pack(side=tk.LEFT, padx=PADDING)

    global start_label
    start_label = tk.Label(points_menu, text="start = {...; ...}", font=NORMAL_FONT)
    start_label.pack(side=tk.LEFT, padx=PADDING)

    global end_label
    end_label = tk.Label(points_menu, text="end = {...; ...}", font=NORMAL_FONT)
    end_label.pack(side=tk.LEFT, padx=PADDING)

    global canvas
    canvas = tk.Canvas(root, bg="#ffffff", width=WIDTH, height=HEIGHT)
    canvas.config(cursor='none')
    canvas.pack(padx=PADDING, pady=PADDING)

    result_menu = tk.Frame(root)
    result_menu.pack(padx=PADDING, pady=PADDING, side=tk.LEFT, anchor='w')

    global distance_label
    distance_label = tk.Label(result_menu, text="Distance: ...", font=NORMAL_FONT)
    distance_label.pack(side=tk.LEFT, padx=PADDING)

    global time_label
    time_label = tk.Label(result_menu, text="Time: ...", font=NORMAL_FONT)
    time_label.pack(side=tk.LEFT, padx=PADDING)

    return window


# Rendering ###################################################################

def draw_dot(pos, color):
    dot_start_x = pos[0] - DOT_RADIUS
    dot_start_y = pos[1] - DOT_RADIUS

    dot_end_x = pos[0] + DOT_RADIUS
    dot_end_y = pos[1] + DOT_RADIUS

    canvas.create_oval(dot_start_x, dot_start_y, dot_end_x, dot_end_y,
                       fill=color, outline='')


def align_point(x, y):
    aligned_x = round(x / TILE_SIZE) * TILE_SIZE
    aligned_y = round(y / TILE_SIZE) * TILE_SIZE
    return aligned_x, aligned_y


def draw_lines(points, fill, width):
    last = ()
    for point in points:
        draw_dot(point, fill)
        if last:
            canvas.create_line(last, point, fill=fill, width=width)

        last = point


def render():
    canvas.delete("all")
    # Draw the grid
    for i in range(MAP_WIDTH + 1):
        canvas.create_line(i * TILE_SIZE, 0, i * TILE_SIZE, HEIGHT,
                           fill=Color.GRID)

    for i in range(MAP_HEIGHT + 1):
        canvas.create_line(0, i * TILE_SIZE, WIDTH, i * TILE_SIZE,
                           fill=Color.GRID)

    draw_lines(map, Color.MAP, LINE_WIDTH)

    # Draw the computed path

    draw_lines(result_path, Color.LINE, LINE_WIDTH)

    # Place the start and end dots
    global start_pos, end_pos
    if start_pos:
        draw_dot(start_pos, Color.START)
    if end_pos:
        draw_dot(end_pos, Color.END)


def draw_cursor(x, y):
    if state == State.IDLE:
        dot_color = Color.CURSOR
    elif state == State.EDIT_START:
        dot_color = Color.START
    elif state == State.EDIT_END:
        dot_color = Color.END
    elif state == State.EDIT_MAP:
        x_tiled = round(x / TILE_SIZE) * TILE_SIZE
        y_tiled = round(y / TILE_SIZE) * TILE_SIZE
        tiled_pos = (x_tiled, y_tiled)
        dot_color = Color.PREVIEW
        if map:
            canvas.create_line(map[0], tiled_pos, fill=Color.PREVIEW,
                               width=LINE_WIDTH)
            canvas.create_line(map[-1], tiled_pos, fill=Color.PREVIEW,
                               width=LINE_WIDTH)

            if len(map) > 1 and tiled_pos == map[0]:
                draw_dot(tiled_pos, Color.START)
            elif tiled_pos in map:
                draw_dot(tiled_pos, Color.END)
            else:
                draw_dot(tiled_pos, Color.PREVIEW)
        else:
            draw_dot(tiled_pos, Color.PREVIEW)
    else:
        raise Exception('Unreachable')
    draw_dot((x, y), dot_color)


# Graph generation ############################################################
# TODO: Implement grid generation


# Pathfinding #################################################################
# TODO: Implement A* with path smoothing for pathfinding

def reset():
    global start_pos, end_pos, result_path
    start_pos = ()
    end_pos = ()
    result_path = []


def get_distance():
    dist = 0
    last_x, last_y = None, None

    for (x, y) in result_path:
        if last_x and last_y:
            dx = x - last_x 
            dy = y - last_y
            dist += sqrt(dx * dx + dy * dy)

        last_x = x
        last_y = y
    return dist / TILE_SIZE
        

def pathfind():
    global result_path
    start_time = time()
    if not start_pos or not end_pos:
        return
    result_path = [start_pos, end_pos]
    distance = get_distance()
    end_time = time()
    elapsed_time = (end_time - start_time) * 1000
    distance_label.config(text=f"Distance: {distance:.2f}")
    time_label.config(text=f"Time: {elapsed_time:.2f}ms")


# Events ######################################################################

def display_pos(pos, name):
    x, y = pos
    return f"{name} = {{{x/TILE_SIZE:.2f}; {y/TILE_SIZE:.2f}}}"


def canvas_motion(e):
    if state == State.EDIT_START:
        start_pos = (e.x, e.y)
        start_label.config(text=display_pos(start_pos, "start"), font=BOLD_FONT)
    elif state == State.EDIT_END:
        end_pos = (e.x, e.y)
        end_label.config(text=display_pos(end_pos, "end"), font=BOLD_FONT)

    render()
    draw_cursor(e.x, e.y)


def canvas_click(e):
    global start_pos, end_pos, state
    if state == State.EDIT_START:
        start_pos = (e.x, e.y)
        start_label.config(text=display_pos(start_pos, "start"),
                           font=NORMAL_FONT)
        end_label.config(text="end = {...; ...}", font=BOLD_FONT)
        end_label.cget('font')
        state = State.EDIT_END
    elif state == State.EDIT_END:
        end_pos = (e.x, e.y)
        end_label.config(text=display_pos(end_pos, "end"), font=NORMAL_FONT)
        pathfind()
        state = State.IDLE
    elif state == State.EDIT_MAP:
        tiled_x = round(e.x / TILE_SIZE) * TILE_SIZE
        tiled_y = round(e.y / TILE_SIZE) * TILE_SIZE

        tiled_pos = (tiled_x, tiled_y)

        if map:
            if len(map) > 1 and tiled_pos == map[0]:
                map.append(map[0])
                state = State.IDLE
            elif tiled_pos in map:
                while map[-1] != tiled_pos:
                    map.pop()
                map.pop()
            else:
                map.append(tiled_pos)
        else:
            map.append(tiled_pos)

    render()
    draw_cursor(e.x, e.y)


def edit_points(_):
    global start_pos, end_pos, state, result_path
    if state == State.IDLE:
        reset()
        render()
        start_label.config(text="start = {...; ...}", font=BOLD_FONT)
        end_label.config(text="end = {...; ...}")

        distance_label.config(text="Distance: ...")
        time_label.config(text="Time: ...")
        state = State.EDIT_START


def save_map(_):
    if not path.exists('maps'):
        mkdir('maps')
    name = "maps/" + map_name.get() + ".mp"
    with open(name, 'w') as f:
        for point in map:
            x, y = point
            f.write(f"{x} {y}\n")


def load_map(_):
    global start_pos, end_pos
    if not path.exists('maps'):
        mkdir('maps')

    name = "maps/" + map_name.get() + ".mp"
    map.clear()
    reset()
    with open(name, 'r') as f:
        for line in f.readlines():
            x, y = (int(i) for i in line.split())
            map.append((x, y))


def edit_map(_):
    global state, start_pos, end_pos
    reset()
    if state == State.IDLE:
        if map:
            map.pop()
        state = State.EDIT_MAP


def attach_events():
    canvas.bind('<Motion>', canvas_motion)
    canvas.bind('<Button-1>', canvas_click)
    points_edit.bind('<Button-1>', edit_points)
    map_save.bind('<Button-1>', save_map)
    map_load.bind('<Button-1>', load_map)
    map_edit.bind('<Button-1>', edit_map)


# Entrypoint ##################################################################

def create_window():
    window = build_widgets()
    attach_events()
    window.mainloop()

if __name__ == "__main__":
    create_window()
