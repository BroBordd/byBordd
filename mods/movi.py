# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Movi v1.0 - Movie Maker

Basic keyframe-based movie maker with dynamic animation system.
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
    TEXT = (1,1,1)
    OPACITY = 0.4
    TEXTURE = 'white'

class Animate:
    def __init__(s, widget, func, attrs, duration, on_start=None, on_finish=None, delay=0, condition=None):
        """
        Dynamic animation system.

        Args:
            widget: The widget to animate
            func: The function to call (e.g., bui.imagewidget, bui.buttonwidget)
            attrs: Dict of attributes to animate, format:
                   {'attr_name': (start_value, end_value), ...}
                   Examples:
                   - {'opacity': (0, 1)}
                   - {'position': ((0,0), (100,200))}
                   - {'size': ((50,50), (200,300)), 'opacity': (0, 0.5)}
            duration: Animation duration in seconds
            on_start: Optional callback when animation starts
            on_finish: Optional callback when animation completes
            delay: Delay in seconds before starting animation
            condition: Optional callable that must return True
        """
        s.widget = widget
        s.func = func
        s.on_start = on_start
        s.on_finish = on_finish
        s.cancelled = False
        s.finished = False
        s.delay = delay
        s.delay_timer = None
        s.timer = None

        # store start and end values for all attributes
        s.attrs_start = {}
        s.attrs_end = {}
        s.attrs_current = {}

        for attr_name, (start_val, end_val) in attrs.items():
            s.attrs_start[attr_name] = start_val
            s.attrs_end[attr_name] = end_val
            # initialize current value
            if isinstance(start_val, (list, tuple)):
                s.attrs_current[attr_name] = list(start_val)
            else:
                s.attrs_current[attr_name] = start_val

        # timing
        s.duration = duration
        s.start_time = None

        # start after delay
        if s.delay > 0:
            s.delay_timer = bui.AppTimer(s.delay, s.start_animation)
        else:
            s.start_animation()

    def start_animation(s):
        """Start the actual animation after delay."""
        if s.cancelled: return
        s.delay_timer = None
        s.start_time = perf_counter()
        s.timer = bui.AppTimer(0.008, s.tick, repeat=True)
        if callable(s.on_start): s.on_start()

    def lerp(s, a, b, t):
        """Linear interpolation for single values or tuples/lists."""
        if isinstance(a, (list, tuple)):
            return [s.lerp(av, bv, t) for av, bv in zip(a, b)]
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

        # interpolate all attributes
        kwargs = {}
        for attr_name in s.attrs_start:
            start_val = s.attrs_start[attr_name]
            end_val = s.attrs_end[attr_name]

            # interpolate
            current_val = s.lerp(start_val, end_val, t)

            # store current state
            s.attrs_current[attr_name] = current_val

            # convert lists back to tuples for widget functions
            if isinstance(current_val, list):
                current_val = tuple(current_val)

            # add to kwargs for function call
            kwargs[attr_name] = current_val

        # apply to widget
        s.func(s.widget, **kwargs)

        # done
        if progress >= 1.0:
            s.timer = None
            s.finish()

    def ease_out(s, t):
        return 1 - (1 - t) ** 3

    def finish(s):
        if callable(s.on_finish) and not s.cancelled:
            s.on_finish()
        s.finished = True

    def cancel(s):
        s.cancelled = True
        s.timer = None
        if s.delay_timer:
            s.delay_timer = None

    def get_state(s):
        """Returns current animation state for all attributes."""
        return {
            'current': s.attrs_current.copy(),
            'start': s.attrs_start.copy(),
            'end': s.attrs_end.copy()
        }

    def reverse(s,**kwargs):
        """
        Create and return a new animation that reverses this one.
        Uses current values as start and original start as end.

        Args:
            Anything __init__ accepts.

        Returns:
            New Animate instance with reversed animation
        """
        # cancel current animation
        s.cancel()

        # build reversed attrs from current state back to original start
        reversed_attrs = {}
        for attr_name in s.attrs_current:
            current = s.attrs_current[attr_name]
            original_start = s.attrs_start[attr_name]

            # convert to appropriate type
            if isinstance(current, list):
                current = tuple(current)
            if isinstance(original_start, list):
                original_start = tuple(original_start)

            reversed_attrs[attr_name] = (current, original_start)

        new = {
            'duration':s.duration
        }
        new.update(kwargs)
        # create new animation
        return Animate(
            widget=s.widget,
            func=s.func,
            attrs=reversed_attrs,
            **new
        )

