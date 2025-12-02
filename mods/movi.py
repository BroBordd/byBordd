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
from weakref import WeakMethod

# global
__version__ = '1.0'

class Theme:
    MAIN = (0,0,0)
    TINT = (0.5,0.5,0.5)
    TEXT = (2,2,2)
    OPACITY = 0.4
    TEXTURE = 'white'

class Animate:
    REVERSE = 0
    def __init__(s, widget, func, attrs, duration, on_start=None, on_finish=None, on_cancel=None, delay=0, condition=None):
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
        s.on_finish = (
            on_finish == Animate.REVERSE
            and s.reverse or on_finish
        )
        s.on_cancel = on_cancel
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
        if callable(s.on_cancel):
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
    _shared = {'callbacks':[]}

    @staticmethod
    def _call(sig):
        for callback_ref in Editor._shared['callbacks']:
            callback = callback_ref()
            callback(sig)

    @staticmethod
    def _register(obj,attr,sig):
        old = getattr(obj,attr)
        setattr(obj,attr,lambda *a,**k:(
            Editor._call(sig),
            old(*a,**k)
        ))

    # register callers
    _register(ba.AppHealthSubsystem,'on_screen_size_change','on_resize')
    _register(ba.AppHealthSubsystem,'on_ui_scale_change','on_rescale')

    # listener
    def callback(s,cb):
        bui.apptimer(0.01,getattr(s,cb))

    def __init__(s):
        # register
        s.__class__._shared['callbacks'].append(WeakMethod(s.callback))
        # toast
        s.toast_zoom = None
        # menu
        s.menu_root = None
        s.menu_on = False
        s.menu_kids = []
        # event
        s.event_root = None
        s.event_on = False
        s.event_kids = []
        # window
        s.window_on = None
        # entries
        s.entry_xs = 50
        s.entry_ys = 50
        # memory
        s.animations = {}
        s.window_animations = {}

    def ui_safe(s):
        return s.root.exists() and not s.root.transitioning_out

    def universal_back(s):
        if s.window_on or s.event_on:
            s.event_button.activate()
        else: s.square.activate()

    def on_resize(s):
        pass

    def on_rescale(s):
        pass

    def toast(s,inp=None):
        b = s.toast_bg
        t,desc = inp or ('','')
        # update
        bui.buttonwidget(b,label=t)
        desc and bui.buttonwidget(
            b,on_activate_call=bui.CallPartial(
                s.toast,
                (desc,Strings.NOTHING_ELSE)
            )
        )
        # default
        key = id(b)
        text_width = t and bui.get_string_width(
            t,suppress_warning=True
        ) or 0
        duration = 0.45
        end_size = dx,dy = (text_width+(t and 20 or 0),30)
        start_size = (0,dy)
        start_opacity = 0
        start_textcolor = Extra.INVISIBLE
        x,y = ox,oy = s.toast_position
        end_pos = epx,epy = (ox-dx/2,oy)
        rush = False
        # override
        if (anim:=s.animations.pop(key,None)):
            start_size = stx,sty = anim.attrs_current['size']
            if (
                (int(stx) == int(dx)) and
                (int(sty) == int(dy))
            ): rush = True
            x,y = anim.attrs_current['position']
            start_opacity = anim.attrs_current['opacity']
            start_textcolor = anim.attrs_current['textcolor']
            anim.cancel()
        # zoom
        zoom = lambda:(
            s.toast_zoom and s.toast_zoom.cancel(),
            setattr(s,'toast_zoom',Animate(
                widget=b,
                func=bui.buttonwidget,
                attrs={
                    'size':(
                        end_size,
                        (dx*1.1,dy*1.1)
                    ),
                    'position':(
                        end_pos,
                        (epx-dx*0.1/2,epy-dy*0.1/2)
                    )
                },
                duration=0.1,
                on_finish=Animate.REVERSE
            ))
        )
        # animate
        s.animations[key] = Animate(
            widget=b,
            func=bui.buttonwidget,
            attrs={
                'size':(start_size,end_size),
                'opacity':(
                    start_opacity,
                    t and Theme.OPACITY or 0
                ),
                'position':(
                    (x,y),
                    end_pos
                ),
                'textcolor':(
                    start_textcolor,
                    (*Theme.TEXT,Theme.OPACITY)
                )
            },
            duration=0.0001 if rush else duration,
            on_finish=zoom
        )
        s.toast_timer = bui.AppTimer(
            max(len(t)*0.05,3),
            s.toast
        )

    def make(s,master):
        # root
        s.root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            background=False
        )
        # toast
        s.toast_bg = bui.buttonwidget(
            parent=s.root,
            label='',
            enable_sound=False,
            selectable=False,
            size=(0,0),
            texture=bui.gettexture(Theme.TEXTURE),
            color=Theme.MAIN
        )
        # trap
        bui.containerwidget(
            s.root,
            cancel_button=(
                bui.buttonwidget(
                    parent=s.root,
                    size=(0,0),
                    label='',
                    selectable=False,
                    enable_sound=False,
                    on_activate_call=s.universal_back,
                    texture=bui.gettexture(Extra.EMPTY)
                )
            )
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
        s.event_root = bui.imagewidget(
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
        s.toast(Strings.WELCOME(master.sessionplayer.getname()))

    def wrap(s):
        rx,ry = s.real = bui.get_virtual_screen_size()
        sx,sy = s.stamp_size = (rx,150)
        # root
        bui.containerwidget(
            s.root,
            size=s.stamp_size,
            stack_offset=(-rx/2+sx/2,-ry/2+sy/2),
        )
        # toast
        s.toast_position = (sx/2,sy+10)
        bui.buttonwidget(
            s.toast_bg,
            position=s.toast_position
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
        bui.imagewidget(
            s.event_root,
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
        if s.window_on:
            s.window_back()
            return
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

        events = Strings.EVENTS
        if s.event_on:
            # collapse = reverse all
            anim = s.animations.get(key)
            if not anim: return

            s.event_on = False
            bui.buttonwidget(s.event_button, label=Strings.EVENT_BUTTON_OFF)

            s.animations[key] = anim.reverse(duration=0.4, on_finish=cleanup)

            # reverse child button animations
            for i in range(len(events)):
                k = id(getattr(s,f'event_kid_{i}'))
                if (anim := s.window_animations.pop(k,None)):
                    anim.cancel()
                if (anim := s.animations.pop(k,None)):
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
        s.event_kid_size = (mx,dy)
        px,py = (x+20,y+sy)

        # animate parent first (event root)
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

        # make and animate kids
        num = len(events)
        parent_width_progress = dx + (sx - dx) * child_start_progress
        start_width_ratio = (parent_width_progress - 40) / mx

        for i,n in enumerate(events):
            # make
            pos = (px,py-(dy+off)*(i+1))
            b = bui.buttonwidget(
                parent=s.root,
                position=pos,
                label=n,
                color=Theme.MAIN,
                textcolor=Extra.INVISIBLE,
                texture=bui.gettexture(Theme.TEXTURE),
                opacity=0,
                enable_sound=False
            )
            call = bui.CallPartial(s.window,b,i,pos)
            bui.buttonwidget(b,on_activate_call=call)
            setattr(s,f'event_kid_{i}',b)
            s.event_kids.append(b)
            # animate
            stagger = 0.02 * (num-i)
            s.animations[id(b)] = Animate(
                widget=b,
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

    def window(s,b,i,pos):
        if s.window_on: s.window_back()
        else: bui.getsound('deek').play()
        # disable
        call = bui.CallPartial(s.window,b,i,pos)
        s.window_on = (b,call)
        bui.buttonwidget(b,on_activate_call=lambda:False)
        # math
        r = s.real
        sx,sy= 450,300
        dx,dy = s.event_kid_size
        y_off = 70
        pos2 = (r[0]/2-sx/2, r[1]/2-sy/2+y_off)
        # animate
        s.window_animations[id(b)] = Animate(
            widget=b,
            func=bui.buttonwidget,
            duration=0.5,
            attrs={
                'position':(pos,pos2),
                'size':((dx,dy),(sx,sy)),
                'textcolor':(
                    (*Theme.TEXT, Theme.OPACITY),
                    (*Theme.TEXT, 0)
                )
            }
        )
        # make universal UI
        x,y = pos2
        def bye():
            s.window_clean()
            s.window_back()
        s.window_kids = []
        marg = 5
        fix = 8
        dx,dy = 35,35

        pos = (x+marg-fix,y+sy-dy-marg)
        b = bui.buttonwidget(
            parent=s.root,
            position=pos,
            size=(dx,dy),
            enable_sound=False,
            label=bui.charstr(bui.SpecialChar.BACK),
            on_activate_call=bye,
            texture=bui.gettexture(Theme.TEXTURE),
            color=Theme.MAIN,
            textcolor=Extra.INVISIBLE,
            opacity=0
        )
        s.window_kids.append((b,pos,50,bui.buttonwidget))

        descs = Strings.EVENT_DESCS
        pos = (x+sx/2,y+sy-marg-32.5)
        w = bui.textwidget(
            parent=s.root,
            text=descs[i],
            color=Extra.INVISIBLE,
            position=pos,
            h_align='center',
            v_align='center',
            maxwidth=sx-marg*3-dx
        )
        s.window_kids.append((w,pos,50,bui.textwidget))
        # make conditional UI
        if i == 0:
            # universal
            text_push = 15
            # type text
            pos = (x+marg-fix,y+sy-88)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                text=Strings.NODE_TYPE_TEXT,
                color=Extra.INVISIBLE
            )
            s.window_kids.append((w,pos,text_push,bui.textwidget))
            # type input
            pos = (x+marg+80-fix,y+sy-95)
            size = (150,40)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                editable=True,
                allow_clear_button=False,
                size=(0,0),
                description=Strings.NODE_TYPE_DESC,
                color=Extra.INVISIBLE,
                v_align='center',
                glow_type='uniform'
            )
            s.window_kids.append((w,pos,text_push,bui.textwidget,
                ('size',((0,size[1]),size))
            ))
            # name text
            pos = (x+marg-fix,y+sy-133)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                text=Strings.NODE_NAME_TEXT,
                color=Extra.INVISIBLE
            )
            s.window_kids.append((w,pos,text_push,bui.textwidget))
            # name input
            pos = (x+marg+80-fix,y+sy-140)
            size = (150,40)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                editable=True,
                allow_clear_button=False,
                size=(0,0),
                description=Strings.NODE_NAME_DESC,
                color=Extra.INVISIBLE,
                v_align='center',
                glow_type='uniform'
            )
            s.window_kids.append((w,pos,text_push,bui.textwidget,
                ('size',((0,size[1]),size))
            ))
            # separator
            pos = (x+marg-fix,y+sy-150)
            size = (229,2)
            w = bui.imagewidget(
                parent=s.root,
                position=pos,
                texture=bui.gettexture(Theme.TEXTURE),
                size=(0,0),
                opacity=0
            )
            s.window_kids.append((w,pos,text_push,bui.imagewidget,
                ('size',((0,size[1]),size))
            ))
            # attr text
            pos = (x+marg-fix,y+sy-193)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                text=Strings.NODE_ATTR_TEXT,
                color=Extra.INVISIBLE
            )
            s.window_kids.append((w,pos,text_push,bui.textwidget))
            # attr input
            pos = (x+marg+80-fix,y+sy-200)
            size = (150,40)
            attr = bui.textwidget(
                parent=s.root,
                position=pos,
                editable=True,
                allow_clear_button=False,
                size=(0,0),
                description=Strings.NODE_ATTR_DESC,
                color=Extra.INVISIBLE,
                v_align='center',
                glow_type='uniform'
            )
            s.window_kids.append((attr,pos,text_push,bui.textwidget,
                ('size',((0,size[1]),size))
            ))
            # eval text
            pos = (x+marg-fix,y+sy-238)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                text=Strings.NODE_EVAL_TEXT,
                color=Extra.INVISIBLE
            )
            s.window_kids.append((w,pos,text_push,bui.textwidget))
            # eval input
            pos = (x+marg+80-fix,y+sy-245)
            size = (150,40)
            val = bui.textwidget(
                parent=s.root,
                position=pos,
                editable=True,
                allow_clear_button=False,
                size=(0,0),
                description=Strings.NODE_EVAL_DESC,
                color=Extra.INVISIBLE,
                v_align='center',
                glow_type='uniform'
            )
            s.window_kids.append((val,pos,text_push,bui.textwidget,
                ('size',((0,size[1]),size))
            ))
            # attr stuff
            so_far = {}
            bx,by = (215,40)
            # attr scroll
            size = dx,dy = (sx/2-marg*3,sy-marg*4-51-by)
            pos = px,py = (x+sx-dx+5,y+marg*2+by+5)
            w = bui.scrollwidget(
                parent=s.root,
                position=pos,
                color=Theme.TINT,
                size=(dx/2,0),
                border_opacity=0
            )
            s.window_kids.append((w,pos,20,bui.scrollwidget,
                ('size',((dx/2,size[1]),size)),
                ('border_opacity',(0,Theme.OPACITY))
            ))
            # attr root
            attr_root = bui.containerwidget(
                parent=w,
                background=False
            )
            # set func
            def do_set():
                bui.getsound('deek').play()
                a = bui.textwidget(query=attr)
                v = bui.textwidget(query=val)
                if not a:
                    s.toast(Strings.ERROR_EMPTY(
                        Strings.NODE_ATTR_TEXT
                    ))
                    return
                if not v:
                    s.toast(Strings.ERROR_EMPTY(
                        Strings.NODE_EVAL_TEXT
                    ))
                    return
                try: v = eval(v)
                except Exception as e:
                    s.toast(Strings.ERROR_EVAL(e))
                w = bui.textwidget(
                    parent=attr_root,
                    size=(dx,30),
                    maxwidth=dx,
                    selectable=True,
                    glow_type='uniform',
                    click_activate=True,
                    on_activate_call=lambda:0,
                    text=a,
                    color=Extra.INVISIBLE
                )
                px,py = (0,len(so_far)*30)
                Animate(
                    widget=w,
                    func=bui.textwidget,
                    attrs={
                        'color':(
                            Extra.INVISIBLE,
                            (*Theme.TEXT,Theme.OPACITY)
                        ),
                        'position':(
                            (px+50,py),
                            (px,py)
                        )
                    },
                    duration=0.5
                )
                bui.containerwidget(
                    attr_root,
                    size=(dx,max(py,dy-15))
                )
            # set button
            pos = (x+marg+7-fix,y+marg)
            size = bx,by
            w = bui.buttonwidget(
                parent=s.root,
                size=(0,0),
                position=pos,
                texture=bui.gettexture(Theme.TEXTURE),
                color=Theme.MAIN,
                enable_sound=False,
                label=Strings.NODE_SET_BUTTON,
                textcolor=Extra.INVISIBLE,
                on_activate_call=do_set
            )
            s.window_kids.append((w,pos,50,bui.buttonwidget,
                ('size',((0,size[1]),size))
            ))
            # done func
            def do_done():
                bui.getsound('deek').play()
            # done button
            pos = (px+8,y+marg)
            size = bx,by = (dx-15,40)
            w = bui.buttonwidget(
                parent=s.root,
                size=(0,0),
                position=pos,
                texture=bui.gettexture(Theme.TEXTURE),
                color=Theme.MAIN,
                enable_sound=False,
                label=Strings.NODE_DONE_BUTTON,
                textcolor=Extra.INVISIBLE,
                on_activate_call=do_done
            )
            s.window_kids.append((w,pos,50,bui.buttonwidget,
                ('size',((0,size[1]),size))
            ))
        # animate all
        for _,g in enumerate(s.window_kids):
            w,pos,off,func,*extra = g
            extra = dict(extra)
            # default
            attrs = {
                'position':(
                    (pos[0]-off,pos[1]),
                    pos
                ),
                **extra
            }
            # widget based
            ty = w.get_widget_type()
            if ty == 'button':
                attrs.update({
                    'opacity':(0,Theme.OPACITY),
                    'textcolor':(
                        Extra.INVISIBLE,
                        (*Theme.TEXT,Theme.OPACITY)
                    )
                })
            elif ty == 'text':
                attrs.update({
                    'color':(
                        Extra.INVISIBLE,
                        (*Theme.TEXT,Theme.OPACITY)
                    )
                })
            elif ty == 'image':
                attrs.update({
                    'opacity':(0,Theme.OPACITY)
                })
            # finally
            s.window_animations[id(w)] = Animate(
                widget=w,
                func=func,
                attrs=attrs,
                duration=0.18,
                delay=0.4+_*0.04
            )

    def window_clean(s):
        for w,*_ in s.window_kids:
            s.window_animations[id(w)].reverse(
                duration=0.1,
                on_finish=w.delete,
                on_cancel=w.delete
            )
        s.window_kids.clear()

    def window_back(s):
        b,call = s.window_on
        bui.getsound('deek').play()
        s.window_clean()
        # restore button
        bui.buttonwidget(b,on_activate_call=call)
        anim = s.window_animations[id(b)].reverse(
            duration=0.5
        )
        # finally
        s.window_on = None
        s.window_animations = {id(b): anim}

