# Copyright 2025 - Solely by BrotherBoard.
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
DevHistory v2.0 - Simple dev console history revealer!

Start by writing 'dh' in dev console. You don't even
need to press enter. Experimental. DH aims to help
me as a mobile user. It is really useful.
"""

from babase import (
    SpecialChar as S,
    charstr as C,
    Plugin as P,
    app
)
from bauiv1 import (
    screenmessage as push,
    containerwidget as cw,
    buttonwidget as bw,
    imagewidget as iw,
    apptimer as teck,
    gettexture as gt,
    getsound as gs,
    CallPartial
)
from _babase import (
    get_dev_console_input_text as get,
    set_dev_console_input_text as set
)

def var(s,v=None):
    c = app.config
    s = 'dh_'+s
    if v is None: return c.get(s,v)
    c[s] = v
    c.commit()

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(P):
    __nam__ = 'DevHistory'
    __ver__ = '2.0'
    __doc__ = 'Just write dh in console and let me do the rest.'
    def __init__(s):
        s.up = False
        s.a = var('a') or ['']
        s.last = ''
        s.sound = [gs(i) for i in ['deek','block']]
        s.eye()
        print (s.__nam__,s.__ver__,'-','Write dh to start')
    def make(s):
        s.i = 0
        s.up = True
        s.w = cw(
            transition='in_left',
            scale=2,
            background=False,
            on_outside_click_call=s.kill,
            size=(60,110)
        )
        iw(
            parent=s.w,
            texture=gt('white'),
            color=(0.1,0.1,0.1),
            size=(60,110)
        )
        for i in range(2):
            bw(
                parent=s.w,
                button_type='square',
                label=C([S.DOWN_ARROW,S.UP_ARROW][i]),
                position=(7.5,7.5+50*i),
                color=(0.5,0.5,0.5),
                text_scale=1.3,
                textcolor=(0.3,0.3,0.3),
                size=(45,45),
                texture=gt('white'),
                enable_sound=False,
                on_activate_call=CallPartial(s.nav,[-1,1][i])
            )
    def nav(s,i):
        n = s.i + i
        l = len(s.a)
        if n >= l or n < 0: s.sound[1].play(); return
        s.sound[0].play()
        s.i = n
        set(s.a[-n])
    def kill(s):
        cw(s.w,transition='out_left')
        s.up = False
    def eye(s):
        n = get()
        if n == 'dh':
            s.kill() if s.up else s.make()
            set('')
        elif not n:
            s.i = 0
            if s.last and s.last != s.a[-1]:
                s.a.append(s.last)
                var('a',s.a)
        elif n != s.last: s.last = n
        teck(0.1,s.eye)
