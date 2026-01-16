# Copyright 2026 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @BroBordd

"""
Board v1.0 - The Board

Yes
"""

import babase as ba
import bauiv1 as bui

from base64 import b64encode, b64decode, b85decode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from mimetypes import guess_type
from weakref import WeakMethod
from datetime import datetime
from time import perf_counter
from json import dumps, loads
from threading import Thread
from hashlib import sha256
from random import random
from enum import Enum

class Config:
    COLOR = 'Light'
    STRING = 'English'
    STARTUP = True

class Board:
    _shared = {'callbacks':[]}

    @staticmethod
    def _call(sig):
        for callback_ref in Editor._shared['callbacks']:
            callback = callback_ref()
            callback(sig)

    def callback(s,cb):
        bui.apptimer(Const.BA_LAG_SMALL,getattr(s,cb))

    def __init__(s,source=None):
        s.__class__._shared['callbacks'].append(
            WeakMethod(s.callback)
        )
        s.anims = {}
        Eval.SOUND(Const.SOUND_HI,0.15)
        x,y = size = Eval.REAL(margin=0.2)
        # root
        s.root = Widget.WINDOW(
            size=size,
            source=source
        )
        # title bg
        bx = 50
        marg = 40
        px,py = bx+marg,y-70
        dx,dy = x-(bx*2+marg*2),50
        Widget.IMAGE(
            s.root,
            position=(px,py-2),
            size=(dx,dy+4),
            color=Color.COLD,
        )
        # back
        bui.buttonwidget(
            (back:=Widget.BUTTON(
                s.root,
                position=(20,py),
                size=(bx,bx),
                label=Eval.CHAR(Const.CHAR_BACK),
                text_scale=0.8
            )), on_activate_call=bui.CallPartial(
                s.exit, source
            )
        )
        bui.containerwidget(s.root,cancel_button=back)
        # title
        s.title = Widget.TEXT(
            s.root,
            position=(px+marg/2,py+dy/4-2),
            text=String.WAIT
        )
        # add
        bui.buttonwidget(
            (b:=Widget.BUTTON(
                s.root,
                position=(marg*1.5+dx+bx,py),
                size=(bx,bx),
                label=Eval.CHAR(Const.CHAR_POST),
                text_scale=1.1
            )), on_activate_call=bui.CallPartial(
                s.post_window, b
            )
        )
        # scroll
        sx,sy = s.scroll_size = x-marg,y-marg*1.5-dy
        s.scroll = Widget.SCROLL(
            s.root,
            position=(marg/2,marg/2),
            size=(sx,sy)
        )
        # scroll root
        cx,cy = sx,sy-15
        s.scroll_root = Widget.CONTAINER(
            s.scroll,
            size=(cx,cy)
        )
        # art
        s.art = Art(
            s.root,
            String.TITLE,
            position=(x/2.35,y/2),
            scale=3,
            opacity=Color.OPACITY/1.5
        )
        # finally
        s.fetch_thread = Thread(target=s.fetch).start()

    def update_title(s, new_text, on_finish=None):
        # fade
        Animate(
            widget=s.title,
            attrs={
                'color': (
                    Eval.TEXT(Color.OPACITY),
                    Const.INVISIBLE
                )
            },
            duration=0.2,
            on_finish=lambda: s._change_title_text(new_text, on_finish)
        )

    def _change_title_text(s, new_text, on_finish=None):
        # update
        bui.textwidget(s.title, text=new_text)
        # fade
        Animate(
            widget=s.title,
            attrs={
                'color': (
                    Const.INVISIBLE,
                    Eval.TEXT(Color.OPACITY)
                )
            },
            duration=0.2,
            on_finish=on_finish
        )

    def render(s, cat):
        if s.art:
            # fade
            s.art.fade_out(
                duration=0.3,
                on_finish=s.art.delete
            )
            # title
            bui.apptimer(0.2, lambda: s.update_title(String.TITLE))
            # catalog
            bui.apptimer(0.1, lambda: s._render_catalog_content(cat))
        else:
            s.update_title(String.TITLE)
            s._render_catalog_content(cat)

    def _render_catalog_content(s, cat):
        x, y = s.scroll_size
        marg = 10
        ey = 150
        xt = 40
        ix = ey - marg
        ry = (marg + ey+xt) * len(cat)
        # widgets
        widgets_to_animate = []

        for i, c in enumerate(cat, start=1):
            px, py = (0, ry - (marg + ey + xt) * i)
            files = c['files']
            # bg
            bg = Widget.IMAGE(
                s.scroll_root,
                size=(x, ey),
                position=(px, py),
                color=Color.COLD,
                opacity=0
            )
            widgets_to_animate.append((bg, 'opacity', (0, Color.OPACITY), 0.1 + i*0.05))
            # head
            head = Widget.IMAGE(
                s.scroll_root,
                size=(x, xt),
                position=(px, py + ey),
                color=Color.WARM,
                opacity=0
            )
            widgets_to_animate.append((head, 'opacity', (0, Color.OPACITY), 0.1 + i*0.05))
            # img
            img = Widget.IMAGE(
                s.scroll_root,
                position=(px + marg/2, py + marg/2),
                size=(ix, ix),
                texture=Eval.COVER_IMG(files),
                opacity=0
            )
            widgets_to_animate.append((img, 'opacity', (0, Color.OPACITY), 0.15 + i*0.05))
            # user
            user = Widget.TEXT(
                s.scroll_root,
                text=Eval.USER(c['user_hash']),
                position=(marg/2, py + ey + marg/2),
                opacity=0
            )
            widgets_to_animate.append((user, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY)), 0.15 + i*0.05))
            # id
            idx = 70
            id_text = Widget.TEXT(
                s.scroll_root,
                text=Eval.METADATA(c['timestamp'], c['id']),
                position=(x - idx - marg/2, py + ey + marg/2),
                h_align=Const.ALIGN_RIGHT,
                opacity=0
            )
            widgets_to_animate.append((id_text, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY/2)), 0.15 + i*0.05))
            # title
            title = Widget.TEXT(
                s.scroll_root,
                position=(px + ix + marg*1.5, py + ey - (marg + 30)),
                text=c['title'],
                maxwidth=x - ix - marg*2,
                scale=1.3,
                v_align=Const.ALIGN_CENTER,
                opacity=0
            )
            widgets_to_animate.append((title, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY)), 0.2 + i*0.05))
            # desc
            desc = Widget.TEXT(
                s.scroll_root,
                position=(px + ix + marg, py + ey - (marg + 60)),
                text='\n'.join(c['description'].split('\n')[:3]),
                maxwidth=x - ix - marg*2,
                max_height=ix - 30,
                opacity=0
            )
            widgets_to_animate.append((desc, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY/2)), 0.2 + i*0.05))
            # sensor
            sensor = bui.buttonwidget(
                parent=s.scroll_root,
                position=(px, py + marg/2),
                size=(x, ey + xt - marg),
                label=Const.BLANK,
                texture=Eval.TEXTURE(Const.EMPTY_IMG),
                opacity=0,
                enable_sound=False
            )
            widgets_to_animate.append((sensor, 'opacity', (0, 0.01), 0.25 + i*0.05))

            bui.buttonwidget(
                sensor,
                on_activate_call=bui.CallPartial(s.msg_window, c, sensor)
            )

        bui.containerwidget(s.scroll_root, size=(x, ry))
        # animate
        for widget, attr_name, (start, end), delay in widgets_to_animate:
            if attr_name == 'opacity':
                attrs = {'opacity': (start, end)}
            else:
                attrs = {'color': (start, end)}

            Animate(
                widget=widget,
                attrs=attrs,
                duration=0.4,
                delay=delay
            )

    def fetch(s):
        try: cat = catalog()
        except Exception as e:
            call = bui.CallPartial(
                bui.textwidget, s.title, text=str(e)
            )
        else: call = bui.CallPartial(s.render, cat)
        ba.pushcall(call, from_other_thread=True)

    def exit(s,source=None):
        if s.art:
            s.art.delete()
            s.art = None
        bui.containerwidget(
            s.root,transition=Eval.TRANSITION(source,out=True)
        )
        Eval.SOUND(Const.SOUND_BYE)

    def on_resize(s):
        pass

    def on_rescale(s):
        pass

    def post_window(s,source=None):
        size = x,y = Eval.REAL(margin=0.5)
        Eval.SOUND(Const.SOUND_HI)
        # root
        root = Widget.WINDOW(
            source=source,
            size=size
        )
        # back
        bx = 50
        marg = 10
        py = y-bx-marg*2
        def back():
            bui.containerwidget(
                root,transition=Eval.TRANSITION(source,True)
            )
            Eval.SOUND(Const.SOUND_BYE)
        bui.containerwidget(root,cancel_button=(
            Widget.BUTTON(
                root,
                position=(20,py),
                size=(bx,bx),
                label=Eval.CHAR(Const.CHAR_BACK),
                text_scale=0.8,
                on_activate_call=back
            )
        ))

    def msg_window(s,c,source=None):
        size = x,y = Eval.REAL(margin=0.3)
        Eval.SOUND(Const.SOUND_HI)
        # root
        root = Widget.WINDOW(
            source=source,
            size=size
        )
        # back
        bx = 50
        marg = 10
        py = y-bx-marg*2
        def back():
            bui.containerwidget(
                root,transition=Eval.TRANSITION(source,True)
            )
            Eval.SOUND(Const.SOUND_BYE)
        bui.containerwidget(root,cancel_button=(
            Widget.BUTTON(
                root,
                position=(20,py),
                size=(bx,bx),
                label=Eval.CHAR(Const.CHAR_BACK),
                text_scale=0.8,
                on_activate_call=back,
                color=Color.WARM
            )
        ))
        # block
        cx = 350
        px = bx+marg*4
        dx,dy = x-(bx*2+marg*3+cx),bx
        bsy = y-(marg*6+dy)
        Widget.IMAGE(
            root,
            position=(marg*2,marg*2),
            size=(bx,bsy),
            color=Color.WARM
        )
        # id
        Widget.TEXT(
            root,
            text=c['id'],
            rotate=90,
            position=(marg+bx/1.43,marg*2),
            opacity=Color.OPACITY/2,
            v_align=Const.ALIGN_CENTER
        )
        # title
        Widget.IMAGE(
            root,
            position=(px,py-2),
            size=(dx,dy+4),
            color=Color.WARM
        )
        Widget.IMAGE(
            root,
            position=(px,marg*2),
            size=(dx,bsy),
            color=Color.COLD
        )
        Widget.TEXT(
            root,
            position=(px+marg*2,marg+bsy-30),
            text=c['title'],
            maxwidth=dx-marg*2,
            scale=1.3,
            v_align=Const.ALIGN_CENTER
        )
        Widget.TEXT(
            root,
            position=(px+marg*1.7,marg+bsy-65),
            text=c['description'],
            maxwidth=dx-marg*2,
            opacity=Color.OPACITY/2
        )
        # comment
        Widget.IMAGE(
            root,
            position=(px+dx+marg*2,py-2),
            size=(cx,dy+4),
            color=Color.WARM
        )
        Widget.IMAGE(
            root,
            position=(px+dx+marg*2,marg*2),
            size=(cx,y-(marg*6+dy)),
            color=Color.COLD
        )
        Widget.TEXT(
            root,
            position=(px+dx+marg/2+cx/2.1,py+marg),
            text=String.COMMENTS,
            h_align=Const.ALIGN_CENTER
        )
        # user
        Widget.TEXT(
            root,
            text=Eval.USER(c['user_hash']),
            position=(bx+marg*5,py+marg),
            maxwidth=dx*0.7-marg,
            v_align=Const.ALIGN_CENTER
        )
        # count
        files = c['files']
        Widget.TEXT(
            root,
            text=Eval.COUNT(files,String.FILE,String.FILES),
            position=(x-(cx+marg*10.5),py+marg),
            h_align=Const.ALIGN_RIGHT,
            maxwidth=dx*0.26,
            v_align=Const.ALIGN_CENTER,
            opacity=Color.OPACITY/2
        )
        # files
        file_x = 100
        xt = 30
        step = (file_x+marg)
        rdx = max(len(files)*step,dx-15)
        file_root = Widget.CONTAINER(
            Widget.HSCROLL(
                root,
                position=(px,marg*2),
                size=(dx,file_x+xt)
            ),
            size=(rdx,file_x+xt)
        )
        for i,f in enumerate(files):
            n = f['original_name']
            im = Eval.FILE_IMG(n)
            gay = marg if im != Const.FILE_IMG else 5
            Widget.IMAGE(
                file_root,
                position=(i*step+gay,xt-marg),
                size=(file_x,file_x),
                texture=Eval.TEXTURE(im)
            )
            Widget.TEXT(
                file_root,
                position=(file_x/3.6+i*step,0),
                maxwidth=file_x,
                text=n,
                v_align=Const.ALIGN_CENTER,
                h_align=Const.ALIGN_CENTER
            )

