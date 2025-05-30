# Copyright 2025 - Solely by BrotherBoard
# Feedback is appreciated - Telegram >> @GalaxyA14user

"""
Core v1.0 - Advanced action recorder bot

Send 'start' for Core to start recording you,
and 'stop' to stop recording. And 'load' for
Core to load recorded moves.
"""

from babase import (
    InputType as IT,
    Plugin
)
from bascenev1lib.actor.spaz import Spaz
from bascenev1 import (
    get_foreground_host_activity as ga,
    get_chat_messages as GCM,
    timer as tick,
    StandMessage,
    Call
)
from bauiv1 import (
    apptimer as teck,
    app as APP
)
from time import perf_counter
from bubble import Bubble

class Core:
    z = [(0,1,1),(0,0.4,0.4)]
    a = []
    m = {}
    t = 0
    @classmethod
    def R(c,i,j):
        c.m[perf_counter()-c.t] = (i,j)
    def __init__(s,p=(0,0,0)):
        c = s.__class__
        d = c.z
        b = s.b = Spaz(
            color=d[0],
            highlight=d[1],
            character='Agent Johnson'
        )
        c.a.append(s)
        b.handlemessage(StandMessage(p,0))
        n = b.node
        n.name = c.__name__
        n.name_color = d[0]
    def key(s,i,j):
        getattr(s.b,'on_'+['jump','bomb','pickup','punch'][i]+'_'+['release','press'][j])()
    def load(s):
        m = s.__class__.m.copy()
        for i,a in m.items():
            tick(i,Call(s._load,a))
    def _load(s,a):
        i,j = a
        if i == 5: s.b.on_move_up_down(j)
        if i == 6: s.b.on_move_left_right(j)
        if i in [0,1,2,3]: s.key(i,j)
        if i == 4: s.b.on_run(j)

from coolbox import getme
def var(s,v=None):
    cfg = APP.config
    s = 'core_'+s
    if v is None: return cfg.get(s,v)
    else:
        cfg[s] = v
        cfg.commit()
LN = lambda d,o: [o.assigninput(getattr(IT,k), d[k]) for k in d]
MS = lambda: perf_counter()
l = ''
def spy():
    global l
    a = GCM()
    teck(0.1,spy)
    if len(a) and a[-1] != l:
        l = a[-1]
        t = l.split(': ',1)[1]
        if t not in ['start','stop','load']: return
        if not len(Core.a): return
        s = Core.a[-1]
        n = s.b.node
        with ga().context:
            Bubble(
                node=n,
                text=t+'!',
                color=n.color,
                time=3
            )
            if t == 'start':
                Core.m.clear()
                R = Core.R
                Core.t = perf_counter()
                me = getme()
                m = me.actor
                LN({
                    'UP_DOWN': lambda v: (m.on_move_up_down(v),R(5,v)),
                    'LEFT_RIGHT': lambda v: (m.on_move_left_right(v),R(6,v)),
                    'PICK_UP_PRESS': lambda: (m.on_pickup_press(),R(2,1)),
                    'PICK_UP_RELEASE': lambda: (m.on_pickup_release(),R(2,0)),
                    'JUMP_PRESS': lambda: (m.on_jump_press(),R(0,1)),
                    'JUMP_RELEASE': lambda: (m.on_jump_release(),R(0,0)),
                    'BOMB_PRESS': lambda: (m.on_bomb_press(),R(1,1)),
                    'BOMB_RELEASE': lambda: (m.on_bomb_release(),R(1,0)),
                    'PUNCH_PRESS': lambda: (m.on_punch_press(),R(3,1)),
                    'PUNCH_RELEASE': lambda: (m.on_punch_release(),R(3,0)),
                    'RUN': lambda v: (m.on_run(v),R(4,v))
                },me)
            elif t == 'stop':
                me = getme()
                me.resetinput()
                me.actor.connect_controls_to_player()
                with open('/sdcard/Android/data/net.froemling.bombsquad/files/mods/core.json','w') as f:
                    f.write(str(Core.m))
#                var('m',Core.m)
            else:
                s.load()
teck(5,spy)

# ba_meta require api 9
# ba_meta export plugin
class byBordd(Plugin): pass
