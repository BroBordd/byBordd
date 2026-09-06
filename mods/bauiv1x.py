# Copyright 2026 BrotherBoard
# Free for everyone to use and share
# Discord >> @BrotherBoard

"""
bauiv1x v1.0 - Ballistica UI Extended

Experimental.
"""

import bauiv1 as bui

from enum import IntEnum

class Widget:
    """
    A bauiv1x Widget, used as subclass for all widgets

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
    action_label: Action button label
    action_callback: Action button call
    duration: Wait before dismiss
    """
    def __init__(
        self,
        parent: bui.Widget,
        text: str,
        action_label: str | None = None,
        action_callback: 'Callable | None' = None,
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

class SidePane(Widget):
    """
    A sliding navigation drawer.

    parent: The current container
    title: Top header label
    text: Optional description
    width: Pane width
    color: Pane bg color
    """

    def __init__(
        self,
        parent: bui.Widget,
        title: str = 'SidePane',
        text: str | None = None,
        width: float = 300,
        color: tuple[float, float, float] = (0.0, 0.0, 0.0)
    ):
        # probe
        cent = parent.get_screen_space_center()
        virt = bui.get_virtual_screen_size()
        that = (hack := bui.textwidget(
            parent=parent,
            size=(0, 0)
        )).get_screen_space_center()
        hack.delete()
        pize = (
            (cent[0] - that[0]) * 2,
            (cent[1] - that[1]) * 2
        )

        super().__init__()
        self.parent = parent
        self.color = color
        self.size = (width, virt[1])

        # position
        base_x = -virt[0] / 2 + pize[0] / 2 - cent[0]
        base_y = -virt[1] / 2 + pize[1] / 2 - cent[1]

        self.root_x = base_x - self.size[0] * 1.5
        self.root_y = base_y

        # root
        self.root = bui.containerwidget(
            parent=parent,
            size=self.size,
            position=(self.root_x, self.root_y),
            background=False
        )

        # bleed
        mult = 1.9
        bgw = self.size[0] * mult
        blx = bgw - self.size[0]
        bly = self.size[1] * 0.25

        self.background = bui.imagewidget(
            parent=self.root,
            size=(
                bgw,
                self.size[1] + bly * 2
            ),
            position=(
                -blx,
                -bly
            ),
            texture=bui.gettexture('white'),
            color=self.color
        )

        # border
        bui.imagewidget(
            parent=self.root,
            size=(1.5, self.size[1] + bly * 2),
            position=(self.size[0], -bly),
            texture=bui.gettexture('white'),
            color=(0.22, 0.22, 0.22)
        )

        # header
        top_y = self.size[1] - 46
        csz = 32

        # scale
        tsc = 1.4
        tmw = self.size[0] - csz - 14
        tox = (tsc - 1.0) * (tmw / 2.0)

        # title
        bui.textwidget(
            parent=self.root,
            position=(tox, top_y),
            size=(tmw, 36),
            text=title,
            scale=tsc,
            color=(1, 1, 1),
            v_align='center',
            maxwidth=tmw
        )

        # close
        bui.buttonwidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=(0.12, 0.12, 0.12),
            textcolor=(1, 1, 1),
            enable_sound=False,
            size=(csz, csz),
            position=(self.size[0] - csz - 8, top_y + 2),
            label=bui.charstr(bui.SpecialChar.CLOSE),
            on_activate_call=self.dismiss
        )

        curr_y = top_y - 6

        # desc
        if text:
            curr_y -= 30
            dsc = 0.75
            dw = self.size[0] - 8
            dox = (dsc - 1.0) * (dw / 2.0)

            bui.textwidget(
                parent=self.root,
                position=(dox, curr_y),
                size=(dw, 28),
                text=text,
                scale=dsc,
                color=(0.6, 0.6, 0.6),
                v_align='top',
                maxwidth=dw
            )

        # separator
        curr_y -= 12
        bui.imagewidget(
            parent=self.root,
            size=(self.size[0], 1.5),
            position=(0, curr_y),
            texture=bui.gettexture('white'),
            color=(0.22, 0.22, 0.22)
        )

        # expose
        self.margin = 16
        self.content_w = self.size[0] - self.margin * 2
        self.curr_y = curr_y

        # lifecycle
        self.life_timer = bui.AppTimer(
            0.01, lambda: (
                not self and self.delete()
            ), repeat=True
        )
        self.anim_finish = None
        self.anim_in()

    def anim_in(self):
        self.anim_buff = 0.0
        self.anim_start = 0.0
        self.anim_end = self.size[0] * 1.5
        self.anim_fire()

    def anim_out(self):
        self.anim_start = self.anim_buff
        self.anim_end = 0.0
        self.anim_fire()

    def anim_fire(self):
        self.anim_duration = 20
        self.anim_indx = 0
        self.anim_timer = bui.AppTimer(
            1 / 60, self.anim_step, repeat=True
        )

    def anim_step(self):
        if not self:
            return
        self.anim_indx += 1
        if self.anim_indx > self.anim_duration:
            self.anim_timer = None
            self.anim_buff = self.anim_end
            if self.anim_finish:
                self.anim_finish()
            return

        t = self.anim_indx / self.anim_duration
        eased_t = self.ease_out(t)
        self.anim_buff = self.lerp(self.anim_start, self.anim_end, eased_t)

        bui.containerwidget(
            self.root,
            position=(
                self.root_x + self.anim_buff,
                self.root_y
            )
        )

    def press(self, callback):
        bui.getsound('deek').play()
        if callback:
            callback()
        self.dismiss()

    def dismiss(self):
        if self.transitioning_out:
            return
        bui.getsound('deek').play()
        self.transitioning_out = True
        self.anim_finish = self.delete
        self.anim_out()

    def delete(self):
        self.anim_timer = None
        self.life_timer = None
        self.root.delete()

