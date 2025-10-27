# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Nuke v1.0 - Stupid minigame

Use the nuke console to bomb anyone.
My first game, don't mind me lol.
Requires my Beam plugin to be installed.
"""

import bascenev1 as bs

# brobord collide grass
# ba_meta require api 9
# ba_meta export bascenev1.GameActivity
class byBordd(bs.TeamGameActivity[bs.Player,bs.Team]):
    name = 'Nuke'
    description = "Nukes coming from above."
    get_availabe_settings = lambda c,_:[]
    supports_session_type = lambda c,_:True
    get_supported_maps = lambda c,_:['Football Stadium']
    get_instance_description = lambda s: "You're very dead"
    get_instance_description_short = lambda s: "You're dead"

    def __init__(s, settings):
        super().__init__(settings)
        s.default_music = bs.MusicType.GRAND_ROMP
        # custom
        s.beam = None

    def on_begin(s) -> None:
        super().on_begin()
        s.beam = s.make_beam()

    def handlemessage(s,m):
        if isinstance(m,bs.PlayerDiedMessage):
            s.respawn_player(m.getplayer(bs.Player))

    def make_beam(s):
        from beam import (
            Container,
            Button,
            Beam,
            Text
        )
        from bauiv1 import (
            SpecialChar as sc,
            charstr as cs
        )
        from bascenev1lib.actor.bomb import Bomb

        # Get map bounds and container size
        x0, y0, z0, x1, y1, z1 = bs.getactivity().globalsnode.area_of_interest_bounds
        size = 450, 350  # Container size (w0, h0)
        w0, h0 = size

        # Map margins (0.1 ratio)
        m = 0.1
        mx, my = w0 * m, h0 * m
        ww, hh = w0 - mx * 2, h0 - my * 2

        # Delta world dimensions.
        dx = x1 - x0
        dz = z1 - z0 

        # Handle the potential for zero division if bounds are equal
        dx = dx if abs(dx) > 1e-6 else 1.0 
        dz = dz if abs(dz) > 1e-6 else 1.0
        
        # --- COORDINATE CONVERSION FUNCTIONS ---

        def world_to_screen(world_x: float, world_z: float) -> tuple[float, float]:
            """
            Converts world coordinates (world_x, world_z) to container screen 
            coordinates (px, py).
            """
            dz_mag = abs(z1 - z0)
            dz_mag = dz_mag if dz_mag > 1e-6 else 1.0 

            # 1. Normalize world position to (u, v)
            u = (world_x - x0) / dx
            v = (z1 - world_z) / dz_mag
            
            # 2. Scale normalized (u, v) to container coordinates (px, py)
            px = mx + u * ww
            py = my + v * hh

            # 3. Clamp position to container bounds
            px = max(0.0, min(w0, px))
            py = max(0.0, min(h0, py))

            return (px, py)

        def screen_to_world(px: float, py: float) -> tuple[float, float, float]:
            """
            Converts container screen coordinates (px, py) to world coordinates (wx, wy, wz).
            """
            dz_mag = abs(z1 - z0)
            dz_mag = dz_mag if dz_mag > 1e-6 else 1.0

            # 1. Normalize position relative to the inner map area (u, v)
            if 0 <= px <= 1 and 0 <= py <= 1:
                px *= w0
                py *= h0

            u = (px - mx) / ww
            v = (py - my) / hh

            # 2. Convert normalized (u, v) to world (wx, wz)
            wx = x0 + u * dx
            wz = z1 - v * dz_mag
            
            # Set fixed Y height for the nuke drop
            wy = 9 
            return (wx, wy, wz)

        def eye(px, py):
            """Nuke dropping function, now using screen_to_world."""
            world_pos = screen_to_world(px, py)
            
            Bomb(
                bomb_type='impact',
                position=world_pos,
                bomb_scale=2,
                blast_radius=4
            ).autoretain()

        # --- Console Setup ---
        c = Container(
            size=size,
            pipe=eye
        )
        # The Beam object 'b' is created here.
        b = Beam(
            position=(0,3,0),
            container=c,
            title=cs(sc.OUYA_BUTTON_Y)+' Nuke Console',
            message=cs(sc.LEFT_BUTTON)+' Punch this for power.'
        )
        Text(
            parent=c,
            text="Nuke Console",
            position=(155,200),
            h_align='center',
            scale=1.5
        )
        Button(
            parent=c,
            position=(25,275),
            size=(50,35),
            label=cs(sc.BACK),
            color=(0.6,0.2,0.1),
            textcolor=(0.9,0.3,0.2),
            call=b.back
        )
        trash = []
        ox,oy = (-10,-20)
        def spy():
            """
            Player tracking function, using the explicit Beam world position.
            """
            for _ in trash:
                if _: _.delete()
            trash.clear()

            # *** SCALE FACTOR ***
            SCALE_FACTOR = 2.0 
            # Consistent text scale
            MARKER_SCALE = 0.6 

            # 1. Add 'Beam Console' Marker using its current world position
            
            if b.node:
                beam_world_pos = b.node.position
                beam_world_x = beam_world_pos[0]
                beam_world_z = beam_world_pos[2]
                
                beam_x, beam_y = world_to_screen(beam_world_x, beam_world_z)
                final_beam_x = beam_x * SCALE_FACTOR
                final_beam_y = beam_y * SCALE_FACTOR

                trash.append(Text(
                    parent=c,
                    text=cs(sc.OUYA_BUTTON_Y)+' Console',
                    color=(1,1,0),
                    h_align='center',
                    scale=MARKER_SCALE, # <-- Corrected scale
                    position=(final_beam_x+ox, final_beam_y+oy)
                ))


            # 2. Add Player Name Markers
            for n in bs.getnodes():
                if not n or n.getnodetype() != 'spaz':
                    continue
                    
                world_pos = n.position
                
                # Convert the world (x, z) to container (x, y)
                container_x, container_y = world_to_screen(world_pos[0], world_pos[2])
                
                # *** APPLY SCALING FIX ***
                final_x = container_x * SCALE_FACTOR
                final_y = container_y * SCALE_FACTOR
                
                trash.append(Text(
                    parent=c,
                    text=cs(sc.DPAD_CENTER_BUTTON)+' '+n.name,
                    color=n.color,
                    h_align='center',
                    scale=MARKER_SCALE, # Consistent scale
                    # Use the scaled position
                    position=(final_x+ox, final_y+oy)
                ))

        return bs.Timer(0.01,spy,repeat=True)
