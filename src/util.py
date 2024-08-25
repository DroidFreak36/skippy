from defs import *
import math

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')



#Pull data from RawMemory into cached memory.
def parse_raw_memory():
    mem_string = RawMemory.get()
    if not mem_string or len(mem_string) < 2:
        mem_string = '{}'
    #mem_string = '{}'
    __pragma__ ('js', '{}', 'global.cached_memory = JSON.parse(mem_string);')



#Inject our cached memory into the Memory object instead of normal parsing
def use_cached_memory():
    __pragma__ ('js', '{}', 'delete global.Memory;')
    __pragma__ ('js', '{}', 'global.Memory = cached_memory;')
    __pragma__ ('js', '{}', 'RawMemory._parsed = cached_memory;')


def array_to_string(in_array):
    out_string = ''
    for thing in in_array:
        out_string += thing
    return out_string

def string_to_array(in_string):
    __pragma__ ('js', '{}', "let out_array = in_string.split('')")
    return out_array

#Serialize the parts of our cached memory object that we want to persist into RawMemory
def serialize_memory():
    __pragma__ ('js', '{}', 'delete RawMemory._parsed;')
    
    mem_string = '{'
    mem_string += '"creeps":{'
    is_first_creep = True
    string_persistent_creep_keys = ["role", "target_room", "target", "task"]
    json_persistent_creep_keys = ["tasq"]
    for creep_name in Object.keys(Memory.creeps):
        creep_mem = Memory.creeps[creep_name]
        if not is_first_creep:
            mem_string += ','
        mem_string += '"' + creep_name + '":{' #begin creep
        is_first_entry = True
        for key_name in string_persistent_creep_keys:
            if creep_mem[key_name]:
                if not is_first_entry:
                    mem_string += ','
                mem_string += '"' + key_name + '":"' + creep_mem[key_name] + '"'
                is_first_entry = False
        for key_name in json_persistent_creep_keys:
            if creep_mem[key_name]:
                if not is_first_entry:
                    mem_string += ','
                mem_string += '"' + key_name + '":' + JSON.stringify(creep_mem[key_name])
                is_first_entry = False
        is_first_creep = False
        mem_string += '}' #end creep
    mem_string += '},' #end creeps section
    mem_string += '"rooms":{'
    is_first_room = True
    number_persistent_room_keys = ['target_carry_parts', 'target_work_parts', 'core', 'lab_container', 'planned', 'built_rcl', 'built_amount', 'planned_rcl', 'planning_step']
    string_persistent_room_keys = []
    json_persistent_room_keys = ['master_map', 'current_map', 'source_labs']
    if not Memory.owned_rooms:
        Memory.owned_rooms = []
        for room_name in Object.keys(Game.rooms):
            room = Game.rooms[room_name]
            if room.controller != None and room.controller.my:
                Memory.owned_rooms.append(room_name)
    for room_name in Memory.owned_rooms:
        room_mem = Memory.rooms[room_name]
        if not is_first_room:
            mem_string += ','
        mem_string += '"' + room_name + '":{' #begin room
        is_first_entry = True
        for key_name in number_persistent_room_keys:
            if room_mem[key_name]:
                if not is_first_entry:
                    mem_string += ','
                mem_string += '"' + key_name + '":' + room_mem[key_name]
                is_first_entry = False
        for key_name in string_persistent_room_keys:
            if room_mem[key_name]:
                if not is_first_entry:
                    mem_string += ','
                mem_string += '"' + key_name + '":"' + room_mem[key_name] + '"'
                is_first_entry = False
        for key_name in json_persistent_room_keys:
            if room_mem[key_name]:
                if not is_first_entry:
                    mem_string += ','
                mem_string += '"' + key_name + '":' + JSON.stringify(room_mem[key_name])
                is_first_entry = False
        is_first_room = False
        mem_string += '}' #end room
    mem_string += '}' #end rooms section
    number_persistant_main_keys = ['avg_cpu_usage']
    for key_name in number_persistant_main_keys:
        if Memory[key_name]:
            mem_string += ',' + '"' + key_name + '":' + Memory[key_name]
    mem_string += '}' #end Memory
    
    RawMemory.set(mem_string)




