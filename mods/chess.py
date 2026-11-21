# Copyright 2026 - Solely by BrotherBoard
# Feel free to use this anywhere
# Bug? Feedback? Discord >> @BrotherBoard

"""
Chess v1.0.0 - Checkmate!

A full game of chess for two players, with clocks. Adds a team game.
"""

from functools import partial
from math import cos, exp, hypot, pi, sin

import bauiv1 as bui
import bascenev1 as bs
from bascenev1._lobby import ChangeMessage

__version__ = '1.0.0'

DEBUG = False

plugman = dict(
    plugin_name="chess",
    description="A full game of chess for two players, with clocks.",
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


WHITE, BLACK = 'white', 'black'
BACK_RANK = (
    'rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook')
KNIGHT_STEPS = (
    (1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
KING_STEPS = (
    (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
ROOK_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
BISHOP_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
PROMOTIONS = ('queen', 'knight', 'rook', 'bishop')
VALUES = {'pawn': 1, 'knight': 3, 'bishop': 3, 'rook': 5, 'queen': 9}


def opponent(side):
    return BLACK if side == WHITE else WHITE


class Move:
    __slots__ = ('frm', 'to', 'promo', 'flag')

    def __init__(self, frm, to, promo=None, flag=None):
        self.frm = frm
        self.to = to
        self.promo = promo
        self.flag = flag

    def __repr__(self):
        return f'Move({self.frm}->{self.to},{self.promo},{self.flag})'


class Position:

    def __init__(self):
        self.board = {}
        self.turn = WHITE
        self.castle = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.ep = None
        self.half = 0
        self.full = 1

    @classmethod
    def start(cls):
        pos = cls()
        for side, back, front in ((WHITE, 0, 1), (BLACK, 7, 6)):
            for col, kind in enumerate(BACK_RANK):
                pos.board[(col, back)] = (side, kind)
                pos.board[(col, front)] = (side, 'pawn')
        return pos

    def copy(self):
        new = Position()
        new.board = dict(self.board)
        new.turn = self.turn
        new.castle = dict(self.castle)
        new.ep = self.ep
        new.half = self.half
        new.full = self.full
        return new

    def attacked(self, sq, by):
        board = self.board
        col, row = sq
        pr = row - 1 if by == WHITE else row + 1
        for dc in (-1, 1):
            if board.get((col + dc, pr)) == (by, 'pawn'):
                return True
        for dc, dr in KNIGHT_STEPS:
            if board.get((col + dc, row + dr)) == (by, 'knight'):
                return True
        for dc, dr in KING_STEPS:
            if board.get((col + dc, row + dr)) == (by, 'king'):
                return True
        for dirs, kinds in ((ROOK_DIRS, 'rook'), (BISHOP_DIRS, 'bishop')):
            for dc, dr in dirs:
                c, r = col + dc, row + dr
                while 0 <= c < 8 and 0 <= r < 8:
                    p = board.get((c, r))
                    if p:
                        if p[0] == by and p[1] in (kinds, 'queen'):
                            return True
                        break
                    c += dc
                    r += dr
        return False

    def king_square(self, side):
        for sq, p in self.board.items():
            if p == (side, 'king'):
                return sq
        return None

    def in_check(self, side=None):
        side = side or self.turn
        ksq = self.king_square(side)
        return ksq is not None and self.attacked(ksq, opponent(side))

    def pseudo_moves(self, only=None):
        board, side = self.board, self.turn
        out = []
        for sq, piece in list(board.items()):
            if piece[0] != side or (only and sq != only):
                continue
            col, row = sq
            kind = piece[1]
            if kind == 'pawn':
                self._pawn_moves(sq, side, out)
            elif kind in ('knight', 'king'):
                steps = KNIGHT_STEPS if kind == 'knight' else KING_STEPS
                for dc, dr in steps:
                    to = (col + dc, row + dr)
                    if not (0 <= to[0] < 8 and 0 <= to[1] < 8):
                        continue
                    target = board.get(to)
                    if target is None or target[0] != side:
                        out.append(Move(sq, to))
                if kind == 'king':
                    self._castle_moves(sq, side, out)
            else:
                dirs = (
                    ROOK_DIRS if kind == 'rook' else
                    BISHOP_DIRS if kind == 'bishop' else
                    ROOK_DIRS + BISHOP_DIRS)
                for dc, dr in dirs:
                    c, r = col + dc, row + dr
                    while 0 <= c < 8 and 0 <= r < 8:
                        target = board.get((c, r))
                        if target is None:
                            out.append(Move(sq, (c, r)))
                        else:
                            if target[0] != side:
                                out.append(Move(sq, (c, r)))
                            break
                        c += dc
                        r += dr
        return out

    def _pawn_moves(self, sq, side, out):
        board = self.board
        col, row = sq
        d = 1 if side == WHITE else -1
        start = 1 if side == WHITE else 6
        last = 7 if side == WHITE else 0

        def add(to, flag=None):
            if to[1] == last:
                for kind in PROMOTIONS:
                    out.append(Move(sq, to, kind, flag))
            else:
                out.append(Move(sq, to, None, flag))
        one = (col, row + d)
        if 0 <= one[1] < 8 and one not in board:
            add(one)
            two = (col, row + 2 * d)
            if row == start and two not in board:
                add(two, 'double')
        for dc in (-1, 1):
            to = (col + dc, row + d)
            if not (0 <= to[0] < 8 and 0 <= to[1] < 8):
                continue
            target = board.get(to)
            if target and target[0] != side:
                add(to)
            elif target is None and to == self.ep:
                add(to, 'ep')

    def _castle_moves(self, sq, side, out):
        row = 0 if side == WHITE else 7
        if sq != (4, row) or self.in_check(side):
            return
        board, enemy = self.board, opponent(side)
        k = 'w' if side == WHITE else 'b'
        if (self.castle[k + 'K'] and board.get((7, row)) == (side, 'rook')
                and (5, row) not in board and (6, row) not in board
                and not self.attacked((5, row), enemy)
                and not self.attacked((6, row), enemy)):
            out.append(Move(sq, (6, row), None, 'castle'))
        if (self.castle[k + 'Q'] and board.get((0, row)) == (side, 'rook')
                and (1, row) not in board and (2, row) not in board
                and (3, row) not in board
                and not self.attacked((3, row), enemy)
                and not self.attacked((2, row), enemy)):
            out.append(Move(sq, (2, row), None, 'castle'))

    def legal_moves(self, only=None):
        side = self.turn
        return [
            m for m in self.pseudo_moves(only)
            if not self.apply(m).in_check(side)]

    def apply(self, m):
        new = self.copy()
        board = new.board
        side = self.turn
        piece = board.pop(m.frm)
        captured = board.get(m.to)
        if m.flag == 'ep':
            captured = board.pop((m.to[0], m.frm[1]))
        if m.flag == 'castle':
            row = m.frm[1]
            if m.to[0] == 6:
                board[(5, row)] = board.pop((7, row))
            else:
                board[(3, row)] = board.pop((0, row))
        board[m.to] = (side, m.promo) if m.promo else piece
        c = new.castle
        if piece[1] == 'king':
            c['wK' if side == WHITE else 'bK'] = False
            c['wQ' if side == WHITE else 'bQ'] = False
        for corner, key in (((0, 0), 'wQ'), ((7, 0), 'wK'),
                            ((0, 7), 'bQ'), ((7, 7), 'bK')):
            if m.frm == corner or m.to == corner:
                c[key] = False
        new.ep = None
        if m.flag == 'double':
            new.ep = (m.frm[0], (m.frm[1] + m.to[1]) // 2)
        new.half = 0 if (piece[1] == 'pawn' or captured) else self.half + 1
        if side == BLACK:
            new.full += 1
        new.turn = opponent(side)
        return new

    def insufficient(self):
        minors = []
        for sq, (side, kind) in self.board.items():
            if kind in ('pawn', 'rook', 'queen'):
                return False
            if kind != 'king':
                minors.append((kind, (sq[0] + sq[1]) % 2))
        if len(minors) <= 1:
            return True
        return (all(k == 'bishop' for k, _ in minors)
                and len({c for _, c in minors}) == 1)

    def can_mate(self, side):
        minors = []
        for sq, (s, kind) in self.board.items():
            if s != side:
                continue
            if kind in ('pawn', 'rook', 'queen'):
                return True
            if kind != 'king':
                minors.append((kind, (sq[0] + sq[1]) % 2))
        if len(minors) <= 1:
            return False
        return not (all(k == 'bishop' for k, _ in minors)
                    and len({c for _, c in minors}) == 1)

    def material(self, side):
        return sum(VALUES.get(p[1], 0)
                   for p in self.board.values() if p[0] == side)

    def key(self, legal=None):
        ep = None
        if self.ep is not None:
            legal = legal if legal is not None else self.legal_moves()
            if any(m.flag == 'ep' for m in legal):
                ep = self.ep
        return (
            tuple(sorted(self.board.items())), self.turn,
            tuple(sorted(self.castle.items())), ep)


class Game:

    def __init__(self, pos=None):
        self.pos = pos or Position.start()
        self.legal = self.pos.legal_moves()
        self.counts = {self.pos.key(self.legal): 1}
        self.result = None
        self.last = None
        self.plies = 0

    @property
    def turn(self):
        return self.pos.turn

    def moves_from(self, sq):
        return [m for m in self.legal if m.frm == sq]

    def play(self, m):
        before = self.pos
        mover = before.turn
        piece = before.board[m.frm]
        cap_sq = (m.to[0], m.frm[1]) if m.flag == 'ep' else m.to
        captured = before.board.get(cap_sq)
        self.pos = after = before.apply(m)
        self.last = m
        self.plies += 1
        self.legal = after.legal_moves()
        check = after.in_check()
        key = after.key(self.legal)
        self.counts[key] = self.counts.get(key, 0) + 1
        if not self.legal:
            self.result = (mover, 'checkmate') if check else (
                None, 'stalemate')
        elif after.insufficient():
            self.result = (None, 'insufficient material')
        elif self.counts[key] >= 3:
            self.result = (None, 'repetition')
        elif after.half >= 100:
            self.result = (None, '50-move rule')
        return {
            'piece': piece, 'captured': captured, 'cap_sq': cap_sq,
            'check': check, 'mover': mover,
        }

    def resign(self, side):
        self.result = (opponent(side), 'resignation')

    def agree_draw(self):
        self.result = (None, 'agreement')

    def timeout(self, side):
        winner = opponent(side)
        if self.pos.can_mate(winner):
            self.result = (winner, 'timeout')
        else:
            self.result = (None, 'timeout vs insufficient material')


def side_of_team(team):
    return WHITE if team.id % 2 == 0 else BLACK


class Strings:
    CHESS = 'Chess'
    DESCRIPTION = f'Checkmate!\nVersion {__version__}'
    INSTANCE_DESCRIPTION_SHORT = f'Checkmate! v{__version__}'
    SIDE = {'white': 'White', 'black': 'Black'}
    WAITING = 'Waiting for player...'
    WINS = '{side} Won'
    DRAW = 'Draw'
    OFFER_BTN = 'Offer draw'
    OFFERED = 'Draw offered'
    ACCEPT = 'Accept draw'
    DECLINE = 'Decline'
    RESIGN_BTN = 'Resign'
    RESIGN_Q = 'Resign?'
    OFFER_Q = 'Offer a draw?'
    MOVE = 'Move'
    CLICK = 'Select'
    DUMMY = 'Dummy'
    CANCEL = 'Cancel'
    REASONS = {
        'checkmate': 'by checkmate',
        'resignation': 'by resignation',
        'timeout': 'on time',
        'stalemate': 'by stalemate',
        'insufficient material': 'by insufficient material',
        'repetition': 'by repetition',
        '50-move rule': 'by the 50-move rule',
        'agreement': 'by agreement',
        'timeout vs insufficient material':
            'timeout vs insufficient material',
    }


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


        glow = gettexture('glow_circle')
        self.glow = {}
        for side in ('white', 'black'):
            self.glow[side] = bs.newnode(
                'image',
                attrs={
                    'texture': glow,
                    'absolute_scale': True,
                    'attach': 'center',
                    'position': (0, 0),
                    'scale': (self.TILE, self.TILE),
                    'color': (1.0, 0.1, 0.05),
                    'opacity': 0.0,
                }
            )


GLYPHS = {
    'king': '\u265a',
    'queen': '\u265b',
    'rook': '\u265c',
    'bishop': '\u265d',
    'knight': '\u265e',
    'pawn': '\u265f\ufe0e',
}


class Piece:
    SCALE = 0.8
    GLYPH = 2.2
    HALO = 1.14
    DY = 0.0
    SLIDE = 0.18
    FILL = {'white': (0.95, 0.95, 0.95), 'black': (0.12, 0.12, 0.12)}
    LINE = {'white': (0.1, 0.1, 0.1), 'black': (0.85, 0.85, 0.85)}

    def __init__(self, kind, side, col, row):
        self.kind = kind
        self.side = side
        self.col = col
        self.row = row
        self.x, self.y = Chessboard.square_offset(col, row)
        self.zoom = 1.0
        self.alpha = 1.0
        self.bump = 1.0
        self.move = None
        self.fade = None
        self.pop = None
        self.dirty = False
        self.dead = False
        self.parts = []
        self.build()

    @property
    def active(self):
        return bool(self.move or self.fade or self.pop or self.dirty)

    def build(self):
        glyph = GLYPHS[self.kind]
        for k, color in ((self.HALO, self.LINE[self.side]),
                         (1.0, self.FILL[self.side])):
            node = bs.newnode(
                'text',
                attrs={
                    'text': glyph,
                    'h_attach': 'center',
                    'v_attach': 'center',
                    'h_align': 'center',
                    'v_align': 'center',
                    'flatness': 1.0,
                    'shadow': 0.0,
                    'color': color,
                    'opacity': self.alpha,
                }
            )
            self.parts.append((node, k))
        self.refresh()

    def refresh(self):
        self.dirty = False
        if self.dead:
            return
        s = self.SCALE * Chessboard.TILE / 68 * self.zoom * self.bump
        for node, k in self.parts:
            node.position = (self.x, self.y + self.DY * s)
            node.scale = self.GLYPH * s * k
            node.opacity = self.alpha

    def release(self):
        for part in self.parts:
            part[0].delete()
        self.parts = []

    def lift(self):
        if self.dead:
            return
        self.release()
        self.build()

    def destroy(self):
        self.release()
        self.dead = True
        self.move = self.fade = self.pop = None

    def snap(self, col, row):
        self.col, self.row = col, row
        self.x, self.y = Chessboard.square_offset(col, row)
        self.move = None
        self.dirty = True

    def glide(self, col, row, dur=None, done=None):
        self.col, self.row = col, row
        tx, ty = Chessboard.square_offset(col, row)
        self.move = (
            bs.time(), self.SLIDE if dur is None else dur,
            self.x, self.y, tx, ty, done)

    def vanish(self, dur=0.12):
        self.fade = (bs.time(), dur)

    def set_kind(self, kind):
        self.kind = kind
        self.lift()
        self.pop = (bs.time(), 0.18)

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.dirty = True

    def update(self, now):
        if self.dead:
            return
        if self.move:
            t0, dur, x0, y0, x1, y1, done = self.move
            t = (now - t0) / dur if dur > 0 else 1.0
            if t >= 1.0:
                self.x, self.y = x1, y1
                self.move = None
                self.dirty = True
                if done:
                    done()
            else:
                e = 1.0 - (1.0 - t) ** 3
                self.x = x0 + (x1 - x0) * e
                self.y = y0 + (y1 - y0) * e
                self.dirty = True
        if self.dead:
            return
        if self.pop:
            t0, dur = self.pop
            t = (now - t0) / dur
            if t >= 1.0:
                self.pop = None
                self.bump = 1.0
            else:
                self.bump = 0.6 + 0.4 * (1.0 - (1.0 - t) ** 2)
            self.dirty = True
        if self.fade:
            t0, dur = self.fade
            t = (now - t0) / dur
            if t >= 1.0:
                self.destroy()
                return
            self.alpha = 1.0 - t
            self.bump = 1.0 - 0.25 * t
            self.dirty = True
        if self.dirty:
            self.refresh()


def setup_pieces():
    pieces = []
    for side, back, front in ((WHITE, 0, 1), (BLACK, 7, 6)):
        for col, kind in enumerate(BACK_RANK):
            pieces.append(Piece(kind, side, col, back))
            pieces.append(Piece('pawn', side, col, front))
    return pieces


class PlayerInfo:
    HEIGHT = 44
    ICON = 40
    GAP = 6
    CLOCK_W = 100
    DOTS_W = 36
    BAR = (0.12, 0.12, 0.12)
    BAR_LIVE = (0.2, 0.2, 0.2)

    def __init__(self, team, clocked):
        self.team = team
        self.side = side_of_team(team)
        self.clocked = clocked
        self.key = None
        self.live = None
        self.diff = None
        self.dummy = False
        half = Chessboard.DIM * Chessboard.TILE / 2 + Chessboard.PAD
        sign = 1 if self.side == BLACK else -1
        self.y = sign * (half + self.GAP + self.HEIGHT / 2)
        self.left = -half
        self.dots_x = half - 4 - self.DOTS_W / 2
        self.back = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('white'),
                'absolute_scale': True,
                'attach': 'center',
                'position': (0, self.y),
                'scale': (half * 2, self.HEIGHT),
                'color': self.BAR,
                'opacity': 1.0,
            }
        )
        self.icon = None
        self.name = self.text(self.left + self.ICON + 10, self.y + 8, 0.85)
        self.label = self.text(self.left + self.ICON + 10, self.y - 11, 0.55)
        self.label.color = (0.6, 0.6, 0.6)
        self.write_label()
        self.clock_back = self.clock = None
        if clocked:
            cx = half - 4 - self.DOTS_W - 4 - self.CLOCK_W / 2
            self.clock_back = bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('white'),
                    'absolute_scale': True,
                    'attach': 'center',
                    'position': (cx, self.y),
                    'scale': (self.CLOCK_W, self.HEIGHT - 10),
                    'color': (0.26, 0.26, 0.26),
                    'opacity': 1.0,
                }
            )
            self.clock = self.text(cx, self.y, 0.95, 'center')
            self.clock.color = (0.85, 0.85, 0.85)

    def text(self, x, y, scale, align='left'):
        return bs.newnode(
            'text',
            attrs={
                'scale': scale,
                'h_attach': 'center',
                'v_attach': 'center',
                'h_align': align,
                'v_align': 'center',
                'position': (x, y),
            }
        )

    def write_label(self):
        text = Strings.SIDE[self.side]
        if self.diff and self.diff > 0:
            text += f'   +{self.diff}'
        self.label.text = text

    def set_advantage(self, diff):
        if diff != self.diff:
            self.diff = diff
            self.write_label()

    def set_turn(self, live):
        if live != self.live:
            self.live = live
            self.back.color = self.BAR_LIVE if live else self.BAR

    def set_clock(self, text, running, low):
        if not self.clocked:
            return
        self.clock.text = text
        if running:
            self.clock_back.color = (1.0, 0.6, 0.55) if low else (
                0.93, 0.93, 0.93)
            self.clock.color = (0.1, 0.1, 0.1)
        else:
            self.clock_back.color = (0.26, 0.26, 0.26)
            self.clock.color = (0.85, 0.85, 0.85)

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
        key = (id(player), name, self.dummy and player is None)
        if key == self.key:
            return
        self.key = key
        if self.icon:
            self.icon.delete()
        self.icon = self.make_icon(player)
        if player:
            self.name.text = name
            self.name.color = readable(self.team.color)
        elif self.dummy:
            self.name.text = Strings.DUMMY
            self.name.color = (0.7, 0.7, 0.7)
        else:
            self.name.text = Strings.WAITING
            self.name.color = (0.5, 0.5, 0.5)

    def destroy(self):
        for node in (self.back, self.icon, self.name, self.label,
                     self.clock_back, self.clock):
            if node:
                node.delete()


ICON_SHAPES = {
    'check': (
        (-6, -4, 4, 10, 45),
        (3.5, -0.5, 4, 19, -45),
    ),
    'cross': (
        (0, 0, 4, 20, 45),
        (0, 0, 4, 20, -45),
    ),
    'flag': (
        (-6, 0, 3, 22, 0),
        (2, 5, 13, 10, 0),
    ),
    'dots': (
        (-9, 0, 5, 5, 0, 'c'),
        (0, 0, 5, 5, 0, 'c'),
        (9, 0, 5, 5, 0, 'c'),
    ),
}


class Button:
    TONES = {
        'gray': ((0.27, 0.26, 0.24), (0.36, 0.35, 0.33), (0.15, 0.14, 0.13)),
        'green': ((0.51, 0.71, 0.27), (0.58, 0.78, 0.34), (0.27, 0.45, 0.14)),
        'off': ((0.2, 0.19, 0.18), (0.2, 0.19, 0.18), (0.13, 0.12, 0.11)),
    }
    ICON = (0.95, 0.95, 0.93)
    H = 44

    def __init__(self, x, y, w, icon, label, call, tone='gray',
                 enabled=True, owner=None, h=None):
        self.x, self.y, self.w, self.h = x, y, w, h or self.H
        self.call = call
        self.enabled = enabled
        self.owner = owner
        self.hover = False
        self.tone = tone
        self.nodes = []
        self.face, self.lit, shade = self.TONES[tone if enabled else 'off']
        white = bs.gettexture('white')
        circle = gettexture('circle')
        tint = self.ICON if enabled else (0.5, 0.5, 0.48)
        self.shade = self.rect(white, x, y, w, self.h, shade)
        self.back = self.rect(white, x, y + 2, w, self.h - 4, self.face)
        ix = x - w / 2 + 19 if label else x
        if icon == 'half':
            self.text(ix, y + 2, '\u00bd', 1.2, 'center', tint)
        else:
            for sx, sy, sw, sh, rot, *kind in ICON_SHAPES[icon]:
                self.rect(
                    circle if kind else white,
                    ix + sx, y + 2 + sy, sw, sh, tint, rot)
        if label:
            self.text(x - w / 2 + 33, y + 2, label, 0.62, 'left', tint)

    def rect(self, texture, x, y, w, h, color, rot=0):
        node = bs.newnode(
            'image',
            attrs={
                'texture': texture,
                'absolute_scale': True,
                'attach': 'center',
                'position': (x, y),
                'scale': (w, h),
                'rotate': rot,
                'color': color,
                'opacity': 1.0,
            }
        )
        self.nodes.append(node)
        return node

    def text(self, x, y, text, scale, align, color):
        self.nodes.append(bs.newnode(
            'text',
            attrs={
                'text': text,
                'scale': scale,
                'h_attach': 'center',
                'v_attach': 'center',
                'h_align': align,
                'v_align': 'center',
                'position': (x, y),
                'color': color,
            }
        ))

    def contains(self, x, y):
        return abs(x - self.x) <= self.w / 2 and abs(y - self.y) <= self.h / 2

    def allows(self, side):
        return self.enabled and self.owner in (None, side)

    def retone(self, tone):
        if tone == self.tone:
            return
        self.tone = tone
        self.face, self.lit, shade = self.TONES[tone if self.enabled else 'off']
        self.shade.color = shade
        self.back.color = self.lit if self.hover else self.face

    def paint(self, hover):
        hover = bool(hover and self.enabled)
        if hover != self.hover:
            self.hover = hover
            self.back.color = self.lit if hover else self.face

    def destroy(self):
        for node in self.nodes:
            node.delete()
        self.nodes = []


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
    XLIM = 280
    YLIM = 330

    def __init__(self, player):
        color = player.team.color
        self.color = color
        self.sq = None
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
                'front': True,
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
                'front': True,
                'scale': (self.width, self.HEIGHT),
                'color': (0.0, 0.0, 0.0),
                'opacity': 0.6,
            }
        )
        self.label = bs.newnode(
            'text',
            attrs={
                'text': name,
                'front': True,
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

    def on_board(self):
        lim = Chessboard.DIM * Chessboard.TILE / 2
        return abs(self.x) <= lim and abs(self.y) <= lim

    def frame(self):
        sq = self.sq = self.square()
        self.board = self.on_board()
        opacity = 0.9 if self.board else 0.0
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
            node.opacity = opacity

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
        self.x = max(-self.XLIM, min(self.XLIM, self.x + self.vx * dt))
        self.y = max(-self.YLIM, min(self.YLIM, self.y + self.vy * dt))
        self.place()
        if self.square() != self.sq or self.on_board() != self.board:
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
    for node in (chooser._text_node, getattr(chooser, 'icon', None)):
        if node:
            node.front = True


SCREEN_H = 720.0


def slot(chooser, y):
    return -SCREEN_H - y if chooser._selected_team_index == 0 else y


def move(chooser, node, x, y):
    target = (x, slot(chooser, y))
    if chooser._inited:
        bs.animate_array(
            node, 'position', 2, {0: node.position, 0.1: target})
    else:
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
    player = chooser.sessionplayer
    for press, what, value in (
        (bs.InputType.UP_PRESS, 'team', 1),
        (bs.InputType.DOWN_PRESS, 'team', -1),
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


def play_sound(name):
    try:
        bs.getsound(name).play()
    except Exception:
        pass


def clock_text(seconds):
    if seconds < 10:
        return f'{seconds:.1f}'
    seconds = int(seconds)
    return f'{seconds // 60}:{seconds % 60:02d}'


# ba_meta export bascenev1.GameActivity
class Chess(bs.TeamGameActivity[Player, Team]):
    name = Strings.CHESS
    description = Strings.DESCRIPTION

    HINT = (0.5, 0.5, 0.5)
    MARK = (1.0, 0.95, 0.0)
    TILE_BG = (0.93, 0.93, 0.93)
    TILE_HOVER = (0.62, 0.78, 1.0)
    DRAG_DIST = 8
    OUTRO = 7.0

    @classmethod
    def supports_session_type(cls, sessiontype):
        return True

    @classmethod
    def get_supported_maps(cls, sessiontype):
        return ['Chessboard']

    @classmethod
    def get_available_settings(cls, sessiontype):
        return [
            bs.IntChoiceSetting(
                'Clock',
                choices=[
                    ('Off', 0),
                    ('1 Minute', 60),
                    ('3 Minutes', 180),
                    ('5 Minutes', 300),
                    ('10 Minutes', 600),
                    ('15 Minutes', 900),
                    ('30 Minutes', 1800),
                ],
                default=0,
            ),
            bs.IntChoiceSetting(
                'Increment',
                choices=[
                    ('None', 0),
                    ('1 Second', 1),
                    ('2 Seconds', 2),
                    ('3 Seconds', 3),
                    ('5 Seconds', 5),
                    ('10 Seconds', 10),
                ],
                default=0,
            ),
        ]

    def get_instance_description_short(self):
        return Strings.INSTANCE_DESCRIPTION_SHORT

    def __init__(self, settings):
        super().__init__(settings)
        self.default_music = bs.MusicType.GRAND_ROMP
        self.base = int(settings.get('Clock', 0))
        self.bonus = int(settings.get('Increment', 0))
        self.infos = []
        self.pieces = []
        self.at = {}
        self.game = Game()
        self.sel = None
        self.drag = None
        self.press = None
        self.menu = None
        self.dots = []
        self.menu_buttons = []
        self.menu_nodes = []
        self.legend_cancel = []
        self.cancel_on = False
        self.promo = None
        self.hints = []
        self.busy = False
        self.over = False
        self.offer = None
        self.clocks = {WHITE: float(self.base), BLACK: float(self.base)}
        self.running = False
        self.clock_t = 0.0
        self.last_clock = 0.0
        self.banner = []
        self.panel = []

    def spawn_player(self, player):
        return None

    def _show_info(self) -> None:
        pass

    def _show_tip(self) -> None:
        pass

    def on_transition_in(self):
        super().on_transition_in()
        self.game = Game()
        self.pieces = setup_pieces()
        self.at = {(p.col, p.row): p for p in self.pieces}
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
        self.close_picker()
        self.clear_hints()
        self.hide_banner()
        for button in self.dots + self.menu_buttons:
            button.destroy()
        self.dots.clear()
        self.menu_buttons.clear()
        for node in self.menu_nodes:
            node.delete()
        self.menu_nodes.clear()
        for info in self.infos:
            info.destroy()
        self.infos.clear()
        for node in self.panel:
            node.delete()
        self.panel.clear()
        for piece in self.pieces:
            piece.destroy()
        self.pieces.clear()
        self.at.clear()

    def on_begin(self):
        super().on_begin()
        cap_players(self.session)
        for sessionplayer in list(self.session.sessionplayers)[2:]:
            sessionplayer.remove_from_game()
        self.last = bs.time()
        self.infos = [PlayerInfo(team, bool(self.base)) for team in self.teams]
        self.build_legend()
        self.dots = [
            Button(info.dots_x, info.y, PlayerInfo.DOTS_W, 'dots', None,
                   self.toggle_menu, owner=info.side, h=34)
            for info in self.infos]
        self.refresh_infos()
        self.refresh_clocks(self.last)
        self.refresh_menu()
        self.timer = bs.Timer(0.005, bs.WeakCallStrict(self.tick), repeat=True)
        self.info_timer = bs.Timer(
            0.2, bs.WeakCallStrict(self.refresh_infos), repeat=True)

    def build_legend(self):
        purple = (0.40, 0.23, 0.72)
        light = (0.75, 0.50, 0.95)
        rows = (
            (50, 'nub', purple, Strings.MOVE, light),
            (0, 'button_punch', (1.0, 1.0, 0.4), Strings.CLICK,
             (1.0, 1.0, 0.4)),
            (-50, 'button_bomb', (1.0, 0.2, 0.2), Strings.CANCEL,
             (1.0, 0.3, 0.3)),
        )
        shown = []
        for y, tex, color, text, tcolor in rows:
            nodes = []
            sizes = ((46, purple), (22, light)) if tex == 'nub' else (
                (46, color),)
            for size, tint in sizes:
                nodes.append(bs.newnode(
                    'image',
                    attrs={
                        'texture': gettexture(tex),
                        'absolute_scale': True,
                        'attach': 'centerLeft',
                        'position': (30, y),
                        'scale': (size, size),
                        'color': tint,
                        'opacity': 0.0,
                    }
                ))
            nodes.append(bs.newnode(
                'text',
                attrs={
                    'text': text,
                    'h_attach': 'left',
                    'v_attach': 'center',
                    'position': (62, y),
                    'v_align': 'center',
                    'color': tcolor,
                    'opacity': 0.0,
                }
            ))
            self.panel.extend(nodes)
            if tex == 'button_bomb':
                self.legend_cancel = nodes
            else:
                shown.extend(nodes)
        for node in shown:
            bs.animate(node, 'opacity', {0.0: 0.0, 0.25: 0.8})

    def refresh_legend(self):
        want = bool(
            not self.over and (
                self.sel is not None or self.drag or self.press
                or self.promo or self.menu))
        if want == self.cancel_on:
            return
        self.cancel_on = want
        for node in self.legend_cancel:
            bs.animate(
                node, 'opacity',
                {0.0: node.opacity, 0.2: 0.8 if want else 0.0})

    def on_player_join(self, player):
        super().on_player_join(player)
        cursor = player.cursor = Cursor(player)
        wcp = bs.WeakCallPartial
        player.assigninput(bs.InputType.LEFT_RIGHT, wcp(cursor.on_left_right))
        player.assigninput(bs.InputType.UP_DOWN, wcp(cursor.on_up_down))
        player.assigninput(bs.InputType.PUNCH_PRESS, wcp(self.on_punch, player))
        player.assigninput(
            bs.InputType.PUNCH_RELEASE, wcp(self.on_release, player))
        player.assigninput(bs.InputType.BOMB_PRESS, wcp(self.on_bomb, player))

    def on_player_leave(self, player):
        if self.drag and self.drag['player'] is player:
            self.cancel_drag()
        if self.press and self.press['player'] is player:
            self.press = None
        if self.promo and self.promo['player'] is player:
            self.cancel_picker()
        if player.cursor:
            player.cursor.destroy()
            player.cursor = None
        super().on_player_leave(player)

    def debug_solo(self):
        return DEBUG and len(self.players) < 2

    def side_of(self, player):
        if self.debug_solo():
            return self.game.turn
        return side_of_team(player.team)

    def can_act(self, player):
        return (
            not self.over and not self.busy and player.cursor is not None
            and self.side_of(player) == self.game.turn)

    def on_punch(self, player):
        cursor = player.cursor
        if self.over or cursor is None:
            return
        side = self.side_of(player)
        button = self.button_at(cursor)
        if button:
            if button.allows(side):
                button.call(player)
            return
        if self.menu and self.menu['side'] == side:
            self.menu = None
            self.refresh_menu()
        if not cursor.on_board():
            if self.promo and self.promo['player'] is player:
                self.cancel_picker()
            return
        if not self.can_act(player) or self.drag or self.press:
            return
        sq = cursor.square()
        if self.promo:
            self.pick_promotion(player, sq)
            return
        game = self.game
        piece = self.at.get(sq)
        mine = piece is not None and piece.side == game.turn
        if self.sel is not None:
            cands = [m for m in game.moves_from(self.sel) if m.to == sq]
            if cands:
                if cands[0].promo:
                    self.open_picker(cands, self.at[self.sel], player, False)
                else:
                    self.commit(cands[0])
                return
            if mine:
                if sq == self.sel:
                    self.arm(player, piece, True)
                else:
                    self.select(sq)
                    self.arm(player, piece, False)
                return
            self.deselect()
            return
        if mine:
            self.select(sq)
            self.arm(player, piece, False)

    def arm(self, player, piece, reclick):
        cursor = player.cursor
        self.press = {
            'player': player, 'piece': piece, 'reclick': reclick,
            'origin': (piece.col, piece.row), 'x': cursor.x, 'y': cursor.y,
        }

    def on_release(self, player):
        press = self.press
        if press and press['player'] is player:
            self.press = None
            if press['reclick']:
                self.deselect()
            return
        drag = self.drag
        if not drag or drag['player'] is not player:
            return
        self.drag = None
        piece, origin = drag['piece'], drag['origin']
        piece.zoom = 1.0
        piece.dirty = True
        cursor = player.cursor
        sq = cursor.square() if cursor and cursor.on_board() else None
        if sq is None:
            piece.glide(origin[0], origin[1], 0.15)
            return
        if sq == origin:
            piece.glide(origin[0], origin[1], 0.08)
            return
        cands = [m for m in self.game.moves_from(origin) if m.to == sq]
        if not cands:
            piece.glide(origin[0], origin[1], 0.15)
            return
        if cands[0].promo:
            self.open_picker(cands, piece, player, True)
        else:
            piece.snap(sq[0], sq[1])
            self.commit(cands[0], glide=False)

    def on_bomb(self, player):
        side = self.side_of(player)
        if self.promo and self.promo['player'] is player:
            self.cancel_picker()
        elif self.drag and self.drag['player'] is player:
            self.cancel_drag()
            self.deselect()
        elif self.press and self.press['player'] is player:
            self.press = None
            self.deselect()
        elif self.menu and self.menu['side'] == side:
            self.menu = None
            self.refresh_menu()
        elif self.sel is not None and side == self.game.turn:
            self.deselect()

    def select(self, sq):
        self.sel = sq
        self.refresh_marks()
        self.show_hints(sq)

    def deselect(self):
        self.sel = None
        self.clear_hints()
        self.refresh_marks()

    def begin_drag(self, player, piece, reclick):
        self.drag = {
            'player': player, 'piece': piece,
            'origin': (piece.col, piece.row), 'reclick': reclick,
        }
        piece.lift()
        piece.zoom = 1.15
        cursor = player.cursor
        piece.x, piece.y = cursor.x, cursor.y
        piece.dirty = True

    def cancel_drag(self):
        drag = self.drag
        if not drag:
            return
        self.drag = None
        piece = drag['piece']
        piece.zoom = 1.0
        piece.glide(drag['origin'][0], drag['origin'][1], 0.12)

    def clear_hints(self):
        for node in self.hints:
            node.delete()
        self.hints.clear()

    def show_hints(self, sq):
        self.clear_hints()
        circle = gettexture('circle')
        tile = Chessboard.TILE
        seen = set()
        for m in self.game.moves_from(sq):
            if m.to in seen:
                continue
            seen.add(m.to)
            cx, cy = Chessboard.square_offset(*m.to)
            if m.to in self.at or m.flag == 'ep':
                count, radius, size = 24, tile * 0.44, tile * 0.1
                for i in range(count):
                    a = 2 * pi * i / count
                    self.hints.append(self.dot(
                        circle, cx + cos(a) * radius,
                        cy + sin(a) * radius, size))
            else:
                self.hints.append(self.dot(circle, cx, cy, tile * 0.3))

    def dot(self, circle, x, y, size):
        return bs.newnode(
            'image',
            attrs={
                'texture': circle,
                'absolute_scale': True,
                'attach': 'center',
                'position': (x, y),
                'scale': (size, size),
                'color': self.HINT,
                'opacity': 0.8,
            }
        )

    def refresh_marks(self):
        marks = self.map.marks
        for node in marks.values():
            node.opacity = 0.0
        last = self.game.last
        if last:
            for sq in (last.frm, last.to):
                marks[sq].color = self.MARK
                marks[sq].opacity = 0.4
        if self.sel is not None:
            marks[self.sel].color = self.MARK
            marks[self.sel].opacity = 0.65

    def refresh_check(self):
        pos = self.game.pos
        for side, node in self.map.glow.items():
            ksq = pos.king_square(side) if pos.in_check(side) else None
            if ksq:
                node.position = Chessboard.square_offset(*ksq)
                node.opacity = 0.95
            else:
                node.opacity = 0.0

    def commit(self, move, glide=True):
        game = self.game
        side = game.turn
        self.drag = None
        self.press = None
        self.menu = None
        self.sel = None
        self.clear_hints()
        self.clock_move(side)
        piece = self.at.pop(move.frm)
        info = game.play(move)
        victim = self.at.pop(info['cap_sq'], None)
        rook = rook_to = None
        if move.flag == 'castle':
            row = move.frm[1]
            kingside = move.to[0] == 6
            rook = self.at.pop((7 if kingside else 0, row))
            rook_to = (5 if kingside else 3, row)
            self.at[rook_to] = rook
        self.at[move.to] = piece
        if self.offer and self.offer != side:
            self.offer = None
        self.refresh_menu()
        self.busy = True
        piece.zoom = 1.0
        done = partial(self.landed, piece, victim, move, info)
        if glide:
            piece.lift()
            piece.glide(move.to[0], move.to[1], None, done)
        else:
            piece.snap(*move.to)
            done()
        if rook:
            rook.lift()
            rook.glide(rook_to[0], rook_to[1])

    def landed(self, piece, victim, move, info):
        self.busy = False
        if victim:
            victim.vanish()
        if move.promo:
            piece.set_kind(move.promo)
        self.pieces = [p for p in self.pieces if not p.dead]
        self.refresh_marks()
        self.refresh_check()
        self.refresh_infos()
        if self.game.result:
            self.finish()
        elif info['check']:
            play_sound('dingSmallHigh')
        elif victim:
            play_sound('powerup01')
        else:
            play_sound('deek')
            if move.flag == 'castle':
                play_sound('deek')

    def open_picker(self, cands, piece, player, dropped):
        self.clear_hints()
        to = cands[0].to
        origin = (piece.col, piece.row)
        if dropped:
            piece.snap(to[0], to[1])
        piece.zoom = 1.0
        piece.set_alpha(0.0)
        white = bs.gettexture('white')
        side = piece.side
        step = -1 if side == WHITE else 1
        size = Chessboard.DIM * Chessboard.TILE
        nodes = [bs.newnode(
            'image',
            attrs={
                'texture': white,
                'absolute_scale': True,
                'attach': 'center',
                'position': (0, 0),
                'scale': (size, size),
                'color': (0.0, 0.0, 0.0),
                'opacity': 0.5,
            }
        )]
        tiles, shown = [], []
        for i, kind in enumerate(PROMOTIONS):
            row = to[1] + step * i
            x, y = Chessboard.square_offset(to[0], row)
            bg = bs.newnode(
                'image',
                attrs={
                    'texture': white,
                    'absolute_scale': True,
                    'attach': 'center',
                    'position': (x, y),
                    'scale': (Chessboard.TILE, Chessboard.TILE),
                    'color': self.TILE_BG,
                    'opacity': 1.0,
                }
            )
            nodes.append(bg)
            tiles.append((row, kind, bg))
            shown.append(Piece(kind, side, to[0], row))
        self.promo = {
            'player': player, 'piece': piece, 'to': to, 'origin': origin,
            'moves': {m.promo: m for m in cands}, 'nodes': nodes,
            'tiles': tiles, 'shown': shown, 'hover': None,
        }

    def close_picker(self):
        promo, self.promo = self.promo, None
        if not promo:
            return
        for node in promo['nodes']:
            node.delete()
        for piece in promo['shown']:
            piece.destroy()

    def pick_promotion(self, player, sq):
        promo = self.promo
        for row, kind, _ in promo['tiles']:
            if sq == (promo['to'][0], row):
                move = promo['moves'][kind]
                piece = promo['piece']
                self.close_picker()
                piece.set_alpha(1.0)
                piece.snap(*move.to)
                self.commit(move, glide=False)
                return
        self.cancel_picker()

    def cancel_picker(self):
        promo = self.promo
        if not promo:
            return
        piece = promo['piece']
        self.close_picker()
        piece.set_alpha(1.0)
        piece.glide(promo['origin'][0], promo['origin'][1], 0.12)
        if self.sel is not None and not self.over:
            self.show_hints(self.sel)

    def refresh_picker(self):
        promo = self.promo
        cursor = promo['player'].cursor if promo['player'].exists() else None
        hover = cursor.square() if cursor else None
        if hover == promo['hover']:
            return
        promo['hover'] = hover
        for row, kind, bg in promo['tiles']:
            bg.color = (
                self.TILE_HOVER if hover == (promo['to'][0], row)
                else self.TILE_BG)

    MENU_W = 152

    def button_at(self, cursor):
        for button in self.menu_buttons + self.dots:
            if button.contains(cursor.x, cursor.y):
                return button
        return None

    def toggle_menu(self, player):
        side = self.side_of(player)
        if self.menu and self.menu['side'] == side:
            self.menu = None
        else:
            self.menu = {'side': side, 'view': 'main'}
        play_sound('tick')
        self.refresh_menu()

    def set_view(self, view, player):
        menu = self.menu
        if menu and menu['side'] == self.side_of(player):
            menu['view'] = view
            self.refresh_menu()

    def confirm(self, player):
        menu = self.menu
        side = self.side_of(player)
        if self.over or not menu or menu['side'] != side:
            return
        if menu['view'] == 'resign':
            self.menu = None
            self.game.resign(side)
            self.finish()
        elif menu['view'] == 'draw' and self.offer is None:
            self.offer = side
            self.menu = {'side': opponent(side), 'view': 'main'}
            play_sound('tick')
            self.refresh_menu()

    def answer_draw(self, player, accept):
        side = self.side_of(player)
        if self.over or self.offer != opponent(side):
            return
        self.offer = None
        self.menu = None
        if accept:
            self.game.agree_draw()
            self.finish()
        else:
            self.refresh_menu()

    def menu_rect(self, x, y, w, h, color):
        self.menu_nodes.append(bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('white'),
                'absolute_scale': True,
                'attach': 'center',
                'position': (x, y),
                'scale': (w, h),
                'color': color,
                'opacity': 1.0,
            }
        ))

    def refresh_menu(self):
        for button in self.menu_buttons:
            button.destroy()
        self.menu_buttons = []
        for node in self.menu_nodes:
            node.delete()
        self.menu_nodes = []
        menu = self.menu
        for dots in self.dots:
            pending = self.offer == opponent(dots.owner) and not self.over
            dots.retone('green' if pending else 'gray')
        if self.over or not menu:
            return
        side = menu['side']
        info = next((i for i in self.infos if i.side == side), None)
        if info is None:
            return
        pad, gap, tall = 6, 4, Button.H
        inner = self.MENU_W - pad * 2
        offer = self.offer
        confirming = menu['view'] != 'main'
        if confirming:
            heights = [22, tall]
        else:
            count = 3 if offer == opponent(side) else 2
            heights = [tall] * count
        total = sum(heights) + gap * (len(heights) - 1) + pad * 2
        sign = -1 if side == BLACK else 1
        edge = info.y + sign * (PlayerInfo.HEIGHT / 2 + 4)
        center = edge + sign * total / 2
        half = Chessboard.DIM * Chessboard.TILE / 2 + Chessboard.PAD
        mx = half - self.MENU_W / 2
        self.menu_rect(mx, center, self.MENU_W + 4, total + 4,
                       (0.32, 0.31, 0.29))
        self.menu_rect(mx, center, self.MENU_W, total, (0.15, 0.145, 0.13))
        y = center + total / 2 - pad
        make = partial(Button, owner=side)
        if confirming:
            self.menu_nodes.append(bs.newnode(
                'text',
                attrs={
                    'text': (Strings.RESIGN_Q if menu['view'] == 'resign'
                             else Strings.OFFER_Q),
                    'scale': 0.62,
                    'h_attach': 'center',
                    'v_attach': 'center',
                    'h_align': 'center',
                    'v_align': 'center',
                    'position': (mx, y - 11),
                    'color': (0.85, 0.85, 0.82),
                }
            ))
            y -= 22 + gap
            bw = (inner - 6) / 2
            self.menu_buttons += [
                make(mx - inner / 2 + bw / 2, y - tall / 2, bw,
                     'check', None, self.confirm, tone='green'),
                make(mx + inner / 2 - bw / 2, y - tall / 2, bw,
                     'cross', None, partial(self.set_view, 'main')),
            ]
            return
        if offer == opponent(side):
            items = [
                ('check', Strings.ACCEPT,
                 partial(self.answer_draw, accept=True), 'green', True),
                ('cross', Strings.DECLINE,
                 partial(self.answer_draw, accept=False), 'gray', True),
            ]
        else:
            items = [(
                'half', Strings.OFFERED if offer else Strings.OFFER_BTN,
                partial(self.set_view, 'draw'), 'gray', offer is None)]
        items.append((
            'flag', Strings.RESIGN_BTN,
            partial(self.set_view, 'resign'), 'gray', True))
        for icon, label, call, tone, enabled in items:
            self.menu_buttons.append(make(
                mx, y - tall / 2, inner, icon, label, call,
                tone=tone, enabled=enabled))
            y -= tall + gap

    def remaining(self, side, now):
        left = self.clocks[side]
        if self.running and side == self.game.turn:
            left -= now - self.clock_t
        return max(0.0, left)

    def clock_move(self, side):
        if not self.base:
            return
        now = bs.time()
        if self.running:
            self.clocks[side] = self.remaining(side, now) + self.bonus
        self.running = self.game.plies + 1 >= 2
        self.clock_t = now

    def refresh_clocks(self, now):
        if not self.base:
            return
        turn = self.game.turn
        for info in self.infos:
            left = self.remaining(info.side, now)
            info.set_clock(
                clock_text(left),
                self.running and not self.over and info.side == turn,
                left < 20)

    def refresh_infos(self):
        pos = self.game.pos
        dummy = self.debug_solo()
        for info in self.infos:
            info.dummy = dummy
            info.refresh()
            diff = pos.material(info.side) - pos.material(
                opponent(info.side))
            info.set_advantage(diff)
            info.set_turn(info.side == pos.turn and not self.over)

    def tick(self):
        now = bs.time()
        dt = min(now - self.last, 0.1)
        if dt <= 0:
            return
        self.last = now
        for player in self.players:
            if player.cursor:
                player.cursor.step(dt)
        press = self.press
        if press and not self.drag:
            cursor = press['player'].cursor
            if cursor is None:
                self.press = None
            elif hypot(cursor.x - press['x'],
                       cursor.y - press['y']) >= self.DRAG_DIST:
                self.press = None
                self.begin_drag(
                    press['player'], press['piece'], press['reclick'])
        self.refresh_legend()
        for button in self.menu_buttons + self.dots:
            button.paint(any(
                p.cursor and button.allows(self.side_of(p))
                and button.contains(p.cursor.x, p.cursor.y)
                for p in self.players))
        drag = self.drag
        if drag:
            cursor = drag['player'].cursor
            if cursor:
                piece = drag['piece']
                piece.x, piece.y = cursor.x, cursor.y
                piece.dirty = True
        for piece in list(self.pieces):
            if piece.active:
                piece.update(now)
        if self.promo:
            self.refresh_picker()
        if now - self.last_clock >= 0.1:
            self.last_clock = now
            self.refresh_clocks(now)
            if (self.base and self.running and not self.over
                    and not self.busy
                    and self.remaining(self.game.turn, now) <= 0):
                self.game.timeout(self.game.turn)
                self.finish()

    def finish(self):
        if self.over:
            return
        self.over = True
        self.running = False
        self.offer = None
        self.menu = None
        self.press = None
        self.cancel_drag()
        if self.promo:
            self.cancel_picker()
        self.clear_hints()
        self.refresh_menu()
        for info in self.infos:
            info.set_turn(False)
        self.refresh_clocks(bs.time())
        winner, reason = self.game.result
        title = (
            Strings.WINS.format(side=Strings.SIDE[winner]) if winner
            else Strings.DRAW)
        sub = Strings.REASONS.get(reason, reason)
        white = bs.gettexture('white')
        head = (0.51, 0.71, 0.27) if winner else (0.45, 0.44, 0.42)
        self.banner = []
        for pos, size, color in (
                ((0, 0), (440, 140), (0.15, 0.145, 0.13)),
                ((0, 40), (440, 60), head)):
            self.banner.append(bs.newnode(
                'image',
                attrs={
                    'texture': white,
                    'absolute_scale': True,
                    'attach': 'center',
                    'position': pos,
                    'scale': size,
                    'color': color,
                    'opacity': 1.0,
                    'front': True,
                }
            ))
        for text, y, scale, color in (
                (title, 40, 1.3, (1.0, 1.0, 1.0)),
                (sub, -22, 0.9, (0.85, 0.85, 0.82))):
            self.banner.append(bs.newnode(
                'text',
                attrs={
                    'text': text,
                    'scale': scale,
                    'h_attach': 'center',
                    'v_attach': 'center',
                    'h_align': 'center',
                    'v_align': 'center',
                    'position': (0, y),
                    'color': color,
                    'front': True,
                }
            ))
        play_sound('gong')
        self.banner_timer = bs.Timer(3.0, bs.WeakCallStrict(self.hide_banner))
        self.end_timer = bs.Timer(
            self.OUTRO, bs.WeakCallStrict(self.conclude))

    def hide_banner(self):
        for node in self.banner:
            node.delete()
        self.banner = []

    def conclude(self):
        winner = self.game.result[0] if self.game.result else None
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(
                team, 1 if side_of_team(team) == winner else 0)
        self.end(results=results, announce_winning_team=False)


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