# custom ui
# more like handmade widgets

class Art:
    def __init__(s,parent,text,position,gap=60,opacity=None,**kw):
        s.opacity = opacity
        s.parent = parent
        px,py = position
        # art
        s.kids = [
            Widget.TEXT(
                parent,
                flatness=-3,
                big=True,
                text=t,
                position=(px+gap*i,py),
                opacity=opacity,
                **kw
            )
            for i,t in enumerate(text)
        ]
        off = random()
        s.art_color_idx = [int(off * len(Const.ART)) for _ in range(len(text))]
        s.art_progress = [(i / len(text) + off) % 1.0 for i in range(len(text))]
        s.art_timer = bui.AppTimer(0.01, s.animate, repeat=True)
        # pro
        s.pro_base_x,s.pro_base_y = pos = px-45,py-40
        s.pro_time = 0.0
        s.pro_bg = Widget.IMAGE(
            parent,
            position=pos,
            opacity=opacity,
            size=(285,5),
            color=Color.COLD
        )
        s.pro = Widget.IMAGE(
            parent,
            position=pos,
            opacity=opacity*2,
            size=(55,5),
            color=Color.COLD
        )
        s.anims = {}

    def animate(s):
        for i,k in enumerate(s.kids):
            s.art_progress[i] -= 0.02

            if s.art_progress[i] < 0:
                s.art_progress[i] += 1.0
                s.art_color_idx[i] = (s.art_color_idx[i] + 1) % len(Const.ART)

            current_idx = s.art_color_idx[i]
            next_idx = (current_idx + 1) % len(Const.ART)

            blended = tuple(
                Const.ART[current_idx][j] * s.art_progress[i] +
                Const.ART[next_idx][j] * (1 - s.art_progress[i])
                for j in range(3)
            )+(s.opacity,)

            bui.textwidget(k, color=blended)
        # pro
        s.pro_time += 0.02
        bg_width = 285
        bar_width = 55

        cycle = (s.pro_time % 2.0) / 2.0
        t = cycle * 2
        t = (t if t < 1 else 2 - t)
        t = t * t * (3.0 - 2.0 * t)

        x_offset = (bg_width - bar_width) * t
        bui.imagewidget(s.pro, position=(s.pro_base_x + x_offset, s.pro_base_y), size=(bar_width, 5))

    def fade_out(s, duration=0.3, on_finish=None):
        """Fade out all art elements"""
        # Stop color animation
        s.art_timer = None

        # Fade out text widgets (using color alpha channel)
        for kid in s.kids:
            s.anims[id(kid)] = Animate(
                widget=kid,
                attrs={
                    'color': (
                        Eval.TEXT(s.opacity),
                        Const.INVISIBLE
                    )
                },
                duration=duration
            )

        # Fade out image widgets (using opacity)
        s.anims[id(s.pro_bg)] = Animate(
            widget=s.pro_bg,
            attrs={'opacity': (s.opacity, 0)},
            duration=duration
        )

        s.anims[id(s.pro)] = Animate(
            widget=s.pro,
            attrs={'opacity': (s.opacity*2, 0)},
            duration=duration,
            on_finish=on_finish  # Call cleanup after last animation
        )

    def delete(s):
        s.art_timer = None
        s.pro_bg.delete()
        s.pro.delete()
        for k in s.kids: k.delete()
        s.kids.clear()
        s.anims.clear()