class Strings:
    # map
    NAME = 'Movi'
    DESCRIPTION = 'Movie Maker'
    INSTANCE_DESCRIPTION = 'Three Two One Action!'
    INSTANCE_DESCRIPTION_SHORT = f'Version {__version__}'
    # UI
    EVENT_BUTTON_OFF = 'Event'
    EVENT_BUTTON_ON = 'Back'
    EVENTS = ['Node','Camera','Sound','FX','Map','Custom']
    EVENT_DESCS = [
        'Add a scene node',
        'Move the camera around',
        'Play a sound',
        'Emit an effect',
        'Control the map',
        'Custom action'
    ]
    # node event
    NODE_TYPE_TEXT = 'Type'
    NODE_TYPE_DESC = 'The node\'s type kwarg\nbascenev1.newnode(type=\'THIS\')\nEnter'
    NODE_NAME_TEXT = 'Name'
    NODE_NAME_DESC = 'The node\'s name kwarg\nbascenev1.newnode(name=\'THIS\')\nEnter'
    NODE_ATTR_TEXT = 'Attr'
    NODE_ATTR_DESC = 'The node\'s attribute name in attr dict\nbascenev1.newnode(attrs={\'THIS\':value})\nEnter'
    NODE_EVAL_TEXT = 'Eval'
    NODE_EVAL_DESC = 'The node\'s attr value in attr dict (evaluated)\nbascenev1.newnode(attrs={\'attr\':THIS})\nEnter'
    NODE_SET_BUTTON = 'Eval & Set'
    NODE_DONE_BUTTON = 'Done'
    # errors
    ERROR_EMPTY = lambda e: (
        f'Empty {e}!',
        'Stop leaving empty text boxes around'
    )
    ERROR_EVAL = lambda e: (
        str(e) and f'Eval: {e}' or 'Error evaluating!',
        'defined' in str(e) and
        'Are you using quotes for str?' or
        'You\'re on your own pal'
    )
    # extra
    WELCOME = lambda n: (
        f'Welcome, {n}! Press for more',
        'Movi is still experimental. Feedback is appreciated!'
    )
    NOTHING_ELSE = 'I have nothing else to say'

class Extra:
    INVISIBLE = (0,0,0,0)
    EMPTY = 'empty'

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
        ba.pushcall(ba.CallPartial(
            s.editor.make,
            master=s.master
        ),raw=True)

    def kill_ui(s):
        ba.pushcall(s.editor.kill,raw=True)
