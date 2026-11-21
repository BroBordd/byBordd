# Copyright 2026 - Solely by BrotherBoard
# Feel free to use this anywhere
# Bug? Feedback? Discord >> @BrotherBoard

"""
Chess v1.0.0 - Checkmate!

Experimental. Adds a team game.
"""

from math import exp

import bauiv1 as bui
import bascenev1 as bs

__version__ = '1.0.0'

plugman = dict(
    plugin_name="chess",
    description="Experimental. Adds a team game.",
    external_url="https://BroBordd.github.io/byBordd",
    authors=[
        {
            "name": "BrotherBoard",
            "email": "brobordd@gmail.com",
            "discord": "BrotherBoard",
            "github": "BroBordd"
        },
    ],
    version=__version__,
)


def getuitexture(tex):
    for i in (
        'builtin',
        'common',
        'classic',
        'classiccatalog',
        'classiccharacter',
        'uiv1',
        'classicui',
        'docuiv2test',
    ):
        if r := getattr(
            getattr(
                getattr(bui, f'_{i}assets', None),
                'textures',
                None,
            ),
            tex,
            None,
        ):
            return r


def readable(color, lo=0.55):
    c = tuple(max(0.0, min(1.0, float(v))) for v in color[:3])

    def lum(x):
        return 0.2126 * x[0] + 0.7152 * x[1] + 0.0722 * x[2]
    k = 0.0
    while k < 1.0 and lum(tuple(v + (1 - v) * k for v in c)) < lo:
        k += 0.05
    return tuple(v + (1 - v) * k for v in c)


def cap_players(session):
    if not hasattr(session, '_chess_mp'):
        session._chess_mp = session.max_players
    session.max_players = 2


def uncap_players(session):
    if hasattr(session, '_chess_mp'):
        session.max_players = session._chess_mp
        del session._chess_mp


class Strings:
    CHESS = 'Chess'
    DESCRIPTION = f'Checkmate!\nVersion {__version__}'
    INSTANCE_DESCRIPTION_SHORT = f'Checkmate! v{__version__}'


class Chessboard(bs.Map):
    name = 'Chessboard'
    DIM = 8
    TILE = 68
    LIGHT = (1.0, 1.0, 1.0)
    DARK = (0.0, 0.0, 0.0)
    TRIM = (0.15, 0.15, 0.15)
    PAD = 8
    defs = type('', (), {
        'points': {
            'spawn1': (0, 0, 5, 0, 0, 5),
            'spawn2': (0, 0, -5, 0, 0, -5),
        },
        'boxes': {
            'area_of_interest_bounds': (0, 0, 0, 0, 0, 0, 10, 10, 10),
            'map_bounds': (0, 0, 0, 0, 0, 0, 200, 200, 200),
        }
    })

    @classmethod
    def get_preview_texture_spec(cls):
        spec = getuitexture('white')
        return type(
            'spec',
            (object,),
            {
                '_name': spec._name.replace('white', 'chess'),
                '_apvernum': spec._apvernum
            }
        )

    @classmethod
    def get_preview_texture(cls):
        return 'chess'

    @classmethod
    def square_offset(cls, col, row):
        half = (cls.DIM - 1) / 2
        return ((col - half) * cls.TILE, (row - half) * cls.TILE)

    def __init__(self):
        super().__init__()
        white = bs.gettexture('white')

        side = self.DIM * self.TILE + self.PAD * 2
        self.frame = bs.newnode(
            'image',
            attrs={
                'texture': white,
                'absolute_scale': True,
                'attach': 'center',
                'position': (0, 0),
                'scale': (side, side),
                'color': self.TRIM,
                'opacity': 1.0,
            }
        )

        self.squares = {}
        for row in range(self.DIM):
            for col in range(self.DIM):
                self.squares[(col, row)] = bs.newnode(
                    'image',
                    attrs={
                        'texture': white,
                        'absolute_scale': True,
                        'attach': 'center',
                        'position': self.square_offset(col, row),
                        'scale': (self.TILE, self.TILE),
                        'color': self.DARK if (col + row) % 2 == 0 else self.LIGHT,
                        'opacity': 1.0,
                    }
                )


