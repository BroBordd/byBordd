# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
KYS v1.0 - Death at its finest

Adds minigame of a series of random levels.
The goal is to die, can't be easier, right?
Supports unlimited players, i hope.
KYS switches between its own activities.
Experimental.
"""

import bauiv1 as bui
import bascenev1 as bs
import bascenev1lib as bslib

from weakref import ref
from math import dist, ceil
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
        'Fate Wins Again',
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

    # zoe
    ZOE_PASSIVE_MSGS = [
        'why are you so close?',
        'do you not know what personal space is?',
        'i can see you.',
        'give me some room.',
        'go away.',
        'leave me alone.',
    ]
    ZOE_HIT_MSGS = [
        'OW!',
        'STOP THAT',
        'did you just',
        'excuse me??',
        'i felt that.',
    ]
    ZOE_PICKUP_MSGS = [
        'PUT ME DOWN',
        'LET GO OF ME',
        'excuse me?!',
        'i am not a toy',
        'HELP',
    ]
    ZOE_DROP_MSGS = [
        'i am going to LOSE IT',
        'that was NOT okay',
        'you threw me.',
        'unbelievable.',
    ]
    ZOE_ENRAGE_MSG = 'THAT IS IT.'
    ZOE_JUMP_MSG = 'STOP JUMPING'
    ZOE_CALM_MSGS = [
        'fine. FINE.',
        'i need a moment.',
        'are you happy now.',
        'do not test me again.',
    ]

    # ritual
    RITUAL_NAME = 'Ritual'
    RITUAL_DESC = 'Trade your soul to the daemon'
    RITUAL_TIPS = [
        'Do exactly what it asks.',
        'Wrong move. Start over.',
        'The daemon remembers.',
    ]
    RITUAL_WIZARD_LINES = [
        'the void remembers your name',
        'something watches from behind your eyes',
        'you were never meant to be here',
        'offer it. you know what it wants.',
        'stillness is a lie they told you',
        'it does not forgive. it simply forgets.',
        'you are already inside it',
        'the ground knows what you have done',
        'close. not close enough.',
        'the daemon is patient. are you?',
    ]
    RITUAL_RESET_MSGS = ['wrong.', 'again.', 'you hesitated.', 'it saw that.']
    RITUAL_COMPLETE_LAST = 'another soul claimed. rest in the void.'
    RITUAL_COMPLETE_OTHER = '...so be it.'
    RITUAL_COWARD = '{} tried to run away.'
    RITUAL_DISPLAY_DONE = '{}/{} completed'
    RITUAL_DISPLAY_STEP = '{}/{}  {}'
    RITUAL_SAY_WORDS = [
        'void', 'blood', 'bones', 'ash', 'shadow', 'stone', 'fire', 'dust',
        'hollow', 'grave', 'rust', 'smoke', 'iron', 'veil', 'dusk', 'mud',
        'rot', 'thorn', 'crow', 'salt', 'pale', 'dark', 'sink', 'lost',
        'cold', 'fade', 'gone', 'husk', 'wilt', 'grim',
    ]

    # stepdown
    pass

    # babysitter
    BABYSITTER_NAME = 'Babysitter'
    BABYSITTER_DESC = 'Agent Johnson is doing his job too well.'
    BABYSITTER_TIPS = [
        'Push Johnson away.',
        'The bots just want to help.',
        'Let them in.',
        'Johnson means well.',
    ]

# the main level class
# used as parent for levels

class Level(bs.GameActivity[bs.Player, bs.Team]):
    __test__ = 'Babysitter'
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
        exclude=None,
        music=None
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
        cls.default_music = None
        cls.music = music

    def __init__(s, settings):
        super().__init__(settings)
        s.music = s.music and choice(s.music) or None
        s.default_music = s.music
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
            if cls.__test__:
                level_cls = globals()[cls.__test__]
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
        s._limit_timer = bs.Timer(limit, bs.WeakCallStrict(s._on_time_limit))
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

    def _end_round(s):
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

class Zoe(
    Level,
    name='Zoe',
    desc='Make her mad. Get killed. Win.',
    tips=[
        'She has limits.',
        'Everyone has a breaking point.',
        'The angrier she gets, the faster you win.',
    ],
    can_bomb=False
):
    ANGER_MAX = 100.0
    ANGER_DECAY = 0.5

    def on_begin(s):
        super().on_begin()

        shared = bslib.gameutils.SharedObjects.get()
        spawn = s.map.ffa_spawn_points[0]
        cx, cy, cz = spawn[0] + 2, spawn[1], spawn[2]

        s._anger = 0.0
        s._top_annoyer = None
        s._anger_contrib = {}
        s._enraged = False
        s._zoe = MadBot(
            position=(cx, cy, cz),
            color=(1, 0.6, 0.8),
            highlight=(0.8, 0.3, 0.6),
            character='Zoe',
        )
        s._zoe.node.name = 'Zoe'
        s._zoe.node.name_color = (1, 0.4, 0.7)
        s._zoe.node.invincible = True

        s._bubble = None
        s._patrol_timer = bs.Timer(4.0, bs.WeakCallStrict(s._patrol), repeat=True)
        s._anger_timer = bs.Timer(1.0, bs.WeakCallStrict(s._tick_anger), repeat=True)
        s._check_timer = bs.Timer(0.1, bs.WeakCallStrict(s._check_annoyances), repeat=True)

        s._meter_node = bs.newnode('text', attrs={
            'in_world': True,
            'h_align': 'center',
            'scale': 0.012,
            'color': (1, 0.3, 0.3, 1),
            'text': '',
        })
        mnode = bs.newnode('math', owner=s._zoe.node, attrs={
            'input1': (0, 2.0, 0),
            'operation': 'add',
        })
        s._zoe.node.connectattr('position', mnode, 'input2')
        mnode.connectattr('output', s._meter_node, 'position')

        s._bar_bg = bs.newnode('image', attrs={
            'texture': bs.gettexture('white'),
            'scale': (420, 18),
            'color': (0.15, 0.05, 0.05),
            'opacity': 0.85,
            'attach': 'topCenter',
            'position': (0, -20),
        })

        s._bar_fg = bs.newnode('image', attrs={
            'texture': bs.gettexture('white'),
            'scale': (1, 18),
            'color': (0.2, 1.0, 0.2),
            'opacity': 1.0,
            'attach': 'topCenter',
            'position': (-210, -20),
        })
        s._bar_label = bs.newnode('text', attrs={
            'v_attach': 'top',
            'h_attach': 'center',
            'h_align': 'center',
            'position': (0, -5),
            'scale': 0.6,
            'color': (1, 1, 1, 1),
            'text': "Zoe's Patience",
            'flatness': 1.0,
            'shadow': 0.5,
        })

        s._zoe_orig_hm = s._zoe.bot.handlemessage
        _self = ref(s)
        def _zoe_hm(m):
            self = _self()
            if self is None: return
            if isinstance(m, bs.HitMessage):
                self._on_punch(m)
                return
            if isinstance(m, bs.PickedUpMessage):
                self._on_pickup(m)
            elif isinstance(m, bs.DroppedMessage):
                self._on_drop(m)
            if self._zoe_orig_hm:
                self._zoe_orig_hm(m)
        s._zoe.bot.handlemessage = _zoe_hm

    def spawn_player(s, p):
        spaz = super().spawn_player(p)
        def _on_jump():
            s._on_player_jump(p)
            spaz.on_jump_press()
        p.assigninput(bs.InputType.JUMP_PRESS, _on_jump)
        return spaz

    def _on_player_jump(s, p):
        if not s._zoe.node.exists(): return
        pp = p.actor.node.position
        zp = s._zoe.node.position
        dist = ((pp[0]-zp[0])**2 + (pp[2]-zp[2])**2) ** 0.5
        if dist < 3.0:
            s._add_anger(2.0, p)
            if uniform(0, 1) < 0.1:
                s._say(Strings.ZOE_JUMP_MSG)

    def _say(s, msg):
        if not s._zoe.node.exists(): return
        bs.timer(0.001, lambda: setattr(s, '_bubble', Bubble(node=s._zoe.node, text=msg, time=4)))

    def _add_anger(s, amount, player=None):
        if s._enraged: return
        s._anger = min(s.ANGER_MAX, s._anger + amount)
        if random() < 0.001 and not s._enraged:
            bs.timer(0.001, lambda: s._say(choice(Strings.ZOE_PASSIVE_MSGS)))
        if player:
            name = player.getname() if hasattr(player, 'getname') else str(player)
            s._anger_contrib[name] = s._anger_contrib.get(name, 0) + amount
            s._top_annoyer = max(s._anger_contrib, key=s._anger_contrib.get)
        s._update_meter()
        if s._anger >= s.ANGER_MAX:
            s._enrage()

    def _update_meter(s):
        ratio = s._anger / s.ANGER_MAX
        width = max(1.0, 420 * ratio)
        s._bar_fg.scale = (width, 18)
        s._bar_fg.position = (-210 + width / 2, -20)
        s._bar_fg.color = (ratio, 1.0 - ratio, 0.0)

    def _on_punch(s, m):
        try:
            src = m.get_source_player(bs.Player)
        except Exception:
            src = None
        s._add_anger(8.0, src)
        s._zoe_orig_hm(bs.HitMessage(
            pos=s._zoe.node.position,
            velocity=(0, 0, 0),
            magnitude=0.001,
            hit_type='punch',
            source_player=None,
        ))
        not s._enraged and s._say(choice(Strings.ZOE_HIT_MSGS))

    def _on_pickup(s, m):
        try:
            src = m.node.source_player
        except Exception:
            src = None
        s._add_anger(20.0, src)
        not s._enraged and s._say(choice(Strings.ZOE_PICKUP_MSGS))

    def _on_drop(s, m):
        vel = s._zoe.node.velocity
        speed = (vel[0]**2 + vel[1]**2 + vel[2]**2) ** 0.5
        bonus = min(30.0, speed * 3.0)
        s._add_anger(10.0 + bonus)
        not s._enraged and s._say(choice(Strings.ZOE_DROP_MSGS))

    def _check_annoyances(s):
        if not s._zoe.node.exists(): return
        zp = s._zoe.node.position

        for p in s.players:
            if not p.actor or not p.actor.node or not p.actor.node.exists(): continue
            pp = p.actor.node.position
            dist = ((pp[0]-zp[0])**2 + (pp[2]-zp[2])**2) ** 0.5

            if dist < 2:
                s._add_anger(0.1,p)

            if dist < 1.5:
                s._add_anger(0.15, p)

    def _tick_anger(s):
        if s._enraged: return
        if s._anger > 0:
            s._anger = max(0, s._anger - s.ANGER_DECAY)
            s._update_meter()

    def _patrol(s):
        if s._enraged or not s._zoe.node.exists(): return
        living = [p for p in s.players if p.actor and p.actor.node and p.actor.node.exists()]
        if not living: return
        target = choice(living)
        pos = target.actor.node.position
        s._zoe.move_to((pos[0] + uniform(-2, 2), pos[1], pos[2] + uniform(-2, 2)), time=3.5)

    def _enrage(s):
        s._enraged = True
        s._patrol_timer = None
        s._check_timer = None
        s._zoe.bot.node.invincible = False
        bs.getsound('orchestraHit4').play()
        s._say(Strings.ZOE_ENRAGE_MSG)

        top = s._top_annoyer
        target_node = None
        for p in s.players:
            if p.actor and p.actor.node and p.actor.node.exists():
                if hasattr(p, 'getname') and p.getname() == top:
                    target_node = p.actor.node
                    break
        if target_node is None:
            living = [p for p in s.players if p.actor and p.actor.node and p.actor.node.exists()]
            if living:
                target_node = choice(living).actor.node

        _self = ref(s)

        def _think():
            self = _self()
            if self is None or not self._enraged: return
            if not self._zoe or not self._zoe.node.exists(): return

            zp = self._zoe.node.position
            living = [p for p in self.players if p.actor and p.actor.node and p.actor.node.exists() and p.actor.node.hurt != 1]
            if not living:
                bs.timer(0.15, _think)
                return

            target = min(living, key=lambda p: (
                (p.actor.node.position[0]-zp[0])**2 +
                (p.actor.node.position[2]-zp[2])**2
            ))
            t_node = target.actor.node
            t_pos = t_node.position
            dx = t_pos[0] - zp[0]
            dz = t_pos[2] - zp[2]
            d = (dx**2 + dz**2) ** 0.5

            if self._zoe.node.hold_node == t_node:
                self._zoe.on_run(0)
                self._zoe.move(0, 0)
                if not getattr(self._zoe, '_skill1_timer', None):
                    self._zoe._start_combos()
                bs.timer(0.15, _think)
                return

            if self._zoe.node.hold_node and self._zoe.node.hold_node != t_node:
                self._zoe._stop_combos()
                self._zoe.on(2)
                self._zoe.move(0, 0)
                bs.timer(0.15, _think)
                return

            self._zoe._stop_combos()

            if d < 1.35:
                self._zoe.move(0, 0)
                self._zoe.skill2()
            else:
                vl = d or 1
                self._zoe.on_run(0)
                bs.timer(0.02, lambda: self._zoe.on_run(1) or self._zoe.move(dx/vl, -dz/vl))

            bs.timer(0.15, _think)
        bs.timer(0.5, _think)
        s._rage_timer = bs.Timer(0.5, bs.WeakCallStrict(s._rage_tick), repeat=True)

    def _rage_tick(s):
        if not s._zoe.node.exists(): return
        zp = s._zoe.node.position
        for p in s.players:
            if not p.actor or not p.actor.node: continue
            pp = p.actor.node.position
            dist = ((pp[0]-zp[0])**2 + (pp[2]-zp[2])**2) ** 0.5
            if dist < 2.0 and p.actor.node.hurt > 0.1:
                s._anger = max(0, s._anger - 10.0)
                s._update_meter()
                if s._anger <= 0:
                    s._calm_down()

    def _calm_down(s):
        s._enraged = False
        s._anger = 0.0
        s._anger_contrib = {}
        s._top_annoyer = None
        s._zoe.node.invincible = True
        s._patrol_timer = bs.Timer(4.0, bs.WeakCallStrict(s._patrol), repeat=True)
        s._check_timer = bs.Timer(0.1, bs.WeakCallStrict(s._check_annoyances), repeat=True)
        s._say(choice(Strings.ZOE_CALM_MSGS))
        s._update_meter()

    def _end_round(s):
        s._zoe_orig_hm = None
        s._rage_timer = None
        s._patrol_timer = None
        s._check_timer = None
        s._anger_timer = None
        try:
            s._zoe.bot.handlemessage(bs.DieMessage())
        except Exception:
            pass
        s._zoe = None
        super()._end_round()

class Ritual(
    Level,
    name=Strings.RITUAL_NAME,
    desc=Strings.RITUAL_DESC,
    tips=Strings.RITUAL_TIPS,
    exclude=['Hockey Stadium', 'Happy Thoughts', 'Lake Frigid'],
    can_bomb=False
):
    TASKS = ['jump', 'punch', 'pickup', 'dizzy', 'offer', 'still', 'punchwiz', 'holdwiz', 'say']
    TASK_LABELS = {
        'jump':     f'{bui.charstr(bui.SpecialChar.BOTTOM_BUTTON)} leap up into nothing',
        'punch':    f'{bui.charstr(bui.SpecialChar.LEFT_BUTTON)} strike the air',
        'pickup':   f'{bui.charstr(bui.SpecialChar.TOP_BUTTON)} lift what remains',
        'dizzy':    f'{bui.charstr(bui.SpecialChar.DPAD_CENTER_BUTTON)} turn until you fall',
        'offer':    f'{bui.charstr(bui.SpecialChar.PLAY_STATION_TRIANGLE_BUTTON)} bring it to him',
        'still':    f'{bui.charstr(bui.SpecialChar.PLAY_STATION_SQUARE_BUTTON)} do not move',
        'punchwiz': f'{bui.charstr(bui.SpecialChar.LEFT_BUTTON)} strike the daemon',
        'holdwiz':  f'{bui.charstr(bui.SpecialChar.TOP_BUTTON)} lift and cast him aside',
        'say':      'auto'
    }

    def __init__(s, settings):
        super().__init__(settings)
        s._wizard = None
        s._wizard_node = None
        s._wizard_speech_timer = None
        s._wizard_move_timer = None
        s._stillness_timer = None
        s._offer_node = None
        s._offer_actor = None
        s._player_rituals = {}
        s._chat_last_len = 0
        s._chat_poll_timer = None

    def on_begin(s):
        super().on_begin()
        s._spawn_wizard()
        s._spawn_offer_object()
        s._wizard_speech_timer = bs.Timer(12.0, bs.WeakCallStrict(s._wizard_speak), repeat=True)
        s._wizard_move_timer = bs.Timer(3.0, bs.WeakCallStrict(s._wizard_wander), repeat=True)
        s._stillness_timer = bs.Timer(0.5, bs.WeakCallStrict(s._check_stillness), repeat=True)
        gn = bs.getactivity().globalsnode
        bs.animate_array(gn, 'tint', 3, {0: (1,1,1), 3: (0.6, 0.4, 0.8)})
        bs.animate_array(gn, 'vignette_outer', 3, {0: (0.7,0.7,0.7), 3: (0.2, 0.1, 0.3)})
        s._total_players = len(s.players)
        for p in s.players:
            s._init_ritual(p)
        s._chat_last_len = len(bs.get_chat_messages())
        s._chat_poll_timer = bs.Timer(0.5, bs.WeakCallStrict(s._poll_chat), repeat=True)

    def _spawn_offer_object(s):
        from bascenev1lib.actor.bomb import Bomb
        pos = choice(s.spawn_points)
        s._offer_actor = Bomb(position=(pos[0], pos[1]+1, pos[2]), bomb_type='tnt')
        s._offer_node = s._offer_actor.node
        _orig_hm = s._offer_actor.handlemessage
        _self = ref(s)
        def _bomb_hm(m):
            if isinstance(m, bs.OutOfBoundsMessage):
                act = _self()
                if act is not None and act._offer_node and act._offer_node.exists():
                    rpos = choice(act.spawn_points)
                    act._offer_node.position = (rpos[0], rpos[1]+1, rpos[2])
                return
            _orig_hm(m)
        s._offer_actor.handlemessage = _bomb_hm

    def _update_ritual_display(s, player):
        r = s._player_rituals.get(player)
        if not r or not r['label_node']:
            return
        step = r['step']
        seq = r['seq']
        if player.actor and player.actor.node and player.actor.node.exists():
            player.actor.node.connectattr('position', r['math_node'], 'input2')
        total = len(seq)
        if step >= total:
            r['label_node'].text = Strings.RITUAL_DISPLAY_DONE.format(total, total)
            r['label_node'].color = (0.2, 1.0, 0.2)
            return
        task = seq[step]
        if task == 'say':
            words = r.get('say_words', {}).get(step, '???')
            label = f'{bui.charstr(bui.SpecialChar.LOGO_FLAT)} say: {words}'
        else:
            label = s.TASK_LABELS.get(task, task)
        r['label_node'].text = Strings.RITUAL_DISPLAY_STEP.format(step, total, label)
        r['label_node'].color = (1.0, 0.8, 0.2)

    def _advance_ritual(s, player):
        r = s._player_rituals.get(player)
        if not r:
            return
        r['step'] += 1
        r['still_time'] = 0.0
        r['wizard_held'] = False
        r['watching_knockout'] = False
        s._update_ritual_display(player)
        if r['step'] >= len(r['seq']):
            s._ritual_complete(player)

    def _reset_ritual(s, player):
        r = s._player_rituals.get(player)
        if not r:
            return
        was_zero = (r['step'] == 0)
        r['step'] = 0
        r['still_time'] = 0.0
        r['wizard_held'] = False
        r['watching_knockout'] = False
        s._update_ritual_display(player)
        if not was_zero:
            if player.actor and player.actor.node and player.actor.node.exists():
                player.actor.node.handlemessage('flash')
            s._wizard_say(choice(Strings.RITUAL_RESET_MSGS))

    def _ritual_complete(s, player):
        r = s._player_rituals.get(player)
        if r:
            r['step'] = 999
        alive_count = sum(
            1 for p in s.players
            if p.actor and p.actor.node and p.actor.node.exists() and p not in s._death_order
        )
        gn = bs.getactivity().globalsnode
        if alive_count <= 1:
            s._wizard_say(Strings.RITUAL_COMPLETE_LAST)
            bs.animate_array(gn, 'tint', 3, {0.0: (0.6, 0.4, 0.8), 1.5: (1.0, 0.0, 0.0)})
        else:
            s._wizard_say(Strings.RITUAL_COMPLETE_OTHER)
            bs.animate_array(gn, 'tint', 3, {0.0: (0.6, 0.4, 0.8), 1.5: (1.0, 0.0, 0.0), 4.5: (0.6, 0.4, 0.8)})
        if s._wizard_node and s._wizard_node.exists():
            if player.actor and player.actor.node and player.actor.node.exists():
                diff = bs.Vec3(player.actor.node.position) - bs.Vec3(s._wizard_node.position)
                s._wizard_node.move_left_right = diff.x
                s._wizard_node.move_up_down = -diff.z
        _p = ref(player)
        def _kill():
            p = _p()
            if p is None:
                return
            if p.actor and p.actor.node and p.actor.node.exists():
                p.actor.node.shattered = 2
                s.stats.player_scored(p, 50, screenmessage=False)
                p.actor.handlemessage(bs.DieMessage())
            elif p not in s._death_order:
                s._death_times[p] = bs.time()
                s._death_order.append(p)
                if len(s._death_order) == s._total_players:
                    bs.timer(1.0, bs.WeakCallStrict(s._end_round))
        bs.timer(2.0, _kill)

    def _poll_chat(s):
        msgs = bs.get_chat_messages()
        new_count = len(msgs)
        if new_count <= s._chat_last_len:
            s._chat_last_len = new_count
            return
        new_msgs = msgs[s._chat_last_len:]
        s._chat_last_len = new_count
        for msg in new_msgs:
            s._on_chat_message(msg)

    def _on_chat_message(s, msg: str):
        parts = msg.split(': ', 1)
        if len(parts) < 2:
            return
        sender_name = parts[0]
        said = parts[1].strip().lower()
        for p in list(s._player_rituals.keys()):
            if p.getname() != sender_name:
                continue
            r = s._player_rituals.get(p)
            if not r or r['step'] >= len(r['seq']):
                continue
            if r['seq'][r['step']] != 'say':
                continue
            required = r.get('say_words', {}).get(r['step'], '')
            if said == required.lower():
                s._advance_ritual(p)

    def _stop_chat_poll(s):
        s._chat_poll_timer = None

    def _end_round(s):
        if getattr(s, '_round_ended', False): return
        s._round_ended = True
        s._stop_chat_poll()
        settings = s.settings_raw
        game_num = settings.get('_game_num', 1)
        total = int(settings.get('Games', 5))

        sorted_players = sorted(
            s._death_order,
            key=lambda p: s._death_times.get(p, float('inf'))
        )
        for i, p in enumerate(sorted_players):
            try:
                pts = max(1, s._total_players - i)
                s.stats.player_scored(p, pts, screenmessage=False)
            except Exception:
                pass

        new_settings = dict(settings)
        new_settings['_game_num'] = game_num + 1
        with bs.getsession().context:
            bs.getsession().setactivity(
                bs.newactivity(KYSScoreScreen, {
                    **new_settings,
                    'game_num': game_num,
                    'total_games': total,
                    'next_settings': new_settings,
                    '_round_death_times': {p.getname(): s._death_times[p] for p in s._death_order},
                    '_round_survivors': [p.getname() for p in s.players if p not in s._death_order],
                })
            )

    def _wizard_speak(s):
        s._wizard_say(choice(Strings.RITUAL_WIZARD_LINES))

    def _wizard_wander(s):
        if not s._wizard_node or not s._wizard_node.exists():
            return
        target = choice(s.spawn_points)
        pos = bs.Vec3(s._wizard_node.position)
        diff = bs.Vec3(target[0], target[1], target[2]) - pos
        if diff.length() > 0.1:
            d = diff.normalized()
            s._wizard_node.move_left_right = d.x * 0.4
            s._wizard_node.move_up_down = -d.z * 0.4
        _s = ref(s)
        def _stop_wander():
            act = _s()
            if act and act._wizard_node and act._wizard_node.exists():
                act._wizard_node.move_left_right = 0
                act._wizard_node.move_up_down = 0
        bs.timer(1.5, _stop_wander)

    def _check_offer(s, player):
        if not s._wizard_node or not s._wizard_node.exists():
            return False
        if not s._offer_node or not s._offer_node.exists():
            return False
        if not player.actor or not player.actor.node or not player.actor.node.exists():
            return False
        held = player.actor.node.hold_node
        if held and held == s._offer_node:
            wpos = bs.Vec3(s._wizard_node.position)
            ppos = bs.Vec3(player.actor.node.position)
            if (wpos - ppos).length() < 2.5:
                player.actor.node.hold_node = None
                s._wizard_node.hold_body = 0
                s._wizard_node.hold_node = s._offer_node
                s._offer_node = None
                bs.timer(2.5, bs.WeakCallStrict(s._wizard_drop_offer))
                return True
        return False

    _WIZARD_DROP_LINES = [
        'it reeks of the living.',
        'i have no use for this.',
        'the void does not keep offerings.',
        'take it back. it means nothing.',
        'your gift is returned. your soul is not.',
    ]

    def _wizard_drop_offer(s):
        if not s._wizard_node or not s._wizard_node.exists():
            return
        held = s._wizard_node.hold_node
        if held and held.exists():
            s._offer_node = held
            s._wizard_node.hold_node = None
        s._wizard_say(choice(s._WIZARD_DROP_LINES))

    def _check_stillness(s):
        for p, r in s._player_rituals.items():
            if r['step'] >= len(r['seq']): continue
            if r['seq'][r['step']] != 'still': continue
            if not p.actor or not p.actor.node or not p.actor.node.exists(): continue
            v = p.actor.node.velocity
            if abs(v[0]) < 0.2 and abs(v[2]) < 0.2:
                r['still_time'] = r.get('still_time', 0.0) + 0.5
                if r['still_time'] >= 2.0:
                    s._advance_ritual(p)
            else:
                if r.get('still_time', 0.0) > 0.5:
                    s._reset_ritual(p)

    def _on_wizard_punched(s, player):
        r = s._player_rituals.get(player)
        if not r or r['step'] >= len(r['seq']): return
        if r['seq'][r['step']] == 'punchwiz':
            s._advance_ritual(player)

    def _on_wizard_picked_up(s, player):
        r = s._player_rituals.get(player)
        if not r or r['step'] >= len(r['seq']): return
        if r['seq'][r['step']] == 'holdwiz':
            r['wizard_held'] = True

    def _on_wizard_dropped(s, player):
        r = s._player_rituals.get(player)
        if not r or r['step'] >= len(r['seq']): return
        if r['seq'][r['step']] == 'holdwiz' and r.get('wizard_held'):
            r['wizard_held'] = False
            s._advance_ritual(player)

    def on_player_join(s, player):
        player.playerspaztype = RitualSpaz
        s.spawn_player_spaz(player)
        s._init_ritual(player)

    def _on_spin(s, player, value):
        r = s._player_rituals.get(player)
        if not r or r['step'] >= len(r['seq']): return
        if r['seq'][r['step']] != 'dizzy': return
        if r['watching_knockout']: return
        if not player.actor or not player.actor.node or not player.actor.node.exists(): return
        if player.actor.node.knockout > 0:
            r['watching_knockout'] = True
            bs.timer(0.2, bs.WeakCallStrict(s._wait_for_wakeup, player))

    def _wait_for_wakeup(s, player):
        r = s._player_rituals.get(player)
        if not r or r['step'] >= len(r['seq']) or r['seq'][r['step']] != 'dizzy': return
        if not player.actor or not player.actor.node or not player.actor.node.exists(): return
        if player.actor.node.knockout > 0:
            bs.timer(0.2, bs.WeakCallStrict(s._wait_for_wakeup, player))
        else:
            s._advance_ritual(player)

    def _on_input(s, player, action):
        if not player.actor or not player.actor.node or not player.actor.node.exists(): return
        if player.actor.node.knockout > 0: return
        r = s._player_rituals.get(player)
        if not r or r['step'] >= len(r['seq']): return
        current = r['seq'][r['step']]
        if action == 'pickup' and current == 'offer':
            if s._check_offer(player):
                s._advance_ritual(player)
            return
        if action in ('punch', 'pickup') and current in ('punchwiz', 'holdwiz'):
            return
        if action == 'still':
            return
        if current == 'say':
            return
        if action == current and action not in ('dizzy', 'punchwiz', 'holdwiz', 'offer'):
            s._advance_ritual(player)
        elif action != current and action in ('jump', 'punch', 'pickup'):
            s._reset_ritual(player)

    def _init_ritual(s, player):
        pool = list(s.TASKS)
        if s._offer_node is None or not s._offer_node.exists():
            if 'offer' in pool: pool.remove('offer')
        seq = []
        while len(seq) < 6:
            t = choice(pool)
            if not seq or seq[-1] != t:
                seq.append(t)
        from random import sample, shuffle as rshuffle
        word_pool = list(Strings.RITUAL_SAY_WORDS)
        rshuffle(word_pool)
        say_words = {}
        wi = 0
        for i, t in enumerate(seq):
            if t == 'say':
                w1 = word_pool[wi % len(word_pool)]
                w2 = word_pool[(wi + 1) % len(word_pool)]
                say_words[i] = f'{w1} {w2}'
                wi += 2
        if player in s._player_rituals:
            old_r = s._player_rituals[player]
            if old_r.get('label_node') and old_r['label_node'].exists():
                old_r['label_node'].delete()
            if old_r.get('math_node') and old_r['math_node'].exists():
                old_r['math_node'].delete()
        node = bs.newnode('text', attrs=dict(
            text='',
            scale=0.012,
            h_attach='center',
            v_attach='center',
            in_world=True,
            shadow=1.0,
            flatness=1.0,
        ))
        mnode = bs.newnode('math', owner=node, attrs={
            'input1': (0, 1.6, 0),
            'input2': (0, 0, 0),
            'operation': 'add'
        })
        if player.actor and player.actor.node and player.actor.node.exists():
            player.actor.node.connectattr('position', mnode, 'input2')
        mnode.connectattr('output', node, 'position')
        s._player_rituals[player] = {
            'seq': seq,
            'step': 0,
            'label_node': node,
            'math_node': mnode,
            'still_time': 0.0,
            'wizard_held': False,
            'watching_knockout': False,
            'say_words': say_words,
        }
        s._update_ritual_display(player)

    def _spawn_wizard(s):
        pos = choice(s.spawn_points)
        s._wizard = WizardSpaz(
            color=(0.1, 0.0, 0.15),
            highlight=(0.4, 0.0, 0.6),
            character='Grumbledorf',
        )
        s._wizard_node = s._wizard.node
        s._wizard_node.name = ''
        s._wizard_node.handlemessage(bs.StandMessage(pos))
        s._wizard.impact_scale = 0.0
        s._wizard_node.invincible = True

    def _wizard_say(s, text):
        if not s._wizard_node or not s._wizard_node.exists():
            return
        bs.timer(0.001, lambda: setattr(s, '_bubble', Bubble(node=s._wizard_node, text=text, color=(0.8, 0.5, 1.0), time=4)))

    def handlemessage(s, m):
        if isinstance(m, bs.PlayerDiedMessage):
            player = m.getplayer(bs.Player)
            if player not in s._death_times:
                s._death_times[player] = bs.time()
            if player not in s._death_order:
                s._death_order.append(player)
            r = s._player_rituals.pop(player, None)
            if r:
                if r.get('label_node') and r['label_node'].exists():
                    r['label_node'].delete()
                if r.get('math_node') and r['math_node'].exists():
                    r['math_node'].delete()
            if len(s._death_order) == s._total_players:
                bs.timer(4.0, bs.WeakCallStrict(s._end_round))
            super().handlemessage(m)
        else:
            super().handlemessage(m)

STEPDOWN_TRACK = {
    bs.MusicType.TO_THE_DEATH: {7.296: (0, 1), 7.36: (0, 0), 8.048: (3, 1), 8.096: (3, 0), 8.64: (2, 1), 8.72: (2, 0), 9.008000000000001: (2, 1), 9.056000000000001: (2, 0), 9.376: (2, 1), 9.44: (2, 0), 10.848: (3, 1), 10.928: (3, 0), 11.552: (2, 1), 11.616: (2, 0), 11.936: (2, 1), 12.0: (2, 0), 12.256: (2, 1), 12.352: (2, 0), 13.408: (1, 1), 13.488: (1, 0), 14.336: (1, 1), 14.416: (1, 0), 15.040000000000001: (2, 1), 15.136000000000001: (2, 0), 16.432: (0, 1), 16.512: (0, 0), 17.12: (0, 1), 17.216: (0, 0), 17.92: (2, 1), 18.016000000000002: (2, 0), 19.424: (3, 1), 19.504: (3, 0), 20.048000000000002: (2, 1), 20.16: (2, 0), 20.400000000000002: (2, 1), 20.496: (2, 0), 20.736: (2, 1), 20.832: (2, 0), 22.304000000000002: (3, 1), 22.432000000000002: (3, 0), 22.96: (2, 1), 23.056: (2, 0), 23.312: (2, 1), 23.408: (2, 0), 23.68: (2, 1), 23.776: (2, 0), 25.264: (1, 1), 25.36: (1, 0), 25.92: (1, 1), 26.032: (1, 0), 26.704: (0, 1), 26.912: (0, 0), 28.048000000000002: (3, 1), 28.208000000000002: (3, 0), 28.72: (3, 1), 28.88: (3, 0), 29.488: (2, 1), 29.744: (2, 0)},
    bs.MusicType.GRAND_ROMP: {3.032: (2, 1), 3.144: (2, 0), 4.328: (2, 1), 4.424: (2, 0), 5.64: (2, 1), 5.736: (2, 0), 6.28: (2, 1), 6.408: (2, 0), 6.968: (2, 1), 7.048: (2, 0), 8.376: (0, 1), 8.456: (0, 0), 9.176: (0, 1), 9.256: (0, 0), 9.8: (0, 1), 9.88: (0, 0), 11.256: (1, 1), 11.384: (1, 0), 11.944: (3, 1), 12.072000000000001: (3, 0), 12.616: (3, 1), 12.712: (3, 0), 12.952: (3, 1), 13.032: (3, 0), 14.024000000000001: (3, 1), 14.072000000000001: (3, 0), 14.312000000000001: (3, 1), 14.392: (3, 0), 15.208: (3, 1), 15.304: (3, 0), 15.88: (3, 1), 15.944: (3, 0), 16.504: (3, 1), 16.568: (3, 0), 17.784: (3, 1), 17.848: (3, 0), 20.472: (2, 1), 20.6: (2, 0), 21.88: (2, 1), 21.96: (2, 0), 23.144000000000002: (2, 1), 23.256: (2, 0), 23.896: (2, 1), 23.976: (2, 0), 24.568: (2, 1), 24.648: (2, 0), 26.296: (1, 1), 26.408: (1, 0), 27.736: (3, 1), 27.784: (3, 0), 28.84: (0, 1), 28.92: (0, 0), 29.176000000000002: (0, 1), 29.256: (0, 0), 29.512: (0, 1), 29.592000000000002: (0, 0), 29.848: (0, 1), 29.928: (0, 0), 30.184: (0, 1), 30.264: (0, 0), 30.504: (0, 1), 30.584: (0, 0), 30.856: (0, 1), 30.936: (0, 0), 31.176000000000002: (0, 1), 31.240000000000002: (0, 0)}
}

STEPDOWN_KEY_TEXTURES = [
    'buttonJump',
    'buttonBomb',
    'buttonPickUp',
    'buttonPunch',
]

STEPDOWN_KEY_COLORS = [
    (0.4, 1.0, 0.4),
    (1.0, 0.3, 0.3),
    (0.5, 0.5, 1.0),
    (1.0, 0.7, 0.3),
]

STEPDOWN_PIXIE_LINES = [
    'anyway.',
    'next.',
    'moving on.',
    'as i was saying.',
    'where were we.',
    'that was necessary.',
    'sorry about that.',
]

STEPDOWN_KILL_LINES = [
    "you're too good to be alive.",
    "impressive. unfortunately.",
    "i don't allow perfection here.",
    "you scored too high. goodbye.",
]


class Stepdown(
    Level,
    name='Stepdown',
    desc='Follow the rhythm. Too good and you die.',
    tips=[
        'The pixie is watching.',
        'Perfection is a death sentence.',
        'Follow the beats of death.',
    ],
    include=['Football Stadium'],
    can_bomb=False,
    music=[
        bs.MusicType.TO_THE_DEATH,
        bs.MusicType.GRAND_ROMP
    ]
):
    KEY_LANE_XS = [-90, -30, 30, 90]
    HIT_LINE_Y = 180
    NOTE_START_Y = 0
    NOTE_FALL_DURATION = 2.0
    MAX_XP = 100
    PIXIE_STAND_X = 6.0
    PIXIE_STAND_Z = 0.0

    PERFECT_WINDOW = 0.5
    GOOD_WINDOW = 1
    HOLD_PERFECT_WINDOW = 0.4

    def __init__(s, settings):
        super().__init__(settings)
        s._player_data = {}
        s._kill_queue = []
        s._pixie_busy = False
        s._pending_notes = []
        s._note_timers = []
        s._dance_timer = None
        s._held_keys = {}
        s._start_time = None
        s._lane_glows = []
        s._disco_colors = [
            (1.0, 0.1, 0.5),
            (0.1, 0.5, 1.0),
            (0.8, 1.0, 0.1),
            (1.0, 0.4, 0.1),
            (0.3, 1.0, 0.6),
        ]
        s._disco_idx = 0
        s._disco_timer = None

    def on_begin(s):
        super().on_begin()

        gn = bs.getactivity().globalsnode
        gn.tint = (0.4, 0.1, 0.8)
        gn.ambient_color = (1.0, 0.5, 1.5)
        gn.vignette_outer = (0.6, 0.0, 0.8)
        gn.vignette_inner = (1.0, 0.8, 1.0)

        s._disco_timer = bs.Timer(0.5, bs.WeakCallStrict(s._disco_pulse), repeat=True)

        s._music_type = s.music
        raw = STEPDOWN_TRACK[s._music_type]
        s._notes = sorted(
            [{'time': t, 'key': v[0], 'type': v[1]} for t, v in raw.items()],
            key=lambda x: x['time']
        )

        s._spawn_pixie()
        s._build_rhythm_ui()

        for p in s.players:
            s._init_player(p)

        bs.setmusic(s._music_type)
        s._start_time = bs.time()
        s._schedule_notes()
        track_end = max(t for t in STEPDOWN_TRACK[s._music_type].keys())
        s._track_end_timer = bs.Timer(track_end + 2.0, bs.WeakCallStrict(s._end_round))

    def _init_player(s, p):
        data = {
            'xp': 0,
            'bar_node': None,
            'feedback_node': None,
            'holding': {},
        }
        s._player_data[p] = data
        if p.actor and p.actor.node and p.actor.node.exists():
            p.assigninput(bs.InputType.BOMB_PRESS, lambda p=p: s._on_key_press(p, 1))
            p.assigninput(bs.InputType.BOMB_RELEASE, lambda p=p: s._on_key_release(p, 1))
            s._build_player_bar(p)

    def _disco_pulse(s):
        gn = bs.getactivity().globalsnode
        c = s._disco_colors[s._disco_idx % len(s._disco_colors)]
        gn.tint = c
        gn.ambient_color = (c[0]*1.5, c[1]*1.5, c[2]*1.5)
        s._disco_idx += 1

    def _build_player_bar(s, p):
        data = s._player_data[p]
        mnode = bs.newnode('math', owner=p.actor.node, attrs={
            'input1': (0, 2.2, 0),
            'operation': 'add',
        })
        p.actor.node.connectattr('torso_position', mnode, 'input2')
        bar_node = bs.newnode('text', owner=p.actor.node, attrs={
            'in_world': True,
            'h_align': 'center',
            'scale': 0.012,
            'color': (0.8, 0.3, 1.0, 1.0),
            'shadow': 1.0,
            'flatness': 1.0,
            'text': '░░░░░░░░░░',
        })
        mnode.connectattr('output', bar_node, 'position')
        data['bar_node'] = bar_node

    def _update_bar(s, player):
        data = s._player_data.get(player)
        if not data or not data['bar_node'] or not data['bar_node'].exists():
            return
        ratio = data['xp'] / s.MAX_XP
        filled = int(ratio * 10)
        r = ratio
        data['bar_node'].color = (0.4 + r * 0.6, 1.0 - r * 0.7, 1.0 - r, 1.0)
        data['bar_node'].text = '█' * filled + '░' * (10 - filled)

    def _spawn_pixie(s):
        s._pixie = Bot(
            position=(s.PIXIE_STAND_X, 0, s.PIXIE_STAND_Z),
            color=(1.0, 0.4, 0.8),
            highlight=(0.8, 0.2, 0.6),
            character='Pixel',
        )
        s._pixie.node.name = 'Pixie'
        s._pixie.node.name_color = (1, 0.4, 0.8)
        s._pixie.node.invincible = True
        s._pixie_home = (s.PIXIE_STAND_X, 0, s.PIXIE_STAND_Z)
        s._dance_timer = bs.Timer(0.3, bs.WeakCallStrict(s._dance), repeat=True)
        s._dance_phase = 0.0

    def _dance(s):
        if s._pixie_busy or not s._pixie.node.exists(): return
        import math
        s._dance_phase += 0.3
        s._pixie.move(math.sin(s._dance_phase) * 0.4, 0)

    def _build_rhythm_ui(s):
        s._ui_nodes = []

        bg = bs.newnode('image', attrs={
            'texture': bs.gettexture('white'),
            'absolute_scale': True,
            'position': (0, s.HIT_LINE_Y + 90),
            'scale': (240, 200),
            'color': (0.05, 0.0, 0.1),
            'opacity': 0.5,
        })
        s._ui_nodes.append(bg)

        hit_line = bs.newnode('image', attrs={
            'texture': bs.gettexture('white'),
            'absolute_scale': True,
            'position': (0, s.HIT_LINE_Y),
            'scale': (240, 3),
            'color': (1.0, 1.0, 1.0),
            'opacity': 0.9,
        })
        s._ui_nodes.append(hit_line)

        s._lane_glows = []
        for i, lx in enumerate(s.KEY_LANE_XS):
            icon = bs.newnode('image', attrs={
                'texture': bs.gettexture(STEPDOWN_KEY_TEXTURES[i]),
                'absolute_scale': True,
                'position': (lx, s.HIT_LINE_Y - 30),
                'scale': (34, 34),
                'color': (*STEPDOWN_KEY_COLORS[i],),
                'opacity': 0.35,
            })
            s._ui_nodes.append(icon)
            glow = bs.newnode('image', attrs={
                'texture': bs.gettexture('white'),
                'absolute_scale': True,
                'position': (lx, s.HIT_LINE_Y),
                'scale': (54, 4),
                'color': (*STEPDOWN_KEY_COLORS[i],),
                'opacity': 0.0,
            })
            s._lane_glows.append(glow)
            s._ui_nodes.append(glow)

        s._feedback_node = bs.newnode('text', attrs={
            'text': '',
            'position': (0, s.HIT_LINE_Y + 30),
            'scale': 0.8,
            'h_align': 'center',
            'v_align': 'center',
            'color': (1, 1, 1, 1),
            'shadow': 0.5,
            'flatness': 1.0,
        })
        s._ui_nodes.append(s._feedback_node)

    def _schedule_notes(s):
        for note in s._notes:
            delay = note['time']
            if note['type'] == 1:
                arrival = s._start_time + note['time']
                spawn_delay = max(0.0, note['time'] - s.NOTE_FALL_DURATION)
                t = bs.Timer(spawn_delay, bs.WeakCallStrict(s._spawn_note, note['key'], arrival))
                s._note_timers.append(t)
            else:
                release_time = s._start_time + note['time']
                s._note_timers.append(
                    bs.Timer(delay, bs.WeakCallStrict(s._mark_release, note['key'], release_time))
                )

    def _spawn_note(s, key_idx, arrival_time):
        lx = s.KEY_LANE_XS[key_idx]
        fall_dur = arrival_time - bs.time()
        if fall_dur <= 0:
            fall_dur = 0.1

        note_node = bs.newnode('image', attrs={
            'texture': bs.gettexture(STEPDOWN_KEY_TEXTURES[key_idx]),
            'absolute_scale': True,
            'position': (lx, s.NOTE_START_Y),
            'scale': (50, 50),
            'color': STEPDOWN_KEY_COLORS[key_idx],
            'opacity': 0.0,
        })

        bs.animate(note_node, 'opacity', {0.0: 0.0, 0.2: 1.0, fall_dur - 0.1: 1.0, fall_dur + 0.2: 0.0})

        bs.animate_array(note_node, 'position', 2, {
            0.0: (lx, s.NOTE_START_Y),
            fall_dur: (lx, s.HIT_LINE_Y),
        })
        bs.timer(fall_dur + 0.3, note_node.delete)

        s._pending_notes.append({
            'node': note_node,
            'key': key_idx,
            'arrival': arrival_time,
            'release_time': None,
            'type': 'tap',
            'hit': False,
            'press_time': None,
        })

    def _mark_release(s, key_idx, release_time):
        for note in reversed(s._pending_notes):
            if note['key'] == key_idx and not note['hit'] and note['type'] == 'tap':
                note['release_time'] = release_time
                note['type'] = 'hold'
                break

    def _flash_lane(s, key_idx, color):
        glow = s._lane_glows[key_idx]
        bs.animate(glow, 'opacity', {0.0: 0.9, 0.15: 0.0})

    def _show_feedback(s, text, color):
        if s._feedback_node.exists():
            s._feedback_node.text = text
            s._feedback_node.color = (*color, 1.0)
            bs.animate(s._feedback_node, 'opacity', {0.0: 1.0, 0.5: 0.0})

    def _on_key_press(s, player, key_idx):
        data = s._player_data.get(player)
        if not data: return
        now = bs.time()
        data['holding'][key_idx] = now
        s._flash_lane(key_idx, STEPDOWN_KEY_COLORS[key_idx])

        best = None
        best_diff = 999.0
        for note in s._pending_notes:
            if note['hit'] or note['key'] != key_idx: continue
            diff = abs(now - note['arrival'])
            if diff < best_diff:
                best_diff = diff
                best = note

        if best is None:
            s._show_feedback('MISS', (1, 0.3, 0.3))
            s._add_xp(player, -5)
            return

        if best['type'] == 'tap':
            if best_diff <= s.PERFECT_WINDOW:
                best['hit'] = True
                best['press_time'] = now
                s._show_feedback('PERFECT', (0.4, 1.0, 0.4))
                s._add_xp(player, 15)
            elif best_diff <= s.GOOD_WINDOW:
                best['hit'] = True
                best['press_time'] = now
                s._show_feedback('GOOD', (1.0, 0.8, 0.3))
                s._add_xp(player, 8)
            else:
                s._show_feedback('MISS', (1, 0.3, 0.3))
                s._add_xp(player, -5)
        elif best['type'] == 'hold':
            if best_diff <= s.PERFECT_WINDOW:
                best['press_time'] = now
            elif best_diff <= s.GOOD_WINDOW:
                best['press_time'] = now
            else:
                s._show_feedback('MISS', (1, 0.3, 0.3))
                s._add_xp(player, -5)

    def _on_key_release(s, player, key_idx):
        data = s._player_data.get(player)
        if not data: return
        now = bs.time()
        data['holding'].pop(key_idx, None)

        for note in s._pending_notes:
            if note['hit'] or note['key'] != key_idx or note['type'] != 'hold':
                continue
            if note['press_time'] is None:
                continue
            if note['release_time'] is None:
                continue
            release_diff = abs(now - note['release_time'])
            press_diff = abs(note['press_time'] - note['arrival'])
            if press_diff <= s.PERFECT_WINDOW and release_diff <= s.HOLD_PERFECT_WINDOW:
                note['hit'] = True
                s._show_feedback('PERFECT', (0.4, 1.0, 0.4))
                s._add_xp(player, 20)
            elif press_diff <= s.GOOD_WINDOW and release_diff <= s.HOLD_PERFECT_WINDOW * 2:
                note['hit'] = True
                s._show_feedback('GOOD', (1.0, 0.8, 0.3))
                s._add_xp(player, 10)
            else:
                note['hit'] = True
                s._show_feedback('MISS', (1, 0.3, 0.3))
                s._add_xp(player, -5)

    def _add_xp(s, player, amount):
        data = s._player_data.get(player)
        if not data: return
        data['xp'] = max(0, min(s.MAX_XP, data['xp'] + amount))
        s._update_bar(player)
        if data['xp'] >= s.MAX_XP:
            s._queue_kill(player)

    def _queue_kill(s, player):
        if player in s._kill_queue: return
        s._kill_queue.append(player)
        if not s._pixie_busy:
            s._process_kill_queue()

    def _process_kill_queue(s):
        if not s._kill_queue: return
        s._pixie_busy = True
        player = s._kill_queue[0]
        s._dance_timer = None

        bs.timer(0.001, lambda: Bubble(s._pixie.node,choice(STEPDOWN_KILL_LINES),color=s._pixie.node.color))

        import weakref
        _self = weakref.ref(s)
        _p = weakref.ref(player)

        def _chase():
            self = _self()
            p = _p()
            if self is None or not self._pixie.node.exists(): return
            if not p or not p.actor or not p.actor.node or not p.actor.node.exists():
                self._pixie_return()
                return
            wp = self._pixie.node.position
            pp = p.actor.node.position
            dx = pp[0]-wp[0]
            dz = pp[2]-wp[2]
            d = (dx**2+dz**2)**0.5 or 1
            if d < 1.2:
                self._pixie.move(0, 0)
                self._pixie.on_run(0)
                bs.timer(0.3, lambda: self._do_kill(p))
                return
            self._pixie.on_run(0)
            bs.timer(0.02, lambda: self._pixie.on_run(1) or self._pixie.move(dx/d, -dz/d))
            bs.timer(0.05, _chase)

        bs.timer(1.0, _chase)

    def _do_kill(s, player):
        try:
            if player.actor and player.actor.node and player.actor.node.exists():
                player.actor.node.shattered = 2
                s.stats.player_scored(player, 50, screenmessage=False)
                player.actor.handlemessage(bs.DieMessage())
        except Exception:
            pass
        if s._kill_queue:
            s._kill_queue.pop(0)
        s._pixie_return()

    def _pixie_return(s):
        import weakref
        _self = weakref.ref(s)
        home = s._pixie_home

        def _go_home():
            self = _self()
            if self is None or not self._pixie.node.exists(): return
            wp = self._pixie.node.position
            dx = home[0]-wp[0]
            dz = home[2]-wp[2]
            d = (dx**2+dz**2)**0.5 or 1
            if d < 0.5:
                self._pixie.move(0, 0)
                self._pixie.on_run(0)
                self._pixie_arrived_home()
                return
            self._pixie.on_run(0)
            bs.timer(0.02, lambda: self._pixie.on_run(1) or self._pixie.move(dx/d, -dz/d))
            bs.timer(0.05, _go_home)

        bs.timer(0.5, _go_home)

    def _pixie_arrived_home(s):
        bs.timer(0.001, lambda: Bubble(s._pixie.node,choice(STEPDOWN_PIXIE_LINES), color=s._pixie.node.color))
        s._pixie_busy = False
        if s._kill_queue:
            bs.timer(1.5, s._process_kill_queue)

    def spawn_player(s, p):
        spaz = super().spawn_player(p)
        s._player_data[p] = {
            'xp': 0,
            'bar_node': None,
            'feedback_node': None,
            'holding': {},
        }
        s._build_player_bar(p)
        s._hook_inputs(p)
        return spaz

    def _hook_inputs(s, p):
        if not p.actor: return
        orig_jump = p.actor.on_jump_press
        orig_jump_r = p.actor.on_jump_release
        orig_bomb = p.actor.on_bomb_press
        orig_bomb_r = p.actor.on_bomb_release
        orig_pickup = p.actor.on_pickup_press
        orig_pickup_r = p.actor.on_pickup_release
        orig_punch = p.actor.on_punch_press
        orig_punch_r = p.actor.on_punch_release

        p.assigninput(bs.InputType.JUMP_PRESS, lambda: (orig_jump(), s._on_key_press(p, 0)))
        p.assigninput(bs.InputType.JUMP_RELEASE, lambda: (orig_jump_r(), s._on_key_release(p, 0)))
        p.actor.on_bomb_press = lambda: s._on_key_press(p, 1)
        p.actor.on_bomb_release = lambda: s._on_key_release(p, 1)
        p.assigninput(bs.InputType.PICK_UP_PRESS, lambda: (orig_pickup(), s._on_key_press(p, 2)))
        p.assigninput(bs.InputType.PICK_UP_RELEASE, lambda: (orig_pickup_r(), s._on_key_release(p, 2)))
        p.assigninput(bs.InputType.PUNCH_PRESS, lambda: (orig_punch(), s._on_key_press(p, 3)))
        p.assigninput(bs.InputType.PUNCH_RELEASE, lambda: (orig_punch_r(), s._on_key_release(p, 3)))

#class Babysitter(
#    Level,
#    name=Strings.BABYSITTER_NAME,
#    desc=Strings.BABYSITTER_DESC,
#    tips=Strings.BABYSITTER_TIPS,
#    can_bomb=False,
#):
#    def on_begin(s):
#        super().on_begin()
#        from bascenev1lib.actor.spazbot import SpazBotSet, BrawlerBot, BomberBot, ChargerBot
#
#        s._bot_set = SpazBotSet()
#        s._spawn_timer = bs.Timer(3.0, bs.WeakCallStrict(s._spawn_wave), repeat=True)
#        s._wave = 0
#
#        spawn = s.map.ffa_spawn_points[0]
#        s._johnson = MadBot(
#            position=(spawn[0] + 2, spawn[1], spawn[2]),
#            color=(0.2, 0.2, 0.8),
#            highlight=(0.1, 0.1, 0.5),
#            character='Agent Johnson',
#        )
#        s._johnson.node.name = 'Babysitter'
#        s._johnson.node.name_color = (0.4, 0.6, 1.0)
#        s._johnson.node.invincible = True
#        s._johson_stream = Stream(s._johnson.node)
#        s._johnson_think_timer = bs.Timer(0.15, bs.WeakCallStrict(s._johnson_think), repeat=True)
#
#        s._johnson_lines = [
#            'stay behind me sir.',
#            'i got this.',
#            'threat neutralized.',
#            'you are safe now.',
#            'do not worry.',
#            'i see them.',
#            'stay back sir.',
#        ]
#        s._johnson_after_kill = [
#            'threat eliminated.',
#            'you are welcome.',
#            'all clear.',
#            'nobody touches my client.',
#            'just doing my job.',
#        ]
#
#    def _spawn_wave(s):
#        from bascenev1lib.actor.spazbot import BrawlerBot, BomberBot, ChargerBot
#        s._wave += 1
#        bot_types = [BrawlerBot, BomberBot, ChargerBot]
#        count = min(2 + s._wave, 6)
#        spawns = s.map.ffa_spawn_points
#        for i in range(count):
#            pos = choice(spawns)
#            s._bot_set.spawn_bot(
#                choice(bot_types),
#                pos=(pos[0], pos[1], pos[2]),
#                spawn_time=1.0,
#                on_spawn_call=s._on_bot_spawn,
#            )
#
#    def _on_bot_spawn(s, bot):
#        if random() < 0.15:
#            bs.timer(0.001, lambda: s._johson_stream.push(choice(s._johnson_lines)))
#
#    def _johnson_think(s):
#        if not s._johnson.node.exists(): return
#
#        living_bots = s._bot_set.get_living_bots()
#        if not living_bots:
#            s._johnson._stop_combos()
#            s._johnson.move(0, 0)
#            s._johnson.on_run(0)
#            return
#
#        jp = s._johnson.node.position
#        nearest = min(
#            (b for b in living_bots if b.node and b.node.exists()),
#            key=lambda b: (b.node.position[0]-jp[0])**2 + (b.node.position[2]-jp[2])**2,
#            default=None
#        )
#        if not nearest: return
#
#        tp = nearest.node.position
#        dx = tp[0]-jp[0]
#        dz = tp[2]-jp[2]
#        d = (dx**2+dz**2)**0.5 or 1
#
#        if s._johnson.node.hold_node:
#            s._johnson.move(0, 0)
#            s._johnson.on_run(0)
#            if not getattr(s._johnson, '_skill1_timer', None):
#                s._johnson._start_combos()
#        elif d < 1.2:
#            s._johnson._stop_combos()
#            s._johnson.move(0, 0)
#            s._johnson.skill2()
#            if random() < 0.05:
#                bs.timer(0.001, lambda: s._johnson_stream.push(choice(s._johnson_after_kill)))
#        else:
#            s._johnson._stop_combos()
#            s._johnson.on_run(0)
#            bs.timer(0.02, lambda: s._johnson.on_run(1) or s._johnson.move(dx/d, -dz/d))
#
#    def handlemessage(s, m):
#        if isinstance(m, bs.PlayerDiedMessage):
#            if getattr(s, '_round_ended', False): return
#            p = m.getplayer(bs.Player)
#            s._death_times[p] = bs.time()
#            s._death_order.append(p)
#            if len(s._death_order) == len(s.players):
#                s._round_ended = True
#                s._timer and s._timer.stop()
#                bs.timer(1.0, s._end_round)
#            super().handlemessage(m)
#        else:
#            super().handlemessage(m)
#
#    def _end_round(s):
#        try:
#            s._johnson_think_timer = None
#            s._spawn_timer = None
#            s._bot_set.clear()
#            s._johnson.bot.handlemessage(bs.DieMessage())
#        except Exception:
#            pass
#        super()._end_round()

# extra dependencies
# stuff used by various levels

class Bubble:
    __mem__ = {}
    def __init__(
        s,
        node: 'bascenev1.Node',
        text: str = 'what',
        color: tuple = (1,1,1),
        time: float | int = 4,
        mode: int = 0,
        res: list = [('█'),('▼')]
    ) -> None:
        if not 0 <= mode <= 5 : raise ValueError(f'mode can be an integer from 0 to 5, not {mode}')
        if not mode: mode = choice([1,2,3,4,5])
        s.gsw = lambda what: (
            (bui.get_string_width(what,1) or (len(what)*30))
            if what else 0
        )
        s.ans,s.kids,s.mats,s.time = [],[],[],time
        s.node,s.dead,s.text = node,False,text
        s.color,s.mode,s.res = color,mode,res
        s.mem = lambda: s.__class__.__mem__
        m = s.mem()
        o = m.get(node,0)
        if not getattr(o,'dead',1): bs.timer(0.2,bs.CallPartial(o.delete,force=True))
        s.show()
        m[node] = s
    def show(s):
        q,l,r = s.mats,s.kids,s.ans
        m = bs.newnode(
            'math',
            owner=s.node,
            attrs={
                'input1': (0,1.65,0),
                'operation': 'add'
            }
        )
        q.append(m)
        c = list(s.color)
        w = s.gsw(s.res[0])
        b = bs.newnode(
            'text',
            owner=m,
            attrs={
                'text': f'{ceil((s.gsw(s.text)+2*w)/w)*s.res[0]}\n{s.res[1]}',
                'in_world': True,
                'shadow': 1.0,
                'flatness': 1.0,
                'color': (c[0],c[1],c[2],0.2),
                'scale': 0.01,
                'h_align': 'center'
            }
        )
        l.append(b)
        txt = []
        mat = []
        kek = -s.gsw(s.text)/185
        sf = 0
        for i in range(len(s.text)):
            j = s.text[i]
            x = s.gsw(j)/95.0
            p1 = bs.newnode(
                'text',
                owner=m,
                attrs={
                    'text': j,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': s.color,
                    'scale': 0.01,
                    'h_align': 'left'
                }
            )
            txt.append(p1)
            ok = kek+sf
            p2 = bs.newnode(
                'math',
                owner=m,
                attrs={
                    'input1': (ok,1.65,0),
                    'operation': 'add'
                }
            )
            mat.append([p2,ok])
            s.node.connectattr('position',p2,'input2')
            p2.connectattr('output',p1,'position')
            sf += x
        l += txt
        q += [mat[i][0] for i in range(len(mat))]
        s.node.connectattr('position',m,'input2')
        m.connectattr('output',b,'position')
        z = s.time
        a = bs.animate(
            b,
            'scale',
            {
                0:0,
                z*0.041: 0.014,
                z*0.154: 0.014,
                z*0.167: 0.010,
                z*0.98: 0.010,
                z:0
            },
        )
        r.append(a)
        a = bs.animate_array(
            m,
            'input1',
            3,
            {
                0:(0,1.2,0),
                z*0.04:(0,1.65,0),
                z*0.98:(0,1.65,0),
                z:(0,1.2,0)
            }
        )
        r.append(a)
        r += [
            bs.animate(
                txt[i],
                'scale',
                {
                    0:0,
                    z*0.041: 0.015,
                    z*0.154: 0.015,
                    z*0.167: 0.010,
                    z*0.98: 0.010,
                    z:0
                },
            )
            for i in range(len(mat))
        ] if s.mode in [1,4] else []
        r += [
            bs.animate_array(
                mat[i][0],
                'input1',
                3,
                {
                    0:(mat[i][1]/4,1.2,0),
                    z*0.04:(mat[i][1]*1.5,1.65,0),
                    z*0.154:(mat[i][1]*1.5,1.65,0),
                    z*0.167:(mat[i][1],1.65,0),
                    z*0.98:(mat[i][1],1.65,0),
                    z:(mat[i][1]/4,1.2,0)
                }
            )
            for i in range(len(mat))
        ] if s.mode in [1,4] else []
        ok = (z*0.04*1.6)
        hm = [0.03,0.05][s.mode==2]
        r += [
            bs.animate_array(
                j[0],
                'input1',
                3,
                {
                    0.5+i*hm:(j[1],1.4,0),
                    0.5+i*hm+(ok*0.6):(j[1],1.9,0),
                    0.5+i*hm+ok:(j[1],1.65,0),
                    (z-(z*0.02)):(j[1],1.65,0),
                    z:(j[1],1.2,0)
                }
            )
            for i,j in enumerate(mat)
        ] if s.mode in [2,5] else []
        r += [
            bs.animate(
                txt[i],
                'opacity',
                {
                    0.5+i*hm:0,
                    (0.5+i*hm+ok)*0.98:1,
                    z*0.9:1,
                    z:0
                }
            )
            for i in range(len(mat))
        ] if s.mode in [2,4,5] else []
        r += [
            bs.animate(
                txt[i],
                'scale',
                {
                    0:0,
                    z*0.154: 0,
                    z*0.167: 0.010,
                    z*0.98: 0.010,
                    z:0
                },
            )
            for i in range(len(mat))
        ] if s.mode == 3 else []
        bs.timer(z,s.delete)
    def delete(s,force=False):
        if s.dead: return
        s.dead = True
        [i.delete() for i in s.ans if hasattr(i,'delete')]
        bs.timer(0.2,lambda:[i.delete() for i in s.kids+s.mats if hasattr(i,'delete')])
        if not force: return
        [bs.animate(
            i,
            'opacity',
            {
                0:i.opacity,
                0.2:0
            }
        ) for i in s.kids]

class Stream:
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

class WizardSpaz(bslib.actor.spaz.Spaz):
    def handlemessage(self, m):
        if isinstance(m, bs.OutOfBoundsMessage):
            act = bs.getactivity()
            if act and hasattr(act, 'spawn_points'):
                self.node.handlemessage(bs.StandMessage(choice(act.spawn_points)))
            return
        elif isinstance(m, bs.HitMessage) and m.hit_type == 'punch':
            try:
                p = m.get_source_player(bs.Player)
                act = bs.getactivity()
                if act and hasattr(act, '_on_wizard_punched'):
                    act._on_wizard_punched(p)
            except Exception:
                pass
        elif isinstance(m, bs.PickedUpMessage):
            try:
                spz = m.node.getdelegate(bslib.actor.spaz.Spaz)
                if spz:
                    p = spz.getplayer(bs.Player, False)
                    act = bs.getactivity()
                    if act and hasattr(act, '_on_wizard_picked_up'):
                        act._on_wizard_picked_up(p)
            except Exception:
                pass
        elif isinstance(m, bs.DroppedMessage):
            try:
                spz = m.node.getdelegate(bslib.actor.spaz.Spaz)
                if spz:
                    p = spz.getplayer(bs.Player, False)
                    act = bs.getactivity()
                    if act and hasattr(act, '_on_wizard_dropped'):
                        act._on_wizard_dropped(p)
            except Exception:
                pass
        super().handlemessage(m)

class RitualSpaz(bslib.actor.playerspaz.PlayerSpaz):
    def on_jump_press(self):
        super().on_jump_press()
        if (p := self.getplayer(bs.Player, False)) and (act := bs.getactivity()):
            act._on_input(p, 'jump')

    def on_punch_press(self):
        super().on_punch_press()
        if (p := self.getplayer(bs.Player, False)) and (act := bs.getactivity()):
            act._on_input(p, 'punch')

    def on_pickup_press(self):
        super().on_pickup_press()
        if (p := self.getplayer(bs.Player, False)) and (act := bs.getactivity()):
            act._on_input(p, 'pickup')

    def on_move_left_right(self, value: float):
        super().on_move_left_right(value)
        if (p := self.getplayer(bs.Player, False)) and (act := bs.getactivity()):
            act._on_spin(p, value)

    def handlemessage(self, m):
        if isinstance(m, bs.OutOfBoundsMessage):
            if (p := self.getplayer(bs.Player, False)) and (act := bs.getactivity()) and hasattr(act, '_reset_ritual'):
                self.node.handlemessage(bs.StandMessage(choice(act.spawn_points)))
                act._reset_ritual(p)
                bs.broadcastmessage(Strings.RITUAL_COWARD.format(p.getname()), color=(0.6, 0.3, 0.8))
                self.hitpoints = self.hitpoints_max
                self.node.hurt = 0.0
            return
        super().handlemessage(m)

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
        s.bub = Stream(s.node)
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

        s._think_timer = bs.Timer(0.15, bs.WeakCallStrict(s._think), repeat=True)

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

class MadBot(Bot):
    def skill1(s):
        s.on(0)
        s.on(1)
        bs.timer(0.04, lambda: s.on(2))
        bs.timer(0.07, lambda: s.on(3))

    def skill2(s):
        s.on(3)
        bs.timer(0.05, lambda: s.on(2))

    def _start_combos(s):
        s._skill1_timer = bs.Timer(0.4, bs.WeakCallStrict(s.skill1), repeat=True)
        s._shake_timer = bs.Timer(0.05, bs.WeakCallStrict(s._shake), repeat=True)

    def _stop_combos(s):
        s._skill1_timer = None
        s._shake_timer = None

    def _shake(s):
        s._is_shaking = not getattr(s, '_is_shaking', False)
        s.move(0.5, 0.1) if s._is_shaking else s.move(-0.5, 0.1)

    def move_to(s, t, min=0.7, time=10, on_done=None):
        _self = ref(s)
        nah = [False]
        def f(b=False):
            self = _self()
            if self is None or nah[0]: return
            try: p = self.node.position
            except: return
            dx = t[0]-p[0]
            dz = p[2]-t[2]
            if b:
                m = (dx**2+dz**2)**0.5
                try: self.move(dx/m, dz/m)
                except ZeroDivisionError: pass
            if dist((p[0],p[2]),(t[0],t[2])) < min:
                nah[0] = True
                self.move(0, 0)
                if on_done: bs.timer(0.2, on_done)
                return
            bs.timer(0.01, f)
        def timeout():
            nah[0] = True
            self = _self()
            if self: self.move(0, 0)
            if on_done: bs.timer(0.2, on_done)
        f(True)
        bs.timer(time, timeout)

    def follow(s, node, min=0.7, time=10, on_done=None):
        _self = ref(s)
        nah = [False]
        def f():
            self = _self()
            if self is None or nah[0] or not node.exists():
                if self: self.move(0, 0)
                return
            try:
                p = self.node.position
                t = node.position
            except: return
            dx = t[0]-p[0]
            dz = p[2]-t[2]
            m = (dx**2+dz**2)**0.5
            if min is not None and dist((p[0],p[2]),(t[0],t[2])) < min:
                self.move(0, 0)
                nah[0] = True
                if on_done: bs.timer(0.2, on_done)
                return
            try: self.move(dx/m, dz/m)
            except ZeroDivisionError: pass
            bs.timer(0.01, f)
        def timeout():
            nah[0] = True
            self = _self()
            if self: self.move(0, 0)
            if on_done: bs.timer(0.2, on_done)
        f()
        bs.timer(time, timeout)

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
            1,
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
