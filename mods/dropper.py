# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Dropper v2.0 - Drop literally everything

Two drop consoles, pick anything, rain it on anyone.
Bombs, powerups, spazzes, bots, mines, TNT and more.
Requires my Beam plugin to be installed.
"""

import logging
import random
from collections import namedtuple
from math import ceil, cos, sin, tau

import bascenev1 as bs
from babase import InputType as IT

# --- tunables ---------------------------------------------------------------
CONSOLES = [(-7, 3, 0), (2, 3, 0)]   # beam world positions (one console each)
SIZE = (450, 350)                    # console size (abstract units)
DROP_Y = 9                           # drop height
GROUND_Y = 0.1                       # height of the ground aim ring
CURSOR_SPEED = 0.45                  # cursor speed while aiming a drop (1 = normal)
COOLDOWN = 0.2                       # min seconds between drops per console
COLS, ROWS = 2, 5                    # menu grid

# --- bright palette (beam bg is black, nothing dark allowed) ----------------
CYAN = (0.4, 1.0, 1.0)
YELLOW = (1.0, 1.0, 0.5)
WHITE = (1.0, 1.0, 1.0)
FILL = (0.12, 0.22, 0.34)
SEL = (0.55, 0.38, 0.05)
EMPTY = (0.03, 0.03, 0.03)
TAB = (0.20, 0.12, 0.34)

Item = namedtuple('Item', 'cat label fn rand')

CATS = [
    ('all', 'Everything'),
    ('bombs', 'Bombs'),
    ('power', 'Powerups'),
    ('spaz', 'Spazzes'),
    ('bots', 'Bots'),
    ('chaos', 'Chaos'),
]


def bright(c):
    """Normalize a color so its strongest channel is full, then lift the rest.
    Dark blue (0,0,0.5) becomes readable (0.35,0.35,1) on a black beam."""
    c = tuple(c[:3])
    m = max(c) if c else 0
    if m < 0.05:
        return WHITE
    return tuple(0.35 + 0.65 * (v / m) for v in c)


def scatter(p, r, up=4.0):
    return (
        p[0] + random.uniform(-r, r),
        p[1] + random.uniform(0, up),
        p[2] + random.uniform(-r, r),
    )


def build_catalog(act):
    """Everything that can be dropped. Imports are lazy on purpose."""
    from bascenev1lib.actor.bomb import Bomb, Blast
    from bascenev1lib.actor.powerupbox import PowerupBox
    from bascenev1lib.actor.spaz import Spaz
    from bascenev1lib.actor.flag import Flag
    from bascenev1lib.actor import spazbot

    items = []

    def add(cat, label, fn, rand=True):
        items.append(Item(cat, label, fn, rand))

    # bombs
    bomb_fns = []
    for label, kind in [
        ('Normal Bomb', 'normal'),
        ('Ice Bomb', 'ice'),
        ('Sticky Bomb', 'sticky'),
        ('Impact Bomb', 'impact'),
        ('Land Mine', 'land_mine'),
        ('TNT', 'tnt'),
    ]:
        f = lambda p, k=kind: Bomb(bomb_type=k, position=p).autoretain()
        bomb_fns.append(f)
        add('bombs', label, f)

    # powerups
    for label, kind in [
        ('Triple Bombs', 'triple_bombs'),
        ('Ice Bombs', 'ice_bombs'),
        ('Sticky Bombs', 'sticky_bombs'),
        ('Impact Bombs', 'impact_bombs'),
        ('Mines Pack', 'land_mines'),
        ('Punch Gloves', 'punch'),
        ('Shield', 'shield'),
        ('Health Pack', 'health'),
        ('Curse', 'curse'),
    ]:
        add('power', label, lambda p, k=kind: PowerupBox(
            position=p, poweruptype=k).autoretain())

    # spazzes (standalone, no player attached)
    def spaz(char):
        def f(p):
            z = Spaz(
                color=tuple(random.random() for _ in range(3)),
                highlight=tuple(random.random() for _ in range(3)),
                character=char,
                source_player=None,
                start_invincible=False,
            )
            z.autoretain()
            z.handlemessage(bs.StandMessage(p, random.uniform(0, 360)))
        return f

    try:
        chars = sorted(bs.app.classic.spaz_appearances.keys())
    except Exception:
        chars = ['Spaz', 'Zoe', 'Kronk', 'Mel', 'Jack Morgan',
                 'Santa Claus', 'Frosty', 'Bones', 'Pixel']
    for ch in chars:
        add('spaz', ch, spaz(ch))

    # bots (need a BotSet so they actually hunt players)
    def botset():
        if act.botset is None:
            act.botset = spazbot.BotSet()
        return act.botset

    def bot(cls):
        return lambda p: botset().spawn_bot(cls, p, spawn_time=0.5)

    for label, name in [
        ('Bomber Bot', 'BomberBot'),
        ('Bomber Pro', 'BomberBotPro'),
        ('Brawler Bot', 'BrawlerBot'),
        ('Brawler Pro', 'BrawlerBotPro'),
        ('Charger Bot', 'ChargerBot'),
        ('Trigger Bot', 'TriggerBot'),
        ('Trigger Pro', 'TriggerBotPro'),
        ('Sticky Bot', 'StickyBot'),
        ('Explodey Bot', 'ExplodeyBot'),
        ('Bouncy Bot', 'BouncyBot'),
    ]:
        cls = getattr(spazbot, name, None)
        if cls:
            add('bots', label, bot(cls))

    # chaos
    add('chaos', 'Nuke', lambda p: Bomb(
        bomb_type='impact', position=p, bomb_scale=2, blast_radius=4
    ).autoretain())

    def rain(p):
        for i in range(12):
            bs.timer(i * 0.07, bs.CallPartial(
                lambda q: random.choice(bomb_fns)(q), scatter(p, 3)))
    add('chaos', 'Bomb Rain', rain)

    def mines(p):
        for i in range(8):
            a = tau * i / 8
            q = (p[0] + cos(a) * 2.5, p[1], p[2] + sin(a) * 2.5)
            bs.timer(i * 0.05, bs.CallPartial(
                lambda q: Bomb(bomb_type='land_mine', position=q).autoretain(), q))
    add('chaos', 'Mine Field', mines)

    def spazrain(p):
        for i in range(6):
            bs.timer(i * 0.15, bs.CallPartial(
                lambda q: spaz(random.choice(chars))(q), scatter(p, 3)))
    add('chaos', 'Spaz Rain', spazrain)

    add('chaos', 'Explosion', lambda p: Blast(
        position=(p[0], 1.0, p[2]), blast_radius=3.0, blast_type='normal'
    ).autoretain())
    add('chaos', 'Ice Blast', lambda p: Blast(
        position=(p[0], 1.0, p[2]), blast_radius=3.0, blast_type='ice'
    ).autoretain())
    add('chaos', 'Flag', lambda p: Flag(position=p, touchable=True).autoretain())
    add('chaos', 'Random Bomb', lambda p: random.choice(bomb_fns)(p), rand=False)
    add('chaos', 'Random Anything',
        lambda p: random.choice([i for i in items if i.rand]).fn(p), rand=False)
    return items


# brobord collide grass
# ba_meta require api 9
# ba_meta export bascenev1.GameActivity
class byBordd(bs.TeamGameActivity[bs.Player, bs.Team]):
    name = 'Dropper'
    description = "Drop literally everything on everyone."
    get_available_settings = classmethod(lambda c, _: [])
    supports_session_type = classmethod(lambda c, _: True)
    get_supported_maps = classmethod(lambda c, _: ['Football Stadium'])
    get_instance_description = lambda s: "Watch the sky"
    get_instance_description_short = lambda s: "Watch the sky"

    def __init__(s, settings):
        super().__init__(settings)
        s.default_music = bs.MusicType.GRAND_ROMP
        # custom
        s.keep = []
        s.items = []
        s.botset = None

    def on_begin(s) -> None:
        super().on_begin()
        s.items = build_catalog(s)
        for i, pos in enumerate(CONSOLES):
            s.keep += s.make_console(i, pos)

    def handlemessage(s, m):
        if isinstance(m, bs.PlayerDiedMessage):
            s.respawn_player(m.getplayer(bs.Player))

    def make_console(s, idx, pos):
        from beam import Container, Button, Beam, Text, GSW
        from bauiv1 import SpecialChar as sc

        def ch(name, fallback):
            e = getattr(sc, name, None)
            return e.value if e else fallback

        UP, DOWN = ch('UP_ARROW', '^'), ch('DOWN_ARROW', 'v')
        LEFT, RIGHT = ch('LEFT_ARROW', '<'), ch('RIGHT_ARROW', '>')

        st = {
            'item': None,
            'cat': 'all',
            'off': 0,
            'menu': False,
            't': -9.0,
        }
        st['item'] = next((i for i in s.items if i.label == 'Nuke'), s.items[0])

        # --- helpers (Text/Button positions are multiplied by their own scale,
        # so divide it back out to place things in container units) ---
        def T(parent, text, x, y, scale=1, **k):
            return Text(
                parent=parent, text=text, position=(x / scale, y / scale),
                scale=scale, **k)

        def settext(t, v):
            t.text = v
            t.line.text = v

        def setlabel(bt, label):
            bt.label = label
            w = GSW(label) if label else 0
            x = bt.size[0] * 0.85
            bt.text.scale = bt.sc if w < x else (x / w) * bt.sc

        def paint(bt, color, textcolor):
            # highlight adds 0.4 to both; keep that offset while highlighted
            k = 0.4 if bt.up else 0
            bt.color = tuple(v + k for v in color)
            bt.textcolor = tuple(v + k for v in textcolor)

        # --- map bounds / coordinate conversion ---
        x0, y0, z0, x1, y1, z1 = bs.getactivity().globalsnode.area_of_interest_bounds
        w0, h0 = SIZE
        mx, my = w0 * 0.1, h0 * 0.1
        ww, hh = w0 - mx * 2, h0 - my * 2
        dx = (x1 - x0) if abs(x1 - x0) > 1e-6 else 1.0
        dz = abs(z1 - z0) if abs(z1 - z0) > 1e-6 else 1.0

        def world_to_screen(wx, wz):
            u = (wx - x0) / dx
            v = (z1 - wz) / dz
            return (
                max(0.0, min(w0, mx + u * ww)),
                max(0.0, min(h0, my + v * hh)),
            )

        def screen_to_world(px, py):
            u = (px - mx) / ww
            v = (py - my) / hh
            return (x0 + u * dx, DROP_Y, z1 - v * dz)

        # --- drop ---
        def eye(px, py):
            if c.on[0]:  # cursor is on a button, not on the map
                return
            now = bs.time()
            if now - st['t'] < COOLDOWN:
                return
            st['t'] = now
            try:
                st['item'].fn(screen_to_world(px, py))
            except Exception:
                logging.exception('dropper: drop failed')

        # --- console ---
        c = Container(size=SIZE, pipe=eye, speed=CURSOR_SPEED)
        # beam first: it zeroes container opacity, kids made after inherit it
        b = Beam(
            position=pos,
            container=c,
            id=f'drop{idx + 1}',
            title=sc.OUYA_BUTTON_Y.value + ' Drop Console',
            message=sc.LEFT_BUTTON.value + ' Punch this for power.'
        )
        T(c, 'Drop Console', 150, 328, 0.9, h_align='center', v_align='center',
          color=CYAN)
        Button(
            parent=c,
            position=(15, 280),
            size=(57, 35),
            label=sc.BACK.value,
            color=(0.6, 0.2, 0.1),
            textcolor=(1.0, 0.65, 0.5),
            call=b.back
        )
        sel = Button(
            parent=c,
            position=(250, 280),
            size=(190, 35),
            label='',
            color=(0.10, 0.30, 0.45),
            textcolor=WHITE,
            call=lambda: to_menu(list(c.captives))
        )
        T(c, 'Punch to drop where the cursor is', 225, 50, 0.6,
          h_align='center', v_align='center', color=WHITE)

        def sel_label():
            setlabel(sel, st['item'].label + ' ' + DOWN)

        # --- full-screen menu (same size and spot as the console) ---
        m = Container(size=SIZE, opacity=0)
        cat_t = T(m, '', 225, 328, 0.9, h_align='center', v_align='center',
                  color=CYAN)
        info = T(m, '', 225, 50, 0.6, h_align='center', v_align='center',
                 color=YELLOW)
        pool = []
        for r in range(ROWS):
            for q in range(COLS):
                pool.append(Button(
                    parent=m,
                    position=(15 + 177 * q, 232 - 48 * r),
                    size=(171, 35),
                    label='',
                    color=FILL,
                    textcolor=WHITE,
                ))
        BACKC, BACKT = (0.6, 0.2, 0.1), (1.0, 0.65, 0.5)
        Button(
            parent=m, position=(15, 280), size=(57, 35), label=sc.BACK.value,
            color=BACKC, textcolor=BACKT,
            call=lambda: [from_menu(p) for p in list(m.captives)]
        )
        Button(
            parent=m, position=(85, 280), size=(38, 35), label=LEFT,
            color=TAB, textcolor=WHITE, call=lambda: cycle(-1)
        )
        Button(
            parent=m, position=(327, 280), size=(38, 35), label=RIGHT,
            color=TAB, textcolor=WHITE, call=lambda: cycle(1)
        )
        for y, label, d in [
            (232, UP + UP, -ROWS), (184, UP, -1),
            (88, DOWN, 1), (40, DOWN + DOWN, ROWS)
        ]:
            Button(
                parent=m, position=(378, y), size=(57, 35), label=label,
                color=TAB, textcolor=WHITE, call=lambda d=d: scroll(d)
            )

        def refresh():
            cat = st['cat']
            items = [i for i in s.items if cat == 'all' or i.cat == cat]
            rows = ceil(len(items) / COLS)
            st['off'] = off = max(0, min(st['off'], max(0, rows - ROWS)))
            for k, bt in enumerate(pool):
                i = (off + k // COLS) * COLS + k % COLS
                if i < len(items):
                    it = items[i]
                    setlabel(bt, it.label)
                    bt.call = bs.CallPartial(pick, it)
                    paint(bt, SEL if it is st['item'] else FILL, WHITE)
                else:
                    setlabel(bt, '')
                    bt.call = None
                    paint(bt, EMPTY, EMPTY)
            first = off * COLS + 1 if items else 0
            last = min(len(items), (off + ROWS) * COLS)
            name = dict(CATS)[cat]
            settext(cat_t, f'{name} ({len(items)})')
            settext(info, f"Dropping: {st['item'].label}   |   "
                          f"{first}-{last} of {len(items)}")

        def cycle(d):
            keys = [k for k, _ in CATS]
            st['cat'] = keys[(keys.index(st['cat']) + d) % len(keys)]
            st['off'] = 0
            refresh()

        def scroll(d):
            st['off'] += d
            refresh()

        def pick(it):
            st['item'] = it
            sel_label()
            for p in list(m.captives):
                from_menu(p)

        def to_menu(players):
            if not players:
                return
            st['menu'] = True
            m.position = tuple(c.node.position)  # right where the console is
            c.opacity = 0
            m.opacity = 1
            refresh()
            for p in players:
                c.release_one(p)
                m.capture(p.actor.node)
                p.assigninput(IT.BOMB_PRESS, bs.CallPartial(from_menu, p))

        def from_menu(p):
            if p in m.captives:
                m.release_one(p)
            if p and p.actor and p.actor.node.exists():
                c.capture(p.actor.node)
            if not m.captives:
                close_menu()

        def close_menu():
            st['menu'] = False
            m.opacity = 0
            c.opacity = 1

        def watchdog():
            # everyone left the menu some other way (died etc.)
            if st['menu'] and not m.captives:
                close_menu()

        sel_label()
        refresh()

        # --- live aim: red beam + ground ring where the drop will land ---
        locs = []  # [line, ring] only exist while aiming, so nothing stale

        def make_locs():
            locs.append(bs.newnode('locator', attrs={
                'shape': 'box',
                'position': (0, DROP_Y / 2, 0),
                'size': [0.06, DROP_Y, 0.06],
                'color': (1, 0, 0),
                'opacity': 1,
                'draw_beauty': True,
                'additive': True,
            }))
            locs.append(bs.newnode('locator', attrs={
                'shape': 'circle',
                'position': (0, GROUND_Y, 0),
                'size': [1.6],
                'color': (1, 0.15, 0.1),
                'opacity': 0.7,
                'draw_beauty': True,
                'additive': True,
            }))

        def aim():
            if c.captives and not st['menu'] and not c.on[0]:
                ox, oy = c.cursor_off
                wx, _, wz = screen_to_world(ox / c.sc, oy / c.sc)
                if not locs:
                    make_locs()
                locs[0].position = (wx, DROP_Y / 2, wz)
                locs[1].position = (wx, GROUND_Y, wz)
            elif locs:
                for n in locs:
                    if n.exists():
                        n.delete()
                locs.clear()

        # --- player markers (only while someone is looking) ---
        trash = []
        MS = 0.6  # marker scale
        ox, oy = 0, -8

        def mark(text, wx, wz, color):
            px, py = world_to_screen(wx, wz)
            trash.append(Text(
                parent=c,
                text=text,
                color=color,
                h_align='center',
                scale=MS,
                position=((px + ox) / MS, (py + oy) / MS)
            ))

        def spy():
            for _ in trash:
                if _:
                    _.delete()
            trash.clear()
            if not b.active or st['menu']:
                return
            if b.node:
                bx, by, bz = b.node.position
                mark(sc.OUYA_BUTTON_Y.value + ' Console', bx, bz, YELLOW)
            for n in bs.getnodes():
                if not n or n.getnodetype() != 'spaz':
                    continue
                p = n.position
                mark(sc.DPAD_CENTER_BUTTON.value + ' ' + (n.name or 'bot'),
                     p[0], p[2], bright(n.color))

        return [
            bs.Timer(0.01, spy, repeat=True),
            bs.Timer(0.25, watchdog, repeat=True),
            bs.Timer(0.02, aim, repeat=True),
        ]
