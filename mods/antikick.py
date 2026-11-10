# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Discord >> @BrotherBoard

"""
Antikick v1.0 - No You Won't

Experimental
"""

from bauiv1 import app, apptimer, screenmessage, Plugin
from bacommon.langstr import LangStrSpecResource, LangStrSpecValue
from bascenev1 import (
    get_game_roster,
    connect_to_party,
    disconnect_from_host,
    get_party_member_names,
    get_connection_to_host_info_2
)

def getme():
    mine = app.plus.get_v1_account_display_string()
    for e in get_game_roster():
        if e['display_string'] == mine:
            players = e['players']
            if len(players) == 1:
                return players[0]['name']
            return get_party_member_names().get(e['client_id'])

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(self):
        cls = type(app.classic.host_ui)
        orig = cls._show

        def _show(self, state, source):
            if isinstance(n, LangStrSpecResource) and n.name.endswith(
                'kick_vote_started'
            ):
                if (who := state.notice.subs.get('name', '')) == getme():
                    screenmessage(
                        "Someone's trying to kick you.\nRejoining server..."
                    )
                    info = get_connection_to_host_info_2()
                    address, port = info.address, info.port
                    disconnect_from_host()
                    apptimer(
                        0.1, lambda: connect_to_party(
                            address, port=port, print_progress=False
                        )
                    )
            orig(self, state, source)

        cls._show = _show
