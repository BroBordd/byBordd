# Copyright 2025 - Solely by BrotherBoard - Feel free to utilize/modify this for personal use
# Feedback is appreciated - Telegram >> @BroBordd

"""
TopMsg v1.0 - Chat on top right

When chat is muted, show messages top right
in the same place as kill logs. Blocks spam
aswell. Combine with APW to see chat when muted.
"""

from babase import app, Plugin as P
from bascenev1 import (
    get_chat_messages as gcm,
    broadcastmessage as b,
    apptimer as z
)

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(P):
    def __init__(s):s.l='';z(5,s.ear)
    def ear(s):
        a = gcm()
        z(0.1,s.ear)
        if not (a and s.l != a[-1]): return
        b(a[-1],top=True) if app.config.resolve('Chat Muted') else None
        s.l = a[-1]
