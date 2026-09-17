# Copyright 2026 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Discord >> @BrotherBoard

"""
BRP Studio v1.0 - Simple Replay Editor

Experimental.
"""

import bauiv1 as bui
import bauiv1x as xui
import bascenev1 as bs

from babase import AppSubsystem
from os.path import join, exists
from bauiv1lib.tabs import TabRow
from bauiv1lib.watch import WatchWindow

class Strings:
    BRP_STUDIO = 'BRP Studio'
    MY_STUDIO = 'My Studio'
    NEXT = 'Next'
    RELATIVE_TO = 'Relative to'
    ENTER_FILENAME = 'Enter filename'
    ENTER_SOMETHING = 'Enter something'
    FILE_DOES_NOT_EXIST = 'File does not exist'
    FILE_IS_NOT_A_REPLAY = 'File is not a replay'
    FILE = 'File'

class Const:
    ID_PREFIX = 'brp_studio'

class Color:
    WATCH_BUTTON = (0.6, 0.53, 0.63)
    WATCH_BUTTON_TEXT = (0.75, 0.7, 0.8)
    ALERT = (0.8, 0.8, 0)
    TEXT = (0,0,0)
    BACKGROUND = (1,1,1)

class Extra:
    BY_SCALE = lambda a,b,c: (
        (
            scale := bui.app.ui_v1.uiscale
        ) and (
            a if scale is bui.UIScale.SMALL else
            b if scale is bui.UIScale.MEDIUM else
            c
        )
    )

class Studio:
    INSTANCE = None

    def __init__(
        self,
        path: str
    ):
        # activity
        bs.new_replay_session(path)
        # math
        real = bui.get_virtual_screen_size()
        rx, ry = real
        bx,by = rx * 0.08, ry * 0.05
        # parent
        self.parent = bui.get_special_widget(
            'overlay_stack'
        )
        # root
        self.root = bui.containerwidget(
            parent=self.parent,
            size=real,
            background=False
        )
        import bauiv1x as xui
        # file
        xui.Button(
            parent=self.root,
            size=(bx,by),
            label=Strings.FILE,
            position=(
                0, ry - by
            ),
            color=Color.BACKGROUND,
            textcolor=Color.TEXT
        )

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(bui.Plugin):
    def __init__(self):
        # append tab
        aaa = TabRow.__init__
        tid = (
            type(
                '',
                (),
                {
                    'value': (
                        Const.ID_PREFIX
                    )
                }
            ),
            Strings.MY_STUDIO
        )
        TabRow.__init__ = lambda \
            _, \
            parent, \
            tabdefs, \
            pos, \
            size, \
            *, \
            on_select_call = None, \
            idprefix = None \
        : (
            tabdefs and
            tabdefs[0] and
            tabdefs[0][0] == (
                WatchWindow.TabID.MY_REPLAYS
            ) and (
                (
                    tabdefs := (
                        *tabdefs,
                        tid
                    )
                ) and (
                    size := (
                        size[0] + (
                            size[0] /
                            len(tabdefs)
                        ),
                        size[1]
                    )
                ) and (
                    pos := (
                        pos[0] - (
                            size[0] /
                            (
                                len(tabdefs) + 2
                            )
                        ),
                        pos[1]
                    )
                ) and (
                    not True
                )
            ) or
            aaa(
                _,
                parent,
                tabdefs,
                pos,
                size,
                on_select_call=on_select_call,
                idprefix=idprefix
            )
        )
        # append function
        aab = WatchWindow._set_tab
        WatchWindow._set_tab = lambda \
            _, \
            tab_id \
        : (
            aab(
                _,
                tab_id
            ) or
            tab_id == tid[0] and
            self.make_ui(_)
        )

    def make_ui(self, _):
        # math
        marg = _._height * 0.015
        # parent
        _._tab_container = parent = (
            bui.containerwidget(
                parent=_._root_widget,
                size=(
                    _._scroll_width,
                    _._scroll_height - 20
                ),
                position=(
                    (_._width - _._scroll_width) * 0.5,
                    _._scroll_y + 10
                ),
                background=False,
                selection_loops_to_parent=True
            )
        )
        # title
        bui.textwidget(
            parent=parent,
            position=(
                 (
                    _._scroll_width * 0.5 -
                    _._width * 0.2
                 ),
                 marg
            ),
            size=(
                _._width * 0.4,
                _._height * 1.1
            ),
            text=Strings.BRP_STUDIO,
            h_align='center',
            v_align='center',
            scale=3.5,
            id=f'{_.main_window_id_prefix}|title'
        )
        # tip1
        bui.textwidget(
            parent=parent,
            position=(
                 (
                    _._scroll_width * 0.5 -
                    _._width * 0.2
                 ),
                 _._height * 0.38
            ),
            size=(
                _._width * 0.4,
                _._height * 0.085
            ),
            v_align='center',
            h_align='center',
            id=f'{_.main_window_id_prefix}|tip1',
            text=Strings.ENTER_FILENAME,
            maxwidth=_._width*0.8
        )
        # input
        self.input = bui.textwidget(
            parent=parent,
            position=(
                 (
                    _._scroll_width * 0.5 -
                    _._width * 0.2
                 ),
                 _._height * 0.3
            ),
            size=(
                _._width * 0.4,
                _._height * 0.085
            ),
            v_align='center',
            editable=True,
            id=f'{_.main_window_id_prefix}|input',
            glow_type='uniform',
            allow_clear_button=False,
            text='test.brp'
        )
        # tip2
        bui.textwidget(
            parent=parent,
            position=(
                 (
                    _._scroll_width * 0.5 -
                    _._width * 0.2
                 ),
                 _._height * 0.2
            ),
            size=(
                _._width * 0.4,
                _._height * 0.085
            ),
            v_align='center',
            h_align='center',
            id=f'{_.main_window_id_prefix}|tip2',
            text=Strings.RELATIVE_TO,
            maxwidth=_._width*0.8
        )
        # tip3
        bui.textwidget(
            parent=parent,
            position=(
                 (
                    _._scroll_width * 0.5 -
                    _._width * 0.2
                 ),
                 _._height * 0.15
            ),
            size=(
                _._width * 0.4,
                _._height * 0.085
            ),
            v_align='center',
            h_align='center',
            id=f'{_.main_window_id_prefix}|tip3',
            text=bui.get_replays_dir(),
            color=Color.ALERT,
            maxwidth=_._width*0.8
        )
        # next btn
        bui.buttonwidget(
            parent=parent,
            position=(
                (
                    _._scroll_width * 0.5 -
                    _._width * 0.1
                ),
                marg
            ),
            size=(
                _._width * 0.2,
                _._height * 0.085
            ),
            text_scale=1.5,
            label=Strings.NEXT,
            color=Color.WATCH_BUTTON,
            textcolor=Color.WATCH_BUTTON_TEXT,
            id=f'{_.main_window_id_prefix}|next',
            enable_sound=False,
            on_activate_call=self.on_next
        )

    def on_next(self):
        bui.getsound('deek').play()
        if (
            reason := (
                Strings.ENTER_SOMETHING
                if not (
                    t := bui.textwidget(
                        query=self.input
                    )
                ) else Strings.FILE_DOES_NOT_EXIST
                if not exists(
                    p := join(
                        bui.get_replays_dir(),
                        t
                    )
                ) else Strings.FILE_IS_NOT_A_REPLAY
                if not (
                    p.lower().endswith('.brp')
                ) else (
                    None
                )
            )
        ):
            bui.getsound('block').play()
            bui.screenmessage(
                reason,
                color=Color.ALERT
            )
            return
        Studio.INSTANCE = Studio(p)
