# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Movi v1.0 - Movie Maker

Experimental.
"""

import babase as ba
import bauiv1 as bui
import _babase as _ba
import bascenev1 as bs

from re import sub
from os import listdir
from random import choice
from time import perf_counter
from weakref import WeakMethod
from os.path import join, dirname
from collections import defaultdict

__version__ = '1.0'

class Config:
    COLOR = 'DarkColor'

class Editor:
    _shared = {'callbacks':[]}

    @staticmethod
    def ui_safe(f):
        return lambda s,*a,**k: (
            hasattr(s,'root') and
            s.root.exists() and
            s.ui_on and f(s,*a,**k)
        )

    @staticmethod
    def clickable(f):
        return lambda s,*a,**k: (
            f(s,*a,**k) if s.ui_clickable else
            s.toast(Strings.ERROR_PAUSE_FIRST) or
            Eval.SOUND(Const.BAD_SOUND).play()
        )

    @staticmethod
    def _call(sig):
        for callback_ref in Editor._shared['callbacks']:
            callback = callback_ref()
            callback(sig)

    def callback(s,cb):
        bui.apptimer(Const.BA_LAG_SMALL,getattr(s,cb))

    def __init__(s,map):
        # register
        s.__class__._shared['callbacks'].append(WeakMethod(s.callback))
        s.ui_on = False
        s.ui_clickable = False
        s.original_map = map
        # timeline
        s.timeline = []
        s.timeline_index = 0
        s.active = {}
        s.active_sounds = {}
        s.active_timers = {}
        # play
        s.play_timer = None
        s.playing = False
        s.playhead = None
        # toast
        s.can_toast = True
        s.toast_zoom = None
        s.toast_blink = None
        s.last_toast = None
        # menu
        s.menu_root = None
        s.menu_on = False
        s.menu_kids = []
        # event
        s.event_root = None
        s.event_on = False
        s.event_kids = {}
        s.event_top = None
        # window
        s.window_on = ()
        s.window_kids = []
        s.window_trash = []
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
        s.stamp_timeline = []
        s.stamp_hack = 14
        s.entries_per_sec = 5
        s.object_duration = 1
        # memory
        s.memory = {}
        s.anims = defaultdict(dict)
        s.in_anims = []
        s.out_anims = []
        s.pending = []
        # controls
        s.controls = []
        s.controls_shown = False
        # tools
        s.tools = []
        s.tools_shown = False
        # camera
        s.camera_timer = None
        s.camera_data = {}
        # extra
        s.sl = None
        s.global_butter = 0.3
        s.can_do = False
        s.blame = None

    def schedule_on_ui(s,f):
        if s.ui_on: f()
        else: s.pending.append(f)

    def universal_back(s):
        if s.window_on or s.event_on:
            s.event_button.activate()
        else: s.square.activate()

    @ui_safe
    def on_resize(s):
        s.on_scroll()
        s.wrap_all()

    @ui_safe
    def on_rescale(s):
        s.on_scroll()
        s.wrap_all()

    @ui_safe
    def on_scroll(s):
        if s.event_on:
            # you're not going anywhere
            for kid in s.event_kids:
                an = s.anims[id(kid)]
                for _ in ['extra','to']:
                    (a:=an.get(_,None)) and a.cancel()

    def toast(s,inp=None,shut=1,extra=0):
        shut or Eval.SOUND(Const.OK_SOUND).play()
        # on toast
        if not s.can_toast and not shut: return
        if s.can_do and extra<1: s.can_do = False
        if s.toast_zoom: s.toast_zoom.cancel()
        s.can_toast = False
        b = s.toast_bg
        t,desc = inp or ('','')
        # update
        if not s.blame:
            s.blame = Eval.BLAME(
                Strings.BLAME(),
                Const.BLAME
            )
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
        zero = 0.0001
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
            anim.cancel()
        def enable(): s.can_toast = True
        # zoom
        zoom_time = 0.2
        def zoom():
            s.toast_zoom = Animate(
                widget=b,
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
        # blink text
        start_textcolor = (*Color.TEXT,Color.OPACITY)
        blink_time = 0.2
        apply_text = bui.CallPartial(
            bui.buttonwidget,
            b, label=t
        )
        skip_blink = s.last_toast == t
        def blink():
            if (anim:=s.toast_blink):
                anim.cancel()
            s.toast_blink = Animate(
                widget=b,
                attrs={
                    'textcolor':(
                        start_textcolor,
                        skip_blink and start_textcolor or Const.INVISIBLE
                    )
                },
                duration=skip_blink and zero or blink_time,
                on_finish=(None,),
                on_reverse=apply_text,
                on_cancel=apply_text
            )
        blink()
        # animate
        s.anims[id(b)] = Animate(
            widget=b,
            attrs={
                'size':(start_size,end_size),
                'opacity':(
                    start_opacity,
                    t and Color.OPACITY or 0
                ),
                'position':(
                    (x,y),
                    end_pos
                )
            },
            duration=rush and zero or duration,
            on_finish=zoom
        )
        s.toast_timer = inp and bui.AppTimer(
            max(len(t)*0.07,3),
            s.toast
        )
        # finally
        s.last_toast = t

    def make(s):
        # root
        s.root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            background=False
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
            color=Color.BASE,
            opacity=0
        )
        # square
        s.square = bui.buttonwidget(
            parent=s.root,
            texture=Eval.TEXTURE(Const.SKIN),
            label=Eval.CHAR(Const.SQUARE),
            color=Color.BASE,
            textcolor=(*Color.TEXT,Color.OPACITY),
            enable_sound=False,
            on_activate_call=s.on_square
        )
        # triangle
        s.triangle = bui.buttonwidget(
            parent=s.root,
            texture=Eval.TEXTURE(Const.SKIN),
            label=Eval.CHAR(Const.TRIANGLE),
            color=Color.BASE,
            textcolor=(*Color.TEXT,Color.OPACITY),
            enable_sound=False,
            on_activate_call=s.on_triangle
        )
        # stamp scroll
        s.stamp_scroll = bui.scrollwidget(
            parent=s.root,
            border_opacity=0,
            color=Color.BASE,
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
            color=Color.BASE
        )
        # stamp hscroll root
        s.stamp_hscroll_root = bui.containerwidget(
            parent=s.stamp_hscroll,
            background=False
        )
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
            color=Color.BASE,
            opacity=0
        )
        # event button
        s.event_button = bui.buttonwidget(
            parent=s.root,
            label=Strings.EVENT_BUTTON_OFF,
            on_activate_call=s.toggle_event,
            texture=Eval.TEXTURE(Const.EMPTY),
            opacity=0,
            textcolor=Const.INVISIBLE,
            enable_sound=False
        )
        # event kids
        for i,n in enumerate(Strings.EVENTS):
            # make
            b = bui.buttonwidget(
                parent=s.root,
                label=n,
                color=Color.BASE,
                textcolor=Const.INVISIBLE,
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                enable_sound=False,
                selectable=False
            )
            sh = bui.imagewidget(
                parent=s.root,
                opacity=0,
                texture=Eval.TEXTURE(Const.SHADOW),
                color=Color.BASE
            )
            s.event_kids[b] = {'shadow':sh}
        # edit button
        s.edit_button = bui.buttonwidget(
            parent=s.root,
            label=Strings.EDIT_BUTTON,
            on_activate_call=s.edit_window,
            texture=Eval.TEXTURE(Const.SKIN),
            opacity=0,
            textcolor=Const.INVISIBLE,
            enable_sound=False,
            color=Color.BASE
        )
        s.edit_button_shadow = bui.imagewidget(
            parent=s.root,
            opacity=0,
            texture=Eval.TEXTURE(Const.SHADOW),
            color=Color.BASE
        )
        # key button
        s.key_button = bui.buttonwidget(
            parent=s.root,
            label=Strings.KEYS,
            on_activate_call=s.key_window,
            texture=Eval.TEXTURE(Const.SKIN),
            opacity=0,
            textcolor=Const.INVISIBLE,
            enable_sound=False,
            color=Color.BASE
        )
        s.key_button_shadow = bui.imagewidget(
            parent=s.root,
            opacity=0,
            texture=Eval.TEXTURE(Const.SHADOW),
            color=Color.BASE
        )
        # tools
        for i,t in enumerate(Const.TOOLS):
            b = bui.buttonwidget(
                parent=s.root,
                color=Color.BASE,
                opacity=0,
                textcolor=Const.INVISIBLE,
                enable_sound=False,
                texture=Eval.TEXTURE(Const.SKIN),
                label=Eval.CHAR(t),
                on_activate_call=bui.CallPartial(
                    s.do_tool, i
                ),
                repeat=True
            )
            s.tools.append(b)
        # controls
        for i,t in enumerate(Const.CONTROLS):
            b = bui.buttonwidget(
                parent=s.root,
                color=Color.BASE,
                opacity=0,
                textcolor=Const.INVISIBLE,
                enable_sound=False,
                texture=Eval.TEXTURE(Const.SKIN),
                label=(
                    isinstance(t,str)
                    and Eval.CHAR(t)
                    or Eval.CHAR(t[s.playing])
                ),
                on_activate_call=bui.CallPartial(
                    s.do_control, i
                ),
                size=(0,0)
            )
            s.controls.append(b)
        # toast
        s.toast_bg = bui.buttonwidget(
            parent=s.root,
            label='',
            enable_sound=False,
            selectable=False,
            size=(0,0),
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE
        )
        # extra
        s.make_menu()
        # finally
        s.ui_clickable = True
        s.wrap_all(init=True)
        s.make_timeline(init=True)
        s.wrap_timeline()
        s.top_left()
        def on_finish():
            for call in s.pending: call()
            s.pending.clear()
        bui.apptimer(0.3,bui.CallPartial(
            s.toggle_ui, on_finish
        ))

    def make_timeline(s,init=False):
        # cleanup
        for i,j in s.stamp_timeline:
            i.delete()
            j.delete()
        s.stamp_timeline.clear()
        # stamp timeline
        eps = s.entries_per_sec
        num_markers = int(s.stamp_deep_x / s.entry_xs_real) + 5
        for i in range(num_markers):
            t = bui.textwidget(
                parent=s.stamp_hscroll_root,
                text=(
                    i%eps == 0
                    and str(int(i/eps))
                    or '.'
                ),
                h_align=Const.ALIGN,
                v_align=Const.ALIGN,
                size=(10,5),
                scale=0.5,
                color=(
                    Const.INVISIBLE if init else
                    (*Color.TEXT,Color.OPACITY)
                )
            )
            l = bui.imagewidget(
                parent=s.stamp_hscroll_root,
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0 if init else Color.OPACITY/10,
                size=(2,s.stamp_deep_y*2),
                color=Color.TEXT
            )
            s.stamp_timeline.append((t,l))

    def build_timeline(s):
        s.timeline = []
        for btn_id, mem in s.memory.items():
            btn = next(
                (b for b in s.stamp_kids if id(b) == btn_id),
                None
            )
            if not btn: continue
            s.timeline.append({
                'time': mem['start'],
                'type': 'start',
                'button': btn,
                'memory': mem,
                'btn_id': btn_id
            })
            s.timeline.append({
                'time': mem['start'] + mem['duration'],
                'type': 'end',
                'button': btn,
                'memory': mem,
                'btn_id': btn_id
            })
        # sort
        s.timeline.sort(key=lambda x: x['time'])
        s.max_time = s.timeline[-1]['time'] if s.timeline else 0

    def wrap_timeline(s):
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
                position=(px+4,-s.stamp_deep_y/2)
            )

    def toggle_ui(s,on_finish=None):
        if s.ui_on:
            s.animate_out(on_finish=on_finish)
            s.ui_on = False
            s.ui_clickable = False
        else:
            s.animate_in(on_finish=on_finish)
            s.ui_on = True
            s.ui_clickable = True

    def animate_in(s,on_finish=None):
        # instant
        bui.scrollwidget(
            s.stamp_scroll,
            size=s.stamp_size
        )
        butter = s.global_butter * 2
        # reversing?
        for anim in s.out_anims:
            anim.cancel()
        s.in_anims.clear()
        s.out_anims.clear()
        # cancellable
        def cleanup():
            callable(on_finish) and on_finish()
        # stamp bg
        a = Animate(
            widget=s.stamp_bg,
            duration=butter,
            attrs={
                'opacity':(0,Color.OPACITY)
            },
            on_finish=cleanup
        )
        s.in_anims.append(a)
        # stamp timeline
        for t,l in s.stamp_timeline:
            # text
            a = Animate(
                widget=t,
                duration=butter,
                attrs={
                    'color':(
                        Const.INVISIBLE,
                        (*Color.TEXT,Color.OPACITY)
                    )
                }
            )
            s.in_anims.append(a)
            # line
            a = Animate(
                widget=l,
                duration=butter,
                attrs={
                    'opacity':(0,Color.OPACITY/10)
                }
            )
            s.in_anims.append(a)
        # event button
        a = Animate(
            widget=s.event_button,
            duration=butter,
            attrs={
                'textcolor':(
                    Const.INVISIBLE,
                    (*Color.TEXT,Color.OPACITY)
                )
            }
        )
        s.in_anims.append(a)
        # event button background
        a = Animate(
            widget=s.event_root,
            duration=butter,
            attrs={
                'opacity':(0,Color.OPACITY)
            }
        )
        s.in_anims.append(a)
        # edit button
        a = Animate(
            widget=s.edit_button,
            duration=butter,
            attrs={
                'opacity':(0,Color.OPACITY),
                'textcolor':(
                    Const.INVISIBLE,
                    (*Color.TEXT,Color.OPACITY)
                )
            }
        )
        s.in_anims.append(a)
        # key button
        a = Animate(
            widget=s.key_button,
            duration=butter,
            attrs={
                'opacity':(0,Color.OPACITY),
                'textcolor':(
                    Const.INVISIBLE,
                    (*Color.TEXT,Color.OPACITY)
                )
            }
        )
        s.in_anims.append(a)
        # finally
        if len(s.memory):
            if s.sl: s.show_tools()
            else: s.show_controls()

    def animate_out(s,on_finish=None):
        butter = s.global_butter*2
        # anything up?
        s.collapse_all(hard=True)
        # instant
        bui.scrollwidget(
            s.stamp_scroll,
            size=(0,0)
        )
        s.out_anims.clear()
        # reverse
        for anim in s.in_anims:
            a = anim.reverse(
                duration=butter
            )
            s.out_anims.append(a)
        s.in_anims.clear()
        callable(on_finish) and bui.apptimer(butter,on_finish)

    def collapse_all(s,hard=False):
        if not s.event_on and s.window_on:
            s.window_back(into_nothing=True)
        if s.event_on and s.window_on:
            s.window_back(into_nothing=True,skip=True)
            s.toggle_event()
        if s.event_on:
            s.toggle_event()
        if s.controls_shown and (hard or not s.memory):
            s.hide_controls()
        if s.tools_shown:
            s.hide_tools()

    @clickable
    def edit_window(s):
        if s.window_on:
            s.window_back()
        if not s.sl:
            Eval.SOUND(Const.BAD_SOUND).play()
            s.toast(Strings.ERROR_SELECT_SOMETHING)
            return
        Eval.SOUND(Const.OK_SOUND).play()
        # disable
        bui.buttonwidget(
            s.edit_button,
            on_activate_call=Const.DO_NOTHING,
            selectable=False
        )
        # math
        start_pos = s.event_on and s.edit_button_pos2 or s.edit_button_pos
        end_pos = s.window_pos
        start_size = s.edit_button_size
        end_size = s.window_size
        butter = s.global_butter*1.3
        # button
        s.anims[id(s.edit_button)]['window'] = Animate(
            s.edit_button,
            duration=butter,
            attrs={
                'position':(start_pos,end_pos),
                'size':(start_size,end_size),
                'textcolor':(
                    (*Color.TEXT,Color.OPACITY),
                    Const.INVISIBLE
                )
            }
        )
        # shadow
        s.anims[id(s.edit_button)]['shadow'] = (
            Animate(
                widget=s.edit_button_shadow,
                attrs={
                    'opacity':(0,Color.OPACITY),
                    'position':(
                        start_pos,
                        s.window_shadow_pos
                    ),
                    'size':(
                        start_size,
                        s.window_shadow_size
                    )
                },
                duration=butter
            )
        )
        # finally
        b = s.sl
        mem = s.memory[id(b)]
        ret = s.make_window_kids(
            mem['event'], edit=mem
        )
        on_back = lambda: (
            callable(ret) and ret(),
            s.toast(Strings.INFO_DISCARDED)
        )
        s.window_on = (s.edit_button,s.edit_window,on_back)

    @clickable
    def key_window(s):
        if not s.sl:
            Eval.SOUND(Const.BAD_SOUND).play()
            s.toast(Strings.ERROR_SELECT_SOMETHING)
            return
        si = s.memory[id(s.sl)]['event']
        if not (keys:=Const.EVENT_KEYS.get(si,())):
            Eval.SOUND(Const.BAD_SOUND).play()
            s.toast(Strings.NO_ACTIONS)
            return
        if s.window_on:
            s.window_back()
        Eval.SOUND(Const.OK_SOUND).play()
        # disable
        bui.buttonwidget(
            s.key_button,
            on_activate_call=Const.DO_NOTHING,
            selectable=False
        )
        # math
        start_pos = s.event_on and s.key_button_pos2 or s.key_button_pos
        end_pos = s.window_pos
        start_size = s.edit_button_size
        end_size = s.window_size
        butter = s.global_butter*1.3
        # button
        s.anims[id(s.key_button)]['window'] = Animate(
            s.key_button,
            duration=butter,
            attrs={
                'position':(start_pos,end_pos),
                'size':(start_size,end_size),
                'textcolor':(
                    (*Color.TEXT,Color.OPACITY),
                    Const.INVISIBLE
                )
            }
        )
        # shadow
        s.anims[id(s.key_button)]['shadow'] = (
            Animate(
                widget=s.key_button_shadow,
                attrs={
                    'opacity':(0,Color.OPACITY),
                    'position':(
                        start_pos,
                        s.window_shadow_pos
                    ),
                    'size':(
                        start_size,
                        s.window_shadow_size
                    )
                },
                duration=butter
            )
        )
        # finally
        ret = s.make_key_kids(
            title=Strings.KEYS_ON.format(
                list(Strings.EVENTS)[si]
            ),
            keys=keys
        )
        on_back = lambda: (
            callable(ret) and ret(),
            s.key_clean()
        )
        s.window_on = (s.key_button,s.key_window,on_back)

    def make_key_kids(s,title,keys):
        s.make_window_default(title=title)
        s.make_key_default(keys)
        s.wrap_window_kids()
        s.animate_window_kids()

    def make_key_default(s,what):
        # math
        x,y = s.window_pos
        sx,sy = s.window_size
        text_push = 15
        delay = 0.35
        cur = s.memory[id(s.sl)]['keys']
        # what scroll
        pos = (s.window_marg-s.window_fix,sy/2+s.window_marg-54)
        size = dx,dy = (150,sy/2-s.window_marg)
        what_scroll = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            border_opacity=Color.OPACITY
        )
        s.window_kids.append((what_scroll,pos,text_push,delay,
            ('size',((dx-130,dy),size))
        ))
        # what root
        what_root = bui.containerwidget(
            parent=what_scroll,
            size=(dx,30*len(what)),
            background=False
        )
        # what texts
        what_texts = []
        top = len(what)*30
        for j,i in enumerate(what,start=1):
            w = bui.textwidget(
                parent=what_root,
                size=(dx,30),
                position=(0,top-j*30),
                color=(*Color.TEXT,Color.OPACITY),
                selectable=True,
                click_activate=True,
                on_activate_call=bui.CallPartial(
                    s.set_act, i
                ),
                text=Strings.ACTIONS[i],
                glow_type=Const.GLOW
            )
            what_texts.append(w)
        # current scroll
        pos = (s.window_marg-s.window_fix,s.window_marg-4)
        size = dx,dy = (150,sy/2-(s.window_marg+50))
        cur_scroll = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            border_opacity=Color.OPACITY
        )
        s.window_kids.append((cur_scroll,pos,text_push,delay,
            ('size',((dx-130,dy),size))
        ))
        # current root
        s.current_key_root = bui.containerwidget(
            parent=cur_scroll,
            size=(dx,30*len(cur)),
            background=False
        )
        # current texts
        s.fresh_current_key_texts()
        # placeholder
        pos = (sx*0.62,sy*0.43)
        t = bui.textwidget(
            parent=s.root,
            text=Strings.ACTION_PLACEHOLDER,
            position=pos,
            color=Const.INVISIBLE,
            h_align=Const.ALIGN,
            v_align=Const.ALIGN
        )
        s.window_kids.append((t,pos,70,delay+0.13,
            ('color',(
                Const.INVISIBLE,
                (*Color.TEXT,Color.OPACITY)
            ))
        ))
        s.key_kids = [(t,0)]
        # finally
        s.window_trash = [what_texts,s.current_key_texts]

    def fresh_current_key_texts(s):
        for _ in s.current_key_root.get_children(): _.delete()
        s.current_key_texts = []
        cur = s.memory[id(s.sl)]['keys']
        top = len(cur)*30
        dx = 150
        for i,g in enumerate(cur.items(),start=1):
            nam,c = g
            w = bui.textwidget(
                parent=s.current_key_root,
                size=(dx,30),
                position=(0,top-i*30),
                color=(*Color.TEXT,Color.OPACITY),
                selectable=True,
                click_activate=True,
                maxwidth=dx-10,
                on_activate_call=bui.CallPartial(
                    s.set_act,
                    c['action'],
                    data=c['data'],
                    nam=nam
                ),
                text=nam,
                glow_type=Const.GLOW
            )
            s.current_key_texts.append(w)

    def key_clean(s):
        for k,_ in s.key_kids:
            if _ == 1:
                k.delete()
                continue
            s.anims[id(k)].reverse(
                on_finish=k.delete
            )
        s.key_kids.clear()

    def set_act(s,i,data=None,nam=''):
        butter = s.global_butter
        s.key_clean()
        # math
        x,y = (
            s.window_pos[0]+150+s.window_marg*2,
            s.window_pos[1]+s.window_marg
        )
        sx,sy = (
            s.window_size[0]-150-s.window_marg,
            s.window_size[1]-54
        )
        had_data = data is not None
        data = data or {}
        # Attribute
        if i == 0:
            tx = Strings.ATTR
            t = bui.textwidget(
                parent=s.root,
                position=(x,y+sy-37-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t,0))
            attr = bui.textwidget(
                parent=s.root,
                position=(x+70,y+sy-37-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80,35),
                allow_clear_button=False,
                description=tx,
                v_align=Const.ALIGN,
                color=(*Color.TEXT,Color.OPACITY),
                text=data.get('attr','')
            )
            s.key_kids.append((attr,1))
            # eval
            tx = Strings.EVAL
            t = bui.textwidget(
                parent=s.root,
                position=(x,y+sy-37*2-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t,0))
            val = bui.textwidget(
                parent=s.root,
                position=(x+70,y+sy-37*2-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80,35),
                allow_clear_button=False,
                description=tx,
                v_align=Const.ALIGN,
                color=(*Color.TEXT,Color.OPACITY),
                text=data.get('eval','')
            )
            s.key_kids.append((val,1))
            # name
            tx = Strings.NAME
            t = bui.textwidget(
                parent=s.root,
                position=(x,y+sy-37*3-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t,0))
            name_inp = bui.textwidget(
                parent=s.root,
                position=(x+70,y+sy-37*3-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80,35),
                allow_clear_button=False,
                description=tx,
                v_align=Const.ALIGN,
                color=(*Color.TEXT,Color.OPACITY),
                text=nam
            )
            s.key_kids.append((name_inp,1))
            # offset
            bx,by = 100,40
            tx = Strings.OFFSET
            t = bui.textwidget(
                parent=s.root,
                position=(x,y+sy-37*4-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t,0))
            time_inp = bui.textwidget(
                parent=s.root,
                position=(x+70,y+sy-37*4-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80,35),
                allow_clear_button=False,
                v_align=Const.ALIGN,
                description=tx,
                color=(*Color.TEXT,Color.OPACITY),
                text=data.get('offset','')
            )
            s.key_kids.append((time_inp,1))
            _old_off = None
            def _off_spy():
                nonlocal _old_off
                if not time_inp.exists():
                    s.off_spy = None
                    return
                o = bui.textwidget(query=time_inp)
                if (
                    o.replace('.','',1).isdigit()
                    and (new:=float(o)) != _old_off
                ):
                    mem = s.memory[id(s.sl)]
                    _old_off = new
                    mem.get('prev_off_wid') and mem['prev_off_wid'].delete()
                    if not (0 <= new <= mem['duration']): return
                    mem['prev_off_wid'] = s.prev_off_wid = bui.imagewidget(
                        parent=s.stamp_hscroll_root,
                        position=(
                            s.magic_x + s.entry_xs_real * (mem['start'] + new) * s.entries_per_sec - s.entry_ys_real/4,
                            s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        ),
                        size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                        texture=Eval.TEXTURE(Const.KEY),
                        color=Color.TEMP,
                        opacity=Color.OPACITY
                    )
                    mem['prev_off'] = new
            s.off_spy = bui.AppTimer(
                0.02, _off_spy, repeat=True
            )
            # done func
            def do_done():
                # collect
                a = bui.textwidget(query=attr)
                ov = bui.textwidget(query=val)
                nam = bui.textwidget(query=name_inp)
                o = bui.textwidget(query=time_inp)
                # verify
                if not a:
                    s.toast(Format.ERROR_EMPTY(Strings.ATTR))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not ov:
                    s.toast(Format.ERROR_EMPTY(Strings.EVAL))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not nam:
                    s.toast(Format.ERROR_EMPTY(Strings.NAME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not o:
                    s.toast(Format.ERROR_EMPTY(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                # evaluate
                try:
                    with bs.get_foreground_host_activity().context:
                        v = eval(ov)
                except Exception as e:
                    s.toast(Format.ERROR(e))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                # finally
                try:
                    offset_val = float(o)
                except ValueError:
                    s.toast(Format.INVALID(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                mem = s.memory[id(s.sl)]
                if not (0 <= offset_val <= mem['duration']):
                    s.toast(Format.OUT_OF_RANGE(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                actual_time = mem['start'] + offset_val
                key_x = s.magic_x + s.entry_xs_real * actual_time * s.entries_per_sec - s.entry_ys_real/4
                key_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                key_wid = bui.imagewidget(
                    parent=s.stamp_hscroll_root,
                    position=(key_x, key_y),
                    size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                    texture=Eval.TEXTURE(Const.KEY),
                    color=Color.WARM,
                    opacity=Color.OPACITY
                )
                if nam in mem['keys']:
                    mem['keys'][nam]['widget'].delete()
                mem['keys'][nam] = {
                    'time':actual_time,
                    'action':i,
                    'data':{
                        'attr':a,
                        'eval':ov,
                        'offset':o,
                        'value':v
                    },
                    'widget':key_wid
                }
                s.toast(
                    had_data and
                    Strings.INFO_EDITED_KEY or
                    Strings.INFO_ADDED_KEY
                )
                s.window_back()
            # done button
            b = bui.buttonwidget(
                parent=s.root,
                position=(x+sx-(bx+5),y),
                size=(bx,by),
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                on_activate_call=do_done,
                enable_sound=False,
                label=Strings.DONE,
                color=Color.BASE,
                textcolor=Const.INVISIBLE
            )
            s.key_kids.append((b,2))
        # Callable
        elif i == 1:
            pass
        # Bubble
        elif i == 2:
            pass
        # Volume
        elif i == 3:
            # volume
            tx = Strings.VALUE
            t = bui.textwidget(
                parent=s.root,
                position=(x,y+sy-37-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t,0))
            vol_inp = bui.textwidget(
                parent=s.root,
                position=(x+70,y+sy-37-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80,35),
                allow_clear_button=False,
                v_align=Const.ALIGN,
                description=tx,
                color=(*Color.TEXT,Color.OPACITY),
                text=str(data.get('volume',''))
            )
            s.key_kids.append((vol_inp,1))
            # offset
            bx,by = 100,40
            tx = Strings.OFFSET
            t = bui.textwidget(
                parent=s.root,
                position=(x,y+sy-37*2-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t,0))
            time_inp = bui.textwidget(
                parent=s.root,
                position=(x+70,y+sy-37*2-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80,35),
                allow_clear_button=False,
                v_align=Const.ALIGN,
                description=tx,
                color=(*Color.TEXT,Color.OPACITY),
                text=str(data.get('offset',''))
            )
            s.key_kids.append((time_inp,1))
            # name
            tx = Strings.NAME
            t = bui.textwidget(
                parent=s.root,
                position=(x,y+sy-37*3-2),
                text=tx,
                maxwidth=60,
                color=Const.INVISIBLE
            )
            s.key_kids.append((t,0))
            name_inp = bui.textwidget(
                parent=s.root,
                position=(x+70,y+sy-37*3-5),
                glow_type=Const.GLOW,
                editable=True,
                size=(sx-80,35),
                allow_clear_button=False,
                v_align=Const.ALIGN,
                description=tx,
                color=(*Color.TEXT,Color.OPACITY),
                text=str(data.get('name',''))
            )
            s.key_kids.append((name_inp,1))
            _old_off = None
            def _off_spy():
                nonlocal _old_off
                if not time_inp.exists():
                    s.off_spy = None
                    return
                o = bui.textwidget(query=time_inp)
                if (
                    o.replace('.','',1).isdigit()
                    and (new:=float(o)) != _old_off
                ):
                    mem = s.memory[id(s.sl)]
                    _old_off = new
                    mem.get('prev_off_wid') and mem['prev_off_wid'].delete()
                    if not (0 <= new <= mem['duration']): return
                    mem['prev_off_wid'] = s.prev_off_wid = bui.imagewidget(
                        parent=s.stamp_hscroll_root,
                        position=(
                            s.magic_x + s.entry_xs_real * (mem['start'] + new) * s.entries_per_sec - s.entry_ys_real/4,
                            s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        ),
                        size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                        texture=Eval.TEXTURE(Const.KEY),
                        color=Color.TEMP,
                        opacity=Color.OPACITY
                    )
                    mem['prev_off'] = new
            s.off_spy = bui.AppTimer(
                0.02, _off_spy, repeat=True
            )
            def do_done():
                v = bui.textwidget(query=vol_inp)
                o = bui.textwidget(query=time_inp)
                nam = bui.textwidget(query=name_inp)
                if not v:
                    s.toast(Format.ERROR_EMPTY(Strings.VALUE))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not o:
                    s.toast(Format.ERROR_EMPTY(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if not nam:
                    s.toast(Format.ERROR_EMPTY(Strings.NAME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                try:
                    volume_val = round(float(v),2)
                except ValueError:
                    s.toast(Format.INVALID(Strings.VOLUME))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                try:
                    offset_val = float(o)
                except ValueError:
                    s.toast(Format.INVALID(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                mem = s.memory[id(s.sl)]
                if not (0 <= offset_val <= mem['duration']):
                    s.toast(Format.OUT_OF_RANGE(Strings.OFFSET))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                actual_time = mem['start'] + offset_val
                key_x = s.magic_x + s.entry_xs_real * actual_time * s.entries_per_sec - s.entry_ys_real/4
                key_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                key_wid = bui.imagewidget(
                    parent=s.stamp_hscroll_root,
                    position=(key_x, key_y),
                    size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                    texture=Eval.TEXTURE(Const.KEY),
                    color=Color.WARM,
                    opacity=Color.OPACITY
                )
                if nam in mem['keys']:
                    mem['keys'][nam]['widget'].delete()
                mem['keys'][nam] = {
                    'time':actual_time,
                    'action':i,
                    'data':{
                        'volume':volume_val,
                        'offset':offset_val,
                        'name':nam
                    },
                    'widget':key_wid
                }
                s.toast(
                    had_data and
                    Strings.INFO_EDITED_KEY or
                    Strings.INFO_ADDED_KEY
                )
                s.window_back()
            # done button
            b = bui.buttonwidget(
                parent=s.root,
                position=(x+sx-(bx+5),y),
                size=(bx,by),
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                on_activate_call=do_done,
                enable_sound=False,
                label=Strings.DONE,
                color=Color.BASE,
                textcolor=Const.INVISIBLE
            )
            s.key_kids.append((b,2))
            # pop button
            def do_pop():
                t = bui.textwidget(query=name_inp)
                mem = s.memory[id(s.sl)]
                if not t:
                    s.toast(Strings.INFO_POP_WHAT)
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                if t not in mem['keys']:
                    s.toast(Format.NOT_FOUND(t))
                    Eval.SOUND(Const.BAD_SOUND).play()
                    return
                mem['keys'].pop(t)['widget'].delete()
                s.toast(Strings.INFO_POPPED(t))
                Eval.SOUND(Const.OK_SOUND).play()
                s.fresh_current_key_texts()
            b = bui.buttonwidget(
                parent=s.root,
                position=(x+(sx/2-145),y),
                size=(bx,by),
                texture=Eval.TEXTURE(Const.SKIN),
                opacity=0,
                on_activate_call=do_pop,
                enable_sound=False,
                label=Strings.POP,
                color=Color.BASE,
                textcolor=Const.INVISIBLE
            )
            s.key_kids.append((b,2))
        # finally
        for k,_ in s.key_kids:
            if _ == 1: continue
            attrs = _ == 2 and {
                'opacity':(0,Color.OPACITY),
                'textcolor':(
                    Const.INVISIBLE,
                    (*Color.TEXT,Color.OPACITY)
                )
            } or {
                'color':(
                    Const.INVISIBLE,
                    (*Color.TEXT,Color.OPACITY)
                )
            }
            s.anims[id(k)] = Animate(
                widget=k,
                attrs=attrs,
                duration=butter
            )

    def wrap(s,what=0,on_finish=None,init=False):
        # global math
        rx,ry = s.real = bui.get_virtual_screen_size()
        sx,sy = s.stamp_size = (rx,150)
        smoly = sy-s.stamp_hack
        # deep y
        old_deep_y = getattr(s,'stamp_deep_y',smoly)
        bigy = old_deep_y > sy
        s.stamp_deep_y = max(s.entry_ys_real*(len(s.memory)+1),smoly)
        # deep x
        smolx = sx-s.stamp_hack
        old_deep_x = getattr(s,'stamp_deep_x',smolx)
        bigx = old_deep_x > sx
        if hasattr(s, 'timeline') and s.timeline:
            s.max_time = s.timeline[-1]['time']
        else:
            # first run?
            times = [
                _['start'] + _['duration']
                for _ in s.memory.values()
            ] or [0]
            s.max_time = max(times)
        rightmost_edge = (
            s.max_time * s.entries_per_sec * s.entry_xs_real
        )
        s.stamp_deep_x = max(rightmost_edge + s.entry_xs_real * 1, smolx)
        # window math
        y_off = 70
        xoff, = Eval.SCALE(25)
        one, = Eval.SCALE(1)
        s.event_kid_ts = one
        s.window_size = wx,wy = 450,300
        s.window_pos = Eval.OFFSET(rx,ry,-wx/2,-wy/2,0,-y_off*2)
        (
            s.window_shadow_pos,
            s.window_shadow_size
        ) = Eval.SHADOW(
            *s.window_pos,
            *s.window_size
        )
        # event math
        s.event_button_size = dx,dy = Eval.SCALE(100,40)
        s.event_kid_off, = Eval.SCALE(40)
        num_events = len(Strings.EVENTS)
        button_height = 40
        spacing = 10
        menu_height = button_height * (num_events + 1) + spacing * (num_events + 2)
        ex,ey = s.event_menu_size = Eval.SCALE(300, menu_height)
        s.event_kid_size = (ex-s.event_kid_off,dy)

        # edit math
        s.edit_button_xoff, = Eval.SCALE(200)
        s.edit_button_xtra, = Eval.SCALE(10)
        s.edit_button_pos = pos = (
            dx+s.edit_button_xtra,
            sy+6.5
        )
        s.edit_button_pos2 = (
            pos[0]+ex-dx,
            pos[1]
        )
        s.edit_button_size = (dx-4,dy-3)
        # key math
        s.key_button_pos = pos = (
            (dx+s.edit_button_xtra)*2,
            sy+6.5
        )
        s.key_button_pos2 = (
            pos[0]+ex-dx,
            pos[1]
        )
        # control math
        s.control_off, = Eval.SCALE(5)
        s.control_size = conx,cony = Eval.SCALE(50,50)
        s.control_pos = lambda i:(
            sx-conx*(i+1)-s.control_off*i-2,sy+s.control_off
        )
        # tool math
        s.tool_off, = Eval.SCALE(5)
        s.tool_size = tx,ty = Eval.SCALE(50,50)
        s.tool_pos = lambda i:(
            sx-tx*(i+1)-s.tool_off*i-2,sy+s.tool_off
        )
        # stupid
        if not isinstance(what,list): what = [what]
        yes = 0 in what
        # main stuff
        if yes or 1 in what:
            # root
            bui.containerwidget(
                s.root,
                size=s.stamp_size,
                stack_offset=Eval.OFFSET(-rx,-ry,sx/2,sy/2)
            )
            # toast (applied on animation)
            s.toast_position = (sx/2,sy+10)
            # stamp background
            bui.imagewidget(s.stamp_bg,size=s.stamp_size)
            # square math
            bx, = Eval.SCALE(55)
            px1,_ = Eval.OFFSET(
                rx, ry, *bui.get_special_widget(
                    'menu_button'
                ).get_screen_space_center(), bx, bx
            )
            # triangle math
            px2,py = Eval.OFFSET(
                rx, ry, *bui.get_special_widget(
                    'squad_button'
                ).get_screen_space_center(), bx, bx
            )
            # square
            bui.buttonwidget(
                s.square,
                position=(px1,py),
                size=(bx,bx),
                text_scale=one
            )
            # triangle
            bui.buttonwidget(
                s.triangle,
                position=(px2,py),
                size=(bx,bx),
                text_scale=one
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
            if bigy or bigx:
                butter = s.global_butter/2
                # stamp scroll root
                s.anims[id(s.stamp_scroll_root)] = Animate(
                    widget=s.stamp_scroll_root,
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
                    attrs={
                        'size':(
                            (old_deep_x,old_deep_y),
                            (s.stamp_deep_x,s.stamp_deep_y)
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
                    size=(s.stamp_deep_x,s.stamp_deep_y)
                )
                if callable(on_finish): on_finish()
        # stamp
        if yes or 3 in what:
            if not init: s.wrap_timeline()
        # event
        if yes or 4 in what:
            # event button background
            dx,dy = (
                s.event_on and
                s.event_menu_size or
                s.event_button_size
            )
            bui.imagewidget(
                s.event_root,
                size=(dx,dy),
                position=(0,sy+5)
            )
            if s.event_on:
                a = s.anims[id(s.event_root)].attrs_end
                a['size'] = s.event_menu_size
                a = s.anims[id(s.event_root)].attrs_start
                a['size'] = s.event_button_size
                a = s.anims[id(s.event_root)].attrs_current
                a['size'] = s.event_menu_size
            # event button
            bui.buttonwidget(
                s.event_button,
                size=s.event_button_size,
                position=(0,sy+5),
                text_scale=one
            )
            # event kids
            s.event_top = sy+ey+5
            s.ev_mult = s.event_button_size[1]+Eval.SCALE(10)[0]
            s.ev_x, = Eval.SCALE(20)
            for i,g in enumerate(s.event_kids.items(),start=1):
                kid,dat = g
                win = kid in s.window_on
                pos = (s.ev_x,s.event_top-s.ev_mult*i)
                size = s.event_kid_size
                bui.buttonwidget(
                    kid,
                    position=(
                        win and s.window_pos
                        or pos
                    ),
                    size=(
                        win and s.window_size
                        or size
                    ),
                    text_scale=one
                )
                bui.imagewidget(
                    dat['shadow'],
                    position=(
                        win and s.window_shadow_pos
                        or pos
                    ),
                    size=(
                        win and s.window_shadow_size
                        or size
                    )
                )
                if win:
                    a = s.anims[id(kid)]['window'].attrs_end
                    a['position'] = s.window_pos
                    a['size'] = s.window_size
                    a = s.anims[id(kid)]['window'].attrs_start
                    a['position'] = pos
                    a['size'] = size
                    a = s.anims[id(kid)]['window'].attrs_current
                    a['position'] = s.window_pos
                    a['size'] = s.window_size
                    a = s.anims[id(kid)]['shadow'].attrs_end
                    a['position'] = s.window_shadow_pos
                    a['size'] = s.window_shadow_size
                    a = s.anims[id(kid)]['shadow'].attrs_start
                    a['position'] = pos
                    a['size'] = size
                    a = s.anims[id(kid)]['shadow'].attrs_current
                    a['position'] = s.window_shadow_pos
                    a['size'] = s.window_shadow_size
        # edit
        if yes or 5 in what:
            # edit button
            win = s.edit_button in s.window_on
            pos = (
                s.event_on and
                s.edit_button_pos2 or
                s.edit_button_pos
            )
            size = s.edit_button_size
            bui.buttonwidget(
                s.edit_button,
                size=(
                    win and s.window_size or
                    s.edit_button_size
                ),
                position=(
                    win and s.window_pos
                    or pos
                ),
                text_scale=one
            )
            if win:
                a = s.anims[id(s.edit_button)]['window'].attrs_start
                a['position'] = pos
                a['size'] = size
                a = s.anims[id(s.edit_button)]['shadow'].attrs_start
                a['position'] = pos
                a['size'] = size
        # key
        if yes or 6 in what:
            # key button
            win = s.key_button in s.window_on
            pos = (
                s.event_on and
                s.key_button_pos2 or
                s.key_button_pos
            )
            size = s.edit_button_size
            bui.buttonwidget(
                s.key_button,
                size=(
                    win and s.window_size or
                    s.edit_button_size
                ),
                position=(
                    win and s.window_pos
                    or pos
                ),
                text_scale=one
            )
            if win:
                a = s.anims[id(s.key_button)]['window'].attrs_start
                a['position'] = pos
                a['size'] = size
                a = s.anims[id(s.key_button)]['shadow'].attrs_start
                a['position'] = pos
                a['size'] = size
        # controls
        if yes or 7 in what:
            for i,b in enumerate(s.controls):
                bui.buttonwidget(
                    b,
                    size=(
                        (0,0) if init or not
                        s.controls_shown else
                        s.control_size
                    ),
                    position=s.control_pos(i),
                    text_scale=one
                )
        # tools
        if yes or 8 in what:
            for i,b in enumerate(s.tools):
                bui.buttonwidget(
                    b,
                    size=init and (0,0) or s.tool_size,
                    position=s.tool_pos(i),
                    text_scale=one
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

    def kill(s,on_kill=None):
        def finish():
            callable(on_kill) and on_kill()
            s.hard_cleanup()
        s.animate_out(
            on_finish=finish
        )
        s.ui_on = False
        s.ui_clickable = False

    def hard_cleanup(s):
        for attr in s.__dict__.copy():
            isinstance(attr,list) and attr.clear()
            delattr(s,attr)

    def make_menu(s):
        # menu background
        s.menu_bg = bui.imagewidget(
            parent=s.root,
            opacity=0,
            color=Color.BASE,
            texture=Eval.TEXTURE(Const.SKIN)
        )
        # menu kids
        s.menu_kids = []
        for t in Strings.MENUS:
            w = bui.buttonwidget(
                parent=s.root,
                enable_sound=False,
                label=t,
                size=(0,0),
                opacity=0,
                textcolor=Const.INVISIBLE,
                color=Color.BASE,
                texture=Eval.TEXTURE(Const.SKIN)
            )
            s.menu_kids.append(w)

    def complete_all(s):
        for widget_id, anim_dict in s.anims.items():
            if isinstance(anim_dict,dict):
                for anim in list(anim_dict.values()):
                    anim.complete()
            else: anim_dict.complete()

    def wrap_all(s,autofix=True,init=False):
        s.complete_all()
        s.wrap(init=init)
        s.wrap_menu()
        s.wrap_window_kids()
        # ballistica bug
        autofix and bui.apptimer(
            Const.BA_LAG, bui.CallPartial(
            s.wrap_all, autofix=False
        ))

    def wrap_menu(s):
        # math
        rx,ry = bui.get_virtual_screen_size()
        sx,sy = s.menu_size = Eval.SCALE(240,220)
        s.menu_start_size = (sx*0.8,sy*0.8)
        s.menu_yoff, = Eval.SCALE(62)
        s.menu_marg, = Eval.SCALE(10)
        x,y = s.menu_pos = rx-sx+2,ry-sy-s.menu_yoff
        s.menu_start_pos = (
            rx-s.menu_start_size[0],
            ry-s.menu_yoff-s.menu_start_size[1]
        )
        bx = sx-s.menu_marg*4
        by, = Eval.SCALE(40)
        one, = Eval.SCALE(1)
        s.menu_kid_size = bx,by
        s.menu_kid_start_size = (bx/2,by)
        s.menu_button_xp = x+s.menu_marg*2
        s.menu_kid_yp = lambda i: (
            y+s.menu_marg*1.5+(by+s.menu_marg)*i
        )
        s.menu_kid_start_pos = lambda i:(
            s.menu_button_xp+bx/2,
            s.menu_kid_yp(i)
        )
        s.menu_kid_pos = lambda i:(
            s.menu_button_xp,
            s.menu_kid_yp(i)
        )
        # menu background
        bui.imagewidget(
            s.menu_bg,
            position=s.menu_pos,
            size=s.menu_size
        )
        if s.menu_on:
            a = s.anims[id(s.menu_bg)].attrs_start
            a['size'] = s.menu_start_size
            a['position'] = s.menu_start_pos
            a = s.anims[id(s.menu_bg)].attrs_end
            a['size'] = s.menu_size
            a['position'] = s.menu_pos
            a = s.anims[id(s.menu_bg)].attrs_current
            a['size'] = s.menu_size
            a['position'] = s.menu_pos
        # menu kids
        for i,kid in enumerate(s.menu_kids):
            bui.buttonwidget(
                kid,
                size=(bx,by),
                position=(
                    s.menu_button_xp,
                    y+s.menu_marg*1.5+(by+s.menu_marg)*i
                ),
                text_scale=one
            )
            if s.menu_on:
                a = s.anims[id(kid)].attrs_start
                a['size'] = s.menu_kid_start_size
                a['position'] = s.menu_kid_start_pos(i)
                a = s.anims[id(kid)].attrs_current
                a['size'] = s.menu_kid_size
                a['position'] = s.menu_kid_pos(i)
                a = s.anims[id(kid)].attrs_end
                a['size'] = s.menu_kid_size
                a['position'] = s.menu_kid_pos(i)

    def toggle_menu(s):
        Eval.SOUND(Const.OK_SOUND).play()
        delay = 0.1
        butter = s.global_butter*0.7
        if s.menu_on:
            s.menu_on = False
            # menu background
            anim = s.anims[id(s.menu_bg)]
            s.anims[id(s.menu_bg)] = anim.reverse(
                duration=butter
            )
            # event kids
            for i,kid in enumerate(s.menu_kids):
                anim = s.anims[id(kid)]
                s.anims[id(kid)] = anim.reverse(
                    duration=butter*0.7
                )
                # disable
                bui.buttonwidget(
                    kid, on_activate_call=Const.DO_NOTHING
                )
            return
        s.menu_on = True
        # menu background
        if (anim:=s.anims[id(s.menu_bg)]):
            anim.cancel()
        s.anims[id(s.menu_bg)] = Animate(
            widget=s.menu_bg,

            duration=butter,
            attrs={
                'opacity':(0,Color.OPACITY),
                'position':(
                    s.menu_start_pos,
                    s.menu_pos
                ),
                'size':(
                    s.menu_start_size,
                    s.menu_size
                )
            }
        )
        # menu action
        def menu_action(i):
            Eval.SOUND(Const.OK_SOUND).play()
            # save & exit
            if i == 0:
                s.toast(Strings.BYE)
                s.toggle_menu()
                s.kill(
                    on_kill=bui.CallPartial(
                        bui.app.classic.return_to_main_menu_session_gracefully,
                        reset_ui=False
                    )
                )
            # load seed
            if i == 1: pass
            # save seed
            if i == 2: pass
            # toggle editor
            if i == 3:
                s.toggle_ui()
                s.toggle_menu()
        # menu kids
        for i,kid in enumerate(s.menu_kids):
            if (anim:=s.anims[id(kid)]):
                anim.cancel()
            s.anims[id(kid)] = Animate(
                widget=kid,

                delay=delay+0.08-0.03*i,
                duration=butter,
                attrs={
                    'size':(
                        s.menu_kid_start_size,
                        s.menu_kid_size
                    ),
                    'opacity':(0,Color.OPACITY),
                    'textcolor':(
                        Const.INVISIBLE,
                        (*Color.TEXT,Color.OPACITY)
                    ),
                    'position':(
                        s.menu_kid_start_pos(i),
                        s.menu_kid_pos(i)
                    )
                }
            )
            # enable
            bui.buttonwidget(
                kid, on_activate_call=bui.CallPartial(
                    menu_action, i
                )
            )

    @clickable
    def toggle_event(s):
        if s.window_on:
            s.window_back()
            return
        Eval.SOUND(Const.OK_SOUND).play()

        # push everything
        def push():
            # edit button
            w = s.edit_button
            ex,ey = s.edit_button_pos
            start,end = s.edit_button_pos, s.edit_button_pos2
            if (anim:=s.anims[id(w)].get('push',None)):
                anim.cancel()
                start_pos = anim.attrs_current['position']
            else: start_pos = s.event_on and end or start
            end_pos = s.event_on and start or end
            s.anims[id(w)]['push'] = Animate(
                widget=w,
                attrs={
                    'position':(start_pos,end_pos)
                },
                duration=s.global_butter,
                delay=s.event_on and 0.07 or 0
            )
            # key button
            w = s.key_button
            ex,ey = s.key_button_pos
            start,end = s.key_button_pos, s.key_button_pos2
            if (anim:=s.anims[id(w)].get('push',None)):
                anim.cancel()
                start_pos = anim.attrs_current['position']
            else: start_pos = s.event_on and end or start
            end_pos = s.event_on and start or end
            s.anims[id(w)]['push'] = Animate(
                widget=w,
                attrs={
                    'position':(start_pos,end_pos)
                },
                duration=s.global_butter,
                delay=s.event_on and 0.07 or 0
            )
        push()
        dur = s.global_butter*1.5
        old_anim = s.anims.get(id(s.event_root),None)
        if s.event_on:
            s.event_on = False
            bui.buttonwidget(s.event_button, label=Strings.EVENT_BUTTON_OFF)

            s.anims[id(s.event_root)] = old_anim.reverse(
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
                    on_activate_call=Const.DO_NOTHING,
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

        # animate parent first (event root)
        if old_anim: old_anim.cancel()
        s.anims[id(s.event_root)] = Animate(
            widget=s.event_root,

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
                    attrs={
                        'opacity': (0, Color.OPACITY),
                        'textcolor': (
                            Const.INVISIBLE,
                            (*Color.TEXT, Color.OPACITY)
                        ),
                        'size': ((mx * start_width_ratio, dy), s.event_kid_size)
                    },
                    duration=child_duration,
                    delay=child_delay + stagger
                )
            )
            # enable
            bui.buttonwidget(
                b,
                on_activate_call=bui.CallPartial(
                    s.event_window,i
                ),
                position=(
                    s.ev_x,
                    s.event_top-s.ev_mult*(i+1)
                )
            )

    @clickable
    def event_window(s,i,edit={},load=False):
        if getattr(s,'making_window_kids',False):
            s.toast(Strings.INFO_SLOW_DOWN)
            Eval.SOUND(Const.BAD_SOUND).play()
            return
        if s.window_on: s.window_back()
        else: Eval.SOUND(Const.OK_SOUND).play()
        # disable
        b = list(s.event_kids)[i]
        call = bui.CallPartial(s.event_window,i)
        s.window_on = [b,call,None]
        bui.buttonwidget(
            b,
            on_activate_call=Const.DO_NOTHING,
            selectable=False
        )
        # backup
        s.event_kid_pos = (s.ev_x,s.event_top-s.ev_mult*(i+1))
        s.last_window_i = i
        # math
        sx,sy = s.window_size
        dx,dy = s.event_kid_size
        butter = 0.5
        # animate
        s.anims[id(b)]['window'] = (
            Animate(
                widget=b,

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
        # make ui
        s.window_on[2] = s.make_window_kids(i,edit=edit,load=load)

    def make_window_kids(s,i,edit={},load=False):
        s.making_window_kids = True
        s.make_window_default(
            title=(
                edit and not load and Strings.EDIT.format(
                    edit['data']['name']
                ) or list(Strings.EVENTS.values())[i]
            )
        )
        func = (
            i == 0 and s.make_node_window or
            i == 1 and s.make_camera_window or
            i == 2 and s.make_sound_window or
            i == 3 and s.make_fx_window or
            i == 4 and s.make_map_window or
            i == 5 and s.make_preset_window or
            (lambda *a,**k:s.toast(Strings.COMING_SOON))
        )
        wait = 0
        fin = lambda: (
            s.wrap_window_kids(),
            s.animate_window_kids(extra_delay=-wait),
            setattr(s,'making_window_kids',False)
        )
        r = func(edit,load)
        if isinstance(r,tuple):
            wait,r = r
            bui.apptimer(wait,fin)
        else: fin()
        return r

    def animate_window_kids(s,extra_delay=0):
        x,y = s.window_pos
        # animate all
        for _,g in enumerate(s.window_kids):
            w,pos,off,delay,*extra = g
            px,py = pos
            extra = dict(extra)
            # default
            attrs = {
                'position':(
                    (x+px-off,y+py),
                    (x+px,y+py)
                ),
                **extra
            }
            # widget based
            ty = w.get_widget_type()
            if ty in ['button','checkbox']:
                attrs.update({
                    'textcolor':(
                        Const.INVISIBLE,
                        (*Color.TEXT,Color.OPACITY)
                    )
                })
            if ty in ['text']:
                attrs.update({
                    'color':(
                        Const.INVISIBLE,
                        (*Color.TEXT,Color.OPACITY)
                    )
                })
            if ty in ['image','button']:
                attrs.update({
                    'opacity':(0,Color.OPACITY)
                })
            # animate
            s.anims[id(w)] = Animate(
                widget=w,
                attrs=attrs,
                duration=0.18,
                delay=delay+extra_delay
            )

    def wrap_window_kids(s):
        x,y = s.window_pos
        for kid in s.window_kids:
            w,p = kid[0:2]
            px,py = p
            Eval.WIDGET(w)(w,position=(x+px,y+py))

    def make_window_default(s,title):
        x,y = s.window_pos
        sx,sy = s.window_size
        def bye():
            s.window_clean()
            s.window_back()
        s.window_marg = 5
        s.window_fix = 8
        dx,dy = 35,35

        pos = (s.window_marg-s.window_fix,sy-dy-s.window_marg)
        back = bui.buttonwidget(
            parent=s.root,
            size=(dx,dy),
            enable_sound=False,
            label=Eval.CHAR(Const.BACK),
            on_activate_call=bye,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            opacity=0
        )
        s.window_kids.append((back,pos,50,0.35))

        pos = (sx/2-s.window_marg*4,sy-s.window_marg-32.5)
        w = bui.textwidget(
            parent=s.root,
            text=title,
            color=Const.INVISIBLE,
            h_align=Const.ALIGN,
            v_align=Const.ALIGN,
            maxwidth=sx-s.window_marg*3-dx
        )
        s.window_kids.append((w,pos,50,0.35))

    def add_entry(s,final,smol=False):
        # setup
        nam = final['name']
        end_size = smol and (
            s.entry_ys_real,
            s.entry_ys_real - s.magic_y
        ) or (
            s.entry_xs_real * (
                s.entries_per_sec *
                s.object_duration
            )*s.magic_right,
            s.entry_ys_real-s.magic_y
        )
        # make
        btn = bui.buttonwidget(
            parent=s.stamp_hscroll_root,
            texture=Eval.TEXTURE(Const.SKIN),
            label=nam,
            textcolor=Const.INVISIBLE,
            color=Color.BASE,
            opacity=0,
            enable_sound=False,
            size=end_size,
            button_type='square'
        )
        bui.buttonwidget(
            btn,
            on_activate_call=bui.CallPartial(
                s.select, btn
            )
        )
        s.stamp_kids.append(btn)
        # memory
        s.memory[id(btn)] = {
            'order':len(s.memory),
            'event':s.last_window_i,
            'data':final,
            'duration':s.object_duration/(smol and s.entries_per_sec or 1),
            'start':0.0,
            'keys':{},
            'smol':smol
        }
        s.build_timeline()
        # push
        def push():
            for i,kid in enumerate(
                reversed(s.stamp_kids)
            ):
                mem = s.memory[id(kid)]
                width_in_steps = mem['duration'] * s.entries_per_sec
                old_x = s.magic_x + s.entry_xs_real*mem['start']*s.entries_per_sec + (width_in_steps * s.magic_left)
                end_pos = (
                    old_x,
                    s.entry_ys_real*i
                )
                s.anims[kid]['push'] = Animate(
                    widget=kid,

                    attrs={
                        'position':(
                            (old_x,s.entry_ys_real*(i-1)),
                            end_pos
                        )
                    },
                    duration=s.global_butter
                )
            for kid in reversed(s.stamp_kids):
                kid_mem = s.memory[id(kid)]

                # Animate all key widgets for this entry
                for key_data in kid_mem.get('keys', {}).values():
                    if 'widget' in key_data and key_data['widget'].exists():
                        wid = key_data['widget']
                        wid_id = id(wid)
                        key_time = key_data['time']

                        # Calculate new position
                        new_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                        new_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 1)

                        # Get old position (one row down)
                        old_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 2)

                        # Create animation dict if needed
                        if wid_id not in s.anims:
                            s.anims[wid_id] = {}

                        # Animate the key widget
                        s.anims[wid_id]['push'] = Animate(
                            widget=wid,
                            attrs={
                                'position': ((new_x, old_y), (new_x, new_y))
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
            if not s.tools_shown:
                s.show_controls()
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
                ),
                'text_scale':(s.event_kid_ts,1)
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
                    Const.INVISIBLE,
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

    def make_node_window(s,edit=None,load=False):
        # math
        x,y = s.window_pos
        sx,sy = s.window_size
        text_push = 15
        delay = 0.35
        data = edit and edit['data']
        # type text
        pos = (s.window_marg-s.window_fix,sy-88)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.TYPE,
            color=Const.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,delay+0))
        # type input
        pos = (s.window_marg+80-s.window_fix,sy-95)
        size = (150,40)
        type_text = bui.textwidget(
            parent=s.root,
            position=pos,
            editable=True,
            allow_clear_button=False,
            size=(0,0),
            maxwidth=size[0],
            description=Strings.TYPE_HELP,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            glow_type=Const.GLOW,
            text=data and data['type'] or ''
        )
        s.window_kids.append((type_text,pos,text_push,delay+0,
            ('size',((0,size[1]),size))
        ))
        # name text
        pos = (s.window_marg-s.window_fix,sy-133)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.NAME,
            color=Const.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,delay+0.05))
        # name input
        pos = (s.window_marg+80-s.window_fix,sy-140)
        size = (150,40)
        name_text = bui.textwidget(
            parent=s.root,
            position=pos,
            editable=True,
            allow_clear_button=False,
            size=(0,0),
            maxwidth=size[0],
            description=Strings.NODE_NAME_HELP,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            glow_type=Const.GLOW,
            text=(
                data and data['name'] or list(Strings.EVENTS)[0]
            )
        )
        s.window_kids.append((name_text,pos,text_push,delay+0.05,
            ('size',((0,size[1]),size))
        ))
        # separator
        pos = (s.window_marg-s.window_fix,sy-150)
        size = (229,2)
        w = bui.imagewidget(
            parent=s.root,
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            size=(0,0),
            opacity=0,
            color=Color.COLD
        )
        s.window_kids.append((w,pos,text_push,delay+0.1,
            ('size',((0,size[1]),size))
        ))
        # attr text
        pos = (s.window_marg-s.window_fix,sy-193)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.ATTR,
            color=Const.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,delay+0.15))
        # attr input
        pos = (s.window_marg+80-s.window_fix,sy-200)
        size = (150,40)
        attr = bui.textwidget(
            parent=s.root,
            position=pos,
            editable=True,
            allow_clear_button=False,
            size=(0,0),
            maxwidth=size[0],
            description=Strings.NODE_ATTR_HELP,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            glow_type=Const.GLOW
        )
        s.window_kids.append((attr,pos,text_push,delay+0.15,
            ('size',((0,size[1]),size))
        ))
        # eval text
        pos = (s.window_marg-s.window_fix,sy-238)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.EVAL,
            color=Const.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,delay+0.2))
        # eval input
        pos = (s.window_marg+80-s.window_fix,sy-245)
        size = (150,40)
        val = bui.textwidget(
            parent=s.root,
            position=pos,
            editable=True,
            allow_clear_button=False,
            size=(0,0),
            description=Strings.EVAL_HELP,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            maxwidth=size[0],
            glow_type=Const.GLOW
        )
        s.window_kids.append((val,pos,text_push,delay+0.2,
            ('size',((0,size[1]),size))
        ))
        # attr stuff
        so_far = {}
        attr_texts = {}
        bx,by = (215,40)
        butter = s.global_butter*1.3
        text_y = 30
        # attr scroll
        size = dx,dy = (sx/2-s.window_marg*3,sy-s.window_marg*4-51-by)
        pos = px,py = (sx-dx+5,s.window_marg*2+by+5)
        w = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            size=(dx/2,0),
            border_opacity=0
        )
        s.window_kids.append((w,pos,20,delay+0,
            ('size',((0,size[1]),size)),
            ('border_opacity',(0,Color.OPACITY)),
            ('color',(Color.COLD,Color.BASE))
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
                s.toast(Format.ERROR_EMPTY(Strings.ATTR))
                return
            if not v:
                s.toast(Format.ERROR_EMPTY(Strings.EVAL))
                return
            return a,v
        # sync
        sync = lambda i=1: bui.containerwidget(
            attr_root,
            size=(dx,max((len(so_far)+i)*text_y,dy-15))
        )
        # pop func
        def do_pop():
            if not (g:=valid()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            a = g[0]
            if not a in so_far:
                s.toast(Format.NOT_FOUND(a))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            so_far.pop(a)
            _i = list(attr_texts).index(a)
            _w = attr_texts.pop(a)
            if (anim:=s.anims[id(_w)]): anim.cancel()
            # fade
            s.anims[id(_w)] = Animate(
                widget=_w,

                attrs={
                    'color':(
                        (*Color.TEXT,Color.OPACITY),
                        Const.INVISIBLE
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
            sync(0)
        # new kid
        def new_kid(a):
            # make
            w = bui.textwidget(
                parent=attr_root,
                size=(dx,text_y),
                maxwidth=dx-15,
                selectable=True,
                glow_type=Const.GLOW,
                click_activate=True,
                on_activate_call=bui.CallPartial(
                    select, a
                ),
                text=a,
                color=Const.INVISIBLE,
                v_align=Const.ALIGN
            )
            attr_texts[a] = w
            return w
        # animate
        def anim_kid(w,px,py):
            if (anim:=s.anims[id(w)]): anim.cancel()
            s.anims[id(w)] = Animate(
                widget=w,

                attrs={
                    'color':(
                        Const.INVISIBLE,
                        (*Color.TEXT,Color.OPACITY)
                    ),
                    'position':(
                        (px+50,py),
                        (px,py)
                    )
                },
                duration=butter
            )
        # set func
        def do_set():
            if not (g:=valid()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            a,v = g
            # evaluate
            try:
                with bs.get_foreground_host_activity().context:
                    v = eval(v)
            except Exception as e:
                s.toast(Format.ERROR(e))
                return
            # check
            if a in so_far:
                w = attr_texts[a]
                px,py = (0,list(so_far).index(a)*text_y)
                s.toast(Strings.INFO_UPDATED(a))
            else:
                px,py = (0,len(so_far)*text_y)
                w = new_kid(a)
                # finally
                sync()
                s.toast(Strings.INFO_ASSIGNED(a))
            # finally
            anim_kid(w,px,py)
            so_far.update({a:v})
        # pop button
        pos = (s.window_marg+7-s.window_fix,s.window_marg)
        size = bx/2-s.window_marg,by
        w = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.POP,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_pop
        )
        s.window_kids.append((w,pos,50,delay+0.08,
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
            color=Color.BASE,
            enable_sound=False,
            label=Strings.SET,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_set
        )
        s.window_kids.append((w,pos,50,delay+0.08,
            ('size',((0,size[1]),size))
        ))
        def ready():
            # collect
            typ = bui.textwidget(query=type_text)
            nam = bui.textwidget(query=name_text)
            # verify
            if not typ:
                s.toast(Format.ERROR_EMPTY(Strings.TYPE))
                return
            if not nam:
                s.toast(Format.ERROR_EMPTY(Strings.NAME))
                return
            return typ,nam
        # done func
        def do_done():
            if not (g:=ready()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            typ,nam = g
            # construct
            final = {
                'type':typ,
                'name':nam,
                'attrs':so_far
            }
            if edit and not load:
                data.update(final)
                bui.buttonwidget(
                    s.stamp_kids[edit['order']],
                    label=nam
                )
                s.window_back()
                s.toast(Strings.INFO_SAVED)
            else: s.add_entry(final)
        # done button
        pos = (px+8,s.window_marg)
        size = bx,by = (dx-15,40)
        w = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.DONE,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((w,pos,50,delay+0.1,
            ('size',((0,size[1]),size))
        ))
        # finally
        s.window_trash = [attr_texts]
        if data:
            so_far = data['attrs'].copy()
            if so_far:
                for i,a in enumerate(so_far):
                    w = new_kid(a)
                    pos = 0,i*text_y
                    anim_kid(w,*pos)
                sync(0)

    def make_camera_window(s,edit=None,load=False):
        # math
        x,y = s.window_pos
        x += 1
        sx,sy = s.window_size
        bx,by = sx/3-s.window_marg*4,40
        text_push = 15
        delay = 0.35
        off = s.window_marg*5+bx
        yoff = by+s.window_marg
        data = edit and edit['data']

        # state
        prv_on = False
        chks = [True,True,False]
        last_pos = _ba.get_camera_position()
        last_tar = _ba.get_camera_target()
        old_pos = list(last_pos)
        old_tar = list(last_tar)
        virgin = True
        original_manual = False
        current_manual = False

        # preview nodes
        prev_pos_node = None
        prev_tar_node = None

        # manage chks
        def do_chk(i,v):
            chks[i] = v

        # position check
        pos = (s.window_marg-3,by+s.window_marg*5)
        pos_chk = bui.checkboxwidget(
            parent=s.root,
            text=Strings.CAMERA_POSITION_CHECK,
            position=pos,
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            scale=0,
            maxwidth=bx-s.window_marg,
            value=chks[0],
            on_value_change_call=bui.CallPartial(do_chk,0)
        )
        s.window_kids.append((pos_chk,pos,text_push,delay+0.12,
            ('size',((bx/2,by),(bx,by))),
            ('scale',(0,1))
        ))

        # position inputs
        pos_texts = []
        top = yoff*4.5
        for i,o in enumerate(old_pos):
            pos = (s.window_marg-3,top-yoff*i)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                editable=True,
                allow_clear_button=False,
                color=Const.INVISIBLE,
                size=(0,0),
                text=str(round(o,2))
            )
            pos_texts.append(w)
            s.window_kids.append((w,pos,text_push,delay+(0.24-0.06*i),
                ('size',((bx/2,by),(bx,by)))
            ))

        # target check
        pos = (off+s.window_marg*2-2,by+s.window_marg*5)
        tar_chk = bui.checkboxwidget(
            parent=s.root,
            text=Strings.CAMERA_TARGET_CHECK,
            position=pos,
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            scale=0,
            maxwidth=bx-s.window_marg,
            value=chks[1],
            on_value_change_call=bui.CallPartial(do_chk,1)
        )
        s.window_kids.append((tar_chk,pos,text_push,delay+0.12,
            ('size',((bx/2,by),(bx,by))),
            ('scale',(0,1))
        ))

        # target inputs
        target_texts = []
        for i,o in enumerate(old_tar):
            pos = (off+s.window_marg-3,top-yoff*i)
            w = bui.textwidget(
                parent=s.root,
                position=pos,
                editable=True,
                allow_clear_button=False,
                color=Const.INVISIBLE,
                size=(0,0),
                text=str(round(o,2))
            )
            target_texts.append(w)
            s.window_kids.append((w,pos,text_push,delay+(0.24-0.06*i),
                ('size',((bx/2,by),(bx,by)))
            ))

        # manual check
        pos = (off*2+s.window_marg*2-2,by+s.window_marg*5)
        man_chk = bui.checkboxwidget(
            parent=s.root,
            text=Strings.CAMERA_MANUAL_CHECK,
            position=pos,
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            scale=0,
            maxwidth=bx-s.window_marg,
            value=chks[2],
            on_value_change_call=bui.CallPartial(do_chk,2)
        )
        s.window_kids.append((man_chk,pos,text_push,delay+0.12,
            ('size',((bx/2,by),(bx,by))),
            ('scale',(0,1))
        ))

        # collect functions
        def collect_pos():
            nonlocal last_pos
            last_pos = [float(bui.textwidget(query=w) or '0') for w in pos_texts]

        def collect_tar():
            nonlocal last_tar
            last_tar = [float(bui.textwidget(query=w) or '0') for w in target_texts]

        def collect():
            collect_pos()
            collect_tar()

        # kill preview nodes
        def kill_prev():
            nonlocal prev_pos_node, prev_tar_node
            if prev_pos_node and prev_pos_node.exists():
                prev_pos_node.delete()
                prev_pos_node = None
            if prev_tar_node and prev_tar_node.exists():
                prev_tar_node.delete()
                prev_tar_node = None

        # preview tick
        def do_see():
            nonlocal prev_pos_node, prev_tar_node, current_manual

            # only change manual mode if needed
            if chks[2] != current_manual:
                _ba.set_camera_manual(chks[2])
                current_manual = chks[2]

            # apply position
            if chks[0]:
                collect_pos()
                _ba.set_camera_position(*last_pos)

                # update position marker
                if prev_pos_node and prev_pos_node.exists():
                    prev_pos_node.text = bui.charstr(getattr(bui.SpecialChar,Const.PIN_POINT)) + ' ' + Strings.POSITION
                    prev_pos_node.position = last_pos
                else:
                    with bs.get_foreground_host_activity().context:
                        prev_pos_node = bs.newnode(
                            'text',
                            attrs={
                                'text':bui.charstr(getattr(bui.SpecialChar,Const.PIN_POINT)) + ' ' + Strings.POSITION,
                                'position':last_pos,
                                'in_world':True,
                                'scale':0.01,
                                'flatness':1,
                                'color':Color.WARM,
                                'shadow':1.0
                            }
                        )

            # apply target
            if chks[1]:
                collect_tar()
                _ba.set_camera_target(*last_tar)

                # update target marker
                if prev_tar_node and prev_tar_node.exists():
                    prev_tar_node.text = bui.charstr(getattr(bui.SpecialChar,Const.PIN_POINT)) + ' ' + Strings.TARGET
                    prev_tar_node.position = last_tar
                else:
                    with bs.get_foreground_host_activity().context:
                        prev_tar_node = bs.newnode(
                            'text',
                            attrs={
                                'text':bui.charstr(getattr(bui.SpecialChar,Const.PIN_POINT)) + ' ' + Strings.TARGET,
                                'position':last_tar,
                                'in_world':True,
                                'scale':0.01,
                                'flatness':1,
                                'color':Color.TEMP,
                                'shadow':1.0
                            }
                        )

        # preview control
        see_timer = None
        def start_preview():
            nonlocal see_timer, prv_on, virgin, current_manual
            prv_on = True
            virgin = False
            current_manual = chks[2]
            if chks[2]:
                _ba.set_camera_manual(True)
            see_timer = bui.AppTimer(0.02, do_see, repeat=True)

        def stop_preview():
            nonlocal see_timer, prv_on, current_manual
            prv_on = False
            see_timer = None
            kill_prev()

            # only reset manual if we changed it and need to go back to False
            if current_manual:
                _ba.set_camera_manual(False)
                current_manual = False

        # enforce values
        def enforce():
            for w,d in zip(pos_texts,last_pos):
                bui.textwidget(w,text=str(d))
            for w,d in zip(target_texts,last_tar):
                bui.textwidget(w,text=str(d))
            for w,b in zip((pos_chk,tar_chk,man_chk),chks):
                bui.checkboxwidget(w,value=b)

        # XZ controls
        mod = 0
        stp = 1
        def add(*d):
            for i,w in enumerate(mod and target_texts or pos_texts):
                old = bui.textwidget(query=w) or '0'
                z = round(float(old)+d[i]*stp,2)
                bui.textwidget(w,text=str(z))
            collect()

        def action(n):
            nonlocal mod
            if n == 0: add(0,0,1)
            if n == 1: add(-1,0,0)
            if n == 2:
                mod = 0
                s.toast(Strings.INFO_POSITION_MODE)
            if n == 3: add(0,-1,0)
            if n == 4: pass
            if n == 5: add(0,1,0)
            if n == 6: add(0,0,-1)
            if n == 7: add(1,0,0)
            if n == 8:
                mod = 1
                s.toast(Strings.INFO_TARGET_MODE)
            Eval.SOUND(Const.OK_SOUND).play()

        # XZ arrows
        for i in range(3):
            for j in range(3):
                n = i*3+j
                pos = (sx-(by+s.window_marg)*(3-i),(by+s.window_marg+1)*(2.5+j))
                t = Const.CAMERA_TOOLS[n]
                t = len(t) > 1 and Eval.CHAR(t) or t
                w = bui.buttonwidget(
                    parent=s.root,
                    position=pos,
                    size=(0,0),
                    opacity=0,
                    label=t,
                    color=Color.BASE,
                    textcolor=Const.INVISIBLE,
                    texture=Eval.TEXTURE(Const.SKIN),
                    enable_sound=False,
                    repeat=True,
                    on_activate_call=bui.CallPartial(action,n)
                )
                s.window_kids.append((w,pos,text_push,delay+0.15+0.02*n,
                    ('size',((by/2,by),(by,by)))
                ))

        # separator
        pos = (s.window_marg-3,by+s.window_marg*4)
        size = (sx-s.window_marg,2)
        w = bui.imagewidget(
            parent=s.root,
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            size=(0,0),
            opacity=0,
            color=Color.COLD
        )
        s.window_kids.append((w,pos,text_push,delay+0.1,
            ('size',((0,size[1]),size))
        ))

        # reset button
        def do_reset(shut=0):
            Eval.SOUND(Const.OK_SOUND).play()
            shut or s.toast(Strings.INFO_RESETTED)

            if prv_on:
                do_preview(1)
            else:
                nonlocal virgin
                virgin = True
                kill_prev()

            if not shut:
                for i in range(3):
                    bui.textwidget(pos_texts[i],text=str(round(old_pos[i],2)))
                    bui.textwidget(target_texts[i],text=str(round(old_tar[i],2)))

        pos = (s.window_marg,s.window_marg)
        w = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.CAMERA_RESET_BUTTON,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_reset
        )
        s.window_kids.append((w,pos,50,delay+0.23,
            ('size',((bx/2,by),(bx,by)))
        ))

        # preview button
        def do_preview(shut=0):
            nonlocal prv_on
            prv_on = not prv_on
            bui.buttonwidget(
                prv_button,
                label=prv_on and Strings.STOP or Strings.PREVIEW
            )
            shut or (
                s.toast(prv_on and Strings.INFO_PREVIEW_ON or Strings.PREVIEW_OFF) or
                Eval.SOUND(Const.OK_SOUND).play()
            )
            if prv_on:
                start_preview()
            else:
                stop_preview()

        pos = (s.window_marg+off,s.window_marg)
        prv_button = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.PREVIEW,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_preview
        )
        s.window_kids.append((prv_button,pos,50,delay+0.23,
            ('size',((bx/2,by),(bx,by)))
        ))

        # done button
        def do_done():
            collect()
            nam = Strings.CAMERA_ENTRY
            final = {
                'chks':chks,
                'name':nam,
                'position':last_pos,
                'target':last_tar
            }
            Eval.SOUND(Const.OK_SOUND).play()
            if edit and not load:
                data.update(final)
                s.window_back()
                s.toast(Strings.INFO_SAVED)
            else:
                s.add_entry(final)

        pos = (s.window_marg+off*2,s.window_marg)
        w = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.DONE,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((w,pos,50,delay+0.23,
            ('size',((bx/2,by),(bx,by)))
        ))

        # load edit data
        if edit:
            last_pos = data['position']
            last_tar = data['target']
            chks = data['chks']
            original_manual = chks[2]
            enforce()

        # cleanup on window close
        return lambda: (kill_prev(), stop_preview()) if not virgin else kill_prev()

    def make_sound_window(s, edit=None, load=False, wait=0.43):
        s.prv_sound = None
        if wait:
            bui.apptimer(
                wait, bui.CallPartial(
                    s.make_sound_window,
                    edit, wait=False
                )
            )
            return (wait,lambda: s.prv_sound and s.prv_sound.delete())
        # math
        x, y = s.window_pos
        sx, sy = s.window_size
        text_push = 15
        delay = 0.35
        data = edit and edit['data']

        # Sample sound list (will be wired to listdir later)
        sound_files = sorted(listdir(join(Const.BA_DATA,'audio')),reverse=True)

        # State
        current_sound = data and data['file'] or None

        # Helper to format sound name
        def format_name(filename):
            # Remove .ogg extension
            name = filename.replace('.ogg', '')
            # Split camelCase: insert space before capitals
            spaced = sub(r'([a-z])([A-Z])', r'\1 \2', name)
            return spaced.title()

        # Helper to stop current sound
        def stop_current():
            if s.prv_sound:
                s.prv_sound.delete()

        # Sound scroll
        size = dx, dy = (sx/2 - s.window_marg*3, sy - s.window_marg*9 - 55)
        pos = px, py = (s.window_marg - s.window_fix, s.window_marg - s.window_fix + 55)
        sound_scroll = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            size=(dx/2, 0),
            border_opacity=0
        )
        s.window_kids.append((sound_scroll, pos, 20, delay + 0,
            ('size', ((0, size[1]), size)),
            ('border_opacity', (0, Color.OPACITY)),
            ('color', (Color.COLD, Color.BASE))
        ))

        # Sound root
        sound_root = bui.containerwidget(
            parent=sound_scroll,
            background=False
        )

        chks = data.get('chks',[False,False])
        def do_chk(i,v):
            chks[i] = v
        # positional check
        bx, by = 80, 40
        pos = (s.window_marg-8,s.window_marg)
        pos_chk = bui.checkboxwidget(
            parent=s.root,
            text=Strings.EVERYWHERE,
            position=pos,
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            scale=0,
            maxwidth=bx-s.window_marg,
            value=chks[0],
            on_value_change_call=bui.CallPartial(do_chk,0)
        )
        s.window_kids.append((pos_chk,pos,text_push,delay+0.12,
            ('size',((bx/2,by),(bx,by))),
            ('scale',(0,1))
        ))

        # loop check
        bx, by = 80, 40
        pos = (s.window_marg-3+bx+40,s.window_marg)
        loop_chk = bui.checkboxwidget(
            parent=s.root,
            text=Strings.LOOP,
            position=pos,
            color=Color.BASE,
            textcolor=Const.INVISIBLE,
            scale=0,
            maxwidth=bx/2,
            value=chks[1],
            on_value_change_call=bui.CallPartial(do_chk,1)
        )
        s.window_kids.append((loop_chk,pos,text_push,delay+0.12,
            ('size',((bx/2,by),(bx,by))),
            ('scale',(0,1))
        ))

        text_y = 30
        sound_texts = []

        # Populate sound list
        for i, filename in enumerate(sound_files):
            w = bui.textwidget(
                parent=sound_root,
                size=(dx, text_y),
                position=(0, i * text_y),
                maxwidth=dx - 15,
                selectable=True,
                glow_type=Const.GLOW,
                click_activate=True,
                text=filename,
                color=Const.INVISIBLE,
                v_align=Const.ALIGN
            )
            sound_texts.append(w)

        # Set container size
        bui.containerwidget(
            sound_root,
            size=(dx, max(len(sound_files) * text_y, dy - 15))
        )

        # Title text position
        title_pos = (sx/2 + s.window_marg, sy - s.window_marg - 80)
        title_text = bui.textwidget(
            parent=s.root,
            position=title_pos,
            text=current_sound and format_name(current_sound) or Strings.SOUND_PLACEHOLDER,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            maxwidth=sx/2 - s.window_marg*2,
            scale=1.2
        )
        s.window_kids.append((title_text, title_pos, text_push, delay + 0.1))

        # Position inputs (X, Y, Z)
        input_width = (sx/2 - s.window_marg*5) / 3 + 5
        input_height = 35
        input_y = sy - s.window_marg - 150
        labels = ['X', 'Y', 'Z']
        position_inputs = []

        for idx, label in enumerate(labels):
            # Label
            label_pos = (sx/2 + s.window_marg + idx * (input_width + s.window_marg), input_y + input_height)
            label_widget = bui.textwidget(
                parent=s.root,
                position=label_pos,
                text=label,
                color=Const.INVISIBLE,
                scale=0.8
            )
            s.window_kids.append((label_widget, label_pos, text_push, delay + 0.12))

            # Input
            input_pos = (sx/2 + s.window_marg + idx * (input_width + s.window_marg) - 5, input_y)
            input_widget = bui.textwidget(
                parent=s.root,
                position=input_pos,
                editable=True,
                allow_clear_button=False,
                color=Const.INVISIBLE,
                size=(0, 0),
                text=data and str(data.get(label.lower(), 0)) or '0',
                glow_type=Const.GLOW,
                v_align=Const.ALIGN
            )
            position_inputs.append(input_widget)
            s.window_kids.append((input_widget, input_pos, text_push, delay + 0.13,
                ('size', ((input_width/2, input_height), (input_width, input_height)))
            ))

        # Volume input
        vol_label_pos = (sx/2, input_y - 36)
        vol_label = bui.textwidget(
            parent=s.root,
            position=vol_label_pos,
            text='Volume',
            color=Const.INVISIBLE,
            scale=0.8
        )
        s.window_kids.append((vol_label, vol_label_pos, text_push, delay + 0.15))

        vol_input_pos = (sx/2 + s.window_marg + 90, input_y - 40)
        volume_input = bui.textwidget(
            parent=s.root,
            position=vol_input_pos,
            editable=True,
            allow_clear_button=False,
            color=Const.INVISIBLE,
            size=(0, 0),
            text=data and str(data.get('volume', 1.0)) or '1.0',
            glow_type=Const.GLOW,
            v_align=Const.ALIGN
        )
        s.window_kids.append((volume_input, vol_input_pos, text_push, delay + 0.16,
            ('size', ((input_width/2, input_height), (input_width * 1.8, input_height)))
        ))

        # Select sound function
        def select_sound(filename):
            nonlocal current_sound
            stop_current()
            current_sound = filename
            bui.textwidget(title_text, text=format_name(filename))

        # Wire up sound text callbacks
        all_delay = (delay-0.35) + 0.05 + len(sound_files) * 0.01
        for i, (filename, w) in enumerate(zip(sound_files, sound_texts)):
            bui.textwidget(
                w,
                on_activate_call=bui.CallPartial(select_sound, filename)
            )
            # Animate
            butter = s.global_butter
            s.anims[id(w)] = Animate(
                widget=w,
                attrs={
                    'color': (
                        Const.INVISIBLE,
                        (*Color.TEXT, Color.OPACITY)
                    ),
                    'position': (
                        (50, i * text_y),
                        (0, i * text_y)
                    )
                },
                duration=butter,
                delay=all_delay - i * 0.01
            )

        s.window_trash = [sound_texts]

        # Button math
        button_x = sx - (dx + s.window_marg*2)
        button_y = s.window_marg

        # Play button
        def do_play():
            if not current_sound:
                s.toast(Strings.ERROR_NO_SOUND_SELECTED)
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            stop_current()
            # Load and play (getsound needs filename without extension)
            sound_name = current_sound.replace('.ogg', '')
            try: pos = collect_pos()
            except Exception as e:
                s.toast(Strings.ERROR_INVALID.format(Strings.POSITION))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            try:
                vol = float(bui.textwidget(query=volume_input) or '1.0')
            except Exception as e:
                Eval.SOUND(Const.BAD_SOUND).play()
                Format.ERROR(e)
                return
            with bs.get_foreground_host_activity().context:
                s.prv_sound = bs.newnode(
                    'sound',
                    attrs={
                        'sound':bs.getsound(sound_name),
                        'position':pos,
                        'volume':vol,
                        'positional':not chks[0],
                        'loop':chks[1]
                    }
                )

        play_pos = (button_x-5, button_y*3+by)
        play_button = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=play_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Eval.CHAR(Const.PLAY_BUTTON),
            textcolor=Const.INVISIBLE,
            on_activate_call=do_play
        )
        s.window_kids.append((play_button, play_pos, 50, delay + 0.15,
            ('size', ((0, by), (dx/2 - s.window_marg/2, by)))
        ))


        # Stop button
        def do_stop():
            stop_current()

        stop_pos = (button_x+dx/2+s.window_marg*2, button_y*3+by)
        stop_button = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=stop_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Eval.CHAR(Const.PAUSE_BUTTON),
            textcolor=Const.INVISIBLE,
            on_activate_call=do_stop
        )
        s.window_kids.append((stop_button, stop_pos, 50, delay + 0.15,
            ('size', ((0, by), (dx/2 - s.window_marg/2+2, by)))
        ))
        def collect_pos():
            return [
                float(bui.textwidget(query=i) or '0')
                for i in position_inputs
            ]
        # Done button
        def do_done():
            if not current_sound:
                s.toast(Strings.ERROR_NO_SOUND_SELECTED)
                Eval.SOUND(Const.BAD_SOUND).play()
                return

            stop_current()

            # Collect position and volume
            try:
                x_val,y_val,z_val = collect_pos()
            except ValueError:
                s.toast(Strings.ERROR_INVALID.format(Strings.POSITION))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            try:
                vol_val = float(bui.textwidget(query=volume_input) or '1.0')
            except Exception as e:
                Eval.SOUND(Const.BAD_SOUND).play()
                Format.ERROR(e)
                return

            Eval.SOUND(Const.OK_SOUND).play()

            final = {
                'name': format_name(current_sound),
                'file': current_sound,
                'x': x_val,
                'y': y_val,
                'z': z_val,
                'volume': vol_val,
                'chks':chks.copy(),
            }

            if edit and not load:
                data.update(final)
                bui.buttonwidget(
                    s.stamp_kids[edit['order']],
                    label=final['name']
                )
                s.window_back()
                s.toast(Strings.INFO_SAVED)
            else:
                s.add_entry(final)

        done_pos = (sx - (dx + s.window_marg*2), button_y)
        done_button = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=done_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.DONE,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((done_button, done_pos, 50, delay + 0.2,
            ('size', ((0, by), (sx/2 - s.window_marg*2, by)))
        ))

    def make_fx_window(s,edit=None,load=False):
        # math
        x,y = s.window_pos
        sx,sy = s.window_size
        text_push = 15
        delay = 0.35
        data = edit and edit['data']
        # name text
        pos = (s.window_marg-s.window_fix,sy-88)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.NAME,
            color=Const.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,delay+0.05))
        # name input
        pos = (s.window_marg+80-s.window_fix,sy-95)
        size = (150,40)
        name_text = bui.textwidget(
            parent=s.root,
            position=pos,
            editable=True,
            allow_clear_button=False,
            size=(0,0),
            maxwidth=size[0],
            description=Strings.FX_NAME_HELP,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            glow_type=Const.GLOW,
            text=(
                data and data['name'] or list(Strings.EVENTS)[3]
            )
        )
        s.window_kids.append((name_text,pos,text_push,delay+0.05,
            ('size',((0,size[1]),size))
        ))
        # separator
        pos = (s.window_marg-s.window_fix,sy-105)
        size = (229,2)
        w = bui.imagewidget(
            parent=s.root,
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            size=(0,0),
            opacity=0,
            color=Color.COLD
        )
        s.window_kids.append((w,pos,text_push,delay+0.1,
            ('size',((0,size[1]),size))
        ))
        # attr text
        pos = (s.window_marg-s.window_fix,sy-148)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.ATTR,
            color=Const.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,delay+0.15))
        # attr input
        pos = (s.window_marg+80-s.window_fix,sy-155)
        size = (150,40)
        attr = bui.textwidget(
            parent=s.root,
            position=pos,
            editable=True,
            allow_clear_button=False,
            size=(0,0),
            maxwidth=size[0],
            description=Strings.FX_ATTR_HELP,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            glow_type=Const.GLOW
        )
        s.window_kids.append((attr,pos,text_push,delay+0.15,
            ('size',((0,size[1]),size))
        ))
        # eval text
        pos = (s.window_marg-s.window_fix,sy-193)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.EVAL,
            color=Const.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,delay+0.2))
        # eval input
        pos = (s.window_marg+80-s.window_fix,sy-200)
        size = (150,40)
        val = bui.textwidget(
            parent=s.root,
            position=pos,
            editable=True,
            allow_clear_button=False,
            size=(0,0),
            description=Strings.EVAL_HELP,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            maxwidth=size[0],
            glow_type=Const.GLOW
        )
        s.window_kids.append((val,pos,text_push,delay+0.2,
            ('size',((0,size[1]),size))
        ))
        # attr stuff
        so_far = {}
        attr_texts = {}
        bx,by = (215,40)
        butter = s.global_butter*1.3
        text_y = 30
        # attr scroll
        size = dx,dy = (sx/2-s.window_marg*3,sy-s.window_marg*4-51-by)
        pos = px,py = (sx-dx+5,s.window_marg*2+by+5)
        w = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            size=(dx/2,0),
            border_opacity=0
        )
        s.window_kids.append((w,pos,20,delay+0,
            ('size',((0,size[1]),size)),
            ('border_opacity',(0,Color.OPACITY)),
            ('color',(Color.COLD,Color.BASE))
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
                s.toast(Format.ERROR_EMPTY(Strings.ATTR))
                return
            if not v:
                s.toast(Format.ERROR_EMPTY(Strings.EVAL))
                return
            return a,v
        # sync
        sync = lambda i=1: bui.containerwidget(
            attr_root,
            size=(dx,max((len(so_far)+i)*text_y,dy-15))
        )
        # pop func
        def do_pop():
            if not (g:=valid()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            a = g[0]
            if not a in so_far:
                s.toast(Format.NOT_FOUND(a))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            so_far.pop(a)
            _i = list(attr_texts).index(a)
            _w = attr_texts.pop(a)
            if (anim:=s.anims[id(_w)]): anim.cancel()
            # fade
            s.anims[id(_w)] = Animate(
                widget=_w,

                attrs={
                    'color':(
                        (*Color.TEXT,Color.OPACITY),
                        Const.INVISIBLE
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
            sync(0)
        # new kid
        def new_kid(a):
            # make
            w = bui.textwidget(
                parent=attr_root,
                size=(dx,text_y),
                maxwidth=dx-15,
                selectable=True,
                glow_type=Const.GLOW,
                click_activate=True,
                on_activate_call=bui.CallPartial(
                    select, a
                ),
                text=a,
                color=Const.INVISIBLE,
                v_align=Const.ALIGN
            )
            attr_texts[a] = w
            return w
        # animate
        def anim_kid(w,px,py):
            if (anim:=s.anims[id(w)]): anim.cancel()
            s.anims[id(w)] = Animate(
                widget=w,

                attrs={
                    'color':(
                        Const.INVISIBLE,
                        (*Color.TEXT,Color.OPACITY)
                    ),
                    'position':(
                        (px+50,py),
                        (px,py)
                    )
                },
                duration=butter
            )
        # set func
        def do_set():
            if not (g:=valid()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            a,v = g
            # evaluate
            try:
                with bs.get_foreground_host_activity().context:
                    v = eval(v)
            except Exception as e:
                s.toast(Format.ERROR(e))
                return
            # check
            if a in so_far:
                w = attr_texts[a]
                px,py = (0,list(so_far).index(a)*text_y)
                s.toast(Strings.INFO_UPDATED(a))
            else:
                px,py = (0,len(so_far)*text_y)
                w = new_kid(a)
                # finally
                sync()
                s.toast(Strings.INFO_ASSIGNED(a))
            # finally
            anim_kid(w,px,py)
            so_far.update({a:v})
        # pop button
        pos = (s.window_marg+2-s.window_fix,s.window_marg+50)
        size = bx/2-s.window_marg+2,by-10
        w = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.POP,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_pop
        )
        s.window_kids.append((w,pos,50,delay+0.08,
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
            color=Color.BASE,
            enable_sound=False,
            label=Strings.SET,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_set
        )
        s.window_kids.append((w,pos,50,delay+0.08,
            ('size',((0,size[1]),size))
        ))
        def ready():
            # collect
            nam = bui.textwidget(query=name_text)
            # verify
            if not nam:
                s.toast(Format.ERROR_EMPTY(Strings.NAME))
                return
            return nam
        # done func
        def do_done():
            if not (nam:=ready()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            # construct
            final = {
                'name':nam,
                'attrs':so_far
            }
            if edit and not load:
                data.update(final)
                bui.buttonwidget(
                    s.stamp_kids[edit['order']],
                    label=nam
                )
                s.window_back()
                s.toast(Strings.INFO_SAVED)
            else: s.add_entry(final)
        # done button
        pos = (px+8,s.window_marg)
        size = bx,by = (dx-15,40)
        w = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.DONE,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((w,pos,50,delay+0.1,
            ('size',((0,size[1]),size))
        ))
        prv_on = False
        # preview button
        def do_preview():
            nonlocal prv_on
            if prv_on:
                prv_on = False
                bui.buttonwidget(
                    prv_btn,
                    label=Strings.PREVIEW
                )
                s.prv_fx = None
                return
            s.prv_fx = bui.AppTimer(
                0.1, do_prv, repeat=True
            )
            bui.buttonwidget(
                prv_btn,
                label=Strings.STOP
            )
            prv_on = True
        def do_prv():
            try:
                with bs.get_foreground_host_activity().context:
                    bs.emitfx(**so_far)
            except Exception as e:
                if prv_on: do_preview()
                s.toast(Format.ERROR(e))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
        pos = (s.window_marg+7-s.window_fix,s.window_marg)
        size = bx,by = (dx+2,40)
        prv_btn = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.PREVIEW,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_preview
        )
        s.window_kids.append((prv_btn,pos,50,delay+0.1,
            ('size',((0,size[1]),size))
        ))
        # finally
        s.window_trash = [attr_texts]
        if data:
            so_far = data['attrs'].copy()
            if so_far:
                for i,a in enumerate(so_far):
                    w = new_kid(a)
                    pos = 0,i*text_y
                    anim_kid(w,*pos)
                sync(0)
        return lambda: setattr(s,'prv_fx',None)

    def make_map_window(s,edit=None,load=False):
        # math
        x,y = s.window_pos
        sx,sy = s.window_size
        text_push = 15
        delay = 0.35
        data = edit and edit['data']
        _act = bs.get_foreground_host_activity()
        # map text
        pos = (s.window_marg-s.window_fix,sy-88)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=list(Strings.EVENTS)[4],
            color=Const.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,delay+0.05))
        # map input
        pos = (s.window_marg+80-s.window_fix,sy-95)
        size = (150,40)
        old_ma = s.original_map
        map_text = bui.textwidget(
            parent=s.root,
            position=pos,
            editable=True,
            allow_clear_button=False,
            size=(0,0),
            maxwidth=size[0],
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            glow_type=Const.GLOW,
            text=(
                data and data['map'] or old_ma
            )
        )
        s.window_kids.append((map_text,pos,text_push,delay+0.05,
            ('size',((0,size[1]),size))
        ))
        # separator
        pos = (s.window_marg-s.window_fix,sy-105)
        size = (229,2)
        w = bui.imagewidget(
            parent=s.root,
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            size=(0,0),
            opacity=0,
            color=Color.COLD
        )
        s.window_kids.append((w,pos,text_push,delay+0.1,
            ('size',((0,size[1]),size))
        ))
        # attr text
        pos = (s.window_marg-s.window_fix,sy-148)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.ATTR,
            color=Const.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,delay+0.15))
        # attr input
        pos = (s.window_marg+80-s.window_fix,sy-155)
        size = (150,40)
        attr = bui.textwidget(
            parent=s.root,
            position=pos,
            editable=True,
            allow_clear_button=False,
            size=(0,0),
            maxwidth=size[0],
            description=Strings.MAP_ATTR_HELP,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            glow_type=Const.GLOW
        )
        s.window_kids.append((attr,pos,text_push,delay+0.15,
            ('size',((0,size[1]),size))
        ))
        # eval text
        pos = (s.window_marg-s.window_fix,sy-193)
        w = bui.textwidget(
            parent=s.root,
            position=pos,
            text=Strings.EVAL,
            color=Const.INVISIBLE
        )
        s.window_kids.append((w,pos,text_push,delay+0.2))
        # eval input
        pos = (s.window_marg+80-s.window_fix,sy-200)
        size = (150,40)
        val = bui.textwidget(
            parent=s.root,
            position=pos,
            editable=True,
            allow_clear_button=False,
            size=(0,0),
            description=Strings.EVAL_HELP,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            maxwidth=size[0],
            glow_type=Const.GLOW
        )
        s.window_kids.append((val,pos,text_push,delay+0.2,
            ('size',((0,size[1]),size))
        ))
        # attr stuff
        so_far = {}
        attr_texts = {}
        bx,by = (215,40)
        butter = s.global_butter*1.3
        text_y = 30
        # attr scroll
        size = dx,dy = (sx/2-s.window_marg*3,sy-s.window_marg*4-51-by)
        pos = px,py = (sx-dx+5,s.window_marg*2+by+5)
        w = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            size=(dx/2,0),
            border_opacity=0
        )
        s.window_kids.append((w,pos,20,delay+0,
            ('size',((0,size[1]),size)),
            ('border_opacity',(0,Color.OPACITY)),
            ('color',(Color.COLD,Color.BASE))
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
                s.toast(Format.ERROR_EMPTY(Strings.ATTR))
                return
            if not v:
                s.toast(Format.ERROR_EMPTY(Strings.EVAL))
                return
            return a,v
        # sync
        sync = lambda i=1: bui.containerwidget(
            attr_root,
            size=(dx,max((len(so_far)+i)*text_y,dy-15))
        )
        # pop func
        def do_pop():
            if not (g:=valid()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            a = g[0]
            if not a in so_far:
                s.toast(Format.NOT_FOUND(a))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            so_far.pop(a)
            _i = list(attr_texts).index(a)
            _w = attr_texts.pop(a)
            if (anim:=s.anims[id(_w)]): anim.cancel()
            # fade
            s.anims[id(_w)] = Animate(
                widget=_w,
                attrs={
                    'color':(
                        (*Color.TEXT,Color.OPACITY),
                        Const.INVISIBLE
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
            sync(0)
        # new kid
        def new_kid(a):
            # make
            w = bui.textwidget(
                parent=attr_root,
                size=(dx,text_y),
                maxwidth=dx-15,
                selectable=True,
                glow_type=Const.GLOW,
                click_activate=True,
                on_activate_call=bui.CallPartial(
                    select, a
                ),
                text=a,
                color=Const.INVISIBLE,
                v_align=Const.ALIGN
            )
            attr_texts[a] = w
            return w
        # animate
        def anim_kid(w,px,py):
            if (anim:=s.anims[id(w)]): anim.cancel()
            s.anims[id(w)] = Animate(
                widget=w,

                attrs={
                    'color':(
                        Const.INVISIBLE,
                        (*Color.TEXT,Color.OPACITY)
                    ),
                    'position':(
                        (px+50,py),
                        (px,py)
                    )
                },
                duration=butter
            )
        # set func
        def do_set():
            if not (g:=valid()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            a,v = g
            # evaluate
            try:
                with bs.get_foreground_host_activity().context:
                    v = eval(v)
            except Exception as e:
                s.toast(Format.ERROR(e))
                return
            # check
            if a in so_far:
                w = attr_texts[a]
                px,py = (0,list(so_far).index(a)*text_y)
                s.toast(Strings.INFO_UPDATED(a))
            else:
                px,py = (0,len(so_far)*text_y)
                w = new_kid(a)
                # finally
                sync()
                s.toast(Strings.INFO_ASSIGNED(a))
            # finally
            anim_kid(w,px,py)
            so_far.update({a:v})
        # pop button
        pos = (s.window_marg+2-s.window_fix,s.window_marg+50)
        size = bx/2-s.window_marg+2,by-10
        w = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.POP,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_pop
        )
        s.window_kids.append((w,pos,50,delay+0.08,
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
            color=Color.BASE,
            enable_sound=False,
            label=Strings.SET,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_set
        )
        s.window_kids.append((w,pos,50,delay+0.08,
            ('size',((0,size[1]),size))
        ))
        def ready():
            # collect
            ma = bui.textwidget(query=map_text)
            # verify
            if not ma:
                s.toast(Format.ERROR_EMPTY(list(Strings.EVENTS)[4]))
                return
            return ma
        # done func
        def do_done():
            if not (ma:=ready()):
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            Eval.SOUND(Const.OK_SOUND).play()
            # construct
            final = {
                'map':ma,
                'attrs':so_far,
                'name':list(Strings.EVENTS)[4]
            }
            if edit and not load:
                data.update(final)
                s.window_back()
                s.toast(Strings.INFO_SAVED)
            else: s.add_entry(final,smol=True)
        # done button
        pos = (px+8,s.window_marg)
        size = bx,by = (dx-15,40)
        w = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.DONE,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_done
        )
        s.window_kids.append((w,pos,50,delay+0.1,
            ('size',((0,size[1]),size))
        ))
        prv_on = False
        # preview button
        def do_preview():
            nonlocal prv_on
            if prv_on:
                prv_on = False
                bui.buttonwidget(
                    prv_btn,
                    label=Strings.PREVIEW
                )
                s.change_map(old_ma)
                return
            if not (ma:=ready()):
                s.toast(Format.ERROR_EMPTY(list(Strings.EVENTS)[4]))
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            try: s.change_map(ma,extra=so_far)
            except AttributeError:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Format.NOT_FOUND(ma))
                return
            try:
                for key,val in so_far.items():
                    setattr(_act.map.node,key,val)
            except Exception as e:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Format.ERROR(e))
                s.change_map(old_ma)
                return
            Eval.SOUND(Const.OK_SOUND).play()
            bui.buttonwidget(
                prv_btn,
                label=Strings.STOP
            )
            prv_on = True

        pos = (s.window_marg+7-s.window_fix,s.window_marg)
        size = bx,by = (dx+2,40)
        prv_btn = bui.buttonwidget(
            parent=s.root,
            size=(0,0),
            position=pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.PREVIEW,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_preview
        )
        s.window_kids.append((prv_btn,pos,50,delay+0.1,
            ('size',((0,size[1]),size))
        ))
        # finally
        s.window_trash = [attr_texts]
        if data:
            so_far = data['attrs'].copy()
            if so_far:
                for i,a in enumerate(so_far):
                    w = new_kid(a)
                    pos = 0,i*text_y
                    anim_kid(w,*pos)
                sync(0)
        return lambda: s.change_map(old_ma)

    def change_map(s, ma, extra={}):
        from bascenev1lib.gameutils import SharedObjects
        _act = bs.get_foreground_host_activity()
        old_map = _act.map
        cls = getattr(__import__('bascenev1lib').maps, ma.title().replace(' ', ''))
        with _act.context:
            if type(old_map) in _act.preloads:
                del _act.preloads[type(old_map)]
            for attr in dir(old_map):
                if not attr.startswith('_') and attr not in ['node', 'activity', 'getactivity', 'handlemessage', 'on_expire', 'autoretain', 'is_alive', 'exists']:
                    try:
                        val = getattr(old_map, attr)
                        if not callable(val):
                            delattr(old_map, attr)
                    except:
                        pass
            _act.preloads[cls] = cls.on_preload()
            preload = _act.preloads[cls]
            shared = SharedObjects.get()
            temp_map = cls()
            gnode_settings = {}
            for attr in ['tint', 'ambient_color', 'vignette_outer', 'vignette_inner', 'vr_camera_offset', 'vr_near_clip', 'floor_reflection', 'debris_friction', 'debris_kill_height', 'shadow_ortho', 'shadow_offset', 'happy_thoughts_mode']:
                try:
                    gnode_settings[attr] = getattr(_act.globalsnode, attr)
                except:
                    pass
            (temp_map.node and temp_map.node.delete())
            for node in bs.getnodes():
                if node.getnodetype() == 'terrain' and node != old_map.node:
                    try:
                        node.delete()
                    except:
                        pass
            if hasattr(old_map, 'node') and old_map.node:
                old_map.node.mesh = preload.get('mesh') or preload.get('mesh_top') or preload.get('meshes', [None])[0]
                old_map.node.color_texture = preload['tex']
                old_map.node.collision_mesh = preload['collision_mesh']
                if 'ice_material' in preload:
                    old_map.node.materials = [shared.footing_material, preload['ice_material']]
                else:
                    old_map.node.materials = [shared.footing_material]
            for attr in ['bottom', 'floor', 'stands', 'background', 'railing', 'bg_collide', 'stem', 'player_wall', 'bg2', 'node_bottom']:
                if hasattr(old_map, attr):
                    try:
                        getattr(old_map, attr).delete()
                        delattr(old_map, attr)
                    except:
                        pass
            if 'mesh_bottom' in preload or 'bottom_mesh' in preload:
                old_map.bottom = bs.newnode('terrain', attrs={'mesh': preload.get('mesh_bottom') or preload.get('bottom_mesh'), 'lighting': False, 'color_texture': preload['tex']})
            if 'meshes' in preload and len(preload['meshes']) > 1:
                mats = [shared.footing_material, preload['ice_material']] if 'ice_material' in preload else [shared.footing_material]
                old_map.floor = bs.newnode('terrain', attrs={'mesh': preload['meshes'][1], 'color_texture': preload['tex'], 'opacity': 0.92, 'opacity_in_low_or_medium_quality': 1.0, 'materials': mats})
            if 'meshes' in preload and len(preload['meshes']) > 2:
                old_map.stands = bs.newnode('terrain', attrs={'mesh': preload['meshes'][2], 'visible_in_reflections': False, 'color_texture': preload.get('stands_tex', preload['tex'])})
            if 'mesh_bg' in preload or 'bgmesh' in preload:
                old_map.background = bs.newnode('terrain', attrs={'mesh': preload.get('mesh_bg') or preload.get('bgmesh'), 'lighting': False, 'background': True, 'color_texture': preload.get('mesh_bg_tex') or preload.get('bgtex')})
            if 'railing_collision_mesh' in preload or 'bumper_collision_mesh' in preload:
                old_map.railing = bs.newnode('terrain', attrs={'collision_mesh': preload.get('railing_collision_mesh') or preload.get('bumper_collision_mesh'), 'materials': [shared.railing_material], 'bumper': True})
            if 'collide_bg' in preload:
                old_map.bg_collide = bs.newnode('terrain', attrs={'collision_mesh': preload['collide_bg'], 'materials': [shared.footing_material, preload.get('bg_material'), shared.death_material]})
            if 'stem_mesh' in preload:
                old_map.stem = bs.newnode('terrain', attrs={'mesh': preload['stem_mesh'], 'lighting': False, 'color_texture': preload['tex']})
            old_map.preloaddata = preload
            old_map.defs = cls.defs
            old_map.is_hockey = hasattr(cls, 'is_hockey') or cls.name in ['Hockey Stadium', 'Lake Frigid']
            old_map.is_flying = cls.name == 'Happy Thoughts'
            gnode = _act.globalsnode
            aoi_bounds = old_map.get_def_bound_box('area_of_interest_bounds') or (-1, -1, -1, 1, 1, 1)
            gnode.area_of_interest_bounds = aoi_bounds
            map_bounds = old_map.get_def_bound_box('map_bounds') or (-30, -10, -30, 30, 100, 30)
            bs.set_map_bounds(map_bounds)
            for attr, val in gnode_settings.items():
                try:
                    setattr(gnode, attr, val)
                except:
                    pass
            for key, val in extra.items():
                try:
                    if hasattr(old_map, key):
                        setattr(old_map, key, val)
                    elif hasattr(gnode, key):
                        setattr(gnode, key, val)
                except:
                    pass

    def make_preset_window(s,edit=None,load=False):
        # math
        x, y = s.window_pos
        sx, sy = s.window_size
        text_push = 15
        delay = 0.35

        # preset scroll
        size = dx, dy = (sx/2 - s.window_marg*3, sy - s.window_marg*9)
        pos = px, py = (s.window_marg - s.window_fix, s.window_marg - s.window_fix)
        preset_scroll = bui.scrollwidget(
            parent=s.root,
            position=pos,
            color=Color.BASE,
            size=(dx/2, 0),
            border_opacity=0
        )
        s.window_kids.append((preset_scroll, pos, 20, delay + 0,
            ('size', ((0, size[1]), size)),
            ('border_opacity', (0, Color.OPACITY)),
            ('color', (Color.COLD, Color.BASE))
        ))

        # preset root
        preset_root = bui.containerwidget(
            parent=preset_scroll,
            background=False
        )

        # select
        sl = None
        def do_select(pre,nam,dsc):
            nonlocal sl
            sl = pre
            bui.textwidget(
                title_text,
                text=nam
            )
            bui.textwidget(
                desc_text,
                text=dsc
            )

        text_y = 30
        preset_texts = []

        # Populate preset list
        presets = Const.PRESETS()
        rsy = max(len(presets) * text_y, dy - 15)
        for i,g in enumerate(zip(presets,Strings.PRESETS.items()),start=1):
            pre,g = g
            nam,dsc = g
            w = bui.textwidget(
                parent=preset_root,
                size=(dx, text_y),
                position=(0, rsy - i * text_y),
                maxwidth=dx - 15,
                selectable=True,
                glow_type=Const.GLOW,
                click_activate=True,
                text=nam,
                color=(*Color.TEXT,Color.OPACITY),
                v_align=Const.ALIGN,
                on_activate_call=bui.CallPartial(
                    do_select, pre, nam, dsc
                )
            )
            preset_texts.append(w)

        # Set container size
        bui.containerwidget(
            preset_root,
            size=(dx, rsy)
        )

        # title
        title_pos = (sx/2 + s.window_marg, sy - s.window_marg - 80)
        title_text = bui.textwidget(
            parent=s.root,
            position=title_pos,
            text=Strings.PRESET_PLACEHOLDER,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            maxwidth=sx/2 - s.window_marg*2,
            scale=1.2
        )
        s.window_kids.append((title_text, title_pos, text_push, delay + 0.1))

        # desc
        desc_pos = (sx/2 + s.window_marg, sy - s.window_marg - 120)
        desc_text = bui.textwidget(
            parent=s.root,
            position=desc_pos,
            text=Strings.DESCRIPTION_HERE,
            color=Const.INVISIBLE,
            v_align=Const.ALIGN,
            maxwidth=sx/2 - s.window_marg*2,
        )
        s.window_kids.append((desc_text, desc_pos, text_push, delay + 0.1))

        # load button
        by = 40
        def do_load():
            Eval.SOUND(Const.OK_SOUND).play()
            s.event_window(sl[0],edit=sl[1],load=True)
        load_pos = (sx - (dx + s.window_marg*2), s.window_marg)
        load_button = bui.buttonwidget(
            parent=s.root,
            size=(0, 0),
            position=load_pos,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.BASE,
            enable_sound=False,
            label=Strings.LOAD,
            textcolor=Const.INVISIBLE,
            on_activate_call=do_load
        )
        s.window_kids.append((load_button, load_pos, 50, delay + 0.2,
            ('size', ((0, by), (sx/2 - s.window_marg*2, by)))
        ))

        # finally
        s.window_trash = [preset_texts]

    def window_clean(s):
        for w,*_ in s.window_kids:
            s.anims[id(w)].reverse(
                duration=0.1,
                on_finish=w.delete,
                on_cancel=w.delete
            )
        s.window_kids.clear()
        for l in s.window_trash:
            for w in (
                l if isinstance(l,list)
                else l.values()
            ): w.delete()
        s.window_trash.clear()
        getattr(s,'prev_off_wid',None) and s.prev_off_wid.delete()

    def window_back(s,to=None,shadow_to=None,on_fix=None,wait=0,extra={},shadow_extra={},instant={},into_nothing=False,skip=False):
        b,call,on_back = s.window_on
        callable(on_back) and on_back()
        def enable():
            bui.buttonwidget(
                b,
                on_activate_call=call,
                selectable=True
            )
        butter = s.global_butter*1.66
        anim = s.anims[id(b)]['window']
        Eval.SOUND(Const.OK_SOUND).play()
        s.window_clean()
        # capture
        if to:
            last_i = s.last_window_i
            def fix():
                for _ in ['extra','to','shadow']:
                    anim = s.anims[id(b)].pop(_,None)
                    if not anim: continue
                    anim.cancel()
                if s.event_on:
                    ox,oy = (s.ev_x, s.event_top - s.ev_mult * (last_i+1))
                    anim = Animate(
                        widget=b,

                        duration=s.global_butter,
                        attrs={
                            'textcolor':(
                                Const.INVISIBLE,
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
                    textcolor=Const.INVISIBLE,
                    label=list(Strings.EVENTS)[last_i],
                    text_scale=s.event_kid_ts
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

                    duration=butter,
                    on_finish=fix,
                    on_cancel=fix
                )
                s.anims[id(b)]['to'] = anim
                # shadow
                s.anims[id(b)]['shadow'] = Animate(
                    widget=s.event_kids[b]['shadow'],

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
                    duration=wait,
                    attrs=extra,
                    on_cancel=nevermind
                )
            if shadow_extra:
                # shadow
                s.anims[id(b)]['shadow'] = Animate(
                    widget=s.event_kids[b]['shadow'],
                    duration=wait,
                    attrs=shadow_extra
                )
            instant and bui.buttonwidget(
                b, **instant
            )
        else:
            zero = 0.0001
            # fading into nothing?
            if into_nothing:
                anim.attrs_start['textcolor'] = Const.INVISIBLE
            # back to place
            s.anims[id(b)]['window'] = anim.reverse(
                duration=skip and zero or butter
            )
            # shadow too
            anim = s.anims[id(b)]['shadow']
            s.anims[id(b)]['shadow'] = anim.reverse(
                duration=skip and zero or butter
            )
            # enable
            enable()
        # finally
        s.window_on = ()

    def show_controls(s,up=False):
        if s.controls_shown: return
        s.controls_shown = True
        if up:
            for b in s.controls:
                s.anims[id(b)][up].reverse()
        else:
            dx,dy = s.control_size
            sx,sy = s.stamp_size
            start_size = (dx,dy/4)
            for i,b in enumerate(s.controls):
                # instant
                bui.buttonwidget(
                    b, position=s.control_pos(i)
                )
                for a in s.anims[id(b)].values():
                    a.cancel()
                attrs = {
                    'size':(
                        start_size,
                        s.control_size
                    ),
                    'textcolor':(
                        Const.INVISIBLE,
                        (*Color.TEXT,Color.OPACITY)
                    ),
                    'opacity':(0,Color.OPACITY)
                }
                s.anims[id(b)][up] = Animate(
                    widget=b,
                    duration=s.global_butter,
                    attrs=attrs
                )

    @ui_safe
    def hide_controls(s,up=False):
        if not s.controls_shown: return
        s.controls_shown = False
        if up:
            dx,dy = s.control_size
            sx,sy = s.stamp_size
            end_size = (dx,0)
            for i,b in enumerate(s.controls):
                for a in s.anims[id(b)].values():
                    a.cancel()
                px,py = s.control_pos(i)
                attrs = {
                    'size':(
                        s.control_size,
                        end_size
                    ),
                    'textcolor':(
                        (*Color.TEXT,Color.OPACITY),
                        Const.INVISIBLE
                    ),
                    'opacity':(Color.OPACITY,0),
                    'position':(
                        (px,py),
                        (px,py+dy)
                    )
                }
                s.anims[id(b)][up] = Animate(
                    widget=b,
                    duration=s.global_butter,
                    attrs=attrs
                )
        else:
            for b in s.controls:
                s.anims[id(b)][up].reverse()

    def do_control(s,i):
        if (
           not s.ui_on or
           s.tools_shown or
           not s.controls_shown
        ): return
        r = None
        # play
        if i == 0: s.toggle_play()
        # stop
        if i == 1: r = s.stop()
        Eval.SOUND(
            r is None and Const.OK_SOUND
            or Const.BAD_SOUND
        ).play()

    def toggle_play(s):
        if s.playing: s.pause()
        else: s.play()
        s.toast(
            s.playing
            and Strings.INFO_PLAYING
            or Strings.INFO_PAUSED
        )
        s.wrap_controls()

    def wrap_controls(s):
        bui.buttonwidget(
            s.controls[0],
            label=Eval.CHAR(
                Const.CONTROLS[0][s.playing]
            )
        )

    def pause(s):
        s.playing = False
        s.pause_start = perf_counter()
        s.freeze_scene()
        for sound in s.active_sounds:
            sound.volume = 0

    def freeze_scene(s,b=True):
        bs.get_foreground_host_activity().globalsnode.paused = b

    def stop(s,shut=0):
        if not s.play_timer:
            s.toast(Strings.ERROR_NOT_PLAYING)
            return False
        s.playing = False
        s.play_timer = None
        s.ui_clickable = True
        s.kill_playhead()
        s.wrap_play()
        s.wrap_controls()
        for _ in s.active.values(): _.delete()
        s.active.clear()
        for _ in s.active_sounds: _.delete()
        s.active_sounds.clear()
        s.active_timers.clear()
        shut or s.toast(Strings.INFO_FINISHED)
        s.freeze_scene(False)
        s.change_map(s.original_map)
        if s.camera_data:
            s.camera_timer = None
            s.camera_data.clear()
            _ba.set_camera_manual(False)

    def wrap_play(s,init=False):
        s.pause_start = None
        s.play_start = perf_counter() if init else None
        s.play_elapsed = 0
        s.paused_time = 0
        s.timeline_index = 0

    def play(s):
        s.freeze_scene(False)
        s.playing = True
        if s.play_timer:
            s.paused_time += perf_counter() - s.pause_start
            s.pause_start = None
            for sound,vol in s.active_sounds.items():
                setattr(sound,'volume',vol)
            return
        # ui
        s.collapse_all()
        s.ui_clickable = False
        s.make_playhead()
        s.wrap_play(init=True)
        # fire
        s.play_timer = bui.AppTimer(
            0.01, s.do_play, repeat=True
        )
        s.wrap_playhead()

    def do_play(s):
        if not s.playing: return
        s.play_elapsed = (
            s.pause_start - s.play_start - s.paused_time
        ) if s.pause_start else (
            perf_counter() - s.play_start - s.paused_time
        )
        while (
            s.timeline_index < len(s.timeline) and
            s.timeline[s.timeline_index]['time'] <= s.play_elapsed
        ):
            event = s.timeline[s.timeline_index]
            try: s.execute_event(event)
            except Exception as e:
                t = event['memory']['data']['name']
                s.toast(Strings.ERROR_EVENT(t,e))
                s.stop(shut=1)
                Eval.SOUND(Const.BAD_SOUND).play()
                return
            s.timeline_index += 1
        if s.play_elapsed >= s.max_time:
            s.stop()
            return
        s.move_playhead()

    def execute_event(s,e):
        mem = e['memory']
        key = e['btn_id']
        start = e['type'] == 'start'
        what = mem['event']
        data = mem['data']
        call = None

        # node
        if what == 0:
            if start:
                attrs = data['attrs'].copy()
                if data['type'] == 'spaz' and 'position' in data['attrs']:
                    position = attrs.pop('position')
                    call = lambda: n.handlemessage(
                        bs.StandMessage,
                        position
                    )
                with bs.get_foreground_host_activity().context:
                    s.active[key] = n = bs.newnode(
                        type=data['type'],
                        name=data['name'],
                        attrs=attrs
                    )
            else: s.active.pop(key).delete()

        # camera
        if what == 1:
            if start:
                has_pos,has_tar,man = data['chks']
                s.camera_data[key] = (
                    has_pos and data['position'],
                    has_tar and data['target'],
                    man
                )
                # wake up
                if not s.camera_timer:
                    def apply():
                        pos,tar,man = next(
                            reversed(
                                s.camera_data.values()
                            )
                        )
                        if apply.last_man != man:
                            apply.last_man = man
                            _ba.set_camera_manual(man)
                        pos and _ba.set_camera_position(
                            *pos
                        )
                        pos and _ba.set_camera_target(
                            *tar
                        )
                    apply.last_man = False
                    s.camera_timer = bui.AppTimer(
                        0.02, apply, repeat=True
                    )
                    apply() # initial
            else:
                man = s.camera_data.pop(key)[2]
                if not s.camera_data:
                    s.camera_timer = None
                    man and _ba.set_camera_manual(False)
        # volume
        if what == 2:
            if start:
                sound_name = data['file'].replace('.ogg', '')
                position = (data['x'], data['y'], data['z'])
                volume = data['volume']
                with bs.get_foreground_host_activity().context:
                    s.active[key] = n = bs.newnode(
                        'sound',
                        attrs={
                            'position':position,
                            'sound':bs.getsound(sound_name),
                            'volume':volume,
                            'positional':not data['chks'][0],
                            'loop':data['chks'][1]
                        }
                    )
                    s.active_sounds[n] = volume
            else:
                n = s.active.pop(key)
                s.active_sounds.pop(n)
                n.delete()

        # fx
        if what == 3:
            if start:
                at = data['attrs']
                def _emit():
                    with bs.get_foreground_host_activity().context:
                        bs.emitfx(**at)
                s.active_timers[key] = bs.AppTimer(
                    data.get('delay',0.1),
                    _emit, repeat=True
                )
            else:
                s.active_timers.pop(key)

        if what == 4:
            if start:
                s.change_map(data['map'], extra=data['attrs'])

        # Execute keys for this event
        # Keys are executed based on time, not start/end
        if e['type'] == 'start':
            for key_data in mem.get('keys', {}).values():
                key_time = key_data['time']

                # Schedule key execution at the right time
                delay = key_time - s.play_elapsed
                if delay >= 0:
                    bui.apptimer(delay, bui.CallPartial(
                        s.execute_key, key_data, key, what
                    ))

        # finally
        callable(call) and call()

    def execute_key(s, key_data, btn_id, event_type):
        action = key_data['action']

        # Attribute (action 0)
        if action == 0:
            da = key_data['data']
            attr_name, attr_value = da['attr'],da['value']

            # Get the node from active entries
            if btn_id in s.active:
                node = s.active[btn_id]
                if node.exists():
                    try:
                        setattr(node, attr_name, attr_value)
                    except Exception as e:
                        s.toast(Format.ERROR(e))
                        Eval.SOUND(Const.BAD_SOUND).play()

        # Callable (action 1)
        elif action == 1:
            # TODO: Implement callable execution
            pass

        # Bubble (action 2)
        elif action == 2:
            # TODO: Implement bubble text
            pass

        # Volume (action 3)
        elif action == 3:
            da = key_data['data']
            v = da['volume']
            if btn_id in s.active:
                node = s.active[btn_id]
                if node.exists():
                    if not s.paused:
                        try: node.volume = v
                        except Exception as e:
                            s.toast(Format.ERROR(e))
                            Eval.SOUND(Const.BAD_SOUND).play()
                    s.active_sounds[node] = v

    def make_playhead(s):
        s.playhead and s.playhead.delete()
        s.playhead = bui.imagewidget(
            parent=s.stamp_hscroll_root,
            texture=Eval.TEXTURE(Const.SKIN),
            color=Color.WARM,
            opacity=Color.OPACITY
        )

    def move_playhead(s):
        bui.imagewidget(
            s.playhead,
            position=s.playhead_pos(s.play_elapsed)
        )
        bui.containerwidget(
            s.stamp_hscroll_root,
            visible_child=s.playhead
        )

    def wrap_playhead(s):
        s.playhead_pos = lambda i:(
            i*(s.entries_per_sec*s.entry_xs_real)+4,
            -s.stamp_deep_y/2
        )
        s.playhead_size = (2,s.stamp_deep_y*2)
        bui.imagewidget(
            s.playhead,
            size=s.playhead_size
        )
        s.move_playhead()

    def kill_playhead(s,instant=False):
        if instant:
            s.playhead.delete()
            return
        px,py = s.playhead_pos(s.play_elapsed)
        sx,sy = s.playhead_size
        end_sx = sx*100
        s.anims[id(s.playhead)] = Animate(
            widget=s.playhead,
            attrs={
                'size':(
                    (sx,sy),
                    (end_sx,sy)
                ),
                'opacity':(
                    Color.OPACITY*0.6,
                    0
                ),
                'position':(
                    (px,py),
                    (px-end_sx/2,py)
                )
            },
            duration=s.global_butter*2,
            on_finish=s.playhead.delete
        )

    @clickable
    def select(s,b):
        Eval.SOUND(Const.OK_SOUND).play()
        # editing? kill
        if s.window_on and s.window_on[1] in (
            s.edit_window,
            s.key_window
        ): s.window_back()
        sl = b
        # yes
        yes = lambda: bui.buttonwidget(
            b,color=Color.COLD
        )
        # no
        no = lambda: bui.buttonwidget(
            s.sl,color=Color.BASE
        )
        # deselect
        if s.sl == sl:
            no()
            s.hide_tools()
            s.show_controls(up=True)
            s.sl = None
            return
        # clear previous
        if s.sl: no()
        s.hide_controls(up=True)
        s.show_tools()
        s.sl = sl
        yes()

    def show_tools(s):
        if s.tools_shown: return
        s.tools_shown = True
        xs,ys = s.tool_size
        # math
        start_size = (xs,ys/4)
        start_tc = Const.INVISIBLE
        start_op = 0
        for i,b in enumerate(s.tools):
            if (a:=s.anims.get(id(b),None)):
                a.cancel()
            s.anims[id(b)] = Animate(
                widget=b,
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

    @ui_safe
    def hide_tools(s):
        if not s.tools_shown: return
        s.tools_shown = False
        for b in s.tools:
            s.anims[id(b)].reverse(
                duration=s.global_butter,
                on_finish=bui.CallPartial(
                    bui.buttonwidget,
                    b, size=(0,0)
                )
            )

    @clickable
    def do_tool(s,which):
        if not s.tools_shown: return
        if not s.sl: return
        b =s.sl
        mem = s.memory[id(b)]
        if mem.get('smol', False) and which in [2, 3]:
            Eval.SOUND(Const.BAD_SOUND).play()
            s.toast(Strings.ERROR_SMOL_NO_RESIZE)
            return
        new = {}
        scroll_butter = s.global_butter/2
        restamp = lambda:(
            s.wrap(2),
            s.make_timeline(),
            s.wrap_timeline()
        )
        start_size = Eval.ENTRY_SIZE(s,mem)
        start_pos = Eval.ENTRY_POS(s,mem)

        # Helper to animate all key widgets for this entry
        def animate_key_widgets(anim_key, key_old_positions):
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data and key_data['widget'].exists():
                    wid = key_data['widget']
                    wid_id = id(wid)
                    key_time = key_data['time']

                    # Calculate NEW position (after time/order update)
                    new_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                    new_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                    # Get OLD position from stored values
                    start_wid_pos = key_old_positions.get(wid_id, (new_x, new_y))

                    # Check for ongoing animation
                    if wid_id in s.anims and anim_key in s.anims[wid_id]:
                        if (anim := s.anims[wid_id].get(anim_key, None)) and not anim.finished:
                            start_wid_pos = anim.attrs_current['position']
                            anim.cancel()

                    # Create animation dict if needed
                    if wid_id not in s.anims:
                        s.anims[wid_id] = {}

                    # Clear the animation key
                    s.anims[wid_id].pop(anim_key, None)

                    # Create new animation
                    s.anims[wid_id][anim_key] = Animate(
                        widget=wid,
                        attrs={'position': (start_wid_pos, (new_x, new_y))},
                        duration=s.global_butter
                    )

        # move right
        if which == 0:
            for key in [1, 2, 3]:
                if (anim := s.anims[id(b)].get(key, None)):
                    anim.cancel()
                    s.anims[id(b)].pop(key, None)

            if (anim := s.anims[id(b)].get(0, None)) and not anim.finished:
                start_pos = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(0, None)

            mem['start'] += 1/s.entries_per_sec

            # Store old positions - check for ongoing animations!
            key_old_positions = {}
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data and key_data['widget'].exists():
                    wid = key_data['widget']
                    wid_id = id(wid)

                    # Check if animating from LEFT movement (key 1)
                    if wid_id in s.anims and 1 in s.anims[wid_id]:
                        if (anim := s.anims[wid_id].get(1, None)) and not anim.finished:
                            # Use current animation position
                            key_old_positions[wid_id] = anim.attrs_current['position']
                            anim.cancel()
                            s.anims[wid_id].pop(1, None)
                        else:
                            # Calculate from data
                            old_x = s.magic_x + s.entry_xs_real * key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                            old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                            key_old_positions[wid_id] = (old_x, old_y)
                    else:
                        # Calculate from data
                        old_x = s.magic_x + s.entry_xs_real * key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        key_old_positions[wid_id] = (old_x, old_y)

            # Update key times
            for key_data in mem.get('keys', {}).values():
                key_data['time'] += 1/s.entries_per_sec

            end_pos = Eval.ENTRY_POS(s,mem)
            new['position'] = (start_pos, end_pos)

            animate_key_widgets(0, key_old_positions)

            if mem.get('prev_off_wid') and mem['prev_off_wid'].exists():
                wid_id = id(mem['prev_off_wid'])

                for key in [1, 4, 5]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                old_wid_x = s.magic_x + s.entry_xs_real * (mem['start'] - 1/s.entries_per_sec + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                new_wid_x = s.magic_x + s.entry_xs_real * (mem['start'] + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                start_wid_pos = (old_wid_x, wid_y)

                if (anim := s.anims.get(wid_id, {}).get(0, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(0, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][0] = Animate(
                    widget=mem['prev_off_wid'],
                    attrs={
                        'position': (start_wid_pos, (new_wid_x, wid_y))
                    },
                    duration=s.global_butter
                )

            restamp()

        # move left
        if which == 1:
            if mem['start'] < 0.01:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_REACHED_ZERO)
                return

            for key in [0, 2, 3]:
                if (anim := s.anims[id(b)].get(key, None)):
                    anim.cancel()
                    s.anims[id(b)].pop(key, None)

            if (anim := s.anims[id(b)].get(1, None)) and not anim.finished:
                start_pos = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(1, None)

            mem['start'] -= 1/s.entries_per_sec

            # Store old positions - check for ongoing animations!
            key_old_positions = {}
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data and key_data['widget'].exists():
                    wid = key_data['widget']
                    wid_id = id(wid)

                    # Check if animating from RIGHT movement (key 0)
                    if wid_id in s.anims and 0 in s.anims[wid_id]:
                        if (anim := s.anims[wid_id].get(0, None)) and not anim.finished:
                            # Use current animation position
                            key_old_positions[wid_id] = anim.attrs_current['position']
                            anim.cancel()
                            s.anims[wid_id].pop(0, None)
                        else:
                            # Calculate from data
                            old_x = s.magic_x + s.entry_xs_real * key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                            old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                            key_old_positions[wid_id] = (old_x, old_y)
                    else:
                        # Calculate from data
                        old_x = s.magic_x + s.entry_xs_real * key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        key_old_positions[wid_id] = (old_x, old_y)

            # Update key times
            for key_data in mem.get('keys', {}).values():
                key_data['time'] -= 1/s.entries_per_sec

            end_pos = Eval.ENTRY_POS(s, mem)
            new['position'] = (start_pos, end_pos)

            animate_key_widgets(1, key_old_positions)

            if mem.get('prev_off_wid') and mem['prev_off_wid'].exists():
                wid_id = id(mem['prev_off_wid'])

                for key in [0, 4, 5]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                old_wid_x = s.magic_x + s.entry_xs_real * (mem['start'] + 1/s.entries_per_sec + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                new_wid_x = s.magic_x + s.entry_xs_real * (mem['start'] + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                start_wid_pos = (old_wid_x, wid_y)

                if (anim := s.anims.get(wid_id, {}).get(1, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(1, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][1] = Animate(
                    widget=mem['prev_off_wid'],
                    attrs={
                        'position': (start_wid_pos, (new_wid_x, wid_y))
                    },
                    duration=s.global_butter
                )

            restamp()

        # expand
        if which == 2:
            if (shrink := s.anims[id(b)].get(3, None)):
                shrink.cancel()
                s.anims[id(b)].pop(3, None)

            if (anim := s.anims[id(b)].get(2, None)) and not anim.finished:
                start_size = anim.attrs_current['size']
                start_pos = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(2, None)

            mem['duration'] += 1 / s.entries_per_sec

            end_size = Eval.ENTRY_SIZE(s,mem)
            end_pos = Eval.ENTRY_POS(s,mem)

            new['size'] = (start_size, end_size)
            new['position'] = (start_pos, end_pos)

            restamp()

            # Check if we need to show previously hidden keys
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data:
                    key_offset = key_data['time'] - mem['start']
                    if key_offset <= mem['duration'] and not key_data['widget'].exists():
                        key_x = s.magic_x + s.entry_xs_real * (mem['start'] + key_offset) * s.entries_per_sec - s.entry_ys_real/4
                        key_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                        key_data['widget'] = bui.imagewidget(
                            parent=s.stamp_hscroll_root,
                            position=(key_x, key_y),
                            size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                            texture=Eval.TEXTURE(Const.KEY),
                            color=Color.WARM,
                            opacity=Color.OPACITY
                        )

            if mem.get('prev_off') is not None and s.window_on and s.window_on[1] == s.key_window:
                old_duration = mem['duration'] - 1/s.entries_per_sec
                new_duration = mem['duration']

                if old_duration < mem['prev_off'] and new_duration >= mem['prev_off']:
                    wid_x = s.magic_x + s.entry_xs_real * (mem['start'] + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                    wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                    mem['prev_off_wid'] = s.prev_off_wid = bui.imagewidget(
                        parent=s.stamp_hscroll_root,
                        position=(wid_x, wid_y),
                        size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                        texture=Eval.TEXTURE(Const.KEY),
                        color=Color.WARM,
                        opacity=Color.OPACITY
                    )

        # shrink
        if which == 3:
            current_ticks = round(mem['duration'] * s.entries_per_sec)
            if current_ticks <= 1:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_SMALLEST)
                return

            if (expand := s.anims[id(b)].get(2, None)):
                expand.cancel()
                s.anims[id(b)].pop(2, None)

            if (anim := s.anims[id(b)].get(3, None)) and not anim.finished:
                start_size = anim.attrs_current['size']
                start_pos = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(3, None)

            mem['duration'] -= 1 / s.entries_per_sec

            new_width_steps = mem['duration'] * s.entries_per_sec
            end_size = (
                s.entry_xs_real * new_width_steps * s.magic_right,
                s.entry_ys_real - s.magic_y
            )
            end_x = s.magic_x + s.entry_xs_real * mem['start']*s.entries_per_sec + (new_width_steps * s.magic_left)
            end_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
            end_pos = (end_x, end_y)

            new['size'] = (start_size, end_size)
            new['position'] = (start_pos, end_pos)

            restamp()

            # Delete keys that are now out of range
            for key_data in mem.get('keys', {}).values():
                key_time = key_data['time'] - mem['start']
                if key_time > mem['duration']:
                    if 'widget' in key_data and key_data['widget'].exists():
                        key_data['widget'].delete()

            if mem.get('prev_off') is not None and s.window_on and s.window_on[1] == s.key_window:
                old_duration = mem['duration'] + 1/s.entries_per_sec
                new_duration = mem['duration']

                if old_duration >= mem['prev_off'] and new_duration < mem['prev_off']:
                    if mem.get('prev_off_wid') and mem['prev_off_wid'].exists():
                        mem['prev_off_wid'].delete()
                        mem['prev_off_wid'] = None

        # move up
        if which == 4:
            current_list_index = s.stamp_kids.index(b)
            if current_list_index == 0:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_AT_TOP)
                return

            Eval.SOUND(Const.OK_SOUND).play()

            target_list_index = current_list_index - 1
            other_btn = s.stamp_kids[target_list_index]
            other_mem = s.memory[id(other_btn)]

            start_pos_b = Eval.ENTRY_POS(s,mem)
            start_pos_other = Eval.ENTRY_POS(s,other_mem)
            new_y_up = Eval.ENTRY_Y(s,other_mem)
            new_y_down = Eval.ENTRY_Y(s,mem)

            key_old_positions = {}
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data and key_data['widget'].exists():
                    wid = key_data['widget']
                    wid_id = id(wid)

                    found = False
                    # Check for ongoing UP (key 4) OR DOWN (key 5) animation
                    for check_key in [4, 5]:
                        if wid_id in s.anims and check_key in s.anims[wid_id]:
                            if (anim := s.anims[wid_id].get(check_key, None)) and not anim.finished:
                                key_old_positions[wid_id] = anim.attrs_current['position']
                                anim.cancel()
                                s.anims[wid_id].pop(check_key, None)
                                found = True
                                break

                    if not found:
                        # Calculate from data
                        old_x = s.magic_x + s.entry_xs_real * key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        key_old_positions[wid_id] = (old_x, old_y)

            # Same for OTHER entry - check for keys 4 AND 5!
            other_key_old_positions = {}
            for key_data in other_mem.get('keys', {}).values():
                if 'widget' in key_data and key_data['widget'].exists():
                    wid = key_data['widget']
                    wid_id = id(wid)

                    found = False
                    # Check for ongoing UP (key 4) OR DOWN (key 5) animation
                    for check_key in [4, 5]:
                        if wid_id in s.anims and check_key in s.anims[wid_id]:
                            if (anim := s.anims[wid_id].get(check_key, None)) and not anim.finished:
                                other_key_old_positions[wid_id] = anim.attrs_current['position']
                                anim.cancel()
                                s.anims[wid_id].pop(check_key, None)
                                found = True
                                break
                    if not found:
                        # Calculate from data
                        old_x = s.magic_x + s.entry_xs_real * key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)
                        other_key_old_positions[wid_id] = (old_x, old_y)

            mem['order'],other_mem['order'] = other_mem['order'],mem['order']

            s.stamp_kids[current_list_index] = other_btn
            s.stamp_kids[target_list_index] = b

            if (down := s.anims[id(b)].get(5, None)):
                down.cancel()
                s.anims[id(b)].pop(5, None)

            if (anim := s.anims[id(b)].get(4, None)) and not anim.finished:
                start_pos_b = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(4, None)

            end_pos_b = (start_pos_b[0], new_y_up)
            s.anims[id(b)][4] = Animate(
                widget=b,
                duration=s.global_butter,
                attrs={'position': (start_pos_b, end_pos_b)}
            )

            if (down := s.anims[id(other_btn)].get(5, None)):
                down.cancel()
                s.anims[id(other_btn)].pop(5, None)

            if (anim := s.anims[id(other_btn)].get(4, None)) and not anim.finished:
                start_pos_other = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(other_btn)].pop(4, None)

            end_pos_other = (start_pos_other[0], new_y_down)
            s.anims[id(other_btn)][4] = Animate(
                widget=other_btn,
                duration=s.global_butter,
                attrs={'position': (start_pos_other, end_pos_other)}
            )

            # Animate all key widgets for this entry
            animate_key_widgets(4, key_old_positions)

            # Animate keys for the other entry
            for key_data in other_mem.get('keys', {}).values():
                if 'widget' in key_data and key_data['widget'].exists():
                    wid = key_data['widget']
                    wid_id = id(wid)
                    key_time = key_data['time']

                    # Calculate new position based on swapped order
                    new_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                    new_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)

                    # Get OLD position from stored values
                    start_wid_pos = other_key_old_positions.get(wid_id, (new_x, new_y))

                    if wid_id in s.anims and 4 in s.anims[wid_id]:
                        if (anim := s.anims[wid_id].get(4, None)) and not anim.finished:
                            start_wid_pos = anim.attrs_current['position']
                            anim.cancel()

                    if wid_id not in s.anims:
                        s.anims[wid_id] = {}

                    s.anims[wid_id].pop(4, None)

                    s.anims[wid_id][4] = Animate(
                        widget=wid,
                        attrs={'position': (start_wid_pos, (new_x, new_y))},
                        duration=s.global_butter
                    )

            if mem.get('prev_off_wid') and mem['prev_off_wid'].exists():
                wid_id = id(mem['prev_off_wid'])

                for key in [5, 0, 1]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                wid_x = s.magic_x + s.entry_xs_real * (mem['start'] + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                old_wid_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)
                new_wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                start_wid_pos = (wid_x, old_wid_y)

                if (anim := s.anims.get(wid_id, {}).get(4, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(4, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][4] = Animate(
                    widget=mem['prev_off_wid'],
                    attrs={
                        'position': (start_wid_pos, (wid_x, new_wid_y))
                    },
                    duration=s.global_butter
                )

            # Animate prev_off_wid for other entry if it exists
            if other_mem.get('prev_off_wid') and other_mem['prev_off_wid'].exists():
                wid_id = id(other_mem['prev_off_wid'])

                for key in [5, 0, 1]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                wid_x = s.magic_x + s.entry_xs_real * (other_mem['start'] + other_mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                old_wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                new_wid_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)

                start_wid_pos = (wid_x, old_wid_y)

                if (anim := s.anims.get(wid_id, {}).get(4, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(4, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][4] = Animate(
                    widget=other_mem['prev_off_wid'],
                    attrs={
                        'position': (start_wid_pos, (wid_x, new_wid_y))
                    },
                    duration=s.global_butter
                )

        # move down
        if which == 5:
            current_list_index = s.stamp_kids.index(b)
            max_list_index = len(s.stamp_kids) - 1
            if current_list_index == max_list_index:
                Eval.SOUND(Const.BAD_SOUND).play()
                s.toast(Strings.ERROR_AT_BOTTOM)
                return

            Eval.SOUND(Const.OK_SOUND).play()

            target_list_index = current_list_index + 1
            other_btn = s.stamp_kids[target_list_index]
            other_mem = s.memory[id(other_btn)]

            start_pos_b = Eval.ENTRY_POS(s,mem)
            start_pos_other = Eval.ENTRY_POS(s,other_mem)
            new_y_down = Eval.ENTRY_Y(s,other_mem)
            new_y_up = Eval.ENTRY_Y(s,mem)

            key_old_positions = {}
            for key_data in mem.get('keys', {}).values():
                if 'widget' in key_data and key_data['widget'].exists():
                    wid = key_data['widget']
                    wid_id = id(wid)

                    found = False
                    # Check for ongoing UP (key 4) OR DOWN (key 5) animation
                    for check_key in [4, 5]:
                        if wid_id in s.anims and check_key in s.anims[wid_id]:
                            if (anim := s.anims[wid_id].get(check_key, None)) and not anim.finished:
                                key_old_positions[wid_id] = anim.attrs_current['position']
                                anim.cancel()
                                s.anims[wid_id].pop(check_key, None)
                                found = True
                                break

                    if not found:
                        # Calculate from data
                        old_x = s.magic_x + s.entry_xs_real * key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                        key_old_positions[wid_id] = (old_x, old_y)

            # Same for OTHER entry - check for keys 4 AND 5!
            other_key_old_positions = {}
            for key_data in other_mem.get('keys', {}).values():
                if 'widget' in key_data and key_data['widget'].exists():
                    wid = key_data['widget']
                    wid_id = id(wid)

                    found = False
                    # Check for ongoing UP (key 4) OR DOWN (key 5) animation
                    for check_key in [4, 5]:
                        if wid_id in s.anims and check_key in s.anims[wid_id]:
                            if (anim := s.anims[wid_id].get(check_key, None)) and not anim.finished:
                                other_key_old_positions[wid_id] = anim.attrs_current['position']
                                anim.cancel()
                                s.anims[wid_id].pop(check_key, None)
                                found = True
                                break

                    if not found:
                        # Calculate from data
                        old_x = s.magic_x + s.entry_xs_real * key_data['time'] * s.entries_per_sec - s.entry_ys_real/4
                        old_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)
                        other_key_old_positions[wid_id] = (old_x, old_y)

            mem['order'],other_mem['order'] = other_mem['order'],mem['order']

            s.stamp_kids[current_list_index] = other_btn
            s.stamp_kids[target_list_index] = b

            if (up := s.anims[id(b)].get(4, None)):
                up.cancel()
                s.anims[id(b)].pop(4, None)

            if (anim := s.anims[id(b)].get(5, None)) and not anim.finished:
                start_pos_b = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(b)].pop(5, None)

            end_pos_b = (start_pos_b[0], new_y_down)
            s.anims[id(b)][5] = Animate(
                widget=b,
                duration=s.global_butter,
                attrs={'position': (start_pos_b, end_pos_b)}
            )

            if (up := s.anims[id(other_btn)].get(4, None)):
                up.cancel()
                s.anims[id(other_btn)].pop(4, None)

            if (anim := s.anims[id(other_btn)].get(5, None)) and not anim.finished:
                start_pos_other = anim.attrs_current['position']
                anim.cancel()

            s.anims[id(other_btn)].pop(5, None)

            end_pos_other = (start_pos_other[0], new_y_up)
            s.anims[id(other_btn)][5] = Animate(
                widget=other_btn,
                duration=s.global_butter,
                attrs={'position': (start_pos_other, end_pos_other)}
            )

            # Animate all key widgets for this entry
            animate_key_widgets(5, key_old_positions)

            # Animate keys for the other entry
            for key_data in other_mem.get('keys', {}).values():
                if 'widget' in key_data and key_data['widget'].exists():
                    wid = key_data['widget']
                    wid_id = id(wid)
                    key_time = key_data['time']

                    # Calculate new position based on swapped order
                    new_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                    new_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)

                    # Get OLD position from stored values
                    start_wid_pos = other_key_old_positions.get(wid_id, (new_x, new_y))

                    if wid_id in s.anims and 5 in s.anims[wid_id]:
                        if (anim := s.anims[wid_id].get(5, None)) and not anim.finished:
                            start_wid_pos = anim.attrs_current['position']
                            anim.cancel()

                    if wid_id not in s.anims:
                        s.anims[wid_id] = {}

                    s.anims[wid_id].pop(5, None)

                    s.anims[wid_id][5] = Animate(
                        widget=wid,
                        attrs={'position': (start_wid_pos, (new_x, new_y))},
                        duration=s.global_butter
                    )

            if mem.get('prev_off_wid') and mem['prev_off_wid'].exists():
                wid_id = id(mem['prev_off_wid'])

                for key in [4, 0, 1]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                wid_x = s.magic_x + s.entry_xs_real * (mem['start'] + mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                old_wid_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)
                new_wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)

                start_wid_pos = (wid_x, old_wid_y)

                if (anim := s.anims.get(wid_id, {}).get(5, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(5, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][5] = Animate(
                    widget=mem['prev_off_wid'],
                    attrs={
                        'position': (start_wid_pos, (wid_x, new_wid_y))
                    },
                    duration=s.global_butter
                )

            # Animate prev_off_wid for other entry if it exists
            if other_mem.get('prev_off_wid') and other_mem['prev_off_wid'].exists():
                wid_id = id(other_mem['prev_off_wid'])

                for key in [4, 0, 1]:
                    if (anim := s.anims.get(wid_id, {}).get(key, None)):
                        anim.cancel()
                        s.anims[wid_id].pop(key, None)

                wid_x = s.magic_x + s.entry_xs_real * (other_mem['start'] + other_mem['prev_off']) * s.entries_per_sec - s.entry_ys_real/4
                old_wid_y = s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
                new_wid_y = s.entry_ys_real * (len(s.memory) - other_mem['order'] - 1)

                start_wid_pos = (wid_x, old_wid_y)

                if (anim := s.anims.get(wid_id, {}).get(5, None)) and not anim.finished:
                    start_wid_pos = anim.attrs_current['position']
                    anim.cancel()

                if wid_id in s.anims:
                    s.anims[wid_id].pop(5, None)
                else:
                    s.anims[wid_id] = {}

                s.anims[wid_id][5] = Animate(
                    widget=other_mem['prev_off_wid'],
                    attrs={
                        'position': (start_wid_pos, (wid_x, new_wid_y))
                    },
                    duration=s.global_butter
                )

        if which == 6:
            Eval.SOUND(Const.OK_SOUND).play()
            if s.can_do != which:
                s.toast(Strings.CONFIRM_DUPLICATE(
                    mem['data']['name']
                ), extra=2)
                s.can_do = which
                return
            s.on_scroll()

            for kid in s.stamp_kids:
                if (anim := s.anims[id(kid)].get(6, None)):
                    anim.cancel()
                    s.anims[id(kid)].pop(6, None)
                    bui.buttonwidget(
                        kid,
                        opacity=Color.OPACITY,
                        textcolor=(*Color.TEXT, Color.OPACITY)
                    )

            original_data = mem.copy()
            original_event = original_data['event']
            original_duration = original_data['duration']
            original_start = original_data['start']
            original_order = original_data['order']
            node_data = {
                i:(
                    isinstance(j,(list,dict))
                    and j.copy() or j
                ) for i,j in original_data['data'].copy().items()
            }

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
                textcolor=Const.INVISIBLE,
                color=Color.BASE,
                opacity=0,
                enable_sound=False,
                size=size,
                button_type='square'
            )

            original_list_index = s.stamp_kids.index(b)
            s.stamp_kids.insert(original_list_index + 1, btn)

            new_order = original_order + 1

            call = bui.CallPartial(
                s.select, btn
            )
            bui.buttonwidget(btn, on_activate_call=call)

            # Copy keys from original entry
            new_keys = {}
            for nam, key_data in original_data.get('keys', {}).items():
                new_key_data = key_data.copy()
                # Create new widget for duplicated key
                key_time = new_key_data['time']
                key_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                key_y = s.entry_ys_real * (len(s.memory) - new_order)

                new_key_wid = bui.imagewidget(
                    parent=s.stamp_hscroll_root,
                    position=(key_x, key_y),
                    size=(s.entry_ys_real, s.entry_ys_real - s.magic_y),
                    texture=Eval.TEXTURE(Const.KEY),
                    color=Color.WARM,
                    opacity=0
                )
                new_key_data['widget'] = new_key_wid
                new_keys[nam] = new_key_data

            s.memory[id(btn)] = {
                'order': new_order,
                'event': original_event,
                'data': node_data,
                'duration': original_duration,
                'start': original_start,
                'keys': new_keys,
                'prev_off': original_data.get('prev_off'),
                'prev_off_wid': None  # Don't duplicate prev_off_wid as it's only for preview
            }

            for kid in s.stamp_kids[original_list_index + 2:]:
                s.memory[id(kid)]['order'] += 1

            s.wrap([1, 2, 3])

            final_x = Eval.ENTRY_X(s, {'start': original_start, 'duration': original_duration})
            orig_y = Eval.ENTRY_Y(s, {'order': original_order})
            final_y = Eval.ENTRY_Y(s, {'order': new_order})

            bui.buttonwidget(btn, position=(final_x, orig_y))

            for kid in s.stamp_kids[:original_list_index + 1]:
                kid_mem = s.memory[id(kid)]
                kid_x = Eval.ENTRY_X(s, kid_mem)

                old_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 2)
                new_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 1)

                s.anims[id(kid)][which] = Animate(
                    widget=kid,
                    attrs={
                        'position': ((kid_x, old_y), (kid_x, new_y))
                    },
                    duration=s.global_butter
                )

            for kid in s.stamp_kids[:original_list_index + 1]:
                kid_mem = s.memory[id(kid)]
                kid_width_steps = kid_mem['duration'] * s.entries_per_sec
                kid_x = s.magic_x + s.entry_xs_real * kid_mem['start']*s.entries_per_sec + (kid_width_steps * s.magic_left)

                old_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 2)
                new_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 1)

                s.anims[id(kid)][which] = Animate(
                    widget=kid,
                    attrs={
                        'position': ((kid_x, old_y), (kid_x, new_y))
                    },
                    duration=s.global_butter
                )

                # Animate existing entry's keys
                for key_data in kid_mem.get('keys', {}).values():
                    if 'widget' in key_data and key_data['widget'].exists():
                        wid = key_data['widget']
                        wid_id = id(wid)
                        key_time = key_data['time']

                        key_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                        old_key_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 2)
                        new_key_y = s.entry_ys_real * (len(s.memory) - kid_mem['order'] - 1)

                        if wid_id not in s.anims:
                            s.anims[wid_id] = {}

                        s.anims[wid_id][which] = Animate(
                            widget=wid,
                            attrs={
                                'opacity': (Color.OPACITY, Color.OPACITY),
                                'position': ((key_x, old_key_y), (key_x, new_key_y))
                            },
                            duration=s.global_butter
                        )

            s.anims[id(btn)][which] = Animate(
                widget=btn,
                attrs={
                    'opacity': (0, Color.OPACITY),
                    'textcolor': (
                        Const.INVISIBLE,
                        (*Color.TEXT, Color.OPACITY)
                    ),
                    'position': ((final_x, orig_y), (final_x, final_y))
                },
                duration=s.global_butter
            )

            # Animate duplicated entry's keys
            for key_data in new_keys.values():
                if 'widget' in key_data and key_data['widget'].exists():
                    wid = key_data['widget']
                    wid_id = id(wid)
                    key_time = key_data['time']

                    key_x = s.magic_x + s.entry_xs_real * key_time * s.entries_per_sec - s.entry_ys_real/4
                    key_y = s.entry_ys_real * (len(s.memory) - new_order - 1)

                    if wid_id not in s.anims:
                        s.anims[wid_id] = {}

                    s.anims[wid_id][which] = Animate(
                        widget=wid,
                        attrs={
                            'opacity': (0, Color.OPACITY),
                            'position': ((key_x, orig_y + 0), (key_x, key_y))
                        },
                        duration=s.global_butter
                    )

            s.scroll_to_timer = bui.AppTimer(
                s.global_butter / 2,
                bui.CallPartial(s.scroll_to, btn)
            )

            call()
            s.toast(Strings.INFO_DUPLICATED(node_data["name"]))
            s.build_timeline()
            return

        # delete
        if which == 7:
            Eval.SOUND(Const.OK_SOUND).play()
            if s.can_do != which:
                s.toast(Strings.CONFIRM_DELETE(
                    mem['data']['name']
                ), extra=2)
                s.can_do = which
                return

            if s.window_on and s.window_on[1] == s.edit_window:
                s.window_back()

            node_name = mem['data']['name']
            deleted_order = mem['order']

            def cleanup():
                # Delete all key widgets for this entry
                for key_data in mem.get('keys', {}).values():
                    if 'widget' in key_data and key_data['widget'].exists():
                        key_data['widget'].delete()

                if mem.get('prev_off_wid') and mem['prev_off_wid'].exists():
                    mem['prev_off_wid'].delete()

                del s.memory[id(b)]

                s.stamp_kids.remove(b)

                if b.exists():
                    b.delete()

                for kid in s.stamp_kids:
                    kid_mem = s.memory[id(kid)]
                    if kid_mem['order'] > deleted_order:
                        kid_mem['order'] -= 1

                s.wrap([1,2,3])

                for idx, kid in enumerate(reversed(s.stamp_kids)):
                    kid_mem = s.memory[id(kid)]
                    if kid_mem['order'] >= deleted_order: continue
                    old_x = Eval.ENTRY_X(s,kid_mem)

                    current_y = s.entry_ys_real*(idx+1)

                    end_pos = (
                        old_x,
                        s.entry_ys_real*idx
                    )

                    s.anims[id(kid)][which] = Animate(
                        widget=kid,
                        attrs={
                            'position':(
                                (old_x, current_y),
                                end_pos
                            )
                        },
                        duration=s.global_butter
                    )

                s.sl = None
                s.hide_tools()
                if len(s.memory):
                    s.show_controls(up=True)

                s.toast(Strings.INFO_DELETED(
                    node_name
                ))
                s.build_timeline()

            s.anims[id(b)][which] = Animate(
                widget=b,
                attrs={
                    'opacity':(Color.OPACITY, 0),
                    'textcolor':(
                        (*Color.TEXT, Color.OPACITY),
                        Const.INVISIBLE
                    )
                },
                duration=s.global_butter/2,
                on_finish=cleanup
            )

            s.wrap(2)
            return

        s.build_timeline()
        bui.apptimer(
            scroll_butter,
            bui.CallPartial(s.scroll_to,b)
        )
        butter = s.global_butter
        if new:
            s.anims[id(b)][which] = Animate(
                widget=b,
                duration=butter,
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

class Strings:
    # map
    MAP_TITLE = 'Movi'
    MAP_DESCRIPTION = 'Movie Maker'
    INSTANCE_DESCRIPTION = 'Three Two One Action!'
    INSTANCE_DESCRIPTION_SHORT = f'Version {__version__}'
    # UI
    MENUS = (
        'Save & Exit',
        'Load Seed',
        'Copy Seed',
        'Toggle Editor'
    )
    EDIT_BUTTON = 'Edit'
    EVENT_BUTTON_OFF = 'Event'
    EVENT_BUTTON_ON = 'Back'
    EVENTS = {
        'Node':'Make a scene node',
        'Camera':'Tune the camera',
        'Sound':'Play a sound',
        'FX':'Emit an effect',
        'Map':'Control the map',
        'Preset':'Load a preset',
        'Custom':'Custom action'
    }
    # yes
    ATTR = 'Attr'
    NODE_ATTR_HELP = 'The node\'s attribute name in attr dict\nbascenev1.newnode(attrs={\'THIS\':value})\nEnter'
    FX_ATTR_HELP = 'The FX\'s attribute name in attr dict\nbascenev1.emitfx(THIS=value)\nEnter'
    MAP_ATTR_HELP = 'The Sound\'s attribute name in attr dict\nsetattr(bascenev1.getactivity().map.node,\'THIS\',value)\nEnter'
    EVAL = 'Eval'
    EVAL_HELP = 'The node\'s attr value in attr dict (evaluated)\nbascenev1.newnode(attrs={\'attr\':THIS})\nEnter'
    OFFSET = 'Offset'
    TYPE = 'Type'
    TYPE_HELP = 'The node\'s type kwarg\nbascenev1.newnode(type=\'THIS\')\nEnter'
    NAME = 'Name'
    NODE_NAME_HELP = 'The node\'s name kwarg\nbascenev1.newnode(name=\'THIS\')\nEnter'
    FX_NAME_HELP = 'The FX name, used only for recognition\nEnter'
    SET = 'Set'
    POP = 'Pop'
    KEYS = 'Keys'
    DONE = 'Done'
    TARGET = 'Traget'
    POSITION = 'Position'
    VALUE = 'Value'
    EVERYWHERE = 'Everywhere'
    LOOP = 'Loop'
    LOAD = 'Load'
    # key
    ACTIONS = [
        'Attribute',
        'Callable',
        'Bubble',
        'Volume'
    ]
    ACTION_PLACEHOLDER = 'Select an action\nNice UI appears here'
    SOUND_PLACEHOLDER = 'Select a sound'
    PRESET_PLACEHOLDER = 'Select a preset'
    # camera event
    CAMERA_RESET_BUTTON = 'Reset'
    PREVIEW = 'Preview'
    STOP = 'Stop'
    CAMERA_POSITION_CHECK = 'Position'
    CAMERA_TARGET_CHECK = 'Target'
    CAMERA_MANUAL_CHECK = 'Manual'
    CAMERA_ENTRY = 'Camera'
    # errors
    ERROR_NO_SOUND_SELECTED = (
        'No sound selected!',
        'Pick one from the list first'
    )
    ERROR_SMOL_NO_RESIZE = (
        'Not resizable!',
        'This is an instant action blud'
    )
    ERROR_INVALID = 'Invalid {}!'
    ERROR_INVALID_HELP = 'Check your input pal'
    ERROR_OUT_OF_RANGE = '{} out of range!'
    ERROR_OUT_OF_RANGE_HELP = 'You went too far'
    ERROR_EMPTY = 'Empty {}!'
    ERROR_EMPTY_HELP = 'Stop leaving empty text boxes around'
    ERROR = 'Error!'
    ERROR_E = 'Error: {}'
    ERROR_HELP = 'You\'re on your own pal'
    ERROR_EVENT = lambda t,e: (
        f'{t}: {e}',
        'Your fault, not mine.'
    )
    ERROR_NOT_FOUND = 'Nothing here is called {}'
    ERROR_NOT_FOUND_HELP = 'Yeah, nothing happened'
    ERROR_REACHED_ZERO = (
        'Reached zero!',
        'Yeah I can\'t move it past that'
    )
    ERROR_AT_TOP = (
        'Already at the top!',
        'No entries above to swap'
    )
    ERROR_AT_BOTTOM = (
        'Hit the bottom!',
        'No entries below to swap'
    )
    ERROR_SMALLEST = (
        'Already at smallest size!',
        'Yeah it can\'t be smaller'
    )
    ERROR_SELECT_SOMETHING = (
        'Select something!',
        'Press on an entry to select it'
    )
    ERROR_NOT_PLAYING = (
        'Not even playing!',
        'There is no playhead to hide'
    )
    ERROR_PAUSE_FIRST = (
        'Stop playback first!',
        'The playhead is watching, I can\'t.'
    )
    NO_ACTIONS = (
        'No actions available!',
        'We\'re stuck with it as is'
    )
    # info
    INFO_SLOW_DOWN = (
        'Slow down poke',
        'I know you\'re spamming the ui'
    )
    INFO_POP_WHAT = (
        'Pop what?',
        'Buddy write some name'
    )
    INFO_SAVED = (
        'Saved changes!',
        'Go look at it'
    )
    INFO_DISCARDED = (
        'Discarded changes!',
        'Because you changed your mind'
    )
    INFO_DELETED = lambda n:(
        f'Deleted "{n}"',
        'Now it\'s gone forever'
    )
    INFO_DUPLICATED = lambda n:(
        f'Duplicated "{n}"',
        'Now there\'s two of them. This is getting out of hand.'
    )
    INFO_ASSIGNED = lambda a:(
        f'Assigned new attribute {a}',
        'Use the same attr name to overwrite it later'
    )
    INFO_UPDATED = lambda a:(
        f'Updated existing attribute {a}',
        'Since you used the same attr name'
    )
    INFO_POPPED = lambda n:(
        f'Popped "{n}"',
        'It\'s in a better place now.'
    )
    INFO_TARGET_MODE = (
        'Target mode',
        'Now arrows apply to target boxes'
    )
    INFO_POSITION_MODE = (
        'Position mode',
        'Now arrows apply to position boxes'
    )
    INFO_PREVIEW_ON = (
        'Preview on',
        'Camera changes are previewed live'
    )
    PREVIEW_OFF = (
        'Preview off',
        'Forget I said anything'
    )
    INFO_RESETTED = (
        'Resetted',
        'Everything is clean once again'
    )
    INFO_PLAYING = (
        'Now playing!',
        'What else should\'ve happened?'
    )
    INFO_PAUSED = (
        'Playback paused!',
        'You just froze time'
    )
    INFO_FINISHED = (
        'Playback finished!',
        'The playhead is gone'
    )
    INFO_ADDED_KEY = (
        'Key added!',
        'Yeah, that red dot'
    )
    INFO_EDITED_KEY = (
        'Key edited!',
        'Now it does something else'
    )
    # confirm
    CONFIRM_DUPLICATE = lambda t:(
        f'Make another "{t}"?',
        f'Press {Eval.CHAR(Const.TOOLS[6])} again to confirm'
    )
    CONFIRM_DELETE = lambda t:(
        f'Really delete "{t}"?',
        f'Press {Eval.CHAR(Const.TOOLS[7])} again to confirm'
    )
    # extra
    KEYS_ON = 'Keys on {}'
    BYE = (
        'That\'s a wrap!',
        'How fast can you read this'
    )
    EDIT = 'Edit {}'
    WELCOME = '{} joined the studio! Press for more'
    DESCRIPTION_HERE = 'Description here'
    WELCOME_HELP = 'Movi v{}, what could go wrong?'
    COMING_SOON = (
        'Coming soon!',
        'Aka not implemented yet lmao'
    )
    # presets
    PRESETS = {
        'Spaz': 'A lovely spaz',
        'TNT': 'A tnt box',
        'Viewpoint 1': 'Close prespective'
    }
    # compressed
    BLAME = lambda: (
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
    BA_DATA = join(
        dirname(
            bui.app.env.cache_directory
        ), 'ballistica_files', 'ba_data'
    )
    # scaling
    BA_LAG = 0.04
    BA_LAG_SMALL = 0.01
    INVISIBLE = (0,0,0,0)
    SCALE = {
        bui.UIScale.SMALL: 1.275,
        bui.UIScale.MEDIUM: 1,
        bui.UIScale.LARGE: 0.764
    }
    # visual
    SKIN = 'white'
    EMPTY = 'empty'
    SHADOW = 'softRect'
    GLOW = 'uniform'
    ALIGN = 'center'
    KEY = 'circleZigZag'
    PLAY_BUTTON = 'PLAY_BUTTON'
    PAUSE_BUTTON = 'PAUSE_BUTTON'
    # charstr
    CONTROLS = (
        ('PLAY_BUTTON','PAUSE_BUTTON'),
        'BACK'
    )
    PIN_POINT = 'PLAY_STATION_CROSS_BUTTON'
    TOOLS = (
        'RIGHT_ARROW',
        'LEFT_ARROW',
        'FAST_FORWARD_BUTTON',
        'REWIND_BUTTON',
        'UP_ARROW',
        'DOWN_ARROW',
        'DPAD_CENTER_BUTTON',
        'PLAY_STATION_CROSS_BUTTON'
    )
    # keys
    EVENT_KEYS = {
        0: (0,1,2),
        2: (3,),
        4: (0,1)
    }
    # arrows
    CAMERA_TOOLS = (
        '-',
        'LEFT_ARROW',
        'LEFT_BUTTON',
        'DOWN_ARROW',
        'DPAD_CENTER_BUTTON',
        'UP_ARROW',
        '+',
        'RIGHT_ARROW',
        'RIGHT_BUTTON'
    )
    # sounds
    OK_SOUND = 'deek'
    BAD_SOUND = 'block'
    # based
    TRIANGLE = 'PLAY_STATION_TRIANGLE_BUTTON'
    SQUARE = 'PLAY_STATION_SQUARE_BUTTON'
    BACK = 'BACK'
    # presets
    PRESETS = lambda:[
        (0,{}),
        (0,{}),
        (1,{'data':{
            'chks':[True,True,True],
            'position':(
                -7,
                3,
                2
            ),
            'target':(
                -13,
                0,
                -6
            )
        }})
    ]
    # extra
    BLAME = " ()',?ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    DO_NOTHING = lambda:None

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
    OFFSET = lambda rx,ry,cx,cy,dx=0,dy=0:(
        (rx/2+cx-dx/2,ry/2+cy-dy/2)
    )
    SCALE = lambda *a: (
        (m:=Const.SCALE[
            bui.app.ui_v1.uiscale
        ]) and tuple(m*n for n in a)
    )
    WIDGET = lambda w: (
        getattr(
            bui, w.get_widget_type() + 'widget'
        )
    )
    ENTRY_X = lambda s, mem: (
        s.magic_x +
        s.entry_xs_real * mem['start'] * s.entries_per_sec +
        (mem['duration'] * s.entries_per_sec * s.magic_left)
    )
    ENTRY_Y = lambda s, mem: (
        s.entry_ys_real * (len(s.memory) - mem['order'] - 1)
    )
    ENTRY_POS = lambda s, mem: (
        Eval.ENTRY_X(s, mem),
        Eval.ENTRY_Y(s, mem)
    )
    ENTRY_SIZE = lambda s, mem: (
        (s.entry_ys_real, s.entry_ys_real - s.magic_y) if mem.get('smol', False)
        else (
            s.entry_xs_real * (mem['duration'] * s.entries_per_sec) * s.magic_right,
            s.entry_ys_real - s.magic_y
        )
    )

class Format:
    ERROR = lambda e: (
        str(e) and Strings.ERROR_E.format(e)
        or Strings.ERROR,
        Strings.ERROR_HELP
    )
    INVALID = lambda e: (
        Strings.ERROR_INVALID.format(e),
        Strings.ERROR_INVALID_HELP
    )
    OUT_OF_RANGE = lambda e: (
        Strings.ERROR_OUT_OF_RANGE.format(e),
        Strings.ERROR_OUT_OF_RANGE_HELP
    )
    ERROR_EMPTY = lambda e: (
        Strings.ERROR_EMPTY.format(e),
        Strings.ERROR_EMPTY_HELP
    )
    NOT_FOUND = lambda a: (
        Strings.ERROR_NOT_FOUND.format(repr(a)),
        Strings.ERROR_NOT_FOUND_HELP
    )
    WELCOME = lambda n: (
        Strings.WELCOME.format(n),
        Strings.WELCOME_HELP.format(__version__)
    )

class DarkColor:
    BASE = (0,0,0)
    COLD = (0.5,0.5,0.5)
    WARM = (2,0,0)
    TEMP = (0,0,1)
    TEXT = (2,2,2)
    OPACITY = 0.4

# global
Color = globals()[Config.COLOR]

# ba_meta export bascenev1.GameActivity
class Movi(bs.TeamGameActivity[bs.Player,bs.Team]):
    name = Strings.MAP_TITLE
    description = Strings.MAP_DESCRIPTION
    get_availabe_settings = lambda s:[]
    supports_session_type = lambda s:True
    get_supported_maps = lambda s:bs.app.classic.getmaps('melee')
    get_instance_description = lambda s: Strings.INSTANCE_DESCRIPTION
    get_instance_description_short = lambda s: Strings.INSTANCE_DESCRIPTION_SHORT

    def __init__(s, settings):
        s.original_map = settings['map']
        super().__init__(settings)
        s.default_music = bs.MusicType.GRAND_ROMP

    def is_master(s,p):
        return p.sessionplayer.inputdevice.client_id == -1

    def on_player_join(s,p):
        if s.is_master(p):
            s.master = p
            s.make_ui()
        s.editor and s.editor.schedule_on_ui(
            lambda: s.editor.toast(
                Format.WELCOME(
                    p.sessionplayer.getname()
                )
            )
        )

    def on_player_leave(s,p):
        if s.is_master(p):
            s.master = None
            s.kill_ui()

    def make_ui(s):
        if not getattr(s,'editor',None):
            s.editor = Editor(map=s.original_map)
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

