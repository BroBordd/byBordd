# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

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
from collections import defaultdict

# static
__version__ = '1.0'
__counter__ = '1'

class Config:
    COLOR = 'DARK'
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
        s.ui_on = False
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
        s.event_kids = {}
        s.event_top = None
        # edit
        s.edit_on = False
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
        s.stamp_kids = []
        s.stamp_y_hack = 14
        s.max_time = 10
        s.entries_per_sec = 5
        s.object_duration = 1
        # memory
        s.memory = {}
        s.anims = defaultdict(dict)
        # tools
        s.tools = []
        s.tools_shown = False
        # extra
        s.sl = None
        s.global_butter = 0.3
        s.long_line_y = 10**10
        s.can_delete = False
        s.pending = []
        s.blame = None

    def run_on_ui(s,f):
        if s.ui_on: f()
        else: s.pending.append(f)

    def ui_safe(s):
        return s.root.exists() and not s.root.transitioning_out

    def universal_back(s):
        if s.window_on or s.event_on:
            s.event_button.activate()
        else: s.square.activate()

    def on_resize(s):
        s.on_scroll()

    def on_rescale(s):
        s.on_scroll()

    def on_scroll(s):
        if s.event_on:
            # you're not going anywhere
            for kid in s.event_kids:
                an = s.anims[id(kid)]
                for _ in ['extra','to','shadow']:
                    (a:=an.get(_,None)) and a.cancel()

    def toast(s,inp=None,shut=1,extra=0):
        shut or Eval.SOUND(Const.OK_SOUND).play()
        # on toast
        if not s.can_toast and not shut: return
        if s.can_delete and extra<1: s.can_delete = False
        if s.toast_zoom: s.toast_zoom.cancel()
        s.can_toast = False
        b = s.toast_bg
        t,desc = inp or ('','')
        # update
        if not s.blame:
            s.blame = Eval.BLAME(
                Strings.BLAME,
                Const.BLAME
            )
        bui.buttonwidget(b,label=t)
        desc and bui.buttonwidget(
            b,on_activate_call=bui.CallPartial(
                s.toast,
                (desc,choice(s.blame)),
                shut=0,
                extra=extra-1
            )
        )
        # default
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
        if (anim:=s.anims.get(id(b),None)):
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
        s.anims[id(b)] = Animate(
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
        s.toast_timer = inp and bui.AppTimer(
            max(len(t)*0.06,3),
            s.toast
        )

    def make(s):
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
            texture=Eval.TEXTURE(Const.SKIN),
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
                    texture=Eval.TEXTURE(Const.EMPTY)
                )
            )
        )
        # stamp background
        s.stamp_bg = bui.imagewidget(
            parent=s.root,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.MAIN,
            opacity=Color.OPACITY
        )
        # square
        s.square = bui.buttonwidget(
            parent=s.root,
            texture=Eval.TEXTURE(Const.SKIN),
            label=Eval.CHAR(Const.SQUARE),
            color=Color.MAIN,
            textcolor=(*Color.TEXT,Color.OPACITY),
            enable_sound=False,
            on_activate_call=s.on_square
        )
        # triangle
        s.triangle = bui.buttonwidget(
            parent=s.root,
            texture=Eval.TEXTURE(Const.SKIN),
            label=Eval.CHAR(Const.TRIANGLE),
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
                texture=Eval.TEXTURE(Const.SKIN),
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
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.MAIN,
            opacity=Color.OPACITY
        )
        # event button
        s.event_button = bui.buttonwidget(
            parent=s.root,
            label=Strings.EVENT_BUTTON_OFF,
            on_activate_call=s.toggle_event,
            texture=Eval.TEXTURE(Const.EMPTY),
            opacity=Color.OPACITY,
            textcolor=(*Color.TEXT,Color.OPACITY),
            enable_sound=False
        )
        # event kids
        for i,n in enumerate(Strings.EVENTS):
            # make
            b = bui.buttonwidget(
                parent=s.root,
                label=n,
                color=Color.MAIN,
                textcolor=Color.INVISIBLE,
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                enable_sound=False,
                selectable=False
            )
            sh = bui.imagewidget(
                parent=s.root,
                opacity=0,
                texture=Eval.TEXTURE(Const.SHADOW),
                color=Color.MAIN
            )
            s.event_kids[b] = {'shadow':sh}
        # edit button
        s.edit_button = bui.buttonwidget(
            parent=s.root,
            label=Strings.EDIT_BUTTON,
            on_activate_call=s.edit_window,
            texture=Eval.TEXTURE(Const.SKIN),
            opacity=Color.OPACITY,
            textcolor=(*Color.TEXT,Color.OPACITY),
            enable_sound=False,
            color=Color.MAIN
        )
        # tools
        tools_str = Const.TOOLS
        for i in range(len(tools_str)):
            b = bui.buttonwidget(
                parent=s.root,
                color=Color.MAIN,
                opacity=0,
                textcolor=Color.INVISIBLE,
                enable_sound=False,
                texture=Eval.TEXTURE(Const.SKIN),
                label=Eval.CHAR(tools_str[i]),
                on_activate_call=bui.CallPartial(
                    s.tool, i
                ),
                repeat=True
            )
            s.tools.append(b)
        # finally
        s.wrap()
        s.top_left()
        s.ui_on = True
        for call in s.pending: call()
        s.pending.clear()

    def edit_window(s):
        if not s.sl: return
        w = s.edit_button
        call = bui.CallPartial(s.edit_window)
        bui.buttonwidget(
            w,
            on_activate_call=lambda:0,
            selectable=False
        )
        s.edit_on = True
        ev = s.sl[2]
        # on finish
        def on_finish():
            s.decide_ui(ev)
            s.window_on = (w,call)
        # math
        start_pos = s.event_on and s.edit_button_pos2 or s.edit_button_pos
        end_pos = s.window_pos
        start_size = s.edit_button_size
        end_size = s.window_size
        s.anims[id(w)] = Animate(
            w,
            duration=s.global_butter,
            func=bui.buttonwidget,
            attrs={
                'position':(start_pos,end_pos),
                'size':(start_size,end_size)
            },
            on_finish=on_finish
        )
        # instant
        bui.buttonwidget(
            w, label=''
        )

    def wrap(s,what=0,on_finish=None):
        # global math
        rx,ry = s.real = bui.get_virtual_screen_size()
        sx,sy = s.stamp_size = (rx,150)
        smol = sy-s.stamp_y_hack
        old_deep_y = getattr(s,'stamp_deep_y',smol)
        big = old_deep_y > sy
        s.stamp_deep_y = max(s.entry_ys_real*(len(s.memory)+1),smol)
        deep_x = s.entry_xs_real*(s.max_time*s.entries_per_sec+1)
        y_off = 70
        s.window_size = wx,wy = 450,300
        s.window_pos = (rx/2-wx/2, ry/2-wy/2+y_off)
        (
            s.window_shadow_pos,
            s.window_shadow_size
        ) = Eval.SHADOW(
            *s.window_pos,
            *s.window_size
        )
        ex,ey = s.event_menu_size = 300, 350
        # stupid
        if not isinstance(what,list): what = [what]
        yes = 0 in what
        # main stuff
        if yes or 1 in what:
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
        if yes or 2 in what:
            # stamp scroll
            bui.scrollwidget(
                s.stamp_scroll,
                size=s.stamp_size
            )
            if big:
                butter = s.global_butter/2
                # stamp scroll root
                s.anims[id(s.stamp_scroll_root)] = Animate(
                    widget=s.stamp_scroll_root,
                    func=bui.containerwidget,
                    attrs={
                        'size':(
                            (sx,old_deep_y),
                            (sx,s.stamp_deep_y)
                        )
                    },
                    duration=butter
                )
                # stamp hscroll
                s.anims[id(s.stamp_hscroll)] = Animate(
                    widget=s.stamp_hscroll,
                    func=bui.hscrollwidget,
                    attrs={
                        'size':(
                            (sx,old_deep_y),
                            (sx,s.stamp_deep_y)
                        )
                    },
                    duration=butter
                )
                # stamp hscroll root
                s.anims[id(s.stamp_hscroll_root)] = Animate(
                    widget=s.stamp_hscroll_root,
                    func=bui.containerwidget,
                    attrs={
                        'size':(
                            (deep_x,old_deep_y),
                            (deep_x,s.stamp_deep_y)
                        )
                    },
                    duration=butter,
                    on_finish=on_finish
                )
            else:
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
                bui.containerwidget(
                    s.stamp_hscroll_root,
                    size=(deep_x,s.stamp_deep_y)
                )
                if callable(on_finish): on_finish()
        # stamp
        if yes or 3 in what:
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
        if yes or 4 in what:
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
            # event kids
            s.event_top = sy+ey+5
            s.ev_mult = (dy+10)
            s.ev_x = 20
            for i,kid in enumerate(s.event_kids):
                pos = (s.ev_x,s.event_top-s.ev_mult*(i+1))
                bui.buttonwidget(kid,position=pos)
        # event
        if yes or 5 in what:
            s.edit_button_pos = pos = (dx+10,sy+6.5)
            s.edit_button_pos2 = (pos[0]+200,pos[1])
            s.edit_button_size = (dx-4,dy-3)
            # edit button
            bui.buttonwidget(
                s.edit_button,
                size=s.edit_button_size,
                position=pos
            )
        # tools
        if yes or 6 in what:
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
        pass

    def toggle_event(s):
        if s.window_on:
            s.window_back()
            return
        Eval.SOUND(Const.OK_SOUND).play()

        # move edit button
        def push_edit():
            w = s.edit_button
            ex,ey = s.edit_button_pos
            start,end = s.edit_button_pos, s.edit_button_pos2
            if (anim:=s.anims.get(id(w),None)):
                anim.cancel()
                start_pos = s.anims[id(w)].attrs_current['position']
            else: start_pos = s.event_on and end or start
            end_pos = s.event_on and start or end
            if (anim:=s.anims.get(id(w),None)):
                anim.cancel()
            s.anims[id(w)] = Animate(
                widget=w,
                func=bui.buttonwidget,
                attrs={
                    'position':(start_pos,end_pos)
                },
                duration=s.global_butter,
                delay=s.event_on and 0.07 or 0
            )
        push_edit()
        dur = s.global_butter*1.5
        old_anim = s.anims.get(id(s.event_button),None)
        if s.event_on:
            s.event_on = False
            bui.buttonwidget(s.event_button, label=Strings.EVENT_BUTTON_OFF)

            s.anims[id(s.event_button)] = old_anim.reverse(
                duration=dur
            )
            # reverse
            for kid,d in s.event_kids.items():
                an = s.anims[id(kid)]
                if (anim:=an.pop('window',None)):
                    anim.cancel()
                if (anim:=an.pop('extra',None)):
                    anim.cancel()
                # animate
                old = an.get('main',None)
                if old:
                    old.cancel()
                    s.anims[id(kid)]['main'] = old.reverse(
                        duration=dur/4
                    )
                # disable
                bui.buttonwidget(
                    kid,
                    on_activate_call=lambda:0,
                    selectable=False
                )
            return

        # expand
        s.event_on = True
        bui.buttonwidget(s.event_button, label=Strings.EVENT_BUTTON_ON)

        # define parent stuff
        rx, ry = s.real
        sx, sy = s.event_menu_size
        dx, dy = s.event_button_size

        # conditional params
        child_start_progress = 0.2
        child_delay = dur * child_start_progress
        child_duration = dur * (1 - child_start_progress)

        # button max
        mx = sx - 40
        s.event_kid_size = (mx,dy)

        # animate parent first (event root)
        if old_anim: old_anim.cancel()
        s.anims[id(s.event_button)] = Animate(
            widget=s.event_root,
            func=bui.imagewidget,
            attrs={
                'size': ((dx, dy), (sx, sy))
            },
            duration=dur
        )

        # make and animate kids
        num = len(Strings.EVENTS)
        parent_width_progress = dx + (sx - dx) * child_start_progress
        start_width_ratio = (parent_width_progress - 40) / mx

        for i,b in enumerate(s.event_kids):
            # animate
            stagger = 0.02 * (num-i)
            s.anims[id(b)]['main'] = (
                Animate(
                    widget=b,
                    func=bui.buttonwidget,
                    attrs={
                        'opacity': (0, Color.OPACITY),
                        'textcolor': (
                            Color.INVISIBLE,
                            (*Color.TEXT, Color.OPACITY)
                        ),
                        'size': ((mx * start_width_ratio, dy), (mx, dy))
                    },
                    duration=child_duration,
                    delay=child_delay + stagger
                )
            )
            # enable
            bui.buttonwidget(
                b,
                on_activate_call=bui.CallPartial(
                    s.window,b,i
                ),
                position=(
                    s.ev_x,
                    s.event_top-s.ev_mult*(i+1)
                )
            )

    def window(s,b,i):
        if s.window_on: s.window_back()
        else: Eval.SOUND(Const.OK_SOUND).play()
        # disable
        call = bui.CallPartial(s.window,b,i)
        s.window_on = (b,call)
        bui.buttonwidget(
            b,
            on_activate_call=lambda:0,
            selectable=False
        )
        # backup
        s.event_kid_pos = pos = (s.ev_x,s.event_top-s.ev_mult*(i+1))
        s.last_window_i = i
        # math
        sx,sy = s.window_size
        dx,dy = s.event_kid_size
        butter = 0.5
        # animate
        s.anims[id(b)]['window'] = (
            Animate(
                widget=b,
                func=bui.buttonwidget,
                duration=butter,
                attrs={
                    'position':(
                        s.event_kid_pos,
                        s.window_pos
                    ),
                    'size':(
                        s.event_kid_size,
                        s.window_size
                    ),
                    'textcolor':(
                        (*Color.TEXT, Color.OPACITY),
                        (*Color.TEXT, 0)
                    )
                }
            )
        )
        # shadow
        s.anims[id(b)]['shadow'] = (
            Animate(
                widget=s.event_kids[b]['shadow'],
                func=bui.imagewidget,
                attrs={
                    'opacity':(0,Color.OPACITY),
                    'position':(
                        s.event_kid_pos,
                        s.window_shadow_pos
                    ),
                    'size':(
                        s.event_kid_size,
                        s.window_shadow_size
                    )
                },
                duration=butter
            )
        )
        # make universal UI
        x,y = s.window_pos
        def bye():
            s.window_clean()
            s.window_back()
        s.window_kids = []
        s.window_marg = 5
        s.window_fix = 8
        dx,dy = 35,35

        pos = (x+s.window_marg-s.window_fix,y+sy-dy-s.window_marg)
        back = bui.buttonwidget(
            parent=s.root,
            position=pos,
            size=(dx,dy),
            enable_sound=False,
            label=Eval.CHAR(Const.BACK),
            on_activate_call=bye,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.MAIN,
            textcolor=Color.INVISIBLE,
            opacity=0
        )
        s.window_kids.append((back,pos,50,bui.buttonwidget,0.35))

        pos = (x+sx/2,y+sy-s.window_marg-32.5)
        w = bui.textwidget(
            parent=s.root,
            text=list(Strings.EVENTS.values())[i],
            color=Color.INVISIBLE,
            position=pos,
            h_align='center',
            v_align='center',
            maxwidth=sx-s.window_marg*3-dx
        )
        s.window_kids.append((w,pos,50,bui.textwidget,0.35))
        # make conditional UI
        s.decide_ui(i)
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
            s.anims[id(w)] = Animate(
                widget=w,
                func=func,
                attrs=attrs,
                duration=0.18,
                delay=delay
            )

    def decide_ui(s,i):
        if i == 0: s.make_node_window()

    def make_node_window(s):
        # math
        x,y = s.window_pos
        sx,sy = s.window_size
        text_push = 15
        delay = 0.35
        # type text
        pos = (x+s.window_marg-s.window_fix,y+sy-88)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.NODE_TYPE_TEXT,
            color=Color.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,bui.textwidget,delay+0))
        # type input
        pos = (x+s.window_marg+80-s.window_fix,y+sy-95)
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
            glow_type='uniform',
            text=Config.DEBUG and Strings.PLACEHOLDER() or ''
        )
        s.window_kids.append((type_text,pos,text_push,bui.textwidget,delay+0,
            ('size',((0,size[1]),size))
        ))
        # name text
        pos = (x+s.window_marg-s.window_fix,y+sy-133)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.NODE_NAME_TEXT,
            color=Color.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,bui.textwidget,delay+0.05))
        # name input
        pos = (x+s.window_marg+80-s.window_fix,y+sy-140)
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
        pos = (x+s.window_marg-s.window_fix,y+sy-150)
        size = (229,2)
        w = bui.imagewidget(
            parent=s.root,
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            size=(0,0),
            opacity=0
        )
        s.window_kids.append((w,pos,text_push,bui.imagewidget,delay+0.1,
            ('size',((0,size[1]),size))
        ))
        # attr text
        pos = (x+s.window_marg-s.window_fix,y+sy-193)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.NODE_ATTR_TEXT,
            color=Color.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,bui.textwidget,delay+0.15))
        # attr input
        pos = (x+s.window_marg+80-s.window_fix,y+sy-200)
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
        pos = (x+s.window_marg-s.window_fix,y+sy-238)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.NODE_EVAL_TEXT,
            color=Color.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,bui.textwidget,delay+0.2))
        # eval input
        pos = (x+s.window_marg+80-s.window_fix,y+sy-245)
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
        bx,by = (215,40)
        butter = 0.5
        text_y = 30
        # attr scroll
        size = dx,dy = (sx/2-s.window_marg*3,sy-s.window_marg*4-51-by)
        pos = px,py = (x+sx-dx+5,y+s.window_marg*2+by+5)
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
        # select attr
        def select(a):
            bui.textwidget(attr,text=a)
            bui.textwidget(val,text=f'{so_far[a]!r}')
        def valid():
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
            return a,v
        # sync
        sync = lambda: bui.containerwidget(
            attr_root,
            size=(dx,max(len(so_far)*text_y,dy-15))
        )
        # pop func
        def do_pop():
            if not (g:=valid()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            a = g[0]
            if not a in so_far:
                s.toast(Strings.ERROR_NOT_FOUND(a))
                return
            so_far.pop(a)
            _i = list(attr_texts).index(a)
            _w = attr_texts.pop(a)
            if (anim:=s.anims[id(_w)]): anim.cancel()
            # fade
            s.anims[id(_w)] = Animate(
                widget=_w,
                func=bui.textwidget,
                attrs={
                    'color':(
                        (*Color.TEXT,Color.OPACITY),
                        Color.INVISIBLE
                    ),
                },
                on_finish=_w.delete,
                on_cancel=_w.delete,
                duration=butter
            )
            # slide
            for i,w in enumerate(
                list(attr_texts.values())[_i:],
                start=_i
            ):
                start_y = (i+1)*text_y
                if (anim:=s.anims[id(w)]):
                    anim.cancel()
                    start_y = anim.attrs_current['position'][1]
                s.anims[id(w)] = Animate(
                    widget=w,
                    func=bui.textwidget,
                    duration=butter,
                    attrs={
                        'position':(
                            (0,start_y),
                            (0,i*text_y)
                        )
                    }
                )
            # finally
            s.toast(Strings.INFO_POPPED(a))
            sync()
        # set func
        def do_set():
            if not (g:=valid()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            a,v = g
            # evaluate
            try: v = eval(v)
            except Exception as e:
                s.toast(Strings.ERROR_EVAL(e))
                return
            # check
            if a in so_far:
                w = attr_texts[a]
                px,py = (0,list(so_far).index(a)*text_y)
                # finally
                s.toast(Strings.INFO_UPDATED(a))
            else:
                px,py = (0,len(so_far)*text_y)
                # attr text
                w = attr_texts[a] = bui.textwidget(
                    parent=attr_root,
                    size=(dx,text_y),
                    maxwidth=dx-15,
                    selectable=True,
                    glow_type='uniform',
                    click_activate=True,
                    on_activate_call=bui.CallPartial(
                        select, a
                    ),
                    text=a,
                    color=Color.INVISIBLE,
                    v_align='center'
                )
                # finally
                sync()
                s.toast(Strings.INFO_ASSIGNED(a))
                # debug
                Config.DEBUG and bui.textwidget(
                    attr,
                    text=Strings.PLACEHOLDER()
                )
            # whatever
            so_far.update({a:v})
            # animate
            if (anim:=s.anims[id(w)]): anim.cancel()
            s.anims[id(w)] = Animate(
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
                duration=butter
            )
        # pop button
        pos = (x+s.window_marg+7-s.window_fix,y+s.window_marg)
        size = bx/2-s.window_marg,by
        w = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.MAIN,
            enable_sound=False,
            label=Strings.NODE_POP_BUTTON,
            textcolor=Color.INVISIBLE,
            on_activate_call=do_pop
        )
        s.window_kids.append((w,pos,50,bui.buttonwidget,delay+0.08,
            ('size',((0,size[1]),size))
        ))
        # set button
        pos = (
            pos[0]+size[0]+s.window_marg*3.5,
            pos[1]
        )
        size = (
            size[0]-s.window_marg,
            size[1]
        )
        w = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.MAIN,
            enable_sound=False,
            label=Strings.NODE_SET_BUTTON,
            textcolor=Color.INVISIBLE,
            on_activate_call=do_set
        )
        s.window_kids.append((w,pos,50,bui.buttonwidget,delay+0.08,
            ('size',((0,size[1]),size))
        ))
        def ready():
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
            return typ,nam
        # done func
        def do_done():
            if not (g:=ready()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            typ,nam = g
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
                texture=Eval.TEXTURE(Const.SKIN),
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
                'event':s.last_window_i,
                'data':final,
                'duration':s.object_duration,
                'start':0
            }
            # capture
            smol = s.stamp_size[1]-s.stamp_y_hack
            old_deep_y = getattr(s,'stamp_deep_y',smol)
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
                    s.anims[kid]['push'] = Animate(
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
            # wrap
            s.wrap([1,2,3],on_finish=s.bottom_left)
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
            half_size = hx,hy = tuple(_/2 for _ in s.window_size)
            half_pos = (hx*3,hy*2.5)
            (
                half_shadow_pos,
                half_shadow_size
            ) = Eval.SHADOW(
                *half_pos,
                *half_size,
                d=0.18
            )
            opacity = Color.OPACITY
            half_opacity = opacity/2
            wait = 0.4
            # animate
            width_in_steps = s.object_duration * s.entries_per_sec

            where_to = lambda: (
                (bl:=s.bottom_left(dry=True)) and (
                    bl[0]+(
                        width_in_steps *
                        s.magic_left
                    ), bl[1]
                )
            )
            s.window_back(
                to=lambda:{
                    'position':(
                        half_pos,
                        where_to()
                    ),
                    'size':(
                        half_size,
                        end_size
                    )
                },
                shadow_to=lambda:{
                    'opacity':(half_opacity,0),
                    'position':(
                        half_shadow_pos,
                        where_to()
                    ),
                    'size':(
                        half_shadow_size,
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
                },
                shadow_extra={
                    'size':(
                        s.window_shadow_size,
                        half_shadow_size
                    ),
                    'position':(
                        s.window_shadow_pos,
                        half_shadow_pos
                    ),
                    'opacity':(
                        opacity,
                        half_opacity
                    )
                }
            )
        # done button
        pos = (px+8,y+s.window_marg)
        size = bx,by = (dx-15,40)
        w = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.MAIN,
            enable_sound=False,
            label=Strings.NODE_DONE_BUTTON,
            textcolor=Color.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((w,pos,50,bui.buttonwidget,delay+0.1,
            ('size',((0,size[1]),size))
        ))

    def window_clean(s):
        for w,*_ in s.window_kids:
            s.anims[id(w)].reverse(
                duration=0.1,
                on_finish=w.delete,
                on_cancel=w.delete
            )
        s.window_kids.clear()

    def window_back(s,to=None,shadow_to=None,on_fix=None,wait=0,extra={},shadow_extra={},instant={}):
        b,call = s.window_on
        def enable():
            bui.buttonwidget(
                b,
                on_activate_call=call,
                selectable=True
            )
        butter = 0.5
        anim = s.anims[id(b)]['window']
        Eval.SOUND(Const.OK_SOUND).play()
        s.window_clean()
        # capture
        if to:
            last_i = s.last_window_i
            last_pos = s.event_kid_pos
            def fix():
                for _ in ['extra','to','shadow']:
                    anim = s.anims[id(b)].pop(_,None)
                    if not anim: continue
                    anim.cancel()
                if s.event_on:
                    ox,oy = last_pos
                    anim = Animate(
                        widget=b,
                        func=bui.buttonwidget,
                        duration=s.global_butter,
                        attrs={
                            'textcolor':(
                                Color.INVISIBLE,
                                (*Color.TEXT,Color.OPACITY)
                            ),
                            'opacity':(0,Color.OPACITY),
                            'position':(
                                (ox-50,oy),
                                (ox,oy)
                            ),
                        }
                    )
                    s.anims[id(b)]['fix'] = anim
                    # enable
                    enable()
                # instant button
                bui.buttonwidget(
                    b,
                    size=s.event_kid_size,
                    opacity=0,
                    textcolor=Color.INVISIBLE,
                    label=list(Strings.EVENTS)[last_i]
                )
                # instant shadow
                bui.imagewidget(
                    s.event_kids[b]['shadow'],
                    opacity=0
                )
                if callable(on_fix): on_fix()
            def do_anim():
                # button
                anim = Animate(
                    widget=b,
                    attrs=to(),
                    func=bui.buttonwidget,
                    duration=butter,
                    on_finish=fix,
                    on_cancel=fix
                )
                s.anims[id(b)]['to'] = anim
                # shadow
                s.anims[id(b)]['shadow'] = Animate(
                    widget=s.event_kids[b]['shadow'],
                    func=bui.imagewidget,
                    attrs=shadow_to(),
                    duration=butter
                )
            if wait:
                s.after_scroll_t = bui.AppTimer(wait,do_anim)
            else: do_anim()
            if extra:
                def nevermind():
                    s.after_scroll_t = None
                    anim.cancel()
                    fix()
                # button
                s.anims[id(b)]['extra'] = Animate(
                    widget=b,
                    func=bui.buttonwidget,
                    duration=wait,
                    attrs=extra,
                    on_cancel=nevermind
                )
            if shadow_extra:
                # shadow
                s.anims[id(b)]['shadow'] = Animate(
                    widget=s.event_kids[b]['shadow'],
                    func=bui.imagewidget,
                    duration=wait,
                    attrs=shadow_extra
                )
            instant and bui.buttonwidget(
                b, **instant
            )
        else:
            # back to event root
            s.anims[id(b)]['window'] = anim.reverse(
                duration=butter
            )
            # fade shadow
            anim = s.anims[id(b)]['shadow']
            s.anims[id(b)]['shadow'] = anim.reverse(
                duration=butter
            )
            # enable
            enable()
        # finally
        s.window_on = None

    def select(s,b,i,ev):
        Eval.SOUND(Const.OK_SOUND).play()
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
        # math
        start_size = (xs,ys/4)
        start_tc = Color.INVISIBLE
        start_op = 0
        for i,b in enumerate(s.tools):
            if (a:=s.anims.get(id(b),None)):
                a.cancel()
            s.anims[id(b)] = Animate(
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

    def hide_tools(s):
        if not s.tools_shown: return
        s.tools_shown = False
        for b in s.tools:
            s.anims[id(b)].reverse(
                duration=s.global_butter
            )

    def tool(s,which):
        if not (s.sl and s.tools_shown): return
        b,i,ev = s.sl
        mem = s.memory[id(b)]
        new = {}
        step = s.entry_xs_real
        scroll_butter = s.global_butter/2

        # move right
        if which == 0:
            # cancel all conflicting animations
            for key in [1, 2, 3]:
                if (anim := s.anims[id(b)].get(key, None)):
                    anim.cancel()
                    s.anims[id(b)].pop(key, None)

            # capture from memory first
            width_steps = mem['duration'] * s.entries_per_sec
            start_x = s.magic_x + s.entry_xs_real * mem['start'] + (width_steps * s.magic_left)
            start_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
            start_pos = (start_x, start_y)

            # override if still running
            if (anim := s.anims[id(b)].get(0, None)) and not anim.finished:
                start_pos = anim.attrs_current['position']
                anim.cancel()

            # clean old right animation
            s.anims[id(b)].pop(0, None)

            # increment start
            mem['start'] += 1

            # calculate target
            new_width_steps = mem['duration'] * s.entries_per_sec
            new_x = s.magic_x + s.entry_xs_real * mem['start'] + (new_width_steps * s.magic_left)
            new_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
            end_pos = (new_x, new_y)

            # assign
            new['position'] = (start_pos, end_pos)

        # move left
        if which == 1:
            # validate minimum
            if mem['start'] <= 0:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_REACHED_ZERO)
                return

            # cancel all conflicting animations
            for key in [0, 2, 3]:
                if (anim := s.anims[id(b)].get(key, None)):
                    anim.cancel()
                    s.anims[id(b)].pop(key, None)

            # capture from memory first
            width_steps = mem['duration'] * s.entries_per_sec
            start_x = s.magic_x + s.entry_xs_real * mem['start'] + (width_steps * s.magic_left)
            start_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
            start_pos = (start_x, start_y)

            # override if still running
            if (anim := s.anims[id(b)].get(1, None)) and not anim.finished:
                start_pos = anim.attrs_current['position']
                anim.cancel()

            # clean old left animation
            s.anims[id(b)].pop(1, None)

            # decrement start
            mem['start'] -= 1

            # calculate target
            new_width_steps = mem['duration'] * s.entries_per_sec
            new_x = s.magic_x + s.entry_xs_real * mem['start'] + (new_width_steps * s.magic_left)
            new_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
            end_pos = (new_x, new_y)

            # assign
            new['position'] = (start_pos, end_pos)

        # expand
        if which == 2:
            # cancel conflicting shrink
            if (shrink := s.anims[id(b)].get(3, None)):
                shrink.cancel()
                s.anims[id(b)].pop(3, None)

            # capture current state from memory first
            current_width_steps = mem['duration'] * s.entries_per_sec
            start_size = (
                s.entry_xs_real * current_width_steps * s.magic_right,
                s.entry_ys_real - s.magic_y
            )
            start_x = s.magic_x + s.entry_xs_real * mem['start'] + (current_width_steps * s.magic_left)
            start_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
            start_pos = (start_x, start_y)

            # override only if same operation is still running
            if (anim := s.anims[id(b)].get(2, None)) and not anim.finished:
                start_size = anim.attrs_current['size']
                start_pos = anim.attrs_current['position']
                anim.cancel()

            # clean old expand animation
            s.anims[id(b)].pop(2, None)

            # increment duration
            mem['duration'] += 1 / s.entries_per_sec

            # calculate target
            new_width_steps = mem['duration'] * s.entries_per_sec
            end_size = (
                s.entry_xs_real * new_width_steps * s.magic_right,
                s.entry_ys_real - s.magic_y
            )
            end_x = s.magic_x + s.entry_xs_real * mem['start'] + (new_width_steps * s.magic_left)
            end_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
            end_pos = (end_x, end_y)

            # assign
            new['size'] = (start_size, end_size)
            new['position'] = (start_pos, end_pos)

        # shrink
        if which == 3:
            # validate minimum
            current_ticks = round(mem['duration'] * s.entries_per_sec)
            if current_ticks <= 1:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_SMALLEST)
                return

            # cancel conflicting expand
            if (expand := s.anims[id(b)].get(2, None)):
                expand.cancel()
                s.anims[id(b)].pop(2, None)

            # capture current state from memory first
            current_width_steps = mem['duration'] * s.entries_per_sec
            start_size = (
                s.entry_xs_real * current_width_steps * s.magic_right,
                s.entry_ys_real - s.magic_y
            )
            start_x = s.magic_x + s.entry_xs_real * mem['start'] + (current_width_steps * s.magic_left)
            start_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
            start_pos = (start_x, start_y)

            # override only if same operation is still running
            if (anim := s.anims[id(b)].get(3, None)) and not anim.finished:
                start_size = anim.attrs_current['size']
                start_pos = anim.attrs_current['position']
                anim.cancel()

            # clean old shrink animation
            s.anims[id(b)].pop(3, None)

            # decrement duration
            mem['duration'] -= 1 / s.entries_per_sec

            # calculate target
            new_width_steps = mem['duration'] * s.entries_per_sec
            end_size = (
                s.entry_xs_real * new_width_steps * s.magic_right,
                s.entry_ys_real - s.magic_y
            )
            end_x = s.magic_x + s.entry_xs_real * mem['start'] + (new_width_steps * s.magic_left)
            end_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
            end_pos = (end_x, end_y)

            # assign
            new['size'] = (start_size, end_size)
            new['position'] = (start_pos, end_pos)

        # move up
        if which == 4:
            # validate bounds
            current_list_index = s.stamp_kids.index(b)
            if current_list_index == 0:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_AT_TOP)
                return

            Eval.SOUND(Const.OK_SOUND).play()

            # neighbor
            target_list_index = current_list_index - 1
            other_btn = s.stamp_kids[target_list_index]
            other_mem = s.memory[id(other_btn)]

            # swap orders
            current_order = mem['order']
            target_order = other_mem['order']
            mem['order'] = target_order
            other_mem['order'] = current_order

            # swap list positions
            s.stamp_kids[current_list_index] = other_btn
            s.stamp_kids[target_list_index] = b

            # calculate target positions
            new_y_up = s.entry_ys_real * (len(s.memory) - target_order - 1)
            new_y_down = s.entry_ys_real * (len(s.memory) - current_order - 1)

            # animate current button moving up
            # cancel conflicting down
            if (down := s.anims[id(b)].get(5, None)):
                down.cancel()
                s.anims[id(b)].pop(5, None)

            # capture from memory first
            width_steps_b = mem['duration'] * s.entries_per_sec
            start_x_b = s.magic_x + s.entry_xs_real * mem['start'] + (width_steps_b * s.magic_left)
            start_y_b = s.entry_ys_real * (len(s.memory) - current_order - 1)
            start_pos_b = (start_x_b, start_y_b)

            # override if still running
            if (anim := s.anims[id(b)].get(4, None)) and not anim.finished:
                start_pos_b = anim.attrs_current['position']
                anim.cancel()

            # clean old up animation
            s.anims[id(b)].pop(4, None)

            # animate
            end_pos_b = (start_pos_b[0], new_y_up)
            s.anims[id(b)][4] = Animate(
                widget=b,
                func=bui.buttonwidget,
                duration=s.global_butter,
                attrs={'position': (start_pos_b, end_pos_b)}
            )

            # animate other button moving down
            # cancel conflicting down
            if (down := s.anims[id(other_btn)].get(5, None)):
                down.cancel()
                s.anims[id(other_btn)].pop(5, None)

            # capture from memory first
            width_steps_other = other_mem['duration'] * s.entries_per_sec
            start_x_other = s.magic_x + s.entry_xs_real * other_mem['start'] + (width_steps_other * s.magic_left)
            start_y_other = s.entry_ys_real * (len(s.memory) - target_order - 1)
            start_pos_other = (start_x_other, start_y_other)

            # override if still running
            if (anim := s.anims[id(other_btn)].get(4, None)) and not anim.finished:
                start_pos_other = anim.attrs_current['position']
                anim.cancel()

            # clean old up animation
            s.anims[id(other_btn)].pop(4, None)

            # animate
            end_pos_other = (start_pos_other[0], new_y_down)
            s.anims[id(other_btn)][4] = Animate(
                widget=other_btn,
                func=bui.buttonwidget,
                duration=s.global_butter,
                attrs={'position': (start_pos_other, end_pos_other)}
            )

        # move down
        if which == 5:
            # validate bounds
            current_list_index = s.stamp_kids.index(b)
            max_list_index = len(s.stamp_kids) - 1
            if current_list_index == max_list_index:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_AT_BOTTOM)
                return

            Eval.SOUND(Const.OK_SOUND).play()

            # neighbor
            target_list_index = current_list_index + 1
            other_btn = s.stamp_kids[target_list_index]
            other_mem = s.memory[id(other_btn)]

            # swap orders
            current_order = mem['order']
            target_order = other_mem['order']
            mem['order'] = target_order
            other_mem['order'] = current_order

            # swap list positions
            s.stamp_kids[current_list_index] = other_btn
            s.stamp_kids[target_list_index] = b

            # calculate target positions
            new_y_down = s.entry_ys_real * (len(s.memory) - target_order - 1)
            new_y_up = s.entry_ys_real * (len(s.memory) - current_order - 1)

            # animate current button moving down
            # cancel conflicting up
            if (up := s.anims[id(b)].get(4, None)):
                up.cancel()
                s.anims[id(b)].pop(4, None)

            # capture from memory first
            width_steps_b = mem['duration'] * s.entries_per_sec
            start_x_b = s.magic_x + s.entry_xs_real * mem['start'] + (width_steps_b * s.magic_left)
            start_y_b = s.entry_ys_real * (len(s.memory) - current_order - 1)
            start_pos_b = (start_x_b, start_y_b)

            # override if still running
            if (anim := s.anims[id(b)].get(5, None)) and not anim.finished:
                start_pos_b = anim.attrs_current['position']
                anim.cancel()

            # clean old down animation
            s.anims[id(b)].pop(5, None)

            # animate
            end_pos_b = (start_pos_b[0], new_y_down)
            s.anims[id(b)][5] = Animate(
                widget=b,
                func=bui.buttonwidget,
                duration=s.global_butter,
                attrs={'position': (start_pos_b, end_pos_b)}
            )

            # animate other button moving up
            # cancel conflicting up
            if (up := s.anims[id(other_btn)].get(4, None)):
                up.cancel()
                s.anims[id(other_btn)].pop(4, None)

            # capture from memory first
            width_steps_other = other_mem['duration'] * s.entries_per_sec
            start_x_other = s.magic_x + s.entry_xs_real * other_mem['start'] + (width_steps_other * s.magic_left)
            start_y_other = s.entry_ys_real * (len(s.memory) - target_order - 1)
            start_pos_other = (start_x_other, start_y_other)

            # override if still running
            if (anim := s.anims[id(other_btn)].get(5, None)) and not anim.finished:
                start_pos_other = anim.attrs_current['position']
                anim.cancel()

            # clean old down animation
            s.anims[id(other_btn)].pop(5, None)

            # animate
            end_pos_other = (start_pos_other[0], new_y_up)
            s.anims[id(other_btn)][5] = Animate(
                widget=other_btn,
                func=bui.buttonwidget,
                duration=s.global_butter,
                attrs={'position': (start_pos_other, end_pos_other)}
            )

        # duplicate
        if which == 6:
            Eval.SOUND(Const.OK_SOUND).play()
            s.on_scroll()

            # cancel all existing duplicate animations and fix their state
            for kid in s.stamp_kids:
                if (anim := s.anims[id(kid)].get(6, None)):
                    anim.cancel()
                    s.anims[id(kid)].pop(6, None)
                    # reset to final state
                    bui.buttonwidget(
                        kid,
                        opacity=Color.OPACITY,
                        textcolor=(*Color.TEXT, Color.OPACITY)
                    )

            # copy memory data
            original_data = mem.copy()
            original_event = original_data['event']
            original_duration = original_data['duration']
            original_start = original_data['start']
            original_order = original_data['order']
            node_data = original_data['data'].copy()

            # create button
            size = (
                s.entry_xs_real * (
                    original_duration *
                    s.entries_per_sec
                ) * s.magic_right,
                s.entry_ys_real - s.magic_y
            )
            btn = bui.buttonwidget(
                parent=s.stamp_hscroll_root,
                texture=Eval.TEXTURE(Const.SKIN),
                label=node_data['name'],
                textcolor=Color.INVISIBLE,
                color=Color.MAIN,
                opacity=0,
                enable_sound=False,
                size=size,
                button_type='square'
            )

            # insert right after original in list
            original_list_index = s.stamp_kids.index(b)
            s.stamp_kids.insert(original_list_index + 1, btn)

            # new order is right after original
            new_order = original_order + 1

            # setup callback
            call = bui.CallPartial(
                s.select, btn, new_order, original_event
            )
            bui.buttonwidget(btn, on_activate_call=call)

            # add to memory
            s.memory[id(btn)] = {
                'order': new_order,
                'event': original_event,
                'data': node_data,
                'duration': original_duration,
                'start': original_start
            }

            # shift all entries below down by one
            for kid in s.stamp_kids[original_list_index + 2:]:
                s.memory[id(kid)]['order'] += 1

            # capture old state
            smol = s.stamp_size[1] - s.stamp_y_hack
            old_deep_y = getattr(s, 'stamp_deep_y', smol)

            # update layout
            s.wrap([1, 2, 3])

            # calculate positions
            width_steps = original_duration * s.entries_per_sec
            final_x = s.magic_x + s.entry_xs_real * original_start + (width_steps * s.magic_left)

            # start from original position
            orig_y = s.entry_ys_real * (len(s.memory) - original_order - 1)
            # end at position right below original
            final_y = s.entry_ys_real * (len(s.memory) - new_order - 1)

            # place at original position
            bui.buttonwidget(btn, position=(final_x, orig_y))

            # animate entries that need to shift
            big = old_deep_y != smol

            # shift entries below duplicate down by one
            for kid in s.stamp_kids[original_list_index + 2:]:
                kid_mem = s.memory[id(kid)]
                kid_width_steps = kid_mem['duration'] * s.entries_per_sec
                kid_x = s.magic_x + s.entry_xs_real * kid_mem['start'] + (kid_width_steps * s.magic_left)

                old_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'])
                new_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 1)

                if big:
                    bui.buttonwidget(kid, position=(kid_x, new_y))
                else:
                    s.anims[id(kid)][which] = Animate(
                        widget=kid,
                        func=bui.buttonwidget,
                        attrs={
                            'position': ((kid_x, old_y), (kid_x, new_y))
                        },
                        duration=s.global_butter
                    )

            # shift entries above and including original up by one
            for kid in s.stamp_kids[:original_list_index + 1]:
                kid_mem = s.memory[id(kid)]
                kid_width_steps = kid_mem['duration'] * s.entries_per_sec
                kid_x = s.magic_x + s.entry_xs_real * kid_mem['start'] + (kid_width_steps * s.magic_left)

                old_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 2)
                new_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 1)

                if big:
                    bui.buttonwidget(kid, position=(kid_x, new_y))
                else:
                    s.anims[id(kid)][which] = Animate(
                        widget=kid,
                        func=bui.buttonwidget,
                        attrs={
                            'position': ((kid_x, old_y), (kid_x, new_y))
                        },
                        duration=s.global_butter
                    )

            # animate new button from original to below
            s.anims[id(btn)][which] = Animate(
                widget=btn,
                func=bui.buttonwidget,
                attrs={
                    'opacity': (0, Color.OPACITY),
                    'textcolor': (
                        Color.INVISIBLE,
                        (*Color.TEXT, Color.OPACITY)
                    ),
                    'position': ((final_x, orig_y), (final_x, final_y))
                },
                duration=s.global_butter
            )

            # scroll to new button
            s.scroll_to_timer = bui.AppTimer(
                s.global_butter / 2,
                bui.CallPartial(s.scroll_to, btn)
            )

            # select and toast
            call()
            s.toast(Strings.INFO_DUPLICATED(node_data["name"]))
            return

        # delete
        if which == 7:
            Eval.SOUND(Const.OK_SOUND).play()
            if not s.can_delete:
                s.toast(Strings.CONFIRM_DELETE(
                    mem['data']['name']
                ), extra=2)
                s.can_delete = 1
                return

            # get the name for toast
            node_name = mem['data']['name']
            deleted_order = mem['order']

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
                s.wrap([1,2,3])

                # animate remaining items into new positions
                for idx, kid in enumerate(reversed(s.stamp_kids)):
                    kid_mem = s.memory[id(kid)]
                    if kid_mem['order'] >= deleted_order: continue
                    width_in_steps = kid_mem['duration'] * s.entries_per_sec
                    old_x = s.magic_x + s.entry_xs_real*kid_mem['start'] + (width_in_steps * s.magic_left)

                    # current position
                    current_y = s.entry_ys_real*(idx+1)

                    end_pos = (
                        old_x,
                        s.entry_ys_real*idx
                    )

                    s.anims[id(kid)][which] = Animate(
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
            s.anims[id(b)][which] = Animate(
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

        # default
        s.scroll_to_timer = bui.AppTimer(
            scroll_butter,
            bui.CallPartial(s.scroll_to,b)
        )
        if not new: return
        s.anims[id(b)][which] = Animate(
            widget=b,
            func=bui.buttonwidget,
            duration=s.global_butter,
            attrs=new
        )
        Eval.SOUND(Const.OK_SOUND).play()

    def scroll_to(s,b):
        # horizontal
        bui.containerwidget(
            s.stamp_hscroll_root,
            visible_child=b
        )
        # vertical hell
        rx,ry = s.real
        bx,by = b.get_screen_space_center()
        dx,dy = s.bottom_left_h.get_screen_space_center()
        to = Eval.RELATIVE(
            rx/2,ry/2,
            dx,dy,
            bx,by
        )
        temp = bui.textwidget(
            parent=s.stamp_scroll_root,
            position=to,
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
        s.condition = condition

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
    EDIT_BUTTON = 'Edit'
    EVENT_BUTTON_OFF = 'Event'
    EVENT_BUTTON_ON = 'Back'
    EVENTS = {
        'Node':'Add a scene node',
        'Camera':'Move the camera around',
        'Sound':'Play a sound',
        'FX':'Emit an effect',
        'Map':'Control the map',
        'Custom':'Custom action'
    }
    # node event
    NODE_TYPE_TEXT = 'Type'
    NODE_TYPE_DESC = 'The node\'s type kwarg\nbascenev1.newnode(type=\'THIS\')\nEnter'
    NODE_NAME_TEXT = 'Name'
    NODE_NAME_DESC = 'The node\'s name kwarg\nbascenev1.newnode(name=\'THIS\')\nEnter'
    NODE_ATTR_TEXT = 'Attr'
    NODE_ATTR_DESC = 'The node\'s attribute name in attr dict\nbascenev1.newnode(attrs={\'THIS\':value})\nEnter'
    NODE_EVAL_TEXT = 'Eval'
    NODE_EVAL_DESC = 'The node\'s attr value in attr dict (evaluated)\nbascenev1.newnode(attrs={\'attr\':THIS})\nEnter'
    NODE_SET_BUTTON = 'Set'
    NODE_POP_BUTTON = 'Pop'
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
    ERROR_NOT_FOUND = lambda a:(
        f'Nothing here is called {a!r}',
        'Yeah, nothing happened'
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
    INFO_ASSIGNED = lambda a:(
        f'Assigned new attribute {a}',
        'Use the same attr name to overwrite it later'
    )
    INFO_UPDATED = lambda a:(
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
    INFO_POPPED = lambda n:(
        f'Popped "{n}"',
        'It\'s in a better place now.'
    )
    # confirm
    CONFIRM_DELETE = lambda t:(
        f'Really delete "{t}"?',
        f'Press {Eval.CHAR(Const.TOOLS[7])} again to confirm'
    )
    # extra
    WELCOME = lambda n: (
        f'{n} joined the studio! Press for more',
         'Experimental. Buggy. Fun. Pick two. Or all three.'
    )
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
    BLAME = (
        '{Wp48S^xk9=GL@E0stWa8~^|S5YJf5;0J63A6)<hiq;LsE8+6)_!8wlJgD2B;9B|#tpRK5'
        'GCU|nmj0kz<}AdtfLdZb6+!sQ4OUYK6Q8uy*r^_3`Pcu$YW|C=9;{Y(LL1VnyQ*>B{gpqX'
        'dk#@9?UBPn;2%V#jMSPv_1XgyAJ^ZvYCOsN&;+crKe;d^f*1&xO5^OsH3p{1PWZr2DvZX#'
        'Q(asi+>+1LJ3~Qw$fLY?PWe0Gz8+_A7Di@~MP;^#5AkfTHb%IeI)Caw!BokT0(B=(PBwFM'
        'J`y4mX1FWa8Uc<=Zf?~Q^yB!g9w1-Ks>f=OJA!hqouOgMGKK+K<}ReB;Y*XYGvVu?pxK;0'
        '%D0$KY!tzmUe!969j2GtKACX6T0Rc4wuI|fIo}Q1><Z{CT{od3#5&02lWo)$FCe_<5~*HM'
        'nBlD2qayQnlBUHBT2XsgCZQ-dx;buhBS@YyKW+~KQcCm;IByjf3-we{=2u*1Y^0M(j$HWk'
        'IWHE~yH_D-wLG~_mX1L<IjBf}soW?)??_d_qs|=35NNufR(c#fv2qnAeqdmdp}`G&t)0;}'
        'WJ6k?{Y40s)mPa;Q<@j?s#eLU9MD~%Tr+YWPZ^zHI(Xo|4k(=>mcXg)cg(+@UNr_t_FI@@'
        'K-z`vn!j^;vk3jjV~X?AF#}P5-lM@%Cm(E@*d0FbkeodJ^wCY=H}(suiou^zL}})0AxqiM'
        'f9o>9`gZTUUMFRuXQ1^80Sed9lNtj1TBkASgF`=Ob9Ll~2$YYYb#|Q;&`99IjGc~in__wo'
        'iPNw?$28MM-FVrS%b&Y$h9=Oi+t0%a%YIX}>Gr<z#Z*yz@R_tj1}<W_b-_in?%9}es&E?D'
        '=q4#J*EC_<r^XPK>?}vc^toT;Juz3GE5ivr@NgN<cUK!%@DZ@{GS$|%XxMcfYB1jY3T5JB'
        'D1S;;wio{syRoRdt419oa!bUns%Gg)eg~VvuoY>aO&Jl5l2R;2eGynkua*2)$i2kE1SDu&'
        '{fQ=D7ZZ?YLF;Krit7Y<MW5FOq6{vVcevZZe2FQrD6=6^U@8{nV!zCzo?W`fILCS@mqZbM'
        'HC&KLY9KG=cD&Wy#o@6(s#)Tr9YTqDuP6-uhb|nzWe>FA*F^Ze6aAM--qkd2l<g|iWz%f!'
        'AIwz9Spi%I@Cg`YO=Sz7LLh*<Y+=mRh4i=-43mqK4X1FQ=02y(=9;{9%4hj%g#`2bbmz<&'
        'V(K(f_Hg+bOH4LG7M2GOC&q>cLC{U{DR)fW57r#Z@fs1Nb(eQY`_!vq?shD>Bk5E?lhEEM'
        'F*ga;#^a?rEOgo?)H<xv3hAFE>l*mC@H&L_`LBwqpgQQ934D*<v<7`V_P8d%*-894y5ak%'
        'XGm@_Sns?57LUIp!FQBP{HMJc5U&6LwATGxLn1;>00FxQ?G69{MaZMAvBYQl0ssI200dcD'
    )

class Const:
    # visual
    SKIN = 'white'
    EMPTY = 'empty'
    SHADOW = 'softRect'
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
    # based
    TRIANGLE = 'PLAY_STATION_TRIANGLE_BUTTON'
    SQUARE = 'PLAY_STATION_SQUARE_BUTTON'
    BACK = 'BACK'
    # extra
    BLAME = " ()',?ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

class Eval:
    CHAR = lambda a: bui.charstr(getattr(bui.SpecialChar,a))
    TEXTURE = lambda t: bui.gettexture(t)
    SOUND = lambda s: bui.getsound(s)
    BLAME = lambda s,c: ''.join(
        c[i] if i < len(c) else '\x00'
        for i in __import__('lzma').decompress(
            __import__('base64').b85decode(s)
        )
    ).split('\x00')
    SHADOW = lambda px,py,sx,sy,d=0.16: (
        (px-sx*d,py-sy*d),
        (sx+sx*(d*2),sy+sy*(d*2))
    )
    RELATIVE = lambda hx,hy,dx,dy,bx,by: (
        (bx+hx)-(dx+hx),
        (by+hy)-(dy+hy)
    )


class DarkColor:
    MAIN = (0,0,0)
    TINT = (0.5,0.5,0.5)
    TEXT = (2,2,2)
    INVISIBLE = (0,0,0,0)
    OPACITY = 0.4

class Colors:
    DARK = DarkColor

# global
Color = getattr(Colors,Config.COLOR)

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
        s.editor and s.editor.run_on_ui(
            lambda: s.editor.toast(
                Strings.WELCOME(
                    p.sessionplayer.getname()
                )
            )
        )

    def on_player_leave(s,p):
        if s.is_master(p):
            s.master = None
            s.kill_ui()

    def make_ui(s):
        ba.pushcall(ba.CallPartial(
            s.editor.make
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
