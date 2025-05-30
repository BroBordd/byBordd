import bauiv1lib.party
from babase import Plugin as P
from bascenev1 import screenmessage as p
from bauiv1 import clipboard_set_text as c, textwidget as tw, getsound as gs, buttonwidget as bw

class CopyPW(bauiv1lib.party.PartyWindow):
    def __init__(s, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bw(parent=s._root_widget,
           size=(20, 20),
           label='c',
           scale=0.8,
           button_type='square',
           position=(s._width - 70, 75),
           on_activate_call=s.cat)
    def cat(s):t=tw(query=s._text_field);c(t);p(f"Copied '{t}'",color=(0,1,0));gs("ding").play()

# ba_meta require api 8
# ba_meta export plugin
class byBordd(P):
    def __init__(s): bauiv1lib.party.PartyWindow = CopyPW
