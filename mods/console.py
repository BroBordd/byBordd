# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Console v1.0 - Better python console

Experimental. Feedback is appreciated.
Helps hacky mobile modders like me!

Improves python dev console, features vary:
- Real time suggestions dropdown (eg, pr -> print).
- Adds up/down arrows to recall executed commands.
- Saves dev console history in env for later.
"""

from babase import (
    get_string_width as strw,
    Plugin,
    app
)
from _babase import (
    get_dev_console_input_text as get,
    set_dev_console_input_text as set
)
from bauiv1 import (
    SpecialChar as sc,
    AppTimer as tuck,
    getsound as gs,
    charstr as cs,
    Call
)
from keyword import kwlist as _kwl
from builtins import set as _set
from sys import modules as _mod

TOKENS = lambda:sorted(_set(_kwl).union(dir(_mod['builtins'])).union(globals().keys()))
GSW = lambda t:strw(t,suppress_warning=True)

def var(s,v=None):
    c = app.config
    s = 'dh_'+s
    if v is None: return c.get(s,v)
    c[s] = v
    c.commit()

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    KEY = 'list'
    def __init__(s):
        # UI
        from babase._devconsoletabs import DevConsoleTabPython as T
        o = T.refresh
        T.refresh = lambda z:(s.kang(z),o(z))
        # Adapter
        from babase._ui import DevConsoleStringEditAdapter as A
        p = A._do_apply
        A._do_apply = lambda z,t: (s.pipe(t),p(z,t))
        # Finally
        s.a = var(s.KEY) or []
        s.i = 0
        s.pk = False
        s.last = s.curr = ''
        s.mem = TOKENS()
        s.spyt = tuck(0.1,s.spy,repeat=True)
    def pipe(s,t):
        if t == s.last: return
        s.last = s.curr = t
        s.i = 0
        s.z.request_refresh()
    def spy(s):
        if not s.last: return
        if not get():
            s.yes()
            s.last = s.curr = ''
    def yes(s):
        if s.last:
            s.i = 0
            if (not s.a or s.a[-1] != s.last):
                s.a.append(s.last)
                var(s.KEY,s.a)
            s.z.request_refresh()
    def kang(s,z):
        s.z = z
        x = z.width/2
        for i,j in enumerate(['UP','DOWN']):
            if z.height == 100:
                pos = (x-250-i*110,60)
                size = (100,30)
            else:
                pos = (x-100,120-i*60)
                size = (100,50)
            k = [1,-1][i]
            z.button(
                cs(getattr(sc,j+'_ARROW')),
                pos=pos,
                size=size,
                call=Call(s.mv,k),
                disabled=not 0<=s.i+k<=len(s.a)
            )
        s.drop()
    def drop(s):
        g = s.last
        if not g: return
        if ' ' in g:
            g,t = g.rsplit(' ',1)
            if not t: return
        else: g,t = ('',g)
        l = [_ for _ in s.mem if _.startswith(t)]
        if not l: return
        if len(l)<2 and l[0] == t and s.pk:
            set(s.last+' ')
            s.pk = False
            return
        s.pk = False
        sx = GSW(max(l,key=GSW))+10
        if g: g+=' '
        x = (-s.z.width/2)+(GSW(g)*0.88)
        for i,j in enumerate(l):
            s.z.button(
                '',
                pos=(x+20,0-i*25),
                size=(sx,25),
                corner_radius=0,
                style='black',
                call=Call(s.pick,g,j)
            )
            s.z.text(
                j,
                h_align='left',
                pos=(x+25,12-i*25),
                scale=0.9,
                style='faded'
            )
            s.z.text(
                t,
                h_align='left',
                pos=(x+25,12-i*25),
                scale=0.9
            )
    def pick(s,g,j):
        s.pk = True
        n = g+j
        set(n)
        s.last = s.curr = n
        s.i = 0
        s.z.request_refresh()
    def mv(s,i):
        gs('deek').play()
        s.i += i
        if s.i == 0: n = s.curr
        else: n = s.a[-s.i]
        set(n)
        s.last = n
        s.z.request_refresh()

