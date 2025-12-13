# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Unlocker v1.0 - Chest unlocker

Autorun on startup:
- Calim pending chests from inbox
- Skip wait time for each chest
- Unlock all pending chests in slots

Experimental.
"""

import bauiv1 as bui
import bacommon as bc
from babase import Plugin

plus = bui.app.plus

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(s):
        s.patch()
        s.wait_timer = bui.AppTimer(
            0.113, s.wait, repeat=True
        )
    def patch(s):
        from baclassic import ClassicAppMode as c
        f = '_on_classic_account_data_change'
        o = getattr(c,f)
        n = lambda z,v: s.check(v) or o(z,v)
        setattr(c,f,n)
    def check(s,v):
        if v.inbox_contains_prize:
            s.fetch()
    def wait(s):
        if plus.cloud.connected:
            s.wait_timer = None
            s.fetch()
    def fetch(s):
        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bc.bs.InboxRequestMessage(),
                on_response=s.claim
            )
    def claim(s,r):
        cd = bc.clouddialog
        with plus.accounts.primary:
            for w in r.wrappers:
                if w.ui.button_label_positive == cd.basic.ButtonLabel.CLAIM:
                    plus.cloud.send_message_cb(
                        cd.ActionMessage(
                            w.id,
                            cd.Action.BUTTON_PRESS_POSITIVE
                         ),
                         on_response=lambda r:None
                    )
        s.scan()
    def scan(s):
        for i in range(4):
            s.query(i)
    def query(s,i,r=0):
        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bc.bs.ChestInfoMessage(
                    chest_id=str(i)
                ),
                on_response=bui.CallPartial(s.parse,i)
            )
    def parse(s,i,r):
        c = r.chest
        if c:
            if c.unlock_tokens != 0: s.skip(i)
            else: s.unlock(i)
    def skip(s,i):
        cl = bc.cloud
        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                cl.ChestActionMessage(
                    chest_id=str(i),
                    action=cl.ChestActionMessage.Action.AD,
                    token_payment=0
                ),
                on_response=bui.CallPartial(s.query,i)
            )
    def unlock(s,i):
        cl = bc.cloud
        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                cl.ChestActionMessage(
                    chest_id=str(i),
                    action=cl.ChestActionMessage.Action.UNLOCK,
                    token_payment=0
                ),
                on_response=lambda r:None
            )
