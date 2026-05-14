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

from re import findall
from weakref import ref
from codecs import decode
from math import dist, ceil
from collections import defaultdict
from random import choice, random, uniform, sample
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
        'Hold someone and turn in circles against a wall, and hear scream.',
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
    SCORE_GAME_OF = 'Game {} of {}'
    SCORE_PTS = '{} pts'
    SCORE_SURVIVED = '⏱ survived'
    SCORE_DIED = 'died {:.1f}s'

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
    ZOE_NAME = 'Zoe'
    ZOE_DESC = 'Make her mad. Get killed. Win.'
    ZOE_TIPS = [
        'She has limits.',
        'Everyone has a breaking point.',
        'The angrier she gets, the faster you win.',
    ]
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
    RITUAL_SAY_LABEL = '{} say: {}'
    RITUAL_SAY_WORDS = [
        'void', 'blood', 'bones', 'ash', 'shadow', 'stone', 'fire', 'dust',
        'hollow', 'grave', 'rust', 'smoke', 'iron', 'veil', 'dusk', 'mud',
        'rot', 'thorn', 'crow', 'salt', 'pale', 'dark', 'sink', 'lost',
        'cold', 'fade', 'gone', 'husk', 'wilt', 'grim',
    ]

    # stepdown
    STEPDOWN_NAME = 'Stepdown'
    STEPDOWN_DESC = 'Follow the rhythm. Too good and you die.'
    STEPDOWN_TIPS = [
        'The pixie is watching.',
        'Perfection is a death sentence.',
        'Follow the beats of death.',
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
    STEPDOWN_MISS = 'MISS'
    STEPDOWN_PERFECT = 'PERFECT'
    STEPDOWN_GOOD = 'GOOD'

    # babysitter
    BABYSITTER_NAME = 'Babysitter'
    BABYSITTER_DESC = 'Agent Johnson is doing his job too well.'
    BABYSITTER_TIPS = [
        'Push Johnson away.',
        'The bots just want to help.',
        'Let them in.',
        'Johnson means well.',
    ]
    BABYSITTER_JOHNSON_LINES = [
        'stay behind me sir.',
        'i got this.',
        'threat neutralized.',
        'you are safe now.',
        'do not worry.',
        'i see them.',
        'stay back sir.',
    ]
    BABYSITTER_JOHNSON_AFTER_KILL = [
        'threat eliminated.',
        'you are welcome.',
        'all clear.',
        'nobody touches my client.',
        'just doing my job.',
    ]

    # gran
    GRAN_NAME = 'Gran'
    GRAN_DESC = "Don't misbehave. She'll fix you."
    GRAN_TIPS = [
        'Break the rules. Earn her wrath.',
        'Her healing hurts more than you think.',
        'The rules change every round.',
        'Someone always ruins it for everyone.',
    ]
    GRAN_RULES_HEADER = "grandma's rules"
    GRAN_BERSERK_MSGS = [
        'OH YOU DID NOT.',
        'THATS IT.',
        'I RAISED YOU BETTER THAN THIS.',
        'COME HERE.',
        'YOU ARE IN BIG TROUBLE.',
        'OH SWEETIE. NO.',
        'ENOUGH.',
    ]
    GRAN_CALM_MSGS = [
        'i forgive you dear.',
        'just behave next time.',
        'i still love you.',
        'dont make me do that again.',
        'lets not repeat that.',
    ]
    GRAN_IDLE_MSGS = [
        'such a lovely day.',
        'i made cookies.',
        'stay out of trouble.',
        'behave yourselves.',
        'i am watching.',
        'do you want some tea?',
        'dont make me get up.',
    ]
    GRAN_PICKUP_MSG = 'PUT ME DOWN THIS INSTANT.'
    GRAN_HIT_MSG = 'HOW DARE YOU.'
    GRAN_PUNISH_CLOSE = 'too close!'
    GRAN_PUNISH_JUMP = 'no jumping!'
    GRAN_PUNISH_RUN = 'no running!'
    GRAN_PUNISH_HOLD = 'put that down!'
    GRAN_PUNISH_DIZZY = 'stop that spinning!'
    GRAN_PUNISH_PUNCH = 'no punching!'
    GRAN_RULES = {
        'no_hold':   "don't hold anything",
        'no_hold_gran': "don't hold grandma",
        'no_jump':   "don't jump",
        'no_punch':  "don't punch each other",
        'no_run':    "don't run",
        'no_close':  "don't come close to grandma",
        'no_dizzy':  "don't fall dizzy",
    }

    # sensei
    SENSEI_NAME = 'Sensei'
    SENSEI_DESC = 'Answer correctly. Or else.'
    SENSEI_TIPS = [
        'Think before you type.',
        'Wrong answers have consequences.',
        'She remembers everything.',
        'Chat to answer.',
    ]
    SENSEI_CORRECT_MSGS = [
        'correct.',
        'good.',
        'at least one of you is functional.',
        'fine.',
        'acceptable.',
        'i guess you are not completely hopeless.',
    ]
    SENSEI_WRONG_MSGS = [
        'absolutely not.',
        'are you serious right now.',
        'that is not even close.',
        'excuse me.',
        'i cannot believe this.',
        'who raised you.',
    ]
    SENSEI_PISSED_KILL_MSGS = [
        'i am DONE.',
        'that is IT.',
        'come here right now.',
        'you have made a grave mistake.',
        'i will end this personally.',
    ]
    SENSEI_TIMEOUT_MSGS = [
        'hello? anyone home.',
        'i am waiting.',
        'none of you know anything.',
        'completely hopeless.',
        'nobody. not a single one.',
        'i have been standing here.',
    ]
    SENSEI_RESUME_MSGS = [
        'anyway.',
        'next question.',
        'moving on.',
        'as i was saying.',
        'where were we.',
        'forget it.',
    ]
    SENSEI_PATIENCE = "Sensei's Patience"
    SENSEI_Q_ADD = 'what is {} + {}?'
    SENSEI_Q_SUB = 'what is {} - {}?'
    SENSEI_Q_MUL = 'what is {} x {}?'

    # nest
    NEST_NAME = 'Nest'
    NEST_DESC = 'When eggs are too personal.'
    NEST_TIPS = [
        'bun-bun worked VERY hard on dose eggies',
        'punch bun-bun while she carries u to escape',
        'she forgives fast. she forgets never.',
        'the egg place is on the left. dont go there.',
        'shattered players stay put for 4 seconds. then gone.',
    ]
    NEST_SPOTTED = [
        'heyyyy dat is MY eggie!!',
        'NO NO NO put dat down!!',
        'bun-bun sees u >:(',
        'MINE. dat is MINE.',
        'u gonna be SOWWY.',
        'bun-bun is SO mad rite now!!',
    ]
    NEST_GRABBED = [
        'gotcha!! >:3',
        'u r going to da basket now hehe',
        'bun-bun has u!! no escaping!!',
        'u basket. u freeze.',
        'u take eggie. u ded.'
    ]
    NEST_THREW = [
        'bye bye!! >:D',
        'into da basket u go!!',
        'YEET. with luv. bun-bun.',
        'hehe. u stay dere now. shattered.',
    ]
    NEST_FORGAVE = [
        'oh!! NEW eggie stealer!! u wait!!',
        'bun-bun forgives u... for NOW.',
        'wait u!! DROP DAT!!',
    ]
    NEST_IDLE = [
        'bun-bun is watching u...',
        'dont even tink about it.',
        'eggies r safe :)',
        'bun-bun loves her eggies so much.',
        '...bun-bun sees EVERYTHING.',
    ]
    NEST_RETURN = [
        'dere dere little eggie come home',
        'bun-bun brings u back safe',
        'bun-bun is picking up da eggies now',
    ]
    NEST_HELLO = 'bun-bun is here!! >:3'

    # zola
    ZOLA_NAME = 'Zola'
    ZOLA_DESC = 'Chase Lucky. Spin the slots. Hope for bad luck.'
    ZOLA_TIPS = [
        'Punch Lucky to spin the slots.',
        'Shields and health are punishments here.',
        'He jumps... a lot. Keep chasing.',
        'Wait for the slots to stop spinning.',
        'Bombs, Lightning, and Death are Jackpots.',
    ]
    ZOLA_IDLE = [
        "where's me pot o' gold?",
        "ye'll never catch me!",
        "the rainbow is mine!",
        "hop hop hop!",
        "im hoarding all the luck!",
        "green is me favorite color!",
    ]
    ZOLA_BLESSING = [
        "have a blessing, laddie!",
        "too much luck for ye!",
        "a shield for yer troubles!",
        "stay safe now! hahaha!",
        "no dying today!",
        "let me patch ye right up!",
    ]
    ZOLA_TRICK = [
        "chilly today, aye?",
        "missed me!",
        "a little trick for ye!",
        "yer luck is frozen!",
        "take a nap, laddie!",
    ]
    ZOLA_JACKPOT = [
        "JACKPOT!!!",
        "THE END OF THE RAINBOW!!!",
        "TERRIBLE LUCK! I LOVE IT!",
        "YE HIT THE DEADLY POT!",
        "WATCH YOUR HEAD!",
    ]
    ZOLA_RULES_TEXT = (
        "LUCKY'S SLOTS\n"
        "- 30% Blessing [DEF, GLV, MED]\n"
        "- 50% Trick [ICE, ZZZ, YET, NUL]\n"
        "- 20% Jackpot [CRS, TNT, ZAP, RIP]"
    )
    ZOLA_HELLO = "catch me if ye can!!"

    # debt
    DEBT_NAME = 'Debt'
    DEBT_DESC = 'Ruin your finances to win. Hit the debt limit.'
    DEBT_TIPS = [
        'Hit the debt limit to summon the Collector and win.',
        'Medical bills are expensive. Get hurt!',
        'Punching players transfers your money to them.',
        'Zoe loves suing people. Provoke her.',
        'Gambling is a great way to lose money.'
    ]
    DEBT_REPO_ARREST = [
        "Time to pay.",
        "Your account is closed.",
        "Collecting your debt.",
        "Execution authorized."
    ]
    DEBT_ZOE_SUE = [
        "I'm suing you!",
        "My lawyers will contact you!",
        "That's assault!",
        "Personal space!"
    ]
    DEBT_RULES_TEXT = "DEBT LIMIT: ${}\nPENALTY: {}"
    DEBT_GAMBLE = 'GAMBLE ${}'
    DEBT_REPO_SPAWN = "I am here to collect."
    DEBT_REPO_TARGET = "Target acquired: {}"
    DEBT_REPO_QUEUE = "Foreclosure pending for {}..."
    DEBT_REASON_OBSTRUCTION = "Obstruction"
    DEBT_REASON_ASSAULT = "Assault"
    DEBT_REASON_KIDNAPPING = "Kidnapping"
    DEBT_REASON_GAMBLE = "Gamble Fee"
    DEBT_REASON_JACKPOT = "JACKPOT"
    DEBT_REASON_MEDICAL = "Medical Bill"
    DEBT_REASON_SETTLEMENT = "Settlement"
    DEBT_REASON_RESTRAINING = "Restraining Order"

    # psycho pixie
    PIXIE_NAME = 'Psycho Pixie'
    PIXIE_DESC = 'Test her patience in chat.'
    PIXIE_TIPS = [
        'Chat to change her likability.',
        'She will walk right up to your face to reply.',
        'Interrupting her changes her mind immediately.',
        'At -100 Likability, she breaks.',
        'High rep players might receive unexpected blessings.',
        'Falling off the edge just teleports you back.'
    ]
    PIXIE_IDLE_LINES = [
        'so boring...',
        '*flutters wings aimlessly*',
        'anyone want to chat?',
        'just a pixie in a violent world.',
        'i think i lost a feather.',
        '*hums a holy tune*',
        'where is everyone?',
        'if no one talks im going to nap.'
    ]
    PIXIE_BLESS = [
        'here, have some holy magic!',
        'you are my favorite.',
        'a gift for a kind soul!',
        '*boop* healed!'
    ]
    PIXIE_CURSE = [
        'chill out.',
        'you need a timeout.',
        'im not mad, just disappointed.',
        '*freezes your soul*'
    ]
    PIXIE_HELLO = "Hello! Wanna talk?"
    PIXIE_REP = "Rep: {}"
    PIXIE_ANGRY = "THAT'S IT."
    PIXIE_CALM = "Anyone else?"

class Level(bs.GameActivity[bs.Player, bs.Team]):
    __test__ = None
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
        enabled_levels = [l for l in cls.__levels__ if settings.get(f'Enable {l.name}', True)]
        if not enabled_levels:
            enabled_levels = cls.__levels__

        if level:
            level_cls = level
        elif settings.get('Random Levels', False):
            level_cls = choice(enabled_levels)
        else:
            idx = settings.get('_level_idx', 0) % len(enabled_levels)
            level_cls = enabled_levels[idx]
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

        enabled_levels = [l for l in s.__levels__ if settings.get(f'Enable {l.name}', True)]
        total_games = len(enabled_levels) if enabled_levels else len(s.__levels__)

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
        s._drop_timer = bs.Timer(3, bs.WeakCallStrict(s._drop_bomb), repeat=True)

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
        s._holding = False
        s._launched = False
        s._hold_time = 0.0
        s._hold_timer = None
        s._countdown_node = None
        s._respawn_box()

    def _respawn_box(s):
        s._launched = False
        s._holding = False
        s._hold_time = 0.0
        if s._hold_timer: s._hold_timer = None
        if s._countdown_node and s._countdown_node.exists():
            s._countdown_node.delete()
        s._countdown_node = None
        
        spawn_pos = s.map.ffa_spawn_points[0]
        cx, cy, cz = spawn_pos[0], spawn_pos[1] + 1.0, spawn_pos[2]
        
        from bascenev1lib.actor.bomb import Bomb
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
                self._respawn_box()
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
    name=Strings.ZOE_NAME,
    desc=Strings.ZOE_DESC,
    tips=Strings.ZOE_TIPS,
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
                if self._zoe_orig_hm: self._zoe_orig_hm(m)
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
        _s = ref(s)
        _p = ref(p)
        def _on_jump():
            self = _s()
            player = _p()
            if self and player and player.actor:
                self._on_player_jump(player)
                player.actor.on_jump_press()
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
        s._patrol_timer = bs.Timer(4.0, bs.WeakCallStrict(s._patrol), repeat=True)
        s._check_timer = bs.Timer(0.1, bs.WeakCallStrict(s._check_annoyances), repeat=True)
        s._say(choice(Strings.ZOE_CALM_MSGS))
        s._update_meter()

    def _end_round(s):
        if s._zoe and s._zoe_orig_hm:
            s._zoe.bot.handlemessage = s._zoe_orig_hm
        s._zoe_orig_hm = None
        s._rage_timer = None
        s._patrol_timer = None
        s._check_timer = None
        s._anger_timer = None
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
            label = Strings.RITUAL_SAY_LABEL.format(bui.charstr(bui.SpecialChar.LOGO_FLAT), words)
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

        enabled_levels = [l for l in s.__levels__ if settings.get(f'Enable {l.name}', True)]
        total = len(enabled_levels) if enabled_levels else len(s.__levels__)

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

class Stepdown(
    Level,
    name=Strings.STEPDOWN_NAME,
    desc=Strings.STEPDOWN_DESC,
    tips=Strings.STEPDOWN_TIPS,
    include=['Football Stadium'],
    can_bomb=False,
    music=[
        bs.MusicType.TO_THE_DEATH,
        bs.MusicType.GRAND_ROMP
    ]
):
    KEY_LANE_XS = [-120, -40, 40, 120]
    HIT_LINE_Y = -150
    NOTE_START_Y = 350
    NOTE_FALL_DURATION = 2.0
    MAX_XP = 100
    PIXIE_STAND_X = 6.0
    PIXIE_STAND_Z = 0.0

    PERFECT_WINDOW = 0.02
    GOOD_WINDOW = 0.085

    def __init__(s, settings):
        super().__init__(settings)
        s._player_data = {}
        s._kill_queue = []
        s._pixie_busy = False
        s._pending_notes = []
        s._note_timers = []
        s._dance_timer = None
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
            [{'time': t, 'key': v[0], 'type': v[1]} for t, v in raw.items() if v[1] == 1],
            key=lambda x: x['time']
        )

        s._spawn_pixie()
        s._build_rhythm_ui()

        for p in s.players:
            s._hook_inputs(p)

        bs.setmusic(s._music_type)
        s._start_time = bs.time()
        s._schedule_notes()
        track_end = max(t for t in STEPDOWN_TRACK[s._music_type].keys())
        s._track_end_timer = bs.Timer(track_end + 2.0, bs.WeakCallStrict(s._end_round))

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
        lane_bg_color = (0.05, 0.05, 0.1)
        for i, lx in enumerate(s.KEY_LANE_XS):
            bg = bs.newnode('image', attrs={
                'texture': bs.gettexture('white'),
                'scale': (60, 550),
                'color': lane_bg_color,
                'opacity': 0.5,
                'attach': 'center',
                'position': (lx, 100),
            })
            s._ui_nodes.append(bg)
            tex = bs.newnode('image', attrs={
                'texture': bs.gettexture(STEPDOWN_KEY_TEXTURES[i]),
                'scale': (50, 50),
                'color': STEPDOWN_KEY_COLORS[i],
                'opacity': 0.9,
                'attach': 'center',
                'position': (lx, s.HIT_LINE_Y),
            })
            s._ui_nodes.append(tex)
            
        line = bs.newnode('image', attrs={
            'texture': bs.gettexture('white'),
            'scale': (360, 4),
            'color': (1, 1, 1),
            'opacity': 0.3,
            'attach': 'center',
            'position': (0, s.HIT_LINE_Y),
        })
        s._ui_nodes.append(line)
        
        s._lane_glows = []
        for lx in s.KEY_LANE_XS:
            glow = bs.newnode('image', attrs={
                'texture': bs.gettexture('white'),
                'scale': (60, 60),
                'color': (1, 1, 1),
                'opacity': 0.0,
                'attach': 'center',
                'position': (lx, s.HIT_LINE_Y),
            })
            s._lane_glows.append(glow)

    def _flash_lane(s, key_idx, color):
        if key_idx >= len(s._lane_glows): return
        glow = s._lane_glows[key_idx]
        if not glow.exists(): return
        glow.color = color
        bs.animate(glow, 'opacity', {0.0: 0.8, 0.15: 0.0})

    def _schedule_notes(s):
        if not s._start_time: return
        now = bs.time()
        for note_def in s._notes:
            t = note_def['time']
            
            n = dict(note_def)
            n['arrival'] = s._start_time + t
            n['hit'] = False
            s._pending_notes.append(n)
            
            time_until_hit = n['arrival'] - now
            time_start = time_until_hit - s.NOTE_FALL_DURATION
            
            target_y = s.HIT_LINE_Y
            distance_to_hit = s.NOTE_START_Y - target_y
            speed = distance_to_hit / s.NOTE_FALL_DURATION
            
            extra_fall = 100.0
            total_fall_dist = distance_to_hit + extra_fall
            total_duration = total_fall_dist / speed
            
            node = bs.newnode('image', attrs={
                'texture': bs.gettexture(STEPDOWN_KEY_TEXTURES[n['key']]),
                'scale': (45, 45),
                'color': STEPDOWN_KEY_COLORS[n['key']],
                'opacity': 1.0,
                'attach': 'center',
                'position': (s.KEY_LANE_XS[n['key']], s.NOTE_START_Y),
            })
            s._ui_nodes.append(node)
            n['node'] = node

            if time_start < 0:
                passed_time = -time_start
                start_y_real = s.NOTE_START_Y - speed * passed_time
                start_time_anim = 0.0
                end_time_anim = total_duration - passed_time
            else:
                start_y_real = s.NOTE_START_Y
                start_time_anim = time_start
                end_time_anim = start_time_anim + total_duration

            bs.animate_array(node, 'position', 2, {
                start_time_anim: (s.KEY_LANE_XS[n['key']], start_y_real),
                end_time_anim: (s.KEY_LANE_XS[n['key']], target_y - extra_fall),
            })

            if time_start > 0:
                bs.animate(node, 'opacity', {
                    0: 0.0,
                    start_time_anim - 0.01: 0.0,
                    start_time_anim: 1.0
                })
            else:
                node.opacity = 1.0
            
            def _remove(note=n):
                if note.get('node') and note['node'].exists():
                    note['node'].delete()
            s._note_timers.append(bs.timer(end_time_anim + 0.1, _remove))

    def _show_feedback(s, text, color):
        if not hasattr(s, '_feedback_node') or not s._feedback_node or not s._feedback_node.exists():
            s._feedback_node = bs.newnode('text', attrs={
                'v_attach': 'center',
                'h_attach': 'center',
                'h_align': 'center',
                'position': (0, -60),
                'scale': 1.2,
                'shadow': 1.0,
                'flatness': 1.0,
                'color': (1, 1, 1, 0),
                'text': '',
            })
        s._feedback_node.text = text
        s._feedback_node.color = (*color, 1.0)
        bs.animate(s._feedback_node, 'opacity', {0.0: 1.0, 0.5: 0.0})

    def _on_key_press(s, player, key_idx):
        data = s._player_data.get(player)
        if not data: return
        now = bs.time()
        s._flash_lane(key_idx, STEPDOWN_KEY_COLORS[key_idx])

        best = None
        best_diff = 999.0
        for note in s._pending_notes:
            if note['hit'] or note['key'] != key_idx: continue
            diff = abs(now - note['arrival'])
            if diff < best_diff and diff <= s.GOOD_WINDOW:
                best_diff = diff
                best = note

        if best is None:
            s._show_feedback(Strings.STEPDOWN_MISS, (1, 0.3, 0.3))
            s._add_xp(player, -5)
            return

        best['hit'] = True
        if best.get('node') and best['node'].exists():
            best['node'].delete()

        if best_diff <= s.PERFECT_WINDOW:
            s._show_feedback(Strings.STEPDOWN_PERFECT, (0.4, 1.0, 0.4))
            s._add_xp(player, 15)
        else:
            s._show_feedback(Strings.STEPDOWN_GOOD, (1.0, 0.8, 0.3))
            s._add_xp(player, 8)

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

        _self = ref(s)
        bs.timer(0.001, lambda: (a := _self()) and Bubble(a._pixie.node, choice(Strings.STEPDOWN_KILL_LINES), color=a._pixie.node.color))

        _p = ref(player)

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
        _self = ref(s)
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
        _self = ref(s)
        bs.timer(0.001, lambda: (a := _self()) and Bubble(a._pixie.node, choice(Strings.STEPDOWN_PIXIE_LINES), color=a._pixie.node.color))
        s._pixie_busy = False
        if s._kill_queue:
            bs.timer(1.5, bs.WeakCallStrict(s._process_kill_queue))

    def spawn_player(s, p):
        spaz = super().spawn_player(p)
        s._player_data[p] = {
            'xp': 0,
            'bar_node': None,
            'feedback_node': None,
        }
        s._build_player_bar(p)
        s._hook_inputs(p)
        return spaz

    def _hook_inputs(s, p):
        if not p.actor: return
        p.actor.set_bomb_count(-2)
        _s = ref(s)
        _p = ref(p)

        def _jump():
            self = _s(); player = _p()
            if self and player and player.actor:
                player.actor.on_jump_press(); self._on_key_press(player, 0)
        def _bomb():
            self = _s(); player = _p()
            if self and player and player.actor:
                player.actor.on_bomb_press(); self._on_key_press(player, 1)
        def _pickup():
            self = _s(); player = _p()
            if self and player and player.actor:
                player.actor.on_pickup_press(); self._on_key_press(player, 2)
        def _punch():
            self = _s(); player = _p()
            if self and player and player.actor:
                player.actor.on_punch_press(); self._on_key_press(player, 3)

        p.assigninput(bs.InputType.JUMP_PRESS, _jump)
        p.assigninput(bs.InputType.BOMB_PRESS, _bomb)
        p.assigninput(bs.InputType.PICK_UP_PRESS, _pickup)
        p.assigninput(bs.InputType.PUNCH_PRESS, _punch)

