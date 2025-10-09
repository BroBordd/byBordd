# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
FPP v1.0 - First person perspective

My failed attempt to implement first person perspective.
Though, it works so, yeah.
Experimental.
"""

from babase import (
    InputType as IT,
    Plugin
)
from _babase import (
    set_camera_position as SCP,
    set_camera_manual as SCM,
    set_camera_target as SCT
)
from bascenev1 import (
    get_foreground_host_activity as ga,
    Timer as tuck,
    newnode
)

class FPP:
    def __init__(s, node):
        s.node = node
        s.forward_vec_norm = (0, 1)
        s.right_vec_norm = (1, 0)
        s.joystick_ud = 0
        s.joystick_lr = 0
        SCM(True)
        s.spyt = tuck(0.01, s.spy, repeat=True)
        o = node.getdelegate(object)
        s.oud = o.on_move_up_down
        s.olr = o.on_move_left_right
        p = node.source_player
        p.assigninput(IT.UP_DOWN, s.ud)
        p.assigninput(IT.LEFT_RIGHT, s.lr)

    def ud(s, v):
        s.joystick_ud = v
        s.move()

    def lr(s, v):
        s.joystick_lr = v
        s.move()
    def move(s):
        v_ud = s.joystick_ud
        v_lr = s.joystick_lr

        if v_ud < 0:
            v_lr = 0

        x_movement = v_ud * s.forward_vec_norm[0] + v_lr * s.right_vec_norm[0]
        z_movement = v_ud * s.forward_vec_norm[1] + v_lr * s.right_vec_norm[1]
        s.olr(x_movement)
        s.oud(z_movement)

    def spy(s):
        if not s.node.exists():
            s.spyt = None
            return

        p_chest = s.node.position
        p_backhead = s.node.position_forward
        distance_factor = 5.0
        camera_back_offset = 0.2

        stable_forward_vector = (
            p_chest[0] - p_backhead[0],
            p_chest[1] - p_backhead[1],
            p_chest[2] - p_backhead[2],
        )

        camera_pos = (
            p_chest[0] - stable_forward_vector[0] * camera_back_offset,
            p_backhead[1] + 1,
            p_chest[2] - stable_forward_vector[2] * camera_back_offset,
        )

        camera_target = (
            camera_pos[0] + stable_forward_vector[0] * distance_factor,
            camera_pos[1] + stable_forward_vector[1] * distance_factor + 0.35 * distance_factor,
            camera_pos[2] + stable_forward_vector[2] * distance_factor,
        )

        forward_vector_xz = (stable_forward_vector[0], stable_forward_vector[2])
        magnitude = (forward_vector_xz[0]**2 + forward_vector_xz[1]**2)**0.5

        if magnitude > 0:
            s.forward_vec_norm = (forward_vector_xz[0] / magnitude, forward_vector_xz[1] / magnitude)
            s.right_vec_norm = (s.forward_vec_norm[1], -s.forward_vec_norm[0])
        else:
            s.forward_vec_norm = (0, 1)
            s.right_vec_norm = (1, 0)

        SCP(*camera_pos)
        SCT(*camera_target)

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin): pass
