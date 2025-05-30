# Copyright 2025 - Solely by BrotherBoard
# Feedback is appreciated - Telegram >> @GalaxyA14user

"""
Kill v1.0 - End bs life

Adds a button to pause menu and mainmenu iirc
it kills the game. Deprecated.
"""

import babase as ba
import bauiv1 as bui
import bauiv1lib.mainmenu as mm
import bascenev1 as bs

class Kill(mm.MainMenuWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bui.buttonwidget(
            parent=self._root_widget,
            size=(100, 50),
            scale = 0.5,
            label='KILL',
            button_type='square',
            position=(-180, -128),
            on_activate_call=bs.Call(ba.quit, quit_type=ba.QuitType.HARD)
        )
# ba_meta require api 8
# ba_meta export plugin
class byBordd(ba.Plugin):
    def __init__(self):
        mm.MainMenuWindow = Kill
