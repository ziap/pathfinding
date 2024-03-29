#!.venv/bin/python

import tkinter as tk
from tkinter import font

from time import perf_counter
from math import sqrt, inf
from random import randrange

from queue import PriorityQueue
from numba import njit

from os import path, mkdir

# Configurations ##############################################################

class State:
    IDLE = 0
    EDIT_START = 1
    EDIT_END = 2
    EDIT_MAP = 3

class Color:
    START   = '#16a34a'
    END     = '#dc2626'
    GRID    = '#a3a3a3'
    CURSOR  = '#000000'
    LINE    = '#facc15'
    MAP     = '#2563eb'
    POLYGON = '#bfdbfe'
    PREVIEW = '#475569'
    GRAPH   = '#60a5fa'

WIDTH      = 1024
HEIGHT     = 768
INF        = inf
PADDING    = 10
DOT_RADIUS = 5
TILE_SIZE  = 32
FONT_SIZE  = 10

MAP_WIDTH  = WIDTH // TILE_SIZE
MAP_HEIGHT = HEIGHT // TILE_SIZE

# Mutable states ##############################################################

start_pos = ()
end_pos = ()
result_path = []
map = [] 
graph = {}

state = State.IDLE

# Tkinter widgets #############################################################

def App():
    window = tk.Tk(className="pathfinding")
    window.title("Pathfinding")
    window.resizable(False, False)

    global NORMAL_FONT, BOLD_FONT
    NORMAL_FONT = font.Font(size=FONT_SIZE, weight='normal')
    BOLD_FONT     = font.Font(size=FONT_SIZE, weight='bold')

    root = tk.Frame(window).pack()

    config_menu = tk.Frame(root)
    config_menu.pack(padx=PADDING / 2, pady=PADDING, fill='x')

    map_menu = tk.Frame(config_menu)
    map_menu.pack(side=tk.LEFT, expand=1, anchor='w')

    global map_name
    map_name = tk.StringVar()
    tk.Entry(map_menu, textvariable=map_name).pack(side=tk.LEFT, padx=PADDING / 2)

    tk.Button(map_menu, text='Save', font=NORMAL_FONT, command=save_map).pack(side=tk.LEFT, padx=PADDING / 2)
    tk.Button(map_menu, text='Load', font=NORMAL_FONT, command=load_map).pack(side=tk.LEFT, padx=PADDING / 2)
    tk.Button(map_menu, text='Edit', font=NORMAL_FONT, command=edit_map).pack(side=tk.LEFT, padx=PADDING / 2)
    tk.Button(map_menu, text='Random', font=NORMAL_FONT, command=random_map).pack(side=tk.LEFT, padx=PADDING / 2)

    points_menu = tk.Frame(config_menu)
    points_menu.pack(side=tk.LEFT, expand=1, anchor='e')

    tk.Button(points_menu, text="Edit", font=NORMAL_FONT, command=edit_points).pack(side=tk.LEFT, padx=PADDING / 2)

    global start_label
    start_label = tk.Label(points_menu, text="start = {...; ...}", font=NORMAL_FONT)
    start_label.pack(side=tk.LEFT, padx=PADDING / 2)

    global end_label
    end_label = tk.Label(points_menu, text="end = {...; ...}", font=NORMAL_FONT)
    end_label.pack(side=tk.LEFT, padx=PADDING / 2)

    global canvas
    canvas = tk.Canvas(root, bg="#ffffff", width=WIDTH, height=HEIGHT)
    canvas.config(cursor='none')
    canvas.pack(padx=PADDING)

    canvas.bind('<Motion>', canvas_motion)
    canvas.bind('<Button-1>', canvas_click)

    result_menu = tk.Frame(root)
    result_menu.pack(padx=PADDING / 2, pady=PADDING, side=tk.LEFT, anchor='w')

    global show_graph
    show_graph = tk.BooleanVar()
    show_graph.trace_add("write", lambda *_: render())
    tk.Checkbutton(result_menu, text="Show graph", variable=show_graph, onvalue=True, offvalue=False).pack(side=tk.RIGHT, padx=PADDING / 2)

    global distance_label
    distance_label = tk.StringVar(value="Distance: ...")
    tk.Label(result_menu, textvariable=distance_label, font=NORMAL_FONT).pack(side=tk.LEFT, padx=PADDING / 2)

    global time_label
    time_label = tk.StringVar(value="Time: ...")
    tk.Label(result_menu, textvariable=time_label, font=NORMAL_FONT).pack(side=tk.LEFT, padx=PADDING / 2)

    init_shapes()
    render()
    return window

# Rendering ###################################################################