# widgets
# logic to save code with defaults

class Widget:
    BUTTON = lambda p,color=None,**kw: bui.buttonwidget(
        parent=p,
        texture=Eval.TEXTURE(Const.BASE),
        color=color or Color.COLD,
        textcolor=Color.TEXT,
        enable_sound=False,
        opacity=Color.OPACITY,
        **kw
    )
    TEXT = lambda p,opacity=None,**kw: bui.textwidget(
        parent=p,
        color=Eval.TEXT(
            Color.OPACITY
            if opacity is None
            else opacity
        ),
        **kw
    )
    IMAGE = lambda p,opacity=None,texture=None,**kw: bui.imagewidget(
        parent=p,
        opacity=(
            Color.OPACITY
            if opacity is None
            else opacity
        ),
        texture=texture or Eval.TEXTURE(Const.BASE),
        **kw
    )
    CONTAINER = lambda p=None,source=None,**kw: bui.containerwidget(
        parent=p or bui.get_special_widget('overlay_stack'),
        background=False,
        scale_origin_stack_offset=source and source.get_screen_space_center() or source,
        transition=Eval.TRANSITION(source),
        **kw
    )
    SCROLL = lambda p,**kw: bui.scrollwidget(
        parent=p,
        color=Color.COLD,
        border_opacity=False,
        **kw
    )
    HSCROLL = lambda p,**kw: bui.hscrollwidget(
        parent=p,
        color=Color.COLD,
        border_opacity=False,
        **kw
    )
    WINDOW = lambda size,source=None,**k: (
        (root:=Widget.CONTAINER(
            source=source,
            size=size,
            **k
        )) and
        (shadow:=Eval.SHADOW(*size)) and
        Widget.IMAGE(
            root,
            position=shadow[0],
            size=shadow[1],
            texture=Eval.TEXTURE(Const.SHADOW),
            color=Color.SHADOW
        ) and
        Widget.IMAGE(
            root,
            position=(-1,-1),
            size=size,
            color=Color.BASE
        ) and root
    )