class Dialog(Widget):
    """
    A modal dialog.

    parent: The current container
    title: Title bar text
    text: Body message
    action_label: Confirm button label
    action_callback: Confirm button call
    cancel_label: Cancel button label
    cancel_callback: Cancel button call
    color: Body color
    """

    # scale
    BG_SCALE_MIN = 0.85
    BG_SCALE_MAX = 1.0

    def __init__(
        self,
        parent: bui.Widget | None = None,
        title: str = 'Dialog',
        text: str = '',
        action_label: str = 'OK',
        action_callback: 'Callable | None' = None,
        cancel_label: str | None = 'Cancel',
        cancel_callback: 'Callable | None' = None,
        color: tuple[float, float, float] = (0.94, 0.94, 0.94)
    ):
        # layout
        pize = (420, 240)
        margin = 16
        titlebar_h = 36
        btn_size = (100, 32)
        btn_gap = 16
        icon_size = titlebar_h * 0.7

        # export
        super().__init__()
        self.parent = parent or bui.get_special_widget('overlay_stack')
        self.size = pize
        self.color = color

        # root
        self.root = bui.containerwidget(
            parent=self.parent,
            transition='none',
            size=pize,
            background=False
        )

        # body
        self.bg_pize = pize
        self.bg_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=pize,
            position=(0, 0),
            color=self.color,
            opacity=0.0
        )

        # border
        self.border_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(pize[0] + 2, pize[1] + 2),
            position=(-1, -1),
            color=(0.6, 0.6, 0.6),
            opacity=0.0
        )
        self.border_fill_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=pize,
            position=(0, 0),
            color=self.color,
            opacity=0.0
        )

        # titlebar
        titlebar_y = pize[1] - titlebar_h
        self.titlebar_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(pize[0], titlebar_h),
            position=(0, titlebar_y),
            color=(0.88, 0.88, 0.88),
            opacity=0.0
        )

        # icon
        icon_head_x = margin * 0.5
        icon_head_y = titlebar_y + (titlebar_h - icon_size) / 2
        self.icon_head_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(icon_size, icon_size),
            position=(icon_head_x, icon_head_y),
            color=(0.5, 0.5, 0.5),
            opacity=0.0
        )
        eye_size = icon_size * 0.16
        eye_y = icon_head_y + icon_size * 0.58
        eye_l_x = icon_head_x + icon_size * 0.22
        eye_r_x = icon_head_x + icon_size * 0.62
        self.icon_eye_l_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(eye_size, eye_size),
            position=(eye_l_x, eye_y),
            color=self.color,
            opacity=0.0
        )
        self.icon_eye_r_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(eye_size, eye_size),
            position=(eye_r_x, eye_y),
            color=self.color,
            opacity=0.0
        )
        mouth_w = icon_size * 0.55
        mouth_h = icon_size * 0.09
        mouth_x = icon_head_x + (icon_size - mouth_w) / 2
        mouth_y = icon_head_y + icon_size * 0.2
        self.icon_mouth_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(mouth_w, mouth_h),
            position=(mouth_x, mouth_y),
            color=self.color,
            opacity=0.0
        )

        # titlebar
        title_x = icon_head_x * 2 + icon_size - margin
        title_w = pize[0] - title_x - margin - titlebar_h
        self.title_col = (0.1, 0.1, 0.1)
        self.title_widget = bui.textwidget(
            parent=self.root,
            position=(title_x, titlebar_y),
            size=(title_w, titlebar_h),
            text=title,
            v_align='center',
            maxwidth=title_w - 8,
            scale=0.85,
            color=(*self.title_col, 0.0)
        )

        # close
        close_size = titlebar_h * 0.9
        close_inset = (titlebar_h - close_size) / 2
        self.close_textcol = (0.1, 0.1, 0.1)
        self.close_btn = bui.buttonwidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=(0.88, 0.88, 0.88),
            textcolor=(*self.close_textcol, 0.0),
            enable_sound=False,
            size=(close_size, close_size),
            position=(pize[0] - close_size - close_inset, titlebar_y + close_inset),
            label=bui.charstr(
                bui.SpecialChar.CLOSE
            ),
            on_activate_call=self.dismiss,
            opacity=0.0
        )

        # body
        body_top = titlebar_y
        body_bottom = btn_size[1] + margin*2
        self.body_col = (0.15, 0.15, 0.15)
        self.body_widget = bui.textwidget(
            parent=self.root,
            position=(margin, body_bottom),
            size=(pize[0] - margin*2, body_top - body_bottom),
            text=text,
            h_align='left',
            v_align='center',
            maxwidth=pize[0] - margin*2,
            color=(*self.body_col, 0.0)
        )

        # buttons
        btn_y = margin
        rip = pize[0] - margin

        self.cancel_btn = None
        if cancel_label:
            cancel_x = rip - btn_size[0]
            self.cancel_textcol = (1, 1, 1)
            self.cancel_btn = bui.buttonwidget(
                parent=self.root,
                texture=bui.gettexture('white'),
                color=(0.45, 0.45, 0.45),
                textcolor=(*self.cancel_textcol, 0.0),
                enable_sound=False,
                size=btn_size,
                position=(cancel_x, btn_y),
                label=cancel_label,
                on_activate_call=bui.CallPartial(
                    self.press, cancel_callback
                ),
                opacity=0.0
            )
            action_x = cancel_x - btn_gap - btn_size[0]
        else:
            action_x = rip - btn_size[0]

        self.action_textcol = (1, 1, 1)
        self.action_btn = bui.buttonwidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=(0.0, 0.0, 0.0),
            textcolor=(*self.action_textcol, 0.0),
            enable_sound=False,
            size=btn_size,
            position=(action_x, btn_y),
            label=action_label,
            on_activate_call=bui.CallPartial(
                self.press, action_callback
            ),
            opacity=0.0
        )

        # finally
        self.life_timer = bui.AppTimer(
            0.01, lambda: (
                not self and self.delete()
            ), repeat=True
        )
        self.anim_timer = None
        self.anim_in()

    def anim_in(self):
        # background
        self.anim_start = self.BG_SCALE_MIN
        self.anim_end = self.BG_SCALE_MAX
        self.anim_apply(self.anim_start)
        self.anim_fire()

    def anim_out(self):
        self.anim_start = self.BG_SCALE_MAX
        self.anim_end = self.BG_SCALE_MIN
        self.anim_fire()

    def anim_fire(self):
        self.anim_duration = 10
        self.anim_indx = 0
        self.anim_timer = bui.AppTimer(
            1 / 60, self.anim_step, repeat=True
        )

    def anim_step(self):
        if not self.root.exists():
            self.anim_timer = None
            return
        self.anim_indx += 1
        if self.anim_indx > self.anim_duration:
            self.anim_timer = None
            self.anim_apply(self.anim_end)
            if self.transitioning_out:
                self.delete()
            return

        t = self.anim_indx / self.anim_duration
        eased_t = self.ease_out(t)
        value = self.lerp(self.anim_start, self.anim_end, eased_t)
        self.anim_apply(value)

    def anim_apply(self, t):
        # background
        scale_span = self.BG_SCALE_MAX - self.BG_SCALE_MIN
        fade_t = (t - self.BG_SCALE_MIN) / scale_span if scale_span else 1.0
        fade_t = max(0.0, min(1.0, fade_t))

        bg_w = self.bg_pize[0] * t
        bg_h = self.bg_pize[1] * t
        extra_x = self.bg_pize[0] - bg_w
        extra_y = self.bg_pize[1] - bg_h
        bui.imagewidget(
            self.bg_widget,
            size=(bg_w, bg_h),
            position=(extra_x/2, extra_y/2),
            opacity=fade_t
        )
        # fade
        bui.imagewidget(self.border_widget, opacity=fade_t)
        bui.imagewidget(self.border_fill_widget, opacity=fade_t)
        bui.imagewidget(self.titlebar_widget, opacity=fade_t)
        bui.imagewidget(self.icon_head_widget, opacity=fade_t)
        bui.imagewidget(self.icon_eye_l_widget, opacity=fade_t)
        bui.imagewidget(self.icon_eye_r_widget, opacity=fade_t)
        bui.imagewidget(self.icon_mouth_widget, opacity=fade_t)
        bui.textwidget(self.title_widget, color=(*self.title_col, fade_t))
        bui.textwidget(self.body_widget, color=(*self.body_col, fade_t))
        bui.buttonwidget(
            self.close_btn,
            opacity=fade_t,
            textcolor=(*self.close_textcol, fade_t)
        )
        if self.cancel_btn:
            bui.buttonwidget(
                self.cancel_btn,
                opacity=fade_t,
                textcolor=(*self.cancel_textcol, fade_t)
            )
        bui.buttonwidget(
            self.action_btn,
            opacity=fade_t,
            textcolor=(*self.action_textcol, fade_t)
        )

    def press(self, callback):
        bui.getsound('deek').play()
        if callback:
            callback()
        self.dismiss()

    def dismiss(self):
        if self.transitioning_out:
            return
        bui.getsound('deek').play()
        self.transitioning_out = True
        self.anim_out()

    def delete(self):
        self.anim_timer = None
        self.life_timer = None
        self.root.delete()

