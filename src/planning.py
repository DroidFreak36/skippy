from defs import *
import math
import util

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def init_cache():
    Memory.planning_steps = [
        planning_start,
        source_fills,
        controller_fill,
        orth_wall_fill,
        place_stamp,
        finalize
    ]
    ff_stamp = [
        [' ',' ',' ',' ',' ','r'],
        [' ',' ',' ',' ','r','r','r'],
        [' ',' ',' ','r','x','x','x','r'],
        [' ',' ','r','r','x','I','x','r','r'],
        [' ','r','x','x','S','x','R','x','x','r'],
        ['r','r','x','I','x','r','x','I','x','r','r'],
        [' ','r','x','x','R','x','S','x','x','r'],
        [' ',' ','r','r','x','I','x','r','r'],
        [' ',' ',' ','r','x','x','x','r'],
        [' ',' ',' ',' ','r','r','r'],
        [' ',' ',' ',' ',' ','r']
    ]
    core_stamp = [
        [' ',' ',' ','r'],
        [' ',' ','r','r','r'],
        [' ','r','t','S','r','r'],
        ['r','r','F','I','s','r','r'],
        [' ','r','l','P','N','r'],
        [' ',' ','r','r','r'],
        [' ',' ',' ','r']
    ]
    lab_stamp = [
        [' ',' ',' ','r'],
        [' ',' ','r','L','r'],
        [' ','r','L','L','R','r'],
        ['r','r','L','L','L','L','r'],
        [' ','r','L','L','L','r'],
        [' ',' ','r','r','r'],
        [' ',' ',' ','r']
    ]
    big_ext_stamp = [
        [' ',' ',' ','r'],
        [' ',' ','r','x','r'],
        [' ','r','x','x','x','r'],
        ['r','x','x','O','x','x','r'],
        [' ','r','x','x','x','r'],
        [' ',' ','r','x','r'],
        [' ',' ',' ','r']
    ]
    smol_ext_stamp = [
        [' ',' ','r'],
        [' ','r','x','r'],
        ['r','x','T','x','r'],
        [' ','r','x','r'],
        [' ',' ','r']
    ]
    Memory.stamp_list = [
        [6, ff_stamp],
        [4, core_stamp],
        [4, lab_stamp],
        [4, big_ext_stamp],
        [3, smol_ext_stamp],
        [3, smol_ext_stamp],
        [3, smol_ext_stamp],
        [3, smol_ext_stamp],
        [3, smol_ext_stamp],
        [3, smol_ext_stamp]
    ]

def plan_step(room_name, visuals_on):
    if not room.memory.pd:
        room.memory.pd = {}
    if Object.keys(Game.rooms).includes(room_name):
        room = Game.rooms[room_name]
        if not room.memory.planning_step:
            room.memory.planning_step = 0
        planning_function = Memory.planning_steps[room.memory.planning_step]
        if planning_function(room, visuals_on):
            room.memory.planning_step += 1

def planning_start(room, visuals_on):
    if not room.memory.pd:
        room.memory.pd = {}
    terrain = room.getTerrain().getRawBuffer()
    room.memory.master_map = []
    for i in range(2500):
        if terrain[i] & TERRAIN_MASK_WALL:
            room.memory.master_map.append('W')
        else:
            room.memory.master_map.append(' ')
    offset = [-51, -50, -49, -1, 1, 49, 50, 51]
    for i in range(50):
        for j in [i, 2450 + i, i * 50, i * 50 + 49]:
            if not terrain[j] & TERRAIN_MASK_WALL:
                room.memory.master_map[j] = 'E'
                for off in offset:
                    if room.memory.master_map[j + off] == ' ':
                        room.memory.master_map[j + off] = 'E'
    return 1


