# Copyright 2026 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
BSDoom v1.0 - DOOM!

Play DOOM under ballistica.
Experimental.
"""

import sys
import os
import threading
import bascenev1 as bs
import babase

DOOM_DIR = os.path.join(os.path.dirname(__file__), 'doom')
if DOOM_DIR not in sys.path:
    sys.path.insert(0, DOOM_DIR)

class Strings:
    GAME_DESC = 'Play DOOM inside BombSquad'
    INST_DESC = 'More like BOOM'
    INST_DESC_SHORT = 'BSD Engine v1.0'

class Const:
    DOOM = 'DOOM'
    PIXEL = 'white'
    SETTINGS = ()
    PLAY_TYPES = (DOOM,)
    SUPPORTED_MAPS = (DOOM,)
    MAP_NAME = DOOM
    GAME_NAME = DOOM
    MAP_PREVIEW = 'doomPreview'
    MAP_DEFS = type('foo',(object,),{
        'points':{},
        'boxes':{
            'map_bounds':(0,)*9,
            'area_of_interest_bounds':(0,)*9
        }
    })()
    BACKGROUND = 'black'
    BACKGROUND_MESH = 'tipTopBG'
    SCREEN_W = 160
    SCREEN_H = 100
    SCALE = 7
    DOOM_W = 320
    DOOM_H = 200

class DoomEngine:
    _started = False

    @classmethod
    def start(cls):
        if cls._started:
            return
        cls._started = True
        t = threading.Thread(target=cls._run, daemon=True)
        t.start()

    @staticmethod
    def _run():
        import d_main
        try:
            d_main.D_DoomMain()
        except Exception as e:
            print(f'[BSDoom] engine crash: {e}')

    @staticmethod
    def get_frame():
        try:
            import v_video
            import i_video
            import doom_progress
            if any(v_video.screens[0]):
                doom_progress.set(100)
            return bytes(v_video.screens[0]), bytes(i_video.current_palette)
        except Exception:
            return None, None

class DoomMap(bs.Map):
    defs = Const.MAP_DEFS
    name = Const.MAP_NAME

    @classmethod
    def get_play_types(cls):
        return Const.PLAY_TYPES

    @classmethod
    def get_preview_texture_name(cls):
        return Const.MAP_PREVIEW

    def __init__(self):
        super().__init__()
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': bs.getmesh(Const.BACKGROUND_MESH),
                'lighting': False,
                'background': True,
                'color_texture': bs.gettexture(Const.BACKGROUND)
            }
        )

# ba_meta export bascenev1.GameActivity
class DoomActivity(bs.GameActivity[bs.Player,bs.Team]):
    name = Const.GAME_NAME
    description = Strings.GAME_DESC
    get_availabe_settings = lambda s: Const.SETTINGS
    supports_session_type = lambda s: True
    get_supported_maps = lambda s: Const.SUPPORTED_MAPS
    get_instance_description = lambda s: Strings.INST_DESC
    get_instance_description_short = lambda s: Strings.INST_DESC_SHORT

    def __init__(self, settings):
        super().__init__(settings)
        self.default_music = None
        self.display = DoomDisplay()
        self._timer = None

    def on_begin(self):
        super().on_begin()
        DoomEngine.start()
        self._schedule_update()

    def _schedule_update(self):
        self._timer = bs.Timer(
            0.05,  # 20fps
            bs.WeakCallPartial(self._update),
            repeat=True
        )

    def _update(self):
        if not self.display._loaded:
            import doom_progress
            pct = doom_progress.get()
            self.display.loading_text.text = f'Loading... {pct}%'
            if pct >= 95:
                raw, palette = DoomEngine.get_frame()
                if raw and any(raw):
                    self.display.loading_text.delete()
                    self.display._loaded = True
            return

        raw, palette = DoomEngine.get_frame()
        if not raw or not palette or not any(raw):
            return
        self.display.update(raw, palette)

    def on_player_join(self, player):
        (
            player
            .sessionplayer
            .inputdevice
            .client_id
        ) == -1 and self.capture(player)

    def capture(self, player):
        for _ in dir(IT := bs.InputType):
            if _.startswith('_'): continue
            player.assigninput(
                getattr(IT, _),
                bs.CallPartial(self.input, _)
            )

    def input(self, key, *data):
        import d_net, d_event, doomkeys
        ev = d_event.event_t()
        
        # Determine if it's a press or release
        if key.endswith('_PRESS'):
            ev.type = d_event.ev_keydown
        elif key.endswith('_RELEASE'):
            ev.type = d_event.ev_keyup
        else:
            ev.type = d_event.ev_keydown

        mapping = {
            'JUMP_PRESS':    doomkeys.KEY_ENTER,
            'JUMP_RELEASE':  doomkeys.KEY_ENTER,
            'PUNCH_PRESS':   ord(' '),       # Space (Use/Open doors in Doom)
            'PUNCH_RELEASE': ord(' '),
            'BOMB_PRESS':    doomkeys.KEY_ESCAPE,
            'BOMB_RELEASE':  doomkeys.KEY_ESCAPE,
        }

        # Setup axis tracking to release previous direction keys
        if not hasattr(self, '_pressed_axes'):
            self._pressed_axes = set()

        if key == 'LEFT_RIGHT' and data:
            val = data[0]
            # Emit key-up for any horizontal axis keys we were holding
            for k in [doomkeys.KEY_LEFTARROW, doomkeys.KEY_RIGHTARROW]:
                if k in self._pressed_axes:
                    rel_ev = d_event.event_t()
                    rel_ev.type = d_event.ev_keyup
                    rel_ev.data1 = k
                    d_net.D_PostEvent(rel_ev)
                    self._pressed_axes.remove(k)
                    
            if val < -0.3:
                ev.type = d_event.ev_keydown
                ev.data1 = doomkeys.KEY_LEFTARROW
                self._pressed_axes.add(ev.data1)
            elif val > 0.3:
                ev.type = d_event.ev_keydown
                ev.data1 = doomkeys.KEY_RIGHTARROW
                self._pressed_axes.add(ev.data1)
            else:
                return # Centered (deadzone), releases are already handled

        elif key == 'UP_DOWN' and data:
            val = data[0]
            # Emit key-up for any vertical axis keys we were holding
            for k in [doomkeys.KEY_DOWNARROW, doomkeys.KEY_UPARROW]:
                if k in self._pressed_axes:
                    rel_ev = d_event.event_t()
                    rel_ev.type = d_event.ev_keyup
                    rel_ev.data1 = k
                    d_net.D_PostEvent(rel_ev)
                    self._pressed_axes.remove(k)

            if val < -0.3:
                ev.type = d_event.ev_keydown
                ev.data1 = doomkeys.KEY_DOWNARROW
                self._pressed_axes.add(ev.data1)
            elif val > 0.3:
                ev.type = d_event.ev_keydown
                ev.data1 = doomkeys.KEY_UPARROW
                self._pressed_axes.add(ev.data1)
            else:
                return # Centered (deadzone), releases are already handled

        elif key in mapping and mapping[key] is not None:
            ev.data1 = mapping[key]
        else:
            return # Ignore unmapped keys silently

        # print(f'[BSDoom] input: {key} -> {ev.data1} (Type: {ev.type})')
        d_net.D_PostEvent(ev)

class DoomDisplay:
    def __init__(self, width=Const.SCREEN_W, height=Const.SCREEN_H, scale=Const.SCALE):
        self.width = width
        self.height = height
        self.step_x = Const.DOOM_W // width
        self.step_y = Const.DOOM_H // height
        self.pixels = [
            bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture(Const.PIXEL),
                    'absolute_scale': True,
                    'position': (
                        (scale * x) - (width * scale) / 2,
                        (scale * y) - (height * scale) / 2
                    ),
                    'scale': (scale, scale),
                    'color': (0.0, 0.0, 0.0),
                    'attach': 'center'
                }
            )
            for x in range(width)
            for y in range(height)
        ]
        self.loading_text = bs.newnode(
            'text',
            attrs={
                'text': 'Loading... 0%',
                'scale': 1.2,
                'position': (0, 0),
                'h_align': 'center',
                'v_align': 'center',
                'color': (1, 1, 1, 1),
            }
        )
        self._loaded = False

    def update(self, raw, palette):
        if not self._loaded:
            import doom_progress
            pct = doom_progress.get()
            if pct < 100:
                self.loading_text.text = f'Loading... {pct}%'
                return
            else:
                self.loading_text.delete()
                self._loaded = True
        for i, node in enumerate(self.pixels):
            px = i // self.height
            py = i % self.height
            doom_x = px * self.step_x
            doom_y = (self.height - 1 - py) * self.step_y  # flip Y
            idx = raw[doom_y * Const.DOOM_W + doom_x]
            r = palette[idx * 3]     / 255.0
            g = palette[idx * 3 + 1] / 255.0
            b = palette[idx * 3 + 2] / 255.0
            node.color = (r, g, b)

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(bs.Plugin):
    def __init__(self):
        bs._map.register_map(DoomMap)
