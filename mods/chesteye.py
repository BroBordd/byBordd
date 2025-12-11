# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
ChestEye v1.0 - Auto claim/open chests

Deprecated. Use Unlocker plugin.
"""

from babase import Plugin
from bauiv1 import (
    apptimer as teck,
    CallPartial,
    app
)
from bacommon.bs import (
    ClientUIActionMessage as UM,
    InboxRequestMessage as RM,
    ChestActionMessage as CM,
    ClientUIAction as CU
)
from efro.error import CommunicationError as CE
from bauiv1lib.inbox import _EntryDisplay as ED

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    R = lambda *a,**k:0
    def __init__(s,i=20):
        if not i: return
        p = app.plus
        try:
            with p.accounts.primary:
                p.cloud.send_message_cb(
                    RM(),
                    on_response=CallPartial(s.eye,i)
                )
        except:
            return
    def eye(s,i,r):
        if isinstance(r,CE): teck(1,CallPartial(s.__init__,i-1))
        else: s.claim(r)
    def claim(s,r):
        p = app.plus
        f = p.cloud.send_message_cb
        with p.accounts.primary:
            for i,w in enumerate(r.wrappers):
                f(
                    UM(w.id,CU.BUTTON_PRESS_POSITIVE),
                    on_response=s.R
                )
            [f(
                CM(
                    chest_id=str(_),
                    action=CM.Action.UNLOCK,
                    token_payment=0,
                ),
                on_response=s.R
            ) for _ in range(4)]