def source_fills(room, visuals_on):
    sources = room.find(FIND_SOURCES)
    if not room.memory.pd.source_fills:
        room.memory.pd.source_fills = {}
    for source in sources:
        if not room.memory.pd.source_fills[source.id]:
            fill = {}
            terrain = room.getTerrain().getRawBuffer()
            for i in range(2500):
                if terrain[i] & 1:
                    fill[i] = 255
                else:
                    fill[i] = 0
            for i in range(50):
                for j in [i, 2450 + i, i * 50, i * 50 + 49]:
                    if fill[j] == 0:
                        fill[j] = -1
            steps = {}
            source_index = source.pos.y * 50 + source.pos.x
            offset = [-51, -50, -49, -1, 1, 49, 50, 51]
            for off in offset:
                steps[source_index + off] = 1
            for i in range(100):
                next_steps = {}
                for j in Object.keys(steps):
                    if fill[j] == 0:
                        fill[j] = i + 1
                        for off in offset:
                            k = int(j) + off
                            next_steps[k] = 1
                    elif fill[j] == -1:
                        fill[j] = i + 1
                        x = j % 50
                        y = math.floor(j / 50)
                        if x == 0:
                            for off in [-49, 1, 51]:
                                k = int(j) + off
                                next_steps[k] = 1
                        elif x == 49:
                            for off in [-51, -1, 49]:
                                k = int(j) + off
                                next_steps[k] = 1
                        elif y == 0:
                            for off in [49, 50, 51]:
                                k = int(j) + off
                                next_steps[k] = 1
                        elif y == 49:
                            for off in [-51, -50, -49]:
                                k = int(j) + off
                                next_steps[k] = 1
                steps = next_steps
            room.memory.pd.source_fills[source.id] = fill
            if visuals_on:
                for i in range(2500):
                    if fill[i] < 255:
                        red = str(min(255, fill[i] * 5))
                        non_red = str(255 - min(255, fill[i] * 5))
                        room.visual.text(str(fill[i]), i % 50, math.floor(i / 50), {'font': '0.6 serif', 'color': 'rgb(' + red + ', ' + non_red + ', ' + non_red + ')'})
            return 0
    return 1


def controller_fill(room, visuals_on):
    fill = {}
    terrain = room.getTerrain().getRawBuffer()
    for i in range(2500):
        if terrain[i] & 1:
            fill[i] = 255
        else:
            fill[i] = 0
    for i in range(50):
        for j in [i, 2450 + i, i * 50, i * 50 + 49]:
            if fill[j] == 0:
                fill[j] = -1
    steps = {}
    controller_index = room.controller.pos.y * 50 + room.controller.pos.x
    offset = [-51, -50, -49, -1, 1, 49, 50, 51]
    for off in offset:
        steps[controller_index + off] = 1
    for i in range(100):
        next_steps = {}
        for j in Object.keys(steps):
            if fill[j] == 0:
                fill[j] = i + 1
                for off in offset:
                    k = int(j) + off
                    next_steps[k] = 1
            elif fill[j] == -1:
                fill[j] = i + 1
                x = j % 50
                y = math.floor(j / 50)
                if x == 0:
                    for off in [-49, 1, 51]:
                        k = int(j) + off
                        next_steps[k] = 1
                elif x == 49:
                    for off in [-51, -1, 49]:
                        k = int(j) + off
                        next_steps[k] = 1
                elif y == 0:
                    for off in [49, 50, 51]:
                        k = int(j) + off
                        next_steps[k] = 1
                elif y == 49:
                    for off in [-51, -50, -49]:
                        k = int(j) + off
                        next_steps[k] = 1
        steps = next_steps
    room.memory.pd.controller_fill = fill
    if visuals_on:
        for i in range(2500):
            if fill[i] < 255:
                red = str(min(255, fill[i] * 5))
                non_red = str(255 - min(255, fill[i] * 5))
                room.visual.text(str(fill[i]), i % 50, math.floor(i / 50), {'font': '0.6 serif', 'color': 'rgb(' + red + ', ' + non_red + ', ' + non_red + ')'})
    return 1


