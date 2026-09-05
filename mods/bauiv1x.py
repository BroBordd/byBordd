# Copyright 2026 BrotherBoard
# Free for everyone to use and share
# Discord >> @BrotherBoard

"""
bauiv1x v1.0 - Ballistica UI Extended

Experimental.
"""

import bauiv1 as bui

from typing import Callable
from enum import IntEnum

class Widget:
    """
    A bauiv1x Widget

    Used as subclass for all widgets
    root: Our very own container
    parent: What we are sitting on
    lerp/ease: These are for animations
    """
    def __init__(self):
        self.transitioning_out = False

    def __bool__(self):
        return (
            self.root.exists() and not
            self.parent.transitioning_out
        )

    def exists(self):
        return bool(self)

    @staticmethod
    def lerp(a, b, t):
        return a + (b - a) * t

    @staticmethod
    def ease_out(t):
        return 1 - (1 - t) ** 3

class SnackBar(Widget):
    """
    An alert that slides from the bottom of screen

    parent: The current container
    text: The text on the snack
    action_label: The label of the action button (optional)
    action_callback: The call of action button (optional)
    duration: How much to wait before dismissing (optional)
    """
    def __init__(
        self,
        parent: bui.Widget,
        text: str,
        action_label: str | None = None,
        action_callback: Callable | None = None,
        duration: float = 2,
        color: tuple[float, float, float] = (1,1,1)
    ):
        # math
        cent = parent.get_screen_space_center()
        virt = bui.get_virtual_screen_size()
        size = (
            virt[0],
            80
        )
        # hack
        that = (hack:=bui.textwidget(
            parent=parent,
            size=(0,0)
        )).get_screen_space_center()
        hack.delete()
        pize = (
            (cent[0]-that[0])*2,
            (cent[1]-that[1])*2
        )
        # export
        super().__init__()
        self.duration = duration
        self.parent = parent
        self.size = size
        self.color = color
        self.root_x, self.root_y = (
            -virt[0]/2 + pize[0]/2 - cent[0],
            -virt[1]/2 + pize[1]/2 - size[1]*2 - cent[1]
        )
        # root
        self.root = bui.containerwidget(
            parent=parent,
            size=size,
            position=(
                self.root_x,
                self.root_y
            ),
            background=False
        )
        # bg
        self.background = bui.imagewidget(
            parent=self.root,
            size=(
                size[0]*1.4,
                size[1]*1.2
            ),
            position=(
                -size[0]*0.2,
                -size[1]*0.2
            ),
            texture=bui.gettexture('white'),
            color=self.color
        )
        # text
        bui.textwidget(
            parent=self.root,
            text=text,
            size=size,
            v_align='center',
            color=(0,0,0)
        )
        # action
        bui.buttonwidget(
            parent=self.root,
            button_type='square',
            texture=bui.gettexture('white'),
            color=(0,0,0),
            textcolor=(1,1,1),
            enable_sound=False,
            label=action_label,
            on_activate_call=action_callback,
            size=(
                130,
                size[1] * 0.6
            ),
            position=(
                size[0] - 130,
                size[1] * 0.2
            )
        )
        # finally
        self.life_timer = bui.AppTimer(
            0.01, lambda: (
                not self and self.delete()
            ), repeat=True
        )
        self.anim_finish = self.standby
        self.anim_in()

    def anim_in(self):
        self.anim_buff = 0
        self.anim_start = 0
        self.anim_end = self.size[1]*1.63
        self.anim_fire()

    def standby(self):
        self.anim_timer = bui.AppTimer(
            self.duration, self.dismiss
        )

    def anim_out(self):
        self.anim_start = self.anim_buff
        self.anim_end = 0
        self.anim_fire()

    def anim_fire(self):
        self.anim_duration = 30
        self.anim_indx = 0
        self.anim_timer = bui.AppTimer(
            1 / 60, self.anim_step, repeat=True
        )

    def anim_step(self):
        if not self: return
        self.anim_indx += 1
        if self.anim_indx > self.anim_duration:
            self.anim_timer = None
            self.anim_buff = self.anim_end
            self.anim_finish()
            return

        t = self.anim_indx / self.anim_duration
        eased_t = self.ease_out(t)
        self.anim_buff = self.lerp(self.anim_start, self.anim_end, eased_t)

        bui.containerwidget(
            self.root,
            position=(
                self.root_x,
                self.root_y+self.anim_buff
            )
        )

    def dismiss(self):
        self.transitioning_out = True
        self.anim_finish = self.delete
        self.anim_out()

    def delete(self):
        self.anim_timer = None
        self.life_timer = None
        self.root.delete()

