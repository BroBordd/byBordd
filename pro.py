from babase import Plugin as P
from bauiv1 import (
    containerwidget as cw,
    hscrollwidget as hsw,
    textwidget as tw)

"""A progress bar"""
class progressbar:
    """Create"""
    def __init__(
        s,
        progress: int = 0,
        on_color: tuple = (1,1,1),
        off_color: tuple = (0,0,0),
        **k
    ) -> None:
        s.k = k
        s.progress = progress
        s.size = k['size']
        o = lambda: hsw(
            border_opacity=0.0,
            highlight=False,
            **k
        )
        s.p = o(); o()
        s.x = s.size[0]*2
        s.y = s.size[1]
        s.w = cw(
            parent=s.p,
            size=(s.x,s.y),
            background=False
        )
        s.kids = []
        for i in range(s.x):
            t = tw(
                parent=s.w,
                text='■',
                shadow=False,
                position=(i-10,s.y/1.8),
                scale=s.y/10,
                size=(1,20),
                color=[on_color,off_color][i>(s.x/2)]
            )
            s.kids.append(t)
        s.set_progress(progress)
    """Set progress"""
    def set_progress(s, progress: int) -> None:
        b = s.progress > progress
        s.progress = p = progress
        p = (p / 2) + 46.5
        p = s.x - int(p * s.x / 100)
        if b: cw(s.w, visible_child=s.kids[-1])
        cw(s.w, visible_child=s.kids[abs(p-1)])
    """Get widget"""
    def get_widget(s) -> hsw:
        return s.widget

# ba_meta require api 9
# ba_meta export plugin
class byBordd(P):
    has_settings_ui = lambda s: True
    show_settings_ui = lambda s, w: s.demo(w)
    def demo(s,src):
        from bauiv1 import buttonwidget as bw
        w = cw(
            transition='in_scale',
            scale_origin_stack_offset=src.get_screen_space_center(),
            color=(1,1,1),
            size=(600,200)
        )
        p = progressbar(
            parent=w,
            size=(500,30),
            position=(50,50)
        )
        t = tw(
            parent=w,
            size=(200,30),
            editable=True,
            allow_clear_button=False,
            position=(50,100)
        )
        for i in range(2):
            j = [lambda: p.set_progress(int(float(tw(query=t) or '0'))),
                 lambda: cw(w,transition='out_scale')][i]
            bw(
                parent=w,
                size=(100,30),
                position=(260+110*i,100),
                textcolor=(1,1,1),
                label=['set','back'][i],
                color=(0.1,0.1,0.1),
                on_activate_call=j
            )
