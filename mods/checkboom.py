# Copyright 2026 - Solely by BrotherBoard
# Feel free to use this anywhere
# Bug? Feedback? Discord >> @BrotherBoard

"""
Checkboom v1.0 - Get SpazMated

Simple turn based game I made because bored.
Experimental. Adds a Team game.
"""

import bauiv1 as bui
import bascenev1 as bs
from collections import defaultdict, deque
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.spaz import Spaz

class Checkboard(bs.Map):
    name = 'Checkboard'
    defs = type('',(),{
        'points':{
            'spawn1': (0, 0, 5, 0, 0, 5),
            'spawn2': (0, 0, -5, 0, 0, -5),
        },
        'boxes':{
            'area_of_interest_bounds': (0,0,0, 0,0,0, 10,10,10),
            'map_bounds': (0,0,0, 0,0,0, 20,20,20),
        }
    })

    @classmethod
    def get_preview_texture_name(cls):
        return 'checkboom'

    def __init__(self):
        super().__init__()
        shared = SharedObjects.get()

        floor_material = bs.Material()
        floor_material.add_actions(
            conditions=('they_are_older_than', -1),
            actions=(
                ('modify_part_collision', 'physical', True),
                ('modify_part_collision', 'collide', True),
            )
        )

        self.node = bs.newnode(
            'region',
            attrs={
                'position': (0, -0.001, 0),
                'type': 'box',
                'scale': (20, 0.001, 20),
                'materials': [floor_material, shared.footing_material]
            }
        )

        self.tiles = []
        self.fills = {}
        tile_size = 1.0
        board_dim = 8
        offset = (board_dim * tile_size) / 2 - (tile_size / 2)
        for row in range(board_dim):
            for col in range(board_dim):
                x = col * tile_size - offset
                z = row * tile_size - offset
                # box
                tile = bs.newnode(
                    'locator',
                    attrs={
                        'position': (x, 0, z),
                        'size': (tile_size, 0.01, tile_size),
                        'color': (1, 1, 1),
                        'shape': 'box',
                        'opacity': 1.0
                    }
                )
                self.tiles.append(tile)
                # circle
                fill = bs.newnode(
                    'locator',
                    attrs={
                        'shape': 'circle',
                        'position': (x, 0.005, z),
                        'size': (tile_size * 0.9,),
                        'color': (1, 1, 1),
                        'opacity': 0.0,
                        'additive': True,
                        'draw_beauty': True
                    }
                )
                self.fills[(round(x, 1), round(z, 1))] = fill

