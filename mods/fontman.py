# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
FontMan v1.0 - Font Manager

Experimental.
"""

import os
import bauiv1 as bui
import os.path as op
from uuid import uuid4
from shutil import copy
from babase import Plugin
from random import choice

class FontMan(bui.MainWindow):
    DEFAULT = '__default__'
    EMPTY = 'spinner0'
    INFO = '__desc__'
    COL0 = (0,0,0)
    COL1 = (0.05,0.05,0.05)
    COL2 = (1,1,1)
    COL3 = (0,0.5,0)
    def __init__(s,src):
        s.ktx_array = []
        s.ktx_anim = 0
        s.ktx_mem = []
        s.ktx_now = None
        s.sl = None
        rx,ry = bui.get_virtual_screen_size()
        s.size = (rx*0.8,ry*0.8)
        x,y = s.size
        # root
        s.p = bui.containerwidget(
            background=False,
            toolbar_visibility='no_menu_minimal',
            size=s.size
        )
        # shadow
        bui.imagewidget(
            texture=bui.gettexture('softRect'),
            opacity=0.85,
            color=s.COL0,
            parent=s.p,
            position=(-x*0.1,-y*0.1),
            size=(x*1.2,y*1.2)
        )
        # main
        super().__init__(
            root_widget=s.p,
            transition='in_scale',
            origin_widget=src
        )
        # background
        bui.imagewidget(
            texture=bui.gettexture('white'),
            parent=s.p,
            position=(-2,0),
            color=s.COL0,
            size=s.size
        )
        # footer
        bui.buttonwidget(
            texture=bui.gettexture('empty'),
            parent=s.p,
            label='',
            size=s.size,
            enable_sound=False
        )
        # back
        bui.containerwidget(s.p,cancel_button=(
            bui.buttonwidget(
                parent=s.p,
                label=bui.charstr(bui.SpecialChar.BACK),
                on_activate_call=s.bye,
                text_scale=0.8,
                texture=bui.gettexture('white'),
                color=s.COL1,
                textcolor=s.COL2,
                position=(20,y-70),
                size=(50,50),
                enable_sound=False
            )
        ))
        # title dock
        dx,dy = (x-110,50+4)
        px,py = (90,y-70)
        bui.imagewidget(
            texture=bui.gettexture('white'),
            parent=s.p,
            position=(px,py-2),
            size=(dx,dy),
            color=s.COL1
        )
        # title
        bui.textwidget(
            parent=s.p,
            text='FontMan',
            color=s.COL2,
            position=(px+dx/2.3,py+dy/5),
            h_align='center',
            v_align='center'
        )
        # preview dock
        bui.imagewidget(
            texture=bui.gettexture('white'),
            parent=s.p,
            color=s.COL1,
            size=(dx,120+4),
            position=(px,py-140-2)
        )
        # preview
        s.mk_tv(main=1)
        # preview sensor
        s.prv_sensor = bui.buttonwidget(
            parent=s.p,
            label='',
            size=(100,100),
            position=(px+dx-110,py-130),
            texture=bui.gettexture('empty'),
            on_activate_call=s.preview_big,
            enable_sound=False
        )
        # info
        bui.buttonwidget(
            parent=s.p,
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_CIRCLE_BUTTON),
            on_activate_call=s.info,
            text_scale=0.8,
            texture=bui.gettexture('white'),
            color=s.COL1,
            textcolor=s.COL2,
            position=(20,y-140),
            size=(50,50),
            enable_sound=False
        )
        # apply
        bui.buttonwidget(
            parent=s.p,
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_SQUARE_BUTTON),
            on_activate_call=s.apply,
            text_scale=0.8,
            texture=bui.gettexture('white'),
            color=s.COL1,
            textcolor=s.COL2,
            position=(20,y-210),
            size=(50,50),
            enable_sound=False
        )
        # name
        s.name_text = bui.textwidget(
            parent=s.p,
            text='Name',
            v_align='center',
            position=(110,y-130),
            maxwidth=x-260
        )
        # desc
        s.desc_text = bui.textwidget(
            parent=s.p,
            text='Description',
            v_align='center',
            position=(110,y-165),
            maxwidth=x-260
        )
        # info
        s.info_text = bui.textwidget(
            parent=s.p,
            text='Extra info',
            v_align='center',
            position=(110,y-200),
            maxwidth=x-260
        )
        # list dock
        bui.imagewidget(
            texture=bui.gettexture('white'),
            parent=s.p,
            color=s.COL1,
            size=(x-40+2,y-250),
            position=(20-2,20)
        )
        # list
        co = core()
        fl = os.listdir(co)
        fy = max(len(fl)*30,y-265)
        p = bui.containerwidget(
            parent=(
                bui.scrollwidget(
                    parent=s.p,
                    color=s.COL2,
                    size=(x-40,y-250),
                    position=(20,20),
                    border_opacity=0
                )
            ),
            size=(x-40,fy),
            background=False
        )
        # dynamic
        s.kids = []
        for i,_ in enumerate(fl):
            t = bui.textwidget(
                parent=p,
                text=_ if _ != s.DEFAULT else 'Default',
                glow_type='uniform',
                click_activate=True,
                selectable=True,
                position=(0,fy-30*i-30),
                size=(x-40,30),
                maxwidth=x-40,
                v_align='center',
                color=s.COL2
            )
            s.kids.append(t)
            bui.textwidget(t,on_activate_call=bui.Call(s.select,t,_))
        # finally
        s.sound('powerup01')
    def mk_tv(s,main,tr='out_scale'):
        x,y = s.size
        dx = x-110
        px,py = (90,y-70)
        pos = (px+dx-110,py-130)
        size = (100,100)
        if (f:=getattr(s,'ktx_tv',0)): f.delete()
        p = s.p if main else bui.containerwidget(
            stack_offset=s.prv_sensor.get_screen_space_center(),
            scale_origin_stack_offset=s.prv_sensor.get_screen_space_center(),
            size=size,
            background=False
        )
        main or bui.containerwidget(p,transition=tr)
        s.ktx_tv = bui.imagewidget(
            texture=s.ktx_now or bui.gettexture(s.EMPTY),
            parent=p,
            size=size,
            position=pos if main else (0,0)
        )
        return p
    def preview_big(s):
        sin = s.sound('powerup01')
        s.mk_tv(main=0)
        x = min(*s.size)*0.8
        p = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=lambda:(
                bui.apptimer(0.2,s.mk_tv(main=0,tr='in_scale').delete) or
                bui.apptimer(0.2,lambda:s.mk_tv(main=1)) or
                (s.sound('laser') and sin.stop()) or
                bui.containerwidget(p,transition='out_scale')
            ),
            transition='in_scale',
            scale_origin_stack_offset=s.prv_sensor.get_screen_space_center(),
            size=(x,x),
            background=False
        )
        bui.imagewidget(
            parent=p,
            size=(x*1.2,x*1.2),
            position=(-x*0.1,-x*0.1),
            texture=bui.gettexture('softRect'),
            color=s.COL0
        )
        bui.imagewidget(
            parent=p,
            size=(x,x),
            texture=bui.gettexture('black'),
            color=s.COL0
        )
        s.big_img = bui.imagewidget(
            parent=p,
            size=(x,x),
            texture=s.ktx_now or bui.gettexture(s.EMPTY)
        )
    def apply(s,what=None,shut=False):
        if not s.sl:
            s.sound('block')
            return
        what = what or s.sl
        if what != s.DEFAULT: s.apply(s.DEFAULT,shut=True)
        ba = base()
        for z in ['textures','fonts']:
            tx = op.join(what,z)
            if op.exists(tx):
                to = op.join(ba,z)
                for _ in os.listdir(tx):
                    copy(op.join(tx,_),op.join(to,_))
        if shut: return
        bui.getsound('gunCocking').play()
        bui.screenmessage('Applied! Restart BombSquad to view changes.',color=s.COL2)
    def info(s):
        if not s.sl:
            s.sound('block')
            return
        bui.screenmessage(s.sl,color=s.COL2)
        bui.getsound('deek').play()
    def select(s,t,_):
        s.ktx_now = None
        f = bui.textwidget
        co = core()
        root = s.sl = op.join(co,_)
        de = op.join(root,s.INFO)
        fo = op.join(root,'fonts')
        te = op.join(root,'textures')
        # hl
        for k in s.kids: f(k,color=s.COL2)
        f(t,color=s.COL3)
        # name
        f(s.name_text,text=[_,'Default'][_==s.DEFAULT])
        # desc
        desc = 'No description availabe.'
        if op.exists(de):
            try:
                with open(de,'r') as ff:
                    desc = ff.read()
            except: pass
        f(s.desc_text,text=desc)
        # info
        fc = tc = 0
        if op.exists(fo): fc = len(os.listdir(fo))
        if op.exists(te): tc = len(os.listdir(te))
        f(s.info_text,text=(
            f'{tc} Bitmap'+['s',''][tc==1]
            +' + '+
            f'{fc} Metric'+['s',''][tc==1]
        ))
        # clean ktx
        bui.imagewidget(s.ktx_tv,texture=bui.gettexture('spinner0'))
        s.clear_ktx()
        # ktx
        if not tc: return
        ba = base()
        tx = op.join(ba,'textures')
        for i in os.listdir(te):
            if not i.endswith('.ktx'): continue
            nam = '.FontMan_'+str(uuid4())
            tmp = op.join(tx,nam+'.ktx')
            copy(op.join(te,i),tmp)
            s.ktx_array.append(tmp)
            s.ktx_mem.append(bui.gettexture(nam))
        # anim ktx
        if not s.ktx_array: return
        if tc > 1: s.ktx_timer = bui.AppTimer(0.7,s.next_ktx,repeat=True)
        else: s.next_ktx()
    def next_ktx(s):
        m = s.ktx_mem
        if len(m) == 1: tex = s.ktx_now = m[0]
        else:
            tex = s.ktx_now = m[s.ktx_anim]
            s.ktx_anim += 1
            if s.ktx_anim >= len(m): s.ktx_anim = 0
        try: bui.imagewidget(s.ktx_tv,texture=tex)
        except:
            try: bui.imagewidget(s.big_img,texture=tex)
            except: s.ktx_timer = None
    def sound(s,t):
        l = bui.getsound(t)
        l.play()
        bui.apptimer(0.16,l.stop)
        return l
    def clear_ktx(s):
        s.ktx_timer = None
        for ktx in s.ktx_array: os.remove(ktx)
        s.ktx_array.clear()
        s.ktx_mem.clear()
        s.ktx_anim = 0
    def bye(s):
        s.clear_ktx()
        s.main_window_back()
        s.sound('laser')

# resources
core = lambda: op.join(bui.app.env.python_directory_user,'FontMan')
base = lambda: op.join(op.dirname(bui.app.env.cache_directory),'ballistica_files','ba_data')

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    on_app_running = lambda s: bui.apptimer(0.1,s.inject)
    post_reload = lambda s: None
    on_reload = lambda s: None
    def __init__(s):
        root = core()
        ba = base()
        os.makedirs(root,exist_ok=True)
        orig = op.join(root,FontMan.DEFAULT)
        to = op.join(ba,'textures')
        if not op.exists(orig):
            os.makedirs(orig)
            # fdata
            fi = op.join(orig,'fonts')
            os.makedirs(fi)
            fo = op.join(ba,'fonts')
            for _ in os.listdir(fo):
                if not _.endswith('.fdata'): continue
                copy(op.join(fo,_),op.join(fi,_))
            # ktx
            fi = op.join(orig,'textures')
            os.makedirs(fi)
            for _ in os.listdir(to):
                if not (_.startswith('font') and _.endswith('.ktx')): continue
                copy(op.join(to,_),op.join(fi,_))
            # desc
            with open(op.join(orig,FontMan.INFO),'w') as desc:
                desc.write('The one that came with the game.')
        # clean ktx
        for _ in os.listdir(op.join(ba,'textures')):
            if _.startswith('.FontMan_'):
                os.remove(op.join(to,_))
                continue
    def inject(s):
        # entry
        i = '__init__'
        from bauiv1lib.settings.allsettings import AllSettingsWindow as m
        o = getattr(m,i)
        setattr(m,i,lambda z,*a,**k:(o(z,*a,**k),s.make(z))[0])
        FontMan.main_window_should_preserve_selection = lambda c: False
    def make(s,z):
        tex = [bui.gettexture(f'chTitleChar{_}') for _ in range(1,6)]
        SCL = lambda a,b,c=None: [a,b,c][bui.app.ui_v1.uiscale.value] or b
        x,y = SCL((1000,800),(900,450))
        s.b = bui.buttonwidget(
            position=(x*0.7-110,y*SCL(0.5,0.9)),
            parent=z._root_widget,
            size=(100,30),
            button_type='square',
            label='Man',
            icon=choice(tex),
            enable_sound=False,
            color=FontMan.COL0,
            textcolor=FontMan.COL2,
            on_activate_call=lambda:s.run(z),
            id='FontMan'+str(id(z))
        )
        s.bt = bui.AppTimer(0.7,bui.Call(s.anim,tex),repeat=True)
    def anim(s,tex):
        try: bui.buttonwidget(s.b,icon=choice(tex))
        except: s.bt = None
    def run(s,z):
        z.main_window_replace(lambda:FontMan(s.b))
