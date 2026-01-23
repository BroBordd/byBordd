# Copyright 2026 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Board v1.0 - The Board

A silly board made for fun
"""

import os, re
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
from uuid import uuid4
from enum import Enum

__version__ = '1.0'

class Config:
    COLOR = 'Light'
    STRING = 'English'
    DEBUG = False

class Board(bui.MainWindow):
    def main_window_should_preserve_selection(s):
        return False
    def get_main_window_state(s):
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
    def __init__(s, source=None):
        s.anims = {}
        s.welcome = False
        s.toast_blink = None
        s.source = source

        s.catalog_widgets = []
        s.catalog_anims = []

        s._build_ui()
        super().__init__(
            root_widget=s.root,
            origin_widget=source,
            refresh_on_screen_size_changes=True,
            transition=Eval.TRANSITION(source)
        )

        Eval.SOUND(Const.SOUND_HI, 0.15)
        s.refresh(shut=True)

    def _build_ui(s):
        if hasattr(s, 'root') and s.root.exists():
            old_root = s.root

        x, y = size = Eval.REAL(margin=0.2)

        s._layout = {
            'margin': 20,
            'button_size': 50,
            'title_height': 50,
        }

        marg = s._layout['margin']
        bx = s._layout['button_size']
        dy = s._layout['title_height']
        py = y - 70

        # root
        s.root = Widget.WINDOW(
            size=size, source=s.source
        )

        # back
        back_x = marg
        s.back_button = Widget.BUTTON(
            s.root,
            position=(back_x, py),
            size=(bx, bx),
            label=Eval.CHAR(Const.CHAR_BACK),
            text_scale=0.8
        )
        bui.buttonwidget(s.back_button, on_activate_call=bui.CallPartial(s.exit, s.source))
        bui.containerwidget(s.root, cancel_button=s.back_button)

        # post
        post_x = x - marg - bx
        s.post_button = Widget.BUTTON(
            s.root,
            position=(post_x, py),
            size=(bx, bx),
            label=Eval.CHAR(Const.CHAR_POST),
            text_scale=1.1
        )
        bui.buttonwidget(s.post_button, on_activate_call=bui.CallPartial(s.post_window, s.post_button))

        # refresh
        rf_x = post_x - marg - bx
        s.refresh_button = Widget.BUTTON(
            s.root,
            position=(rf_x, py),
            size=(bx, bx),
            on_activate_call=s.refresh
        )
        s.refresh_icon = Widget.IMAGE(
            s.root,
            position=(rf_x + bx*0.1, py + bx*0.1),
            size=(bx*0.8, bx*0.8),
            texture=Eval.TEXTURE(Const.IMG_REFRESH),
            color=Color.TEXT
        )

        # title
        px = back_x + bx + marg
        dx = rf_x - px - marg
        s.title_bg = Widget.IMAGE(
            s.root,
            position=(px, py - 2),
            size=(dx, dy + 4),
            color=Color.COLD,
        )
        s.title = Widget.TEXT(
            s.root,
            position=(px + marg/2, py + dy/4 - 2),
            text=String.WAIT
        )

        # scroll
        sx, sy = s.scroll_size = x - marg, y - marg*2.5 - dy
        s.scroll = Widget.SCROLL(
            s.root,
            position=(marg/2, marg/2),
            size=(sx, sy)
        )

        # scroll root
        cx, cy = sx, sy - 15
        s.scroll_root = Widget.CONTAINER(
            s.scroll,
            size=(cx, cy)
        )

    def on_resize(s):
        """Called when screen size changes - rebuild UI"""
        if not hasattr(s, 'root') or not s.root.exists():
            return
        # Store current catalog data if we have it
        current_catalog = getattr(s, '_current_catalog', None)
        # Rebuild UI with new dimensions
        s._build_ui()
        print('built')
        # Restore catalog if we had one loaded
        if current_catalog:
            s._render_catalog_content(current_catalog)
        # Otherwise check if art widget is showing (loading state)
        elif hasattr(s, 'art') and s.art and not s.art.art_timer is None:
            x, y = Eval.REAL(margin=0.2)
            art_sx = 350
            art_sy = 250
            old_art = s.art
            s.art = Art(
                s.root,
                position=(x/2-art_sx/2, y/2-art_sy/4),
                size=(art_sx, art_sy),
            )
            if old_art:
                old_art.delete()

    def on_rescale(s):
        """Called when UI scale changes - can reuse on_resize logic"""
        s.on_resize()

    def render(s, cat):
        if not s.root.exists(): return
        # Store catalog for resize
        s._current_catalog = cat

        if s.art:
            s.art.fade_out(
                duration=0.3,
                on_finish=s.art.delete
            )
            bui.apptimer(0.2, lambda: s.update_title(String.BOARD))
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
        lc = len(cat)
        ry = (marg + ey + xt)*lc-marg

        # Clear old catalog widgets
        for w in getattr(s, 'catalog_widgets', []):
            if hasattr(w, 'delete'):
                w.delete()
        for anim in getattr(s, 'catalog_anims', []):
            if hasattr(anim, 'cancel'):
                anim.cancel()

        s.catalog_widgets = []
        s.catalog_anims = []
        widgets_to_animate = []

        for i, c in enumerate(cat, start=1):
            px, py = (0, (marg + ey + xt) * (i - 1))
            files = c['files']

            # bg
            bg = Widget.IMAGE(
                s.scroll_root,
                size=(x, ey),
                position=(px, py),
                color=Color.COLD,
                opacity=0
            )
            s.catalog_widgets.append(bg)
            widgets_to_animate.append((bg, 'opacity', (0, Color.OPACITY), 0.1 + (lc-i)*0.05))

            # head
            head = Widget.IMAGE(
                s.scroll_root,
                size=(x, xt),
                position=(px, py + ey),
                color=Color.WARM,
                opacity=0
            )
            s.catalog_widgets.append(head)
            widgets_to_animate.append((head, 'opacity', (0, Color.OPACITY), 0.1 + (lc-i)*0.05))

            # img
            img = Widget.IMAGE(
                s.scroll_root,
                position=(px + marg/2, py + marg/2),
                size=(ix, ix),
                texture=Eval.COVER_IMG(files),
                opacity=0
            )
            s.catalog_widgets.append(img)
            widgets_to_animate.append((img, 'opacity', (0, Color.OPACITY), 0.15 + (lc-i)*0.05))

            # user
            user = Widget.TEXT(
                s.scroll_root,
                text=Eval.FORMAT_USER(c['user_hash']),
                position=(marg/2, py + ey + marg/2),
                opacity=0
            )
            s.catalog_widgets.append(user)
            widgets_to_animate.append((user, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY)), 0.15 + (lc-i)*0.05))

            # id
            idx = 70
            id_text = Widget.TEXT(
                s.scroll_root,
                text=Eval.METADATA(c['timestamp'], c['id']),
                position=(x - idx - marg/2, py + ey + marg/2),
                h_align=Const.ALIGN_RIGHT,
                opacity=0
            )
            s.catalog_widgets.append(id_text)
            widgets_to_animate.append((id_text, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY/2)), 0.15 + (lc-i)*0.05))

            # title
            title = Widget.TEXT(
                s.scroll_root,
                position=(px + ix + marg*1.5, py + ey - (marg + 30)),
                text=c['title'] or String.NO_TITLE,
                maxwidth=x - ix - marg*2,
                scale=1.3,
                v_align=Const.ALIGN_CENTER,
                opacity=0
            )
            s.catalog_widgets.append(title)
            widgets_to_animate.append((title, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY)), 0.2 + (lc-i)*0.05))

            # desc
            mw = x - ix - marg*4
            desc = Widget.TEXT(
                s.scroll_root,
                position=(px + ix + marg, py + ey - (marg + 60)),
                text='\n'.join(
                    fit_string(
                        (c['description'] or String.NO_DESCRIPTION),
                        mw
                    ).split('\n')[:3]
                ),
                maxwidth=mw,
                max_height=ix - 30,
                opacity=0
            )
            s.catalog_widgets.append(desc)
            widgets_to_animate.append((desc, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY/2)), 0.2 + (lc-i)*0.05))

            # sensor
            sensor = Widget.SENSOR(
                s.scroll_root,
                position=(px, py + marg/2),
                size=(x, ey + xt - marg),
            )
            s.catalog_widgets.append(sensor)
            widgets_to_animate.append((sensor, 'opacity', (0, 0.01), 0.25 + (lc-i)*0.05))
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

            anim = Animate(
                widget=widget,
                attrs=attrs,
                duration=butter,
                delay=delay
            )
            s.catalog_anims.append(anim)

        if not s.welcome:
            s.welcome = True
            bui.apptimer(butter, bui.CallPartial(
                s.toast, String.WELCOME
            ))

    def toast(s,t):
        if not s.root.exists(): return
        if getattr(s,'toast_zoom',None):
            s.toast_zoom.cancel()
        # create once
        if not hasattr(s,'toast_bg'):
            s.toast_bg = bui.buttonwidget(
                parent=s.root,
                label='',
                enable_sound=False,
                selectable=False,
                size=(0,0),
                texture=Eval.TEXTURE(Const.IMG_BASE),
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

    def refresh(s,shut=False):
        if not hasattr(s,'loaded'):
            s.loaded = False
        elif not s.loaded:
            Eval.SOUND(Const.SOUND_BAD)
            return
        shut or Eval.SOUND(Const.SOUND_OK)
        x, y = Eval.REAL(margin=0.2)
        art_sx = 350
        art_sy = 250
        s.art = Art(
            s.root,
            position=(x/2-art_sx/2,y/2-art_sy/4),
            size=(art_sx,art_sy),
        )
        s.update_title(String.WAIT)
        s.loaded = False
        if Config.DEBUG == 'title':
            return
        def kill():
            for w in getattr(s, 'catalog_widgets', []): w.delete()
            s.catalog_widgets = []
            Thread(target=s.fetch).start()
        if getattr(s, 'catalog_anims', None):
            for anim in s.catalog_anims: anim.reverse()
            s.catalog_anims = []
            bui.apptimer(0.4, kill)
        else:
            kill()

    def fetch(s):
        try: cat = catalog()
        except Exception as e:
            call = bui.CallPartial(
                bui.textwidget, s.title, text=str(e)
            )
        else:
            call = bui.CallPartial(s.render, cat)
            s.loaded = True
        ba.pushcall(call, from_other_thread=True)

    def exit(s,source=None):
        s.anims.clear()
        s.catalog_anims.clear()
        Eval.SOUND(Const.SOUND_BYE)
        s.main_window_back()

    def post_window(s,source=None):
        if not s.loaded:
            Eval.SOUND(Const.SOUND_BAD)
            return
        size = x,y = Eval.REAL(margin=0.4)
        Eval.SOUND(Const.SOUND_HI)
        busy = False
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
        def back(shut=False):
            bui.containerwidget(
                root,transition=Eval.TRANSITION(source,True)
            )
            shut or Eval.SOUND(Const.SOUND_BYE)
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
            size=(dx-(bx+marg*2),dy+4),
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
        # is busy
        def is_busy():
            if not busy: return False
            Eval.SOUND(Const.SOUND_BAD)
            s.toast(String.NOT_NOW)
            return True
        # done
        def done():
            if is_busy(): return
            if not pass_inp.text:
                s.toast(String.ENTER_PASSWORD)
                Eval.SOUND(Const.SOUND_BAD)
                return
            s.toast(String.UPLOADING)
            Eval.DOUBLE_DING(1,0)
            Thread(target=_upload).start()
        # upload
        def _upload():
            nonlocal busy
            busy = True
            upload(
                pass_inp.text,
                Eval.FLATTEN(title_inp.text),
                desc_inp.text,
                files
            )
            bui.pushcall(_on_upload, from_other_thread=True)
        def _on_upload():
            Eval.DOUBLE_DING(0,1)
            back(shut=True)
            s.toast(String.PUBLISHED)
        Widget.BUTTON(
            root,
            position=(dx+marg*4-2,py),
            size=(bx,bx),
            label=Eval.CHAR(Const.CHAR_DONE),
            color=Color.WARM,
            on_activate_call=done
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
        title_inp = Input(
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
        pass_inp = Input(
            root,
            position=(p_px,py-marg*2),
            size=(p_sx,bx),
            hint=String.PASSWORD,
            maxwidth=p_sx-marg*2,
            on_edit=set_as
        )
        # newline
        def nl():
            if not desc_inp.text:
                Eval.SOUND(Const.SOUND_BAD)
                s.toast(String.ENTER_SOMETHING)
                return
            Eval.SOUND(Const.SOUND_OK)
            w = desc_inp.widget
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
        desc_inp = Input(
            root,
            position=(t_px+marg/2,py-(bx+marg)),
            size=(sx,bx*2),
            hint=String.DESCRIPTION,
            v_align=Const.ALIGN_BOTTOM,
            maxwidth=sx-marg*2
        )
        def pad():
            for w in (desc_inp.widget,desc_inp.hint_widget):
                bui.textwidget(w,padding=10)
        bui.apptimer(Const.BA_LAG,pad)
        # attach
        def push_file(txt,ty,img):
            i = len(files)
            files.append(txt)
            sx = i*step
            gay = (
                15 if img in (
                    Const.IMG_FILE,
                    Const.IMG_DEFAULT,
                    Const.IMG_SCRIPT
                )
                else marg
            )
            to = Widget.IMAGE(
                file_root,
                position=(i*step+gay,xt-marg),
                size=(file_x,file_x),
                texture=Eval.TEXTURE(img)
            )
            if img == Const.IMG_FILE:
                Widget.TEXT(
                    file_root,
                    position=(i*step+gay+file_x-54,xt-marg*2),
                    text=Eval.FILE_EXTENTION(txt),
                    size=(file_x,30),
                    big=True,
                    opacity=Color.OPACITY/2,
                    rotate=90,
                    maxwidth=file_x*0.5
                )
            corn = file_x/3.6+marg*0.8+step*i,0
            Widget.TEXT(
                file_root,
                position=corn,
                maxwidth=file_x,
                text=(
                    ty != 2 and Eval.ELLIPSE_END
                    or Eval.ELLIPSE_START
                )(txt,Const.FILENAME_MAX),
                v_align=Const.ALIGN_CENTER,
                h_align=Const.ALIGN_CENTER
            )
            def prv(txt):
                Eval.SOUND(Const.SOUND_OK)
                s.toast(txt)
            bui.buttonwidget(
                (sensor:=Widget.SENSOR(
                    file_root,
                    position=corn,
                    size=(file_x,file_x+xt),
                )), on_activate_call=bui.CallPartial(
                    prv, txt
                )
            )
            bui.containerwidget(
                file_root, size=(max(dx-15,sx),file_x+xt)
            )
            return to
        py -= (bx+marg*2)
        bui.buttonwidget(
            (btn:=Widget.BUTTON(
                root,
                position=(20,py-2),
                size=(bx,bx),
                label=Eval.CHAR(Const.CHAR_ATTACH),
                color=Color.WARM
            )), on_activate_call=bui.CallPartial(
                s.attach_window, btn, pipe=push_file
            )
        )
        # files
        files = []
        file_x = 100
        step = file_x+marg*2
        xt = 30
        file_root = Widget.CONTAINER(
            Widget.HSCROLL(
                root,
                position=(px,marg*2),
                size=(dx,file_x+xt)
            ),
            size=(dx-15,file_x+xt)
        )

    def attach_window(s,source=None,pipe=None):
        x,y = Eval.REAL(margin=0.7)
        Eval.SOUND(Const.SOUND_HI)
        extra_y = y
        # root
        root = Widget.WINDOW(
            source=source,
            size=(x,y+extra_y)
        )
        # back
        bx = 50
        marg = 10
        py = y-bx-marg*2+extra_y
        def back(src=None):
            src and bui.containerwidget(
                root, scale_origin_stack_offset=(
                    src.get_screen_space_center()
                )
            )
            bui.containerwidget(
                root,transition=Eval.TRANSITION(
                    src or source, True
                )
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
            position=(marg*2-1,extra_y+marg*2),
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
        # suspect
        txt = ''
        ty = -1
        def set_sus(t):
            nonlocal ty, txt
            txt = t
            ty = Eval.STRING_TYPE(t)
            bui.textwidget(
                suspect,
                text=Eval.FORMAT_STRING_TYPE(t,ty)
            )
        suspect = Widget.TEXT(
            root,
            text=String.HMM,
            rotate=90,
            position=(marg+bx/1.43,extra_y+marg*2),
            opacity=Color.OPACITY/2,
            v_align=Const.ALIGN_CENTER,
            maxwidth=bsy-marg*4
        )
        # done
        def done():
            nonlocal txt
            if not txt or ty < 0:
                Eval.SOUND(Const.SOUND_BAD)
                s.toast(String.ENTER_SOMETHING)
                return

            img = Const.IMG_DEFAULT
            # URL
            if ty == 0:
                try:
                    if not Eval.VALIDATE_URL(txt): raise
                except:
                    Eval.SOUND(Const.SOUND_BAD)
                    s.toast(String.INVALID_URI)
                    return

            # URI (data:)
            elif ty == 1:
                try:
                    if not Eval.VALIDATE_URI(txt): raise
                except:
                    Eval.SOUND(Const.SOUND_BAD)
                    s.toast(String.INVALID_URI)
                    return

            # path (local file)
            else:
                if not os.path.isabs(txt):
                    txt = os.path.join(
                        Const.ROOT_PATH, txt
                    )
                if not os.path.exists(txt):
                    Eval.SOUND(Const.SOUND_BAD)
                    s.toast(String.FILE_NOT_FOUND)
                    return
                img = Eval.IMG_FILE(txt)

            # finally
            s.toast(String.ATTACH_DONE)
            back(
                callable(pipe) and pipe(
                    txt, ty, img
                )
            )
        Widget.BUTTON(
            root,
            position=(dx+bx+marg*6,py),
            size=(bx,bx),
            label=Eval.CHAR(Const.CHAR_DONE),
            color=Color.WARM,
            on_activate_call=done
        )
        # string in
        sx = dx+bx+marg+2
        sy = 40
        inp = Input(
            root,
            position=(bx+marg*5,y-marg*4-bx-sy+extra_y),
            size=(sx,sy),
            hint=String.HINT_ATTACH,
            on_edit=set_sus,
            maxwidth=sx-marg
        )
        # help
        mw = x-(bx+marg*7)
        Widget.TEXT(
            root,
            position=(bx+marg*4.5,marg*5+extra_y),
            text=String.PATH_MEANS,
            maxwidth=mw,
            v_align=Const.ALIGN_CENTER
        )
        Widget.TEXT(
            root,
            position=(bx+marg*4.5,marg*2+extra_y),
            text=String.URL_MEANS,
            maxwidth=mw,
            v_align=Const.ALIGN_CENTER
        )
        # cwd
        py -= (extra_y-marg*2)
        px -= (bx+marg*2)
        dx = x-marg*4
        Widget.IMAGE(
            root,
            position=(px,py-2),
            size=(dx-(bx+marg*2),dy+4),
            color=Color.WARM
        )
        cwd_text = Widget.TEXT(
            root,
            position=(px+marg*2,py+marg),
            maxwidth=dx-(bx+marg*6),
            v_align=Const.ALIGN_CENTER
        )
        # kang
        def kang():
            if not sl:
                s.toast(String.SELECT_SOMETHING)
                Eval.SOUND(Const.SOUND_BAD)
                return
            bui.textwidget(
                inp.widget,
                text=sl[0].path
            )
            Eval.SOUND(Const.SOUND_ACTION,0)
        Widget.BUTTON(
            root,
            position=(dx+marg*2-bx,py),
            size=(bx,bx),
            label=Eval.CHAR(Const.CHAR_POST),
            color=Color.WARM,
            on_activate_call=kang
        )
        # ls root
        Widget.IMAGE(
            root,
            position=(px,marg*2),
            size=(dx+2,py-marg*4-2),
            color=Color.COLD
        )
        sy = py-marg*4-2
        ls_root = Widget.CONTAINER(
            Widget.SCROLL(
                root,
                position=(px,marg*2),
                size=(dx+2,sy)
            )
        )
        sy -= 15
        # ls
        def cd(n=Const.DOT_DOT):
            nonlocal wd, sl, ls
            new = os.path.normpath(
                os.path.join(wd,n)
            )
            try:
                ls = list(os.scandir(new))
                ls.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                s.toast(String.ACCESS_DENIED)
                Eval.SOUND(Const.SOUND_BAD)
                return
            wd = new
            sl = None
            fresh()
        def slct(f,w):
            nonlocal sl
            sl and bui.textwidget(
                sl[1], color=Eval.TEXT(Color.OPACITY)
            )
            sl = (f,w)
            bui.textwidget(
                w, color=Color.BASE
            )
        sl = None
        wd = Const.ROOT_PATH
        ls = list(os.scandir(wd))
        ls.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        lx = 30
        fx = 30
        dx -= fx+marg*2
        trash = []
        def fresh():
            bui.textwidget(
                cwd_text,
                text=Eval.ELLIPSE_START(
                    wd,
                    Const.PATH_MAX
                )
            )
            for w in trash: w.delete()
            trash.clear()
            lsy = max((len(ls)+1)*(lx+5),sy)
            bui.containerwidget(
                ls_root,
                size=(dx+2,lsy)
            )
            # dot dot
            w = Widget.IMAGE(
                ls_root,
                texture=Eval.TEXTURE(Const.IMG_DOT_DOT),
                size=(fx,fx),
                position=(0,lsy-lx)
            )
            trash.append(w)
            w = Widget.HYPER(
                ls_root,
                position=(fx+marg,lsy-lx),
                size=(dx,lx),
                text=Const.DOT_DOT,
                on_activate_call=cd
            )
            trash.append(w)
            # files
            for i,f in enumerate(ls,start=2):
                py = lsy-i*(lx+5)
                is_dir = f.is_dir()
                im = (
                    is_dir and Const.IMG_FOLDER
                    or Eval.IMG_FILE(f.name)
                )
                w = Widget.IMAGE(
                    ls_root,
                    texture=Eval.TEXTURE(im),
                    size=(fx,fx),
                    position=(0,py),
                    color=Color.WARM
                )
                trash.append(w)
                bui.textwidget(
                    (w:=Widget.HYPER(
                        ls_root,
                        position=(fx+marg,py),
                        size=(dx,lx),
                        text=f.name,
                        v_align=Const.ALIGN_CENTER
                    )), on_activate_call=(
                        is_dir and bui.CallPartial(
                            cd, f.name
                        ) or bui.CallPartial(
                            slct, f, w
                        )
                    )
                )
                trash.append(w)
        # finally
        fresh()

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
        # title and desc
        file_x = 100
        xt = 30
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
            text=c['title'] or String.NO_TITLE,
            maxwidth=dx-marg*4,
            scale=1.3,
            v_align=Const.ALIGN_CENTER
        )
        mw = dx-marg*4
        mh = bsy-(file_x+xt+marg*3+30)
        Widget.TEXT(
            root,
            position=(px+marg*1.7,marg+bsy-65),
            text=fit_string(
                c['description'] or String.NO_DESCRIPTION,
                mw, mh
            ),
            maxwidth=mw,
            max_height=mh,
            opacity=Color.OPACITY/2
        )
        # comment box
        def push_com():
            if not loaded:
                Eval.SOUND(Const.SOUND_BAD)
                s.toast(String.NOT_NOW)
                return
            if not com_inp.text:
                s.toast(String.ENTER_SOMETHING)
                Eval.SOUND(Const.SOUND_BAD)
                return
            if not pass_inp.text:
                s.toast(String.ENTER_PASSWORD)
                Eval.SOUND(Const.SOUND_BAD)
                return
            bui.textwidget(
                com_inp.widget,
                text=Const.BLANK
            )
            Eval.DOUBLE_DING(1,0)
            s.toast(String.SENDING_COMMENT)
            Thread(target=_comment).start()
        def _comment():
            call = done
            try:
                comment(
                    pass_inp.text,
                    c['id'],
                    com_inp.text
                )
            except Exception as e:
                call = bui.CallPartial(
                    done, str(e)
                )
            bui.pushcall(call,from_other_thread=True)
        def done(err=None):
            if err:
                Eval.DOUBLE_DING(0,0)
                s.toast(Eval.FORMAT_ERROR(err))
                return
            Eval.DOUBLE_DING(0,1)
            s.toast(String.COMMENT_SENT)
        com_x = px+dx+marg*2
        Widget.IMAGE(
            root,
            position=(com_x,py-2),
            size=(cx-(bx+marg*2),dy+4),
            color=Color.WARM
        )
        ys = y-(marg*6+dy)
        box_y = 35
        box_x = cx-(box_y+marg*4)
        Widget.IMAGE(
            root,
            position=(com_x,marg*2),
            size=(cx,box_y*2+marg*3),
            color=Color.COLD
        )
        Widget.TEXT(
            root,
            position=(px+dx+marg/2+cx/2.7,py+marg),
            text=String.COMMENTS,
            h_align=Const.ALIGN_CENTER
        )
        com_inp = Input(
            root,
            position=(com_x+marg*2,marg*3),
            size=(box_x,box_y),
            hint=String.COMMENT
        )
        Widget.BUTTON(
            root,
            position=(com_x+box_x+marg*3,marg*3+2),
            size=(box_y-2,box_y-2),
            label=Eval.CHAR(Const.CHAR_POST),
            color=Color.WARM,
            text_scale=1.2,
            on_activate_call=push_com
        )
        pass_inp = Input(
            root,
            position=(com_x+marg*2,marg*4+box_y),
            size=(box_x+box_y+marg,box_y),
            hint=String.PASSWORD
        )
        # list comment
        coms = None
        art = None
        com_widgets = []
        com_anims = []
        last_anim = None
        com_big = False
        def refresh(shut=False):
            nonlocal art, loaded
            if not loaded:
                Eval.SOUND(Const.SOUND_BAD)
                s.toast(String.NOT_NOW)
                return
            shut or Eval.SOUND(Const.SOUND_OK)
            loaded = False
            if com_anims:
                for anim in com_anims:
                    anim.reverse()
                com_anims.clear()
                def cleanup_and_fetch():
                    for w in com_widgets:
                        w.delete()
                    com_widgets.clear()
                    if com_big:
                        nonlocal last_anim
                        lx,_ = last_size
                        last_anim = Animate(
                            widget=com_scroll,
                            duration=10,
                            attrs={
                                'size':(
                                    last_size,
                                    (lx,0)
                                )
                            }
                        )
                    Thread(target=_get).start()
                bui.apptimer(0.4, cleanup_and_fetch)
            else:
                for w in com_widgets:
                    w.delete()
                com_widgets.clear()
                Thread(target=_get).start()
            artx = cx-marg*8
            art = Art(
                root,
                position=(com_x+cx/8,com_yp+com_ys/4+artx/8),
                size=(artx,artx/2),
                opacity=Color.OPACITY/1.3
            )
        def _get():
            nonlocal coms
            coms = get_comments(c['id'])
            coms.reverse()
            bui.pushcall(do_list,from_other_thread=True)
        def do_list():
            if not com_scroll.exists(): return
            nonlocal com_big
            last_anim and last_anim.cancel()
            art.fade_out(on_finish=art.delete)
            bui.scrollwidget(
                com_scroll,
                size=last_size
            )
            # id user_hash text timestamp
            step = 30
            each_y = step*2+marg*2
            ry = len(coms)*each_y
            com_ry = max(com_ys-15,ry)
            com_big = ry > (com_ys-15)
            bui.containerwidget(
                com_root,
                size=(cx,com_ry)
            )
            widgets_to_animate = []
            for i,com in enumerate(coms):
                cur_y = i*each_y
                # head
                head = Widget.IMAGE(
                    com_root,
                    color=Color.WARM,
                    size=(cx,step),
                    position=(0,cur_y+step),
                    opacity=0
                )
                com_widgets.append(head)
                widgets_to_animate.append((head, 'opacity', (0, Color.OPACITY), 0.1 + i*0.05))
                # body
                body = Widget.IMAGE(
                    com_root,
                    color=Color.COLD,
                    size=(cx,step),
                    position=(0,cur_y),
                    opacity=0
                )
                com_widgets.append(body)
                widgets_to_animate.append((body, 'opacity', (0, Color.OPACITY), 0.1 + i*0.05))
                # user
                user = Widget.TEXT(
                    com_root,
                    text=Eval.FORMAT_USER(com['user_hash']),
                    position=(marg/2,cur_y+step),
                    size=(cx,step),
                    maxwidth=cx-marg*4,
                    v_align=Const.ALIGN_CENTER,
                    opacity=0
                )
                com_widgets.append(user)
                widgets_to_animate.append((user, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY)), 0.15 + i*0.05))
                # text
                text_widget = Widget.TEXT(
                    com_root,
                    text=Eval.ELLIPSE_END(
                        com['text'],
                        Const.COMMENT_MAX
                    ),
                    position=(marg/2,cur_y),
                    size=(cx,step),
                    maxwidth=cx-marg*4,
                    v_align=Const.ALIGN_CENTER,
                    opacity=0
                )
                com_widgets.append(text_widget)
                widgets_to_animate.append((text_widget, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY/2)), 0.15 + i*0.05))
                # sensor
                bui.buttonwidget(
                    (sensor:=Widget.SENSOR(
                        com_root,
                        position=(marg/2,cur_y),
                        size=(cx,step*2)
                    )), on_activate_call=bui.CallPartial(
                        s.comment_window, com, sensor
                    )
                )
            bui.containerwidget(
                com_root,
                visible_child=foo
            )
            # animate
            butter = 0.4
            for widget, attr_name, (start, end), delay in widgets_to_animate:
                if attr_name == 'opacity':
                    attrs = {'opacity': (start, end)}
                else:
                    attrs = {'color': (start, end)}
                anim = Animate(
                    widget=widget,
                    attrs=attrs,
                    duration=butter,
                    delay=delay
                )
                com_anims.append(anim)
            # placeholder
            if not coms:
                w = Widget.TEXT(
                    root,
                    position=(com_x+box_x/2+marg,com_yp+com_ys/2.3),
                    h_align=Const.ALIGN_CENTER,
                    text=String.NO_COMMENTS
                )
                com_widgets.append(w)
            # finally
            nonlocal loaded
            loaded = True
        off_up = box_y*2+marg*4
        com_ys = ys-off_up
        com_yp = marg*2+off_up
        last_size = (cx+marg-2,com_ys)
        com_scroll = Widget.SCROLL(
            root,
            size=last_size,
            position=(com_x-marg/2,com_yp)
        )
        com_root = Widget.CONTAINER(com_scroll)
        foo = Widget.FOO(com_root)
        rf_x = x-(bx+marg*2+2)
        rf_y = y-(bx+marg*2)
        Widget.BUTTON(
            root,
            position=(rf_x,rf_y),
            size=(bx,bx),
            color=Color.WARM,
            on_activate_call=refresh
        )
        Widget.IMAGE(
            root,
            position=(rf_x + bx*0.1, rf_y + bx*0.1),
            size=(bx*0.8, bx*0.8),
            texture=Eval.TEXTURE(Const.IMG_REFRESH),
            color=Color.TEXT
        )
        loaded = True
        refresh(shut=True)
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
            im = Eval.IMG_FILE(n)
            gay = 5 if im in (
                Const.IMG_FILE,
                Const.IMG_DEFAULT,
                Const.IMG_SCRIPT
            ) else marg
            Widget.IMAGE(
                file_root,
                position=(i*step+gay,xt-marg),
                size=(file_x,file_x),
                texture=Eval.TEXTURE(im)
            )
            if im == Const.IMG_FILE:
                Widget.TEXT(
                    file_root,
                    position=(i*step+gay+file_x-54,xt-marg*2),
                    text=Eval.FILE_EXTENTION(n),
                    size=(file_x,30),
                    big=True,
                    opacity=Color.OPACITY/2,
                    rotate=90,
                    maxwidth=file_x*0.5
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

    def comment_window(s,com,source):
        bx = 50
        marg = 10
        x,y = Eval.REAL(margin=0.4)
        size = (x,y)
        Eval.SOUND(Const.SOUND_HI)
        # root
        root = Widget.WINDOW(
            source=source,
            size=size
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
                position=(marg*2,py),
                size=(bx,bx),
                label=Eval.CHAR(Const.CHAR_BACK),
                text_scale=0.8,
                on_activate_call=back,
                color=Color.WARM
            )
        ))
        # copy
        def cp():
            if not bui.clipboard_is_supported():
                Eval.SOUND(Const.SOUND_BAD)
                s.toast(String.CLIPBOARD_UNSUPPORTED)
                return
            Eval.SOUND(Const.SOUND_DING)
            bui.clipboard_set_text(com['text'])
            s.toast(String.COPIED)
        Widget.BUTTON(
            root,
            position=(marg*2,py-(bx+marg*2)),
            size=(bx,bx),
            label=Eval.CHAR(Const.CHAR_COPY),
            text_scale=0.8,
            color=Color.WARM,
            on_activate_call=cp
        )
        # user
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
            text=Eval.FORMAT_USER(com['user_hash']),
            position=(bx+marg*5,py+marg),
            maxwidth=dx-marg*2,
            v_align=Const.ALIGN_CENTER
        )
        Widget.IMAGE(
            root,
            position=(px,marg*2-1),
            size=(dx,bsy),
            color=Color.COLD
        )
        # block
        blk_y = bsy-(bx+marg*2)+2
        Widget.IMAGE(
            root,
            position=(marg*2-2,marg*2-1),
            size=(bx+4,blk_y),
            color=Color.WARM
        )
        # id
        Widget.TEXT(
            root,
            text=com['id'],
            rotate=90,
            position=(marg+bx/1.43,marg*2),
            opacity=Color.OPACITY/2,
            v_align=Const.ALIGN_CENTER,
            maxwidth=blk_y-marg*4
        )
        # text
        py -= (bx+marg)
        mw = x-(bx+marg*4)
        mh = y-(bx+marg*7)
        Widget.TEXT(
            root,
            position=(px+marg,py),
            maxwidth=mw-marg*4,
            max_height=mh,
            text=fit_string(com['text'],mw,mh)
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
                size=(art_sx,art_sy)
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
            nam = file['original_name']
            def _abort(e):
                switch()
                s.toast(Eval.FORMAT_ERROR(e))
                Eval.DOUBLE_DING(0,0)
            try:
                acquire(
                    uh,
                    file['id'],
                    Eval.FORMAT_DOWNLOAD_PATH(nam)
                )
            except Exception as e:
                bui.pushcall(
                    bui.CallPartial(_abort,e),
                    from_other_thread=True
                )
                return
            def _done():
                switch()
                s.toast(Eval.FORMAT_DOWNLOADED(nam))
                Eval.DOUBLE_DING(0,1)
            bui.pushcall(_done,from_other_thread=True)
        def download():
            nonlocal clickable
            if not clickable:
                Eval.SOUND(Const.SOUND_BAD)
                return
            clickable = False
            switch()
            Thread(target=_acquire).start()
            Eval.DOUBLE_DING(1,0)
            s.toast(String.DOWNLOADING)
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
                s.toast(String.CLIPBOARD_UNSUPPORTED)
                return
            Eval.SOUND(Const.SOUND_DING)
            bui.clipboard_set_text(file['path'])
            s.toast(String.COPIED)
        art_sx = dx-marg*4
        art_sy = art_sx-100
        art_x = px+marg*2
        art_y = bsy/2-art_sy/8
        py -= (marg*2+bx+2)
        Widget.BUTTON(
            root,
            position=(marg*2,py),
            size=(bx,bx),
            label=Eval.CHAR(Const.CHAR_COPY),
            text_scale=0.8,
            color=Color.WARM,
            on_activate_call=cp
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
    def __init__(s, parent, position, size, opacity=None,**kw):
        s.opacity = opacity or Color.OPACITY
        s.parent = parent
        px, py = position
        sx, sy = size
        # text
        text = String.BOARD
        num_letters = len(text)
        # calculate letter sizing
        letter_height = sy * 0.5
        letter_scale = letter_height / 40
        total_text_width = sx
        gap = total_text_width / num_letters if num_letters > 1 else 0
        letter_start_x = px
        letter_y = py
        # shadow
        xoff = sx*0.1
        yoff = letter_height*0.2
        s.shadow = Widget.IMAGE(
            parent,
            position=(px-xoff,py-yoff),
            size=(sx+xoff*2,letter_height+yoff*2),
            texture=Eval.TEXTURE(Const.IMG_SHADOW),
            opacity=s.opacity/2.5,
        )
        # bg
        s.bg = Widget.IMAGE(
            parent,
            position=position,
            size=(sx,letter_height),
            texture=Eval.TEXTURE(Const.IMG_REFLECTION),
            opacity=s.opacity
        )
        # create letters
        s.kids = [
            Widget.TEXT(
                parent,
                flatness=-2.5,
                big=True,
                text=t,
                position=(letter_start_x + gap * i, letter_y),
                opacity=s.opacity,
                scale=letter_scale,
                size=(gap, letter_height),
                h_align=Const.ALIGN_CENTER,
                v_align=Const.ALIGN_CENTER,
                **kw
            )
            for i, t in enumerate(text)
        ]
        # color animation state
        off = random()
        s.art_color_idx = [int(off * len(Const.ART)) for _ in range(num_letters)]
        s.art_progress = [i * 0.1 + off for i in range(num_letters)]
        s.art_timer = bui.AppTimer(0.01, s.animate, repeat=True)
        # progress bar
        bar_height = sy * 0.02
        bar_y = py
        bar_margin = 0 #sx * 0.05
        bar_width = sx - bar_margin * 2
        indicator_width = bar_width * 0.2
        s.pro_base_x = px + bar_margin
        s.pro_base_y = bar_y
        s.pro_width = bar_width
        s.pro_indicator_width = indicator_width
        s.pro_time = 0.0
        # background bar
        s.pro_bg = Widget.IMAGE(
            parent,
            position=(s.pro_base_x, s.pro_base_y),
            opacity=s.opacity/2,
            size=(bar_width, bar_height),
            color=Color.WARM
        )
        # moving indicator
        s.pro = Widget.IMAGE(
            parent,
            position=(s.pro_base_x, s.pro_base_y),
            opacity=s.opacity,
            size=(indicator_width, bar_height),
            color=Color.WARM
        )
        s.anims = {}

    def animate(s):
        for i, k in enumerate(s.kids):
            # variable speed based on current color
            current_idx = s.art_color_idx[i]
            current_color = Const.ART[current_idx]

            # speed up if red is dominant (R high, G low, B low)
            # The red one is: (3.0, 0.3, 0.3)
            if current_idx in (0,2):
                speed = 0.03
            else:
                speed = 0.02

            s.art_progress[i] -= speed
            if s.art_progress[i] < 0:
                s.art_progress[i] += 1.0
                s.art_color_idx[i] = (s.art_color_idx[i] + 1) % len(Const.ART)
            current_idx = s.art_color_idx[i]
            next_idx = (current_idx + 1) % len(Const.ART)
            progress = s.art_progress[i] % 1.0
            r,g,b,a = tuple(
                Const.ART[current_idx][j] * progress +
                Const.ART[next_idx][j] * (1 - progress)
                for j in range(3)
            )+(s.opacity,)
            if not k.exists():
                s.art_timer = None
                return
            bui.textwidget(k, color=(r,g,b,a))

        # progress bar animation
        s.pro_time += 0.02
        cycle = (s.pro_time % 2.0) / 2.0
        t = cycle * 2
        t = t if t < 1 else 2 - t
        t = t * t * (3.0 - 2.0 * t)
        x_offset = (s.pro_width - s.pro_indicator_width) * t

        # sample 3 gradient colors for bg
        base_idx = s.art_color_idx[0]
        base_prog = s.art_progress[0] % 1.0

        # color 1: current position
        idx1, idx1_next = base_idx, (base_idx + 1) % len(Const.ART)
        c1 = tuple(Const.ART[idx1][j] * base_prog + Const.ART[idx1_next][j] * (1 - base_prog) for j in range(3))

        bui.imagewidget(s.bg, color=c1, tint_color=c1, tint2_color=c1)
        bui.imagewidget(
            s.pro,
            position=(s.pro_base_x + x_offset, s.pro_base_y),
            color=c1
        )
        bui.imagewidget(s.pro_bg, color=c1)
        bui.imagewidget(s.shadow, color=c1)

    def fade_out(s, duration=0.3, on_finish=None):
        s.art_timer = None
        s.anims[id(s.bg)] = Animate(
            widget=s.bg,
            attrs={'opacity': (s.opacity, 0)},
            duration=duration
        )
        s.anims[id(s.shadow)] = Animate(
            widget=s.shadow,
            attrs={'opacity': (s.opacity, 0)},
            duration=duration
        )
        for kid in s.kids:
            if not kid.exists():
                return
            s.anims[id(kid)] = Animate(
                widget=kid,
                attrs={'color': (Eval.TEXT(s.opacity), Const.INVISIBLE)},
                duration=duration
            )
        s.anims[id(s.pro_bg)] = Animate(
            widget=s.pro_bg,
            attrs={'opacity': (s.opacity, 0)},
            duration=duration
        )
        s.anims[id(s.pro)] = Animate(
            widget=s.pro,
            attrs={'opacity': (s.opacity, 0)},
            duration=duration,
            on_finish=on_finish
        )

    def delete(s):
        s.art_timer = None
        s.pro_bg.delete()
        s.pro.delete()
        for k in s.kids:
            k.delete()
        s.bg.delete()
        s.shadow.delete()
        s.kids.clear()
        s.anims.clear()

# widgets
# logic to save code with defaults

class Widget:
    BUTTON = lambda p,label=None,color=None,**kw: bui.buttonwidget(
        parent=p,
        texture=Eval.TEXTURE(Const.IMG_BASE),
        color=color or Color.COLD,
        textcolor=Color.TEXT,
        enable_sound=False,
        opacity=Color.OPACITY,
        label=label or Const.BLANK,
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
    HYPER = lambda p,color=None,opacity=None,**kw: bui.textwidget(
        parent=p,
        color=color or Eval.TEXT(
            Color.OPACITY
            if opacity is None
            else opacity
        ),
        glow_type=Const.GLOW_TYPE,
        selectable=True,
        click_activate=True,
        **kw
    )
    IMAGE = lambda p,opacity=None,texture=None,**kw: bui.imagewidget(
        parent=p,
        opacity=(
            Color.OPACITY
            if opacity is None
            else opacity
        ),
        texture=texture or Eval.TEXTURE(Const.IMG_BASE),
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
            toolbar_visibility=Const.TOOLBAR_VISIBILITY,
            **k
        )),
        (shadow:=Eval.SHADOW(*size)),
        Widget.IMAGE(
            root,
            position=shadow[0],
            size=shadow[1],
            texture=Eval.TEXTURE(Const.IMG_SHADOW),
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
        texture=Eval.TEXTURE(Const.IMG_EMPTY),
        opacity=0,
        enable_sound=False,
        **k
    )
    FOO = lambda p: bui.textwidget(
        parent=p,
        text=Const.BLANK
    )

# evaluation
# static math by various parts in code

class Eval:
    WIDGET = lambda w: getattr(
        bui, w.get_widget_type() + 'widget'
    )
    BY_SCALE = lambda a,b,c:(
        (scale:=bui.app.ui_v1.uiscale) and (
            a if scale is bui.UIScale.SMALL else
            b if scale is bui.UIScale.MEDIUM else
            c
        )
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
    SOUNDS = lambda s1,s2,gap=0.12:(
        (sound:=bui.getsound(s1)).play() or
        (gap and bui.apptimer(gap,sound.stop)) or
        bui.apptimer(gap,bui.getsound(s2).play)
    )
    DOUBLE_DING = lambda i,j: (
        (l:=(Const.SOUND_DONG,Const.SOUND_DING)),
        Eval.SOUNDS(l[i],l[j])
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
    FORMAT_ERROR = lambda e: (
        String.ERROR + (str(e) and (
            Const.COLON + Const.SPACE +
            str(e)
        )) or Const.DOT
    )
    METADATA = lambda t,i: (
        datetime.fromisoformat(t).strftime(Const.TIMESTAMP_FORMAT) +
        Const.SPACE * 3 + i
    )
    COVER_IMG = lambda files: Eval.TEXTURE(
        Const.IMG_DEFAULT if not files
        else Eval.IMG_FILE(files[0]['original_name'])
    )
    IMG_FILE = lambda file: (
        (ty:=guess_type(
            file
        )[0] or Const.BLANK),(
            Const.IMG_AUDIO
            if (
                ty.startswith('audio/') or
                file.endswith('.ogg')
            )
            else Const.IMG_REPLAY
            if file.endswith(Const.VIDEO_PREFIX)
            else Const.IMG_SCRIPT
            if file.endswith('.py')
            else Const.IMAGE_IMG
            if ty.startswith('image/')
            else Const.IMG_FILE
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
    STRING_TYPE = lambda s: (
        0 if s.startswith(Const.URL_PREFIX) else
        1 if s.startswith(Const.URI_PREFIX) else
        2 if s else
        -1
    )
    FORMAT_STRING_TYPE = lambda t,i: [
        String.URL,
        String.URI,
        String.PATH,
        String.HMM
    ][i]
    VALIDATE_URI = lambda t: (
        re.match(Const.VALID_URI,t)
    )
    VALIDATE_URL = lambda t: (
        re.match(Const.VALID_URL,t)
    )
    ELLIPSE_START = lambda t,i: (
        len(t)<=i and t or (Const.ELLIPSIS+t[-i:])
    )
    ELLIPSE_END = lambda t,i: (
        len(t)<=i and t or t[:i]+Const.ELLIPSIS
    )
    FORMAT_DOWNLOADED = lambda t: (
        String.DOWNLOADED + Const.SPACE +
        String.AS + Const.SPACE +
        Const.QUOTE + t + Const.QUOTE
    )
    FLATTEN = lambda t:(
        t.replace(Const.FAKE_NEWLINE,Const.BLANK)
    )
    FILE_EXTENTION = lambda n:(
        n.rsplit(Const.DOT,1)[-1]
        if Const.DOT in n else Const.BLANK
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
    SHADOW = (0.1,0.1,0.1)
    OPACITY = 0.8

Color = Eval.SUBCLASS(Color,Config.COLOR,DarkColor)

# strings
# all text used is defined here

class String: pass

class EnglishString(String):
    ACCESS_DENIED = 'Access denied!'
    AS = 'as'
    ATTACH = 'Attach'
    ATTACH_DONE = 'Attached!'
    BOARD = 'Board'
    BYTES = 'Bytes'
    CLIPBOARD_UNSUPPORTED = 'Clipboard unsupported!'
    COMMENT = 'Comment'
    COMMENTS = 'Comments'
    COMMENT_SENT = 'Comment sent! It should be availabe in seconds.'
    COPIED = 'Copied to clipboard!'
    DESCRIPTION = 'Description'
    DOWNLOADED = 'Saved to downloads'
    DOWNLOADING = 'Downloading... (you can close this window)'
    EMPTY = 'Empty'
    ENTER_PASSWORD = 'Enter password!'
    ENTER_SOMETHING = 'Enter something!'
    ERROR = 'An error occured'
    FILE = 'File'
    FILE_NOT_FOUND = 'File not found!'
    FILES = 'Files'
    HELP_POST = 'Press NL to break line, better just paste text here tho'
    HINT_ATTACH = 'Path, URL, URI or FullPath'
    HMM = 'Hmm'
    INVALID_URI = 'Invalid URI!'
    NEW_POST = 'New Post'
    NL = 'NL'
    NOT_NOW = 'Not now I\'m busy!'
    NO_COMMENTS = 'No comments'
    NO_DESCRIPTION = 'No description provided.'
    NO_TITLE = 'No title'
    PASSWORD = 'Password'
    PATH = 'Path'
    PATH_MEANS = 'Path: uploads file'
    PUBLISHED = 'Post published! It should be availabe in seconds.'
    SELECT_SOMETHING = 'Select something!'
    SENDING_COMMENT = 'Sending comment, please wait...'
    TITLE = 'Title'
    UPLOADING = 'Uploading, please wait...'
    URI = 'URI'
    URL = 'URL'
    URL_MEANS = 'URL/URI: directly sent to server'
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
    IMG_BASE = 'white'
    IMG_SHADOW = 'softRect'
    IMG_DEFAULT = 'star'
    IMG_FILE = 'file'
    IMG_FOLDER = 'folder'
    IMG_SCRIPT = 'settingsIcon'
    IMG_EMPTY = 'empty'
    IMAGE_IMG = 'alwaysLandBGColor'
    IMG_REPLAY = 'tv'
    IMG_REFRESH = 'replayIcon'
    IMG_AUDIO = 'audioIcon'
    IMG_DOT_DOT = 'replayIcon'
    IMG_REFLECTION = 'reflectionSoft_+y'
    BUTTON_TYPE = 'square'
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
    TOOLBAR_VISIBILITY = 'no_menu_minimal'
    SOUND_HI = 'powerup01'
    SOUND_OK = 'deek'
    SOUND_DING = 'dingSmallHigh'
    SOUND_DONG = 'dingSmall'
    SOUND_BAD = 'block'
    SOUND_BYE = 'laser'
    SOUND_ACTION = 'gunCocking'
    GLOW_TYPE = 'uniform'
    SPACE = ' '
    BLANK = ''
    NEWLINE = '\n'
    FAKE_NEWLINE = '\\n'
    ELLIPSIS = '...'
    QUOTE = '\''
    COLON = ':'
    DOT = '.'
    DOT_DOT = '..'
    FILENAME_MAX = 20
    PATH_MAX = 50
    COMMENT_MAX = 40
    BA_LAG_SMALL = 0.01
    BA_LAG = 0.04
    ART = (
        (2.0, 0.3, 2.2),
        (2.2, 0.3, 1.5),
        (3.0, 0.3, 0.3),
        (2.2, 1.8, 0.3),
        (0.3, 2.0, 1.8),
    )
    TRANSITION = (
        ('in_left','out_left'),
        ('in_scale','out_scale')
    )
    INVISIBLE = (0,0,0,0)
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
    URL_PREFIX = ('http://', 'https://', 'ftp://')
    URI_PREFIX = ('data:')
    VIDEO_PREFIX = ('mkv','brp','mp4','webm')
    VALID_URI = r'data:([^;,]+)?(;base64)?,(.+)'
    VALID_URL = r'https?://.+'
    TIMESTAMP_FORMAT = '%d/%m/%y %H:%M:%S'

# tools
# they do big stuff

def fit_string(text, max_width, max_height=None):
    if not text: return Const.BLANK
    result_lines = []
    line_height = 20

    # If height is constrained, calculate effective width
    effective_width = max_width
    if max_height:
        max_lines = int(max_height / line_height)
        # Do a first pass to see how many lines we'd get
        temp_lines = []
        for paragraph in text.split(Const.NEWLINE):
            words = paragraph.split()
            if not words:
                temp_lines.append('')
                continue
            current_line, current_width = [], 0
            for word in words:
                word_width = Eval.STRING_WIDTH(word)
                space_width = Eval.STRING_WIDTH(Const.SPACE)
                needed = current_width + (space_width if current_line else 0) + word_width
                if needed > max_width:
                    temp_lines.append(Const.SPACE.join(current_line))
                    current_line, current_width = [word], word_width
                else:
                    current_line.append(word)
                    current_width = needed
            if current_line:
                temp_lines.append(Const.SPACE.join(current_line))

        # If we'd exceed max_lines, increase effective width to compensate
        if len(temp_lines) > max_lines:
            scale_factor = max_lines / len(temp_lines)
            effective_width = max_width / scale_factor

    # Now do the actual wrapping with effective_width
    for paragraph in text.split(Const.NEWLINE):
        lines, current_line, current_width = [], [], 0
        for word in paragraph.split():
            word_width = Eval.STRING_WIDTH(word)
            space_width = Eval.STRING_WIDTH(Const.SPACE)
            if max_height and len(result_lines) * line_height >= max_height:
                break
            if word_width > effective_width:
                if current_line:
                    lines.append(Const.SPACE.join(current_line))
                    current_line, current_width = [], 0
                chunk, chunk_width = [], 0
                for char in word:
                    char_width = Eval.STRING_WIDTH(char)
                    if chunk_width + char_width > effective_width:
                        lines.append(Const.BLANK.join(chunk))
                        chunk, chunk_width = [char], char_width
                    else:
                        chunk.append(char)
                        chunk_width += char_width
                if chunk:
                    current_line, current_width = [Const.BLANK.join(chunk)], chunk_width
            else:
                needed = current_width + (space_width if current_line else 0) + word_width
                if needed > effective_width:
                    lines.append(Const.SPACE.join(current_line))
                    current_line, current_width = [word], word_width
                else:
                    current_line.append(word)
                    current_width = needed
        if current_line:
            lines.append(Const.SPACE.join(current_line))
        result_lines.extend(lines)

    return Const.NEWLINE.join(result_lines)

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
        # Check if it's a URL
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

        # Check if it's a data URI
        elif item.startswith('data:'):
            # Parse data URI format: data:[<mediatype>][;base64],<data>
            import re
            match = re.match(r'data:([^;,]+)?(;base64)?,(.+)', item)
            if not match:
                continue  # Skip invalid data URIs

            mime_type = match.group(1) or 'application/octet-stream'
            is_base64 = match.group(2) is not None
            data = match.group(3)

            # Decode the data
            if is_base64:
                file_content = b64decode(data)
            else:
                # URL-encoded data
                from urllib.parse import unquote
                file_content = unquote(data).encode()

            # Generate filename from mime type
            ext = mime_type.split('/')[-1]
            # Generate a unique name
            unique_id = uuid4().hex[:8]
            original_name = f"data_uri_{unique_id}.{ext}"

            files_data.append({
                "name": original_name,
                "ext": ext,
                "size": len(file_content),
                "data": b64encode(file_content).decode()  # Re-encode for transport
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

def comment(secret, post_id, text):
    """Post a comment on a specific post"""
    stamp = _seal(secret)

    payload_data = {
        "post_id": post_id,
        "user_hash": stamp,
        "text": text
    }

    payload = f"COMMENT:{dumps(payload_data)}"
    subject = f"Comment on {post_id} by user_{stamp}"

    return _forge(subject, payload)

def get_comments(post_id):
    """Get all comments for a specific post"""
    probe = f"{Data.API_URL.real}/repos/{Data.OWNER.real}/{Data.VAULT.real}/contents/database.json"

    req = Request(probe, headers=_get_headers())

    try:
        with urlopen(req) as response:
            meta = loads(response.read().decode())
            raw = b64decode(meta['content'])
            registry = loads(raw.decode('utf-8'))

            comments = registry.get('comments', {}).get(post_id, [])
            return comments
    except HTTPError as e:
        if e.code == 404:
            return []
        raise

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(ba.Plugin):
    has_settings_ui = lambda s: True
    show_settings_ui = lambda s, source: Board(source)
    def __init__(s):
        from bauiv1lib.mainmenu import MainMenuWindow
        old = MainMenuWindow._refresh
        MainMenuWindow._refresh = lambda z:(old(z),s.make(z))
    def make(s,z):
        px,py = -190,Eval.BY_SCALE(-10,-45,-80)
        sx = 60
        bui.buttonwidget(
            (btn:=bui.buttonwidget(
                parent=z._root_widget,
                label=Const.BLANK,
                color=Color.BASE,
                textcolor=Color.TEXT,
                size=(sx,sx),
                position=(px,py),
                button_type=Const.BUTTON_TYPE,
                id=f"{z.main_window_id_prefix}|board",
            )), on_activate_call=bui.CallPartial(
                z.main_window_replace, bui.CallPartial(
                    Board, btn
                )
            )
        )
        i = sx * 0.1
        gap = sx * 0.05
        square_size = (sx - i * 2 - gap) / 2

        for row in range(2):
            for col in range(2):
                bui.imagewidget(
                    parent=z._root_widget,
                    draw_controller=btn,
                    position=(px + i + col * (square_size + gap), 
                             py + i + row * (square_size + gap)),
                    texture=Eval.TEXTURE(Const.IMG_SHADOW),
                    color=Color.SHADOW,
                    size=(square_size, square_size)
                )
