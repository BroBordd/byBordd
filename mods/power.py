# Copyright 2025 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Power v1.0 - Feel the power

Because we developers are powerful.
Power is mainly focused on the multiplayer side.
Adds a dev console tab with some features I find useful.
Power can be considered a good tool to have around.
"""

from typing import override
from babase import (
    clipboard_is_supported as CIS,
    clipboard_set_text as CST,
    push_back_press as BACK,
    Plugin,
    app
)
from babase._devconsole import (
    DevConsoleTab as TAB,
    DevConsoleTabEntry as ENT
)
from bascenev1 import (
    get_connection_to_host_info_2 as HOST,
    disconnect_from_host as LEAVE,
    connect_to_party as CON,
    disconnect_client as kick,
    broadcastmessage as push,
    get_game_roster as ROST,
    chatmessage as chat
)
from bauiv1 import (
    get_string_width as sw,
    SpecialChar as sc,
    apptimer as teck,
    charstr as cs,
    Call
)

class Power(TAB):
    def __init__(s):
        s.ri = 0
        s.c = s.p = s.n = s.h = None
        s.j = [None,None,None]
        s.ji = 1
        s.re = 0
        s.r = []
        s.hi = {}
        s.ii = 0
        teck(3,s.spy)
    def rf(s):
        try: s.request_refresh()
        except RuntimeError: pass
    def spy(s):
        _ = 0
        r = ROST()
        if r != s.r: s.r = r; _ = 1
        h = HOST()
        if h != s.h: s.h = h; _ = 1
        _ and s.rf()
        teck(0.1,s.spy)
    @override
    def refresh(s):
        sf = s.width / 1605.3
        x = -s.width/2
        T,B = s.text,s.button
        if len(s.r) and s.ri >= len(s.r): s.ri = len(s.r) - 1
        if s.j[0] == 'JRejoin' and s.ji <= s.re:
            s.ji = s.re + 1
            push('Job time cannot be less than rejoin time\nwhen job is JRejoin. Updated job time to '+str(s.ji),color=(1,1,0))
        if s.height <= 100:
            B(
                cs(sc.DOWN_ARROW),
                pos=(x + 10 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=s.ri >= len(s.r)-3,
                call=Call(s.mv,'ri',1)
            )
            B(
                cs(sc.UP_ARROW),
                pos=(x + 250 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=s.ri <= 0,
                call=Call(s.mv,'ri',-1)
            )
            nt = "No roster\nYou're alone"
            w = GSW(nt)
            0 if len(s.r) else T(
                nt,
                pos=(x + 147 * sf, s.height-17),
                h_align='center',
                v_align='top',
                scale=1 if w<(200*sf) else (200*sf)/w
            )
            for i,k in enumerate(s.r):
                if i < s.ri: continue
                if i>=(s.ri+3): break
                c = k['client_id']
                n = k['display_string']
                p = k['players']
                w = GSW(n)
                B(
                    n,
                    size=(210 * sf, 27),
                    pos=(x + 40 * sf, s.height-35-27*(i-s.ri)),
                    style=[['blue','blue_bright'],['purple','purple_bright']][not p][s.c==c],
                    call=Call(s.prv,c,p,n),
                    label_scale=1 if w < 200 * sf else (200 * sf)/w
                )
            bb = s.c is None
            B(
                'Bomb' if bb else (['Client','Host'][s.c==-1]+f' {s.c}'),
                pos=(x + 287 * sf, s.height-34),
                size=(120 * sf, 27),
                disabled=bb,
                call=Call(push,str(s.n))
            )
            B(
                'Mention',
                size=(120 * sf, 27),
                pos=(x + 287 * sf, s.height-90),
                call=Call(chat,str(s.n)),
                disabled=bb
            )
            B(
                'Players',
                size=(120 * sf, 27),
                pos=(x + 287 * sf, s.height-62),
                call=Call(push,'\n'.join([' '.join([f'{i}={j}' for i,j in _.items()]) for _ in s.p]) if s.p else ''),
                disabled=bb or (not s.p)
            )
            B(
                'Kick',
                size=(120 * sf, 27),
                pos=(x + 407 * sf, s.height-34),
                call=Call(kick,s.c),
                disabled=bb or (s.c==-1)
            )
            B(
                'JKick',
                size=(120 * sf, 27),
                pos=(x + 407 * sf, s.height-62),
                call=Call(s.job,Call(kick,s.c),['JKick',s.c,s.n]),
                disabled=bb or (s.c==-1)
            )
            B(
                'Vote',
                size=(120 * sf, 27),
                pos=(x + 407 * sf, s.height-90),
                call=Call(chat,'1'),
                disabled=not s.r
            )
            B(
                '',
                size=(1 * sf, s.height-17),
                pos=(x + 535 * sf, 10),
                style='bright'
            )
            bb = s.j[0] is None
            ra = cs(sc.RIGHT_ARROW)
            B(
                'No job' if bb else 'Job',
                size=(120 * sf, 27),
                pos=(x + 544 * sf, s.height-34),
                call=Call(push,s.j[0]),
                disabled=bb
            )
            w = 0 if bb else GSW(str(s.j[1]))
            B(
                'Target' if bb else str(s.j[1]),
                size=(120 * sf, 27),
                pos=(x + 544 * sf, s.height-62),
                call=Call(push,s.j[2]),
                disabled=bb,
                label_scale=1 if w<110 * sf else (110 * sf)/w
            )
            B(
                'Stop',
                size=(120 * sf, 27),
                pos=(x + 544 * sf, s.height-90),
                call=Call(s.job,None,[None,None,None]),
                disabled=bb
            )
            B(
                '+',
                size=(50 * sf, 27),
                pos=(x + 664 * sf, s.height-34),
                call=Call(s.mv,'ji',1)
            )
            B(
                str(s.ji or 0.1),
                size=(50 * sf, 27),
                pos=(x + 664 * sf, s.height-62),
                call=Call(push,f"Job runs every {s.ji or 0.1} second{['','s'][s.ji!=1]}")
            )
            B(
                '-',
                size=(50 * sf, 27),
                pos=(x + 664 * sf, s.height-90),
                disabled=s.ji<=0.5,
                call=Call(s.mv,'ji',-1)
            )
            B(
                '',
                size=(1 * sf, s.height-17),
                pos=(x + 722 * sf, 10),
                style='bright'
            )
            t = getattr(s.h,'name','Not in a server')
            a = getattr(s.h,'address','127.0.0.1')
            p = getattr(s.h,'port','43210')
            if s.h:
                tt = t if t.strip() else '...'
                s.hi.update({(tt,a):(tt,p)}) if (t.strip()) or (a not in s.hi) else None
                0 if tt == '...' else [s.hi.pop((v,_)) for v,_ in s.hi.copy() if v == '...']
            w = GSW(t)
            B(
                t if t.strip() else 'Loading...',
                size=(300 * sf, 27),
                pos=(x + 732 * sf, s.height-34),
                disabled=not s.h,
                label_scale=1 if w < 290 * sf else (290 * sf)/w,
                call=Call(push,f"{t}\nHosted on build {getattr(s.h,'build_number','0')}" if t.strip() else 'Server is still loading...\nIf it remains stuck on this\nthen either party is full, or a network issue.'),
            )
            w = GSW(a)
            B(
                a,
                size=(200 * sf, 27),
                pos=(x + 732 * sf, s.height-62),
                call=Call(COPY,a),
                disabled=not s.h,
                label_scale=1 if w < 190 * sf else (190 * sf)/w
            )
            w = GSW(str(p))
            B(
                str(p),
                size=(97 * sf, 27),
                pos=(x + 935 * sf, s.height-62),
                disabled=not s.h,
                call=Call(COPY,str(p)),
                label_scale=1 if w < 90 * sf else (90 * sf)/w
            )
            B(
                'Leave',
                size=(100 * sf, 27),
                pos=(x + 732 * sf, s.height-90),
                call=LEAVE,
                disabled=not s.h
            )
            B(
                'Rejoin',
                size=(97 * sf, 27),
                pos=(x + 835 * sf, s.height-90),
                call=Call(REJOIN,a,p,lambda:s.re),
                disabled=not s.h
            )
            B(
                'JRejoin',
                size=(97 * sf, 27),
                pos=(x + 935 * sf, s.height-90),
                call=Call(s.job,Call(REJOIN,a,p,lambda:s.re),['JRejoin',a,str(p)]),
                disabled=not s.h
            )
            B(
                '+',
                size=(50 * sf, 27),
                pos=(x + 1035 * sf, s.height-34),
                call=Call(s.mv,'re',1)
            )
            B(
                str(s.re or 0.1),
                size=(50 * sf, 27),
                pos=(x + 1035 * sf, s.height-62),
                call=Call(push,f"Rejoins after {s.re or 0.1} second{['','s'][s.re!=1]}\nKeep this 0.1 unless server kicks fast rejoins\nLife in server = job time - rejoin time")
            )
            B(
                '-',
                size=(50 * sf, 27),
                pos=(x + 1035 * sf, s.height-90),
                disabled=s.re<=0.5,
                call=Call(s.mv,'re',-1)
            )
            B(
                '',
                size=(1 * sf, s.height-17),
                pos=(x + 1092 * sf, 10),
                style='bright'
            )
            for i,e in enumerate(s.hi.items()):
                if i < s.ii: continue
                if i >= (s.ii+3): break
                g,v = e
                _,a = g
                n,p = v
                w = GSW(n)
                B(
                    n,
                    size=(300 * sf, 27),
                    pos=(x + 1134 * sf, s.height-34-28*(i-s.ii)),
                    label_scale=1 if w < 290 * sf else (290 * sf)/w,
                    call=Call(JOIN,a,p,False),
                    disabled=n == '...'
                )
            nt = "Your server join history\nwill appear here. Hi."
            w = GSW(nt)
            0 if len(s.hi) else T(
                nt,
                pos=(x + 1285 * sf, s.height-17),
                h_align='center',
                v_align='top',
                scale=1 if w<(280*sf) else (280*sf)/w
            )
            B(
                cs(sc.DOWN_ARROW),
                pos=(x + 1102 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=s.ii >= len(s.hi)-3,
                call=Call(s.mv,'ii',1)
            )
            B(
                cs(sc.UP_ARROW),
                pos=(x + 1436 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=s.ii <= 0,
                call=Call(s.mv,'ii',-1)
            )
            B(
                'Force leave',
                call=FORCE,
                pos=(x + 1469 * sf, s.height-34),
                size=(130 * sf, 27),
                label_scale=0.9
            )
            B(
                'Back',
                call=BACK,
                pos=(x + 1469 * sf, s.height-62),
                size=(130 * sf, 27)
            )
            B(
                'Power',
                call=Call(push,'Power v1.0 MinUI\nExpand dev console to switch to FullUI'),
                pos=(x + 1469 * sf, s.height-90),
                size=(130 * sf, 27)
            )
    def mv(s,a,i):
        setattr(s,a,getattr(s,a)+i)
        s.rf()
    def job(s,f,j):
        s.j = j
        s.lf = f
        if f is not None:
            s._job(f)
            push('Job started',color=(1,1,0))
        else: push('Job stopped',color=(1,1,0))
        s.rf()
    def _job(s,f):
        if f != s.lf: return
        f(); teck(s.ji or 0.1,Call(s._job,f))
    def prv(s,c,p,n):
        s.c,s.p,s.n = c,p,n
        s.rf()

HAS = app.ui_v1.has_main_window
SAVE = app.classic.save_ui_state
FORCE = lambda: ((BACK() or 1) if HAS() else 1) and teck(0.7 if HAS() else 0.1,lambda: 0 if HAS() else app.classic.return_to_main_menu_session_gracefully())
JOIN = lambda *a: (SAVE() or 1) and CON(*a)
GSW = lambda s: sw(s,suppress_warning=True)
REJOIN = lambda a,p,f: ((LEAVE() if getattr(HOST(),'name','') else 0) or 1) and teck(f() or 0.1,Call(JOIN,a,p,False))
COPY = lambda s: ((CST(s) or 1) if CIS() else push('Clipboard not supported!')) and push('Copied!',color=(0,1,0))

# brobord collide grass
# ba_meta require api 9
# ba_meta export plugin
class byBordd(Plugin):
    def __init__(s):
        I = app.devconsole
        E = ENT('Power',Power)
        I.tabs.append(E)
        I._tab_instances['Power'] = E.factory()