#Initialize some parts of Memory if they are not initialized yet
def initialize_memory():
    if Memory.creeps == None:
        Memory.creeps = {}
    if Memory.rooms == None:
        Memory.rooms = {}
    if Memory.spawns == None:
        Memory.spawns = {}
    Memory.my_username = Game.structures[Object.keys(Game.structures)[0]].owner.username
    Memory.boost_tier = {
        [RESOURCE_UTRIUM_HYDRIDE]: 1,
        [RESOURCE_UTRIUM_OXIDE]: 1,
        [RESOURCE_KEANIUM_HYDRIDE]: 1,
        [RESOURCE_KEANIUM_OXIDE]: 1,
        [RESOURCE_LEMERGIUM_HYDRIDE]: 1,
        [RESOURCE_LEMERGIUM_OXIDE]: 1,
        [RESOURCE_ZYNTHIUM_HYDRIDE]: 1,
        [RESOURCE_ZYNTHIUM_OXIDE]: 1,
        [RESOURCE_GHODIUM_HYDRIDE]: 1,
        [RESOURCE_GHODIUM_OXIDE]: 1,
        
        [RESOURCE_UTRIUM_ACID]: 2,
        [RESOURCE_UTRIUM_ALKALIDE]: 2,
        [RESOURCE_KEANIUM_ACID]: 2,
        [RESOURCE_KEANIUM_ALKALIDE]: 2,
        [RESOURCE_LEMERGIUM_ACID]: 2,
        [RESOURCE_LEMERGIUM_ALKALIDE]: 2,
        [RESOURCE_ZYNTHIUM_ACID]: 2,
        [RESOURCE_ZYNTHIUM_ALKALIDE]: 2,
        [RESOURCE_GHODIUM_ACID]: 2,
        [RESOURCE_GHODIUM_ALKALIDE]: 2,
        
        [RESOURCE_CATALYZED_UTRIUM_ACID]: 3,
        [RESOURCE_CATALYZED_UTRIUM_ALKALIDE]: 3,
        [RESOURCE_CATALYZED_KEANIUM_ACID]: 3,
        [RESOURCE_CATALYZED_KEANIUM_ALKALIDE]: 3,
        [RESOURCE_CATALYZED_LEMERGIUM_ACID]: 3,
        [RESOURCE_CATALYZED_LEMERGIUM_ALKALIDE]: 3,
        [RESOURCE_CATALYZED_ZYNTHIUM_ACID]: 3,
        [RESOURCE_CATALYZED_ZYNTHIUM_ALKALIDE]: 3,
        [RESOURCE_CATALYZED_GHODIUM_ACID]: 3,
        [RESOURCE_CATALYZED_GHODIUM_ALKALIDE]: 3
    }
    Memory.owned_room_signs = [
        'skippy'
    ]
    Memory.remote_room_signs = [
        'boop'
    ]
    Memory.plan_key = {'w':STRUCTURE_WALL, 'R':null, 'r':STRUCTURE_ROAD, 'c':STRUCTURE_CONTAINER, 'S':STRUCTURE_SPAWN, 'l':STRUCTURE_LINK, 'x':STRUCTURE_EXTENSION, 'T':STRUCTURE_TOWER, 'L':STRUCTURE_LAB, 's':STRUCTURE_STORAGE, 't':STRUCTURE_TERMINAL, 'F':STRUCTURE_FACTORY, 'P':STRUCTURE_POWER_SPAWN, 'N':STRUCTURE_NUKER, 'X':STRUCTURE_EXTRACTOR, 'O':STRUCTURE_OBSERVER, ' ':null, 'E':null, 'e':null, 'W':null, 'U':null}