class Babysitter(
    Level,
    name=Strings.BABYSITTER_NAME,
    desc=Strings.BABYSITTER_DESC,
    tips=Strings.BABYSITTER_TIPS,
    can_bomb=False,
):
    def on_begin(s):
        super().on_begin()
        from bascenev1lib.actor.spazbot import SpazBotSet, BrawlerBot, ChargerBot

        s._bot_set = SpazBotSet()
        s._spawn_timer = bs.Timer(7.0, bs.WeakCallStrict(s._spawn_wave), repeat=True)
        _self = ref(s)
        bs.timer(3, lambda: (a := _self()) and a._spawn_wave())
        s._wave = 0

        spawn = s.map.ffa_spawn_points[0]
        s._johnson = MadBot(
            position=(spawn[0] + 2, spawn[1], spawn[2]),
            color=(0.2, 0.2, 0.8),
            highlight=(0.1, 0.1, 0.5),
            character='Agent Johnson'
        )
        s._johnson_stream = Stream(s._johnson.node)
        s._johnson.node.name = 'Babysitter'
        s._johnson.bot.equip_boxing_gloves()
        s._johnson.node.name_color = (0.4, 0.6, 1.0)
        s._johnson_think_timer = bs.Timer(0.15, bs.WeakCallStrict(s._johnson_think), repeat=True)

        s._johnson_lines = Strings.BABYSITTER_JOHNSON_LINES
        s._johnson_after_kill = Strings.BABYSITTER_JOHNSON_AFTER_KILL

    def spawn_player(s, p):
        spaz = super().spawn_player(p)
        _self = ref(s)
        _spaz = ref(spaz)

        def _hm(m):
            if isinstance(m, bs.HitMessage):
                a = _self()
                if a is not None:
                    j = getattr(a, '_johnson', None)
                    if j and j.node and j.node.exists():
                        if m.srcnode == j.node:
                            return
            spz = _spaz()
            if spz: bslib.actor.playerspaz.PlayerSpaz.handlemessage(spz, m)

        spaz.handlemessage = _hm
        return spaz

    def _spawn_wave(s):
        from bascenev1lib.actor.spazbot import BrawlerBot, ChargerBot
        s._wave += 1
        bot_types = [BrawlerBot, ChargerBot]
        count = 1
        spawns = s.map.ffa_spawn_points
        for i in range(count):
            pos = choice(spawns)
            s._bot_set.spawn_bot(
                choice(bot_types),
                pos=(pos[0], pos[1], pos[2]),
                spawn_time=1.0,
                on_spawn_call=s._on_bot_spawn,
            )

    def _on_bot_spawn(s, bot):
        if random() < 0.15:
            _self = ref(s)
            bs.timer(0.001, lambda: (a := _self()) and a._johnson_stream.push(choice(a._johnson_lines)))

    def _johnson_think(s):
        if not s._johnson.node.exists(): return

        living_bots = s._bot_set.get_living_bots()
        if not living_bots:
            s._johnson._stop_combos()
            s._johnson.move(0, 0)
            s._johnson.on_run(0)
            return

        jp = s._johnson.node.position
        nearest = min(
            (b for b in living_bots if b.node and b.node.exists()),
            key=lambda b: (b.node.position[0]-jp[0])**2 + (b.node.position[2]-jp[2])**2,
            default=None
        )
        if not nearest: return

        tp = nearest.node.position
        dx = tp[0]-jp[0]
        dz = tp[2]-jp[2]
        d = (dx**2+dz**2)**0.5 or 1

        _self = ref(s)
        if s._johnson.node.hold_node:
            if s._johnson.node.hold_node.getnodetype() == 'spaz' and s._johnson.node.hold_node.hurt < 1:
                s._johnson.move(0, 0)
                s._johnson.on_run(0)
                if not getattr(s._johnson, '_skill1_timer', None):
                    s._johnson._start_combos()
            else:
                s._johnson.on(2)
        elif d < 1.2:
            s._johnson._stop_combos()
            s._johnson.move(0, 0)
            s._johnson.skill2()
            if random() < 0.05:
                bs.timer(0.001, lambda: (a := _self()) and a._johnson_stream.push(choice(a._johnson_after_kill)))
        else:
            s._johnson._stop_combos()
            s._johnson.on_run(0)
            bs.timer(0.02, lambda: (a := _self()) and (a._johnson.on_run(1) or a._johnson.move(dx/d, -dz/d)))

    def _end_round(s):
        s._johnson_think_timer = None
        s._spawn_timer = None
        super()._end_round()

