# Copyright 2026 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Discord >> @BrotherBoard

"""
Public+

Because the current public tab is boring.
Adds a new tab at the gather window.
Experimental.
"""

import babase as ba
import bauiv1 as bui
from bauiv1lib.tabs import TabRow
from bauiv1lib.gather import GatherTab, GatherWindow
from bascenev1 import protocol_version, connect_to_party

from socket import socket, AF_INET, SOCK_DGRAM, timeout
from struct import unpack_from
from json import loads, dumps
from uuid import uuid4
from random import choice, randint
from threading import Thread
from time import monotonic, sleep as _sleep, time
from collections import defaultdict
from asyncio import (
    wait_for, gather, Semaphore,
    TimeoutError, run,
    DatagramProtocol, get_running_loop
)
from math import ceil
from re import findall, sub

__version__ = '1.0'

class Strings:
    BUTTON_QUERY = 'Query'
    BUTTON_PING = 'Ping'
    BUTTON_RESET = 'Reset'
    BUTTON_CONNECT = 'Connect'
    TEXT_PUBLIC_PLUS = 'Public+'
    TEXT_VERSION = 'Version {}'
    TEXT_FILTER='Filter'
    TEXT_FILTER_PING='Max Ping (ms)'
    TEXT_NOTHING = 'Nothing'
    TEXT_OFFLINE = 'Offline'
    TEXT_ELLIPSIS = '...'
    TEXT_NOW_PLAYING = 'Now Playing'
    TEXTS_SPLASH = (
        'Public but it\'s better.\nSelect a server to Begin.',
        'More features, less waiting.\nNow select a server.',
        'Let\'s find the perfect server\njust for you.',
        'Select a server to\nshow its info here.',
        'We\'ll squeeze out the\nbest server for you.',
        'Press on Query, it\'ll grab\nall the servers globally.',
        'The Query button is waiting.\nSelect a server to begin.'
    )

class Theme:
    BUTTON_ENABLED = (0.5,0.7,0.2)
    BUTTON_DISABLED = (0.5,0.5,0.5)
    TEXT_ENABLED = (1,1,1)
    TEXT_LAZY = (1,1,1,0.5)
    TEXT_DISABLED = (0.35,0.35,0.35)
    TEXT_SELECTED = (0,1,1)
    TEXT_MARK = (1,1,0,0.5)