def orth_wall_fill(room, visuals_on):
    fill = {}
    terrain = room.getTerrain().getRawBuffer()
    for i in range(2500):
        if [' ', 'r'].includes(room.memory.master_map[i]):
            fill[i] = 0
        else:
            fill[i] = 255
    for i in range(50):
        for j in [i, 2450 + i, i * 50, i * 50 + 49]:
            if fill[j] == 0:
                fill[j] = -1
    steps = {}
    offset = [-50, -1, 1, 50]
    for x in range(50):
        for y in range(50):
            index = y * 50 + x
            if not [' ','r'].includes(room.memory.master_map[i]):
                if x == 0:
                    for off in [-50, 1, 50]:
                        steps[index + off] = 1
                elif x == 49:
                    for off in [-50, -1, 50]:
                        steps[index + off] = 1
                elif y == 0:
                    for off in [-1, 50, 1]:
                        steps[index + off] = 1
                elif y == 49:
                    for off in [-1, -50, 1]:
                        steps[index + off] = 1
                else:
                    for off in offset:
                        steps[index + off] = 1
    for i in range(100):
        next_steps = {}
        for j in Object.keys(steps):
            if fill[j] == 0:
                fill[j] = i + 1
                for off in offset:
                    k = int(j) + off
                    next_steps[k] = 1
            elif fill[j] == -1:
                fill[j] = i + 1
                x = j % 50
                y = math.floor(j / 50)
                if x == 0:
                    for off in [-50, 1, 50]:
                        k = int(j) + off
                        next_steps[k] = 1
                elif x == 49:
                    for off in [-50, -1, 50]:
                        k = int(j) + off
                        next_steps[k] = 1
                elif y == 0:
                    for off in [-1, 50, 1]:
                        k = int(j) + off
                        next_steps[k] = 1
                elif y == 49:
                    for off in [-1, -50, 1]:
                        k = int(j) + off
                        next_steps[k] = 1
        steps = next_steps
    room.memory.pd.orth_wall_fill = fill
    if visuals_on:
        for i in range(2500):
            if fill[i] < 255:
                red = str(min(255, fill[i] * 25))
                non_red = str(255 - min(255, fill[i] * 25))
                room.visual.text(str(fill[i]), i % 50, math.floor(i / 50), {'font': '0.6 serif', 'color': 'rgb(' + red + ', ' + non_red + ', ' + non_red + ')'})
    return 1


def place_stamp(room, visuals_on):
    if not room.memory.pd.stamp_index:
        room.memory.pd.stamp_index = 0
    current_stamp_size = Memory.stamp_list[room.memory.pd.stamp_index][0]
    current_stamp_layout = Memory.stamp_list[room.memory.pd.stamp_index][1]
    best_spot = 0
    lowest_score = 9001
    
    for i in range(2500):
        if room.memory.pd.orth_wall_fill[i] >= current_stamp_size:
            score = room.memory.pd.controller_fill[i] * 3
            for s_id in Object.keys(room.memory.pd.source_fills):
                score += room.memory.pd.source_fills[s_id][i] * 2
            if score < lowest_score:
                lowest_score = score
                best_spot = i
    if best_spot:
        anchor_x = best_spot & 50 - (current_stamp_size - 1)
        anchor_y = math.floor(best_spot / 50) - (current_stamp_size - 1)
        for i in range(len(current_stamp_layout)):
            for j in range(len(current_stamp_layout[i])):
                x = anchor_x + j
                y = anchor_y + i
                room.memory.master_map[y * 50 + x] = current_stamp_layout[i][j]
    room.memory.pd.stamp_index += 1
    if len(Memory.stamp_list) > room.memory.pd.stamp_index:
        room.memory.planning_step -= 1
        return 0
    return 1

def finalize(room, visuals_on):
    del room.memory.planning_step
    del room.memory.pd
    room.memory.planned = 1
    return 0