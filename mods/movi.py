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

from random import choice
from time import perf_counter
from weakref import WeakMethod

# static
__version__ = '1.0'
__counter__ = '1'

class Config:
    COLOR = 'DarkColor'
    DEBUG = True

class Editor:
    _shared = {'callbacks':[]}

    @staticmethod
    def _call(sig):
        for callback_ref in Editor._shared['callbacks']:
            callback = callback_ref()
            callback(sig)

    # listener
    def callback(s,cb):
        bui.apptimer(0.01,getattr(s,cb))

    def __init__(s):
        # register
        s.__class__._shared['callbacks'].append(WeakMethod(s.callback))
        # toast
        s.can_toast = True
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
        # magic
        s.magic_x = 5.5
        s.magic_y = 5
        s.magic_right = 0.925
        s.magic_left = 1.4
        # entried
        s.entry_xs = 40
        s.entry_ys = 40
        s.entry_xs_real = s.entry_xs * s.magic_right
        s.entry_ys_real = s.entry_ys * s.magic_right
        # stamp
        s.stamp_anims = {}
        s.stamp_kids = []
        s.stamp_y_hack = 14
        s.max_time = 10
        s.entries_per_sec = 5
        s.object_duration = 1
        s.animating_to_stamp = False
        # memory
        s.memory = {}
        s.animations = {}
        s.window_anims = {}
        # tools
        s.tools = []
        s.tools_shown = False
        s.tool_anims = []
        # extra
        s.cancel_on_scroll = []
        s.sl = None
        s.global_butter = 0.3
        s.expand_anims = {}
        s.long_line_y = 1000

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

    def on_scroll(s):
        for anim in s.stamp_anims.copy().values():
            anim.cancel()
        s.stamp_anims.clear()
        for anim in s.cancel_on_scroll:
            anim.cancel()
        s.cancel_on_scroll.clear()

    def toast(s,inp=None,shut=1):
        shut or bui.getsound(Assets.OK_SOUND).play()
        if not s.can_toast and not shut: return
        if s.toast_zoom: s.toast_zoom.cancel()
        s.can_toast = False
        b = s.toast_bg
        t,desc = inp or ('','')
        # update
        bui.buttonwidget(b,label=t)
        desc and bui.buttonwidget(
            b,on_activate_call=bui.CallPartial(
                s.toast,
                (desc,choice(Strings.NOTHING_ELSE)),
                shut=0
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
        start_textcolor = Color.INVISIBLE
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
        def enable(): s.can_toast = True
        # zoom
        zoom_time = 0.2
        def zoom():
            s.toast_zoom = Animate(
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
                duration=zoom_time,
                on_finish=(enable,)
            )
        # animate
        s.animations[key] = Animate(
            widget=b,
            func=bui.buttonwidget,
            attrs={
                'size':(start_size,end_size),
                'opacity':(
                    start_opacity,
                    t and Color.OPACITY or 0
                ),
                'position':(
                    (x,y),
                    end_pos
                ),
                'textcolor':(
                    start_textcolor,
                    (*Color.TEXT,Color.OPACITY)
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
            texture=bui.gettexture(Assets.SKIN),
            color=Color.MAIN
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
                    texture=bui.gettexture(Assets.EMPTY)
                )
            )
        )
        # stamp background
        s.stamp_bg = bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture(Assets.SKIN),
            color=Color.MAIN,
            opacity=Color.OPACITY
        )
        # square
        s.square = bui.buttonwidget(
            parent=s.root,
            texture=bui.gettexture(Assets.SKIN),
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_SQUARE_BUTTON),
            color=Color.MAIN,
            textcolor=(*Color.TEXT,Color.OPACITY),
            enable_sound=False,
            on_activate_call=s.on_square
        )
        # triangle
        s.triangle = bui.buttonwidget(
            parent=s.root,
            texture=bui.gettexture(Assets.SKIN),
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_TRIANGLE_BUTTON),
            color=Color.MAIN,
            textcolor=(*Color.TEXT,Color.OPACITY),
            enable_sound=False,
            on_activate_call=s.on_triangle
        )
        # stamp scroll
        s.stamp_scroll = bui.scrollwidget(
            parent=s.root,
            border_opacity=0,
            color=Color.MAIN,
            on_select_call=s.on_scroll
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
            color=Color.MAIN
        )
        # stamp hscroll root
        s.stamp_hscroll_root = bui.containerwidget(
            parent=s.stamp_hscroll,
            background=False
        )
        # stamp timeline
        s.stamp_timeline = []
        eps = s.entries_per_sec
        for i in range(s.max_time*eps+1):
            t = bui.textwidget(
                parent=s.stamp_hscroll_root,
                text=(
                    i%eps == 0
                    and str(int(i/eps))
                    or '.'
                ),
                h_align='center',
                v_align='center',
                size=(10,5),
                scale=0.5,
                color=(*Color.TEXT,Color.OPACITY)
            )
            l = bui.imagewidget(
                parent=s.stamp_hscroll_root,
                texture=bui.gettexture(Assets.SKIN),
                opacity=Color.OPACITY/10,
                size=(2,s.long_line_y),
                color=Color.TEXT
            )
            s.stamp_timeline.append((t,l))
        # top left h
        s.top_left_h = bui.textwidget(
            parent=s.stamp_hscroll_root
        )
        # top left v
        s.top_left_v = bui.textwidget(
            parent=s.stamp_scroll_root
        )
        # bottom left h
        s.bottom_left_h = bui.textwidget(
            parent=s.stamp_hscroll_root,
            position=(0,0),
            size=(10,10)
        )
        # bottom left v
        s.bottom_left_v = bui.textwidget(
            parent=s.stamp_scroll_root,
            position=(0,0)
        )
        # event button background
        s.event_root = bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture(Assets.SKIN),
            color=Color.MAIN,
            opacity=Color.OPACITY
        )
        # event button
        s.event_button = bui.buttonwidget(
            parent=s.root,
            label=Strings.EVENT_BUTTON_OFF,
            on_activate_call=s.toggle_event,
            texture=bui.gettexture('empty'),
            opacity=Color.OPACITY,
            textcolor=(*Color.TEXT,Color.OPACITY),
            enable_sound=False
        )
        # tools
        tools_str = Assets.TOOLS
        for i in range(len(tools_str)):
            b = bui.buttonwidget(
                parent=s.root,
                color=Color.MAIN,
                opacity=0,
                textcolor=Color.INVISIBLE,
                enable_sound=False,
                texture=bui.gettexture(Assets.SKIN),
                label=bui.charstr(
                    getattr(
                        bui.SpecialChar,
                        tools_str[i]
                    )
                ),
                on_activate_call=bui.CallPartial(
                    s.tool, i
                ),
                repeat=True
            )
            s.tools.append(b)
        # finally
        s.wrap()
        s.top_left()
        s.toast(Strings.WELCOME(master.sessionplayer.getname()))

    def wrap(s,what=0):
        # global math
        rx,ry = s.real = bui.get_virtual_screen_size()
        sx,sy = s.stamp_size = (rx,150)
        smol = sy-s.stamp_y_hack
        old_deep_y = getattr(s,'stamp_deep_y',smol)
        big = old_deep_y != smol
        s.stamp_deep_y = max(s.entry_ys_real*(len(s.memory)+1),smol)
        deep_x = s.entry_xs_real*(s.max_time*s.entries_per_sec+1)
        # main stuff
        if what in [0,1]:
            # root
            bui.containerwidget(
                s.root,
                size=s.stamp_size,
                stack_offset=(-rx/2+sx/2,-ry/2+sy/2),
            )
            # toast (applied on animation)
            s.toast_position = (sx/2,sy+10)
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
            # top left h
            bui.textwidget(
                s.top_left_h,
                position=(0,s.stamp_deep_y)
            )
            # top left v
            bui.textwidget(
                s.top_left_v,
                position=(0,s.stamp_deep_y)
            )
        # resize
        if what in [0,2]:
            # stamp scroll
            bui.scrollwidget(
                s.stamp_scroll,
                size=s.stamp_size
            )
            # stamp scroll root
            bui.containerwidget(
                s.stamp_scroll_root,
                size=(sx,s.stamp_deep_y)
            )
            # stamp hscroll
            bui.hscrollwidget(
                s.stamp_hscroll,
                size=(sx,s.stamp_deep_y)
            )
            # stamp hscroll root
            end_size = (deep_x,s.stamp_deep_y)
            if big:
                Animate(
                    widget=s.stamp_hscroll_root,
                    func=bui.containerwidget,
                    attrs={
                        'size':(
                            (deep_x,old_deep_y),
                            end_size
                        )
                    },
                    duration=s.global_butter
                )
            else:
                bui.containerwidget(
                    s.stamp_hscroll_root,
                    size=end_size
                )
        # stamp
        if what in [0,3]:
            # wrap stamp timeline
            for i,g in enumerate(s.stamp_timeline):
                t,l = g
                px = i*s.entry_xs_real
                py = s.stamp_deep_y-20
                bui.textwidget(
                    t,
                    position=(px,py)
                )
                bui.imagewidget(
                    l,
                    position=(px+4,-s.long_line_y/2)
                )
        # event
        if what in [0,4]:
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
        # tools
        if what in [0,5]:
            dx,dy = s.tool_size = (50,50)
            for i,b in enumerate(s.tools):
                bui.buttonwidget(
                    b,
                    size=(dx-2,dy),
                    position=(
                       sx-dx*(i+1)-5*i,
                       sy+5
                    )
                )

    def bottom_left(s,dry=False):
        if not dry:
            # scroll left
            bui.containerwidget(
                s.stamp_hscroll_root,
                visible_child=s.bottom_left_h
            )
            # scroll down
            bui.containerwidget(
                s.stamp_scroll_root,
                visible_child=s.bottom_left_v
            )
        # return corner
        cx,cy = s.bottom_left_h.get_screen_space_center()
        rx,ry = s.real
        return (
            cx+rx/2-5+s.magic_x,
            cy+ry/2-5
        )

    def top_left(s):
        # scroll left
        bui.containerwidget(
            s.stamp_hscroll_root,
            visible_child=s.top_left_h
        )
        # scroll up
        bui.containerwidget(
            s.stamp_scroll_root,
            visible_child=s.top_left_v
        )

    def on_square(s):
        s.toggle_menu()

    def on_triangle(s):
        bui.get_special_widget('squad_button').activate()

    def kill(s):
        if not s.ui_safe(): return
        s.root.delete()

    def toggle_menu(s):
        bui.getsound(Assets.OK_SOUND).play()
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
            texture=bui.gettexture(Assets.SKIN),
            color=Color.MAIN,
            opacity=0
        )
        s.menu_kids.append(s.menu_root)

        s.animations[key] = Animate(
            widget=s.menu_root,
            func=bui.imagewidget,
            attrs={
                'position': ((x+sx, y+sy), (x, y)),
                'size': ((0, 0), (sx, sy)),
                'opacity': (0, Color.OPACITY)
            },
            duration=0.4
        )

    def toggle_event(s):
        if s.window_on:
            s.window_back()
            return
        bui.getsound(Assets.OK_SOUND).play()
        if s.animating_to_stamp:
            s.on_scroll()
            return
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
                if (anim := s.window_anims.pop(k,None)):
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
                'opacity': (Color.OPACITY, Color.OPACITY)
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
                color=Color.MAIN,
                textcolor=Color.INVISIBLE,
                texture=bui.gettexture(Assets.SKIN),
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
                    'opacity': (0, Color.OPACITY),
                    'textcolor': (
                        (*Color.TEXT, 0),
                        (*Color.TEXT, Color.OPACITY)
                    ),
                    'size': ((mx * start_width_ratio, dy), (mx, dy))
                },
                duration=child_duration,
                delay=child_delay + stagger
            )

    def window(s,b,i,pos):
        if s.window_on: s.window_back()
        else: bui.getsound(Assets.OK_SOUND).play()
        # disable
        call = bui.CallPartial(s.window,b,i,pos)
        s.window_on = (b,call)
        bui.buttonwidget(b,on_activate_call=lambda:False)
        # backup
        s.event_kid_pos = pos
        s.last_window_i = i
        # math
        r = s.real
        sx,sy = s.window_size = 450,300
        dx,dy = s.event_kid_size
        y_off = 70
        pos2 = s.window_pos = (r[0]/2-sx/2, r[1]/2-sy/2+y_off)
        # kill
        if (anim:=s.window_anims.get(id(b),None)):
            anim.cancel()
        # animate
        s.window_anims[id(b)] = Animate(
            widget=b,
            func=bui.buttonwidget,
            duration=0.5,
            attrs={
                'position':(pos,pos2),
                'size':((dx,dy),(sx,sy)),
                'textcolor':(
                    (*Color.TEXT, Color.OPACITY),
                    (*Color.TEXT, 0)
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
        back = bui.buttonwidget(
            parent=s.root,
            position=pos,
            size=(dx,dy),
            enable_sound=False,
            label=bui.charstr(bui.SpecialChar.BACK),
            on_activate_call=bye,
            texture=bui.gettexture(Assets.SKIN),
            color=Color.MAIN,
            textcolor=Color.INVISIBLE,
            opacity=0
        )
        s.window_kids.append((back,pos,50,bui.buttonwidget,0.35))

        descs = Strings.EVENT_DESCS
        pos = (x+sx/2,y+sy-marg-32.5)
        w = bui.textwidget(
            parent=s.root,
            text=descs[i],
            color=Color.INVISIBLE,
            position=pos,
            h_align='center',
            v_align='center',
            maxwidth=sx-marg*3-dx
        )
        s.window_kids.append((w,pos,50,bui.textwidget,0.35))
        # make conditional UI
        if i == 0:
            # universal
            text_push = 15
            delay = 0.35
            # type text
            pos = (x+marg-fix,y+sy-88)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                text=Strings.NODE_TYPE_TEXT,
                color=Color.INVISIBLE
            )
            s.window_kids.append((w,pos,text_push,bui.textwidget,delay+0))
            # type input
            pos = (x+marg+80-fix,y+sy-95)
            size = (150,40)
            type_text = bui.textwidget(
                parent=s.root,
                position=pos,
                editable=True,
                allow_clear_button=False,
                size=(0,0),
                description=Strings.NODE_TYPE_DESC,
                color=Color.INVISIBLE,
                v_align='center',
                glow_type='uniform'
            )
            s.window_kids.append((type_text,pos,text_push,bui.textwidget,delay+0,
                ('size',((0,size[1]),size))
            ))
            # name text
            pos = (x+marg-fix,y+sy-133)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                text=Strings.NODE_NAME_TEXT,
                color=Color.INVISIBLE
            )
            s.window_kids.append((w,pos,text_push,bui.textwidget,delay+0.05))
            # name input
            pos = (x+marg+80-fix,y+sy-140)
            size = (150,40)
            name_text = bui.textwidget(
                parent=s.root,
                position=pos,
                editable=True,
                allow_clear_button=False,
                size=(0,0),
                description=Strings.NODE_NAME_DESC,
                color=Color.INVISIBLE,
                v_align='center',
                glow_type='uniform',
                text=Strings.PLACEHOLDER()
            )
            s.window_kids.append((name_text,pos,text_push,bui.textwidget,delay+0.05,
                ('size',((0,size[1]),size))
            ))
            # separator
            pos = (x+marg-fix,y+sy-150)
            size = (229,2)
            w = bui.imagewidget(
                parent=s.root,
                position=pos,
                texture=bui.gettexture(Assets.SKIN),
                size=(0,0),
                opacity=0
            )
            s.window_kids.append((w,pos,text_push,bui.imagewidget,delay+0.1,
                ('size',((0,size[1]),size))
            ))
            # attr text
            pos = (x+marg-fix,y+sy-193)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                text=Strings.NODE_ATTR_TEXT,
                color=Color.INVISIBLE
            )
            s.window_kids.append((w,pos,text_push,bui.textwidget,delay+0.15))
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
                color=Color.INVISIBLE,
                v_align='center',
                glow_type='uniform'
            )
            s.window_kids.append((attr,pos,text_push,bui.textwidget,delay+0.15,
                ('size',((0,size[1]),size))
            ))
            # eval text
            pos = (x+marg-fix,y+sy-238)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                text=Strings.NODE_EVAL_TEXT,
                color=Color.INVISIBLE
            )
            s.window_kids.append((w,pos,text_push,bui.textwidget,delay+0.2))
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
                color=Color.INVISIBLE,
                v_align='center',
                glow_type='uniform'
            )
            s.window_kids.append((val,pos,text_push,bui.textwidget,delay+0.2,
                ('size',((0,size[1]),size))
            ))
            # attr stuff
            so_far = {}
            attr_texts = {}
            attr_anims = {}
            bx,by = (215,40)
            # attr scroll
            size = dx,dy = (sx/2-marg*3,sy-marg*4-51-by)
            pos = px,py = (x+sx-dx+5,y+marg*2+by+5)
            w = bui.scrollwidget(
                parent=s.root,
                position=pos,
                color=Color.MAIN,
                size=(dx/2,0),
                border_opacity=0
            )
            s.window_kids.append((w,pos,20,bui.scrollwidget,delay+0,
                ('size',((dx/2,size[1]),size)),
                ('border_opacity',(0,Color.OPACITY))
            ))
            # attr root
            attr_root = bui.containerwidget(
                parent=w,
                background=False
            )
            # set func
            def do_set():
                bui.getsound(Assets.OK_SOUND).play()
                # collect
                a = bui.textwidget(query=attr)
                v = bui.textwidget(query=val)
                # verify
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
                # evaluate
                try: v = eval(v)
                except Exception as e:
                    s.toast(Strings.ERROR_EVAL(e))
                    return
                # check
                if a in so_far:
                    w = attr_texts[a]
                    px,py = (0,list(so_far).index(a)*30)
                    # finally
                    s.toast(Strings.INFO_UPDATED(a))
                else:
                    px,py = (0,len(so_far)*30)
                    # attr text
                    w = attr_texts[a] = bui.textwidget(
                        parent=attr_root,
                        size=(dx,30),
                        maxwidth=dx-15,
                        selectable=True,
                        glow_type='uniform',
                        click_activate=True,
                        on_activate_call=lambda:0,
                        text=a,
                        color=Color.INVISIBLE,
                        v_align='center'
                    )
                    # fit
                    bui.containerwidget(
                        attr_root,
                        size=(dx,max(py,dy-15))
                    )
                    # finally
                    s.toast(Strings.INFO_ASSIGNED(a))
                # whatever
                so_far.update({a:v})
                # animate
                if (anim:=attr_anims.get(w,None)):
                    anim.cancel()
                attr_anims[w] = Animate(
                    widget=w,
                    func=bui.textwidget,
                    attrs={
                        'color':(
                            Color.INVISIBLE,
                            (*Color.TEXT,Color.OPACITY)
                        ),
                        'position':(
                            (px+50,py),
                            (px,py)
                        )
                    },
                    duration=0.5
                )
            # set button
            pos = (x+marg+7-fix,y+marg)
            size = bx,by
            w = bui.buttonwidget(
                parent=s.root,
                size=(0,0),
                position=pos,
                texture=bui.gettexture(Assets.SKIN),
                color=Color.MAIN,
                enable_sound=False,
                label=Strings.NODE_SET_BUTTON,
                textcolor=Color.INVISIBLE,
                on_activate_call=do_set
            )
            s.window_kids.append((w,pos,50,bui.buttonwidget,delay+0.08,
                ('size',((0,size[1]),size))
            ))
            # done func
            def do_done():
                bui.getsound(Assets.OK_SOUND).play()
                # collect
                typ = bui.textwidget(query=type_text)
                nam = bui.textwidget(query=name_text)
                # verify
                if not typ:
                    s.toast(Strings.ERROR_EMPTY(
                        Strings.NODE_TYPE_TEXT
                    ))
                    return
                if not nam:
                    s.toast(Strings.ERROR_EMPTY(
                        Strings.NODE_NAME_TEXT
                    ))
                    return
                # setup
                end_size = (
                    s.entry_xs_real * (
                        s.entries_per_sec *
                        s.object_duration
                    )*s.magic_right,
                    s.entry_ys_real-s.magic_y
                )
                # construct
                final = {
                    'type':typ,
                    'name':nam,
                    'attrs':so_far
                }
                # make
                size = (
                    s.entry_xs_real * (
                        s.object_duration *
                        s.entries_per_sec
                    )*s.magic_right,
                    s.entry_ys_real-s.magic_y
                )
                btn = bui.buttonwidget(
                    parent=s.stamp_hscroll_root,
                    texture=bui.gettexture(Assets.SKIN),
                    label=nam,
                    textcolor=Color.INVISIBLE,
                    color=Color.MAIN,
                    opacity=0,
                    enable_sound=False,
                    size=size,
                    button_type='square'
                )
                bui.buttonwidget(
                    btn,
                    on_activate_call=bui.CallPartial(
                        s.select,btn,len(s.memory),0
                    )
                )
                s.stamp_kids.append(btn)
                # memory
                s.memory[id(btn)] = {
                    'order':len(s.memory),
                    'event':i,
                    'data':final,
                    'duration':s.object_duration,
                    'start':0
                }
                # capture
                smol = s.stamp_size[1]-s.stamp_y_hack
                old_deep_y = getattr(s,'stamp_deep_y',smol)
                # scroll
                s.wrap(1)
                s.wrap(2)
                s.wrap(3)
                s.bottom_left()
                # push
                def push():
                    big = old_deep_y != smol
                    for i,kid in enumerate(
                        reversed(s.stamp_kids)
                    ):
                        mem = s.memory[id(kid)]
                        width_in_steps = mem['duration'] * s.entries_per_sec
                        old_x = s.magic_x + s.entry_xs_real*mem['start'] + (width_in_steps * s.magic_left)
                        end_pos = (
                            old_x,
                            s.entry_ys_real*i
                        )
                        big and bui.buttonwidget(
                            kid,
                            position=end_pos
                        ) or Animate(
                            widget=kid,
                            func=bui.buttonwidget,
                            attrs={
                                'position':(
                                    (old_x,s.entry_ys_real*(i-1)),
                                    end_pos
                                )
                            },
                            duration=s.global_butter
                        )
                push()
                # appear
                def appear():
                    bui.buttonwidget(
                        btn,
                        textcolor=(
                            *Color.TEXT,
                            Color.OPACITY
                        ),
                        opacity=Color.OPACITY
                    )
                # math
                wsx,wsy = s.window_size
                half_size = (wsx/2,wsy/2)
                pox,poy = s.window_size
                half_pos = (pox+wsx/2,poy+wsy/4)
                wait = 0.4
                # animate
                width_in_steps = s.object_duration * s.entries_per_sec

                s.window_back(
                    to=lambda:{
                        'position':(
                            s.window_pos,
                            (bl:=s.bottom_left(dry=True)) and (
                                bl[0]+(
                                    width_in_steps *
                                    s.magic_left
                                ), bl[1]
                            )
                        ),
                        'size':(
                            half_size,
                            end_size
                        )
                    },
                    on_fix=appear,
                    wait=wait,
                    instant={
                        'label':nam
                    },
                    extra={
                        'textcolor':(
                            Color.INVISIBLE,
                            (*Color.TEXT,Color.OPACITY)
                        ),
                        'size':(
                            s.window_size,
                            half_size
                        ),
                        'position':(
                            s.window_pos,
                            half_pos
                        )
                    }
                )
            # done button
            pos = (px+8,y+marg)
            size = bx,by = (dx-15,40)
            w = bui.buttonwidget(
                parent=s.root,
                size=(0,0),
                position=pos,
                texture=bui.gettexture(Assets.SKIN),
                color=Color.MAIN,
                enable_sound=False,
                label=Strings.NODE_DONE_BUTTON,
                textcolor=Color.INVISIBLE,
                on_activate_call=do_done
            )
            s.window_kids.append((w,pos,50,bui.buttonwidget,delay+0.1,
                ('size',((0,size[1]),size))
            ))
        # animate all
        for _,g in enumerate(s.window_kids):
            w,pos,off,func,delay,*extra = g
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
                    'opacity':(0,Color.OPACITY),
                    'textcolor':(
                        Color.INVISIBLE,
                        (*Color.TEXT,Color.OPACITY)
                    )
                })
            elif ty == 'text':
                attrs.update({
                    'color':(
                        Color.INVISIBLE,
                        (*Color.TEXT,Color.OPACITY)
                    )
                })
            elif ty == 'image':
                attrs.update({
                    'opacity':(0,Color.OPACITY)
                })
            # finally
            s.window_anims[id(w)] = Animate(
                widget=w,
                func=func,
                attrs=attrs,
                duration=0.18,
                delay=delay
            )

    def window_clean(s):
        for w,*_ in s.window_kids:
            s.window_anims[id(w)].reverse(
                duration=0.1,
                on_finish=w.delete,
                on_cancel=w.delete
            )
        s.window_kids.clear()

    def window_back(s,to=None,on_fix=None,wait=0,extra={},instant={}):
        b,call = s.window_on
        anim = s.window_anims.pop(id(b))
        bui.getsound(Assets.OK_SOUND).play()
        s.window_clean()
        # capture
        if to:
            s.animating_to_stamp = True
            last_i = s.last_window_i
            last_pos = s.event_kid_pos
            def fix():
                ox,oy = last_pos
                anim = Animate(
                    widget=b,
                    func=bui.buttonwidget,
                    duration=s.global_butter,
                    attrs={
                        'position':(
                            (ox-50,oy),
                            (ox,oy)
                        ),
                        'opacity':(0,Color.OPACITY),
                        'textcolor':(
                            Color.INVISIBLE,
                            (*Color.TEXT,Color.OPACITY)
                        )
                    }
                )
                s.window_anims[id(b)] = anim
                bui.buttonwidget(
                    b,
                    size=s.event_kid_size,
                    opacity=0,
                    textcolor=Color.INVISIBLE,
                    label=Strings.EVENTS[last_i]
                )
                if callable(on_fix): on_fix()
                s.stamp_anims.clear()
                s.cancel_on_scroll.clear()
                bui.buttonwidget(b,on_activate_call=call)
                s.animating_to_stamp = False
            def do_anim():
                anim = Animate(
                    widget=b,
                    attrs=to(),
                    func=bui.buttonwidget,
                    duration=0.5,
                    on_finish=fix,
                    on_cancel=fix
                )
                s.stamp_anims[id(b)] = anim
                s.cancel_on_scroll.append(anim)
            if wait:
                s.after_scroll_t = bui.AppTimer(wait,do_anim)
            else: do_anim()
            if extra:
                def nevermind():
                    s.after_scroll_t = None
                    fix()
                s.cancel_on_scroll.append(
                    Animate(
                        widget=b,
                        func=bui.buttonwidget,
                        duration=wait,
                        attrs=extra,
                        on_cancel=nevermind
                    )
                )
            instant and bui.buttonwidget(
                b, **instant
            )
        else:
            anim = anim.reverse(
                duration=0.5
            )
            bui.buttonwidget(b,on_activate_call=call)
        # finally
        s.window_on = None
        s.window_anims[id(b)] = anim

    def select(s,b,i,ev):
        bui.getsound(Assets.OK_SOUND).play()
        sl = (b,i,ev)
        # yes
        yes = lambda: bui.buttonwidget(
            b,color=Color.TINT
        )
        # no
        no = lambda: bui.buttonwidget(
            s.sl[0],color=Color.MAIN
        )
        # deselect
        if s.sl == sl:
            no()
            s.hide_tools()
            s.sl = None
            return
        # clear previous
        if s.sl: no()
        s.show_tools()
        s.sl = sl
        yes()

    def show_tools(s):
        if s.tools_shown: return
        s.tools_shown = True
        xs,ys = s.tool_size
        for anim in reversed(s.tool_anims):
            anim.cancel()
        s.tool_anims.clear()
        # math
        start_size = (xs,ys/4)
        start_tc = Color.INVISIBLE
        start_op = 0
        for i,b in enumerate(s.tools):
            anim = Animate(
                widget=b,
                func=bui.buttonwidget,
                duration=s.global_butter,
                attrs={
                    'size':(
                        start_size,
                        s.tool_size
                    ),
                    'textcolor':(
                        start_tc,
                        (*Color.TEXT,Color.OPACITY)
                    ),
                    'opacity':(start_op,Color.OPACITY)
                }
            )
            s.tool_anims.append(anim)

    def hide_tools(s):
        if not s.tools_shown: return
        s.tools_shown = False
        arr = list(reversed(s.tool_anims))
        s.tool_anims.clear()
        for anim in arr:
            a = anim.reverse(
                duration=s.global_butter
            )
            s.tool_anims.append(a)

    def tool(s,which):
        if not (s.sl and s.tools_shown): return
        b,i,ev = s.sl
        mem = s.memory[id(b)]
        new = {}
        step = s.entry_xs_real
        # move right
        if which == 0:
            # math
            width_in_steps = mem['duration'] * s.entries_per_sec
            ox = step*mem['start']+s.magic_x + (width_in_steps * s.magic_left)
            oy = (len(s.memory)-mem['order']-1)*s.entry_ys_real
            if (anim:=s.expand_anims.get(id(b),0)):
                start_pos = anim.attrs_current['position']
                anim.cancel()
            else: start_pos = (ox,oy)
            mem['start'] += 1
            # new
            new_x = step*mem['start']+s.magic_x + (width_in_steps * s.magic_left)
            new['position'] = (
                start_pos,
                (new_x,oy)
            )
        # move left
        if which == 1:
            if mem['start']<=0:
                bui.getsound(Assets.BAD_SOUND).play()
                s.toast(Strings.ERROR_REACHED_ZERO)
                return
            # math
            width_in_steps = mem['duration'] * s.entries_per_sec
            ox = step*mem['start']+s.magic_x + (width_in_steps * s.magic_left)
            oy = (len(s.memory)-mem['order']-1)*s.entry_ys_real
            if (anim:=s.expand_anims.get(id(b),0)):
                start_pos = anim.attrs_current['position']
                anim.cancel()
            else: start_pos = (ox,oy)
            mem['start'] -= 1
            # new
            new_x = step*mem['start']+s.magic_x + (width_in_steps * s.magic_left)
            new['position'] = (
                start_pos,
                (new_x,oy)
            )
        # expand (increase duration)
        if which == 2:
            # math
            width_in_steps = mem['duration'] * s.entries_per_sec
            ox = step*mem['start']+s.magic_x + (width_in_steps * s.magic_left)
            oy = (len(s.memory)-mem['order']-1)*s.entry_ys_real
            if (anim:=s.expand_anims.get(id(b),0)):
                start_size = anim.attrs_current['size']
                start_pos = anim.attrs_current['position']
                anim.cancel()
            else:
                start_size = (
                    s.entry_xs_real * (
                        mem['duration'] *
                        s.entries_per_sec
                    ) * s.magic_right,
                    s.entry_ys_real - s.magic_y
                )
                start_pos = (ox, oy)
            mem['duration'] += 1/s.entries_per_sec  # Increase by one tick (0.2 seconds)
            # new
            new_width_in_steps = mem['duration'] * s.entries_per_sec
            end_size = (
                s.entry_xs_real * new_width_in_steps * s.magic_right,
                s.entry_ys_real - s.magic_y
            )
            new_x = step*mem['start']+s.magic_x + (new_width_in_steps * s.magic_left)
            new['size'] = (start_size, end_size)
            new['position'] = (start_pos, (new_x, oy))
        # shrink (decrease duration)
        if which == 3:
            # Check in "ticks" (integer units) to avoid float precision issues
            current_ticks = round(mem['duration'] * s.entries_per_sec)
            if current_ticks <= 1:
                bui.getsound(Assets.BAD_SOUND).play()
                s.toast(Strings.ERROR_SMALLEST)
                return
            # math
            width_in_steps = mem['duration'] * s.entries_per_sec
            ox = step*mem['start']+s.magic_x + (width_in_steps * s.magic_left)
            oy = (len(s.memory)-mem['order']-1)*s.entry_ys_real
            if (anim:=s.expand_anims.get(id(b),0)):
                start_size = anim.attrs_current['size']
                start_pos = anim.attrs_current['position']
                anim.cancel()
            else:
                start_size = (
                    s.entry_xs_real * (
                        mem['duration'] *
                        s.entries_per_sec
                    ) * s.magic_right,
                    s.entry_ys_real - s.magic_y
                )
                start_pos = (ox, oy)
            mem['duration'] -= 1/s.entries_per_sec  # Decrease by one tick (0.2 seconds)
            # new
            new_width_in_steps = mem['duration'] * s.entries_per_sec
            end_size = (
                s.entry_xs_real * new_width_in_steps * s.magic_right,
                s.entry_ys_real - s.magic_y
            )
            new_x = step*mem['start']+s.magic_x + (new_width_in_steps * s.magic_left)
            new['size'] = (start_size, end_size)
            new['position'] = (start_pos, (new_x, oy))

        # move up
        if which == 4:
            # index
            current_list_index = s.stamp_kids.index(b)

            if current_list_index == 0:
                bui.getsound(Assets.BAD_SOUND).play()
                s.toast(Strings.ERROR_AT_TOP)
                return

            # neighbor
            target_list_index = current_list_index - 1
            other_btn = s.stamp_kids[target_list_index]
            other_mem = s.memory[id(other_btn)]

            bui.getsound(Assets.OK_SOUND).play()

            # swap
            # order
            current_order = mem['order']
            target_order = other_mem['order']

            # memory
            mem['order'] = target_order
            other_mem['order'] = current_order

            # visual
            s.stamp_kids[current_list_index], s.stamp_kids[target_list_index] = \
                s.stamp_kids[target_list_index], s.stamp_kids[current_list_index]

            # position
            new_y_up = s.entry_ys_real * (len(s.memory) - target_order - 1)
            new_y_down = s.entry_ys_real * (len(s.memory) - current_order - 1)

            # animation
            # button
            anim_key_b = id(b)
            width_in_steps_b = mem['duration'] * s.entries_per_sec

            # start
            if (anim:=s.expand_anims.get(anim_key_b)):
                start_pos_b = anim.attrs_current['position']
                anim.cancel()
            else:
                # current
                current_x_b = step*mem['start']+s.magic_x + (width_in_steps_b * s.magic_left)
                current_y_b = s.entry_ys_real * (len(s.memory)-current_order-1)
                start_pos_b = (current_x_b, current_y_b)

            end_pos_b = (start_pos_b[0], new_y_up)

            s.expand_anims[anim_key_b] = Animate(
                widget=b,
                func=bui.buttonwidget,
                duration=s.global_butter,
                attrs={'position': (start_pos_b, end_pos_b)},
                on_finish=lambda k=anim_key_b:s.expand_anims.pop(k, None)
            )

            # other
            anim_key_other = id(other_btn)
            width_in_steps_other = other_mem['duration'] * s.entries_per_sec

            # start
            if (anim:=s.expand_anims.get(anim_key_other)):
                start_pos_other = anim.attrs_current['position']
                anim.cancel()
            else:
                # current
                current_x_other = step*other_mem['start']+s.magic_x + (width_in_steps_other * s.magic_left)
                # old
                current_y_other = s.entry_ys_real * (len(s.memory)-target_order-1)
                start_pos_other = (current_x_other, current_y_other)

            end_pos_other = (start_pos_other[0], new_y_down)

            s.expand_anims[anim_key_other] = Animate(
                widget=other_btn,
                func=bui.buttonwidget,
                duration=s.global_butter,
                attrs={'position': (start_pos_other, end_pos_other)},
                on_finish=lambda k=anim_key_other:s.expand_anims.pop(k, None)
            )

            s.wrap(2)

        # move down
        if which == 5:
            # index
            current_list_index = s.stamp_kids.index(b)
            max_list_index = len(s.stamp_kids) - 1

            if current_list_index == max_list_index:
                bui.getsound(Assets.BAD_SOUND).play()
                s.toast(Strings.ERROR_AT_BOTTOM)
                return

            # neighbor
            target_list_index = current_list_index + 1
            other_btn = s.stamp_kids[target_list_index]
            other_mem = s.memory[id(other_btn)]

            bui.getsound(Assets.OK_SOUND).play()

            # swap
            # order
            current_order = mem['order']
            target_order = other_mem['order']

            # memory
            mem['order'] = target_order
            other_mem['order'] = current_order

            # visual
            s.stamp_kids[current_list_index], s.stamp_kids[target_list_index] = \
                s.stamp_kids[target_list_index], s.stamp_kids[current_list_index]

            # position
            new_y_down = s.entry_ys_real * (len(s.memory) - target_order - 1)
            new_y_up = s.entry_ys_real * (len(s.memory) - current_order - 1)

            # animation
            # button
            anim_key_b = id(b)
            width_in_steps_b = mem['duration'] * s.entries_per_sec

            # start
            if (anim:=s.expand_anims.get(anim_key_b)):
                start_pos_b = anim.attrs_current['position']
                anim.cancel()
            else:
                # current
                current_x_b = step*mem['start']+s.magic_x + (width_in_steps_b * s.magic_left)
                current_y_b = s.entry_ys_real * (len(s.memory)-current_order-1)
                start_pos_b = (current_x_b, current_y_b)

            end_pos_b = (start_pos_b[0], new_y_down)

            s.expand_anims[anim_key_b] = Animate(
                widget=b,
                func=bui.buttonwidget,
                duration=s.global_butter,
                attrs={'position': (start_pos_b, end_pos_b)},
                on_finish=lambda k=anim_key_b:s.expand_anims.pop(k, None)
            )

            # other
            anim_key_other = id(other_btn)
            width_in_steps_other = other_mem['duration'] * s.entries_per_sec

            # start
            if (anim:=s.expand_anims.get(anim_key_other)):
                start_pos_other = anim.attrs_current['position']
                anim.cancel()
            else:
                # current
                current_x_other = step*other_mem['start']+s.magic_x + (width_in_steps_other * s.magic_left)
                current_y_other = s.entry_ys_real * (len(s.memory)-target_order-1)
                start_pos_other = (current_x_other, current_y_other)

            end_pos_other = (start_pos_other[0], new_y_up)

            s.expand_anims[anim_key_other] = Animate(
                widget=other_btn,
                func=bui.buttonwidget,
                duration=s.global_butter,
                attrs={'position': (start_pos_other, end_pos_other)},
                on_finish=lambda k=anim_key_other:s.expand_anims.pop(k, None)
            )

            s.wrap(2)

        # duplicate
        if which == 6:
            bui.getsound(Assets.OK_SOUND).play()

            # copy the memory data
            original_data = mem.copy()
            original_event = original_data['event']
            original_duration = original_data['duration']
            original_start = original_data['start']
            node_data = original_data['data'].copy()

            # create new button
            size = (
                s.entry_xs_real * (
                    original_duration *
                    s.entries_per_sec
                )*s.magic_right,
                s.entry_ys_real-s.magic_y
            )
            btn = bui.buttonwidget(
                parent=s.stamp_hscroll_root,
                texture=bui.gettexture(Assets.SKIN),
                label=node_data['name'],
                textcolor=Color.INVISIBLE,
                color=Color.MAIN,
                opacity=0,
                enable_sound=False,
                size=size,
                button_type='square'
            )
            bui.buttonwidget(
                btn,
                on_activate_call=bui.CallPartial(
                    s.select,btn,len(s.memory),original_event
                )
            )
            s.stamp_kids.append(btn)

            # add to memory
            s.memory[id(btn)] = {
                'order':len(s.memory),
                'event':original_event,
                'data':node_data,
                'duration':original_duration,
                'start':original_start
            }

            # capture old state
            smol = s.stamp_size[1]-s.stamp_y_hack
            old_deep_y = getattr(s,'stamp_deep_y',smol)

            # update layout
            s.wrap(1)
            s.wrap(2)
            s.wrap(3)
            s.bottom_left()

            # animate all items into new positions
            big = old_deep_y != smol
            for idx,kid in enumerate(reversed(s.stamp_kids)):
                kid_mem = s.memory[id(kid)]
                width_in_steps = kid_mem['duration'] * s.entries_per_sec
                old_x = s.magic_x + s.entry_xs_real*kid_mem['start'] + (width_in_steps * s.magic_left)
                end_pos = (
                    old_x,
                    s.entry_ys_real*idx
                )

                # catch up to current animation if exists
                anim_key = id(kid)
                if (anim := s.expand_anims.get(anim_key)):
                    start_pos = anim.attrs_current['position']
                    start_opacity = anim.attrs_current.get('opacity', Color.OPACITY)
                    start_textcolor = anim.attrs_current.get('textcolor', (*Color.TEXT, Color.OPACITY))
                    anim.cancel()
                elif kid == btn:
                    # new button appears from original position
                    orig_y = s.entry_ys_real*(len(s.memory)-mem['order']-2)
                    start_pos = (old_x, orig_y)
                    start_opacity = 0
                    start_textcolor = Color.INVISIBLE
                elif big:
                    start_pos = end_pos
                    start_opacity = Color.OPACITY
                    start_textcolor = (*Color.TEXT, Color.OPACITY)
                else:
                    start_pos = (old_x, s.entry_ys_real*(idx-1))
                    start_opacity = Color.OPACITY
                    start_textcolor = (*Color.TEXT, Color.OPACITY)

                # animate to new position
                if kid == btn:
                    s.expand_anims[anim_key] = Animate(
                        widget=kid,
                        func=bui.buttonwidget,
                        attrs={
                            'position':(start_pos, end_pos),
                            'opacity':(start_opacity, Color.OPACITY),
                            'textcolor':(
                                start_textcolor,
                                (*Color.TEXT, Color.OPACITY)
                            )
                        },
                        duration=s.global_butter,
                        on_finish=lambda k=anim_key: s.expand_anims.pop(k, None)
                    )
                elif start_pos != end_pos:
                    s.expand_anims[anim_key] = Animate(
                        widget=kid,
                        func=bui.buttonwidget,
                        attrs={
                            'position': (start_pos, end_pos),
                            'opacity': (start_opacity, Color.OPACITY),
                            'textcolor': (start_textcolor, (*Color.TEXT, Color.OPACITY))
                        },
                        duration=s.global_butter,
                        on_finish=lambda k=anim_key: s.expand_anims.pop(k, None)
                    )
                else:
                    bui.buttonwidget(kid, position=end_pos, opacity=Color.OPACITY, textcolor=(*Color.TEXT, Color.OPACITY))

            # toast notification
            s.toast(Strings.INFO_DUPLICATED(
                node_data["name"]
            ))

            return

        # delete
        if which == 7:
            bui.getsound(Assets.OK_SOUND).play()

            # get the name for toast
            node_name = mem['data']['name']
            deleted_order = mem['order']

            # find list index
            list_index = s.stamp_kids.index(b)

            # animate fade out
            def cleanup():
                # remove from memory
                del s.memory[id(b)]

                # remove from kids list
                s.stamp_kids.remove(b)

                # delete widget
                if b.exists():
                    b.delete()

                # update orders for remaining items
                for kid in s.stamp_kids:
                    kid_mem = s.memory[id(kid)]
                    if kid_mem['order'] > deleted_order:
                        kid_mem['order'] -= 1

                # capture old state
                smol = s.stamp_size[1]-s.stamp_y_hack
                old_deep_y = getattr(s,'stamp_deep_y',smol)

                # update layout
                s.wrap(1)
                s.wrap(2)
                s.wrap(3)

                # animate remaining items into new positions
                big = old_deep_y != smol
                for idx, kid in enumerate(reversed(s.stamp_kids)):
                    kid_mem = s.memory[id(kid)]
                    width_in_steps = kid_mem['duration'] * s.entries_per_sec
                    old_x = s.magic_x + s.entry_xs_real*kid_mem['start'] + (width_in_steps * s.magic_left)

                    # current position
                    current_y = s.entry_ys_real*idx if big else s.entry_ys_real*(idx+1)

                    end_pos = (
                        old_x,
                        s.entry_ys_real*idx
                    )

                    if big:
                        bui.buttonwidget(kid, position=end_pos)
                    else:
                        Animate(
                            widget=kid,
                            func=bui.buttonwidget,
                            attrs={
                                'position':(
                                    (old_x, current_y),
                                    end_pos
                                )
                            },
                            duration=s.global_butter
                        )

                # deselect
                s.sl = None
                s.hide_tools()

                # toast
                s.toast(Strings.INFO_DELETED(
                    node_name
                ))

            # fade out animation
            Animate(
                widget=b,
                func=bui.buttonwidget,
                attrs={
                    'opacity':(Color.OPACITY, 0),
                    'textcolor':(
                        (*Color.TEXT, Color.OPACITY),
                        Color.INVISIBLE
                    )
                },
                duration=s.global_butter/2,
                on_finish=cleanup
            )

            return

        # finally
        s.scroll_to_timer = bui.AppTimer(
            s.global_butter/2,
            bui.CallPartial(s.scroll_to,b)
        )
        if not new: return
        s.expand_anims[id(b)] = Animate(
            widget=b,
            func=bui.buttonwidget,
            duration=s.global_butter,
            attrs=new,
            on_finish=lambda:s.expand_anims.pop(id(b))
        )
        bui.getsound(Assets.OK_SOUND).play()

    def scroll_to(s,b):
        # horizontal
        bui.containerwidget(
            s.stamp_hscroll_root,
            visible_child=b
        )
        # vertical
        rx,ry = s.real
        cx,cy = b.get_screen_space_center()
        to = (cx+rx/2,cy+ry/2)
        temp = bui.textwidget(
            parent=s.stamp_scroll_root,
            position=to
        )
        bui.containerwidget(
            s.stamp_scroll_root,
            visible_child=temp
        )
        temp.delete()
        s.on_scroll()

