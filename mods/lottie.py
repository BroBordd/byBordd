# Copyright 2026 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Discord >> @BroBordd

from os.path import join, exists
import json, math
import bauiv1 as bui

"""
Lottie v1.0 - Lottie Player

Experimental.
"""

class LottiePlayer:
    def __init__(s, parent, cx=250.0, cy=210.0, w=420.0, h=360.0, max_widgets=1000, fill=False):
        s.parent, s.cx, s.cy, s.vw, s.vh, s.max_widgets, s.fill_enabled = parent, cx, cy, w, h, max_widgets, fill
        s.tex_c, s.tex_s = bui.gettexture('circle'), bui.gettexture('white')
        s.canvas = s.p = s.data = s.assets = None
        s.pool, s.tex_state, s.wstate, s.last_active = [], [], [], 0
        s.frame = s.ip = s.op = 0.0
        s.fps, s.interval, s.last_t = 60.0, 1.0 / 60.0, None
        s.scale, s.lw, s.lh = 1.0, 500.0, 500.0
        s.playing, s.token = False, 0

    def _alloc(s):
        w = bui.imagewidget(parent=s.canvas, size=(0.0, 0.0), position=(0.0, 0.0), texture=s.tex_c, opacity=0.0)
        s.pool.append(w); s.tex_state.append(s.tex_c); s.wstate.append(None)
        return w

    def stop(s):
        s.token += 1; s.playing = False; s.last_t = None
        s.canvas and s.canvas.exists() and s.canvas.delete()
        s.canvas = None
        s.pool.clear(); s.tex_state.clear(); s.wstate.clear(); s.last_active = 0

    def load(s, path, max_widgets=None):
        s.stop()
        if max_widgets: s.max_widgets = max(10, max_widgets)
        if not exists(path): return False
        try:
            with open(path, 'r', encoding='utf-8') as f: data = json.load(f)
        except Exception:
            return False
        s.data = data
        s.assets = {a['id']: a for a in data.get('assets', []) if 'id' in a}
        s.canvas = bui.containerwidget(parent=s.parent, size=(500, 500), background=False, position=(0, 0))
        [s._alloc() for _ in range(s.max_widgets)]
        s.ip, s.op = float(data.get('ip', 0.0)), float(data.get('op', 60.0))
        s.frame, s.fps = s.ip, float(data.get('fr', 60.0))
        s.lw, s.lh = float(data.get('w', 500.0)) or 500.0, float(data.get('h', 500.0)) or 500.0
        s.scale = min(s.vw / s.lw, s.vh / s.lh)
        s.playing, s.last_t, s.token = True, bui.apptime(), s.token + 1
        s._sched(s.token)
        return True

    def _sched(s, tok):
        s.playing and tok == s.token and bui.apptimer(s.interval, lambda: s._tick(tok))

    def _tick(s, tok):
        if not s.playing or tok != s.token: return
        if s.parent is None or not s.parent.exists(): s.playing = False; return
        try:
            now = bui.apptime()
            dt = min(0.04, max(0.001, (now - s.last_t) if s.last_t is not None else s.interval))
            s.last_t = now
            s.frame += s.fps * dt
            if s.frame >= s.op: s.frame = s.ip; s.wstate = [None] * len(s.pool)

            prims = s._render(s.frame)
            n = len(prims)
            if n > s.max_widgets:
                stride = n / float(s.max_widgets)
                prims = [prims[int(i * stride)] for i in range(s.max_widgets)]; n = s.max_widgets

            for i in range(n):
                x, y, w, h, col, op, tex = prims[i]
                rx, ry, rw, rh, rop = round(x, 1), round(y, 1), round(w, 1), round(h, 1), round(op, 2)
                state = (rx, ry, rw, rh, col, rop, tex)
                if s.wstate[i] != state:
                    s.wstate[i] = state; wgt = s.pool[i]
                    if s.tex_state[i] != tex: bui.imagewidget(wgt, texture=tex); s.tex_state[i] = tex
                    bui.imagewidget(wgt, position=(rx - rw * 0.5, ry - rh * 0.5), size=(max(1.0, rw), max(1.0, rh)),
                                     color=col, opacity=max(0.0, min(1.0, rop)))

            for i in range(n, s.last_active):
                if s.wstate[i] != 0: s.wstate[i] = 0; bui.imagewidget(s.pool[i], size=(0.0, 0.0), opacity=0.0)
            s.last_active = n
        except Exception:
            pass
        finally:
            s._sched(tok)

    def _cval(s, v, d):
        if v is None: return d
        if isinstance(v, (int, float)): return float(v)
        if isinstance(v, list): return s._cval(v[0], d) if len(v) == 1 and not isinstance(d, list) else v
        return v

    def _ishape(s, a, b, t):
        v1, v2, i1, i2, o1, o2, c = a.get('v', []), b.get('v', []), a.get('i', []), b.get('i', []), a.get('o', []), b.get('o', []), a.get('c', False)
        n = min(len(v1), len(v2)); nv, ni, no = [], [], []
        for k in range(n):
            p0, p1 = v1[k], v2[k]
            nv.append([p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t])
            j0, j1 = (i1[k] if k < len(i1) else [0.0, 0.0]), (i2[k] if k < len(i2) else [0.0, 0.0])
            ni.append([j0[0] + (j1[0] - j0[0]) * t, j0[1] + (j1[1] - j0[1]) * t])
            k0, k1 = (o1[k] if k < len(o1) else [0.0, 0.0]), (o2[k] if k < len(o2) else [0.0, 0.0])
            no.append([k0[0] + (k1[0] - k0[0]) * t, k0[1] + (k1[1] - k0[1]) * t])
        return {'v': nv, 'i': ni, 'o': no, 'c': c}

    def _ival(s, a, b, t, d):
        if isinstance(a, list) and len(a) == 1 and not isinstance(d, list): a = a[0]
        if isinstance(b, list) and len(b) == 1 and not isinstance(d, list): b = b[0]
        if isinstance(a, (int, float)) and isinstance(b, (int, float)): return a + (b - a) * t
        if isinstance(a, list) and isinstance(b, list):
            if a and isinstance(a[0], dict) and b and isinstance(b[0], dict): return [s._ishape(a[0], b[0], t)]
            return [x + (y - x) * t for x, y in zip(a, b)]
        if isinstance(a, dict) and isinstance(b, dict): return s._ishape(a, b, t)
        return a

    def _eval(s, prop, frame, d=0.0):
        if prop is None: return d
        if isinstance(prop, (int, float)): return float(prop)
        if isinstance(prop, (str, bool, list)): return prop
        if not isinstance(prop, dict): return d
        k = prop.get('k', prop)
        if isinstance(k, (int, float)): return float(k)
        if not isinstance(k, list): return k
        if not k: return d
        if isinstance(k[0], (int, float)): return [float(x) for x in k]
        if isinstance(k[0], dict) and 't' in k[0]:
            first = k[0]
            if frame <= first.get('t', 0.0): return s._cval(first.get('s'), d)
            for i in range(len(k) - 1):
                kf1, kf2 = k[i], k[i + 1]
                t1, t2 = kf1.get('t', 0.0), kf2.get('t', kf1.get('t', 0.0))
                if t1 <= frame < t2:
                    s1, s2 = kf1.get('s'), kf1.get('e')
                    if s2 is None: s2 = kf2.get('s', s1)
                    if s1 is None: return d
                    if t2 <= t1 or kf1.get('h', 0) == 1: return s._cval(s1, d)
                    return s._ival(s1, s2, (frame - t1) / float(t2 - t1), d)
            last = k[-1]; val = last.get('s')
            if val is None and len(k) >= 2: val = k[-2].get('e', k[-2].get('s'))
            return s._cval(val, d)
        return k

    def _layer_xform(s, layer, frame, by_ind):
        chain, curr, seen = [], layer, set()
        while curr and curr.get('ind') not in seen:
            seen.add(curr.get('ind')); chain.append(curr)
            pi = curr.get('parent'); curr = by_ind.get(pi) if pi is not None else None
        gx = gy = gr = 0.0; gsx = gsy = g_op = 1.0
        for l in reversed(chain):
            ks = l.get('ks', {}); lf = (frame - float(l.get('st', 0.0))) / float(l.get('sr', 1.0))
            p, sc, a = s._eval(ks.get('p'), lf, [0.0, 0.0]), s._eval(ks.get('s'), lf, [100.0, 100.0]), s._eval(ks.get('a'), lf, [0.0, 0.0])
            r, o = s._eval(ks.get('r'), lf, 0.0), s._eval(ks.get('o'), lf, 100.0)
            px, py = (p[0] if isinstance(p, list) and p else 0.0), (p[1] if isinstance(p, list) and len(p) > 1 else 0.0)
            ax, ay = (a[0] if isinstance(a, list) and a else 0.0), (a[1] if isinstance(a, list) and len(a) > 1 else 0.0)
            sx, sy = (sc[0] / 100.0 if isinstance(sc, list) and sc else 1.0), (sc[1] / 100.0 if isinstance(sc, list) and len(sc) > 1 else 1.0)
            rot, op = (float(r) if isinstance(r, (int, float)) else 0.0), (o / 100.0 if isinstance(o, (int, float)) else 1.0)
            gx += (px - ax * sx) * gsx; gy += (py - ay * sy) * gsy
            gsx *= sx; gsy *= sy; gr += rot; g_op *= op
        return gx, gy, gsx, gsy, gr, g_op

    def _ncolor(s, c):
        if not isinstance(c, (list, tuple)) or len(c) < 3: return (0.15, 0.75, 0.95)
        r, g, b = float(c[0]), float(c[1]), float(c[2])
        return (r / 255.0, g / 255.0, b / 255.0) if max(r, g, b) > 1.0 else (max(0.0, min(1.0, r)), max(0.0, min(1.0, g)), max(0.0, min(1.0, b)))

    def _hex(s, h):
        h = str(h).lstrip('#')
        return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0) if len(h) == 6 else (0.15, 0.75, 0.95)

    def _render(s, frame):
        prims = []
        s._layers(s.data.get('layers', []), frame, 0.0, 0.0, 1.0, 1.0, 0.0, 1.0, prims)
        return prims

    def _layers(s, layers, frame, bx, by, bsx, bsy, br, bop, prims):
        by_ind = {l['ind']: l for l in layers if 'ind' in l}
        for layer in layers:
            ip, op = float(layer.get('ip', s.ip)), float(layer.get('op', s.op))
            if frame < ip or frame >= op: continue
            lf = (frame - float(layer.get('st', 0.0))) / float(layer.get('sr', 1.0))
            gx, gy, gsx, gsy, gr, g_op = s._layer_xform(layer, frame, by_ind)
            gx, gy, gsx, gsy, gr, g_op = bx + gx * bsx, by + gy * bsy, gsx * bsx, gsy * bsy, gr + br, g_op * bop
            if g_op <= 0.01 or abs(gsx) < 0.001 or abs(gsy) < 0.001: continue
            ty = layer.get('ty')
            if ty == 0:
                asset = s.assets.get(layer.get('refId'))
                asset and 'layers' in asset and s._layers(asset['layers'], lf, gx, gy, gsx, gsy, gr, g_op, prims)
            elif ty == 1:
                sw, sh, col = float(layer.get('sw', 0)), float(layer.get('sh', 0)), s._hex(layer.get('sc', '#ffffff'))
                w, h = sw * abs(gsx) * s.scale, sh * abs(gsy) * s.scale
                sx, sy = s.cx + (gx - s.lw * 0.5) * s.scale, s.cy - (gy - s.lh * 0.5) * s.scale
                prims.append((sx, sy, w, h, col, g_op, s.tex_s))
            elif ty == 4:
                s._shape_layer(layer.get('shapes', []), lf, gx, gy, gsx, gsy, gr, g_op, prims)

    def _bezier(s, p0, p1, p2, p3, step=2.5):
        chord = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
        net = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) + math.hypot(p2[0] - p1[0], p2[1] - p1[1]) + math.hypot(p3[0] - p2[0], p3[1] - p2[1])
        alen = max(1.0, (chord + net) * 0.5); steps = max(4, int(alen / step)); pts = []
        for step_i in range(steps):
            t = step_i / float(steps); u = 1.0 - t
            u3, u2t, ut2, t3 = u ** 3, 3 * u * u * t, 3 * u * t * t, t ** 3
            pts.append((u3 * p0[0] + u2t * p1[0] + ut2 * p2[0] + t3 * p3[0], u3 * p0[1] + u2t * p1[1] + ut2 * p2[1] + t3 * p3[1]))
        return pts, alen

    def _paths(s, items, frame, px, py, psx, psy, pr, pop, out, itrim, ifill):
        cur_sc, cur_so, sw = (0.15, 0.75, 0.95), 1.0, 4.0
        has_fill, cur_fc, cur_fo = (ifill if ifill is not None else (False, (0.15, 0.75, 0.95), 0.0))
        gx, gy, gsx, gsy, gr, gop, ltrim = px, py, psx, psy, pr, pop, itrim

        for it in items:
            ty = it.get('ty')
            if ty == 'tr':
                p, sc, a = s._eval(it.get('p'), frame, [0.0, 0.0]), s._eval(it.get('s'), frame, [100.0, 100.0]), s._eval(it.get('a'), frame, [0.0, 0.0])
                r, o = s._eval(it.get('r'), frame, 0.0), s._eval(it.get('o'), frame, 100.0)
                px_, py_ = (p[0] if isinstance(p, list) and p else 0.0), (p[1] if isinstance(p, list) and len(p) > 1 else 0.0)
                ax, ay = (a[0] if isinstance(a, list) and a else 0.0), (a[1] if isinstance(a, list) and len(a) > 1 else 0.0)
                sx, sy = (sc[0] / 100.0 if isinstance(sc, list) and sc else 1.0), (sc[1] / 100.0 if isinstance(sc, list) and len(sc) > 1 else 1.0)
                gx += (px_ - ax * sx) * gsx; gy += (py_ - ay * sy) * gsy; gsx *= sx; gsy *= sy
                gr += float(r) if isinstance(r, (int, float)) else 0.0
                gop *= (o / 100.0) if isinstance(o, (int, float)) else 1.0
            elif ty == 'fl':
                has_fill = True; c = s._eval(it.get('c'), frame, [0.15, 0.75, 0.95, 1.0]); cur_fc = s._ncolor(c)
                o = s._eval(it.get('o'), frame, 100.0); cur_fo = (o / 100.0) if isinstance(o, (int, float)) else 1.0
            elif ty == 'st':
                c = s._eval(it.get('c'), frame, [0.15, 0.75, 0.95, 1.0]); cur_sc = s._ncolor(c)
                w = s._eval(it.get('w'), frame, 4.0); sw = float(w) if isinstance(w, (int, float)) else 4.0
                o = s._eval(it.get('o'), frame, 100.0); cur_so = (o / 100.0) if isinstance(o, (int, float)) else 1.0
            elif ty == 'tm':
                st, e, o = s._eval(it.get('s'), frame, 0.0), s._eval(it.get('e'), frame, 100.0), s._eval(it.get('o'), frame, 0.0)
                ltrim = (max(0.0, min(1.0, (st if isinstance(st, (int, float)) else 0.0) / 100.0)),
                         max(0.0, min(1.0, (e if isinstance(e, (int, float)) else 100.0) / 100.0)),
                         ((o if isinstance(o, (int, float)) else 0.0) % 360.0) / 360.0, int(it.get('m', 2)))

        pass_fill = (has_fill, cur_fc, cur_fo)
        for it in items:
            ty = it.get('ty')
            if ty == 'gr':
                s._paths(it.get('it', []), frame, gx, gy, gsx, gsy, gr, gop, out, ltrim, pass_fill)
            elif ty == 'sh':
                ks = s._eval(it.get('ks'), frame, None)
                if isinstance(ks, list) and ks and isinstance(ks[0], dict) and 'v' in ks[0]: ks = ks[0]
                if isinstance(ks, dict) and 'v' in ks:
                    out.append({'ks': ks, 'gx': gx, 'gy': gy, 'gsx': gsx, 'gsy': gsy, 'gr': gr,
                                'stroke_color': cur_sc, 'stroke_opacity': gop * cur_so, 'stroke_w': sw,
                                'has_fill': has_fill, 'fill_color': cur_fc, 'fill_opacity': gop * cur_fo, 'trim': ltrim})

    def _shape_layer(s, items, frame, px, py, psx, psy, pr, pop, prims):
        layer_trim = None
        for it in items:
            if it.get('ty') == 'tm':
                st, e, o = s._eval(it.get('s'), frame, 0.0), s._eval(it.get('e'), frame, 100.0), s._eval(it.get('o'), frame, 0.0)
                layer_trim = (max(0.0, min(1.0, (st if isinstance(st, (int, float)) else 0.0) / 100.0)),
                              max(0.0, min(1.0, (e if isinstance(e, (int, float)) else 100.0) / 100.0)),
                              ((o if isinstance(o, (int, float)) else 0.0) % 360.0) / 360.0, int(it.get('m', 2)))
                break

        path_list = []
        s._paths(items, frame, px, py, psx, psy, pr, pop, path_list, layer_trim, None)
        if not path_list: return

        sampled, total_len = [], 0.0
        for pi in path_list:
            ks = pi['ks']; v, it_, ot_, closed = ks.get('v', []), ks.get('i', []), ks.get('o', []), ks.get('c', False)
            count = len(v); seg = count if closed else count - 1
            if seg <= 0: continue
            pts, plen = [], 0.0
            for k in range(seg):
                nxt = (k + 1) % count; p0, p3 = v[k], v[nxt]
                o = ot_[k] if k < len(ot_) else [0.0, 0.0]; i = it_[nxt] if nxt < len(it_) else [0.0, 0.0]
                p1, p2 = [p0[0] + o[0], p0[1] + o[1]], [p3[0] + i[0], p3[1] + i[1]]
                sp, sl = s._bezier(p0, p1, p2, p3); pts.extend(sp); plen += sl
            if not closed and v: pts.append((v[-1][0], v[-1][1]))
            pi['pts'], pi['closed'], pi['length'] = pts, closed, max(1.0, plen)
            sampled.append(pi); total_len += pi['length']

        if total_len <= 0.0: return
        accum, fill_prims, stroke_prims = 0.0, [], []

        for pi in sampled:
            pts, plen, trim, closed = pi['pts'], pi['length'], pi['trim'], pi['closed']
            if trim is not None:
                ts, te, to, tm = trim
                if tm == 2:
                    p_s, p_e = accum / total_len, (accum + plen) / total_len
                    ls = max(0.0, min(1.0, (ts - p_s) / (p_e - p_s))); le = max(0.0, min(1.0, (te - p_s) / (p_e - p_s)))
                else:
                    ls, le = ts, te
                if abs(le - ls) < 0.001 or le <= ls: accum += plen; continue
                tp = len(pts); active = pts[int(ls * tp):int(le * tp)]
            else:
                active = pts
            accum += plen
            if not active: continue

            gx, gy, gsx, gsy, gr = pi['gx'], pi['gy'], pi['gsx'], pi['gsy'], pi['gr']
            rad = math.radians(gr); cr, sr = math.cos(rad), math.sin(rad)

            active_screen = []
            for lx, ly in active:
                lx, ly = lx * gsx, ly * gsy
                rx, ry = lx * cr - ly * sr, lx * sr + ly * cr
                wx, wy = gx + rx, gy + ry
                active_screen.append((s.cx + (wx - s.lw * 0.5) * s.scale, s.cy - (wy - s.lh * 0.5) * s.scale))

            if s.fill_enabled and pi['has_fill'] and closed and pi['fill_opacity'] > 0.01:
                poly = []
                for lx, ly in pts:
                    lx, ly = lx * gsx, ly * gsy
                    rx, ry = lx * cr - ly * sr, lx * sr + ly * cr
                    wx, wy = gx + rx, gy + ry
                    poly.append((s.cx + (wx - s.lw * 0.5) * s.scale, s.cy - (wy - s.lh * 0.5) * s.scale))

                if len(poly) >= 3:
                    min_y, max_y = min(p[1] for p in poly), max(p[1] for p in poly)
                    clip_x = max(p[0] for p in active_screen) if trim is not None else None
                    dy, span_h, y = 3.0, 3.6, min_y + 1.5
                    n_poly, fc, fo = len(poly), pi['fill_color'], pi['fill_opacity']
                    while y <= max_y:
                        xs = []
                        for i in range(n_poly):
                            p1, p2 = poly[i], poly[(i + 1) % n_poly]
                            y1, y2 = p1[1], p2[1]
                            if (y1 <= y < y2) or (y2 <= y < y1):
                                abs(y2 - y1) > 1e-4 and xs.append(p1[0] + (y - y1) * (p2[0] - p1[0]) / (y2 - y1))
                        xs.sort()
                        for k in range(0, len(xs) - 1, 2):
                            xl, xr = xs[k], min(xs[k + 1], clip_x) if clip_x is not None else xs[k + 1]
                            if (sw_ := xr - xl) > 0.8:
                                fill_prims.append(((xl + xr) * 0.5, y, sw_, span_h, fc, fo, s.tex_s))
                        y += dy

            sc, so, stw = pi['stroke_color'], pi['stroke_opacity'], pi['stroke_w']
            dot = max(3.5, stw * max(abs(gsx), abs(gsy)) * s.scale)
            stroke_prims.extend((sx, sy, dot, dot, sc, so, s.tex_c) for sx, sy in active_screen)

        prims.extend(fill_prims); prims.extend(stroke_prims)


# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(bui.Plugin):
    def __init__(s):
        s.p = s.player = s.input_name = s.input_amount = s.fill_checkbox = None
        s.fill_enabled = False

    def _on_fill(s, v):
        s.fill_enabled = bool(v)

    def has_settings_ui(s):
        return 1

    def show_settings_ui(s, btn=None):
        s.p = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'), size=(500, 500), background=False, transition='in_scale', scale_origin_stack_offset=btn.get_screen_space_center())
        bui.imagewidget(parent=s.p, texture=bui.gettexture('white'), size=(500, 500), color=(0.0, 0.0, 0.0))
        bui.imagewidget(parent=s.p, position=(20, 434), size=(165, 44), texture=bui.gettexture('white'), color=(1.0, 1.0, 1.0))
        s.input_name = bui.textwidget(parent=s.p, position=(25, 434), size=(155, 44), text='lottie.json',
                                       editable=True, v_align='center', color=(0.0, 0.0, 0.0), glow_type='uniform')
        bui.imagewidget(parent=s.p, position=(193, 434), size=(72, 44), texture=bui.gettexture('white'), color=(1.0, 1.0, 1.0))
        s.input_amount = bui.textwidget(parent=s.p, position=(197, 434), size=(64, 44), text='1000',
                                         editable=True, v_align='center', color=(0.0, 0.0, 0.0), glow_type='uniform')
        bui.imagewidget(parent=s.p, position=(273, 434), size=(95, 44), texture=bui.gettexture('white'), color=(1.0, 1.0, 1.0))
        s.fill_checkbox = bui.checkboxwidget(parent=s.p, position=(278, 434), size=(85, 44), text='Fill',
                                              value=False, textcolor=(0.0, 0.0, 0.0), on_value_change_call=s._on_fill)
        bui.buttonwidget(parent=s.p, position=(376, 434), size=(104, 44), label='Play', on_activate_call=s.start_demo,
                          texture=bui.gettexture('white'), color=(1.0, 1.0, 1.0), textcolor=(0.0, 0.0, 0.0), enable_sound=False)

    def start_demo(s):
        if s.fill_checkbox and s.fill_checkbox.exists():
            try: s.fill_enabled = bool(bui.checkboxwidget(query=s.fill_checkbox))
            except Exception: pass

        fname = bui.textwidget(query=s.input_name).strip()
        path = join(bui.app.env.python_directory_user, fname)
        try: amt = max(10, int(bui.textwidget(query=s.input_amount).strip()))
        except Exception: amt = 1000

        if not exists(path):
            bui.getsound('block').play(); bui.screenmessage('File not found: ' + fname); return

        s.player is None and setattr(s, 'player', LottiePlayer(s.p, max_widgets=amt, fill=s.fill_enabled))
        s.player.max_widgets, s.player.fill_enabled = amt, s.fill_enabled

        if s.player.load(path):
            bui.getsound('deek').play()
        else:
            bui.getsound('block').play(); bui.screenmessage('JSON Error loading: ' + fname)
