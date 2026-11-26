# Copyright (c) 2026 BroBordd
# https://github.com/BroBordd
"""Test Chess.

3D chess on a green field. Every piece is a vector shape (lathe profile
or extruded polygon) baked at runtime into its own collision mesh and
display mesh, written to disk, loaded, then deleted. Moving a piece
bakes it again at its new square.

Walk onto a square. Punch selects a piece or confirms a move, pick up
cancels. Team 1 plays white, team 2 plays black.
"""

# ba_meta require api 9

from __future__ import annotations

import math
import os
import random
import struct
from typing import TYPE_CHECKING, override

import babase
import bascenev1 as bs
from bascenev1 import _commonassets
from bauiv1 import _classiccatalogassets as uicatalogassets
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any

    from bacommon.assetspec import TextureSpec

CLEANUP_DELAY = 20.0
COB_FILE_ID = 13467
BOB_FILE_ID = 45623
BOB_FORMAT_INDEX16 = 1

SQUARE = 3.5
BOARD_TOP = 0.3
FRAME = 1.6
SEGMENTS = 12
SKY_HALF = 400.0
SKY_COLOR = (0.45, 0.72, 1.0)

COLORS = {
    'ground': (0.25, 0.6, 0.2),
    'light': (0.92, 0.87, 0.72),
    'dark': (0.38, 0.22, 0.12),
    'frame': (0.22, 0.13, 0.07),
    'white': (0.94, 0.91, 0.82),
    'black': (0.14, 0.12, 0.12),
}
OUTLINE = 0.09
PIECE_Y = 0.3 + OUTLINE + 0.02
OUTLINE_COLORS = {'white': (0.02, 0.02, 0.02), 'black': (0.97, 0.97, 0.97)}
LIFT = 5.6
SELECT_COLOR = (1.0, 0.9, 0.1)
MOVE_COLOR = (0.2, 0.9, 0.3)
CAPTURE_COLOR = (1.0, 0.25, 0.2)

PROFILES = {
    'p': [(0, 0), (1.05, 0), (1.05, 0.25), (0.8, 0.4), (0.5, 0.8),
          (0.35, 1.2), (0.6, 1.25), (0.6, 1.4), (0.35, 1.5), (0.55, 1.7),
          (0.6, 1.95), (0.45, 2.2), (0.2, 2.35), (0, 2.4)],
    'r': [(0, 0), (1.2, 0), (1.2, 0.3), (0.95, 0.5), (0.8, 0.7),
          (0.75, 1.8), (0.95, 1.9), (0.95, 2.5), (0, 2.5)],
    'b': [(0, 0), (1.1, 0), (1.1, 0.3), (0.85, 0.5), (0.5, 1.0),
          (0.4, 1.5), (0.7, 1.6), (0.7, 1.75), (0.45, 1.9), (0.65, 2.4),
          (0.6, 2.8), (0.3, 3.2), (0.25, 3.3), (0.3, 3.4), (0, 3.55)],
    'q': [(0, 0), (1.2, 0), (1.2, 0.3), (0.9, 0.5), (0.55, 1.1),
          (0.45, 2.0), (0.8, 2.1), (0.8, 2.3), (0.5, 2.4), (0.9, 3.0),
          (1.0, 3.5), (0.85, 3.6), (0, 3.6)],
    'k': [(0, 0), (1.2, 0), (1.2, 0.3), (0.9, 0.5), (0.55, 1.1),
          (0.5, 2.2), (0.85, 2.3), (0.85, 2.5), (0.55, 2.6), (0.9, 3.2),
          (0.8, 3.8), (0, 3.8)],
    'n': [(0, 0), (1.15, 0), (1.15, 0.3), (0.9, 0.5), (0.8, 0.7),
          (0, 0.7)],
}
KNIGHT_NECK = [(-0.5, 0.7), (0.5, 0.7), (0.45, 1.8), (-0.1, 2.3)]
KNIGHT_HEAD = [(-0.1, 2.3), (0.45, 1.8), (1.15, 1.85), (1.15, 2.2),
               (0.3, 3.0), (-0.2, 3.0)]

START_ROWS = ['RNBQKBNR', 'P' * 8, '.' * 8, '.' * 8, '.' * 8, '.' * 8,
              'p' * 8, 'rnbqkbnr']
KNIGHT_STEPS = [(1, 2), (2, 1), (-1, 2), (-2, 1),
                (1, -2), (2, -1), (-1, -2), (-2, -1)]
