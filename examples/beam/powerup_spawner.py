from bascenev1lib.actor.powerupbox import PowerupBox
from beam import (
    Beam,
    Text,
    Button,
    Container
)

def make_beam(position=(-4,0.4,0)):
    def power(t):
        x,y,z = beam.node.position
        PowerupBox(position=(x-1,y+1,z),poweruptype=t).autoretain()
    c = Container(
        size=(450,350)
    )
    Text(
        parent=c,
        text='Select a powerup',
        position=(155,200),
        h_align='center',
        scale=1.5
    )
    Button(
        parent=c,
        position=(20,20),
        size=(120,60),
        label='Health',
        call=lambda:power('health')
    )
    Button(
        parent=c,
        position=(165,20),
        size=(120,60),
        label='Gloves',
        call=lambda:power('punch')
    )
    Button(
        parent=c,
        position=(310,20),
        size=(120,60),
        label='Ice',
        call=lambda:power('ice_bombs')
    )
    Button(
        parent=c,
        position=(25,275),
        size=(50,35),
        label=cs(sc.BACK),
        color=(0.6,0.2,0.1),
        textcolor=(0.9,0.3,0.2),
        call=lambda:beam.back()
    )
    beam = Beam(
        container=c,
        position=position
    )
