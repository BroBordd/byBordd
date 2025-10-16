# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
UEye v1.0 - Real-Time UI Debugger

Your eye for UI. Adds a dev console tab.
Ability to modify any visible UI without having its references.
Experimental.
"""

import bauiv1 as bui
from re import match
from babase import Plugin
from functools import wraps
from random import random, choice
from babase._devconsole import (
    DevConsoleTabEntry as ENT,
    DevConsoleTab as TAB
)

class UEye(TAB):
    def __init__(s):
        s.sl = s.editor = s.shower = None
        s.hot = False
    def refresh(s):
        if s.sl and not (getattr(s.sl[1],'exists',lambda:0)()): s.sl = None
        s.up()
    def safe_refresh(s):
        try: s.request_refresh()
        except RuntimeError: pass
    def up(s):
        num_items = len(MEM)
        if num_items == 0: return

        grid_width = s.width
        grid_height = s.height
        if grid_height <= 0: return

        desired_ratio = 200 / 50

        sqrt_val = (grid_width * num_items) / (grid_height * desired_ratio)
        cols = max(1, round(sqrt_val ** 0.5))

        rows = (num_items + cols - 1) // cols

        button_width = grid_width / cols
        button_height = grid_height / rows

        start_x = -s.width / 2
        start_y = 0

        for i,h in enumerate(MEM.items()):
            g,at = h
            text, widget = g
            args, kwargs = at
            current_row = i // cols
            current_col = i % cols

            pos_x = start_x + (current_col * button_width)
            pos_y = start_y + (current_row * button_height)

            guess = (
                kwargs.get('text',0) or
                kwargs.get('label',0) or
                text[:-6]
            )
            if hasattr(guess,'evaluate'):
                guess = guess.evaluate()
            s.button(
                '',
                size=(button_width, button_height),
                pos=(pos_x, pos_y),
                call=bui.Call(s.pick,widget) if s.hot else (bui.Call(s.edit,g) if s.sl != g else bui.Call(s.show,widget)),
                style='yellow' if s.hot else ('purple' if s.sl != g else 'purple_bright'),
                corner_radius=10
            )
            chk = bui.get_string_width(guess,suppress_warning=True)
            s.text(
                guess,
                pos=(pos_x+button_width/2, pos_y+button_height/2),
                scale=1 if chk<button_width else button_width/chk
            )
    def edit(s,g):
        s.sl = g
        if s.editor: s.editor.bye()
        s.editor = Editor(g)
        s.safe_refresh()
    def show(s,w):
        if s.shower: s.shower.decay()
        s.shower = Shower(w)
        bui.apptimer(1,s.shower.decay)
    def picker(s,on_pick):
        s.hot = True
        s.on_pick = on_pick
        s.safe_refresh()
    def pick(s,widget):
        s.on_pick(widget)[0] and s.release()
    def release(s):
        if not s.hot: return
        del s.on_pick
        s.hot = False
        s.safe_refresh()

class Editor:
    COL0 = (0,0,0)
    COL1 = (0.1,0.1,0.1)
    COL2 = (0.7,0.7,0.7)
    COL3 = (3,3,3)
    def __init__(s,g):
        s.sl = None
        s.trash = []
        # sound
        wop = bui.getsound('powerup01')
        wop.play()
        bui.apptimer(0.15,wop.stop)
        # ui
        x,y = s.x,s.y = (600,450)
        s.opacity = 0.7
        s.what, s.widget = g
        snipe = s.widget.get_screen_space_center()
        # root
        s.root = ORG['containerwidget'](
            parent=bui.get_special_widget('overlay_stack'),
            size=(x,y),
            background=False,
            scale_origin_stack_offset=snipe,
            transition='in_scale'
        )
        # shadow
        ORG['imagewidget'](
            parent=s.root,
            position=(-x*0.1,-y*0.1),
            size=(x*1.2,y*1.2),
            texture=bui.gettexture('softRect'),
            opacity=s.opacity,
            color=s.COL0
        )
        # bg
        ORG['imagewidget'](
            parent=s.root,
            position=(-1,-1),
            size=(x,y),
            texture=bui.gettexture('white'),
            color=s.COL0,
            opacity=s.opacity
        )
        # bye
        s.backb = ORG['buttonwidget'](
            parent=s.root,
            position=(20,y-70),
            size=(50,50),
            label=bui.charstr(bui.SpecialChar.BACK),
            text_scale=0.8,
            texture=bui.gettexture('white'),
            color=s.COL1,
            textcolor=s.COL2,
            on_activate_call=lambda:s.bye(manual=True) or bui.getsound('laser').play(),
            enable_sound=False
        )
        # title dock
        px,py = 90,y-70-2
        dx,dy = x-110,50+4
        ORG['imagewidget'](
            parent=s.root,
            texture=bui.gettexture('white'),
            color=s.COL1,
            position=(px,py),
            size=(dx,dy),
            opacity=s.opacity
        )
        # title
        ORG['textwidget'](
            parent=s.root,
            text=f'{s.what} at {hex(id(s.widget))}',
            h_align='center',
            v_align='center',
            maxwidth=dx-20,
            position=(px+dx/2.23,py+dy/4-2),
            color=s.COL3
        )
        # attr scroll
        fx,fy = x/2-20,y-110
        p0 = ORG['scrollwidget'](
            parent=s.root,
            position=(20,20),
            size=(fx,fy),
            border_opacity=0,
            color=s.COL2
        )
        # attr root
        s.attrs = inspect(ORG[s.what],bad=['edit'])
        ry = max(fy-5,len(s.attrs)*30)
        p1 = ORG['containerwidget'](
            parent=p0,
            background=False,
            size=(fx,ry)
        )
        # attr bg
        ORG['imagewidget'](
            parent=p1,
            size=(fx+2,ry*1.5),
            position=(-1,-ry/4),
            texture=bui.gettexture('white'),
            color=s.COL1,
            opacity=s.opacity
        )
        # scoller bg
        ORG['imagewidget'](
            parent=p1,
            size=(20,ry),
            position=(fx-20+2,0),
            texture=bui.gettexture('white'),
            color=s.COL1,
            opacity=1
        )
        # attrs
        s.kids = []
        for i,a in enumerate(s.attrs):
            w = ORG['textwidget'](
                parent=p1,
                text=a,
                maxwidth=fx-20,
                position=(0,ry-30*i-30),
                size=(fx,30),
                v_align='center',
                click_activate=True,
                selectable=True,
                glow_type='uniform',
                color=s.COL2
            )
            ORG['textwidget'](
                w,on_activate_call=bui.Call(s.select,w,a)
            )
            s.kids.append(w)
        # finally
        s.make()
    def clean(s):
        for _ in s.trash: _.delete()
    def make(s):
        s.clean()
        # setters
        ops = ['String','Bool','Widget','Color','Eval','Hint']
        by = (s.y-110)/len(ops)
        s.mx = s.x/2+20
        for i,_ in enumerate(ops):
            b = ORG['buttonwidget'](
                parent=s.root,
                position=(s.mx,s.y-142-by*i),
                size=(s.mx-70,by-10),
                label=_,
                texture=bui.gettexture('white'),
                color=s.COL1,
                textcolor=s.COL3,
                on_activate_call=bui.Call(s.action,_),
                enable_sound=False
            )
            s.trash.append(b)
        ORG['containerwidget'](s.root,cancel_button=s.backb)
    def select(s,w,a):
        f = ORG['textwidget']
        for _ in s.kids: f(_,color=s.COL2)
        f(w,color=s.COL3)
        s.sl = a
    def bye(s,manual=False):
        byBordd.INS.release()
        if manual:
            byBordd.INS.sl = None
            try: byBordd.INS.safe_refresh()
            except: pass
        if not s.root: return
        ORG['containerwidget'](s.root,transition='out_scale')
    def action(s,_):
        # safe
        if _ == 'Hint':
            if s.sl is None:
                bui.getsound('block').play()
                bui.screenmessage('Select an attribute to grab hints from!',color=s.COL3)
                return
        else: s.clean()
        # menus
        match _:
            case 'String':
                # tip
                s.trash.append(ORG['textwidget'](
                    parent=s.root,
                    text='Enter raw text here:',
                    color=s.COL3,
                    maxwidth=s.mx-70,
                    position=(s.mx,s.y-120)
                ))
                # input
                tw = ORG['textwidget'](
                    parent=s.root,
                    editable=True,
                    color=s.COL2,
                    v_align='center',
                    allow_clear_button=False,
                    description='Example input:\nHello World!\nEnter',
                    position=(s.mx,s.y-165),
                    size=(s.mx-65,40),
                    glow_type='uniform'
                )
                s.trash.append(tw)
                # apply
                s.trash.append(ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,s.y-215),
                    size=(s.mx-70,40),
                    label='Apply',
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    textcolor=s.COL3,
                    on_activate_call=lambda:(
                        (e:=tri(
                            s.what,
                            s.widget,
                            s.sl,
                            ORG['textwidget'](query=tw)
                        )) and (
                            bui.getsound('block').play(),
                            bui.screenmessage(e,color=s.COL3)
                        ) or (
                            bui.getsound('gunCocking').play()
                        )
                    ),
                    enable_sound=False
                ))
                # bye
                backb = ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,s.y-265),
                    size=(s.mx-70,40),
                    label='Back',
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    textcolor=s.COL3,
                    on_activate_call=lambda:bui.getsound('deek').play() or s.make(),
                    enable_sound=False
                )
                s.trash.append(backb)
                ORG['containerwidget'](s.root,cancel_button=backb)
            case 'Bool':
                # yes
                s.trash.append(ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,s.y-135),
                    size=(s.mx-70,40),
                    label='True',
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    textcolor=s.COL3,
                    on_activate_call=lambda:(
                        (e:=tri(
                            s.what,
                            s.widget,
                            s.sl,
                            True
                        )) and (
                            bui.getsound('block').play(),
                            bui.screenmessage(e,color=s.COL3)
                        ) or (
                            bui.getsound('gunCocking').play()
                        )
                    ),
                    enable_sound=False
                ))
                # no
                s.trash.append(ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,s.y-185),
                    size=(s.mx-70,40),
                    label='False',
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    textcolor=s.COL3,
                    on_activate_call=lambda:(
                        (e:=tri(
                            s.what,
                            s.widget,
                            s.sl,
                            False
                        )) and (
                            bui.getsound('block').play(),
                            bui.screenmessage(e,color=s.COL3)
                        ) or (
                            bui.getsound('gunCocking').play()
                        )
                    ),
                    enable_sound=False
                ))
                # bye
                backb = ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,s.y-235),
                    size=(s.mx-70,40),
                    label='Back',
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    textcolor=s.COL3,
                    on_activate_call=lambda:bui.getsound('deek').play() or s.make(),
                    enable_sound=False
                )
                s.trash.append(backb)
                ORG['containerwidget'](s.root,cancel_button=backb)
            case 'Widget':
                # tip
                s.trash.append(ORG['textwidget'](
                    parent=s.root,
                    text='Now select a widget\nfrom the UEye tab',
                    color=s.COL3,
                    maxwidth=s.mx-70,
                    position=(s.mx,s.y-120)
                ))
                # bye
                backb = ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,s.y-205),
                    size=(s.mx-70,40),
                    label='Back',
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    textcolor=s.COL3,
                    on_activate_call=lambda:(
                        bui.getsound('deek').play(),
                        s.make(),
                        byBordd.INS.release()
                    ),
                    enable_sound=False
                )
                s.trash.append(backb)
                ORG['containerwidget'](s.root,cancel_button=backb)
                # picker
                byBordd.INS.picker(on_pick=lambda widget:(
                    (e:=tri(
                        s.what,
                        s.widget,
                        s.sl,
                        widget
                    )) and (
                        False,
                        bui.getsound('block').play(),
                        bui.screenmessage(e,color=s.COL3)
                    ) or (
                        True,
                        bui.getsound('gunCocking').play(),
                        s.make()
                    )
                ))
            case 'Color':
                color = None
                blind = lambda r,g,b:0 if(0.299*r+0.587*g+0.114*b)>0.5 else 1
                rcol = lambda: tuple(round(random(),2) for _ in range(3))
                # color scroll
                p0 = ORG['scrollwidget'](
                    parent=s.root,
                    position=(s.mx-11,220),
                    border_opacity=0,
                    size=(s.mx-46,138),
                    color=s.COL2
                )
                s.trash.append(p0)
                # color root
                all = 52*20
                p1 = ORG['containerwidget'](
                    parent=p0,
                    background=False,
                    size=(s.mx-56,all)
                )
                # color bg
                ORG['imagewidget'](
                    parent=p1,
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    position=(-20,-all/4),
                    size=(s.mx,all*1.5),
                    opacity=s.opacity
                )
                # color scroll bg
                ORG['imagewidget'](
                    parent=p1,
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    opacity=1,
                    position=(s.mx-63,-all/4),
                    size=(10,all*1.5),
                )
                # make color kids
                ckids = []
                for j in range(20):
                    for i in range(5):
                        ckids.append(ORG['buttonwidget'](
                            label='',
                            parent=p1,
                            size=(40,40),
                            position=(i*52,5+j*52),
                            texture=bui.gettexture('white'),
                            enable_sound=False
                        ))
                # colorize color kids
                def cckids():
                    f = ORG['buttonwidget']
                    for k in ckids:
                        c = rcol()
                        f(
                            k,
                            color=c,
                            on_activate_call=bui.Call(cset,c)
                        )
                # set color
                def cset(c):
                    bui.getsound('deek').play()
                    nonlocal color
                    color = c
                    ORG['buttonwidget'](
                        pre,
                        color=c,
                        label=f'{choice(LOREM())} {choice(IPSUM())}',
                        textcolor=[s.COL0,s.COL2][blind(*c)]
                    )
                # color preview
                pre = ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,125),
                    size=(s.mx-70,40),
                    texture=bui.gettexture('white'),
                    on_activate_call=lambda:(
                        bui.getsound('deek').play(),
                        bui.screenmessage(str(color),color=s.COL3)
                    ),
                    enable_sound=False
                )
                s.trash.append(pre)
                # color randomizer
                s.trash.append(ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,175),
                    size=(s.mx-70,40),
                    label='Randomize',
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    textcolor=s.COL3,
                    on_activate_call=lambda:(
                        (ca:=bui.getsound('dingSmallHigh')),
                        ca.play(),
                        bui.apptimer(0.16,ca.stop),
                        cckids()
                    ),
                    enable_sound=False
                ))
                # apply
                s.trash.append(ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,75),
                    size=(s.mx-70,40),
                    label='Apply',
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    textcolor=s.COL3,
                    on_activate_call=lambda:(
                        (e:=tri(
                            s.what,
                            s.widget,
                            s.sl,
                            color
                        )) and (
                            bui.getsound('block').play(),
                            bui.screenmessage(e,color=s.COL3)
                        ) or (
                            bui.getsound('gunCocking').play()
                        )
                    ),
                    enable_sound=False
                ))
                # bye
                backb = ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,25),
                    size=(s.mx-70,40),
                    label='Back',
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    textcolor=s.COL3,
                    on_activate_call=lambda:(
                        bui.getsound('deek').play(),
                        s.make()
                    ),
                    enable_sound=False
                )
                ORG['containerwidget'](s.root,cancel_button=backb)
                s.trash.append(backb)
                # finally
                cckids()
                cset(rcol())
            case 'Eval':
                # tip
                s.trash.append(ORG['textwidget'](
                    parent=s.root,
                    text='Enter something to evaluate.\nYou can use globals that are\ndefined in ueye.py',
                    color=s.COL3,
                    maxwidth=s.mx-70,
                    position=(s.mx,s.y-120)
                ))
                # input
                tw = ORG['textwidget'](
                    parent=s.root,
                    editable=True,
                    color=s.COL2,
                    v_align='center',
                    allow_clear_button=False,
                    description="Example input:\nbui.gettexture('logo')\nEnter",
                    position=(s.mx,s.y-205),
                    size=(s.mx-65,40),
                    glow_type='uniform'
                )
                s.trash.append(tw)
                # apply
                s.trash.append(ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,s.y-255),
                    size=(s.mx-70,40),
                    label='Apply',
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    textcolor=s.COL3,
                    on_activate_call=lambda:(
                        (e:=tri(
                            s.what,
                            s.widget,
                            s.sl,
                            ORG['textwidget'](query=tw),
                            ev=True
                        )) and (
                            bui.getsound('block').play(),
                            bui.screenmessage(e,color=s.COL3)
                        ) or (
                            bui.getsound('gunCocking').play()
                        )
                    ),
                    enable_sound=False
                ))
                # bye
                backb = ORG['buttonwidget'](
                    parent=s.root,
                    position=(s.mx,s.y-305),
                    size=(s.mx-70,40),
                    label='Back',
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    textcolor=s.COL3,
                    on_activate_call=lambda:bui.getsound('deek').play() or s.make(),
                    enable_sound=False
                )
                s.trash.append(backb)
                ORG['containerwidget'](s.root,cancel_button=backb)
            case 'Hint':
                bui.screenmessage(s.attrs[s.sl],color=s.COL3)
                bui.getsound('dingSmall').play()
                return
        bui.getsound('deek').play()

class Shower:
    def __init__(s,w):
        s.width = 100
        s.opacity=0.6
        s.dying = False
        s.off = w.get_screen_space_center()
        s.root = ORG['containerwidget'](
            parent=bui.get_special_widget('overlay_stack'),
            size=(s.width,s.width),
            background=False,
            stack_offset=s.off
        )
        s.img = ORG['imagewidget'](
            parent=s.root,
            texture=bui.gettexture('achievementOutline'),
            color=(10,0,0),
            opacity=s.opacity
        )
        s.anim(s.width*10)
    def anim(s,i):
        o = -i/2+s.width/2
        ORG['imagewidget'](s.img,size=(i,i),position=(o,o))
        if i <= 100: return
        bui.apptimer(0.01,bui.Call(s.anim,i-25))
    def decay(s):
        if s.dying: return
        s.dying = True
        s.fade(s.opacity)
        bui.apptimer(0.5,s.delete)
    def fade(s,i):
        try: ORG['imagewidget'](s.img,opacity=i)
        except: return
        bui.apptimer(0.01,bui.Call(s.fade,i-0.05))
    def delete(s):
        s.root.delete()

# attribute fetcher
def inspect(f, bad=[]):
    doc = f.__doc__
    if not doc:
        return {}
    res = {}
    lines = doc.splitlines()
    ml = cn = None
    cp = []
    for l in lines:
        sl = l.strip()
        if ml:
            cp.append(sl)
            if sl.endswith('] | None = None,') or sl.endswith('],'):
                fs = " ".join(cp).rstrip(',')
                if cn:
                    res[cn] = fs
                ml = cn = None
                cp = []
            continue
        m = match(r'^\s*(\w+):\s*(.*)', l)
        if m and not any(k in l for k in ['(*,', ') -> ', 'Create or edit', 'Pass a valid existing']):
            an = m.group(1)
            ts = m.group(2).strip()
            if ts.startswith('Literal['):
                ml = True
                cn = an
                cp.append(ts)
            elif an not in bad:
                res[an] = ts.rstrip(',')
    return res

# try and see
def tri(what,obj,attr,value,ev=False):
    if attr is None:
        bui.getsound('block').play()
        return 'Select an attribute first!'
    if ev:
        try: value = eval(value,globals())
        except Exception as e: return f"eval('{value}') says:\n{e}"
    try: ORG[what](obj,**{attr:value})
    except Exception as e:
        if isinstance(value,str): value = f"'{value}'"
        if hasattr(value,'get_widget_type'): value = 'that'
        return f'{what}(this, {attr}={value}) says:\n{e}'

# global
ORG = {}
MEM = {}
EYE = None
LOREM = lambda: [
    "Lorem", "Ipsum", "Dolor", "Sit", "Amet",
    "Consectetur", "Adipiscing", "Elit", "Sed", "Eiusmod",
    "Tempor", "Incididunt", "Labore", "Magna", "Aliqua",
    "Veniam", "Quis", "Nostrud", "Exercitation", "Ullamco"
]
IPSUM = lambda: [
    "Ipsum", "Placeholder", "Sample", "Text", "Content",
    "Example", "Dummy", "Filler", "Template", "Mock",
    "Test", "Demo", "Specimen", "Prototype", "Draft",
    "Snippet", "Fragment", "Block", "Element", "Component"
]

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    INS = None
    def __init__(s):
        # tab
        C = UEye
        N = C.__name__
        E = ENT(N,C)
        I = bui.app.devconsole
        I.tabs = [_ for _ in I.tabs if _.name != N]+[E]
        I._tab_instances[N] = s.__class__.INS = E.factory()
        # stealer
        for _ in dir(bui):
            if not (
                _.endswith('widget')
                and '_' not in _
                and 'widget' != _
            ): continue
            ORG[_] = getattr(bui,_)
            setattr(bui,_,getattr(s,_))
        # cleaner
        global EYE
        EYE = bui.AppTimer(0.05,s.eye,repeat=True)
    def __getattr__(s,_):
        @wraps(ORG[_])
        def wrapper(*a,**k):
            r = ORG[_](*a,**k)
            z = (_,r)
            MEM.update({z:(a,k)})
            return r
        return wrapper
    def eye(s):
        pure = 1
        for _ in MEM.copy():
           w = _[1]
           if not (
               w and
               getattr(w,'exists',lambda:0)()
           ):
               MEM.pop(_)
               pure = 0
        if not pure: s.__class__.INS.safe_refresh()
