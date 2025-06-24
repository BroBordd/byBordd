# Feel free to kang - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
DumTab v1.0 - Dummy dev console tab example

Simple demo to show how a custom dev console tab is added.
See code to know more.
"""

from typing import override
from babase import Plugin, app
from babase._devconsole import (
    DevConsoleTabEntry as ENT,
    DevConsoleTab as TAB
)

class DumTab(TAB):
    @override
    def refresh(s):
        s.button(
            'Button example',
            pos=(-100,5),
            size=(200,50)
        )
        s.text(
            'Text example',
            pos=(250,15),
            v_align='bottom'
        )

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(s):
        I = app.devconsole
        E = ENT('DumTab',DumTab)
        I.tabs.append(E)
        I._tab_instances['DumTab'] = E.factory()