class Piece(Spaz):
    def __init__(self, *args, game=None, team_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.game = game
        self.team_id = team_id
        self.can_take_damage = False
        self.claimed_by = None
        self.source_player = None

    def handlemessage(self, msg):
        if isinstance(
            msg, bs.HitMessage
        ):
            puncher = msg.get_source_player(bs.Player)
            if (
                msg.hit_type == 'punch'
                and puncher is not None
                and puncher.team.id == self.team_id
            ):
                self.game.claim_spaz(puncher, self)
            if not self.can_take_damage:
                return
        # drop
        elif isinstance(msg, bs.PickedUpMessage):
            if msg.node and any(p.actor and p.actor.node == msg.node and p.team.id != self.team_id for p in self.game.memory['players'].values()):
                msg.node.hold_node = None
        # die
        elif isinstance(msg, bs.DieMessage):
            self.game.stop_run(self)
            if not msg.immediate:
                self.game.respawn_spaz(self)
                return
        super().handlemessage(msg)

# ba_meta export bascenev1.GameActivity
class Checkboom(bs.TeamGameActivity[bs.Player,bs.Team]):
    name = 'Checkboom'
    description = 'A turn-based game.\nVersion 1.0'

    @classmethod
    def supports_session_type(cls, type):
        return True

    def get_availabe_settings(self):
        return []

    def get_supported_maps(self):
        return ['Checkboard']

    def get_instance_description(self):
        return 'That\'s how it\'s done'

    def get_instance_description_short(self):
        return 'Version 1.0'

    @property
    def playing(self):
        return self.memory.get('playing', False)

    @playing.setter
    def playing(self, val):
        self.memory['playing'] = val

    def __init__(self, settings):
        super().__init__(settings)
        self.default_music = bs.MusicType.GRAND_ROMP
        self.memory = defaultdict(dict)
        self.playing = False
        # subtext
        self.subtext = bs.newnode(
            'text',
            attrs={
                'v_attach': 'top',
                'h_align': 'center',
                'position': (0,-50)
            }
        )
        # legend
        self.legend = []
        for i, (tex, c, t) in enumerate((
            ('buttonPunch', (1, 1, 0.4), 'Control'),
            ('buttonBomb', (1, 0, 0), 'Release'),
        )):
            y = 40 - i * 50
            # pic
            self.legend.append(bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture(tex),
                    'absolute_scale': True,
                    'attach': 'centerLeft',
                    'position': (30, y),
                    'scale': (50, 50),
                    'color': c,
                    'opacity': 0
                }
            ))
            # lbl
            self.legend.append(bs.newnode(
                'text',
                attrs={
                    'text': t,
                    'h_attach': 'left',
                    'v_attach': 'center',
                    'position': (60, y),
                    'v_align': 'center',
                    'color': c,
                    'opacity': 0
                }
            ))

    def on_begin(self):
        super().on_begin()
        bs.getsession().max_players = 2
        # bounds
        self.memory['timers']['bounds'] = bs.Timer(0.1, self.bounds_tick, repeat=True)
        self.sanity_tick()

    def alert(self, text, color=(1,1,1)):
        self.subtext.text = text
        self.subtext.color = color

    def start_run(self, piece):
        if not piece or not piece.node:
            return
        pid = id(piece)
        def run_tick():
            if not piece.node or not piece.is_alive() or piece.claimed_by is not None:
                self.stop_run(piece)
                return

            # Stop running if close to square (within 2 squares' width worth)
            sq = self.memory['squares'].get(piece)
            if sq:
                px, _, pz = piece.node.position
                dist = ((sq[0] - px) ** 2 + (sq[1] - pz) ** 2) ** 0.5
                if dist <= 2.0:
                    piece.on_run(0)
                    return

            piece.on_run(0)
            self.memory['timers'][f'run_pulse_{pid}'] = bs.Timer(
                0.01, lambda: piece.node and piece.on_run(1)
            )

        run_tick()
        self.memory['timers'][f'run_{pid}'] = bs.Timer(0.1, run_tick, repeat=True)

    def stop_run(self, piece):
        if not piece:
            return
        pid = id(piece)
        self.memory['timers'][f'run_{pid}'] = None
        self.memory['timers'][f'run_pulse_{pid}'] = None
        if piece.node:
            piece.on_run(0)

    def on_bomb_press(self, player):
        if self.memory.get('can_start') and not self.memory.get('started'):
            self.memory['started'] = True
            self.alert('')
            bs.getsound('activateBeep').play()

    def assign_controls(self, player, target):
        player.resetinput()
        for name, handler in (
            ('UP_DOWN', target.on_move_up_down),
            ('LEFT_RIGHT', target.on_move_left_right),
            ('RUN', target.on_run),
            ('JUMP_PRESS', target.on_jump_press),
            ('JUMP_RELEASE', target.on_jump_release),
            ('PUNCH_PRESS', target.on_punch_press),
            ('PUNCH_RELEASE', target.on_punch_release),
            ('PICK_UP_PRESS', target.on_pickup_press),
            ('PICK_UP_RELEASE', target.on_pickup_release),
        ):
            player.assigninput(getattr(bs.InputType, name), handler)

        if isinstance(target, Piece):
            player.assigninput(bs.InputType.BOMB_PRESS, bs.CallPartial(self.release_control, player, target))
            player.assigninput(bs.InputType.BOMB_RELEASE, lambda: None)
        else:
            player.assigninput(bs.InputType.BOMB_PRESS, bs.CallPartial(self.on_bomb_press, player))
            player.assigninput(bs.InputType.BOMB_RELEASE, lambda: None)

    def on_player_join(self, player):
        super().on_player_join(player)
        actor = player.actor
        actor.orig_pos = self.map.defs.points[f'spawn{player.team.id+1}'][:3]
        actor.orig_rot = 0 if player.team.id else 180
        actor.handlemessage = lambda msg, _actor=actor: self.handlemessage(_actor, msg)
        # color
        self.memory['team_colors'][player.team.id] = getattr(player.team, 'color', actor.node.color)
        # pickup
        old_pick = actor.on_pickup_press
        def safe_pick():
            old_pick()
            def chk():
                if actor.node and actor.node.hold_node:
                    for tid, bots in self.memory['spazzes'].items():
                        if tid != player.team.id and any(b and b.node == actor.node.hold_node for b in bots):
                            actor.node.hold_node = None
            self.memory['timers'][f'pick1_{id(actor)}'] = bs.Timer(0.01, chk)
            self.memory['timers'][f'pick2_{id(actor)}'] = bs.Timer(0.05, chk)
        actor.on_pickup_press = safe_pick
        actor.handlemessage(
            bs.StandMessage(
                actor.orig_pos,
                actor.orig_rot
            )
        )
        self.assign_controls(player, actor)
        self.memory['players'][player.team.id] = player
        self.sanity_tick()

    def on_player_leave(self, player):
        # uncontrol
        if target := self.memory['control'].get(player.team.id):
            self.release_control(player, target)
        # kill
        if player.actor:
            if player.actor.node:
                player.actor.node.delete()
            player.actor = None
        super().on_player_leave(player)
        self.memory['players'].pop(player.team.id, None)
        self.sanity_tick()

    def handlemessage(self, actor, msg):
        if not actor or not actor.node: return
        if isinstance(msg, bs.HitMessage): return
        # die
        if isinstance(msg, bs.DieMessage):
            if not msg.immediate:
                self.respawn_spaz(actor)
                return
        return type(actor).handlemessage(actor, msg)

    def sanity_tick(self):
