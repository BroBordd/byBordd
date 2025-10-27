# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Console v1.2 - Enhanced Python Console

Improves the Python development console with the following features:
- Command History: Recall previously executed commands across sessions using dedicated controls.
- Real-Time Suggestions: Displays smart, context-aware suggestions for globals, attributes, and non-imported modules as you type.
- Intelligent Completion: Automatically appends appropriate syntax (e.g., dot or opening parenthesis) upon selecting a suggestion.
- Dynamic UI: Suggestion dropdown dynamically adjusts its size based on content length and line-wrapping needs.
- Contextual Filtering: Dunder methods are appropriately filtered and sorted for attribute lookups.
"""

from babase import (
    get_string_width as strw,
    Plugin,
    app
)
from _babase import (
    get_dev_console_input_text as get,
    set_dev_console_input_text as set
)
from bauiv1 import (
    SpecialChar as sc,
    AppTimer as tuck,
    getsound as gs,
    charstr as cs,
    Call
)
from keyword import kwlist as _kwl
from builtins import set as _set
from sys import modules as _mod, path as _path
from pkgutil import iter_modules
from types import ModuleType

# Global
VAR = lambda s,v=None:(
    (c:=app.config),(key:='console_'+s),
    c.get(key,v) if v is None else (c.__setitem__(key,v) or c.commit())
)[2]
GSW = lambda t:strw(t,suppress_warning=True)
NPW = 10.0
LH = 25.0
SPECIAL_UP = '__up__'
SPECIAL_DELETE = '__delete__'
SPECIAL_MODE_0 = '__mode_0__'
SPECIAL_MODE_1 = '__mode_1__'
SPECIAL_LOGO = '__logo__'
SPECIAL_TAB = '__tab__'
SPECIAL_SPACE = '__space__'

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    K = 'list'
    def __init__(s):
        from babase._devconsoletabs import DevConsoleTabPython as T
        o = T.refresh
        T.refresh = lambda z:(s.kang(z),o(z))
        from babase._ui import DevConsoleStringEditAdapter as A
        p = A._do_apply
        A._do_apply = lambda z,t: (s.pipe(t),p(z,t))
        s.a = VAR(s.K) or []
        s.i = s.kb_on = s.kb_caps = s.kb_mode = 0
        s.l = s.c = ''
        s.on_tab = None
        s.st = tuck(0.1,s.spy,repeat=True)
    def pipe(s,t):
        if t == s.l: return
        s.l = s.c = t
        s.i = 0
        s.z.request_refresh()
    def spy(s):
        if not s.l: return
        if not get():
            s.yes()
            s.l = s.c = ''
    def yes(s):
        if s.l:
            s.i = 0
            if (not s.a or s.a[-1] != s.l):
                s.a.append(s.l)
                VAR(s.K,s.a)
            s.z.request_refresh()
    def kang(s,z):
        try: s._kang(z)
        except RuntimeError: pass
    def _kang(s,z):
        s.z = z
        x = z.width/2
        m = z.height == 100
        px,py = (x-250,60) if m else (x-100,180)
        size = (100,30 if m else 50)
        for i,j in enumerate(['UP','DOWN']):
            k = [1,-1][i]
            z.button(
                cs(getattr(sc,j+'_ARROW')),
                pos=(
                    (px-i*110,py) if m else
                    (px,py-i*60)
                ),
                size=size,
                call=Call(s.mv,k),
                disabled=not 0<=s.i+k<=len(s.a)
            )
        i += 1
        z.button(
            f"KB {['OFF','ON'][s.kb_on]}",
            pos=(
                (px-i*110,py) if m else
                (px,py-i*60)
            ),
            size=size,
            call=s.kb
        )
        s.drop()
        if s.kb_on: s.mk_kb()
    def kb(s):
        s.kb_on = not s.kb_on
        s.z.request_refresh()
    def get_yoff(s):
        return (
            -375 if s.z.height == 100 else
            -s.z.height
        ) if s.kb_on else 0
    def mk_kb(s):
        x = -s.z.width/2
        if s.kb_mode == 0:
            rows = [
                [(c, c) for c in s.upper('qwertyuiop')],
                [(c, c) for c in s.upper('asdfghjkl')],
                [(SPECIAL_UP, cs(sc.UP_ARROW))] + [(c, c) for c in s.upper('zxcvbnm')],
                [(SPECIAL_MODE_1, '!#1'), (SPECIAL_LOGO, cs(sc.LOGO_FLAT)), (',', ','),
                 (SPECIAL_SPACE, ' '), ('.', '.'), (SPECIAL_TAB, 'TAB')]
            ]
        elif s.kb_mode == 1:
            rows = [
                [(c, c) for c in '1234567890'],
                [(c, c) for c in '+"`\\|/_<>[]'],
                [(c, c) for c in "-'%^&*{}()"],
                [(SPECIAL_MODE_0, 'ABC'), (SPECIAL_LOGO, cs(sc.LOGO_FLAT)), (',', ','),
                 (SPECIAL_SPACE, ' '), ('.', '.'), (SPECIAL_TAB, 'TAB')]
            ]
        else:
            icons = [(name, cs(getattr(sc, name))) for name in dir(sc) if not name.startswith('_')]
            base_len = len(icons) // 3
            rows = [
                icons[:base_len],
                icons[base_len:2*base_len],
                icons[2*base_len:],
                [(SPECIAL_MODE_0, 'ABC'), (SPECIAL_MODE_1, '!#1'), (',', ','),
                 (SPECIAL_SPACE, ' '), ('.', '.'), (SPECIAL_TAB, 'TAB')]
            ]
        rows[2].append((SPECIAL_DELETE, cs(sc.DELETE)))
        sy = 75
        yoff = 120 if s.z.height == 100 else -s.z.height+120
        for i, row in enumerate(rows):
            la = len(row)
            if i == 3: sx = s.z.width/(la+3)
            else: sx = s.z.width/la
            x_offset = 0
            for j, (key_id, display) in enumerate(row):
                style = s.get_button_style(i, j, la, key_id, display)
                if key_id == SPECIAL_SPACE:
                    button_width = sx * 4
                    x_offset_after = sx * 3
                else:
                    button_width = sx
                    x_offset_after = 0
                s.z.button(
                    display,
                    size=(button_width, sy),
                    pos=(x+(j*sx)+x_offset, -i*sy-yoff),
                    call=Call(s.kb_man, key_id),
                    style=style,
                    corner_radius=0
                )
                x_offset += x_offset_after
    def get_button_style(s, row, col, row_len, key_id, display):
        if row == 2:
            if key_id == SPECIAL_UP:
                return 'yellow_bright' if s.kb_caps else 'yellow'
            elif col == row_len - 1:
                return 'red_bright'
        elif row == 3:
            if display == ' ':
                return 'black_bright'
            elif key_id == SPECIAL_TAB:
                return 'white'
            elif key_id == SPECIAL_LOGO:
                return 'red'
            elif key_id == SPECIAL_MODE_0:
                return 'blue_bright'
            elif key_id == SPECIAL_MODE_1:
                return 'blue'
            else:
                return 'purple'
        return 'black'
    def upper(s, t):
        return t.upper() if s.kb_caps else t
    def kb_man(s, b):
        if b == SPECIAL_UP:
            s.kb_caps = not s.kb_caps
            s.z.request_refresh()
            return
        elif b == SPECIAL_DELETE:
            o = get()
            o = o and o[:-1]
        elif b == SPECIAL_MODE_1:
            s.kb_mode = 1
            s.z.request_refresh()
            return
        elif b == SPECIAL_MODE_0:
            s.kb_mode = 0
            s.z.request_refresh()
            return
        elif b == SPECIAL_TAB:
            if s.on_tab is None:
                return
            s.pick(*s.on_tab)
            return
        elif b == SPECIAL_LOGO:
            s.kb_mode = 2
            s.z.request_refresh()
            return
        elif b == SPECIAL_SPACE:
            o = get() + ' '
        elif b in dir(sc):
            o = get() + cs(getattr(sc,b))
        else:
            o = get() + b
        set(o)
        s.pipe(o)
    def drop(s):
        s.on_tab = None
        yoff = s.get_yoff() if s.z.height == 100 else 0
        g = s.l
        if not g or g.endswith(' ') or g.endswith('('): return
        c = []
        p = t = oe = ''
        isa = False
        try:
            ns = _mod.get('__main__', _mod[__name__]).__dict__
            if g.endswith('('):
                ltg = ''
            elif ' ' in g:
                ltg = g.split(' ')[-1]
            else:
                ltg = g
            if '(' in ltg:
                pts = ltg.rsplit('(', 1)
                pbl = len(g) - len(ltg)
                p = g[:pbl] + pts[0] + '('
                t = pts[1]
            elif '.' in ltg:
                isa = True
                os, t = ltg.rsplit('.', 1)
                obj = eval(os, ns)
                c = dir(obj)
                pbl = len(g) - len(ltg)
                pb = g[:pbl]
                p = pb + os + '.'
                oe = os + '.'
            else: t = ltg
            if not c:
                c = _set(_kwl).union(dir(_mod['builtins'])).union(ns.keys())
                if len(t) > 0:
                    try:
                        fm = {
                            n for f, n, i in iter_modules(_path)
                            if n.startswith(t) and not n.startswith('__')
                        }
                        c = c.union(fm)
                    except Exception:
                        pass
                if not p:
                    if g.endswith('('):
                        p = g
                        t = ''
                    elif ' ' in g:
                        p = g.rsplit(' ', 1)[0] + ' '
        except Exception: return
        if isa:
            l = sorted([_ for _ in c if _.startswith(t)], key=lambda x: (x.startswith('__'), x))
        else:
            l = sorted([_ for _ in c if _.startswith(t) and not _.startswith('__')])
        if not l: return
        mxnw = 0.0
        for n in l: mxnw = max(mxnw, GSW(n))
        sf = 0.88
        pw = GSW(p) * sf
        xn = (-s.z.width / 2) + pw
        bsx = xn + 20
        mbw = s.z.width - (pw + 20.0)
        sxn = (mxnw + NPW) * 0.9
        adwm = mbw - sxn - 5.0
        slwl = adwm
        pds = []
        mrsw = 0.0
        for n in l:
            fds = ''
            rdl = []
            mxdlws = 0.0
            lbo = False
            try:
                fn = oe + n
                obj = eval(fn, ns)
                if obj.__doc__:
                    fd = obj.__doc__.strip()
                    ds = fd.replace('\n', ' ')
                    while '  ' in ds:
                        ds = ds.replace('  ',' ')
                    ds = ds.strip()
                    if ds:
                        cl = ""
                        ws = ds.split(' ')
                        for w in ws:
                            tl = (cl + ' ' + w).strip()
                            mw = GSW(tl)
                            mws = mw * 0.7
                            if cl and mws > slwl:
                                lbo = True
                                rdl.append(cl)
                                mxdlws = max(mxdlws, GSW(cl) * 0.7)
                                cl = w
                            elif not cl and mws > slwl:
                                lbo = True
                                rdl.append(w)
                                mxdlws = max(mxdlws, mws)
                                cl = ""
                            else: cl = tl
                        if cl:
                            rdl.append(cl)
                            mxdlws = max(mxdlws, GSW(cl) * 0.7)
                        fds = '\n'.join([ln.strip() for ln in rdl if ln.strip()])
            except Exception: pass
            ndl = len(fds.split('\n')) if fds else 0
            nel = max(0, ndl - 1)
            nl = 1 + nel
            th = nl * LH
            pds.append((fds, th))
            if lbo: rcw = mbw
            else: rcw = sxn + mxdlws + 25.0 + 10.0
            mrsw = max(mrsw, rcw)
        sx = mrsw
        sx = max(sx, sxn + 50.0)
        sx = min(sx, mbw)
        xd = xn + sxn
        cyp = LH + yoff
        for i, (n, (d, th)) in enumerate(zip(l, pds)):
            byp = cyp - th
            s.z.button(
                '', pos=(bsx, byp),
                size=(sx, th),
                corner_radius=0, style='black', call=Call(s.pick, p, n)
            )
            nyc = cyp - (LH/2)
            s.z.text(
                n, h_align='left', pos=(xn + 25, nyc),
                scale=0.9, style='faded'
            )
            s.z.text(
                t, h_align='left', pos=(xn + 25, nyc), scale=0.9
            )
            if d:
                dty = cyp - 1.0
                s.z.text(
                    d, h_align='left', v_align='top',
                    pos=(xd + 25, dty),
                    scale=0.7, style='faded'
                )
            cyp -= th
        if l: s.on_tab = (p,l[0])
    def pick(s,p,j):
        n = p+j
        suffix = ' '
        try:
            ns = _mod.get('__main__',_mod[__name__]).__dict__
            on = (p + j).split(' ')[-1]
            obj = eval(on.split('(')[0], ns)
            if isinstance(obj,(ModuleType,type)):
                suffix = '.'
            elif callable(obj): suffix = '('
        except Exception: pass
        set(n + suffix)
        s.l = s.c = n + suffix
        s.i = 0
        s.z.request_refresh()
    def mv(s,i):
        gs('deek').play()
        s.i += i
        if s.i == 0: n = s.c
        else: n = s.a[-s.i]
        set(n)
        s.l = n
        s.z.request_refresh()