# evaluation
# static math by various parts in code

class Eval:
    WIDGET = lambda w: getattr(
        bui, w.get_widget_type() + 'widget'
    )
    TRANSITION = lambda source=None,out=False:(
        Const.TRANSITION[bool(source)][out]
    )
    SUBCLASS = lambda cls,sub,fallback: next(
        (c for c in cls.__subclasses__()
        if c.__name__[:-len(cls.__name__)] == sub), fallback
    )
    SOUND = lambda which,duration=0:(
        (sound:=bui.getsound(which)).play() or
        (duration and bui.apptimer(duration,sound.stop))
    )
    TEXTURE = lambda texture:(
        bui.gettexture(texture)
    )
    CHAR = lambda char:(
        char in bui.SpecialChar.__members__
        and bui.charstr(
            getattr(
                bui.SpecialChar,
                char
            )
        ) or char
    )
    SHADOW = lambda x,y:(
        (-x*0.1,-y*0.1),
        (x*1.2,y*1.2)
    )
    REAL = lambda margin=0: tuple(
        r-(margin*r) for r in
        bui.get_virtual_screen_size()
    )
    TEXT = lambda opacity: (*Color.TEXT,opacity)
    USER = lambda u: (
        Eval.CHAR(Const.CHAR_USER) + Const.SPACE +
        Const.USER_PREFIX + u
    )
    METADATA = lambda t,i: (
        datetime.fromisoformat(t).strftime(Const.TIMESTAMP_FORMAT) +
        Const.SPACE * 3 + i
    )
    COVER_IMG = lambda files: Eval.TEXTURE(
        Const.DEFAULT_IMG if not files
        else Eval.FILE_IMG(files[0]['original_name'])
    )
    FILE_IMG = lambda file: (
        (ty:=guess_type(
            file
        )[0] or Const.BLANK),(
            Const.AUDIO_IMG
            if (
                ty.startswith('audio/') or
                file.endswith('.ogg')
            )
            else Const.REPLAY_IMG
            if file.endswith('.brp')
            else Const.SCRIPT_IMG
            if file.endswith('.py')
            else Const.FILE_IMG
        )
    )[1]
    COUNT = lambda l,t1,t2: (
        ((i:=len(l)) or 1) and (
            str(i) + Const.SPACE +
            (i != 1 and t2 or t1)
        )
    )

