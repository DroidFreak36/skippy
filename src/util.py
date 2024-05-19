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

#Serialize the oarts of our cached memory object that we want to persist into RawMemory
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
    number_persistent_room_keys = ['target_carry_parts', 'target_work_parts']
    string_persistent_room_keys = []
    json_persistent_room_keys = ['master_map']
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