KING_STEPS = [(1, 0), (-1, 0), (0, 1), (0, -1),
              (1, 1), (1, -1), (-1, 1), (-1, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
RIGHTS_LOST = {
    4: 'KQ', 7: 'K', 0: 'Q', 60: 'kq', 63: 'k', 56: 'q',
}

Move = tuple[int, int, str | None]


class Position:
    def __init__(
        self,
        board: list[str] | None = None,
        white: bool = True,
        rights: str = 'KQkq',
        ep: int | None = None,
    ) -> None:
        if board is None:
            board = [c for row in START_ROWS for c in row]
        self.board = board
        self.white = white
        self.rights = rights
        self.ep = ep

    def attacked(self, sq: int, by_white: bool) -> bool:
        f, r = sq & 7, sq >> 3
        b = self.board
        pawn, knight, bishop, rook, queen, king = (
            'PNBRQK' if by_white else 'pnbrqk'
        )
        pr = r - 1 if by_white else r + 1
        if 0 <= pr < 8:
            for df in (-1, 1):
                if 0 <= f + df < 8 and b[pr * 8 + f + df] == pawn:
                    return True
        for steps, piece in ((KNIGHT_STEPS, knight), (KING_STEPS, king)):
            for df, dr in steps:
                cf, cr = f + df, r + dr
                if 0 <= cf < 8 and 0 <= cr < 8 and b[cr * 8 + cf] == piece:
                    return True
        for dirs, kinds in (
            (BISHOP_DIRS, (bishop, queen)),
            (ROOK_DIRS, (rook, queen)),
        ):
            for df, dr in dirs:
                cf, cr = f + df, r + dr
                while 0 <= cf < 8 and 0 <= cr < 8:
                    p = b[cr * 8 + cf]
                    if p != '.':
                        if p in kinds:
                            return True
                        break
                    cf += df
                    cr += dr
        return False

    def in_check(self) -> bool:
        king = 'K' if self.white else 'k'
        return self.attacked(self.board.index(king), not self.white)

    def _own(self, p: str) -> bool:
        return p != '.' and p.isupper() == self.white

    def pseudo_moves(self) -> list[Move]:
        b = self.board
        out: list[Move] = []
        for sq in range(64):
            p = b[sq]
            if not self._own(p):
                continue
            f, r = sq & 7, sq >> 3
            kind = p.lower()
            if kind == 'p':
                self._pawn_moves(sq, f, r, out)
            elif kind in 'nk':
                steps = KNIGHT_STEPS if kind == 'n' else KING_STEPS
                for df, dr in steps:
                    cf, cr = f + df, r + dr
                    if 0 <= cf < 8 and 0 <= cr < 8:
                        t = cr * 8 + cf
                        if not self._own(b[t]):
                            out.append((sq, t, None))
                if kind == 'k':
                    self._castles(sq, out)
            else:
                dirs = (
                    BISHOP_DIRS if kind == 'b'
                    else ROOK_DIRS if kind == 'r'
                    else BISHOP_DIRS + ROOK_DIRS
                )
                for df, dr in dirs:
                    cf, cr = f + df, r + dr
                    while 0 <= cf < 8 and 0 <= cr < 8:
                        t = cr * 8 + cf
                        if self._own(b[t]):
                            break
                        out.append((sq, t, None))
                        if b[t] != '.':
                            break
                        cf += df
                        cr += dr
        return out

    def _pawn_moves(self, sq: int, f: int, r: int, out: list[Move]) -> None:
        b = self.board
        d = 1 if self.white else -1
        home = 1 if self.white else 6
        last = 7 if self.white else 0
        queen = 'Q' if self.white else 'q'
        nr = r + d
        if not 0 <= nr < 8:
            return
        t = nr * 8 + f
        if b[t] == '.':
            out.append((sq, t, queen if nr == last else None))
            t2 = (r + 2 * d) * 8 + f
            if r == home and b[t2] == '.':
                out.append((sq, t2, None))
        for df in (-1, 1):
            cf = f + df
            if not 0 <= cf < 8:
                continue
            t = nr * 8 + cf
            target = b[t]
            if (target != '.' and not self._own(target)) or t == self.ep:
                out.append((sq, t, queen if nr == last else None))

    def _castles(self, sq: int, out: list[Move]) -> None:
        b = self.board
        white = self.white
        base = 0 if white else 56
        if sq != base + 4:
            return
        king_right, queen_right = ('K', 'Q') if white else ('k', 'q')
        rook = 'R' if white else 'r'
        if self.attacked(sq, not white):
            return
        if (
            king_right in self.rights
            and b[base + 7] == rook
            and b[base + 5] == '.'
            and b[base + 6] == '.'
            and not self.attacked(base + 5, not white)
            and not self.attacked(base + 6, not white)
        ):
            out.append((sq, base + 6, None))
        if (
            queen_right in self.rights
            and b[base] == rook
            and b[base + 1] == '.'
            and b[base + 2] == '.'
            and b[base + 3] == '.'
            and not self.attacked(base + 3, not white)
            and not self.attacked(base + 2, not white)
        ):
            out.append((sq, base + 2, None))

    def apply(self, move: Move) -> Position:
        frm, to, promo = move
        b = self.board[:]
        p = b[frm]
        captured = b[to]
        b[frm] = '.'
        b[to] = promo if promo else p
        ep = None
        if p in 'Pp':
            if to == self.ep and captured == '.' and (frm & 7) != (to & 7):
                b[to - 8 if p == 'P' else to + 8] = '.'
            if abs(to - frm) == 16:
                ep = (frm + to) // 2
        if p in 'Kk' and abs((to & 7) - (frm & 7)) == 2:
            if to & 7 == 6:
                b[to - 1] = b[to + 1]
                b[to + 1] = '.'
            else:
                b[to + 1] = b[to - 2]
                b[to - 2] = '.'
        rights = self.rights
        for sq in (frm, to):
            for ch in RIGHTS_LOST.get(sq, ''):
                rights = rights.replace(ch, '')
        return Position(b, not self.white, rights, ep)

    def legal_moves(self) -> list[Move]:
        out = []
        for move in self.pseudo_moves():
            nxt = self.apply(move)
            king = 'K' if self.white else 'k'
            if not nxt.attacked(nxt.board.index(king), nxt.white):
                out.append(move)
        return out


def _orient(
    verts: list[list[float]], tris: list[list[int]]
) -> list[list[int]]:
    c = [sum(p[k] for p in verts) / len(verts) for k in range(3)]
    out = []
    for a, b, d in tris:
        p, q, r = verts[a], verts[b], verts[d]
        u = [q[k] - p[k] for k in range(3)]
        w = [r[k] - p[k] for k in range(3)]
        n = (
            u[1] * w[2] - u[2] * w[1],
            u[2] * w[0] - u[0] * w[2],
            u[0] * w[1] - u[1] * w[0],
        )
        m = [p[k] - c[k] for k in range(3)]
        outward = sum(n[k] * m[k] for k in range(3)) > 0
        out.append([a, b, d] if outward else [a, d, b])
    return out


def _box(
    x0: float, x1: float, y0: float, y1: float, z0: float, z1: float
) -> tuple[list[list[float]], list[list[int]]]:
    verts = [
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ]
    quads = [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5),
    ]
    tris: list[list[int]] = []
    for a, b, c, d in quads:
        tris += [[a, b, c], [a, c, d]]
    return verts, _orient(verts, tris)


def _lathe(
    profile: list[tuple[float, float]],
) -> tuple[list[list[float]], list[list[int]]]:
    verts = []
    for r, y in profile:
        for j in range(SEGMENTS):
            a = 2 * math.pi * j / SEGMENTS
            verts.append([r * math.cos(a), y, r * math.sin(a)])
    tris = []
    for i in range(len(profile) - 1):
        for j in range(SEGMENTS):
            k = (j + 1) % SEGMENTS
            a = i * SEGMENTS + j
            b = i * SEGMENTS + k
            c = (i + 1) * SEGMENTS + k
            d = (i + 1) * SEGMENTS + j
            tris += [[a, c, b], [a, d, c]]
    return verts, tris


def _prism(
    poly: list[tuple[float, float]], half: float, sign: float
) -> tuple[list[list[float]], list[list[int]]]:
    n = len(poly)
    verts = [[-half, y, sign * u] for u, y in poly]
    verts += [[half, y, sign * u] for u, y in poly]
    tris: list[list[int]] = []
    for i in range(n):
        j = (i + 1) % n
        tris += [[i, j, n + j], [i, n + j, n + i]]
    for i in range(1, n - 1):
        tris += [[0, i, i + 1], [n, n + i, n + i + 1]]
    return verts, _orient(verts, tris)


def _pyramid(
    cx: float, cy: float, cz: float, half: float, height: float
) -> tuple[list[list[float]], list[list[int]]]:
    verts = [
        [cx - half, cy, cz - half], [cx + half, cy, cz - half],
        [cx + half, cy, cz + half], [cx - half, cy, cz + half],
        [cx, cy + height, cz],
    ]
    tris = [[0, 1, 2], [0, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]
    return verts, _orient(verts, tris)


def _merge(
    parts: list[tuple[list[list[float]], list[list[int]]]],
) -> tuple[list[list[float]], list[list[int]]]:
    verts: list[list[float]] = []
    tris: list[list[int]] = []
    for pv, pt in parts:
        offset = len(verts)
        verts.extend(pv)
        tris.extend([[a + offset, b + offset, c + offset] for a, b, c in pt])
    return verts, tris


def _clean(
    verts: list[list[float]], tris: list[list[int]]
) -> tuple[list[list[float]], list[list[int]]]:
    kept = []
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        u = [q[k] - p[k] for k in range(3)]
        w = [r[k] - p[k] for k in range(3)]
        n = (
            u[1] * w[2] - u[2] * w[1],
            u[2] * w[0] - u[0] * w[2],
            u[0] * w[1] - u[1] * w[0],
        )
        if n[0] ** 2 + n[1] ** 2 + n[2] ** 2 > 1e-10:
            kept.append([a, b, c])
    return verts, kept


def square_center(sq: int) -> tuple[float, float]:
    return ((sq & 7) - 3.5) * SQUARE, (3.5 - (sq >> 3)) * SQUARE


def _outline(
    verts: list[list[float]], tris: list[list[int]]
) -> tuple[list[list[float]], list[list[int]]]:
    acc: dict[tuple[float, ...], list[float]] = {}
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        u = [q[k] - p[k] for k in range(3)]
        w = [r[k] - p[k] for k in range(3)]
        n = (
            u[1] * w[2] - u[2] * w[1],
            u[2] * w[0] - u[0] * w[2],
            u[0] * w[1] - u[1] * w[0],
        )
        for i in (a, b, c):
            total = acc.setdefault(tuple(round(x, 3) for x in verts[i]),
                                   [0.0, 0.0, 0.0])
            for k in range(3):
                total[k] += n[k]
    grown = []
    for v in verts:
        n = acc[tuple(round(x, 3) for x in v)]
        length = (n[0] ** 2 + n[1] ** 2 + n[2] ** 2) ** 0.5 or 1.0
        grown.append([v[k] + OUTLINE * n[k] / length for k in range(3)])
    return grown, [[a, c, b] for a, b, c in tris]


def build_piece(piece: str, sq: int | None = None) -> list[dict]:
    kind = piece.lower()
    white = piece.isupper()
    parts = [_lathe(PROFILES[kind])]
    if kind == 'r':
        for sx in (-1, 1):
            for sz in (-1, 1):
                cx, cz = sx * 0.62, sz * 0.62
                parts.append(_box(cx - 0.17, cx + 0.17, 2.5, 2.95,
                                  cz - 0.17, cz + 0.17))
    elif kind == 'q':
        for k in range(6):
            a = math.pi / 3 * k
            parts.append(_pyramid(0.7 * math.cos(a), 3.6,
                                  0.7 * math.sin(a), 0.2, 0.65))
    elif kind == 'k':
        parts.append(_box(-0.16, 0.16, 3.8, 4.7, -0.16, 0.16))
        parts.append(_box(-0.45, 0.45, 4.15, 4.45, -0.16, 0.16))
    elif kind == 'n':
        sign = -1.0 if white else 1.0
        parts.append(_prism(KNIGHT_NECK, 0.38, sign))
        parts.append(_prism(KNIGHT_HEAD, 0.38, sign))
    verts, tris = _clean(*_merge(parts))
    grown, flipped = _outline(verts, tris)
    if sq is None:
        cx, cz, cy = 0.0, 0.0, 0.0
    else:
        cx, cz = square_center(sq)
        cy = PIECE_Y

    def place(vs: list[list[float]]) -> list[list[float]]:
        return [[round(v[0] + cx, 4), round(v[1] + cy, 4),
                 round(v[2] + cz, 4)] for v in vs]

    side = 'white' if white else 'black'
    return [
        {'name': 'piece', 'color': list(COLORS[side]),
         'vertices': place(verts), 'triangles': tris},
        {'name': 'outline', 'color': list(OUTLINE_COLORS[side]),
         'vertices': place(grown), 'triangles': flipped, 'flip': True},
    ]


def build_marker(sq: int, ring: bool, level: int = 0) -> dict:
    cx, cz = square_center(sq)
    if ring:
        half = SQUARE / 2 - 0.1
        y0 = BOARD_TOP + 0.1 + 0.05 * level
        y1 = y0 + 0.05
        t = 0.2
        parts = [
            _box(cx - half, cx + half, y0, y1, cz - half, cz - half + t),
            _box(cx - half, cx + half, y0, y1, cz + half - t, cz + half),
            _box(cx - half, cx - half + t, y0, y1,
                 cz - half + t, cz + half - t),
            _box(cx + half - t, cx + half, y0, y1,
                 cz - half + t, cz + half - t),
        ]
    else:
        half = SQUARE / 2 - 0.3
        parts = [_box(cx - half, cx + half, BOARD_TOP, BOARD_TOP + 0.05,
                      cz - half, cz + half)]
    verts, tris = _merge(parts)
    return {
        'name': 'marker',
        'color': [1.0, 1.0, 1.0],
        'vertices': verts,
        'triangles': tris,
    }


def build_board() -> dict:
    acc: dict[str, tuple[tuple[float, ...], list, list]] = {}

    def add(name: str, color: tuple[float, ...], part: Any) -> None:
        if name not in acc:
            acc[name] = (color, [], [])
        _, verts, tris = acc[name]
        offset = len(verts)
        verts.extend(part[0])
        tris.extend([[a + offset, b + offset, c + offset]
                     for a, b, c in part[1]])

    add('ground', COLORS['ground'], _box(-80, 80, -2, 0, -80, 80))
    for sq in range(64):
        cx, cz = square_center(sq)
        dark = ((sq & 7) + (sq >> 3)) % 2 == 0
        add('dark' if dark else 'light',
            COLORS['dark' if dark else 'light'],
            _box(cx - SQUARE / 2, cx + SQUARE / 2, 0, BOARD_TOP,
                 cz - SQUARE / 2, cz + SQUARE / 2))
    h = 4 * SQUARE
    o = h + FRAME
    for part in (
        _box(-o, o, 0, BOARD_TOP, -o, -h),
        _box(-o, o, 0, BOARD_TOP, h, o),
        _box(-o, -h, 0, BOARD_TOP, -h, h),
        _box(h, o, 0, BOARD_TOP, -h, h),
    ):
        add('frame', COLORS['frame'], part)
    sv, st = _box(-SKY_HALF, SKY_HALF, -SKY_HALF, SKY_HALF,
                  -SKY_HALF, SKY_HALF)
    add('sky', SKY_COLOR, (sv, [[a, c, b] for a, b, c in st]))
    return {
        'groups': [
            {'name': n, 'color': list(c), 'vertices': v, 'triangles': t}
            for n, (c, v, t) in acc.items()
        ]
    }


GOOD_DIRS: list[str] = []


def _mesh_dirs() -> list[str]:
    dirs = []
    user = babase.app.env.python_directory_user
    if user is not None:
        dirs.append(os.path.join(user, 'meshes'))
    data = os.path.join(babase.app.env.data_directory, 'ba_data')
    dirs.append(os.path.join(data, 'meshes2'))
    dirs.append(os.path.join(data, 'meshes'))
    return GOOD_DIRS + [d for d in dirs if d not in GOOD_DIRS]


def _triangles(group: dict) -> list[tuple[tuple[float, ...], ...]]:
    verts = group['vertices']
    return [
        (tuple(verts[a]), tuple(verts[b]), tuple(verts[c]))
        for a, b, c in group['triangles']
    ]


def _normal(tri: tuple[tuple[float, ...], ...]) -> tuple[float, float, float]:
    p, q, r = tri
    u = [q[i] - p[i] for i in range(3)]
    w = [r[i] - p[i] for i in range(3)]
    n = (
        u[1] * w[2] - u[2] * w[1],
        u[2] * w[0] - u[0] * w[2],
        u[0] * w[1] - u[1] * w[0],
    )
    length = (n[0] ** 2 + n[1] ** 2 + n[2] ** 2) ** 0.5 or 1.0
    return (n[0] / length, n[1] / length, n[2] / length)


def build_cob(mesh: dict) -> bytes:
    positions: list[float] = []
    indices: list[int] = []
    for group in mesh['groups']:
        if group['name'] in ('sky', 'marker', 'outline'):
            continue
        base = len(positions) // 3
        for vert in group['vertices']:
            positions.extend(vert)
        for tri in group['triangles']:
            indices.extend(base + i for i in tri)
    out = struct.pack(
        '<III', COB_FILE_ID, len(positions) // 3, len(indices) // 3
    )
    out += struct.pack(f'<{len(positions)}f', *positions)
    out += struct.pack(f'<{len(indices)}I', *indices)
    return out


def build_bob(group: dict) -> bytes:
    verts = b''
    count = 0
    for tri in _triangles(group):
        sign = -1 if group.get('flip') else 1
        nx, ny, nz = (round(sign * c * 32767) for c in _normal(tri))
        for pos in tri:
            verts += struct.pack(
                '<3f2H3h2x', pos[0], pos[1], pos[2], 32768, 32768, nx, ny, nz
            )
            count += 1
    out = struct.pack(
        '<IIII', BOB_FILE_ID, BOB_FORMAT_INDEX16, count, count // 3
    )
    out += verts
    out += struct.pack(f'<{count}H', *range(count))
    return out


def write_assets(
    name: str, folder: str, mesh: dict, collide: bool
) -> list[str]:
    os.makedirs(folder, exist_ok=True)
    written = []
    if collide:
        path = os.path.join(folder, name + '.cob')
        with open(path, 'wb') as f:
            f.write(build_cob(mesh))
        written.append(path)
    for group in mesh['groups']:
        path = os.path.join(folder, f'{name}_{group["name"]}.bob')
        with open(path, 'wb') as f:
            f.write(build_bob(group))
        written.append(path)
    return written


def remove_assets(paths: list[str]) -> None:
    for path in paths:
        try:
            os.remove(path)
        except OSError:
            pass


def load_assets(
    name: str, mesh: dict, collide: bool = True
) -> tuple[Any, list[Any]]:
    last: Exception | None = None
    for folder in _mesh_dirs():
        paths: list[str] = []
        try:
            paths = write_assets(name, folder, mesh, collide)
            collision = bs.getcollisionmesh(name) if collide else None
            parts = [
                (
                    bs.getmesh(f'{name}_{group["name"]}'),
                    tuple(group['color']),
                    group['name'],
                )
                for group in mesh['groups']
            ]
        except (OSError, RuntimeError) as exc:
            remove_assets(paths)
            last = exc
            continue
        last = None
        GOOD_DIRS[:] = [folder]
        babase.apptimer(CLEANUP_DELAY, babase.CallStrict(remove_assets, paths))
        return collision, parts
    raise RuntimeError('no mesh directory was accepted by the engine') from last


class _Defs:
    points = {
        'spawn1': (0.0, 1.0, 19.5) + (8.0, 0.0, 1.0),
        'spawn2': (0.0, 1.0, -19.5) + (8.0, 0.0, 1.0),
        'flag_default': (0.0, 1.0, 0.0),
    }
    boxes = {
        'area_of_interest_bounds': (0.0, 2.0, 0.0) + (0.0, 0.0, 0.0)
        + (36.0, 8.0, 44.0),
        'map_bounds': (0.0, 10.0, 0.0) + (0.0, 0.0, 0.0)
        + (160.0, 60.0, 160.0),
    }


class ChessMap(bs.Map):
    defs = _Defs
    name = 'Chess Field'

    @override
    @classmethod
    def get_preview_texture_spec(cls) -> TextureSpec:
        return uicatalogassets.textures.bridgit_preview

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        return ['melee']

    @override
    @classmethod
    def on_preload(cls) -> Any:
        prefix = f'chess_{random.randrange(10**6)}'
        collision, parts = load_assets(f'{prefix}_board', build_board())
        pieces = {}
        for sq, piece in enumerate(Position().board):
            if piece != '.':
                pieces[(piece, sq)] = _load_piece(prefix, piece, sq)
        flyers = {p: _load_flyer(prefix, p) for p in 'PNBRQKpnbrqk'}
        return {
            'prefix': prefix,
            'collision_mesh': collision,
            'parts': parts,
            'pieces': pieces,
            'flyers': flyers,
            'tex': _commonassets.textures.white.get(),
            'tex_white': _commonassets.textures.white.get(),
            'tex_black': _commonassets.textures.black.get(),
        }

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'materials': [shared.footing_material],
            },
        )
        self.parts = []
        for part, color, name in self.preloaddata['parts']:
            sky = name == 'sky'
            self.parts.append(
                bs.newnode(
                    'terrain',
                    attrs={
                        'mesh': part,
                        'color': color,
                        'color_texture': self.preloaddata['tex'],
                        'lighting': not sky,
                        'background': sky,
                    },
                )
            )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.1, 1.1)
        gnode.ambient_color = (1.0, 1.0, 1.0)
        gnode.vignette_outer = (0.9, 0.95, 1.0)
        gnode.vignette_inner = (1.0, 1.0, 1.0)