class Switch(Widget):
    class Style(IntEnum):
        OUTLINE = 0
        MATERIAL = 1
        SPLIT = 2
        M3 = 3
        ICON = 4

    def __init__(
        self,
        parent: bui.Widget,
        size: tuple[float, float] = (80,50),
        position: tuple[float, float] = (0,0),
        value: bool = False,
        style: int = Style.OUTLINE,
        color: tuple[float, float, float] = (0,0,0),
        on_value_change: Callable[[bool], None] | None = None
    ):
        # export
        super().__init__()
        self.parent = parent
        self.size = size
        self.value = value
        self.anim_t = 1.0 if value else 0.0
        self.style = Switch.Style(style)
        self.color = color
        self.on_value_change = on_value_change
        # root
        self.root = bui.containerwidget(
            parent=parent,
            size=size,
            background=False,
            position=position
        )
        # border
        col = self.color if self.style != Switch.Style.SPLIT else (0.2,0.2,0.2)
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(
                0, 0
            ),
            size=(size[1],size[1]),
            color=col
        )
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(
                size[0] - size[1], 0
            ),
            size=(size[1],size[1]),
            color=col
        )
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=col,
            position=(
                size[1]/2,
                0
            ),
            size=(
                size[0] - size[1],
                size[1]
            )
        )
        # style build
        getattr(self, f'wear_{self.style.name.lower()}')()
        # listener
        self.button = bui.buttonwidget(
            parent=self.root,
            texture=bui.gettexture('empty'),
            enable_sound=False,
            label='',
            size=size,
            position=(0,0),
            on_activate_call=self.toggle
        )
        # finally
        self.anim_timer = None

    @staticmethod
    def lerp_col(a, b, t):
        return tuple(
            Widget.lerp(a[i], b[i], t) for i in range(3)
        )

    def toggle(self):
        bui.getsound('deek').play()
        self.value = not self.value
        self.anim_start = self.anim_t
        self.anim_end = 1.0 if self.value else 0.0
        self.anim_fire()
        if self.on_value_change:
            self.on_value_change(self.value)

    def anim_fire(self):
        self.anim_duration = 20
        self.anim_indx = 0
        self.anim_timer = bui.AppTimer(
            1 / 60, self.anim_step, repeat=True
        )

    def anim_step(self):
        if not self: return
        self.anim_indx += 1
        if self.anim_indx > self.anim_duration:
            self.anim_timer = None
            self.anim_t = self.anim_end
            self.anim_apply()
            return

        t = self.anim_indx / self.anim_duration
        eased_t = self.ease_out(t)
        self.anim_t = self.lerp(self.anim_start, self.anim_end, eased_t)
        self.anim_apply()

    def anim_apply(self):
        getattr(self, f'wiggle_{self.style.name.lower()}')()

    def wear_outline(self):
        pize = self.size
        self.track_off_col = (0.15,0.15,0.15)
        self.track_on_col = (0.45,0.45,0.45)
        self.thumb_off_col = (1,1,1)
        self.thumb_on_col = (0.05,0.05,0.05)

        squish = 0.9
        gap = 0.08
        self.nub_size = pize[1] * squish
        self.nub_y = (pize[1] - self.nub_size) / 2
        self.nub_lo = pize[1] * gap
        self.nub_hi = pize[0] - self.nub_size - pize[1] * gap

        squash = 0.85
        fudge = 0.966
        shove = 0.035

        chunk = (pize[0] * squash, pize[1] * squash)
        nudge = (
            (pize[0] - chunk[0]) / 2,
            (pize[1] - chunk[1]) / 2
        )
        shove_px = chunk[1] * shove
        slab_h = chunk[1] * fudge
        slab_y = nudge[1] + (chunk[1] - slab_h) / 2

        juice = self.lerp_col(self.track_off_col, self.track_on_col, self.anim_t)

        self.capsule_l = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(
                nudge[0] - shove_px, nudge[1]
            ),
            size=(chunk[1], chunk[1]),
            color=juice
        )
        self.capsule_r = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(
                nudge[0] + chunk[0] - chunk[1] + shove_px, nudge[1]
            ),
            size=(chunk[1], chunk[1]),
            color=juice
        )
        self.capsule_bar = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=juice,
            position=(
                nudge[0] + chunk[1] / 2,
                slab_y
            ),
            size=(
                chunk[0] - chunk[1],
                slab_h
            )
        )

        blob = self.lerp_col(self.thumb_off_col, self.thumb_on_col, self.anim_t)
        nub_x = self.lerp(self.nub_lo, self.nub_hi, self.anim_t)

        self.thumb = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(
                nub_x, self.nub_y
            ),
            size=(self.nub_size, self.nub_size),
            color=blob
        )

    def wiggle_outline(self):
        juice = self.lerp_col(self.track_off_col, self.track_on_col, self.anim_t)
        blob = self.lerp_col(self.thumb_off_col, self.thumb_on_col, self.anim_t)
        nub_x = self.lerp(self.nub_lo, self.nub_hi, self.anim_t)

        bui.imagewidget(self.capsule_l, color=juice)
        bui.imagewidget(self.capsule_r, color=juice)
        bui.imagewidget(self.capsule_bar, color=juice)
        bui.imagewidget(
            self.thumb,
            position=(nub_x, self.nub_y),
            color=blob
        )

    def wear_material(self):
        pize = self.size
        self.track_off_col = (0.15,0.15,0.15)
        self.track_on_col = (0.45,0.45,0.45)
        self.thumb_off_col = (1,1,1)
        self.thumb_on_col = (0.05,0.05,0.05)

        squash = 0.85
        fudge = 0.966
        shove = 0.035

        chunk = (pize[0] * squash, pize[1] * squash)
        nudge = (
            (pize[0] - chunk[0]) / 2,
            (pize[1] - chunk[1]) / 2
        )
        shove_px = chunk[1] * shove
        slab_h = chunk[1] * fudge
        slab_y = nudge[1] + (chunk[1] - slab_h) / 2

        juice = self.lerp_col(self.track_off_col, self.track_on_col, self.anim_t)

        self.capsule_l = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(nudge[0] - shove_px, nudge[1]),
            size=(chunk[1], chunk[1]),
            color=juice
        )
        self.capsule_r = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(nudge[0] + chunk[0] - chunk[1] + shove_px, nudge[1]),
            size=(chunk[1], chunk[1]),
            color=juice
        )
        self.capsule_bar = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=juice,
            position=(nudge[0] + chunk[1] / 2, slab_y),
            size=(chunk[0] - chunk[1], slab_h)
        )

        squirt_lo = 0.55
        squirt_hi = 0.85
        gap_lo = pize[1] * 0.12
        gap_hi = pize[1] * 0.08

        self.nub_lo_size = pize[1] * squirt_lo
        self.nub_hi_size = pize[1] * squirt_hi
        self.nub_lo_x = gap_lo
        self.nub_hi_x = pize[0] - self.nub_hi_size - gap_hi

        blob_size = self.lerp(self.nub_lo_size, self.nub_hi_size, self.anim_t)
        nub_x = self.lerp(self.nub_lo_x, self.nub_hi_x, self.anim_t)
        nub_y = (pize[1] - blob_size) / 2
        blob = self.lerp_col(self.thumb_off_col, self.thumb_on_col, self.anim_t)

        self.thumb = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(nub_x, nub_y),
            size=(blob_size, blob_size),
            color=blob
        )

        # check
        res = 80
        pts = [(0.30,0.50),(0.42,0.38),(0.66,0.62)]
        dot = blob_size * 0.06
        off_x = 0.05
        off_y = -0.05

        self.dots = []
        for i in range(res):
            t = i / (res-1)
            seg = t * (len(pts)-1)
            a = pts[int(seg)]
            b = pts[min(int(seg)+1, len(pts)-1)]
            f = seg - int(seg)
            px = self.lerp(a[0], b[0], f)
            py = self.lerp(a[1], b[1], f)

            dx = nub_x + (px + off_x) * blob_size - dot/2
            dy = nub_y + (py + off_y) * blob_size - dot/2

            d = bui.imagewidget(
                parent=self.root,
                texture=bui.gettexture('circle'),
                position=(dx, dy),
                size=(dot, dot),
                color=juice,
                opacity=self.anim_t
            )
            self.dots.append(d)

    def wiggle_material(self):
        pize = self.size
        juice = self.lerp_col(self.track_off_col, self.track_on_col, self.anim_t)
        blob = self.lerp_col(self.thumb_off_col, self.thumb_on_col, self.anim_t)
        blob_size = self.lerp(self.nub_lo_size, self.nub_hi_size, self.anim_t)
        nub_x = self.lerp(self.nub_lo_x, self.nub_hi_x, self.anim_t)
        nub_y = (pize[1] - blob_size) / 2

        bui.imagewidget(self.capsule_l, color=juice)
        bui.imagewidget(self.capsule_r, color=juice)
        bui.imagewidget(self.capsule_bar, color=juice)
        bui.imagewidget(
            self.thumb,
            position=(nub_x, nub_y),
            size=(blob_size, blob_size),
            color=blob
        )

        # check
        res = 80
        pts = [(0.30,0.50),(0.42,0.38),(0.66,0.62)]
        dot = blob_size * 0.06
        off_x = 0.05
        off_y = -0.05

        for i in range(res):
            t = i / (res-1)
            seg = t * (len(pts)-1)
            a = pts[int(seg)]
            b = pts[min(int(seg)+1, len(pts)-1)]
            f = seg - int(seg)
            px = self.lerp(a[0], b[0], f)
            py = self.lerp(a[1], b[1], f)

            dx = nub_x + (px + off_x) * blob_size - dot/2
            dy = nub_y + (py + off_y) * blob_size - dot/2

            bui.imagewidget(
                self.dots[i],
                position=(dx, dy),
                size=(dot, dot),
                color=juice,
                opacity=self.anim_t
            )

    def wear_split(self):
        pize = self.size
        # shades
        self.track_off_col = (0.15,0.15,0.15)
        self.track_on_col = (0.3,0.3,0.3)
        self.thumb_off_col = (1,1,1)
        self.thumb_on_col = (1,1,1)

        squash = 0.85
        fudge = 0.966
        shove = 0.035

        chunk = (pize[0] * squash, pize[1] * squash)
        nudge = (
            (pize[0] - chunk[0]) / 2,
            (pize[1] - chunk[1]) / 2
        )
        shove_px = chunk[1] * shove
        slab_h = chunk[1] * fudge
        slab_y = nudge[1] + (chunk[1] - slab_h) / 2
        half = (chunk[0] - chunk[1]) / 2

        self.capsule_l = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(nudge[0] - shove_px, nudge[1]),
            size=(chunk[1], chunk[1]),
            color=self.track_off_col
        )
        self.capsule_r = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(nudge[0] + chunk[0] - chunk[1] + shove_px, nudge[1]),
            size=(chunk[1], chunk[1]),
            color=self.track_on_col
        )
        self.split_l = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=self.track_off_col,
            position=(nudge[0] + chunk[1] / 2, slab_y),
            size=(half, slab_h)
        )
        self.split_r = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=self.track_on_col,
            position=(nudge[0] + chunk[1] / 2 + half, slab_y),
            size=(half, slab_h)
        )

        squirt = 0.7
        gap_lo = pize[1] * 0.12
        gap_hi = pize[1] * 0.12

        self.nub_size = pize[1] * squirt
        self.nub_lo_x = gap_lo
        self.nub_hi_x = pize[0] - self.nub_size - gap_hi
        self.nub_y = (pize[1] - self.nub_size) / 2

        nub_x = self.lerp(self.nub_lo_x, self.nub_hi_x, self.anim_t)
        blob = self.lerp_col(self.thumb_off_col, self.thumb_on_col, self.anim_t)

        self.thumb = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(nub_x, self.nub_y),
            size=(self.nub_size, self.nub_size),
            color=blob
        )

    def wiggle_split(self):
        nub_x = self.lerp(self.nub_lo_x, self.nub_hi_x, self.anim_t)
        blob = self.lerp_col(self.thumb_off_col, self.thumb_on_col, self.anim_t)

        bui.imagewidget(
            self.thumb,
            position=(nub_x, self.nub_y),
            color=blob
        )

    def wear_m3(self):
        pize = self.size
        self.track_off_col = (0.1,0.1,0.1)
        self.track_on_col = (0,0,0)
        self.thumb_off_col = (0.6,0.6,0.6)
        self.thumb_on_col = (1,1,1)

        squirt_lo = 0.55
        squirt_hi = 0.85
        gap_lo = pize[1] * 0.12
        gap_hi = pize[1] * 0.08

        self.nub_lo_size = pize[1] * squirt_lo
        self.nub_hi_size = pize[1] * squirt_hi
        self.nub_lo_x = gap_lo
        self.nub_hi_x = pize[0] - self.nub_hi_size - gap_hi

        juice = self.lerp_col(self.track_off_col, self.track_on_col, self.anim_t)
        blob_size = self.lerp(self.nub_lo_size, self.nub_hi_size, self.anim_t)
        nub_x = self.lerp(self.nub_lo_x, self.nub_hi_x, self.anim_t)
        nub_y = (pize[1] - blob_size) / 2
        blob = self.lerp_col(self.thumb_off_col, self.thumb_on_col, self.anim_t)

        self.track_fill = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(0, 0),
            size=(pize[1], pize[1]),
            color=juice,
            opacity=self.anim_t
        )
        self.track_fill_r = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(pize[0] - pize[1], 0),
            size=(pize[1], pize[1]),
            color=juice,
            opacity=self.anim_t
        )
        self.track_fill_bar = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=juice,
            position=(pize[1] / 2, 0),
            size=(pize[0] - pize[1], pize[1]),
            opacity=self.anim_t
        )

        self.thumb = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(nub_x, nub_y),
            size=(blob_size, blob_size),
            color=blob
        )

    def wiggle_m3(self):
        pize = self.size
        juice = self.lerp_col(self.track_off_col, self.track_on_col, self.anim_t)
        blob_size = self.lerp(self.nub_lo_size, self.nub_hi_size, self.anim_t)
        nub_x = self.lerp(self.nub_lo_x, self.nub_hi_x, self.anim_t)
        nub_y = (pize[1] - blob_size) / 2
        blob = self.lerp_col(self.thumb_off_col, self.thumb_on_col, self.anim_t)

        bui.imagewidget(self.track_fill, color=juice, opacity=self.anim_t)
        bui.imagewidget(self.track_fill_r, color=juice, opacity=self.anim_t)
        bui.imagewidget(self.track_fill_bar, color=juice, opacity=self.anim_t)
        bui.imagewidget(
            self.thumb,
            position=(nub_x, nub_y),
            size=(blob_size, blob_size),
            color=blob
        )

    def wear_icon(self):
        pize = self.size
        self.track_off_col = (0.15,0.15,0.15)
        self.track_on_col = (0.45,0.45,0.45)
        self.thumb_off_col = (1,1,1)
        self.thumb_on_col = (0.05,0.05,0.05)

        squash = 0.85
        fudge = 0.966
        shove = 0.035

        chunk = (pize[0] * squash, pize[1] * squash)
        nudge = (
            (pize[0] - chunk[0]) / 2,
            (pize[1] - chunk[1]) / 2
        )
        shove_px = chunk[1] * shove
        slab_h = chunk[1] * fudge
        slab_y = nudge[1] + (chunk[1] - slab_h) / 2

        juice = self.lerp_col(self.track_off_col, self.track_on_col, self.anim_t)

        self.capsule_l = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(nudge[0] - shove_px, nudge[1]),
            size=(chunk[1], chunk[1]),
            color=juice
        )
        self.capsule_r = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(nudge[0] + chunk[0] - chunk[1] + shove_px, nudge[1]),
            size=(chunk[1], chunk[1]),
            color=juice
        )
        self.capsule_bar = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=juice,
            position=(nudge[0] + chunk[1] / 2, slab_y),
            size=(chunk[0] - chunk[1], slab_h)
        )

        self.nub_size = pize[1] * 0.75
        gap = (pize[1] - self.nub_size) / 2
        self.nub_lo = gap
        self.nub_hi = pize[0] - self.nub_size - gap

        nub_x = self.lerp(self.nub_lo, self.nub_hi, self.anim_t)
        nub_y = gap
        blob = self.lerp_col(self.thumb_off_col, self.thumb_on_col, self.anim_t)

        self.thumb = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(nub_x, nub_y),
            size=(self.nub_size, self.nub_size),
            color=blob
        )

        dot = self.nub_size * 0.3
        dot_x = nub_x + (self.nub_size - dot) / 2
        dot_y = nub_y + (self.nub_size - dot) / 2

        self.icon_dot = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(dot_x, dot_y),
            size=(dot, dot),
            color=juice
        )

    def wiggle_icon(self):
        pize = self.size
        juice = self.lerp_col(self.track_off_col, self.track_on_col, self.anim_t)
        blob = self.lerp_col(self.thumb_off_col, self.thumb_on_col, self.anim_t)
        nub_x = self.lerp(self.nub_lo, self.nub_hi, self.anim_t)
        nub_y = (pize[1] - self.nub_size) / 2

        bui.imagewidget(self.capsule_l, color=juice)
        bui.imagewidget(self.capsule_r, color=juice)
        bui.imagewidget(self.capsule_bar, color=juice)
        bui.imagewidget(
            self.thumb,
            position=(nub_x, nub_y),
            color=blob
        )

        dot = self.nub_size * 0.3
        dot_x = nub_x + (self.nub_size - dot) / 2
        dot_y = nub_y + (self.nub_size - dot) / 2

        bui.imagewidget(
            self.icon_dot,
            position=(dot_x, dot_y),
            size=(dot, dot),
            color=juice
        )

