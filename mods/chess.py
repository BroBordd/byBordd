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
from bascenev1._lobby import ChangeMessage

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


def gettexture(tex):
    for i in (
        'builtin',
        'classiccatalog',
        'common',
        'classicmap',
        'classic',
        'scenev1',
    ):
        if r := getattr(
            getattr(getattr(bs, f'_{i}assets', None), 'textures', None),
            tex,
            None,
        ):
            return r.get()
    return bs.gettexture(tex)


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

        self.backdrop = bs.newnode(
            'image',
            attrs={
                'texture': white,
                'fill_screen': True,
                'attach': 'center',
                'color': (0.0, 0.0, 0.0),
                'opacity': 1.0,
            }
        )

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
        self.marks = {}
        for col, row in self.squares:
            self.marks[(col, row)] = bs.newnode(
                'image',
                attrs={
                    'texture': white,
                    'absolute_scale': True,
                    'attach': 'center',
                    'position': self.square_offset(col, row),
                    'scale': (self.TILE, self.TILE),
                    'color': (1.0, 1.0, 0.0),
                    'opacity': 0.0,
                }
            )


# (shape, x, y, w, h, rotate, cut) in a 68px tile, y up. r=rect, c=circle.
# cut shapes are drawn last in the outline color (eyes, bishop slit).
PIECE_SHAPES = {
    'pawn': (
        ('r', 0, -22, 34, 8, 0, 0),
        ('r', 0, -10, 16, 18, 0, 0),
        ('r', 0, 1, 24, 5, 0, 0),
        ('c', 0, 10, 18, 18, 0, 0),
    ),
    'rook': (
        ('r', 0, -22, 38, 8, 0, 0),
        ('r', 0, -8, 24, 24, 0, 0),
        ('r', 0, 6, 32, 8, 0, 0),
        ('r', -11, 14, 8, 8, 0, 0),
        ('r', 0, 14, 8, 8, 0, 0),
        ('r', 11, 14, 8, 8, 0, 0),
    ),
    'knight': (
        ('r', 0, -22, 36, 8, 0, 0),
        ('r', 2, -8, 24, 22, 0, 0),
        ('r', 0, 8, 14, 24, 15, 0),
        ('r', -7, 20, 24, 12, 20, 0),
        ('r', 5, 28, 6, 8, 0, 0),
        ('c', -3, 22, 4, 4, 0, 1),
    ),
    'bishop': (
        ('r', 0, -22, 34, 8, 0, 0),
        ('r', 0, -9, 16, 20, 0, 0),
        ('r', 0, 2, 26, 5, 0, 0),
        ('c', 0, 11, 18, 22, 0, 0),
        ('c', 0, 24, 7, 7, 0, 0),
        ('r', 2, 11, 3, 14, -40, 1),
    ),
    'queen': (
        ('r', 0, -22, 38, 8, 0, 0),
        ('r', 0, -8, 20, 24, 0, 0),
        ('r', 0, 5, 30, 6, 0, 0),
        ('r', 0, 14, 28, 10, 0, 0),
        ('c', -12, 22, 8, 8, 0, 0),
        ('c', 0, 25, 8, 8, 0, 0),
        ('c', 12, 22, 8, 8, 0, 0),
    ),
    'king': (
        ('r', 0, -22, 38, 8, 0, 0),
        ('r', 0, -8, 20, 24, 0, 0),
        ('r', 0, 5, 30, 6, 0, 0),
        ('r', 0, 14, 24, 12, 0, 0),
        ('r', 0, 26, 5, 14, 0, 0),
        ('r', 0, 27, 14, 5, 0, 0),
    ),
}
BACK_RANK = (
    'rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook')


class Piece:
    SCALE = 0.8
    GROW = 3
    FILL = {'white': (0.95, 0.95, 0.95), 'black': (0.12, 0.12, 0.12)}
    LINE = {'white': (0.1, 0.1, 0.1), 'black': (0.85, 0.85, 0.85)}

    def __init__(self, kind, side, col, row):
        cx, cy = Chessboard.square_offset(col, row)
        k = self.SCALE * Chessboard.TILE / 68
        white = bs.gettexture('white')
        circle = gettexture('circle')
        self.nodes = []
        # outlines first, then fills, then cuts, so each piece reads solid
        for stage in range(3):
            for shape, x, y, w, h, rot, cut in PIECE_SHAPES[kind]:
                if bool(cut) != (stage == 2):
                    continue
                grow = self.GROW if stage == 0 else 0
                self.nodes.append(bs.newnode(
                    'image',
                    attrs={
                        'texture': white if shape == 'r' else circle,
                        'absolute_scale': True,
                        'attach': 'center',
                        'position': (cx + x * k, cy + y * k),
                        'scale': ((w + grow) * k, (h + grow) * k),
                        'rotate': rot,
                        'color': (
                            self.FILL[side] if stage == 1
                            else self.LINE[side]),
                        'opacity': 1.0,
                    }
                ))

    def destroy(self):
        for node in self.nodes:
            node.delete()
        self.nodes.clear()


