import bauiv1lib.settings.audio as A
from babase import Plugin as P
from bauiv1 import (
    get_special_widget as gw,
    containerwidget as cw,
    screenmessage as E,
    buttonwidget as bw,
    gettexture as gt,
    textwidget as tw,
    getsound as gs,
    Call,
    app
)

class SetAudio(A.AudioSettingsWindow):
    def __init__(s,*a,**k):
        super().__init__(*a,**k)
        for i in [0,1]:
            b = bw(
                position=(265,220-50*i),
                parent=s._root_widget,
                button_type='square',
                texture=gt('empty'),
                enable_sound=False,
                selectable=False,
                autoselect=False,
                size=(50,35),
                label='',
            )
            bw(b,on_activate_call=Call(s.set,b,i))
    def set(s,b,i):
        p = b.get_screen_space_center()
        c = cw(
            scale_origin_stack_offset=p,
            parent=gw('overlay_stack'),
            transition='in_scale',
            stack_offset=p,
            size=(70,40),
            scale=2
        )
        z = ['Sound','Music'][i]+' Volume'
        t = tw(
            text=str(int(app.config[z]*100)),
            allow_clear_button=False,
            h_align='center',
            position=(5,5),
            editable=True,
            size=(60,30),
            parent=c,
        )
        cw(c,on_outside_click_call=lambda:(s.bye(tw(query=t),z),cw(c,transition='out_scale')))
        t.activate()
        gs('deek').play()
    def bye(s,t,z):
        try: p = int(t); p = [[100,0][p<0],p][0<=p<=100]
        except: (E('Invalid input',color=(1,0,0)),gs('error').play())
        else:
            gs('dingSmallHigh').play()
            c = app.config
            c[z] = p/100
            c.apply_and_commit()
            t = getattr(s,f"_{['sound','music']['M' in z]}_volume_numedit")
            t._value = p/100
            t._update_display()

# ba_meta require api 9
# ba_meta export plugin
class byBordd(P):
    def __init__(s):
        A.AudioSettingsWindow = SetAudio