class Notification(Widget):
    """
    A notification, bottom-right corner.

    parent: The current container
    title: Top title text
    text: Body text
    duration: Wait before dismiss
    action_label: Primary button label
    action_callback: Primary button call
    secondary_label: Secondary button label
    secondary_callback: Secondary button call
    """
    NOTIF_BTN_ALPHA = 0.15
    NOTIF_OPACITY = 0.55

    def __init__(
        self,
        parent: bui.Widget,
        title: str = 'Notification',
        text: str = 'This is a notification!\nPick a button below to dismiss it.',
        duration: float = 4,
        action_label: str | None = 'Dismiss',
        action_callback: 'Callable | None' = None,
        secondary_label: str | None = 'OK',
        secondary_callback: 'Callable | None' = None,
        color: tuple[float, float, float] = (0.94, 0.94, 0.94)
    ):
        # math
        cent = parent.get_screen_space_center()
        virt = bui.get_virtual_screen_size()
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
        self.color = color

        # size
        size = (360, 150)
        self.size = size

        # position
        self.root_x = virt[0]/2 + pize[0]/2 - size[0] - cent[0]
        self.root_y = -virt[1]/2 + pize[1]/2 - cent[1]

        # root
        self.root = bui.containerwidget(
            parent=parent,
            size=size,
            position=(self.root_x, self.root_y),
            background=False
        )

        # body
        self.bg_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=size,
            position=(0, 0),
            color=self.color,
            opacity=0.0
        )
        self.border_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(size[0]+2, size[1]+2),
            position=(-1, -1),
            color=(0.6, 0.6, 0.6),
            opacity=0.0
        )
        self.border_fill_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=size,
            position=(0, 0),
            color=self.color,
            opacity=0.0
        )

        # icon
        margin = 14
        icon_size = 22
        icon_x = margin * 0.5
        icon_y = size[1] - icon_size - margin * 0.7
        self.icon_head_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(icon_size, icon_size),
            position=(icon_x, icon_y),
            color=(0.5, 0.5, 0.5),
            opacity=0.0
        )
        eye_size = icon_size * 0.16
        eye_y = icon_y + icon_size * 0.58
        eye_l_x = icon_x + icon_size * 0.22
        eye_r_x = icon_x + icon_size * 0.62
        self.icon_eye_l_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(eye_size, eye_size),
            position=(eye_l_x, eye_y),
            color=self.color,
            opacity=0.0
        )
        self.icon_eye_r_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(eye_size, eye_size),
            position=(eye_r_x, eye_y),
            color=self.color,
            opacity=0.0
        )
        mouth_w = icon_size * 0.55
        mouth_h = icon_size * 0.09
        mouth_x = icon_x + (icon_size - mouth_w) / 2
        mouth_y = icon_y + icon_size * 0.2
        self.icon_mouth_widget = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(mouth_w, mouth_h),
            position=(mouth_x, mouth_y),
            color=self.color,
            opacity=0.0
        )

        # title
        title_x = icon_x * 2 + icon_size - margin
        title_w = size[0] - title_x - margin
        self.title_col = (0.1, 0.1, 0.1)
        self.title_widget = bui.textwidget(
            parent=self.root,
            position=(title_x, icon_y),
            size=(title_w, icon_size),
            text=title,
            v_align='center',
            maxwidth=title_w - 8,
            scale=0.8,
            color=(*self.title_col, 0.0)
        )

        # buttons
        btn_h = 32
        btn_row_gap = 24
        btn_y = margin * 0.7
        row_left = margin
        row_right = size[0] - margin
        row_w = row_right - row_left

        if action_label and secondary_label:
            btn_w = (row_w - btn_row_gap) / 2
            action_x = row_left
            secondary_x = row_left + btn_w + btn_row_gap
        else:
            btn_w = row_w
            action_x = row_left
            secondary_x = row_left
        btn_size = (btn_w, btn_h)

        self.action_btn = None
        if action_label:
            self.action_textcol = (0.1, 0.1, 0.1)
            self.action_btn = bui.buttonwidget(
                parent=self.root,
                texture=bui.gettexture('white'),
                color=(0.0, 0.0, 0.0),
                textcolor=(*self.action_textcol, 0.0),
                enable_sound=False,
                size=btn_size,
                position=(action_x, btn_y),
                label=action_label,
                on_activate_call=bui.CallPartial(
                    self.press, action_callback
                ),
                opacity=0.0
            )

        self.secondary_btn = None
        if secondary_label:
            self.secondary_textcol = (0.1, 0.1, 0.1)
            self.secondary_btn = bui.buttonwidget(
                parent=self.root,
                texture=bui.gettexture('white'),
                color=(0.0, 0.0, 0.0),
                textcolor=(*self.secondary_textcol, 0.0),
                enable_sound=False,
                size=btn_size,
                position=(secondary_x, btn_y),
                label=secondary_label,
                on_activate_call=bui.CallPartial(
                    self.press, secondary_callback
                ),
                opacity=0.0
            )

        # body
        body_top = icon_y - 4
        body_bottom = btn_size[1] + margin * 1.4
        self.body_col = (0.15, 0.15, 0.15)
        self.body_widget = bui.textwidget(
            parent=self.root,
            position=(margin, body_bottom),
            size=(size[0] - margin*2, body_top - body_bottom),
            text=text,
            h_align='left',
            v_align='center',
            maxwidth=size[0] - margin*2,
            color=(*self.body_col, 0.0)
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
        self.anim_start = 0.0
        self.anim_end = self.NOTIF_OPACITY
        self.anim_fire()

    def standby(self):
        self.anim_timer = bui.AppTimer(
            self.duration, self.dismiss
        )

    def anim_out(self):
        self.anim_start = self.NOTIF_OPACITY
        self.anim_end = 0.0
        self.anim_fire()

    def anim_fire(self):
        self.anim_duration = 10
        self.anim_indx = 0
        self.anim_timer = bui.AppTimer(
            1 / 60, self.anim_step, repeat=True
        )

    def anim_step(self):
        if not self: return
        self.anim_indx += 1
        if self.anim_indx > self.anim_duration:
            self.anim_timer = None
            self.anim_apply(self.anim_end)
            self.anim_finish()
            return

        t = self.anim_indx / self.anim_duration
        eased_t = self.ease_out(t)
        value = self.lerp(self.anim_start, self.anim_end, eased_t)
        self.anim_apply(value)

    def anim_apply(self, t):
        bui.imagewidget(self.bg_widget, opacity=t)
        bui.imagewidget(self.border_widget, opacity=t)
        bui.imagewidget(self.border_fill_widget, opacity=t)
        bui.imagewidget(self.icon_head_widget, opacity=t)
        bui.imagewidget(self.icon_eye_l_widget, opacity=t)
        bui.imagewidget(self.icon_eye_r_widget, opacity=t)
        bui.imagewidget(self.icon_mouth_widget, opacity=t)
        # title
        title_t = min(1.0, t * 2)
        bui.textwidget(self.title_widget, color=(*self.title_col, title_t))
        bui.textwidget(self.body_widget, color=(*self.body_col, t))

        # buttons
        bg_ratio = min(1.0, t / self.NOTIF_OPACITY) if self.NOTIF_OPACITY else t
        btn_bg_t = bg_ratio * self.NOTIF_BTN_ALPHA
        btn_text_t = bg_ratio
        if self.secondary_btn:
            bui.buttonwidget(
                self.secondary_btn,
                opacity=btn_bg_t,
                textcolor=(*self.secondary_textcol, btn_text_t)
            )
        if self.action_btn:
            bui.buttonwidget(
                self.action_btn,
                opacity=btn_bg_t,
                textcolor=(*self.action_textcol, btn_text_t)
            )

    def press(self, callback):
        bui.getsound('deek').play()
        if callback:
            callback()
        self.dismiss()

    def dismiss(self):
        if self.transitioning_out:
            return
        self.transitioning_out = True
        self.anim_finish = self.delete
        self.anim_out()

    def delete(self):
        self.anim_timer = None
        self.life_timer = None
        self.root.delete()

class Toast(Widget):
    """
    A Material-style toast capsule.

    parent: The current container
    text: Capsule text
    duration: Wait before dismiss
    color: Capsule background color
    """
    def __init__(
        self,
        parent: bui.Widget,
        text: str = 'This is a toast!',
        duration: float = 3,
        color: tuple[float, float, float] = (0.0, 0.0, 0.0)
    ):
        # math
        cent = parent.get_screen_space_center()
        virt = bui.get_virtual_screen_size()
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
        self.parent = parent
        self.duration = duration
        self.color = color

        # size
        text_w = bui.get_string_width(text, True)
        if text_w <= 0 and text:
            text_w = len(text) * 30

        pad_x = 40
        height = 50
        maxwidth = virt[0] * 0.8
        width = min(maxwidth, text_w + pad_x * 2)
        size = (width, height)
        self.size = size

        # position
        base_x = -virt[0]/2 + pize[0]/2 - cent[0]
        self.root_x = base_x + (virt[0] - width) / 2
        self.root_y = -virt[1]/2 + pize[1]/2 - cent[1]

        # root
        self.root = bui.containerwidget(
            parent=parent,
            size=size,
            position=(self.root_x, self.root_y),
            background=False
        )

        # capsule
        self.cap_l = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(0, 0),
            size=(height, height),
            color=self.color,
            opacity=0.0
        )
        self.cap_r = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=(width - height, 0),
            size=(height, height),
            color=self.color,
            opacity=0.0
        )
        self.body_widget_bg = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            color=self.color,
            position=(height / 2, 0),
            size=(width - height, height),
            opacity=0.0
        )

        # text
        self.text_col = (1, 1, 1)
        self.text_widget = bui.textwidget(
            parent=self.root,
            position=(0, 0),
            size=size,
            text=text,
            h_align='center',
            v_align='center',
            maxwidth=max(1.0, width - pad_x * 2),
            color=(*self.text_col, 0.0)
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
        self.anim_start = 0.0
        self.anim_end = 1.0
        self.anim_fire()

    def standby(self):
        self.anim_timer = bui.AppTimer(
            self.duration, self.dismiss
        )

    def anim_out(self):
        self.anim_start = 1.0
        self.anim_end = 0.0
        self.anim_fire()

    def anim_fire(self):
        self.anim_duration = 10
        self.anim_indx = 0
        self.anim_timer = bui.AppTimer(
            1 / 60, self.anim_step, repeat=True
        )

    def anim_step(self):
        if not self: return
        self.anim_indx += 1
        if self.anim_indx > self.anim_duration:
            self.anim_timer = None
            self.anim_apply(self.anim_end)
            self.anim_finish()
            return

        t = self.anim_indx / self.anim_duration
        eased_t = self.ease_out(t)
        value = self.lerp(self.anim_start, self.anim_end, eased_t)
        self.anim_apply(value)

    def anim_apply(self, t):
        bui.imagewidget(self.cap_l, opacity=t)
        bui.imagewidget(self.cap_r, opacity=t)
        bui.imagewidget(self.body_widget_bg, opacity=t)
        bui.textwidget(self.text_widget, color=(*self.text_col, t))

    def dismiss(self):
        if self.transitioning_out:
            return
        self.transitioning_out = True
        self.anim_finish = self.delete
        self.anim_out()

    def delete(self):
        self.anim_timer = None
        self.life_timer = None
        self.root.delete()

class Switch(Widget):
    """
    A toggle switch with a couple different visual styles

    parent: The current container
    size: Switch size
    position: Where it sits
    value: Starting on/off state
    style: Visual style
    color: Accent color when on
    on_value_change: Toggle callback
    """
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
        on_value_change: 'Callable[[bool], None] | None' = None
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
        # style
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

class Checkbox(Widget):
    """
    A checkbox with a couple different fill animations

    parent: The current container
    size: Box size
    position: Where it sits
    value: Starting checked state
    style: Fill style
    color: Fill color when checked
    on_value_change: Toggle callback
    """
    class Style(IntEnum):
        SQUARE = 0
        RADIAL = 1
        SWEEP_H = 2
        SWEEP_V = 3
        STAIRS = 4
        BLINDS = 5
        PINWHEEL = 6
        PULSE = 7
        COMET = 8

    def __init__(
        self,
        parent: bui.Widget,
        size: tuple[float, float] = (40,40),
        position: tuple[float, float] = (0,0),
        value: bool = False,
        style: int = Style.SQUARE,
        color: tuple[float, float, float] = (0,0,0),
        on_value_change: 'Callable[[bool], None] | None' = None
    ):
        # export
        super().__init__()
        self.parent = parent
        self.size = size
        self.value = value
        self.anim_t = 1.0 if value else 0.0
        self.style = Checkbox.Style(style)
        self.color = color
        self.on_value_change = on_value_change
        # against
        self.against = tuple(1.0 - c for c in color)
        # root
        self.root = bui.containerwidget(
            parent=parent,
            size=size,
            background=False,
            position=position
        )
        self.thick = size[0] * 0.09
        self.outer = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=size,
            position=(0,0),
            color=(0,0,0)
        )
        # empty
        self.inner_size = (size[0]-self.thick*2, size[1]-self.thick*2)
        bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=self.inner_size,
            position=(self.thick, self.thick),
            color=self.against
        )
        # fill
        getattr(self, f'wear_{self.style.name.lower()}')()
        # check
        self.has_check = self.style in (
            Checkbox.Style.SWEEP_H, Checkbox.Style.SWEEP_V
        )
        self.dots = []
        if self.has_check:
            res = 40
            self.pts = [(0.22,0.55),(0.42,0.30),(0.80,0.68)]
            self.dot = size[0] * 0.09
            for i in range(res):
                t = i / (res-1)
                seg = t * (len(self.pts)-1)
                a = self.pts[int(seg)]
                b = self.pts[min(int(seg)+1, len(self.pts)-1)]
                f = seg - int(seg)
                px = self.lerp(a[0], b[0], f)
                py = self.lerp(a[1], b[1], f)
                dx = px * size[0] - self.dot/2
                dy = py * size[1] - self.dot/2
                d = bui.imagewidget(
                    parent=self.root,
                    texture=bui.gettexture('circle'),
                    position=(dx, dy),
                    size=(self.dot, self.dot),
                    color=self.against,
                    opacity=self.anim_t
                )
                self.dots.append(d)
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
        base = 6 if self.value else 10
        slow_mults = {
            Checkbox.Style.PINWHEEL: 2.5,
            Checkbox.Style.COMET: 2.5,
        }
        mult = slow_mults.get(self.style, 1)
        self.anim_duration = int(base * mult)
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
        if self.has_check:
            for d in self.dots:
                bui.imagewidget(d, opacity=self.anim_t)

    # square
    def wear_square(self):
        size = self.size
        d = self.lerp(0.0, self.inner_size[0] * 0.6, self.anim_t)
        self.fill = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(d, d),
            position=(
                size[0]/2 - d/2,
                size[1]/2 - d/2
            ),
            color=self.color
        )

    def wiggle_square(self):
        size = self.size
        d = self.lerp(0.0, self.inner_size[0] * 0.6, self.anim_t)
        bui.imagewidget(
            self.fill,
            size=(d, d),
            position=(
                size[0]/2 - d/2,
                size[1]/2 - d/2
            )
        )

    # stairs
    def wear_stairs(self):
        n = 4
        p = self.anim_t if self.value else 1.0 - self.anim_t
        step_w = self.inner_size[0] / n
        step_h = self.inner_size[1] / n
        self.stairs = []
        for i in range(n):
            lo = i / n
            hi = (i + 1) / n
            local_t = min(1.0, max(0.0, (p - lo) / (hi - lo)))
            if not self.value:
                local_t = 1.0 - local_t
            h = step_h * (i + 1) * local_t
            widget = bui.imagewidget(
                parent=self.root,
                texture=bui.gettexture('white'),
                size=(step_w, h),
                position=(
                    self.thick + step_w * i,
                    self.thick
                ),
                color=self.color
            )
            self.stairs.append(widget)

    def wiggle_stairs(self):
        n = 4
        p = self.anim_t if self.value else 1.0 - self.anim_t
        step_w = self.inner_size[0] / n
        step_h = self.inner_size[1] / n
        for i, widget in enumerate(self.stairs):
            lo = i / n
            hi = (i + 1) / n
            local_t = min(1.0, max(0.0, (p - lo) / (hi - lo)))
            if not self.value:
                local_t = 1.0 - local_t
            h = step_h * (i + 1) * local_t
            bui.imagewidget(
                widget,
                size=(step_w, h),
                position=(
                    self.thick + step_w * i,
                    self.thick
                )
            )

    # blinds
    def wear_blinds(self):
        n = 3
        p = self.anim_t if self.value else 1.0 - self.anim_t
        slat_h = self.inner_size[1] / n
        self.blinds = []
        for i in range(n):
            lo = i * 0.2
            hi = lo + 0.6
            local_t = min(1.0, max(0.0, (p - lo) / (hi - lo)))
            if not self.value:
                local_t = 1.0 - local_t
            w = self.inner_size[0] * local_t
            widget = bui.imagewidget(
                parent=self.root,
                texture=bui.gettexture('white'),
                size=(w, slat_h * 0.8),
                position=(
                    self.thick,
                    self.thick + slat_h * i + slat_h * 0.1
                ),
                color=self.color
            )
            self.blinds.append(widget)

    def wiggle_blinds(self):
        n = 3
        p = self.anim_t if self.value else 1.0 - self.anim_t
        slat_h = self.inner_size[1] / n
        for i, widget in enumerate(self.blinds):
            lo = i * 0.2
            hi = lo + 0.6
            local_t = min(1.0, max(0.0, (p - lo) / (hi - lo)))
            if not self.value:
                local_t = 1.0 - local_t
            w = self.inner_size[0] * local_t
            bui.imagewidget(
                widget,
                size=(w, slat_h * 0.8),
                position=(
                    self.thick,
                    self.thick + slat_h * i + slat_h * 0.1
                )
            )

    # radial
    def wear_radial(self):
        size = self.size
        d = self.lerp(0.0, self.inner_size[0], self.anim_t)
        self.fill = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            size=(d, d),
            position=(
                size[0]/2 - d/2,
                size[1]/2 - d/2
            ),
            color=self.color
        )

    def wiggle_radial(self):
        size = self.size
        d = self.lerp(0.0, self.inner_size[0], self.anim_t)
        bui.imagewidget(
            self.fill,
            size=(d, d),
            position=(
                size[0]/2 - d/2,
                size[1]/2 - d/2
            )
        )

    # sweep_h
    def wear_sweep_h(self):
        w = self.lerp(0.0, self.inner_size[0], self.anim_t)
        if self.value:
            x = self.thick
        else:
            x = self.thick + self.inner_size[0] - w
        self.fill = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(w, self.inner_size[1]),
            position=(x, self.thick),
            color=self.color
        )

    def wiggle_sweep_h(self):
        w = self.lerp(0.0, self.inner_size[0], self.anim_t)
        if self.value:
            x = self.thick
        else:
            x = self.thick + self.inner_size[0] - w
        bui.imagewidget(self.fill, size=(w, self.inner_size[1]), position=(x, self.thick))

    # sweep_v
    def wear_sweep_v(self):
        h = self.lerp(0.0, self.inner_size[1], self.anim_t)
        if self.value:
            y = self.thick + self.inner_size[1] - h
        else:
            y = self.thick
        self.fill = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('white'),
            size=(self.inner_size[0], h),
            position=(self.thick, y),
            color=self.color
        )

    def wiggle_sweep_v(self):
        h = self.lerp(0.0, self.inner_size[1], self.anim_t)
        if self.value:
            y = self.thick + self.inner_size[1] - h
        else:
            y = self.thick
        bui.imagewidget(self.fill, size=(self.inner_size[0], h), position=(self.thick, y))

    # pinwheel
    def wear_pinwheel(self):
        qw = self.inner_size[0] / 2
        qh = self.inner_size[1] / 2
        p = self.anim_t if self.value else 1.0 - self.anim_t
        self.quads = []
        origins = [
            (self.thick, self.thick + qh),
            (self.thick + qw, self.thick + qh),
            (self.thick + qw, self.thick),
            (self.thick, self.thick),
        ]
        for i, origin in enumerate(origins):
            lo = i / 4
            hi = lo + 0.4
            local_t = min(1.0, max(0.0, (p - lo) / (hi - lo)))
            if not self.value:
                local_t = 1.0 - local_t
            d = min(qw, qh) * local_t
            cx = origin[0] + qw/2
            cy = origin[1] + qh/2
            widget = bui.imagewidget(
                parent=self.root,
                texture=bui.gettexture('white'),
                size=(d, d),
                position=(cx - d/2, cy - d/2),
                color=self.color
            )
            self.quads.append(widget)

    def wiggle_pinwheel(self):
        qw = self.inner_size[0] / 2
        qh = self.inner_size[1] / 2
        p = self.anim_t if self.value else 1.0 - self.anim_t
        origins = [
            (self.thick, self.thick + qh),
            (self.thick + qw, self.thick + qh),
            (self.thick + qw, self.thick),
            (self.thick, self.thick),
        ]
        for i, (widget, origin) in enumerate(zip(self.quads, origins)):
            lo = i / 4
            hi = lo + 0.4
            local_t = min(1.0, max(0.0, (p - lo) / (hi - lo)))
            if not self.value:
                local_t = 1.0 - local_t
            d = min(qw, qh) * local_t
            cx = origin[0] + qw/2
            cy = origin[1] + qh/2
            bui.imagewidget(
                widget,
                size=(d, d),
                position=(cx - d/2, cy - d/2)
            )

    # pulse
    def wear_pulse(self):
        size = self.size
        p = self.anim_t
        cx, cy = size[0]/2, size[1]/2
        core_d = self.inner_size[0] * p
        self.pulse_core = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            size=(core_d, core_d),
            position=(cx - core_d/2, cy - core_d/2),
            color=self.color
        )
        glow_d = self.inner_size[0] * min(1.0, p * 1.25)
        glow_o = 0.35 * (1.0 - p) if 0.0 < p < 1.0 else 0.0
        self.pulse_glow = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            size=(glow_d, glow_d),
            position=(cx - glow_d/2, cy - glow_d/2),
            color=self.color,
            opacity=glow_o
        )

    def wiggle_pulse(self):
        size = self.size
        p = self.anim_t
        cx, cy = size[0]/2, size[1]/2
        core_d = self.inner_size[0] * p
        bui.imagewidget(
            self.pulse_core,
            size=(core_d, core_d),
            position=(cx - core_d/2, cy - core_d/2)
        )
        glow_d = self.inner_size[0] * min(1.0, p * 1.25)
        glow_o = 0.35 * (1.0 - p) if 0.0 < p < 1.0 else 0.0
        bui.imagewidget(
            self.pulse_glow,
            size=(glow_d, glow_d),
            position=(cx - glow_d/2, cy - glow_d/2),
            opacity=glow_o
        )

    # comet
    def wear_comet(self):
        size = self.size
        p = self.anim_t
        cx, cy = size[0]/2, size[1]/2
        d = self.inner_size[0] * p
        self.comet_fill = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            size=(d, d),
            position=(cx - d/2, cy - d/2),
            color=self.color,
            opacity=0.55
        )
        margin = self.inner_size[0] * 0.12
        corners = [
            (self.thick + margin, self.thick + margin),
            (self.thick + self.inner_size[0] - margin, self.thick + margin),
            (self.thick + self.inner_size[0] - margin, self.thick + self.inner_size[1] - margin),
            (self.thick + margin, self.thick + self.inner_size[1] - margin),
            (self.thick + margin, self.thick + margin),
        ]
        head_d = size[0] * 0.16
        self.comet_dots = []
        tails = 5
        for i in range(tails):
            spacing = 0.09
            tp = p - i * spacing
            tp = min(1.0, max(0.0, tp))
            leg = tp * 4
            leg_i = min(3, int(leg))
            leg_t = leg - leg_i
            a = corners[leg_i]
            b = corners[leg_i + 1]
            dd = head_d * (1.0 - i / tails * 0.6)
            dx = self.lerp(a[0], b[0], leg_t) - dd/2
            dy = self.lerp(a[1], b[1], leg_t) - dd/2
            visible = 0.0 < p < 1.0 and tp > 0.0
            widget = bui.imagewidget(
                parent=self.root,
                texture=bui.gettexture('circle'),
                size=(dd, dd),
                position=(dx, dy),
                color=self.color,
                opacity=(1.0 - i / tails * 0.8) if visible else 0.0
            )
            self.comet_dots.append(widget)

    def wiggle_comet(self):
        size = self.size
        p = self.anim_t
        cx, cy = size[0]/2, size[1]/2
        d = self.inner_size[0] * p
        bui.imagewidget(self.comet_fill, size=(d, d), position=(cx - d/2, cy - d/2))
        margin = self.inner_size[0] * 0.12
        corners = [
            (self.thick + margin, self.thick + margin),
            (self.thick + self.inner_size[0] - margin, self.thick + margin),
            (self.thick + self.inner_size[0] - margin, self.thick + self.inner_size[1] - margin),
            (self.thick + margin, self.thick + self.inner_size[1] - margin),
            (self.thick + margin, self.thick + margin),
        ]
        head_d = size[0] * 0.16
        tails = 5
        for i, widget in enumerate(self.comet_dots):
            spacing = 0.09
            tp = p - i * spacing
            tp = min(1.0, max(0.0, tp))
            leg = tp * 4
            leg_i = min(3, int(leg))
            leg_t = leg - leg_i
            a = corners[leg_i]
            b = corners[leg_i + 1]
            dd = head_d * (1.0 - i / tails * 0.6)
            dx = self.lerp(a[0], b[0], leg_t) - dd/2
            dy = self.lerp(a[1], b[1], leg_t) - dd/2
            visible = 0.0 < p < 1.0 and tp > 0.0
            bui.imagewidget(
                widget,
                size=(dd, dd),
                position=(dx, dy),
                opacity=(1.0 - i / tails * 0.8) if visible else 0.0
            )

