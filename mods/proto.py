# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Proto v1.0 - Your client bot

Experimental. Used for debugging and understanding client to server communication.
Start by sending Proto() in dev console, or via settings UI.
"""

import socket
import babase as ba
import bauiv1 as bui
import bascenev1 as bs

from traceback import format_exc
from threading import Thread
from time import time, sleep
from random import randint
from enum import IntEnum
from json import dumps
from re import match

# static
__version__ = "1.0"
__counter__ = 1

# tools
_snd = lambda s,t=0: (s:=bui.getsound(s)) and s.play() and t and bui.apptimer(t,s.stop)
_say = lambda t: bui.screenmessage(t,color=Theme.TEXT)
_dum = lambda t: dumps(t).encode('utf-8')
_mrf = lambda o,n: (lambda s,r:([None for i in range(len(s))if i<len(s)and s[i]not in n and(s.pop(i),r.append("".join(s)))],[[s.__setitem__(k,c),r.append("".join(s))]if k<len(s)and s[k]!=c else[s.append(c),r.append("".join(s))]if k>=len(s)else None for k,c in enumerate(n)],[(s.pop(),r.append("".join(s)))for _ in range(len(s)-len(n))],r)[-1])(list(o),[o])
_var = lambda s,v=None: (cfg:=bui.app.config) and (s:='proto_'+s) and v is None and cfg.get(s,v) or (cfg.__setitem__(s,v) or cfg.commit())

# global
_incr = 0x20
_inst = None
_info = {}
_logs = []
_sock = None
_thrd = None
_attr = ['addr','port','spec_n','spec_sn','spec_a','spec_d','auth_b','auth_tk','auth_ph','buffer','buffer2','delay']

# visual
class DarkTheme:
    MAIN = (0,0,0)
    TINT = (0.1,0.1,0.1)
    TEXT = (0.8,0.8,0.8)
    BAD = (1,0,0)
    GOOD = (0,1,0)
    INFO = (1,1,0)
    SHADOW = (0,0,0)
    OPACITY = 0.7

class LightTheme:
    MAIN = (1,1,1)
    TINT = (0.7,0.7,0.7)
    TEXT = (0.2,0.2,0.2)
    BAD = (1,0.3,0.3)
    GOOD = (0.3,1,0.3)
    INFO = (1,1,0.3)
    SHADOW = (0.2,0.2,0.2)
    OPACITY = 0.7

Theme = LightTheme

class Log:
    @classmethod
    def text(c,z):
        return Theme.TEXT if z else Theme.MAIN
    @classmethod
    def bg(c,z):
        return [
            Theme.TEXT,
            Theme.MAIN,
            Theme.TINT,
            Theme.BAD,
            Theme.GOOD,
            Theme.INFO
        ][z]
    ME = 0
    HIM = 1
    BASIC = 2
    BAD = 3
    GOOD = 4
    INFO = 5

class Proto:
    def __init__(s):
        s.cache = {}
        global _inst
        _inst = s
        _snd('powerup01',0.15)
        x,y = (450,500)
        ex = 320
        ex2 = 240
        rx = x+ex+ex2
        # root
        s.root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=(rx,y),
            background=False,
            transition='in_left'
        )
        # shadow
        bui.imagewidget(
            parent=s.root,
            position=(-rx*0.1,-y*0.1),
            size=(rx*1.2,y*1.2),
            texture=bui.gettexture('softRect'),
            opacity=Theme.OPACITY,
            color=Theme.SHADOW
        )
        # background
        bui.imagewidget(
            parent=s.root,
            position=(-1,-1),
            size=(rx,y),
            texture=bui.gettexture('white'),
            color=Theme.MAIN,
            opacity=Theme.OPACITY
        )
        # title
        px,py = 90,y-70
        dx,dy = x-110,50
        bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            position=(px,py-2),
            size=(dx,dy+4),
            opacity=Theme.OPACITY
        )
        # title
        s.title = bui.textwidget(
            parent=s.root,
            h_align='center',
            v_align='center',
            maxwidth=dx-60,
            position=(px+dx/2.4,py+dy/4-2),
            color=Theme.TEXT
        )
        # back
        bui.containerwidget(s.root,cancel_button=(
            bui.buttonwidget(
                parent=s.root,
                position=(20,py),
                size=(50,50),
                label=bui.charstr(bui.SpecialChar.BACK),
                text_scale=0.8,
                texture=bui.gettexture('white'),
                color=Theme.TINT,
                textcolor=Theme.TEXT,
                on_activate_call=s.exit,
                enable_sound=False,
                opacity=Theme.OPACITY
            )
        ))
        # kang address
        def kang():
            i = bs.get_connection_to_host_info_2()
            if i is None:
                _say("You're not connected to any server!")
                _snd('block')
                return
            bui.textwidget(s.addr,text=i.address)
            bui.textwidget(s.port,text=str(i.port))
            _snd('gunCocking')
        py -= 70
        bui.buttonwidget(
            parent=s.root,
            position=(20,py),
            size=(50,50),
            label=bui.charstr(bui.SpecialChar.DPAD_CENTER_BUTTON),
            text_scale=0.8,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            textcolor=Theme.TEXT,
            on_activate_call=kang,
            enable_sound=False,
            opacity=Theme.OPACITY
        )
        # address
        zx = 100
        dx = x-zx-130
        s.addr = bui.textwidget(
            parent=s.root,
            position=(96,py-4),
            size=(dx,dy+8),
            editable=True,
            maxwidth=dx,
            max_height=dy,
            v_align='center',
            description="Server address to socket into.\nExample: 127.0.0.1\nEnter",
            glow_type='uniform',
            color=Theme.TEXT,
            allow_clear_button=False,
            text=_info.get('addr','')
        )
        # address hint
        s.addr_hint = bui.textwidget(
            parent=s.root,
            position=(96,py-4),
            size=(dx,dy+8),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Address'
        )
        # port
        s.port = bui.textwidget(
            parent=s.root,
            position=(110+dx,py-4),
            size=(zx,dy+8),
            editable=True,
            maxwidth=zx,
            max_height=dy,
            v_align='center',
            description='Server port to socket into.\nExample: 43210\nEnter',
            glow_type='uniform',
            color=Theme.TEXT,
            allow_clear_button=False,
            text=_info.get('port','')
        )
        # port hint
        s.port_hint = bui.textwidget(
            parent=s.root,
            position=(110+dx,py-4),
            size=(zx,dy+8),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Port'
        )
        # separator
        bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            size=(x-40,4),
            opacity=Theme.OPACITY,
            position=(20,py-20)
        )
        # spec n
        dx = (x-80)/3
        py -= 90
        s.spec_n = bui.textwidget(
            parent=s.root,
            editable=True,
            glow_type='uniform',
            allow_clear_button=False,
            color=Theme.TEXT,
            text=str(_info.get('spec_n','')),
            size=(dx,dy+8),
            maxwidth=dx,
            v_align='center',
            max_height=dy,
            position=(20,py-4),
            description="Client name in spec.\nSpecifically: {'s':{'n':THIS,'sn':'','a':''},'d':''}\nEnter"
        )
        # spec n hint
        s.spec_n_hint = bui.textwidget(
            parent=s.root,
            position=(20,py-4),
            size=(dx,dy+8),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Spec n'
        )
        # spec sn
        s.spec_sn = bui.textwidget(
            parent=s.root,
            editable=True,
            glow_type='uniform',
            allow_clear_button=False,
            color=Theme.TEXT,
            text=str(_info.get('spec_sn','')),
            size=(dx,dy+8),
            maxwidth=dx,
            max_height=dy,
            v_align='center',
            position=(40+dx,py-4),
            description="Client sn in spec.\nSpecifically: {'s':{'n':'','sn':THIS,'a':''},'d':''}\nEnter"
        )
        # spec sn hint
        s.spec_sn_hint = bui.textwidget(
            parent=s.root,
            position=(40+dx,py-4),
            size=(dx,dy+8),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Spec sn'
        )
        # spec a
        s.spec_a = bui.textwidget(
            parent=s.root,
            editable=True,
            glow_type='uniform',
            allow_clear_button=False,
            color=Theme.TEXT,
            text=str(_info.get('spec_a','')),
            size=(dx,dy+8),
            maxwidth=dx,
            v_align='center',
            max_height=dy,
            position=(60+2*dx,py-4),
            description="Client a in spec.\nSpecifically: {'s':{'n':'','sn':'','a':THIS},'d':''}\nEnter"
        )
        # spec a hint
        s.spec_a_hint = bui.textwidget(
            parent=s.root,
            position=(60+2*dx,py-4),
            size=(dx,dy+8),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Spec a'
        )
        py -= 70
        dx = x-116
        # eval spec d
        def ev():
            t = bui.textwidget(query=s.spec_d)
            if not t:
                _say('Write somrthing to eval!')
                _snd('block')
                return
            try: bui.textwidget(s.spec_d,text=str(eval(t)))
            except Exception as e:
                _say(str(e))
                _snd('block')
            else: _snd('gunCocking')
        bui.buttonwidget(
            parent=s.root,
            position=(20,py),
            size=(50,50),
            label=bui.charstr(bui.SpecialChar.PLAY_BUTTON),
            text_scale=0.8,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            textcolor=Theme.TEXT,
            on_activate_call=ev,
            enable_sound=False,
            opacity=Theme.OPACITY
        )
        # spec d
        s.spec_d = bui.textwidget(
            parent=s.root,
            editable=True,
            glow_type='uniform',
            allow_clear_button=False,
            color=Theme.TEXT,
            text=str(_info.get('spec_d','')),
            size=(dx,dy+8),
            maxwidth=dx,
            v_align='center',
            max_height=dy,
            position=(98,py-4),
            description="Client d in spec.\nSpecifically: {'s':{'n':'','sn':'','a':''},'d':THIS}\nEnter"
        )
        # spec d hint
        s.spec_d_hint = bui.textwidget(
            parent=s.root,
            position=(98,py-4),
            size=(dx,dy+8),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Spec d'
        )
        # separator
        bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            size=(x-40,4),
            opacity=Theme.OPACITY,
            position=(20,py-20)
        )
        # auth b
        dx = (x-80)/3
        py -= 90
        s.auth_b = bui.textwidget(
            parent=s.root,
            editable=True,
            glow_type='uniform',
            allow_clear_button=False,
            color=Theme.TEXT,
            text=str(_info.get('auth_b','')),
            size=(dx,dy+8),
            maxwidth=dx,
            v_align='center',
            max_height=dy,
            position=(20,py-4),
            description="Client b in auth.\nSpecifically: {'b':THIS,'tk':'','ph':''}\nEnter"
        )
        # auth b hint
        s.auth_b_hint = bui.textwidget(
            parent=s.root,
            position=(20,py-4),
            size=(dx,dy+8),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Auth b'
        )
        # auth tk
        s.auth_tk = bui.textwidget(
            parent=s.root,
            editable=True,
            glow_type='uniform',
            allow_clear_button=False,
            color=Theme.TEXT,
            text=str(_info.get('auth_tk','')),
            size=(dx,dy+8),
            maxwidth=dx,
            max_height=dy,
            v_align='center',
            position=(40+dx,py-4),
            description="Client tk in auth.\nSpecifically: {'b':'','tk':THIS,'ph':''}\nEnter"
        )
        # auth tk hint
        s.auth_tk_hint = bui.textwidget(
            parent=s.root,
            position=(40+dx,py-4),
            size=(dx,dy+8),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Auth tk'
        )
        # auth ph
        s.auth_ph = bui.textwidget(
            parent=s.root,
            editable=True,
            glow_type='uniform',
            allow_clear_button=False,
            color=Theme.TEXT,
            text=str(_info.get('auth_ph','')),
            size=(dx,dy+8),
            maxwidth=dx,
            v_align='center',
            max_height=dy,
            position=(60+2*dx,py-4),
            description="Client ph in auth.\nSpecifically: {'b':'','tk':'','ph':THIS}\nEnter"
        )
        # auth ph hint
        s.auth_ph_hint = bui.textwidget(
            parent=s.root,
            position=(60+2*dx,py-4),
            size=(dx,dy+8),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Auth ph'
        )
        # separator
        bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            size=(x-40,4),
            opacity=Theme.OPACITY,
            position=(20,py-20)
        )
        # save
        py -= 90
        dx = (x-110)/3
        def save():
            mem = _var('save') or {}
            if mem:
                nam = f'# Save '+str(
                    1 + int(
                        list(mem)[-1].split()[-1]
                    )
                )
            else: nam = '# Save 1'
            buf = {}
            for _ in _attr:
                val = bui.textwidget(query=getattr(s,_))
                if not val: continue
                buf[_] = val
            if not buf:
                _say('Nothing to save!')
                _snd('block')
                return
            mem[nam] = buf
            _var('save',mem)
            _say(f'Saved as {nam}!')
            _snd('gunCocking')
            return True
        bui.buttonwidget(
            parent=s.root,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            textcolor=Theme.TEXT,
            enable_sound=False,
            size=(dx,50),
            position=(23,py),
            label='Save',
            on_activate_call=save
        )
        # memory
        s.memory_b = bui.buttonwidget(
            parent=s.root,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            textcolor=Theme.TEXT,
            enable_sound=False,
            size=(dx,50),
            position=(53+dx,py),
            label='Memory',
            on_activate_call=s.memory
        )
        # connect
        s.esta_button = bui.buttonwidget(
            parent=s.root,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            textcolor=Theme.TEXT,
            enable_sound=False,
            size=(dx,50),
            position=(83+2*dx,py),
            on_activate_call=s.safe_esta
        )
        # splitter
        bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            size=(4,y-36),
            opacity=Theme.OPACITY,
            position=(x,18)
        )
        # packet scroll
        fx = ex-40
        p0 = bui.scrollwidget(
            parent=s.root,
            border_opacity=Theme.OPACITY,
            color=Theme.TINT,
            position=(x+20,y/2+20),
            size=(fx,y/2-40)
        )
        # packet root
        pak = Packet.get()
        all = pak
        ry = len(all)*30
        p1 = bui.containerwidget(
            parent=p0,
            color=Theme.TINT,
            size=(fx,ry),
            background=False
        )
        # packet list
        def add_data(_):
            bui.textwidget(
                s.buffer,
                text=bui.textwidget(
                    query=box
                ) + (
                    _ in pak and
                    getattr(Packet,_).to_bytes().hex()
                    or '??'
                )
            )
            _snd('deek')
        for i,_ in enumerate(all):
            bui.textwidget(
                parent=p1,
                size=(fx,30),
                text=_,
                maxwidth=fx-20,
                v_align='center',
                color=Theme.TEXT,
                position=(0,ry-30-30*i),
                selectable=True,
                glow_type='uniform',
                click_activate=True,
                on_activate_call=bui.CallPartial(add_data,_)
            )
        # separator
        bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            size=(ex-40,4),
            opacity=Theme.OPACITY,
            position=(x+20,y/2)
        )
        dx,dy = ex-40,50
        py = y/2-dy-20
        # buffer box
        s.buffer = bui.textwidget(
            parent=s.root,
            color=Theme.TEXT,
            editable=True,
            glow_type='uniform',
            size=(dx,dy),
            v_align='center',
            allow_clear_button=False,
            position=(x+24,py+2),
            description='Appended first in packet\nExample input: 250b17ff00ff\nEnter',
            maxwidth=dx
        )
        # buffer hint
        s.buffer_hint = bui.textwidget(
            parent=s.root,
            position=(x+24,py+2),
            size=(dx,dy),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Hex header'
        )
        # buffer2 box
        py -= (dy+5)
        s.buffer2 = bui.textwidget(
            parent=s.root,
            color=Theme.TEXT,
            editable=True,
            glow_type='uniform',
            size=(dx,dy),
            v_align='center',
            allow_clear_button=False,
            position=(x+24,py+2),
            maxwidth=dx,
            description='Appened after hex data as bytes\nExample input: {"b":"123456","a":"foo"}blarg!\nEnter'
        )
        # buffer2 hint
        s.buffer2_hint = bui.textwidget(
            parent=s.root,
            position=(x+24,py+2),
            size=(dx,dy),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Tailing data'
        )
        # delay box
        py -= (dy+3)
        s.delay = bui.textwidget(
            parent=s.root,
            size=(dx,dy),
            position=(x+24,py-1),
            color=Theme.TEXT,
            glow_type='uniform',
            allow_clear_button=False,
            editable=True
        )
        # delay hint
        s.delay_hint = bui.textwidget(
            parent=s.root,
            position=(x+24,py+2),
            size=(dx,dy),
            v_align='center',
            color=(*Theme.TEXT,Theme.OPACITY),
            text='Delay'
        )
        # send
        def safe_send():
            try: send()
            except Exception as e:
                s.log([str(e),format_exc()],Log.BAD)
            _snd('deek')
        def wrap(t):
            for old,new in {
                '{incr}': _incr.to_bytes(3,'little').hex(),
                '{me}': _info['me'],
                '{him}': _info['him'],
                '{spec_size}': f"{len(_info['spec']):x}",
                '{auth_size}': f"{len(_info['auth']):x}"
            }.items(): t = t.replace(old, new)
            return t
        def wrap2(t):
            for old,new in {
                '{spec}': _info['spec'].decode(),
                '{auth}': _info['auth'].decode()
            }.items(): t = t.replace(old,new)
            return t
        def send():
            if not _sock:
                _say('Socket is not active!')
                _snd('block')
                return
            # hex head
            out = bytes.fromhex(
                wrap(
                    bui.textwidget(
                        query=s.buffer
                    ).strip()
                )
            )
            # raw tail
            out += wrap2(bui.textwidget(
                query=s.buffer2
            )).encode()
            # finally
            s.log(out,Log.ME)
            _sock.sendto(
                out,
                (_info['addr'],int(_info['port']))
            )
        py -= dy
        bui.buttonwidget(
            parent=s.root,
            label='Send',
            position=(x+30,py-2),
            size=(dx-18,dy-14),
            color=Theme.TINT,
            textcolor=Theme.TEXT,
            on_activate_call=safe_send,
            enable_sound=False,
            texture=bui.gettexture('white')
        )
        # splitter
        bui.imagewidget(
            parent=s.root,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            size=(4,y-36),
            opacity=Theme.OPACITY,
            position=(x+ex,18)
        )
        # log scroll
        s.log_next = 0
        s.log_x = ex2-40
        s.log_y = y-90
        px,py = x+ex+20,70
        p0 = bui.scrollwidget(
            border_opacity=Theme.OPACITY,
            position=(px,py),
            size=(s.log_x,s.log_y),
            color=Theme.TINT,
            parent=s.root
        )
        # log root
        s.log_root = bui.containerwidget(
            parent=p0,
            background=False
        )
        # clear logs
        def clear_logs():
            _logs.clear()
            s.log_next = 0
            for _ in s.log_root.get_children(): _.delete()
            bui.containerwidget(s.log_root,size=(s.log_x,0))
        bui.buttonwidget(
            parent=s.root,
            texture=bui.gettexture('white'),
            enable_sound=False,
            on_activate_call=clear_logs,
            label='Clear',
            position=(px+8,20),
            size=(s.log_x-14,dy-14),
            color=Theme.TINT,
            textcolor=Theme.TEXT
        )
        # log note
        s.cache['log_note'] = type('',(object,),{'__del__':(
            bui.textwidget(
                parent=s.root,
                position=(
                    x+ex+s.log_x/2-5,
                    y-s.log_y/2-30
                ),
                color=(*Theme.TINT,Theme.OPACITY),
                text='No logs',
                h_align='center',
                v_align='center'
            ).delete
        )})()
        # finally
        s.catch_up()
        s.cache['spy'] = bui.AppTimer(0.01,s.safe_spy,repeat=True)
        if not _info.get('ready',0):
            _info['ready'] = 1
            s.gather()
        # debug
        def debug():
            if 0:
                # animation
                global _sock
                _sock = 1
                _info['me'] = _info['him'] = '69'
                s.update()
            if 1:
                # logging
                try: 1+"BrotherBoard"
                except Exception as e: s.log([str(e),format_exc()],Log.BAD)
                s.log((
                    (10*('BrotherBoard should touch grass!'*5+'\n'))
                ).encode(),Log.ME)
                s.log('Utterly amazing! Very nice!',Log.GOOD)
        0 and bui.apptimer(2,debug)
    def catch_up(s):
        # list logs
        for z,t in _logs: s.log(t,z,dry=True)
        # set texts
        s.sync()
        # update online state
        s.update(dry=True)
    def log(s,t,z=2,dry=False):
        if z in [Log.ME,Log.HIM]: real = t.hex(' ')
        elif z == Log.BAD: real = t[0]
        else: real = t
        if not dry: _logs.append((z,t))
        if not s.root: return
        # background
        bui.imagewidget(
            parent=s.log_root,
            texture=bui.gettexture('white'),
            color=Log.bg(z),
            size=(s.log_x-15,30),
            position=(-5,s.log_next*30),
            opacity=Theme.OPACITY
        )
        # text
        if len(real) >= 30: tx = real[:30]+bui.charstr(bui.SpecialChar.RIGHT_ARROW)
        else: tx = real
        vc = bui.textwidget(
            parent=s.log_root,
            position=(0,s.log_next*30),
            text=tx,
            color=(*Log.text(z),Theme.OPACITY),
            size=(s.log_x,30),
            selectable=True,
            click_activate=True,
            glow_type='uniform',
            v_align='center',
            maxwidth=s.log_x-20
        )
        bui.textwidget(vc,on_activate_call=ba.CallPartial(s.expand,t,z,vc))
        # finally
        bui.containerwidget(s.log_root,size=(s.log_x,max(s.log_next*30+30,s.log_y-15)),visible_child=vc)
        s.log_next += 1
        s.cache.pop('log_note',0)
    def tran(s,w,o,t,f,h):
        s.cache[str(w)] = [0,_mrf(o,t),bui.AppTimer(0.03,ba.CallPartial(s.safe_anim,w),repeat=True),f,h]
    def safe_anim(s,w):
        try: s.anim(w)
        except: s.cache.pop(str(w),0)
    def anim(s,w):
        g = s.cache[str(w)]
        i,a,_,f,h = g
        f(w,**{h:a[i]})
        i += 1
        if i >= len(a):
            s.cache.pop(str(w),0)
            return
        g[0] = i
    def update(s,dry=False):
        up = bool(_sock)
        # title
        t = f'Proto v{__version__} - '
        if up: t += f"Online! ({_info['me']} -> {_info['him']})"
        else: t += 'Ready.'
        dry and bui.textwidget(s.title,text=t) or s.tran(s.title,bui.textwidget(query=s.title),t,bui.textwidget,'text')
        # establish button
        a = ['Establish','Terminate']
        dry and bui.buttonwidget(s.esta_button,label=a[up]) or s.tran(s.esta_button,a[not up],a[up],bui.buttonwidget,'label')
    def sync(s):
        for _ in _attr:
            if (v:=_info.get(_,None)) is None: continue
            bui.textwidget(getattr(s,_),text=v)
    def gather(s):
        for _ in _attr:
            _info[_] = bui.textwidget(query=getattr(s,_)).strip()
    def exit(s):
        bui.containerwidget(s.root,transition='out_left')
        _snd('laser')
        s.cache.clear()
    def safe_spy(s):
        try: s.spy()
        except: s.cache['spy'] = None
    def spy(s):
        for _ in _attr:
            if (
                (new:=bui.textwidget(
                    query=getattr(s,_)
                )) != s.cache.get(_,None)
            ):
                s.cache[_] = new
                bui.textwidget(
                    getattr(s,_+'_hint'),
                    color=(
                        *Theme.TEXT,
                        int(not bool(new))
                        and Theme.OPACITY
                    )
                )
    def memory(s):
        _snd('powerup01',0.15)
        x,y = (160,240)
        ox,oy = s.memory_b.get_screen_space_center()
        bye = lambda z=1: (z and _snd('laser')) or bui.containerwidget(root,transition='out_scale')
        # root
        root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=(x,y),
            scale=1.3,
            background=False,
            transition='in_scale',
            scale_origin_stack_offset=(ox,oy),
            stack_offset=(ox,oy/1.8),
            on_outside_click_call=bye
        )
        # shadow
        bui.imagewidget(
            parent=root,
            position=(-x*0.1,-y*0.1),
            size=(x*1.2,y*1.2),
            texture=bui.gettexture('softRect'),
            opacity=Theme.OPACITY,
            color=Theme.SHADOW
        )
        # background
        bui.imagewidget(
            parent=root,
            position=(-1,-1),
            size=(x,y),
            texture=bui.gettexture('white'),
            color=Theme.MAIN,
            opacity=Theme.OPACITY
        )
        # footing
        bui.buttonwidget(
            parent=root,
            size=(x,y),
            enable_sound=False,
            texture=bui.gettexture('empty'),
            opacity=0,
            selectable=False,
            label=''
        )
        # mem scroll
        fx,fy = (x-20,y-60)
        p0 = bui.scrollwidget(
            border_opacity=Theme.OPACITY,
            parent=root,
            size=(fx,fy),
            position=(10,50),
            color=Theme.TINT
        )
        # mem root
        mem = _var('save') or {}
        ry = max(len(mem)*30,fy-15)
        p1 = bui.containerwidget(
            parent=p0,
            background=False,
            size=(fx,ry)
        )
        # selection
        cache = {}
        def sl(t):
            if (w:=cache.get('on')):
                bui.textwidget(w,color=Theme.TEXT)
            cache['on'] = t
            bui.textwidget(t,color=Theme.MAIN)
        # list mem
        def mk():
            for _ in p1.get_children(): _.delete()
            for i,_ in enumerate(mem):
                t = bui.textwidget(
                    parent=p1,
                    position=(0,ry-30-30*i),
                    text=_,
                    maxwidth=fx,
                    selectable=True,
                    click_activate=True,
                    color=Theme.TEXT,
                    glow_type='uniform',
                    size=(fx,30)
                )
                bui.textwidget(t,on_activate_call=bui.CallPartial(sl,t))
        mk()
        # delete
        no = lambda: _say('Select something!') or _snd('block')
        def rm():
            if not (o:=cache.get('on',0)): no(); return
            mem.pop((q:=bui.textwidget(query=o)))
            _var('save',mem)
            _say(f'Deleted {q}!')
            _snd('laser')
            mk()
        dx = x/2-20
        bui.buttonwidget(
            parent=root,
            position=(10,10),
            color=Theme.TINT,
            textcolor=Theme.TEXT,
            texture=bui.gettexture('white'),
            size=(dx,30),
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_CROSS_BUTTON)+' ',
            enable_sound=False,
            on_activate_call=rm
        )
        # load
        def ld():
            if not (o:=cache.get('on',0)): no(); return
            _info.update(mem[(q:=bui.textwidget(query=o))])
            _say(f'Loaded {q}!')
            _snd('gunCocking')
            bye(0)
            s.sync()
        bui.buttonwidget(
            parent=root,
            position=(dx+25,10),
            color=Theme.TINT,
            textcolor=Theme.TEXT,
            texture=bui.gettexture('white'),
            size=(dx,30),
            label=bui.charstr(bui.SpecialChar.PLAY_STATION_CIRCLE_BUTTON)+' ',
            enable_sound=False,
            on_activate_call=ld
        )
    def expand(s,t,z,src):
        _snd('powerup01',0.15)
        real = t
        if z == Log.ME or z == Log.HIM:
            try: rep = '\n'.join((3*' ').join((3*' ').join(chr(b) if 32 <= b < 127 else '.' for b in t[i:i+8]) for i in range(j, min(j+16, len(t)), 8)) for j in range(0, len(t), 16))
            except: z = -1
            else: real = '\n'.join((' ').join(t[i:i+8].hex(' ') for i in range(j, min(j+16, len(t)), 8)) for j in range(0, len(t), 16))
        elif z == Log.BAD:
            real = t[0]
            rep = t[1]
        x,y = (650,(z == Log.ME or z == Log.HIM or z == Log.BAD) and 400 or 200)
        ox,oy = src.get_screen_space_center()
        bye = lambda z=1: (z and _snd('laser')) or bui.containerwidget(root,transition='out_scale')
        # root
        root = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=(x,y),
            background=False,
            transition='in_scale',
            scale_origin_stack_offset=(ox,oy),
            on_outside_click_call=bye
        )
        # shadow
        bui.imagewidget(
            parent=root,
            position=(-x*0.1,-y*0.1),
            size=(x*1.2,y*1.2),
            texture=bui.gettexture('softRect'),
            opacity=Theme.OPACITY,
            color=Theme.SHADOW
        )
        # background
        bui.imagewidget(
            parent=root,
            position=(-1,-1),
            size=(x,y),
            texture=bui.gettexture('white'),
            color=Theme.MAIN,
            opacity=Theme.OPACITY
        )
        # footing
        bui.buttonwidget(
            parent=root,
            size=(x,y),
            enable_sound=False,
            texture=bui.gettexture('empty'),
            opacity=0,
            selectable=False,
            label=''
        )
        # hex scroll
        dx,dy = x-40,160
        py = 20
        p0 = bui.scrollwidget(
            border_opacity=Theme.OPACITY,
            parent=root,
            position=(20,20),
            size=(dx,dy),
            color=Theme.TINT
        )
        # hex box (references?)
        ry = bui.get_string_height(real,suppress_warning=True)
        ry = max(ry,dy-15)
        p1 = bui.containerwidget(
            parent=p0,
            background=False,
            size=(dx,ry)
        )
        # hex bg
        bui.imagewidget(
            parent=p1,
            size=(dx-17,ry),
            color=Log.bg(z),
            texture=bui.gettexture('white'),
            opacity=Theme.OPACITY
        )
        # hex text
        bui.textwidget(
            parent=p1,
            text=real,
            color=(*Log.text(z),Theme.OPACITY),
            position=(5,0),
            selectable=True,
            size=(dx,ry),
            click_activate=True,
            glow_type='uniform',
            on_activate_call=ba.CallPartial(
                bui.clipboard_set_text,
                t.hex() if (z == Log.ME or z == Log.HIM) else real
            )
        )
        if z != Log.ME and z != Log.HIM and z != Log.BAD: return
        # separator
        py += dy+20
        bui.imagewidget(
            parent=root,
            texture=bui.gettexture('white'),
            color=Theme.TINT,
            size=(x-40,4),
            opacity=Theme.OPACITY,
            position=(20,py)
        )
        # repr scroll
        py += 20
        p0 = bui.scrollwidget(
            border_opacity=Theme.OPACITY,
            parent=root,
            position=(20,py),
            size=(dx,dy),
            color=Theme.TINT
        )
        # repr box
        if z == Log.ME or z == Log.HIM:
            ry = bui.get_string_height(rep,suppress_warning=True)
            ry = max(ry,dy-15)
            p1 = bui.containerwidget(
                parent=p0,
                background=False,
                size=(dx,ry)
            )
            # repr bg
            bui.imagewidget(
                parent=p1,
                size=(dx-17,ry),
                color=Log.bg(z),
                texture=bui.gettexture('white'),
                opacity=Theme.OPACITY
            )
            # repr text
            bui.textwidget(
                parent=p1,
                text=rep,
                color=(*Log.text(z),Theme.OPACITY),
                position=(5,0),
                selectable=True,
                click_activate=True,
                size=(dx,ry),
                glow_type='uniform',
                on_activate_call=ba.CallPartial(
                    bui.clipboard_set_text,
                    t.decode('utf-8', errors='replace').translate(str.maketrans({c: '.' for c in range(0x10000) if not chr(c).isprintable()}))
                )
            )
        elif z == Log.BAD:
            rx = bui.get_string_width(rep,suppress_warning=True)
            ry = bui.get_string_height(rep,suppress_warning=True)
            mw = dx - 30
            if rx > mw:
                scale_factor = mw / rx
                actual_height = ry * scale_factor
            else:
                actual_height = ry

            actual_height = max(actual_height, dy - 15)

            p1 = bui.containerwidget(
                parent=p0,
                background=False,
                size=(dx, actual_height)
            )
            # repr bg
            bui.imagewidget(
                parent=p1,
                size=(dx-15, actual_height),
                color=Log.bg(z),
                texture=bui.gettexture('white'),
                opacity=Theme.OPACITY
            )
            # repr text
            bui.textwidget(
                parent=p1,
                text=rep,
                color=(*Log.text(z), Theme.OPACITY),
                position=(5, 0),
                selectable=True,
                maxwidth=mw,
                click_activate=True,
                size=(dx, actual_height),
                glow_type='uniform',
                on_activate_call=ba.CallPartial(
                    bui.clipboard_set_text,
                    rep
                )
            )
    def safe_esta(s):
        if _info.get('busy',0):
            _say('Already Establishing, wait.')
            _snd('block')
            return
        _info['busy'] = s.esta()
    def esta(s):
        if _sock:
            s.log('Terminating',Log.INFO)
            _snd('deek')
            s.cleanup()
            s.update()
            s.log('Terminated',Log.GOOD)
            return
        s.gather()
        # addr
        if not _info.get('addr',0):
            _say('Enter an address!')
            _snd('block')
            return
        # port
        if (port:=_info.get('port','')):
            try: int(port)
            except:
                _say('Port must be an integer!')
                _snd('block')
                return
        else:
            _say('Enter a port!')
            _snd('block')
            return
        # build
        spec = s.build_spec()
        auth = s.build_auth()
        # start thread
        global _thrd
        _thrd = Thread(
            target=lambda:s.safe_connect(spec,auth),
            daemon=True
        )
        _thrd.start()
        _snd('dingSmall')
        s.log('Establishing',Log.INFO)
        return True
    def build_spec(s):
        _info['spec'] = r = _dum({
            's':dumps({
                'n':_info['spec_n'],
                'sn':_info['spec_sn'],
                'a':_info['spec_a']
            }),
            'd':_info['spec_d']
        })
        return r
    def build_auth(s):
        _info['auth'] = r = _dum({
            'b':(auth_b:=_info['auth_b']).isdigit() and int(auth_b) or auth_b,
            'tk':_info['auth_tk'],
            'ph':_info['auth_ph']
        })
        return r
    def safe_connect(s,*a):
        try: s.connect(*a)
        except Exception as e:
            ba.pushcall(ba.CallPartial(s.log,[str(e),format_exc()],Log.BAD),from_other_thread=True)
            ba.pushcall(s.cleanup,from_other_thread=True)
            ba.pushcall(ba.CallPartial(_snd,'dingSmall'),from_other_thread=True)
        else: ba.pushcall(ba.CallPartial(_snd,'dingSmallHigh'),from_other_thread=True)
        _info['busy'] = False
    def connect(s,spec,auth):
        _log = lambda t,c=2: (
            ba.pushcall(
                ba.CallPartial(s.log,t,c),
                from_other_thread=True
            )
        )
        _com = lambda d: (
            (_sock.sendto(d,(addr,port)) or 1) and
            _log(d,Log.ME)
        )
        _get = lambda s: (
            (d:=_sock.recvfrom(s)[0]),
            _log(d,Log.HIM)
        ) and d
        _hex = lambda t: bytes.fromhex(t)
        _pak = lambda t: getattr(Packet,t).to_bytes()
        addr = _info['addr']
        port = int(_info['port'])
        global _sock
        # create socket
        _log('Creating socket')
        _sock = socket.socket(bui.get_ip_address_type(addr), socket.SOCK_DGRAM)
        _sock.settimeout(5.0)
        # ping first
        _log('Pinging')
        ping_start = time()
        _com(_pak('P_SIMPLE_PING'))
        data, recv_addr = _sock.recvfrom(10)

        if (
            data != _pak('P_SIMPLE_PONG')
            or recv_addr[0] != addr
        ): _log('Ping failed!',Log.ERROR); return

        ping_ms = (time() - ping_start) * 1000
        _log(f'Pong! {ping_ms:.1f}ms',Log.GOOD)
        # send handshake
        _info['me'] = me = f'{(71 + randint(0, 150)):02x}'
        _log(f"Trying '{me}'")
        _com(
            _pak('P_CLIENT_REQUEST') +
            _hex('21') + #TODO define these
            _hex('00') +
            _hex(me) +
            ba.app_instance_uuid().encode()
        )
        # handle
        _tmp = None
        while not (shake:=_get(1024)).startswith(_pak('P_CLIENT_ACCEPT')):
            if _tmp == shake: continue
            elif shake.startswith(_pak('P_CLIENT_DENY_PARTY_FULL')):
                _log('Waiting (party full)')
            elif shake.startswith(_pak('P_CLIENT_DENY_ALREADY_IN_PARTY')):
                _log('Waiting (already in party)')
            elif shake.startswith(_pak('P_CLIENT_DENY')):
                _log('Still waiting')
            elif shake.startswith(_pak('P_CLIENT_DENY_VERSION_MISMATCH')):
                raise Exception('Version mismatch')
            else:
                raise Exception('Unexpected response: '+shake.hex(' '))
            _tmp = shake
            sleep(1)
        del _tmp
        # shake back
        _info['him'] = him = f'{shake[1]:02x}'
        _log(f"Established! {me} -> {him}",Log.GOOD)
        # flush host info
        _log('Flushing host info')
        _get(1024)
        # send spec
        _log('Sending spec')
        _com(
            _pak('P_CLIENT_GAMEPACKET_COMPRESSED') +
            _hex(him) +
            _hex('10') +
            _hex('21') +
            _hex('00') +
            spec
        )
        # send auth
        _log('Sending auth')
        _com(
            _pak('P_CLIENT_GAMEPACKET_COMPRESSED') +
            _hex(him) +
            _hex('11') +
            _hex('f0') +
            _hex('ff') +
            _hex('f0') +
            _hex('ff') +
            _hex('00') +
            _hex('12') +
            auth
        )
        # send empty packet
        _log('Sending empty packet')
        _com(
            _pak('P_CLIENT_GAMEPACKET_COMPRESSED') +
            _hex(him) +
            _hex('11') +
            _hex('f1') +
            _hex('ff') +
            _hex('f0') +
            _hex('ff') +
            _hex('00') +
            _hex('15') +
            _dum({})
        )
        # final shake
        _log('Sending final shake')
        _com(
            _pak('P_CLIENT_GAMEPACKET_COMPRESSED') +
            _hex(him) +
            _hex('11') +
            _hex('f2') +
            _hex('ff') +
            _hex('f0') +
            _hex('ff') +
            _hex('00') +
            _hex('03')
        )
        # flush stuff
        _log('Flushing party info')
        _get(1024)
        _get(9)
        # keepalive
        _log('Starting keepalive service')
        def keepalive():
            global _incr
            _incr = (_incr+32) & 0xFFFFFF
            _sock.sendto(
                _pak('P_CLIENT_GAMEPACKET_COMPRESSED') +
                _hex(him) +
                _pak('SP_KEEPALIVE') +
                _incr.to_bytes(3,'little'),
                (addr, port)
            )
        ba.pushcall(bui.CallPartial(
            s.pack_timer,
            'keepalive',
            0.1,
            keepalive,
            repeat=True
        ),from_other_thread=True)
        # listener
        _log('Starting listener')
        pfix = (
            _pak('P_HOST_GAMEPACKET_COMPRESSED') +
            _hex(me) +
            _pak('SP_MESSAGE')
        )
        chat = Packet.M_CHAT.to_bytes()
        def listener():
            resp = _sock.recvfrom(1024)[0]
            ty = resp[0]
            if ty in Packet:
                print(resp.hex(' '),resp)
        ba.pushcall(bui.CallPartial(
            s.pack_timer,
            'listener',
            0.01,
            listener,
            repeat=True
        ),from_other_thread=True)
        # register disconnect
        def disconnect():
            _sock.sendto(
                _pak('P_DISCONNECT_FROM_CLIENT_REQUEST') +
                _hex(him),
                (addr, port)
            )
            s.log('Disconnecting')
        _info['disconnect'] = disconnect
        # finally
        ba.pushcall(s.update,from_other_thread=True)
        _log('Connected!',Log.GOOD)
    def pack_timer(s,n,*a,**kw):
        _info[n] = bui.AppTimer(*a,**kw)
    def cleanup(s):
        global _sock, _thrd, _incr
        # stop services
        _info['keepalive'] = None
        _info['listener'] = None
        # reset
        _info.pop('disconnect',lambda:0)()
        _sock.close()
        _sock = None
        _thrd.join()
        _thrd = None
        _incr = 0x20

class Packet(IntEnum):
    @classmethod
    def get(cls):
        return [p.name for p in cls]
    def to_bytes(self):
        return bytes([self.value])
    P_REMOTE_PING = 0
    P_REMOTE_PONG = 1
    P_REMOTE_ID_REQUEST = 2
    P_REMOTE_ID_RESPONSE = 3
    P_REMOTE_DISCONNECT = 4
    P_REMOTE_STATE = 5
    P_REMOTE_STATE_ACK = 6
    P_REMOTE_DISCONNECT_ACK = 7
    P_REMOTE_GAME_QUERY = 8
    P_REMOTE_GAME_RESPONSE = 9
    P_REMOTE_STATE2 = 10
    P_SIMPLE_PING = 11
    P_SIMPLE_PONG = 12
    P_JSON_PING = 13
    P_JSON_PONG = 14
    P_POKE = 21
    P_HOST_QUERY = 22
    P_HOST_QUERY_RESPONSE = 23
    P_CLIENT_REQUEST = 24
    P_CLIENT_ACCEPT = 25
    P_CLIENT_DENY = 26
    P_CLIENT_DENY_VERSION_MISMATCH = 27
    P_CLIENT_DENY_ALREADY_IN_PARTY = 28
    P_CLIENT_DENY_PARTY_FULL = 29
    P_DISCONNECT_FROM_CLIENT_REQUEST = 32
    P_DISCONNECT_FROM_CLIENT_ACK = 33
    P_DISCONNECT_FROM_HOST_REQUEST = 34
    P_DISCONNECT_FROM_HOST_ACK = 35
    P_CLIENT_GAMEPACKET_COMPRESSED = 36
    P_HOST_GAMEPACKET_COMPRESSED = 37
    SP_HANDSHAKE = 15
    SP_HANDSHAKE_RESPONSE = 16
    SP_MESSAGE = 17
    SP_MESSAGE_UNRELIABLE = 18
    SP_DISCONNECT = 19
    SP_KEEPALIVE = 20
    M_SESSION_RESET = 0
    M_SESSION_COMMANDS = 1
    M_SESSION_DYNAMICS_CORRECTION = 2
    M_NULL = 3
    M_REQUEST_REMOTE_PLAYER = 4
    M_ATTACH_REMOTE_PLAYER = 5
    M_DETACH_REMOTE_PLAYER = 6
    M_REMOTE_PLAYER_INPUT_COMMANDS = 7
    M_REMOVE_REMOTE_PLAYER = 8
    M_PARTY_ROSTER = 9
    M_CHAT = 10
    M_PARTY_MEMBER_JOINED = 11
    M_PARTY_MEMBER_LEFT = 12
    M_MULTIPART = 13
    M_MULTIPART_END = 14
    M_CLIENT_PLAYER_PROFILES = 15
    M_ATTACH_REMOTE_PLAYER_2 = 16
    M_HOST_INFO = 17
    M_CLIENT_INFO = 18
    M_KICK_VOTE = 19
    M_JMESSAGE = 20
    M_CLIENT_PLAYER_PROFILES_JSON = 21

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(ba.Plugin):
    has_settings_ui = lambda s: True
    show_settings_ui = lambda s,b=0: Proto()
    def __init__(s):
        # dumb workaround
        import _babase as _ba
        a = 'dev_console_add_python_terminal'
        o = getattr(_ba,a)
        def f(*a,**k):
            try: r = o(*a,**k)
            except RuntimeError: pass
            else: return r
        setattr(_ba,a,f)
        # catch input
        pipe = lambda t: t.lower() == 'proto()' and (
            _ba.set_dev_console_input_text('') or
            Proto()
        )
        from babase._ui import DevConsoleStringEditAdapter as A
        a = '_do_apply'
        p = getattr(A,a)
        setattr(A,a,lambda z,t: (p(z,t),pipe(t)))
        print(f'Proto v{__version__} ({__counter__}) - Start by writing Proto() here or via settings ui')
        # debug
        bui.apptimer(1,Proto)
