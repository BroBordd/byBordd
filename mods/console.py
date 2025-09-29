# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Console v1.1 - Better Python Console

Improves the Python development console with the following features:
- Command History: Use up/down arrows to recall previously executed commands. History is saved across sessions.
- Real-Time Suggestions: Displays a dropdown list of suggestions for global names, attributes, and non-imported modules as you type.
- Smart Completion: Automatically adds a dot (.) for modules/classes or an opening parenthesis (() for callable objects upon selection.
- Argument Support: Suggestions appear inside function calls (e.g., print(ba).
- Attribute Filtering: Dunder methods (like __init__) are shown only in attribute completion context and are sorted to the bottom of the list.
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
import pkgutil 

from types import ModuleType

GSW = lambda t:strw(t,suppress_warning=True)

def var(s,v=None):
    c = app.config
    s = 'dh_'+s
    if v is None: return c.get(s,v)
    c[s] = v
    c.commit()

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    KEY = 'list'
    def __init__(s):
        from babase._devconsoletabs import DevConsoleTabPython as T
        o = T.refresh
        T.refresh = lambda z:(s.kang(z),o(z))
        from babase._ui import DevConsoleStringEditAdapter as A
        p = A._do_apply
        A._do_apply = lambda z,t: (s.pipe(t),p(z,t))
        s.a = var(s.KEY) or []
        s.i = 0
        s.last = s.curr = ''
        s.spyt = tuck(0.1,s.spy,repeat=True)
    def pipe(s,t):
        if t == s.last: return
        s.last = s.curr = t
        s.i = 0
        s.z.request_refresh()
    def spy(s):
        if not s.last: return
        if not get():
            s.yes()
            s.last = s.curr = ''
    def yes(s):
        if s.last:
            s.i = 0
            if (not s.a or s.a[-1] != s.last):
                s.a.append(s.last)
                var(s.KEY,s.a)
            s.z.request_refresh()
    def kang(s,z):
        s.z = z
        x = z.width/2
        for i,j in enumerate(['UP','DOWN']):
            if z.height == 100:
                pos = (x-250-i*110,60)
                size = (100,30)
            else:
                pos = (x-100,120-i*60)
                size = (100,50)
            k = [1,-1][i]
            z.button(
                cs(getattr(sc,j+'_ARROW')),
                pos=pos,
                size=size,
                call=Call(s.mv,k),
                disabled=not 0<=s.i+k<=len(s.a)
            )
        s.drop()

    def drop(s):
        g = s.last
        if not g or g.endswith(' ') or g.endswith('('): return

        c = []
        p = ''
        t = ''
        is_attribute_lookup = False

        try:
            ns = _mod.get('__main__', _mod[__name__]).__dict__
            
            if g.endswith('('):
                last_token_group = ''
            elif ' ' in g:
                last_token_group = g.split(' ')[-1]
            else:
                last_token_group = g
            
            if '(' in last_token_group:
                parts = last_token_group.rsplit('(', 1)
                prefix_base_length = len(g) - len(last_token_group)
                p = g[:prefix_base_length] + parts[0] + '('
                t = parts[1] 
                
            elif '.' in last_token_group:
                is_attribute_lookup = True
                obj_string, t = last_token_group.rsplit('.', 1)
                obj = eval(obj_string, ns)
                c = dir(obj)
                prefix_base_length = len(g) - len(last_token_group)
                prefix_base = g[:prefix_base_length]
                p = prefix_base + obj_string + '.'

            else:
                t = last_token_group 

            if not c:
                c = _set(_kwl).union(dir(_mod['builtins'])).union(ns.keys())
                
                if len(t) > 0:
                    try:
                        found_modules = {
                            name for finder, name, ispkg in pkgutil.iter_modules(_path)
                            if name.startswith(t) and not name.startswith('__')
                        }
                        c = c.union(found_modules)
                    except Exception:
                        pass
                
                if not p:
                    if g.endswith('('):
                        p = g
                        t = ''
                    elif ' ' in g:
                        p = g.rsplit(' ', 1)[0] + ' '

        except Exception:
            return

        if is_attribute_lookup:
            l = sorted([_ for _ in c if _.startswith(t)], key=lambda x: (x.startswith('__'), x))
        else:
            l = sorted([_ for _ in c if _.startswith(t) and not _.startswith('__')])
            
        if not l: return

        sx = GSW(max(l, key=GSW)) + 10
        x = (-s.z.width / 2) + (GSW(p) * 0.88)

        for i,j in enumerate(l):
            s.z.button(
                '', pos=(x+20, 0-i*25), size=(sx, 25),
                corner_radius=0, style='black', call=Call(s.pick, p, j)
            )
            s.z.text(
                j, h_align='left', pos=(x+25, 12-i*25),
                scale=0.9, style='faded'
            )
            s.z.text(
                t, h_align='left', pos=(x+25, 12-i*25), scale=0.9
            )

    def pick(s,p,j):
        n = p+j
        suffix = ' ' 
        
        try:
            ns = _mod.get('__main__',_mod[__name__]).__dict__
            object_name = (p + j).split(' ')[-1]
            
            obj = eval(object_name.split('(')[0], ns) 

            if isinstance(obj, (ModuleType, type)):
                suffix = '.'
            
            elif callable(obj):
                suffix = '('
                
        except Exception:
            pass 

        set(n + suffix)
        s.last = s.curr = n + suffix
        s.i = 0
        s.z.request_refresh()

    def mv(s,i):
        gs('deek').play()
        s.i += i
        if s.i == 0: n = s.curr
        else: n = s.a[-s.i]
        set(n)
        s.last = n
        s.z.request_refresh()
