import util
import creep_roles
import planning
import math
# defs is a package which claims to export all constants and some JavaScript objects, but in reality does
#  nothing. This is useful mainly when using an editor like PyCharm, so that it 'knows' that things like Object, Creep,
#  Game, etc. do exist.
from defs import *

# These are currently required for Transcrypt in order to use the following names in JavaScript.
# Without the 'noalias' pragma, each of the following would be translated into something like 'py_Infinity' or
#  'py_keys' in the output file.
__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


__pragma__ ('js', '{}', __include__ ('RoomVisual.js'))

def _master_map_visuals(room_name):
    if not room_name:
        del Memory.master_map_visual_room
    else:
        Memory.master_map_visual_room = room_name

__pragma__ ('js', '{}', 'global.master_map_visuals = _master_map_visuals')

#====== Start of main code ======

print(' ======= Global reset! Time of reset: ' + Game.time + ' ======= ')

#Initial pulling of parsed memory into cached memory
util.parse_raw_memory()
util.use_cached_memory()
memory_time = Game.time


#Initialize some parts of Memory if they are not initialized yet
util.initialize_memory()
creep_roles.init_cache()
planning.init_cache()


#This function turns the long creep body array into a shorter form for readability in the console
def body_shorthand(body):
    body_count = {}
    for part in body:
        if body_count[part] == None:
            body_count[part] = 1
        else:
            body_count[part] += 1
    outstring = ''
    for part_type in Object.keys(body_count):
        outstring += '' + body_count[part_type] + part_type + ' '
    return outstring

        
