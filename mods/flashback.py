# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Flashback v1.1 - Let's see that again (Time-Accurate Edition)

Record what happens, and see it happen again.
Plays recordings by creating passthrough ghosts that try to imitate what happened.
Now with accurate timing for node spawning, despawning, and attribute changes!
"""

import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.spaz import Spaz
from math import atan2, degrees, pi
from time import perf_counter as MS
from threading import Lock
from babase import Plugin

__version__ = "1.1"

_og = None
_recording_active = False
_playback_active = False
_recorded_data = {}
_recorded_props = {}
_recording_t0 = None
_monitor_timer = None
_lock = Lock()
_ghost_refs = []  # Keep strong references to ghost delegates
_ghost_nodes = []  # Keep references to all ghost nodes for cleanup
_real_to_ghost_map = {}  # Map real node IDs to their ghost counterparts

SPAZ_CONSTRUCTOR_ARGS = ['color', 'highlight', 'character', 'source_player']
STRICT_BLACKLIST = [
    'knockout', 'velocity', 'damage', 'damage_smoothed',
    'position', 'position_forward', 'position_center',
    'torso_position', 'punch_momentum_linear', 'punch_momentum_angular',
    'punch_velocity', 'punch_power', 'punch_position'
]

yaw = lambda p,q:(degrees(atan2(q[0]-p[0],q[2]-p[2])+pi))%360
_say = lambda t,**k: print(t)

def ghost(c, s=0.7):
    """Desaturate"""
    r,g,b = c
    if max(r,g,b) > 1.0: r,g,b = r/255,g/255,b/255
    l = 0.299*r + 0.587*g + 0.114*b
    return ((r+(l-r)*s)*0.6, (g+(l-g)*s)*0.6, (b+(l-b)*s)*0.6)

_ghost_material = None

def gmat():
    """Creates and returns the ghost material."""
    global _ghost_material
    if _ghost_material is None:
        shared = SharedObjects.get()
        _ghost_material = bs.Material()
        _ghost_material.add_actions(
            conditions=(
                ('they_dont_have_material', _ghost_material)
            ),
            actions=(
                ('modify_part_collision', 'collide', False)
            )
        )
        _ghost_material.add_actions(
            conditions=(
                ('they_have_material', shared.footing_material),
                'and',
                ('they_dont_have_material', shared.object_material)
            ),
            actions=(
                ('modify_part_collision', 'collide', True)
            )
        )
    return _ghost_material

def rec(nid, i, j):
    """Record single action"""
    if nid in _recorded_data and _recording_t0 is not None:
        t = MS() - _recording_t0
        _recorded_data[nid]['moves'][t] = (i, j)

def _create_input_patch(og, R, nid):
    """Creates a dictionary of patched input handlers for the Spaz delegate."""
    def jp(): og['jp'](); R(0, 1)
    def bp(): og['bp'](); R(1, 1)
    def pp(): og['pp'](); R(2, 1)
    def up(): og['up'](); R(3, 1)
    def jr(): og['jr'](); R(0, 0)
    def br(): og['br'](); R(1, 0)
    def pr(): og['pr'](); R(2, 0)
    def ur(): og['ur'](); R(3, 0)
    def lr(v): og['lr'](v); R(6, v)
    def ud(v): og['ud'](v); R(5, v)
    def rn(v): og['rn'](v); R(4, v)
    return {
        'lr': lr, 'ud': ud, 'jp': jp, 'jr': jr,
        'bp': bp, 'br': br, 'pp': pp, 'pr': pr,
        'up': up, 'ur': ur, 'rn': rn
    }

def _get_node_attrs(n, node_type):
    """Extract all non-blacklisted attributes from a node."""
    at = {}
    for i in dir(n):
        if i.startswith('_'): continue
        if i in STRICT_BLACKLIST: continue
        if i in ['node', 'getdelegate']: continue
        v = getattr(n, i)
        if callable(v): continue
        at[i] = v
    return at

def patch(*a, **k):
    """Patched newnode"""
    n = _og(*a, **k)
    if _recording_active and not _playback_active and _recording_t0 is not None:
        t = a[0] if a else k.get('type')
        spawn_time = MS() - _recording_t0
        
        if t == 'spaz':
            with _lock:
                nid = id(n)
                o = n.getdelegate(object)
                og = {
                    'lr': o.on_move_left_right, 'ud': o.on_move_up_down,
                    'jp': o.on_jump_press, 'jr': o.on_jump_release,
                    'bp': o.on_bomb_press, 'br': o.on_bomb_release,
                    'pp': o.on_pickup_press, 'pr': o.on_pickup_release,
                    'up': o.on_punch_press, 'ur': o.on_punch_release,
                    'rn': o.on_run
                }
                at = _get_node_attrs(n, 'spaz')
                at['start_position'] = n.position
                at['fpos'] = n.position_forward
                
                _recorded_data[nid] = {
                    'node': n,
                    'og': og,
                    'spawn_time': spawn_time,
                    'despawn_time': None,
                    'initial_attrs': at,
                    'attr_changes': {},
                    'moves': {},
                    'last_attrs': at.copy()
                }
                
                R = lambda i,j: rec(nid, i, j)
                patched_methods = _create_input_patch(og, R, nid)
                o.on_move_left_right = patched_methods['lr']
                o.on_move_up_down = patched_methods['ud']
                o.on_jump_press = patched_methods['jp']
                o.on_jump_release = patched_methods['jr']
                o.on_bomb_press = patched_methods['bp']
                o.on_bomb_release = patched_methods['br']
                o.on_pickup_press = patched_methods['pp']
                o.on_pickup_release = patched_methods['pr']
                o.on_punch_press = patched_methods['up']
                o.on_punch_release = patched_methods['ur']
                o.on_run = patched_methods['rn']
            
        elif t == 'prop':
            with _lock:
                nid = id(n)
                at = _get_node_attrs(n, 'prop')
                at['start_position'] = n.position
                
                _recorded_props[nid] = {
                    'node': n,
                    'spawn_time': spawn_time,
                    'despawn_time': None,
                    'initial_attrs': at,
                    'attr_changes': {},
                    'last_attrs': at.copy()
                }
    return n

def _monitor_nodes():
    """Monitor all tracked nodes for existence and attribute changes."""
    if not _recording_active or _playback_active or _recording_t0 is None:
        return
    
    current_time = MS() - _recording_t0
    
    with _lock:
        # Monitor spaz nodes
        for nid, data in list(_recorded_data.items()):
            n = data['node']
            if not n or not n.exists():
                # Node disappeared
                if data['despawn_time'] is None:
                    data['despawn_time'] = current_time
                continue
            
            # Check for attribute changes
            current_attrs = _get_node_attrs(n, 'spaz')
            changed_attrs = {}
            
            for key, val in current_attrs.items():
                if key in ['start_position', 'fpos']:
                    continue
                old_val = data['last_attrs'].get(key)
                # Compare values (handle tuples, lists, primitives)
                if old_val != val:
                    changed_attrs[key] = val
                    data['last_attrs'][key] = val
            
            if changed_attrs:
                data['attr_changes'][current_time] = changed_attrs
        
        # Monitor prop nodes
        for nid, data in list(_recorded_props.items()):
            n = data['node']
            if not n or not n.exists():
                # Node disappeared
                if data['despawn_time'] is None:
                    data['despawn_time'] = current_time
                continue
            
            # Check for attribute changes
            current_attrs = _get_node_attrs(n, 'prop')
            current_attrs['position'] = n.position
            current_attrs['velocity'] = n.velocity
            changed_attrs = {}
            
            for key, val in current_attrs.items():
                if key == 'start_position':
                    continue
                old_val = data['last_attrs'].get(key)
                if old_val != val:
                    changed_attrs[key] = val
                    data['last_attrs'][key] = val
            
            if changed_attrs:
                data['attr_changes'][current_time] = changed_attrs

def record():
    """record -> start the spy that records stuff. Overwrites previous recording."""
    global _og, _recording_active, _recorded_data, _recorded_props, _recording_t0, _monitor_timer
    
    if _recording_active:
        _say('Recording is already active. Stopping previous...', color=(1,1,0))
        stop()
    
    _recorded_data.clear()
    _recorded_props.clear()
    _recording_t0 = MS()  # Global timestamp
    
    if _og is None:
        _og = bs.newnode
        bs.newnode = patch
    
    _recording_active = True
    
    a = bs.get_foreground_host_activity()
    if not a:
        _say('No active game!')
        return
        
    with a.context:
        players = a.players
        
        # Track existing spaz nodes (spawn_time = 0)
        existing = [
            n for n in bs.getnodes()
            if n.getnodetype() == 'spaz'
            and n.exists()
            and not n.getdelegate(object)._dead
        ]
        
        for n in existing:
            with _lock:
                nid = id(n)
                o = n.getdelegate(object)
                og = {
                    'lr': o.on_move_left_right, 'ud': o.on_move_up_down,
                    'jp': o.on_jump_press, 'jr': o.on_jump_release,
                    'bp': o.on_bomb_press, 'br': o.on_bomb_release,
                    'pp': o.on_pickup_press, 'pr': o.on_pickup_release,
                    'up': o.on_punch_press, 'ur': o.on_punch_release,
                    'rn': o.on_run
                }
                at = _get_node_attrs(n, 'spaz')
                at['start_position'] = n.position
                at['fpos'] = n.position_forward
                
                _recorded_data[nid] = {
                    'node': n,
                    'og': og,
                    'spawn_time': 0.0,
                    'despawn_time': None,
                    'initial_attrs': at,
                    'attr_changes': {},
                    'moves': {},
                    'last_attrs': at.copy()
                }
                
                R = lambda i,j,nid=nid: rec(nid, i, j)
                patched_methods = _create_input_patch(og, R, nid)
                o.on_move_left_right = patched_methods['lr']
                o.on_move_up_down = patched_methods['ud']
                o.on_jump_press = patched_methods['jp']
                o.on_jump_release = patched_methods['jr']
                o.on_bomb_press = patched_methods['bp']
                o.on_bomb_release = patched_methods['br']
                o.on_pickup_press = patched_methods['pp']
                o.on_pickup_release = patched_methods['pr']
                o.on_punch_press = patched_methods['up']
                o.on_punch_release = patched_methods['ur']
                o.on_run = patched_methods['rn']
                
                for p in players:
                    if p.actor and p.actor.node == n:
                        p.actor.disconnect_controls_from_player()
                        p.actor.connect_controls_to_player()
                        break
        
        # Track existing prop nodes (spawn_time = 0)
        existing_props = [
            n for n in bs.getnodes()
            if n.getnodetype() == 'prop'
            and n.exists()
        ]
        
        for n in existing_props:
            with _lock:
                nid = id(n)
                at = _get_node_attrs(n, 'prop')
                at['start_position'] = n.position
                
                _recorded_props[nid] = {
                    'node': n,
                    'spawn_time': 0.0,
                    'despawn_time': None,
                    'initial_attrs': at,
                    'attr_changes': {},
                    'last_attrs': at.copy()
                }
    
    # Start monitoring timer
    _monitor_timer = bs.Timer(0.01, _monitor_nodes, repeat=True)
    
    _say('Recording started! History cleared.', color=(0,1,0))

def stop():
    """stop -> stops recording, doesn't delete anything."""
    global _recording_active, _monitor_timer
    
    if not _recording_active:
        _say('Recording is not active.', color=(1,1,0))
        return
    
    # Kill the monitoring timer
    _monitor_timer = None
    
    with _lock:
        for nid, data in list(_recorded_data.items()):
            if data['node'] and data['node'].exists():
                o = data['node'].getdelegate(object)
                if o and 'og' in data:
                    og = data['og']
                    o.on_move_left_right = og['lr']
                    o.on_move_up_down = og['ud']
                    o.on_jump_press = og['jp']
                    o.on_jump_release = og['jr']
                    o.on_bomb_press = og['bp']
                    o.on_bomb_release = og['br']
                    o.on_pickup_press = og['pp']
                    o.on_pickup_release = og['pr']
                    o.on_punch_press = og['up']
                    o.on_punch_release = og['ur']
                    o.on_run = og['rn']
                    
                    a = bs.get_foreground_host_activity()
                    if a:
                        for p in a.players:
                            if p.actor and p.actor.node == data['node']:
                                p.actor.disconnect_controls_from_player()
                                p.actor.connect_controls_to_player()
                                break
            
            data['node'] = None
            if 'og' in data:
                del data['og']
    
    _recording_active = False
    _say('Recording stopped! History saved.', color=(1,0,0))