def setup_pieces():
    pieces = []
    # white along the bottom, black along the top
    for side, back, front in (('white', 0, 1), ('black', 7, 6)):
        for col, kind in enumerate(BACK_RANK):
            pieces.append(Piece(kind, side, col, back))
            pieces.append(Piece('pawn', side, col, front))
    return pieces


class PlayerInfo:
    HEIGHT = 44
    ICON = 40
    GAP = 6
    SIDES = ('Black', 'White')

    def __init__(self, team):
        self.team = team
        self.key = None
        half = Chessboard.DIM * Chessboard.TILE / 2 + Chessboard.PAD
        sign = 1 if team.id % 2 == 0 else -1
        self.y = sign * (half + self.GAP + self.HEIGHT / 2)
        self.left = -half
        self.back = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('white'),
                'absolute_scale': True,
                'attach': 'center',
                'position': (0, self.y),
                'scale': (half * 2, self.HEIGHT),
                'color': (0.12, 0.12, 0.12),
                'opacity': 1.0,
            }
        )
        self.icon = None
        self.name = self.text(self.y + 8, 0.85)
        self.side = self.text(self.y - 11, 0.55)
        self.side.text = self.SIDES[team.id % 2]
        self.side.color = (0.6, 0.6, 0.6)

    def text(self, y, scale):
        return bs.newnode(
            'text',
            attrs={
                'scale': scale,
                'h_attach': 'center',
                'v_attach': 'center',
                'h_align': 'left',
                'v_align': 'center',
                'position': (self.left + self.ICON + 10, y),
            }
        )

    def make_icon(self, player):
        pos = (self.left + self.ICON / 2 + 2, self.y)
        size = (self.ICON, self.ICON)
        mask = gettexture('character_icon_mask')
        if player is None:
            return bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('white'),
                    'mask_texture': mask,
                    'absolute_scale': True,
                    'attach': 'center',
                    'position': pos,
                    'scale': size,
                    'color': (0.28, 0.28, 0.28),
                }
            )
        depiction = player.get_icon_depiction()
        if depiction is not None:
            return bs.newnode(
                'depictiondisplay',
                attrs={
                    'depiction': depiction,
                    'attach': 'center',
                    'position': pos,
                    'scale': size,
                }
            )
        icon = player.get_icon()
        return bs.newnode(
            'image',
            attrs={
                'texture': icon['texture'],
                'tint_texture': icon['tint_texture'],
                'tint_color': icon['tint_color'],
                'tint2_color': icon['tint2_color'],
                'mask_texture': mask,
                'absolute_scale': True,
                'attach': 'center',
                'position': pos,
                'scale': size,
            }
        )

    def refresh(self):
        player = next((p for p in self.team.players if p.exists()), None)
        name = player.getname() if player else None
        key = (id(player), name)
        if key == self.key:
            return
        self.key = key
        if self.icon:
            self.icon.delete()
        self.icon = self.make_icon(player)
        if player:
            self.name.text = name
            self.name.color = readable(self.team.color)
        else:
            self.name.text = 'Waiting for player...'
            self.name.color = (0.5, 0.5, 0.5)

    def destroy(self):
        for node in (self.back, self.icon, self.name, self.side):
            if node:
                node.delete()


