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
from bascenev1lib.gameutils import SharedObjects

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

    def on_begin(self):
        super().on_begin()
        bs.getsession().max_players = 2
        # subtext
        self.subtext = bs.newnode(
            'text',
            attrs={
                'v_attach': 'bottom',
                'h_align': 'center'
            }
        )
        # finally
        self.sanity_tick()

    def alert(self, text, color=(1,1,1)):
        self.subtext.text = text
        self.subtext.color = color

    def on_player_join(self, player):
        super().on_player_join(player)
        player.actor.handlemessage(
            bs.StandMessage(
                self.map.defs.points[
                    f'spawn{player.team.id+1}'
                ][:3],
                0 if player.team.id else 180
            )
        )
        self.sanity_tick()

    def sanity_tick(self):
        if len(bs.getactivity().players) == 2:
            self.alert('')
            if not self.playing:
                self.start_game()
        else:
            self.alert('Waiting for players',(1,1,0))
            if self.playing:
                self.stop_game()

    def start_game(self):
        self.playing = True

    def stop_game(self):
        self.playing = False

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
