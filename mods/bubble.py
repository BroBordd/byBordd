# Copyright 2025 - Solely by BrotherBoard
# Telegram >> GalaxyA14user

"""
Bubble v3.0 - Let out your Spaz thoughts that come in mind.

An advanced pop up bubble, which can appear from any
bascenev1.Node you like. Just call Bubble() in your
code. Refer to __doc__ of Bubble class for examples.
"""

from babase import (
    get_string_width as ssw,
    Plugin
)
from bascenev1 import (
    timer as tick,
    animate_array,
    animate,
    newnode,
    Call
)
from math import ceil
from random import choice as CH
GSW = lambda t: ssw(t,suppress_warning=True)

"""Portable class"""
class Bubble:
    __doc__ = ("""
        Highly customizable floating bubble

        Arguments:
        - node: bascenev1.Node to follow (*required)
        - text: the text to show in bubble
        - color: the color of bubble
        - time: how long to show bubble (in seconds)
        - mode: how should the text animate

        Supported modes:
        - 0: random (default)
        - 1: text pops up with bubble
        - 2: text slides letter by letter
        - 3: text fades in letter by letter
        - 4: text comes up from bubble
        - 5: text waves in letter by letter

        Besides copy pasting, inline usage varies:
        >>> from bubble import Bubble
        >>> bub = Bubble(
        ...     text='Kill me please',
        ...     color=(0.2,0.8,0.9),
        ...     node=bot.node,
        ...     time=6
        ... )
        >>>
    """)
    __mem__ = {}
    def __init__(
        s,
        node: 'bascenev1.Node',
        text: str = 'Hello!',
        color: tuple = (1,1,1),
        time: float | int = 6,
        mode: int = 0,
        res: list = [('█'),('▼')]
    ) -> None:
        if not 0 <= mode <= 5 : raise ValueError(f'mode can be an integer from 0 to 5, not {mode}')
        if not mode: mode = CH([1,2,3,4,5])
        text = f" {text}"
        s.ans,s.kids,s.mats,s.time = [],[],[],time
        s.node,s.dead,s.text = node,False,text
        s.color,s.mode,s.res = color,mode,res
        # nuke existing bubbles if possible
        s.mem = lambda: s.__class__.__mem__
        m = s.mem()
        o = m.get(node,0)
        if not getattr(o,'dead',1): tick(0.2,Call(o.delete,force=True))
        s.show()
        m[node] = s
    def show(s):
        q,l,r = s.mats,s.kids,s.ans
        # offset
        m = newnode(
            'math',
            owner=s.node,
            attrs={
                'input1': (0,1.65,0),
                'operation': 'add'
            }
        )
        q.append(m)
        # the bubble
        c = list(s.color)
        w = GSW(s.res[0])
        b = newnode(
            'text',
            owner=m,
            attrs={
                'text': f'{ceil((GSW(s.text)+2*w)/w)*s.res[0]}\n{s.res[1]}',
                'in_world': True,
                'shadow': 1.0,
                'flatness': 1.0,
                'color': (c[0],c[1],c[2],0.2),
                'scale': 0.01,
                'h_align': 'center'
            }
        )
        l.append(b)
        # the text
        txt = []
        mat = []
        kek = -GSW(s.text)/185
        sf = 0
        for i in range(len(s.text)):
            j = s.text[i]
            x = GSW(j)/95.0
            p1 = newnode(
                'text',
                owner=m,
                attrs={
                    'text': j,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': s.color,
                    'scale': 0.01,
                    'h_align': 'left'
                }
            )
            txt.append(p1)
            ok = kek+sf
            p2 = newnode(
                'math',
                owner=m,
                attrs={
                    'input1': (ok,1.65,0),
                    'operation': 'add'
                }
            )
            mat.append([p2,ok])
            s.node.connectattr('position',p2,'input2')
            p2.connectattr('output',p1,'position')
            sf += x
        l += txt
        q += [mat[i][0] for i in range(len(mat))]
        # connect
        s.node.connectattr('position',m,'input2')
        m.connectattr('output',b,'position')
        # hardcoded animators
        # conditionally used based on animation
        z = s.time
        # scale bubble in out
        a = animate(
            b,
            'scale',
            {
                0:0,
                z*0.041: 0.014,
                z*0.154: 0.014,
                z*0.167: 0.010,
                z*0.98: 0.010,
                z:0
            },
        )
        r.append(a)
        # move bubble up down
        a = animate_array(
            m,
            'input1',
            3,
            {
                0:(0,1.2,0),
                z*0.04:(0,1.65,0),
                z*0.98:(0,1.65,0),
                z:(0,1.2,0)
            }
        )
        r.append(a)
        # scale text in out
        r += [
            animate(
                txt[i],
                'scale',
                {
                    0:0,
                    z*0.041: 0.015,
                    z*0.154: 0.015,
                    z*0.167: 0.010,
                    z*0.98: 0.010,
                    z:0
                },
            )
            for i in range(len(mat))
        ] if s.mode in [1,4] else []
        # move text up down
        r += [
            animate_array(
                mat[i][0],
                'input1',
                3,
                {
                    0:(mat[i][1]/4,1.2,0),
                    z*0.04:(mat[i][1]*1.5,1.65,0),
                    z*0.154:(mat[i][1]*1.5,1.65,0),
                    z*0.167:(mat[i][1],1.65,0),
                    z*0.98:(mat[i][1],1.65,0),
                    z:(mat[i][1]/4,1.2,0)
                }
            )
            for i in range(len(mat))
        ] if s.mode in [1,4] else []
        # slide in overshoot letter by letter
        ok = (z*0.04*1.6)
        hm = [0.03,0.05][s.mode==2]
        r += [
            animate_array(
                j[0],
                'input1',
                3,
                {
                    0.5+i*hm:(j[1],1.4,0),
                    0.5+i*hm+(ok*0.6):(j[1],1.9,0),
                    0.5+i*hm+ok:(j[1],1.65,0),
                    (z-(z*0.02)):(j[1],1.65,0),
                    z:(j[1],1.2,0)
                }
            )
            for i,j in enumerate(mat)
        ] if s.mode in [2,5] else []
        # fade in letter by letter
        r += [
            animate(
                txt[i],
                'opacity',
                {
                    0.5+i*hm:0,
                    (0.5+i*hm+ok)*0.98:1,
                    z*0.9:1,
                    z:0
                }
            )
            for i in range(len(mat))
        ] if s.mode in [2,4,5] else []
        # scale slide up text
        r += [
            animate(
                txt[i],
                'scale',
                {
                    0:0,
                    z*0.154: 0,
                    z*0.167: 0.010,
                    z*0.98: 0.010,
                    z:0
                },
            )
            for i in range(len(mat))
        ] if s.mode == 3 else []
        # autokill
        tick(z,s.delete)
    def delete(s,force=False):
        if s.dead: return
        s.dead = True
        [i.delete() for i in s.ans if hasattr(i,'delete')]
        tick(0.2,lambda:[i.delete() for i in s.kids+s.mats if hasattr(i,'delete')])
        if not force: return
        [animate(
            i,
            'opacity',
            {
                0:i.opacity,
                0.2:0
            }
        ) for i in s.kids]

# ba_meta require api 9
# ba_meta export plugin
class byBordd(Plugin): pass
