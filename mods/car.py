# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Car v1.0 - vroom vroom

Experimental. Feedback is appreciated.
Creates a stupid car to ride in.
"""

from babase import Plugin
from bascenev1 import (
    newnode,
    getmesh,
    gettexture
)

class Car:
    def __init__(s):
        p = (-4,0.3,0)
        s.wheels = [
            newnode(
                'prop',
                delegate=s,
                attrs={
                    'position':(p[0]+_[0],p[1],p[2]+_[1]),
                    'body':'sphere',
                    'mesh':getmesh('impactBomb'),
                    'color_texture':gettexture('impactBombColor'),
                    'shadow_size':0.3
                }
            )
            for _ in [(0,0),(0,1),(2,0),(2,1)]
        ]

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin): pass
