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
from collections import defaultdict

__version__ = '1.0'

class Strings:
    BUTTON_QUERY = 'Query'
    TEXT_PUBLIC_PLUS = 'Public+'
    TEXT_VERSION = 'Version {}'
    TEXT_FILTER='Filter'
    TEXT_NOTHING = 'Nothing'
    TEXT_READY = 'Ready.'
    TEXT_QUERYING = 'Querying...'
    TEXT_LISTING = 'Listing...'
    TEXT_FILTERING = 'Filtering...'
    TEXT_FOUND_SERVERS = 'Found {} servers.'
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
    BLOCK_EMPTY = (0,0,0)
    BLOCK_FULL = (0.3,0.3,0.3)
    DEBUG = (1,1,0)

class PublicPlusTab(GatherTab):
    DATA = defaultdict(list)
    def __init__(self,*a):
        self.data = type(self).DATA
        self.rendering = False
        self.lit_kid = None
        self.last_filter = self.data.get('last_filter','')
        self.memory = self.data['memory']
        self.memory_kids = []

    def on_activate(
        self, parent, btn, width, height, left, bottom
    ):
        # math
        mx,my,me = 21,14,10
        scroll_xs = width*0.4
        btn_ys = 50
        scroll_ys = height-2*my-btn_ys-me-40
        btn_xs = scroll_xs/3
        # export
        self.scroll_xs = scroll_xs
        # parent
        self.parent = bui.containerwidget(
            parent=parent,
            position=(left+mx, bottom+my),
            size=(width-mx*2,height*-my*2),
            background=False
        )
        # filter
        self.filter_hint = bui.textwidget(
            parent=self.parent,
            size=(scroll_xs-5,40),
            position=(10,scroll_ys+btn_ys+me),
            color=Theme.TEXT_LAZY,
            text=Strings.TEXT_FILTER,
            v_align='center'
        )
        self.filter_input = bui.textwidget(
            parent=self.parent,
            size=(scroll_xs-5,40),
            position=(5,scroll_ys+btn_ys+me),
            glow_type='uniform',
            editable=True,
            id='filter_input',
            color=Theme.TEXT_ENABLED,
            description=Strings.TEXT_FILTER,
            v_align='center'
        )
        self.start_filter_timer()
        # memory
        self.memory_root = bui.containerwidget(
            parent=bui.scrollwidget(
                parent=self.parent,
                size=(scroll_xs,scroll_ys),
                border_opacity=0.7,
                position=(0,btn_ys+me)
            ),
            background=False
        )
        # query
        self.query_btn = bui.buttonwidget(
            parent=self.parent,
            button_type='square',
            label=Strings.BUTTON_QUERY,
            color=Theme.BUTTON_ENABLED,
            textcolor=Theme.TEXT_ENABLED,
            size=(btn_xs,btn_ys),
            enable_sound=False,
            id='query_btn',
            on_activate_call=bui.CallPartial(
                self.on_query_press
            )
        )
        # info
        self.info_text = bui.textwidget(
            parent=self.parent,
            text=Strings.TEXT_READY,
            position=(btn_xs+me,0),
            size=(btn_xs*2,btn_ys),
            v_align='center',
            maxwidth=btn_xs*2-me*2,
            color=Theme.TEXT_ENABLED
        )
        # nothing
        self.nothing_text = bui.textwidget(
            parent=self.parent,
            color=Theme.TEXT_LAZY,
            position=(0,btn_ys),
            text=Strings.TEXT_NOTHING,
            size=(scroll_xs,scroll_ys),
            h_align='center',
            v_align='center'
        )
        # finally
        if self.memory:
            self.set_info(Strings.TEXT_LISTING)
            self.render_memory()
        if self.data['init_hidden']: return
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

    def hide_init(self):
        for widget in (
            self.title_text,
            self.version_text,
            self.splash_text
        ): widget.delete()
        self.data['init_hidden'] = True

    def start_filter_timer(self):
        self.data['filter_timer'] = bui.AppTimer(
            0.01, lambda: (
                (t:=bui.textwidget(query=self.filter_input))
                != self.last_filter and (
                    setattr(self,'last_filter',t)
                    or self.data.__setitem__(
                        'last_filter', t
                    )
                    or self.on_filter_changed(t)
                    or bui.textwidget(
                        self.filter_hint,
                        text=(
                            t and ' ' or Strings.TEXT_FILTER
                        )
                    )
                )
            ), repeat=True
        )

    def on_query_press(self):
        bui.getsound('deek').play()
        self.set_info(Strings.TEXT_QUERYING)
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
        bui.buttonwidget(
            self.query_btn,
            color=Theme.BUTTON_ENABLED,
            textcolor=Theme.TEXT_ENABLED,
            on_activate_call=self.on_query_press
        )

    def disable_ui(self):
        bui.buttonwidget(
            self.query_btn,
            color=Theme.BUTTON_DISABLED,
            textcolor=Theme.TEXT_DISABLED,
            on_activate_call=lambda:None
        )

    def set_info(self, text):
        bui.textwidget(
            self.info_text,
            text=text
        )

    def set_nothing(self, text):
        bui.textwidget(
            self.nothing_text,
            text=text
        )

    def on_filter_changed(self, text):
        self.set_info(Strings.TEXT_FILTERING)
        self.render_memory()

    def render_memory(self):
        if not self.memory: return
        self.disable_ui()
        self.reset_scroll()
        self.render(
            self.memory,
            on_finish=self.enable_ui
        )

    def query_servers(self):
        bui.app.plus.add_v1_account_transaction(
            {
                'type': 'PUBLIC_PARTY_QUERY',
                'proto': protocol_version(),
                'lang': bui.app.lang.language
            },
            callback=self.on_query_result
        )
        bui.app.plus.run_v1_account_transactions()

    def on_query_result(self, data):
        data = data['l']
        self.set_info(Strings.TEXT_LISTING)
        self.set_nothing('')
        self.render(
            data,
            on_finish=self.enable_ui
        )

    def render(self, data, on_finish=None):
        if not data: return
        if self.rendering:
            self.clear_render()
        self.memory = self.data['memory'] = data
        self.memory_set = (m for m in data)
        self.memory_index = 0
        self.lit_mem_ref = self.data['lit_mem']
        self.data['render_timer'] = (
            bui.AppTimer(
                0.0001, self.render_step, repeat=True
            ),
            on_finish
        )

    def render_step(self):
        try: mem = next(self.memory_set)
        except StopIteration:
            return self.on_render_finish()
        else:
            lf = self.last_filter.lower()
            if (
                lf and lf not in mem['a'] and
                lf not in mem['n'].lower()
            ): return
        pos_y = self.memory_index*30
        text_xs = self.scroll_xs-20
        kids = (
            bui.imagewidget(
                parent=self.memory_root,
                size=(text_xs,30),
                position=(0,pos_y),
                texture=bui.gettexture('white'),
                color=Theme.BLOCK_EMPTY
            ),
            bui.imagewidget(
                parent=self.memory_root,
                size=(text_xs*(mem['s']/mem['sm']),30),
                position=(0,pos_y),
                texture=bui.gettexture('white'),
                color=Theme.BLOCK_FULL
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
        if lf:
            lfw = self.measure_text(lf)
            li = -1
            overs = []
            while True:
                li = nam.lower().find(lf,li+1)
                if li < 0: break
                left = self.measure_text(
                    nam[:li]
                )
                sc = min(
                    1,
                    text_xs/self.measure_text(
                        nam
                    )
                )
                overs.append(
                    bui.textwidget(
                        parent=self.memory_root,
                        text=nam[li:li+len(lf)],
                        color=Theme.DEBUG,
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
        self.set_info(
            Strings.TEXT_FOUND_SERVERS.format(
                self.memory_index
            )
        )
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

    def preview(self, mem, kid=None):
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

    def abandon(self):
        type(self).DATA['filter_timer'] = None
        if self.rendering:
            self.clear_render(final=True)

    def on_deactivate(self):
        self.abandon()
        self.parent.delete()

    def save_state(self):
        self.abandon()

    def restore_state(self):
        pass

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