def draw_dot(pos, color, tag):
    dot_start_x = pos[0] - DOT_RADIUS
    dot_start_y = pos[1] - DOT_RADIUS

    dot_end_x = pos[0] + DOT_RADIUS
    dot_end_y = pos[1] + DOT_RADIUS

    canvas.create_oval(dot_start_x, dot_start_y, dot_end_x, dot_end_y, fill=color, outline='', tags=tag)


def align_point(x, y):
    aligned_x = round(x / TILE_SIZE) * TILE_SIZE
    aligned_y = round(y / TILE_SIZE) * TILE_SIZE
    return aligned_x, aligned_y


def draw_lines(points, fill, width, tag):
    canvas.delete(tag)
    last = ()
    for point in points:
        draw_dot(point, fill, tag)
        if last:
            canvas.create_line(last, point, fill=fill, width=width, tags=tag)

        last = point


def init_shapes():
    global poly
    poly = canvas.create_polygon([0, 0], fill=Color.POLYGON, outline='')

    # Draw the grid
    for i in range(MAP_WIDTH + 1):
        canvas.create_line(i * TILE_SIZE, 0, i * TILE_SIZE, HEIGHT, width=1, fill=Color.GRID)

    for i in range(MAP_HEIGHT + 1):
        canvas.create_line(0, i * TILE_SIZE, WIDTH, i * TILE_SIZE, width=1, fill=Color.GRID)


def render():
    global start_pos, end_pos, poly

    if state != State.EDIT_MAP and len(map) > 0:
        canvas.coords(poly, sum([[i[0], i[1]] for i in map], []))
    else:
        canvas.coords(poly, [0, 0])

    canvas.delete('graph')
    if state != State.EDIT_MAP and show_graph.get():
        for e1 in graph:
            pos1 = start_pos if e1 == -1 else end_pos if e1 == -2 else map[e1]
            for e2 in graph[e1]:
                if e1 < e2 or e2 == -2:
                    pos2 = start_pos if e2 == -1 else end_pos if e2 == -2 else map[e2]
                    
                    if pos1 and pos2:
                        canvas.create_line(pos1, pos2, fill=Color.GRAPH, width=1, tags='graph')
                        
    draw_lines(map, Color.MAP, 3, 'map_outline')

    draw_lines(result_path, Color.LINE, 3, 'result_path')

    canvas.delete('start-end')
    if start_pos:
        draw_dot(start_pos, Color.START, 'start-end')
    if end_pos:
        draw_dot(end_pos, Color.END, 'start-end')


def draw_cursor(x, y):
    canvas.delete("cursor")
    if state == State.IDLE:
        dot_color = Color.CURSOR
    elif state == State.EDIT_START:
        dot_color = Color.START if in_polygon(x, y) else Color.CURSOR
    elif state == State.EDIT_END:
        dot_color = Color.END if in_polygon(x, y) else Color.CURSOR
    elif state == State.EDIT_MAP:
        x_tiled = round(x / TILE_SIZE) * TILE_SIZE
        y_tiled = round(y / TILE_SIZE) * TILE_SIZE
        tiled_pos = (x_tiled, y_tiled)
        dot_color = Color.PREVIEW
        if map:
            canvas.create_line(map[0], tiled_pos, fill=Color.PREVIEW, width=3, tags='cursor')
            canvas.create_line(map[-1], tiled_pos, fill=Color.PREVIEW, width=3, tags='cursor')

            if len(map) > 2 and tiled_pos == map[0]:
                draw_dot(tiled_pos, Color.START, 'cursor')
            elif tiled_pos in map:
                draw_dot(tiled_pos, Color.END, 'cursor')
            else:
                draw_dot(tiled_pos, Color.PREVIEW, 'cursor')
        else:
            draw_dot(tiled_pos, Color.PREVIEW, 'cursor')
    else:
        raise Exception('Unreachable')
    draw_dot((x, y), dot_color, 'cursor')

# Geometry ####################################################################


@njit
def distance(a, b):
    xa, ya = a
    xb, yb = b
    dx = xa - xb
    dy = ya - yb
    return sqrt(dx * dx + dy * dy)


@njit
def orientation(a, b, c):
    xa, ya = a
    xb, yb = b
    xc, yc = c
    val = (yb - ya) * (xc - xb) - (xb - xa) * (yc - yb)
    return 1 if val > 0 else 2 if val < 0 else 0


@njit
def on_segment(a, b, c):
    xa, ya = a
    xb, yb = b
    xc, yc = c
    return xb <= max(xa, xc) and xb >= min(xa, xc) and yb <= max(ya, yc) and yb >= min(ya, yc)


@njit
def intersect(p1, q1, p2, q2):
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    if o1 != o2 and o3 != o4:
        return True

    if o1 == 0 and on_segment(p1, p2, q1):
        return True

    if o2 == 0 and on_segment(p1, q2, q1):
        return True

    if o3 == 0 and on_segment(p2, p1, q2):
        return True

    if o4 == 0 and on_segment(p2, q1, q2):
        return True

    return False


