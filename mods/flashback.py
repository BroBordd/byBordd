# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Flashback v1.0 - Let's see that again

Record what happens, and see it happen again.
Plays recordings by creating passthrough ghosts tha try to imitate what happened.
Heavily experimental! Feedback is appreciated.
"""

import babase as bui
import _babase as _ba
import bascenev1 as bs

from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.spaz import Spaz
from math import atan2, degrees, pi
from time import perf_counter as MS
from babase import InputType as IT
from threading import Lock

__version__ = "1.0"

# Global State
_og = None
_recording_active = False
_playback_active = False
_recorded_data = {}
_lock = Lock()

# Spaz constructor only accepts a handful of args. We explicitly define them.
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
    # Reduce brightness/saturation for a visual ghost effect
    return ((r+(l-r)*s)*0.6, (g+(l-g)*s)*0.6, (b+(l-b)*s)*0.6)

_ghost_material = None

def gmat():
    """
    Creates and returns the ghost material.
    """
    global _ghost_material
    if _ghost_material is None:
        shared = SharedObjects.get()

        _ghost_material = bs.Material()

        # no third party collision
        _ghost_material.add_actions(
            conditions=(
                ('they_dont_have_material', _ghost_material)
            ),
            actions=(
                ('modify_part_collision', 'collide', False)
            )
        )

        # allow ground collision
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
    try:
        if nid in _recorded_data:
            t = MS()
            _recorded_data[nid]['moves'][t - _recorded_data[nid]['t0']] = (i, j)
    except: pass

def _create_input_patch(og, R, nid):
    """
    Creates a dictionary of patched input handlers for the Spaz delegate.
    """
    # Press events (always send 1)
    def jp():
        og['jp']()
        R(0, 1)
    def bp(): og['bp'](); R(1, 1)
    def pp(): og['pp'](); R(2, 1)
    def up(): og['up'](); R(3, 1)

    # Release events (always send 0)
    def jr(): og['jr'](); R(0, 0)
    def br(): og['br'](); R(1, 0)
    def pr(): og['pr'](); R(2, 0)
    def ur(): og['ur'](); R(3, 0)

    # Value events (send the value v)
    def lr(v): og['lr'](v); R(6, v)
    def ud(v): og['ud'](v); R(5, v)
    def rn(v): og['rn'](v); R(4, v)

    return {
        'lr': lr, 'ud': ud, 'jp': jp, 'jr': jr,
        'bp': bp, 'br': br, 'pp': pp, 'pr': pr,
        'up': up, 'ur': ur, 'rn': rn
    }


def patch(*a, **k):
    """Patched newnode"""
    n = _og(*a, **k)
    if _recording_active and not _playback_active:
        t = a[0] if a else k.get('type')
        if t == 'spaz':
            try:
                with _lock:
                    nid = id(n)
                    o = n.getdelegate(object)
                    # Store original methods
                    og = {
                        'lr': o.on_move_left_right, 'ud': o.on_move_up_down,
                        'jp': o.on_jump_press, 'jr': o.on_jump_release,
                        'bp': o.on_bomb_press, 'br': o.on_bomb_release,
                        'pp': o.on_pickup_press, 'pr': o.on_pickup_release,
                        'up': o.on_punch_press, 'ur': o.on_punch_release,
                        'rn': o.on_run
                    }
                    # Collect attrs
                    at = {}
                    at['start_position'] = n.position
                    at['fpos'] = n.position_forward

                    for i in dir(n):
                        if i.startswith('_'): continue
                        if i in STRICT_BLACKLIST: continue
                        if i in ['node', 'getdelegate']: continue
                        try: v = getattr(n, i)
                        except: continue
                        if callable(v): continue
                        try: at[i] = v
                        except: pass

                    t0 = MS()
                    _recorded_data[nid] = {
                        'node': n, 'og': og, 'attrs': at, 't0': t0, 'moves': {}
                    }

                    # Apply the robust patch
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

            except: pass
    return n

def record():
    """record -> start the spy that records stuff. Overwrites previous recording."""
    global _og, _recording_active, _recorded_data
    if _recording_active:
        _say('Recording is already active. Stopping previous...', color=(1,1,0))
        stop()

    _recorded_data.clear()

    if _og is None: _og = bs.newnode; bs.newnode = patch
    _recording_active = True

    # Patch existing spazzes and RE-CONNECT controls
    try:
        a = bs.get_foreground_host_activity()
        if not a: _say('No active game!'); return

        with a.context:
            players = a.players
            # 1. Identify Spaz nodes for patching
            existing = [
                n for n in bs.getnodes()
                if n.getnodetype() == 'spaz'
                and n.exists()
                and not n.getdelegate(object)._dead
            ]

            for n in existing:
                try:
                    with _lock:
                        nid = id(n)
                        o = n.getdelegate(object)
                        # Store original methods
                        og = {
                            'lr': o.on_move_left_right, 'ud': o.on_move_up_down,
                            'jp': o.on_jump_press, 'jr': o.on_jump_release,
                            'bp': o.on_bomb_press, 'br': o.on_bomb_release,
                            'pp': o.on_pickup_press, 'pr': o.on_pickup_release,
                            'up': o.on_punch_press, 'ur': o.on_punch_release,
                            'rn': o.on_run
                        }
                        # Collect attrs (with strict filtering)
                        at = {}
                        at['start_position'] = n.position
                        at['fpos'] = n.position_forward

                        for i in dir(n):
                            if i.startswith('_'): continue
                            if i in STRICT_BLACKLIST: continue
                            if i in ['node', 'getdelegate']: continue
                            try: v = getattr(n, i)
                            except: continue
                            if callable(v): continue
                            try: at[i] = v
                            except: pass

                        t0 = MS()
                        _recorded_data[nid] = {
                            'node': n, 'og': og, 'attrs': at, 't0': t0, 'moves': {}
                        }

                        # Apply the robust patch
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

                        # Re-connect the player's controls to the now-patched Spaz
                        for p in players:
                            if p.actor and p.actor.node == n:
                                # Disconnect then Re-connect (this forces the use of the new delegate methods)
                                p.actor.disconnect_controls_from_player()
                                p.actor.connect_controls_to_player()
                                break # Found the player, move to next Spaz

                except: pass
    except: pass

    _say('Recording started! History cleared.', color=(0,1,0))

def stop():
    """stop -> stops recording, doesn't delete anything."""
    global _recording_active
    if not _recording_active:
        _say('Recording is not active.', color=(1,1,0))
        return

    with _lock:
        for nid, data in list(_recorded_data.items()):
            try:
                if data['node'] and data['node'].exists():
                    o = data['node'].getdelegate(object)
                    # When stopping, we should un-patch (restore originals) and re-connect controls
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

                        # Re-connect controls for affected players
                        a = bs.get_foreground_host_activity()
                        if a:
                            for p in a.players:
                                if p.actor and p.actor.node == data['node']:
                                    p.actor.disconnect_controls_from_player()
                                    p.actor.connect_controls_to_player()
                                    break

                # Clean up references after unpatching
                data['node'] = None
                if 'og' in data: del data['og']

            except: pass

    _recording_active = False
    _say('Recording stopped! History saved.', color=(1,0,0))