def play():
    """play -> plays recorded stuff with time-accurate spawning/despawning."""
    global _playback_active, _recording_active, _ghost_refs, _ghost_nodes, _real_to_ghost_map
    
    if _playback_active:
        _say('Already playing! Wait for current playback to finish.', color=(1,1,0))
        return
    if not _recorded_data and not _recorded_props:
        _say('No history recorded. Call record() first.', color=(1,1,0))
        return
    if _recording_active:
        _say('Stopping recording to start playback...', color=(1,1,0))
        stop()
    
    # Clear previous ghost references
    _ghost_refs.clear()
    _ghost_nodes.clear()
    _real_to_ghost_map.clear()
    
    with _lock:
        snap = {
            k: {
                'spawn_time': v['spawn_time'],
                'despawn_time': v['despawn_time'],
                'initial_attrs': v['initial_attrs'].copy(),
                'attr_changes': v['attr_changes'].copy(),
                'moves': v['moves'].copy(),
                'real_nid': k  # Keep track of original real node ID
            }
            for k, v in _recorded_data.items()
        }
        snap_props = {
            k: {
                'spawn_time': v['spawn_time'],
                'despawn_time': v['despawn_time'],
                'initial_attrs': v['initial_attrs'].copy(),
                'attr_changes': v['attr_changes'].copy(),
                'real_nid': k  # Keep track of original real node ID
            }
            for k, v in _recorded_props.items()
        }
    
    _say(f'Found {len(snap)} spazzes and {len(snap_props)} props to replay', color=(1,1,0))
    _playback_active = True
    
    a = bs.get_foreground_host_activity()
    if not a:
        _playback_active = False
        return
        
    with a.context:
        ghost_mat = gmat()
        
        # Calculate max playback time
        max_playback_time = 0.0
        for sp in snap.values():
            if sp['despawn_time'] is not None:
                max_playback_time = max(max_playback_time, sp['despawn_time'])
            if sp['moves']:
                max_playback_time = max(max_playback_time, max(sp['moves'].keys()))
            if sp['attr_changes']:
                max_playback_time = max(max_playback_time, max(sp['attr_changes'].keys()))
        
        for sp in snap_props.values():
            if sp['despawn_time'] is not None:
                max_playback_time = max(max_playback_time, sp['despawn_time'])
            if sp['attr_changes']:
                max_playback_time = max(max_playback_time, max(sp['attr_changes'].keys()))
        
        # Schedule spaz ghost creation
        for nid, sp in snap.items():
            bs.timer(sp['spawn_time'], bs.CallPartial(_spawn_spaz_ghost, sp, ghost_mat))
        
        # Schedule prop ghost creation
        for nid, sp in snap_props.items():
            bs.timer(sp['spawn_time'], bs.CallPartial(_spawn_prop_ghost, sp, ghost_mat))
        
        # Schedule cleanup after playback finishes
        bs.timer(max_playback_time + 1.0, _finish_playback)
        
        _say(f'Replaying {len(snap)} ghosts and {len(snap_props)} props...', color=(0,1,1))

