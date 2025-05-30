# Copyright 2025 - Solely by BrotherBoard
# Feedback is appreciated - Telegram >> @GalaxyA14user

"""
Pos v1.0 - Simple 2D UI positioner

Simple usage:
from pos import Pos
Pos(widget,initial_pos)
"""

from babase import Plugin as P
from bauiv1 import (
    Call,
    Widget,
    charstr as cs,
    getsound as gs,
    rowwidget as rw,
    textwidget as tw,
    SpecialChar as sc,
    imagewidget as iw,
    scrollwidget as sw,
    buttonwidget as bw,
    columnwidget as cow,
    hscrollwidget as hsw,
    checkboxwidget as cbw,
    screenmessage as push,
    containerwidget as cw,
    get_special_widget as gsw,
    clipboard_set_text as copy
)

"""Simple 2D widget positioner for ui development"""
class pos:
    """On call"""
    def __init__(
        s,
        widget: Widget,
        position: tuple = (0,0),
        step: int | float = 2,
        size: tuple = (300, 200),
        offset: tuple = (0, 0),
        color: tuple = (0.10,0.10,0.10)
    ) -> None:
        s.w = widget
        s.s = step
        s.p = position
        x, y = size
        # Main container
        c = cw(
            parent=gsw('overlay_stack'),
            size=size,
            color=color,
            transition='in_scale',
            scale_origin_stack_offset=s.p,
            stack_offset=offset
        )
        # Back button
        b = bw(
            parent=c,
            button_type='backSmall',
            size=(30,30),
            color=color,
            position=(30,y-60),
            on_activate_call=lambda:cw(c,transition='out_left'),
            label=cs(sc.BACK)
        )
        cw(c,cancel_button=b)
        # Info
        s.t = tw(
            parent=c,
            text=str(s.p),
            on_activate_call=lambda:copy(str(s.p).replace(' ','')),
            h_align='center',
            size=(100,30),
            selectable=True,
            click_activate=True,
            position=(x/2-50,y/2)
        )
        # Arrows
        for i in range(4):
            j = [
                [(30,y/2),'LEFT'],
                [(x-60,y/2),'RIGHT'],
                [(x/2-15,y-30),'UP'],
                [(x/2-15,30),'DOWN']
            ][i]
            bw(
                parent=c,
                color=color,
                repeat=True,
                size=(30,30),
                position=j[0],
                enable_sound=False,
                on_activate_call=Call(s.mv,i),
                label=cs(getattr(sc,j[1]+'_ARROW')),
            )
    """Refresh"""
    def fresh(s):
        for i in [bw,tw,cw,iw,sw,rw,hsw,cbw,cow]:
            try: i(s.w,position=s.p)
            except: continue
            else: break
        tw(s.t,text=str(s.p))
    """Move"""
    def mv(s,i):
        p = s.p
        s.p = [
            (p[0]-s.s,p[1]),
            (p[0]+s.s,p[1]),
            (p[0],p[1]+s.s),
            (p[0],p[1]-s.s)
        ][i]
        s.fresh()
        gs('deek').play()

# ba_meta require api 9
# ba_meta export plugin
class byBordd(P): pass
