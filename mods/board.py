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
from random import random, uniform
from urllib.error import HTTPError
from mimetypes import guess_type
from datetime import datetime
from time import perf_counter
from json import dumps, loads
from threading import Thread
from zlib import decompress
from hashlib import sha256
from weakref import ref
from uuid import uuid4
from enum import Enum

__version__ = '1.0'

class ConfigManager:
    COLOR = 'Dark'
    STRING = 'English'

    def __setattr__(s, name, value):
        bui.app.config[Const.CONFIG_PREFIX + name] = value
        bui.app.config.commit()
        object.__setattr__(s, name, value)
        glo = globals()
        glo[name.capitalize()] = glo[
            value+getattr(s,'_'+name)
        ]

    def __init__(s):
        for key, value in bui.app.config.items():
            if key.startswith(Const.CONFIG_PREFIX):
                object.__setattr__(s, key[len(Const.CONFIG_PREFIX):], value)
        glo = globals()
        for k in dir(s):
            if not k.startswith('_'):
                cap = k.capitalize()
                nam = getattr(s,k)+cap
                glo[cap] = glo[nam]
                object.__setattr__(s,'_'+k,cap)

class Board(bui.MainWindow):
    CACHE = defaultdict(dict)
    def main_window_should_preserve_selection(s):
        return False
    def get_main_window_state(s):
        s.cleanup()
        cls = type(s)
        return bui.BasicMainWindowState(
            create_call=lambda *a,**k:cls(
                fast=True
            )
        )
    def __init__(s, source=None, fast=False, main=True):
        s.main = main
        s.cache = type(s).CACHE
        s.anims = {}
        s.toast_blink = None
        s.source = source

        s.catalog_widgets = []
        s.catalog_anims = []
        s.rest_anims = []

        s._build_ui()
        super().__init__(
            root_widget=s.root,
            origin_widget=None if fast else source,
            refresh_on_screen_size_changes=True,
            transition=Eval.TRANSITION(
                False if fast else source
            )
        )
        if fast:
            source and bui.containerwidget(
                s.root, scale_origin_stack_offset=(
                    source.get_screen_space_center()
                )
            )
        else: Eval.SOUND(Const.SOUND_HI)
        fast and s.remake_windows()
        if bool(s.cache['catalog'].get('call',None)):
            s.cache['catalog']['call'] = bui.CallPartial(
                s.render,fast=True
            )
            s.make_art(
                continue_from=s.cache['art']
            )
        elif (cat:=s.cache['catalog'].get('data',None)):
            s.render(cat,fast=True)
        else:
            s.refresh(shut=True)
        (f:=s.cache.pop('pending',None)) and f(s)

    def ui_safe(s):
        return s.root.exists() and not s.root.transitioning_out

    def _build_ui(s):
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
            size=size, source=False
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
        bui.buttonwidget(s.back_button, on_activate_call=s.exit)
        bui.containerwidget(s.root, cancel_button=s.back_button)

        # post
        post_x = x - marg - bx
        bui.buttonwidget(
            (btn:=Widget.BUTTON(
                s.root,
                position=(post_x, py),
                size=(bx, bx),
                label=Eval.CHAR(Const.CHAR_POST),
                text_scale=1.1
            )), on_activate_call=bui.CallPartial(s.post_window,btn)
        )

        # refresh
        rf_x = post_x - marg - bx
        Widget.BUTTON(
            s.root,
            position=(rf_x, py),
            size=(bx, bx),
            on_activate_call=s.refresh
        )
        Widget.IMAGE(
            s.root,
            position=(rf_x + bx*0.1, py + bx*0.1),
            size=(bx*0.8, bx*0.8),
            texture=Eval.TEXTURE(Const.IMG_REFRESH),
            color=Color.TEXT
        )

        # settings
        st_x = post_x - (marg+bx)*2
        bui.buttonwidget(
            (btn:=Widget.BUTTON(
                s.root,
                position=(st_x, py),
                size=(bx, bx)
            )), on_activate_call=bui.CallPartial(
                s.settings_window, source=btn
            )
        )
        Widget.IMAGE(
            s.root,
            position=(st_x + bx*0.1, py + bx*0.1),
            size=(bx*0.8, bx*0.8),
            texture=Eval.TEXTURE(Const.IMG_SETTINGS),
            color=Color.TEXT
        )

        # title
        px = back_x + bx + marg
        dx = st_x - px - marg
        Widget.IMAGE(
            s.root,
            position=(px, py - 2),
            size=(dx, dy + 4),
            color=Color.COLD,
        )
        s.title = Widget.TEXT(
            s.root,
            position=(px + marg/2, py + dy/4 - 2),
            text=String.WAIT,
            maxwidth=dx-marg*2
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
            source=False,
            size=(cx, cy)
        )

    def remake(s):
        if s.main:
            ui = bui.app.ui_v1
            ui._last_win_recreate_uiscale = None
            ui._do_main_win_recreate()
        else:
            s.exit(fast=True)
            type(s)(
                source=s.source,
                fast=True,
                main=False
            )

    def remake_windows(s):
        for which,data in s.cache['windows'].items():
            data.pop('root').delete()
            getattr(s,which)(
                data=data
            )

    def render(s, cat, fast=False):
        if not s.root.exists(): return
        s.cache['catalog']['data'] = cat

        art = s.cache['art']
        if art:
            art.fade_out(
                duration=0.3,
                on_finish=s.kill_art
            )
            bui.apptimer(0.2, lambda: s.update_title(String.BOARD))
            bui.apptimer(0.1, lambda: s._render_catalog_content(cat))
        else:
            s.update_title(String.BOARD,fast=fast)
            s._render_catalog_content(cat, fast)

    def _render_catalog_content(s, cat, fast=False):
        if not s.ui_safe(): return
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

        initial_opacity = Color.OPACITY if fast else 0

        for i, c in enumerate(cat, start=1):
            px, py = (0, (marg + ey + xt) * (i - 1))
            files = c['files']

            # bg
            bg = Widget.IMAGE(
                s.scroll_root,
                size=(x, ey),
                position=(px, py),
                color=Color.COLD,
                opacity=initial_opacity
            )
            s.catalog_widgets.append(bg)
            if not fast:
                widgets_to_animate.append((bg, 'opacity', (0, Color.OPACITY), 0.1 + (lc-i)*0.05))

            # head
            head = Widget.IMAGE(
                s.scroll_root,
                size=(x, xt),
                position=(px, py + ey),
                color=Color.WARM,
                opacity=initial_opacity
            )
            s.catalog_widgets.append(head)
            if not fast:
                widgets_to_animate.append((head, 'opacity', (0, Color.OPACITY), 0.1 + (lc-i)*0.05))

            # img
            tex = Eval.COVER_IMG(files)
            img = Widget.IMAGE(
                s.scroll_root,
                position=(px + marg/2, py + marg/2),
                size=(ix, ix),
                texture=tex,
                opacity=initial_opacity,
                tint_texture=tex,
                tint_color=ba.normalized_color(Color.BASE)
            )
            s.catalog_widgets.append(img)
            if not fast:
                widgets_to_animate.append((img, 'opacity', (0, Color.OPACITY), 0.15 + (lc-i)*0.05))

            # user
            user = Widget.TEXT(
                s.scroll_root,
                text=Eval.FORMAT_USER(c['user_hash']),
                position=(marg/2, py + ey + marg/2),
                opacity=initial_opacity
            )
            s.catalog_widgets.append(user)
            if not fast:
                widgets_to_animate.append((user, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY)), 0.15 + (lc-i)*0.05))

            # id
            idx = 70
            id_text = Widget.TEXT(
                s.scroll_root,
                text=Eval.METADATA(c['timestamp'], c['id']),
                position=(x - idx - marg/2, py + ey + marg/2),
                h_align=Const.ALIGN_RIGHT,
                opacity=initial_opacity/2
            )
            s.catalog_widgets.append(id_text)
            if not fast:
                widgets_to_animate.append((id_text, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY/2)), 0.15 + (lc-i)*0.05))

            # title
            title = Widget.TEXT(
                s.scroll_root,
                position=(px + ix + marg*1.5, py + ey - (marg + 30)),
                text=c['title'] or String.NO.format(String.TITLE),
                maxwidth=x - ix - marg*2,
                scale=1.3,
                v_align=Const.ALIGN_CENTER,
                opacity=initial_opacity
            )
            s.catalog_widgets.append(title)
            if not fast:
                widgets_to_animate.append((title, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY)), 0.2 + (lc-i)*0.05))

            # desc
            mw = x - ix - marg*4
            desc = Widget.TEXT(
                s.scroll_root,
                position=(px + ix + marg, py + ey - (marg + 60)),
                text='\n'.join(
                    fit_string(
                        (c['description'] or String.NO.format(String.DESCRIPTION)),
                        mw
                    ).split('\n')[:3]
                ),
                maxwidth=mw,
                max_height=ix - 30,
                opacity=initial_opacity/2
            )
            s.catalog_widgets.append(desc)
            if not fast:
                widgets_to_animate.append((desc, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY/2)), 0.2 + (lc-i)*0.05))

            # sensor
            sensor = Widget.SENSOR(
                s.scroll_root,
                position=(px, py + marg/2),
                size=(x, ey + xt - marg),
            )
            s.catalog_widgets.append(sensor)
            bui.buttonwidget(
                sensor,
                on_activate_call=bui.CallPartial(s.msg_window, c, sensor)
            )

        bui.containerwidget(s.scroll_root, size=(x, ry))

        # Only animate if not fast
        if not fast: s.fade_catalog(widgets_to_animate)
        else: s.temp_cat = widgets_to_animate
        if not s.cache['welcome']:
            s.cache['welcome'] = True
            s.toast(String.WELCOME)

    def fade_catalog(s,widgets,out=False):
        butter = 0.4
        for widget, attr_name, (start, end), delay in widgets:
            if attr_name == 'opacity':
                attrs = {'opacity': (start, end)}
            else:
                attrs = {'color': (start, end)}

            anim = Animate(
                widget=widget,
                attrs=attrs,
                duration=butter,
                delay=delay,
                swapped=out
            )
            s.catalog_anims.append(anim)

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
            s.rest_anims.append(s.toast_zoom)
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
            s.rest_anims.append(s.toast_blink)
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

    def update_title(s, new_text, fast=False,on_finish=None):
        if fast:
            bui.textwidget(
                s.title, text=new_text
            )
            return
        a = Animate(
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
        s.rest_anims.append(a)

    def _change_title_text(s, new_text, on_finish=None):
        # update
        bui.textwidget(s.title, text=new_text)
        # fade
        a = Animate(
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
        s.rest_anims.append(a)

    def make_art(s,continue_from=None):
        s.kill_art()
        x, y = Eval.REAL(margin=0.2)
        art_sx = 350
        art_sy = 250
        s.cache['art'] = Art(
            s.root,
            position=(x/2-art_sx/2,y/2-art_sy/4),
            size=(art_sx,art_sy),
            continue_from=continue_from
        )

    def kill_art(s):
        (art:=s.cache.pop('art',None)) and art.delete()

    def refresh(s,shut=False):
        s.cache['catalog'].pop('data',None)
        if s.cache['catalog'].get('call',None):
            Eval.SOUND(Const.SOUND_BAD)
            return
        shut or Eval.SOUND(Const.SOUND_OK)
        s.update_title(String.WAIT)
        s.make_art()
        def kill():
            for w in getattr(s, 'catalog_widgets', []): w.delete()
            s.catalog_widgets = []
            s.cache['catalog']['call'] = s.render
            Thread(target=s.fetch).start()
        if getattr(s, 'catalog_anims', None):
            for anim in s.catalog_anims: anim.reverse()
            s.catalog_anims = []
            bui.apptimer(0.4, kill)
        else:
            if hasattr(s,'temp_catalog'):
                s.fade_catalog(s.temp_catalog,out=True)
                del s.temp_catalog
            kill()

    def fetch(s):
        try: cat = catalog()
        except Exception as e:
            ba.pushcall(
                bui.CallPartial(
                    bui.textwidget, s.title, text=str(e)
                ),
                from_other_thread=True
            )
        else:
            call = s.cache['catalog'].pop('call',None)
            callable(call) and ba.pushcall(
                bui.CallPartial(call,cat),
                from_other_thread=True
            )

    def cleanup(s):
        for a in s.anims.values(): a.cancel()
        for a in s.catalog_anims: a.cancel()
        for a in s.rest_anims: a.cancel()
        s.anims.clear()
        s.catalog_anims.clear()
        s.rest_anims.clear()
        s.toast_timer = None

    def exit(s,fast=False):
        s.cleanup()
        fast or Eval.SOUND(Const.SOUND_BYE)
        if s.main:
            s.main_window_back()
        else:
            if fast:
                s.root.delete()
            else: bui.containerwidget(
                s.root, transition=Eval.TRANSITION(
                    s.source, out=True
                )
            )

    def post_window(s,source=None,data=None):
        if s.cache['catalog'].get('call',None):
            Eval.SOUND(Const.SOUND_BAD)
            return
        s.cache['windows']['post_window'] = data = data or {}
        size = x,y = Eval.REAL(margin=0.4)
        data or Eval.SOUND(Const.SOUND_HI)
        busy = False
        # root
        root = data['root'] = Widget.WINDOW(
            source=False if data else source,
            size=size
        )
        # back
        bx = 50
        marg = 10
        px,py = bx+marg*4,y-bx-marg*2
        dx,dy = x-(bx+marg*6),bx
        bsy = y-(marg*6+dy)
        def back(shut=False):
            if not root.exists(): return
            bui.containerwidget(
                root,transition=Eval.TRANSITION(
                    source,True
                )
            )
            shut or Eval.SOUND(Const.SOUND_BYE)
            s.cache['windows'].pop('post_window')
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
                s.toast(String.ENTER.format(String.PASSWORD))
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
        # capture
        def capture(t,k,f=None):
            data[k] = t
            callable(f) and f(t)
        # title in
        t_px = bx+marg*6.65
        t_sx = dx*0.65-(bx+marg*2)
        data['title'] = t = data.get('title','')
        title_inp = Input(
            root,
            position=(t_px,py-marg*2),
            size=(t_sx,bx),
            hint=String.TITLE,
            maxwidth=t_sx-marg*2,
            on_edit=lambda t:capture(t,'title'),
            text=t
        )
        # password in
        def set_as(t):
            bui.textwidget(
                title,
                text=(
                    t and String.POST_BY.format(Eval.SEAL_PASSWORD(t))
                    or String.NEW_POST
                )
            )
        p_px = t_px + t_sx + marg*2
        p_sx = dx - (t_sx + marg*6)
        data['pass'] = t = data.get('pass','')
        pass_inp = Input(
            root,
            position=(p_px,py-marg*2),
            size=(p_sx,bx),
            hint=String.PASSWORD,
            maxwidth=p_sx-marg*2,
            on_edit=lambda t:capture(t,'pass',set_as),
            text=t
        )
        # newline
        def nl():
            if not desc_inp.text:
                Eval.SOUND(Const.SOUND_BAD)
                s.toast(String.ENTER.format(String.SOMETHING))
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
        data['desc'] = t = data.get('desc','')
        desc_inp = Input(
            root,
            position=(t_px+marg/2,py-(bx+marg)),
            size=(sx,bx*2),
            hint=String.DESCRIPTION,
            v_align=Const.ALIGN_BOTTOM,
            maxwidth=sx-marg*2,
            on_edit=lambda t:capture(t,'desc'),
            text=t
        )
        def pad():
            for w in (desc_inp.widget,desc_inp.hint_widget):
                bui.textwidget(w,padding=10)
        bui.apptimer(Const.BA_LAG,pad)
        # attach
        def on_attach(*a):
            ui_files.append(a)
            push_file(*a)
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
            tex = Eval.TEXTURE(img)
            to = Widget.IMAGE(
                file_root,
                position=(i*step+gay,xt-marg),
                size=(file_x,file_x),
                texture=tex,
                tint_texture=tex,
                tint_color=ba.normalized_color(Color.BASE)
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
                Widget.SENSOR(
                    file_root,
                    position=corn,
                    size=(file_x,file_x+xt),
                ), on_activate_call=bui.CallPartial(
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
                s.attach_window, btn, pipe=on_attach
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
        # finally
        data['ui_files'] = ui_files = data.get('ui_files',[])
        for a in ui_files: push_file(*a)

    def attach_window(s,source=None,pipe=None,data=None):
        sw = ref(s)
        x,y = Eval.REAL(margin=0.7)
        s.cache['windows']['attach_window'] = data = data or {}
        data or Eval.SOUND(Const.SOUND_HI)
        extra_y = y
        # root
        root = data['root'] = Widget.WINDOW(
            source=False if data else source,
            size=(x,y+extra_y)
        )
        # back
        bx = 50
        marg = 10
        py = y-bx-marg*2+extra_y
        def back(src=None):
            bord = sw()
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
            bord.cache['windows'].pop('attach_window')
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
            data['sus'] = t
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
            bord = sw()
            if not txt or ty < 0:
                Eval.SOUND(Const.SOUND_BAD)
                bord.toast(String.ENTER.format(String.SOMETHING))
                return

            img = Const.IMG_DEFAULT
            # URL
            if ty == 0:
                try:
                    if not Eval.VALIDATE_URL(txt): raise
                except:
                    Eval.SOUND(Const.SOUND_BAD)
                    bord.toast(String.INVALID.format(String.URI))
                    return

            # URI (data:)
            elif ty == 1:
                try:
                    if not Eval.VALIDATE_URI(txt): raise
                except:
                    Eval.SOUND(Const.SOUND_BAD)
                    bord.toast(String.INVALID.format(String.URI))
                    return

            # path (local file)
            else:
                if not os.path.isabs(txt):
                    txt = os.path.join(
                        Const.ROOT_PATH, txt
                    )
                if not os.path.exists(txt):
                    Eval.SOUND(Const.SOUND_BAD)
                    bord.toast(String.NOT_FOUND.format(String.FILE))
                    return
                img = Eval.IMG_FILE(txt)

            # finally
            bord.toast(String.DONE.format(String.ATTACH))
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
        sus = data['sus'] = data.get('sus','')
        inp = Input(
            root,
            position=(bx+marg*5,y-marg*4-bx-sy+extra_y),
            size=(sx,sy),
            hint=String.HINT_ATTACH,
            on_edit=set_sus,
            maxwidth=sx-marg,
            text=sus
        )
        # help
        mw = x-(bx+marg*7)
        Widget.TEXT(
            root,
            position=(bx+marg*4.5,marg*5+extra_y),
            text=String.PATH_INFO,
            maxwidth=mw,
            v_align=Const.ALIGN_CENTER
        )
        Widget.TEXT(
            root,
            position=(bx+marg*4.5,marg*2+extra_y),
            text=String.URL_INFO,
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
            bord = sw()
            if not sl:
                bord.toast(String.SELECT.format(String.SOMETHING))
                Eval.SOUND(Const.SOUND_BAD)
                return
            bui.textwidget(
                inp.widget,
                text=sl
            )
            Eval.SOUND(Const.SOUND_ACTION,cut=False)
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
                size=(dx+2,sy),
            ), source=False
        )
        sy -= 15
        # ls
        def cd(n=Const.DOT_DOT):
            nonlocal wd, sl, ls
            bord = sw()
            new = os.path.normpath(
                os.path.join(wd,n)
            )
            try:
                ls = list(os.scandir(new))
                ls.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                bord.toast(String.ACCESS_DENIED)
                Eval.SOUND(Const.SOUND_BAD)
                return
            wd = data['wd'] = new
            sl = data['sl'] = None
            fresh()
        def slct(f,yes=True):
            nonlocal sl
            sl and yes and bui.textwidget(
                texts[sl], color=Eval.TEXT(Color.OPACITY)
            )
            sl = data['sl'] = f
            w = texts[f]
            bui.textwidget(
                w, color=Color.BASE
            )
            bui.containerwidget(
                ls_root, visible_child=w
            )
        sl = data['sl'] = data.get('sl',None)
        wd = data['wd'] = data.get('wd',Const.ROOT_PATH)
        ls = list(os.scandir(wd))
        ls.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        lx = 30
        fx = 30
        dx -= fx+marg*2
        texts = {}
        trash = []
        def fresh():
            bui.textwidget(
                cwd_text,
                text=Eval.ELLIPSE_START(
                    wd,
                    Const.PATH_MAX
                )
            )
            for w in texts.values(): w.delete()
            texts.clear()
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
                            slct, f.path
                        )
                    )
                )
                if is_dir: trash.append(w)
                else: texts[f.path] = w
        # finally
        fresh()
        sl and slct(sl,yes=False)
        sus and set_sus(sus)

    def pass_window(s,post=None,source=None,pipe=None,data=None,shut=False):
        weak_s = ref(s)
        size = x,y = Eval.REAL(margin=0.7)
        s.cache['windows']['pass_window'] = data = data or {}
        data or Eval.SOUND(Const.SOUND_HI)
        # root
        root = data['root'] = Widget.WINDOW(
            source=False if data else source,
            size=size
        )
        post = data['post'] = post or data['post']
        # back
        bx = 50
        marg = 10
        py = y-bx-marg*2
        def back(shut=False):
            bui.containerwidget(
                root,transition=Eval.TRANSITION(source,True)
            )
            shut or Eval.SOUND(Const.SOUND_BYE)
            weak_s().cache['windows'].pop('pass_window')
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
        correct = data['correct'] = data.get('correct',None)
        ha = data['hash'] = data.get('hash',None)
        # done
        def done():
            # only send correct passwords
            # we don't want server cussing at us
            if not correct or not ha:
                weak_s().toast(
                    ha is None and String.ENTER.format(String.PASSWORD)
                    or String.INCORRECT.format(String.PASSWORD)
                )
                Eval.SOUND(Const.SOUND_BAD)
                return
            callable(pipe) and pipe(inp.text)
            back(shut=shut)
        Widget.BUTTON(
            root,
            position=(x-(bx+marg*2+2),py),
            size=(bx,bx),
            label=Eval.CHAR(Const.CHAR_DONE),
            text_scale=0.8,
            on_activate_call=done,
            color=Color.WARM
        )
        # block
        dx,dy = x-(bx+marg*6),bx
        bsy = y-(marg*6+dy)
        px = bx+marg*4
        Widget.IMAGE(
            root,
            position=(marg*2-2,marg*2),
            size=(bx+4,bsy+2),
            color=Color.WARM
        )
        # hmm
        hmm = Widget.TEXT(
            root,
            text=String.HMM,
            rotate=90,
            position=(marg+bx/1.43,marg*2),
            opacity=Color.OPACITY/2,
            v_align=Const.ALIGN_CENTER,
            maxwidth=bsy-marg*3.5
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
        Widget.TEXT(
            root,
            text=String.DELETE_ID.format(post['id']),
            position=(px+marg*2,py+marg),
            maxwidth=dx-(marg*8+bx),
            v_align=Const.ALIGN_CENTER
        )
        # capture
        def capture(t):
            nonlocal correct, ha
            ha = t and _seal(t) or None
            correct = ha in [post['user_hash']]+Const.ADMIN
            data['text'] = t
            data['hash'] = ha
            bui.textwidget(
                hmm, text=(
                    String.CORRECT if correct else
                    String.WRONG if t else String.HMM
                )
            )
        # inp
        t = data['text'] = data.get('text','')
        t and capture(t)
        inp = Input(
            root,
            text=t,
            hint=String.PASSWORD,
            position=(px+marg*2.5,marg*2+bsy/2-dy/2),
            size=(dx-marg*4,dy),
            on_edit=capture
        )

    def msg_window(s,c=None,source=None,data=None):
        weak_s = ref(s)
        size = x,y = Eval.REAL(margin=0.3)
        s.cache['windows']['msg_window'] = data = data or {}
        data or Eval.SOUND(Const.SOUND_HI)
        # root
        root = data['root'] = Widget.WINDOW(
            source=False if data else source,
            size=size
        )
        c = data['c'] = c or data['c']
        # back
        bx = 50
        marg = 10
        py = y-bx-marg*2
        def back(shut=False):
            if not root.exists(): return
            bui.containerwidget(
                root,transition=Eval.TRANSITION(source,True)
            )
            shut or Eval.SOUND(Const.SOUND_BYE)
            weak_s().cache['windows'].pop('msg_window')
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
        # nuke
        def on_nuke(e=None):
            data.pop('delete_call',None)
            bord = weak_s()
            if e:
                bord.toast(String.ERROR_WITH.format(str(e)) if e else String.ERROR_UNKNOWN)
                Eval.DOUBLE_DING(0,0)
                return
            bord.toast(String.DELETED.format(String.POST))
            Eval.DOUBLE_DING(0,1)
            back(shut=True)
        if data.get('delete_call',None):
            data['delete_call'] = on_nuke
        def _nuke(t):
            try: delete_post(t,c['id'])
            except Exception as e:
                call = bui.CallPartial(
                    data['delete_call'], str(e)
                )
            else: call = data['delete_call']
            bui.pushcall(call,from_other_thread=True)
        def nuke(t):
            data['delete_call'] = on_nuke
            Thread(target=lambda:_nuke(t)).start()
            Eval.DOUBLE_DING(1,0)
            weak_s().toast(String.DELETING)
        bui.buttonwidget(
            (nuke_btn:=Widget.BUTTON(
                root,
                position=(20,py-(bx+marg*2)),
                label=Eval.CHAR(Const.CHAR_DELETE),
                size=(bx,bx),
                text_scale=0.8,
                color=Color.WARM,
            )), on_activate_call=bui.CallPartial(
                s.pass_window,
                post=c,
                source=nuke_btn,
                pipe=nuke,
                shut=True
            )
        )
        # copy
        def cp():
            if not bui.clipboard_is_supported():
                Eval.SOUND(Const.SOUND_BAD)
                s.toast(String.UNSUPPORTED.format(String.CLIPBOARD))
                return
            Eval.SOUND(Const.SOUND_DING)
            bui.clipboard_set_text(
                c['title']+Const.NEWLINE*2+c['description']
            )
            s.toast(String.COPIED)
        Widget.BUTTON(
            root,
            position=(marg*2,py-(bx*2+marg*4)),
            size=(bx,bx),
            label=Eval.CHAR(Const.CHAR_COPY),
            text_scale=0.8,
            color=Color.WARM,
            on_activate_call=cp
        )
        # block
        cx = 350
        px = bx+marg*4
        dx,dy = x-(bx*2+marg*3+cx),bx
        bsy = y-(marg*6+dy)
        Widget.IMAGE(
            root,
            position=(marg*2-2,marg*2),
            size=(bx+4,bsy-(bx*2+marg*4)+2),
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
            text=c['title'] or String.NO.format(String.TITLE),
            maxwidth=dx-marg*4-(bx*2+marg*2),
            scale=1.3,
            v_align=Const.ALIGN_CENTER
        )
        mw = dx-marg*4
        mh = bsy-(file_x+xt+marg*3+30)
        Widget.TEXT(
            root,
            position=(px+marg*1.7,marg+bsy-65),
            text=fit_string(
                c['description'] or String.NO.format(String.DESCRIPTION),
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
                s.toast(String.ENTER.format(String.SOMETHING))
                Eval.SOUND(Const.SOUND_BAD)
                return
            if not pass_inp.text:
                s.toast(String.ENTER.format(String.PASSWORD))
                Eval.SOUND(Const.SOUND_BAD)
                return
            bui.textwidget(
                com_inp.widget,
                text=Const.BLANK
            )
            Eval.DOUBLE_DING(1,0)
            weak_s().toast(String.CAN_CLOSE.format(String.SENDING + ' ' + String.COMMENT.lower()))
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
            bord = weak_s()
            if err:
                Eval.DOUBLE_DING(0,0)
                bord.toast(String.ERROR_WITH.format(err))
                return
            Eval.DOUBLE_DING(0,1)
            bord.toast(String.SENT.format(String.COMMENT))
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
        def capture(t,k):
            data[k] = t
        t = data['com'] = data.get('com','')
        com_inp = Input(
            root,
            position=(com_x+marg*2,marg*3),
            size=(box_x,box_y),
            hint=String.COMMENT,
            on_edit=lambda t:capture(t,'com'),
            text=t
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
        t = data['pass'] = data.get('pass','')
        pass_inp = Input(
            root,
            position=(com_x+marg*2,marg*4+box_y),
            size=(box_x+box_y+marg,box_y),
            hint=String.PASSWORD,
            on_edit=lambda t:capture(t,'pass'),
            text=t
        )
        # list comment
        coms = data['coms'] = data.get('coms',None)
        had_coms = coms is not None
        art = data['art'] = data.get('art',None)
        com_widgets = []
        com_anims = []
        last_anim = None
        com_big = False
        def refresh(shut=False):
            nonlocal loaded
            bord = weak_s()
            if not loaded:
                Eval.SOUND(Const.SOUND_BAD)
                bord.toast(String.NOT_NOW)
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
                        bord.rest_anims.append(last_anim)
                    data['call'] = do_list
                    Thread(target=_get).start()
                    make_art()
                bui.apptimer(0.4, cleanup_and_fetch)
            else:
                if had_coms and not data.get('call',None):
                    do_list()
                    return
                else:
                    if com_widgets:
                        for w in com_widgets: w.delete()
                        com_widgets.clear()
                    if data.get('call',None):
                        data['call'] = do_list
                    else:
                        data['call'] = do_list
                        Thread(target=_get).start()
                    make_art()
        def make_art():
            nonlocal art
            artx = cx-marg*8
            art = data['art'] = Art(
                root,
                position=(com_x+cx/8,com_yp+com_ys/2-artx/8),
                size=(artx,artx/2),
                opacity=Color.OPACITY/1.3,
                continue_from=art
            )
        def kill_art():
            art.fade_out(
                on_finish=art.delete
            )
            data.pop('art',None)
        def _get():
            nonlocal coms
            coms = get_comments(c['id'])
            coms.reverse()
            data['coms'] = coms
            bui.pushcall(data['call'],from_other_thread=True)
        def do_list():
            if not com_scroll.exists(): return
            bord = weak_s()
            nonlocal com_big, had_coms
            last_anim and last_anim.cancel()
            if art:
                kill_art()
                bui.scrollwidget(
                    com_scroll,
                    size=last_size
                )
            # id user_hash text timestamp
            step = 30
            each_y = step*2+marg*2
            ry = 0 if coms is None else (len(coms)*each_y)
            com_ry = max(com_ys-15,ry)
            com_big = ry > (com_ys-15)
            bui.containerwidget(
                com_root,
                size=(cx,com_ry)
            )
            widgets_to_animate = []
            initial_opacity = Color.OPACITY if had_coms else 0
            for i,com in enumerate(coms or []):
                cur_y = i*each_y
                # head
                head = Widget.IMAGE(
                    com_root,
                    color=Color.WARM,
                    size=(cx,step),
                    position=(0,cur_y+step),
                    opacity=initial_opacity
                )
                com_widgets.append(head)
                had_coms or widgets_to_animate.append((head, 'opacity', (0, Color.OPACITY), 0.1 + i*0.05))
                # body
                body = Widget.IMAGE(
                    com_root,
                    color=Color.COLD,
                    size=(cx,step),
                    position=(0,cur_y),
                    opacity=initial_opacity
                )
                com_widgets.append(body)
                had_coms or widgets_to_animate.append((body, 'opacity', (0, Color.OPACITY), 0.1 + i*0.05))
                # user
                user = Widget.TEXT(
                    com_root,
                    text=Eval.FORMAT_USER(com['user_hash']),
                    position=(marg/2,cur_y+step),
                    size=(cx,step),
                    maxwidth=cx-marg*4,
                    v_align=Const.ALIGN_CENTER,
                    opacity=initial_opacity
                )
                com_widgets.append(user)
                had_coms or widgets_to_animate.append((user, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY)), 0.15 + i*0.05))
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
                    opacity=initial_opacity/2
                )
                com_widgets.append(text_widget)
                had_coms or widgets_to_animate.append((text_widget, 'color', (Const.INVISIBLE, Eval.TEXT(Color.OPACITY/2)), 0.15 + i*0.05))
                # sensor
                bui.buttonwidget(
                    (sensor:=Widget.SENSOR(
                        com_root,
                        position=(marg/2,cur_y),
                        size=(cx,step*2)
                    )), on_activate_call=bui.CallPartial(
                        bord.comment_window,
                        com=com,
                        source=sensor,
                        pid=c['id']
                    )
                )
            bui.containerwidget(
                com_root,
                visible_child=foo
            )
            if not had_coms:
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
                    bord.rest_anims.append(anim)
            # placeholder
            if not coms:
                w = Widget.TEXT(
                    root,
                    position=(com_x+box_x/2+marg,com_yp+com_ys/2.3),
                    h_align=Const.ALIGN_CENTER,
                    text=String.NO.format(String.COMMENTS)
                )
                com_widgets.append(w)
            # finally
            nonlocal loaded
            loaded = True
            had_coms = False
            data.pop('call',None)
        off_up = box_y*2+marg*4
        com_ys = ys-off_up
        com_yp = marg*2+off_up
        last_size = (cx+marg-2,com_ys)
        com_scroll = Widget.SCROLL(
            root,
            size=last_size,
            position=(com_x-marg/2,com_yp)
        )
        com_root = Widget.CONTAINER(
            com_scroll,
            source=False
        )
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
        tex = Eval.TEXTURE(Const.IMG_REFRESH)
        Widget.IMAGE(
            root,
            position=(rf_x + bx*0.1, rf_y + bx*0.1),
            size=(bx*0.8, bx*0.8),
            texture=tex,
            tint_texture=tex,
            tint_color=ba.normalized_color(Color.BASE),
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
            text=Eval.COUNT(len(files),String.FILE,String.FILES),
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
            size=(rdx,file_x+xt),
            source=False
        )
        for i,f in enumerate(files):
            n = f['original_name']
            im = Eval.IMG_FILE(n)
            gay = 5 if im in (
                Const.IMG_FILE,
                Const.IMG_DEFAULT,
                Const.IMG_SCRIPT
            ) else marg
            tex = Eval.TEXTURE(im)
            Widget.IMAGE(
                file_root,
                position=(i*step+gay,xt-marg),
                size=(file_x,file_x),
                texture=tex,
                tint_texture=tex,
                tint_color=ba.normalized_color(Color.BASE)
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

    def comment_window(s,com=None,source=None,data=None,pid=None):
        weak_s = ref(s)
        bx = 50
        marg = 10
        x,y = Eval.REAL(margin=0.4)
        s.cache['windows']['comment_window'] = data = data or {}
        size = (x,y)
        data or Eval.SOUND(Const.SOUND_HI)
        # root
        root = data['root'] = Widget.WINDOW(
            source=False if data else source,
            size=size
        )
        com = data['com'] = com or data.get('com',None)
        pid = data['pid'] = pid or data.get('pid',None)
        # back
        py = y-bx-marg*2
        def back(shut=False):
            if not root.exists(): return
            bui.containerwidget(
                root,transition=Eval.TRANSITION(source,True)
            )
            shut or Eval.SOUND(Const.SOUND_BYE)
            s.cache['windows'].pop('comment_window')
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
        # nuke
        def on_nuke(e=None):
            data.pop('delete_call',None)
            bord = weak_s()
            if e:
                bord.toast(String.ERROR_WITH.format(str(e)) if e else String.ERROR_UNKNOWN)
                Eval.DOUBLE_DING(0,0)
                return
            bord.toast(String.DELETED.format(String.COMMENT))
            Eval.DOUBLE_DING(0,1)
            back(shut=True)
        if data.get('delete_call',None):
            data['delete_call'] = on_nuke
        def _nuke(t):
            try: delete_comment(t,com['id'],pid)
            except Exception as e:
                call = bui.CallPartial(
                    data['delete_call'], str(e)
                )
            else: call = data['delete_call']
            bui.pushcall(call,from_other_thread=True)
        def nuke(t):
            data['delete_call'] = on_nuke
            Thread(target=lambda:_nuke(t)).start()
            Eval.DOUBLE_DING(1,0)
            weak_s().toast(String.DELETING)
        bui.buttonwidget(
            (nuke_btn:=Widget.BUTTON(
                root,
                position=(20,py-(bx+marg*2)),
                label=Eval.CHAR(Const.CHAR_DELETE),
                size=(bx,bx),
                text_scale=0.8,
                color=Color.WARM,
            )), on_activate_call=bui.CallPartial(
                s.pass_window,
                post=com,
                source=nuke_btn,
                pipe=nuke,
                shut=True
            )
        )
        # copy
        def cp():
            if not bui.clipboard_is_supported():
                Eval.SOUND(Const.SOUND_BAD)
                s.toast(String.UNSUPPORTED.format(String.CLIPBOARD))
                return
            Eval.SOUND(Const.SOUND_DING)
            bui.clipboard_set_text(com['text'])
            s.toast(String.COPIED)
        Widget.BUTTON(
            root,
            position=(marg*2,py-(bx*2+marg*4)),
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
        blk_y = bsy-(bx*2+marg*4)+2
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

    def file_window(s,file=None,source=None,uh=None,data=None):
        weak_s = ref(s)
        s.cache['windows']['file_window'] = data = data or {}
        clickable = True
        butter = 0.2
        bx = 50
        marg = 10
        x,y = Eval.REAL(margin=0.4)
        x /= 2
        size = (x,y)
        data or Eval.SOUND(Const.SOUND_HI)
        # root
        root_parts = Widget.WINDOW(
            source=False if data else source,
            size=size,
            parts=True
        )
        file = data['file'] = file or data['file']
        uh = data['uh'] = uh or data['uh']
        shadow,root_bg,root = root_parts
        data['root'] = root
        # expand
        to_hide = []
        art = data.get('art',None)
        switched = data.get('switched',None)
        anims = {}
        def switch(fast=False):
            nonlocal switched, clickable
            bord = weak_s()
            dur = Const.EPSILON if fast else butter
            if switched:
                clickable = True
                switched = data['switched'] = False
                for w,at in to_hide:
                    if (a:=anims.get(w)): a.cancel()
                    anims[w] = a = Animate(
                        widget=w,
                        duration=dur,
                        attrs=at,
                        swapped=True
                    )
                    bord.rest_anims.append(a)
            else:
                clickable = False
                switched = data['switched'] = True
                for w,at in to_hide:
                    if (a:=anims.get(w)): a.cancel()
                    anims[w] = a = Animate(
                        widget=w,
                        duration=dur,
                        attrs=at
                    )
                    bord.rest_anims.append(a)
        def make_art():
            nonlocal art
            art = data['art'] = Art(
                root,
                position=(art_x,art_y),
                size=(art_sx,art_sy),
                continue_from=data.get('art',None)
            )
        def kill_art():
            art.fade_out(
                duration=butter,
                on_finish=art.delete
            )
            data.pop('art',None)
        # back
        py = y-bx-marg*2
        def back():
            bui.containerwidget(
                root,transition=Eval.TRANSITION(source,True)
            )
            Eval.SOUND(Const.SOUND_BYE)
            weak_s().cache['windows'].pop('file_window')
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
        initial_opacity = 0 if switched else Color.OPACITY
        w = Widget.IMAGE(
            root,
            position=(px,marg*2-1),
            size=(dx,bsy),
            color=Color.COLD,
            opacity=initial_opacity
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
            text=Eval.COUNT(file['size'], String.BYTE, String.BYTES),
            opacity=initial_opacity
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
            try:
                acquire(
                    uh,
                    file['id'],
                    Eval.FORMAT_DOWNLOAD_PATH(nam)
                )
            except Exception as e:
                bui.pushcall(
                    bui.CallPartial(data['abort'],e),
                    from_other_thread=True
                )
                return
            bui.pushcall(
                bui.CallPartial(
                    data['call'], nam
                ),
                from_other_thread=True
            )
        def _done(nam):
            switch()
            kill_art()
            weak_s().toast(String.SAVED_AS.format(nam))
            Eval.DOUBLE_DING(0,1)
            data.pop('call',None)
        def _abort(e):
            switch()
            kill_art()
            weak_s().toast(String.ERROR_WITH.format(str(e)) if e else String.ERROR_UNKNOWN)
            Eval.DOUBLE_DING(0,0)
            data.pop('abort',None)
        def download():
            if not clickable:
                Eval.SOUND(Const.SOUND_BAD)
                return
            switch()
            make_art()
            data['call'] = _done
            data['abort'] = _abort
            Thread(target=_acquire).start()
            Eval.DOUBLE_DING(1,0)
            weak_s().toast(String.DOWNLOADING)
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
            bord = weak_s()
            if not bui.clipboard_is_supported():
                Eval.SOUND(Const.SOUND_BAD)
                bord.toast(String.UNSUPPORTED.format(String.CLIPBOARD))
                return
            Eval.SOUND(Const.SOUND_DING)
            bui.clipboard_set_text(file['path'])
            bord.toast(String.COPIED)
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
        # finally
        if data.get('call',None):
            data['call'] = _done
            data['abort'] = _abort
            make_art()

    def settings_window(s,source=None,data=None):
        weak_s = ref(s)
        x = y = min(Eval.REAL(margin=0.5))
        s.cache['windows']['settings_window'] = data = data or {}
        data or Eval.SOUND(Const.SOUND_HI)
        # root
        root = data['root'] = Widget.WINDOW(
            source=False if data else source,
            size=(x,y)
        )
        data['hi'] = 1
        # back
        bx = 50
        marg = 10
        py = y-bx-marg*2
        def back():
            bui.containerwidget(
                root,transition=Eval.TRANSITION(source,True)
            )
            Eval.SOUND(Const.SOUND_BYE)
            weak_s().cache['windows'].pop('settings_window')
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
        dx,dy = x-(bx+marg*6),bx
        bsy = y-(marg*6+dy)
        px = bx+marg*4
        Widget.IMAGE(
            root,
            position=(marg*2-2,marg*2),
            size=(bx+4,bsy),
            color=Color.WARM
        )
        # version
        Widget.TEXT(
            root,
            text=__version__,
            rotate=90,
            position=(marg+bx/1.43,marg*2),
            opacity=Color.OPACITY/2,
            v_align=Const.ALIGN_CENTER,
            maxwidth=bsy-marg*3.5
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
            text=String.SETTINGS,
            position=(px+marg*2,py+marg),
            maxwidth=dx-marg*4,
            v_align=Const.ALIGN_CENTER
        )
        # color
        color_x = dx/2
        ex = 30
        Widget.TEXT(
            root,
            position=(px+marg,marg*3),
            size=(color_x-40,ex),
            text=String.THEME,
            maxwidth=color_x-marg*2,
            h_align=Const.ALIGN_CENTER,
            v_align=Const.ALIGN_CENTER
        )
        glo = globals()
        colors = [
            glo[_] for _ in glo
            if _.endswith(Config._COLOR)
            and not _ == Config._COLOR
        ]
        waffle_w = color_x/2
        waffle_px = color_x/8
        step = waffle_w+waffle_px
        color_y = len(colors)*step+waffle_px
        color_root = Widget.CONTAINER(
            Widget.SCROLL(
                root,
                position=(px,ex+marg*3),
                size=(color_x,bsy-(ex+marg))
            ),
            source=False,
            size=(color_x,color_y)
        )
        def apply(color):
            color_name = Config.COLOR = color.__name__[
                :-len(Config._COLOR)
            ]
            Eval.SOUND(Const.SOUND_ACTION,cut=False)
            s.cache['pending'] = lambda bord:(
                bord.toast(color_name)
            )
            s.remake()
        waffles = [
            Waffle(
                color_root,
                theme=color,
                position=(waffle_px,waffle_px+i*step),
                width=waffle_w,
                on_activate_call=bui.CallPartial(
                    apply, color
                )
            ).waffle
            for i,color in enumerate(colors)
        ]
        (i:=colors.index(Color)-1)<0 and (i:=0)
        bui.containerwidget(
            color_root,
            visible_child=waffles[i]
        )
        # language
        px += color_x
        lang_x = dx/2
        ex = 30
        Widget.TEXT(
            root,
            position=(px+marg,marg*3),
            size=(color_x-40,ex),
            text=String.LANGUAGE,
            maxwidth=color_x-marg*2,
            h_align=Const.ALIGN_CENTER,
            v_align=Const.ALIGN_CENTER
        )
        langs = [
            glo[_] for _ in glo
            if _.endswith(Config._STRING)
            and not _ == Config._STRING
        ]
        del glo
        step = 30
        lang_y = max(len(langs)*step+waffle_px,bsy-(ex+15))
        lang_root = Widget.CONTAINER(
            Widget.SCROLL(
                root,
                position=(px,ex+marg*3),
                size=(lang_x,bsy-(ex+marg))
            ),
            source=False,
            size=(lang_x,lang_y)
        )
        get_name = lambda l: l.__name__[
           :-len(Config._STRING)
        ]
        def apply(lang):
            Config.STRING = get_name(lang)
            Eval.SOUND(Const.SOUND_ACTION,cut=False)
            s.cache['pending'] = lambda bord:(
                bord.toast(String.LANGUAGE_IS_NOW)
            )
            s.remake()
        hypers = [
            Widget.HYPER(
                lang_root,
                text=get_name(lang),
                size=(lang_x,step),
                position=(0,step*i+waffle_px),
                on_activate_call=bui.CallPartial(
                    apply, lang
                )
            ) for i,lang in enumerate(langs)
        ]
        bui.containerwidget(
            lang_root,
            visible_child=hypers[langs.index(String)]
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
        s.hint_opacity = s.hint_up and (s.opacity / 2) or 0
        kw.update({
            'v_align':v_align or Const.ALIGN_CENTER,
            'opacity':s.opacity,
            'description':hint,
            'maxwidth':kw['size'][0]
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
    def __init__(s, parent, position, size, opacity=None, continue_from=None, **kw):
        s.opacity = opacity or Color.OPACITY
        s.parent = parent
        px, py = position
        sx, sy = size
        # text
        text = s.text = String.ART_WORD
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
        # color animation state - CONTINUE FROM PREVIOUS OR START FRESH
        if (
            continue_from and
            isinstance(continue_from, Art)
            and text == continue_from.text
        ):
            # Copy state from previous art object
            s.art_color_idx = continue_from.art_color_idx.copy()
            s.art_progress = continue_from.art_progress.copy()
            s.pro_time = continue_from.pro_time
        else:
            # Fresh start
            off = random()
            s.art_color_idx = [int(off * len(Const.ART)) for _ in range(num_letters)]
            s.art_progress = [i * 0.1 + off for i in range(num_letters)]
            s.pro_time = 0.0

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

class Waffle:
    def __init__(s,parent,theme,width,position,opacity=None,patch={},**k):
        s.theme = theme
        s.parent = parent
        s.width = width
        s.position = position
        s.patch = patch
        s.colors = [
            s.theme.SHADOW,
            s.theme.TEXT,
            s.theme.COLD,
            s.theme.BASE
        ]
        s.waffle = bui.buttonwidget(
            parent=parent,
            label=Const.BLANK,
            button_type=Const.BUTTON_TYPE,
            enable_sound=False,
            color=s.theme.BASE,
            size=(width,width),
            position=position,
            opacity=(
                s.theme.OPACITY if opacity is None
                else opacity
            ),
            texture=Eval.TEXTURE(Const.IMG_BASE),
            **patch,
            **k
        )
        s.waffie()
    def waffie(s):
        i = s.width * 0.1
        gap = s.width * 0.05
        width = (s.width - i * 2 - gap) / 2
        px,py = s.position

        s.waffies = [
            bui.imagewidget(
                parent=s.parent,
                draw_controller=s.waffle,
                position=(
                    px + i + col * (width + gap),
                    py + i + row * (width + gap)
                ),
                texture=Eval.TEXTURE(Const.IMG_SHADOW),
                color=color,
                size=(width, width),
                opacity=s.theme.OPACITY,
                **s.patch
            )
            for (row, col), color in zip(
                ((r, c) for r in range(2) for c in range(2)),
                s.colors
            )
        ]

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
        scale_origin_stack_offset=source and source.get_screen_space_center() or None,
        transition=Eval.TRANSITION(source),
        toolbar_visibility=Const.TOOLBAR_VISIBILITY,
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
        source is False and Const.TRANSITION[-1]
        or Const.TRANSITION[bool(source)][out]
    )
    SUBCLASS = lambda cls,sub,fallback: next(
        (c for c in cls.__subclasses__()
        if c.__name__[:-len(cls.__name__)] == sub), fallback
    )
    SOUND = lambda which,cut=True:(
        (sound:=bui.getsound(which)).play() or
        cut and bui.apptimer(uniform(0.13,0.16),sound.stop)
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
    SEAL_PASSWORD = lambda t: (
        Eval.FORMAT_USER(_seal(t))
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
    COUNT = lambda c, singular, plural: (
        str(c) + Const.SPACE +
        (singular if c == 1 else plural)
    )
    STRING_WIDTH = lambda s: (
        bui.get_string_width(s,suppress_warning=True) or
        sum(Const.FONT_METRICS.get(c, 30) for c in s)
    )
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
        len(t)<(i+3) and t or ('...'+t[-i:])
    )
    ELLIPSE_END = lambda t,i: (
        len(t)<(i+3) and t or (t[:i]+'...')
    )
    FLATTEN = lambda t:(
        t.replace(Const.FAKE_NEWLINE,Const.BLANK)
    )
    FILE_EXTENTION = lambda n:(
        n.rsplit('.',1)[-1]
        if '.' in n else Const.BLANK
    )

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
    def __init__(s, widget, attrs, duration, on_start=None, on_finish=None, on_cancel=None, delay=0, condition=None, on_reverse=None, swapped=False):
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
            swapped: If True, reverses all (start, end) pairs in attrs
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
            # Swap if requested
            if swapped:
                start_val, end_val = end_val, start_val

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

        # done yay
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

RSA_N = 27321016455872970153435061322102843068117802788066857575354989798581441304368333543812172900582339893414374885719022106941726835586910186382053285180800941118539011913752707750584159208680749389405539123498054393651075075550524228812884595667618312831826500182658930289453617762268344437866179838283517261669120873221350569059077320630684008926266200390117790096706692563539867158289318647413060959988455869497749819138508236022241206137457419764137231146887704843917014609242446616024201982853364800053373812825990901307811948186971166417741287726307239433990417229351072712410502988786339036772898038762461642017093
RSA_E = 65537

def _get_headers():
    return {
        "Authorization": f"Bearer github_pat_{Data.KEY.real}"
    }

def _seal(secret):
    return sha256(secret.encode()).hexdigest()[:12]

def _mgf1(seed, length):
    out = b''
    i = 0
    while len(out) < length:
        out += sha256(seed + i.to_bytes(4, 'big')).digest()
        i += 1
    return out[:length]

def _oaep_pad(msg, k):
    h_len = 32
    l_hash = sha256(b'').digest()
    ps = bytes(k - 2*h_len - 2 - len(msg))
    db = l_hash + ps + b'\x01' + msg
    seed = os.urandom(h_len)
    db_mask = _mgf1(seed, k - h_len - 1)
    masked_db = bytes(a ^ b for a, b in zip(db, db_mask))
    seed_mask = _mgf1(masked_db, h_len)
    masked_seed = bytes(a ^ b for a, b in zip(seed, seed_mask))
    return b'\x00' + masked_seed + masked_db

def _encrypt_password(password, context):
    k = (RSA_N.bit_length() + 7) // 8
    padded = _oaep_pad(f"{password}:{context}".encode(), k)
    m = int.from_bytes(padded, 'big')
    c = pow(m, RSA_E, RSA_N)
    return b64encode(c.to_bytes(k, 'big')).decode()

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

    ts = str(int(__import__('time').time()))
    payload_data = {
        "title": title,
        "description": description,
        "user_hash": stamp,
        "timestamp": ts,
        "password": _encrypt_password(secret, ts),
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
        "password": _encrypt_password(secret, post_id),
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

def delete_post(secret, post_id):
    """Delete a post (must be owner)"""
    stamp = _seal(secret)

    payload_data = {
        "post_id": post_id,
        "user_hash": stamp,
        "password": _encrypt_password(secret, f"delete_post:{post_id}"),
    }

    payload = f"DELETE_POST:{dumps(payload_data)}"
    subject = f"Delete post {post_id} by user_{stamp}"

    return _forge(subject, payload)

def delete_comment(secret, comment_id, post_id):
    """Delete a comment (must be owner)"""
    stamp = _seal(secret)

    payload_data = {
        "comment_id": comment_id,
        "post_id": post_id,
        "user_hash": stamp,
        "password": _encrypt_password(secret, f"delete_comment:{comment_id}"),
    }

    payload = f"DELETE_COMMENT:{dumps(payload_data)}"
    subject = f"Delete comment {comment_id} by user_{stamp}"

    return _forge(subject, payload)

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(ba.Plugin):
    has_settings_ui = lambda s: True
    show_settings_ui = lambda s, source: Board(source=source,main=False)
    def __init__(s):
        from bauiv1lib.mainmenu import MainMenuWindow
        old = MainMenuWindow._refresh
        MainMenuWindow._refresh = lambda z:(old(z),s.make(z))
    def make(s,z):
        px,py = -190,Eval.BY_SCALE(-10,-45,-80)
        sx = 60
        bui.buttonwidget(
            (btn:=Waffle(
                z._root_widget,
                theme=Color,
                width=sx,
                position=(px,py),
                id=f"{z.main_window_id_prefix}|board",
                opacity=0.3,
                patch={
                    'transition_delay':z._tdelay+3*z._t_delay_inc
                }
            ).waffle), on_activate_call=bui.CallPartial(
                z.main_window_replace, bui.CallPartial(
                    Board, source=btn
                )
            )
        )

# colors
# generated by claude ai

THEMES = lambda: {
    'Dark': ((0,0,0), (0.08,0.08,0.08), (0.2,0.2,0.2), (2,2,2), (0,0,0), 0.8),
    'Light': ((1,1,1), (0.75,0.75,0.75), (0.6,0.6,0.6), (0,0,0), (0.2,0.2,0.2), 0.8),
    'Ocean': ((0.05,0.15,0.25), (0.1,0.3,0.45), (0.2,0.5,0.7), (0.9,0.95,1), (0,0.05,0.1), 0.8),
    'Forest': ((0.1,0.2,0.1), (0.15,0.35,0.15), (0.3,0.5,0.2), (0.9,0.95,0.85), (0.05,0.1,0.05), 0.8),
    'Sunset': ((0.2,0.1,0.15), (0.5,0.2,0.3), (0.9,0.4,0.2), (1,0.95,0.9), (0.1,0.05,0.1), 0.8),
    'Cherry': ((0.95,0.9,0.92), (0.9,0.7,0.8), (1,0.75,0.85), (0.3,0.15,0.25), (0.8,0.6,0.7), 0.8),
    'Midnight': ((0.05,0.05,0.15), (0.1,0.1,0.3), (0.2,0.15,0.4), (0.7,0.8,1), (0,0,0.05), 0.8),
    'Desert': ((0.3,0.25,0.15), (0.6,0.5,0.3), (0.85,0.65,0.35), (0.95,0.9,0.8), (0.15,0.1,0.05), 0.8),
    'Lavender': ((0.9,0.88,0.95), (0.7,0.65,0.85), (0.8,0.7,0.9), (0.2,0.15,0.3), (0.6,0.55,0.7), 0.8),
    'Cyberpunk': ((0.05,0.05,0.1), (0.15,0.1,0.3), (0.8,0.1,0.5), (0,1,0.9), (0.3,0,0.2), 0.8),
    'Autumn': ((0.25,0.15,0.1), (0.5,0.3,0.15), (0.8,0.4,0.1), (1,0.9,0.7), (0.15,0.08,0.05), 0.8),
    'Minty': ((0.9,0.98,0.95), (0.6,0.9,0.8), (0.4,0.95,0.75), (0.1,0.3,0.25), (0.5,0.8,0.7), 0.8),
    'Slate': ((0.15,0.17,0.2), (0.25,0.28,0.32), (0.4,0.43,0.48), (0.85,0.88,0.92), (0.08,0.09,0.11), 0.8),
    'Amber': ((0.2,0.12,0.05), (0.6,0.4,0.1), (0.95,0.65,0.15), (1,0.95,0.85), (0.12,0.07,0.02), 0.8),
    'Sapphire': ((0.05,0.08,0.2), (0.1,0.2,0.5), (0.2,0.4,0.8), (0.9,0.95,1), (0.02,0.04,0.12), 0.8),
    'Moss': ((0.12,0.18,0.1), (0.25,0.38,0.2), (0.4,0.6,0.3), (0.85,0.95,0.8), (0.06,0.1,0.05), 0.8),
    'Crimson': ((0.2,0.05,0.08), (0.5,0.1,0.15), (0.8,0.15,0.25), (1,0.9,0.92), (0.1,0.02,0.04), 0.8),
    'Ivory': ((0.98,0.96,0.92), (0.9,0.88,0.82), (0.95,0.92,0.85), (0.15,0.12,0.08), (0.75,0.73,0.68), 0.8),
    'Coral': ((0.25,0.18,0.15), (0.7,0.4,0.35), (1,0.5,0.45), (1,0.95,0.93), (0.15,0.1,0.08), 0.8),
    'Teal': ((0.08,0.18,0.18), (0.15,0.4,0.4), (0.25,0.65,0.6), (0.9,1,0.98), (0.04,0.1,0.1), 0.8),
    'Plum': ((0.18,0.1,0.2), (0.4,0.2,0.45), (0.65,0.35,0.7), (0.95,0.88,1), (0.1,0.05,0.12), 0.8),
    'Wheat': ((0.35,0.3,0.2), (0.7,0.6,0.4), (0.95,0.85,0.55), (0.2,0.15,0.1), (0.25,0.2,0.12), 0.8),
    'Lemon': ((0.25,0.25,0.05), (0.7,0.7,0.15), (0.95,0.95,0.25), (0.15,0.15,0.02), (0.15,0.15,0.03), 0.8),
    'Lime': ((0.15,0.22,0.05), (0.4,0.6,0.15), (0.65,0.9,0.25), (0.95,1,0.9), (0.08,0.12,0.02), 0.8),
    'Cyan': ((0.05,0.2,0.22), (0.1,0.5,0.55), (0.2,0.8,0.85), (0.9,1,1), (0.02,0.12,0.13), 0.8),
    'Magenta': ((0.22,0.05,0.2), (0.6,0.15,0.55), (0.9,0.25,0.85), (1,0.9,1), (0.13,0.02,0.12), 0.8),
    'Amoled': ((0,0,0), (0.02,0.02,0.02), (0.05,0.05,0.05), (1,1,1), (0,0,0), 1.0),
    'AmoledBlue': ((0,0,0), (0,0.05,0.12), (0,0.1,0.25), (0.7,0.85,1), (0,0,0), 1.0),
    'AmoledRed': ((0,0,0), (0.12,0,0.02), (0.25,0,0.05), (1,0.75,0.8), (0,0,0), 1.0),
    'AmoledGreen': ((0,0,0), (0,0.1,0.05), (0.05,0.2,0.1), (0.75,1,0.85), (0,0,0), 1.0),
    'AmoledPurple': ((0,0,0), (0.08,0,0.12), (0.15,0,0.25), (0.9,0.75,1), (0,0,0), 1.0),
    'Glass': ((0.95,0.97,1), (0.85,0.9,0.98), (0.75,0.82,0.95), (0.1,0.15,0.25), (0.6,0.7,0.85), 0.3),
    'Frosted': ((0.9,0.92,0.95), (0.7,0.75,0.82), (0.6,0.65,0.75), (0.15,0.18,0.25), (0.5,0.55,0.65), 0.5),
    'Misty': ((0.85,0.88,0.9), (0.65,0.7,0.75), (0.5,0.58,0.65), (0.2,0.25,0.3), (0.45,0.52,0.6), 0.6),
    'Smoke': ((0.3,0.32,0.35), (0.2,0.22,0.25), (0.15,0.17,0.2), (0.85,0.88,0.92), (0.1,0.11,0.13), 0.7),
    'Aurora': ((0.05,0.1,0.15), (0.1,0.3,0.4), (0.2,0.5,0.6), (0.8,0.95,1), (0,0.05,0.08), 0.65),
    'Copper': ((0.18,0.1,0.08), (0.72,0.45,0.2), (0.95,0.6,0.3), (1,0.9,0.8), (0.1,0.05,0.03), 0.8),
    'Bronze': ((0.2,0.15,0.08), (0.55,0.42,0.25), (0.8,0.6,0.35), (1,0.95,0.85), (0.12,0.08,0.04), 0.8),
    'Gold': ((0.25,0.2,0.05), (0.85,0.7,0.15), (1,0.85,0.2), (0.2,0.15,0.02), (0.15,0.12,0.03), 0.8),
    'Silver': ((0.4,0.42,0.45), (0.7,0.72,0.75), (0.9,0.92,0.95), (0.1,0.1,0.12), (0.25,0.27,0.3), 0.8),
    'Pewter': ((0.25,0.27,0.28), (0.45,0.48,0.5), (0.65,0.68,0.7), (0.9,0.92,0.95), (0.15,0.17,0.18), 0.8),
    'Steel': ((0.2,0.22,0.25), (0.4,0.45,0.5), (0.6,0.65,0.72), (0.85,0.9,0.95), (0.12,0.14,0.16), 0.8),
    'Clay': ((0.28,0.22,0.18), (0.6,0.48,0.38), (0.85,0.68,0.52), (0.95,0.9,0.85), (0.18,0.14,0.1), 0.8),
    'Terracotta': ((0.3,0.18,0.12), (0.7,0.42,0.28), (0.95,0.58,0.38), (1,0.95,0.9), (0.18,0.1,0.06), 0.8),
    'Sienna': ((0.25,0.15,0.1), (0.62,0.38,0.25), (0.88,0.55,0.35), (1,0.95,0.88), (0.15,0.08,0.05), 0.8),
    'Umber': ((0.18,0.12,0.08), (0.48,0.32,0.22), (0.72,0.48,0.32), (0.95,0.9,0.82), (0.1,0.06,0.04), 0.8),
    'Ochre': ((0.3,0.25,0.12), (0.72,0.58,0.25), (0.95,0.78,0.35), (0.2,0.15,0.05), (0.18,0.15,0.07), 0.8),
    'Emerald': ((0.05,0.18,0.12), (0.15,0.55,0.35), (0.25,0.82,0.52), (0.9,1,0.95), (0.02,0.1,0.06), 0.8),
    'Ruby': ((0.22,0.05,0.08), (0.65,0.12,0.18), (0.95,0.18,0.28), (1,0.9,0.92), (0.12,0.02,0.04), 0.8),
    'Topaz': ((0.25,0.2,0.08), (0.75,0.62,0.22), (0.98,0.85,0.32), (0.15,0.1,0.02), (0.15,0.12,0.04), 0.8),
    'Onyx': ((0.08,0.08,0.1), (0.18,0.18,0.22), (0.28,0.28,0.32), (0.85,0.85,0.9), (0.04,0.04,0.05), 0.8),
    'Jade': ((0.08,0.2,0.15), (0.25,0.55,0.42), (0.38,0.82,0.62), (0.9,1,0.95), (0.04,0.12,0.08), 0.8),
    'Turquoise': ((0.08,0.22,0.22), (0.25,0.62,0.58), (0.38,0.92,0.85), (0.95,1,1), (0.04,0.12,0.12), 0.8),
    'Peach': ((0.95,0.9,0.88), (0.98,0.75,0.65), (1,0.85,0.72), (0.25,0.15,0.12), (0.75,0.6,0.55), 0.8),
    'Rose': ((0.92,0.88,0.9), (0.95,0.7,0.78), (1,0.8,0.88), (0.3,0.15,0.2), (0.72,0.58,0.65), 0.8),
    'Periwinkle': ((0.88,0.88,0.95), (0.68,0.7,0.92), (0.78,0.8,0.98), (0.15,0.15,0.3), (0.58,0.6,0.75), 0.8),
    'Neon': ((0.05,0.05,0.08), (0.15,0.15,0.25), (0.25,0.25,0.4), (0,1,0.5), (0.02,0.02,0.04), 0.8),
    'Electric': ((0.05,0.08,0.15), (0.12,0.22,0.45), (0.2,0.35,0.75), (0,0.9,1), (0.02,0.04,0.08), 0.8),
    'HotPink': ((0.15,0.05,0.12), (0.55,0.15,0.35), (0.95,0.25,0.65), (1,0.9,0.95), (0.08,0.02,0.06), 0.8),
    'Acid': ((0.15,0.18,0.05), (0.45,0.55,0.15), (0.75,0.95,0.25), (0.98,1,0.9), (0.08,0.1,0.02), 0.8),
    'Spring': ((0.88,0.95,0.9), (0.65,0.88,0.72), (0.52,0.98,0.68), (0.15,0.3,0.2), (0.55,0.75,0.6), 0.8),
    'Summer': ((0.95,0.95,0.85), (0.95,0.88,0.55), (0.98,0.92,0.45), (0.2,0.18,0.08), (0.75,0.72,0.45), 0.8),
    'Winter': ((0.88,0.92,0.98), (0.7,0.78,0.92), (0.6,0.7,0.9), (0.12,0.18,0.3), (0.58,0.65,0.78), 0.8),
    'Dawn': ((0.25,0.18,0.22), (0.85,0.55,0.65), (0.98,0.72,0.78), (1,0.95,0.98), (0.15,0.1,0.12), 0.8),
    'Dusk': ((0.15,0.12,0.18), (0.45,0.32,0.52), (0.72,0.48,0.75), (0.95,0.9,1), (0.08,0.06,0.1), 0.8),
    'Twilight': ((0.12,0.1,0.2), (0.35,0.28,0.55), (0.55,0.42,0.82), (0.88,0.85,1), (0.06,0.05,0.12), 0.8),
    'Noon': ((0.85,0.92,0.98), (0.72,0.85,0.98), (0.58,0.78,1), (0.08,0.15,0.3), (0.62,0.72,0.85), 0.8),
    'Chocolate': ((0.2,0.12,0.08), (0.48,0.3,0.2), (0.72,0.45,0.3), (0.95,0.9,0.85), (0.12,0.07,0.04), 0.8),
    'Caramel': ((0.28,0.22,0.15), (0.68,0.52,0.35), (0.92,0.72,0.48), (1,0.95,0.9), (0.18,0.14,0.08), 0.8),
    'Vanilla': ((0.98,0.95,0.88), (0.95,0.9,0.78), (0.98,0.92,0.82), (0.2,0.15,0.1), (0.78,0.72,0.62), 0.8),
    'Mint': ((0.88,0.98,0.92), (0.65,0.92,0.78), (0.48,0.98,0.75), (0.1,0.25,0.18), (0.58,0.78,0.68), 0.8),
    'Coffee': ((0.15,0.1,0.08), (0.38,0.25,0.2), (0.58,0.38,0.3), (0.92,0.88,0.85), (0.08,0.05,0.04), 0.8),
    'Wine': ((0.18,0.08,0.12), (0.52,0.18,0.28), (0.78,0.28,0.42), (0.98,0.9,0.92), (0.1,0.04,0.06), 0.8),
    'Stone': ((0.35,0.37,0.38), (0.58,0.6,0.62), (0.78,0.8,0.82), (0.15,0.15,0.18), (0.25,0.27,0.28), 0.8),
    'Sand': ((0.45,0.42,0.35), (0.82,0.78,0.62), (0.95,0.9,0.72), (0.2,0.18,0.12), (0.35,0.32,0.25), 0.8),
    'Sky': ((0.65,0.85,0.95), (0.52,0.75,0.92), (0.42,0.68,0.95), (0.08,0.15,0.25), (0.45,0.65,0.78), 0.8),
    'Cloud': ((0.92,0.94,0.96), (0.82,0.85,0.88), (0.75,0.78,0.82), (0.18,0.2,0.25), (0.68,0.72,0.75), 0.8),
    'Fog': ((0.75,0.78,0.8), (0.62,0.65,0.68), (0.52,0.55,0.58), (0.15,0.18,0.22), (0.48,0.52,0.55), 0.7),
    'Storm': ((0.15,0.17,0.2), (0.32,0.35,0.4), (0.48,0.52,0.58), (0.85,0.88,0.92), (0.08,0.1,0.12), 0.8),
    'AmoledOrange': ((0,0,0), (0.12,0.05,0), (0.25,0.1,0), (1,0.8,0.6), (0,0,0), 1.0),
    'AmoledYellow': ((0,0,0), (0.12,0.12,0), (0.25,0.25,0), (1,1,0.7), (0,0,0), 1.0),
    'AmoledCyan': ((0,0,0), (0,0.1,0.12), (0,0.2,0.25), (0.7,1,1), (0,0,0), 1.0),
    'AmoledPink': ((0,0,0), (0.12,0,0.08), (0.25,0,0.15), (1,0.75,0.9), (0,0,0), 1.0),
    'Pastel': ((0.95,0.92,0.95), (0.85,0.78,0.88), (0.78,0.68,0.85), (0.25,0.18,0.3), (0.72,0.65,0.75), 0.8),
    'Bubblegum': ((0.98,0.88,0.95), (0.95,0.68,0.85), (0.98,0.58,0.82), (0.3,0.15,0.25), (0.78,0.58,0.72), 0.8),
}

for name, (base, cold, warm, text, shadow, opacity) in THEMES().items():
    globals()[f'{name}Color'] = type(f'{name}Color', (), {
        'BASE': base,
        'COLD': cold,
        'WARM': warm,
        'TEXT': text,
        'SHADOW': shadow,
        'OPACITY': opacity
    })

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
    IMG_SETTINGS = 'settingsIcon'
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
    CHAR_DELETE = 'PLAY_STATION_CROSS_BUTTON'
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
    DOT_DOT = '..'
    FILENAME_MAX = 20
    PATH_MAX = 50
    COMMENT_MAX = 40
    BA_LAG_SMALL = 0.01
    BA_LAG = 0.04
    EPSILON = 1e-8
    ART = (
        (2.0, 0.3, 2.2),
        (2.2, 0.3, 1.5),
        (3.0, 0.3, 0.3),
        (2.2, 1.8, 0.3),
        (0.3, 2.0, 1.8),
    )
    TRANSITION = (
        ('in_left','out_right'),
        ('in_scale','out_scale'),
        'none'
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
    CONFIG_PREFIX = 'board_'
    URL_PREFIX = ('http://', 'https://', 'ftp://')
    URI_PREFIX = ('data:')
    VIDEO_PREFIX = ('mkv','brp','mp4','webm')
    VALID_URI = r'data:([^;,]+)?(;base64)?,(.+)'
    VALID_URL = r'https?://.+'
    TIMESTAMP_FORMAT = '%d/%m/%y %H:%M:%S'
    ADMIN = ['760222dac06c']

# strings
# non english are generated by claude ai

class EnglishString:
    # core
    BOARD = 'Board'
    WELCOME = 'Welcome to Board!'
    WAIT = 'Just a sec...'
    ERROR = 'An error occurred'
    HMM = 'Hmm'
    EMPTY = 'Empty'
    ART_WORD = 'BOARD'

    # actions & status
    ATTACH = 'Attach'
    DELETE = 'Delete'
    SENDING = 'Sending'
    DELETING = 'Deleting'
    DOWNLOADING = 'Downloading'
    UPLOADING = 'Uploading'
    COPIED = 'Copied to clipboard!'

    # completion messages
    DONE = '{} done!'
    SAVED_AS = 'Saved to downloads as "{}"'
    PUBLISHED = 'Post published! Should take seconds (reload to see)'
    DELETED = '{} deleted! Should take seconds (reload to see)'
    SENT = '{} sent! Should take seconds (reload to see)'

    # prompts & instructions
    ENTER = 'Enter {}!'
    SELECT = 'Select {}!'
    NOT_NOW = "Not now I'm busy!"
    HELP_POST = 'Press NL to break line, better just paste text here tho'
    HINT_ATTACH = 'Path, URL, URI or FullPath'
    CAN_CLOSE = '{}... (you can close this window)'

    # validation & errors
    CORRECT = 'Correct'
    WRONG = 'Wrong'
    INCORRECT = 'Incorrect {}!'
    INVALID = 'Invalid {}!'
    NOT_FOUND = '{} not found!'
    UNSUPPORTED = '{} unsupported!'
    ACCESS_DENIED = 'Access denied!'
    ERROR_WITH = 'An error occurred: {}'
    ERROR_UNKNOWN = 'An error occurred.'

    # ui labels
    TITLE = 'Title'
    DESCRIPTION = 'Description'
    COMMENT = 'Comment'
    COMMENTS = 'Comments'
    PASSWORD = 'Password'
    SETTINGS = 'Settings'
    THEME = 'Theme'
    LANGUAGE = 'Language'
    NEW_POST = 'New Post'
    POST_BY = 'New Post by {}'
    DELETE_ID = 'Delete {}'
    NL = 'NL'
    POST = 'Post'
    CLIPBOARD = 'Clipboard'
    SOMETHING = 'something'

    # file & data
    FILE = 'File'
    FILES = 'Files'
    BYTE = 'Byte'
    BYTES = 'Bytes'
    PATH = 'Path'
    URI = 'URI'
    URL = 'URL'
    PATH_INFO = 'Path: uploads file'
    URL_INFO = 'URL/URI: directly sent to server'

    # empty states
    NO = 'No {}'
    NO_PROVIDED = 'No {} provided.'

    # language specific
    LANGUAGE_IS_NOW = 'Language is now English!'

class ArabicString:
    # core
    BOARD = 'اللوحة'
    WELCOME = 'مرحباً بك في اللوحة!'
    WAIT = 'لحظة من فضلك...'
    ERROR = 'حدث خطأ'
    HMM = 'همم'
    EMPTY = 'فارغ'
    ART_WORD = 'ﺔـﺣﻮـﻟ'

    # actions & status
    ATTACH = 'إرفاق'
    DELETE = 'حذف'
    SENDING = 'جارٍ الإرسال'
    DELETING = 'جارٍ الحذف'
    DOWNLOADING = 'جارٍ التنزيل'
    UPLOADING = 'جارٍ الرفع'
    COPIED = 'تم النسخ إلى الحافظة!'

    # completion messages
    DONE = 'تم {}!'
    SAVED_AS = 'تم الحفظ في التنزيلات باسم "{}"'
    PUBLISHED = 'تم نشر المنشور! سيظهر خلال ثوانٍ (حدّث الصفحة)'
    DELETED = 'تم حذف {}! سيظهر التحديث خلال ثوانٍ (حدّث الصفحة)'
    SENT = 'تم إرسال {}! سيظهر خلال ثوانٍ (حدّث الصفحة)'

    # prompts & instructions
    ENTER = 'أدخل {}!'
    SELECT = 'اختر {}!'
    NOT_NOW = 'ليس الآن، أنا مشغول!'
    HELP_POST = 'اضغط NL لكسر السطر، لكن الأفضل لصق النص هنا مباشرة'
    HINT_ATTACH = 'مسار، رابط، URI أو المسار الكامل'
    CAN_CLOSE = '{}... (يمكنك إغلاق هذه النافذة)'

    # validation & errors
    CORRECT = 'صحيح'
    WRONG = 'خطأ'
    INCORRECT = '{} غير صحيح!'
    INVALID = '{} غير صالح!'
    NOT_FOUND = '{} غير موجود!'
    UNSUPPORTED = '{} غير مدعوم!'
    ACCESS_DENIED = 'تم رفض الوصول!'
    ERROR_WITH = 'حدث خطأ: {}'
    ERROR_UNKNOWN = 'حدث خطأ.'

    # ui labels
    TITLE = 'العنوان'
    DESCRIPTION = 'الوصف'
    COMMENT = 'تعليق'
    COMMENTS = 'التعليقات'
    PASSWORD = 'كلمة المرور'
    SETTINGS = 'الإعدادات'
    THEME = 'المظهر'
    LANGUAGE = 'اللغة'
    NEW_POST = 'منشور جديد'
    POST_BY = 'منشور جديد بواسطة {}'
    DELETE_ID = 'حذف {}'
    NL = 'سطر'
    POST = 'نشر'
    CLIPBOARD = 'الحافظة'
    SOMETHING = 'شيئاً ما'

    # file & data
    FILE = 'ملف'
    FILES = 'ملفات'
    BYTE = 'بايت'
    BYTES = 'بايت'
    PATH = 'المسار'
    URI = 'URI'
    URL = 'رابط'
    PATH_INFO = 'المسار: رفع الملف'
    URL_INFO = 'الرابط/URI: إرسال مباشر إلى الخادم'

    # empty states
    NO = 'لا يوجد {}'
    NO_PROVIDED = 'لم يتم تقديم {}.'

    # language specific
    LANGUAGE_IS_NOW = 'اللغة الآن هي العربية!'

class JapaneseString:
    # core
    BOARD = 'ボード'
    ART_WORD = 'ボード'
    WELCOME = 'ボードへようこそ！'
    WAIT = '少々お待ちください...'
    ERROR = 'エラーが発生しました'
    HMM = 'うーん'
    EMPTY = '空'

    # actions & status
    ATTACH = '添付'
    DELETE = '削除'
    SENDING = '送信中'
    DELETING = '削除中'
    DOWNLOADING = 'ダウンロード中'
    UPLOADING = 'アップロード中'
    COPIED = 'クリップボードにコピーしました！'

    # completion messages
    DONE = '{}が完了しました！'
    SAVED_AS = '"{}"としてダウンロードに保存しました'
    PUBLISHED = '投稿が公開されました！数秒後に表示されます（再読み込みしてください）'
    DELETED = '{}が削除されました！数秒後に表示されます（再読み込みしてください）'
    SENT = '{}が送信されました！数秒後に表示されます（再読み込みしてください）'

    # prompts & instructions
    ENTER = '{}を入力してください！'
    SELECT = '{}を選択してください！'
    NOT_NOW = '今は忙しいです！'
    HELP_POST = 'NLを押して改行、またはテキストを直接貼り付けてください'
    HINT_ATTACH = 'パス、URL、URIまたはフルパス'
    CAN_CLOSE = '{}...（このウィンドウを閉じても構いません）'

    # validation & errors
    CORRECT = '正しい'
    WRONG = '間違い'
    INCORRECT = '{}が正しくありません！'
    INVALID = '{}が無効です！'
    NOT_FOUND = '{}が見つかりません！'
    UNSUPPORTED = '{}はサポートされていません！'
    ACCESS_DENIED = 'アクセスが拒否されました！'
    ERROR_WITH = 'エラーが発生しました：{}'
    ERROR_UNKNOWN = 'エラーが発生しました。'

    # ui labels
    TITLE = 'タイトル'
    DESCRIPTION = '説明'
    COMMENT = 'コメント'
    COMMENTS = 'コメント'
    PASSWORD = 'パスワード'
    SETTINGS = '設定'
    THEME = 'テーマ'
    LANGUAGE = '言語'
    NEW_POST = '新規投稿'
    POST_BY = '{}による新規投稿'
    DELETE_ID = '{}を削除'
    NL = '改行'
    POST = '投稿'
    CLIPBOARD = 'クリップボード'
    SOMETHING = '何か'

    # file & data
    FILE = 'ファイル'
    FILES = 'ファイル'
    BYTE = 'バイト'
    BYTES = 'バイト'
    PATH = 'パス'
    URI = 'URI'
    URL = 'URL'
    PATH_INFO = 'パス：ファイルをアップロード'
    URL_INFO = 'URL/URI：サーバーに直接送信'

    # empty states
    NO = '{}なし'
    NO_PROVIDED = '{}が提供されていません。'

    # language specific
    LANGUAGE_IS_NOW = '言語が日本語になりました！'

class SpanishString:
    # core
    BOARD = 'Tablero'
    ART_WORD = 'TABLERO'
    WELCOME = '¡Bienvenido al Tablero!'
    WAIT = 'Un momento...'
    ERROR = 'Ocurrió un error'
    HMM = 'Hmm'
    EMPTY = 'Vacío'

    # actions & status
    ATTACH = 'Adjuntar'
    DELETE = 'Eliminar'
    SENDING = 'Enviando'
    DELETING = 'Eliminando'
    DOWNLOADING = 'Descargando'
    UPLOADING = 'Subiendo'
    COPIED = '¡Copiado al portapapeles!'

    # completion messages
    DONE = '¡{} completado!'
    SAVED_AS = 'Guardado en descargas como "{}"'
    PUBLISHED = '¡Publicación publicada! Aparecerá en segundos (recarga para ver)'
    DELETED = '¡{} eliminado! Aparecerá en segundos (recarga para ver)'
    SENT = '¡{} enviado! Aparecerá en segundos (recarga para ver)'

    # prompts & instructions
    ENTER = '¡Ingresa {}!'
    SELECT = '¡Selecciona {}!'
    NOT_NOW = '¡Ahora no, estoy ocupado!'
    HELP_POST = 'Presiona NL para salto de línea, mejor pega el texto aquí'
    HINT_ATTACH = 'Ruta, URL, URI o ruta completa'
    CAN_CLOSE = '{}... (puedes cerrar esta ventana)'

    # validation & errors
    CORRECT = 'Correcto'
    WRONG = 'Incorrecto'
    INCORRECT = '¡{} incorrecto!'
    INVALID = '¡{} inválido!'
    NOT_FOUND = '¡{} no encontrado!'
    UNSUPPORTED = '¡{} no soportado!'
    ACCESS_DENIED = '¡Acceso denegado!'
    ERROR_WITH = 'Ocurrió un error: {}'
    ERROR_UNKNOWN = 'Ocurrió un error.'

    # ui labels
    TITLE = 'Título'
    DESCRIPTION = 'Descripción'
    COMMENT = 'Comentario'
    COMMENTS = 'Comentarios'
    PASSWORD = 'Contraseña'
    SETTINGS = 'Configuración'
    THEME = 'Tema'
    LANGUAGE = 'Idioma'
    NEW_POST = 'Nueva publicación'
    POST_BY = 'Nueva publicación de {}'
    DELETE_ID = 'Eliminar {}'
    NL = 'NL'
    POST = 'Publicar'
    CLIPBOARD = 'Portapapeles'
    SOMETHING = 'algo'

    # file & data
    FILE = 'Archivo'
    FILES = 'Archivos'
    BYTE = 'Byte'
    BYTES = 'Bytes'
    PATH = 'Ruta'
    URI = 'URI'
    URL = 'URL'
    PATH_INFO = 'Ruta: sube el archivo'
    URL_INFO = 'URL/URI: enviado directamente al servidor'

    # empty states
    NO = 'Sin {}'
    NO_PROVIDED = 'No se proporcionó {}.'

    # language specific
    LANGUAGE_IS_NOW = '¡El idioma ahora es español!'

class BruhString:
    # core
    BOARD = 'The Board™'
    WELCOME = 'get in loser'
    WAIT = 'stfu im loading...'
    ERROR = 'skill issue'
    HMM = 'sus af'
    EMPTY = 'empty like ur brain'
    ART_WORD = 'BOARD?'

    # actions & status
    ATTACH = 'attach shit'
    DELETE = 'nuke'
    SENDING = 'sending ur trash'
    DELETING = 'deleting this garbage'
    DOWNLOADING = 'downloading (finally)'
    UPLOADING = 'uploading (this better work)'
    COPIED = 'copied. u happy now?'

    # completion messages
    DONE = '{} done. now touch grass'
    SAVED_AS = 'saved as "{}". not like ur gonna use it'
    PUBLISHED = 'posted. nobody cares. refresh if u want'
    DELETED = '{} deleted. good riddance. refresh to confirm'
    SENT = '{} sent. congrats i guess. refresh'

    # prompts & instructions
    ENTER = 'enter {} blud'
    SELECT = 'select {} you walnut'
    NOT_NOW = 'not now donut im busy!'
    HELP_POST = 'press NL to break line. or just paste ur wall of text idc'
    HINT_ATTACH = 'path, url, uri. figure it out'
    CAN_CLOSE = '{}... (close window idc)'

    # validation & errors
    CORRECT = 'WOW'
    WRONG = 'pathetic'
    INCORRECT = 'wrong {} you moron'
    INVALID = 'invalid {}. dont try again'
    NOT_FOUND = '{} not found. check your eyes'
    UNSUPPORTED = '{} unsupported. skull tissue'
    ACCESS_DENIED = 'access denied lmfao'
    ERROR_WITH = 'it gives error: {}'
    ERROR_UNKNOWN = 'error. idk what u did but u broke it'

    # ui labels
    TITLE = 'title'
    DESCRIPTION = 'description'
    COMMENT = 'comment'
    COMMENTS = 'yappers'
    PASSWORD = 'secret'
    SETTINGS = 'settings'
    THEME = 'skin'
    LANGUAGE = 'language'
    NEW_POST = 'cook up a post'
    POST_BY = 'cook up a post as {}'
    DELETE_ID = 'nuke {}'
    NL = 'NL'
    POST = 'post'
    CLIPBOARD = 'clipboard'
    SOMETHING = 'smth'

    # file & data
    FILE = 'file'
    FILES = 'files'
    BYTE = 'byte'
    BYTES = 'bytes'
    PATH = 'path'
    URI = 'URI'
    URL = 'url'
    PATH_INFO = 'path: uploads file'
    URL_INFO = 'url/uri: sends to server'

    # empty states
    NO = '{} is gone'
    NO_PROVIDED = '{} went brrrr'

    # language specific
    LANGUAGE_IS_NOW = 'what are you doing'

class FrancaisString:
    # core
    BOARD = 'Tableau'
    ART_WORD = 'TABLEAU'
    WELCOME = 'Bienvenue sur le Tableau !'
    WAIT = 'Un instant...'
    ERROR = 'Une erreur est survenue'
    HMM = 'Hmm'
    EMPTY = 'Vide'

    # actions & status
    ATTACH = 'Joindre'
    DELETE = 'Supprimer'
    SENDING = 'Envoi en cours'
    DELETING = 'Suppression'
    DOWNLOADING = 'Téléchargement'
    UPLOADING = 'Mise en ligne'
    COPIED = 'Copié dans le presse-papiers !'

    # completion messages
    DONE = '{} terminé !'
    SAVED_AS = 'Enregistré dans les téléchargements sous "{}"'
    PUBLISHED = 'Publication publiée ! Devrait apparaître en quelques secondes (actualiser pour voir)'
    DELETED = '{} supprimé ! Devrait apparaître en quelques secondes (actualiser pour voir)'
    SENT = '{} envoyé ! Devrait apparaître en quelques secondes (actualiser pour voir)'

    # prompts & instructions
    ENTER = 'Entrez {} !'
    SELECT = 'Sélectionnez {} !'
    NOT_NOW = 'Pas maintenant, je suis occupé !'
    HELP_POST = 'Appuyez sur NL pour sauter une ligne, ou collez simplement le texte ici'
    HINT_ATTACH = 'Chemin, URL, URI ou chemin complet'
    CAN_CLOSE = '{}... (vous pouvez fermer cette fenêtre)'

    # validation & errors
    CORRECT = 'Correct'
    WRONG = 'Incorrect'
    INCORRECT = '{} incorrect !'
    INVALID = '{} invalide !'
    NOT_FOUND = '{} introuvable !'
    UNSUPPORTED = '{} non pris en charge !'
    ACCESS_DENIED = 'Accès refusé !'
    ERROR_WITH = 'Une erreur est survenue : {}'
    ERROR_UNKNOWN = 'Une erreur est survenue.'

    # ui labels
    TITLE = 'Titre'
    DESCRIPTION = 'Description'
    COMMENT = 'Commentaire'
    COMMENTS = 'Commentaires'
    PASSWORD = 'Mot de passe'
    SETTINGS = 'Paramètres'
    THEME = 'Thème'
    LANGUAGE = 'Langue'
    NEW_POST = 'Nouvelle publication'
    POST_BY = 'Nouvelle publication par {}'
    DELETE_ID = 'Supprimer {}'
    NL = 'NL'
    POST = 'Publier'
    CLIPBOARD = 'Presse-papiers'
    SOMETHING = 'quelque chose'

    # file & data
    FILE = 'Fichier'
    FILES = 'Fichiers'
    BYTE = 'Octet'
    BYTES = 'Octets'
    PATH = 'Chemin'
    URI = 'URI'
    URL = 'URL'
    PATH_INFO = 'Chemin : téléverse le fichier'
    URL_INFO = 'URL/URI : envoyé directement au serveur'

    # empty states
    NO = 'Aucun {}'
    NO_PROVIDED = 'Aucun {} fourni.'

    # language specific
    LANGUAGE_IS_NOW = 'La langue est maintenant le français !'

class DeutschString:
    # core
    BOARD = 'Brett'
    ART_WORD = 'BRETT'
    WELCOME = 'Willkommen beim Brett!'
    WAIT = 'Einen Moment...'
    ERROR = 'Ein Fehler ist aufgetreten'
    HMM = 'Hmm'
    EMPTY = 'Leer'

    # actions & status
    ATTACH = 'Anhängen'
    DELETE = 'Löschen'
    SENDING = 'Wird gesendet'
    DELETING = 'Wird gelöscht'
    DOWNLOADING = 'Wird heruntergeladen'
    UPLOADING = 'Wird hochgeladen'
    COPIED = 'In die Zwischenablage kopiert!'

    # completion messages
    DONE = '{} fertig!'
    SAVED_AS = 'Als "{}" in Downloads gespeichert'
    PUBLISHED = 'Beitrag veröffentlicht! Sollte in Sekunden erscheinen (neu laden zum Anzeigen)'
    DELETED = '{} gelöscht! Sollte in Sekunden erscheinen (neu laden zum Anzeigen)'
    SENT = '{} gesendet! Sollte in Sekunden erscheinen (neu laden zum Anzeigen)'

    # prompts & instructions
    ENTER = 'Geben Sie {} ein!'
    SELECT = 'Wählen Sie {} aus!'
    NOT_NOW = 'Nicht jetzt, ich bin beschäftigt!'
    HELP_POST = 'Drücken Sie NL für Zeilenumbruch, oder fügen Sie einfach Text hier ein'
    HINT_ATTACH = 'Pfad, URL, URI oder vollständiger Pfad'
    CAN_CLOSE = '{}... (Sie können dieses Fenster schließen)'

    # validation & errors
    CORRECT = 'Richtig'
    WRONG = 'Falsch'
    INCORRECT = 'Falsches {}!'
    INVALID = 'Ungültiges {}!'
    NOT_FOUND = '{} nicht gefunden!'
    UNSUPPORTED = '{} nicht unterstützt!'
    ACCESS_DENIED = 'Zugriff verweigert!'
    ERROR_WITH = 'Ein Fehler ist aufgetreten: {}'
    ERROR_UNKNOWN = 'Ein Fehler ist aufgetreten.'

    # ui labels
    TITLE = 'Titel'
    DESCRIPTION = 'Beschreibung'
    COMMENT = 'Kommentar'
    COMMENTS = 'Kommentare'
    PASSWORD = 'Passwort'
    SETTINGS = 'Einstellungen'
    THEME = 'Thema'
    LANGUAGE = 'Sprache'
    NEW_POST = 'Neuer Beitrag'
    POST_BY = 'Neuer Beitrag von {}'
    DELETE_ID = '{} löschen'
    NL = 'NL'
    POST = 'Posten'
    CLIPBOARD = 'Zwischenablage'
    SOMETHING = 'etwas'

    # file & data
    FILE = 'Datei'
    FILES = 'Dateien'
    BYTE = 'Byte'
    BYTES = 'Bytes'
    PATH = 'Pfad'
    URI = 'URI'
    URL = 'URL'
    PATH_INFO = 'Pfad: lädt Datei hoch'
    URL_INFO = 'URL/URI: direkt an Server gesendet'

    # empty states
    NO = 'Kein {}'
    NO_PROVIDED = 'Kein {} angegeben.'

    # language specific
    LANGUAGE_IS_NOW = 'Die Sprache ist jetzt Deutsch!'

class ItalianoString:
    # core
    BOARD = 'Bacheca'
    ART_WORD = 'BACHECA'
    WELCOME = 'Benvenuto sulla Bacheca!'
    WAIT = 'Un momento...'
    ERROR = 'Si è verificato un errore'
    HMM = 'Hmm'
    EMPTY = 'Vuoto'

    # actions & status
    ATTACH = 'Allega'
    DELETE = 'Elimina'
    SENDING = 'Invio in corso'
    DELETING = 'Eliminazione'
    DOWNLOADING = 'Download'
    UPLOADING = 'Caricamento'
    COPIED = 'Copiato negli appunti!'

    # completion messages
    DONE = '{} completato!'
    SAVED_AS = 'Salvato nei download come "{}"'
    PUBLISHED = 'Post pubblicato! Dovrebbe apparire tra pochi secondi (ricarica per vedere)'
    DELETED = '{} eliminato! Dovrebbe apparire tra pochi secondi (ricarica per vedere)'
    SENT = '{} inviato! Dovrebbe apparire tra pochi secondi (ricarica per vedere)'

    # prompts & instructions
    ENTER = 'Inserisci {}!'
    SELECT = 'Seleziona {}!'
    NOT_NOW = 'Non ora, sono occupato!'
    HELP_POST = 'Premi NL per andare a capo, oppure incolla il testo qui'
    HINT_ATTACH = 'Percorso, URL, URI o percorso completo'
    CAN_CLOSE = '{}... (puoi chiudere questa finestra)'

    # validation & errors
    CORRECT = 'Corretto'
    WRONG = 'Sbagliato'
    INCORRECT = '{} non corretto!'
    INVALID = '{} non valido!'
    NOT_FOUND = '{} non trovato!'
    UNSUPPORTED = '{} non supportato!'
    ACCESS_DENIED = 'Accesso negato!'
    ERROR_WITH = 'Si è verificato un errore: {}'
    ERROR_UNKNOWN = 'Si è verificato un errore.'

    # ui labels
    TITLE = 'Titolo'
    DESCRIPTION = 'Descrizione'
    COMMENT = 'Commento'
    COMMENTS = 'Commenti'
    PASSWORD = 'Password'
    SETTINGS = 'Impostazioni'
    THEME = 'Tema'
    LANGUAGE = 'Lingua'
    NEW_POST = 'Nuovo post'
    POST_BY = 'Nuovo post di {}'
    DELETE_ID = 'Elimina {}'
    NL = 'NL'
    POST = 'Pubblica'
    CLIPBOARD = 'Appunti'
    SOMETHING = 'qualcosa'

    # file & data
    FILE = 'File'
    FILES = 'File'
    BYTE = 'Byte'
    BYTES = 'Bytes'
    PATH = 'Percorso'
    URI = 'URI'
    URL = 'URL'
    PATH_INFO = 'Percorso: carica il file'
    URL_INFO = 'URL/URI: inviato direttamente al server'

    # empty states
    NO = 'Nessun {}'
    NO_PROVIDED = 'Nessun {} fornito.'

    # language specific
    LANGUAGE_IS_NOW = 'La lingua è ora italiano!'

class PortuguesString:
    # core
    BOARD = 'Quadro'
    ART_WORD = 'QUADRO'
    WELCOME = 'Bem-vindo ao Quadro!'
    WAIT = 'Só um momento...'
    ERROR = 'Ocorreu um erro'
    HMM = 'Hmm'
    EMPTY = 'Vazio'

    # actions & status
    ATTACH = 'Anexar'
    DELETE = 'Excluir'
    SENDING = 'Enviando'
    DELETING = 'Excluindo'
    DOWNLOADING = 'Baixando'
    UPLOADING = 'Carregando'
    COPIED = 'Copiado para a área de transferência!'

    # completion messages
    DONE = '{} concluído!'
    SAVED_AS = 'Salvo nos downloads como "{}"'
    PUBLISHED = 'Post publicado! Deve aparecer em segundos (recarregue para ver)'
    DELETED = '{} excluído! Deve aparecer em segundos (recarregue para ver)'
    SENT = '{} enviado! Deve aparecer em segundos (recarregue para ver)'

    # prompts & instructions
    ENTER = 'Digite {}!'
    SELECT = 'Selecione {}!'
    NOT_NOW = 'Agora não, estou ocupado!'
    HELP_POST = 'Pressione NL para quebrar linha, ou apenas cole o texto aqui'
    HINT_ATTACH = 'Caminho, URL, URI ou caminho completo'
    CAN_CLOSE = '{}... (você pode fechar esta janela)'

    # validation & errors
    CORRECT = 'Correto'
    WRONG = 'Errado'
    INCORRECT = '{} incorreto!'
    INVALID = '{} inválido!'
    NOT_FOUND = '{} não encontrado!'
    UNSUPPORTED = '{} não suportado!'
    ACCESS_DENIED = 'Acesso negado!'
    ERROR_WITH = 'Ocorreu um erro: {}'
    ERROR_UNKNOWN = 'Ocorreu um erro.'

    # ui labels
    TITLE = 'Título'
    DESCRIPTION = 'Descrição'
    COMMENT = 'Comentário'
    COMMENTS = 'Comentários'
    PASSWORD = 'Senha'
    SETTINGS = 'Configurações'
    THEME = 'Tema'
    LANGUAGE = 'Idioma'
    NEW_POST = 'Nova publicação'
    POST_BY = 'Nova publicação de {}'
    DELETE_ID = 'Excluir {}'
    NL = 'NL'
    POST = 'Publicar'
    CLIPBOARD = 'Área de transferência'
    SOMETHING = 'algo'

    # file & data
    FILE = 'Arquivo'
    FILES = 'Arquivos'
    BYTE = 'Byte'
    BYTES = 'Bytes'
    PATH = 'Caminho'
    URI = 'URI'
    URL = 'URL'
    PATH_INFO = 'Caminho: carrega o arquivo'
    URL_INFO = 'URL/URI: enviado diretamente ao servidor'

    # empty states
    NO = 'Sem {}'
    NO_PROVIDED = 'Nenhum {} fornecido.'

    # language specific
    LANGUAGE_IS_NOW = 'O idioma agora é português!'

class RussianString:
    # core
    BOARD = 'Доска'
    ART_WORD = 'ДОСКА'
    WELCOME = 'Добро пожаловать на Доску!'
    WAIT = 'Минутку...'
    ERROR = 'Произошла ошибка'
    HMM = 'Хм'
    EMPTY = 'Пусто'

    # actions & status
    ATTACH = 'Прикрепить'
    DELETE = 'Удалить'
    SENDING = 'Отправка'
    DELETING = 'Удаление'
    DOWNLOADING = 'Загрузка'
    UPLOADING = 'Выгрузка'
    COPIED = 'Скопировано в буфер обмена!'

    # completion messages
    DONE = '{} готово!'
    SAVED_AS = 'Сохранено в загрузках как "{}"'
    PUBLISHED = 'Пост опубликован! Появится через несколько секунд (обновите страницу)'
    DELETED = '{} удалено! Появится через несколько секунд (обновите страницу)'
    SENT = '{} отправлено! Появится через несколько секунд (обновите страницу)'

    # prompts & instructions
    ENTER = 'Введите {}!'
    SELECT = 'Выберите {}!'
    NOT_NOW = 'Не сейчас, я занят!'
    HELP_POST = 'Нажмите NL для переноса строки, или просто вставьте текст сюда'
    HINT_ATTACH = 'Путь, URL, URI или полный путь'
    CAN_CLOSE = '{}... (можете закрыть это окно)'

    # validation & errors
    CORRECT = 'Верно'
    WRONG = 'Неверно'
    INCORRECT = 'Неверный {}!'
    INVALID = 'Недействительный {}!'
    NOT_FOUND = '{} не найден!'
    UNSUPPORTED = '{} не поддерживается!'
    ACCESS_DENIED = 'Доступ запрещен!'
    ERROR_WITH = 'Произошла ошибка: {}'
    ERROR_UNKNOWN = 'Произошла ошибка.'

    # ui labels
    TITLE = 'Заголовок'
    DESCRIPTION = 'Описание'
    COMMENT = 'Комментарий'
    COMMENTS = 'Комментарии'
    PASSWORD = 'Пароль'
    SETTINGS = 'Настройки'
    THEME = 'Тема'
    LANGUAGE = 'Язык'
    NEW_POST = 'Новый пост'
    POST_BY = 'Новый пост от {}'
    DELETE_ID = 'Удалить {}'
    NL = 'NL'
    POST = 'Опубликовать'
    CLIPBOARD = 'Буфер обмена'
    SOMETHING = 'что-то'

    # file & data
    FILE = 'Файл'
    FILES = 'Файлы'
    BYTE = 'Байт'
    BYTES = 'Байт'
    PATH = 'Путь'
    URI = 'URI'
    URL = 'URL'
    PATH_INFO = 'Путь: загружает файл'
    URL_INFO = 'URL/URI: отправляется напрямую на сервер'

    # empty states
    NO = 'Нет {}'
    NO_PROVIDED = '{} не предоставлен.'

    # language specific
    LANGUAGE_IS_NOW = 'Язык теперь русский!'

class KoreanString:
    # core
    BOARD = '게시판'
    ART_WORD = '게시판'
    WELCOME = '게시판에 오신 것을 환영합니다!'
    WAIT = '잠시만요...'
    ERROR = '오류가 발생했습니다'
    HMM = '음'
    EMPTY = '비어있음'

    # actions & status
    ATTACH = '첨부'
    DELETE = '삭제'
    SENDING = '전송 중'
    DELETING = '삭제 중'
    DOWNLOADING = '다운로드 중'
    UPLOADING = '업로드 중'
    COPIED = '클립보드에 복사되었습니다!'

    # completion messages
    DONE = '{} 완료!'
    SAVED_AS = '"{}"(으)로 다운로드에 저장됨'
    PUBLISHED = '게시물이 게시되었습니다! 몇 초 후에 표시됩니다 (새로고침하세요)'
    DELETED = '{}이(가) 삭제되었습니다! 몇 초 후에 표시됩니다 (새로고침하세요)'
    SENT = '{}이(가) 전송되었습니다! 몇 초 후에 표시됩니다 (새로고침하세요)'

    # prompts & instructions
    ENTER = '{}을(를) 입력하세요!'
    SELECT = '{}을(를) 선택하세요!'
    NOT_NOW = '지금은 안 돼요, 바빠요!'
    HELP_POST = 'NL을 눌러 줄바꿈하거나 여기에 텍스트를 붙여넣으세요'
    HINT_ATTACH = '경로, URL, URI 또는 전체 경로'
    CAN_CLOSE = '{}... (이 창을 닫아도 됩니다)'

    # validation & errors
    CORRECT = '정확함'
    WRONG = '틀림'
    INCORRECT = '잘못된 {}!'
    INVALID = '유효하지 않은 {}!'
    NOT_FOUND = '{}을(를) 찾을 수 없습니다!'
    UNSUPPORTED = '{}은(는) 지원되지 않습니다!'
    ACCESS_DENIED = '액세스가 거부되었습니다!'
    ERROR_WITH = '오류가 발생했습니다: {}'
    ERROR_UNKNOWN = '오류가 발생했습니다.'

    # ui labels
    TITLE = '제목'
    DESCRIPTION = '설명'
    COMMENT = '댓글'
    COMMENTS = '댓글'
    PASSWORD = '비밀번호'
    SETTINGS = '설정'
    THEME = '테마'
    LANGUAGE = '언어'
    NEW_POST = '새 게시물'
    POST_BY = '{}의 새 게시물'
    DELETE_ID = '{} 삭제'
    NL = '줄바꿈'
    POST = '게시'
    CLIPBOARD = '클립보드'
    SOMETHING = '무언가'

    # file & data
    FILE = '파일'
    FILES = '파일'
    BYTE = '바이트'
    BYTES = '바이트'
    PATH = '경로'
    URI = 'URI'
    URL = 'URL'
    PATH_INFO = '경로: 파일 업로드'
    URL_INFO = 'URL/URI: 서버로 직접 전송'

    # empty states
    NO = '{} 없음'
    NO_PROVIDED = '{}이(가) 제공되지 않았습니다.'

    # language specific
    LANGUAGE_IS_NOW = '언어가 한국어로 변경되었습니다!'

class ChineseString:
    # core
    BOARD = '看板'
    ART_WORD = '看板'
    WELCOME = '欢迎来到看板！'
    WAIT = '请稍候...'
    ERROR = '发生错误'
    HMM = '嗯'
    EMPTY = '空'

    # actions & status
    ATTACH = '附加'
    DELETE = '删除'
    SENDING = '发送中'
    DELETING = '删除中'
    DOWNLOADING = '下载中'
    UPLOADING = '上传中'
    COPIED = '已复制到剪贴板！'

    # completion messages
    DONE = '{}完成！'
    SAVED_AS = '已保存到下载为"{}"'
    PUBLISHED = '帖子已发布！几秒钟后显示（刷新查看）'
    DELETED = '{}已删除！几秒钟后显示（刷新查看）'
    SENT = '{}已发送！几秒钟后显示（刷新查看）'

    # prompts & instructions
    ENTER = '输入{}！'
    SELECT = '选择{}！'
    NOT_NOW = '现在不行，我很忙！'
    HELP_POST = '按NL换行，或直接粘贴文本'
    HINT_ATTACH = '路径、URL、URI或完整路径'
    CAN_CLOSE = '{}...（可以关闭此窗口）'

    # validation & errors
    CORRECT = '正确'
    WRONG = '错误'
    INCORRECT = '{}不正确！'
    INVALID = '{}无效！'
    NOT_FOUND = '未找到{}！'
    UNSUPPORTED = '不支持{}！'
    ACCESS_DENIED = '访问被拒绝！'
    ERROR_WITH = '发生错误：{}'
    ERROR_UNKNOWN = '发生错误。'

    # ui labels
    TITLE = '标题'
    DESCRIPTION = '描述'
    COMMENT = '评论'
    COMMENTS = '评论'
    PASSWORD = '密码'
    SETTINGS = '设置'
    THEME = '主题'
    LANGUAGE = '语言'
    NEW_POST = '新帖子'
    POST_BY = '{}的新帖子'
    DELETE_ID = '删除{}'
    NL = '换行'
    POST = '发布'
    CLIPBOARD = '剪贴板'
    SOMETHING = '某物'

    # file & data
    FILE = '文件'
    FILES = '文件'
    BYTE = '字节'
    BYTES = '字节'
    PATH = '路径'
    URI = 'URI'
    URL = 'URL'
    PATH_INFO = '路径：上传文件'
    URL_INFO = 'URL/URI：直接发送到服务器'

    # empty states
    NO = '无{}'
    NO_PROVIDED = '未提供{}。'

    # language specific
    LANGUAGE_IS_NOW = '语言现在是中文！'

class HindiString:
    # core
    BOARD = 'बोर्ड'
    ART_WORD = 'बोर्ड'
    WELCOME = 'बोर्ड में आपका स्वागत है!'
    WAIT = 'एक पल...'
    ERROR = 'एक त्रुटि हुई'
    HMM = 'हम्म'
    EMPTY = 'खाली'

    # actions & status
    ATTACH = 'संलग्न करें'
    DELETE = 'हटाएं'
    SENDING = 'भेजा जा रहा है'
    DELETING = 'हटाया जा रहा है'
    DOWNLOADING = 'डाउनलोड हो रहा है'
    UPLOADING = 'अपलोड हो रहा है'
    COPIED = 'क्लिपबोर्ड पर कॉपी किया गया!'

    # completion messages
    DONE = '{} पूर्ण!'
    SAVED_AS = '"{}" के रूप में डाउनलोड में सहेजा गया'
    PUBLISHED = 'पोस्ट प्रकाशित! कुछ सेकंड में दिखाई देगा (देखने के लिए रीफ्रेश करें)'
    DELETED = '{} हटा दिया गया! कुछ सेकंड में दिखाई देगा (देखने के लिए रीफ्रेश करें)'
    SENT = '{} भेजा गया! कुछ सेकंड में दिखाई देगा (देखने के लिए रीफ्रेश करें)'

    # prompts & instructions
    ENTER = '{} दर्ज करें!'
    SELECT = '{} चुनें!'
    NOT_NOW = 'अभी नहीं, मैं व्यस्त हूं!'
    HELP_POST = 'लाइन तोड़ने के लिए NL दबाएं, या यहां टेक्स्ट पेस्ट करें'
    HINT_ATTACH = 'पथ, URL, URI या पूर्ण पथ'
    CAN_CLOSE = '{}... (आप यह विंडो बंद कर सकते हैं)'

    # validation & errors
    CORRECT = 'सही'
    WRONG = 'गलत'
    INCORRECT = 'गलत {}!'
    INVALID = 'अमान्य {}!'
    NOT_FOUND = '{} नहीं मिला!'
    UNSUPPORTED = '{} असमर्थित!'
    ACCESS_DENIED = 'पहुंच अस्वीकृत!'
    ERROR_WITH = 'एक त्रुटि हुई: {}'
    ERROR_UNKNOWN = 'एक त्रुटि हुई।'

    # ui labels
    TITLE = 'शीर्षक'
    DESCRIPTION = 'विवरण'
    COMMENT = 'टिप्पणी'
    COMMENTS = 'टिप्पणियां'
    PASSWORD = 'पासवर्ड'
    SETTINGS = 'सेटिंग्स'
    THEME = 'थीम'
    LANGUAGE = 'भाषा'
    NEW_POST = 'नया पोस्ट'
    POST_BY = '{} द्वारा नया पोस्ट'
    DELETE_ID = '{} हटाएं'
    NL = 'लाइन ब्रेक'
    POST = 'पोस्ट करें'
    CLIPBOARD = 'क्लिपबोर्ड'
    SOMETHING = 'कुछ'

    # file & data
    FILE = 'फ़ाइल'
    FILES = 'फ़ाइलें'
    BYTE = 'बाइट'
    BYTES = 'बाइट्स'
    PATH = 'पथ'
    URI = 'URI'
    URL = 'URL'
    PATH_INFO = 'पथ: फ़ाइल अपलोड करता है'
    URL_INFO = 'URL/URI: सीधे सर्वर को भेजा गया'

    # empty states
    NO = 'कोई {} नहीं'
    NO_PROVIDED = 'कोई {} प्रदान नहीं किया गया।'

    # language specific
    LANGUAGE_IS_NOW = 'भाषा अब हिंदी है!'

# config
# manager is defined at module level

Config = ConfigManager()