class SeekBar(Widget):
    """
    A bar you can tap/drag to jump to a position

    parent: The current container
    size: How big the bar is (very wide switch basically)
    position: Where it sits
    value: 0.0 to 1.0, where the thumb starts
    segments: How many invisible click sensors to slice the bar into
    on_seek: Called with 0.0-1.0 when a sensor is clicked
    """
    def __init__(
        self,
        parent: bui.Widget,
        size: tuple[float, float] = (400,20),
        position: tuple[float, float] = (0,0),
        value: float = 0.0,
        segments: int = 40,
        color: tuple[float, float, float] = (1,1,1),
        on_seek: Callable[[float], None] | None = None
    ):
        # export
        super().__init__()
        self.parent = parent
        self.size = size
        self.value = value
        self.color = color
        self.on_seek = on_seek
        # root
        self.root = bui.containerwidget(
            parent=parent,
            size=size,
            background=False,
            position=position
        )
        # border
        pize = self.size
        border_col = (0.05,0.05,0.05)
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(0,0),
            size=(pize[1],pize[1]),
            color=border_col
        )
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(pize[0]-pize[1],0),
            size=(pize[1],pize[1]),
            color=border_col
        )
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=border_col,
            position=(pize[1]/2,0),
            size=(pize[0]-pize[1],pize[1])
        )
        # empty (inset grey space between border and fill)
        rim = pize[1] * 0.12
        chunk = (pize[0]-rim*2, pize[1]-rim*2)
        chunk_y = rim
        empty_col = (0.55,0.55,0.55)
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(rim,chunk_y),
            size=(chunk[1],chunk[1]),
            color=empty_col
        )
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(rim+chunk[0]-chunk[1],chunk_y),
            size=(chunk[1],chunk[1]),
            color=empty_col
        )
        self.track = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=empty_col,
            position=(rim+chunk[1]/2,chunk_y),
            size=(chunk[0]-chunk[1],chunk[1])
        )
        # fill
        self.rim = rim
        self.chunk = chunk
        self.chunk_y = chunk_y
        self.cap_l = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(rim,chunk_y),
            size=(chunk[1],chunk[1]),
            color=self.color
        )
        self.fill = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=self.color,
            position=(rim+chunk[1]/2,chunk_y),
            size=(max(0.0,chunk[0]*self.value-chunk[1]/2),chunk[1])
        )
        # thumb (the classic big circle showing this is clickable)
        self.thumb_size = pize[1] * 1.5
        self.thumb = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=self.thumb_pos(self.value),
            size=(self.thumb_size,self.thumb_size),
            color=border_col
        )
        # sensors
        self.blip_count = segments
        self.blip_w = size[0] / segments
        self.blips = []
        for i in range(segments):
            blip = bui.buttonwidget(
                parent=self.root,
                texture=bui.gettexture('empty'),
                enable_sound=False,
                label='',
                size=(self.blip_w, size[1]),
                position=(i*self.blip_w, 0),
                on_activate_call=bui.CallPartial(self.seek, i)
            )
            self.blips.append(blip)

    def thumb_pos(self, value):
        pize = self.size
        cx = pize[1]/2 + (pize[0]-pize[1])*value
        cy = pize[1]/2
        return (
            cx - self.thumb_size/2,
            cy - self.thumb_size/2
        )

    def seek(self, blip_indx):
        t = (blip_indx + 0.5) / self.blip_count
        self.set_value(t)
        if self.on_seek:
            self.on_seek(t)

    def set_value(self, value):
        self.value = value
        chunk = self.chunk
        bui.imagewidget(
            self.fill,
            size=(max(0.0,chunk[0]*value-chunk[1]/2), chunk[1])
        )
        bui.imagewidget(
            self.thumb,
            position=self.thumb_pos(value)
        )