class PublicPlusTab(GatherTab):
    DATA = defaultdict(list)
    def __init__(self,*a):
        self.data = type(self).DATA
        self.rendering = False
        self.lit_kid = None
        self.last_filter = self.data.get('last_filter','')
        self.last_filter_ping = self.data.get('last_filter_ping','')
        self.memory = self.data['memory']
        self.memory_kids = []
        self.mem_kids = []
        self.preview_ping_gen = 0
        self.page = self.data.get('page', 0) or 0
        self.total_pages = 1
        self.data['gen'] = self.data.get('gen', 0) + 1
        self.gen = self.data['gen']
        self.alive = False
        self.sniff_client = None

    def on_activate(
        self, parent, btn, width, height, left, bottom
    ):
        # math
        mx,my,me = 21,14,10
        scroll_xs = width*0.4
        btn_ys = 50
        scroll_ys = height-2*my-btn_ys-me-40
        btn_xs = scroll_xs/3
        pg_ys = 36
        pg_xs = 40
        list_ys = scroll_ys-pg_ys-me
        # export
        self.scroll_xs = scroll_xs
        self.width = width
        self.height = height
        self.filter_y = scroll_ys+btn_ys+me
        self.page_size = max(1, int(list_ys//30)) * 2
        self.online = bui.app.plus.cloud.is_connected()
        # parent
        self.parent = bui.containerwidget(
            parent=parent,
            position=(left+mx, bottom+my),
            size=(width-mx*2,height*-my*2),
            background=False
        )
        # filter (name)
        filter_half = scroll_xs/2
        self.filter_hint = bui.textwidget(
            parent=self.parent,
            size=(filter_half-5,40),
            position=(10,scroll_ys+btn_ys+me),
            color=Theme.TEXT_LAZY,
            text=(self.last_filter and ' ' or Strings.TEXT_FILTER),
            v_align='center'
        )
        self.filter_input = bui.textwidget(
            parent=self.parent,
            size=(filter_half-5,40),
            position=(5,scroll_ys+btn_ys+me),
            glow_type='uniform',
            editable=True,
            id='filter_input',
            color=Theme.TEXT_ENABLED,
            description=Strings.TEXT_FILTER,
            text=self.last_filter,
            v_align='center'
        )
        # filter (max ping)
        self.filter_ping_hint = bui.textwidget(
            parent=self.parent,
            size=(filter_half-5,40),
            position=(filter_half+10,scroll_ys+btn_ys+me),
            color=Theme.TEXT_LAZY,
            text=(
                self.last_filter_ping and ' '
                or Strings.TEXT_FILTER_PING
            ),
            v_align='center'
        )
        self.filter_ping_input = bui.textwidget(
            parent=self.parent,
            size=(filter_half-5,40),
            position=(filter_half+5,scroll_ys+btn_ys+me),
            glow_type='uniform',
            editable=True,
            max_chars=5,
            id='filter_ping_input',
            color=Theme.TEXT_ENABLED,
            description=Strings.TEXT_FILTER_PING,
            text=self.last_filter_ping,
            v_align='center'
        )
        self.start_filter_timer()
        # memory
        self.memory_root = bui.containerwidget(
            parent=bui.scrollwidget(
                parent=self.parent,
                size=(scroll_xs,list_ys),
                border_opacity=0.7,
                position=(0,btn_ys+me*2+pg_ys)
            ),
            background=False
        )
        # pages
        pg_m = 6
        self.left_btn = bui.buttonwidget(
            parent=self.parent,
            button_type='square',
            label=bui.charstr(bui.SpecialChar.LEFT_ARROW),
            color=Theme.BUTTON_ENABLED,
            textcolor=Theme.TEXT_ENABLED,
            size=(pg_xs,pg_ys),
            position=(0,btn_ys+me),
            enable_sound=False,
            repeat=True,
            id='left_btn',
            on_activate_call=bui.CallPartial(
                self.on_page_left
            )
        )
        self.page_btn = bui.textwidget(
            parent=self.parent,
            text='1/1',
            color=Theme.TEXT_ENABLED,
            size=(scroll_xs-pg_xs*2-pg_m*2,pg_ys),
            position=(pg_xs+pg_m,btn_ys+me),
            h_align='center',
            v_align='center',
            selectable=True,
            click_activate=True,
            glow_type='uniform',
            id='page_btn',
            on_activate_call=bui.CallPartial(
                self.on_page_snap_press
            )
        )
        self.right_btn = bui.buttonwidget(
            parent=self.parent,
            button_type='square',
            label=bui.charstr(bui.SpecialChar.RIGHT_ARROW),
            color=Theme.BUTTON_ENABLED,
            textcolor=Theme.TEXT_ENABLED,
            size=(pg_xs,pg_ys),
            position=(scroll_xs-pg_xs,btn_ys+me),
            enable_sound=False,
            repeat=True,
            id='right_btn',
            on_activate_call=bui.CallPartial(
                self.on_page_right
            )
        )
        self.update_pages_ui()
        btn_gap = 10
        btn_xs_new = (scroll_xs - 2 * btn_gap) / 3
        # query
        self.query_btn = bui.buttonwidget(
            parent=self.parent,
            button_type='square',
            label=Strings.BUTTON_QUERY,
            color=Theme.BUTTON_ENABLED,
            textcolor=Theme.TEXT_ENABLED,
            size=(btn_xs_new,btn_ys),
            position=(0,0),
            enable_sound=False,
            id='query_btn',
            on_activate_call=bui.CallPartial(
                self.on_query_press
            )
        )
        # ping
        self.ping_btn = bui.buttonwidget(
            parent=self.parent,
            button_type='square',
            label=Strings.BUTTON_PING,
            color=Theme.BUTTON_ENABLED,
            textcolor=Theme.TEXT_ENABLED,
            size=(btn_xs_new,btn_ys),
            position=(btn_xs_new + btn_gap,0),
            enable_sound=False,
            id='ping_btn',
            on_activate_call=bui.CallPartial(
                self.on_ping_press
            )
        )
        # reset
        self.reset_btn = bui.buttonwidget(
            parent=self.parent,
            button_type='square',
            label=Strings.BUTTON_RESET,
            color=Theme.BUTTON_ENABLED,
            textcolor=Theme.TEXT_ENABLED,
            size=(btn_xs_new,btn_ys),
            position=(scroll_xs-btn_xs_new,0),
            enable_sound=False,
            id='reset_btn',
            on_activate_call=bui.CallPartial(
                self.on_reset_press
            )
        )
        # nothing
        self.nothing_text = bui.textwidget(
            parent=self.parent,
            color=Theme.TEXT_LAZY,
            position=(0,btn_ys+me+pg_ys),
            text=Strings.TEXT_NOTHING,
            size=(scroll_xs,list_ys),
            h_align='center',
            v_align='center'
        )
        # finally
        self.alive = True
        if self.memory:
            self.render_memory()
        if self.data['init_hidden']:
            if (mem:=self.data['mem']):
                self.render_mem(mem)
        else: self.show_init()
        if (
            not self.online
            and not self.memory
        ): self.set_nothing(Strings.TEXT_OFFLINE)
        self.start_online_timer()

    def start_online_timer(self):
        self.data['online_timer'] = bui.AppTimer(
            0.2, lambda: (
                setattr(
                    self,
                    'online',
                    bui.app.plus.cloud.is_connected()
                )
            )
        )

    def show_init(self):
        self.reset_mem()
        width, height = self.width, self.height
        # title
        self.title_text = bui.textwidget(
            parent=self.parent,
            color=Theme.TEXT_ENABLED,
            text=Strings.TEXT_PUBLIC_PLUS,
            position=(width*0.4,height*0.4),
            size=(width*0.6,height*0.6),
            v_align='center',
            h_align='center',
            scale=3,
            flatness=-3
        )
        # version
        self.version_text = bui.textwidget(
            parent=self.parent,
            color=Theme.TEXT_ENABLED,
            position=(width*0.392,height*0.2),
            size=(width*0.6,height*0.8),
            v_align='center',
            h_align='center',
            flatness=-1,
            text=Strings.TEXT_VERSION.format(
                __version__
            )
        )
        # splash
        self.splash_text = bui.textwidget(
            parent=self.parent,
            color=Theme.TEXT_ENABLED,
            position=(width*0.392,0),
            size=(width*0.6,height*0.7),
            v_align='center',
            h_align='center',
            text=choice(Strings.TEXTS_SPLASH)
        )
        self.data['init_hidden'] = False

    def render_mem(self, mem):
        self.reset_mem()
        x = self.scroll_xs + 10
        y = self.height - 135 + 10
        xs = self.width*0.45
        bgx = self.width-self.scroll_xs-45
        # bg
        self.mem_kids.append(
            bui.imagewidget(
                parent=self.parent,
                position=(self.scroll_xs+10,0),
                size=(
                    bgx, self.height-73
                ),
                texture=bui.gettexture('white'),
                color=(0.08,0.08,0.08)
            )
        )
        # close
        close_size, close_m = 40, 10
        close_x = self.width-close_size-close_m-close_size*0.6
        # bar
        title_m = 10
        title_x = self.scroll_xs+title_m
        title_w = close_x-title_m-title_x
        self.mem_kids.append(
            bui.imagewidget(
                parent=self.parent,
                position=(title_x,self.filter_y),
                size=(title_w+4,close_size),
                texture=bui.gettexture('white'),
                color=(0.15,0.15,0.15)
            )
        )
        self.mem_kids.append(
            bui.imagewidget(
                parent=self.parent,
                position=(title_x,self.filter_y),
                size=(close_size,close_size),
                texture=bui.gettexture('playerLineup'),
                mesh_transparent=bui.getmesh('angryComputerTransparent'),
            )
        )
        self.mem_kids.append(
            bui.textwidget(
                parent=self.parent,
                position=(title_x+close_size,self.filter_y),
                size=(title_w-close_size,close_size),
                text=mem['n'],
                maxwidth=title_w-close_size-10,
                color=Theme.TEXT_ENABLED,
                h_align='center',
                v_align='center'
            )
        )
        self.mem_kids.append(
            bui.buttonwidget(
                parent=self.parent,
                button_type='square',
                label=bui.charstr(bui.SpecialChar.CLOSE),
                texture=bui.gettexture('white'),
                textcolor=Theme.TEXT_ENABLED,
                color=(0.15,0.15,0.15),
                size=(close_size-4,close_size-4),
                position=(
                    close_x+2,
                    self.filter_y+2
                ),
                enable_sound=False,
                id='close_btn',
                on_activate_call=bui.CallPartial(
                    self.on_close_press
                )
            )
        )
        # address
        self.mem_kids.append(
            bui.imagewidget(
                parent=self.parent,
                position=(x+9,y),
                size=(40,40),
                texture=bui.gettexture('cursor')
            )
        )
        self.mem_kids.append(
            bui.textwidget(
                parent=self.parent,
                position=(x+60,y-2),
                text=f"{mem['a']}:{mem['p']}",
                maxwidth=xs-5,
                size=(xs,50),
                v_align='center'
            )
        )
        # players
        y -= self.height*0.1
        self.mem_kids.append(
            bui.imagewidget(
                parent=self.parent,
                position=(x+9,y+6),
                size=(40,40),
                texture=bui.gettexture('usersButton'),
            )
        )
        self.mem_kids.append(
            bui.textwidget(
                parent=self.parent,
                position=(x+60,y-2),
                text=f"{mem['s']}/{mem['sm']}",
                maxwidth=xs-5,
                size=(xs,50),
                v_align='center'
            )
        )
        # ping
        y -= self.height*0.1
        star_kid = bui.imagewidget(
            parent=self.parent,
            position=(x+9,y+6),
            size=(40,40),
            texture=bui.gettexture('star'),
            color=self.get_ping_colors(mem.get('ping'))[1],
        )
        self.mem_kids.append(star_kid)

        ping_kid = bui.textwidget(
            parent=self.parent,
            position=(x+60,y-2),
            text=Strings.TEXT_ELLIPSIS if mem.get('ping') is None else f"{int(mem['ping']*1000)} ms",
            color=self.get_ping_colors(mem.get('ping'))[1],
            maxwidth=xs-5,
            size=(xs,50),
            v_align='center'
        )
        self.mem_kids.append(ping_kid)

        # separator
        y -= self.height*0.02
        self.mem_kids.append(
            bui.imagewidget(
                parent=self.parent,
                position=(x+12,y),
                size=(self.width-self.scroll_xs-69,2),
                texture=bui.gettexture('white'),
                color=(1,1,1),
                opacity=0.1
            )
        )

        # now playing (TV Restored)
        y -= self.height*0.16
        tv_y = y
        self.mem_kids.append(
            bui.imagewidget(
                parent=self.parent,
                texture=bui.gettexture('tv'),
                position=(x+2,y+5),
                size=(
                    self.height*0.15,
                    self.height*0.15
                )
            )
        )
        self.mem_kids.append(
            bui.textwidget(
                parent=self.parent,
                size=(
                    bgx-self.height*0.15,
                    self.height*0.15
                ),
                position=(
                    x+self.height*0.15,
                    y
                ),
                text=Strings.TEXT_NOW_PLAYING,
                v_align='center'
            )
        )

        # Sniff Info Area (Game Info & Roster)
        sniff_y = 90
        sniff_h = tv_y - sniff_y
        self.sniff_w = (bgx - 30) / 2

        # Left Side: Game Info (No Scroll)
        self.sniff_left_container = bui.containerwidget(
            parent=self.parent,
            position=(x + 10, sniff_y),
            size=(self.sniff_w, sniff_h),
            background=False
        )
        self.mem_kids.append(self.sniff_left_container)

        self.sniff_game_name = bui.textwidget(
            parent=self.sniff_left_container,
            position=(0, sniff_h - 25),
            size=(self.sniff_w, 25),
            text="",
            maxwidth=self.sniff_w,
            color=Theme.TEXT_ENABLED,
            v_align='center'
        )
        self.sniff_game_desc = bui.textwidget(
            parent=self.sniff_left_container,
            position=(0, sniff_h - 50),
            size=(self.sniff_w, 25),
            text="",
            maxwidth=self.sniff_w,
            color=Theme.TEXT_LAZY,
            scale=0.8,
            v_align='center'
        )
        self.sniff_extra = bui.textwidget(
            parent=self.sniff_left_container,
            position=(0, 0),
            size=(self.sniff_w, sniff_h - 55),
            text="",
            maxwidth=self.sniff_w,
            color=Theme.TEXT_ENABLED,
            scale=0.7,
            v_align='top'
        )
        self.mem_kids.extend([self.sniff_game_name, self.sniff_game_desc, self.sniff_extra])

        # Right Side: Roster Scroll
        self.sniff_right_scroll = bui.scrollwidget(
            parent=self.parent,
            position=(x + 10 + self.sniff_w + 10, sniff_y),
            size=(self.sniff_w, sniff_h),
            color=(0.15,0.15,0.15)
        )
        self.sniff_right_container = bui.containerwidget(parent=self.sniff_right_scroll, size=(self.sniff_w, 100), background=False)
        self.mem_kids.extend([self.sniff_right_scroll, self.sniff_right_container])

        # bottom separator
        self.mem_kids.append(
            bui.imagewidget(
                parent=self.parent,
                position=(x+12,74),
                size=(self.width-self.scroll_xs-69,2),
                texture=bui.gettexture('white'),
                color=(1,1,1),
                opacity=0.1
            )
        )

        # Sniff Button
        sniff_btn_w = bgx * 0.3
        self.sniff_btn = bui.buttonwidget(
            parent=self.parent,
            label="Sniff",
            position=(x + bgx * 0.03, 12),
            size=(sniff_btn_w, 50),
            on_activate_call=bui.CallPartial(self.on_sniff_press, mem),
            texture=bui.gettexture('white'),
            color=(0.15,0.15,0.15),
            textcolor=Theme.TEXT_ENABLED,
            enable_sound=False
        )
        self.mem_kids.append(self.sniff_btn)

        # connect
        self.mem_kids.append(
            bui.buttonwidget(
                parent=self.parent,
                texture=bui.gettexture('white'),
                color=(0.15,0.15,0.15),
                label=Strings.BUTTON_CONNECT,
                position=(x+bgx*0.67,12),
                size=(bgx*0.3,50),
                textcolor=Theme.TEXT_ENABLED,
                enable_sound=False,
                on_activate_call=self.on_connect_press,
                id='connect_btn'
            )
        )
        # finally
        self.start_preview_ping(mem, ping_kid, star_kid)

    def populate_roster(self, roster):
        if not self.sniff_right_container or not self.sniff_right_container.exists():
            return

        for child in self.sniff_right_container.get_children():
            child.delete()

        if not roster:
            bui.textwidget(
                parent=self.sniff_right_container,
                position=(5, 5),
                size=(self.sniff_w - 10, 20),
                text="Empty or hidden.",
                scale=0.8,
                color=Theme.TEXT_LAZY
            )
            bui.containerwidget(edit=self.sniff_right_container, size=(self.sniff_w, 30))
            return

        item_h = 25
        total_h = max(100, len(roster) * item_h)
        bui.containerwidget(edit=self.sniff_right_container, size=(self.sniff_w, total_h))

        for i, player in enumerate(roster):
            y_pos = total_h - (i + 1) * item_h
            bui.textwidget(
                parent=self.sniff_right_container,
                position=(5, y_pos),
                size=(self.sniff_w - 10, item_h),
                text=player,
                maxwidth=self.sniff_w - 20,
                v_align='center',
                selectable=True,
                click_activate=True,
                on_activate_call=lambda: None
            )

    def on_sniff_press(self, mem):
        if getattr(self, 'sniff_client', None):
            self.sniff_client.abort()
            self.sniff_client = None

        if not self.online:
            bui.getsound('block').play()
            return
        bui.getsound('deek').play()
        if self.sniff_btn and self.sniff_btn.exists():
            bui.buttonwidget(
                edit=self.sniff_btn, 
                label='Sniffing...',
                color=Theme.BUTTON_DISABLED,
                textcolor=Theme.TEXT_DISABLED,
                on_activate_call=lambda: None
            )
        self.sniff_client = MinimalSniffClient(mem['a'], mem['p'], bui.CallPartial(self.on_sniff_result, mem))

    def on_sniff_result(self, mem, err, game_name, game_desc, extra_info, roster, map_name):
        if not self.alive or not self.data.get('mem') or (self.data['mem']['a'], self.data['mem']['p']) != (mem['a'], mem['p']):
            return # Navigated away

        if self.sniff_btn and self.sniff_btn.exists():
            bui.buttonwidget(
                edit=self.sniff_btn, 
                label='Sniff',
                color=(0.15, 0.15, 0.15),
                textcolor=Theme.TEXT_ENABLED,
                on_activate_call=bui.CallPartial(self.on_sniff_press, mem)
            )

        if err:
            if self.sniff_extra and self.sniff_extra.exists():
                bui.textwidget(edit=self.sniff_extra, text=f"Failed to sniff:\n{err}", color=Theme.TEXT_MARK)
            return

        if self.sniff_game_name and self.sniff_game_name.exists():
            bui.textwidget(edit=self.sniff_game_name, text=game_name)
        if self.sniff_game_desc and self.sniff_game_desc.exists():
            bui.textwidget(edit=self.sniff_game_desc, text=game_desc)
        if self.sniff_extra and self.sniff_extra.exists():
            if map_name:
                extra_info = f"Map: {map_name}\n\n{extra_info}".strip()
            bui.textwidget(edit=self.sniff_extra, text=extra_info)

        self.populate_roster(roster)

    def on_connect_press(self):
        bui.getsound('deek').play()
        if (classic:=bui.app.classic) is not None:
            classic.save_ui_state()
        connect_to_party(
            *self.data['lit_mem']
        )

    def reset_mem(self):
        if getattr(self, 'sniff_client', None):
            self.sniff_client.abort()
            self.sniff_client = None

        self.preview_ping_gen += 1
        for kid in self.mem_kids:
            if kid and kid.exists():
                kid.delete()
        self.mem_kids.clear()

        self.sniff_game_name = None
        self.sniff_game_desc = None
        self.sniff_extra = None
        self.sniff_right_container = None
        self.sniff_btn = None

    def on_close_press(self):
        bui.getsound('deek').play()
        self.preview(None, self.lit_kid)

    def start_preview_ping(self, mem, ping_kid, star_kid=None):
        gen = self.preview_ping_gen
        addr = (mem['a'], mem['p'])
        wait_secs = 0.001 * mem.get('pd', 500)

        def apply(rtt):
            if not self.alive or gen != self.preview_ping_gen: return
            if not ping_kid.exists(): return
            empty_c, full_c = self.get_ping_colors(rtt)
            bui.textwidget(
                ping_kid,
                text=(
                    Strings.TEXT_ELLIPSIS if rtt is None
                    else f"{int(rtt*1000)} ms"
                ),
                color=full_c
            )
            if star_kid and star_kid.exists():
                bui.imagewidget(star_kid, color=full_c)

        def worker():
            sock = socket(AF_INET, SOCK_DGRAM)
            sock.setblocking(False)
            try:
                while self.alive and gen == self.preview_ping_gen:
                    next_ping_time = bui.apptime() + wait_secs
                    start = monotonic()
                    try:
                        sock.sendto(b'\x0b', addr)
                    except Exception:
                        pass
                    rtt = None
                    while bui.apptime() < next_ping_time:
                        if not (self.alive and gen == self.preview_ping_gen):
                            return
                        try:
                            data, raddr = sock.recvfrom(1024)
                            if raddr == addr and data == b'\x0c':
                                rtt = monotonic() - start
                                break
                        except BlockingIOError:
                            pass
                        except Exception:
                            break
                        _sleep(0.01)
                    bui.pushcall(
                        bui.CallPartial(apply, rtt),
                        from_other_thread=True
                    )
                    if rtt is None:
                        continue
                    while bui.apptime() < next_ping_time:
                        if not (self.alive and gen == self.preview_ping_gen):
                            return
                        _sleep(0.01)
            finally:
                sock.close()

        Thread(target=worker, daemon=True).start()

    def copy_text(self, text):
        bui.getsound('ding').play()
        bui.clipboard_set_text(text)

    def on_ping_press(self):
        if not self.online:
            bui.getsound('block').play()
            return
        bui.getsound('deek').play()
        self.disable_ui()
        gen = self.gen
        self.ping_all(
            on_finish=bui.CallPartial(self.on_ping_finish, gen)
        )

    def on_ping_finish(self, gen):
        if not self.alive or gen != self.gen: return
        def ping_key(m):
            p = m.get('ping')
            return p if p is not None else float('inf')
        self.memory.sort(key=ping_key)
        self.reset_scroll()
        self.render_page(
            on_finish=self.enable_ui,
            catch_selected=True
        )

    def ping_all(self, on_finish=None, max_ping=0.5, max_concurrent=1000, tries=3):
        targets = list(self.visible_memory)

        class PingProtocol(DatagramProtocol):
            def __init__(self):
                self.pending = {}
                self.transport = None

            def connection_made(self, transport):
                self.transport = transport

            def datagram_received(self, data, addr):
                fut = self.pending.get(addr)
                if fut and not fut.done() and data == b'\x0c':
                    fut.set_result(monotonic())

        async def ping_one(mem, protocol, sem):
            async with sem:
                addr = (mem['a'], mem['p'])
                loop = get_running_loop()
                best = None
                for _ in range(tries):
                    fut = loop.create_future()
                    protocol.pending[addr] = fut
                    start = monotonic()
                    protocol.transport.sendto(b'\x0b', addr)
                    try:
                        end = await wait_for(fut, timeout=max_ping)
                        rtt = end - start
                        if best is None or rtt < best:
                            best = rtt
                    except TimeoutError:
                        pass
                    finally:
                        protocol.pending.pop(addr, None)
                mem['ping'] = best

        async def run_all():
            loop = get_running_loop()
            transport, protocol = (
                await loop.create_datagram_endpoint(
                    PingProtocol, local_addr=('0.0.0.0', 0)
                )
            )
            self.data['ping_transport'] = transport
            self.data['ping_loop'] = loop
            try:
                sem = Semaphore(max_concurrent)
                await gather(
                    *(ping_one(m, protocol, sem) for m in targets),
                    return_exceptions=True
                )
            finally:
                transport.close()
                if self.data.get('ping_transport') is transport:
                    self.data['ping_transport'] = None
                    self.data['ping_loop'] = None

        def worker():
            try: run(run_all())
            except Exception: pass
            on_finish and bui.pushcall(
                on_finish, from_other_thread=True
            )

        Thread(target=worker, daemon=True).start()

    def on_reset_press(self):
        bui.getsound('deek').play()
        self.reset_scroll()
        self.reset_mem()
        self.memory.clear()
        self.data['memory'] = self.memory
        self.data['visible_memory'] = []
        self.visible_memory = []
        self.data['lit_mem'] = None
        self.data['mem'] = None
        self.lit_kid = None
        self.data['page'] = self.page = 0
        self.total_pages = 1
        self.total_filtered = 0
        self.last_filter = ''
        self.data['last_filter'] = ''
        self.last_filter_ping = ''
        self.data['last_filter_ping'] = ''
        bui.textwidget(self.filter_input, text='')
        bui.textwidget(self.filter_hint, text=Strings.TEXT_FILTER)
        bui.textwidget(self.filter_ping_input, text='')
        bui.textwidget(
            self.filter_ping_hint, text=Strings.TEXT_FILTER_PING
        )
        self.set_nothing(
            self.online and
            Strings.TEXT_NOTHING or
            Strings.TEXT_OFFLINE
        )
        self.update_pages_ui()
        self.data['init_hidden'] and self.show_init()

    def hide_init(self):
        for widget in (
            self.title_text,
            self.version_text,
            self.splash_text
        ): widget.delete()
        self.data['init_hidden'] = True

    def start_filter_timer(self):
        self.data['filter_timer'] = bui.AppTimer(
            0.01, self.check_filter_inputs, repeat=True
        )

    def check_filter_inputs(self):
        if not self.alive: return
        if not self.filter_input.exists():
            self.abandon()
            return
        t = bui.textwidget(query=self.filter_input)
        if t != self.last_filter:
            self.last_filter = t
            self.data['last_filter'] = t
            bui.textwidget(
                self.filter_hint,
                text=(t and ' ' or Strings.TEXT_FILTER)
            )
            self.on_filter_changed()
        tp = bui.textwidget(query=self.filter_ping_input)
        if tp != self.last_filter_ping:
            self.last_filter_ping = tp
            self.data['last_filter_ping'] = tp
            bui.textwidget(
                self.filter_ping_hint,
                text=(tp and ' ' or Strings.TEXT_FILTER_PING)
            )
            self.on_filter_changed()

    def on_query_press(self):
        if not self.online:
            bui.getsound('block').play()
            return
        bui.getsound('deek').play()
        self.disable_ui()
        self.reset_scroll()
        self.query_servers()

    def reset_scroll(self):
        bui.containerwidget(
            self.memory_root,
            size=(1,1)
        )
        for group in (
            full:=self.memory_kids
        ):
            for arr in group:
                for kid in arr:
                    kid and kid.delete()
        full.clear()

    def enable_ui(self):
        if not self.alive: return
        bui.buttonwidget(
            self.query_btn,
            color=Theme.BUTTON_ENABLED,
            textcolor=Theme.TEXT_ENABLED,
            on_activate_call=self.on_query_press
        )
        bui.buttonwidget(
            self.ping_btn,
            color=Theme.BUTTON_ENABLED,
            textcolor=Theme.TEXT_ENABLED,
            on_activate_call=self.on_ping_press
        )
        bui.buttonwidget(
            self.reset_btn,
            color=Theme.BUTTON_ENABLED,
            textcolor=Theme.TEXT_ENABLED,
            on_activate_call=self.on_reset_press
        )
        self.update_pages_ui()

    def disable_ui(self):
        bui.buttonwidget(
            self.query_btn,
            color=Theme.BUTTON_DISABLED,
            textcolor=Theme.TEXT_DISABLED,
            on_activate_call=lambda:None
        )
        bui.buttonwidget(
            self.ping_btn,
            color=Theme.BUTTON_DISABLED,
            textcolor=Theme.TEXT_DISABLED,
            on_activate_call=lambda:None
        )
        bui.buttonwidget(
            self.reset_btn,
            color=Theme.BUTTON_DISABLED,
            textcolor=Theme.TEXT_DISABLED,
            on_activate_call=lambda:None
        )
        bui.buttonwidget(
            self.left_btn,
            color=Theme.BUTTON_DISABLED,
            textcolor=Theme.TEXT_DISABLED,
            on_activate_call=lambda:None
        )
        bui.buttonwidget(
            self.right_btn,
            color=Theme.BUTTON_DISABLED,
            textcolor=Theme.TEXT_DISABLED,
            on_activate_call=lambda:None
        )
        bui.textwidget(
            self.page_btn,
            color=Theme.TEXT_DISABLED,
            on_activate_call=lambda:None
        )

    def set_nothing(self, text):
        if not self.alive: return
        bui.textwidget(
            self.nothing_text,
            text=text
        )

    def on_filter_changed(self):
        self.render_memory()

    def render_memory(self):
        self.disable_ui()
        self.reset_scroll()
        self.render_page(
            on_finish=self.enable_ui,
            catch_selected=True
        )

    def query_servers(self):
        gen = self.gen
        bui.app.plus.add_v1_account_transaction(
            {
                'type': 'PUBLIC_PARTY_QUERY',
                'proto': protocol_version(),
                'lang': bui.app.lang.language
            },
            callback=bui.CallPartial(self.on_query_result, gen)
        )
        bui.app.plus.run_v1_account_transactions()

    def on_query_result(self, gen, data):
        if not self.alive or gen != self.gen: return
        data = data['l']
        self.set_nothing('')
        self.render_page(
            data,
            on_finish=self.enable_ui,
            catch_selected=True
        )

    def calc_filtered(self):
        lf = self.last_filter.lower()
        try: max_ping = float(self.last_filter_ping)
        except ValueError: max_ping = None
        result = list(self.memory)
        if lf:
            result = [
                m for m in result
                if lf in m['a'] or lf in m['n'].lower()
            ]
        if max_ping is not None:
            result = [
                m for m in result
                if (p:=m.get('ping')) is not None
                and p*1000 <= max_ping
            ]
        return result

    def render_page(self, data=None, on_finish=None, catch_selected=False):
        if not self.alive: return
        if data is not None:
            self.memory = self.data['memory'] = data
        filtered = self.calc_filtered()
        self.visible_memory = self.data['visible_memory'] = filtered
        total_pages = max(1, ceil(len(filtered)/self.page_size))
        page = self.data.get('page', 0) or 0
        if catch_selected and (lit:=self.data.get('lit_mem')):
            for i, m in enumerate(filtered):
                if (m['a'],m['p']) == lit:
                    page = i//self.page_size
                    break
        page = max(0, min(page, total_pages-1))
        self.data['page'] = self.page = page
        self.total_pages = total_pages
        self.total_filtered = len(filtered)
        page_slice = filtered[
            page*self.page_size : page*self.page_size+self.page_size
        ]
        self.render(page_slice, on_finish=on_finish)

    def update_pages_ui(self):
        page = self.page
        total = self.total_pages
        no_pages = total <= 1
        bui.textwidget(
            self.page_btn,
            text=f'{page+1}/{total}',
            color=(
                Theme.TEXT_DISABLED if no_pages
                else Theme.TEXT_ENABLED
            ),
            on_activate_call=(
                (lambda:None) if no_pages
                else self.on_page_snap_press
            )
        )
        at_first = page <= 0
        at_last = page >= total-1
        bui.buttonwidget(
            self.left_btn,
            color=(
                Theme.BUTTON_DISABLED if at_first
                else Theme.BUTTON_ENABLED
            ),
            textcolor=(
                Theme.TEXT_DISABLED if at_first
                else Theme.TEXT_ENABLED
            ),
            on_activate_call=(
                (lambda:None) if at_first
                else self.on_page_left
            )
        )
        bui.buttonwidget(
            self.right_btn,
            color=(
                Theme.BUTTON_DISABLED if at_last
                else Theme.BUTTON_ENABLED
            ),
            textcolor=(
                Theme.TEXT_DISABLED if at_last
                else Theme.TEXT_ENABLED
            ),
            on_activate_call=(
                (lambda:None) if at_last
                else self.on_page_right
            )
        )

    def on_page_left(self):
        if self.page <= 0: return
        bui.getsound('deek').play()
        self.data['page'] = self.page-1
        self.disable_ui()
        self.reset_scroll()
        self.render_page(on_finish=self.enable_ui)

    def on_page_right(self):
        if self.page >= self.total_pages-1: return
        bui.getsound('deek').play()
        self.data['page'] = self.page+1
        self.disable_ui()
        self.reset_scroll()
        self.render_page(on_finish=self.enable_ui)

    def on_page_snap_press(self):
        if not self.data.get('lit_mem'):
            return
        self.disable_ui()
        self.reset_scroll()
        self.render_page(
            on_finish=self.enable_ui,
            catch_selected=True
        )

    def render(self, data, on_finish=None):
        if self.rendering:
            self.clear_render(final=True)
        self.rendering = True
        self.memory_set = (m for m in data)
        self.memory_total = len(data)
        self.memory_index = 0
        self.lit_kid = None
        self.lit_mem_ref = self.data['lit_mem']
        self.data['render_timer'] = (
            bui.AppTimer(
                0.0001, self.render_step, repeat=True
            ),
            on_finish
        )

    def get_ping_colors(self, ping):
        if ping is None:
            c = (0.5, 0.5, 0.5)
        else:
            p = ping * 1000
            if p < 100:
                c = (0.2, 1.0, 0.2)
            elif p < 200:
                r = (p - 100) / 100.0
                c = (0.2 + 0.8 * r, 1.0, 0.2)
            elif p < 300:
                r = (p - 200) / 100.0
                c = (1.0, 1.0 - 0.8 * r, 0.2)
            else:
                c = (1.0, 0.2, 0.2)
        return (c[0]*0.15, c[1]*0.15, c[2]*0.15), (c[0]*0.5, c[1]*0.5, c[2]*0.5)

    def render_step(self):
        if not self.alive:
            return
        try: mem = next(self.memory_set)
        except StopIteration:
            return self.on_render_finish()
        lf = self.last_filter.lower()
        pos_y = (self.memory_total-1-self.memory_index)*30
        text_xs = self.scroll_xs-20

        empty_c, full_c = self.get_ping_colors(mem.get('ping'))

        kids = (
            bui.imagewidget(
                parent=self.memory_root,
                size=(text_xs,30),
                position=(0,pos_y),
                texture=bui.gettexture('white'),
                color=empty_c
            ),
            bui.imagewidget(
                parent=self.memory_root,
                size=(text_xs*(mem['s']/mem['sm']),30),
                position=(0,pos_y),
                texture=bui.gettexture('white'),
                color=full_c
            ),
            kid:=bui.textwidget(
                parent=self.memory_root,
                size=(text_xs,30),
                position=(0,pos_y),
                text=(nam:=mem['n']),
                selectable=True,
                click_activate=True,
                maxwidth=text_xs,
                v_align='center',
                glow_type='uniform',
                id=str(self.memory_index)
            )
        )
        namw = self.measure_text(nam)
        if lf and nam.isascii() and namw:
            lfw = self.measure_text(lf)
            li = -1
            overs = []
            while lfw:
                li = nam.lower().find(lf,li+1)
                if li < 0: break
                left = self.measure_text(
                    nam[:li]
                )
                sc = min(1, text_xs/namw)
                overs.append(
                    bui.textwidget(
                        parent=self.memory_root,
                        text=nam[li:li+len(lf)],
                        color=Theme.TEXT_MARK,
                        position=(left*sc,pos_y),
                        size=(lfw,30),
                        v_align='center',
                        scale=sc
                    )
                )
        else: overs = ()
        lit = (mem['a'],mem['p']) == self.lit_mem_ref
        bui.textwidget(
            kid,
            on_activate_call=bui.CallPartial(
                self.preview, mem, kid
            ),
            color=(
                self.lit_mem_ref and lit
                and Theme.TEXT_SELECTED
                or Theme.TEXT_ENABLED
            )
        )
        if lit: self.lit_kid = kid
        self.memory_index += 1
        bui.containerwidget(
            self.memory_root,
            size=(
                self.scroll_xs,
                self.memory_index*30
            )
        )
        self.memory_kids.append((kids,overs))

    def measure_text(self, text):
        return bui.get_string_width(
            text, True
        )

    def scroll_to(self, kid):
        if kid and kid.exists():
            bui.containerwidget(
                self.memory_root,
                visible_child=kid
            )

    def on_render_finish(self):
        if not self.alive:
            self.clear_render(final=True)
            return
        self.set_nothing(
            self.memory_index and ' ' or
            Strings.TEXT_NOTHING
        )
        self.scroll_to(self.lit_kid)
        self.clear_render()

    def clear_render(self, final=False):
        callable(
            on_finish:=self.data.pop(
                'render_timer'
            )[1]
        ) and not final and on_finish()
        self.rendering = False
        del self.lit_mem_ref
        del self.memory_index
        del self.memory_set
        del self.memory_total

    def preview(self, mem, kid=None):
        if kid and kid == self.lit_kid:
            bui.textwidget(
                kid,
                color=Theme.TEXT_ENABLED
            )
            self.lit_kid = None
            self.data['lit_mem'] = None
            self.data['mem'] = None
            self.data['init_hidden'] and self.show_init()
            return
        if (
            (lit:=self.lit_kid)
            and lit.exists()
        ):
            bui.textwidget(
                lit,
                color=Theme.TEXT_ENABLED
            )
        self.lit_kid = kid
        bui.textwidget(
            kid,
            color=Theme.TEXT_SELECTED
        )
        self.data['lit_mem'] = (mem['a'],mem['p'])
        self.data['mem'] = mem
        not self.data['init_hidden'] and self.hide_init()
        self.render_mem(mem)
        kid and self.scroll_to(kid)

    def abandon(self):
        self.alive = False
        if getattr(self, 'sniff_client', None):
            self.sniff_client.abort()
            self.sniff_client = None

        self.preview_ping_gen += 1
        self.data['filter_timer'] = None
        self.data['online_timer'] = None
        if self.rendering:
            self.clear_render(final=True)
        transport = self.data.pop('ping_transport', None)
        loop = self.data.pop('ping_loop', None)
        if transport is not None and loop is not None:
            try:
                loop.call_soon_threadsafe(transport.close)
            except Exception: pass

    def on_deactivate(self):
        self.abandon()
        self.parent.delete()

    def save_state(self):
        self.abandon()

class HuffmanNode:
    def __init__(self):
        self.left_child_index = -1
        self.right_child_index = -1
        self.parent_index = 0
        self.bit_count = 0
        self.bit_value = 0
        self.frequency = 0

class HuffmanCodec:
    def __init__(self):
        frequencies = [
            101342, 9667, 3497, 1072, 0, 3793, 0, 0, 2815, 5235,
            *([0]*3), 3570, *([0]*3), 1383, *([0]*3), 2970, 0, 0, 2857,
            *([0]*8), 1199, *([0]*29), 1494, 1974, *([0]*12), 1351,
            *([0]*113), 1475, *([0]*64)
        ]
        self.nodes = [HuffmanNode() for _ in range(511)]
        for i in range(256): self.nodes[i].frequency = frequencies[i]

        curr = 256
        while curr < 511:
            search = 0
            while self.nodes[search].parent_index != 0: search += 1
            min1 = search
            search += 1
            while self.nodes[search].parent_index != 0: search += 1
            min2 = search
            search += 1
            while search < curr:
                if self.nodes[search].parent_index == 0:
                    if self.nodes[min1].frequency > self.nodes[min2].frequency:
                        if self.nodes[search].frequency < self.nodes[min1].frequency: min1 = search
                    else:
                        if self.nodes[search].frequency < self.nodes[min2].frequency: min2 = search
                search += 1

            self.nodes[curr].frequency = self.nodes[min1].frequency + self.nodes[min2].frequency
            self.nodes[min1].parent_index = curr - 255
            self.nodes[min2].parent_index = curr - 255
            self.nodes[curr].right_child_index = min1
            self.nodes[curr].left_child_index = min2
            curr += 1

    def DecompressPayload(self, input_data: bytes) -> bytes:
        if not input_data: return bytes()
        rem = input_data[0] & 0x0F
        is_comp = (input_data[0] >> 7) & 1
        if not is_comp: return input_data

        total_bits = (len(input_data) - 1) * 8 - rem
        out = []
        b_pos = 0
        b_off = 1

        while b_pos < total_bits:
            bit = (input_data[b_off + b_pos // 8] >> (b_pos % 8)) & 1
            b_pos += 1
            if bit:
                n_idx = 510
                res = 0
                while True:
                    bit = (input_data[b_off + b_pos // 8] >> (b_pos % 8)) & 1
                    if bit == 0:
                        if self.nodes[n_idx].left_child_index == -1: res = n_idx; break
                        else: n_idx = self.nodes[n_idx].left_child_index; b_pos += 1
                    else:
                        if self.nodes[n_idx].right_child_index == -1: res = n_idx; break
                        else: n_idx = self.nodes[n_idx].right_child_index; b_pos += 1

                    if self.nodes[n_idx].left_child_index == -1 and self.nodes[n_idx].right_child_index == -1:
                        res = n_idx; break
                    if b_pos > total_bits: return bytes(out)
                out.append(res & 0xFF)
            else:
                idx = b_off + b_pos // 8
                off = b_pos % 8
                if off != 0: res = (input_data[idx] >> off) | (input_data[idx + 1] << (8 - off))
                else: res = input_data[idx]
                out.append(res & 0xFF)
                b_pos += 8
                if b_pos > total_bits: return bytes(out)
        return bytes(out)

class MinimalSniffClient:
    def __init__(self, ip, port, callback):
        self.ip = ip
        self.port = port
        self.callback = callback
        self.nodes = {}
        self.game_name = ""
        self.game_desc = ""
        self.map_name = ""
        self.roster = []
        self.multipart_buffer = b""
        self.huff = HuffmanCodec()
        self._aborted = False
        Thread(target=self._run, daemon=True).start()

    def abort(self):
        self._aborted = True

    def parse_session_commands(self, body):
        cursor = 0
        length = len(body)
        while cursor < length:
            if cursor + 2 > length: break
            cmd_len = unpack_from('<H', body, cursor)[0]
            cursor += 2
            if cursor + cmd_len > length: break
            cmd_body = body[cursor:cursor+cmd_len]
            cursor += cmd_len
            if not cmd_body: continue

            cmd = cmd_body[0]
            data = cmd_body[1:]

            if cmd == 4:
                if len(data) >= 12:
                    _, type_id, node_id = unpack_from('<iii', data)
                    self.nodes[node_id] = {"type": type_id, "attrs": {}, "connects": []}
            elif cmd == 7:
                if len(data) >= 4:
                    self.nodes.pop(unpack_from('<i', data)[0], None)
            elif cmd == 26:
                if len(data) >= 12:
                    node_id, attr_id = unpack_from('<ii', data, 0)
                    str_len = unpack_from('<I', data, 8)[0]
                    if len(data) >= 12 + str_len:
                        s = data[12:12+str_len].decode('utf-8', errors='replace').strip('\x00')
                        if node_id in self.nodes:
                            self.nodes[node_id]["attrs"][attr_id] = s
                        if '"gameNames"' in s or '"gameDescriptions"' in s:
                            try:
                                p = loads(s)
                                t = p.get('t', [])
                                if len(t) >= 2:
                                    if t[0] == "gameNames": self.game_name = t[1]
                                    elif t[0] == "gameDescriptions":
                                        desc = t[1]
                                        for sub_item in p.get("s", []):
                                            if len(sub_item) == 2: desc = desc.replace(sub_item[0], str(sub_item[1]))
                                        self.game_desc = desc
                            except Exception: pass
            elif cmd == 22:
                if len(data) >= 12:
                    node_id, attr_id, val = unpack_from('<iii', data)
                    if node_id in self.nodes:
                        self.nodes[node_id]["attrs"][attr_id] = val
            elif cmd == 24:
                if len(data) >= 12:
                    node_id, attr_id, count = unpack_from('<iii', data)
                    if len(data) >= 12 + count*4:
                        floats = unpack_from(f'<{count}f', data, 12)
                        if node_id in self.nodes:
                            self.nodes[node_id]["attrs"][attr_id] = floats
            elif cmd == 19:
                if len(data) >= 16:
                    src_n, src_a, dst_n, dst_a = unpack_from('<iiii', data)
                    if dst_n in self.nodes:
                        self.nodes[dst_n]["connects"].append((src_n, src_a, dst_a))

    def parse_roster(self, body):
        if not body: return
        try:
            rlist = loads(body[:-1].decode('utf-8', errors='replace'))
            self.roster.clear()
            for e in rlist:
                spec = loads(e.get('spec', '{}'))
                players = e.get('p', [])
                if players:
                    for p in players:
                        self.roster.append(p.get('n', 'Unknown'))
                else:
                    name = spec.get('n', 'Unknown')
                    if name: self.roster.append(name + " (Spectating)")
        except Exception: pass

    def GatherSceneText(self):
        nodes = self.nodes

        def _parse_hud_val(val):
            try:
                p = loads(val)
                if isinstance(p, dict) and "t" in p and len(p["t"]) > 1:
                    t_name = p["t"][0]
                    if t_name in ("gameNames", "gameDescriptions"):
                        return None
                    base = p["t"][1]
                    for sub_item in p.get("s", []):
                        if len(sub_item) == 2:
                            base = base.replace(sub_item[0], str(sub_item[1]))
                    return base
            except Exception:
                pass
            return str(val).strip()

        extra_parts = []

        for nid, node in nodes.items():
            if node["type"] == 9:
                raw_val = node.get("attrs", {}).get(5, "")
                if not raw_val or not str(raw_val).strip():
                    continue
                parsed_val = _parse_hud_val(raw_val)
                if not parsed_val:
                    continue

                pos = node.get("attrs", {}).get(4, (0.0, 0.0, 0.0))
                y = round(pos[1], 1) if isinstance(pos, (list, tuple)) and len(pos) >= 2 else 0.0
                x = round(pos[0], 1) if isinstance(pos, (list, tuple)) and len(pos) >= 2 else 0.0
                extra_parts.append((parsed_val, y, x))

        extra_parts.sort(key=lambda i: (-i[1], i[2]))

        lines = []
        current_line = []
        current_y = None
        for p_val, y, x in extra_parts:
            if current_y is None:
                current_y = y
            if abs(y - current_y) > 25.0:
                lines.append(" | ".join(current_line))
                current_line = [p_val]
                current_y = y
            else:
                current_line.append(p_val)
        if current_line:
            lines.append(" | ".join(current_line))

        return "\n".join(lines)

    def _run(self):
        try:
            sock = socket(AF_INET, SOCK_DGRAM)
            sock.settimeout(1.0)

            client_id = f"{randint(71, 200):02x}"
            uuid_b = str(uuid4()).encode()

            req = bytes([24, 33, 0]) + bytes.fromhex(client_id) + uuid_b
            sock.sendto(req, (self.ip, self.port))

            host_id = None
            start_time = time()
            while time() - start_time < 3.0:
                if self._aborted: return
                try:
                    data, _ = sock.recvfrom(2048)
                    if data[0] == 25:
                        host_id = f"{data[1]:02x}"
                        break
                    elif data[0] in (26, 27, 28, 29):
                        return self._finish("Connection Denied by Server")
                except timeout:
                    sock.sendto(req, (self.ip, self.port))

            if not host_id: return self._finish("Timeout waiting for accept")

            host_spec = ""
            host_salt = ""
            start_time = time()
            while time() - start_time < 3.0:
                if self._aborted: return
                try:
                    data, _ = sock.recvfrom(2048)
                    if data[0] == 37:
                        dec = self.huff.DecompressPayload(data[2:])
                        if dec and dec[0] == 15:
                            j_start = dec.find(b'{')
                            if j_start != -1:
                                hs = loads(dec[j_start:].decode(errors='ignore').rstrip('\x00'))
                                host_spec, host_salt = hs.get('s', ''), hs.get('l', '')
                            break
                except timeout: pass

            spec = dumps({'s': dumps({'n': '', 'a': 'Proto', 'sn': ''}), 'd': 'device'}).encode()
            hres = bytes([36]) + bytes.fromhex(host_id) + bytes([16, 33, 0]) + spec
            sock.sendto(hres, (self.ip, self.port))

            try: import _babase; ph = _babase.calc_v1_peer_hash(host_spec + host_salt)
            except Exception: ph = "fallback"

            auth = dumps({'b': 14248, 'tk': '', 'ph': ph}).encode()
            sock.sendto(bytes([36]) + bytes.fromhex(host_id) + bytes([17, 0, 0, 0, 0, 0, 18]) + auth, (self.ip, self.port))
            sock.sendto(bytes([36]) + bytes.fromhex(host_id) + bytes([17, 1, 0, 0, 0, 0, 21]) + b'{}', (self.ip, self.port))
            sock.sendto(bytes([36]) + bytes.fromhex(host_id) + bytes([17, 2, 0, 0, 0, 0, 3]) + b'', (self.ip, self.port))

            start_time = time()
            sock.settimeout(0.5)
            while time() - start_time < 2.5:
                if self._aborted: return
                try:
                    data, _ = sock.recvfrom(4096)
                    if data[0] == 37:
                        dec = self.huff.DecompressPayload(data[2:])
                        if dec and dec[0] == 17:
                            msg_type = dec[6]
                            msg_body = dec[7:]

                            if not self.map_name:
                                matches = findall(b'([a-zA-Z0-9_]+)LevelColor', msg_body)
                                if not matches:
                                    matches = findall(b'([a-zA-Z0-9_]+)LevelCollide', msg_body)
                                if matches:
                                    raw_id = matches[0].decode('utf-8', errors='ignore')
                                    s = sub(r'(.)([A-Z][a-z]+)', r'\1 \2', raw_id)
                                    s = sub(r'([a-z0-9])([A-Z])', r'\1 \2', s)
                                    self.map_name = s.title()

                            if msg_type == 1: self.parse_session_commands(msg_body)
                            elif msg_type == 13: self.multipart_buffer += msg_body
                            elif msg_type == 14:
                                full = self.multipart_buffer + msg_body
                                self.multipart_buffer = b""
                                if full[0] == 1: self.parse_session_commands(full[1:])
                                elif full[0] == 9: self.parse_roster(full[1:])
                            elif msg_type == 9: self.parse_roster(msg_body)
                except timeout: pass

            sock.sendto(bytes([32]) + bytes.fromhex(host_id), (self.ip, self.port))
            self._finish(None)
        except Exception as e:
            self._finish(f"Error: {e}")

    def _finish(self, err):
        if self._aborted: return
        bui.pushcall(lambda: self.callback(err, self.game_name, self.game_desc, self.GatherSceneText(), self.roster, self.map_name), from_other_thread=True)

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(bui.Plugin):
    def __init__(self):
        nam = Strings.TEXT_PUBLIC_PLUS
        tid = type(nam, (), {'value': nam})
        old_tr = TabRow.__init__
        def new(slf, par, dfs, *arg, **kwg):
            if (
                (cal := getattr(
                    kwg.get('on_select_call'), '_call', None
                )) and getattr(cal.obj(),'_r',None) == 'gatherWindow'
            ):
                dfs.insert(2, (tid, nam))
            old_tr(slf, par, dfs, *arg, **kwg)
        TabRow.__init__ = new
        old_gw = GatherWindow.__setattr__
        def new(slf, att, val):
            if att == '_tabs':
                val[tid] = PublicPlusTab(slf)
            old_gw(slf, att, val)
        GatherWindow.__setattr__ = new
        GatherWindow.TabID._value2member_map_[nam] = tid