def main():
    """
    Main game logic loop.
    """
    
    try:
        
        if memory_time != Game.time:
            if Game.time - memory_time > 1:
                util.parse_raw_memory()
            util.use_cached_memory()
            memory_time = Game.time
    
    
        #This catalogues your owned rooms.
        Memory.owned_rooms = []
        for room_name in Object.keys(Game.rooms):
            room = Game.rooms[room_name]
            if room.controller != None and room.controller.my:
                if Memory.rooms[room_name] == None:
                    Memory.rooms[room_name] = {}
                Memory.owned_rooms.append(room_name)
                Memory.rooms[room_name].current_work_parts = 0
                Memory.rooms[room_name].current_carry_parts = 0
        
        
        #This clears out memory of creeps, rooms, and spawns that no longer exist.
        for name in Object.keys(Memory.creeps):
            if Game.creeps[name] == None:
                print('RIP ' + name)
                del Memory.creeps[name]
        for name in Object.keys(Memory.rooms):
            if Game.rooms[name] == None:
                del Memory.rooms[name]
        for name in Object.keys(Memory.spawns):
            if Game.spawns[name] == None:
                del Memory.spawns[name]
        
        
        #This runs the action function for each creep, as defined in the creep_roles.py module.
        for name in Object.keys(Game.creeps):
            creep = Game.creeps[name]
            if not creep.spawning:
                creep_roles.do_action(creep)
        
        
        #This tries to activate safe mode if your spawn gets damaged.
        for spawn_name in Object.keys(Game.spawns):
            spawn = Game.spawns[spawn_name]
            if spawn.hits < spawn.hitsMax and spawn.room.controller.my:
                spawn.room.controller.activateSafeMode()
        
        
        #All spawning related code runs every 3 ticks, because creep spawning duration is always a mutliple of 3 ticks.
        if Game.time % 3 == 0:
            #This prepares for unique creep names (because having multiple creeps with the same name is not allowed).
            timestamp = Game.time.toString().split("")
            timecode = 'snek '
            for i in range(4):
                char = timestamp[i + len(timestamp) - 4]
                if char == '0':
                    timecode += '--'
                if char == '1':
                    timecode += '-~'
                if char == '2':
                    timecode += '~-'
                if char == '3':
                    timecode += '~~'
                if char == '4':
                    timecode += '=-'
                if char == '5':
                    timecode += '-='
                if char == '6':
                    timecode += '=='
                if char == '7':
                    timecode += '=~'
                if char == '8':
                    timecode += '~='
                if char == '9':
                    timecode += '<>'
            timecode += ':3'
        
        
            #This catalogues how many active work parts our workers have and how many active carry parts our haulers have.
            for name in Object.keys(Game.creeps):
                creep = Game.creeps[name]
                if creep.memory.role == 'worker' and Memory.rooms[creep.memory.target_room] != None:
                    Memory.rooms[creep.memory.target_room].current_work_parts += creep.getActiveBodyparts(WORK)
                if creep.memory.role == 'hauler' and (creep.ticksToLive > 150 or creep.spawning) and Memory.rooms[creep.memory.target_room] != None:
                    Memory.rooms[creep.memory.target_room].current_carry_parts += creep.getActiveBodyparts(CARRY)
            
            #This number tracks how many total creeps have been spawned so far on this tick.
            num_spawns = 0
            
            for room_name in Memory.owned_rooms:
                room = Game.rooms[room_name]
                
                #This finds all of your spawns in the room.
                spawns = room.find(FIND_MY_SPAWNS)
                
                #This keeps track of how much energy we've used on spawning creeps so far this tick (for cases where we have multiple spawns in a room)
                used_energy = 0
                
                for spawn in spawns:
                    if not spawn.spawning and spawn.isActive():
                        #This constructs a creep name from the timecode we made earlier, adding an 's' to the front for every previous creep we've spawned on this tick.
                        name = ''
                        for i in range(num_spawns):
                            name += 's'
                        name += timecode
                        
                        
                        #This creates a list of all of our creeps with this room as their target room, which we can filter later.
                        creep_names = filter(lambda n: Game.creeps[n].memory.target_room == room.name, Object.keys(Game.creeps))
                        current_creeps = []
                        for creep_name in creep_names:
                            current_creeps.append(Game.creeps[creep_name])
                        
                        #Check how many miners we have, because we might have to spawn smaller miners if we don't have any.
                        num_miners = len(filter(lambda c: c.memory.role == 'miner', current_creeps))
                        
                        
                        #Spawn miners if we have at least one hauler.
                        sources = room.find(FIND_SOURCES)
                        if Memory.rooms[room_name].current_carry_parts > 0:
                            spawned = False
                            for source in sources:
                                current_miners = filter(lambda c: c.memory.role == 'miner' and c.memory.target == source.id and (c.spawning or (c.ticksToLive > 50)), current_creeps)
                                if len(current_miners) == 0:
                                    energy_to_use = room.energyCapacityAvailable
                                    if room.memory.no_miner_ticks > 20:
                                        energy_to_use = room.energyAvailable
                                    miner_multiple = min(3, math.floor(energy_to_use / 250))
                                    body = []
                                    cost = 0
                                    for i in range(miner_multiple):
                                        body.append(WORK)
                                        body.append(WORK)
                                        cost += 200
                                    for i in range(miner_multiple):
                                        body.append(MOVE)
                                        cost += 50
                                    if room.energyAvailable - used_energy >= cost:
                                        result = spawn.spawnCreep(body, name, {'memory': {'target_room': room.name, 'role': "miner", 'target': source.id}})
                                        if result == OK:
                                            room.memory.no_miner_ticks = 0
                                            num_spawns += 1
                                            used_energy += cost
                                        elif result == ERR_NOT_ENOUGH_ENERGY and len(current_miners) == 0:
                                            if room.memory.no_miner_ticks == None:
                                                room.memory.no_miner_ticks = 0
                                            room.memory.no_miner_ticks += 1
                                    spawned = True
                                    break
                            if spawned:
                                continue
                        
                        
                        #This calculates the income based on the number of sources and the size of our miners. That is used to scale our hauler and worker spawning.
                        miner_multiple = min(3, math.floor(room.energyCapacityAvailable / 250))
                        income = len(sources) * min(10, 4 * miner_multiple)
                        
                        
                        #Spawn haulers if we have less carry parts than three times our income.
                        if Memory.rooms[room_name].current_carry_parts < income * 3:
                            #Use the current energy available in the room rather than the maximum if there are no haulers currently.
                            energy_to_use = spawn.room.energyCapacityAvailable
                            if Memory.rooms[room_name].current_carry_parts == 0:
                                energy_to_use = spawn.room.energyAvailable
                            hauler_multiple = min(16, math.floor(energy_to_use / 150))
                            part_change = 0
                            body = []
                            cost = 0
                            for i in range(hauler_multiple):
                                body.append(CARRY)
                                body.append(CARRY)
                                body.append(MOVE)
                                part_change += 2
                                cost += 150
                            if room.energyAvailable - used_energy >= cost:
                                result = spawn.spawnCreep(body, name, {'memory': {'target_room': room.name, 'role': "hauler"}})
                                if result == OK:
                                    num_spawns += 1
                                    used_energy += cost
                                    Memory.rooms[room_name].current_carry_parts += part_change
                                    print(spawn.room.name + ' spawned hauler ' + name + ' with body ' + body_shorthand(body))
                            continue
                        
                        
                        #Spawn workers if we have less work parts than our income.
                        if Memory.rooms[room_name].current_work_parts < income:
                            worker_multiple = min(16, math.floor(spawn.room.energyCapacityAvailable / 200))
                            body = []
                            cost = 0
                            part_change = 0
                            for i in range(worker_multiple):
                                body.append(WORK)
                                part_change += 1
                                cost += 100
                            for i in range(worker_multiple):
                                body.append(CARRY)
                                cost += 50
                            for i in range(worker_multiple):
                                body.append(MOVE)
                                cost += 50
                            if room.energyAvailable - used_energy >= cost:
                                result = spawn.spawnCreep(body, name, {'memory': {'target_room': room.name, 'role': "worker"}})
                                if result == OK:
                                    num_spawns += 1
                                    used_energy += cost
                                    Memory.rooms[room_name].current_work_parts += part_change
                                    print(spawn.room.name + ' spawned worker ' + name + ' with body ' + body_shorthand(body))
                            continue
                        
                        
                        #If we got here without trying to spawn anything, skip the remaining spawns.
                        break

        for room_name in Memory.owned_rooms:
            room = Game.rooms[room_name]
            if not room.memory.planned:
                while Game.cpu.tickLimit - Game.cpu.getUsed() > 200 and Game.cpu.bucket > 800 and not room.memory.planned:
                    print('Planning in ' + room.name + ' with step ' + room.memory.planning_step)
                    planning.plan_step(room.name, False)
                #if Game.cpu.tickLimit - Game.cpu.getUsed() > 200 and Game.cpu.bucket > 800:
                #    print('Planning in ' + room.name + ' with step ' + room.memory.planning_step)
                #    planning.plan_step(room.name, True)
            else:
                util.manage_building(room)
        
        
        if Memory.master_map_visual_room:
            room = Game.rooms[Memory.master_map_visual_room]
            if room:
                for i in range(2500):
                    char = room.memory.master_map[i]
                    if char == 'R':
                        room.visual.structure(i % 50, math.floor(i / 50), STRUCTURE_CONTAINER)
                        room.visual.structure(i % 50, math.floor(i / 50), STRUCTURE_ROAD)
                    elif char == 'U':
                        room.visual.structure(i % 50, math.floor(i / 50), STRUCTURE_CONTAINER)
                        room.visual.structure(i % 50, math.floor(i / 50), STRUCTURE_LINK)
                    else:
                        s_type = Memory.plan_key[char]
                        if s_type:
                            room.visual.structure(i % 50, math.floor(i / 50), s_type)
                room.visual.connectRoads()
        
        
        #It's likely that you won't fully utilize your CPU when starting out, so this will use your excess CPU to generate pixels that you can sell later.
        if Game.cpu.generatePixel and Game.cpu.bucket == 10000 and Game.cpu.getUsed() < Game.cpu.limit and ['shard0', 'shard1', 'shard2', 'shard3'].includes(Game.shard.name):
            if Game.cpu.generatePixel() == OK:
                print(' ======= Generating pixel! Press F to pay respects to your bucket! ======= ')
        
        util.serialize_memory()
        if not Memory.avg_cpu_usage:
            Memory.avg_cpu_usage = 0
        Memory.avg_cpu_usage = .99 * Memory.avg_cpu_usage + .01 * Game.cpu.getUsed()
        #print(Game.cpu.getUsed() + ' CPU used on game tick.')
    except:
        print('Errored - performing emergency serialize')
        util.serialize_memory()
        raise
        

module.exports.loop = main