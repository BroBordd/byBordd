# Copyright 2026 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Discord >> @BrotherBoard

from collections import defaultdict
import heapq
import math
import os
import random
import re
import struct
import threading
import time
import weakref
import babase
import bascenev1 as bs
from babase import get_string_width
from bascenev1lib.actor.spaz import Spaz

SPAZ_Y_OFF = 0.30
_pc = getattr(bs, 'pushcall', getattr(babase, 'pushcall', None))
def pushcall(call):
    if _pc: _pc(call, from_other_thread=True)


class Tri:
    __slots__ = ('id', 'p1', 'p2', 'p3', 'v_ids', 'nx', 'ny', 'nz', 'cx', 'cy', 'cz', 'min_x', 'max_x', 'min_y', 'max_y', 'min_z', 'max_z', 'pen')
    def __init__(s, tid, p1, p2, p3, v1, v2, v3):
        s.id = tid
        s.p1, s.p2, s.p3 = p1, p2, p3
        s.v_ids = (v1, v2, v3)
        s.cx = (p1[0] + p2[0] + p3[0]) / 3.0
        s.cy = (p1[1] + p2[1] + p3[1]) / 3.0
        s.cz = (p1[2] + p2[2] + p3[2]) / 3.0
        s.min_x = min(p1[0], p2[0], p3[0])
        s.max_x = max(p1[0], p2[0], p3[0])
        s.min_y = min(p1[1], p2[1], p3[1])
        s.max_y = max(p1[1], p2[1], p3[1])
        s.min_z = min(p1[2], p2[2], p3[2])
        s.max_z = max(p1[2], p2[2], p3[2])
        s.pen = 0.0
        ax, ay, az = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]
        bx, by, bz = p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]
        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        l = math.sqrt(nx * nx + ny * ny + nz * nz)
        s.nx, s.ny, s.nz = (nx / l, ny / l, nz / l) if l > 1e-6 else (0, 1, 0)

    def contains_2d(s, px, pz):
        def sgn(x1, z1, x2, z2, x3, z3):
            return (x1 - x3) * (z2 - z3) - (x2 - x3) * (z1 - z3)
        d1 = sgn(px, pz, s.p1[0], s.p1[2], s.p2[0], s.p2[2])
        d2 = sgn(px, pz, s.p2[0], s.p2[2], s.p3[0], s.p3[2])
        d3 = sgn(px, pz, s.p3[0], s.p3[2], s.p1[0], s.p1[2])
        return not (((d1 < -1e-5) or (d2 < -1e-5) or (d3 < -1e-5)) and ((d1 > 1e-5) or (d2 > 1e-5) or (d3 > 1e-5)))

    def height_at(s, px, pz):
        return s.cy if abs(s.ny) < 1e-5 else (-s.nx * (px - s.cx) - s.nz * (pz - s.cz)) / s.ny + s.cy


