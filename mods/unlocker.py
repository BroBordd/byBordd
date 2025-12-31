# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Unlocker v1.0 - Chest unlocker

Autorun on startup:
- Calim pending chests from inbox
- Unlock all pending chests in slots
- Handle notifications

Experimental.
"""

import babase as ba
import bacommon as bc

LAMENT = True
PLUS = ba.app.plus

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(ba.Plugin):
    @staticmethod
    def lament(f):
        return LAMENT and (
            lambda s,*a: (
                f(s,*a) or print(
                    '[Unlocker]',
                    f.__name__,
                    *a
                )
            )
        ) or f
    def __init__(s):
        s.patch()
        s.wait_timer = ba.AppTimer(
            0.113, s.wait, repeat=True
        )
    def patch(s):
        from baclassic import ClassicAppMode as c
        f = '_on_classic_account_data_change'
        o = getattr(c,f)
        n = lambda z,v: (
            v.inbox_contains_prize
            and s.fetch() or o(z,v)
        )
        setattr(c,f,n)
    def wait(s):
        if PLUS.cloud.connected:
            s.wait_timer = None
            s.fetch()
    @lament
    def fetch(s):
        with PLUS.accounts.primary:
            PLUS.cloud.send_message_cb(
                bc.bs.InboxRequestMessage(),
                on_response=s.claim
            )
    def claim(s,r):
        cd = bc.clouddialog
        with PLUS.accounts.primary:
            for w in r.wrappers:
                if w.ui.button_label_positive == cd.basic.ButtonLabel.CLAIM:
                    PLUS.cloud.send_message_cb(
                        cd.ActionMessage(
                            w.id,
                            cd.Action.BUTTON_PRESS_POSITIVE
                         ),
                         on_response=lambda r:None
                    )
        ba.apptimer(3,lambda:[
            s.query(i) for i in range(4)
        ])
    @lament
    def unlock(s,i):
        cl = bc.cloud
        with PLUS.accounts.primary:
            PLUS.cloud.send_message_cb(
                cl.ChestActionMessage(
                    chest_id=str(i),
                    action=cl.ChestActionMessage.Action.UNLOCK,
                    token_payment=0
                ),
                on_response=lambda r:None
            )
    def query(s,i,r=0):
        with PLUS.accounts.primary:
            PLUS.cloud.send_message_cb(
                bc.bs.ChestInfoMessage(
                    chest_id=str(i)
                ),
                on_response=lambda i:(
                    getattr(r,'chest',None)
                    and s.unlock(i)
                )
            )