def _spawn_spaz_ghost(sp, ghost_mat):
    """Spawn a single spaz ghost at the correct time."""
    at = sp['initial_attrs'].copy()
    if 'start_position' not in at or 'fpos' not in at:
        return
    
    pos = at.pop('start_position')
    fpos = at.pop('fpos')
    real_nid = sp['real_nid']
    
    constructor_args = {}
    node_attrs = {}
    
    for key, val in at.items():
        if key in SPAZ_CONSTRUCTOR_ARGS:
            constructor_args[key] = val
        else:
            node_attrs[key] = val
    
    if 'color' in constructor_args:
        constructor_args['color'] = ghost(constructor_args['color'])
    if 'highlight' in constructor_args:
        constructor_args['highlight'] = ghost(constructor_args['highlight'])
    
    g_delegate = Spaz(**constructor_args)
    g_node = g_delegate.node
    
    # Keep strong references to prevent garbage collection
    _ghost_refs.append(g_delegate)
    _ghost_nodes.append(g_node)
    
    # Map real node ID to ghost node for attribute replacement
    _real_to_ghost_map[real_nid] = g_node
    
    for key, val in node_attrs.items():
        if 'material' in key:
            val = (*val, ghost_mat)
        # Replace real nodes with ghost twins if they exist
        val = _replace_real_nodes_with_ghosts(val)
        setattr(g_node, key, val)
    
    fixed_pos = (pos[0], pos[1] - 0.5, pos[2])
    angle = yaw(fixed_pos, fpos)
    g_node.handlemessage(bs.StandMessage(fixed_pos, angle))
    
    # Schedule moves
    for t, act in sp['moves'].items():
        bs.timer(t - sp['spawn_time'], bs.CallPartial(play_act, g_node, act))
    
    # Schedule attribute changes
    for t, changes in sp['attr_changes'].items():
        bs.timer(t - sp['spawn_time'], bs.CallPartial(_apply_attr_changes, g_node, changes))
    
    # Schedule despawn
    if sp['despawn_time'] is not None:
        bs.timer(sp['despawn_time'] - sp['spawn_time'], bs.CallPartial(_despawn_ghost, g_node))