# colors
# very flexible

class Color: pass

class DarkColor(Color):
    BASE = (0,0,0)
    COLD = (0.08,0.08,0.08)
    WARM = (0.2,0.2,0.2)
    TEXT = (2,2,2)
    SHADOW = (0,0,0)
    OPACITY = 0.8

class LightColor(Color):
    BASE = (1,1,1)
    COLD = (0.75,0.75,0.75)
    WARM = (0.6,0.6,0.6)
    TEXT = (0,0,0)
    SHADOW = (0.3,0.3,0.3)
    OPACITY = 0.8

Color = Eval.SUBCLASS(Color,Config.COLOR,DarkColor)

# strings
# all text used is defined here

class String: pass

class EnglishString(String):
    TITLE = 'Board'
    WAIT = 'Just a sec...'
    FILE = 'File'
    FILES = 'Files'
    COMMENTS = 'Comments'

String = Eval.SUBCLASS(String,Config.STRING,EnglishString)

# constants
# these are never changed on runtime

class Const:
    BA_LAG_SMALL = 0.01
    TRANSITION = (
        ('in_left','out_left'),
        ('in_scale','out_scale')
    )
    BASE = 'white'
    SHADOW = 'softRect'
    DEFAULT_IMG = 'star'
    FILE_IMG = 'file'
    SCRIPT_IMG = 'advancedIcon'
    EMPTY_IMG = 'empty'
    REPLAY_IMG = 'tv'
    AUDIO_IMG = 'audioIcon'
    CHAR_BACK = 'BACK'
    CHAR_USER = 'LOGO_FLAT'
    CHAR_POST = 'DPAD_CENTER_BUTTON'
    USER_PREFIX = 'Anonymous_'
    ALIGN_CENTER = 'center'
    ALIGN_RIGHT = 'right'
    SOUND_HI = 'powerup01'
    SOUND_BYE = 'laser'
    INVISIBLE = (0,0,0,0)
    SPACE = ' '
    BLANK = ''
    TIMESTAMP_FORMAT = '%d/%m/%y %H:%M:%S'
    ART = (
        (2.0, 0.3, 2.2),
        (2.2, 0.3, 1.5),
        (3.0, 0.3, 0.3),
        (2.2, 1.8, 0.3),
        (0.3, 2.0, 1.8),
    )