def in_polygon(x, y):
    inside = False
    for i in range(len(map) - 1):
        x1, y1 = map[i]
        x2, y2 = map[i + 1]

        if (y1 > y2):
            x1, x2 = x2, x1
            y1, y2 = y2, y1

        # Check collision with horizontal line to the right of (x, y)
        if y > y1 and y <= y2 and x <= x1 + (x2 - x1) * (y - y1) / (y2 - y1):
            inside = not inside
    
    return inside 

# Graph generation ############################################################

def add_edge(idx1, idx2, pos1, pos2, rev):
    xi, yi = pos1
    xj, yj = pos2

    # In case it doesn't intersect with any polygon edge, discard if the
    # midpoint is outside of the polygon
    if not in_polygon((xi + xj) / 2, (yi + yj) / 2):
        return

    is_intersect = False
    
    for k in range(len(map) - 1):
        k1 = (k + 1) % (len(map) - 1)
        if k == idx1 or k == idx2 or k1 == idx1 or k1 == idx2:
            continue
        if intersect(pos1, pos2, map[k], map[k1]):
            is_intersect = True
            break

    if not is_intersect:
        dx, dy = xj - xi, yj - yi
        w = sqrt(dx * dx + dy * dy)
        
        if idx1 not in graph:
            graph[idx1] = {}

        graph[idx1][idx2] = w
        
        if rev:
            if idx2 not in graph:
                graph[idx2] = {}

            graph[idx2][idx1] = w


def generate_graph():
    global graph
    graph = {}
    
    for i in range(len(map) - 1):
        # All polygon edges are also edges of visibility graph
        j = (i + 1) % (len(map) - 1)
        w = distance(map[i], map[j])
        
        if i not in graph:
            graph[i] = {}

        if j not in graph:
            graph[j] = {}

        graph[i][j] = graph[j][i] = w

        for j in range(i + 2, len(map) - 1):
            add_edge(i, j, map[i], map[j], True)

# Pathfinding #################################################################    

def pathfind():
    global result_path
    start_time = perf_counter()
    if not start_pos or not end_pos:
        return

    n = len(map) - 1

    # Add the start and end node to the visibility graph
    for i in range(n):
        p = map[i]
        add_edge(-1, i, start_pos, p, False)
        add_edge(i, -2, p, end_pos, False)
    add_edge(-1, -2, start_pos, end_pos, False)

    g = [INF] * n    # g(x) = smallest distance from start to x
    h = [0.0] * n    # h(x) = estimated cost to travel from x to end
    f = [INF] * n    # f(x) = g(x) + h(x)
    p = [-3] * n     # the parent of a node in the final path

    # Use euclidean distance to calculate h(x)
    for i in range(n):
        h[i] = distance(map[i], end_pos)

    # NOTE: switch to a binary heap to improve performance
    open = PriorityQueue()

    g_end = INF
    p_end = -3
    open_end = False

    # Basic A* implementation
    for adj in graph[-1]:
        if adj != -2:
            dist = graph[-1][adj]
            if dist < g[adj]:
                g[adj] = dist
                f[adj] = dist + h[adj]
                p[adj] = -1
                open.put((f[adj], adj))
        else:
            if graph[-1][-2] < g_end:
                g_end = graph[-1][-2]
                open_end = True
                p_end = -1

    while True:
        f_v, v = open.get()
        
        if open_end and g_end < f_v:
            break

        for adj in graph[v]:
            dist = g[v] + graph[v][adj]
            if adj != -2:
                if dist < g[adj]:
                    g[adj] = dist
                    f[adj] = dist + h[adj]
                    p[adj] = v
                    open.put((f[adj], adj))
            else:
                if dist < g_end:
                    g_end = dist
                    open_end = True
                    p_end = v
    
    # Path reconstruction
    result_path = [end_pos]
    last = p_end

    while last != -1:
        result_path.append(map[last])
        last = p[last]
    
    result_path.append(start_pos)

    end_time = perf_counter()
    elapsed_time = (end_time - start_time) * 1000
    distance_label.set(f"Distance: {g_end / TILE_SIZE:.2f}")
    time_label.set(f"Time: {elapsed_time:.2f}ms")

# Random map generation #######################################################

@njit
def shuffle(a):
    for i in range(len(a)):
        idx = randrange(len(a))
        a[i], a[idx] = a[idx], a[i]