class ProgressBar(Widget):
    """
    A pill-shaped bar that shows progress, no touch input

    parent: The current container
    size: How big the bar is (very wide switch basically)
    position: Where it sits
    value: 0.0 to 1.0, how full it is (ignored if indeterminate)
    indeterminate: If True, a Material-style breathing chunk loops instead
    """
    def __init__(
        self,
        parent: bui.Widget,
        size: tuple[float, float] = (400,20),
        position: tuple[float, float] = (0,0),
        value: float = 0.0,
        indeterminate: bool = False,
        color: tuple[float, float, float] = (1,1,1)
    ):
        # export
        super().__init__()
        self.parent = parent
        self.size = size
        self.value = value
        self.indeterminate = indeterminate
        self.color = color
        # root
        self.root = bui.containerwidget(
            parent=parent,
            size=size,
            background=False,
            position=position
        )
        # border
        pize = self.size
        border_col = (0.05,0.05,0.05)
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(0,0),
            size=(pize[1],pize[1]),
            color=border_col
        )
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(pize[0]-pize[1],0),
            size=(pize[1],pize[1]),
            color=border_col
        )
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=border_col,
            position=(pize[1]/2,0),
            size=(pize[0]-pize[1],pize[1])
        )
        # empty (inset grey space between border and fill)
        rim = pize[1] * 0.12
        chunk = (pize[0]-rim*2, pize[1]-rim*2)
        chunk_y = rim
        empty_col = (0.55,0.55,0.55)
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(rim,chunk_y),
            size=(chunk[1],chunk[1]),
            color=empty_col
        )
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(rim+chunk[0]-chunk[1],chunk_y),
            size=(chunk[1],chunk[1]),
            color=empty_col
        )
        self.track = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=empty_col,
            position=(rim+chunk[1]/2,chunk_y),
            size=(chunk[0]-chunk[1],chunk[1])
        )
        # fill
        self.rim = rim
        self.chunk = chunk
        self.chunk_y = chunk_y
        self.cap_l = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(rim,chunk_y),
            size=(chunk[1],chunk[1]),
            color=self.color,
            opacity=0.0 if self.indeterminate else 1.0
        )
        chunk_t = 0.0 if self.indeterminate else self.value
        self.fill = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=self.color,
            position=(rim+chunk[1]/2,chunk_y),
            size=(max(0.0,chunk[0]*chunk_t-chunk[1]/2),chunk[1])
        )
        # chunk (indeterminate only, the edge caps that ride the
        # wave's tail and head edges)
        self.wave_l = None
        self.wave_r = None
        self.wave_h = None
        if self.indeterminate:
            self.wave_l = bui.imagewidget(
                parent=self.root,
                texture=bui.gettexture('circle'),
                position=(rim,chunk_y),
                size=(chunk[1],chunk[1]),
                color=self.color,
                opacity=1.0
            )
            self.wave_r = bui.imagewidget(
                parent=self.root,
                texture=bui.gettexture('circle'),
                position=(rim+chunk[0]-chunk[1],chunk_y),
                size=(chunk[1],chunk[1]),
                color=self.color,
                opacity=0.0
            )
            self.wave_h = bui.imagewidget(
                parent=self.root,
                texture=bui.gettexture('circle'),
                position=(rim,chunk_y),
                size=(chunk[1],chunk[1]),
                color=self.color,
                opacity=0.0
            )
        # finally
        self.anim_timer = None
        if self.indeterminate:
            self.anim_indx = 0
            self.anim_timer = bui.AppTimer(
                1 / 60, self.anim_step, repeat=True
            )

    def set_value(self, value):
        self.value = value
        chunk = self.chunk
        bui.imagewidget(
            self.fill,
            size=(max(0.0,chunk[0]*value-chunk[1]/2), chunk[1])
        )

    def anim_step(self):
        if not self: return
        rim = self.rim
        chunk = self.chunk
        chunk_y = self.chunk_y
        # radius of the rounded caps, in inner-chunk space, so the
        # square fill texture's corners never poke past the round
        # ends: travel is clamped inward by this much on both sides
        radius = chunk[1] / 2

        self.anim_indx += 1
        loop = 100
        t = (self.anim_indx % loop) / loop

        # head races out ahead, tail chases and eats it, so the wave
        # grows then shrinks as it slides across, like the material
        # indeterminate spec (google sign-in nougat bars, but material)
        head_t = self.ease_out(min(1.0, t*1.6))
        tail_t = self.ease_out(max(0.0, (t-0.35)*1.55))

        head = self.lerp(0.0, 1.0, head_t)
        tail = self.lerp(0.0, 1.0, tail_t)
        head = max(head, tail)

        # map 0..1 onto the inset travel range instead of the full
        # chunk width, so head/tail never cross into the cap circles
        span = chunk[0] - radius*2
        head_px = rim + radius + span*head
        tail_px = rim + radius + span*tail
        w = max(0.0, head_px-tail_px)
        # once the fill would shrink down to (or past) a square, the
        # two edge caps already fully cover that space - so don't let
        # it shrink further, just cut it instantly with no animation
        w_drawn = w if w > chunk[1] else 0.0

        bui.imagewidget(
            self.fill,
            position=(tail_px,chunk_y),
            size=(w_drawn,chunk[1])
        )
        # left cap: stays put covering the seam until the tail
        # actually lifts off the left edge, so there's no gap before
        # the bar starts moving
        bui.imagewidget(
            self.wave_l,
            opacity=1.0 if tail <= 0.0 else 0.0
        )
        # right cap: sticks to the fill's own LEFT (tail) edge the
        # whole time it's moving, offset inward by half its own width
        # so it sits centered on that edge - this is the edge that
        # touches the right wall last, so it rides the whole trip
        right_wall = rim + chunk[0] - radius
        cap_x = min(tail_px, right_wall) - radius
        # fades out instead of hard-cutting: full life is the same
        # half-hold window as before, but the last chunk of it eases
        # opacity down to 0 rather than snapping
        hold_start = 0.625
        hold_end = 1.0
        hold_mid = hold_start + (hold_end - hold_start) / 2 + 0.072
        fade_span = 0.08
        fade_t = 1.0
        if t >= hold_mid - fade_span:
            fade_t = max(0.0, (hold_mid - t) / fade_span)
        alpha = fade_t if w > 0.0 else 0.0
        bui.imagewidget(
            self.wave_r,
            position=(cap_x, chunk_y),
            opacity=alpha
        )
        # head cap: same idea, but rides the fill's own RIGHT (head)
        # edge instead - same inward offset, same fade-out behaviour
        left_wall = rim + radius
        cap_h_x = max(head_px, left_wall) - radius
        alpha_h = fade_t if w > 0.0 else 0.0
        bui.imagewidget(
            self.wave_h,
            position=(cap_h_x, chunk_y),
            opacity=alpha_h
        )

