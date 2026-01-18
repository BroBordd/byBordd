# Copyright 2026 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @BroBordd

"""
Board v1.0 - The Board

A silly board made for fun
"""

import os
import babase as ba
import bauiv1 as bui

from base64 import b64encode, b64decode, b85decode
from urllib.request import Request, urlopen
from collections import defaultdict
from urllib.error import HTTPError
from mimetypes import guess_type
from weakref import WeakMethod
from datetime import datetime
from time import perf_counter
from json import dumps, loads
from threading import Thread
from zlib import decompress
from hashlib import sha256
from random import random
from enum import Enum

__version__ = '1.0.0'

class Config:
    COLOR = 'Light'
    STRING = 'English'
    STARTUP = True
    DEBUG = True

class Board:
    _shared = defaultdict(list)

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
        s.welcome = False
        s.toast_blink = None
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
            String.BOARD,
            position=(x/2.35,y/2),
            scale=3
        )
        # finally
        s.fetch_thread = Thread(target=s.fetch).start()

    def toast(s,t):
        # create once
        if not hasattr(s,'toast_bg'):
            s.toast_bg = bui.buttonwidget(
                parent=s.root,
                label='',
                enable_sound=False,
                selectable=False,
                size=(0,0),
                texture=Eval.TEXTURE(Const.BASE),
                color=Color.COLD,
                textcolor=Const.INVISIBLE
            )
            s.toast_last = None
        # update
        text_width = t and Eval.STRING_WIDTH(t) or 0
        duration = 0.45
        end_size = dx,dy = (text_width+(t and 20 or 0),30)
        start_size = (0,dy)
        start_opacity = 0
        zero = 0.0001
        x,y = Eval.REAL(margin=0.2)
        end_pos = epx,epy = (x/2-dx/2,-40)
        rush = False
        # override
        if (anim:=s.anims.get(id(s.toast_bg),None)):
            start_size = stx,sty = anim.attrs_current['size']
            if (
                (int(stx) == int(dx)) and
                (int(sty) == int(dy))
            ): rush = True
            start_pos = anim.attrs_current['position']
            start_opacity = anim.attrs_current['opacity']
            anim.cancel()
        else:
            start_pos = (x/2,epy)
        # zoom
        zoom_time = 0.2
        def zoom():
            s.toast_zoom = Animate(
                widget=s.toast_bg,
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
                on_finish=(None,)
            )
        # blink text
        start_textcolor = (*Color.TEXT,Color.OPACITY)
        blink_time = 0.2
        apply_text = bui.CallPartial(
            bui.buttonwidget,
            s.toast_bg, label=t
        )
        skip_blink = s.toast_last == t
        def blink():
            if (anim:=s.toast_blink):
                anim.cancel()
            s.toast_blink = Animate(
                widget=s.toast_bg,
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
        s.anims[id(s.toast_bg)] = Animate(
            widget=s.toast_bg,
            attrs={
                'size':(start_size,end_size),
                'opacity':(
                    start_opacity,
                    t and Color.OPACITY or 0
                ),
                'position':(
                    start_pos,
                    end_pos
                )
            },
            duration=rush and zero or duration,
            on_finish=zoom
        )
        s.toast_timer = t and bui.AppTimer(
            max(len(t)*0.07,3),
            bui.CallPartial(s.toast,'')
        )
        # finally
        s.toast_last = t

    def update_title(s, new_text, on_finish=None):
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
            bui.apptimer(0.2, lambda: s.update_title(String.BOARD))
            # catalog
            bui.apptimer(0.1, lambda: s._render_catalog_content(cat))
        else:
            s.update_title(String.BOARD)
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
                text=Eval.FORMAT_USER(c['user_hash']),
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
            sensor = Widget.SENSOR(
                s.scroll_root,
                position=(px, py + marg/2),
                size=(x, ey + xt - marg),

            )
            widgets_to_animate.append((sensor, 'opacity', (0, 0.01), 0.25 + i*0.05))

            bui.buttonwidget(
                sensor,
                on_activate_call=bui.CallPartial(s.msg_window, c, sensor)
            )

        bui.containerwidget(s.scroll_root, size=(x, ry))
        # animate
        butter = 0.4
        for widget, attr_name, (start, end), delay in widgets_to_animate:
            if attr_name == 'opacity':
                attrs = {'opacity': (start, end)}
            else:
                attrs = {'color': (start, end)}

            Animate(
                widget=widget,
                attrs=attrs,
                duration=butter,
                delay=delay
            )
        if not s.welcome:
            s.welcome = True
            bui.apptimer(butter,bui.CallPartial(
                s.toast, String.WELCOME
            ))

    def fetch(s):
        try: cat = (
            Config.DEBUG and
            DEBUG_CATALOG
            or catalog()
        )
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
        size = x,y = Eval.REAL(margin=0.4)
        Eval.SOUND(Const.SOUND_HI)
        # root
        root = Widget.WINDOW(
            source=source,
            size=size
        )
        # back
        bx = 50
        marg = 10
        px,py = bx+marg*4,y-bx-marg*2
        dx,dy = x-(bx+marg*6),bx
        bsy = y-(marg*6+dy)
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
        Widget.IMAGE(
            root,
            position=(marg*2-1,marg*2),
            size=(bx+2,bsy-(bx+marg*2)*3),
            color=Color.WARM
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
        title = Widget.TEXT(
            root,
            text=String.NEW_POST,
            position=(bx+marg*5,py+marg),
            maxwidth=dx*0.7-marg,
            v_align=Const.ALIGN_CENTER
        )
        # help
        def hlp():
            Eval.SOUND(Const.SOUND_OK)
            s.toast(String.HELP_POST)
        py -= (bx+marg*2)
        Widget.BUTTON(
            root,
            position=(20,py-2),
            size=(bx,bx),
            label=Eval.CHAR(Const.CHAR_HELP),
            on_activate_call=hlp,
            color=Color.WARM
        )
        # title in
        t_px = bx+marg*6.65
        t_sx = dx*0.65-(bx+marg*2)
        Input(
            root,
            position=(t_px,py-marg*2),
            size=(t_sx,bx),
            hint=String.TITLE,
            maxwidth=t_sx-marg*2
        )
        # password in
        def set_as(t):
            bui.textwidget(
                title,
                text=Eval.FORMAT_USER_AS(t)
            )
        p_px = t_px + t_sx + marg*2
        p_sx = dx - (t_sx + marg*6)
        Input(
            root,
            position=(p_px,py-marg*2),
            size=(p_sx,bx),
            hint=String.PASSWORD,
            maxwidth=p_sx-marg*2,
            on_edit=set_as
        )
        # newline
        def nl():
            if not desc.text:
                Eval.SOUND(Const.SOUND_BAD)
                s.toast(String.ERROR_EMPTY_DESC)
                return
            Eval.SOUND(Const.SOUND_OK)
            w = desc.widget
            t = bui.textwidget(query=w)
            bui.textwidget(
                w,text=Eval.APPEND_NEWLINE(t)
            )
        py -= (bx+marg*2)
        Widget.BUTTON(
            root,
            position=(20,py-2),
            size=(bx,bx),
            label=String.NL,
            on_activate_call=nl,
            color=Color.WARM
        )
        # desc in
        sx = dx-marg*4.5
        desc = Input(
            root,
            position=(t_px+marg/2,py-(bx+marg)),
            size=(sx,bx*2),
            hint=String.DESCRIPTION,
            v_align=Const.ALIGN_BOTTOM,
            maxwidth=sx-marg*2
        )
        def pad():
            for w in (desc.widget,desc.hint_widget):
                bui.textwidget(w,padding=10)
        bui.apptimer(Const.BA_LAG,pad)
        # attach
        py -= (bx+marg*2)
        bui.buttonwidget(
            (btn:=Widget.BUTTON(
                root,
                position=(20,py-2),
                size=(bx,bx),
                label=Eval.CHAR(Const.CHAR_ATTACH),
                color=Color.WARM
            )), on_activate_call=bui.CallPartial(
                s.attach_window, btn
            )
        )
        # files
        file_x = 100
        xt = 40
        file_root = Widget.CONTAINER(
            Widget.HSCROLL(
                root,
                position=(px,marg*2),
                size=(dx,file_x+xt)
            ),
            size=(0,file_x+xt)
        )

    def attach_window(s,source=None):
        size = x,y = Eval.REAL(margin=0.7)
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
        dx,dy = x-(bx*2+marg*8),bx
        bsy = y-(marg*6+dy)
        Widget.IMAGE(
            root,
            position=(marg*2-1,marg*2),
            size=(bx+2,bsy),
            color=Color.WARM
        )
        # title
        px = bx+marg*4
        Widget.IMAGE(
            root,
            position=(px,py-2),
            size=(dx,dy+4),
            color=Color.WARM
        )
        Widget.TEXT(
            root,
            text=String.ATTACH,
            position=(bx+marg*5,py+marg),
            maxwidth=dx*0.7-marg,
            v_align=Const.ALIGN_CENTER
        )
        # sus
        Widget.TEXT(
            root,
            text=String.HMM,
            rotate=90,
            position=(marg+bx/1.43,marg*2),
            opacity=Color.OPACITY/2,
            v_align=Const.ALIGN_CENTER,
            maxwidth=bsy-marg*4
        )
        # done
        Widget.BUTTON(
            root,
            position=(dx+bx+marg*6,py),
            size=(bx,bx),
            label=Eval.CHAR(Const.CHAR_DONE),
            color=Color.WARM
        )
        # string in
        sx = dx+bx+marg+2
        sy = 40
        Input(
            root,
            position=(bx+marg*5,y-marg*4-bx-sy),
            size=(sx,sy),
            hint=String.HINT_ATTACH
        )

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
            position=(marg*2-1,marg*2),
            size=(bx+2,bsy),
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
            text=Eval.FORMAT_USER(c['user_hash']),
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
            corn = file_x/3.6+i*step,0
            Widget.TEXT(
                file_root,
                position=corn,
                maxwidth=file_x,
                text=n,
                v_align=Const.ALIGN_CENTER,
                h_align=Const.ALIGN_CENTER
            )
            bui.buttonwidget(
                (sensor:=Widget.SENSOR(
                    file_root,
                    position=corn,
                    size=(file_x,file_x+xt),
                )), on_activate_call=bui.CallPartial(
                    s.file_window, f, sensor, c['user_hash']
                )
            )

    def file_window(s,file,source,uh):
        clickable = True
        butter = 0.2
        bx = 50
        marg = 10
        x,y = Eval.REAL(margin=0.4)
        x /= 2
        size = (x,y)
        Eval.SOUND(Const.SOUND_HI)
        # root
        root_parts = Widget.WINDOW(
            source=source,
            size=size,
            parts=True
        )
        shadow,root_bg,root = root_parts
        # expand
        to_hide = []
        art = None
        switched = False
        anims = {}
        def switch():
            nonlocal switched, art
            if switched:
                switched = False
                for w,a in anims.copy().items():
                    anims[w] = a.reverse()
                art.fade_out(
                    duration=butter,
                    on_finish=art.delete
                )
                nonlocal clickable
                clickable = True
                return
            switched = True
            for w,at in to_hide:
                if (a:=anims.get(w)): a.cancel()
                anims[w] = Animate(
                    widget=w,
                    duration=butter,
                    attrs=at
                )
            art = Art(
                root,
                position=(art_x,art_y),
                text=String.BOARD,
                scale=3.2
            )
            if (a:=anims.get(wait,None)): a.cancel()
            anims[wait] = Animate(
                widget=wait,
                duration=butter,
                attrs={
                    'color':(
                        Const.INVISIBLE,
                        Eval.TEXT(Color.OPACITY/2)
                    )
                }
            )

        # back
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
        # title
        dx,dy = x-(bx+marg*6),bx
        px = bx+marg*4
        bsy = y-(marg*6+dy)
        Widget.IMAGE(
            root,
            position=(px,py-2),
            size=(dx,dy+4),
            color=Color.WARM
        )
        Widget.TEXT(
            root,
            text=file['original_name'],
            position=(bx+marg*5,py+marg),
            maxwidth=dx-marg*2,
            v_align=Const.ALIGN_CENTER
        )
        w = Widget.IMAGE(
            root,
            position=(px,marg*2-1),
            size=(dx,bsy),
            color=Color.COLD
        )
        to_hide.append((
            w, {'opacity':(Color.OPACITY,0)}
        ))
        # block
        blk_y = bsy-(bx+marg*2.2)*2
        Widget.IMAGE(
            root,
            position=(marg*2-2,marg*2-1),
            size=(bx+4,blk_y),
            color=Color.WARM
        )
        # id
        Widget.TEXT(
            root,
            text=file['id'],
            rotate=90,
            position=(marg+bx/1.43,marg*2),
            opacity=Color.OPACITY/2,
            v_align=Const.ALIGN_CENTER,
            maxwidth=blk_y-marg*4
        )
        # size
        py -= (bx+marg)
        w = Widget.TEXT(
            root,
            position=(px+marg,py),
            maxwidth=dx-marg*2,
            max_height=dy-marg*2,
            text=Eval.FORMAT_SIZE(file['size'])
        )
        to_hide.append((
            w, {
                'color':(
                    (Eval.TEXT(Color.OPACITY)),
                    Const.INVISIBLE
                 )
            }
        ))
        # download
        def _acquire():
            os.makedirs(Const.DOWNLOAD_PATH,exist_ok=True)
            acquire(
                uh,
                file['id'],
                Eval.FORMAT_DOWNLOAD_PATH(file['original_name'])
            )
            def _done():
                switch()
                s.toast(String.DOWNLOADED)
            bui.pushcall(_done,from_other_thread=True)
        def download():
            nonlocal clickable
            if not clickable:
                Eval.SOUND(Const.SOUND_BAD)
                return
            clickable = False
            Eval.SOUND(Const.SOUND_OK)
            switch()
            Thread(target=_acquire).start()
        py -= (marg+3)
        Widget.BUTTON(
            root,
            position=(marg*2,py),
            size=(bx,bx),
            label=Eval.CHAR(Const.CHAR_DOWNLOAD),
            text_scale=0.8,
            color=Color.WARM,
            on_activate_call=download
        )
        # copy
        def cp():
            if not bui.clipboard_is_supported():
                Eval.SOUND(Const.SOUND_BAD)
                return
            Eval.SOUND(Const.SOUND_GOOD)
            bui.clipboard_set_text(file['path'])
            s.toast(String.COPIED)
        py -= (marg*2+bx+2)
        art_x = px+bx+marg*4
        art_y = py-marg*2
        Widget.BUTTON(
            root,
            position=(marg*2,py),
            size=(bx,bx),
            label=Eval.CHAR(Const.CHAR_COPY),
            text_scale=0.8,
            color=Color.WARM,
            on_activate_call=cp
        )
        # wait
        wait = Widget.TEXT(
            root,
            text=String.WAIT,
            position=(art_x+marg*3,art_y-(bx+marg*3)),
            opacity=0
        )

# custom ui
# more like handmade widgets

class Input:
    def __init__(s,parent,on_edit=None,hint=None,v_align=None,**kw):
        s.text = kw.get('text','')
        s.hint = hint
        s.hint_up = not s.text
        s.on_edit = on_edit
        s.opacity = Color.OPACITY
        s.hint_opacity = s.opacity / 2
        kw.update({
            'v_align':v_align or Const.ALIGN_CENTER,
            'opacity':s.opacity,
            'description':hint
        })
        s.widget = Widget.EDITABLE(
            parent, **kw
        )
        kw.update({
            'text':hint or '',
            'opacity':s.hint_opacity
        })
        s.hint_widget = Widget.TEXT(
            parent, **kw
        )
        s.timer = bui.AppTimer(
            0.02, s.tick, repeat=True
        )
    def tick(s):
        if not s.widget.exists():
            s.delete()
            return
        if (t:=bui.textwidget(query=s.widget)) != s.text:
            s.text = t
            if s.hint:
                if s.hint_up and t:
                    bui.textwidget(
                        s.hint_widget,
                        color=Const.INVISIBLE
                    )
                if not s.hint_up and not t:
                    bui.textwidget(
                        s.hint_widget,
                        color=Eval.TEXT(s.hint_opacity)
                    )
                s.hint_up = not t
            callable(s.on_edit) and s.on_edit(t)
    def delete(s):
        s.timer = None
        s.widget.delete()

class Art:
    def __init__(s,parent,text,position,scale=3,opacity=None,**kw):
        s.opacity = opacity or Color.OPACITY/1.5
        gap = 20*scale
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
                opacity=s.opacity,
                scale=scale,
                **kw
            )
            for i,t in enumerate(text)
        ]
        off = random()
        s.art_color_idx = [int(off * len(Const.ART)) for _ in range(len(text))]
        s.art_progress = [(i * 0.1 + off) % 1.0 for i in range(len(text))]
        s.art_timer = bui.AppTimer(0.01, s.animate, repeat=True)
        # pro
        s.pro_base_x,s.pro_base_y = pos = px-(15*scale),py-(13.3*scale)
        s.pro_time = 0.0
        s.prox = gap*scale*(-0.97*scale+4.49)
        s.prox2 = s.prox*0.19
        s.pro_bg = Widget.IMAGE(
            parent,
            position=pos,
            opacity=s.opacity,
            size=(s.prox,5),
            color=Color.COLD
        )
        s.pro = Widget.IMAGE(
            parent,
            position=pos,
            opacity=s.opacity*2,
            size=(s.prox*0.19,5),
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

            if not k.exists():
                s.art_timer = None
                return
            bui.textwidget(k, color=blended)
        # pro
        s.pro_time += 0.02

        cycle = (s.pro_time % 2.0) / 2.0
        t = cycle * 2
        t = (t if t < 1 else 2 - t)
        t = t * t * (3.0 - 2.0 * t)

        x_offset = (s.prox - s.prox2) * t
        bui.imagewidget(s.pro, position=(s.pro_base_x + x_offset, s.pro_base_y), size=(s.prox2, 5))

    def fade_out(s, duration=0.3, on_finish=None):
        """Fade out all art elements"""
        # Stop color animation
        s.art_timer = None

        # Fade out text widgets (using color alpha channel)
        for kid in s.kids:
            if not kid.exists():
                return
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
    TEXT = lambda p,color=None,opacity=None,**kw: bui.textwidget(
        parent=p,
        color=color or Eval.TEXT(
            Color.OPACITY
            if opacity is None
            else opacity
        ),
        **kw
    )
    EDITABLE = lambda p,color=None,opacity=None,**kw: bui.textwidget(
        parent=p,
        editable=True,
        glow_type=Const.GLOW_TYPE,
        allow_clear_button=False,
        color=color or Eval.TEXT(
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
    WINDOW = lambda size,source=None,parts=False,**k: (
        (root:=Widget.CONTAINER(
            source=source,
            size=size,
            **k
        )),
        (shadow:=Eval.SHADOW(*size)),
        Widget.IMAGE(
            root,
            position=shadow[0],
            size=shadow[1],
            texture=Eval.TEXTURE(Const.SHADOW),
            color=Color.SHADOW
        ),
        Widget.IMAGE(
            root,
            position=(-1,-1),
            size=size,
            color=Color.BASE
        ),root
    )[parts and slice(2,5) or 4]
    SENSOR = lambda p,**k: bui.buttonwidget(
        parent=p,
        label=Const.BLANK,
        texture=Eval.TEXTURE(Const.EMPTY_IMG),
        opacity=0,
        enable_sound=False,
        **k
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
    SOUND = lambda which,duration=0.15:(
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
    FORMAT_ROOT_PATH = lambda t: os.path.join(
        Const.ROOT_PATH, t
    )
    FORMAT_DOWNLOAD_PATH = lambda t: os.path.join(
        Const.DOWNLOAD_PATH, t
    )
    FORMAT_USER = lambda u: (
        Eval.CHAR(Const.CHAR_USER) + Const.SPACE +
        Const.USER_PREFIX + u
    )
    FORMAT_USER_AS = lambda t: (
        String.NEW_POST + Const.SPACE + String.AS +
        Const.SPACE + Eval.FORMAT_USER(_seal(t))
    )
    FORMAT_SIZE = lambda s: (
        str(s) + Const.SPACE + String.BYTES
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
            if (
                file.endswith('.brp') or
                file.endswith('.mp4') or
                file.endswith('.mkv')
            )
            else Const.SCRIPT_IMG
            if file.endswith('.py')
            else Const.IMAGE_IMG
            if ty.startswith('image/')
            else Const.FILE_IMG
        )
    )[1]
    COUNT = lambda l,t1,t2: (
        ((i:=len(l)) or 1) and (
            str(i) + Const.SPACE +
            (i != 1 and t2 or t1)
        )
    )
    STRING_WIDTH = lambda s: sum(Const.FONT_METRICS.get(c, 30) for c in s)
    APPEND_NEWLINE = lambda t: t+Const.NEWLINE

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
    AS = 'as'
    ATTACH = 'Attach'
    BOARD = 'Board'
    BYTES = 'Bytes'
    COMMENTS = 'Comments'
    COPIED = 'Copied to clipboard'
    DESCRIPTION = 'Description'
    DOWNLOADED = 'Saves to downloads'
    ERROR_EMPTY_DESC = 'The description box is empty blud'
    FILE = 'File'
    FILES = 'Files'
    HELP_POST = 'Press NL to break line, better just paste text here tho'
    HINT_ATTACH = 'Path, URL, URI or FullPath'
    HMM = 'Hmm'
    NEW_POST = 'New Post'
    NL = 'NL'
    PASSWORD = 'Password'
    TITLE = 'Title'
    WAIT = 'Just a sec...'
    WELCOME = f'Welcome to Board! v{__version__}'

String = Eval.SUBCLASS(String,Config.STRING,EnglishString)

# constants
# these are never changed on runtime

class Const:
    ROOT_PATH = os.path.join(
        bui.app.env.python_directory_user,
        'Board'
    )
    DOWNLOAD_PATH = os.path.join(
        bui.app.env.python_directory_user,
        'Board', 'Downloads'
    )
    BA_LAG_SMALL = 0.01
    BA_LAG = 0.04
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
    IMAGE_IMG = 'alwaysLandBGColor'
    REPLAY_IMG = 'tv'
    AUDIO_IMG = 'audioIcon'
    CHAR_BACK = 'BACK'
    CHAR_HELP = '?'
    CHAR_DOWNLOAD = 'DOWN_ARROW'
    CHAR_ATTACH = '+'
    CHAR_COPY = 'PLAY_STATION_TRIANGLE_BUTTON'
    CHAR_DONE = 'PLAY_STATION_CIRCLE_BUTTON'
    CHAR_USER = 'LOGO_FLAT'
    CHAR_POST = 'UP_ARROW'
    USER_PREFIX = 'Anonymous_'
    ALIGN_CENTER = 'center'
    ALIGN_RIGHT = 'right'
    ALIGN_BOTTOM = 'bottom'
    SOUND_HI = 'powerup01'
    SOUND_OK = 'deek'
    SOUND_GOOD = 'dingSmallHigh'
    SOUND_BAD = 'block'
    SOUND_BYE = 'laser'
    GLOW_TYPE = 'uniform'
    INVISIBLE = (0,0,0,0)
    SPACE = ' '
    BLANK = ''
    NEWLINE = '\n'
    TIMESTAMP_FORMAT = '%d/%m/%y %H:%M:%S'
    ART = (
        (2.0, 0.3, 2.2),
        (2.2, 0.3, 1.5),
        (3.0, 0.3, 0.3),
        (2.2, 1.8, 0.3),
        (0.3, 2.0, 1.8),
    )
    FONT_METRICS = loads(decompress(b85decode(
        'c$`&KXG0Y+5d13|QHmH-F6}H>Y4+Zpf)znQl&Xlo-DI+P+<v=xvpYMPY~G'
        'PLC3-KDSIGu9D^80($Y_++CZmxkFeRg7A<u|jcQX1=;Y5a3Hu7vnNvaUhc'
        '~11kN|Kory_42dW-8ZdsiLa`r#YO-&`IYy57F~%#4NLVp&+H5FRGGJ7jv7'
        'DWK%H>&5&WpGSo5T81f7Sh9X0Wp`O{i#L#6{d4-{?49y`kM@PSwqgGi4)b'
        '&hx85~{14a6B!>@eacPxlszN#-^#*EZF8Ow=89E^wj641?4y{Uxl4!uPW1'
        'lf>5@^aSH;(OoDSTNUoXb&RwX_qpH$4j)2ESsL*OtfiHC46-?U!jJfrcRm'
        '}Q_&GQ#d;ve5s~h_gl%Y^x4GUi*r$mKs#-|;PL?5LO)bn;syh8(B@(MPS-'
        'o<LEp#a{4XtqB9MRNTS_Z<R7_X$B(>N5&`dt6_N2g+p)WnHcNI_Oz1YuD1'
        '-C|73{&HV;B5Z_Bx-M39-W81smf|hN65<dpg+uY7i4u55+q-hJW1Ga1Xzg'
        'xTq;`WB-_fK3Mu&X}=VOmbVPwM_4GSl9{(fBt0mMPkk^6~ihe}flx{2woD'
        '1Pc'
    )))

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

DEBUG_CATALOG = (
    [{'description': 'Yeah this is a test',
      'files': [{'download_url': 'https://api.github.com/repos/BroBordd/board/releases/assets/341170127',
                 'downloads': 0,
                 'extension': 'txt',
                 'id': '5bf241fecf92',
                 'original_name': 'file1.txt',
                 'path': '5e884898da28/5bf241fecf92.txt',
                 'size': 4}],
      'id': 'a6a8c8e03f27',
      'timestamp': '2026-01-15T23:13:10.583785',
      'title': 'Test File',
      'user_hash': '5e884898da28'},
     {'description': 'This is getting interesting',
      'files': [{'download_url': 'https://api.github.com/repos/BroBordd/board/releases/assets/341178181',
                 'downloads': 0,
                 'extension': 'txt',
                 'id': '9d5f16531678',
                 'original_name': 'file2.txt',
                 'path': '6cf615d5bcaa/9d5f16531678.txt',
                 'size': 16}],
      'id': 'e2a31d379fc6',
      'timestamp': '2026-01-15T23:22:54.067707',
      'title': 'Another File',
      'user_hash': '6cf615d5bcaa'},
     {'description': 'No files were attached this time.\nHaha!',
      'files': [],
      'id': 'b63a09d68067',
      'timestamp': '2026-01-16T20:49:32.198125',
      'title': 'No File',
      'user_hash': '5906ac361a13'},
     {'description': 'Hey there!\n'
                     'Welcome to Board!\n'
                     '\n'
                     'This post contains random various media.\n'
                     'For testing purposes of course!',
      'files': [{'download_url': 'https://api.github.com/repos/BroBordd/board/releases/assets/341638260',
                 'downloads': 0,
                 'extension': 'ogg',
                 'id': '9c6e39a6ed9d',
                 'original_name': 'vine-boom.ogg',
                 'path': 'b97873a40f73/9c6e39a6ed9d.ogg',
                 'size': 14935},
                {'download_url': 'https://api.github.com/repos/BroBordd/board/releases/assets/341638262',
                 'downloads': 0,
                 'extension': 'py',
                 'id': 'c57fb8c78f7f',
                 'original_name': 'nice.py',
                 'path': 'b97873a40f73/c57fb8c78f7f.py',
                 'size': 13},
                {'download_url': 'https://api.github.com/repos/BroBordd/board/releases/assets/341638264',
                 'downloads': 0,
                 'extension': 'txt',
                 'id': '918c27ac9cef',
                 'original_name': 'file2.txt',
                 'path': 'b97873a40f73/918c27ac9cef.txt',
                 'size': 16},
                {'download_url': 'https://api.github.com/repos/BroBordd/board/releases/assets/341638271',
                 'downloads': 0,
                 'extension': 'txt',
                 'id': 'ceaf5d97e83c',
                 'original_name': 'file1.txt',
                 'path': 'b97873a40f73/ceaf5d97e83c.txt',
                 'size': 4}],
      'id': 'bd51a341c9e6',
      'timestamp': '2026-01-16T21:30:11.902400',
      'title': 'Various Media!',
      'user_hash': 'b97873a40f73'}]
)