def update_current_map(room):
    if not room.memory.planned:
        return
    
    
    #Generate initial current map
    room.memory.current_map = []
    terrain = room.getTerrain().getRawBuffer()
    for i in range(2500):
        if room.memory.master_map[i] == 's' and room.controller.level >= 4:
            room.memory.current_map.append('s')
        elif room.memory.master_map[i] == 'w' and room.controller.level >= 5:
            room.memory.current_map.append('w')
        elif room.memory.master_map[i] == 't' and room.controller.level >= 6:
            room.memory.current_map.append('t')
        elif room.memory.master_map[i] == 'F' and room.controller.level >= 7:
            room.memory.current_map.append('F')
        elif room.memory.master_map[i] == 'N' and room.controller.level >= 8:
            room.memory.current_map.append('N')
        elif room.memory.master_map[i] == 'O' and room.controller.level >= 8:
            room.memory.current_map.append('O')
        elif room.memory.master_map[i] == 'P' and room.controller.level >= 8:
            room.memory.current_map.append('P')
        elif room.memory.master_map[i] == 'r' and room.controller.level >= 3:
            room.memory.current_map.append('r')
        elif terrain[i] % 2 == 1:
            room.memory.current_map.append('W')
        else:
            room.memory.current_map.append(' ')
    
    #Set up tracking for structures placed:
    placed = {'S':0, 'x':0, 'T':0, 'l':0, 'L':0}
    limit = {}
    limit['x'] = CONTROLLER_STRUCTURES[STRUCTURE_EXTENSION][room.controller.level]
    limit['l'] = CONTROLLER_STRUCTURES[STRUCTURE_LINK][room.controller.level]
    limit['S'] = CONTROLLER_STRUCTURES[STRUCTURE_SPAWN][room.controller.level]
    limit['L'] = CONTROLLER_STRUCTURES[STRUCTURE_LAB][room.controller.level]
    
    #Place spawns next to core
    for off in [-51, 51]:
        i = room.memory.core + off
        if room.memory.master_map[i] == 'S':
            room.memory.current_map[i] = 'S'
            placed['S'] += 1
            if placed['S'] >= limit['S']:
                break
    
    #Place final spawn if RCL8
    if placed['S'] < limit['S']:
        for i in range(2500):
            if room.memory.master_map[i] == 'S' and not room.memory.current_map[i] == 'S':
                room.memory.current_map[i] = 'S'
                placed['S'] += 1
    
    
    offset = [-51, -50, -49, -1, 1, 49, 50, 51]
    
    #Place fast filler extensions and containers
    if room.controller.level >= 2:
        for inserter_spot in [-100, -2, 2, 100]:
            i = room.memory.core + inserter_spot
            room.memory.current_map[i] = 'I'
            for off in offset:
                j = i + off
                if room.memory.master_map[j] == 'x' and not room.memory.current_map[j] == 'x' and placed['x'] < limit['x']:
                    room.memory.current_map[j] = 'x'
                    placed['x'] += 1
                elif room.memory.master_map[j] == 'R':
                    if room.memory.current_map[j] == 'r':
                        room.memory.current_map[j] = 'R'
                    else:
                        room.memory.current_map[j] = 'c'
            if placed['x'] >= limit['x']:
                break
    
    #Place more extensions
    if placed['x'] < limit['x']:
        core_dt = []
        for i in range(2500):
            core_dt.append(0)
        steps = {}
        steps[0] = [room.memory.core]
        for i in range(100):
            if steps[i] != None:
                for j in steps[i]:
                    check = [j - 51, j - 50, j - 49, j - 1, j + 1, j + 49, j + 50, j + 51]
                    for k in check:
                        if core_dt[k] == 0:
                            core_dt[k] = i + 1
                            if ['R', 'r'].includes(room.memory.master_map[k]):
                                if room.memory.current_map[k] == 'c' or room.memory.current_map[k] == 'R':
                                    room.memory.current_map[k] = 'R'
                                else:
                                    room.memory.current_map[k] = 'r'
                                if steps[i + 1] == None:
                                    steps[i + 1] = [k]
                                else:
                                    if not steps[i + 1].includes(k):
                                        steps[i + 1].append(k)
                            elif room.memory.master_map[k] == 'x' and room.memory.current_map[k] != 'x':
                                room.memory.current_map[k] = 'x'
                                placed['x'] += 1
                                if placed['x'] >= limit['x']:
                                    break
                    if placed['x'] >= limit['x']:
                        break
            if placed['x'] >= limit['x']:
                break
    
    
    
    
    
    #Place towers
    limit['T'] = CONTROLLER_STRUCTURES[STRUCTURE_TOWER][room.controller.level]
    if placed['T'] < limit['T']:
        for i in range(2500):
            if room.memory.master_map[i] == 'T' and room.memory.current_map[i] != 'T':
                room.memory.current_map[i] = 'T'
                placed['T'] += 1
                break
    if placed['T'] < limit['T']:
        for i in range(2500, -1, -1):
            if room.memory.master_map[i] == 'T' and room.memory.current_map[i] != 'T':
                room.memory.current_map[i] = 'T'
                placed['T'] += 1
                break
    if placed['T'] < limit['T']:
        for i in range(2500):
            mod_index = (i % 50) * 50 + math.floor(i / 50)
            if room.memory.master_map[mod_index] == 'T' and room.memory.current_map[mod_index] != 'T':
                room.memory.current_map[mod_index] = 'T'
                placed['T'] += 1
                break
    if placed['T'] < limit['T']:
        for i in range(2500, -1, -1):
            mod_index = (i % 50) * 50 + math.floor(i / 50)
            if room.memory.master_map[mod_index] == 'T' and room.memory.current_map[mod_index] != 'T':
                room.memory.current_map[mod_index] = 'T'
                placed['T'] += 1
                break
    if placed['T'] < limit['T']:
        for i in range(2500):
            if room.memory.master_map[i] == 'T' and room.memory.current_map[i] != 'T':
                room.memory.current_map[i] = 'T'
                placed['T'] += 1
                if placed['T'] >= limit['T']:
                    break
    
    #Place links and/or source containers.
    if room.controller.level >= 2:
        sources = room.find(FIND_SOURCES)
        for source in sources:
            i = source.pos.y * 50 + source.pos.x
            check = [i - 51, i - 50, i - 49, i - 1, i + 1, i + 49, i + 50, i + 51]
            for j in check:
                if room.memory.master_map[j] == 'c' or room.memory.master_map[j] == 'R':
                    if limit['l'] > placed['l']:
                        check1 = [j - 51, j - 50, j - 49, j - 1, j + 1, j + 49, j + 50, j + 51]
                        for k in check1:
                            if room.memory.master_map[k] == 'l' and room.memory.current_map[k] != 'l' and placed['l'] < limit['l']:
                                room.memory.current_map[k] = 'l'
                                placed['l'] += 1
                    else:
                        room.memory.current_map[j] = 'c'
        
    
    #Place labs, extractor and mineral container
    if room.controller.level >= 6:
        for i in room.memory.source_labs:
            room.memory.current_map[i] = 'L'
            placed['L'] += 1
        for j in range(2500):
            if room.memory.master_map[j] == 'X':
                room.memory.current_map[j] = 'X'
                check = [j - 51, j - 50, j - 49, j - 1, j + 1, j + 49, j + 50, j + 51]
                for k in check:
                    if room.memory.master_map[k] == 'c' or room.memory.master_map[k] == 'R':
                        if room.memory.current_map[k] == 'r':
                            room.memory.current_map[k] = 'R'
                        else:
                            room.memory.current_map[k] = 'c'
            elif room.memory.master_map[j] == 'L' and room.memory.current_map[j] != 'L' and placed['L'] < limit['L']: 
                room.memory.current_map[j] = 'L'
                placed['L'] += 1
    
    
    #Place updog
    if room.controller.level >= 2:
        x_start = max(room.controller.pos.x - 2, 0)
        x_end = min(room.controller.pos.x + 2, 49)
        y_start = max(room.controller.pos.y - 2, 0)
        y_end = min(room.controller.pos.y + 2, 49)
        for look_x in range(x_start, x_end + 1):
            for look_y in range(y_start, y_end + 1):
                index = look_y * 50 + look_x
                if room.memory.master_map[index] == 'U':
                    if room.controller.level == 8 and limit['l'] > placed['l']:
                        room.memory.current_map[index] = 'l'
                        placed['l'] += 1
                    else:
                        room.memory.current_map[index] = 'c'
    
    if room.controller.level >= 6:
        if room.memory.current_map[room.memory.lab_container] == 'r':
            room.memory.current_map[room.memory.lab_container] = 'R'
        else:
            room.memory.current_map[room.memory.lab_container] = 'c'
    