def _spawn_prop_ghost(sp, ghost_mat):
    """Spawn a single prop ghost at the correct time."""
    at = sp['initial_attrs'].copy()
    if 'start_position' not in at:
        return
    
    pos = at.pop('start_position')
    materials = at.pop('materials', [])
    materials = (*materials, ghost_mat)
    real_nid = sp['real_nid']
    
    if 'color' in at:
        at['color'] = ghost(at['color'])
    
    # Replace real nodes with ghost twins in initial attributes
    for key, val in list(at.items()):
        at[key] = _replace_real_nodes_with_ghosts(val)
    
    g_node = bs.newnode('prop', attrs=at)
    g_node.materials = materials
    g_node.position = pos
    
    # Keep reference to this ghost node for cleanup
    _ghost_nodes.append(g_node)
    
    # Map real node ID to ghost node for attribute replacement
    _real_to_ghost_map[real_nid] = g_node
    
    # Schedule attribute changes
    for t, changes in sp['attr_changes'].items():
        bs.timer(t - sp['spawn_time'], bs.CallPartial(_apply_attr_changes, g_node, changes))
    
    # Schedule despawn
    if sp['despawn_time'] is not None:
        bs.timer(sp['despawn_time'] - sp['spawn_time'], bs.CallPartial(_despawn_ghost, g_node))