class Hitomi:
    def __init__(s, pos):
        act = bs.getactivity()
        s.act_ref = weakref.ref(act) if act else None
        with act.context:
            s.bot = Spaz(color=(0, 0, 0), highlight=(0, 0, 0), character='Pixel')
            s.bot.node.name = 'Hitomi'
            s.bot.node.name_color = (0, 0, 0)
            s.bot.handlemessage(bs.StandMessage(pos, 0))

            s.stream = Stream(s.bot.node)
            s.last_msgs = bs.get_chat_messages()
            s.c_tmr = bs.Timer(0.2, s._chk_chat, repeat=True)

            s.max_step = 0.05
            s.min_fall = 0.40
            s.max_fall = 0.50
            s.fin_dist = 0.30
            s.far_pref = 0.0
            s.n_timeout = 2.0

            s.exploring = True
            s.prog = "0/0"
            s.stream.push("I'm exploring")
            s.look_tmr = None
            s._sched_look()

            s.m_name = None
            s.cob_path = None
            s.m_vecs = []
            s.m_faces = []

            s.w_tris = {}
            s.obs_tris = []
            s.graph = {}

            s.w_hash = defaultdict(list)
            s.obs_hash = defaultdict(list)

            s.path = []
            s.idx = 0
            s.tgt = None
            s.m_tmr = None

            s.v_nodes = []
            s.v_tmr = bs.Timer(0.2, s._draw_path, repeat=True)

            s.dot_nodes = []
            s.dot_last = None
            s.dots_tmr = bs.Timer(0.25, s._dots_tick, repeat=True)

        s.read_cob()

    def _get_act(s):
        if s.act_ref:
            act = s.act_ref()
            if act and not act.has_ended():
                return act
        act = bs.getactivity()
        if act and not act.has_ended():
            return act
        return None

    def _sched_look(s):
        if not s.exploring: return
        act = s._get_act()
        if not act: return
        with act.context:
            s.look_tmr = bs.Timer(random.uniform(0.12, 0.55), s._random_look)

    def _random_look(s):
        if not s.exploring or not s.bot.node or not s.bot.node.exists(): return
        act = s._get_act()
        if not act: return
        with act.context:
            ang = random.uniform(0, math.tau)
            mag = random.uniform(0.012, 0.035)
            dur = random.uniform(0.03, 0.08)
            s.bot.on_move_left_right(math.cos(ang) * mag)
            s.bot.on_move_up_down(-math.sin(ang) * mag)
            bs.timer(dur, s._stop)
            s._sched_look()

    def read_cob(s):
        act = s._get_act()
        if not act or not hasattr(act, 'map'): return
        s.m_name = getattr(act.map, 'name', 'Crag Castle')
        s.cob_data = None
        s.cob_path = None
        err = None
        try: s.cob_data = s._cas_cob(s.m_name, type(act.map).__name__)
        except Exception as e:
            s.cob_data = None
            err = f"{type(e).__name__}: {e}"
        if s.cob_data is None and err is None: err = 'no leaf for map'
        if err: print('[hitomi] cas lookup failed:', err)
        if s.cob_data is None:
            s.cob_path = s._find_cob(s.m_name)
            if not s.cob_path or not os.path.exists(s.cob_path):
                with act.context:
                    s.stream.push(f"Cannot find mesh: {(err or '?')[:70]}")
                s.exploring = False
                s.look_tmr = None
                return
        threading.Thread(target=s._thread_load, daemon=True).start()

    def _thread_load(s):
        try:
            vecs, faces = s._parse_cob(s.cob_data if s.cob_data is not None else s.cob_path)
            s._bake(vecs, faces)
        except Exception as e:
            pushcall(lambda: s._on_err(str(e)))

    def _on_err(s, e):
        act = s._get_act()
        if act:
            with act.context:
                s.stream.push(f"Cob error: {e}")

    def _get_env_paths(s):
        p = []
        for app in (getattr(bs, 'app', None), getattr(babase, 'app', None)):
            if app and hasattr(app, 'env'):
                for k in ('data_directory', 'python_directory_app', 'python_directory_user'):
                    v = getattr(app.env, k, None)
                    if v and os.path.exists(v): p.append(str(v))
        p.append(os.getcwd())
        return list(dict.fromkeys(p))

    # 1.8: collision meshes are hash-named blobs in asset-packages, not
    # loose .cob files. Resolve map -> logical path -> blob hash -> bytes.
    _CAS_ALIAS = {'happythoughts': 'always_land_level_collide'}

    def _cas_leaf(s, name, cls):
        from bascenev1 import _classicmapassets as cma
        tree = cma._TREE['meshes']
        norm = lambda t: re.sub(r'[^a-z0-9]', '', t.lower())
        for k in (norm(name), norm(cls)):
            if k in s._CAS_ALIAS and tree.get(s._CAS_ALIAS[k]) == 'c':
                return s._CAS_ALIAS[k]
        bad = ('bumper', 'wall', 'railing', 'nature_background', 'stem')
        cands = []
        for leaf, kind in tree.items():
            if kind != 'c' or any(b in leaf for b in bad): continue
            nl = norm(leaf)
            if any(k and (k in nl or nl in k) for k in (norm(name), norm(cls))):
                cands.append(leaf)
        return cands[0] if cands else None

    def _cas_cob(s, name, cls):
        import json
        from bascenev1 import _classicmapassets as cma
        leaf = s._cas_leaf(name, cls)
        if not leaf: return None
        try: import _babase
        except Exception: _babase = babase._babase
        assets = babase.app.assets
        def rd(h):
            try: b = assets._read_blob(h)
            except Exception: b = None
            return b if b is not None else _babase.bundled_cas_blob_bytes(h)
        pk = str(int(cma._ASSET_PACKAGE))
        srcs = []
        try:
            t = _babase.bundled_asset_manifest_text()
            if t: srcs += [(k, v.get('flavor_manifests', {})) for k, v in json.loads(t).get('asset_package_versions', {}).items()]
        except Exception: pass
        try:
            with open(os.path.join(str(babase.app.env.cache_directory), 'manifest.json'), encoding='utf-8') as f:
                srcs += [(k, v.get('fm', {})) for k, v in json.load(f).get('p', {}).items()]
        except Exception: pass
        srcs.sort(key=lambda kv: kv[0] != pk)
        for k, fms in srcs:
            h = fms.get('constant')
            if not h: continue
            try: ent = json.loads(rd(h))['e'].get('meshes/' + leaf)
            except Exception: continue
            if not ent: continue
            part = next((x for x in ent if x.startswith('c.')), None)
            if part: return bytes(rd(ent[part]['h']))
        raise LookupError(f'{leaf} not in {len(srcs)} pkgs (want {pk})')

    def _find_cob(s, name):
        c_name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
        cands = []
        for base in s._get_env_paths():
            for root, _, files in os.walk(base):
                for f in files:
                    if f.lower().endswith('.cob'):
                        cf = re.sub(r'[^a-zA-Z0-9]', '', f[:-4]).lower()
                        if c_name in cf or cf in c_name:
                            cands.append(os.path.join(root, f))
        for c in cands:
            if 'collide' in os.path.basename(c).lower(): return c
        return cands[0] if cands else None

    def _parse_cob(s, src):
        if isinstance(src, (bytes, bytearray)): d = src
        else:
            with open(src, 'rb') as f: d = f.read()
        _, vc, fc = struct.unpack_from('<III', d, 0)
        off = 12
        v = [struct.unpack_from('<fff', d, off + i * 12) for i in range(vc)]
        off += vc * 12
        faces = [struct.unpack_from('<III', d, off + i * 12) for i in range(fc)]
        return v, faces

    def _bake(s, vecs, faces):
        w_tris = {}
        obs_tris = []
        graph = {}
        w_hash = defaultdict(list)
        obs_hash = defaultdict(list)

        w_grid = {}
        w_verts = []
        m_indices = []
        for v in vecs:
            k = (round(v[0], 3), round(v[1], 3), round(v[2], 3))
            if k not in w_grid:
                w_verts.append(v)
                w_grid[k] = len(w_verts) - 1
            m_indices.append(w_grid[k])

        tid = 0
        e_map = defaultdict(list)
        gs = 2.0
        tri_edges = {}
        for i1, i2, i3 in faces:
            v1, v2, v3 = m_indices[i1], m_indices[i2], m_indices[i3]
            if v1 == v2 or v2 == v3 or v3 == v1: continue
            tri = Tri(tid, w_verts[v1], w_verts[v2], w_verts[v3], v1, v2, v3)
            gx0, gx1 = int(math.floor(tri.min_x / gs)), int(math.floor(tri.max_x / gs))
            gy0, gy1 = int(math.floor(tri.min_y / gs)), int(math.floor(tri.max_y / gs))
            gz0, gz1 = int(math.floor(tri.min_z / gs)), int(math.floor(tri.max_z / gs))
            if tri.ny >= 0.65:
                w_tris[tid] = tri
                ed1, ed2, ed3 = tuple(sorted([v1, v2])), tuple(sorted([v2, v3])), tuple(sorted([v3, v1]))
                tri_edges[tid] = (ed1, ed2, ed3)
                e_map[ed1].append(tid)
                e_map[ed2].append(tid)
                e_map[ed3].append(tid)
                for x in range(gx0, gx1 + 1):
                    for y in range(gy0, gy1 + 1):
                        for z in range(gz0, gz1 + 1):
                            w_hash[(x, y, z)].append(tri)
            else:
                obs_tris.append(tri)
                for x in range(gx0, gx1 + 1):
                    for y in range(gy0, gy1 + 1):
                        for z in range(gz0, gz1 + 1):
                            obs_hash[(x, y, z)].append(tri)
            tid += 1

        for t_id, tri in w_tris.items():
            eds = tri_edges.get(t_id, ())
            open_count = sum(1 for e in eds if len(e_map[e]) < 2)
            tri.pen = open_count * 2.5

        for edge, tids in e_map.items():
            if len(tids) >= 2:
                pA, pB = w_verts[edge[0]], w_verts[edge[1]]
                mid = ((pA[0] + pB[0]) / 2.0, (pA[1] + pB[1]) / 2.0, (pA[2] + pB[2]) / 2.0)
                for i in range(len(tids)):
                    for j in range(i + 1, len(tids)):
                        if tids[j] not in [n[0] for n in graph.get(tids[i], [])]:
                            graph.setdefault(tids[i], []).append((tids[j], mid, 0.0))
                            graph.setdefault(tids[j], []).append((tids[i], mid, 0.0))

        max_cd = int(math.ceil(s.max_fall / gs)) + 1
        total_w = max(1, len(w_tris))
        done = 0

        for t_id, tri in w_tris.items():
            done += 1
            if done % 4 == 0 or done == total_w:
                pushcall(lambda c=done, t=total_w: s._on_progress(c, t))

            for pA, pB in ((tri.p1, tri.p2), (tri.p2, tri.p3), (tri.p3, tri.p1)):
                ex, ez = pB[0] - pA[0], pB[2] - pA[2]
                elen = math.hypot(ex, ez)
                if elen < 1e-4: continue
                ux, uz = ex / elen, ez / elen

                mid_x, mid_z = (pA[0] + pB[0]) * 0.5, (pA[2] + pB[2]) * 0.5
                vx, vz = mid_x - tri.cx, mid_z - tri.cz
                nx, nz = (-uz, ux) if (-uz * vx + ux * vz) > 0 else (uz, -ux)

                for frac in (0.25, 0.5, 0.75):
                    px = pA[0] + ex * frac
                    py = pA[1] + (pB[1] - pA[1]) * frac
                    pz = pA[2] + ez * frac

                    for po in (0.0, 0.25):
                        qx = px + nx * po
                        qz = pz + nz * po
                        gx = int(math.floor(qx / gs))
                        gy = int(math.floor(py / gs))
                        gz = int(math.floor(qz / gs))

                        gcands = []
                        seen = set()
                        for oy in range(-max_cd, 2):
                            for ot in w_hash.get((gx, gy + oy, gz), []):
                                if ot.id == t_id or ot.id in seen: continue
                                seen.add(ot.id)
                                if ot.contains_2d(qx, qz):
                                    gcands.append((ot.height_at(qx, qz), ot))

                        if not gcands: continue
                        gcands.sort(key=lambda c: c[0], reverse=True)

                        for y_land, l_tri in gcands:
                            fall_d = py - y_land
                            if abs(fall_d) <= s.max_step:
                                tp = (qx, (py + y_land) / 2.0, qz)
                                if l_tri.id not in [x[0] for x in graph.get(t_id, [])]:
                                    graph.setdefault(t_id, []).append((l_tri.id, tp, 0.0))
                                    graph.setdefault(l_tri.id, []).append((t_id, tp, 0.0))
                                break
                            elif s.min_fall <= fall_d <= s.max_fall:
                                blocked = False
                                for oy in range(-max_cd, 2):
                                    for obs in obs_hash.get((gx, gy + oy, gz), []):
                                        if obs.contains_2d(qx, qz):
                                            oy_h = obs.height_at(qx, qz)
                                            if y_land < oy_h < py:
                                                blocked = True
                                                break
                                    if blocked: break

                                if not blocked:
                                    dp = (px + nx * 0.2, y_land, pz + nz * 0.2)
                                    if l_tri.id not in [x[0] for x in graph.get(t_id, [])]:
                                        graph.setdefault(t_id, []).append((l_tri.id, dp, fall_d))
                                break

        pushcall(lambda: s._on_done_bake(w_tris, obs_tris, graph, w_hash, obs_hash))

    def _on_progress(s, c, t):
        act = s._get_act()
        if not s.exploring or not act: return
        with act.context:
            s.prog = f"{c}/{t}"
            s.stream.push(f"I'm exploring {s.prog}")

    def _on_done_bake(s, w_tris, obs_tris, graph, w_hash, obs_hash):
        act = s._get_act()
        if not act: return
        with act.context:
            s.w_tris = w_tris
            s.obs_tris = obs_tris
            s.graph = graph
            s.w_hash = w_hash
            s.obs_hash = obs_hash
            s.exploring = False
            s.look_tmr = None
            s.stream.push("I see everything now.")
            if s.bot.node and s.bot.node.exists():
                s.bot.on_move_left_right(0.0)
                s.bot.on_move_up_down(-0.03)
                bs.timer(0.06, s._stop)
                bs.timer(0.12, s._jump_final)

    def _jump_final(s):
        act = s._get_act()
        if not act or not s.bot.node or not s.bot.node.exists(): return
        with act.context:
            s.bot.on_jump_press()
            bs.timer(0.1, s.bot.on_jump_release)

    def _get_tri(s, x, y, z):
        gs = 2.0
        gx, gy, gz = int(math.floor(x / gs)), int(math.floor(y / gs)), int(math.floor(z / gs))
        cands = []
        for oy in (-1, 0, 1):
            for tri in s.w_hash.get((gx, gy + oy, gz), []):
                if tri.contains_2d(x, z):
                    dy = abs(y - tri.height_at(x, z))
                    if dy < 1.0: cands.append((dy, tri))
        if cands:
            cands.sort(key=lambda c: c[0])
            return cands[0][1]
        best, min_d = None, float('inf')
        for tri in s.w_tris.values():
            d = (tri.cx - x)**2 + (tri.cy - y)**2 + (tri.cz - z)**2
            if d < min_d: min_d, best = d, tri
        return best

    def _find_path(s, start, goal):
        s_tri = s._get_tri(*start)
        g_tri = s._get_tri(*goal)
        if not s_tri or not g_tri or s_tri.id == g_tri.id: return [goal]

        frontier = []
        heapq.heappush(frontier, (0.0, s_tri.id))
        came = {s_tri.id: None}
        edge_pt = {s_tri.id: start}
        cost = {s_tri.id: 0.0}

        while frontier:
            _, curr = heapq.heappop(frontier)
            if curr == g_tri.id: break
            c_tri = s.w_tris[curr]
            for nxt, mid, fh in s.graph.get(curr, []):
                if fh > s.max_fall or (fh > 0.0 and fh < s.min_fall): continue
                n_tri = s.w_tris[nxt]
                d_step = math.dist((c_tri.cx, c_tri.cy, c_tri.cz), (n_tri.cx, n_tri.cy, n_tri.cz))
                step_cost = d_step * max(0.01, 1.0 - s.far_pref) if s.far_pref > 0.0 else d_step
                step_cost += n_tri.pen
                if fh > s.max_step:
                    step_cost += fh * 0.25
                nc = cost[curr] + step_cost
                if nxt not in cost or nc < cost[nxt]:
                    cost[nxt] = nc
                    h = math.dist((n_tri.cx, n_tri.cy, n_tri.cz), (g_tri.cx, g_tri.cy, g_tri.cz)) * 1.01
                    heapq.heappush(frontier, (nc + h, nxt))
                    came[nxt] = curr
                    edge_pt[nxt] = mid

        curr = g_tri.id
        p = []
        while curr is not None and curr != s_tri.id:
            if curr not in edge_pt: break
            p.append(edge_pt[curr])
            curr = came.get(curr)
        p.reverse()
        p.append(goal)
        return p

    def _dist_pt_line(s, px, py, ax, ay, bx, by):
        C, D = bx - ax, by - ay
        lsq = C * C + D * D
        param = ((px - ax) * C + (py - ay) * D) / lsq if lsq != 0 else -1
        if param < 0: xx, yy = ax, ay
        elif param > 1: xx, yy = bx, by
        else: xx, yy = ax + param * C, ay + param * D
        return math.hypot(px - xx, py - yy), xx, yy

    def _track_node(s, node_idx):
        def _worker():
            time.sleep(s.n_timeout)
            pushcall(lambda: s._chk_timeout(node_idx))
        threading.Thread(target=_worker, daemon=True).start()

    def _chk_timeout(s, node_idx):
        if s.idx != node_idx or not s.tgt: return
        act = s._get_act()
        if not act or not s.bot.node or not s.bot.node.exists() or not s.tgt.node or not s.tgt.node.exists(): return
        with act.context:
            bp = s.bot.node.position
            cp = s.tgt.node.position
            b_feet = (bp[0], bp[1] - 0.3, bp[2])
            c_feet = (cp[0], cp[1] - 0.3, cp[2])
            s.path = s._find_path(b_feet, c_feet)
            s.idx = 0
            s._track_node(0)

    def _start_nav(s, tgt):
        s.tgt = tgt
        act = s._get_act()
        if not s.bot.node or not tgt.node or not act: return
        bp, cp = s.bot.node.position, tgt.node.position
        b_feet = (bp[0], bp[1] - 0.3, bp[2])
        c_feet = (cp[0], cp[1] - 0.3, cp[2])
        s.path = s._find_path(b_feet, c_feet)
        s.idx = 0
        s._track_node(0)
        with act.context:
            s.m_tmr = bs.Timer(0.04, s._step, repeat=True)

    def _step(s):
        if not s.bot.node or not s.bot.node.exists() or not s.tgt or not s.tgt.node or not s.tgt.node.exists():
            s._stop()
            s.m_tmr = None
            return

        b_pos = s.bot.node.position
        c_pos = s.tgt.node.position
        b_feet = (b_pos[0], b_pos[1] - 0.3, b_pos[2])
        c_feet = (c_pos[0], c_pos[1] - 0.3, c_pos[2])
        d_call = math.dist(b_feet, c_feet)

        if d_call <= 1.2 and abs(b_feet[1] - c_feet[1]) <= 0.05:
            s._stop()
            s.m_tmr = None
            act = s._get_act()
            if act:
                with act.context:
                    s.stream.push("im here")
            s.path.clear()
            return

        if s.path and math.dist(c_feet, s.path[-1]) > 2.0:
            s.path = s._find_path(b_feet, c_feet)
            s.idx = 0
            s._track_node(0)

        if s.idx < len(s.path) - 1:
            wp = s.path[s.idx]
            for _ in range(3):
                if s.idx >= len(s.path) - 1: break
                wp = s.path[s.idx]
                hd = math.hypot(wp[0] - b_feet[0], wp[2] - b_feet[2])
                y_dist = abs(b_feet[1] - wp[1])
                # slopes: feet y never lines up with the waypoint, so use a
                # looser y and also count it reached once we're past it
                # along the path direction (else we overshoot and go back)
                nx_, nz_ = s.path[s.idx + 1][0] - wp[0], s.path[s.idx + 1][2] - wp[2]
                nl = math.hypot(nx_, nz_)
                passed = (nl > 1e-3 and hd < 1.0 and y_dist < 1.0 and
                          ((b_feet[0] - wp[0]) * nx_ + (b_feet[2] - wp[2]) * nz_) / nl > 0)
                if (hd <= s.fin_dist and y_dist <= 0.35) or passed:
                    s.idx += 1
                    wp = s.path[s.idx]
                    s._track_node(s.idx)
                else: break

            if s.far_pref > 0.0 and s.idx < len(s.path) - 1:
                look_idx = min(len(s.path) - 1, s.idx + int(math.ceil(s.far_pref * 3.0)))
                f_wp = s.path[look_idx]
                f_d3d = math.dist(f_wp, b_feet)
                if f_d3d <= (s.fin_dist + s.far_pref * 1.5) and abs(b_feet[1] - f_wp[1]) <= 0.05:
                    s.idx = look_idx
                    wp = s.path[s.idx]
                    s._track_node(s.idx)
        else:
            wp = c_feet

        dx, dz = wp[0] - b_feet[0], wp[2] - b_feet[2]
        d = math.hypot(dx, dz)
        if d > 0.05:
            nx, nz = dx / d, dz / d
            lx, lz = -nz, nx

            rep_x, rep_z = 0.0, 0.0
            gs = 2.0
            gx, gy, gz = int(math.floor(b_feet[0] / gs)), int(math.floor(b_feet[1] / gs)), int(math.floor(b_feet[2] / gs))
            b_radius = 1.0

            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    for oz in (-1, 0, 1):
                        for obs in s.obs_hash.get((gx + ox, gy + oy, gz + oz), []):
                            if obs.max_y < b_feet[1] or obs.min_y > b_feet[1] + 0.9: continue
                            for pA, pB in [(obs.p1, obs.p2), (obs.p2, obs.p3), (obs.p3, obs.p1)]:
                                dist, px, pz = s._dist_pt_line(b_feet[0], b_feet[2], pA[0], pA[2], pB[0], pB[2])
                                if 0.001 < dist < b_radius:
                                    f = ((b_radius - dist) / b_radius) ** 2
                                    rep_x += ((b_feet[0] - px) / dist) * f * 1.5
                                    rep_z += ((b_feet[2] - pz) / dist) * f * 1.5

            lat_f = max(-1.0, min(1.0, (rep_x * lx + rep_z * lz)))
            sx = nx + lx * lat_f
            sz = nz + lz * lat_f
            smag = math.hypot(sx, sz)
            if smag > 0.001: sx, sz = sx / smag, sz / smag

            spd = 1.0 if d_call > 2.5 else max(0.25, d_call / 2.5)
            s.bot.on_move_left_right(sx * spd)
            s.bot.on_move_up_down(-sz * spd)
        else:
            s._stop()

    def _stop(s):
        if s.bot.node and s.bot.node.exists():
            s.bot.on_move_left_right(0.0)
            s.bot.on_move_up_down(0.0)

    def _draw_path(s):
        for n in s.v_nodes:
            if n: n.delete()
        s.v_nodes.clear()
        act = s._get_act()
        if not s.bot.node or not s.bot.node.exists() or not s.path or not act: return
        with act.context:
            for wp in s.path[s.idx:]:
                n = bs.newnode('locator', attrs={'position': wp, 'color': (0.2, 1.0, 0.4), 'shape': 'circle', 'size': [0.4]})
                s.v_nodes.append(n)

    # --- debug: mesh dots in a sphere around her while she walks ---
    # green = walkable tri, red = not. Tune these.
    DOT_R = 2.5      # sphere radius
    DOT_STEP = 0.5   # sample spacing on big triangles
    DOT_MAX = 220    # max dots (nearest kept)
    DOT_SIZE = 0.01  # text scale

    def _tri_pts(s, t):
        e = max(math.dist(t.p1, t.p2), math.dist(t.p2, t.p3), math.dist(t.p3, t.p1))
        n = max(1, min(8, int(e / s.DOT_STEP)))
        pts = []
        for i in range(n + 1):
            for j in range(n + 1 - i):
                a, b = i / n, j / n
                c = 1.0 - a - b
                pts.append((t.p1[0] * c + t.p2[0] * a + t.p3[0] * b,
                            t.p1[1] * c + t.p2[1] * a + t.p3[1] * b,
                            t.p1[2] * c + t.p2[2] * a + t.p3[2] * b))
        return pts

    def _dots_collect(s, pos):
        R = s.DOT_R
        gs = 2.0
        x, y, z = pos
        g0 = [int(math.floor((v - R) / gs)) for v in pos]
        g1 = [int(math.floor((v + R) / gs)) for v in pos]
        seen = set()
        out = {}
        for tbl, walk in ((s.obs_hash, False), (s.w_hash, True)):
            for gx in range(g0[0], g1[0] + 1):
                for gy in range(g0[1], g1[1] + 1):
                    for gz in range(g0[2], g1[2] + 1):
                        for t in tbl.get((gx, gy, gz), ()):
                            if t.id in seen: continue
                            seen.add(t.id)
                            dx = max(t.min_x - x, 0.0, x - t.max_x)
                            dy = max(t.min_y - y, 0.0, y - t.max_y)
                            dz = max(t.min_z - z, 0.0, z - t.max_z)
                            if dx * dx + dy * dy + dz * dz > R * R: continue
                            for p in s._tri_pts(t):
                                d = math.dist(p, pos)
                                if d > R: continue
                                k = (round(p[0], 2), round(p[1], 2), round(p[2], 2))
                                if walk or k not in out: out[k] = (d, p, walk)
        return sorted(out.values(), key=lambda v: v[0])[:s.DOT_MAX]

    def _clear_dots(s):
        act = s._get_act()
        for n in s.dot_nodes:
            try:
                if n: n.delete()
            except Exception: pass
        s.dot_nodes = []
        s.dot_last = None

    def _dots_tick(s):
        act = s._get_act()
        if not act: return
        walking = (s.m_tmr is not None and not s.exploring and s.w_tris
                   and s.bot.node and s.bot.node.exists())
        if not walking:
            if s.dot_nodes: s._clear_dots()
            return
        pos = tuple(s.bot.node.position)
        if s.dot_last and math.dist(pos, s.dot_last) < 0.2: return
        s.dot_last = pos
        items = s._dots_collect(pos)
        with act.context:
            nodes = s.dot_nodes
            for i, (d, p, walk) in enumerate(items):
                col = (0.1, 1.0, 0.2) if walk else (1.0, 0.1, 0.1)
                if i < len(nodes):
                    nodes[i].position = p
                    nodes[i].color = col
                else:
                    nodes.append(bs.newnode('text', attrs={'text': '\u2022', 'in_world': True, 'position': p, 'color': col, 'scale': s.DOT_SIZE, 'flatness': 1.0, 'shadow': 0.0, 'h_align': 'center', 'v_align': 'center'}))
            while len(nodes) > len(items):
                n = nodes.pop()
                if n: n.delete()

    def _chk_chat(s):
        m = bs.get_chat_messages()
        if m != s.last_msgs:
            if m:
                last = m[-1]
                snd, cnt = last.split(': ', 1) if ': ' in last else (None, last)
                cmd = cnt.strip().lower()
                if cmd == 'hitomi': s._cmd_hitomi(snd)
                elif cmd == 'come': s._cmd_come(snd)
            s.last_msgs = m

    def _cmd_hitomi(s, snd):
        act = s._get_act()
        if not act: return
        with act.context:
            if s.exploring:
                s.stream.push(f"not now {s.prog}")
                return
            c = s._get_caller(snd)
            if c and c.node and c.node.exists() and s.bot.node and s.bot.node.exists():
                bp = s.bot.node.position
                cp = c.node.position
                dx, dz = cp[0] - bp[0], cp[2] - bp[2]
                d = math.hypot(dx, dz)
                if d > 0.01:
                    s.bot.on_move_left_right((dx / d) * 0.02)
                    s.bot.on_move_up_down((-dz / d) * 0.02)
                    bs.timer(0.04, s._stop)
            s.stream.push('Processing Mesh...')

    def _cmd_come(s, snd):
        act = s._get_act()
        if not act: return
        with act.context:
            if s.exploring:
                s.stream.push(f"not now {s.prog}")
                return
            c = s._get_caller(snd)
            if c and c.node and c.node.exists(): s._start_nav(c)
            else: s.stream.push("Target lost.")

    def _get_caller(s, name):
        act = s._get_act()
        if not act or not hasattr(act, 'players'): return None
        if name:
            for p in act.players:
                try:
                    if name.lower() in (p.getname(full=True).lower(), p.getname(full=False).lower()):
                        if p.actor and p.actor.node and p.actor.node.exists(): return p.actor
                except: pass
        closest, min_d = None, float('inf')
        bp = s.bot.node.position if s.bot.node else (0, 0, 0)
        for p in act.players:
            try:
                if p.actor and p.actor.node and p.actor.node.exists() and p.actor is not s.bot:
                    d = math.dist(bp, p.actor.node.position)
                    if d < min_d: min_d, closest = d, p.actor
            except: pass
        return closest