class Cursor:
    SIZE = 72
    SPEED = 480
    EASE = 18.0
    SCALE = 0.7
    PADX = 8
    HEIGHT = 30
    TAGX = 44
    TAGY = 60

    def __init__(self, player):
        color = player.team.color
        name = player.getname()
        self.x = 0.0
        self.y = 0.0
        self.h = 0.0
        self.v = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.width = bui.get_string_width(
            name, suppress_warning=True) * self.SCALE + self.PADX * 2
        self.icon = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('cursor'),
                'absolute_scale': True,
                'attach': 'center',
                'scale': (self.SIZE, self.SIZE),
                'color': color,
                'opacity': 1.0,
            }
        )
        self.back = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('white'),
                'absolute_scale': True,
                'attach': 'center',
                'scale': (self.width, self.HEIGHT),
                'color': (0.0, 0.0, 0.0),
                'opacity': 0.6,
            }
        )
        self.label = bs.newnode(
            'text',
            attrs={
                'text': name,
                'scale': self.SCALE,
                'h_attach': 'center',
                'v_attach': 'center',
                'h_align': 'left',
                'v_align': 'center',
                'color': readable(color),
            }
        )
        self.place()

    def on_left_right(self, value):
        self.h = value

    def on_up_down(self, value):
        self.v = value

    def place(self):
        x, y = self.x, self.y
        self.icon.position = (x + self.SIZE / 2, y - self.SIZE / 2)
        self.back.position = (x + self.TAGX + self.width / 2, y - self.TAGY)
        self.label.position = (x + self.TAGX + self.PADX, y - self.TAGY)

    def step(self, dt):
        k = 1.0 - exp(-self.EASE * dt)
        self.vx += (self.h * self.SPEED - self.vx) * k
        self.vy += (self.v * self.SPEED - self.vy) * k
        lim = Chessboard.DIM * Chessboard.TILE / 2
        self.x = max(-lim, min(lim, self.x + self.vx * dt))
        self.y = max(-lim, min(lim, self.y + self.vy * dt))
        self.place()

    def destroy(self):
        self.icon.delete()
        self.back.delete()
        self.label.delete()


class Ghost:
    def __bool__(self):
        return True

    def delete(self):
        pass


def hide_chooser(chooser):
    if chooser._text_node:
        chooser._text_node.delete()
    chooser._text_node = Ghost()
    for name in (
        'update_position',
        '_slide_icon_into_place',
        '_update_text',
        '_update_icon',
    ):
        setattr(chooser, name, lambda *a, **k: None)


class Selector:
    WIDTH = 380
    HEIGHT = 110
    GAP = 14
    SIDES = ('WHITE', 'BLACK')

    def __init__(self, chooser, slot):
        self.chooser = chooser
        self.key = None
        y = 70 - slot * (self.HEIGHT + self.GAP)
        self.back = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('white'),
                'absolute_scale': True,
                'attach': 'center',
                'position': (0, y),
                'scale': (self.WIDTH, self.HEIGHT),
                'color': (0.0, 0.0, 0.0),
                'opacity': 0.75,
            }
        )
        self.name = self.text(y + 26, 0.9)
        self.side = self.text(y - 16, 1.3)

    @staticmethod
    def text(y, scale):
        return bs.newnode(
            'text',
            attrs={
                'scale': scale,
                'h_attach': 'center',
                'v_attach': 'center',
                'h_align': 'center',
                'v_align': 'center',
                'position': (0, y),
            }
        )

    def refresh(self):
        chooser = self.chooser
        try:
            name = chooser._getname(True)
        except Exception:
            name = chooser.sessionplayer.getname(full=True, icon=False)
        team = chooser.sessionteam
        ready = chooser.ready
        key = (name, team.id, ready)
        if key == self.key:
            return
        self.key = key
        color = readable(team.color)
        side = self.SIDES[team.id % 2]
        self.name.text = name
        self.name.color = color
        self.side.text = f'{side}  READY' if ready else f'<  {side}  >'
        self.side.color = color

    def destroy(self):
        for node in (self.back, self.name, self.side):
            node.delete()


class Player(bs.Player['Team']):
    def __init__(self):
        self.cursor = None


class Team(bs.Team[Player]):
    pass