def _replace_real_nodes_with_ghosts(value):
    """
    If value is a node reference, check if we have a ghost twin for it.
    If yes, return the ghost node. Otherwise return the original value.
    """
    # Check if value is a bs.Node
    if hasattr(value, 'exists') and callable(value.exists):
        real_nid = id(value)
        if real_nid in _real_to_ghost_map:
            ghost_node = _real_to_ghost_map[real_nid]
            if ghost_node and ghost_node.exists():
                return ghost_node
    return value

def _apply_attr_changes(n, changes):
    """Apply attribute changes to a ghost node."""
    if not n.exists():
        return
    for key, val in changes.items():
        # Replace real nodes with ghost twins if they exist
        val = _replace_real_nodes_with_ghosts(val)
        setattr(n, key, val)

def _despawn_ghost(n):
    """Delete a ghost node."""
    if n.exists():
        n.delete()

def play_act(n, act):
    """Play single action"""
    if not n.exists():
        return
    o = n.getdelegate(object)
    i, j = act
    if i == 5:
        o.on_move_up_down(j)
    elif i == 6:
        o.on_move_left_right(j)
    elif i == 4:
        o.on_run(j)
    else:
        k = ['jump', 'bomb', 'pickup', 'punch'][i]
        getattr(o, f'on_{k}_{"press" if j else "release"}')()

def _finish_playback():
    """Called when playback finishes to clean up state."""
    global _playback_active, _ghost_refs, _ghost_nodes, _real_to_ghost_map
    
    # Delete all ghost nodes first to prevent death animations
    for node in _ghost_nodes:
        if node and node.exists():
            node.delete()
    
    # Now clear references
    _ghost_nodes.clear()
    _ghost_refs.clear()
    _real_to_ghost_map.clear()
    _playback_active = False
    
    _say('Playback finished!', color=(0,0,1))

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    pass