class Stream:
    def __init__(s, head, res='\u2588', resw=19.0):
        act = bs.getactivity()
        s.act_ref = weakref.ref(act) if act else None
        s.head, s.res, s.resw, s.text, s.bye = head, res, resw, '', None
        with act.context:
            s.node = bs.newnode('math', delegate=s, attrs={'input1': (0, 0, 0), 'operation': 'add'})
            head.connectattr('position', s.node, 'input2')
            s.kids = [bs.newnode('text', owner=s.node, attrs={'in_world': True, 'scale': 0.01, 'flatness': 1, 'h_align': 'center', 'color': (c, c, c)}) for c in (0, 0.85)]
            for k in s.kids: s.node.connectattr('output', k, 'position')

    def _get_act(s):
        if s.act_ref:
            act = s.act_ref()
            if act and not act.has_ended():
                return act
        act = bs.getactivity()
        if act and not act.has_ended():
            return act
        return None

    def push(s, t=''):
        s.bye = None
        if not t: s.anim(1, 0); s.text = t; return
        ls = len(t.splitlines())
        s.node.input1 = (0, 1.3 + 0.32 * ls, 0)
        s.kids[0].text = (round(get_string_width(t, suppress_warning=True) / s.resw + 1) * s.res + '\n') * ls
        s.kids[1].text = t
        if not s.text: s.anim(0, 1)
        s.text = t
        act = s._get_act()
        if act and hasattr(act, 'context'):
            with act.context:
                s.bye = bs.Timer(3.5, s.push)
        else:
            s.bye = bs.Timer(3.5, s.push)

    def anim(s, a, b):
        try: [bs.animate(k, 'opacity', {0: a, 0.2: b}) for k in s.kids]
        except: pass


# ba_meta require api 9
# ba_meta export bascenev1.GameActivity
class HitomiDebugGame(bs.TeamGameActivity[bs.Player, bs.Team]):
    name = 'Playground v2'
    description = 'Hitomi Analytic Mesh Testing.'

    @classmethod
    def get_supported_maps(cls, sessiontype):
        return bs.app.classic.getmaps('melee')

    @classmethod
    def supports_session_type(cls, sessiontype):
        return True

    def get_instance_description(self): return 'Math-Driven Pathfinding'
    def get_instance_description_short(self): return 'Perfect Pathing'

    def __init__(self, settings):
        super().__init__(settings)
        self.default_music = bs.MusicType.GRAND_ROMP
        self.hitomi = None

    def on_begin(self):
        super().on_begin()
        pos = self.map.ffa_spawn_points[0]
        self.hitomi = Hitomi(pos)

    def handlemessage(self, msg):
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            self.respawn_player(msg.getplayer(bs.Player))
        else:
            super().handlemessage(msg)
