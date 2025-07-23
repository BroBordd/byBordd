# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Replay v1.0 - Look again

Simple replay manager.
Adds a button to pause menu.
Read code to know more.
"""

from babase import Plugin
from bauiv1 import (
    buttonwidget as obw,
    containerwidget as ocw,
    scrollwidget as sw,
    textwidget as otw,
    imagewidget as iw,
    spinnerwidget as spin,
    get_special_widget as gsw,
    get_replays_dir as rdir,
    gettexture as gt,
    getsound as gs,
    fade_screen as fade,
    screenmessage as push,
    clipboard_set_text as COPY,
    get_virtual_screen_size as res,
    apptimer as teck,
    AppTimer as tock,
    charstr as cs,
    SpecialChar as sc,
    Call,
    app
)
from bascenev1 import (
    set_replay_speed_exponent as SET,
    get_replay_speed_exponent as GET,
    new_replay_session as PLAY,
    resume_replay as RESUME,
    pause_replay as PAUSE,
    seek_replay as SEEK,
    is_in_replay as ON
)
from time import time, strftime, gmtime
from os.path import join, dirname
from random import uniform as uf
from os import listdir as ls
from threading import Thread
from struct import unpack
from io import BytesIO

class Replay:
    COL1 = (0.18,0.18,0.18)
    COL2 = (1,1,1)
    COL3 = (0,1,0)
    COL4 = (0,1,1)
    BUSY = False
    @classmethod
    def BUS(c,b=None):
        if b is None: return c.BUSY
        c.BUSY = b
    def __init__(s,source=None):
        s.sl = s.rn = s.buf = None
        s.p = s.cw(
            src=source.get_screen_space_center(),
            p=GOS(),
            size=(400,500),
            oac=lambda:(ocw(s.p,transition='out_scale' if source and source.exists() else 'out_left'),s.snd('laser'),s.trs.stop())
        )
        s.trs = s.snd('powerup01')
        s.tw(
            p=s.p,
            h_align='center',
            text='Replay',
            pos=(175,460),
            scale=2
        )
        sy = 360
        p1 = sw(
           parent=s.p,
           size=(sy,sy),
           position=(25,80)
        )
        s.rd = rdir()
        a = [_ for _ in ls(s.rd) if _.endswith('.brp')]
        v = 30*len(a)
        p2 = ocw(
            parent=p1,
            background=False,
            size=(sy,v)
        )
        s.kids = []
        for i,_ in enumerate(a):
            t = s.tw(
                p=p2,
                click_activate=True,
                selectable=True,
                pos=(0,v-30*i-30),
                text=_,
                maxwidth=sy,
                size=(sy,30),
                color=s.COL2,
                oac=Call(s.hl,i,_)
            )
            s.kids.append(t)
        s.runb = None
        for _ in range(3):
            b = s.bw(
                p=s.p,
                pos=(25+120*_,30),
                size=(120,40),
                label=['Show','Copy','Run'][_],
                oac=Call(s.con,[s.show,s.copy,s.play][_]),
                icon=gt(['folder','file','nextLevelIcon'][_])
            )
            s.runb = b
    def snd(s,t):
        h = gs(t)
        h.play()
        teck(uf(0.14,0.17),h.stop)
        return h
    def get(s):
        return join(s.rd,s.rn)
    def copy(s):
        s.snd('dingSmallHigh')
        COPY(s.get())
        push('Copied replay path to clipboard!',color=s.COL3)
    def show(s):
        gs('ding').play()
        push(s.get(),color=s.COL3)
    def con(s,f):
        if s.sl is None: BTW('Select a replay!'); return
        if ON(): BTW('A replay is already running!'); return
        return f()
    def hl(s,i,n):
        s.sl = i
        s.rn = n
        [otw(_,color=s.COL2) for _ in s.kids]
        otw(s.kids[i],color=s.COL3)
    def play(s):
        if s.BUS(): return
        s.BUS(True)
        gs('deek').play()
        s.load()
    def load(s):
        c = s.cw(
            src=s.runb.get_screen_space_center(),
            size=(300,160),
            p=GOS()
        )
        s.tw(
            p=c,
            text='Run',
            pos=(125,110),
            h_align='center',
            scale=1.4
        )
        spin(
            parent=c,
            size=60,
            position=(75,45)
        )
        s.st = s.tw(
            p=c,
            text='Processing...',
            pos=(115,32)
        )
        Thread(target=s.calc).start()
        s.spy(s.calc2)
    def calc(s):
        s.buf = DBRP(s.get(),_H())
    def calc2(s,d):
        otw(s.st,text='Starting...')
        Thread(target=Call(s.calc3,d)).start()
        s.spy(s._play)
    def calc3(s,d):
        s.buf = GRD(d)
    def spy(s,f,i=60):
        if not i:
            s.buf = None
            f(None)
            return
        if s.buf:
            b = s.buf
            s.buf = None
            f(b)
            return
        teck(0.5,Call(s.spy,f,i-1))
    def _play(s,t):
        SET(0)
        fade(1)
        Player(path=s.get(),duration=t)
        s.BUS(False)
    bw = lambda s,p=None,oac=None,pos=None,**k: obw(
        parent=p,
        color=s.COL1,
        textcolor=s.COL2,
        on_activate_call=oac,
        position=pos,
        button_type='square',
        enable_sound=False,
        **k
    )
    cw = lambda s,p=None,pos=None,src=None,oac=None,**k: ocw(
        color=s.COL1,
        parent=p,
        position=pos,
        scale_origin_stack_offset=src,
        transition='in_scale',
        on_outside_click_call=oac,
        **k
    )
    tw = lambda s,color=None,oac=None,p=None,pos=None,**k: otw(
        parent=p,
        position=pos,
        color=color or s.COL2,
        on_activate_call=oac,
        **k
    )

class Player:
    COL0 = (0.5,0,0)
    COL1 = (1,0,0)
    COL2 = (0.5,0.5,0)
    COL3 = (1,1,0)
    COL4 = (0,0.5,0)
    COL5 = (0,1,0)
    COL6 = (0,0.5,0.5)
    COL7 = (0,1,1)
    COL8 = (0.6,0.6,0.6)
    COL9 = (8,0,0)
    def __init__(s,path,duration):
        s.du = duration*0.97
        s.ds = s.du / 1000
        s.ps = False
        s.pr = 0
        s.kids = []
        PLAY(path)
        x,y = res()
        sy = 80
        p = ocw(
            size=(x,sy),
            stack_offset=(0,-y/2+sy/2),
            background=False
        )
        iw(
            parent=p,
            texture=gt('black'),
            size=(x+3,sy+5),
            position=(0,-2),
            opacity=0.4
        )
        # buttons
        s.bw(
            p=p,
            pos=(x-65,15),
            size=(50,50),
            color=s.COL0,
            oac=s.bye
        )
        c = s.COL1
        iw(
            parent=p,
            texture=gt('crossOut'),
            color=(c[0]*10,c[1]*10,c[2]*10),
            position=(x-60,20),
            size=(40,40)
        )
        for _ in range(2):
            a = [
                'FAST_FORWARD_BUTTON',
                'REWIND_BUTTON'
            ][_]
            pos = (x-130-260*_,15)
            s.bw(
                p=p,
                pos=pos,
                size=(50,50),
                color=s.COL2,
                oac=Call(s.boost,[1,-1][_]),
                repeat=True
            )
            otw(
                parent=p,
                text=cs(getattr(sc,a)),
                color=s.COL3,
                position=(pos[0]-2,pos[1]+13),
                h_align='center',
                v_align='center',
                scale=1.8,
                shadow=0.3
            )
        for _ in range(2):
            a = [
                'RIGHT_ARROW',
                'LEFT_ARROW'
            ][_]
            pos = (x-195-130*_,15)
            s.bw(
                p=p,
                pos=pos,
                size=(50,50),
                color=s.COL4,
                oac=Call(s.seek,[1,-1][_]),
                repeat=True
            )
            otw(
                parent=p,
                text=cs(getattr(sc,a)),
                color=s.COL5,
                position=(pos[0]-1,pos[1]+12),
                h_align='center',
                v_align='center',
                scale=1.7,
                shadow=0.2
            )
        pos = (x-260,15)
        s.bw(
            p=p,
            pos=pos,
            size=(50,50),
            color=s.COL6,
            oac=s.toggle
        )
        s.tt = otw(
            parent=p,
            color=s.COL7,
            position=(pos[0]+12,pos[1]+11),
            scale=1.5,
            shadow=0.3
        )
        s.toggle(dry=True)
        # progress
        pos = (150,sy/2-2)
        s.px = x-600
        iw(
            parent=p,
            texture=gt('white'),
            size=(s.px,5),
            position=pos,
            opacity=0.4,
            color=s.COL8
        )
        s.nbp = (pos[0]-24,pos[1]-22)
        s.nb = iw(
            parent=p,
            texture=gt('nub'),
            size=(50,50),
            position=s.nbp,
            opacity=0.4,
            color=s.COL9
        )
        # timestamp
        s.ct = otw(
            parent=p,
            position=(20,40),
            color=s.COL7
        )
        otw(
            parent=p,
            position=(20,15),
            text=FOR(s.ds),
            color=s.COL6
        )
        # sensor
        sx,sy = (150,15)
        n = 100
        tp = s.px/n
        for _ in range(n):
            obw(
                label='',
                parent=p,
                position=(sx+tp*_,sy),
                size=(tp,50),
                texture=gt('empty'),
                enable_sound=False,
                on_activate_call=Call(s.jump,_/n)
            )
        # info
        ix,iy = (378,98)
        s.ok = iw(
            texture=gt('white'),
            position=(x-391,100),
            parent=p,
            size=(ix,iy),
            opacity=0
        )
        s.ok2 = otw(
            position=(x-ix+150,iy+64),
            h_align='center',
            scale=1.2,
            parent=p
        )
        s.ok3 = otw(
            position=(x-ix+150,iy+10),
            h_align='center',
            parent=p
        )
        # finally
        s.sp = 1
        s.rn = s.st = 0
        s.play()
    def hm(s,t1,t2,c1,c2):
        if getattr(s,'tbye',0) and getattr(s,'frbro',0):
            s.frbro = s.tbye = False
        s.okt = None
        iw(s.ok,color=c1)
        otw(s.ok2,text=t1,color=c2)
        otw(s.ok3,text=t2,color=c2)
        s.fok()
        s.okt = tock(1.5,s.unhm)
    def unhm(s):
        s.fok(1,-0.1)
        [otw(_,text='') for _ in [s.ok2,s.ok3] if _.exists()]
    def fok(s,i=0,a=0.1):
        if i > 1.0 or i < 0: return
        if not s.ok.exists(): return
        iw(s.ok,opacity=i)
        teck(0.02,Call(s.fok,i+a,a))
    def toggle(s,dry=False):
        if not dry: s.ps = not s.ps
        t = cs(getattr(sc,['PAUSE','PLAY'][s.ps]+'_BUTTON'))
        otw(s.tt,text=t)
        if not dry:
            if s.ps:
                s.stop()
                PAUSE()
            else:
                s.play()
                RESUME()
    def clock(s):
        t = time()
        r = t - s.rt
        s.rt = t
        s.rn += r * s.sp
    def boost(s,i):
        n = GET()+i
        SET(n)
        s.sp = 2**n
        h = 'Snail Mode' if s.sp == 0.0625 else 'Slow Motion' if s.sp<1 else 'Quake Pro' if s.sp==16 else 'Fast Motion' if s.sp>1 else 'Normal Speed'
        s.hm(h,f'Current exponent: x{s.sp}',s.COL2,s.COL3)
    def play(s):
        s.rt = time()+0.01
        s.pt = tock(0.01,s.pro,repeat=True)
        s.clt = tock(0.01,s.clock,repeat=True)
    def stop(s):
        s.pt = s.clt = None
    def seek(s,i):
        h = ['Forward by','Rewind by'][i==-1]
        i = i * s.sp
        i = (s.ds/20)*i
        t = (s.rn-s.st)+i
        if (t >= s.ds) or (t <= 0):
            s.loop()
        else:
            s.st = s.rn-t
            s.replay()
            SEEK(t)
        if s.ps:
            s.toggle()
            teck(0.1,s.toggle)
        i = abs(round(i,2))
        s.hm('Seek',h+f" {i} second{['s',''][i==1]}",s.COL4,s.COL5)
    def jump(s,p):
        t = s.ds * p
        s.st = s.rn-t
        s.replay()
        SEEK(t)
        if s.ps:
            s.toggle()
            teck(0.1,s.toggle)
    def bye(s):
        if getattr(s,'frbro',0): s._bye(); return
        s.hm('Exit','Press again to confirm',s.COL0,s.COL1)
        s.frbro = True
        s.tbye = tock(1.5,Call(setattr,s,'frbro',False))
    def _bye(s):
        fade(0,time=0.75,endcall=Call(fade,1,time=0.75))
        gs('deek').play()
        BYE()
        s.stop()
    def pro(s):
        t = s.rn-s.st
        if t >= s.ds: s.loop(); return
        x,y = s.nbp
        p = (t/s.ds)*s.px
        iw(s.nb,position=(x+p,y))
        otw(s.ct,text=FOR(t))
    def replay(s):
        SEEK(-10**10)
    def loop(s):
        s.st = s.rn = 0
        s.replay()
    bw = lambda s,p=None,oac=None,pos=None,**k: obw(
        parent=p,
        on_activate_call=oac,
        position=pos,
        label='',
        texture=gt('white'),
        enable_sound=False,
        **k
    )

# Tools
BYE = lambda: app.classic.return_to_main_menu_session_gracefully(reset_ui=False)
BTW = lambda t: (gs('block').play() or 1) and push(t,color=(1,1,0))
GOS = lambda: gsw('overlay_stack')
FOR = lambda t: strftime('%H:%M:%S',gmtime(t))

# pybrp_inline
Z = lambda _:_*[0]
G_FREQS = [
    101342,9667,3497,1072,0,3793,*Z(2),2815,5235,*Z(3),3570,*Z(3),
    1383,*Z(3),2970,*Z(2),2857,*Z(8),1199,*Z(30),
    1494,1974,*Z(12),1351,*Z(122),1475,*Z(65)
]
class _H:
    class _N:
        def __init__(self):
            self.l,self.r,self.p,self.f=-1,-1,0,0
    def __init__(self):
        self.nodes=[self._N()for _ in range(511)]
        for i in range(256):self.nodes[i].f=G_FREQS[i]
        nc=256
        while nc<511:
            s1,s2=-1,-1
            i=0
            while self.nodes[i].p!=0:i+=1
            s1=i;i+=1
            while self.nodes[i].p!=0:i+=1
            s2=i;i+=1
            while i<nc:
                if self.nodes[i].p==0:
                    if self.nodes[s1].f>self.nodes[s2].f:
                        if self.nodes[i].f<self.nodes[s1].f:s1=i
                    elif self.nodes[i].f<self.nodes[s2].f:s2=i
                i+=1
            self.nodes[nc].f=self.nodes[s1].f+self.nodes[s2].f
            self.nodes[s1].p=self.nodes[s2].p=nc-255
            self.nodes[nc].r,self.nodes[nc].l=s1,s2
            nc+=1
    def decompress(self,src):
        if not src:return b''
        rem,comp=src[0]&15,src[0]>>7
        if not comp:return src
        out,ptr,l=bytearray(),src[1:],len(src)
        bl=((l-1)*8)-rem;bit=0
        while bit<bl:
            m_bit=(ptr[bit>>3]>>(bit&7))&1;bit+=1
            if m_bit:
                n=510
                while n>=256:
                    if bit>=bl:raise ValueError("A")
                    p_bit=(ptr[bit>>3]>>(bit&7))&1;bit+=1
                    n=self.nodes[n].l if p_bit==0 else self.nodes[n].r
                out.append(n)
            else:
                if bit+8>bl:break
                bi,b_in_b=bit>>3,bit&7
                val=ptr[bi]if b_in_b==0 else(ptr[bi]>>b_in_b)|(ptr[bi+1]<<(8-b_in_b))
                out.append(val&255);bit+=8
        return bytes(out)
def DBRP(brp_path,ins):
    raw_out=BytesIO()
    with open(brp_path,'rb')as f:
        raw_out.write(f.read(6))
        while True:
            b_data=f.read(1)
            if not b_data:break
            b1,m_len=b_data[0],0
            if b1<254:m_len=b1
            elif b1==254:m_len=unpack('<H',f.read(2))[0]
            else:m_len=unpack('<I',f.read(4))[0]
            if m_len>0:
                decomp_data=ins.decompress(f.read(m_len))
                l32=len(decomp_data)
                if l32<254:raw_out.write(bytes([l32]))
                elif l32<=65535:raw_out.write(bytes([254]));raw_out.write(l32.to_bytes(2,'little'))
                else:raw_out.write(bytes([255]));raw_out.write(l32.to_bytes(4,'little'))
                raw_out.write(decomp_data)
    return raw_out.getvalue()
def GRD(raw_data):
    total_ms=0
    f=BytesIO(raw_data)
    f.seek(6)
    while True:
        b_data=f.read(1)
        if not b_data:break
        b1,msg_len=b_data[0],0
        if b1<254:msg_len=b1
        elif b1==254:msg_len=unpack('<H',f.read(2))[0]
        else:msg_len=unpack('<I',f.read(4))[0]
        msg_data=f.read(msg_len)
        if not msg_data or msg_data[0]!=1:continue
        sub_off=1
        while sub_off<len(msg_data):
            try:sub_size=unpack('<H',msg_data[sub_off:sub_off+2])[0]
            except:break
            sub_data=msg_data[sub_off+2:sub_off+2+sub_size]
            if sub_data and sub_data[0]==0:total_ms+=sub_data[1]
            sub_off+=2+sub_size
    return total_ms

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(s):
        from bauiv1lib.ingamemenu import InGameMenuWindow as m
        a = '_refresh_in_game'; o = getattr(m,a)
        setattr(m,a,lambda v,*a,**k:(s.mk(v),o(v,*a,**k))[1])
        from bauiv1lib.watch import WatchWindow as n
        b = '__init__'; p = getattr(n,b)
        setattr(n,b,lambda v,*a,**k:(p(v,*a,**k),s.mk(v,1))[0])
    def mk(s,v,i=0):
        s.b = Replay.bw(
            Replay,
            p=v._root_widget,
            label='Replay',
            pos=(v._width-300,v._height-100) if i else (-70,0),
            icon=gt('replayIcon'),
            iconscale=0.8,
            size=(200,70) if i else (90,35),
            oac=lambda:Replay(source=s.b)
        )