# tools
# classes that do big stuff

class Animate:
    def __init__(s, widget, attrs, duration, on_start=None, on_finish=None, on_cancel=None, delay=0, condition=None, on_reverse=None):
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
        s.on_start = on_start
        s.on_finish = (
            isinstance(on_finish,tuple) and bui.CallPartial(
                s.reverse,
                on_finish=on_finish[0]
            ) or on_finish
        )
        s.on_reverse = on_reverse
        s.on_cancel = on_cancel
        s.cancelled = False
        s.finished = False
        s.delay = delay
        s.delay_timer = None
        s.timer = None
        s.condition = condition
        if not widget.exists(): return
        s.func = Eval.WIDGET(widget)

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

    def __del__(s):
        s.cancel()

    def start_animation(s):
        """Start the actual animation after delay."""
        if s.cancelled: return
        if callable(s.condition) and not s.condition(): return
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
        if s.cancelled:
            s.timer = None
            return s.finish()

        # no thanks
        if not s.widget.exists():
            s.timer = None
            s.delay_timer = None
            s.cancelled = True
            return

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
        s.finished = True
        if callable(s.on_finish) and not s.cancelled:
            s.on_finish()

    def complete(s):
        """Immediately complete the animation by applying final values."""
        if s.cancelled or s.finished:
            return

        s.cancel()  # Stop the timer

        # Apply final state
        if s.widget.exists():
            kwargs = {}
            for attr_name, end_val in s.attrs_end.items():
                # Convert lists to tuples for widget functions
                if isinstance(end_val, list):
                    end_val = tuple(end_val)
                kwargs[attr_name] = end_val
                # Update current state to match end
                s.attrs_current[attr_name] = end_val

            s.func(s.widget, **kwargs)

        # Mark as finished and call callback
        s.finished = True
        if callable(s.on_finish):
            s.on_finish()

    def cancel(s):
        s.cancelled = True
        s.timer = None
        if s.delay_timer:
            s.delay_timer = None
        if callable(s.on_cancel) and not s.finished:
            s.on_cancel()

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
        callable(s.on_reverse) and s.on_reverse()
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
            attrs=reversed_attrs,
            **new
        )

