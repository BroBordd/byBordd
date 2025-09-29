# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Console v1.2 - Better Python Console

Experimental. Feedback is appreciated.
Modifies the existing Python development console.

Features vary between:
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

GSW = lambda t:strw(t,suppress_warning=True)
NAME_PADDING_WIDTH = 10.0
LINE_HEIGHT = 25.0

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
        obj_eval_prefix = ''
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
                obj_eval_prefix = obj_string + '.'
            else:
                t = last_token_group
            if not c:
                c = _set(_kwl).union(dir(_mod['builtins'])).union(ns.keys())
                if len(t) > 0:
                    try:
                        found_modules = {
                            name for finder, name, ispkg in iter_modules(_path)
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
        processed_descriptions = []
        max_name_width = 0
        scale_factor = 0.88
        for name in l:
            max_name_width = max(max_name_width, GSW(name))
        prefix_width = GSW(p) * scale_factor
        x_name = (-s.z.width / 2) + prefix_width
        button_start_x = x_name + 20
        MAX_BUTTON_WIDTH = s.z.width - (prefix_width + 20.0)
        sx_name_scaled = (max_name_width + NAME_PADDING_WIDTH) * 0.9
        AVAILABLE_DESC_WIDTH_MAX = MAX_BUTTON_WIDTH - sx_name_scaled - 5.0
        SCALED_LINE_WIDTH_LIMIT = AVAILABLE_DESC_WIDTH_MAX
        max_required_button_width = 0.0
        for name in l:
            final_doc_string = ''
            raw_doc_lines = []
            max_desc_line_width_scaled = 0.0
            line_break_occurred = False
            try:
                full_name = obj_eval_prefix + name
                obj = eval(full_name, ns)
                if obj.__doc__:
                    full_doc = obj.__doc__.strip()
                    doc_string = ''
                    if " -> " in full_doc:
                        arrow_index = full_doc.find(" -> ")
                        line_end = full_doc.find('\n', arrow_index)
                        if line_end == -1:
                            line_end = len(full_doc)
                        doc_string = full_doc[:line_end].strip()
                    else:
                        for line in full_doc.split('\n'):
                            line = line.strip()
                            if line:
                                doc_string = line
                                break
                    if doc_string:
                        doc_string = doc_string.replace('\n', ' ')
                        while '  ' in doc_string:
                            doc_string = doc_string.replace('  ', ' ')
                        doc_string = doc_string.strip()
                        current_line = ""
                        words = doc_string.split(' ')
                        for word in words:
                            test_line = (current_line + ' ' + word).strip()
                            measured_width_unscaled = GSW(test_line)
                            measured_width_scaled = measured_width_unscaled * 0.7
                            if current_line and measured_width_scaled > SCALED_LINE_WIDTH_LIMIT:
                                line_break_occurred = True
                                raw_doc_lines.append(current_line)
                                max_desc_line_width_scaled = max(max_desc_line_width_scaled, GSW(current_line) * 0.7)
                                current_line = word
                            elif not current_line and measured_width_scaled > SCALED_LINE_WIDTH_LIMIT:
                                line_break_occurred = True
                                raw_doc_lines.append(word)
                                max_desc_line_width_scaled = max(max_desc_line_width_scaled, measured_width_scaled)
                                current_line = ""
                            else:
                                current_line = test_line
                        if current_line:
                            raw_doc_lines.append(current_line)
                            max_desc_line_width_scaled = max(max_desc_line_width_scaled, GSW(current_line) * 0.7)
                        final_doc_string = '\n'.join([line.strip() for line in raw_doc_lines if line.strip()])
            except Exception:
                pass
            num_doc_lines = len(final_doc_string.split('\n')) if final_doc_string else 0
            num_extra_lines = max(0, num_doc_lines - 1)
            num_lines = 1 + num_extra_lines
            total_height = num_lines * LINE_HEIGHT
            processed_descriptions.append((final_doc_string, total_height))
            name_width_scaled_0_9 = GSW(name) * 0.9
            if line_break_occurred:
                required_content_width = MAX_BUTTON_WIDTH
            else:
                required_content_width = name_width_scaled_0_9 + max_desc_line_width_scaled + 25.0 + 10.0
            max_required_button_width = max(max_required_button_width, required_content_width)
        sx = max_required_button_width
        sx = max(sx, sx_name_scaled + 50.0)
        sx = min(sx, MAX_BUTTON_WIDTH)
        x_desc = x_name + sx_name_scaled
        current_y_pos = LINE_HEIGHT
        for i, (name, (desc, total_height)) in enumerate(zip(l, processed_descriptions)):
            button_y_pos = current_y_pos - total_height
            s.z.button(
                '', pos=(button_start_x, button_y_pos),
                size=(sx, total_height),
                corner_radius=0, style='black', call=Call(s.pick, p, name)
            )
            name_y_center = current_y_pos - (LINE_HEIGHT/2)
            s.z.text(
                name, h_align='left', pos=(x_name + 25, name_y_center),
                scale=0.9, style='faded'
            )
            s.z.text(
                t, h_align='left', pos=(x_name + 25, name_y_center), scale=0.9
            )
            if desc:
                desc_top_y = current_y_pos - 1.0
                s.z.text(
                    desc, h_align='left', v_align='top',
                    pos=(x_desc + 25, desc_top_y),
                    scale=0.7, style='faded'
                )
            current_y_pos -= total_height
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