@njit
def gen_poly(w, h, d=0.2):
    c = int((w - 1) * (h - 1) * d * d)

    vl = [(i, j) for i in range(1, w) for j in range(1, h)]
    shuffle(vl)
    vl = vl[:c]

    x = [i[0] for i in vl]
    y = [i[1] for i in vl]

    found = True    
    while found:
        found = False
        for i in range(c - 1):
            if found:
                break

            for j in range(i + 2, c):
                if i == 0 and j == c - 1:
                    continue
                i1, j1 = i + 1, (j + 1) % c
                p1 = (x[i], y[i])
                p2 = (x[i1], y[i1])
                p3 = (x[j], y[j])
                p4 = (x[j1], y[j1])

                if distance(p1, p2) + distance(p3, p4) > distance(p1, p3) + distance(p2, p4):
                    found = True
                    x[i + 1:j + 1] = x[j:i:-1]
                    y[i + 1:j + 1] = y[j:i:-1]
                    break

    res = []

    for i in range(c):
        p = (x[i] * TILE_SIZE, y[i] * TILE_SIZE)
        if len(res) > 1 and orientation(res[-2], res[-1], p) == 0:
            res.pop()
        res.append(p)
    
    if len(res) > 2 and orientation(res[-1], res[0], res[1]) == 0:
        res.pop(0)

    res.append(res[0])

    return res

# Events ######################################################################

def reset():
    global start_pos, end_pos, result_path, graph
    start_pos = ()
    end_pos = ()
    result_path = []

    # Remove start and end from visibility graph
    if -1 in graph:
        del graph[-1]
    for e in graph:
        if -2 in graph[e]:
            del graph[e][-2]


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

    draw_cursor(e.x, e.y)


def canvas_click(e):
    global start_pos, end_pos, state
    if state == State.EDIT_START and in_polygon(e.x, e.y):
        start_pos = (e.x, e.y)
        start_label.config(text=display_pos(start_pos, "start"),
                             font=NORMAL_FONT)
        end_label.config(text="end = {...; ...}", font=BOLD_FONT)
        end_label.cget('font')
        state = State.EDIT_END
    elif state == State.EDIT_END and in_polygon(e.x, e.y):
        end_pos = (e.x, e.y)
        end_label.config(text=display_pos(end_pos, "end"), font=NORMAL_FONT)
        pathfind()
        state = State.IDLE
    
    # Map editor
    elif state == State.EDIT_MAP:
        tiled_pos = align_point(e.x, e.y)

        if map:
            # Remove nodes by clicking it
            if tiled_pos in map and (len(map) == 1 or tiled_pos != map[0]):
                while map[-1] != tiled_pos:
                    map.pop()
                map.pop()
            else:
                # Prevent self-intersecting polygons
                is_intersect = False
                for k in range(len(map) - 2):
                    if tiled_pos == map[0] and k == 0:
                        continue
                    if intersect(map[-1], tiled_pos, map[k], map[k + 1]):
                        is_intersect = True
                        break

                if not is_intersect:
                    if len(map) > 2:
                        # Join colinear edges to lower edge count
                        if orientation(map[-2], map[-1], tiled_pos) == 0:
                            map.pop()

                        # Finish editing by clicking the first node
                        if tiled_pos == map[0]:
                            if orientation(map[-1], map[0], map[1]) == 0:
                                map.pop(0)

                            map.append(map[0])
                            state = State.IDLE
                            global graph
                            generate_graph()
                        else:
                            map.append(tiled_pos)
                    elif tiled_pos != map[0]:
                        map.append(tiled_pos)
        else:
            map.append(tiled_pos)

    render()
    draw_cursor(e.x, e.y)

def edit_points():
    global start_pos, end_pos, state, result_path
    if state == State.IDLE and len(map) > 3:
        reset()
        render()
        start_label.config(text="start = {...; ...}", font=BOLD_FONT)
        end_label.config(text="end = {...; ...}")

        distance_label.set("Distance: ...")
        time_label.set("Time: ...")
        state = State.EDIT_START


def save_map():
    global state
    if state == State.IDLE:
        if not path.exists('maps'):
            mkdir('maps')
        name = "maps/" + map_name.get() + ".mp"
        with open(name, 'w') as f:
            for point in map:
                x, y = point
                f.write(f"{x // TILE_SIZE} {y // TILE_SIZE}\n")


def load_map():
    global state, graph
    if state == State.IDLE:
        if not path.exists('maps'):
            mkdir('maps')

        name = "maps/" + map_name.get() + ".mp"
        map.clear()
        reset()
        with open(name, 'r') as f:
            for line in f.readlines():
                x, y = (int(i) for i in line.split())
                map.append((x * TILE_SIZE, y * TILE_SIZE))
            generate_graph()
            render()


def edit_map():
    global state
    if state == State.IDLE:
        reset()
        if map:
            map.pop()
        state = State.EDIT_MAP
        render()


def random_map():
    global state, map, graph
    if state == State.IDLE:
        reset()
        map = gen_poly(MAP_WIDTH, MAP_HEIGHT, 0.5)
        generate_graph()
        render()

# Entrypoint ##################################################################

if __name__ == "__main__":
    App().mainloop()