class SeekBar(Widget):
    """
    A bar you can tap/drag to jump to a position

    parent: The current container
    size: Bar size
    position: Where it sits
    value: Starting thumb value
    segments: Number of click sensors
    on_seek: Seek callback
    """
    def __init__(
        self,
        parent: bui.Widget,
        size: tuple[float, float] = (400,20),
        position: tuple[float, float] = (0,0),
        value: float = 0.0,
        segments: int = 40,
        color: tuple[float, float, float] = (1,1,1),
        on_seek: 'Callable[[float], None] | None' = None,
        thumb_color: tuple[float, float, float] = (0,0,0)
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
        # empty
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
        # thumb
        self.thumb_size = pize[1] * 1.5
        self.thumb = bui.imagewidget(
            parent=self.root,
            texture=bui.gettexture('circle'),
            position=self.thumb_pos(self.value),
            size=(self.thumb_size,self.thumb_size),
            color=thumb_color
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
        bui.getsound('deek').play()
        t = (blip_indx + 0.5) / self.blip_count
        self.animate_to(t)
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

    def animate_to(self, target, duration=12):
        # lerp
        self.anim_val_start = self.value
        self.anim_val_target = target
        self.anim_val_indx = 0
        self.anim_val_duration = max(1, duration)
        self.anim_val_timer = bui.AppTimer(
            1 / 60, self.anim_val_step, repeat=True
        )

    def anim_val_step(self):
        if not self: return
        self.anim_val_indx += 1
        if self.anim_val_indx > self.anim_val_duration:
            self.anim_val_timer = None
            self.set_value(self.anim_val_target)
            return

        t = self.anim_val_indx / self.anim_val_duration
        eased_t = self.ease_out(t)
        value = self.lerp(self.anim_val_start, self.anim_val_target, eased_t)
        self.set_value(value)

class ProgressBar(Widget):
    """
    A pill-shaped bar that shows progress, no touch input

    parent: The current container
    size: Bar size
    position: Where it sits
    value: Fill amount
    indeterminate: Loop instead of fill
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
        # empty
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
        # chunk
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

    def animate_to(self, target, duration=12):
        # lerp
        if self.indeterminate:
            return
        self.anim_val_start = self.value
        self.anim_val_target = target
        self.anim_val_indx = 0
        self.anim_val_duration = max(1, duration)
        self.anim_val_timer = bui.AppTimer(
            1 / 60, self.anim_val_step, repeat=True
        )

    def anim_val_step(self):
        if not self: return
        self.anim_val_indx += 1
        if self.anim_val_indx > self.anim_val_duration:
            self.anim_val_timer = None
            self.set_value(self.anim_val_target)
            return

        t = self.anim_val_indx / self.anim_val_duration
        eased_t = self.ease_out(t)
        value = self.lerp(self.anim_val_start, self.anim_val_target, eased_t)
        self.set_value(value)

    def anim_step(self):
        if not self: return
        rim = self.rim
        chunk = self.chunk
        chunk_y = self.chunk_y
        # radius
        radius = chunk[1] / 2

        self.anim_indx += 1
        loop = 100
        t = (self.anim_indx % loop) / loop

        # wave
        head_t = self.ease_out(min(1.0, t*1.6))
        tail_t = self.ease_out(max(0.0, (t-0.35)*1.55))

        head = self.lerp(0.0, 1.0, head_t)
        tail = self.lerp(0.0, 1.0, tail_t)
        head = max(head, tail)

        # span
        span = chunk[0] - radius*2
        head_px = rim + radius + span*head
        tail_px = rim + radius + span*tail
        w = max(0.0, head_px-tail_px)
        # clamp
        w_drawn = w if w > chunk[1] else 0.0

        bui.imagewidget(
            self.fill,
            position=(tail_px,chunk_y),
            size=(w_drawn,chunk[1])
        )
        # leftcap
        fade_span_l = 0.05
        alpha_l = 1.0 if tail <= 0.0 else max(0.0, 1.0 - tail/fade_span_l)
        bui.imagewidget(
            self.wave_l,
            opacity=alpha_l
        )
        # rightcap
        right_wall = rim + chunk[0] - radius
        cap_x = min(tail_px, right_wall) - radius
        # fade
        hold_start = 0.625
        hold_end = 1.0
        hold_mid = hold_start + (hold_end - hold_start) / 2 + 0.072
        fade_span = 0.08
        fade_t = 1.0
        if t >= hold_mid - fade_span:
            fade_t = max(0.0, (hold_mid - t) / fade_span)
        # headpos
        left_wall = rim + radius
        cap_h_x = max(head_px, left_wall) - radius
        # tailcap
        merge_t = self.ease_out(max(0.0, min(1.0, 1.0 - fade_t)))
        cap_x_merged = self.lerp(cap_x, cap_h_x, merge_t)
        alpha = (1.0 - merge_t) if w > 0.0 else 0.0
        bui.imagewidget(
            self.wave_r,
            position=(cap_x_merged, chunk_y),
            opacity=alpha
        )
        # headcap
        alpha_h = fade_t if w > 0.0 else 0.0
        bui.imagewidget(
            self.wave_h,
            position=(cap_h_x, chunk_y),
            opacity=alpha_h
        )

class DemoWindow:
    """
    A scratch window that shows off every widget style side by side

    src: Widget to transition from
    """
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
        y = 520
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
        # toast
        y -= 150
        self.toast_btn = bui.buttonwidget(
            parent=self.root,
            position=(50,y),
            size=(500,50),
            label='Toast',
            color=(1,1,1),
            textcolor=(0,0,0),
            on_activate_call=self.show_toast,
            enable_sound=False
        )
        # snackbar
        y -= 60
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
        y -= 40
        self.seekbar_widget = SeekBar(
            parent=self.root,
            position=(50,y),
            size=(500,20),
            value=0.3,
            on_seek=lambda t: self.progress_widget_2.animate_to(1.0 - t)
        )
        # progress
        y -= 40
        self.progress_widget = ProgressBar(
            parent=self.root,
            position=(50,y),
            size=(500,20),
            indeterminate=True
        )
        # progress2
        y -= 40
        self.progress_widget_2 = ProgressBar(
            parent=self.root,
            position=(50,y),
            size=(500,20),
            value=0.6
        )
        # checkbox
        y -= 60
        size = (40,40)
        lip = 50
        rip = 550
        goo = rip - lip - size[0]
        blorp = 9
        gap = goo / (blorp - 1)
        self.checkbox_widget = Checkbox(
            parent=self.root,
            position=(lip + gap*0, y),
            size=size,
            style=Checkbox.Style.SQUARE,
            value=True,
            color=(0,0,0)
        )
        self.checkbox_widget_2 = Checkbox(
            parent=self.root,
            position=(lip + gap*1, y),
            size=size,
            style=Checkbox.Style.RADIAL,
            value=True,
            color=(1,1,1)
        )
        self.checkbox_widget_3 = Checkbox(
            parent=self.root,
            position=(lip + gap*2, y),
            size=size,
            style=Checkbox.Style.SWEEP_H,
            value=True,
            color=(0,0,0)
        )
        self.checkbox_widget_4 = Checkbox(
            parent=self.root,
            position=(lip + gap*3, y),
            size=size,
            style=Checkbox.Style.SWEEP_V,
            value=True,
            color=(1,1,1)
        )
        self.checkbox_widget_5 = Checkbox(
            parent=self.root,
            position=(lip + gap*4, y),
            size=size,
            style=Checkbox.Style.STAIRS,
            value=True,
            color=(0,0,0)
        )
        self.checkbox_widget_6 = Checkbox(
            parent=self.root,
            position=(lip + gap*5, y),
            size=size,
            style=Checkbox.Style.BLINDS,
            value=True,
            color=(1,1,1)
        )
        self.checkbox_widget_7 = Checkbox(
            parent=self.root,
            position=(lip + gap*6, y),
            size=size,
            style=Checkbox.Style.PINWHEEL,
            value=True,
            color=(0,0,0)
        )
        self.checkbox_widget_8 = Checkbox(
            parent=self.root,
            position=(lip + gap*7, y),
            size=size,
            style=Checkbox.Style.PULSE,
            value=True,
            color=(1,1,1)
        )
        self.checkbox_widget_9 = Checkbox(
            parent=self.root,
            position=(lip + gap*8, y),
            size=size,
            style=Checkbox.Style.COMET,
            value=True,
            color=(0,0,0)
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

    def show_toast(self):
        bui.getsound('deek').play()
        existing = getattr(self, 'toast', None)
        if existing and not existing.transitioning_out:
            existing.dismiss()
            return
        self.toast = Toast(
            parent=self.root,
            text='This is a toast!'
        )

    def show_dialog(self):
        bui.getsound('deek').play()
        Dialog(
            parent=bui.get_special_widget('overlay_stack'),
            title='Dialog',
            text='This is a Dialog! Press a button below.',
            action_label='OK',
            cancel_label='Cancel'
        )

    def show_notification(self):
        bui.getsound('deek').play()
        existing = getattr(self, 'notification', None)
        if existing:
            existing.dismiss()
            return
        self.notification = Notification(
            parent=self.root,
            title='Notification',
            text='This is a notification!\nPick a button below to dismiss it.'
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
        # dialog
        y -= 150
        self.windows_btn = bui.buttonwidget(
            parent=self.root,
            position=(50,y),
            size=(500,50),
            label='Dialog',
            color=(1,1,1),
            textcolor=(0,0,0),
            on_activate_call=self.show_dialog,
            enable_sound=False
        )
        # toast
        y -= 60
        bui.buttonwidget(
            parent=self.root,
            position=(50,y),
            size=(500,50),
            label='Notification',
            color=(1,1,1),
            textcolor=(0,0,0),
            on_activate_call=self.show_notification,
            enable_sound=False
        )
        # sidepane
        y -= 60
        bui.buttonwidget(
            parent=self.root,
            position=(50,y),
            size=(500,50),
            label='SidePane',
            color=(1,1,1),
            textcolor=(0,0,0),
            on_activate_call=self.show_sidepane,
            enable_sound=False
        )

    def show_sidepane(self):
        bui.getsound('deek').play()
        existing = getattr(self, 'sidepane', None)
        if existing and not existing.transitioning_out:
            existing.dismiss()
            return

        # instantiate
        pane = SidePane(
            parent=self.root,
            title='SidePane',
            text='Customize settings and preferences.'
        )
        self.sidepane = pane

        # layout
        margin = pane.margin
        content_w = pane.content_w
        curr_y = pane.curr_y

        # helper
        def scalex(base_x: float, width: float, scale: float) -> float:
            return base_x + (scale - 1.0) * (width / 2.0)

        # checkboxes
        csz = (30, 30)
        items = ['Unlock Greatness', 'Be Happy', 'Thrive']
        cts = 0.85
        ctw = content_w - csz[0] - 10
        ctx = scalex(margin, ctw, cts)

        for label in items:
            curr_y -= 44
            # text
            bui.textwidget(
                parent=pane.root,
                position=(ctx, curr_y),
                size=(ctw, csz[1]),
                text=label,
                scale=cts,
                color=(0.95, 0.95, 0.95),
                v_align='center',
                maxwidth=ctw
            )
            # checkbox
            Checkbox(
                parent=pane.root,
                position=(margin + content_w - csz[0], curr_y),
                size=csz,
                style=Checkbox.Style.SQUARE,
                value=True,
                color=(0, 0, 0)
            )

        # separator
        curr_y -= 16
        bui.imagewidget(
            parent=pane.root,
            size=(content_w, 1.5),
            position=(margin, curr_y),
            texture=bui.gettexture('white'),
            color=(0.22, 0.22, 0.22)
        )

        # buttons
        curr_y -= 46
        bg = 14
        bw = (content_w - bg) / 2
        bh = 34

        # close
        bui.buttonwidget(
            parent=pane.root,
            texture=bui.gettexture('white'),
            color=(0.12, 0.12, 0.12),
            textcolor=(0.9, 0.9, 0.9),
            enable_sound=False,
            size=(bw, bh),
            position=(margin, curr_y),
            label='Close',
            on_activate_call=pane.dismiss
        )

        # dismiss
        bui.buttonwidget(
            parent=pane.root,
            texture=bui.gettexture('white'),
            color=(0.12, 0.12, 0.12),
            textcolor=(0.9, 0.9, 0.9),
            enable_sound=False,
            size=(bw, bh),
            position=(margin + bw + bg, curr_y),
            label='Dismiss',
            on_activate_call=pane.dismiss
        )

        # separator
        curr_y -= 16
        bui.imagewidget(
            parent=pane.root,
            size=(content_w, 1.5),
            position=(margin, curr_y),
            texture=bui.gettexture('white'),
            color=(0.22, 0.22, 0.22)
        )

        # seekbar
        curr_y -= 26
        csc = 0.8
        cx = scalex(margin, content_w, csc)

        # text
        bui.textwidget(
            parent=pane.root,
            position=(cx, curr_y),
            size=(content_w, 20),
            text='Cool Level',
            scale=csc,
            color=(0.85, 0.85, 0.85),
            v_align='center',
            maxwidth=content_w
        )

        curr_y -= 26
        bar = SeekBar(
            parent=pane.root,
            position=(margin, curr_y),
            size=(content_w, 18),
            value=0.75,
            color=(1, 1, 1),
            thumb_color=(0.7,0.7,0.7)
        )
        # thumb
        bui.imagewidget(bar.thumb, color=(0.7, 0.7, 0.7))

        # save
        sh = 36
        sy = margin * 1.5
        bui.buttonwidget(
            parent=pane.root,
            texture=bui.gettexture('white'),
            color=(1,1,1),
            textcolor=(0,0,0),
            enable_sound=False,
            size=(content_w, sh),
            position=(margin, sy),
            label='Save',
            on_activate_call=lambda: (
                bui.getsound('gunCocking').play() or pane.dismiss()
            )
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
    """
    Plugin entry point that pops open the DemoWindow
    """
    def has_settings_ui(self):
        return True
    def show_settings_ui(self, src):
        DemoWindow(src)
    def on_app_running(self):
        bui.apptimer(1,DemoWindow)