#        if len(self.players) == 2:
        if len(self.players) > 0: # XXX DEBUG
            self.alert('Get ready')
            if not self.playing:
                self.start_game()
        else:
            self.alert('Waiting for players', (1, 1, 0))
            if self.playing:
                self.stop_game()

    def start_game(self):
        self.playing = True
        self.memory['timers']['swarm'] = bs.Timer(
            3, self.spawn
        )

    def spawn(self):
        self.alert('Place your pieces')
        bs.getsound('spawn').play()

        characters = ['Zoe', 'Agent Johnson', 'Pixel', 'Spaz', 'Kronk']

        board_edge = 4.0
        deck_x_min = -board_edge
        deck_x_max = board_edge
        spacing = (deck_x_max - deck_x_min) / (len(characters) - 1)

        self.memory['kings'] = {}
        for team_id, player in self.memory['players'].items():
            spawn_z = self.map.defs.points[f'spawn{team_id+1}'][2]
            side = 1 if spawn_z > 0 else -1
            spawn_offset = spawn_z - side * board_edge
            deck_z = side * board_edge + spawn_offset * 2
            rotation = 0 if team_id else 180

            # king
            ksq = (0.5, 3.5 if side > 0 else -3.5)
            self.memory['kings'][team_id] = ksq
            col = self.get_team_color(team_id)
            self.highlight_tile(ksq, color=self.neon(*col), active=True)

            self.memory['spazzes'][team_id] = []
            for i, character in enumerate(characters):
                x = deck_x_min + spacing * i
                bot = Piece(
                    character=character,
                    start_invincible=False,
                    game=self,
                    team_id=team_id
                )
                bot.orig_pos = (x, 0, deck_z)
                bot.orig_rot = rotation
                bot.handlemessage(
                    bs.StandMessage(
                        bot.orig_pos,
                        bot.orig_rot
                    )
                )
                # color
                bot.node.color = (1, 1, 1)
                bot.node.highlight = self.get_team_color(team_id)
                self.memory['spazzes'][team_id].append(bot)
                self.retain(bot)
                self.start_run(bot)

        # fade
        self.memory['timers']['legend'] = arr = []
        for n in self.legend:
             arr.append(bs.Timer(1, bs.animate(n, 'opacity', {0: 0, 0.6: 0.7}).delete))

    def claim_spaz(self, player, target):
        if target.claimed_by is not None:
            return

        # kill
        self.memory['timers'][f'retain_{id(target)}'] = None
        self.stop_run(target)

        origin = player.actor
        prev = self.memory['control'].get(player.team.id)

        # release
        losing = prev or origin
        losing.node.hold_node = None

        target.claimed_by = player.team.id
        target.source_player = player
        self.memory['control'][player.team.id] = target

        bs.getsound('gunCocking').play(1.0, position=target.node.position)
        target.node.handlemessage('flash')

        if prev is None:
            # swap
            self.memory['swap'][player.team.id] = (
                origin.node.name, origin.node.name_color,
                origin.node.color, origin.node.highlight
            )
            origin.node.name = ''

            # fade
            bs.animate_array(origin.node, 'color', 3, {0: origin.node.color, 0.3: (0.5,0.5,0.5)})
            bs.animate_array(origin.node, 'highlight', 3, {0: origin.node.highlight, 0.3: (0.5,0.5,0.5)})

            # paralyze
            origin.on_move_up_down(0)
            origin.on_move_left_right(0)

            self.knockdown(player.team.id, origin)
        else:
            # switch
            prev.claimed_by = None
            prev.source_player = None
            prev.node.name = ''

            # paralyze
            prev.on_move_up_down(0)
            prev.on_move_left_right(0)

            # square
            self.handle_release(prev)
            self.start_run(prev)

        name, name_color = self.memory['swap'][player.team.id][:2]
        target.node.name = name
        target.node.name_color = name_color

        # controls
        self.assign_controls(player, target)

    def release_control(self, player, target):
        if self.memory['control'].get(player.team.id) is not target:
            return

        self.memory['control'][player.team.id] = None
        self.memory['timers'][f'knock{player.team.id}'] = None
        target.claimed_by = None
        target.source_player = None

        # release
        target.node.hold_node = None

        bs.getsound('laser').play(1.0, position=target.node.position)

        # paralyze
        target.on_move_up_down(0)
        target.on_move_left_right(0)

        # square
        self.handle_release(target)
        self.start_run(target)

        # unswap
        if target.node:
            target.node.name = ''
        name, name_color, color, highlight = self.memory['swap'].pop(player.team.id)
        if player.actor and player.actor.node:
            player.actor.node.name = name
            player.actor.node.name_color = name_color
            # unfade
            bs.animate_array(player.actor.node, 'color', 3, {0: player.actor.node.color, 0.3: color})
            bs.animate_array(player.actor.node, 'highlight', 3, {0: player.actor.node.highlight, 0.3: highlight})
            self.assign_controls(player, player.actor)

    def handle_release(self, piece):
        if not piece or not piece.node:
            return
        px, _, pz = piece.node.position
        side = 1 if self.map.defs.points[f'spawn{piece.team_id+1}'][2] > 0 else -1
        rows = (6, 7) if side > 0 else (0, 1)
        # bounds
        if -4.0 <= px <= 4.0 and -4.0 <= pz <= 4.0 and (side * pz > 0):
            # squares
            occupied = {v for k, v in self.memory['squares'].items() if k is not piece and k.is_alive()}
            occupied.update(self.memory['kings'].values())
            free = [
                (c - 3.5, r - 3.5)
                for r in rows for c in range(8)
                if (c - 3.5, r - 3.5) not in occupied
            ]
            if free:
                # unlight
                if prev_sq := self.memory['squares'].get(piece):
                    self.highlight_tile(prev_sq, active=False)

                sq = min(free, key=lambda s: (s[0] - px)**2 + (s[1] - pz)**2)
                self.memory['squares'][piece] = sq

                # light
                c = self.get_team_color(piece.team_id)
                self.highlight_tile(sq, color=c, active=True)

                # color
                self.recolor(piece, occupied=True)
                self.retain(piece)
                return
        # clear
        if old_sq := self.memory['squares'].pop(piece, None):
            self.highlight_tile(old_sq, active=False)
        self.recolor(piece, occupied=False)
        self.retain(piece)

    def path(self, piece, pos, sq):
        px, pz = pos
        sx, sz = sq
        sc, sr = int(round(px + 3.5)), int(round(pz + 3.5))
        ec, er = int(round(sx + 3.5)), int(round(sz + 3.5))

        if (sc, sr) == (ec, er):
            return sq

        # Blocks: only avoid occupied squares (assigned squares of other pieces + kings)
        blocked = set()
        for p, s in self.memory['squares'].items():
            if p is not piece and p.is_alive():
                blocked.add((int(round(s[0] + 3.5)), int(round(s[1] + 3.5))))
        for k in self.memory['kings'].values():
            blocked.add((int(round(k[0] + 3.5)), int(round(k[1] + 3.5))))
        blocked.discard((ec, er))

        def bfs(allow_outside: bool):
            if not allow_outside:
                if not (0 <= sc < 8 and 0 <= sr < 8):
                    return None
                min_c, max_c = 0, 7
                min_r, max_r = 0, 7
            else:
                min_c = max(-5, min(-2, sc - 1))
                max_c = min(12, max(9, sc + 1))
                min_r = max(-5, min(-2, sr - 1))
                max_r = min(12, max(9, sr + 1))

            q = deque([(sc, sr)])
            prev = {(sc, sr): None}
            found = False

            while q:
                c, r = q.popleft()
                if (c, r) == (ec, er):
                    found = True
                    break
                neighbors = [(c + dc, r + dr) for dc, dr in ((0, 1), (0, -1), (1, 0), (-1, 0))]
                neighbors.sort(key=lambda n: (n[0] - ec) ** 2 + (n[1] - er) ** 2)
                for nc, nr in neighbors:
                    if (
                        min_c <= nc <= max_c
                        and min_r <= nr <= max_r
                        and (nc, nr) not in blocked
                        and (nc, nr) not in prev
                    ):
                        prev[(nc, nr)] = (c, r)
                        q.append((nc, nr))

            if not found:
                return None

            curr = (ec, er)
            trace = []
            while curr != (sc, sr):
                trace.append(curr)
                curr = prev[curr]

            nxt = trace[-1]
            return sq if nxt == (ec, er) else (nxt[0] - 3.5, nxt[1] - 3.5)

        # 1. Try path strictly inside grid
        res = bfs(allow_outside=False)
        if res is not None:
            return res

        # 2. Last resort fallback: whitelist pathing outside grid
        return bfs(allow_outside=True)

    def check_kings(self):
        # ready
        teams_ready = {}
        both_in = True
        for tid, ksq in self.memory['kings'].items():
            bots = self.memory['spazzes'].get(tid, [])
            teams_ready[tid] = len(bots) > 0 and all(b in self.memory['squares'] for b in bots)
            player = self.memory['players'].get(tid)
            p_in = False
            if player and player.actor and player.actor.node:
                px, _, pz = player.actor.node.position
                p_in = abs(px - ksq[0]) < 0.5 and abs(pz - ksq[1]) < 0.5
            if not p_in:
                both_in = False

            # state
            st = 'in' if p_in else 'fade'
            if st != self.memory['glow'].get(tid):
                self.memory['glow'][tid] = st
                if node := self.map.fills.get((round(ksq[0], 1), round(ksq[1], 1))):
                    c = self.get_team_color(tid)
                    if st == 'in':
                        bs.animate_array(node, 'color', 3, {0.0: node.color, 0.2: self.neon(*c)})
                    else:
                        bs.animate_array(node, 'color', 3, {0.0: c, 0.8: c, 1.1: self.neon(*c), 1.4: c}, loop=True)

        if self.memory.get('started'):
            return

        # alert
        req = 2 if len(self.players) >= 2 else 1
        both_ready = len(self.memory['players']) >= req and all(teams_ready.get(tid, False) for tid in self.memory['players'])
        if not both_ready:
            self.alert('Place your pieces')
            self.memory['can_start'] = False
            return

        if both_in:
            self.alert(f'Press {bui.charstr(bui.SpecialChar.RIGHT_BUTTON)}BOMB to start')
            self.memory['can_start'] = True
        else:
            self.alert('Stand in position')
            self.memory['can_start'] = False

    def retain(self, piece):
        cnt = [0]
        def tick():
            cnt[0] += 1
            # dead
            if not piece.node or not piece.is_alive():
                self.memory['timers'][f'retain_{id(piece)}'] = None
                if old_sq := self.memory['squares'].pop(piece, None):
                    self.highlight_tile(old_sq, active=False)
                return
            # controlled
            if piece.claimed_by is not None or not self.playing:
                self.memory['timers'][f'retain_{id(piece)}'] = None
                return
            # drop
            for p in self.memory['players'].values():
                if p.actor and p.actor.node and p.actor.node.hold_node == piece.node and p.team.id != piece.team_id:
                    p.actor.node.hold_node = None
            # held
            holders = [
                p.actor for p in self.memory['players'].values() if p.actor and p.actor.node
            ] + [
                b for team in self.memory['spazzes'].values() for b in team if b and b.node
            ]
            if any(getattr(h.node, 'hold_node', None) == piece.node for h in holders):
                # jump
                if cnt[0] % 5 == 0:
                    piece.on_jump_press()
                    piece.on_jump_release()
                piece.on_move_up_down(0)
                piece.on_move_left_right(0)
                return

            px, _, pz = piece.node.position
            side = 1 if self.map.defs.points[f'spawn{piece.team_id+1}'][2] > 0 else -1

            # walk
            sq = self.memory['squares'].get(piece)
            if sq:
                tgt = self.path(piece, (px, pz), sq)
                if tgt is None:
                    piece.on_move_left_right(0)
                    piece.on_move_up_down(0)
                    return

                # walk
                dx, dz = tgt[0] - px, tgt[1] - pz
                dist = (dx * dx + dz * dz) ** 0.5
                if tgt != sq or dist > 0.08:
                    piece.on_move_left_right(max(-1.0, min(1.0, dx * 3)))
                    piece.on_move_up_down(max(-1.0, min(1.0, -dz * 3)))
                else:
                    # look
                    if cnt[0] % 30 == 0 and (plr := self.memory['players'].get(piece.team_id)) and plr.actor and plr.actor.node:
                        mx, _, mz = plr.actor.node.position
                        vx, vz = mx - px, mz - pz
                        l = (vx * vx + vz * vz) ** 0.5 or 1
                        piece.on_move_left_right((vx / l) * 0.05)
                        piece.on_move_up_down((-vz / l) * 0.05)
                    else:
                        # stop
                        piece.on_move_left_right(0)
                        piece.on_move_up_down(0)
            else:
                # enemy
                if side * pz < 0:
                    dz = side * 1.5 - pz
                    piece.on_move_left_right(max(-1.0, min(1.0, -px * 2)))
                    piece.on_move_up_down(max(-1.0, min(1.0, -dz * 3)))
                else:
                    # stop
                    piece.on_move_left_right(0)
                    piece.on_move_up_down(0)

        self.memory['timers'][f'retain_{id(piece)}'] = bs.Timer(0.1, tick, repeat=True)

    def knockdown(self, team_id, origin):
        def tick():
            if (target := self.memory['control'].get(team_id)) is None or not origin.node:
                self.memory['timers'][f'knock{team_id}'] = None
                return
            origin.node.handlemessage('knockout', 100)
            # bounds
            if target.node:
                tx, _, tz = target.node.position
                if not (-4.0 <= tx <= 4.0 and -4.0 <= tz <= 4.0):
                    if target in self.memory['squares']:
                        old_sq = self.memory['squares'].pop(target, None)
                        self.highlight_tile(old_sq, active=False)
                        self.recolor(target, occupied=False)

        self.memory['timers'][f'knock{team_id}'] = bs.Timer(0.09, tick, repeat=True)

    def bounds_tick(self):
        # players
        for p in self.memory['players'].values():
            if p.actor and p.actor.node:
                x, y, z = p.actor.node.position
                if y < -1.0 or not (-10.0 <= x <= 10.0 and -10.0 <= z <= 10.0):
                    self.respawn_spaz(p.actor)
        # pieces
        for team in self.memory['spazzes'].values():
            for b in team:
                if b and b.node:
                    x, y, z = b.node.position
                    if y < -1.0 or not (-10.0 <= x <= 10.0 and -10.0 <= z <= 10.0):
                        self.respawn_spaz(b)
        self.check_kings()

    def respawn_spaz(self, spaz):
        if not spaz or not spaz.node:
            return
        pos = getattr(spaz, 'orig_pos', None)
        rot = getattr(spaz, 'orig_rot', 0)
        if not pos:
            return
        # drop
        spaz.node.hold_node = None
        # paralyze
        spaz.on_move_up_down(0)
        spaz.on_move_left_right(0)
        # teleport
        spaz.handlemessage(bs.StandMessage(pos, rot))
        # piece
        if isinstance(spaz, Piece):
            self.start_run(spaz)
            if old_sq := self.memory['squares'].pop(piece := spaz, None):
                self.highlight_tile(old_sq, active=False)
            self.recolor(spaz, occupied=False)
            # release
            if spaz.claimed_by is not None:
                if plr := self.memory['players'].get(spaz.claimed_by):
                    self.release_control(plr, spaz)

    def neon(self,a,b,c,z=4):
        return (
            a*z,b*z,c*z
        )

    def get_team_color(self, team_id):
        if c := self.memory['team_colors'].get(team_id):
            return c
        if team_id in self.memory['swap']:
            return self.memory['swap'][team_id][2]
        if (plr := self.memory['players'].get(team_id)):
            c = getattr(plr.team, 'color', None)
            if c:
                self.memory['team_colors'][team_id] = c
                return c
            if plr.actor and plr.actor.node and plr.actor.node.color != (0.5, 0.5, 0.5):
                self.memory['team_colors'][team_id] = plr.actor.node.color
                return plr.actor.node.color
        return (1, 1, 1)

    def recolor(self, piece, occupied=False):
        if not piece or not piece.node:
            return
        c = self.get_team_color(piece.team_id)
        tc = self.neon(*c) if occupied else (1, 1, 1)
        th = self.neon(*c) if occupied else c
        # fade
        bs.animate_array(piece.node, 'color', 3, {0: piece.node.color, 0.3: tc})
        bs.animate_array(piece.node, 'highlight', 3, {0: piece.node.highlight, 0.3: th})

    def highlight_tile(self, sq, color=None, active=True):
        if not sq:
            return
        if node := self.map.fills.get((round(sq[0], 1), round(sq[1], 1))):
            target_op = 0.7 if active else 0.0
            # fade op
            bs.animate(node, 'opacity', {0: node.opacity, 0.3: target_op})
            # fade col
            if active and color:
                bs.animate_array(node, 'color', 3, {0: node.color, 0.3: color})

    def stop_game(self):
        self.playing = False
        # clear
        for fill in self.map.fills.values():
            if fill:
                fill.opacity = 0.0
        for team in self.memory['spazzes'].values():
            for b in team:
                if b:
                    self.memory['timers'][f'retain_{id(b)}'] = None
                    self.stop_run(b)
                    b.handlemessage(bs.DieMessage(immediate=True))
        for k in ['timers', 'squares', 'control', 'swap', 'spazzes', 'kings', 'glow', 'can_start', 'started', 'team_colors']:
            self.memory[k] = {}

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(bs.Plugin):
    def __init__(self):
        # register
        bs.app.classic.maps['Checkboard'] = Checkboard
        # patch gt
        old_gt = bui.gettexture
        def new_gt(tex):
            if tex == 'checkboom':
                return 'checkboom'
            return old_gt(tex)
        bui.gettexture = new_gt
        # patch wids
        def wid(_):
            def new(*a,**k):
                if k.get('texture',None) == 'checkboom':
                    k['texture'] = old_gt('reflectionSharper_-z')
                    k['color'] = (0,2,2)
                    wid = _(*a,**k)
                    bui.textwidget(
                        parent=k['parent'],
                        big=True,
                        size=(size:=k['size']),
                        scale=1.3*(scl:=size[0]/220),
                        position=(
                            (p:=k['position']) and
                            (p[0]-3*scl,p[1]-3*scl)
                        ),
                        h_align='center',
                        v_align='center',
                        text='Checkboom',
                        flatness=-2,
                        color=(1.4,1.4,1.4),
                        draw_controller=k.get('draw_controller',wid)
                    )
                    return wid
                return _(*a,**k)
            new.__name__ = _.__name__
            new.__doc__ = _.__doc__
            return new
        bui.imagewidget = wid(_:=bui.imagewidget)
        bui.buttonwidget = wid(_:=bui.buttonwidget)
        # balance
        old = bs.app.config.get
        bs.app.config.get = lambda b,*a,**k:(
            True if b == 'Auto Balance Teams' and
            (
                (
                    (activity:=(session:=bs.getsession()).getactivity()) and
                    isinstance(activity,bs.JoinActivity) and
                    session._next_game is Checkboom
                ) or isinstance(activity, Checkboom)
            )
            else old(b,*a,**k)
        )
