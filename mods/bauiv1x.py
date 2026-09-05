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
        self.anim_start = 0
        self.anim_end = self.size[1]*1.63
        self.anim_fire()

    def standby(self):
        self.anim_timer = bui.AppTimer(
            self.duration, self.dismiss
        )

    def anim_out(self):
        self.anim_start = self.size[1]*1.63
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
            self.anim_finish()
            return

        t = self.anim_indx / self.anim_duration
        eased_t = self.ease_out(t)
        anim_buff = self.lerp(self.anim_start, self.anim_end, eased_t)

        bui.containerwidget(
            self.root,
            position=(
                self.root_x,
                self.root_y+anim_buff
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
        col = self.color
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
            size=(y,y),
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
        self.switch_widget = Switch(
            parent=self.root,
            position=(550-size[0],y),
            size=size
        )
        self.switch_widget_2 = Switch(
            parent=self.root,
            position=(550-size[0]*2-20,y),
            size=size,
            style=Switch.Style.MATERIAL
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