class DemoWindow:
    def __init__(self, src=None):
        # root
        y = 310
        self.parent = bui.get_special_widget(
            'overlay_stack'
        )
        self.root = bui.containerwidget(
            parent=self.parent,
            transition=(
                src
                and 'in_scale'
                or 'in_left'
            ),
            size=(600,y),
            scale_origin_stack_offset=(
                src and
                src.get_screen_space_center()
                or (0,0)
            ),
            color=(1.2,1.2,1.2)
        )
        # close
        bui.containerwidget(
            self.root,
            cancel_button=(
                bui.buttonwidget(
                    parent=self.root,
                    size=(50,50),
                    position=(50,y-75),
                    label=bui.charstr(
                        bui.SpecialChar.CLOSE
                    ),
                    on_activate_call=bui.CallPartial(
                        bui.containerwidget,
                        self.root,
                        transition='out_scale'
                    ),
                    color=(1.2,1.2,1.2),
                    textcolor=(0,0,0)
                )
            )
        )
        # title
        bui.textwidget(
            parent=self.root,
            position=(50,y-75),
            size=(500,50),
            text='bauiv1x',
            h_align='center',
            v_align='center',
            scale=2,
            flatness=-2,
            color=(0,0,0)
        )
        # android
        y -= 150
        self.android_btn = bui.buttonwidget(
            parent=self.root,
            position=(50,y),
            size=(500,50),
            label='Android',
            color=(1,1,1),
            textcolor=(0,0,0),
            on_activate_call=self.android_demo
        )
        # windows
        y -= 60
        bui.buttonwidget(
            parent=self.root,
            position=(50,y),
            size=(500,50),
            label='Windows',
            color=(1,1,1),
            textcolor=(0,0,0),
            on_activate_call=self.windows_demo
        )
        # ios
        y -= 60
        bui.buttonwidget(
            parent=self.root,
            position=(50,y),
            size=(500,50),
            label='IOS',
            color=(1,1,1),
            textcolor=(0,0,0),
            on_activate_call=self.ios_demo
        )

    def android_demo(self):
        # bye
        bui.containerwidget(
            self.root,
            transition='out_left'
        )
        y = 600
        # root
        self.root = bui.containerwidget(
            parent=bui.get_special_widget(
                'overlay_stack'
            ),
            transition='in_scale',
            size=(600,y),
            scale_origin_stack_offset=(
                self.android_btn.get_screen_space_center()
            ),
            color=(1.2,1.2,1.2)
        )
        # close
        bui.containerwidget(
            self.root,
            cancel_button=(
                bui.buttonwidget(
                    parent=self.root,
                    size=(50,50),
                    position=(50,y-75),
                    label=bui.charstr(
                        bui.SpecialChar.BACK
                    ),
                    on_activate_call=lambda: (
                        bui.containerwidget(
                            self.root,
                            transition='out_scale'
                       ), DemoWindow()
                    ),
                    color=(1.2,1.2,1.2),
                    textcolor=(0,0,0)
                )
            )
        )
        # title
        bui.textwidget(
            parent=self.root,
            position=(50,y-75),
            size=(500,50),
            text='Android',
            h_align='center',
            v_align='center',
            scale=2,
            flatness=-2,
            color=(0,0,0)
        )
        # snackbar
        y -= 150
        self.android_btn = bui.buttonwidget(
            parent=self.root,
            position=(50,y),
            size=(500,50),
            label='SnackBar',
            color=(1,1,1),
            textcolor=(0,0,0),
            on_activate_call=self.show_snackbar,
            enable_sound=False
        )
        # switch
        y -= 70
        size = (80,50)
        lip = 50
        rip = 550
        goo = rip - lip - size[0]
        blorp = 5
        gap = goo / (blorp - 1)
        self.switch_widget = Switch(
            parent=self.root,
            position=(lip + gap*0, y),
            size=size
        )
        self.switch_widget_2 = Switch(
            parent=self.root,
            position=(lip + gap*1, y),
            size=size,
            style=Switch.Style.MATERIAL
        )
        self.switch_widget_3 = Switch(
            parent=self.root,
            position=(lip + gap*2, y),
            size=size,
            style=Switch.Style.SPLIT
        )
        self.switch_widget_4 = Switch(
            parent=self.root,
            position=(lip + gap*3, y),
            size=size,
            style=Switch.Style.M3
        )
        self.switch_widget_5 = Switch(
            parent=self.root,
            position=(lip + gap*4, y),
            size=size,
            style=Switch.Style.ICON
        )
        # seekbar
        y -= 70
        self.seekbar_widget = SeekBar(
            parent=self.root,
            position=(50,y),
            size=(500,20),
            value=0.3
        )
        # progress
        y -= 50
        self.progress_widget = ProgressBar(
            parent=self.root,
            position=(50,y),
            size=(500,20),
            indeterminate=True
        )
        # progress2
        y -= 50
        self.progress_widget_2 = ProgressBar(
            parent=self.root,
            position=(50,y),
            size=(500,20),
            value=0.6
        )

    def show_snackbar(self):
        bui.getsound('deek').play()
        if (
            (snack:=getattr(self,'snackbar',None))
            and not snack.transitioning_out
        ):
            snack.dismiss()
            return
        self.snackbar = SnackBar(
            parent=self.root,
            text='This is a SnackBar! Press the button to dismiss it.',
            action_label='OKAY',
            action_callback=lambda: (
                self.snackbar.dismiss()
                or bui.getsound('deek').play()
            )
        )

    def windows_demo(self):
        # bye
        bui.containerwidget(
            self.root,
            transition='out_left'
        )
        # root
        y = 600
        self.root = bui.containerwidget(
            parent=bui.get_special_widget(
                'overlay_stack'
            ),
            transition='in_scale',
            size=(600,y),
            scale_origin_stack_offset=(
                self.android_btn.get_screen_space_center()
            ),
            color=(1.2,1.2,1.2)
        )
        # close
        bui.containerwidget(
            self.root,
            cancel_button=(
                bui.buttonwidget(
                    parent=self.root,
                    size=(50,50),
                    position=(50,y-75),
                    label=bui.charstr(
                        bui.SpecialChar.BACK
                    ),
                    on_activate_call=lambda: (
                        bui.containerwidget(
                            self.root,
                            transition='out_scale'
                       ), DemoWindow()
                    ),
                    color=(1.2,1.2,1.2),
                    textcolor=(0,0,0),
                )
            )
        )
        # title
        bui.textwidget(
            parent=self.root,
            position=(50,y-75),
            size=(500,50),
            text='Windows',
            h_align='center',
            v_align='center',
            scale=2,
            flatness=-2,
            color=(0,0,0)
        )

    def ios_demo(self):
        # bye
        bui.containerwidget(
            self.root,
            transition='out_left'
        )
        # root
        y = 600
        self.root = bui.containerwidget(
            parent=bui.get_special_widget(
                'overlay_stack'
            ),
            transition='in_scale',
            size=(600,y),
            scale_origin_stack_offset=(
                self.android_btn.get_screen_space_center()
            ),
            color=(1.2,1.2,1.2)
        )
        # close
        bui.containerwidget(
            self.root,
            cancel_button=(
                bui.buttonwidget(
                    parent=self.root,
                    size=(50,50),
                    position=(50,y-75),
                    label=bui.charstr(
                        bui.SpecialChar.BACK
                    ),
                    on_activate_call=lambda: (
                        bui.containerwidget(
                            self.root,
                            transition='out_scale'
                       ), DemoWindow()
                    ),
                    color=(1.2,1.2,1.2),
                    textcolor=(0,0,0),
                )
            )
        )
        # title
        bui.textwidget(
            parent=self.root,
            position=(50,y-75),
            size=(500,50),
            text='IOS',
            h_align='center',
            v_align='center',
            scale=2,
            flatness=-2,
            color=(0,0,0)
        )

# ba_meta require api 9
# ba_meta export babase.Plugin
class Demo(bui.Plugin):
    def has_settings_ui(self):
        return True
    def show_settings_ui(self, src):
        DemoWindow(src)
    def on_app_running(self):
        bui.apptimer(1,DemoWindow)
