import tkinter as tk
from tkinter import font

from time import time
from math import sqrt, floor, ceil

from enum import Enum
from types import SimpleNamespace

window = tk.Tk(className="pathfinding")

# Configurations ##############################################################

class State(Enum):
    IDLE = 0
    EDIT_START = 1
    EDIT_END = 2

class Color(SimpleNamespace):
    START  = '#16a34a'
    END    = '#dc2626'
    GRID   = '#d4d4d4'
    CURSOR = '#000000'
    LINE   = '#db2777'

WIDTH      = 800
HEIGHT     = 600
PADDING    = 2.5
DOT_RADIUS = 5
TILE_SIZE  = 40
FONT_SIZE  = 10
LINE_WIDTH = 3

MAP_WIDTH  = WIDTH // TILE_SIZE
MAP_HEIGHT = HEIGHT // TILE_SIZE

NORMAL_FONT = font.Font(size=FONT_SIZE, weight='normal')
BOLD_FONT   = font.Font(size=FONT_SIZE, weight='bold')


# Mutable states ##############################################################

start_pos = ()
end_pos = ()
lines = []
state = State.IDLE


# Tkinter widgets #############################################################

# Layout:
# window
#  └──root
#      ├── config_menu
#      │    ├── map_menu
#      │    │    ├── map_name
#      │    │    ├── map_save
#      │    │    ├── map_load
#      │    │    ... (not implemented)
#      │    └── points_menu
#      │         ├── points_edit
#      │         ├── start_label
#      │         └── end_label
#      ├── canvas
#      └── result_menu
#           ├── distance_label
#           └── time_label

root = tk.Frame(window)
root.pack(padx=PADDING, pady=PADDING)

config_menu = tk.Frame(root)
config_menu.pack(padx=PADDING, pady=PADDING, fill='x')

map_menu = tk.Frame(config_menu)
map_menu.pack(side=tk.LEFT, expand=1, anchor='w')

map_name = tk.Entry(map_menu)
map_name.pack(side=tk.LEFT, padx=PADDING)

map_save = tk.Button(map_menu, text='Save', font=NORMAL_FONT)
map_save.pack(side=tk.LEFT, padx=PADDING)

map_load = tk.Button(map_menu, text='Load', font=NORMAL_FONT)
map_load.pack(side=tk.LEFT, padx=PADDING)

points_menu = tk.Frame(config_menu)
points_menu.pack(side=tk.LEFT, expand=1, anchor='e')

points_edit = tk.Button(points_menu, text="Edit", font=NORMAL_FONT)
points_edit.pack(side=tk.LEFT, padx=PADDING)

start_label = tk.Label(points_menu, text="start = {...; ...}", font=NORMAL_FONT)
start_label.pack(side=tk.LEFT, padx=PADDING)

end_label = tk.Label(points_menu, text="end = {...; ...}", font=NORMAL_FONT)
end_label.pack(side=tk.LEFT, padx=PADDING)

canvas = tk.Canvas(root, bg="#ffffff", width=WIDTH, height=HEIGHT)
canvas.config(cursor='none')
canvas.pack(padx=PADDING, pady=PADDING)

result_menu = tk.Frame(root)
result_menu.pack(padx=PADDING, pady=PADDING, side=tk.LEFT, anchor='w')

distance_label = tk.Label(result_menu, text="Distance: ...", font=NORMAL_FONT)
distance_label.pack(side=tk.LEFT, padx=PADDING)

time_label = tk.Label(result_menu, text="Time: ...", font=NORMAL_FONT)
time_label.pack(side=tk.LEFT, padx=PADDING)


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


def render():
    canvas.delete("all")
    # Draw the grid
    for i in range(MAP_WIDTH + 1):
        canvas.create_line(i * TILE_SIZE, 0, i * TILE_SIZE, HEIGHT,
                           fill=Color.GRID)

    for i in range(MAP_HEIGHT + 1):
        canvas.create_line(0, i * TILE_SIZE, WIDTH, i * TILE_SIZE,
                           fill=Color.GRID)

    # TODO: Draw the map

    # Draw the computed path
    for line in lines:
        canvas.create_line(line, fill=Color.LINE, width=LINE_WIDTH)

    # Place the start and end dots
    global start_pos, end_pos
    if start_pos:
        draw_dot(start_pos, Color.START)
    if end_pos:
        draw_dot(end_pos, Color.END)


def draw_cursor(x, y):
    global state
    if state == State.IDLE:
        dot_color = Color.CURSOR
    elif state == State.EDIT_START:
        dot_color = Color.START
    elif state == State.EDIT_END:
        dot_color = Color.END
    else:
        raise Exception('Unreachable')
    draw_dot((x, y), dot_color)


# Map representation ##########################################################
# TODO: Implement map representation


# Graph generation ############################################################
# TODO: Implement grid generation


# Pathfinding #################################################################
# TODO: Implement A* with path smoothing for pathfinding

def get_distance():
    dist = 0
    for ((x1, y1), (x2, y2)) in lines:
        dx = x1 - x2
        dy = y1 - y2
        dist += sqrt(dx * dx + dy * dy)
    return dist / TILE_SIZE
        

def pathfind():
    global lines
    start_time = time()
    lines = [(start_pos, end_pos)]
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

    render()
    draw_cursor(e.x, e.y)


def edit_points(e):
    global start_pos, end_pos, state, lines
    if state == State.IDLE:
        start_pos = ()
        end_pos = ()
        lines = []
        render()
        start_label.config(text="start = {...; ...}", font=BOLD_FONT)
        end_label.config(text="end = {...; ...}")

        distance_label.config(text="Distance: ...")
        time_label.config(text="Time: ...")
        state = State.EDIT_START

canvas.bind('<Motion>', canvas_motion)
canvas.bind('<Button-1>', canvas_click)
points_edit.bind('<Button-1>', edit_points)


# Start window ################################################################

window.wm_title("Pathfinding")
window.wm_resizable(False, False)
window.mainloop()
