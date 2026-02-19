# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Viewer v1.0 - KTX Viewer

For debugging purposes
"""

import os
import bauiv1 as bui

class Viewer:
    def __init__(s,source=None):
        s.source = source
        size = x,y = 512,512
        tex = bui.gettexture('white')
        color1 = (0,0,0)
        color2 = (0.3,0.3,0.3)
        color3 = (1,1,1)
        # root
        s.root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=size,
            background=False,
            transition=(
                source and 'in_scale'
                or 'in_right'
            ),
            scale_origin_stack_offset=(
                source and
                source.get_screen_space_center()
                or None
            )
        )
        # bg
        s.background = bui.imagewidget(
            parent=s.root,
            size=size,
            texture=tex,
            color=color1
        )
        bx = 50
        marg = 20
        # back
        bui.containerwidget(
            s.root,
            cancel_button=bui.buttonwidget(
                parent=s.root,
                size=(bx,bx),
                label=bui.charstr(
                    bui.SpecialChar.BACK
                ),
                on_activate_call=s.back,
                position=(
                    marg,
                    y-(bx+marg)
                ),
                texture=tex,
                enable_sound=False,
                color=color2,
                textcolor=color3
            )
        )
        # apply
        bui.buttonwidget(
            parent=s.root,
            size=(bx,bx),
            label=bui.charstr(
                bui.SpecialChar.PLAY_STATION_CIRCLE_BUTTON
            ),
            on_activate_call=s.apply,
            position=(
                x-(bx+marg),
                y-(bx+marg)
            ),
            texture=tex,
            enable_sound=False,
            color=color2,
            textcolor=color3
        )
        # tv
        tv_width = x/2
        s.tv = bui.imagewidget(
            parent=s.root,
            size=(tv_width,tv_width),
            position=(
                tv_width/2,
                tv_width/2
            ),
            texture=tex,
            color=color3
        )
        # pro
        s.pro = bui.textwidget(
            parent=s.root,
            position=(
                tv_width/2,
                tv_width/2-30
            ),
            maxwidth=tv_width,
            color=color3
        )
        # input
        s.input = bui.textwidget(
            parent=s.root,
            position=(bx+marg*2,y-(bx+marg)),
            size=(x-(bx*2+marg*4),bx),
            glow_type='uniform',
            editable=True,
            v_align='center',
            color=color3,
            text='test',
            allow_clear_button=False
        )
    def back(s):
        bui.containerwidget(
            s.root, transition=(
                s.source and 'out_scale'
                or 'out_left'
            )
        )
        bui.getsound('deek').play()
    def apply(s):
        bui.imagewidget(
            s.tv, texture=bui.gettexture(
                bui.textwidget(
                    query=s.input
                )
            )
        )

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(bui.Plugin):
    has_settings_ui = lambda s: True
    show_settings_ui = lambda s,src: Viewer(src)
    def __init__(s):
        bui.apptimer(2,Viewer)
