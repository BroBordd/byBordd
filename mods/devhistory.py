# Copyright 2025 - Solely by BrotherBoard.
# Bug? Feedback? @GalaxyA14user >> Telegram!

"""
DevHistory v1.0 - Simple dev console history revealer!

Start by writing 'dh' in dev console. You don't even
need to press enter. Experimental. DH aims to help
me as a mobile user. It is really useful.
"""

from babase import (
    SpecialChar as S,
    charstr as C,
    Plugin as P
)
from bauiv1 import (
    screenmessage as push,
    containerwidget as cw,
    buttonwidget as bw,
    apptimer as teck,
    getsound as gs,
    Call
)
from _babase import (
    get_dev_console_input_text as get,
    set_dev_console_input_text as set
)

# ba_meta require api 9
# ba_meta export plugin
class byBordd(P):
    __nam__ = 'DevHistory'
    __ver__ = '1.0'
    __doc__ = 'Just write dh in console and let me do the rest.'
    """Set up"""
    def __init__(s):
        s.up = False
        s.a = ['']
        s.last = ''
        s.sound = [gs(i) for i in ['deek','block']]
        s.eye()
        print (s.__nam__,s.__ver__)
    """Make buttons"""
    def make(s):
        s.i = 0
        s.up = True
        s.w = cw(
            transition='in_left',
            scale=2,
            color=(0.1,0.1,0.1),
            on_outside_click_call=s.kill,
            size=(60,110)
        )
        for i in range(2):
            bw(
                parent=s.w,
                button_type='square',
                label=C([S.DOWN_ARROW,S.UP_ARROW][i]),
                position=(7.5,7.5+50*i),
                color=(0.5,0.5,0.5),
                textcolor=(0.3,0.3,0.3),
                size=(45,45),
                enable_sound=False,
                on_activate_call=Call(s.nav,[-1,1][i])
            )
    """Navigate"""
    def nav(s,i):
        n = s.i + i
        l = len(s.a)
        if n >= l or n < 0: s.sound[1].play(); return
        s.sound[0].play()
        s.i = n
        set(s.a[-n])
    """Kill"""
    def kill(s):
        cw(s.w,transition='out_left')
        s.up = False
    """The eye"""
    def eye(s):
        n = get()
        if n == 'dh':
            s.kill() if s.up else s.make()
            set('')
        elif not n:
            s.i = 0
            if s.last and s.last != s.a[-1]: s.a.append(s.last)
        elif n != s.last: s.last = n
        teck(0.1,s.eye)