def play():
    """play -> plays recorded stuff."""
    global _playback_active, _recording_active
    if _playback_active: _say('Already playing!'); return

    if not _recorded_data: _say('No history recorded. Call record() first.', color=(1,1,0)); return

    # Stop recording if it's currently active
    if _recording_active:
        stop()

    with _lock:
        snap = {
            k: {'attrs': v['attrs'].copy(), 'moves': v['moves'].copy()}
            for k, v in _recorded_data.items()
        }

    _say(f'Found {len(snap)} spazzes to replay', color=(1,1,0))

    _playback_active = True

    try:
        a = bs.get_foreground_host_activity()
        if not a: _playback_active = False; return

        with a.context:
            ghost_mat = gmat()
            ghosts = []
            max_playback_time = 0.0

            for nid, sp in snap.items():
                try:
                    at = sp['attrs'].copy()
                    if 'start_position' not in at: continue
                    if 'fpos' not in at: continue
                    pos = at.pop('start_position')
                    fpos = at.pop('fpos')

                    # 1. Filter attributes for Spaz() constructor
                    constructor_args = {}
                    node_attrs = {}

                    for key, val in at.items():
                        if key in SPAZ_CONSTRUCTOR_ARGS:
                            constructor_args[key] = val
                        else:
                            node_attrs[key] = val

                    # Apply ghost coloring
                    if 'color' in constructor_args: constructor_args['color'] = ghost(constructor_args['color'])
                    if 'highlight' in constructor_args: constructor_args['highlight'] = ghost(constructor_args['highlight'])

                    # 2. Create the Spaz delegate
                    g_delegate = Spaz(**constructor_args)
                    g_node = g_delegate.node

                    # 3. Apply the non-constructor attributes directly to the node
                    for key, val in node_attrs.items():
                        if 'material' in key: val = (*val,ghost_mat)
                        setattr(g_node, key, val)
                    # 4. Apply the initial position offset
                    fixed_pos = (pos[0], pos[1] - 0.5, pos[2])
                    angle = yaw(fixed_pos,fpos)
                    g_node.handlemessage(bs.StandMessage(fixed_pos, angle))

                    # Store the delegate object to maintain a strong reference
                    ghosts.append({'node': g_node, 'delegate': g_delegate, 'moves': sp['moves']})

                    if sp['moves']:
                        max_time_for_ghost = max(sp['moves'].keys())
                        if max_time_for_ghost > max_playback_time:
                            max_playback_time = max_time_for_ghost
                except: pass

            _say(f'Replaying {len(ghosts)} ghosts...', color=(0,1,1))

            # Schedule actions
            for gh in ghosts:
                mvs = gh['moves']
                for t, act in mvs.items():
                    bs.timer(t, bs.CallPartial(play_act, gh['node'], act))

            # Cleanup only the temporary ghosts, using the true max recorded time
            bs.timer(max_playback_time + 1.0, lambda: cleanup(ghosts))

    except Exception as e: _say(f'Error: {e}', color=(1,0,0))
    finally: _playback_active = False

def play_act(n, act):
    """Play single action"""
    try:
        if not n.exists(): return
        o = n.getdelegate(object)
        i, j = act
        if i == 5: o.on_move_up_down(j)
        elif i == 6: o.on_move_left_right(j)
        elif i == 4: o.on_run(j)
        else:
            k = ['jump', 'bomb', 'pickup', 'punch'][i]
            getattr(o, f'on_{k}_{"press" if j else "release"}')()
    except: pass

def cleanup(ghosts):
    """Clean up ghosts nodes"""
    for g in ghosts:
        if g['node'].exists():
            g['node'].delete()
    _say('Playback finished!', color=(0,0,1))

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd: pass