def get_core_ff(room):
    if room.memory.planned_rcl != room.controller.level:
        update_current_map(room)
        room.memory.planned_rcl = room.controller.level
        room.memory.built_rcl = 0
    if room.memory.core_ff_rcl == room.controller.level:
        return room.memory.core_ff
    room.memory.core_ff = []
    passable = {' ': 1, 'e': 1, 'E': 1, 'r': 1, 'R': 1, 'c': 1}
    edges = {0: 1, 49: 1}
    for i in range(2500):
        room.memory.core_ff.append(0)
    steps = {}
    steps[0] = [room.memory.core]
    for i in range(100):
        if steps[i] != None:
            for j in steps[i]:
                check = [j - 51, j - 50, j - 49, j - 1, j + 1, j + 49, j + 50, j + 51]
                for k in check:
                    if room.memory.current_map[k] == 0:
                        room.memory.current_map[k] = 1
                        if passable[room.memory.current_map[k]] and not edges[k % 50] and not edges[math.floor(k / 50)]:
                            if steps[i + 1] == None:
                                steps[i + 1] = [k]
                            else:
                                if not steps[i + 1].includes(k):
                                    steps[i + 1].append(k)
    room.memory.core_ff_rcl = room.controller.level
    return room.memory.core_ff


def construct_build_queue(room):
    build_queue = []
    
    #Tower
    for i in range(2500):
        if room.memory.current_map[i] == 'T':
            build_queue.append(i)
    #Spawn
    for i in range(2500):
        if room.memory.current_map[i] == 'S':
            build_queue.append(i)
    #FF containers
    source_containers = []
    up_containers = []
    for i in range(2500):
        if room.memory.current_map[i] == 'c' or room.memory.current_map[i] == 'R':
            check = [i - 51, i - 50, i - 49, i - 1, i + 1, i + 49, i + 50, i + 51]
            is_ff = 0
            for j in check:
                if j == room.memory.core:
                    is_ff = 1
            if is_ff:
                build_queue.append(i)
            else:
                if len(room.getPositionAt(i % 50, math.floor(i / 50)).findInRange(FIND_SOURCES, 1)):
                    source_containers.append(i)
                else:
                    up_containers.append(i)
    #FF extensions
    non_ff_exts = []
    for i in range(2500):
        if room.memory.current_map[i] == 'x':
            check = [i - 51, i - 50, i - 49, i - 1, i + 1, i + 49, i + 50, i + 51]
            is_ff = 0
            for j in check:
                if room.memory.current_map[j] == 'I':
                    is_ff = 1
            if is_ff:
                build_queue.append(i)
            else:
                non_ff_exts.append(i)
    #non-FF extensions
    for i in non_ff_exts:
        build_queue.append(i)
    #source containers
    for i in source_containers:
        build_queue.append(i)
    #storage
    for i in range(2500):
        if room.memory.current_map[i] == 's':
            build_queue.append(i)
    #upgrade container
    for i in up_containers:
        build_queue.append(i)
    
    room.memory.build_queue = build_queue


