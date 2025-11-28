# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Movi v1.0 - Movie Maker

Basic keyframe-based movie maker.
Experimental.
"""

import babase as ba
import bauiv1 as bui
import bascenev1 as bs
from time import perf_counter

# global
__version__ = '1.0'

class Theme:
    MAIN = (0,0,0)
    TINT = (0.5,0.5,0.5)
    OPACITY = 0.4
    TEXTURE = 'white'

class Animate:
    def __init__(s, widget, func, pos, size, opacity, duration, on_finish=None):
        s.widget = widget
        s.func = func
        s.on_finish = on_finish
        s.cancelled = False

        # targets
        s.pos_start = pos[0]
        s.pos_end = pos[1]
        s.size_start = size[0]
        s.size_end = size[1]
        s.opacity_start = opacity[0]
        s.opacity_end = opacity[1]

        # state
        s.pos_current = list(s.pos_start)
        s.size_current = list(s.size_start)
        s.opacity_current = s.opacity_start

        # timing
        s.duration = duration
        s.start_time = perf_counter()

        # tick
        s.timer = bui.AppTimer(0.008, s.tick, repeat=True)

    def lerp(s, a, b, t):
        return a + (b - a) * t

    def tick(s):
        if s.cancelled or not s.widget.exists():
            s.timer = None
            return s.finish()

        # progress
        elapsed = perf_counter() - s.start_time
        progress = min(elapsed / s.duration, 1.0)

        # easing
        t = s.ease_out(progress)

        # interpolate
        px = s.lerp(s.pos_start[0], s.pos_end[0], t)
        py = s.lerp(s.pos_start[1], s.pos_end[1], t)
        sx = s.lerp(s.size_start[0], s.size_end[0], t)
        sy = s.lerp(s.size_start[1], s.size_end[1], t)
        o = s.lerp(s.opacity_start, s.opacity_end, t)

        # update
        s.pos_current = [px, py]
        s.size_current = [sx, sy]
        s.opacity_current = o

        # apply
        s.func(s.widget, position=(px, py), size=(sx, sy), opacity=o)

        # done
        if progress >= 1.0:
            s.timer = None
            s.finish()

    def ease_out(s, t):
        return 1 - (1 - t) ** 3

    def finish(s):
        if callable(s.on_finish) and not s.cancelled:
            s.on_finish()

    def cancel(s):
        s.cancelled = True
        s.timer = None

    def get_state(s):
        return {
            'pos': s.pos_current,
            'size': s.size_current,
            'opacity': s.opacity_current,
            'pos_start': s.pos_start,
            'size_start': s.size_start,
            'opacity_start': s.opacity_start
        }

class Editor:
    def __init__(s):
        s.menu_on = False
        s.animations = {}
        s.menu_root = None
        s.menu_kids = []

    def ui_safe(s):
        return s.root.exists() and not s.root.transitioning_out

    def make(s):
        rx,ry = s.real = bui.get_virtual_screen_size()
        sx,sy = s.size = (rx,150)
        # root
        s.root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=s.size,
            stack_offset=(-rx/2+sx/2,-ry/2+sy/2),
            background=False
        )
        # background
        bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture(Theme.TEXTURE),
            color=Theme.MAIN,
            opacity=Theme.OPACITY,
            size=s.size
        )
        # square
        bx = 55
        px,py = rx-bx,ry-bx
        bui.buttonwidget(
            parent=s.root,
            position=(px,py),
            size=(bx,bx),
            texture=bui.gettexture(Theme.TEXTURE),
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_SQUARE_BUTTON),
            color=Theme.MAIN,
            textcolor=Theme.TINT,
            enable_sound=False,
            on_activate_call=s.on_square
        )
        # triangle
        px -= bx+5
        bui.buttonwidget(
            parent=s.root,
            position=(px,py),
            size=(bx,bx),
            texture=bui.gettexture(Theme.TEXTURE),
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_TRIANGLE_BUTTON),
            color=Theme.MAIN,
            textcolor=Theme.TINT,
            enable_sound=False,
            on_activate_call=s.on_triangle
        )

    def on_square(s):
        s.toggle_menu()

    def on_triangle(s):
        bui.get_special_widget('squad_button').activate()

    def kill(s):
        if not s.ui_safe(): return
        s.root.delete()

    def cleanup_menu(s):
        if s.menu_root and s.menu_root.exists():
            s.menu_root.delete()
        for kid in s.menu_kids:
            if kid.exists():
                kid.delete()
        s.menu_kids.clear()
        s.menu_root = None

    def toggle_menu(s):
        key = 'menu'

        # cancel
        if key in s.animations:
            s.animations[key].cancel()

        if s.menu_on:
            # collapse
            anim = s.animations.get(key)
            if not anim: return
            state = anim.get_state()

            # reverse
            pos = [state['pos'], state['pos_start']]
            size = [state['size'], state['size_start']]
            opacity = [state['opacity'], state['opacity_start']]

            # toggle
            s.menu_on = False

            s.animations[key] = Animate(
                widget=s.menu_root,
                func=bui.imagewidget,
                pos=pos,
                size=size,
                opacity=opacity,
                duration=0.4,
                on_finish=s.cleanup_menu
            )
            return

        # cleanup
        s.cleanup_menu()

        # expand
        s.menu_on = True
        rx,ry = s.real
        sx,sy = 300,200
        x,y = rx-sx,ry-sy-60

        # background
        s.menu_root = bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture(Theme.TEXTURE),
            color=Theme.MAIN,
            opacity=0
        )
        s.menu_kids.append(s.menu_root)

        s.animations[key] = Animate(
            widget=s.menu_root,
            func=bui.imagewidget,
            pos=[(x+sx, y+sy), (x, y)],
            size=[(0, 0), (sx, sy)],
            opacity=[0, Theme.OPACITY],
            duration=0.4
        )

# ba_meta require api 9
# ba_meta export bascenev1.GameActivity
class byBordd(bs.TeamGameActivity[bs.Player,bs.Team]):
    name = 'Movi'
    description = 'Movie Maker'
    get_availabe_settings = lambda s:[]
    supports_session_type = lambda s:True
    get_supported_maps = lambda s:bs.app.classic.getmaps('melee')
    get_instance_description = lambda s: 'Three Two One Action!'
    get_instance_description_short = lambda s: f'Version {__version__}'

    def __init__(s, settings):
        super().__init__(settings)
        s.default_music = bs.MusicType.GRAND_ROMP
        s.editor = Editor()

    def on_begin(s):
        super().on_begin()

    def is_master(s,p):
        return p.sessionplayer.inputdevice.client_id == -1

    def on_player_join(s,p):
        if s.is_master(p):
            s.master = p
            s.make_ui()

    def on_player_leave(s,p):
        if s.is_master(p):
            s.master = None
            s.kill_ui()

    def make_ui(s):
        ba.pushcall(s.editor.make,raw=True)

    def kill_ui(s):
        ba.pushcall(s.editor.kill,raw=True)