class Cursor:
    SIZE = 72
    SPEED = 480
    EASE = 18.0
    SCALE = 0.7
    PADX = 8
    HEIGHT = 30
    TAGX = 44
    TAGY = 60
    EDGE = 5

    def __init__(self, player):
        color = player.team.color
        self.color = color
        self.sq = None
        # hover frame (edges only), under the pointer and label
        self.edges = [
            bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('white'),
                    'absolute_scale': True,
                    'attach': 'center',
                    'color': color,
                    'opacity': 0.9,
                }
            ) for _ in range(4)
        ]
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
        self.frame()

    def frame(self):
        # chess.com style hover: just the edges, inset in the square
        sq = self.sq = self.square()
        tile, w = Chessboard.TILE, self.EDGE
        sx, sy = Chessboard.square_offset(*sq)
        top, bottom, left, right = self.edges
        light = (sq[0] + sq[1]) % 2 == 1
        color = self.color if light else readable(self.color)
        for node, pos, size in (
            (top, (sx, sy + (tile - w) / 2), (tile, w)),
            (bottom, (sx, sy - (tile - w) / 2), (tile, w)),
            (left, (sx - (tile - w) / 2, sy), (w, tile - 2 * w)),
            (right, (sx + (tile - w) / 2, sy), (w, tile - 2 * w)),
        ):
            node.position = pos
            node.scale = size
            node.color = color

    def square(self):
        half = Chessboard.DIM * Chessboard.TILE / 2
        top = Chessboard.DIM - 1
        col = int((self.x + half) // Chessboard.TILE)
        row = int((self.y + half) // Chessboard.TILE)
        return (max(0, min(top, col)), max(0, min(top, row)))

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
        if self.square() != self.sq:
            self.frame()

    def destroy(self):
        for node in self.edges:
            node.delete()
        self.icon.delete()
        self.back.delete()
        self.label.delete()


def in_chess():
    activity = bs.get_foreground_host_activity()
    if isinstance(activity, Chess):
        return True
    return isinstance(activity, bs.JoinActivity) and getattr(
        bs.get_foreground_host_session(), '_next_game', None) is Chess


def bring_front(chooser):
    # draw the vanilla chooser in the front overlay pass, above the board
    for node in (chooser._text_node, getattr(chooser, 'icon', None)):
        if node:
            node.front = True


SCREEN_H = 720.0


def slot(chooser, y):
    # team 0 hangs from the top of the screen, team 1 mirrors from the bottom
    return y if chooser._selected_team_index == 0 else -SCREEN_H - y


def move(chooser, node, x, y):
    target = (x, slot(chooser, y))
    if chooser._inited:
        bs.animate_array(
            node, 'position', 2, {0: node.position, 0.1: target})
    else:
        # first appearance: spawn on our team's side, no slide from the other
        node.position = target


def slide_name(chooser):
    move(chooser, chooser._text_node, -10.0, chooser._vpos + 23)


def slide_icon(chooser):
    move(chooser, chooser.icon, -130.0, chooser._vpos + 22)


def update_position(chooser):
    assert chooser._text_node
    slide_name(chooser)
    slide_icon(chooser)


def swap_axes(chooser):
    # vanilla: up/down = profile, left/right = team. here it's flipped.
    player = chooser.sessionplayer
    for press, what, value in (
        (bs.InputType.UP_PRESS, 'team', -1),
        (bs.InputType.DOWN_PRESS, 'team', 1),
        (bs.InputType.LEFT_PRESS, 'profileindex', -1),
        (bs.InputType.RIGHT_PRESS, 'profileindex', 1),
    ):
        player.assigninput(
            press,
            bs.CallStrict(chooser.handlemessage, ChangeMessage(what, value)),
        )


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
        self.infos = []
        self.pieces = []
        self.chosen = {}

    def spawn_player(self, player):
        return None

    def _show_info(self) -> None:
        pass

    def _show_tip(self) -> None:
        pass

    def on_transition_in(self):
        super().on_transition_in()
        self.pieces = setup_pieces()
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
        for info in self.infos:
            info.destroy()
        self.infos.clear()
        for piece in self.pieces:
            piece.destroy()
        self.pieces.clear()

    def on_begin(self):
        super().on_begin()
        cap_players(self.session)
        # first two to join have the most right to play
        for sessionplayer in list(self.session.sessionplayers)[2:]:
            sessionplayer.remove_from_game()
        self.last = bs.time()
        self.timer = bs.Timer(0.005, bs.WeakCallStrict(self.tick), repeat=True)
        self.infos = [PlayerInfo(team) for team in self.teams]
        self.info_timer = bs.Timer(
            0.2, bs.WeakCallStrict(self.refresh_infos), repeat=True)
        self.refresh_infos()

    def update_marks(self):
        marks = self.map.marks
        for node in marks.values():
            node.opacity = 0.0
        for player, square in self.chosen.items():
            node = marks[square]
            node.color = readable(player.team.color)
            node.opacity = 0.6

    def on_punch(self, player):
        if player.cursor:
            self.chosen[player] = player.cursor.square()
            self.update_marks()

    def on_bomb(self, player):
        # cancel, like esc
        if self.chosen.pop(player, None) is not None:
            self.update_marks()

    def refresh_infos(self):
        for info in self.infos:
            info.refresh()

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
        player.assigninput(
            bs.InputType.PUNCH_PRESS,
            bs.WeakCallPartial(self.on_punch, player))
        player.assigninput(
            bs.InputType.BOMB_PRESS,
            bs.WeakCallPartial(self.on_bomb, player))

    def on_player_leave(self, player):
        if self.chosen.pop(player, None) is not None:
            self.update_marks()
        if player.cursor:
            player.cursor.destroy()
            player.cursor = None
        super().on_player_leave(player)


# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(bs.Plugin):
    def __init__(self):
        bs.app.classic.maps['Chessboard'] = Chessboard
        if not getattr(bs.Chooser._set_ready, '_chess', False):
            def wrap(name, after):
                old = getattr(bs.Chooser, name)

                def new(chooser, *a, **k):
                    out = old(chooser, *a, **k)
                    if in_chess():
                        after(chooser, *a, **k)
                    return out
                new._chess = name == '_set_ready'
                setattr(bs.Chooser, name, new)

            def vertical(name, fn):
                old = getattr(bs.Chooser, name)

                def new(chooser):
                    return fn(chooser) if in_chess() else old(chooser)
                setattr(bs.Chooser, name, new)
            vertical('update_position', update_position)
            vertical('_slide_icon_into_place', slide_icon)

            def on_ready(chooser, ready):
                bring_front(chooser)
                if not ready:
                    swap_axes(chooser)
            wrap('_update_text', lambda c: bring_front(c))
            wrap('_update_icon', lambda c: bring_front(c))
            wrap('_set_ready', on_ready)

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