def manage_building(room):
    if not room.memory.planned:
        return
    if room.memory.built_rcl == room.controller.level:
        if room.memory.built_amount == len(room.find(FIND_STRUCTURES)):
            if room.memory.current_csite:
                del room.memory.current_csite
            return
    if room.memory.planned_rcl != room.controller.level:
        update_current_map(room)
        room.memory.planned_rcl = room.controller.level
        room.memory.built_rcl = 0
        del room.memory.build_queue
    
    if not room.memory.build_queue:
        construct_build_queue(room)
    
    if room.memory.current_csite:
        current_csite = Game.getObjectById(room.memory.current_csite)
        if not current_csite:
            del room.memory.current_csite
    else:
        current_csite = 0
    
    if current_csite and room.memory.next_csite and Game.getObjectById(room.memory.next_csite):
        return
    
    processed = 0
    s_type_map = {'T': STRUCTURE_TOWER, 'S': STRUCTURE_SPAWN, 's': STRUCTURE_STORAGE, 'c': STRUCTURE_CONTAINER, 'R': STRUCTURE_CONTAINER, 'x': STRUCTURE_EXTENSION}
    while processed < 2 and len(room.memory.build_queue) > processed:
        spot = room.memory.build_queue[processed]
        intended_code = room.memory.current_map[spot]
        intended_s_type = s_type_map[intended_code]
        structs_in_spot = room.getPositionAt(spot % 50, math.floor(spot / 50)).lookFor(LOOK_STRUCTURES)
        if len(structs_in_spot):
            is_done = 0
            for struct in structs_in_spot:
                if struct.structureType == intended_s_type:
                    is_done = 1
            if is_done:
                room.memory.build_queue.pop(processed)
                continue
            else:
                pass #Destroy bad structs?
        sites_in_spot = room.getPositionAt(spot % 50, math.floor(spot / 50)).lookFor(LOOK_CONSTRUCTION_SITES)
        if len(sites_in_spot):
            processed += 1
            if processed == 1:
                room.memory.current_csite = sites_in_spot[0].id
            if processed == 2:
                room.memory.next_csite = sites_in_spot[0].id
            continue
        if intended_s_type == STRUCTURE_SPAWN:
            if room.getPositionAt(spot % 50, math.floor(spot / 50)).inRangeTo(room.memory.core % 50, math.floor(room.memory.core / 50), 2) and room.getPositionAt(spot % 50, math.floor(spot / 50)).createConstructionSite(STRUCTURE_SPAWN, room.name + '-1') == OK:
                pass
            elif room.getPositionAt(spot % 50, math.floor(spot / 50)).createConstructionSite(STRUCTURE_SPAWN, room.name + '-2') == OK:
                pass
            elif room.getPositionAt(spot % 50, math.floor(spot / 50)).createConstructionSite(STRUCTURE_SPAWN, room.name + '-3') == OK:
                pass
        else:
            room.getPositionAt(spot % 50, math.floor(spot / 50)).createConstructionSite(intended_s_type)
        processed += 1
    
    if not len(room.memory.build_queue):
        room.memory.built_rcl = room.controller.level
        room.memory.built_amount = len(room.find(FIND_STRUCTURES))
    else:
        room.memory.built_rcl = 0