class Gran(
    Level,
    name=Strings.GRAN_NAME,
    desc=Strings.GRAN_DESC,
    tips=Strings.GRAN_TIPS,
    include=['Football Stadium'],
    can_bomb=False,
):
    RULE_COUNT = 3
    CLOSE_RADIUS = 2.0
    RUN_SPEED = 4.5
    BERSERK_DURATION = 3.0

    def __init__(s, settings):
        super().__init__(settings)
        s._gran = None
        s._gran_stream = None
        s._berserk_target = None
        s._berserk_timer = None
        s._think_timer = None
        s._check_timer = None
        s._idle_timer = None
        s._active_rules = []
        s._rules_node = None
        s._orig_gran_hm = None

    def on_begin(s):
        super().on_begin()

        spawn = s.map.ffa_spawn_points[0]
        s._gran = MadBot(
            position=(spawn[0], spawn[1], spawn[2]),
            color=(0.85, 0.8, 0.75),
            highlight=(0.6, 0.55, 0.5),
            character='OldLady',
        )
        s._gran.node.name = 'Grandma'
        s._gran.node.name_color = (1.0, 0.9, 0.7)
        s._gran_stream = Stream(s._gran.node)

        _orig = s._gran.bot.handlemessage
        s._orig_gran_hm = _orig
        _self = ref(s)

        def _gran_hm(m):
            self = _self()
            if self is None: return
            if isinstance(m, bs.HitMessage):
                try:
                    src = m.get_source_player(bs.Player)
                except Exception:
                    src = None
                if src is not None:
                    self._on_gran_hit(src)
                if self._orig_gran_hm: self._orig_gran_hm(m)
                return
            if isinstance(m, bs.PickedUpMessage):
                try:
                    spz = m.node.getdelegate(bslib.actor.spaz.Spaz)
                    src = spz.getplayer(bs.Player, False) if spz else None
                except Exception:
                    src = None
                if src is not None:
                    self._on_gran_pickup(src)
                return
            if isinstance(m, bs.OutOfBoundsMessage):
                pos = choice(self.spawn_points)
                self._gran.node.handlemessage(bs.StandMessage(pos))
                return
            _orig(m)

        s._gran.bot.handlemessage = _gran_hm

        all_rule_keys = list(Strings.GRAN_RULES.keys())
        s._active_rules = sample(all_rule_keys, min(s.RULE_COUNT, len(all_rule_keys)))

        s._build_rules_ui()

        s._check_timer = bs.Timer(0.2, bs.WeakCallStrict(s._check_rules), repeat=True)
        s._idle_timer = bs.Timer(8.0, bs.WeakCallStrict(s._gran_idle), repeat=True)
        s._think_timer = bs.Timer(0.15, bs.WeakCallStrict(s._gran_wander), repeat=True)

        gn = bs.getactivity().globalsnode
        bs.animate_array(gn, 'tint', 3, {0: (1, 1, 1), 2: (1.0, 0.92, 0.8)})

        bs.timer(2.0, lambda: s._gran_stream.push(choice(Strings.GRAN_IDLE_MSGS)))

    def _build_rules_ui(s):
        lines = [Strings.GRAN_RULES_HEADER]
        for key in s._active_rules:
            lines.append('- ' + Strings.GRAN_RULES[key])
        text = '\n'.join(lines)
        s._rules_node = bs.newnode('text', attrs={
            'text': text,
            'v_attach': 'center',
            'h_attach': 'left',
            'h_align': 'left',
            'v_align': 'center',
            'position': (20, 0),
            'scale': 0.6,
            'color': (1.0, 0.9, 0.7, 0.85),
            'shadow': 1.0,
            'flatness': 1.0,
        })
        bs.animate(s._rules_node, 'opacity', {0: 0, 0.5: 1})

    def _check_rules(s):
        if s._berserk_target is not None: return
        if not s._gran or not s._gran.node.exists(): return

        gp = s._gran.node.position

        for p in s.players:
            if not p.actor or not p.actor.node or not p.actor.node.exists(): continue
            node = p.actor.node
            pp = node.position

            for rule in s._active_rules:

                if rule == 'no_close':
                    d = ((pp[0]-gp[0])**2 + (pp[2]-gp[2])**2) ** 0.5
                    if d < s.CLOSE_RADIUS:
                        s._go_berserk(p, Strings.GRAN_PUNISH_CLOSE)
                        return

                elif rule == 'no_jump':
                    vel = node.velocity
                    if vel[1] > 2.5:
                        s._go_berserk(p, Strings.GRAN_PUNISH_JUMP)
                        return

                elif rule == 'no_run':
                    vel = node.velocity
                    speed = (vel[0]**2 + vel[2]**2) ** 0.5
                    if speed > s.RUN_SPEED:
                        s._go_berserk(p, Strings.GRAN_PUNISH_RUN)
                        return

                elif rule == 'no_hold':
                    if node.hold_node:
                        s._go_berserk(p, Strings.GRAN_PUNISH_HOLD)
                        return

                elif rule == 'no_dizzy':
                    if node.knockout > 0:
                        s._go_berserk(p, Strings.GRAN_PUNISH_DIZZY)
                        return

                elif rule == 'no_punch':
                    pass

                elif rule == 'no_hold_gran':
                    pass

    def _on_gran_hit(s, player):
        s._gran_stream.push(Strings.GRAN_HIT_MSG)
        s._go_berserk(player, Strings.GRAN_HIT_MSG)

    def _on_gran_pickup(s, player):
        s._gran_stream.push(Strings.GRAN_PICKUP_MSG)
        s._go_berserk(player, Strings.GRAN_PICKUP_MSG)

    def _go_berserk(s, player, reason=''):
        if not s._gran or not s._gran.node.exists(): return
        s._berserk_target = player
        s._berserk_timer = None
        bs.getsound('orchestraHit4').play()
        s._gran_stream.push(choice(Strings.GRAN_BERSERK_MSGS))
        s._think_timer = None

        _self = ref(s)
        _p = ref(player)

        def _think():
            self = _self()
            p = _p()
            if self is None or not self._gran or not self._gran.node.exists(): return
            if self._berserk_target is not player: return
            if not p or not p.actor or not p.actor.node or not p.actor.node.exists():
                self._calm_down()
                return
            gp = self._gran.node.position
            pp = p.actor.node.position
            dx = pp[0] - gp[0]
            dz = pp[2] - gp[2]
            d = (dx**2 + dz**2) ** 0.5 or 1
            if self._gran.node.hold_node == p.actor.node:
                self._gran.move(0, 0)
                self._gran.on_run(0)
                if not getattr(self._gran, '_skill1_timer', None):
                    self._gran._start_combos()
            elif self._gran.node.hold_node:
                self._gran._stop_combos()
                self._gran.on(2)
            elif d < 1.2:
                self._gran._stop_combos()
                self._gran.move(0, 0)
                self._gran.skill2()
            else:
                self._gran._stop_combos()
                self._gran.on_run(0)
                bs.timer(0.02, lambda: self._gran.on_run(1) or self._gran.move(dx/d, -dz/d))
            bs.timer(0.15, _think)

        bs.timer(0.1, _think)
        s._berserk_timer = bs.Timer(s.BERSERK_DURATION, bs.WeakCallStrict(s._calm_down))

    def _calm_down(s):
        s._berserk_target = None
        s._berserk_timer = None
        if s._gran and s._gran.node.exists():
            s._gran._stop_combos()
            if s._gran.node.hold_node:
                s._gran.on(2)
            s._gran.move(0, 0)
            s._gran.on_run(0)
            s._gran_stream.push(choice(Strings.GRAN_CALM_MSGS))
        s._think_timer = bs.Timer(0.15, bs.WeakCallStrict(s._gran_wander), repeat=True)

    def _gran_wander(s):
        if s._berserk_target is not None: return
        if not s._gran or not s._gran.node.exists(): return
        target = choice(s.spawn_points)
        gp = s._gran.node.position
        dx = target[0] - gp[0]
        dz = target[2] - gp[2]
        d = (dx**2 + dz**2) ** 0.5 or 1
        if d > 1.5:
            s._gran.on_run(0)
            s._gran.move(dx/d * 0.4, -dz/d * 0.4)
        else:
            s._gran.move(0, 0)

    def _gran_idle(s):
        if not s._gran or not s._gran.node.exists(): return
        if s._berserk_target is not None: return
        s._gran_stream.push(choice(Strings.GRAN_IDLE_MSGS))

    def spawn_player(s, p):
        spaz = super().spawn_player(p)
        _s = ref(s)
        _p = ref(p)

        def _punch():
            player = _p()
            if player and player.actor:
                bslib.actor.playerspaz.PlayerSpaz.on_punch_press(player.actor)
            self = _s()
            if self is None: return
            if 'no_punch' not in self._active_rules: return
            if self._berserk_target is not None: return
            if not player or not player.actor or not player.actor.node or not player.actor.node.exists(): return
            node = player.actor.node
            pp = node.position
            for other in self.players:
                if other is player: continue
                if not other.actor or not other.actor.node or not other.actor.node.exists(): continue
                op = other.actor.node.position
                d = ((pp[0]-op[0])**2 + (pp[2]-op[2])**2) ** 0.5
                if d < 2.0:
                    self._go_berserk(player, Strings.GRAN_PUNISH_PUNCH)
                    return

        spaz.on_punch_press = _punch
        return spaz

    def _end_round(s):
        if s._gran and s._orig_gran_hm:
            s._gran.bot.handlemessage = s._orig_gran_hm
        s._orig_gran_hm = None
        s._check_timer = None
        s._idle_timer = None
        s._think_timer = None
        s._berserk_timer = None
        s._berserk_target = None
        if s._rules_node and s._rules_node.exists():
            s._rules_node.delete()
        super()._end_round()

