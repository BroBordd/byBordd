# Copyright 2025 - Solely by BrotherBoard
# Feedback is appreciated - Telegram >> @GalaxyA14user

"""
HTW v1.0 - Your highlight textwidget

A simple bauiv1 textwidget with highlight support

Made in 1 hour in GNU Nano in Termux using my Galaxy A14
Because I was offline outside and bored.
Refer to __doc__ of class htw for more info.
"""

from bauiv1 import textwidget as tw
from babase import (
    get_string_height as ogh,
    get_string_width as ogw,
    Plugin as P
)

"""Highlight text widget"""
class htw:
    """
        Pass a dict of {word: color, ...} as map.
        Other kwargs are passed to bauiv1.textwidget directly.
        Instance suppports set() later which overrides any non NoneType.
        Supports multiline using '\\n' as delimeter.

        Example:
            instance = htw(
                parent=parent,
                position=(165,68),
                text='I like colors\\nlike red\\nand cyan too',
                map={
                    'like red': (1,0,0),
                    'cyan too': (0,1,1)
                },
                **kwargs
            )
            widget = instance.widget # Plain base -> bauiv1.textwidget
            kids = instance.kids # Color overlays -> [bauiv1.textwidget, ...]
            def f():
                instance.set(
                    text='New text, only:\\nhighlight green apple.',
                    map={
                        'green apple': (0,1,0)
                    }
                )
    """
    """Create"""
    def __init__(
        s,
        parent,
        position: tuple = (0,0),
        text: str = '',
        map: dict = {},
        **k
    ) -> None:
        s.widget = tw(
            parent=parent,
            position=position,
            **k
        )
        s.parent = parent
        s.position = position
        s.kids = []
        s.set(
            text=text,
            map=map
        )
    """Override current"""
    def set(
        s,
        text: str = None,
        map: dict = None
    ) -> None:
        if text is not None:
            if '\\n' in text:
                text = '\n'.join(text.split('\\n'))
            s.text = text
            tw(
                s.widget,
                text=text
            )
        if map is not None:
            s.map = map
        s.place()
    """Place highlight kids"""
    def place(s) -> None:
        [i.delete() for i in s.kids]
        s.kids.clear()
        p = s.position
        for m in s.map:
            i = -1
            while True:
                i = s.text.find(m,i+1)
                if i < 0: break
                l = s.text[:i]
                f = l.split('\n')[-1]
                t = tw(
                    parent=s.parent,
                    text=m,
                    color=s.map[m],
                    position=(
                        p[0]+gw(f),
                        p[1]+(-gh(l)+gh(f))
                    )
                )
                s.kids.append(t)
    """Delete everything"""
    def delete(s) -> None:
        [i.delete for i in s.kids()]
        s.widget.delete()

"""Clean string info"""
gw, gh = (
    lambda s: ogw(s,suppress_warning=True),
    lambda s: ogh(s,suppress_warning=True)
)

# ba_meta require api 9
# ba_meta export plugin
class byBordd(P):
    has_settings_ui = lambda s: True
    show_settings_ui = lambda s, src: s.demo(src)
    """Our demo"""
    def demo(s,src):
        from bauiv1 import (
            containerwidget as cw,
            buttonwidget as bw
        )
        w = cw(
            transition='in_scale',
            scale_origin_stack_offset=src.get_screen_space_center(),
            color=(0.2,0.2,0.2),
            size=(450,300),
            scale=2
        )
        tw(
            parent=w,
            text='Demo!',
            position=(200,260),
            h_align='center',
            scale=2,
        )
        ins = htw(
            text='I like green!\nand ofc red and...\nalso blue!',
            map={
                'like green': (0,1,0),
                'red': (1,0,0),
                'also blue': (0,0,1)
            },
            parent=w,
            position=(30,160)
        )
        widget = ins.widget
        kids = ins.kids
        t = []
        for i in range(2):
            o = [
                'I prefer magenta\\nand cyan\\nand orange tho!',
                "{'magenta':(1,0,1), 'cyan':(0,1,1), 'orange':(1,0.5,0)}"
            ][i]
            g = [
                'Input is passed as text',
                'Input is evaluated and passed as map'
            ][i]
            j = tw(
                parent=w,
                size=(310,30),
                position=(40,220-30*i),
                maxwidth=310,
                text=o,
                allow_clear_button=False,
                description=f'{g}, enter',
                editable=True,
                v_align='center'
            )
            t.append(j)
            o = [
                ('Set', (0,0.4,0), (0,0.8,0)),
                ('Back', (0.4,0,0), (0.8,0,0))
            ][i]
            g = [
                lambda: (
                    ins.set(
                        text=tw(query=t[0]),
                        map=eval(tw(query=t[1]))
                    )
                ),
                lambda: (
                    cw(
                        w,
                        transition='out_scale'
                    )
                )
            ][i]
            bw(
                parent=w,
                label=o[0],
                color=o[1],
                textcolor=o[2],
                button_type='square',
                position=(360,225-30*i),
                size=(80,20),
                on_activate_call=g
            )
