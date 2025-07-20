# Copyright 2025 - Solely by BrotherBoard - Feel free to utilize/modify this for personal use
# Bug? Feedback? Telegram >> GalaxyA14user

"""
Byte v1.1 - At your service.

Simple bombsquad AI that takes orders.

How to use?
- Go to https://ai.google.dev/gemini-api/docs
- Log in with your Googoe account
- Create an API key and copy it
- Open dev console terminal
- Run `__import__('byte').Byte("YOUR_KEY")

Try help(Byte) for more info.
And always read code to know more.
"""

from bascenev1lib.actor.spaz import Spaz
from babase import (
    get_string_height as gsh,
    get_string_width as gsw,
    Plugin
)
from bascenev1 import (
    get_foreground_host_activity as ga,
    get_chat_messages as GCM,
    broadcastmessage as push,
    OutOfBoundsMessage,
    getnodes as GN,
    getsound as gs,
    timer as tick,
    Timer as tock,
    StandMessage,
    DieMessage,
    newnode,
    animate
)
from bauiv1 import (
    SpecialChar as sc,
    apptimer as teck,
    charstr as cs
)
from http.client import HTTPSConnection
from json import dumps, loads
from threading import Thread
from math import dist

class Byte:
    MEM = {}
    def __init__(
        s,
        key: str,
        position: tuple = (0,0,0),
        color: tuple = (0,0,0),
        highlight: tuple = (0,0,0),
        character: str = 'Pixel'
    ):
        s.master = s.getmast()
        if not s.master:
            gs('block').play()
            push('Join the game first!',color=(1,1,0))
            return
        s.key = key
        s.MEM[s.master.name] = s
        s.bot = Spaz(
            color=color,
            highlight=highlight,
            character='Pixel'
        )
        s.bot.handlemessage(StandMessage(position,0))
        s.bot.handlemessage = s.hm
        s.node = s.bot.node
        s.node.name = s.__class__.__name__
        s.bub = Bubble(s.node)
        s.text = s.ot = ''
        s.fol = False
        with ga().context: s.spy()
    def hm(s,m):
        if True in [isinstance(m,_) for _ in [DieMessage,OutOfBoundsMessage]]:
            s.node.delete()
    def hear(s,j):
        s.text = GET(j,API_KEY=s.key)
    def spy(s):
        if s.text != s.ot:
            s.ot = s.text
            print(s.text)
            s.act(s.text)
        tick(0.05,s.spy)
    def act(s,r):
        c,t = r.split(':',1)
        for _ in c.split('|'):
            s.parse(_.strip()[1:])
        else: s.bub.push(t)
    def parse(s,_):
        f = _.startswith
        a = _.split(' ')
        if f('move'): print('lets move',a[1:])
        if f('jump'): s.on(0)
        if f('bomb'): s.on(1)
        if f('grab'): s.on(2)
        if f('punch'): s.on(3)
        if f('idle'): s.idle()
        if f('follow'): s.follow()
        if f('stop'): s.stop()
        if f('wave'): s.wave()
    def wave(s):
        s.node.handlemessage('celebrate_r',1000)
    def on(s,i):
        for _ in [1,0]:
            getattr(s.bot,'on_'+['jump','bomb','pickup','punch'][i]+'_'+['release','press'][_])()
    def idle(s):
        pass
    def follow(s):
        if s.fol: return
        s.fol = True
        s._follow()
    def _follow(s):
        if not s.fol:
            s.move(0,0)
            return
        p = s.getmast().position
        q = s.node.position
        d = dist(p,q)
        tick(0.1,s._follow)
        if d < 1.7:
            s.move(0,0)
            return
        s.bot.on_run(int(d>3))
        px,_,pz = p
        qx,_,qz = q
        dx = px - qx
        dz = pz - qz
        s.move(dx,-dz)
    def move(s,x,z):
        s.bot.on_move_left_right(x)
        s.bot.on_move_up_down(z)
    def getmast(s):
        return ([p.actor.node for p in ga().players if p.sessionplayer.inputdevice.client_id == -1] or [None])[0]
    def stop(s):
        s.fol = False

