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
from collections import defaultdict
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
            'map_bounds': (0,0,0, 0,0,0, 40,40,40),
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
                'scale': (40, 0.001, 40),
                'materials': [floor_material, shared.footing_material]
            }
        )

        self.tiles = []
        tile_size = 1.0
        board_dim = 8
        offset = (board_dim * tile_size) / 2 - (tile_size / 2)
        for row in range(board_dim):
            for col in range(board_dim):
                x = col * tile_size - offset
                z = row * tile_size - offset
                tile = bs.newnode(
                    'locator',
                    attrs={
                        'position': (x, 0, z),
                        'size': (tile_size, 0.01, tile_size),
                        'color': (1,1,1),
                        'shape': 'box',
                        'opacity': 1.0
                    }
                )
                self.tiles.append(tile)

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

    def __init__(self, settings):
        super().__init__(settings)
        self.default_music = bs.MusicType.GRAND_ROMP
        self.memory = defaultdict(dict)
        self.playing = False
        # subtext
        self.subtext = bs.newnode(
            'text',
            attrs={
                'v_attach': 'bottom',
                'h_align': 'center'
            }
        )

    def on_begin(self):
        super().on_begin()
        bs.getsession().max_players = 2
        self.sanity_tick()

    def alert(self, text, color=(1,1,1)):
        self.subtext.text = text
        self.subtext.color = color

    def on_player_join(self, player):
        super().on_player_join(player)
        actor = player.actor
        actor.handlemessage = lambda msg, _actor=actor: self.handlemessage(_actor, msg)
        actor.handlemessage(
            bs.StandMessage(
                self.map.defs.points[
                    f'spawn{player.team.id+1}'
                ][:3],
                0 if player.team.id else 180
            )
        )
        self.memory['players'][player.team.id] = player
        self.sanity_tick()

    def on_player_leave(self, player):
        super().on_player_leave(player)
        del self.memory['players'][player.team.id]
        self.sanity_tick()

    def handlemessage(self, actor, msg):
        if isinstance(msg, bs.HitMessage): return
        return type(actor).handlemessage(actor, msg)

    def sanity_tick(self):
        if len(bs.getactivity().players) == 1:
            self.alert('Get ready')
            if not self.playing:
                self.start_game()
        else:
            self.alert('Waiting for players',(1,1,0))
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

        for team_id, player in self.memory['players'].items():
            node = player.actor.node
            spawn_z = self.map.defs.points[f'spawn{team_id+1}'][2]
            side = 1 if spawn_z > 0 else -1
            spawn_offset = spawn_z - side * board_edge
            deck_z = side * board_edge + spawn_offset * 2
            rotation = 0 if team_id else 180

            self.memory['spazzes'][team_id] = []
            for i, character in enumerate(characters):
                x = deck_x_min + spacing * i
                bot = Piece(
                    character=character,
                    start_invincible=False,
                    game=self,
                    team_id=team_id
                )
                bot.handlemessage(
                    bs.StandMessage(
                        (x, 0, deck_z),
                        rotation
                    )
                )
                bot.node.color = self.neon(*node.color)
                bot.node.highlight = self.neon(*node.color)
                self.memory['spazzes'][team_id].append(bot)

    def claim_spaz(self, player, target):
        if target.claimed_by is not None:
            return

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

        name, name_color = self.memory['swap'][player.team.id][:2]
        target.node.name = name
        target.node.name_color = name_color

        for name, handler in zip(
            ['UP_DOWN', 'LEFT_RIGHT', 'RUN', 'JUMP_PRESS', 'JUMP_RELEASE',
             'PUNCH_PRESS', 'PUNCH_RELEASE', 'PICK_UP_PRESS', 'PICK_UP_RELEASE'],
            [target.on_move_up_down, target.on_move_left_right, target.on_run,
             target.on_jump_press, target.on_jump_release,
             target.on_punch_press, target.on_punch_release,
             target.on_pickup_press, target.on_pickup_release],
        ):
            player.assigninput(getattr(bs.InputType, name), handler)

        player.assigninput(bs.InputType.BOMB_PRESS, bs.CallPartial(self.release_control, player, target))
        player.assigninput(bs.InputType.BOMB_RELEASE, lambda: None)

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
        player.resetinput()

        # paralyze
        target.on_move_up_down(0)
        target.on_move_left_right(0)

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
            player.actor.connect_controls_to_player()

    def knockdown(self, team_id, origin):
        def tick():
            if self.memory['control'].get(team_id) is None or not origin.node:
                self.memory['timers'][f'knock{team_id}'] = None
                return
            origin.node.handlemessage('knockout', 100)

        self.memory['timers'][f'knock{team_id}'] = bs.Timer(0.09, tick, repeat=True)

    def neon(self,a,b,c,z=4):
        return (
            a*z,b*z,c*z
        )

    def stop_game(self):
        self.playing = False
        self.memory['timers'] = None

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

