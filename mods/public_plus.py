# Copyright 2026 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Discord >> @BrotherBoard

"""
Public+

Because the current public tab is boring.
Adds a new tab at the gather window.
Experimental.
"""

import bauiv1 as bui
from bauiv1lib.tabs import TabRow
from bascenev1 import protocol_version
from bauiv1lib.gather import GatherTab, GatherWindow

from random import choice
from math import ceil
from threading import Thread
from collections import defaultdict
from asyncio import (
    wait_for, gather, Semaphore,
    TimeoutError, run,
    DatagramProtocol, get_running_loop
)
from time import monotonic, sleep as _sleep

__version__ = '1.0'

class Strings:
    BUTTON_QUERY = 'Query'
    BUTTON_PING = 'Ping'
    BUTTON_RESET = 'Reset'
    TEXT_PUBLIC_PLUS = 'Public+'
    TEXT_VERSION = 'Version {}'
    TEXT_FILTER='Filter'
    TEXT_FILTER_PING='Max Ping (ms)'
    TEXT_NOTHING = 'Nothing'
    TEXT_PINGING_DOTS = '...'
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
        # bg
        self.mem_kids.append(
            bui.imagewidget(
                parent=self.parent,
                position=(self.scroll_xs+10,0),
                size=(
                    self.width-self.scroll_xs-45,
                    self.height-75
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
        self.mem_kids.append(
            star_kid:=bui.imagewidget(
                parent=self.parent,
                position=(x+9,y+6),
                size=(40,40),
                texture=bui.gettexture('star'),
                color=self.get_ping_colors(mem.get('ping'))[1],
            )
        )
        self.mem_kids.append(
            ping_kid:=bui.textwidget(
                parent=self.parent,
                position=(x+60,y-2),
                text=Strings.TEXT_PINGING_DOTS if mem.get('ping') is None else f"{int(mem['ping']*1000)} ms",
                color=self.get_ping_colors(mem.get('ping'))[1],
                maxwidth=xs-5,
                size=(xs,50),
                v_align='center'
            )
        )
        # separator
        y -= self.height*0.02
        self.mem_kids.append(
            bui.imagewidget(
                parent=self.parent,
                position=(x+20,y),
                size=(self.width-self.scroll_xs-85,2),
                texture=bui.gettexture('white'),
                color=(1,1,1),
                opacity=0.1
            )
        )
        # finally
        self.start_preview_ping(mem, ping_kid, star_kid)

    def reset_mem(self):
        self.preview_ping_gen += 1
        for kid in self.mem_kids:
            kid.delete()
        self.mem_kids.clear()

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
                    Strings.TEXT_PINGING_DOTS if rtt is None
                    else f"{int(rtt*1000)} ms"
                ),
                color=full_c
            )
            if star_kid and star_kid.exists():
                bui.imagewidget(star_kid, color=full_c)

        def worker():
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
        self.set_nothing(Strings.TEXT_NOTHING)
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
        self.preview_ping_gen += 1
        self.data['filter_timer'] = None
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
                )) and cal.obj()._r == 'gatherWindow'
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

