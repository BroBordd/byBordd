# Copyright 2025 - Solely by BrotherBoard
# Feedback is appreciated - Telegram >> @GalaxyA14user

"""
Chatools v1.0 - Simple chat window tools

Kind of deprecated. Chatools gives you some
cool partywindow features. I don't recall much
"""

from babase import Plugin as P
import bauiv1lib.party
from re import match, sub
from babase import charstr, SpecialChar
from bascenev1 import (apptimer as tick,
                       Call,
                       get_chat_messages as gcm,
                       get_game_roster as GGR)
from bauiv1 import (screenmessage as push,
                    set_party_icon_always_visible as spv,
                    clipboard_set_text as COPY,
                    buttonwidget as bw,
                    containerwidget as cw,
                    textwidget as tw,
                    get_special_widget as gsw,
                    app as APP,
                    checkboxwidget as cb)

"""Filter JSON"""
def pick(dict, name, what='name_full', root=False):
    name = nuke(name)
    for e in dict:
        if not e.get('players'):
            if name == nuke(e['display_string']) and root:
                return e[what]
        for p in e.get('players', []):
            if name == nuke(p['name'])\
            or name == nuke(p['name_full']):
                if e.get(what, 0) and root: return e[what]
                return p[what]
    return None

"""Full Name Extractor"""
def full(n): return pick(GGR(), n) or n

"""Part Name Extractor"""
def part(n): return n if len(n) <= 10 else f"{n[:10]}..."

"""Get Overlay Stack"""
def gos(): return gsw('overlay_stack')

"""Kill A Container"""
def kill(w,t='out_right'): cw(w, transition=t)

"""Nuke Icons"""
def nuke(t):
    for i in [charstr(i) for i in SpecialChar]:
        t = t.replace(i,"",1)
    return t

"""Config Control"""
def var(c, v=None):
    cfg = APP.config
    id = 'ct_'
    if v is None:
        try: return cfg[id+c]
        except: return 0
    else:
        cfg[id+c] = v
        cfg.commit()

"""ChaTools - Useful Chat Tools"""
class CTPW(bauiv1lib.party.PartyWindow):
    """Our Gate"""
    def __init__(s,*a,**kw):
        super().__init__(*a,**kw)
        s.cola = (0.13,0.13,0.13)
        s.TB = bw(parent=s._root_widget,
               size=(90,35),
               scale=0.8,
               color=s.cola,
               label="Tools",
               position=(s._width - 425, s._height - 45),
               on_activate_call=s.main)

    """Filter Before Adding"""
    def _add_msg(s,m,fresh=True):
        super()._add_msg(m)
        if fresh: s.fresh()

    """The Lovely Window"""
    def main(s):
        SZ = (400,250)
        s.CW = cw(parent=gos(),
                  transition='in_right',
                  size=SZ,
                  stack_offset=(SZ[0],0),
                  color=s.cola)
        s.BB = bw(parent=s.CW,
                  label='back',
                  color=s.cola,
                  scale=1.2,
                  position=(SZ[0]*0.06,SZ[1]*0.06),
                  on_activate_call=Call(kill, s.CW))
        s.LB = tw(parent=s.CW,
                  text="ChaTools",
                  scale=1.2,
                  h_align='right',
                  position=(SZ[0]/2, SZ[1]*0.8))
        cw(s.CW, cancel_button=s.BB)
        cb_scale=1.3
        cb(parent=s.CW,
           position=(SZ[0]*0.06,SZ[1]*0.6),
           text="Show full names",
           value=var('FULL'),
           scale=cb_scale,
           on_value_change_call=Call(s.check, 'FULL'),
           color=s.cola)
        s.IDCB = cb(parent=s.CW,
           position=(SZ[0]*0.06,SZ[1]*0.45),
           text="Show client IDs",
           value=var('ID'),
           scale=cb_scale,
           on_value_change_call=Call(s.check, 'ID'),
           color=s.cola)
        cb(parent=s.CW,
           position=(SZ[0]*0.06,SZ[1]*0.3),
           text="Show icons",
           value=var('ICON'),
           scale=cb_scale,
           on_value_change_call=Call(s.check, 'ICON'),
           color=s.cola)

    """Checkbox Manager"""
    def check(s,t,u):
        if not GGR() and t == 'ID' and u:
            push("Join a public party for client IDs",
                 color=(1,1,0))
        var(t,u)
        s.fresh()

    """Apply Changes"""
    def fresh(s):
        haxx = s._chat_texts_haxx
        old = gcm()
        for i in range(len(haxx)): tw(haxx[i], text=old[i])
        for w in haxx:
            t = tw(query=w)
            n, m = t.split(': ',1)
            id = pick(GGR(),n,'client_id',True)
            if not id and '] ' in n:
                n2 = n.split('] ',1)[1]
                id = pick(GGR(),n2,'client_id',True)
                if id: n = n2
            h = f"[{id}] " if var('ID') and id is not None\
                else "[?] " if var('ID') else ''
            n = full(n) if var('FULL') else part(n)
            n = n if var('ICON') else nuke(n)
            t = f"{h}{n}: {m}"
            tw(w, text=t)

# ba_meta require api 8
# ba_meta export plugin
class byBordd(P):
    bauiv1lib.party.PartyWindow = CTPW
    tick(0.1, Call(spv, True))