class Bubble:
    def __init__(s,head,res='\u2588'):
        s.head = head
        s.res = res
        s.text = ''
        s.kids = []
        s.bye = None
        s.node = newnode(
            'math',
            delegate=s,
            owner=head,
            attrs={
                'input1':(0,0,0),
                'operation':'add'
            }
        )
        head.connectattr('position',s.node,'input2')
        for _ in [0,0.85]:
            n = TEX(s.node,color=(_,_,_))
            s.kids.append(n)
            s.node.connectattr('output',n,'position')
    def push(s,text=''):
        s.bye = None
        if not text: s.anim(1,0); s.text = text; return
        ls = len(text.splitlines())
        s.node.input1 = (0,1.3+0.32*ls,0)
        bg,t = s.kids
        bg.text = (round(GSW(text)/GSW(s.res)+1)*s.res+'\n')*ls
        t.text = text
        if not s.text: s.anim(0,1)
        s.text = text
        s.bye = tock(3.5,s.push)
    def anim(s,p1,p2):
        [animate(_,'opacity',{0:p1,0.2:p2}) for _ in s.kids]

SYS = """
Byte: sweet, simple female bot. Output: '$cmd1 args|$cmd2 args|...:dialogue'. Cmds '|' separated. Dialogue after final ':'.
Cmds: $jump, $punch, $grab, $stop, $follow, $idle.
Waves: $wave (both), $wave_l (left), $wave_r (right).
$stop terminates all. Default (no cmd): $idle.
Examples but not literally please:
Ex1: 'Jump!'->'$jump:Yay! Hoppie!'
Ex2: 'Jump and wave!'->'$jump|$wave:Wheeeeee! So much fun!'
Ex3: 'Hello!'->'$wave:Heyo! What are we doing?'
"""
def GET(user_input: str,API_KEY) -> str:
    MODEL_ID = "gemini-2.5-flash-lite-preview-06-17"
    HOST = "generativelanguage.googleapis.com"
    PATH = f"/v1beta/models/{MODEL_ID}:generateContent?key={API_KEY}"

    PAYLOAD = {
        "contents": [
            {
                "parts": [
                    {"text": user_input}
                ]
            }
        ]
    }

    PAYLOAD["system_instruction"] = {
        "parts": [
            {"text": SYS}
        ]
    }

    J_PAYLOAD = dumps(PAYLOAD)
    CONN = None

    try:
        CONN = HTTPSConnection(HOST)

        HEADERS = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        CONN.request("POST", PATH, body=J_PAYLOAD, headers=HEADERS)

        RES = CONN.getresponse()
        STATUS = RES.status
        R_BODY = RES.read().decode('utf-8')

        if STATUS == 200:
            R_DATA = loads(R_BODY)
            if 'candidates' in R_DATA and R_DATA['candidates']:
                F_CAND = R_DATA['candidates'][0]
                if 'content' in F_CAND and 'parts' in F_CAND['content']:
                    return F_CAND['content']['parts'][0]['text']
        return "" # Return empty string on error or no text found
    except Exception:
        return "" # Return empty string on exception

    finally:
        if CONN:
            CONN.close()

GSW = lambda s: gsw(s,suppress_warning=True)
GSH = lambda s: gsh(s,suppress_warning=True)
TEX = lambda o,**k: newnode(
    'text',
    owner=o,
    attrs={
        'in_world':True,
        'scale':0.01,
        'flatness':1,
        'h_align':'center',
        **k
    }
)

# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def on_app_running(s):
        s.o = []
        teck(5,s.spy)
    def spy(s):
        teck(0.1,s.spy)
        try: a = GCM()
        except RuntimeError: return
        if a == s.o: return
        s.o = a
        i,j = a[-1].split(': ',1)
        m = Byte.MEM
        if True not in [_ in m for _ in [i,i.replace(cs(sc.V2_LOGO),'',1)]]: return
        Thread(target=lambda:m[i].hear(j)).start()