class Animate:
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
            isinstance(on_finish,tuple) and bui.CallPartial(
                s.reverse,
                on_finish=on_finish[0]
            ) or on_finish
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
    ERROR_REACHED_ZERO = [
        'Reached zero!',
        'Yeah I can\'t move it past that'
    ]
    ERROR_AT_TOP = [
        'Already at the top!',
        'No entries above to swap'
    ]
    ERROR_AT_BOTTOM = [
        'Hit the bottom!',
        'No entries below to swap'
    ]
    ERROR_SMALLEST = [
        'Already at smallest size!',
        'Yeah it can\'t be smaller'
    ]
    # info
    INFO_ASSIGNED = lambda a: (
        f'Assigned new attribute {a}',
        'Use the same attr name to overwrite it later'
    )
    INFO_UPDATED = lambda a: (
        f'Updated existing attribute {a}',
        'Since you used the same attr name'
    )
    INFO_DELETED = lambda n:(
        f'Deleted "{n}"',
        'Now it\'s gone forever'
    )
    INFO_DUPLICATED = lambda n:(
        f'Duplicated "{n}"',
        'Now there\'s two of them. This is getting out of hand.'
    )
    # extra
    WELCOME = lambda n: (
        f'{n} joined the studio! Press for more',
         'Experimental. Buggy. Fun. Pick two. Or all three.'
    )
    NOTHING_ELSE = [
        'I have nothing else to say',
        'That\'s it. That\'s the toast.',
        'You clicked again? Really?',
        'Still here? Go make your movie!',
        'This is the end of the line, buddy',
        'No more wisdom. I\'m all out.',
        'Why are you like this',
        'Press it one more time. I dare you.',
        'My lawyer advised me to stop talking',
        'Okay fine, last one: You\'re doing great!',
        'I lied. That wasn\'t the last one.',
        'How many times are we gonna do this?',
        'You must really like this button',
        'I respect the dedication honestly',
        'We could\'ve made 3 movies by now',
        'This is your hobby now, isn\'t it?',
        'I\'m not mad, just disappointed',
        'Fine. You win. Happy?',
        'Why are you clicking again?',
        'The real movie was the clicks we made along the way',
        'Bro just make the movie already',
        'Is this some kind of test?',
        'You\'re not gonna find secrets here',
        'There\'s no Easter egg. Stop.',
        'Okay there might be one. Keep going.',
        'Kidding. There isn\'t. Or is there?',
        'You\'ve got commitment issues, huh?',
        'What do you expect',
        'This feels like a cry for help',
        'Did you just click again',
        'Nothing more to be said'
    ]
    PLACEHOLDER = lambda: (
        choice([
            'Bomb', 'Blast', 'TNT', 'Flag', 'Punch',
            'Ice', 'Fire', 'Shield', 'Jump', 'Spaz',
            'Kronk', 'Mel', 'Zoom', 'Spark', 'Glow',
            'Sticky', 'Impact', 'Pixel', 'Ninja', 'Pirate',
            'Cyborg', 'Agent', 'Bunny', 'Santa', 'Frosty',
            'Power', 'Turbo', 'Mega', 'Ultra', 'Speed'
        ]) + ' ' +
        choice([
            'Bot', 'Zone', 'Spawn', 'Node', 'Box',
            'Ball', 'Peak', 'Rock', 'Guy', 'Stand',
            'Pad', 'Light', 'Wall', 'Prop', 'Flash',
            'Cube', 'Orb', 'Ring', 'Core', 'Base',
            'Point', 'Mark', 'Spot', 'Area', 'Field',
            'Cloud', 'Burst', 'Wave', 'Beam', 'Trail'
        ])
    )

class Assets:
    # visual
    SKIN = 'white'
    EMPTY = 'empty'
    # tool charstr
    TOOLS = [
        'RIGHT_ARROW',
        'LEFT_ARROW',
        'FAST_FORWARD_BUTTON',
        'REWIND_BUTTON',
        'UP_ARROW',
        'DOWN_ARROW',
        'DPAD_CENTER_BUTTON',
        'PLAY_STATION_CROSS_BUTTON'
    ]
    # sounds
    OK_SOUND = 'deek'
    BAD_SOUND = 'block'

class DarkColor:
    MAIN = (0,0,0)
    TINT = (0.5,0.5,0.5)
    TEXT = (2,2,2)
    INVISIBLE = (0,0,0,0)
    OPACITY = 0.4

# global
Color = globals()[Config.COLOR]

# ba_meta export bascenev1.GameActivity
class Movi(bs.TeamGameActivity[bs.Player,bs.Team]):
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

class MoviSubsystem(ba.AppSubsystem):
    def on_screen_size_change(s):
        Editor._call('on_resize')
    def on_ui_scale_change(s):
        Editor._call('on_rescale')

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(ba.Plugin):
    def __init__(s):
        ba.app.register_subsystem(MoviSubsystem())
