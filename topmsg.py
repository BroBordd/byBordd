from babase import app, Plugin as P
from bascenev1 import (
    get_chat_messages as gcm,
    broadcastmessage as b,
    apptimer as z
)

# ba_meta require api 9
# ba_meta export plugin
class byBordd(P):
    def __init__(s):s.l='';z(5,s.ear)
    def ear(s):
        a = gcm()
        z(0.1,s.ear)
        if not (a and s.l != a[-1]): return
        b(a[-1],top=True) if app.config.resolve('Chat Muted') else None
        s.l = a[-1]
