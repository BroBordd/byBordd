# Copyright 2025 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Calculator v1.5 - Math operations in the scene

Deploys buttons on the ground, controllong a simple
LCD which shows numbers. Send /calc to chat for usage.
"""

from bascenev1 import (
    get_foreground_host_activity as ga,
    chatmessage as cm,
    gettexture as gt,
    timer as tick,
    getcollision,
    getmesh,
    newnode,
    Player,
    Actor,
    Call
)
from bascenev1lib.actor.powerupbox import PowerupBoxFactory
from bascenev1lib.gameutils import SharedObjects
from babase import Plugin as P, InputType as IT
from bascenev1 import broadcastmessage as push
from bauiv1 import textwidget as tw
from bauiv1lib import party
from typing import Any
from math import dist

"""3D In-Game Calculator"""
class CALC:
    def __init__(s, position):
        p = position
        s.keys = s.pend = {}
        s.lcd = None
        s.input = ''
        s.active = False
        s.tdoze = 10
        s.doze_n = 0
        s.eta = 0
        s.off = -10
        s.loff = []
        s.last = None
        s.snail = []
        s.can_snail = True
        for i in range(3): s.keys[KEY((i+p[0], p[1], 3+p[2]),i+1,s).node]=0
        for i in range(3): s.keys[KEY((i+p[0], p[1],1.5+p[2]),i+4,s).node]=0
        for i in range(3): s.keys[KEY((i+p[0], p[1], p[2]),i+7,s).node] = 0
        s.keys[KEY((0+p[0], p[1], 4.5+p[2]),0,s).node]=0
        s.keys[KEY((1+p[0], p[1], 4.5+p[2]),'.',s).node]=0
        s.keys[KEY((3+p[0], p[1], 4.5+p[2]),"nuke",s).node]=0
        s.keys[KEY((4+p[0], p[1], 4.5+p[2]),"=",s).node]=0
        s.keys[KEY((3+p[0], p[1], 3+p[2]),"+",s).node]=0
        s.keys[KEY((4+p[0], p[1], 1.5+p[2]),"/",s).node]=0
        s.keys[KEY((4+p[0], p[1], 3+p[2]),"-",s).node]=0
        s.keys[KEY((3+p[0], p[1], 1.5+p[2]),"*",s).node]=0
        yes('Calculator!', i='menuButton')

    """Start controling calculator instance"""
    def control(s):
        for p in ga().players:
            p.assigninput(IT.BOMB_PRESS, Call(s.press, p.node))
        s.eta = s.tdoze
        s.rdoze()
        if s.active: return
        s.active = True
        s.wake()
        s.eye()
        s.blink()

    """Key signal reciever"""
    def key(s, k):
        with ga().context: s.lcd.strip()
        if k == 'nuke':
            try: loff = s.loff[-1]
            except IndexError:
                s.clear()
                yes("Can't delete more!", (1,1,0), i='textClearButton')
                return
            s.off -= loff
            s.loff.pop()
            s.input = s.input[:-1]
            with ga().context: s.lcd.simue(range(s.off, s.off + loff)[::-1])
            s.lcd.strip()
            return
        if k == '=': s.solve(); return
        try: s.lcd.simu(ART(s).get(k), (0,0,0))
        except TypeError: return
        s.input += str(k)

    """eye on idle time"""
    def eye(s):
        if s.can_snail: s.eta -= 1
        else: s.eta = s.tdoze
        if s.eta > 0:
            with ga().context: tick(s.tdoze/10, Call(s.eye))
        else:
            s.active = False

    """Doze countdown snail"""
    def sdoze(s):
        i = s.doze_n
        if i >= (s.tdoze): return
        if s.can_snail:
            s.snail[i].color = (0,1,1)
            s.doze_n += 1
        else: s.doze_n = 0
        tick(s.tdoze/10, Call(s.sdoze))

    """Reset doze"""
    def rdoze(s, i=0):
       for p in s.snail:
           p.color = (1,1,1,1)
       s.doze_n = 0

    """Dim all pixels on doze"""
    def doze(s):
        yes('doze', i='ouyaUButton', c=(0,1,1))
        for p in s.lcd.pixels:
            c = p.color
            p.color = (c[0],c[1],c[2],0.3)
        for p in s.snail:
            p.color = (0,1,1,0.3)

    """Wake up when not idle"""
    def wake(s):
        for p in s.lcd.pixels:
            c = p.color
            if p not in s.snail: p.color = (c[0],c[1],c[2],1)
        with ga().context:
            s.rdoze(); s.sdoze()

    """Connect LCD to calculator"""
    def connect_lcd(s, lcd):
        s.lcd = lcd
        s.add_snail()
        s.active = True
        s.eta = s.tdoze
        s.wake()
        with ga().context: s.blink()
        s.eye()

    """Add a snail to LCD"""
    def add_snail(s):
        p = s.lcd.position
        w = s.lcd.width
        sp = s.lcd.pixel_spacing
        for j in range(10): s.lcd.add((p[0]+(sp*w), p[1]+(j*sp), p[2]),s.snail,(1,0,0))

    """Clear the connected LCD"""
    def clear(s):
        s.lcd.clear()
        s.off = -10
        s.loff.clear()

    """Add a blinker to connected LCD"""
    def blink(s, c=(1,1,1), down=True):
        n = s.off
        a = list(s.lcd.pixels)
        if c[1] <= 0: down = False
        if c[1] >= 1: down = True
        z = -0.1 if down else 0.1
        c = (c[0], c[1]+z, c[2])
        if not s.active: c = (1,1,1)
        try:
            for i in range(10):
                a[n+i+10].color = c
                s.lcd.pixels[a[n+i]] = c
                a[n+i+20].color = c
                s.lcd.pixels[a[n+i+10]] = c
        except IndexError: pass
        except: push('Some of Calculator LCD pixels went out of bounds,\nreduce pixels or pick another position.', color=(1,0,0)); s.delete(); return
        if s.active: tick(0.01, Call(s.blink, c, down))
        else: tick(0.1, s.doze)

    """Handle bomb press"""
    def press(s, p):
        n = p
        try: dux = (s.pend[n])
        except KeyError: return
        s.key(dux)
        try:
            with ga().context: s.tink(list(s.keys)[dux-1])
        except: pass

    """Small blink after each press"""
    def tink(s, n, b=False):
        n.color_texture = gt(f"ouya{'Y' if b else 'O'}Button")
        if not b: tick(0.1, Call(s.tink, n, True))

    """Solve the input"""
    def solve(s):
        try: out = eval(s.input); float(out)
        except Exception as E:
            push(str(E), color=(1,0,0))
            with ga().context: s.lcd.flash()
        else:
            s.clear()
            s.input = ""
            for n in list(str(out)):
                try: n = int(n)
                except: pass
                s.key(n)
            with ga().context: s.lcd.flash((0,1,0))

    """Delete the calculator"""
    def delete(s):
        s.lcd.delete()
        for k in s.keys: s.delete()

"""Simple node-based LCD"""
class LCD:
    def __init__(s, position=(0,3,0), width=30, root=None, pixel_scale=None, pixel_spacing=0.2):
        s.pixels = {}
        s.pixel_spacing = sp = pixel_spacing
        s.root = root
        s.width = width
        s.pixel_scale = pixel_scale
        p = s.position = position
        for i in range(width):
            for j in range(10): s.add((p[0]+i*sp, p[1]+j*sp, p[2]),s.pixels)

    """Create a pixel"""
    def add(s, p, add_to, c=(1,1,1)):
        pixel = PIXEL(p, s.pixel_scale).node
        if isinstance(add_to, dict): add_to[pixel] = c
        elif isinstance(add_to, list): add_to.append(pixel)
        else: raise TypeError(f"unsupported add_to type '{type(add_to).__name__}'")

    """Color pixels simultaneously"""
    def simu(s, l, c, i=0):
        for j in range(10):
            try: p = l[i+j]
            except IndexError: return
            s.pixels[p] = c
            p.color = c
        if i >= (len(l)): return
        tick(0.015, Call(s.simu,l,c,i+10))

    """Erase pixels simultaneously"""
    def simue(s, l, i=0):
        a = list(s.pixels)
        if i >= (len(l)): return
        for j in range(10): a[l[i+j]].color = (1,1,1)
        tick(0.015, Call(s.simue,l,i+10))

    """Fill white pixels"""
    def fill(s, c):
        for p in s.pixels:
            l = p.color
            if l[0] != 0 or l[1] != 0 or l[2] != 0: p.color = c

    """Flash the LCD"""
    def flash(s, c=(1,0,0)):
        s.fill(c)
        tick(1, Call(s.grad, c))

    """Gradually cool the LCD"""
    def grad(s, c):
        s.fill(c)
        if c[0] >= 1 and c[1] >= 1 and c[2] >= 1: return
        c = list(c)
        for i in range(len(c)):
            if c[i] < 1: c[i] += 0.1
        tick(0.05, Call(s.grad, (c[0],c[1],c[2])))

    """Clear the LCD"""
    def clear(s):
        for p in s.pixels:
            s.pixels[p] = (1,1,1)
            p.color = (1,1,1)

    """Strip non-black pixels"""
    def strip(s):
        for p in s.pixels:
            l = p.color
            if l[0] == 0 and l[1] == 0 and l[2] == 0: continue
            s.pixels[p] = (1,1,1)
            p.color = (1,1,1)

    """Delete the LCD"""
    def delete(s):
        for p in s.pixels: p.delete(True)

# Define signal codes
# Simple draw functions
def R(*i): return [j for j in range(*i)]
def S(*i): k=int(str(i[0])[-1]); return [j for j in range(*i) if int(str(j)[-1]) in [k,k+1]]
def T(*i):
    s = 0; a = []
    for j in i:
        if isinstance(j, int): s = 1; continue
        b = S(*j) if s else R(*j)
        for k in b: a.append(k)
    return a
sig = {
    0: [*R(20),*S(20,40),*S(28,40),*R(40,60),6],
    1: [*R(20),2],
    2: [*R(6),*S(8,50),*R(10,16),*S(20,60),*S(24,40),*R(44,50),*R(54,60),6],
    3: [*S(40),*S(4,40),*S(8,40),*R(40,60),6],
    4: [*R(4,10),*R(14,20),*S(24,40),*R(40,60),6],
    5: [*S(40),*R(40,46),*R(50,56),*S(24,40),*R(4,10),*R(14,20),*S(28,60),6],
    6: [*R(20),*S(20,40),*S(24,40),*S(28,60),*R(40,46),*R(50,56),6],
    7: [*R(40,60),*S(28,40),*S(8,20),6],
    8: [*R(20),*S(20,40),*S(24,40),*S(28,40),*R(40,60),6],
    9: [*S(40),*R(4,10),*R(14,20),*S(24,40),*S(28,40),*R(40,60),6],
    '+': [*S(4,20),*R(22,28),*R(32,38),*S(44,60),6],
    '-': [*S(4,60),6],
    '/': [*S(2,20),*S(24,40),*S(46,60),6],
    '*': [*S(2,20),*S(6,20),*S(24,40),*S(42,60),*S(46,60),6],
    '=': [-1],
    '.': [*S(20),2]
}

for s in sig:
    i = sig[s]
    sig[s] = sorted(i[:-1])
    sig[s].append(i[-1])
del i

"""Convert key signal into pixel art"""
class ART:
    def __init__(s, root):
        s.root = root

    """Convert signal codes"""
    def get(s, k):
        s.a = list(s.root.lcd.pixels)
        s.b = []
        s.k = k
        s.o = 1
        signal = sig[k]
        if not s.f(*signal[:-1]): return
        off = (signal[-1]+1)*10
        s.root.off += off
        s.root.loff.append(off)
        return s.b

    """Validate input-ability"""
    def f(s, *ar, r=0):
        for i in ar:
            try: t = s.a[i+s.root.off+10]
            except IndexError: yes('LCD is full', (1,0,0), i='ouyaAButton'); return 0
            else:
                if s.o: yes(s.k, i='ouyaOButton'); s.o = 0
            try: s.b.remove(t) if r else s.b.append(t)
            except: continue
        return 1

"""Simple pixel, part of class LCD"""
class PIXEL(Actor):
    def __init__(s, position, scale):
        with ga().context:
            super().__init__()
            shared = SharedObjects.get()
            factory = PowerupBoxFactory.get()
            s.node = newnode(
                'text',
                delegate=s,
                attrs={
                    'text': '■',
                    'position': position,
                    'in_world': True,
                    'color': (1,1,1),
                    'flatness': 1.0,
                    'scale': scale
                }
            )

"""Simple touch-sensitive key, part of class KB"""
class KEY(Actor):
    def __init__(s, position, k, root):
        with ga().context:
            super().__init__()
            s.k = k
            s.held= False
            s.root = root
            tex = 'crossOut' if k == 'nuke'\
                   else 'eggTex3' if k == ' '\
                   else 'egg1' if k == '-'\
                   else 'egg2' if k == '+'\
                   else 'egg3' if k == '*'\
                   else 'egg4' if k == '/'\
                   else 'circle' if k == '.'\
                   else 'ticketsMore' if k == '='\
                   else 'ouyaAButton'
            tex = gt(tex)
            shared = SharedObjects.get()
            factory = PowerupBoxFactory.get()
            s.node = newnode(
                'prop',
                delegate=s,
                attrs={
                    'body': 'landMine',
                    'position': position,
                    'mesh': getmesh('landMine'),
                    'light_mesh': factory.mesh_simple,
                    'shadow_size': 0.5,
                    'color_texture': tex,
                    'reflection_scale': [1.0],
                    'materials': (factory.powerup_material, shared.object_material),
                    'gravity_scale': 5,
                    'is_area_of_interest': True
                })
            s.node.getdelegate(object).handlemessage = s.handlemessage
    def handlemessage(s, msg: Any) -> Any:
        if '_Touched' in str(msg):
            s.root.control()
            s.root.eta = s.root.tdoze
            s.root.rdoze()
            s.node2 = getcollision().opposingnode.getdelegate(object).getplayer(Player, True).node
            if s.k != s.root.last:
                yes(s.k, (1,1,0), i='ouyaYButton'); s.root.last = s.k
                s.root.control()
            for key in s.root.keys:
                if s.root.keys[key] == s.node2: s.root.keys[key] = 0
            s.root.keys[s.node] = s.node2; s.hold(True)
            s.spam()
        super().handlemessage(msg)
    def spam(s):
        p1 = s.node.position
        p2 = s.node2.position
        if dist(p1,p2) < 0.7 and s.root.keys[s.node]: tick(0.1, s.spam)
        else: s.root.keys[s.node] = 0; s.hold(False)
    def hold(s, b):
        if b: s.root.pend[s.node2] = s.k
        else: s.root.pend.pop(s.node2, None)
        s.held = b
        s.root.can_snail = not b
        tex = ('achievementCrossHair' if b else 'crossOut') if s.k == 'nuke'\
              else ('eggTex3' if b else 'egg1') if s.k == '-'\
              else ('bombColorIce' if b else 'egg2') if s.k == '+'\
              else ('eggTex1' if b else 'egg3') if s.k == '*'\
              else ('coin' if b else 'egg4') if s.k == '/'\
              else ('eggTex3' if b else 'eggTex2') if s.k == ' '\
              else ('ticketRolls' if b else 'ticketsMore') if s.k == '='\
              else ('circleOutlineNoAlpha' if b else 'circle') if s.k == '.'\
              else f"ouya{'Y' if b else 'A'}Button"
        s.node.color_texture = gt(tex)

# Patch
class PWIDK(party.PartyWindow):
    def __init__(s,*a,**k): super().__init__(*a,**k)
    def _send_chat_message(self) -> None:
        if ga():
            s = tw(query=self._text_field)
            if s.startswith("/calc "):
                try:
                    pos = tuple(eval(' ('+s.split('(', 1)[1].split(')')[0]+')'))
                    try: wid = int(s.split(') ')[1].split(' ')[0])
                    except: wid = 60
                    try: pxs = float(s.split(') ')[1].split(' ')[1])
                    except: pxs = 0.0075
                    try: pxm = float(s.split(') ')[1].split(' ')[2])
                    except: pxm = 0.1
                    cm(f"Calculator! position={pos}, width={wid}, pixel_scale={pxs}, pixel_spacing={pxm}")
                except Exception as E: bruh(E); return
                tw(edit=self._text_field, text='')
                start_calculator(pos, wid, pxs, pxm)
            elif s == "/calc": bruh('missing 1 required argument: position'); return
            else: super()._send_chat_message()
            return
        super()._send_chat_message()

# Demo - start calculator
def start_calculator(p, wid, pxs, pxm):
    if p[1] <= 0.099: push('warning: Y position is too small,\nbuttons might be swallowed by the ground, recommended Y=0.1 for good.')
    calc = CALC(p)
    calc.connect_lcd(
        LCD(
            position=(p[0],p[1]+3,p[2]),
            width=wid,
            root=calc,
            pixel_scale=pxs,
            pixel_spacing=pxm
        )
    )

# Simple top message
stty_yes = True
def yes(t, c=(0,1,0), top=True, i=None):
    if not stty_yes: return
    with ga().context: i = gt(i) if i else i
    push(str(t), image=i, top=top, color=c)

# Bruh that's incorrect
def bruh(e):
    cm('CALC - incorrect usage')
    cm(f'error: {e}')
    cm('usage: /calc [position] [width=60px] [pixel_scale=0.0075] [pixel_spacing=0.1]')
    cm('ex. ezy: /calc (3, 0.1, 0)')
    cm('ex. mid: /calc (-4, 0.2, 0) 100')
    cm('ex. adv: /calc (-11.2, 0.17, 0) 80 0.0075 0.1')

# brobord collide grass
# ba_meta require api 9
# ba_meta export plugin
class byBordd(P):
    def __init__(s): party.PartyWindow = PWIDK