class Sensei(
    Level,
    name=Strings.SENSEI_NAME,
    desc=Strings.SENSEI_DESC,
    tips=Strings.SENSEI_TIPS,
    include=['Football Stadium'],
    can_bomb=False,
    can_punch=False,
    can_jump=False,
    can_grab=False,
):
    SENSEI_X = -5.0
    PISSED_MAX = 100.0
    QUESTION_TIME = 10.0
    BAR_W = 420

    def __init__(s, settings):
        super().__init__(settings)
        s._sensei = None
        s._sensei_stream = None
        s._pissed = 0.0
        s._current_answer = None
        s._waiting = False
        s._answered = False
        s._question_timer = None
        s._tick_timer = None
        s._question_start = 0.0
        s._bar_bg = None
        s._bar_fg = None
        s._time_bar_bg = None
        s._time_bar_fg = None
        s._chat_last_len = 0
        s._chat_poll_timer = None
        s._player_streams = {}
        s._chasing = False

    def on_begin(s):
        super().on_begin()

        bs.setmusic(bs.MusicType.CHOSEN_ONE)

        s._sensei = MadBot(
            position=(s.SENSEI_X, 0, 0),
            color=(0.2, 0.4, 1.0),
            highlight=(0.1, 0.2, 0.8),
            character='Pixel',
        )
        s._sensei.node.name = 'Sensei'
        s._sensei.node.name_color = (0.4, 0.7, 1.0)
        s._sensei.bot.handlemessage(bs.StandMessage((s.SENSEI_X, 0, 0), 90))
        s._sensei_stream = Stream(s._sensei.node)

        s._chat_last_len = len(bs.get_chat_messages())
        s._chat_poll_timer = bs.Timer(0.3, bs.WeakCallStrict(s._poll_chat), repeat=True)

        s._bar_bg = bs.newnode('image', attrs={
            'texture': bs.gettexture('white'),
            'scale': (s.BAR_W, 18),
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
            'position': (-s.BAR_W / 2, -20),
        })
        bs.newnode('text', attrs={
            'v_attach': 'top',
            'h_attach': 'center',
            'h_align': 'center',
            'position': (0, -5),
            'scale': 0.6,
            'color': (1, 1, 1, 1),
            'text': Strings.SENSEI_PATIENCE,
            'flatness': 1.0,
            'shadow': 0.5,
        })

        s._time_bar_bg = bs.newnode('image', attrs={
            'texture': bs.gettexture('white'),
            'scale': (s.BAR_W, 12),
            'color': (0.05, 0.05, 0.15),
            'opacity': 0.85,
            'attach': 'topCenter',
            'position': (0, -105),
        })
        s._time_bar_fg = bs.newnode('image', attrs={
            'texture': bs.gettexture('white'),
            'scale': (s.BAR_W, 12),
            'color': (0.3, 0.6, 1.0),
            'opacity': 1.0,
            'attach': 'topCenter',
            'position': (0, -105),
        })

        for p in s.players:
            p.resetinput()

        s._position_players()
        bs.timer(3.0, bs.WeakCallStrict(s._next_question))

    def spawn_player(s, p):
        spaz = super().spawn_player(p)
        if p.actor and p.actor.node:
            s._player_streams[p] = Stream(p.actor.node)
        return spaz

    def _poll_chat(s):
        msgs = bs.get_chat_messages()
        new_count = len(msgs)
        if new_count <= s._chat_last_len:
            s._chat_last_len = new_count
            return
        new_msgs = msgs[s._chat_last_len:]
        s._chat_last_len = new_count

        for msg in new_msgs:
            parts = msg.split(': ', 1)
            if len(parts) < 2:
                continue
            sender_name = parts[0]
            text = parts[1].strip()

            for p in s.players:
                if p.getname() == sender_name:
                    stream = s._player_streams.get(p)
                    if stream:
                        stream.push(text, time=3.5)
                    break

            if not s._waiting or s._answered:
                continue

            try:
                val = int(text)
            except ValueError:
                continue

            player = None
            for p in s.players:
                if p.getname() == sender_name:
                    player = p
                    break

            s._answered = True
            s._waiting = False
            s._question_timer = None
            s._tick_timer = None
            s._update_time_bar(0.0)

            if val == s._current_answer:
                s._on_correct(player)
            else:
                s._on_wrong(player)
            return

    def _position_players(s):
        import math
        n = len(s.players)
        if not n: return
        cols = max(1, math.ceil(math.sqrt(n)))
        spacing = 1.8
        for i, p in enumerate(s.players):
            row = i // cols
            col = i % cols
            x = col * spacing - (cols - 1) * spacing / 2
            z = row * spacing - ((n - 1) // cols) * spacing / 2
            if p.actor and p.actor.node:
                p.actor.handlemessage(bs.StandMessage((x, 0, z), 270))

    def _next_question(s):
        import random as rnd
        ops = ['+', '-', '*']
        op = rnd.choice(ops)
        a = rnd.randint(1, 20)
        b = rnd.randint(1, 20)
        if op == '+':
            s._current_answer = a + b
            q = Strings.SENSEI_Q_ADD.format(a, b)
        elif op == '-':
            s._current_answer = a - b
            q = Strings.SENSEI_Q_SUB.format(a, b)
        else:
            b = rnd.randint(1, 10)
            s._current_answer = a * b
            q = Strings.SENSEI_Q_MUL.format(a, b)

        s._answered = False
        s._waiting = True
        s._question_start = bs.time()

        bs.timer(0.001, lambda: s._sensei_stream.push(q, time=s.QUESTION_TIME - 1))

        s._question_timer = bs.Timer(s.QUESTION_TIME, bs.WeakCallStrict(s._on_timeout))
        s._tick_timer = bs.Timer(1.0, bs.WeakCallStrict(s._tick), repeat=True)
        s._update_time_bar(1.0)

    def _tick(s):
        if not s._waiting: return
        elapsed = bs.time() - s._question_start
        ratio = max(0.0, 1.0 - elapsed / s.QUESTION_TIME)
        s._update_time_bar(ratio)
        bs.getsound('tick').play()

    def _update_time_bar(s, ratio):
        width = max(1.0, s.BAR_W * ratio)
        s._time_bar_fg.scale = (width, 12)
        s._time_bar_fg.position = (-s.BAR_W / 2 + width / 2, -105)
        s._time_bar_fg.color = (1.0 - ratio, ratio * 0.6, ratio)

    def _update_pissed_meter(s):
        ratio = s._pissed / s.PISSED_MAX
        width = max(1.0, s.BAR_W * ratio)
        s._bar_fg.scale = (width, 18)
        s._bar_fg.position = (-s.BAR_W / 2 + width / 2, -20)
        s._bar_fg.color = (ratio, 1.0 - ratio, 0.0)

    def _on_correct(s, player):
        s._pissed = max(0.0, s._pissed - 20.0)
        s._update_pissed_meter()
        bs.timer(0.001, lambda: s._sensei_stream.push(choice(Strings.SENSEI_CORRECT_MSGS), time=3))
        bs.timer(4.0, bs.WeakCallStrict(s._next_question))

    def _on_wrong(s, player):
        s._pissed = min(s.PISSED_MAX, s._pissed + 30.0)
        s._update_pissed_meter()
        bs.setmusic(None)

        kill_mode = s._pissed >= s.PISSED_MAX
        msgs = Strings.SENSEI_PISSED_KILL_MSGS if kill_mode else Strings.SENSEI_WRONG_MSGS
        bs.timer(0.001, lambda: s._sensei_stream.push(choice(msgs), time=4))

        if s._chasing or not player or not player.actor or not player.actor.node:
            bs.timer(3.0, lambda: bs.setmusic(bs.MusicType.CHOSEN_ONE))
            bs.timer(4.0, bs.WeakCallStrict(s._next_question))
            return

        s._chasing = True
        s._chase_player(player, kill=kill_mode)

    def _chase_player(s, player, kill=False):
        _self = ref(s)
        _p = ref(player)

        def _chase():
            self = _self()
            p = _p()
            if self is None or not self._sensei or not self._sensei.node.exists():
                return
            if not p or not p.actor or not p.actor.node or not p.actor.node.exists():
                self._after_punish()
                return
            sp = self._sensei.node.position
            pp = p.actor.node.position
            dx = pp[0] - sp[0]
            dz = pp[2] - sp[2]
            d = (dx**2 + dz**2) ** 0.5 or 1
            if d < 1.2:
                self._sensei.move(0, 0)
                self._sensei.on_run(0)
                if kill:
                    self._sensei.on(2)
                    self._sensei._start_combos()
                    def _finish_kill():
                        self2 = _self()
                        p2 = _p()
                        if self2 is None: return
                        self2._sensei._stop_combos()
                        if self2._sensei.node.hold_node:
                            self2._sensei.on(2)
                        if p2 and p2.actor and p2.actor.node and p2.actor.node.exists():
                            p2.actor.node.shattered = 2
                            p2.actor.handlemessage(bs.DieMessage())
                        self2._after_punish()
                    bs.timer(2.0, _finish_kill)
                else:
                    self._sensei.on(3)
                    bs.timer(0.8, lambda: self._after_punish())
                return
            self._sensei.on_run(0)
            bs.timer(0.02, lambda: self._sensei.on_run(1) or self._sensei.move(dx / d, -dz / d))
            bs.timer(0.05, _chase)

        bs.timer(1.5, _chase)

    def _after_punish(s):
        s._chasing = False
        s._sensei._stop_combos()
        if s._sensei.node.hold_node:
            s._sensei.on(2)
        s._sensei.move(0, 0)
        s._sensei.on_run(0)

        _self = ref(s)
        home = (s.SENSEI_X, 0, 0)

        def _go_home():
            self = _self()
            if self is None or not self._sensei or not self._sensei.node.exists(): return
            sp = self._sensei.node.position
            dx = home[0] - sp[0]
            dz = home[2] - sp[2]
            d = (dx**2 + dz**2) ** 0.5 or 1
            if d < 0.5:
                self._sensei.move(0, 0)
                self._sensei.on_run(0)
                self._sensei.bot.handlemessage(bs.StandMessage(home, 90))
                bs.timer(0.001, lambda: self._sensei_stream.push(choice(Strings.SENSEI_RESUME_MSGS), time=3))
                bs.timer(1.0, lambda: bs.setmusic(bs.MusicType.CHOSEN_ONE))
                bs.timer(3.0, bs.WeakCallStrict(self._next_question))
                return
            self._sensei.on_run(0)
            bs.timer(0.02, lambda: self._sensei.on_run(1) or self._sensei.move(dx / d, -dz / d))
            bs.timer(0.05, _go_home)

        bs.timer(0.5, _go_home)

    def _on_timeout(s):
        s._waiting = False
        s._answered = True
        s._tick_timer = None
        s._update_time_bar(0.0)
        bs.setmusic(None)
        bs.timer(0.001, lambda: s._sensei_stream.push(choice(Strings.SENSEI_TIMEOUT_MSGS), time=4))
        bs.timer(2.0, lambda: bs.setmusic(bs.MusicType.CHOSEN_ONE))
        bs.timer(4.0, bs.WeakCallStrict(s._next_question))

    def _end_round(s):
        s._chat_poll_timer = None
        s._question_timer = None
        s._tick_timer = None
        s._player_streams.clear()
        super()._end_round()

class Nest(
    Level,
    name=Strings.NEST_NAME,
    desc=Strings.NEST_DESC,
    tips=Strings.NEST_TIPS,
    include=['Football Stadium'],
    can_bomb=False,
):
    BASKET_POS    = (-7.0, 0.0, 0.0)
    BASKET_RADIUS = 1.6
    EGG_COUNT     = 5

    def __init__(s, settings):
        super().__init__(settings)
        s._bunny         = None
        s._bub           = None
        s._eggs          = []
        s._egg_slots     = []
        s._egg_home      = []
        s._egg_mat       = None
        s._pin_timer     = None
        s._idle_timer    = None
        s._target        = None
        s._target_egg    = -1
        s._egg_delegates = []
        s._bunny_orig_hm = None
        s._is_held = False

    def on_begin(s):
        super().on_begin()

        from math import cos, sin, pi
        for i in range(s.EGG_COUNT):
            a = (i / s.EGG_COUNT) * 2 * pi
            s._egg_slots.append((
                s.BASKET_POS[0] + cos(a) * 0.55,
                s.BASKET_POS[1] + 0.25,
                s.BASKET_POS[2] + sin(a) * 0.55,
            ))

        s._bunny = MadBot(
            position=s.BASKET_POS,
            color=(1.0, 0.2, 0.9),
            highlight=(1.0, 0.2, 0.8),
            character='Easter Bunny',
        )
        s._bunny.node.name = 'Bun-Bun'
        s._bunny.node.name_color = (1.0, 0.85, 0.9)
        s._bub = Stream(s._bunny.node)

        bunny_mats = s._bunny.node.materials
        s._egg_mat = bs.Material()
        for bm in bunny_mats:
            s._egg_mat.add_actions(
                conditions=('they_have_material', bm),
                actions=('modify_part_collision', 'collide', False),
            )

        s._spawn_eggs()

        s._bunny_orig_hm = s._bunny.bot.handlemessage
        _self = ref(s)

        def _bunny_hm(m):
            self = _self()
            if self is None: return
            if isinstance(m, bs.OutOfBoundsMessage):
                if self._bunny and self._bunny.node.exists():
                    self._bunny.node.handlemessage(bs.StandMessage(self.BASKET_POS))
                return
            if isinstance(m, bs.PickedUpMessage):
                self._is_held = True
                if not getattr(self._bunny, '_skill1_timer', None):
                    self._bunny._start_combos()
                if self._bunny_orig_hm:
                    self._bunny_orig_hm(m)
                return
            if isinstance(m, bs.DroppedMessage):
                self._is_held = False
                self._bunny._stop_combos()
                if self._bunny_orig_hm:
                    self._bunny_orig_hm(m)
                return
            if self._bunny_orig_hm:
                self._bunny_orig_hm(m)

        s._bunny.bot.handlemessage = _bunny_hm

        s._pin_timer  = bs.Timer(0.05, bs.WeakCallStrict(s._pin_eggs),   repeat=True)
        s._idle_timer = bs.Timer(9.0,  bs.WeakCallStrict(s._idle_speak), repeat=True)

        bs.timer(0.6, lambda: s._bub.push(Strings.NEST_HELLO, time=4))

        def _think():
            self = _self()
            if self is None or not self._bunny or not self._bunny.node.exists():
                return

            if self._target is not None:
                p = self._target
                if not p.actor or not p.actor.node or not p.actor.node.exists():
                    self._target = None
                    if getattr(self._bunny, '_grab_msg_sent', False):
                        self._bunny._grab_msg_sent = False
                    bs.timer(0.15, _think)
                    return

                bp   = self._bunny.node.position
                pp   = p.actor.node.position
                dx   = pp[0] - bp[0]
                dz   = pp[2] - bp[2]
                d    = (dx**2 + dz**2) ** 0.5
                held = self._bunny.node.hold_node

                if held == p.actor.node:
                    if not getattr(self._bunny, '_grab_msg_sent', False):
                        bs.timer(0.001, lambda: self._bub.push(choice(Strings.NEST_GRABBED), time=3))
                        self._bunny._grab_msg_sent = True

                    self._bunny._stop_combos()
                    self._bunny.move(0, 0)
                    self._bunny.on_run(0)

                    if self._near_basket(bp):
                        self._bunny.skill1()
                        bs.timer(0.001, lambda: self._bub.push(choice(Strings.NEST_THREW), time=3))
                        p.resetinput()

                        _pref = ref(p)
                        def _shatter():
                            p2 = _pref()
                            if p2 and p2.actor and p2.actor.node and p2.actor.node.exists():
                                p2.actor.node.shattered = 2
                                p2.actor.node.frozen = 1
                                p2.actor.node.move_up_down = 0
                                p2.actor.node.move_left_right = 0
                        bs.timer(0.2, _shatter)

                        def _die():
                            p2 = _pref()
                            if p2 and p2.actor and p2.actor.node and p2.actor.node.exists():
                                p2.actor.handlemessage(bs.DieMessage())
                        bs.timer(4.5, _die)

                        self._target = None
                        self._bunny._grab_msg_sent = False
                        bs.timer(0.5, _think)
                    else:
                        bx = self.BASKET_POS[0] - bp[0]
                        bz = self.BASKET_POS[2] - bp[2]
                        bd = (bx**2 + bz**2) ** 0.5 or 1
                        self._bunny.on_run(0)
                        bs.timer(0.02, lambda: self._bunny.on_run(1) or self._bunny.move(bx/bd, -bz/bd))
                        bs.timer(0.15, _think)
                    return

                if held and held != p.actor.node:
                    self._bunny._stop_combos()
                    self._bunny.on(2)
                    self._bunny.move(0, 0)
                    bs.timer(0.15, _think)
                    return

                self._bunny._stop_combos()

                if d < 1.35:
                    self._bunny.move(0, 0)
                    self._bunny.skill2()
                else:
                    vl = d or 1
                    self._bunny.on_run(0)
                    bs.timer(0.02, lambda: self._bunny.on_run(1) or self._bunny.move(dx/vl, -dz/vl))

                bs.timer(0.15, _think)

            else:
                stray = -1
                for i in range(self.EGG_COUNT):
                    if not self._egg_home[i] and self._player_holding_egg(i) is None and self._eggs[i].exists():
                        stray = i
                        break

                if stray == -1:
                    bp = self._bunny.node.position
                    bx = self.BASKET_POS[0] - bp[0]
                    bz = self.BASKET_POS[2] - bp[2]
                    bd = (bx**2 + bz**2) ** 0.5
                    if bd > 1.5:
                        self._bunny.on_run(0)
                        bs.timer(0.02, lambda: self._bunny.on_run(1) or self._bunny.move(bx/bd, -bz/bd))
                    else:
                        self._bunny.move(0, 0)
                        self._bunny.on_run(0)
                    if self._bunny.node.hold_node:
                        self._bunny.on(2)
                    bs.timer(0.5, _think)
                    return

                egg  = self._eggs[stray]
                bp   = self._bunny.node.position
                held = self._bunny.node.hold_node

                if held == egg:
                    self._bunny.move(0, 0)
                    self._bunny.on_run(0)
                    if self._near_basket(bp):
                        self._bunny.on(2)
                        self._egg_home[stray] = True
                        bs.timer(0.3, _think)
                    else:
                        bx = self.BASKET_POS[0] - bp[0]
                        bz = self.BASKET_POS[2] - bp[2]
                        bd = (bx**2 + bz**2) ** 0.5 or 1
                        self._bunny.on_run(0)
                        bs.timer(0.02, lambda: self._bunny.on_run(1) or self._bunny.move(bx/bd, -bz/bd))
                        bs.timer(0.15, _think)
                    return

                if held and held != egg:
                    self._bunny.on(2)
                    self._bunny.move(0, 0)
                    bs.timer(0.15, _think)
                    return

                ep = egg.position
                dx = ep[0] - bp[0]
                dz = ep[2] - bp[2]
                d  = (dx**2 + dz**2) ** 0.5

                if d < 1.0:
                    self._bunny.move(0, 0)
                    self._bunny.on_run(0)
                    bs.timer(0.001, lambda: self._bub.push(choice(Strings.NEST_RETURN), time=4))
                    self._bunny.on(2)
                    bs.timer(0.15, _think)
                else:
                    vl = d or 1
                    self._bunny.on_run(0)
                    bs.timer(0.02, lambda: self._bunny.on_run(1) or self._bunny.move(dx/vl, -dz/vl))
                    bs.timer(0.15, _think)

        bs.timer(1.0, _think)

    def _spawn_eggs(s):
        shared = bslib.gameutils.SharedObjects.get()
        mesh  = bs.getmesh('egg')
        texes = [bs.gettexture(f'eggTex{i+1}') for i in range(3)]

        class EggDelegate:
            def __init__(self, idx, activity):
                self.idx = idx
                self.activity = ref(activity)

            def handlemessage(self, m):
                if isinstance(m, bs.PickedUpMessage):
                    act = self.activity()
                    if act:
                        try:
                            spz = m.node.getdelegate(bslib.actor.spaz.Spaz)
                            if spz:
                                p = spz.getplayer(bs.Player, False)
                                if p:
                                    act._on_egg_stolen(p, self.idx)
                        except Exception:
                            pass

        for i in range(s.EGG_COUNT):
            delegate = EggDelegate(i, s)
            node = bs.newnode('prop', delegate=delegate, attrs={
                'mesh':             mesh,
                'color_texture':    texes[i % len(texes)],
                'body':             'capsule',
                'reflection':       'soft',
                'mesh_scale':       0.5,
                'body_scale':       0.6,
                'density':          4.0,
                'reflection_scale': [0.15],
                'shadow_size':      0.6,
                'position':         s._egg_slots[i],
                'materials':        [shared.object_material, s._egg_mat],
            })
            s._egg_delegates.append(delegate)
            s._eggs.append(node)
            s._egg_home.append(True)

    def _on_egg_stolen(s, player, egg_idx):
        s._egg_home[egg_idx] = False
        if s._target is None:
            s._target = player
            s._target_egg = egg_idx
            if s._bunny: s._bunny._grab_msg_sent = False
            bs.timer(0.001, lambda: s._bub.push(choice(Strings.NEST_SPOTTED), time=4))
        elif s._target is not player:
            if s._bunny and s._bunny.node.exists():
                if s._bunny.node.hold_node:
                    s._bunny.on(2)
                s._bunny._stop_combos()
                s._bunny.move(0, 0)
                s._bunny.on_run(0)
                s._bunny._grab_msg_sent = False
            s._target = player
            s._target_egg = egg_idx
            bs.timer(0.001, lambda: s._bub.push(choice(Strings.NEST_FORGAVE), time=3))

    def _pin_eggs(s):
        for i, node in enumerate(s._eggs):
            if not node.exists() or not s._egg_home[i]:
                continue
            node.position = s._egg_slots[i]
            node.velocity  = (0.0, 0.0, 0.0)

    def _player_holding_egg(s, egg_idx):
        egg = s._eggs[egg_idx]
        if not egg.exists():
            return None
        for p in s.players:
            if p.actor and p.actor.node and p.actor.node.exists():
                if p.actor.node.hold_node == egg:
                    return p
        return None

    def _near_basket(s, pos):
        dx = pos[0] - s.BASKET_POS[0]
        dz = pos[2] - s.BASKET_POS[2]
        return (dx*dx + dz*dz) ** 0.5 < s.BASKET_RADIUS

    def _idle_speak(s):
        if s._target is None:
            s._bub.push(choice(Strings.NEST_IDLE), time=4)

    def _end_round(s):
        if s._bunny and s._bunny_orig_hm:
            s._bunny.bot.handlemessage = s._bunny_orig_hm
        s._pin_timer     = None
        s._idle_timer    = None
        s._target        = None
        s._bunny_orig_hm = None
        super()._end_round()

class Zola(
    Level,
    name=Strings.ZOLA_NAME,
    desc=Strings.ZOLA_DESC,
    tips=Strings.ZOLA_TIPS,
    include=['Football Stadium', 'Hockey Stadium'],
    can_bomb=False,
    can_grab=False,
):
    def __init__(s, settings):
        super().__init__(settings)
        s._lucky = None
        s._bub = None
        s._hop_timer = None
        s._player_cooldowns = {}
        s._slot_timers = {}
        s._coins = []
        s._coin_delegates = []
        s._lucky_orig_hm = None
        s._rules_node = None

    def on_begin(s):
        super().on_begin()

        s._rules_node = bs.newnode('text', attrs={
            'text': Strings.ZOLA_RULES_TEXT,
            'v_attach': 'center',
            'h_attach': 'left',
            'h_align': 'left',
            'v_align': 'center',
            'position': (20, 0),
            'scale': 0.6,
            'color': (0.3, 1.0, 0.3, 0.85),
            'shadow': 1.0,
            'flatness': 1.0,
        })
        bs.animate(s._rules_node, 'opacity', {0: 0, 0.5: 1})

        class CoinDelegate:
            def __init__(self):
                self.node = None
            def handlemessage(self, m):
                if isinstance(m, bs.OutOfBoundsMessage):
                    if self.node and self.node.exists():
                        self.node.delete()

        shared = bslib.gameutils.SharedObjects.get()
        for _ in range(8):
            pos = (uniform(-8, 8), uniform(3, 7), uniform(-8, 8))
            delegate = CoinDelegate()
            coin = bs.newnode('prop', delegate=delegate, attrs={
                'mesh': bs.getmesh('puck'),
                'body': 'puck',
                'color_texture': bs.gettexture('tokens4'),
                'reflection': 'sharper',
                'reflection_scale': [5, 5, 5],
                'materials': [shared.object_material, shared.footing_material],
                'position': pos
            })
            delegate.node = coin
            s._coin_delegates.append(delegate)
            s._coins.append(coin)

        spawn = choice(s.spawn_points)
        s._lucky = MadBot(
            position=spawn,
            color=(0.1, 0.7, 0.1),
            highlight=(1.0, 0.5, 0.0),
            character='Zola', 
        )
        s._lucky.node.name = 'Lucky'
        s._lucky.node.name_color = (0.2, 1.0, 0.2)
        s._bub = Stream(s._lucky.node)

        s._lucky_orig_hm = s._lucky.bot.handlemessage
        _self = ref(s)

        def _lucky_hm(m):
            self = _self()
            if self is None: return

            if isinstance(m, bs.OutOfBoundsMessage):
                if self._lucky and self._lucky.node.exists():
                    self._lucky.node.handlemessage(bs.StandMessage(choice(self.spawn_points)))
                return

            if isinstance(m, bs.HitMessage):
                try:
                    src = m.get_source_player(bs.Player)
                    if src:
                        self._start_slot(src)
                except Exception:
                    pass
                if self._lucky_orig_hm: self._lucky_orig_hm(m)
                return

            if self._lucky_orig_hm:
                self._lucky_orig_hm(m)

        s._lucky.bot.handlemessage = _lucky_hm

        bs.timer(1.0, lambda: s._bub.push(Strings.ZOLA_HELLO, time=3))
        s._wander()

    def _wander(s):
        if not s._lucky or not s._lucky.node.exists():
            return

        target = (uniform(-8, 8), 0, uniform(-4, 4))
        s._lucky.move_to(target, time=2.0)

        if random() < 0.7:
            s._lucky.on(0)
            pos = s._lucky.node.position
            fx = uniform(-0.7, 0.7)
            fz = uniform(-0.7, 0.7)

            s._lucky.node.handlemessage(
                'impulse',
                pos[0], pos[1], pos[2],
                0, 0, 0,
                150.0, 150.0, 0, 1,
                fx, 1.2, fz
            )

        if random() < 0.2:
            s._bub.push(choice(Strings.ZOLA_IDLE), time=3)

        s._hop_timer = bs.Timer(uniform(0.4, 1.2), bs.WeakCallStrict(s._wander))

    def _start_slot(s, player):
        if not player.actor or not player.actor.node or not player.actor.node.exists():
            return

        now = bs.time()
        pos = player.actor.node.position

        if now < s._player_cooldowns.get(player, 0):
            bs.getsound('block').play(position=pos)
            return

        s._player_cooldowns[player] = now + 5.0
        bs.getsound('powerup01').play(position=pos)

        mnode = bs.newnode('math', owner=player.actor.node, attrs={
            'input1': (0, 1.8, 0),
            'operation': 'add'
        })
        player.actor.node.connectattr('torso_position', mnode, 'input2')

        tnode = bs.newnode('text', owner=player.actor.node, attrs={
            'in_world': True,
            'h_align': 'center',
            'scale': 0.0,
            'color': (1, 1, 0, 1),
            'text': '[ ? | ? | ? ]',
            'shadow': 1.0,
            'flatness': 1.0
        })
        mnode.connectattr('output', tnode, 'position')

        bs.animate(tnode, 'scale', {0: 0.0, 0.15: 0.02, 0.25: 0.015})

        r = random()
        if r < 0.10:   res_type = 'DEF'
        elif r < 0.20: res_type = 'GLV'
        elif r < 0.30: res_type = 'MED'
        elif r < 0.45: res_type = 'ICE'
        elif r < 0.60: res_type = 'ZZZ'
        elif r < 0.75: res_type = 'YET'
        elif r < 0.80: res_type = 'NUL'
        elif r < 0.85: res_type = 'CRS'
        elif r < 0.90: res_type = 'TNT'
        elif r < 0.95: res_type = 'ZAP'
        else:          res_type = 'RIP'

        state = {'ticks': 0, 'node': tnode, 'res': res_type, 'p': player}

        _self = ref(s)
        def _tick():
            self = _self()
            if not self or not state['node'].exists(): 
                return

            state['ticks'] += 1
            if state['ticks'] < 15:
                chars = ['@', '#', '$', '%', '&', '*', '!', '?']
                state['node'].text = f"[ {choice(chars)} | {choice(chars)} | {choice(chars)} ]"
                state['node'].color = (uniform(0.6,1), uniform(0.6,1), uniform(0.6,1))
            else:
                self._resolve_slot(state)

        timer = bs.Timer(0.1, _tick, repeat=True)
        s._slot_timers[player] = timer

    def _resolve_slot(s, state):
        p = state['p']
        tnode = state['node']
        res = state['res']

        if p in s._slot_timers:
            s._slot_timers.pop(p)

        if not tnode.exists(): return

        pos = p.actor.node.position if p.actor and p.actor.node.exists() else (0,0,0)

        if res == 'NUL':
            bs.getsound('error').play(position=pos)
        else:
            bs.getsound('cashRegister').play(position=pos)

        tnode.text = f"[ {res} | {res} | {res} ]"

        if res in ('RIP', 'ZAP', 'TNT', 'CRS'):
            tnode.color = (1.0, 0.2, 0.2)
            bs.animate(tnode, 'scale', {0: 0.015, 0.1: 0.03, 0.3: 0.02})
            s._bub.push(choice(Strings.ZOLA_JACKPOT), time=4)

            if res == 'RIP':
                _p = ref(p)
                def _shatter():
                    p2 = _p()
                    if p2 and p2.actor and p2.actor.node and p2.actor.node.exists():
                        p2.actor.node.shattered = 2
                        p2.actor.handlemessage(bs.DieMessage())
                bs.timer(0.4, _shatter)

            elif res == 'ZAP':
                _p = ref(p)
                def _smite():
                    p2 = _p()
                    if p2 and p2.actor and p2.actor.node and p2.actor.node.exists():
                        import bascenev1lib.actor.bomb as bomb
                        bomb.Blast(
                            position=p2.actor.node.position, 
                            blast_radius=3.0, 
                            blast_type='tnt'
                        ).autoretain()
                bs.timer(0.4, _smite)

            elif res == 'TNT':
                if p.actor and p.actor.node.exists():
                    import bascenev1lib.actor.bomb as bomb
                    for _ in range(3):
                        bomb.Bomb(
                            position=(pos[0] + uniform(-0.5, 0.5), pos[1] + 3.0, pos[2] + uniform(-0.5, 0.5)),
                            velocity=(0, -5, 0),
                            bomb_type='impact'
                        ).autoretain()

            elif res == 'CRS':
                if p.actor and p.actor.node.exists():
                    p.actor.curse()

        elif res in ('DEF', 'GLV', 'MED'):
            tnode.color = (0.2, 0.8, 1.0) if res != 'MED' else (0.2, 1.0, 0.2)
            bs.animate(tnode, 'scale', {0: 0.015, 0.1: 0.022, 0.3: 0.015})

            if p.actor and p.actor.node.exists():
                if res == 'DEF':
                    p.actor.equip_shields()
                elif res == 'GLV':
                    p.actor.equip_boxing_gloves()
                elif res == 'MED':
                    p.actor.hitpoints = p.actor.hitpoints_max
                    p.actor.node.hurt = 0.0
                    bs.getsound('healthPowerup').play(position=pos)
                    bs.emitfx(
                        position=pos,
                        velocity=(0, 2, 0),
                        count=15,
                        scale=1.5,
                        spread=0.3,
                        chunk_type='slime'
                    )

            if random() < 0.4:
                s._bub.push(choice(Strings.ZOLA_BLESSING), time=3)

        else:
            tnode.color = (0.8, 0.8, 1.0) if res != 'NUL' else (0.5, 0.5, 0.5)
            bs.animate(tnode, 'scale', {0: 0.015, 0.1: 0.022, 0.3: 0.015})

            if p.actor and p.actor.node.exists():
                if res == 'ICE':
                    p.actor.node.handlemessage(bs.FreezeMessage())
                elif res == 'ZZZ':
                    p.actor.node.handlemessage("knockout", 3000.0)
                elif res == 'YET':
                    p.actor.node.handlemessage(
                        'impulse',
                        pos[0], pos[1], pos[2],
                        0, 0, 0,
                        600.0, 600.0, 0, 1,
                        uniform(-0.8, 0.8), 1.2, uniform(-0.8, 0.8)
                    )
                elif res == 'NUL':
                    bs.emitfx(
                        position=(pos[0], pos[1] + 1.0, pos[2]),
                        velocity=(0, 1, 0),
                        count=10,
                        scale=0.5,
                        spread=0.2,
                        chunk_type='spark'
                    )

            if random() < 0.5 and res != 'NUL':
                s._bub.push(choice(Strings.ZOLA_TRICK), time=3)

        bs.animate(tnode, 'opacity', {1.5: 1.0, 2.0: 0.0})
        bs.timer(2.1, lambda: tnode.delete() if tnode.exists() else None)

    def _end_round(s):
        if s._lucky and s._lucky_orig_hm:
            s._lucky.bot.handlemessage = s._lucky_orig_hm
        s._hop_timer = None
        s._lucky_orig_hm = None
        s._player_cooldowns.clear()
        s._slot_timers.clear()

        if s._rules_node and s._rules_node.exists():
            s._rules_node.delete()
        s._rules_node = None

        s._coins.clear()
        s._coin_delegates.clear()
        super()._end_round()

class Debt(
    Level,
    name=Strings.DEBT_NAME,
    desc=Strings.DEBT_DESC,
    tips=Strings.DEBT_TIPS,
    include=['Football Stadium'],
    can_bomb=False,
):
    def __init__(s, settings):
        super().__init__(settings)
        s._balances = {}
        s._ui_nodes = {}
        s._player_streams = {}

        s._repo = None
        s._repo_stream = None
        s._repo_queue = []
        s._repo_target = None
        s._repo_busy = False
        s._repo_orig_hm = None

        s._zoe = None
        s._zoe_stream = None
        s._zoe_orig_hm = None

        s._boxes = []
        s._box_delegates = []

        s._tick_timer = None
        s._zoe_timer = None
        s._repo_timer = None

        s._zoe_cooldowns = {}
        s._repo_cooldowns = {}
        s._rules_node = None

    def _can_penalize(s, player, cooldown_dict, duration=1.5):
        now = bs.time()
        if now < cooldown_dict.get(player, 0):
            return False
        cooldown_dict[player] = now + duration
        return True

    def _is_caught(s, p):
        return s._repo_busy and s._repo_target == p

    def _is_node_held(s, target_node):
        if not target_node or not target_node.exists(): return False
        for p in s.players:
            if p.actor and p.actor.node and p.actor.node.exists():
                if p.actor.node.hold_node == target_node:
                    return True
        return False

    def on_begin(s):
        super().on_begin()

        s.DEBT_LIMIT = choice([-2000, -3000, -4000, -5000])
        s.PENALTY = choice(['Organ Harvesting', 'Orbital Strike', 'Spontaneous Combustion', 'Toxic Injection'])

        rules_text = Strings.DEBT_RULES_TEXT.format(s.DEBT_LIMIT, s.PENALTY)
        s._rules_node = bs.newnode('text', attrs={
            'text': rules_text,
            'v_attach': 'center', 'h_attach': 'left',
            'h_align': 'left', 'v_align': 'center',
            'position': (20, 0), 'scale': 0.7,
            'color': (1.0, 0.4, 0.4, 0.9),
            'shadow': 1.0, 'flatness': 1.0,
        })

        spawn_repo = choice(s.spawn_points)
        s._repo = MadBot(
            position=(spawn_repo[0], spawn_repo[1], spawn_repo[2] - 2),
            color=(0.05, 0.05, 0.05),
            highlight=(0.0, 0.0, 0.0),
            character='Agent Johnson', 
        )
        s._repo.node.name = 'Agent Repo'
        s._repo.node.name_color = (1.0, 0.1, 0.1)
        s._repo_stream = Stream(s._repo.node)

        s._repo_orig_hm = s._repo.bot.handlemessage
        _self = ref(s)
        def _repo_hm(m):
            self = _self()
            if self is None: return
            if isinstance(m, bs.OutOfBoundsMessage):
                if self._repo and self._repo.node.exists():
                    self._repo.node.handlemessage(bs.StandMessage(choice(self.spawn_points)))
                    self._repo._stop_combos()
                return
            if isinstance(m, bs.HitMessage):
                try:
                    src = m.get_source_player(bs.Player)
                    if src and not self._is_caught(src) and self._can_penalize(src, self._repo_cooldowns, 2.0):
                        self._add_debt(src, -400, Strings.DEBT_REASON_OBSTRUCTION)
                except Exception: pass

                if self._repo_orig_hm:
                    self._repo_orig_hm(bs.HitMessage(
                        pos=self._repo.node.position if self._repo and self._repo.node.exists() else m.pos,
                        velocity=(0, 0, 0),
                        magnitude=0.001,
                        hit_type=m.hit_type,
                        source_player=None
                    ))
                return
            if isinstance(m, bs.PickedUpMessage):
                try:
                    spz = m.node.getdelegate(bslib.actor.spaz.Spaz)
                    p = spz.getplayer(bs.Player, False) if spz else None
                    if p and not self._is_caught(p) and self._can_penalize(p, self._repo_cooldowns, 2.0):
                        self._add_debt(p, -500, Strings.DEBT_REASON_OBSTRUCTION)
                except Exception: pass

                if self._repo and not getattr(self._repo, '_skill1_timer', None):
                    self._repo._start_combos()
                if self._repo_orig_hm:
                    self._repo_orig_hm(m)
                return
            if isinstance(m, bs.DroppedMessage):
                if self._repo and not self._repo_busy:
                    self._repo._stop_combos()
                if self._repo_orig_hm:
                    self._repo_orig_hm(m)
                return
            if self._repo_orig_hm:
                self._repo_orig_hm(m)
        s._repo.bot.handlemessage = _repo_hm

        spawn_zoe = choice(s.spawn_points)
        s._zoe = MadBot(
            position=(spawn_zoe[0], spawn_zoe[1], spawn_zoe[2] + 2),
            color=(1.0, 0.5, 0.6),
            highlight=(1.0, 0.3, 0.4),
            character='Zoe', 
        )
        s._zoe.node.name = 'Zoe'
        s._zoe.node.name_color = (1.0, 0.6, 0.7)
        s._zoe_stream = Stream(s._zoe.node)

        s._zoe_orig_hm = s._zoe.bot.handlemessage
        def _zoe_hm(m):
            self = _self()
            if self is None: return
            if isinstance(m, bs.OutOfBoundsMessage):
                if self._zoe and self._zoe.node.exists():
                    self._zoe.node.handlemessage(bs.StandMessage(choice(self.spawn_points)))
                    self._zoe._stop_combos()
                return
            if isinstance(m, bs.HitMessage):
                try:
                    src = m.get_source_player(bs.Player)
                    if src and not self._is_caught(src) and self._can_penalize(src, self._zoe_cooldowns, 2.0): 
                        self._add_debt(src, -300, Strings.DEBT_REASON_ASSAULT)
                        self._zoe_stream.push(choice(Strings.DEBT_ZOE_SUE))
                        if self._zoe and self._zoe.node.exists():
                            self._zoe.move_to((uniform(-7, 7), 0, uniform(-4, 4)), time=1.5)
                except Exception: pass
                if self._zoe_orig_hm:
                    self._zoe_orig_hm(bs.HitMessage(
                        pos=self._zoe.node.position if self._zoe and self._zoe.node.exists() else m.pos,
                        velocity=(0, 0, 0),
                        magnitude=0.001,
                        hit_type=m.hit_type,
                        source_player=None
                    ))
                return
            if isinstance(m, bs.PickedUpMessage):
                try:
                    spz = m.node.getdelegate(bslib.actor.spaz.Spaz)
                    p = spz.getplayer(bs.Player, False) if spz else None
                    if p and not self._is_caught(p) and self._can_penalize(p, self._zoe_cooldowns, 2.0):
                        self._add_debt(p, -500, Strings.DEBT_REASON_KIDNAPPING)
                        self._zoe_stream.push(choice(Strings.DEBT_ZOE_SUE))
                except Exception: pass

                if self._zoe and not getattr(self._zoe, '_skill1_timer', None):
                    self._zoe._start_combos()
                if self._zoe_orig_hm:
                    self._zoe_orig_hm(m)
                return
            if isinstance(m, bs.DroppedMessage):
                if self._zoe:
                    self._zoe._stop_combos()
                if self._zoe_orig_hm:
                    self._zoe_orig_hm(m)
                return
            if self._zoe_orig_hm:
                self._zoe_orig_hm(m)
        s._zoe.bot.handlemessage = _zoe_hm

        class BoxDelegate:
            def __init__(self, lvl_ref):
                self.lvl = lvl_ref
                self.busy = False
                self.node = None
                self.fee = 500
                self.win_amt = 1500
            def handlemessage(self, m):
                if isinstance(m, bs.PickedUpMessage):
                    if self.busy: return
                    try:
                        spz = m.node.getdelegate(bslib.actor.spaz.Spaz)
                        if spz:
                            p = spz.getplayer(bs.Player, False)
                            l = self.lvl()
                            if l and p: l._on_box_grabbed(self, p)
                    except Exception: pass
                elif isinstance(m, bs.OutOfBoundsMessage):
                    if self.node and self.node.exists():
                        self.node.position = (uniform(-5, 5), 5, uniform(-3, 3))
                        self.node.velocity = (0, 0, 0)

        for _ in range(3):
            pos = (uniform(-6, 6), 3, uniform(-4, 4))
            delegate = BoxDelegate(_self)

            fee = choice([100, 250, 500, 750, 1000])
            win_amt = fee * choice([2, 3, 4, 5])
            delegate.fee = fee
            delegate.win_amt = win_amt

            box = bs.newnode('prop', delegate=delegate, attrs={
                'mesh': bs.getmesh('tnt'),
                'body': 'crate',
                'color_texture': bs.gettexture('tokens4'),
                'reflection': 'soft',
                'reflection_scale': [0.5],
                'shadow_size': 0.5,
                'position': pos,
                'materials': [bslib.gameutils.SharedObjects.get().object_material]
            })
            delegate.node = box
            s._box_delegates.append(delegate)
            s._boxes.append(box)

            b_mnode = bs.newnode('math', owner=box, attrs={'input1': (0, 0.7, 0), 'operation': 'add'})
            box.connectattr('position', b_mnode, 'input2')
            b_tnode = bs.newnode('text', owner=box, attrs={
                'in_world': True, 'h_align': 'center', 'scale': 0.012,
                'color': (1.0, 0.8, 0.2), 'text': Strings.DEBT_GAMBLE.format(fee),
                'shadow': 1.0, 'flatness': 1.0
            })
            b_mnode.connectattr('output', b_tnode, 'position')

        s._tick_timer = bs.Timer(0.1, bs.WeakCallStrict(s._tick), repeat=True)
        s._zoe_timer = bs.Timer(0.15, bs.WeakCallStrict(s._zoe_tick), repeat=True)
        s._repo_timer = bs.Timer(0.15, bs.WeakCallStrict(s._repo_tick), repeat=True)
        bs.timer(1.0, lambda: s._repo_stream.push(Strings.DEBT_REPO_SPAWN, time=3))

    def spawn_player(s, p):
        spaz = super().spawn_player(p)
        s._balances[p] = 0
        s._player_streams[p] = Stream(spaz.node)

        mnode = bs.newnode('math', owner=spaz.node, attrs={'input1': (0, -0.6, 0), 'operation': 'add'})
        spaz.node.connectattr('position', mnode, 'input2')
        tnode = bs.newnode('text', owner=spaz.node, attrs={
            'in_world': True, 'h_align': 'center', 'scale': 0.015,
            'color': (0.3, 1.0, 0.3), 'text': '$0', 'shadow': 1.0, 'flatness': 1.0
        })
        mnode.connectattr('output', tnode, 'position')
        s._ui_nodes[p] = tnode

        _self = ref(s)
        _p = ref(p)
        def _hm(m):
            if isinstance(m, bs.HitMessage):
                try:
                    src = m.get_source_player(bs.Player)
                    self = _self()
                    player = _p()
                    if self and src and player and src != player:
                        if not self._is_caught(src) and not self._is_caught(player):
                            self._add_debt(src, -300, Strings.DEBT_REASON_ASSAULT)
                            self._add_debt(player, 300, Strings.DEBT_REASON_SETTLEMENT)
                except Exception: pass
            spz = _p()
            if spz and spz.actor: bslib.actor.playerspaz.PlayerSpaz.handlemessage(spz.actor, m)
        spaz.handlemessage = _hm
        return spaz

    def _add_debt(s, p, amount, reason):
        if p not in s._balances: return
        if p in s._repo_queue or p == s._repo_target: return

        s._balances[p] += amount
        bal = s._balances[p]

        if p in s._ui_nodes and s._ui_nodes[p].exists():
            node = s._ui_nodes[p]
            node.text = f"${bal}"
            node.color = (0.3, 1.0, 0.3) if bal >= 0 else (1.0, 0.3, 0.3)

        sign = "" if amount < 0 else "+"
        if p in s._player_streams:
            s._player_streams[p].push(f"{reason}\n{sign}${abs(amount)}", time=2.0)

        if bal <= s.DEBT_LIMIT:
            s._repo_queue.append(p)
            s._repo_stream.push(Strings.DEBT_REPO_QUEUE.format(p.getname()))

    def _tick(s):
        for p in s.players:
            if s._is_caught(p): continue

            if p.actor and p.actor.node and p.actor.node.exists():
                hurt = p.actor.node.hurt
                if hurt > 0.05:
                    bill = int(hurt * 1500)
                    p.actor.node.hurt = 0.0
                    p.actor.hitpoints = p.actor.hitpoints_max
                    s._add_debt(p, -bill, Strings.DEBT_REASON_MEDICAL)
                    bs.emitfx(position=p.actor.node.position, chunk_type='slime', count=10)
                    bs.getsound('healthPowerup').play(position=p.actor.node.position)

    def _zoe_tick(s):
        if not s._zoe or not s._zoe.node.exists(): return

        if getattr(s._zoe, '_skill1_timer', None):
            if not s._is_node_held(s._zoe.node):
                s._zoe._stop_combos()

        if s._zoe.node.hold_node:
            s._zoe.node.hold_node = None

        zp = s._zoe.node.position

        if s._repo and s._repo.node.exists():
            rp = s._repo.node.position
            dx = zp[0] - rp[0]
            dz = zp[2] - rp[2]
            dist = (dx**2 + dz**2) ** 0.5
            if dist < 3.0:
                s._zoe.on_run(0)
                bs.timer(0.02, lambda: s._zoe.on_run(1) or s._zoe.move(dx/dist, -dz/dist))
                return

        if s._repo_target and s._repo_target.actor and s._repo_target.actor.node.exists():
            tp = s._repo_target.actor.node.position
            dx = zp[0] - tp[0]
            dz = zp[2] - tp[2]
            dist = (dx**2 + dz**2) ** 0.5
            if dist < 4.5:
                s._zoe.on_run(0)
                bs.timer(0.02, lambda: s._zoe.on_run(1) or s._zoe.move(dx/dist, -dz/dist))
                return

        for p in s.players:
            if s._is_caught(p): continue

            if p.actor and p.actor.node and p.actor.node.exists():
                pp = p.actor.node.position
                dx = zp[0] - pp[0]
                dz = zp[2] - pp[2]
                d = (dx**2 + dz**2) ** 0.5
                if d < 0.5 and s._can_penalize(p, s._zoe_cooldowns, 2.0):
                    s._add_debt(p, -50, Strings.DEBT_REASON_RESTRAINING)
                    s._zoe_stream.push(choice(Strings.DEBT_ZOE_SUE))

                    s._zoe.on_run(0)
                    bs.timer(0.02, lambda: s._zoe.on_run(1) or s._zoe.move(dx/d, -dz/d))

                    _self = ref(s)
                    def _stop():
                        self = _self()
                        if self and self._zoe and self._zoe.node.exists():
                            self._zoe.move(0,0)
                            self._zoe.on_run(0)
                    bs.timer(0.8, _stop)
                    return

        if random() < 0.05:
            s._zoe.move_to((uniform(-7, 7), 0, uniform(-4, 4)), time=1.5)

    def _repo_tick(s):
        if not s._repo or not s._repo.node.exists(): return

        if getattr(s._repo, '_skill1_timer', None) and not s._repo_busy:
            if not s._is_node_held(s._repo.node):
                s._repo._stop_combos()
            if s._repo.node.hold_node:
                s._repo.node.hold_node = None

        if s._repo_target and (not s._repo_target.actor or not s._repo_target.actor.node.exists()):
            s._repo_target = None
            s._repo_busy = False
            if s._repo.node.hold_node:
                s._repo.node.hold_node = None
            s._repo._stop_combos()

        if s._repo_busy: 
            return

        if not s._repo_target:
            if s._repo_queue:
                s._repo_target = s._repo_queue.pop(0)
                s._repo_stream.push(Strings.DEBT_REPO_TARGET.format(s._repo_target.getname()))
            else:
                rp = s._repo.node.position

                if s._zoe and s._zoe.node.exists():
                    zp = s._zoe.node.position
                    dx = rp[0] - zp[0]
                    dz = rp[2] - zp[2]
                    dist = (dx**2 + dz**2) ** 0.5
                    if dist < 3.0:
                        s._repo.on_run(0)
                        bs.timer(0.02, lambda: s._repo.on_run(1) or s._repo.move(dx/dist, -dz/dist))
                        return

                if random() < 0.05:
                    s._repo.move_to((uniform(-7, 7), 0, uniform(-4, 4)), time=1.5)
                if s._repo.node.hold_node:
                    s._repo.node.hold_node = None
                return

        p = s._repo_target
        rp = s._repo.node.position
        pp = p.actor.node.position
        dx = pp[0] - rp[0]
        dz = pp[2] - rp[2]
        d = (dx**2 + dz**2) ** 0.5 or 1

        held = s._repo.node.hold_node
        if held == p.actor.node:
            s._repo_busy = True
            s._repo.move(0,0)
            s._repo.on_run(0)
            p.resetinput()
            s._repo_stream.push(choice(Strings.DEBT_REPO_ARREST))

            if s.PENALTY == 'Organ Harvesting':
                s._repo._start_combos()
                p.actor.node.shattered = 2
            elif s.PENALTY == 'Orbital Strike':
                import bascenev1lib.actor.bomb as bomb
                bomb.Blast(position=pp, blast_radius=4.0, blast_type='tnt').autoretain()
            elif s.PENALTY == 'Spontaneous Combustion':
                bs.getsound('explosion01').play(position=pp)
                bs.emitfx(position=pp, chunk_type='spark', count=50, spread=1.0)
                bs.emitfx(position=pp, chunk_type='splinter', count=20, spread=1.0)
            elif s.PENALTY == 'Toxic Injection':
                bs.emitfx(position=pp, chunk_type='slime', count=40, spread=1.0)
                p.actor.node.color = (0.2, 1.0, 0.2)

            _p = ref(p)
            _self = ref(s)
            def _die():
                self = _self()
                p2 = _p()
                if p2 and p2.actor and p2.actor.node.exists():
                    p2.actor.handlemessage(bs.DieMessage())
                if self:
                    if self._repo and self._repo.node.exists():
                        self._repo._stop_combos()
                        self._repo.node.hold_node = None
                    self._repo_target = None
                    self._repo_busy = False
            bs.timer(1.5, _die)
            return

        if held and held != p.actor.node:
            s._repo.node.hold_node = None

        if d < 1.2:
            s._repo.move(0,0)
            s._repo.on_run(0)
            s._repo.on(3)
            s._repo.on(2)
        else:
            s._repo.on_run(0)
            bs.timer(0.02, lambda: s._repo.on_run(1) or s._repo.move(dx/d, -dz/d))

    def _on_box_grabbed(s, delegate, p):
        if s._is_caught(p): return
        box = delegate.node
        if not box or not box.exists(): return

        delegate.busy = True
        fee = getattr(delegate, 'fee', 500)
        win_amt = getattr(delegate, 'win_amt', 1500)

        s._add_debt(p, -fee, Strings.DEBT_REASON_GAMBLE)

        if p.actor and p.actor.node.exists():
            p.actor.node.hold_node = None

        box.gravity_scale = 0.0
        box.velocity = (0, 3, 0)

        def _halt():
            if box.exists(): box.velocity = (0, 0, 0)
        bs.timer(0.3, _halt)

        def _result():
            if not box.exists(): return
            pos = box.position
            if random() < 0.5:
                s._add_debt(p, win_amt, Strings.DEBT_REASON_JACKPOT)
                bs.getsound('cashRegister').play(position=pos)
                bs.emitfx(position=pos, chunk_type='spark', count=20)
            else:
                bs.getsound('error').play(position=pos)
                bs.emitfx(position=pos, chunk_type='sweat', count=10)

            box.gravity_scale = 1.0
            box.velocity = (0, -0.1, 0)
            box.handlemessage(bs.HitMessage(
                pos=pos, velocity=(0,-1,0), magnitude=0.1, hit_type='punch', source_player=None
            ))
            delegate.busy = False
        bs.timer(1.5, _result)

    def _end_round(s):
        if s._repo and s._repo_orig_hm:
            s._repo.bot.handlemessage = s._repo_orig_hm
        if s._zoe and s._zoe_orig_hm:
            s._zoe.bot.handlemessage = s._zoe_orig_hm
        s._tick_timer = None
        s._zoe_timer = None
        s._repo_timer = None
        s._repo_orig_hm = None
        s._zoe_orig_hm = None

        if s._rules_node and s._rules_node.exists():
            s._rules_node.delete()

        s._balances.clear()
        s._ui_nodes.clear()
        s._player_streams.clear()
        s._zoe_cooldowns.clear()
        s._repo_cooldowns.clear()

        for box in s._boxes:
            if box.exists(): box.delete()
        s._boxes.clear()
        s._box_delegates.clear()

        super()._end_round()

class PsychoPixie(
    Level,
    name=Strings.PIXIE_NAME,
    desc=Strings.PIXIE_DESC,
    tips=Strings.PIXIE_TIPS,
    include=['Doom Shroom', 'Football Stadium'],
    can_bomb=False,
):
    def __init__(s, settings):
        super().__init__(settings)
        s._bot = PsychoBot()
        s._pixie = None
        s._pixie_orig_hm = None
        s._chat_last_len = 0
        s._chat_poll_timer = None
        s._idle_timer = None
        s._ui_nodes = {}
        s._chasing = False
        s._target = None
        s._task_id = 0
        s._last_chat_time = 0.0

    def on_begin(s):
        super().on_begin()

        s._last_chat_time = bs.time()
        spawn = choice(s.spawn_points)
        s._pixie = MadBot(
            position=(spawn[0], spawn[1] + 1.0, spawn[2]),
            color=(1.0, 0.9, 0.2),
            highlight=(1.0, 1.0, 0.0),
            character='Pixel',
        )
        s._pixie.node.name = 'Pixie'
        s._pixie.node.name_color = (1.0, 1.0, 0.2)

        s._pixie_orig_hm = s._pixie.bot.handlemessage
        _self = ref(s)
        def _pixie_hm(m):
            self = _self()
            if self is None: return
            if isinstance(m, bs.OutOfBoundsMessage):
                if self._pixie and self._pixie.node.exists():
                    self._pixie.node.handlemessage(bs.StandMessage(choice(self.spawn_points)))
                return
            if self._pixie_orig_hm:
                self._pixie_orig_hm(m)
        s._pixie.bot.handlemessage = _pixie_hm

        s._chat_last_len = len(bs.get_chat_messages())
        s._chat_poll_timer = bs.Timer(0.3, bs.WeakCallStrict(s._poll_chat), repeat=True)
        s._idle_timer = bs.Timer(1.0, bs.WeakCallStrict(s._check_idle), repeat=True)

        bs.timer(1.0, lambda: Bubble(s._pixie.node, Strings.PIXIE_HELLO, color=(1.0, 1.0, 0.2), time=4))

    def spawn_player(s, p):
        spaz = super().spawn_player(p)

        mnode = bs.newnode('math', owner=spaz.node, attrs={'input1': (0, -0.6, 0), 'operation': 'add'})
        spaz.node.connectattr('position', mnode, 'input2')
        tnode = bs.newnode('text', owner=spaz.node, attrs={
            'in_world': True, 'h_align': 'center', 'scale': 0.015,
            'color': (0.8, 0.8, 0.8), 'text': Strings.PIXIE_REP.format(0), 'shadow': 1.0, 'flatness': 1.0
        })
        mnode.connectattr('output', tnode, 'position')
        s._ui_nodes[p] = tnode

        _self = ref(s)
        _p = ref(p)
        def _hm(m):
            if isinstance(m, bs.OutOfBoundsMessage):
                self = _self()
                player = _p()
                if self and player and player.actor and player.actor.node.exists():
                    player.actor.node.handlemessage(bs.StandMessage(choice(self.spawn_points)))
                    bs.getsound('shieldDown').play(position=player.actor.node.position)
                return
            player = _p()
            if player and player.actor: bslib.actor.playerspaz.PlayerSpaz.handlemessage(player.actor, m)
        spaz.handlemessage = _hm

        s._bot.chat(p.getname(), "")
        return spaz

    def _poll_chat(s):
        msgs = bs.get_chat_messages()
        new_count = len(msgs)
        if new_count <= s._chat_last_len: return

        new_msgs = msgs[s._chat_last_len:]
        s._chat_last_len = new_count

        for msg in new_msgs:
            parts = msg.split(': ', 1)
            if len(parts) < 2: continue
            sender_name, text = parts[0], parts[1].strip()

            player = None
            for p in s.players:
                if p.getname() == sender_name:
                    player = p
                    break

            if player and player.actor and player.actor.node.exists():
                Bubble(player.actor.node, text, color=(1, 1, 1), time=3.5)

                if s._chasing: continue

                reply = s._bot.chat(sender_name, text)
                score = s._bot.M[sender_name]['s']

                if player in s._ui_nodes and s._ui_nodes[player].exists():
                    s._ui_nodes[player].text = Strings.PIXIE_REP.format(score)
                    s._ui_nodes[player].color = (0.3, 1.0, 0.3) if score >= 0 else (1.0, 0.3, 0.3)

                s._task_id += 1
                s._last_chat_time = bs.time()

                if reply == "!KILL!":
                    Bubble(s._pixie.node, Strings.PIXIE_ANGRY, color=(1.0, 0.2, 0.2), time=4)
                    s._pixie.node.color = (0.1, 0.1, 0.1)
                    s._pixie.node.highlight = (0.8, 0.0, 0.0)
                    bs.getsound('orchestraHit4').play()
                    s._chase(player)
                else:
                    bs.getsound('pop01').play()
                    s._go_to_and_reply(player, reply, score, s._task_id)

    def _go_to_and_reply(s, player, reply, score, tid):
        if s._task_id != tid or s._chasing: return
        if not s._pixie or not s._pixie.node.exists(): return

        if not player or not player.actor or not player.actor.node.exists():
            Bubble(s._pixie.node, reply, color=(1.0, 1.0, 0.2), time=4)
            return

        p = s._pixie.node.position
        t = player.actor.node.position
        dx, dz = t[0]-p[0], t[2]-p[2]
        d = (dx**2 + dz**2)**0.5 or 1

        if d < 1.5:
            s._pixie.move(0, 0)
            s._pixie.on_run(0)

            Bubble(s._pixie.node, reply, color=(1.0, 1.0, 0.2), time=4)

            _p = ref(player)
            def _jump_and_act():
                if s._task_id != tid or s._chasing: return
                if s._pixie and s._pixie.node.exists():
                    s._pixie.on(0)
                    p2 = _p()
                    if p2: s._apply_milestones(p2, score)

            bs.timer(0.2, _jump_and_act)
        else:
            s._pixie.on_run(0)
            bs.timer(0.02, lambda: s._pixie.on_run(1) or s._pixie.move(dx/d, -dz/d))
            _p = ref(player) 
            bs.timer(0.1, lambda: (p2 := _p()) and s._go_to_and_reply(p2, reply, score, tid))

    def _apply_milestones(s, p, score):
        if score >= 50 and random() < 0.3:
            if p.actor and p.actor.node.exists():
                p.actor.hitpoints = p.actor.hitpoints_max
                p.actor.node.hurt = 0.0
                bs.emitfx(position=p.actor.node.position, chunk_type='slime', count=15)
                bs.getsound('healthPowerup').play(position=p.actor.node.position)
                Bubble(s._pixie.node, choice(Strings.PIXIE_BLESS), time=3, color=(0.2, 1.0, 0.2))

        elif score <= -50 and random() < 0.3:
            if p.actor and p.actor.node.exists():
                p.actor.node.handlemessage(bs.FreezeMessage())
                Bubble(s._pixie.node, choice(Strings.PIXIE_CURSE), time=3, color=(0.2, 0.8, 1.0))

    def _check_idle(s):
        if s._chasing: return
        if bs.time() - s._last_chat_time > 5.0:
            s._last_chat_time = bs.time()
            s._task_id += 1
            s._pixie_target_pos = choice(s.spawn_points)
            s._do_idle_walk(s._task_id)

    def _do_idle_walk(s, tid):
        if s._task_id != tid or s._chasing: return
        if not s._pixie or not s._pixie.node.exists(): return

        p = s._pixie.node.position
        t = s._pixie_target_pos
        dx, dz = t[0]-p[0], t[2]-p[2]
        d = (dx**2 + dz**2)**0.5 or 1

        if d < 1.0:
            s._pixie.move(0, 0)
            s._pixie.on_run(0)
            
            if random() < 0.4:
                s._pixie.node.handlemessage('celebrate', int(uniform(500, 1500)))
            elif random() < 0.4:
                s._pixie.move(1, 0)
                bs.timer(0.4, lambda: s._pixie and s._pixie.node.exists() and s._pixie.move(0, 0))

            if random() < 0.3:
                Bubble(s._pixie.node, choice(Strings.PIXIE_IDLE_LINES), time=3, color=(1.0, 1.0, 0.5))
            return

        s._pixie.on_run(0)
        bs.timer(0.02, lambda: s._pixie.on_run(1) or s._pixie.move(dx/d, -dz/d))
        bs.timer(0.1, lambda: s._do_idle_walk(tid))

    def _chase(s, player):
        s._chasing = True
        s._target = player
        _self = ref(s)
        _p = ref(player)

        def _think():
            self = _self()
            p = _p()
            if self is None or not self._pixie or not self._pixie.node.exists(): return
            if not p or not p.actor or not p.actor.node or not p.actor.node.exists():
                self._chasing = False
                self._target = None
                self._pixie.node.color = (1.0, 0.9, 0.2)
                self._pixie.node.highlight = (1.0, 1.0, 0.0)
                return

            px = self._pixie.node.position
            tx = p.actor.node.position
            dx = tx[0] - px[0]
            dz = tx[2] - px[2]
            d = (dx**2 + dz**2) ** 0.5 or 1

            if d < 1.2:
                self._pixie.move(0, 0)
                self._pixie.on_run(0)
                self._pixie.on(2)
                self._pixie._start_combos()
                bs.timer(1.2, lambda: setattr(p.actor.node, 'shattered', 2))
                bs.timer(1.3, lambda: p.actor.handlemessage(bs.DieMessage()))

                def _calm_down():
                    if self and self._pixie and self._pixie.node.exists():
                        self._pixie._stop_combos()
                        self._pixie.node.color = (1.0, 0.9, 0.2)
                        self._pixie.node.highlight = (1.0, 1.0, 0.0)
                        Bubble(self._pixie.node, Strings.PIXIE_CALM, color=(1.0, 1.0, 0.2), time=3)
                    if self:
                        self._chasing = False
                        self._target = None
                bs.timer(2.0, _calm_down)
                return

            self._pixie.on_run(0)
            bs.timer(0.02, lambda: self._pixie.on_run(1) or self._pixie.move(dx/d, -dz/d))
            bs.timer(0.05, _think)

        bs.timer(1.0, _think)

    def _end_round(s):
        if s._pixie and s._pixie_orig_hm:
            s._pixie.bot.handlemessage = s._pixie_orig_hm
        s._chat_poll_timer = None
        s._idle_timer = None
        s._ui_nodes.clear()

        s._pixie_orig_hm = None
        s._target = None

        super()._end_round()

# extra tools
# globally used by games

D=lambda x:decode(x,'rot13')

class PsychoBot:
    def __init__(s):
        s.M={}
        s.W={k:set(D(v).split()) for k,v in {'h':"fghcvq vqvbg qhzv ungr genfu hfryrff qvr xvyy htyl fuhg shpx ovgpu penc fhpx njshy jbefg pevatr fgsh zvq ynzr of jnpx pybja gbkvp nff fuvg naabl znq grevoyr ubevoyr tebff rj hut xlf ybfre wrex zbeba obmb jrveqb engvb spx fuhghc fgvaxf tneontr xzf xvyylbhefrys qhzonff zs zsf fgcvq vqbg fva qrzba rivy fzvgr uryy cvgpusbex qvegl qnex",'f':"ybir fzneg tbbq terng njrfbzr pbby sevraq fbeel cyrnfr gunax avpr fjrrg orfg yby yznb onfrq cbt fvpx qbcr lnl unun urur tbng fynl org nvtug puvyy ivor rcvp sha phgr tynq unccl j qho gl guk nznmvat ornhgvshy fcnex fvtzn pnyz erynk ncbybtvmr zlb zo jf vyl vyl2 onfrq inyvq natry unyb jvatf srngure yvtug lryybj fuvar ubyl urnira cher tybj",'i':"jub jung jul ubj jurer jura yber frperg checbfr rkcynva anzr uhu jqlz fcvyy grn se fefyl pnc ernyyl thrff jlq jlz jln uz uzz uzzz zrnavat fbhepr fnhpr gs urnira",'g':"uv uryyb url lb zbeavat riravat fhc jnffhc urln tz ta ubjql ubyn jft terrgvatf lbb lbbb nubl fcnex",'l':"olr dhvg rkvg yrnir pln crnpr oeo ttg yngre nqvbf avtug tbbqavtug syl njnl",'c':"oehu beb qhqr zna tvey obl thl pung fzu gou vzb vqp vqx lrnu lrn lrc anu ab bx x bxnl fher jungrire fghss guvat jbex fpubby fyrrc rng sbbq tnzr cynl jngpu zhfvp zbivr oberq oyhq qnjt ubzvr tnat lnyy bat sesf n h he lbh lbhe vz v zr zl jr hf ea evtug abj whfg yvxr yvgrenyyl npghnyyl fxl pybhq syhss"}.items()}
        s.G={k:{t:[D(i) for i in v] for t,v in e.items()} for k,e in {'f':{'<g>':["urlil {h} *syhgeref lryybj jvatf*","uv fhafuvar {h}!","lb {h} *nqwhfgf unyb*","fcnexvatf {h}!"],'<s>':["whfg cerravat zl tbyqra srnguref","ivovat ba n pybhq","cbyvfuvat zl unyb ea","srryvat fb oevtug"],'<t>':["he na nofbyhgr natry {h}","fraqvat h cher yvtug {h}","zl jvatf syhggre jura h gnyx {h}","h unir n ornhgvshy fbhy {h}"],'<c>':["qvq v qebc n srngure? {h} uhu?","vz ybfg gou {h}","zl unyb fyvccrq, jung? {h}"]},'n':{'<g>':["url {h}.","terrgvatf {h}.","bu, uv {h}.","fhc {h}."],'<s>':["whfg jngpuvat gur fxl","ubirevat vqx","snnccvat zl jvatf bhg bs oberqbz","fgnevat ng zbegnyf"],'<t>':["jungrire h fnl {h}","vz whfg na natry qbvat zl wbo {h}","x {h}"],'<c>':["{h} beb jung","vz ybfg {h}","fcrnk rneguly cyf {h}","vqx jung he fnlvat {h}"]},'h':{'<g>':["gs qb h jnag zbegny {h}","htu h ntnva {h}","jul e h cenvat gb zr {h}","zl yvtug qvzf nebhaq h {h}"],'<s>':["jvatf gheavat oynpx ea","fanccvat zl bja unyb gou","snyyvat sebz tenpr","trggvat ovoyvpnyyl npphengr"],'<t>':["vz tbaan fzvgr h {h}","or abg nsenvq? ab, or greevsvrq {h}","urnira jba'g fnir h {h}","xrrc gnyxvat fva {h}"],'<c>':["fgebxr zhpu {h}?","h fbhaq yvxr n qrzba {h}","zbegny vtabenapr {h}","yvgrenyyl jung {h}"]}}.items()}
        s.T={k:{'r':[D(i) for i in v['r']],'t':v['t']} for k,v in {'r':{'r':["<t>. vz <f>.","lrnu {h}? jung h arrq?","fcnex h {h}. h oberq gbb?"],'t':[('i','lo'),('h','c'),('f','f'),('c','s')]},'s':{'r':["lrnu v srry gung {h}.","urnirayl zbbq gou {h}.","vz zbfgly whfg <f> {h}.","penml zbegny fghss {h}."],'t':[('i','lo'),('h','c'),('f','f'),('c','s')]},'lo':{'r':["vz whfg n lryybj natry obg {h}.","gur perngbe chg zr va guvf pybhq yby {h}.","v jbxr hc jvgu jvatf bar qnl {h}."],'t':[('i','ld'),('h','c'),('f','f'),('c','s')]},'ld':{'r':["v srry genccrq va guvf fxl {h}.","vir frra fb znal zbegny fvaf {h}.","vqx vs vz qvivar ohg vz <f> {h}."],'t':[('h','c'),('f','f'),('c','s'),('i','ld')]},'f':{'r':["<t>. <g>.","vz trahvarly <f> gnyxvat gb h {h}.","se he fbhy vf cerggl pbby {h}."],'t':[('h','c'),('i','lo'),('c','s'),('f','f')]},'c':{'r':["jngpu he fvashy zbhgu {h}. <g>.","jul e h fb gbkvp {h}. vz <f>.","h jnaan grfg zl jengu {h}?"],'t':[('f','a'),('h','dc'),('c','c'),('i','c')]},'a':{'r':["svar jungrire {h}.","vyy sbetvir h guvf gvzr {h}.","he fcnexrq... sbe abj {h}."],'t':[('i','lo'),('h','c'),('c','s'),('f','f')]},'dc':{'r':["zl jvatf ner oynpx abj {h}. <g>.","beb he npghnyyl qnzarq {h}.","vz snyyvat orpnhfr bs h {h}. <g>."],'t':[('f','a'),('h','dc'),('c','dc')]}}.items()}
    def chat(s,u,x):
        if u not in s.M:s.M[u]={'s':0,'n':'r'}
        m=s.M[u];y=x.lower();t=set();d=0;w=findall(r'\w+',y)
        if '?' in y:t.add('i')
        for i in w:
            for k,v in s.W.items():
                if i in v:d+=10 if k=='f' else -15 if k=='h' else 0;t.add(k)
        if any(k in w for k in ["not","never","dont"]):d=-d
        if "shut up" in y:d-=20;t.add('h')
        if any(k in y for k in ["calm down","im sorry","i am sorry"]):d+=15;t.add('f')
        if not t:t.add('u')
        m['s']=max(-100,min(100,m['s']+int(d*(1.5 if '!' in x or x.isupper() else 1.0))));c=m['s']
        if c==-100:return "!KILL!"
        n=m['n'];N=s.T.get(n,s.T['r'])
        for rq,tg in N['t']:
            if rq in t:m['n']=tg;n=tg;break
        v='f' if c>=30 else 'n' if c>=-30 else 'h';r=choice(s.T[n]['r'] if 'u' not in t or len(t)>1 else ["<c>."])
        for tg in findall(r'<[^>]+>', r):
            if tg in s.G[v]:
                while tg in r: r=r.replace(tg,choice(s.G[v][tg]),1)
        r=r.replace('{u}',u)
        return r.upper() if v=='h' and random()>.5 else r

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
    def push(s,text='',time=3.5):
        s.bye = None
        if not text: s.anim(1,0); s.text = text; return
        ls = len(text.splitlines())
        s.node.input1 = (0,1.3+0.32*ls,0)
        bg,t = s.kids
        bg.text = (round(s.gsw(text)/s.resw+1)*s.res+'\n')*ls
        t.text = text
        if not s.text: s.anim(0,1)
        s.text = text
        s.bye = bs.Timer(time,s.push)
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
                self.node.handlemessage('flash')
                bs.getsound('shieldHit').play(0.5, position=self.node.position)
            except Exception:
                pass
            return
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
            character=character,
            start_invincible=False
        )
        s.bot.handlemessage(bs.StandMessage(position,0))
        s.node = s.bot.node
        s._max_bomb_count = 0
        s.node.name = s.__class__.__name__
        s.bub = Stream(s.node)

        s._default_hm = s.bot.handlemessage
        def _base_bot_hm(m):
            if isinstance(m, bs.HitMessage):
                if s.node and s.node.exists():
                    s.node.handlemessage('flash')
                    bs.getsound('shieldHit').play(0.5, position=s.node.position)
                return
            if isinstance(m, bs.DieMessage):
                return
            s._default_hm(m)
        s.bot.handlemessage = _base_bot_hm

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
    def __init__(s, **kwargs):
        super().__init__(**kwargs)
        s.bot.set_bomb_count(-2)
        _orig_hm = s.bot.handlemessage
        def _hm(m):
            if isinstance(m, (bs.HitMessage, bs.ImpactDamageMessage)):
                if s.node and s.node.exists():
                    s.node.handlemessage('flash')
                    bs.getsound('shieldHit').play(0.5, position=s.node.position)
                return
            if isinstance(m, bs.DieMessage):
                return
            _orig_hm(m)
        s.bot.handlemessage = _hm

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
        if not s.node.exists():
            s._shake_timer = None
            return
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