# core
# do not modify

class Data(Enum):
    @property
    def real(s):
        return b85decode(s.value).decode()

    OWNER = "LUM0HZ*pX0"
    VAULT = "VsBw`WB"
    KEY = (
        'F)>0;Hbz-cNia7yQgcc'
        '$LsMFCH!)v#Fj8VdF-A'
        '%-O+{jEWHvT5S5;&&Mo'
        'dyMMrCY9dQE9-M@=+2M'
        '0s;kLQpqXLNixLOH*)V'
        'Zdh?lS9b'
    )
    API_URL = 'XmoUNb2=|CVQ^_KXK8e3bz&}KZ*2'
    GRAPHQL = 'XmoUNb2=|CVQ^_KXK8e3bz&}KZ*4DUa$#_2acl'

def _get_headers():
    return {
        "Authorization": f"Bearer github_pat_{Data.KEY.real}"
    }

def _seal(secret):
    return sha256(secret.encode()).hexdigest()[:12]

def _upload_to_temp_host(filepath):
    """Upload file to catbox.moe and return URL"""
    with open(filepath, 'rb') as f:
        file_data = f.read()

    filename = os.path.basename(filepath)

    try:
        boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="reqtype"\r\n\r\n'
            f'fileupload\r\n'
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="fileToUpload"; filename="{filename}"\r\n'
            f'Content-Type: application/octet-stream\r\n\r\n'
        ).encode() + file_data + f'\r\n--{boundary}--\r\n'.encode()

        req = Request(
            'https://catbox.moe/user/api.php',
            data=body,
            headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
        )

        with urlopen(req, timeout=30) as response:
            url = response.read().decode().strip()
            if url.startswith('http'):
                return url
    except Exception as e:
        raise Exception(f"Upload to catbox failed: {e}")

def _forge(subject, payload):
    """Create GitHub Discussion"""
    probe = """
    query {
      repository(owner: "%s", name: "%s") {
        id
        discussionCategories(first: 1) {
          nodes {
            id
            name
          }
        }
      }
    }
    """ % (Data.OWNER.real, Data.VAULT.real)

    headers = {
        **_get_headers(),
        "Content-Type": "application/json"
    }

    data = dumps({"query": probe}).encode('utf-8')
    req = Request(Data.GRAPHQL.real, data=data, headers=headers)

    with urlopen(req) as response:
        result = loads(response.read().decode('utf-8'))

    vault_id = result['data']['repository']['id']
    space_id = result['data']['repository']['discussionCategories']['nodes'][0]['id']

    escaped_payload = payload.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
    escaped_subject = subject.replace('\\', '\\\\').replace('"', '\\"')

    spell = """
    mutation {
      createDiscussion(input: {
        repositoryId: "%s",
        categoryId: "%s",
        title: "%s",
        body: "%s"
      }) {
        discussion {
          id
          url
        }
      }
    }
    """ % (vault_id, space_id, escaped_subject, escaped_payload)

    data = dumps({"query": spell}).encode('utf-8')
    req = Request(Data.GRAPHQL.real, data=data, headers=headers)

    with urlopen(req) as response:
        result = loads(response.read().decode('utf-8'))

    return result['data']['createDiscussion']['discussion']['url']

