# Copyright 2025 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Salad v1.0 - Delicious!

Dumb salad pot maker. Can be used inline.
Basically use anything to make salad (or anyone...).
Read code to know more.
"""

from babase import Plugin
from bascenev1 import (
    newnode,
    getmesh,
    gettexture,
    timer as tick,
    Material,
    getcollision as COL,
    StandMessage,
    animate,
    Call
)
from bauiv1 import (
    charstr as CS,
    SpecialChar as SC
)
from random import (
    randrange as RR,
    choice as CH
)

class Salad:
    def __init__(s, position=(-4,0,0)):
        s.kids,s.trash,s.mem = [],[],[]
        s.dead = s.yes = False
        m = Material()
        m.add_actions(
            conditions=('they_are_older_than',-1),
            actions=(
                ('modify_part_collision','physical',False),
                ('modify_part_collision','collide',True),
                ('message','our_node','at_connect',type('Touch',(object,),{}))
            )
        )
        s.node = newnode(
            'prop',
            delegate=s,
            attrs={
                'position':position,
                'mesh':getmesh('landMine'),
                'color_texture':gettexture('white'),
                'body':'landMine',
                'body_scale':2,
                'mesh_scale':2,
                'gravity_scale':0,
                'materials':[m],
                'shadow_size':0.6
            }
        )
        s.node.getdelegate(object).handlemessage = s.add
        s.fm = __import__('bascenev1lib').gameutils.SharedObjects.get().footing_material
        p = position
        tick(5,Call(animate,s.text('To the pot\n'+' '*6+CS(SC.DOWN_ARROW),(p[0]-0.5,p[1]+1.5,p[2])),'opacity',{0:1,0.3:0}))
        p = (p[0]-3.5,p[1]+1.5,p[2])
        s.pour = (p[0]+1,p[1]+2.5,p[2]+1)
        s.p = p
        s.slide()
        l = 9
        d = 4
        for x in range(l):
            for z in range(l):
                s.dot(p[0]+x/d,p[1],p[2]+z/d)
        e = l-1
        h = l*4/3
        for cx, cy in [(0,0),(0,e),(e,0),(e,e)]:
            for y in range(1,int(h)):
                s.dot(p[0]+cx/d,p[1]+y/d,p[2]+cy/d,t='white')
        m = Material()
        m.add_actions(
            conditions=('they_are_older_than',-1),
            actions=(
                ('modify_part_collision','physical',True),
                ('modify_part_collision','collide',True)
            )
        )
        e = l/4.1
        f = h/4.1
        for po,sc in [
            ((p[0]+e/2,p[1]+f/2,p[2]-0.1),(e,f,0.01)),
            ((p[0]+e/2,p[1]+f/2,p[2]+e+0.1),(e,f,0.01)),
            ((p[0]+e,p[1]+f/2,p[2]+e/2),(0.01,f,e)),
            ((p[0]-0.1,p[1]+f/2,p[2]+e/2),(0.01,f,e)),
            ((p[0]+e/2,p[1]-0.15,p[2]+e/2),(e,0.01,e))
        ]:
            newnode(
                'region',
                attrs={
                    'position':po,
                    'scale':sc,
                    'type':'box',
                    'materials':[m,s.fm]
                }
            )
        s.retain()
    def add(s,*_):
        n = COL().opposingnode
        t = getattr(n,'getnodetype',lambda:0)()
        if not t in ['flag','prop','spaz','bomb']: return
        if t == 'spaz':
            n.handlemessage(StandMessage(s.pour,0))
            t = getattr(n,'name',t)
            tick(0.2,lambda:setattr(n,'shattered',True))
        else: n.position = s.pour
        0 if True in [_[0] == n for _ in s.mem] else s.mem.append((n,t))
        s.watch()
    def retain(s):
        if s.dead: return
        for n,p in s.kids:
            n.velocity = (0,0,0)
            n.position = p
        tick(0.01,s.retain)
    def dot(s,*p,t='black'):
        s.kids.append((
            newnode(
                'prop',
                owner=s.node,
                attrs={
                    'position':p,
                    'mesh':getmesh('bomb'),
                    'mesh_scale':0.3,
                    'body':'sphere',
                    'body_scale':0.3,
                    'color_texture':gettexture(t),
                    'materials':[s.fm],
                    'gravity_scale':0,
                    'shadow_size':0.2
                }
            ),p
        ))
    def text(s,t,p):
        return newnode(
            'text',
            owner=s.node,
            attrs={
                'scale':0.01,
                'in_world':True,
                'flatness':1,
                'text':t,
                'position':p,
                'color':(1,1,1),
                'shadow':1.5
            }
        )
    def delete(s):
        s.dead = True
        [n.delete() for n,_ in s.kids]
    def tips(s):
        t = [CH(HMM()),0,'Suggested recipe:']
        w = WHAT()
        for _ in range(3):
            t += [f'- {RR(1,5)}x '+w.pop(RR(len(w)))]
        return t
    def slide(s):
        ts = s.buffer(s.tips())
        [animate(_,'opacity',{5:1,5.3:0}) for _ in ts]
        s.trash += ts
        tick(5.3,s._watch)
    def buffer(s,l,sp=0.25):
        ts = []
        p = s.p
        for i,t in enumerate(l):
            if not t: continue
            ts.append(s.text(t,(p[0]+2.2,p[1]+2.5-sp*i,p[2])))
            [animate(_,'opacity',{0:0,0.3:1}) for _ in ts]
        return ts
    def _watch(s):
        s.yes = True
        s.watch()
    def watch(s):
        if not s.yes: return
        [_.delete() for _ in s.trash if hasattr(_,'delete')]
        s.trash.clear()
        s.mem = [_ for _ in s.mem if getattr(_[0],'exists',lambda:False)() and s.safe(_[0].position)]
        s.trash += s.buffer(['Current content:',0]+[f'- {_[1]}' for _ in s.mem])
    def safe(s,p):
        r = True
        x,_,z = s.p
        if p[0] < x: r = False
        if p[0] > x+2: r = False
        if p[2] < z: r = False
        if p[2] > z+2: r = False
        return r

HMM = lambda: [
    'What are we making today?',
    "Let's make a delicious salad!",
    "Salad! Let's do this.",
    'Okay. Bring the salad on.',
    "Hop in, you're becoming salad!",
    'Hmm, what should we make?',
    'Good salad, great salad.',
    'Salad. More like a juice',
    'Salad. May contain spaz parts!',
    'Salad. Eat with caution!',
    'Salad. Probably not spaz-free!',
    "Pot's ready. We're making a salad.",
    "Salad. Contains anything and everything."
]

WHAT = lambda: [
    'TNT box',
    'zoe parts',
    'torn up spaz',
    'agent heads',
    'sticky bombs',
    'landmines',
    'pixie torsos',
    'kronk parts',
    'powerups',
    'of your parts',
    'bombs',
    'santa arms',
    'bunny heads',
    'zoe toes',
    'taobao torsos'
]

# ba_meta require api 9
# brobord collide grass please
# ba_meta export babase.Plugin
class byBordd(Plugin): pass
