# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
BSV v1.0 - The BombSquad Video

Very stupid video playing approach
Check out https://github.com/BroBordd/bsvideo
"""

import os
import bauiv1 as bui
from json import load
from zipfile import ZipFile
from threading import Thread

ROOT = os.path.join(
    bui.app.env.python_directory_user,
    'BSV'
)
TEMP = os.path.join(
    os.path.dirname(
        bui.app.env.cache_directory
    ), 'ballistica_files', 'ba_data', 'textures'
)

class BSV:
    def __init__(s,source=None):
        s.source = source
        s.playing = False
        s.busy = False
        s.frames = []
        s.fps = None
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
        # play
        s.play_btn = bui.buttonwidget(
            parent=s.root,
            size=(bx,bx),
            label=bui.charstr(
                bui.SpecialChar.PLAY_BUTTON
            ),
            on_activate_call=s.play,
            position=(
                x-(bx+marg),marg
            ),
            texture=tex,
            enable_sound=False,
            color=color2,
            textcolor=color3
        )
        # scan
        s.scan_btn = bui.buttonwidget(
            parent=s.root,
            size=(bx,bx),
            label=bui.charstr(
                bui.SpecialChar.PLAY_STATION_CIRCLE_BUTTON
            ),
            on_activate_call=s.scan,
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
        # input
        s.input = bui.textwidget(
            parent=s.root,
            position=(bx+marg*2,y-(bx+marg)),
            size=(x-(bx*2+marg*4),bx),
            glow_type='uniform',
            editable=True,
            v_align='center',
            color=color3,
            text='cube.bsv',
            allow_clear_button=False
        )
        # finally
        s.cleanup()

    def play(s,set=None):
        if s.busy or not s.frames:
            bui.getsound('block').play()
            return
        if set is not None:
            s.playing = set
        else: s.playing = not s.playing
        if s.playing:
            bui.buttonwidget(
                s.play_btn,
                label=bui.charstr(
                    bui.SpecialChar.PAUSE_BUTTON
                )
            )
        else:
            bui.buttonwidget(
                s.play_btn,
                label=bui.charstr(
                    bui.SpecialChar.PLAY_BUTTON
                )
            )
        bui.getsound('deek').play()
        if set is not None: return
        if s.playing:
            s.play_timer = bui.AppTimer(
                s.fps, s.tick, repeat=True
            )
        else:
            s.play_timer = None

    def tick(s):
        s.current += 1
        if s.current >= len(s.frames): s.current = 0
        bui.imagewidget(
            s.tv, texture=bui.gettexture(
                s.frames[s.current]
            )
        )

    def back(s):
        bui.containerwidget(
            s.root, transition=(
                s.source and 'out_scale'
                or 'out_left'
            )
        )
        bui.getsound('deek').play()

    def scan(s):
        t = bui.textwidget(query=s.input)
        if s.busy or not t:
            bui.screenmessage('no')
            bui.getsound('block').play()
            return
        os.makedirs(ROOT,exist_ok=True)
        filepath = os.path.join(
            ROOT, t
        )
        if not os.path.exists(filepath):
            bui.screenmessage('does not exist')
            bui.getsound('block').play()
            return
        bui.getsound('deek').play()
        s.frames.clear()
        s.current = 0
        s.cleanup()
        s.busy = True
        bui.screenmessage('wait...')
        Thread(target=lambda: s._scan(filepath)).start()

    def _scan(s,filepath):
        video_name = os.path.splitext(os.path.basename(filepath))[0]
        prefix = type(s).__name__.lower()
        with ZipFile(filepath, 'r') as zf:
            with zf.open('metadata.json') as f:
                metadata = load(f)
            s.fps = metadata['fps']
            ktx_files = sorted([n for n in zf.namelist() if n.endswith('.ktx')])

            for idx, name in enumerate(ktx_files):
                fn = f'.{prefix}_{video_name}_frame{idx:04d}'
                temp_path = os.path.join(TEMP,fn+'.ktx')
                s.frames.append(fn)
                with zf.open(name) as src, open(temp_path, 'wb') as dst:
                    dst.write(src.read())
        bui.pushcall(s.done,from_other_thread=True)

    def done(s):
        s.busy = False
        bui.getsound('gunCocking').play()
        bui.screenmessage('loaded!')
        s.play(set=False)

    def cleanup(s):
        prefix = type(s).__name__.lower()
        for filename in os.listdir(TEMP):
            if filename.startswith(f'.{prefix}'):
                os.remove(os.path.join(TEMP, filename))

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(bui.Plugin):
    has_settings_ui = lambda s: True
    show_settings_ui = lambda s,src: BSV(src)
    def __init__(s):
        bui.apptimer(2,BSV)
