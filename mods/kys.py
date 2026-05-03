# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
KYS v1.0 - Death at its finest

Adds minigame of a series of random levels.
The goal is to die, can't be easier, right?
KYS switches between its own activities.
Experimental.
"""

import bauiv1 as bui
import bascenev1 as bs
import bascenev1lib as bslib

from math import dist
from weakref import ref
from collections import defaultdict
from random import choice, random, uniform
from bascenev1lib.activity.multiteamscore import MultiTeamScoreScreenActivity

# all strings - good for quick edit
# and translation of course

class Strings:
    # lobby
    KYS_NAME = 'KYS'
    KYS_DESC = 'Death at its finest'
    PRESS_TO_START = 'Press {} to start the game.'
    PLAYERS_VOTED = '{}/{} players voted'
    STARTING_GAME = 'Starting game...'

    # level
    LEVEL_DESC = 'Kill your spaz.'
    LEVEL_DESC_SHORT = 'Kill your spaz'

    # trust fall
    TRUSTFALL_NAME = 'Trust Fall'
    TRUSTFALL_DESC = 'Let gravity decide your fate'
    TRUSTFALL_TIPS = [
        'Find edge. Commit.',
        'Don\'t fight gravity.',
        'Middle bad. Edge good.',
        'Jump out, not down.',
        'No one is catching you.',
        'Run past the ledge.',
        'Miss the platform on purpose.',
        'One step too far is perfect.',
        'Balance is failure.',
        'Air is your goal.',
        'Stop turning back.',
        'Overjump everything.',
        'The void is closer than you think.',
        'If safe, move worse.'
    ]

    # death fuse
    DEATHFUSE_NAME = 'Death Fuse'
    DEATHFUSE_DESC = 'Just press bomb'
    DEATHFUSE_TIPS = [
        'Punch someone to drop their bomb',
        'Steal their bombs, die in their place!',
        'Make sure the boom works'
    ]

    # last hit
    LASTHIT_NAME = 'Last Hit'
    LASTHIT_DESC = 'The art of ouch'
    LASTHIT_TIPS = [
        'Run into walls, it deals damage.',
        'Fall on your head, it\'s most effective.',
        'A 180 degree turn mid-air can help fall on your head.',
        'More speee, more kinetic energy, more self damage.',
        'You could form a double suicide pact with some other spaz.',
        'Master the momentum, more ouch.',
        'I doubt there\'s any other way to die, start gaining speeed!',
        'Jump before throwing spaz to throw higher.',
        'Hold someone and turn in circles against a wall, and hear them scream.',
        'You could help someone, but will they help back?'
    ]

    # boomerang
    BOOMERANG_NAME = 'Boomerang'
    BOOMERANG_DESC = 'Hunt the thing. Regret it.'
    BOOMERANG_TIPS = [
        'It never asked for this.',
        'Every punch is a lesson.',
        'The universe has a sense of humor.',
    ]

    # bullseye
    BULLSEYE_NAME = 'Bullseye'
    BULLSEYE_DESC = 'The sky picks favorites.'
    BULLSEYE_TIPS = [
        'The circle is an honor.',
        'Running is embarrassing.',
        'Death comes from above. Always.',
        'Stand still and let it happen.',
        'You were chosen. Accept it.',
        'Dodging is illegal (morally).',
        'The bombs have good aim.'
    ]

    # scaredy bot
    SCARED_MESSAGES = [
        'bro im literally shaking',
        'i have done nothing wrong',
        'this is harassment',
        'leave me alone im begging',
        'i just want to live',
        'WHY ARE YOU LIKE THIS',
        'i am filing a report',
        'please i have a family',
        'i never asked for this',
        'stay back i mean it',
        'this is not okay',
        'i am so scared right now',
    ]

    HIT_MESSAGES = [
        'read the desc.',
        'you asked for that.',
        'boomerang energy.',
        'did that feel worth it.',
        'skill issue. yours not mine.',
        'i literally warned you.',
        'try again champ.',
        'touching me was a choice.',
        'you punched yourself basically.',
        'i felt nothing.',
        'next time think first.',
    ]

    # victory screen
    VICTORY_TITLES = [
        'Died With Honor',
        'Left on Purpose',
        'Fell First',
        'Gone Too Soon',
        'Chose the Floor',
        'Speedran Life',
        'Took the Exit',
        'Jumped at the Chance',
        'Went for It',
        'Called It Early',
    ]

    # score screen
    ROUND_OVER_TITLES = [
        'Tragic',
        'Another One',
        'Rest Well',
        'The Round Has Spoken',
        'They Fell',
        'All According to Plan',
        'Gravity Wins Again',
        'Certified Fumble',
        'That Happened',
        'Moving On',
        'Okay Then',
        'Next Round',
        'Gone Too Soon',
        'Dust Settles',
        'The Verdict Is In',
        'Moment of Silence',
    ]

    # sky box
    SKYBOX_NAME = 'Sky Box'
    SKYBOX_DESC = 'Ascend to the heavens.'
    SKYBOX_TIPS = [
        'The box is your ticket out.',
        'Hold on. Never let go.',
        'The sky is not the limit.',
        'Rise above. Literally.',
        'Gravity is a suggestion.',
    ]

# the main level class
# used as parent for levels

class Level(bs.GameActivity[bs.Player, bs.Team]):
    __levels__ = []
    description = Strings.LEVEL_DESC
    get_instance_description_short = lambda s: Strings.LEVEL_DESC_SHORT
    announce_player_deaths = True
    allow_mid_activity_joins = False

    def __init_subclass__(
        cls,
        name,
        desc,
        tips,
        can_jump=True,
        can_bomb=True,
        can_grab=True,
        can_punch=True,
        include=None,
        exclude=None
    ):
        Level.__levels__.append(cls)
        cls.can_do = (can_jump,can_bomb,can_grab,can_punch)
        if include and exclude: raise ValueError('make up your mind')
        if not include and not exclude: include = ['Football Stadium']
        if exclude:
            include = [
                _ for _ in bs.app.classic.getmaps('melee')
                if _ not in exclude
            ]
        cls.maps = include
        cls.name = name
        cls.tips = tips
        cls.description = desc

    def __init__(s, settings):
        super().__init__(settings)
        s.default_music = None
        s.cache = defaultdict(dict)
        s.spawn_points = [(0,)*6]
        s._death_order = []
        s._death_times = {}
        s._timer = None

    @classmethod
    def switch_to_level(cls, settings, level=None):
        if level:
            level_cls = level
        elif settings.get('Random Levels', False):
            level_cls = choice(cls.__levels__)
        else:
            idx = settings.get('_level_idx', 0) % len(cls.__levels__)
            level_cls = cls.__levels__[idx]
            settings = dict(settings)
            settings['_level_idx'] = idx + 1
        with bs.getsession().context:
            bs.getsession().setactivity(
                bs.newactivity(level_cls, {
                    **settings,
                    'map': choice(level_cls.maps),
                })
            )

    def on_begin(s):
        super().on_begin()
        s._timer = bslib.actor.onscreentimer.OnScreenTimer()
        s._timer.start()
        limit = int(s.settings_raw.get('Time Limit', 60))
        s._limit_node = bs.newnode('text', attrs={
            'v_attach': 'top',
            'h_attach': 'center',
            'h_align': 'center',
            'color': (1, 0.4, 0.4, 0.8),
            'flatness': 0.5,
            'shadow': 0.5,
            'position': (0, -95),
            'scale': 0.7,
            'text': f'/ {limit}s',
        })
        s._limit_timer = bs.Timer(limit, s._on_time_limit)
        s.spawn_points = s.map.get_def_points('spawn')
        yay = lambda i: bs.CallPartial(s.on_key, p, i)
        for p in s.players:
            p.actor and p.actor.handlemessage(bs.StandMessage(choice(s.spawn_points)))
            not s.can_do[0] and p.assigninput(bs.InputType.JUMP_PRESS, yay(0))
            not s.can_do[1] and p.assigninput(bs.InputType.BOMB_PRESS, yay(2))
            not s.can_do[2] and p.assigninput(bs.InputType.PICK_UP_PRESS, yay(0))
            not s.can_do[3] and p.assigninput(bs.InputType.PUNCH_PRESS, yay(1))

    def spawn_player_spaz(s, player, position=None, angle=0):
        player_t = bslib.actor.playerspaz.PlayerSpaz

        color = player.color
        highlight = player.highlight

        playerspaztype = getattr(player, 'playerspaztype', player_t)
        if not issubclass(playerspaztype, player_t):
            playerspaztype = player_t

        display_color = bs.safecolor(color, target_intensity=0.75)
        spaz = playerspaztype(
            color=color,
            highlight=highlight,
            character=player.character,
            player=player,
        )

        player.actor = spaz
        assert spaz.node

        if isinstance(s.session, bs.CoopSession) and s.map.getname() in [
            'Courtyard', 'Tower D',
        ]:
            mat = s.map.preloaddata['collide_with_wall_material']
            assert isinstance(spaz.node.materials, tuple)
            assert isinstance(spaz.node.roller_materials, tuple)
            spaz.node.materials += (mat,)
            spaz.node.roller_materials += (mat,)

        spaz.node.name = player.getname()
        spaz.node.name_color = display_color
        spaz.connect_controls_to_player()

        pos = position or choice(s.spawn_points)
        spaz.handlemessage(bs.StandMessage(pos))
        s._spawn_sound.play(1, position=spaz.node.position)
        return spaz

    def _end_round(s):
        if getattr(s, '_round_ended', False): return
        settings = s.settings_raw
        game_num = settings.get('_game_num', 1)
        total_games = settings.get('Games', 5)

        players = list(s.players)
        total = len(players)

        sorted_players = sorted(
            s._death_order,
            key=lambda p: s._death_times[p]
        )

        for i, p in enumerate(sorted_players):
            base = total - i
            time_bonus = int(s._death_times[p] * 10)
            score = base + time_bonus
            try:
                s.stats.player_scored(p, score, screenmessage=False)
            except Exception:
                pass

        new_settings = dict(settings)
        new_settings['_game_num'] = game_num + 1

        with bs.getsession().context:
            if game_num >= total_games:
                bs.getsession().setactivity(
                    bs.newactivity(KYSVictoryScreen, new_settings)
                )
            else:
                bs.getsession().setactivity(
                    bs.newactivity(KYSScoreScreen, {
                        **new_settings,
                        'game_num': game_num,
                        'total_games': total_games,
                        'next_settings': new_settings,
                        '_round_death_times': {p.getname(): s._death_times[p] for p in s._death_order},
                        '_round_survivors': [p.getname() for p in s.players if p not in s._death_order],
                    })
                )

    def on_key(s, p, i):
        if p in (cool := s.cache['cooldown']): return
        cool[p] = bs.Timer(0.5, lambda: cool.pop(p))
        (node := p.actor.node).handlemessage(
            'celebrate' + (
                '_l' if i > 1 else
                '_r' if i else
                ''
            ), 50
        )
        choice(node.attack_sounds).play(position=node.position)

    def _on_time_limit(s):
        if not s._timer: return
        s._timer.stop()
        bs.getsound('boxingBell').play()
        bs.timer(0.5, s._end_round)

    def handlemessage(s, m):
        if isinstance(m, bs.PlayerDiedMessage):
            player = m.getplayer(bs.Player)

            if player not in s._death_times:
                t = bs.time()
                s._death_times[player] = t
                s._death_order.append(player)

            if len(s._death_order) == len(s.players):
                if not s._timer: return
                s._timer.stop()
                bs.getsound('boxingBell').play()
                bs.timer(1.0, s._end_round)
        else:
            super().handlemessage(m)

# level classes
# all levels are defined below

class Trustfall(
    Level,
    name=Strings.TRUSTFALL_NAME,
    desc=Strings.TRUSTFALL_DESC,
    tips=Strings.TRUSTFALL_TIPS,
    exclude=['Football Stadium', 'Hockey Stadium', 'Courtyard', 'Happy Thoughts'],
    can_bomb=False
): pass

class DeathFuse(
    Level,
    name=Strings.DEATHFUSE_NAME,
    desc=Strings.DEATHFUSE_DESC,
    tips=Strings.DEATHFUSE_TIPS,
    include=['Football Stadium', 'Hockey Stadium', 'Lake Frigid']
): pass

class LastHit(
    Level,
    name=Strings.LASTHIT_NAME,
    desc=Strings.LASTHIT_DESC,
    tips=Strings.LASTHIT_TIPS,
    include=['Football Stadium'],
    can_bomb=False,
    can_punch=False
): pass

class Boomerang(
    Level,
    name=Strings.BOOMERANG_NAME,
    desc=Strings.BOOMERANG_DESC,
    tips=Strings.BOOMERANG_TIPS,
    include=['Football Stadium', 'Hockey Stadium'],
    can_bomb=False,
    can_grab=False
):
    def on_begin(s):
        super().on_begin()
        spawn = choice(s.map.ffa_spawn_points)
        s._scaredy = ScaredyBot(position=spawn)

    def end(s):
        if hasattr(s, '_scaredy') and s._scaredy.node.exists():
            s._scaredy.bot.handlemessage(bs.DieMessage())
        super()._end_round()

class Bullseye(
    Level,
    name=Strings.BULLSEYE_NAME,
    desc=Strings.BULLSEYE_DESC,
    tips=Strings.BULLSEYE_TIPS,
    include=['Football Stadium', 'Hockey Stadium', 'Lake Frigid'],
    can_bomb=False,
    can_punch=False,
):
    def on_begin(s):
        super().on_begin()
        s._warn_sound = bs.getsound('tick')
        s._drop_timer = bs.Timer(3, s._drop_bomb, repeat=True)

    def _drop_bomb(s):
        gnode = bs.getactivity().globalsnode
        b = gnode.area_of_interest_bounds
        cx = (b[0] + b[3]) * 0.4
        cz = (b[2] + b[5]) * 0.4
        hw = (b[3] - b[0]) * 0.3
        hd = (b[5] - b[2]) * 0.3
        ground_y = s.map.ffa_spawn_points[0][1]

        tx = cx + uniform(-hw, hw)
        tz = cz + uniform(-hd, hd)

        loc = bs.newnode('locator', attrs={
            'shape': 'circle',
            'position': (tx, ground_y + 0.1, tz),
            'color': (1, 0.2, 0.2),
            'opacity': 0.0,
            'draw_beauty': False,
            'additive': True,
        })

        bs.animate(loc, 'opacity', {0.0: 0.0, 0.3: 0.8})
        bs.animate_array(loc, 'size', 1, {0.0: (4.0,), 0.3: (1.0,)})
        tick = lambda t: bs.timer(
            t, lambda: s._warn_sound.play(1.0, position=(tx, ground_y, tz))
        )

        def _spawn():
            if loc.exists(): loc.delete()
            for _ in range(3):
                bslib.actor.bomb.Bomb(
                    position=(tx, ground_y + 6, tz),
                    velocity=(0, -30, 0),
                    bomb_type='impact'
                ).autoretain()

        tick(0.001)
        tick(1)
        tick(2)
        bs.timer(3, _spawn)

class SkyBox(
    Level,
    name=Strings.SKYBOX_NAME,
    desc=Strings.SKYBOX_DESC,
    tips=Strings.SKYBOX_TIPS,
    can_bomb=False,
):
    def on_begin(s):
        super().on_begin()
        from bascenev1lib.actor.bomb import Bomb

        spawn_pos = s.map.ffa_spawn_points[0]
        cx, cy, cz = spawn_pos[0], spawn_pos[1] + 1.0, spawn_pos[2]

        s._holding = False
        s._launched = False
        s._hold_time = 0.0
        s._hold_timer = None
        s._countdown_node = None

        s._box = Bomb(
            position=(cx, cy, cz),
            velocity=(0, 0, 0),
            bomb_type='tnt',
        )

        _self = ref(s)
        _box = ref(s._box)

        def _box_hm(m):
            self = _self()
            box = _box()
            if self is None or box is None: return
            if isinstance(m, bs.PickedUpMessage):
                self._on_pickup()
            elif isinstance(m, bs.DroppedMessage):
                self._on_drop()
            elif isinstance(m, bs.OutOfBoundsMessage):
                if box.node.exists():
                    bs.timer(0.001, box.node.delete)
                return
            else:
                box.__class__.handlemessage(box, m)

        s._box.handlemessage = _box_hm

    def _on_pickup(s):
        if s._launched: return
        s._holding = True
        s._hold_time = bs.time()

        mnode = bs.newnode('math', owner=s._box.node, attrs={
            'input1': (0, 1.5, 0),
            'operation': 'add',
        })
        s._box.node.connectattr('position', mnode, 'input2')

        s._countdown_node = bs.newnode('text', owner=s._box.node, attrs={
            'in_world': True,
            'h_align': 'center',
            'scale': 0.02,
            'color': (1, 1, 0, 1),
            'text': '3.0',
        })
        mnode.connectattr('output', s._countdown_node, 'position')

        s._hold_timer = bs.Timer(0.05, bs.WeakCallStrict(s._tick_hold), repeat=True)

    def _on_drop(s):
        s._holding = False
        s._hold_timer = None
        if s._countdown_node and s._countdown_node.exists():
            node = s._countdown_node
            bs.timer(0.001, node.delete)
        s._countdown_node = None

    def _tick_hold(s):
        if not s._holding or s._launched: return
        if not s._box.node.exists(): return

        elapsed = bs.time() - s._hold_time
        remaining = max(0.0, 3.0 - elapsed)

        if s._countdown_node and s._countdown_node.exists():
            s._countdown_node.text = f'{remaining:.1f}'

        if elapsed >= 3.0:
            s._hold_timer = None
            s._launch()

    def _launch(s):
        if s._launched: return
        s._launched = True
        s._hold_timer = None
        if s._countdown_node and s._countdown_node.exists():
            bs.timer(0.001, s._countdown_node.delete)
        s._countdown_node = None
        bs.getsound('powerup01').play()
        s._box.node.gravity_scale = -4.0
        s._box.node.velocity = (0, 8, 0)

# extra dependencies
# stuff used by various levels

class Bubble:
    def __init__(s,head,res='\u2588',resw=19.0):
        s.head = head
        s.res = res
        s.resw = resw
        s.text = ''
        s.kids = []
        s.bye = None
        s.node = bs.newnode(
            'math',
            delegate=s,
            attrs={
                'input1':(0,0,0),
                'operation':'add'
            }
        )
        head.connectattr('position',s.node,'input2')
        for _ in [0,0.85]:
            n = bs.newnode(
                'text',
                owner=s.node,
                attrs=dict(
                   in_world=True,
                   scale=0.01,
                   flatness=1,
                   h_align='center',
                   color=(_,_,_)
                )
            )
            s.kids.append(n)
            s.node.connectattr('output',n,'position')
        s.gsw = lambda what: (
            (bui.get_string_width(what,1) or (len(what)*30))
            if what else 0
        )
    def push(s,text=''):
        s.bye = None
        if not text: s.anim(1,0); s.text = text; return
        ls = len(text.splitlines())
        s.node.input1 = (0,1.3+0.32*ls,0)
        bg,t = s.kids
        bg.text = (round(s.gsw(text)/s.resw+1)*s.res+'\n')*ls
        t.text = text
        if not s.text: s.anim(0,1)
        s.text = text
        s.bye = bs.Timer(3.5,s.push)
    def anim(s,p1,p2):
        try:
            [bs.animate(_,'opacity',{0:p1,0.2:p2}) for _ in s.kids]
        except:
            pass

class Bot:
    def __init__(
        s,
        position: tuple = (0,0,0),
        color: tuple = (0,0,0),
        highlight: tuple = (0,0,0),
        character: str = 'Pixel'
    ):
        s.bot = bslib.actor.spaz.Spaz(
            color=color,
            highlight=highlight,
            character=character
        )
        s.bot.handlemessage(bs.StandMessage(position,0))
        s.node = s.bot.node
        s.node.name = s.__class__.__name__
        s.bub = Bubble(s.node)
    def on(s,i):
        for _ in [1,0]:
            getattr(s.bot,'on_'+['jump','bomb','pickup','punch'][i]+'_'+['release','press'][_])()
    def on_run(s, v: int):
        s.bot.on_run(v)
    def move(s,x,z):
        s.bot.on_move_left_right(x)
        s.bot.on_move_up_down(z)

class ScaredyBot(Bot):
    def __init__(s, position=(0,0,0)):
        super().__init__(
            position=position,
            color=(1, 1, 0.3),
            highlight=(1, 0.5, 0),
            character='Mel'
        )
        s.node.name = 'scared'
        s.node.name_color = (1, 1, 0)

        s.speech_cooldown = 2.0
        s.last_speech_time = 0.0

        s.scared_messages = Strings.SCARED_MESSAGES
        s.hit_messages = Strings.HIT_MESSAGES

        s._think_timer = bs.Timer(0.15, s._think, repeat=True)

        _orig_hm = s.bot.handlemessage
        def _patched(m):
            if isinstance(m, bs.HitMessage) and m.hit_type == 'punch':
                try:
                    src = m.get_source_player(bs.Player)
                    if src and src.actor and src.actor.node and src.actor.node.exists():
                        src.actor.handlemessage(bs.HitMessage(
                            pos=src.actor.node.position,
                            velocity=(uniform(0,4),uniform(0,4),uniform(0,4)),
                            magnitude=1000,
                            hit_type='punch',
                            source_player=None,
                        ))
                        s._say(choice(s.hit_messages))
                except Exception:
                    pass
                return
            return _orig_hm(m)
        s.bot.handlemessage = _patched

        s.bub.push('...')

    def _say(s, msg):
        now = bs.time()
        if now - s.last_speech_time > s.speech_cooldown:
            s.bub.push(msg)
            s.last_speech_time = now

    def _get_nearest_player(s):
        if not s.node.exists(): return None
        my_pos = s.node.position
        nodes = [
            n for n in bs.getnodes()
            if n.exists() and n.getnodetype() == 'spaz'
            and n is not s.node and n.hurt < 1.0
        ]
        if not nodes: return None
        return min(nodes, key=lambda n: (
            (my_pos[0]-n.position[0])**2 + (my_pos[2]-n.position[2])**2
        ))

    def _think(s):
        if not s.node.exists():
            s._think_timer = None
            return

        nearest = s._get_nearest_player()
        if not nearest:
            s.on_run(0)
            s.move(0, 0)
            return

        my_pos = s.node.position
        t_pos = nearest.position
        dx = my_pos[0] - t_pos[0]
        dz = my_pos[2] - t_pos[2]
        length = (dx**2 + dz**2) ** 0.5

        if length > 5.0:
            s.on_run(0)
            s.move(0, 0)
            return

        if length < 0.01:
            dx, dz, length = 1.0, 0.0, 1.0

        flee_x = dx / length
        flee_z = dz / length

        now = bs.time()

        if not hasattr(s, '_panic_until'):
            s._panic_until = 0.0
        if now > getattr(s, '_next_panic', 0.0):
            s._next_panic = now + uniform(3.0, 7.0)
            if random() < 0.25:
                s._panic_until = now + 0.4
                s._say(choice(s.scared_messages))

        if now < s._panic_until:
            s.on_run(0)
            bs.timer(0.02, lambda: s.on_run(1))
            s.move(-flee_x, flee_z)
            return

        if now > getattr(s, '_next_twitch', 0.0):
            perp_x = -flee_z
            perp_z = flee_x
            t = uniform(-1, 1)
            s._twitch_x = perp_x * t + uniform(-0.3, 0.3)
            s._twitch_z = perp_z * t + uniform(-0.3, 0.3)
            s._next_twitch = now + uniform(0.25, 0.8)

        if length < 3.0 and random() < 0.1:
            s._say(choice(s.scared_messages))

        fx = flee_x + getattr(s, '_twitch_x', 0) * 0.9
        fz = flee_z + getattr(s, '_twitch_z', 0) * 0.9
        fl = (fx**2 + fz**2) ** 0.5 or 1

        s.on_run(0)
        bs.timer(0.02, lambda: s.on_run(1))
        s.move(fx/fl, -fz/fl)

# screens
# they between games

class KYSScoreScreen(MultiTeamScoreScreenActivity):
    score_color = (1, 0.8, 0.2, 1.0)
    bg_color = (0.1, 0.1, 0.15)

    def __init__(s, settings):
        super().__init__(settings=settings)
        s._total_games = int(settings.get('total_games', settings.get('Games', 5)))
        s._do_shuffle = bool(settings.get('Shuffle Order', False))
        s._game_num = settings.get('game_num', 1)
        s._next_settings = settings.get('next_settings', {})

    def on_begin(s):
        super().on_begin()
        s._min_view_time = 999.0
        Text = bslib.actor.text.Text
        Image = bslib.actor.image.Image

        death_times = s.settings_raw.get('_round_death_times', {})
        survivors = s.settings_raw.get('_round_survivors', [])

        Text(
            choice(Strings.ROUND_OVER_TITLES),
            scale=1.4,
            h_attach=Text.HAttach.CENTER,
            v_attach=Text.VAttach.TOP,
            h_align=Text.HAlign.CENTER,
            v_align=Text.VAlign.CENTER,
            position=(0, -60),
            color=s.score_color,
            transition=Text.Transition.FADE_IN,
            transition_delay=0.3,
        ).autoretain()

        Text(
            f'Game {s._game_num} of {s._total_games}',
            scale=0.8,
            h_attach=Text.HAttach.CENTER,
            v_attach=Text.VAttach.TOP,
            h_align=Text.HAlign.CENTER,
            v_align=Text.VAlign.CENTER,
            position=(0, -95),
            color=(0.6, 0.6, 0.7, 1.0),
            transition=Text.Transition.FADE_IN,
            transition_delay=0.5,
        ).autoretain()

        records = list(s.stats.get_records().values())
        records.sort(key=lambda r: r.accumscore, reverse=True)
        top_score = records[0].accumscore if records else 0

        spacing = 48
        start_y = 60 + spacing * len(records) * 0.5
        tdelay = 0.8

        for i, rec in enumerate(records):
            y = start_y - i * spacing
            is_top = rec.accumscore == top_score
            rank_color = (1, 0.85, 0.2, 1.0) if is_top else (0.7, 0.7, 0.8, 1.0)

            try:
                Image(
                    rec.get_icon(),
                    position=(-200, y),
                    scale=(30, 30),
                    transition=Image.Transition.IN_LEFT,
                    transition_delay=tdelay,
                ).autoretain()
            except Exception:
                pass

            Text(
                f'{rec.getname()}',
                scale=0.9,
                position=(-165, y),
                h_align=Text.HAlign.LEFT,
                v_align=Text.VAlign.CENTER,
                color=rank_color,
                transition=Text.Transition.IN_LEFT,
                transition_delay=tdelay,
            ).autoretain()

            Text(
                f'{rec.accumscore} pts',
                scale=0.9,
                position=(0, y),
                h_align=Text.HAlign.CENTER,
                v_align=Text.VAlign.CENTER,
                color=rank_color,
                transition=Text.Transition.IN_LEFT,
                transition_delay=tdelay + 0.05,
            ).autoretain()

            name = rec.getname()
            if name in survivors:
                time_str = '⏱ survived'
                time_color = (1.0, 0.3, 0.3, 1.0)
            elif name in death_times:
                t = death_times[name]
                time_str = f'died {t:.1f}s'
                time_color = (0.6, 0.6, 0.7, 1.0)
            else:
                time_str = '-'
                time_color = (0.4, 0.4, 0.4, 1.0)

            Text(
                time_str,
                scale=0.8,
                position=(210, y),
                h_align=Text.HAlign.RIGHT,
                v_align=Text.VAlign.CENTER,
                color=time_color,
                transition=Text.Transition.IN_LEFT,
                transition_delay=tdelay + 0.1,
            ).autoretain()

            tdelay += 0.05

        bs.timer(4.0, s._proceed)

    def _proceed(s):
        if s._game_num >= s._total_games:
            with bs.getsession().context:
                bs.getsession().setactivity(
                    bs.newactivity(KYSVictoryScreen, s._next_settings)
                )
        else:
            Level.switch_to_level(s._next_settings)

class KYSVictoryScreen(bs.ScoreScreenActivity):

    def __init__(s, settings):
        super().__init__(settings=settings)
        s._min_view_time = 10.0

    def on_begin(s):
        super().on_begin()
        Text = bslib.actor.text.Text
        Image = bslib.actor.image.Image
        ZoomText = bslib.actor.zoomtext.ZoomText

        bs.timer(0.6, lambda: bs.setmusic(bs.MusicType.VICTORY))
        bs.timer(4.6, lambda: bs.getsound('scoreHit01').play())

        records = list(s.stats.get_records().values())
        records.sort(key=lambda r: r.accumscore, reverse=True)
        winner = records[0] if records else None

        if winner:
            try:
                i = Image(
                    winner.get_icon(),
                    position=(0, 180),
                    scale=(100, 100),
                    transition=Image.Transition.FADE_IN,
                    transition_delay=4.4,
                ).autoretain()
            except Exception:
                pass

            bs.timer(4.4, lambda: ZoomText(
                winner.getname(),
                position=(0, 60),
                color=(1, 0.8, 0.2),
                scale=1.2,
                jitter=1.0,
                maxwidth=300,
            ).autoretain())

            bs.timer(4.8, lambda: ZoomText(
                choice(Strings.VICTORY_TITLES),
                position=(0, -15),
                color=(1, 1, 1),
                scale=0.65,
                jitter=0.5,
                maxwidth=300,
            ).autoretain())

        tdelay = 6.0
        top_score = records[0].accumscore if records else 0
        spacing = 44
        start_y = -100 - spacing * len(records) * 0.5

        for i, rec in enumerate(records):
            y = start_y - i * spacing
            is_top = rec.accumscore == top_score
            color = (1, 0.85, 0.2, 1.0) if is_top else (0.6, 0.6, 0.7, 1.0)

            try:
                Image(
                    rec.get_icon(),
                    position=(-180, y),
                    scale=(28, 28),
                    transition=Image.Transition.IN_LEFT,
                    transition_delay=tdelay,
                ).autoretain()
            except Exception:
                pass

            Text(
                f'{rec.getname()}',
                scale=0.85,
                position=(-145, y),
                h_align=Text.HAlign.LEFT,
                v_align=Text.VAlign.CENTER,
                color=color,
                transition=Text.Transition.IN_LEFT,
                transition_delay=tdelay,
            ).autoretain()

            Text(
                f'{rec.accumscore} pts',
                scale=0.85,
                position=(180, y),
                h_align=Text.HAlign.RIGHT,
                v_align=Text.VAlign.CENTER,
                color=color,
                transition=Text.Transition.IN_LEFT,
                transition_delay=tdelay + 0.05,
            ).autoretain()

            tdelay += 0.06

        bs.timer(14.0, s._finish)

    def _finish(s):
        reset = dict(s.settings_raw)
        reset['_game_num'] = 1
        with bs.getsession().context:
            bs.getsession().setactivity(
                bs.newactivity(KYS, reset)
            )

# brobord collide grass
# ba_meta require api 9
# ba_meta export bascenev1.GameActivity
class KYS(bs.GameActivity[bs.Player, bs.Team]):
    name = Strings.KYS_NAME
    get_instance_description = lambda s: Strings.KYS_DESC
    get_available_settings = lambda c: [
        bs.IntSetting('Games', default=5, min_value=1, max_value=20, increment=1),
        bs.IntChoiceSetting('Time Limit', choices=[('10s',10),('30s',30),('60s',60),('90s',90),('120s',120)], default=60),
        bs.BoolSetting('Random Levels', default=False),
    ]
    supports_session_type = lambda c: True
    get_supported_maps = lambda c: bs.app.classic.getmaps('melee')
    allow_mid_activity_joins = True

    def __init__(s, settings):
        super().__init__(settings)
        s.cache = {'settings': settings, 'votes': {}, 'cooldown': {}}
        s.info = None

    def on_begin(s) -> None:
        super().on_begin()
        s.spawn_points = s.map.get_def_points('spawn')
        s._started = False
        s._can_vote = False
        for p in s.players:
            if p.actor and p.actor.node:
                p.actor.handlemessage(bs.StandMessage(choice(s.spawn_points)))
        s.info = bs.newnode(
            'text',
            attrs=dict(
                text=Strings.PRESS_TO_START.format(bui.charstr(bui.SpecialChar.LEFT_BUTTON)),
                h_attach='center',
                v_attach='bottom',
                h_align='center',
                opacity=0,
            )
        )
        bs.animate(s.info, 'opacity', {0.5: 0, 1: 1})
        bs.timer(
            1.5,
            bs.CallPartial(
                setattr, s,'_can_vote',True
            )
        )

    def handlemessage(s, m):
        if isinstance(m, bs.PlayerDiedMessage):
            s.respawn_player(m.getplayer(bs.Player))

    def on_key(s, p, i):
        if i == 1:
            s.on_vote(p)
        if p in (cool := s.cache['cooldown']):
            return
        cool[p] = bs.Timer(0.5, lambda: cool.pop(p))
        (node := p.actor.node).handlemessage(
            'celebrate' + (
                '_l' if i > 1 else
                '_r' if i else
                ''
            ), 50
        )
        choice(node.attack_sounds).play(position=node.position)

    def on_vote(s, p):
        if not s._can_vote: return
        if s._started: return
        votes = s.cache['votes']
        if p in votes: return
        votes[p] = 1
        s.on_info()

    def on_info(s):
        if not s.info: return
        all_players = len(s.players)
        votes = len(s.cache['votes'])

        if not all_players:
            s.info.text = Strings.PRESS_TO_START.format(bui.charstr(bui.SpecialChar.LEFT_BUTTON))
        elif votes >= (all_players // 2) + 1:
            if s._started: return
            s._started = True
            s.info.text = Strings.STARTING_GAME
            bs.animate_array(s.info, 'color', 3, {0: (0,1,0), 0.5: (0,1,0)})
            bs.timer(2.0, lambda: (
                bs.getactivity() is s and
                Level.switch_to_level(s.cache['settings'])
            ))
            return
        else:
            s.info.text = Strings.PLAYERS_VOTED.format(votes, all_players)

        bs.animate_array(s.info, 'color', 3, {
            0: (1,1,1), 0.25: (0,1,1), 0.5: (1,1,1),
        })

    def on_player_join(s, p):
        s.spawn_player(p)
        yay = lambda i: bs.CallPartial(s.on_key, p, i)
        p.assigninput(bs.InputType.BOMB_PRESS, yay(2))
        p.assigninput(bs.InputType.PICK_UP_PRESS, yay(0))
        p.assigninput(bs.InputType.PUNCH_PRESS, yay(1))
        s.on_info()

    def on_player_leave(s, p):
        if p in (votes := s.cache['votes']):
            votes.pop(p)
        s.on_info()
