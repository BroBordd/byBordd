# Copyright 2025 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Slider v1.0 - UI Element

Simple UI slider, read code to know more.
"""

from babase import Plugin
from bauiv1 import (
    apptimer as teck,
    imagewidget as iw,
    gettexture as gt,
    buttonwidget as bw,
    Call
)

class Slider:
    def __init__(s, parent):
        s.p = parent
        s.pro = 0
        s.kids = []
        for i in range(35):
            bw(
                parent=s.p,
                position=(100+10*i,200),
                label='',
                button_type='square',
                on_activate_call=Call(s.set,i),
                size=(10,10),
                texture=gt('empty')
            )
        s.make()
    def set(s,i):
        s.pro = i*10
        s.make()
    def make(s):
        [_.delete() for _ in s.kids]
        s.kids.clear()
        s.kids.append(iw(
            parent=s.p,
            size=(350,5),
            opacity=0.5,
            texture=gt('white'),
            position=(100,200)
        ))
        s.kids.append(iw(
            parent=s.p,
            texture=gt('white'),
            opacity=0.5,
            position=(100,200),
            size=(s.pro,5),
            color=(0,1,1)
        ))
        s.kids.append(iw(
            parent=s.p,
            texture=gt('nub'),
            opacity=1,
            position=(96+s.pro,200-12),
            size=(30,30),
            color=(0,1,1)
        ))

# brobord collide grass
# ba_meta require api 9
# ba_meta export plugin
class byBordd(Plugin):
    def __init__(s):
        teck(1, s.demo) if 0 else 0
    def demo(s):
        from bauiv1 import (
            containerwidget as cw
        )
        c = cw(
            size=(500,300),
            color=(0.3,0.3,0.3),
            scale=2
        )
        Slider(parent=c)