# ba_meta export bascenev1.GameActivity
class Chess(bs.TeamGameActivity[Player, Team]):
    name = Strings.CHESS
    description = Strings.DESCRIPTION

    @classmethod
    def supports_session_type(cls, sessiontype):
        return True

    @classmethod
    def get_supported_maps(cls, sessiontype):
        return ['Chessboard']

    def get_instance_description_short(self):
        return Strings.INSTANCE_DESCRIPTION_SHORT

    def __init__(self, settings):
        super().__init__(settings)
        self.default_music = bs.MusicType.GRAND_ROMP
        self.selectors = []

    def spawn_player(self, player):
        return None

    def _show_info(self) -> None:
        pass

    def _show_tip(self) -> None:
        pass

    def on_transition_in(self):
        super().on_transition_in()
        for attr in ('_standard_game_title', '_title_text', '_game_title_text', '_title'):
            if hasattr(self, attr):
                val = getattr(self, attr)
                if val:
                    if hasattr(val, 'node') and val.node:
                        val.node.delete()
                    elif hasattr(val, 'delete'):
                        val.delete()
                setattr(self, attr, None)

    def on_transition_out(self):
        super().on_transition_out()
        uncap_players(self.session)
        self.selectors.clear()

    def add_selector(self, chooser):
        self.selectors.append(Selector(chooser, len(self.selectors)))

    def refresh(self):
        live = self.session.lobby.get_choosers()
        for selector in list(self.selectors):
            if selector.chooser not in live:
                selector.destroy()
                self.selectors.remove(selector)
            else:
                selector.refresh()

    def on_begin(self):
        super().on_begin()
        cap_players(self.session)
        for sessionplayer in list(self.session.sessionplayers):
            sessionplayer.remove_from_game()
        self.last = bs.time()
        self.timer = bs.Timer(0.005, bs.WeakCallStrict(self.tick), repeat=True)
        self.refresh_timer = bs.Timer(0.1, bs.WeakCallStrict(self.refresh), repeat=True)

    def tick(self):
        now = bs.time()
        dt = min(now - self.last, 0.1)
        if dt <= 0:
            return
        self.last = now
        for player in self.players:
            if player.cursor:
                player.cursor.step(dt)

    def on_player_join(self, player):
        super().on_player_join(player)
        cursor = player.cursor = Cursor(player)
        player.assigninput(
            bs.InputType.LEFT_RIGHT, bs.WeakCallPartial(cursor.on_left_right))
        player.assigninput(
            bs.InputType.UP_DOWN, bs.WeakCallPartial(cursor.on_up_down))

    def on_player_leave(self, player):
        if player.cursor:
            player.cursor.destroy()
            player.cursor = None
        super().on_player_leave(player)


# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(bs.Plugin):
    def __init__(self):
        bs.app.classic.maps['Chessboard'] = Chessboard
        if not getattr(bs.Lobby.add_chooser, '_chess', False):
            old_add = bs.Lobby.add_chooser

            def add_chooser(lobby, sessionplayer):
                old_add(lobby, sessionplayer)
                activity = bs.getsession().getactivity()
                if not isinstance(activity, Chess):
                    return
                for chooser in lobby.get_choosers():
                    if chooser.sessionplayer is sessionplayer:
                        hide_chooser(chooser)
                        with activity.context:
                            activity.add_selector(chooser)
            add_chooser._chess = True
            bs.Lobby.add_chooser = add_chooser

        old_gt = bui.texture_from_ref

        def new_gt(tex):
            if 'chess' in tex:
                return 'chess'
            return old_gt(tex)
        bui.texture_from_ref = new_gt

        def patch(orig):
            def new(*a, **k):
                if k.get('texture', None) != 'chess':
                    return orig(*a, **k)
                k['texture'] = getuitexture('light').get()
                k['color'] = (0.0, 0.4, 0.15)
                widget = orig(*a, **k)
                size = k['size']
                scl = size[0] / 220
                pos = k['position']
                bui.textwidget(
                    parent=k['parent'],
                    big=True,
                    size=size,
                    scale=1.8 * scl,
                    position=pos and (pos[0] - 3 * scl, pos[1] - 3 * scl),
                    h_align='center',
                    v_align='center',
                    text='CHESS',
                    flatness=-2,
                    color=(1.0, 2.0, 1.0),
                    draw_controller=k.get('draw_controller', widget),
                )
                return widget
            new.__name__ = orig.__name__
            new.__doc__ = orig.__doc__
            return new
        bui.imagewidget = patch(bui.imagewidget)
        bui.buttonwidget = patch(bui.buttonwidget)
        old = bs.app.config.get
        bs.app.config.get = lambda b, *a, **k: (
            True if b == 'Auto Balance Teams' and
            isinstance(bs.getsession().getactivity(), Chess)
            else old(b, *a, **k)
        )
