# Copyright 2025 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Car v1.1 - vroom vroom

Experimental. Feedback is appreciated.
Creates a stupid car to ride in.
"""

from bascenev1lib.gameutils import SharedObjects
from babase import Plugin
from bascenev1 import (
    OutOfBoundsMessage,
    InputType as IT,
    Timer as tock,
    StandMessage,
    getcollision,
    gettexture,
    InputType,
    Material,
    newnode,
    getmesh,
    Call
)

class Car:
    Touch = type('Touch',(object,),{})
    MEM = []
    def __init__(s):
        s.driver = None
        s.kids = []
        s.nah = []
        so = SharedObjects.get()
        p = (-4,0.3,0)
        s.nx = s.ny = 0
        # design
        z = Material()
        z.add_actions(
            conditions=(
                ('they_are_older_than',-1),
                'and',
                ('they_have_material',so.player_material)
            ),
            actions=(
                ('message','our_node','at_connect',s.__class__.Touch)
            )
        )
        # make
        s.node = newnode(
            'prop',
            name='car',
            delegate=s,
            attrs={
                'body':'landMine',
                'mesh':getmesh('landMine'),
                'materials':[z,so.footing_material],
                'color_texture':gettexture('black'),
                'reflection':'sharper',
                'reflection_scale':[5],
                'is_area_of_interest':True,
                'body_scale':2,
                'mesh_scale':2,
                'position':p,
                'gravity_scale':1.5
            }
        )
        s.node.getdelegate(object).handlemessage = s.hm
        s.wheels = [
            newnode(
                'prop',
                name='wheel',
                owner=s.node,
                attrs={
                    'body':'sphere',
                    'mesh':getmesh('impactBomb'),
                    'color_texture':gettexture('impactBombColor'),
                    'shadow_size':0.5,
                    'reflection':'sharper',
                    'reflection_scale':[5]
                }
            )
            for _ in range(4)
        ]
        # connect
        m = newnode(
            'math',
            owner=s.node,
            attrs={
                'operation':'add',
                'input1':(1,0,0.5)
            }
        )
        s.node.connectattr('position',m,'input2')
        x,y,z = 1,0,0.5
        for i,w in enumerate(s.wheels):
            off = [
                (-x,y,z),
                (x,y,z),
                (-x,y,-z),
                (x,y,-z)
            ][i]
            m = newnode(
                'math',
                owner=s.node,
                attrs={
                    'operation':'add',
                    'input1':off
                }
            )
            s.node.connectattr('position',m,'input2')
            m.connectattr('output',w,'position')
        # finally
        s.movet = tock(0.01,s.move,repeat=True)
    def hm(s,m):
        if isinstance(m,OutOfBoundsMessage):
            s.node.delete()
            s.movet = None
            for _ in s.kids: s.bye(_)
        c = s.__class__
        if m is c.Touch:
            n = getcollision().opposingnode
            if n not in c.MEM:
                s.kang(n)
                c.MEM.append(n)
    def kang(s,n):
        p = n.source_player
        if p in s.nah:
            s.nah.remove(p)
            s.__class__.MEM.remove(n)
            return
        a = p.actor
        a.node.move_up_down = 0
        a.node.move_left_right = 0
        p.resetinput()
        p.assigninput(IT.BOMB_PRESS,Call(s.bye,p))
        s.kids.append(p)
        if not s.driver: s.grant(p)
    def grant(s,p):
        s.driver = p
        for i,_ in enumerate(['UP_DOWN','LEFT_RIGHT']):
            p.assigninput(getattr(IT,_),Call(s.man,p,i))
    def man(s,p,i,v):
        if i: s.nx = v
        else: s.ny = v
    def move(s):
        x,y,z = s.node.position
        sc = 0.1
        s.node.position = p = (x+s.nx*sc,y,z-s.ny*sc)
        for _ in s.kids:
            _.actor.handlemessage(StandMessage((x,y-0.6,z),90))
    def bye(s,p):
        a = p.actor
        s.__class__.MEM.remove(a.node)
        s.kids.remove(p)
        a.connect_controls_to_player()
        s.nah.append(p)
        if s.driver == p:
            s.nx = s.ny = 0
            if s.kids: s.grant(s.kids[0])
            else: s.driver = None

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin): pass
