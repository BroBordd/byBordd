# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Polish v2.7 - Your very UI designer

Beta - Aims to help modders like me draw UI.
Start by writing Polish() in dev console, or via settings UI.
Polish uses a different static appearance to avoid visually conflicting with target container.
In a nutshell, Polish a container, get code, thrive.
"""

from babase import (
    clipboard_set_text as COPY,
    PluginSubsystem as SUB,
    Plugin,
    env
)
from _babase import (
    set_dev_console_input_text as dset
)
from bascenev1 import broadcastmessage as broad
from bauiv1 import (
    get_virtual_screen_size as res,
    get_special_widget as gsw,
    get_string_width as strw,
    containerwidget as cw,
    hscrollwidget as hsw,
    scrollwidget as sw,
    buttonwidget as bw,
    imagewidget as iw,
    SpecialChar as sc,
    textwidget as tw,
    gettexture as gt,
    apptimer as teck,
    UIScale as scl,
    getsound as gs,
    charstr as cs,
    app as APP,
    Call
)
from random import choice as CH, uniform as uf
from traceback import print_exc as ERR
from colorsys import hsv_to_rgb as HTR
from zlib import compress, decompress
from json import dumps, loads
from os.path import join
from os import makedirs
from uuid import uuid4
from re import match

class Polish:
    INS = None
    KEY = 'CACHE'
    PRF = 'POLISH'
    INC = 2
    width = 200
    @classmethod
    def resize(c):
        s = c.INS
        if s is None: return
        s.setup()
        s.nuke()
    def __init__(
        s,
        *,
        size=(500,450),
        parent=None,
        tr=None,
        **k
    ):
        c = s.__class__
        if c.INS:
            btw('Already running!')
            return
        c.INS = s
        r = res()
        s.stack_offset = k.get('stack_offset',(0,0))
        at = s.at = {
            'size':size,
            'stack_offset':s.stack_offset,
            **k
        }
        s.tar = cw(**at)
        if tr and 'transition' not in at:
            cw(s.tar,background=False)
            teck(0.1,lambda:cw(s.tar,transition=tr,background=True))
        s.TAR = (s.tar,(at,cw))
        s.width = 200
        s.c = [0,0,0]
        s.MEM = []
        s.MOM = []
        s.size = size
        s.kid = None
        s.sl = (None,None)
        s.grid = [5,5]
        s.gtrash = []
        s.bt = []
        s.wids = {}
        s.nid = -1
        s.trash,s.ok,s.sps,s.bws,s.K,s.hell = [[] for _ in range(6)]
        K = s.K
        # parent
        s.p = cw(
            parent=GOS(),
            background=False
        )
        s.i = iw(
            parent=s.p,
            texture=gt('black')
        )
        # file
        s.bws.append(bw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-30,30),
            label='File',
            enable_sound=False,
            color=File.COL1,
            textcolor=File.COL2,
            on_activate_call=Call(s.go,File,[s])
        ))
        # separator
        s.sps.append(iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            opacity=0.6
        ))
        # Root
        s.bws.append(bw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-30,30),
            label='Root',
            enable_sound=False,
            color=Root.COL1,
            textcolor=Root.COL2,
            on_activate_call=Call(s.go,Root)
        ))
        # Tran
        s.bws.append(bw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-30,30),
            label='Animation',
            enable_sound=False,
            color=(0,0.2,0.2),
            textcolor=(0,0.5,0.5),
            on_activate_call=Call(s.go,Anim)
        ))
        # separator
        s.sps.append(iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            opacity=0.6
        ))
        # child control
        s.bws.append(bw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-30,30),
            label='Widget',
            enable_sound=False,
            color=(0,0.4,0),
            textcolor=(0,0.7,0),
            on_activate_call=Call(s.go,Add)
        ))
        s.bws.append(bw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-30,30),
            label='Preset',
            enable_sound=False,
            color=(0.4,0.4,0),
            textcolor=(0.7,0.7,0),
            on_activate_call=Call(s.go,Preset,[s])
        ))
        s.bws.append(bw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-30,30),
            label='Grid',
            enable_sound=False,
            color=(0.4,0,0),
            textcolor=(0.7,0,0),
            on_activate_call=Call(s.go,Grid,[s,s.gtrash])
        ))
        # separator
        s.sps.append(iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            opacity=0.6
        ))
        # button scroll
        s.bs = sw(
            parent=s.p,
            border_opacity=0,
            highlight=False
        )
        s.bc = cw(
            parent=s.bs,
            background=False
        )
        # finally
        s.sync()
        s.setup(first=True)
        # resume
        chk = var(c.KEY)
        if chk: s.proload(chk,shut=1)
    def clearall(s):
        var(s.__class__.KEY,0)
        s.exit(tr='out_left',die=True)
        s.__class__(tr='in_right')
    def debug(s):
        s.exit(tr='out_scale')
        c = s.tr()+'base=make()'
        global BASE,CONT
        CONT = {}
        try: exec(c,CONT)
        except:
            btw('Debugger found an error!\nSee logs now')
            print('Polish: Debugger just took the L:')
            ERR()
            return
        BASE = CONT.get('base',None)
        print(f'Polish: Now debugging {BASE}')
        print('- Container reference >>> from polish import BASE')
        print('- Context reference >>> from polish import CONT')
        print('- Back to designer >>> polish()')
    def sync(s):
        s.MOM = []
        rev = {v:k for k,v in s.wids.items()}
        ty = type(gt('nub'))
        ta = list(s.TAR)
        ta[0] = -1
        for _ in [ta]+s.MEM:
            k,f = _[1]
            nk = {}
            for i,j in k.items():
                uid = rev.get(j,None)
                if uid is not None: j = ('uid',uid)
                if j == s.tar: j = ('uid',-1)
                if isinstance(j,ty): j = ('texture',str(j)[len("<bauiv1.Texture '"):-2])
                nk[i] = j
            cid = _[0]
            o = [cid,(nk,f.__name__)]
            s.MOM.append(o)
    def nextid(s):
        s.nid += 1
        return s.nid
    def cp(s):
        if s.sl[0] is None: btw('Select a widget first!'); return
        data = s.MEM[s.sl[1]][1]
        nid = s.nextid()
        s.wids[nid] = data[1](**data[0])
        s.MEM.insert(s.sl[1]+1,(nid,(data[0].copy(),data[1])))
        s.sync()
        s.bt.insert(s.sl[1]+1,s.bt[s.sl[1]])
        s.bord(False)
        s.fresh()
        s.flash(s.ok[s.sl[1]+1])
        s.hl(s.sl[1])
        s.bord()
        nice('Copied!')
    def flash(s,b,c=None):
        c = c or Man.COL0
        c = (c[0]-0.1,c[1]-0.1,c[2]-0.1)
        bw(b,color=c)
        if c[0] <= Man.COL1[0]+0.01: return
        teck(0.05,Call(s.flash,b,c))
    def bye(s):
        if s.sl[0] is None: btw('Select a widget first!'); return
        s.MEM.pop(s.sl[1])
        s.sync()
        s.bt.pop(s.sl[1])
        s.wids[s.sl[0]].delete()
        s.sl = (None,None)
        s.bord(False)
        s.clear()
        s.fresh()
        nice('Deleted!')
    def hold(s):
        if getattr(s,'busy',0): return 1
        s.busy = 1; teck(0.2,Call(setattr,s,'busy',0))
    def logo(s):
        [h.delete() for h in s.hell]; s.hell.clear()
        x = res()[1]
        # vector
        for size,pos,col in [
            ((10,40),(10,x-50),(255,255,0)),
            ((25,25),(10,x-35),(0,255,255)),
            ((10,10),(17,x-27),(255,0,255)),
            ((25,40),(40,x-50),(0,255,0)),
            ((10,25),(47.5,x-42.5),(0,127,255)),
            ((25,10),(70,x-50),(255,0,0)),
            ((10,40),(70,x-50),(255,255,0)),
            ((10,40),(107.5,x-50),(0,255,255)),
            ((25,10),(100,x-50),(255,0,255)),
            ((25,10),(100,x-20),(0,127,255)),
            ((25,8),(130,x-50),(255,0,0)),
            ((10,8),(145,x-42),(0,255,0)),
            ((25,8),(130,x-34),(100,100,255)),
            ((10,8),(130,x-26),(0,255,255)),
            ((25,8),(130,x-18),(255,255,0)),
            ((10,40),(160,x-50),(255,0,255)),
            ((10,40),(175,x-50),(100,100,255)),
            ((25,10),(160,x-35),(255,0,0))
        ]: s.hell.append(iw(
            parent=s.p,
            texture=gt('white'),
            opacity=0.4,
            size=size,
            position=pos,
            color=col
        ))
    def go(s,cls,ex=[]):
        if s.hold(): return
        deek()
        if isinstance(s.kid,cls): s.clear(); s.bord(False); return
        elif s.kid: s.clear(); s.hl(None); s.sl = (None,None)
        s.kid = cls(*ex)
        if cls == Root:
            s.bord(False)
            p = s.TAR[1][0]
            s._bord((0,0),p['size'],p.get('scale',1),18,15)
    def setup(s,first=False):
        r = res()
        z = (s.width,r[1])
        cw(s.p,size=z,stack_offset=(r[0]/2.2,0))
        iw(s.i,size=z)
        for i,b in enumerate(s.bws):
            h = [90,140,178,228,265,302][i]
            bw(b,position=(15,z[1]-h))
        for i,b in enumerate(s.sps):
            h = [100,189,313][i]
            iw(b,position=(9,z[1]-h))
        s.bsy = z[1]-310
        sw(s.bs,size=(s.width,s.bsy),position=(0,0))
        s.logo()
        if not first: return
        fade(s.i)
    def clear(s):
        e = s.kid
        if e is None: return
        j = e.I
        fade(j,i=1.0,a=-0.2)
        teck(0.5,j.delete)
        ij = e.K.copy(); e.K.clear()
        teck(0.005,lambda:([k.delete() for k in ij if k != j]))
        s.kid = None
    def nuke(s):
        if not s.kid: return
        e = s.kid
        e.I.delete()
        [j.delete() for j in e.K]; e.K.clear()
        s.kid = None
    def fresh(s):
        [_.delete() for _ in s.bc.get_children()]
        kids = s.kids()
        hm = s.bsy - 20
        ys = len(kids)*37; ys = [ys,hm][ys<hm]
        cw(s.bc,size=(s.width,ys))
        [_.delete() for _ in s.ok]; s.ok.clear()
        for i,w in enumerate(kids):
            b = bw(
                parent=s.bc,
                position=(10,ys-37*(i+1)),
                label=s.bt[i],
                color=Man.COL1,
                textcolor=Man.COL2,
                texture=gt('white'),
                enable_sound=False,
                size=(s.width-30,30),
                on_activate_call=Call(s.wid,i)
            )
            s.K.append(b)
            s.ok.append(b)
        cw(s.bc,visible_child=s.ok[-1]) if len(s.ok) else None
        if len(s.gtrash): Grid(s,s.gtrash,dry=True)
        if isinstance(s.kid,Root):
            s.bord(False)
            p = s.TAR[1][0]
            s._bord((0,0),p['size'],p.get('scale',1),18,15)
    def hl(s,i):
        s.bord(False)
        if s.sl[0] is not None:
            bw(s.ok[s.sl[1]],color=Man.COL1,textcolor=Man.COL2)
        if i is None: return
        s.sl = (s.MEM[i][0],i)
        w = s.ok[i]
        bw(w,color=Man.COL3,textcolor=Man.COL1)
        s.bord(i)
    def bord(s,i=None):
        [_.delete() for _ in s.trash]; s.trash.clear()
        if i is False: return
        if s.sl is None: return
        at = s.MEM[s.sl[1]][1][0]
        pos = at['position']
        size = at['size']
        gx,gy = (18,15)
        if not isinstance(size,tuple):
            gx,gy = (43,39)
            size = (size,size)
        scale = at.get('scale',1)
        if size[0] < 20:
            pos = (pos[0]-(20-size[0])/2,pos[1])
            size = (20,size[1])
        if size[1] < 20:
            pos = (pos[0],pos[1]-(20-size[1])/2)
            size = (size[0],20)
        size = (size[0]*scale,size[1]*scale)
        s._bord(pos,size,scale,gx,gy)
    def _bord(s,pos,size,scale,gx,gy):
        corners = [
            (pos[0], pos[1]),  # Top-Left
            (pos[0] + size[0] - 1, pos[1]),  # Top-Right
            (pos[0], pos[1] + size[1] - 1),  # Bottom-Left
            (pos[0] + size[0] - 1, pos[1] + size[1] - 1)   # Bottom-Right
        ]

        offsets = [(0, 0), (5, 0), (0, 5), (10, 0), (0, 10)]
        for i, (cx, cy) in enumerate(corners):
            for dx, dy in offsets:
                x = cx + dx if i % 2 == 0 else cx - dx
                y = cy + dy if i < 2 else cy - dy
                t = tw(
                    parent=s.tar,
                    text='\u25A0',
                    position=(x-gx,y-gy),
                    scale=0.4,
                    h_align='left',
                    v_align='bottom',
                    shadow=0,
                    flatness=1,
                    color=(1,0,0)
                )
                s.trash.append(t)
    def kids(s):
        return [s.wids[_] for _ in [i[0] for i in s.MEM]]
    def wid(s,i):
        o = getattr(s.kid,'w',69)
        s.clear()
        deek()
        w = s.kids()[i]
        if o == w:
            s.hl(None)
            return
        s.kid = Man(w,s,i)
        s.hl(i)
    def exit(s,tr=None,die=False):
        c = s.__class__
        if not die: var(c.KEY,ENCODE(s.MOM))
        s.clear()
        fade(s.i,i=1,a=-0.1)
        teck(0.15,lambda:(
            s.p.delete(),
            cw(s.tar,transition=(
                tr or s.TAR[1][0].get('out_anim','out_left')
            ))
        ))
        c.INS = None
    def cpcode(s):
        COPY(s.tr())
        nice('Copied python code!')
    def excode(s):
        n = f'polish_autogen_{str(uuid4())[:5]}.py'
        p = join(ROOT(),n)
        with open(p,'w') as f: f.write(s.tr())
        nice(f'Exported {n}\nAt {p}')
    def tr(s):
        t, n, e = ' '*4, '\n', ','
        im, fcs_initial, sigt = set(), [], False
        fcs_deferred = []
        generated_vars = {}
        obj_id_to_var_name = {}

        # s.TAR = (root_obj_instance, (kwargs, func)) - root_obj_instance is already the object
        root_obj_instance, (root_k_original, root_f) = s.TAR

        # mem_items will now start with the root_obj_instance directly from s.TAR
        mem_items = [(root_obj_instance, (root_k_original, root_f))]

        # Iterate through s.MEM (which contains integer IDs) to get the instances
        # s.MEM: [(integer_id, (kwargs, func)), ...]
        for obj_id_int, (k_original, f) in s.MEM:
            obj_instance = s.wids[obj_id_int] # Get the actual instance from s.wids
            mem_items.append((obj_instance, (k_original, f)))

        for i, (obj_instance, (k_original, f)) in enumerate(mem_items):
            obj_name_base = f.__name__
            current_var_name = ""

            if obj_name_base in generated_vars:
                generated_vars[obj_name_base] += 1
            else:
                generated_vars[obj_name_base] = 1

            current_var_name = f"{obj_name_base}{generated_vars[obj_name_base]}"
            if i == 0:
                current_var_name = "root"
            # Map the actual object instance to its generated variable name
            obj_id_to_var_name[obj_instance] = current_var_name
            im.add(f.__name__)

        # The root_obj_instance is already identified from s.TAR

        for i, (obj_instance, (k_original, f)) in enumerate(mem_items):
            initial_kwp = []
            deferred_kwp = []
            oav = None
            ck = k_original.copy()

            if i == 0 and "out_anim" in ck:
                oav = ck.pop("out_anim")
            for K, V in ck.items():
                v_s = repr(V)
                # V in kwargs can be an object instance (like for 'parent')
                if K == 'parent' and V == root_obj_instance:
                    v_s = obj_id_to_var_name[V]
                    initial_kwp.append(f"{K}={v_s}")
                    continue
                # Check if V (which is an object instance) is one of our mapped instances
                elif V in obj_id_to_var_name:
                    v_s = obj_id_to_var_name[V]
                    deferred_kwp.append(f"{K}={v_s}")
                    continue
                elif hasattr(V, '__class__') and V.__class__.__name__ == 'Texture':
                    sv = str(V)
                    if sv.startswith("<bauiv1.Texture '") and sv.endswith("'>"):
                        tn = sv[len("<bauiv1.Texture '"):-2]
                        v_s, sigt = f"gettexture('{tn}')", True
                    else:
                        v_s = repr(sv)
                elif isinstance(V, str):
                    v_s = f"'{V}'"
                initial_kwp.append(f"{K}={v_s}")

            var_name = obj_id_to_var_name[obj_instance]
            fcs_initial.append((
                f.__name__,
                (e + n + t*2).join(initial_kwp) if initial_kwp else '',
                i == 0,
                oav,
                var_name
            ))

            if deferred_kwp:
                fcs_deferred.append((
                    f.__name__,
                    var_name,
                    (e + n + t*2).join(deferred_kwp)
                ))

        imp_list = sorted(list(im))
        if sigt: imp_list.append('gettexture')

        o = 'from bauiv1 import (' + n
        for fn_imp in imp_list: o += t + fn_imp + e + n
        o = o[:-len(e+n)] + n + ')' + n*2 + 'def make():' + n

        for fn, initial_gk, isf, oav, var_name in fcs_initial:
            if isf:
                if initial_gk:
                    o += t + f"root = {fn}(" + n + t*2 + initial_gk + n + t + ")" + n
                else:
                    o += t + f"root = {fn}()" + n
                if oav is not None:
                    o += t + f"back = lambda: {fn}(root,transition={repr(oav) if not isinstance(oav, str) else f"'{oav}'"})" + n
            else:
                if initial_gk:
                    o += t + f"{var_name} = {fn}(" + n + t*2 + initial_gk + n + t + ")" + n
                else:
                    o += t + f"{var_name} = {fn}()" + n
        if fcs_deferred:
            o += n
        for fn, var_name, deferred_gk in fcs_deferred:
            o += t + f"{fn}({var_name}," + n + t*2 + deferred_gk + n + t + ")" + n
        o += t + 'return root' + n
        return o
    def procp(s):
        o = ENCODE(s.MOM)
        COPY(o)
        nice('Copied!')
    def proload(s,o,shut=0):
        try: m = DECODE(o)
        except Exception as e: err(str(e)); return
        # cleanup
        if hasattr(s,'tar'):
            s.tar.delete()
            s.nid = -1
            [_.clear() for _ in [s.MEM,s.MOM,s.wids,s.bt]]
        if BASE: cw(BASE,transition='out_scale')
        # parent
        t = m.pop(0)
        at = {i:(tuple(j) if isinstance(j,list) else j) for i,j in t[1][0].items()}
        s.tar = cw(**at)
        s.TAR = (s.tar,(at,cw))
        # kids
        bui = __import__('bauiv1')
        gay = []
        for _ in m:
            uid,g = _
            at,n = g
            at = {i:(tuple(j) if isinstance(j,list) else j) for i,j in at.items()}
            f = getattr(bui,n)
            nat = {}
            for i,j in at.items():
                if isinstance(j,tuple) and len(j)==2:
                    if j[0]=='texture': j = gt(j[1])
                    elif j[0]=='uid':
                        if j[1]<0: j = s.tar
                        else: gay.append((uid,f,i,j[1])); continue
                nat[i] = j
            s.wids[uid] = f(**nat)
            s.MEM.append((uid,(nat,f)))
            tt = f'#{uid+1} {f.__name__[:-6]}'
            s.bt.append(tt)
            s.nid = uid
        for uid,f,i,j in gay:
            f(s.wids[uid],**{i:s.wids[j]})
        # finally
        s.sync()
        s.fresh()
        shut or nice('Loaded project!')

# [-1, [{'size': [500, 450], 'stack_offset': [0, 0]}, 'containerwidget']]
# [0, [{'parent': ['tar', 0], 'position': [253.9, 136.0], 'size': [100, 30], 'label': '#0 button'}, 'buttonwidget']]

#def ENCODE(a):
#    c=compress(dumps(a,separators=(',',':')).encode())
#    return str(int.from_bytes(c,'big'))
#def DECODE(s):
#    b=int(s); n=(b.bit_length()+7)//8
#    return loads(decompress(b.to_bytes(n,'big')).decode())

def CLEAN(obj, path=""):
    # Check if it's any type of callable (function, lambda, method, etc.)
    if callable(obj):
        print(f"Ignored callable object ({type(obj).__name__}) at {path}")
        return None
    elif hasattr(obj, '__dict__') and not isinstance(obj, (str, int, float, bool, type(None))):
        # Handle custom objects by converting to dict, then clean
        try:
            obj_dict = {}
            for k, v in obj.__dict__.items():
                cleaned_v = CLEAN(v, f"{path}.{k}" if path else k)
                obj_dict[k] = cleaned_v
            return obj_dict
        except:
            print(f"Ignored complex object ({type(obj).__name__}) at {path}")
            return None
    elif isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            cleaned_v = CLEAN(v, f"{path}.{k}" if path else str(k))
            cleaned[k] = cleaned_v
        return cleaned
    elif isinstance(obj, (list, tuple)):
        cleaned = []
        for i, item in enumerate(obj):
            cleaned_item = CLEAN(item, f"{path}[{i}]")
            cleaned.append(cleaned_item)
        return cleaned
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # Catch any other non-JSON-serializable types
        print(f"Ignored non-serializable object ({type(obj).__name__}) at {path}")
        return None
def ENCODE(a):
    c = compress(dumps(CLEAN(a), separators=(',', ':')).encode())
    return str(int.from_bytes(c, 'big'))
def DECODE(s):
    b = int(s); n = (b.bit_length() + 7) // 8
    return loads(decompress(b.to_bytes(n, 'big')).decode())

class File:
    COL1 = (0.4,0.4,0.4)
    COL2 = (0.7,0.7,0.7)
    def __init__(s,po):
        s.po = po
        r = res()
        K = s.K = []
        ys = s.ys = 307
        x,y = (-po.width-5,r[1]-ys)
        s.I = iw(
            parent=po.p,
            texture=gt('white'),
            position=(x,y),
            size=(po.width,ys),
            color=(0.25,0.25,0.25)
        )
        fade(s.I,j=0.0125,a=0.1)
        K.append(s.I)
        # debug
        K.append(bw(
            parent=po.p,
            position=(x+15,y+267),
            label='Debug Now',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL2,
            color=s.COL1,
            enable_sound=False,
            on_activate_call=po.debug
        ))
        # separator
        K.append(iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-17,1),
            opacity=0.6,
            position=(x+8,y+257)
        ))
        # save seed
        K.append(bw(
            parent=po.p,
            position=(x+15,y+217.5),
            label='Save Seed',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL2,
            color=s.COL1,
            enable_sound=False,
            on_activate_call=po.procp
        ))
        # load seed
        K.append(bw(
            parent=po.p,
            position=(x+15,y+180),
            label='Load Seed',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL2,
            color=s.COL1,
            enable_sound=False,
            on_activate_call=s.load
        ))
        # separator
        K.append(iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-17,1),
            opacity=0.6,
            position=(x+8,y+170)
        ))
        # export code
        K.append(bw(
            parent=po.p,
            position=(x+15,y+132.5),
            label='Export Code',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL2,
            color=s.COL1,
            enable_sound=False,
            on_activate_call=po.excode
        ))
        # copy code
        K.append(bw(
            parent=po.p,
            position=(x+15,y+95),
            label='Copy Code',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL2,
            color=s.COL1,
            enable_sound=False,
            on_activate_call=po.cpcode
        ))
        # separator
        K.append(iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-17,1),
            opacity=0.6,
            position=(x+8,y+85)
        ))
        # clear all
        K.append(bw(
            parent=po.p,
            position=(x+15,y+47),
            label='Clear All',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL2,
            color=s.COL1,
            enable_sound=False,
            on_activate_call=po.clearall
        ))
        # exit
        K.append(bw(
            parent=po.p,
            position=(x+15,y+10),
            label='Save & Exit',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL2,
            color=s.COL1,
            enable_sound=False,
            on_activate_call=po.exit
        ))
    def load(s):
        deek()
        i = getattr(s,'loadi',0)
        j = getattr(s,'loadj',[])
        if i:
            fade(i,i=1,a=-0.2)
            teck(1,i.delete)
            [_.delete() for _ in j]
            s.loadj = []
            s.loadi = 0
            return
        ys = 220
        x,y = -s.po.width*2-10,res()[1]-ys
        s.loadi = ij = iw(
            parent=s.po.p,
            texture=gt('white'),
            position=(x,y),
            size=(s.po.width,ys),
            color=(0.25,0.25,0.25)
        )
        s.K.append(ij)
        fade(ij,a=0.2)
        lj = s.loadj = getattr(s,'loadj',[])
        # note
        ij = tw(
            color=s.COL2,
            text='Paste your project\nseed below. Generate\nIt by pressing the\nCopy project button.',
            position=(x+10,y+ys-40),
            maxwidth=s.po.width-20,
            parent=s.po.p,
            shadow=1.2
        )
        s.K.append(ij)
        lj.append(ij)
        # separator
        ij = iw(
            parent=s.po.p,
            texture=gt('white'),
            size=(s.po.width-18,1),
            position=(x+9,y+ys-120),
            opacity=0.6
        )
        s.K.append(ij)
        lj.append(ij)
        # input
        ij = inp = tw(
            editable=True,
            size=(s.po.width-20,30),
            parent=s.po.p,
            color=s.COL2,
            position=(x+10,y+ys-160)
        )
        s.K.append(ij)
        lj.append(ij)
        # separator
        ij = iw(
            parent=s.po.p,
            texture=gt('white'),
            size=(s.po.width-18,1),
            position=(x+9,y+ys-170),
            opacity=0.6
        )
        s.K.append(ij)
        lj.append(ij)
        # load
        ij = bw(
            parent=s.po.p,
            texture=gt('white'),
            enable_sound=False,
            size=(s.po.width-30,30),
            textcolor=s.COL2,
            color=s.COL1,
            position=(x+15,y+ys-210),
            label='Load'
        )
        bw(ij,on_activate_call=lambda: s.po.proload(tw(query=inp)))
        s.K.append(ij)
        lj.append(ij)

class Grid:
    GRID_MAX = 100**2
    def __init__(s,po,trash=[],dry=False):
        s.po = po
        size = po.grid
        s.trash = trash
        K = s.K = []
        if dry:
            s.make(size[0],size[1])
            return
        r = res()
        x,y = -po.width-5,r[1]-360
        s.I = iw(
            parent=po.p,
            texture=gt('white'),
            position=(x,y),
            size=(po.width,140),
            color=(0.3,0,0)
        )
        fade(s.I,a=0.2)
        K.append(s.I)
        # size
        K.append(tw(
            parent=po.p,
            position=(x+10,y+95),
            text='Size',
            color=(0.7,0.2,0)
        ))
        K.append(tw(
            position=(x+65,y+95),
            size=(po.width/2-40,30),
            parent=po.p,
            editable=True,
            color=(1,0.6,0.6),
            allow_clear_button=False,
            text=str(size[0])
        ))
        K.append(tw(
            position=(x+130,y+95),
            size=(po.width/2-37,30),
            parent=po.p,
            editable=True,
            color=(1,0.6,0.6),
            allow_clear_button=False,
            text=str(size[1])
        ))
        # separator
        K.append(iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-18,1),
            position=(x+9,y+88),
            opacity=0.6
        ))
        # set
        K.append(bw(
            parent=po.p,
            position=(x+15,y+48),
            label='Set',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=(0.7,0.2,0.2),
            color=(0.5,0,0),
            on_activate_call=s.set,
            enable_sound=False
        ))
        # remove
        K.append(bw(
            parent=po.p,
            position=(x+15,y+10),
            label='Remove',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=(0.7,0.2,0.2),
            color=(0.5,0,0),
            on_activate_call=s.nuke,
            enable_sound=False
        ))
    def nuke(s):
        deek()
        [_.delete() for _ in s.trash]; s.trash.clear()
    def set(s):
        x,y = [tw(query=s.K[i]) for i in [2,3]]
        ok = '0.123456789'
        b = True
        if (not x or not y): b = False
        if (False in [_ in ok for _ in x]): b = False
        if (False in [_ in ok for _ in y]): b = False
        if not b: btw('Fix your input!'); return
        x,y = [int(float(_)) for _ in [x,y]]
        if x*y > s.GRID_MAX: btw('Grid too big!'); return
        deek()
        s.make(x,y)
        s.po.grid = [x,y]
    def make(s, w, h):
        s.nuke()
        zw, zh = s.po.TAR[1][0]['size']

        for i in range(h + 1):
            y = i * (zh / h) if h > 0 else 0
            s.trash.append(iw(
                parent=s.po.tar,
                position=(0, y),
                size=(zw, 1),
                texture=gt('white'),
                color=(1,0,0)
            ))

        for i in range(w + 1):
            x = i * (zw / w) if w > 0 else 0
            s.trash.append(iw(
                parent=s.po.tar,
                position=(x, 0),
                size=(1, zh),
                texture=gt('white'),
                color=(1,0,0)
            ))

class Preset:
    def __init__(s,po):
        s.K = K = []
        s.po = po
        src = s.src()
        sy = 8+len(src)*37
        r = res()
        x,y = -po.width-5,r[1]-sy*1.34
        s.I = iw(
            parent=po.p,
            texture=gt('white'),
            position=(x,y),
            size=(po.width,sy),
            color=(0.5,0.5,0)
        )
        fade(s.I,a=0.2)
        K.append(s.I)
        # presets
        c1,c2 = (1,1,0),(0.65,0.65,0)
        [K.append(bw(
            label=g[0],
            size=(po.width-26,30),
            position=(x+13,y+7+37*i),
            color=c2,
            enable_sound=False,
            textcolor=c1,
            parent=po.p,
            texture=gt('white'),
            on_activate_call=Call(s.load,i)
        )) for i,g in enumerate(src)]
    def load(s,i):
        deek()
        nid = s.po.nextid()
        f,k = s.src()[i][1:]
        s.po.wids[nid] = f(**k)
        s.po.MEM.append((nid,(k,f)))
        s.po.sync()
        s.po.bt.append(f'#{nid+1} {f.__name__[:-6]}')
        s.po.fresh()
    def src(s):
        ps = s.po.TAR[1][0]['size']
        h = s.po.nid + 1
        return [
            ('Small Back',bw,{
                'size':(40,40),
                'button_type':'backSmall',
                'textcolor':(1,1,1),
                'color':(0.75,0.2,0.2),
                'position':(50,ps[1]-50),
                'label':cs(sc.BACK),
                'parent':s.po.tar
            }),
            ('Big Back',bw,{
                'size':(100,40),
                'textcolor':(1,1,1),
                'button_type':'back',
                'color':(0.75,0.2,0.2),
                'position':(40,40),
                'label':f'#{h} Back',
                'parent':s.po.tar
            }),
            ('Slim Button',bw,{
                'size':(120,40),
                'textcolor':(1,1,1),
                'button_type':'square',
                'color':(0.2,0.7,0.8),
                'position':ran(ps),
                'label':f'#{h} Slim',
                'parent':s.po.tar
            }),
            ('Player Button',bw,{
                'size':(100,100),
                'button_type':'back',
                'color':(1,1,1),
                'position':ran(ps),
                'label':'',
                'texture':gt('agentIcon'),
                'mask_texture':gt('characterIconMask'),
                'parent':s.po.tar
            }),
            ('Editable Text',tw,{
                'parent':s.po.tar,
                'editable':True,
                'position':ran(ps),
                'size':(130,30),
                'text':f'#{h} Editable'
            }),
            ('Big Title',tw,{
                'parent':s.po.tar,
                'text':f'#{h} Title',
                'size':(130,40),
                'scale':2,
                'v_align':'top',
                'h_align':'right',
                'position':(ps[0]/2,ps[1]/2)
            }),
            ('H Separator',iw,{
                'texture':gt('white'),
                'opacity':0.6,
                'position':ran(ps),
                'size':(200,1),
                'parent':s.po.tar
            }),
            ('V Separator',iw,{
                'texture':gt('white'),
                'opacity':0.6,
                'position':ran(ps),
                'size':(1,200),
                'parent':s.po.tar
            }),
            ('Polish Button',bw,{
                'label':f'#{h} Polish',
                'parent':s.po.tar,
                'size':(s.po.width-30,30),
                'textcolor':Man.COL2,
                'button_type':'square',
                'color':Man.COL1,
                'position':ran(ps),
                'texture':gt('white')
            })
        ]

class Man:
    COL0 = (1.0,0.5,1.0)
    COL1 = (0.5,0.0,0.5)
    COL2 = (0.8,0.6,0.8)
    COL3 = (1.0,0.5,1.0) #(0.6,0.5,0.7)
    COL4 = (2.0,1,2.0) #(1.0,1.0,1.0)
    def __init__(s,w,po,wi):
        s.po = po
        x = -po.width-5
        s.wi = wi
        mem = po.MEM[s.wi][1]
        d = s.d = mem[0]
        s.f = f = mem[1]
        pos = d['position']
        size = d['size']
        s.K = K = []
        s.w,r = w,res()
        s.I = iw(
            parent=po.p,
            texture=gt('white'),
            position=(x,1),
            size=(po.width,r[1]-2),
            color=s.COL1
        )
        fade(s.I,a=0.2)
        K.append(s.I)
        # offset
        K.append(tw(
            parent=po.p,
            position=(x+10,r[1]-35),
            text='Pos',
            color=s.COL2
        ))
        K.append(ctw(
            position=(x+65,r[1]-35),
            fall=str(round(pos[0],1)),
            size=(po.width/2-40,30),
            mode=0,
            parent=po.p,
            color=s.COL2,
            on_edit=Call(s.set,'position',0)
        ).widget)
        K.append(ctw(
            position=(x+130,r[1]-35),
            fall=str(round(pos[1],1)),
            size=(po.width/2-35,30),
            mode=0,
            parent=po.p,
            color=s.COL2,
            on_edit=Call(s.set,'position',1)
        ).widget)
        # size
        K.append(tw(
            parent=po.p,
            position=(x+10,r[1]-65),
            text='Size',
            color=s.COL2
        ))
        s.fine = type(size) is tuple
        if s.fine:
            K.append(ctw(
                position=(x+65,r[1]-65),
                fall=str(round(size[0],1)),
                size=(po.width/2-40,30),
                mode=0,
                parent=po.p,
                color=s.COL2,
                on_edit=Call(s.set,'size',0)
            ).widget)
            K.append(ctw(
                position=(x+130,r[1]-65),
                fall=str(round(size[1],1)),
                size=(po.width/2-35,30),
                mode=0,
                parent=po.p,
                color=s.COL2,
                on_edit=Call(s.set,'size',1)
            ).widget)
        else:
            K.append(ctw(
                position=(x+65,r[1]-65),
                fall=str(round(size,1)),
                size=(po.width-70,30),
                mode=0,
                parent=po.p,
                color=s.COL2,
                on_edit=Call(s.set,'size',None)
            ).widget)
        # separator
        K.append(iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-18,1),
            position=(x+10,r[1]-70),
            opacity=0.6
        ))
        # btns
        for i in range(4):
            l = ['LEFT','DOWN','UP','RIGHT'][i]
            b = bw(
                texture=gt('white'),
                label=cs(getattr(sc,l+'_ARROW')),
                enable_sound=False,
                repeat=True,
                position=(x+i*(po.width/4.2)+11,r[1]-115),
                parent=po.p,
                size=(po.width/5-2,po.width/5-2),
                color=s.COL2,
                textcolor=s.COL1,
                on_activate_call=Call(s.mv,i)
            )
            K.append(b)
        for i in range(4):
            l = ['REWIND_BUTTON','DOWN_ARROW','UP_ARROW','FAST_FORWARD_BUTTON'][i]
            b = bw(
                texture=gt('white'),
                label=cs(getattr(sc,l))*[1,2][i in [1,2]],
                enable_sound=False,
                repeat=True,
                position=(x+i*(po.width/4.2)+11,r[1]-160),
                parent=po.p,
                size=(po.width/5-2,po.width/5-2),
                color=s.COL2,
                textcolor=s.COL1,
                on_activate_call=Call(s.mv,i,10)
            )
            K.append(b)
        # separator
        K.append(iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-18,1),
            position=(x+10,r[1]-167.5),
            opacity=0.6
        ))
        # kang
        d = kang(f,bad=['edit','size','position','parent'])
        ys = len(d)*30+10
        p0 = sw(
            parent=po.p,
            position=(x,78),
            border_opacity=0,
            size=(po.width,r[1]-244),
            color=s.COL1
        )
        K.append(p0)
        xs = GSW(max(d,key=GSW)+" ") if len(d) else GSW(' ')
        xs = [po.width,xs][xs>po.width]
        c0 = cw(
            parent=p0,
            size=(po.width,ys),
            background=False
        )
        p1 = hsw(
            parent=c0,
            position=(0,0),
            border_opacity=0,
            size=(po.width,ys)
        )
        K.append(p1)
        c1 = cw(
            parent=p1,
            size=(xs,po.width),
            background=False
        )
        for i,k in enumerate(d):
            t = tw(
                text=k,
                position=(5,ys-30*(i+1)-10),
                parent=c1,
                click_activate=True,
                selectable=True,
                glow_type='uniform',
                v_align='center',
                size=(xs,30),
                color=s.COL3,
            )
            tw(t,on_activate_call=Call(s.prev,k,t,mem=d))
        # dot
        dot = tw(parent=c1,position=(0,ys),text='.')
        cw(c1,visible_child=dot)
        dot.delete()
        # separator
        K.append(iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-18,1),
            position=(x+10,78),
            opacity=0.6
        ))
        # copy
        K.append(bw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-20,30),
            position=(x+10,42),
            enable_sound=False,
            on_activate_call=po.cp,
            label='Copy',
            color=s.COL2,
            textcolor=s.COL1
        ))
        # delete
        K.append(bw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-20,30),
            position=(x+10,6),
            enable_sound=False,
            label='Delete',
            on_activate_call=po.bye,
            color=s.COL2,
            textcolor=s.COL1
        ))
    def set(s,a,i,v):
        if i is None:
            o = s.d[a]
            o = float(v)
            s.d[a] = o
            d = {a:o}
        else:
            o = list(s.d[a])
            o[i] = float(v)
            s.d[a] = tuple(o)
            d = {a:tuple(o)}
        s.f(s.w,**d)
        s.d.update(d)
        s.po.bord()
    def mv(s,i,j=1):
        o = s.d['position']
        if i == 0: o = (o[0]-j,o[1])
        if i == 1: o = (o[0],o[1]-j)
        if i == 2: o = (o[0],o[1]+j)
        if i == 3: o = (o[0]+j,o[1])
        s.d['position'] = o
        s.f(s.w,position=o)
        tw(s.K[2],text=str(round(o[0],1)))
        tw(s.K[3],text=str(round(o[1],1)))
        s.po.bord()
        s.po.sync()
    def prev(s,k,t,mem,fa=1):
        on = t
        po = s.po
        o = getattr(s,'on',None)
        if o == on: return
        if o: tw(o,color=s.COL3)
        tw(on,color=s.COL4)
        p3 = getattr(s,'p3',0)
        if getattr(p3,'exists',lambda:False)():
            fade(p3,i=1,a=-0.2)
            p3j = getattr(s,'p3junk',[]).copy()
            [_.delete() for _ in p3j]
            p3.delete()
            s.prev(k,t,mem,fa=0)
            return
        s.on = on
        x,y = -2*s.po.width-10,res()[1]-341
        # bg
        ij = s.p3 = iw(
            parent=po.p,
            texture=gt('white'),
            color=s.COL1,
            position=(x,y),
            size=(po.width,341)
        )
        s.K.append(ij)
        fade(ij,a=0.2) if fa else 0
        # type hints
        b = bw(
            parent=po.p,
            position=(x+15,y+301),
            label='Type hints',
            enable_sound=False,
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            on_activate_call=lambda: (broad(brk(mem[k],70),color=s.COL1),deek())
        )
        s.K.append(b)
        s.p3junk = [b]
        # separator
        ij = iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-18,1),
            position=(x+10,y+291.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        # custom value
        at = po.MEM[s.wi][1][0]
        v = at.get(k,None)
        b = bw(
            parent=po.p,
            position=(x+15,y+215),
            label='Eval',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            enable_sound=False,
            on_activate_call=Call(s._val1,k)
        )
        s.K.append(b)
        s.p3junk.append(b)
        # pass widget
        b = bw(
            parent=po.p,
            position=(x+15,y+177),
            label='Widget',
            size=(po.width-30,30),
            enable_sound=False,
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            on_activate_call=Call(s._val2,k)
        )
        s.K.append(b)
        s.p3junk.append(b)
        # color
        b = bw(
            parent=po.p,
            position=(x+15,y+139),
            label='Color',
            size=(po.width-30,30),
            enable_sound=False,
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            on_activate_call=Call(s._val3,k)
        )
        s.K.append(b)
        s.p3junk.append(b)
        # separator
        ij = iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-18,1),
            position=(x+10,y+128),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        # value
        ij = s.val1v = tw(
            parent=po.p,
            color=s.COL2,
            position=(x+po.width/2.75+2.5,y+55),
            text=brk(str(v)),
            h_align='center',
            v_align='center',
            maxwidth=po.width-15,
            max_height=110,
            shadow=1.2
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        # text
        b = bw(
            parent=po.p,
            position=(x+15,y+253),
            label='Text',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            enable_sound=False,
            on_activate_call=Call(s._val0,k,v)
        )
        s.K.append(b)
        s.p3junk.append(b)
    def _val1(s,k,*a):
        deek()
        s.val1(k,*a,s.po.MEM[s.wi][1][0].get(k,None))
    def _val2(s,*a):
        deek()
        s.val2(*a)
    def _val3(s,*a):
        deek()
        s.val3(*a)
    def _val0(s,*a):
        deek()
        s.val0(*a)
    def val0(s,k,o,fa=1):
        p4 = getattr(s,'p4',0)
        po = s.po
        if getattr(p4,'exists',lambda:False)():
            fade(p4,i=1,a=-0.2)
            p4j = getattr(s,'p4junk',[]).copy()
            [_.delete() for _ in p4j]
            p4.delete()
            s.val0(k,o,fa=0)
            return
        x,y = -3*po.width-15,res()[1]-200
        # bg
        ij = s.p4 = iw(
            parent=po.p,
            texture=gt('white'),
            color=s.COL1,
            position=(x,y),
            size=(po.width,200)
        )
        fade(ij,a=0.2) if fa else 0
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk = [ij]
        # info
        ij = tw(
            parent=po.p,
            color=s.COL2,
            position=(x+10,y+160),
            text='Input literal text here,\nNo need to use quotes.\nUse Eval for raw input.',
            maxwidth=po.width-20,
            shadow=1.2
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-18,1),
            position=(x+10,y+98),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # input
        ij = s.val0t = tw(
            parent=po.p,
            editable=True,
            color=s.COL2,
            position=(x+10,y+60),
            size=(po.width-20,30),
            description='Example input: Hello, World!\nEnter',
            text=str(o or ''),
            allow_clear_button=False
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-18,1),
            position=(x+10,y+52.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # continue
        b = bw(
            parent=po.p,
            position=(x+15,y+10),
            label='Apply',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            enable_sound=False,
            on_activate_call=Call(s.val0a,k)
        )
        s.K.append(b)
        s.p3junk.append(b)
        s.p4junk.append(b)
    def val0a(s,k):
        v = tw(query=s.val0t)
        try: s.f(s.w,**{k:v})
        except Exception as e: err(str(e)); return
        nice('Applied!')
        tw(s.val1v,text=brk(v))
        s.po.MEM[s.wi][1][0].update({k:v})
        s.po.sync()
        s.po.bord()
    def val3(s,k,fa=1):
        po = s.po
        p4 = getattr(s,'p4',0)
        if getattr(p4,'exists',lambda:False)():
            fade(p4,i=1,a=-0.2)
            p4j = getattr(s,'p4junk',[]).copy()
            [_.delete() for _ in p4j]
            p4.delete()
            s.val3(k,fa=0)
            return
        oy = 280
        x,y = -3*s.po.width-15,res()[1]-oy
        # bg
        ij = s.p4 = iw(
            parent=po.p,
            texture=gt('white'),
            color=s.COL1,
            position=(x,y),
            size=(po.width,oy)
        )
        fade(ij,a=0.2) if fa else 0
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk = [ij]
        # colors
        ok = 19
        c = s.d.get(k,())
        s.val3oc = c = c if isinstance(c,tuple) else ()
        for cx in range(10):
            for cy in range(10):
                px, py = (x+5+cx*ok,y+oy-5-ok-cy*ok)
                c = HTR(cx / 9.0, 1.0, 1.0 - (cy / 9.0))
                ij = bw(
                    parent=po.p,
                    texture=gt('white'),
                    color=c,
                    on_activate_call=Call(s.val3p,c,px,py),
                    label='',
                    size=(ok,ok),
                    position=(px,py),
                    enable_sound=False
                )
                s.K.append(ij)
                s.p3junk.append(ij)
                s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-8,1),
            position=(x+4,y+oy-199.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # preview
        s.val3pr = ij = bw(
            parent=po.p,
            size=(po.width-22,30),
            position=(x+11,y+oy-235),
            label='',
            on_activate_call=s.val3br,
            enable_sound=False,
            color=s.val3oc or (0,0,0),
            texture=gt('white')
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-8,1),
            position=(x+4,y+oy-240.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # set
        ij = bw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-22,30),
            label='Set',
            position=(x+11,y+oy-275),
            enable_sound=False,
            textcolor=s.COL1,
            color=s.COL2,
            on_activate_call=Call(s.val3s,k)
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
    def val3s(s,k):
        c = s.val3oc
        if not c: btw('Select a color first!'); return
        c = tuple(RND(c))
        d = {k:c}
        try: s.f(s.w,**d)
        except Exception as e: err(str(e)); return
        s.po.MEM[s.wi][1][0].update(d)
        s.po.sync()
        tw(s.val1v,text=str(c))
        nice('Applied!')
    def val3br(s):
        c = s.val3oc
        if not c: btw('Select a color first!'); return
        broad(SHRT(c),color=c)
        deek()
    def val3p(s,c,px,py):
        deek()
        s.val3oc = c
        bw(s.val3pr,color=c)
        j = getattr(s,'val3j',[])
        [_.delete() for _ in j]; j.clear()
        s.val3j = []
        for _ in range(4):
            x = [0,18,0,0][_]
            y = [18,0,0,0][_]
            sx = [20,2,20,2][_]
            sy = [2,20,2,20][_]
            ij = iw(
                parent=s.po.p,
                texture=gt('white'),
                size=(sx,sy),
                position=(px+x,py+y)
            )
            s.K.append(ij)
            s.p3junk.append(ij)
            s.p4junk.append(ij)
            s.val3j.append(ij)
    def val1(s,k,o,fa=1):
        p4 = getattr(s,'p4',0)
        po = s.po
        if getattr(p4,'exists',lambda:False)():
            fade(p4,i=1,a=-0.2)
            p4j = getattr(s,'p4junk',[]).copy()
            [_.delete() for _ in p4j]
            p4.delete()
            s.val1(k,o,fa=0)
            return
        x,y = -3*po.width-15,res()[1]-200
        # bg
        ij = s.p4 = iw(
            parent=po.p,
            texture=gt('white'),
            color=s.COL1,
            position=(x,y),
            size=(po.width,200)
        )
        fade(ij,a=0.2) if fa else 0
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk = [ij]
        # info
        ij = tw(
            parent=po.p,
            color=s.COL2,
            position=(x+10,y+160),
            text='Input something to\neval. Make sure to\nuse quotes for str.',
            maxwidth=po.width-20,
            shadow=1.2
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-18,1),
            position=(x+10,y+98),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # input
        ij = s.val1t = tw(
            parent=po.p,
            editable=True,
            color=s.COL2,
            position=(x+10,y+60),
            size=(po.width-20,30),
            description='Example input: (123,68)\nYou can also use anything defined in polish.py. Enter',
            text=o if o is None else f"'{o}'" if isinstance(o,str) else str(o),
            allow_clear_button=False
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-18,1),
            position=(x+10,y+52.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # continue
        b = bw(
            parent=po.p,
            position=(x+15,y+10),
            label='Run',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            enable_sound=False,
            on_activate_call=Call(s.val1e,k)
        )
        s.K.append(b)
        s.p3junk.append(b)
        s.p4junk.append(b)
    def val1e(s,k):
        t = tw(query=s.val1t)
        try:
            v = eval(t)
            if k == 'transition' and v.startswith('out'): raise Exception('What are you doing?')
            s.f(s.w,**{k:v})
        except Exception as e: err(str(e)); return
        nice('Saved!')
        tw(s.val1v,text=brk(str(v)))
        s.po.MEM[s.wi][1][0].update({k:v})
        s.po.sync()
        s.po.bord()
    def val2(s,k,fa=1):
        po = s.po
        p4 = getattr(s,'p4',0)
        if getattr(p4,'exists',lambda:False)():
            fade(p4,i=1,a=-0.2)
            p4j = getattr(s,'p4junk',[]).copy()
            [_.delete() for _ in p4j]
            p4.delete()
            s.val2(k,fa=0)
            return
        x,y = -3*s.po.width-15,res()[1]-200
        # bg
        ij = s.p4 = iw(
            parent=po.p,
            texture=gt('white'),
            color=s.COL1,
            position=(x,y),
            size=(po.width,200)
        )
        fade(ij,a=0.2) if fa else 0
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk = [ij]
        # scroll
        l = s.po.kids()
        i = len(l)
        ij = sw(
            parent=po.p,
            position=(x,y+60),
            border_opacity=0,
            size=(po.width,140)
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        ys = 30*i
        cv = cw(
            parent=ij,
            size=(po.width,ys),
            background=False
        )
        for n,w in enumerate(l):
            t = tw(
                parent=cv,
                size=(po.width,30),
                text=po.bt[n],
                position=(10,ys-30*(n+1)),
                color=(0.7,0.5,1),
                maxwidth=po.width-20,
                selectable=True,
                glow_type='uniform',
                click_activate=True
            )
            tw(t,on_activate_call=Call(s.val2p,t,n))
        # separator
        ij = iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-18,1),
            position=(x+10,y+52.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # continue
        b = bw(
            parent=po.p,
            position=(x+15,y+10),
            label='Select',
            size=(po.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            enable_sound=False,
            on_activate_call=Call(s.val2c,k)
        )
        s.K.append(b)
        s.p3junk.append(b)
        s.p4junk.append(b)
        # fallback
        if not len(l):
            ij = tw(
                parent=po.p,
                position=(x+75,y+110),
                text='No children!',
                color=(0,1,1),
                h_align='center',
                v_align='center'
            )
            s.K.append(ij)
            s.p3junk.append(ij)
            s.p4junk.append(ij)
    def val2c(s,k):
        o = getattr(s,'val2o',(0,0))
        if not o[0]: btw('Select a widget!'); return
        try: w = s.po.kids()[o[1]]; s.f(s.w,**{k:w})
        except Exception as e: err(str(e)); return
        nice('Value set!')
        s.po.MEM[s.wi][1][0].update({k:w})
        s.po.sync()
        tw(s.val1v,text=brk(str(w)))
        refresh()
    def val2p(s,w,i):
        o = getattr(s,'val2o',(0,0))
        if o[0] == w: return
        if o[0]: tw(o[0],color=s.COL3)
        s.val2o = (w,i); tw(w,color=s.COL4)

class Add:
    def __init__(s):
        po = s.po = Polish.INS
        s.p = po.p
        s.width = po.width
        s.at = po.at
        s.tar = po.tar
        r = res()
        s.ui = __import__('bauiv1')
        a = s.a = [_ for _ in dir(s.ui) if _.endswith('widget') and '_' not in _ and _ != 'widget']
        sy = (len(a)+1)*30
        x,y = -s.width-5,r[1]-sy*1.25
        s.K = K = []
        s.I = iw(
            parent=s.p,
            texture=gt('white'),
            position=(x,y),
            size=(s.width,sy+35),
            color=(0,0.3,0)
        )
        fade(s.I,a=0.2)
        K.append(s.I)
        for i,w in enumerate(a):
            t = w[:-6]
            s.K.append(bw(
                parent=s.p,
                size=(s.width-30,30),
                texture=gt('white'),
                color=(0,0.5,0),
                textcolor=(0,0.8,0),
                enable_sound=False,
                on_activate_call=Call(s.add,i,t),
                label=t,
                position=(x+15,10+y+35*i)
            ))
    def add(s,i,t):
        deek()
        f = getattr(s.ui,s.a[i])
        p = s.at['size']; p = ran(p)
        nid = s.po.nextid()
        tt = f'#{nid+1} {f.__name__[:-6]}'
        d = {
            'parent':s.tar,
            'position':p,
            'size':50 if t in ['spinner'] else (100,30),
            **([{},{'text':tt}][f.__name__[:-6] in ['text','checkbox']]),
            **([{'label':tt},{}][f!=bw])
        }
        s.po.wids[nid] = f(**d)
        s.po.MEM.append((nid,(d,f)))
        s.po.sync()
        s.po.bt.append(tt)
        s.po.fresh()

class Anim:
    def __init__(s):
        po = s.po = Polish.INS
        s.p = po.p
        s.width = po.width
        s.tar = po.tar
        r = res()
        x,y = -s.width-5,r[1]-250
        K = s.K = []
        s.I = iw(
            parent=s.p,
            texture=gt('white'),
            position=(x,y),
            size=(s.width,165),
            color=(0,0.2,0.2)
        )
        fade(s.I,a=0.2)
        K.append(s.I)
        # in
        K.append(tw(
            parent=s.p,
            position=(x+10,y+130),
            text=cs(sc.RIGHT_ARROW),
            color=(0,0.6,0.6)
        ))
        K.append(tw(
            parent=s.p,
            editable=True,
            text=po.TAR[1][0].get('transition',None),
            size=(s.width-56,30),
            allow_clear_button=False,
            color=(0,0.6,0.6),
            position=(x+45,y+127)
        ))
        # out
        K.append(tw(
            parent=s.p,
            position=(x+10,y+98),
            text=cs(sc.LEFT_ARROW),
            color=(0,0.6,0.6)
        ))
        K.append(tw(
            parent=s.p,
            editable=True,
            size=(s.width-56,30),
            text=po.TAR[1][0].get('out_anim',None),
            allow_clear_button=False,
            color=(0,0.6,0.6),
            position=(x+45,y+95)
        ))
        # separator
        K.append(iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            position=(x+10,y+87),
            opacity=0.6
        ))
        # play
        K.append(bw(
            parent=s.p,
            position=(x+15,y+48),
            label='Play',
            size=(s.width-30,30),
            texture=gt('white'),
            textcolor=(0,0.6,0.6),
            color=(0,0.35,0.35),
            on_activate_call=s.play,
            enable_sound=False
        ))
        # set
        K.append(bw(
            parent=s.p,
            position=(x+15,y+10),
            label='Set',
            size=(s.width-30,30),
            texture=gt('white'),
            textcolor=(0,0.6,0.6),
            color=(0,0.35,0.35),
            on_activate_call=s.set,
            enable_sound=False
        ))
    def get(s,i):
        return tw(query=s.K[i])
    def play(s,dry=False):
        t = s.get(2)
        ok = ['in_'+_ for _ in OK()]
        if not t in ok: btw(f'In animation varies from:\n{ok}'); return
        if dry: return t
        cw(s.tar,transition=t)
        gs('swish').play()
    def set(s):
        i = s.play(True)
        o = s.get(4)
        if not i: return
        ok = ['out_'+_ for _ in OK()]
        if o not in ok: btw(f'Out animation varies from:\n{ok}'); return
        s.po.TAR[1][0].update({'transition':i,'out_anim':o})
        s.po.sync()
        nice('Saved!')

class Root:
    COL1 = (0,0.4,0.4)
    COL2 = (0,0.7,0.7)
    COL3 = (0,1,1)
    def __init__(s):
        po = s.po = Polish.INS
        s.p = po.p
        s.tar = po.tar
        s.size = s.po.TAR[1][0]['size']
        r = res()
        s.width = Polish.width
        x,y = -s.width-5,1
        K = s.K = []
        s.I = iw(
            parent=s.p,
            texture=gt('white'),
            position=(x,y),
            size=(s.width,r[1]-1),
            color=s.COL1
        )
        fade(s.I,j=0.0125,a=0.1)
        K.append(s.I)
        # offset
        off = s.po.TAR[1][0]['stack_offset']
        K.append(tw(
            parent=s.p,
            position=(x+10,r[1]-35),
            text='Offs',
            color=s.COL2
        ))
        K.append(ctw(
            position=(x+65,r[1]-35),
            fall=str(round(off[0],1)),
            size=(s.width/2-40,30),
            mode=0,
            parent=s.p,
            color=s.COL2,
            on_edit=Call(s.set,'stack_offset',0)
        ).widget)
        K.append(ctw(
            position=(x+130,r[1]-35),
            fall=str(round(off[1],1)),
            size=(s.width/2-35,30),
            mode=0,
            parent=s.p,
            color=s.COL2,
            on_edit=Call(s.set,'stack_offset',1)
        ).widget)
        # size
        K.append(tw(
            parent=s.p,
            position=(x+10,r[1]-65),
            text='Size',
            color=s.COL2
        ))
        K.append(ctw(
            position=(x+65,r[1]-65),
            fall=str(round(s.size[0],1)),
            size=(s.width/2-40,30),
            mode=0,
            parent=s.p,
            color=s.COL2,
            on_edit=Call(s.set,'size',0)
        ).widget)
        K.append(ctw(
            position=(x+130,r[1]-65),
            fall=str(round(s.size[1],1)),
            size=(s.width/2-35,30),
            mode=0,
            parent=s.p,
            color=s.COL2,
            on_edit=Call(s.set,'size',1)
        ).widget)
        # separator
        K.append(iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            position=(x+10,r[1]-70),
            opacity=0.6
        ))
        # btns
        for i in range(4):
            l = ['LEFT','DOWN','UP','RIGHT'][i]
            b = bw(
                texture=gt('white'),
                label=cs(getattr(sc,l+'_ARROW')),
                enable_sound=False,
                repeat=True,
                position=(x+i*(s.width/4.2)+11,r[1]-115),
                parent=s.p,
                size=(s.width/5-2,s.width/5-2),
                color=s.COL2,
                textcolor=s.COL1,
                on_activate_call=Call(s.mv,i)
            )
            K.append(b)
        for i in range(4):
            l = ['REWIND_BUTTON','DOWN_ARROW','UP_ARROW','FAST_FORWARD_BUTTON'][i]
            b = bw(
                texture=gt('white'),
                label=cs(getattr(sc,l))*[1,2][i in [1,2]],
                enable_sound=False,
                repeat=True,
                position=(x+i*(s.width/4.2)+11,r[1]-160),
                parent=s.p,
                size=(s.width/5-2,s.width/5-2),
                color=s.COL2,
                textcolor=s.COL1,
                on_activate_call=Call(s.mv,i,10)
            )
            K.append(b)
        # separator
        K.append(iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            position=(x+10,r[1]-167.5),
            opacity=0.6
        ))
        # kang
        d = kang(cw,bad=['edit','size','stack_offset','parent'])
        ys = len(d)*30+10
        p0 = sw(
            parent=s.p,
            position=(x,1),
            border_opacity=0,
            size=(s.width,r[1]-170),
            color=s.COL2
        )
        K.append(p0)
        xs = GSW(max(d,key=GSW)+" ")
        c0 = cw(
            parent=p0,
            size=(s.width,ys),
            background=False
        )
        p1 = hsw(
            parent=c0,
            position=(0,0),
            border_opacity=0,
            size=(s.width,ys)
        )
        K.append(p1)
        c1 = cw(
            parent=p1,
            size=(xs,s.width),
            background=False
        )
        for i,k in enumerate(d):
            t = tw(
                text=k,
                position=(5,ys-30*(i+1)-10),
                parent=c1,
                click_activate=True,
                selectable=True,
                glow_type='uniform',
                v_align='center',
                size=(xs,30),
                color=s.COL2,
            )
            tw(t,on_activate_call=Call(s.prev,k,t,mem=d))
        # dot
        dot = tw(parent=c1,position=(0,ys),text='.')
        cw(c1,visible_child=dot)
        dot.delete()
    def prev(s,k,t,mem,fa=1):
        on = t
        o = getattr(s,'on',None)
        if o == on: return
        if o: tw(o,color=s.COL2)
        tw(on,color=s.COL3)
        p3 = getattr(s,'p3',0)
        if getattr(p3,'exists',lambda:False)():
            fade(p3,i=1,a=-0.2)
            p3j = getattr(s,'p3junk',[]).copy()
            [_.delete() for _ in p3j]
            p3.delete()
            s.prev(k,t,mem,fa=0)
            return
        s.on = on
        x,y = -2*s.width-10,res()[1]-341
        # bg
        ij = s.p3 = iw(
            parent=s.p,
            texture=gt('white'),
            color=s.COL1,
            position=(x,y),
            size=(s.width,341)
        )
        s.K.append(ij)
        fade(ij,a=0.2) if fa else 0
        # type hints
        b = bw(
            parent=s.p,
            position=(x+15,y+301),
            label='Type hints',
            enable_sound=False,
            size=(s.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            on_activate_call=lambda: (broad(brk(mem[k],70),color=s.COL1),deek())
        )
        s.K.append(b)
        s.p3junk = [b]
        # separator
        ij = iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            position=(x+10,y+291.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        # custom value
        at = s.po.TAR[1][0]
        v = at.get(k,None)
        b = bw(
            parent=s.p,
            position=(x+15,y+215),
            label='Eval',
            size=(s.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            enable_sound=False,
            on_activate_call=Call(s._val1,k,v)
        )
        s.K.append(b)
        s.p3junk.append(b)
        # pass widget
        b = bw(
            parent=s.p,
            position=(x+15,y+177),
            label='Widget',
            size=(s.width-30,30),
            enable_sound=False,
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            on_activate_call=Call(s._val2,k)
        )
        s.K.append(b)
        s.p3junk.append(b)
        # color
        b = bw(
            parent=s.p,
            position=(x+15,y+139),
            label='Color',
            size=(s.width-30,30),
            enable_sound=False,
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            on_activate_call=Call(s._val3,k)
        )
        s.K.append(b)
        s.p3junk.append(b)
        # separator
        ij = iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            position=(x+10,y+128),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        # value
        ij = s.val1v = tw(
            parent=s.p,
            color=s.COL3,
            position=(x+s.width/2.75+2.5,y+55),
            text=brk(str(v)),
            h_align='center',
            v_align='center',
            maxwidth=s.width-15,
            max_height=110
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        # text
        b = bw(
            parent=s.p,
            position=(x+15,y+253),
            label='Text',
            size=(s.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            enable_sound=False,
            on_activate_call=Call(s._val0,k,v)
        )
        s.K.append(b)
        s.p3junk.append(b)
    def _val0(s,*a):
        deek()
        s.val0(*a)
    def val0(s,k,o,fa=1):
        p4 = getattr(s,'p4',0)
        if getattr(p4,'exists',lambda:False)():
            fade(p4,i=1,a=-0.2)
            p4j = getattr(s,'p4junk',[]).copy()
            [_.delete() for _ in p4j]
            p4.delete()
            s.val0(k,o,fa=0)
            return
        x,y = -3*s.width-15,res()[1]-200
        # bg
        ij = s.p4 = iw(
            parent=s.p,
            texture=gt('white'),
            color=s.COL1,
            position=(x,y),
            size=(s.width,200)
        )
        fade(ij,a=0.2) if fa else 0
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk = [ij]
        # info
        ij = tw(
            parent=s.p,
            color=s.COL3,
            position=(x+10,y+160),
            text='Input literal text here,\nNo need to use quotes.\nUse Eval for raw input.',
            maxwidth=s.width-20
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            position=(x+10,y+98),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # input
        ij = s.val0t = tw(
            parent=s.p,
            editable=True,
            color=s.COL3,
            position=(x+10,y+60),
            size=(s.width-20,30),
            description='Example input: Hello, World!\nEnter',
            text=str(o or ''),
            allow_clear_button=False
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            position=(x+10,y+52.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # continue
        b = bw(
            parent=s.p,
            position=(x+15,y+10),
            label='Apply',
            size=(s.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            enable_sound=False,
            on_activate_call=Call(s.val0a,k)
        )
        s.K.append(b)
        s.p3junk.append(b)
        s.p4junk.append(b)
    def val0a(s,k):
        v = tw(query=s.val0t)
        try: cw(s.tar,**{k:v})
        except Exception as e: err(str(e)); return
        nice('Applied!')
        tw(s.val1v,text=brk(v))
        s.po.TAR[1][0].update({k:v})
        s.po.sync()
        refresh()
    def _val3(s,*a):
        deek()
        s.val3(*a)
    def val3(s,k,fa=1):
        po = s.po
        p4 = getattr(s,'p4',0)
        if getattr(p4,'exists',lambda:False)():
            fade(p4,i=1,a=-0.2)
            p4j = getattr(s,'p4junk',[]).copy()
            [_.delete() for _ in p4j]
            p4.delete()
            s.val3(k,fa=0)
            return
        oy = 280
        x,y = -3*s.po.width-15,res()[1]-oy
        # bg
        ij = s.p4 = iw(
            parent=po.p,
            texture=gt('white'),
            color=s.COL2,
            position=(x,y),
            size=(po.width,oy)
        )
        fade(ij,a=0.2) if fa else 0
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk = [ij]
        # colors
        ok = 19
        d = po.TAR[1][0]
        c = d.get(k,())
        s.val3oc = c = c if isinstance(c,tuple) else ()
        for cx in range(10):
            for cy in range(10):
                px, py = (x+5+cx*ok,y+oy-5-ok-cy*ok)
                c = HTR(cx / 9.0, 1.0, 1.0 - (cy / 9.0))
                ij = bw(
                    parent=po.p,
                    texture=gt('white'),
                    color=c,
                    on_activate_call=Call(s.val3p,c,px,py),
                    label='',
                    size=(ok,ok),
                    position=(px,py),
                    enable_sound=False
                )
                s.K.append(ij)
                s.p3junk.append(ij)
                s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-8,1),
            position=(x+4,y+oy-199.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # preview
        s.val3pr = ij = bw(
            parent=po.p,
            size=(po.width-22,30),
            position=(x+11,y+oy-235),
            label='',
            on_activate_call=s.val3br,
            enable_sound=False,
            color=s.val3oc or (0,0,0),
            texture=gt('white')
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-8,1),
            position=(x+4,y+oy-240.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # set
        ij = bw(
            parent=po.p,
            texture=gt('white'),
            size=(po.width-22,30),
            label='Set',
            position=(x+11,y+oy-275),
            enable_sound=False,
            textcolor=s.COL2,
            color=s.COL1,
            on_activate_call=Call(s.val3s,k)
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
    def val3s(s,k):
        c = s.val3oc
        if not c: btw('Select a color first!'); return
        c = tuple(RND(c))
        d = {k:c}
        try: cw(s.po.tar,**d)
        except Exception as e: err(str(e)); return
        s.po.TAR[1][0].update(d)
        s.po.sync()
        tw(s.val1v,text=str(c))
        nice('Applied!')
    def val3br(s):
        c = s.val3oc
        if not c: btw('Select a color first!'); return
        broad(SHRT(c),color=c)
        deek()
    def val3p(s,c,px,py):
        deek()
        s.val3oc = c
        bw(s.val3pr,color=c)
        j = getattr(s,'val3j',[])
        [_.delete() for _ in j]; j.clear()
        s.val3j = []
        for _ in range(4):
            x = [0,18,0,0][_]
            y = [18,0,0,0][_]
            sx = [20,2,20,2][_]
            sy = [2,20,2,20][_]
            ij = iw(
                parent=s.po.p,
                texture=gt('white'),
                size=(sx,sy),
                position=(px+x,py+y)
            )
            s.K.append(ij)
            s.p3junk.append(ij)
            s.p4junk.append(ij)
            s.val3j.append(ij)
    def _val1(s,*a):
        deek()
        s.val1(*a)
    def _val2(s,*a):
        deek()
        s.val2(*a)
    def val1(s,k,o,fa=1):
        p4 = getattr(s,'p4',0)
        if getattr(p4,'exists',lambda:False)():
            fade(p4,i=1,a=-0.2)
            p4j = getattr(s,'p4junk',[]).copy()
            [_.delete() for _ in p4j]
            p4.delete()
            s.val1(k,o,fa=0)
            return
        x,y = -3*s.width-15,res()[1]-200
        # bg
        ij = s.p4 = iw(
            parent=s.p,
            texture=gt('white'),
            color=s.COL1,
            position=(x,y),
            size=(s.width,200)
        )
        fade(ij,a=0.2) if fa else 0
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk = [ij]
        # info
        ij = tw(
            parent=s.p,
            color=s.COL3,
            position=(x+10,y+160),
            text='Input something to\neval. Make sure to\nuse quotes for str.',
            maxwidth=s.width-20
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            position=(x+10,y+98),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # input
        ij = s.val1t = tw(
            parent=s.p,
            editable=True,
            color=s.COL3,
            position=(x+10,y+60),
            size=(s.width-20,30),
            description='Example input: (123,68)\nYou can also use anything defined in polish.py. Enter',
            text=o if o is None else f"'{o}'" if isinstance(o,str) else str(o),
            allow_clear_button=False
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # separator
        ij = iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            position=(x+10,y+52.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # continue
        b = bw(
            parent=s.p,
            position=(x+15,y+10),
            label='Run',
            size=(s.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            enable_sound=False,
            on_activate_call=Call(s.val1e,k)
        )
        s.K.append(b)
        s.p3junk.append(b)
        s.p4junk.append(b)
    def val1e(s,k):
        t = tw(query=s.val1t)
        try:
            v = eval(t)
            if (k == 'transition' and v.startswith('out')) or (isinstance(v,(tuple,list)) and len(v) == 2 and v[0] == 'uid' and isinstance(v[1],int)): raise Exception('What are you doing?')
            cw(s.tar,**{k:v})
        except Exception as e: err(str(e)); return
        nice('Saved!')
        tw(s.val1v,text=brk(str(v)))
        s.po.TAR[1][0].update({k:v})
        s.po.sync()
        refresh()
    def val2(s,k,fa=1):
        p4 = getattr(s,'p4',0)
        if getattr(p4,'exists',lambda:False)():
            fade(p4,i=1,a=-0.2)
            p4j = getattr(s,'p4junk',[]).copy()
            [_.delete() for _ in p4j]
            p4.delete()
            s.val2(k,fa=0)
            return
        x,y = -3*s.width-15,res()[1]-200
        # bg
        ij = s.p4 = iw(
            parent=s.p,
            texture=gt('white'),
            color=s.COL1,
            position=(x,y),
            size=(s.width,200)
        )
        fade(ij,a=0.2) if fa else 0
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk = [ij]
        # scroll
        l = s.po.kids()
        i = len(l)
        ij = sw(
            parent=s.p,
            position=(x,y+60),
            border_opacity=0,
            size=(s.width,140)
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        ys = 30*i
        cv = cw(
            parent=ij,
            size=(s.width,ys),
            background=False
        )
        for n,w in enumerate(l):
            t = tw(
                parent=cv,
                size=(s.width,30),
                text=s.po.bt[n],
                position=(10,ys-30*(n+1)),
                color=(0.7,0.5,1),
                maxwidth=s.width-20,
                selectable=True,
                glow_type='uniform',
                click_activate=True
            )
            tw(t,on_activate_call=Call(s.val2p,t,n))
        # separator
        ij = iw(
            parent=s.p,
            texture=gt('white'),
            size=(s.width-18,1),
            position=(x+10,y+52.5),
            opacity=0.6
        )
        s.K.append(ij)
        s.p3junk.append(ij)
        s.p4junk.append(ij)
        # continue
        b = bw(
            parent=s.p,
            position=(x+15,y+10),
            label='Select',
            size=(s.width-30,30),
            texture=gt('white'),
            textcolor=s.COL1,
            color=s.COL2,
            enable_sound=False,
            on_activate_call=Call(s.val2c,k)
        )
        s.K.append(b)
        s.p3junk.append(b)
        s.p4junk.append(b)
        # fallback
        if not len(l):
            ij = tw(
                parent=s.p,
                position=(x+75,y+110),
                text='No children!',
                color=s.COL3,
                h_align='center',
                v_align='center'
            )
            s.K.append(ij)
            s.p3junk.append(ij)
            s.p4junk.append(ij)
    def val2c(s,k):
        o = getattr(s,'val2o',(0,0))
        if not o[0]: btw('Select a widget!'); return
        try: w = s.po.kids()[o[1]]; cw(s.tar,**{k:w})
        except Exception as e: err(str(e)); return
        nice('Value set!')
        s.po.TAR[1][0].update({k:w})
        s.po.sync()
        tw(s.val1v,text=brk(str(w)))
        refresh()
    def val2p(s,w,i):
        o = getattr(s,'val2o',(0,0))
        if o[0] == w: return
        if o[0]: tw(o[0],color=(0.7,0.5,1))
        s.val2o = (w,i); tw(w,color=s.COL2)
    def set(s,a,i,v):
        o = list(s.po.TAR[1][0][a])
        o[i] = float(v)
        d = {a:tuple(o)}
        cw(s.tar,**d)
        s.po.TAR[1][0].update(d)
        s.po.sync()
        s.po.fresh()
        refresh()
    def mv(s,i,j=1):
        o = s.po.TAR[1][0]['stack_offset']
        if i == 0: o = (o[0]-j,o[1])
        if i == 1: o = (o[0],o[1]-j)
        if i == 2: o = (o[0],o[1]+j)
        if i == 3: o = (o[0]+j,o[1])
        s.po.TAR[1][0]['stack_offset'] = o
        s.po.sync()
        cw(s.tar,stack_offset=o)
        tw(s.K[2],text=str(round(o[0],1)))
        tw(s.K[3],text=str(round(o[1],1)))
        refresh()

class ctw:
    def __init__(s,mode,fall,on_edit=None,**k):
        s.fall = fall
        s.allow = ['-0.123456789',True][mode]
        s.bad = False
        s.on_edit = on_edit
        s.color = k['color']
        s.widget = tw(
            editable=True,
            text=fall,
            allow_clear_button=False,
            flatness=1.0,
            shadow=0.0,
            v_align='center',
            maxwidth=k['size'][0],
            **k
        )
        s.ot = fall
        s.spy()
    def get_text(s): return tw(query=s.widget)
    def col(s,c=None): tw(s.widget,color=c or s.color)
    def spy(s):
        if not s.widget.exists(): return
        t = s.get_text()
        teck(0.25,s.spy)
        if t == s.ot: return
        s.ot = t
        if False in [i in s.allow for i in t]:
            s.bad = True
            btw('Fix your input!')
            s.col((1,0,0))
            return # bad text
        elif s.bad:
            s.bad = False
            s.col()
        s.on_edit(t) if callable(s.on_edit) and t else None

# Global
BASE = CONT = None
ROOT = lambda: join(env()['python_directory_user'],'Polish')
makedirs(ROOT(), exist_ok=True)
ran = lambda s: (round(uf(0,s[0]),1),round(uf(0,s[1]),1))
refresh = lambda: APP.set_ui_scale(UIS())
push = lambda t,**k: broad(t,**k,top=True)
err = lambda t: (broad(t,color=(1,0,0)),gs('error').play())
GOS = lambda: gsw('overlay_stack')
OK = lambda: ['scale','left','right']
GSW = lambda t: strw(t,suppress_warning=True)
SHRT = lambda c: '\n'.join([['RED','GREEN','BLUE'][_]+'='+str(round(c[_],2)) for _ in [0,1,2]])
RND = lambda c: [round(_,2) for _ in c]
def UIS(a=None):
    if a is None: return APP.ui_v1.uiscale
    APP.ui_v1.uiscale = a
f = SUB.on_screen_size_change; SUB.on_screen_size_change = lambda *a,**k: (Polish.resize(),f(*a,**k))
deek = lambda: gs('deek').play()
nice = lambda t: (broad(t,color=(0,1,0)),gs('dingSmallHigh').play())
btw = lambda t: (broad(t,color=(1,1,0)),gs('block').play())
def var(s, v=None):
    cfg = APP.config; s = Polish.PRF+s
    return cfg.get(s,v) if v is None else (cfg.__setitem__(s,v),cfg.commit())
df = lambda i,j: var(i,j) if var(i) is None else None
def kang(f, bad=[]):
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
def brk(t,l=15):
    o = ''
    for i,c in enumerate(t):
        o += c
        if i and i%l == 0: o += '\n'
    return o
def fade(w,i=0,j=0.025,a=0.1):
    if i > 1.0 or i < 0: return
    if not w.exists(): return
    iw(w,opacity=i)
    teck(j,Call(fade,w,i+a,j,a))

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    has_settings_ui = lambda s: True
    show_settings_ui = lambda s,b: s.make()
    def __init__(s):
        s.last = ''
        # dumb workaround
        B = __import__('_babase')
        a = 'dev_console_add_python_terminal'
        o = getattr(B,a)
        def f(*a,**k):
            try: r = o(*a,**k)
            except RuntimeError: pass
            else: return r
        setattr(B,a,f)
        # catch input
        from babase._ui import DevConsoleStringEditAdapter as A
        p = A._do_apply
        A._do_apply = lambda z,t: (p(z,t),s.pipe(t))
        print(f'Polish v2.7 ({Polish.INC}) - Start by writing Polish() here or via settings ui')
    def pipe(s,t):
        if t.lower() == 'polish()': dset('') or Polish()
