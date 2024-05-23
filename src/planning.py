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

"""

General base planning module notes:

The index values used at many points in this planner represent positions in the room with the relationship "i = y * 50 + x". This flattens the 2D space into 1D so arrays of length 2500 can be used to represent the whole room. This is also the same type of index the game uses internally for terrain data, as one can see by using "room.getTerrain().getRawBuffer()", which this planner uses any time it wants terrain data.

This planner uses singe characters to represent each structure type (or special codes to represent special structures). The code are defined in Memory.plan_key (by the util module), except for the special codes, but here's a human-readable key that includes the special ones:

' ' - Nothing
'W' - Natural wall
'E' - Exclusion zone (where structures should not be placed)
'e' - Special exclusion zone for controller container spots
'U' - Link or container (for upgrade)
'R' - Road and container
'r' - Road
'w' - Constructed wall
'c' - Container
'S' - Spawn
'l' - Link
'x' - Extensions
'T' - Tower
'L' - Lab
's' - Storage
't' - Terminal
'F' - Factory
'P' - Power spawn
'N' - Nuker
'X' - Extractor
'O' - Observer

In this planner, maps are often used as sets, by setting the value of things that should be in the set to 1 and deleting (or never inserting) things that should not be in the set. This is for greater performance compared to lists, and because actual sets would likely not translate to JS very well. These maps-as-sets do translate well to JS and perform very well.

"""


def init_cache():
    #This lists the planning step functions in the order that they are executed (although steps can send the execution back to a previous step by editing the step counter, if needed).
    Memory.planning_steps = [
        planning_start,
        source_fills,
        controller_fill,
        orth_wall_fill,
        place_stamp,
        finalize
    ]
    #This defines the stamps as 2D arrays, with the character codes that represent the structures in them.
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
    room = Game.rooms[room_name]
    if room: #Failsafe in case we somehow attempt to plan a room we don't have vision on.
        #Set planning step to the first step if it is not set
        if not room.memory.planning_step:
            room.memory.planning_step = 0
        #Run the planning function as defined by the planning steps list in Memory.
        planning_function = Memory.planning_steps[room.memory.planning_step]
        if planning_function(room, visuals_on): #If the function returns a truthy value, move to the next step.
            room.memory.planning_step += 1

def planning_start(room, visuals_on):
    #Create the planning data object if it does not exist.
    if not room.memory.pd:
        room.memory.pd = {}
    #Create the master map, initialized with the natural walls.
    terrain = room.getTerrain().getRawBuffer()
    room.memory.master_map = []
    for i in range(2500):
        if terrain[i] & TERRAIN_MASK_WALL:
            room.memory.master_map.append('W')
        else:
            room.memory.master_map.append(' ')
    #Fill in an exclusion zone on the exits and the adjacent tiles.
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
    #Create the source fills object in planning data, if it doesn't exist.
    if not room.memory.pd.source_fills:
        room.memory.pd.source_fills = {}
    for source in sources:
        if not room.memory.pd.source_fills[source.id]: #Skips this source if it has already had the fill made for it.
            #Initialize the fill to have 255 on the walls and zero elsewhere.
            fill = {}
            terrain = room.getTerrain().getRawBuffer()
            for i in range(2500):
                if terrain[i] & 1:
                    fill[i] = 255
                else:
                    fill[i] = 0
            #Exit tiles are set to -1 (to avoid going out of bounds later)
            for i in range(50):
                for j in [i, 2450 + i, i * 50, i * 50 + 49]:
                    if fill[j] == 0:
                        fill[j] = -1
            #Set the initial steps to the tiles adjacent to the source
            steps = {}
            source_index = source.pos.y * 50 + source.pos.x
            offset = [-51, -50, -49, -1, 1, 49, 50, 51]
            for off in offset:
                steps[source_index + off] = 1
            #The main flood fill loop
            for i in range(100):
                next_steps = {} #The steps set for the next iteration of the loop
                for j in Object.keys(steps): #For every entry in the current steps
                    if fill[j] == 0: #Zero means this tile is unfilled and not an exit.
                        fill[j] = i + 1 #Set the tile
                        for off in offset: #Add all adjacent tiles to the steps for the next iteration of the main loop
                            k = int(j) + off
                            next_steps[k] = 1
                    elif fill[j] == -1: #One means this tile is unfilled and is an exit.
                        fill[j] = i + 1 #Set the tile
                        #Translate the index to x and y, for ease of checking which exit we're next to.
                        x = j % 50
                        y = math.floor(j / 50)
                        #Depending on which exit we're next to, add the tiles inside and adjacent to it to the steps for the next iteration of the main loop
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
                steps = next_steps #Set the steps set for the next iteration of the loop to the next steps set we constructed.
            room.memory.pd.source_fills[source.id] = fill #Set the memory entry to the fill we created
            #If visuals are on, render the flood fill values as colored numbers.
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
    steps = {}
    offset = [-50, -1, 1, 50]
    for x in range(50):
        for y in range(50):
            index = y * 50 + x
            if fill[index] == 255:
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
        if room.memory.pd.orth_wall_fill[i] >= current_stamp_size and room.memory.pd.orth_wall_fill[i] < 255:
            score = room.memory.pd.controller_fill[i] * 3
            for s_id in Object.keys(room.memory.pd.source_fills):
                score += room.memory.pd.source_fills[s_id][i] * 2
            if score < lowest_score:
                lowest_score = score
                best_spot = i
    if best_spot:
        if room.memory.pd.stamp_index == 0:
            room.memory.core = best_spot
        if room.memory.pd.stamp_index = 2
            room.memory.source_labs = [best_spot - 50, best_spot + 1]
        anchor_x = best_spot % 50 - (current_stamp_size - 1)
        anchor_y = math.floor(best_spot / 50) - (current_stamp_size - 1)
        for i in range(len(current_stamp_layout)):
            for j in range(len(current_stamp_layout[i])):
                x = anchor_x + j
                y = anchor_y + i
                if current_stamp_layout[i][j] != ' ':
                    room.memory.master_map[y * 50 + x] = current_stamp_layout[i][j]
    if visuals_on:
        for i in range(2500):
            if room.memory.pd.orth_wall_fill[i] < 255:
                red = str(min(255, room.memory.pd.orth_wall_fill[i] * 25))
                non_red = str(255 - min(255, room.memory.pd.orth_wall_fill[i] * 25))
                room.visual.text(str(room.memory.pd.orth_wall_fill[i]), i % 50, math.floor(i / 50), {'font': '0.6 serif', 'color': 'rgb(' + red + ', ' + non_red + ', ' + non_red + ')'})
    
        room.visual.circle(best_spot % 50, math.floor(best_spot / 50), {'radius': 0.5, 'fill': '#ff0000'})
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