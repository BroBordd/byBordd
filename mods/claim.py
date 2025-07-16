# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Claim v1.0 - Auto gift claimer

Experimental. Silently claims any pending gifs on startup.
Read code to know more.
"""

from babase import Plugin
from bauiv1 import (
    apptimer as teck,
    Call,
    app
)
from bacommon.bs import (
    ClientUIActionMessage as CM,
    InboxRequestMessage as RM,
    ClientUIAction as CU
)
from efro.error import CommunicationError as CE
from bauiv1lib.inbox import _EntryDisplay as ED

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(s,i=5):
        if not i: return
        p = app.plus
        with p.accounts.primary:
            p.cloud.send_message_cb(
                RM(),
                on_response=Call(s.eye,i)
            )
    def eye(s,i,r):
        if isinstance(r,CE): teck(1,Call(s.__init__,i-1))
        else: s.claim(r)
    def claim(s,r):
        p = app.plus
        with p.accounts.primary:
            for i,w in enumerate(r.wrappers):
                p.cloud.send_message_cb(
                    CM(w.id,CU.BUTTON_PRESS_POSITIVE),
                    on_response=lambda *a,**k:0
                )