class Editor:
    def __init__(s):
        s.animations = {}
        # menu
        s.menu_root = None
        s.menu_on = False
        s.menu_kids = []
        # event
        s.event_root = None
        s.event_on = False
        s.event_kids = []
        # entries
        s.entry_xs = 50
        s.entry_ys = 50

    def ui_safe(s):
        return s.root.exists() and not s.root.transitioning_out

    def make(s):
        # root
        s.root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            background=False
        )
        # stamp background
        s.stamp_bg = bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture(Theme.TEXTURE),
            color=Theme.MAIN,
            opacity=Theme.OPACITY
        )
        # square
        s.square = bui.buttonwidget(
            parent=s.root,
            texture=bui.gettexture(Theme.TEXTURE),
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_SQUARE_BUTTON),
            color=Theme.MAIN,
            textcolor=(*Theme.TEXT,Theme.OPACITY),
            enable_sound=False,
            on_activate_call=s.on_square
        )
        bui.containerwidget(s.root,cancel_button=s.square)
        # triangle
        s.triangle = bui.buttonwidget(
            parent=s.root,
            texture=bui.gettexture(Theme.TEXTURE),
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_TRIANGLE_BUTTON),
            color=Theme.MAIN,
            textcolor=(*Theme.TEXT,Theme.OPACITY),
            enable_sound=False,
            on_activate_call=s.on_triangle
        )
        # stamp scroll
        s.stamp_scroll = bui.scrollwidget(
            parent=s.root,
            border_opacity=0,
            color=Theme.TINT
        )
        # stamp scroll root
        s.stamp_scroll_root = bui.containerwidget(
            parent=s.stamp_scroll,
            background=False
        )
        # stamp hscroll
        s.stamp_hscroll = bui.hscrollwidget(
            parent=s.stamp_scroll_root,
            border_opacity=0,
            color=Theme.TINT
        )
        # stamp hscroll root
        s.stamp_hscroll_root = bui.containerwidget(
            parent=s.stamp_hscroll,
            background=False
        )
        # stamp timeline
        s.stamp_timeline = []
        for i in range(100):
            t = bui.textwidget(
                parent=s.stamp_hscroll_root,
                text=(
                    i%5 == 0
                    and str(int(i/5))
                    or '.'
                ),
                h_align='center',
                v_align='center',
                scale=0.5
            )
            s.stamp_timeline.append(t)
        # event button background
        s.event_button_bg = bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture(Theme.TEXTURE),
            color=Theme.MAIN,
            opacity=Theme.OPACITY
        )
        # event button
        s.event_button = bui.buttonwidget(
            parent=s.root,
            label=Strings.EVENT_BUTTON_OFF,
            on_activate_call=s.toggle_event,
            texture=bui.gettexture('empty'),
            opacity=Theme.OPACITY,
            textcolor=(*Theme.TEXT,Theme.OPACITY),
            enable_sound=False
        )
        # finally
        s.wrap()

    def wrap(s):
        rx,ry = s.real = bui.get_virtual_screen_size()
        sx,sy = s.stamp_size = (rx,150)
        # root
        bui.containerwidget(
            s.root,
            size=s.stamp_size,
            stack_offset=(-rx/2+sx/2,-ry/2+sy/2),
        )
        # stamp background
        bui.imagewidget(s.stamp_bg,size=s.stamp_size)
        # square
        bx = 55
        px,py = rx-bx,ry-bx
        bui.buttonwidget(
            s.square,
            position=(px,py),
            size=(bx,bx)
        )
        # triangle
        px -= bx+5
        bui.buttonwidget(
            s.triangle,
            position=(px,py),
            size=(bx,bx)
        )
        # stamp scroll
        bui.scrollwidget(s.stamp_scroll,size=s.stamp_size)
        # stamp scroll root
        deep_y = s.entry_ys*10
        bui.containerwidget(
            s.stamp_scroll_root,
            size=(sx,deep_y)
        )
        # stamp hscroll
        bui.hscrollwidget(
            s.stamp_hscroll,
            size=(sx,deep_y)
        )
        # stamp hscroll root
        deep_x = s.entry_xs*50
        bui.containerwidget(
            s.stamp_hscroll_root,
            size=(deep_x,deep_y)
        )
        # top left
        bui.containerwidget(
            s.stamp_hscroll_root,
            visible_child=(
                (tl:=bui.textwidget(
                    parent=s.stamp_hscroll_root,
                    position=(0,deep_y)
                ))
            )
        ) or 1 and tl.delete()
        # stamp timeline
        for i,t in enumerate(s.stamp_timeline):
            bui.textwidget(
                t,
                position=(i*s.entry_xs,deep_y-30)
            )
        # event button background
        dx,dy = s.event_button_size = 100,40
        s.event_root = bui.imagewidget(
            s.event_button_bg,
            size=(dx,dy),
            position=(0,sy+5)
        )
        # event button
        bui.buttonwidget(
            s.event_button,
            size=(dx,dy),
            position=(0,sy+5)
        )

    def on_square(s):
        s.toggle_menu()

    def on_triangle(s):
        bui.get_special_widget('squad_button').activate()

    def kill(s):
        if not s.ui_safe(): return
        s.root.delete()

    def toggle_menu(s):
        bui.getsound('deek').play()
        key = 'menu'

        # cancel
        if key in s.animations:
            s.animations[key].cancel()

        def cleanup():
            if s.menu_root and s.menu_root.exists():
                s.menu_root.delete()
            for kid in s.menu_kids:
                if kid.exists():
                    kid.delete()
            s.menu_kids.clear()
            s.menu_root = None

        if s.menu_on:
            # collapse
            anim = s.animations.get(key)
            if not anim: return

            # toggle
            s.menu_on = False

            s.animations[key] = anim.reverse(
                duration=0.4,
                on_finish=cleanup
            )
            return

        # cleanup
        cleanup()

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
            attrs={
                'position': ((x+sx, y+sy), (x, y)),
                'size': ((0, 0), (sx, sy)),
                'opacity': (0, Theme.OPACITY)
            },
            duration=0.4
        )

    def toggle_event(s):
        bui.getsound('deek').play()
        key = id(s.event_button)

        # cancel
        if key in s.animations:
            s.animations[key].cancel()

        def cleanup():
            for kid in s.event_kids:
                if kid.exists():
                    kid.delete()
            s.event_kids.clear()

        if s.event_on:
            # collapse = reverse all
            anim = s.animations.get(key)
            if not anim: return

            s.event_on = False
            bui.buttonwidget(s.event_button, label=Strings.EVENT_BUTTON_OFF)

            s.animations[key] = anim.reverse(duration=0.4, on_finish=cleanup)

            # reverse child button animations
            for btn_id in [id(s.node_button), id(s.camera_button), id(s.sound_button),
                           id(s.fx_button), id(s.map_button), id(s.custom_button)]:
                if (anim := s.animations.get(btn_id, None)):
                    anim.reverse(duration=0.1)
            return

        # cleanup
        cleanup()

        # expand
        s.event_on = True
        bui.buttonwidget(s.event_button, label=Strings.EVENT_BUTTON_ON)

        # define parent stuff
        rx, ry = s.real
        sx, sy = 300, 350
        x, y = 0, s.stamp_size[1] + 5
        dx, dy = s.event_button_size
        off = 10
        parent_duration = 0.4

        # conditional params
        child_start_progress = 0.2
        child_delay = parent_duration * child_start_progress
        child_duration = parent_duration * (1 - child_start_progress)

        # button max
        mx = sx - 40

        # make buttons
        s.node_button = bui.buttonwidget(
            parent=s.root,
            position=(x + 20, y + sy - (dy + off)),
            label=Strings.NODE_BUTTON,
            color=Theme.MAIN,
            textcolor=(0, 0, 0, 0),
            texture=bui.gettexture(Theme.TEXTURE),
            opacity=0
        )
        s.camera_button = bui.buttonwidget(
            parent=s.root,
            position=(x + 20, y + sy - (dy + off) * 2),
            label=Strings.CAMERA_BUTTON,
            color=Theme.MAIN,
            textcolor=(0, 0, 0, 0),
            texture=bui.gettexture(Theme.TEXTURE),
            opacity=0
        )
        s.sound_button = bui.buttonwidget(
            parent=s.root,
            position=(x + 20, y + sy - (dy + off) * 3),
            label=Strings.SOUND_BUTTON,
            color=Theme.MAIN,
            textcolor=(0, 0, 0, 0),
            texture=bui.gettexture(Theme.TEXTURE),
            opacity=0
        )
        s.fx_button = bui.buttonwidget(
            parent=s.root,
            position=(x + 20, y + sy - (dy + off) * 4),
            label=Strings.FX_BUTTON,
            color=Theme.MAIN,
            textcolor=(0, 0, 0, 0),
            texture=bui.gettexture(Theme.TEXTURE),
            opacity=0
        )
        s.map_button = bui.buttonwidget(
            parent=s.root,
            position=(x + 20, y + sy - (dy + off) * 5),
            label=Strings.MAP_BUTTON,
            color=Theme.MAIN,
            textcolor=(0, 0, 0, 0),
            texture=bui.gettexture(Theme.TEXTURE),
            opacity=0
        )
        s.custom_button = bui.buttonwidget(
            parent=s.root,
            position=(x + 20, y + sy - (dy + off) * 6),
            label=Strings.CUSTOM_BUTTON,
            color=Theme.MAIN,
            textcolor=(0, 0, 0, 0),
            texture=bui.gettexture(Theme.TEXTURE),
            opacity=0
        )
        buttons_config = [
            (s.node_button, 1),
            (s.camera_button, 2),
            (s.sound_button, 3),
            (s.fx_button, 4),
            (s.map_button, 5),
            (s.custom_button, 6),
        ]

        # all buttons are kids
        for btn, _ in buttons_config:
            s.event_kids.append(btn)

        # animate parent (event root)
        s.animations[key] = Animate(
            widget=s.event_root,
            func=bui.imagewidget,
            attrs={
                'position': ((x, y), (x, y)),
                'size': ((dx, dy), (sx, sy)),
                'opacity': (Theme.OPACITY, Theme.OPACITY)
            },
            duration=parent_duration
        )

        # animate kids
        # start based on expanision
        parent_width_progress = dx + (sx - dx) * child_start_progress
        # proportional size
        start_width_ratio = (parent_width_progress - 40) / mx  # 40 is margin

        num_buttons = len(buttons_config)
        for btn, idx in buttons_config:
            # stagger delay
            stagger = 0.02 * (num_buttons - idx)

            s.animations[id(btn)] = Animate(
                widget=btn,
                func=bui.buttonwidget,
                attrs={
                    'opacity': (0, Theme.OPACITY),
                    'textcolor': (
                        (*Theme.TEXT, 0),
                        (*Theme.TEXT, Theme.OPACITY)
                    ),
                    'size': ((mx * start_width_ratio, dy), (mx, dy))
                },
                duration=child_duration,
                delay=child_delay + stagger
            )

class Strings:
    EVENT_BUTTON_OFF = 'Event'
    EVENT_BUTTON_ON = 'Back'
    NAME = 'Movi'
    DESCRIPTION = 'Movie Maker'
    INSTANCE_DESCRIPTION = 'Three Two One Action!'
    INSTANCE_DESCRIPTION_SHORT = f'Version {__version__}'
    NODE_BUTTON = 'Node'
    CAMERA_BUTTON = 'Camera'
    SOUND_BUTTON = 'Sound'
    FX_BUTTON = 'FX'
    MAP_BUTTON = 'Map'
    CUSTOM_BUTTON = 'Custom'

# ba_meta require api 9
# ba_meta export bascenev1.GameActivity
class byBordd(bs.TeamGameActivity[bs.Player,bs.Team]):
    name = Strings.NAME
    description = Strings.DESCRIPTION
    get_availabe_settings = lambda s:[]
    supports_session_type = lambda s:True
    get_supported_maps = lambda s:bs.app.classic.getmaps('melee')
    get_instance_description = lambda s: Strings.INSTANCE_DESCRIPTION
    get_instance_description_short = lambda s: Strings.INSTANCE_DESCRIPTION_SHORT

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