def upload(secret, title, description, filepaths_or_urls):
    """Upload multiple files/URLs as a post"""
    stamp = _seal(secret)

    # GitHub Discussion body limit is ~65KB
    # Base64 increases size by ~33%, so max raw file size 48KB
    # Use 40KB safety margin
    MAX_DIRECT_SIZE = 40 * 1024  # 40KB

    files_data = []
    total_local_size = 0

    for item in filepaths_or_urls:
        # Check if it's a URL or local file
        if item.startswith('http://') or item.startswith('https://'):
            # Direct URL - let server download it
            # Extract filename from URL or use a default
            url_path = item.split('?')[0]  # Remove query params
            original_name = os.path.basename(url_path) or 'download'
            extension = os.path.splitext(original_name)[1][1:] or 'bin'

            files_data.append({
                "name": original_name,
                "ext": extension,
                "size": 0,  # Unknown size
                "direct_url": item
            })
        else:
            # Local file
            original_name = os.path.basename(item)
            extension = os.path.splitext(original_name)[1][1:]
            file_size = os.path.getsize(item)
            total_local_size += file_size

            files_data.append({
                "name": original_name,
                "ext": extension,
                "size": file_size,
                "filepath": item  # Mark as local file
            })

    # Decide method based on local files only
    use_temp_host = total_local_size > MAX_DIRECT_SIZE

    # Process local files
    for file_data in files_data:
        if 'filepath' in file_data:
            filepath = file_data['filepath']

            if use_temp_host:
                # Upload to catbox
                temp_url = _upload_to_temp_host(filepath)
                file_data['temp_url'] = temp_url
                del file_data['filepath']
            else:
                # Base64 encode
                with open(filepath, 'rb') as f:
                    file_content = f.read()
                file_data['data'] = b64encode(file_content).decode()
                del file_data['filepath']

    # Determine method
    has_direct = any('direct_url' in f for f in files_data)
    has_temp = any('temp_url' in f for f in files_data)
    has_base64 = any('data' in f for f in files_data)

    if has_direct and not has_temp and not has_base64:
        method = "direct_url"
    elif has_temp:
        method = "temp_url"
    elif has_base64:
        method = "base64"
    else:
        method = "mixed"  # Has multiple types

    payload_data = {
        "title": title,
        "description": description,
        "user_hash": stamp,
        "files": files_data,
        "method": method
    }

    payload = f"POST:{dumps(payload_data)}"
    subject = f"Post: {title} by user_{stamp}"

    return _forge(subject, payload)

def catalog():
    """Get list of all posts"""
    probe = f"{Data.API_URL.real}/repos/{Data.OWNER.real}/{Data.VAULT.real}/contents/database.json"

    req = Request(probe, headers=_get_headers())

    try:
        with urlopen(req) as response:
            meta = loads(response.read().decode())
            raw = b64decode(meta['content'])
            registry = loads(raw.decode('utf-8'))
            return registry.get('posts', [])
    except HTTPError as e:
        if e.code == 404:
            return []
        raise

def acquire(user_hash, file_id, destination):
    """Download a specific file from a post"""
    posts = catalog()
    file_info = None

    for post in posts:
        if post['user_hash'] == user_hash:
            for f in post.get('files', []):
                if f['id'] == file_id:
                    file_info = f
                    break
        if file_info:
            break

    if not file_info:
        return None

    TAG = "files"
    release_url = f"https://api.github.com/repos/{Data.OWNER.real}/{Data.VAULT.real}/releases/tags/{TAG}"

    req = Request(release_url, headers=_get_headers())
    with urlopen(req) as response:
        release = loads(response.read().decode())

    filename = f"{user_hash}_{file_id}.{file_info['extension']}"
    asset = None
    for a in release['assets']:
        if a['name'] == filename:
            asset = a
            break

    if not asset:
        return None

    req = Request(asset['url'], headers={
        **_get_headers(),
        'Accept': 'application/octet-stream'
    })

    with urlopen(req) as response:
        data = response.read()

    with open(destination, 'wb') as f:
        f.write(data)

    return destination

# the ba corner
# ballistica related stuff lies here

class BoardSubsystem(ba.AppSubsystem):
    def on_screen_size_change(s):
        Board._call('on_resize')
    def on_ui_scale_change(s):
        Board._call('on_rescale')

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(ba.Plugin):
    has_settings_ui = lambda s: True
    show_settings_ui = lambda s, source: Board(source)
    def __init__(s):
        Config.STARTUP and bui.apptimer(1,Board)
