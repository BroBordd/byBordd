# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
LightsOut v1.0 - Oh my eyes

Disables bright stuff from the game.
"""

from babase import Plugin

# global
DUM = type('DUM', (object,), {
    '__getattr__': lambda self, name: self,
    '__call__': lambda self, *a, **k: self
})()

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(s):
        import bascenev1 as bs
        # animation
        o = bs.animate
        bs.animate = lambda *a,**k:(
            a and a[0].getnodetype() == 'light' and
            'intensity' in a and
            (a[2].clear(),a[2].update({0:0}))
        ) or o(*a,**k)
        # fx
        bs.emitfx = lambda *a,**k: None
        # light
        p = bs.newnode
        bs.newnode = lambda *a,**k: (
            'explosion' in a and DUM
        ) or p(*a,**k)