def _load_piece(prefix: str, piece: str, sq: int) -> tuple[Any, Any, Any]:
    side = 'w' if piece.isupper() else 'b'
    collision, parts = load_assets(
        f'{prefix}_{side}{piece.lower()}{sq}',
        {'groups': build_piece(piece, sq)},
    )
    return collision, parts[0][0], parts[1][0]


def _load_flyer(prefix: str, piece: str) -> tuple[Any, Any]:
    side = 'w' if piece.isupper() else 'b'
    _, parts = load_assets(
        f'{prefix}_fly{side}{piece.lower()}',
        {'groups': build_piece(piece)},
        collide=False,
    )
    return parts[0][0], parts[1][0]


bs.register_map(ChessMap)


class Player(bs.Player['Team']):
    def __init__(self) -> None:
        self.cursor: bs.Node | None = None
        self.cursor_sq = -1


class Team(bs.Team[Player]):
    pass


# ba_meta export bascenev1.GameActivity
class TestChessGame(bs.TeamGameActivity[Player, Team]):
    name = 'Test Chess'
    description = 'Punch selects and moves. Pick up cancels. Mate wins.'
    scoreconfig = bs.ScoreConfig(
        label='Checkmate', scoretype=bs.ScoreType.POINTS
    )

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession)

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return [ChessMap.name]

    def __init__(self, settings: dict) -> None:
        super().__init__(settings)
        self._pos = Position()
        self._legal: list[Move] = []
        self._selected: int | None = None
        self._targets: dict[int, Move] = {}
        self._shown: dict[int, tuple[str, list[bs.Node]]] = {}
        self._assets: dict[tuple[str, int], tuple[Any, Any, Any]] = {}
        self._rings: dict[tuple[int, int], Any] = {}
        self._plates: dict[int, Any] = {}
        self._marks: list[bs.Node] = []
        self._hud: bs.Node | None = None
        self._tick_timer: bs.Timer | None = None
        self._winner: int | None = None
        self._over = False
        self._busy = False
        self._finished = False
        self._flyers: list[bs.Node] = []
        self._ghost: bs.Material | None = None

    @override
    def on_player_join(self, player: Player) -> None:
        self.spawn_player(player)

    @override
    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        if player.cursor:
            player.cursor.delete()
            player.cursor = None

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self._assets = dict(self.map.preloaddata['pieces'])
        self._ghost = bs.Material()
        self._ghost.add_actions(
            actions=('modify_part_collision', 'collide', False)
        )
        self._legal = self._pos.legal_moves()
        self._sync()
        self._hud = bs.newnode(
            'text',
            attrs={
                'v_attach': 'top',
                'h_attach': 'center',
                'h_align': 'center',
                'position': (0, -60),
                'scale': 1.4,
                'flatness': 1.0,
                'shadow': 1.0,
                'text': '',
            },
        )
        self._refresh()
        self._tick_timer = bs.Timer(0.1, self._tick, repeat=True)

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)
        player.resetinput()
        spaz.connect_controls_to_player(
            enable_punch=False, enable_bomb=False, enable_pickup=False
        )
        player.assigninput(
            babase.InputType.PUNCH_PRESS,
            babase.CallStrict(self._confirm, player),
        )
        player.assigninput(
            babase.InputType.PICK_UP_PRESS,
            babase.CallStrict(self._cancel, player),
        )
        return spaz

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            if not self._over:
                self.respawn_player(msg.getplayer(Player))
            return None
        return super().handlemessage(msg)

    def _square_of(self, player: Player) -> int | None:
        actor = player.actor
        if actor is None or not actor.node:
            return None
        x, y, z = actor.node.position
        f = math.floor(x / SQUARE + 4)
        r = math.floor(4 - z / SQUARE)
        if not (0 <= f < 8 and 0 <= r < 8) or y > 6.0:
            return None
        return r * 8 + f

    def _own_team(self, player: Player) -> bool:
        return (player.team.id == 0) == self._pos.white

    def _confirm(self, player: Player) -> None:
        if self._over or self._busy or not player.is_alive():
            return
        sq = self._square_of(player)
        if sq is None:
            return
        if not self._own_team(player):
            bs.broadcastmessage('Not your turn', color=(1, 0.6, 0.2),
                                transient=True)
            return
        if self._selected is not None and sq in self._targets:
            self._play(self._targets[sq])
            return
        piece = self._pos.board[sq]
        if piece != '.' and piece.isupper() == self._pos.white:
            targets = {m[1]: m for m in self._legal if m[0] == sq}
            if targets and sq != self._selected:
                self._selected = sq
                self._targets = targets
                self._refresh()
                return
        self._selected = None
        self._targets = {}
        self._refresh()

    def _cancel(self, player: Player) -> None:
        if self._over or self._busy or self._selected is None:
            return
        self._selected = None
        self._targets = {}
        self._refresh()

    def _motions(self, move: Move) -> list[tuple[int, int, str]]:
        frm, to, _promo = move
        board = self._pos.board
        piece = board[frm]
        out = [(frm, to, piece)]
        if piece in 'Kk' and abs((to & 7) - (frm & 7)) == 2:
            if to & 7 == 6:
                out.append((to + 1, to - 1, board[to + 1]))
            else:
                out.append((to - 2, to + 1, board[to - 2]))
        return out

    def _play(self, move: Move) -> None:
        motions = self._motions(move)
        self._pos = self._pos.apply(move)
        self._selected = None
        self._targets = {}
        self._legal = self._pos.legal_moves()
        self._busy = True
        self._finished = not self._legal
        if self._finished and self._pos.in_check():
            self._winner = 1 if self._pos.white else 0
        total = 0.0
        for frm, to, piece in motions:
            self._lift_off(frm)
            total = max(total, self._fly(piece, frm, to))
        self._refresh()
        bs.timer(total + 0.05, self._land)

    def _lift_off(self, sq: int) -> None:
        have = self._shown.pop(sq, None)
        if have is not None:
            for node in have[1]:
                node.delete()

    def _fly(self, piece: str, frm: int, to: int) -> float:
        data = self.map.preloaddata
        mesh, outline = data['flyers'][piece]
        white = piece.isupper()
        x0, z0 = square_center(frm)
        x1, z1 = square_center(to)
        dist = math.hypot(x1 - x0, z1 - z0) / SQUARE
        up, glide = 0.45, 0.55 + 0.05 * dist
        total = up + glide + up
        keys: dict[float, tuple[float, float, float]] = {}
        steps = 10

        def ease(u: float) -> float:
            return 0.5 - 0.5 * math.cos(math.pi * u)

        for i in range(steps + 1):
            u = i / steps
            keys[up * u] = (x0, PIECE_Y + LIFT * ease(u), z0)
            e = ease(u)
            keys[up + glide * u] = (
                x0 + (x1 - x0) * e,
                PIECE_Y + LIFT + 0.7 * math.sin(math.pi * u),
                z0 + (z1 - z0) * e,
            )
            keys[up + glide + up * u] = (
                x1, PIECE_Y + LIFT * (1.0 - ease(u)), z1
            )
        keys = dict(sorted(keys.items()))
        for shape, texture in (
            (mesh, data['tex_white' if white else 'tex_black']),
            (outline, data['tex_black' if white else 'tex_white']),
        ):
            node = bs.newnode(
                'prop',
                attrs={
                    'mesh': shape,
                    'color_texture': texture,
                    'body': 'sphere',
                    'body_scale': 0.1,
                    'gravity_scale': 0.0,
                    'shadow_size': 0.0,
                    'materials': [self._ghost],
                    'position': keys[0.0],
                },
            )
            bs.animate_array(node, 'position', 3, keys)
            self._flyers.append(node)
        return total

    def _land(self) -> None:
        for node in self._flyers:
            node.delete()
        self._flyers = []
        self._sync()
        self._busy = False
        if self._finished:
            self._over = True
            self._update_hud()
            bs.timer(4.0, self.end_game)

    def _sync(self) -> None:
        for sq in range(64):
            want = self._pos.board[sq]
            have = self._shown.get(sq)
            if have is not None and have[0] == want:
                continue
            if have is not None:
                for node in have[1]:
                    node.delete()
                del self._shown[sq]
            if want != '.':
                self._show(sq, want)

    def _show(self, sq: int, piece: str) -> None:
        key = (piece, sq)
        if key not in self._assets:
            prefix = self.map.preloaddata['prefix']
            self._assets[key] = _load_piece(prefix, piece, sq)
        collision, mesh, outline = self._assets[key]
        tex = self.map.preloaddata['tex']
        side = 'white' if piece.isupper() else 'black'
        nodes = [
            bs.newnode(
                'terrain',
                attrs={
                    'collision_mesh': collision,
                    'materials': [SharedObjects.get().footing_material],
                },
            ),
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': mesh,
                    'color': COLORS[side],
                    'color_texture': tex,
                    'lighting': True,
                },
            ),
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': outline,
                    'color': OUTLINE_COLORS[side],
                    'color_texture': tex,
                    'lighting': False,
                },
            ),
        ]
        self._shown[sq] = (piece, nodes)

    def _marker_mesh(self, sq: int, ring: bool, level: int = 0) -> Any:
        cache: dict[Any, Any] = self._rings if ring else self._plates
        key = (sq, level) if ring else sq
        if key not in cache:
            prefix = self.map.preloaddata['prefix']
            kind = f'ring{level}_' if ring else 'plate'
            _, parts = load_assets(
                f'{prefix}_{kind}{sq}',
                {'groups': [build_marker(sq, ring, level)]},
                collide=False,
            )
            cache[key] = parts[0][0]
        return cache[key]

    def _mark(self, sq: int, color: tuple[float, float, float]) -> None:
        self._marks.append(
            bs.newnode(
                'terrain',
                attrs={
                    'mesh': self._marker_mesh(sq, False),
                    'color': color,
                    'color_texture': self.map.preloaddata['tex'],
                    'lighting': False,
                },
            )
        )

    def _refresh(self) -> None:
        for node in self._marks:
            node.delete()
        self._marks = []
        colors: dict[int, tuple[float, float, float]] = {}
        if self._pos.in_check():
            king = 'K' if self._pos.white else 'k'
            colors[self._pos.board.index(king)] = CAPTURE_COLOR
        if self._selected is not None:
            colors[self._selected] = SELECT_COLOR
            for to in self._targets:
                capture = self._pos.board[to] != '.' or (
                    self._pos.board[self._selected] in 'Pp'
                    and to == self._pos.ep
                )
                colors[to] = CAPTURE_COLOR if capture else MOVE_COLOR
        for sq, color in colors.items():
            self._mark(sq, color)
        self._update_hud()

    def _update_hud(self) -> None:
        if self._hud is None:
            return
        side = 'White' if self._pos.white else 'Black'
        team = self.teams[0 if self._pos.white else 1]
        if self._over:
            if self._winner is None:
                text = 'Stalemate'
            else:
                text = 'Checkmate! ' + (
                    'White' if self._winner == 0 else 'Black'
                ) + ' wins'
        else:
            text = f'{side} to move' + (
                ' - CHECK' if self._pos.in_check() else ''
            )
        self._hud.text = text
        self._hud.color = tuple(team.color) if not self._over else (1, 1, 0.3)

    def _tick(self) -> None:
        for player in self.players:
            sq = self._square_of(player) if player.is_alive() else None
            if sq is None:
                if player.cursor:
                    player.cursor.delete()
                    player.cursor = None
                    player.cursor_sq = -1
                continue
            if player.cursor is None:
                player.cursor = bs.newnode(
                    'terrain',
                    attrs={
                        'color': tuple(player.team.color),
                        'color_texture': self.map.preloaddata['tex'],
                        'lighting': False,
                    },
                )
            if sq != player.cursor_sq:
                level = self.players.index(player) % 4
                player.cursor.mesh = self._marker_mesh(sq, True, level)
                player.cursor_sq = sq

    @override
    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(
                team, 1 if self._winner == team.id else 0
            )
        self.end(results=results)
