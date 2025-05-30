from babase import Plugin as P
from bauiv1lib.mainmenu import MainMenuWindow as m
from bascenev1 import apptimer as teck
from bauiv1 import app
c = app.classic
u = app.ui_v1
o = m._refresh_in_game

def f():
    # do something on pause
    from bauiv1 import screenmessage as push
    push ('Hello World!')
    return True

def resume(s) -> None:
    assert c is not None
    c.resume()
    u.clear_main_menu_window()
    [z() for z in u.main_menu_resume_callbacks]
    del u.main_menu_resume_callbacks[:]

def on_pause(*a,**kw):
    r = o(*a, **kw)
    if not f(): teck(0.0001, lambda: resume(a[0]))
    return r

# ba_meta require api 8
# ba_meta export plugin
class byBordd(P):
    def __init__(s):
        m._refresh_in_game = on_pause