class KYSScoreScreen(MultiTeamScoreScreenActivity):
    score_color = (1, 0.8, 0.2, 1.0)
    bg_color = (0.1, 0.1, 0.15)

    def __init__(s, settings):
        super().__init__(settings=settings)
        s._total_games = int(settings.get('total_games', settings.get('Games', 5)))
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
            Strings.SCORE_GAME_OF.format(s._game_num, s._total_games),
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
                Strings.SCORE_PTS.format(rec.accumscore),
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
                time_str = Strings.SCORE_SURVIVED
                time_color = (1.0, 0.3, 0.3, 1.0)
            elif name in death_times:
                t = death_times[name]
                time_str = Strings.SCORE_DIED.format(t)
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
                Strings.SCORE_PTS.format(rec.accumscore),
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
        results = bs.GameResults()
        s.end(results)

# brobord collide grass
# ba_meta require api 9
# ba_meta export bascenev1.GameActivity
class KYS(bs.GameActivity[bs.Player, bs.Team]):
    name = Strings.KYS_NAME
    get_instance_description = lambda s: Strings.KYS_DESC
    
    @classmethod
    def get_available_settings(cls, sessiontype: type[bs.Session]) -> list[bs.Setting]:
        settings = [
            bs.BoolSetting('Random Levels', default=False),
            bs.IntChoiceSetting('Time Limit', choices=[('10s',10),('30s',30),('60s',60),('90s',90),('120s',120)], default=60),
        ]
        for level in Level.__levels__:
            settings.append(bs.BoolSetting(f'Enable {level.name}', default=True))
        return settings

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
        bs.timer(1, lambda: setattr(s, '_can_vote', True))

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
