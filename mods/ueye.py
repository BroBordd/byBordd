# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
UEye v1.0 - Real-Time UI Debugger

Your eye for UI. Adds a dev console tab.
Ability to tweak any visible UI without having its references.
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
    CONTAINER_OFF = 'purple'
    CONTAINER_ON = 'purple_bright'
    CONTAINER_HOT = 'red'
    WIDGET_OFF = 'blue'
    WIDGET_ON = 'black'
    WIDGET_HOT = 'red'
    BACK_BUTTON = 'red_bright'
    HEADER_BUTTON_OFF = 'black_bright'
    HEADER_BUTTON_ON = 'black'
    HEADER_BUTTON_HOT = 'red'
    EMPTY_STATE = 'faded'
    def __init__(s):
        s.sl = s.editor = s.shower = None
        s.hot = False
        s.expanded = None
    def refresh(s):
        if s.sl and not (getattr(s.sl[1],'exists',lambda:0)()): s.sl = None
        s.up()
    def deek(s):
        bui.getsound('deek').play()
    def safe_refresh(s):
        try: s.request_refresh()
        except RuntimeError: pass
    def check(s,t,size,i=1):
        z = {'suppress_warning':1}
        w = bui.get_string_width(t,**z)
        h = bui.get_string_height(t,**z)
        x,y = size
        return min(
            i if w < x else x/w,
            i if h < y else y/h
        )
    def up(s):
        containers = MEM.items()
        num_containers = len(containers)
        if num_containers == 0: return

        grid_width = s.width
        grid_height = s.height
        if grid_height <= 0: return

        if s.expanded is None:
            desired_ratio = 200 / 50
            sqrt_val = (grid_width * num_containers) / (grid_height * desired_ratio)
            cols = max(1, round(sqrt_val ** 0.5))
            rows = (num_containers + cols - 1) // cols

            button_width = grid_width / cols
            button_height = grid_height / rows
            size = (button_width,button_height)

            start_x = -s.width / 2
            start_y = 0

            for i,(g,at) in enumerate(containers):
                text, widget = g
                args, kwargs = at
                current_row = i // cols
                current_col = i % cols

                pos_x = start_x + (current_col * button_width)
                pos_y = start_y + (current_row * button_height)

                style = s.CONTAINER_HOT if s.hot else (s.CONTAINER_OFF if s.sl != g else s.CONTAINER_ON)
                
                s.button(
                    '',
                    size=size,
                    pos=(pos_x, pos_y),
                    call=bui.CallPartial(s.expand_container,g) if not s.hot else bui.CallPartial(s.pick,widget),
                    style=style,
                    corner_radius=10
                )
                t = text[:-6]
                s.text(
                    t,
                    pos=(pos_x+button_width/2, pos_y+button_height/2),
                    scale=s.check(t,size),
                    style='normal'
                )
        else:
            text, widget = s.expanded
            is_selected = s.sl and s.sl[1] == widget
            
            header_height = 50
            back_button_width = 60
            
            s.button(
                bui.charstr(bui.SpecialChar.BACK),
                size=(back_button_width, header_height),
                pos=(-s.width/2, grid_height - header_height),
                call=bui.CallPartial(s.collapse_container),
                style=s.BACK_BUTTON,
                corner_radius=10
            )

            size = (grid_width - back_button_width, header_height)
            s.button(
                '',
                size=size,
                pos=(-s.width/2 + back_button_width, grid_height - header_height),
                call=bui.CallPartial(s.pick,widget) if s.hot else bui.CallPartial(s.edit,s.expanded),
                style=s.HEADER_BUTTON_HOT if s.hot else s.HEADER_BUTTON_ON if is_selected else s.HEADER_BUTTON_OFF,
                corner_radius=10
            )
            
            label_text = f'Inside container at {hex(id(widget))} - Click to '+['debug','pick'][s.hot]
            max_label_width = grid_width - back_button_width - 20
            s.text(
                label_text,
                pos=(back_button_width/2, grid_height - header_height/2),
                scale=s.check(label_text,size),
                style='normal'
            )
            
            try:
                children = widget.get_children()
            except:
                children = []
            
            margin = 20 if s.height > 100 else 0
            inner_width = grid_width - 2 * margin
            inner_height = grid_height - header_height - 2 * margin
            
            if children:
                num_children = len(children)
                desired_ratio = 150 / 40
                sqrt_val = (inner_width * num_children) / (inner_height * desired_ratio)
                child_cols = max(1, round(sqrt_val ** 0.5))
                child_rows = (num_children + child_cols - 1) // child_cols

                child_width = inner_width / child_cols
                child_height = inner_height / child_rows

                start_x = -s.width / 2 + margin
                start_y = margin

                for i, child in enumerate(children):
                    current_row = i // child_cols
                    current_col = i % child_cols

                    pos_x = start_x + (current_col * child_width)
                    pos_y = start_y + (current_row * child_height)

                    child_type = child.get_widget_type()
                    
                    if s.hot:
                        child_style = s.WIDGET_HOT
                        child_call = bui.CallPartial(s.pick,child)
                    else:
                        is_selected = s.sl and s.sl[1] == child
                        child_style = s.WIDGET_ON if is_selected else s.WIDGET_OFF
                        child_call = bui.CallPartial(s.edit,(child_type+'widget',child)) if not is_selected else bui.CallPartial(s.show,child)

                    size = (child_width, child_height)
                    s.button(
                        '',
                        size=size,
                        pos=(pos_x, pos_y),
                        call=child_call,
                        style=child_style,
                        corner_radius=5
                    )
                    guess = (
                        ORG['textwidget'](query=child) if child_type == 'text' else
                        child_type
                    )
                    try: guess = bui.Lstr.from_json(guess).evaluate()
                    except: pass
                    chk = s.check(guess,size)
                    s.text(
                        guess,
                        pos=(pos_x+child_width/2, pos_y+child_height/2),
                        scale=s.check(guess,size,0.8),
                        style='normal'
                    )
            else:
                s.text(
                    'No children' if widget.exists() else "I'm dead",
                    pos=(0, (grid_height - header_height)/2),
                    scale=1.5,
                    style=s.EMPTY_STATE
                )
    
    def expand_container(s,g):
        s.deek()
        s.expanded = g
        s.safe_refresh()
    
    def collapse_container(s):
        s.deek()
        s.expanded = None
        s.safe_refresh()
    
    def edit(s,g):
        widget = g[1]
        if not widget.exists():
            bui.getsound('block').play()
            return
        if s.sl == g:
            s.show(widget)
            return
        if s.editor: s.editor.bye()
        s.sl = g
        s.editor = Editor(g)
        s.safe_refresh()
    def show(s,w):
        if not w.exists():
            bui.getsound('block').play()
            return
        s.deek()
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
        wop = bui.getsound('powerup01')
        wop.play()
        bui.apptimer(0.15,wop.stop)
        x,y = s.x,s.y = (600,450)
        s.opacity = 0.7
        s.what, s.widget = g
        snipe = s.widget.get_screen_space_center()
        s.root = ORG['containerwidget'](
            parent=bui.get_special_widget('overlay_stack'),
            size=(x,y),
            background=False,
            scale_origin_stack_offset=snipe,
            transition='in_scale'
        )
        ORG['imagewidget'](
            parent=s.root,
            position=(-x*0.1,-y*0.1),
            size=(x*1.2,y*1.2),
            texture=bui.gettexture('softRect'),
            opacity=s.opacity,
            color=s.COL0
        )
        ORG['imagewidget'](
            parent=s.root,
            position=(-1,-1),
            size=(x,y),
            texture=bui.gettexture('white'),
            color=s.COL0,
            opacity=s.opacity
        )
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
        ORG['textwidget'](
            parent=s.root,
            text=f'{s.what[:-6]} at {hex(id(s.widget))}',
            h_align='center',
            v_align='center',
            maxwidth=dx-20,
            position=(px+dx/2.23,py+dy/4-2),
            color=s.COL3
        )
        fx,fy = x/2-20,y-110
        p0 = ORG['scrollwidget'](
            parent=s.root,
            position=(20,20),
            size=(fx,fy),
            border_opacity=0,
            color=s.COL2
        )
        s.attrs = inspect(ORG[s.what],bad=['edit'])
        ry = max(fy-5,len(s.attrs)*30)
        p1 = ORG['containerwidget'](
            parent=p0,
            background=False,
            size=(fx,ry)
        )
        ORG['imagewidget'](
            parent=p1,
            size=(fx+2,ry*1.5),
            position=(-1,-ry/4),
            texture=bui.gettexture('white'),
            color=s.COL1,
            opacity=s.opacity
        )
        ORG['imagewidget'](
            parent=p1,
            size=(20,ry),
            position=(fx-20+2,0),
            texture=bui.gettexture('white'),
            color=s.COL1,
            opacity=1
        )
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
                w,on_activate_call=bui.CallPartial(s.select,w,a)
            )
            s.kids.append(w)
        s.make()
    def clean(s):
        for _ in s.trash: _.delete()
    def make(s):
        s.clean()
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
                on_activate_call=bui.CallPartial(s.action,_),
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
        if _ == 'Hint':
            if s.sl is None:
                bui.getsound('block').play()
                bui.screenmessage('Select an attribute to grab hints from!',color=s.COL3)
                return
        else: s.clean()
        match _:
            case 'String':
                s.trash.append(ORG['textwidget'](
                    parent=s.root,
                    text='Enter raw text here:',
                    color=s.COL3,
                    maxwidth=s.mx-70,
                    position=(s.mx,s.y-120)
                ))
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
                s.trash.append(ORG['textwidget'](
                    parent=s.root,
                    text='Now select a widget\nfrom the UEye tab',
                    color=s.COL3,
                    maxwidth=s.mx-70,
                    position=(s.mx,s.y-120)
                ))
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
                p0 = ORG['scrollwidget'](
                    parent=s.root,
                    position=(s.mx-11,220),
                    border_opacity=0,
                    size=(s.mx-46,138),
                    color=s.COL2
                )
                s.trash.append(p0)
                all = 52*20
                p1 = ORG['containerwidget'](
                    parent=p0,
                    background=False,
                    size=(s.mx-56,all)
                )
                ORG['imagewidget'](
                    parent=p1,
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    position=(-20,-all/4),
                    size=(s.mx,all*1.5),
                    opacity=s.opacity
                )
                ORG['imagewidget'](
                    parent=p1,
                    texture=bui.gettexture('white'),
                    color=s.COL1,
                    opacity=1,
                    position=(s.mx-63,-all/4),
                    size=(10,all*1.5),
                )
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
                def cckids():
                    f = ORG['buttonwidget']
                    for k in ckids:
                        c = rcol()
                        f(
                            k,
                            color=c,
                            on_activate_call=bui.CallPartial(cset,c)
                        )
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
                cckids()
                cset(rcol())
            case 'Eval':
                s.trash.append(ORG['textwidget'](
                    parent=s.root,
                    text='Enter something to evaluate.\nYou can use globals that are\ndefined in ueye.py',
                    color=s.COL3,
                    maxwidth=s.mx-70,
                    position=(s.mx,s.y-120)
                ))
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
            stack_offset=s.off,
            on_outside_click_call=s.delete
        )
        s.img = ORG['imagewidget'](
            parent=s.root,
            texture=bui.gettexture('achievementOutline'),
            color=(10,0,0),
            opacity=s.opacity
        )
        s.anim(s.width*10)
    def anim(s,i):
        if not s.img: return
        o = -i/2+s.width/2
        ORG['imagewidget'](s.img,size=(i,i),position=(o,o))
        if i <= 100: return
        bui.apptimer(0.01,bui.CallPartial(s.anim,i-25))
    def decay(s):
        if not s.img: return
        if s.dying: return
        s.dying = True
        s.fade(s.opacity)
        bui.apptimer(0.5,s.delete)
    def fade(s,i):
        if not s.img: return
        try: ORG['imagewidget'](s.img,opacity=i)
        except: return
        bui.apptimer(0.01,bui.CallPartial(s.fade,i-0.05))
    def delete(s):
        s.root.delete()

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
        C = UEye
        N = C.__name__
        E = ENT(N,C)
        I = bui.app.devconsole
        I.tabs = [_ for _ in I.tabs if _.name != N]+[E]
        I._tab_instances[N] = s.__class__.INS = E.factory()
        for _ in dir(bui):
            if not (
                _.endswith('widget')
                and '_' not in _
                and 'widget' != _
            ): continue
            ORG[_] = getattr(bui,_)
            setattr(bui,_,getattr(s,_))
        global EYE
        EYE = bui.AppTimer(0.05,s.eye,repeat=True)
    def __getattr__(s,_):
        @wraps(ORG[_])
        def wrapper(*a,**k):
            r = ORG[_](*a,**k)
            if _ == 'containerwidget':
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
