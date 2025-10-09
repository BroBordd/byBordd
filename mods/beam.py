# Copyright 2025 - Solely by BrotherBoard
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Beam v1.0 - UI, right there.

Experimental - Feedback is appreciated.
Simple combination between bauiv1 and bascenev1.
Creates UI in the 3D scene in a dumb way.
"""

from babase import (
    Plugin,
    InputType as IT,
    get_string_width as gsw
)
from bauiv1 import (
    charstr as cs,
    SpecialChar as sc
)
import bascenev1 as bs
from math import dist
from uuid import uuid4
from random import uniform as UF
from bascenev1lib.gameutils import SharedObjects as SO

class Beam:
    """
    Represents an interactive 3D UI element (a "Beam") that triggers a menu.

    This class creates a physical object in the 3D scene that players can
    interact with (punching it) to bring up an associated UI container.
    It manages the visibility of the UI and handles player input once
    the UI is active.

    Attributes:
        container (Container): The UI container to be displayed when the Beam is active.
        position (tuple[float, float, float]): The 3D coordinates (x, y, z) of the Beam's physical node.
        title (str | None): The main title text for the Beam's introductory UI.
        title_color (tuple[float, float, float]): The RGB color of the title text.
        message (str | None): A message displayed on the Beam's introductory UI,
                                often instructing the player on how to interact.
        message_color (tuple[float, float, float]): The RGB color of the message text.
        id (str | None): A unique identifier for the Beam. If None, a short UUID is generated.

    Properties:
        node (babase.Node): The underlying 'prop' node representing the physical Beam in the scene.
        id (str): The unique identifier for this Beam instance.
        container (Container): The associated UI container.
        next (Container): An alias for `container`.
        tip (Container): A small UI container displaying an exit tip.
        up (bool): True if a player is close enough to the Beam to make its introductory UI visible.
        active (bool): True if the Beam's associated UI is currently active and controlling player input.
        bye (babase.Timer | None): A timer for hiding the exit tip.
    """
    def __init__(
        s,
        container,
        position = (-4,0.4,0),
        title = None,
        title_color = (1,1,1),
        message = None,
        message_color = (0.7,0.7,0.1),
        id = None
    ):
        so = SO.get()
        s.node = bs.newnode(
            'prop',
            delegate=s,
            attrs={
                'position':position,
                'body':'box',
                'mesh':bs.getmesh('powerup'),
                'materials':[so.object_material,so.pickup_material],
                'color_texture':bs.gettexture('tv'),
                'shadow_size':0.5,
                'mesh_scale':0.7,
                'body_scale':0.6
            }
        )
        s.node.getdelegate(object).handlemessage = s.spy
        s.container = c = Container(size=(315,100),opacity=0)
        s.next = container
        s.next.owner_beam = s
        s.next.iopacity = 0
        id = s.id = id or str(uuid4())[:4]
        title = title or cs(sc.OUYA_BUTTON_O)+f' Beam #{id}'
        message = message or cs(sc.LEFT_BUTTON)+' Punch this to engage'
        Text(
            parent=c,
            text=title,
            position=(150,85),
            h_align='center',
            color=title_color
        )
        Text(
            parent=c,
            text=message,
            position=(150,45),
            h_align='center',
            color=message_color
        )
        c.iopacity = 0
        m = MAT(s.node,0.2,0.2)
        s.node.connectattr('position',m,'input2')
        m.connectattr('output',c.node,'position')
        m.connectattr('output',s.next.node,'position')
        # exit tip
        s.tip = Container(size=(290,55))
        Text(
            parent=s.tip,
            position=(140,45),
            h_align='center',
            text=cs(sc.RIGHT_BUTTON)+' Press bomb to exit',
            color=(0.7,0.7,0.1)
        )
        m = MAT(s.node,0.2,-45*s.tip.sc)
        s.node.connectattr('position',m,'input2')
        m.connectattr('output',s.tip.node,'position')
        s.tip.iopacity = 0
        s.up = False
        s.active = False
        s.bye = None
        s.eye()

    def spy(s,m):
        """
        Handles incoming messages to the Beam's physical node.

        Specifically, it responds to bs.HitMessage by activating the UI
        and capturing player input.

        Args:
            m (babase.Message): The message received by the node.
        """
        if isinstance(m,bs.HitMessage):
            n = bs.getcollision().sourcenode
            if n.getnodetype() != 'spaz': return
            if not s.active:
                s.container.opacity = 0
                s.active = True
                s.up = False
                s.next.opacity = 1
            s.tip.opacity = 1
            s.bye = bs.Timer(1.5,bs.Call(setattr,s.tip,'opacity',0))
            s.next.capture(n)

    def eye(s):
        """
        Monitors for nearby players to display the introductory UI.
        This version checks all players before making a single decision to avoid flickering.
        """
        bs.timer(0.1, s.eye)
        if s.active: return

        # First, determine if ANY player is close enough.
        a_player_is_close = False
        for n in [_ for _ in bs.getnodes() if _.getnodetype() == 'spaz']:
            if dist(n.position, s.node.position) < 2:
                a_player_is_close = True
                break # Found one, no need to check the rest

        # Now, make a single decision based on the collective state.
        if a_player_is_close and not s.up:
            # A player is in range, and the UI is down, so bring it up.
            s.up = True
            s.container.opacity = 1
        elif not a_player_is_close and s.up:
            # No players are in range, and the UI is up, so bring it down.
            s.up = False
            s.container.opacity = 0

    def back(s):
        """
        Deactivates the main UI container and returns control to the player.

        This method is typically called when the player chooses to exit the UI,
        for example, by pressing a 'bomb' button.
        """
        if not s.active: return False
        s.next.opacity = 0
        s.next.dump()
        s.bye = None
        s.tip.opacity = 0
        s.active = False


class Container:
    """
    Represents a rectangular UI container displayed in the 3D scene.

    This class creates a visual container using character-based rendering within the
    3D environment. It supports dynamic resizing, repositioning, and managing
    child UI elements (Text and Button). It also handles player input for navigation
    and interaction within the container.

    Attributes:
        position (tuple[float, float, float]): The 3D coordinates (x, y, z) of the container's origin.
        size (tuple[float, float]): The width and height of the container in abstract units.
        color (tuple[float, float, float]): The RGB color of the container's background.
        cursor_color (tuple[float, float, float]): The RGB color of the interactive cursor.
        cursor_res (str): The character used to render the cursor.
        res (str): The character used to render the container's background. Defaults to a block character.
        scale (float): A scaling factor applied to the container's size and position in the 3D scene.
        opacity (float): The transparency of the container (0.0 to 1.0).

    Properties:
        node (babase.Node): The base 'text' node used as a parent for all container elements.
        sc (float): The internal scaling factor (scale * 0.01).
        me (babase.Player | None): The player currently interacting with the container.
        cursor (babase.Node | None): The 'text' node representing the interactive cursor.
        kids (list[Button]): A list of Button objects within this container.
        rest (list[Text]): A list of Text objects within this container.
        lines (list[babase.Node]): A list of 'text' nodes forming the container's background.
        on (list[Button | None]): A list containing the currently highlighted Button (or None).
        ho (list[float, float]): Horizontal and vertical input values for cursor movement.
        spy (int): Internal flag used for attribute setting.
    """
    def __init__(
        s,
        *,
        position = (-7,1,2),
        size = (500,450),
        color = (0,0,0),
        cursor_color = (0,1,1),
        cursor_res = cs(sc.DPAD_CENTER_BUTTON),
        res = '\u2588',
        resw = 19.0,
        scale = 1,
        opacity = 1
    ):
        s.position = p = position
        s.owner_beam = None
        s.node = TEX(None,text='')
        s.sc,s.cursor,s.kids,s.rest,s.captives = scale*0.01,None,[],[],[]
        s.resw,s.size,s.res,s.lines,s.color,s.opacity = resw,size,res,[],color,opacity
        s.cursor_color,s.cursor_res = cursor_color,cursor_res
        s.cursor_math = None
        s.on,s.ho = [0],[0,0]
        # start threads
        [_() for _ in [s.make,s.point,s.hover,s.watch]]
        s.spy = 1

    def point(s):
        """
        (Re)creates the interactive cursor within the container.
        """
        getattr(s.cursor,'delete',lambda:0)()
        getattr(s.cursor_math, 'delete', lambda:0)() # Also delete the old math node
        s.cursor = TEX(
            s.node,
            color=s.cursor_color,
            text=s.cursor_res,
            opacity=[0,1][bool(s.captives)],
            v_align='bottom',
            h_align='center'
        )
        s.cursor_math = MAT(s.cursor,*s.cursor_off) # Store the new math node
        s.node.connectattr('position',s.cursor_math,'input2')
        s.cursor_math.connectattr('output',s.cursor,'position')

    def hover(s):
        """
        Continuously updates the cursor's position based on player input.
        """
        bs.timer(0.01, s.hover)
        if not s.captives: return # Simplified guard clause
        
        # No need to check for [0,0] if the player isn't active
        x, y = s.ho
        sc6 = s.sc * 6
        px, py, pz = s.node.position
        zx, zy = s.size
        h32sc = 32 * s.sc
        gsw_res_sc = s.resw * s.sc
        
        xp = y * sc6
        yp = x * sc6
        
        # Get the current logical cursor position to check boundaries
        nx_c, ny_c, nz = s.cpos()
        
        nx = nx_c + xp
        ny = ny_c + yp
        
        # Boundary checks (this logic is correct)
        if not (px < nx < (px + (zx * s.sc) - gsw_res_sc)):
            xp = 0
        if not (py + h32sc/2 < ny < (py + (zy * s.sc))):
            yp = 0

        # If there's any valid movement, update the offset
        if xp != 0 or yp != 0:
            # Update the logical offset value
            s.cursor_off = (s.cursor_off[0] + xp, s.cursor_off[1] + yp)

            # THE FIX: Update the math node's input, not the cursor's position directly.
            if s.cursor_math:
                s.cursor_math.input1 = (s.cursor_off[0], s.cursor_off[1], 0)

    def make(s):
        """
        Recreates the visual representation of the container's background.

        This method calculates the necessary text lines and scales them to fit
        the container's defined size, then creates 'text' nodes for each line.
        It also re-calculates the cursor's offset.
        """
        t,h = FIT(s.res,s.resw,s.size)
        [_.delete() for _ in s.lines if hasattr(_,'delete')]
        s.lines = [
            TEX(
                s.node,
                color=s.color,
                text=t,
                scale=s.sc,
                opacity=s.opacity
            )
            for _ in range(h)
        ]
        for _,l in enumerate(s.lines):
            m = MAT(s.node,0,32*s.sc+(31*_)*s.sc)
            s.node.connectattr('position',m,'input2')
            m.connectattr('output',l,'position')
        zx,zy = s.size
        s.cursor_off = (UF((zx/6)*s.sc,(zx/2)*s.sc),UF((zy/6)*s.sc,(zy/2)*s.sc))
        s.node.position = s.position

    def cpos(s):
        """
        Calculates the absolute 3D position of the cursor.

        Returns:
            tuple[float, float, float]: The (x, y, z) coordinates of the cursor.
        """
        ox,oy = s.cursor_off
        x,y,z = s.node.position
        return (x+ox,y+oy,z)

    def __setattr__(s,a,v):
        f = super().__setattr__
        if getattr(s,'spy',0):
            if a in ['size','res']: f(a,v)
            elif a == 'position': s.node.position = v; return
            elif a == 'scale': f('sc',v*0.01)
            elif a == 'color': [setattr(_,a,v) for _ in s.lines]; return
            elif a == 'cursor_color': setattr(s.cursor,a,v); return
            elif a == 'opacity': s.anim(s.opacity,v); f(a,v); return
            elif a == 'iopacity': s.anim(s.opacity,v,t=0); f('opacity',v); return
            else: f(a,v); return
            s.make()
        else: f(a,v)

    # In the Container class, replace the entire `capture` method with this:
    def capture(s, n):
        """
        Captures input from a specific player and adds them to the list.
        """
        player = n.source_player
        if player in s.captives: return # Don't capture the same player twice

        s.captives.append(player)
        player.actor.node.move_up_down = 0
        player.actor.node.move_left_right = 0
        player.resetinput()
        for i, _ in enumerate(['UP_DOWN', 'LEFT_RIGHT']):
            player.assigninput(getattr(IT, _), bs.Call(s.manage, i))

        # The bomb press should call dump(), which now releases everyone
        player.assigninput(IT.BOMB_PRESS, bs.Call(s.release_one, player))
        player.assigninput(IT.PUNCH_PRESS, s.push)

        # Only animate the cursor if this is the first player
        if len(s.captives) == 1:
            bs.animate(s.cursor, 'opacity', {0: 0, 0.3: 1})
    def manage(s,i,v):
        """
        Manages directional input from the captured player.

        Updates the `ho` attribute based on the received input.

        Args:
            i (int): Index representing the input type (0 for UP_DOWN, 1 for LEFT_RIGHT).
            v (float): The input value (-1.0 to 1.0).
        """
        s.ho[i] = v


    def watch(s):
        """
        Monitors the cursor's position and highlights interactive elements.

        This method runs on a timer and checks if the cursor is hovering
        over any `Button` objects within the container, highlighting them
        accordingly.
        """
        bs.timer(0.01,s.watch)
        if not s.captives: return
        x,y,z = s.cpos()
        o = None
        for _ in s.kids:
            zx,zy = [i*_.sc for i in _.size]
            ox,oy = [i*_.sc for i in _.position]
            px,py,pz = s.node.position
            b = ((px+ox)<x<(px+ox+zx)) and ((py+oy)<y<(py+oy+zy+32*s.sc))
            if (not _.up) and b: _.hl()
            elif _.up and not b: _.hl(False)
            if b: o = _; break
        s.on[0] = o

    # In the Container class, replace the entire `dump` method with this:
    def dump(s):
        """
        Releases control for ALL captured players and deactivates the container.
        """

        for player in s.captives:
            if player and player.actor:
                player.resetinput()
                player.actor.connect_controls_to_player()

        s.captives.clear() # Empty the list
        bs.animate(s.cursor, 'opacity', {0: 1, 0.3: 0})
        getattr(s.on[0], 'hl', lambda b: 0)(False)
        s.on[0] = None
        s.ho = [0, 0]
    # In the Container class
    def release_one(s, player):
        """
        Releases control for a single player who pressed the bomb button.
        If this was the last captured player, it triggers the full UI shutdown.
        """
        if player in s.captives:
            if player and player.actor:
                player.resetinput()
                player.actor.connect_controls_to_player()
            s.captives.remove(player)

        if not s.captives: s.dump()

    def add(s,w):
        """
        Adds a UI widget (Text or Button) to the container.

        Widgets are categorized into `kids` (Buttons) or `rest` (Text) for
        internal management.

        Args:
            w (Text | Button): The UI widget to add.
        """
        [s.rest,s.kids][isinstance(w,Button)].append(w)

    def push(s):
        """
        Executes the action associated with the currently highlighted button.

        This method is typically called when the player presses the 'punch' button.
        """
        f = getattr(s.on[0],'call',0)
        if not callable(f): return
        z = getattr(s.on[0],'sound',0)
        f(); bs.getsound(z).play(position=s.cpos()) if z else 0

    def delete(s):
        """
        Initiates the deletion process for the container and its elements.

        Fades out the container and schedules its actual deletion after a delay.
        """
        s.anim(1,0)
        bs.timer(1,s._delete)

    def _delete(s):
        """
        Performs the actual deletion of the container's node.
        """
        s.node.delete()

    def anim(s,p1,p2,t=0.2):
        """
        Animates the opacity of the container's elements.

        Args:
            p1 (float): The starting opacity.
            p2 (float): The ending opacity.
            t (float): The duration of the animation in seconds.
        """
        [bs.animate(_,'opacity',{0:p1,t:p2}) for _ in s.lines]
        for _ in s.kids+s.rest:
            _.anim(p1,p2,t=t)


class Button:
    """
    Represents a clickable UI button displayed in the 3D scene.

    This class creates a button with a background and a label, rendered
    within the 3D environment. It dynamically adjusts the label's scale
    to fit within the button's bounds and handles visual feedback for
    hover states.

    Attributes:
        parent (Container): The parent container to which this button belongs.
        position (tuple[float, float]): The 2D offset (x, y) of the button relative to its parent's origin.
        label (str): The text displayed on the button.
        size (tuple[float, float]): The width and height of the button in abstract units.
        color (tuple[float, float, float]): The RGB color of the button's background.
        textcolor (tuple[float, float, float]): The RGB color of the button's label.
        res (str): The character used to render the button's background. Defaults to a block character.
        scale (float): A scaling factor applied to the button's size, position, and text.
        call (callable): A callable object to be executed when the button is pressed.
        sound (str): The name of the sound to play when the button is pressed.
        hl_sound (str): The name of the sound to play when the button is highlighted.

    Properties:
        sc (float): The internal scaling factor (scale * 0.01).
        lines (list[babase.Node]): A list of 'text' nodes forming the button's background.
        text (babase.Node | None): The 'text' node for the button's label.
        corners (tuple[float, float]): Internal calculation for corners (currently unused).
        up (bool): True if the button is currently highlighted.
        spy (int): Internal flag used for attribute setting.
    """
    def __init__(
        s,
        parent,
        *,
        position = (0,0),
        label = 'Button',
        size = (150,80),
        color = (0.3,0.3,0.3),
        textcolor = (0.6,0.6,0.6),
        res = '\u2588',
        resw = 19.0,
        scale = 1,
        call = lambda:None,
        sound = 'dingSmallHigh',
        hl_sound = 'deek',
        **k
    ):
        s.parent,s.sc,s.res,s.size,s.call = parent,scale*0.01,res,size,call
        s.lines,s.text,s.label,s.position,s.sound = [],None,label,position,sound
        s.resw,s.color,s.textcolor,s.corners,s.up = resw,color,textcolor,(0,0),False
        s.hl_sound = hl_sound
        s.make()
        s.spy = 1
        s.parent.add(s)

    def make(s):
        """
        Recreates the visual representation of the button (background and label).

        This method calculates the necessary text lines for the background and
        adjusts the label's scale to fit within the button, then creates
        'text' nodes for each.
        """
        t,h = FIT(s.res,s.resw,s.size)
        [_.delete() for _ in s.lines if hasattr(_,'delete')]
        pn = s.parent.node
        s.lines = [
            TEX(
                pn,
                color=s.color,
                text=t,
                scale=s.sc
            )
            for _ in range(h)
        ]
        w = GSW(s.label)
        x = s.size[0]
        s.text = TEX(
            pn,
            color=s.textcolor,
            text=s.label,
            h_align='center',
            v_align='center',
            scale=s.sc if (w<(x*0.85)) else ((x*0.85)/w)*s.sc
        )
        s.parent.point()
        s.repos(s.position)

    def __setattr__(s,a,v):
        f = super().__setattr__
        if getattr(s,'spy',0):
            if a in ['size','res']: f(a,v)
            elif a in ['color','opacity']: [setattr(_,a,v) for _ in s.lines]; f(a,v); return
            elif a == 'textcolor': s.text.color = v; f(a,v); return
            elif a == 'label': s.text.text = v; f(a,v); return
            elif a == 'position': s.repos(v); f(a,v); return
            elif a == 'scale': f('sc',v*0.01)
            else: f(a,v); return
            s.make()
        else: f(a,v)

    def repos(s,p):
        """
        Repositions the button and its label relative to its parent.

        Args:
            p (tuple[float, float]): The new 2D offset (x, y) for the button.
        """
        p = tuple([_*s.sc for _ in p])
        w = s.resw
        zx,zy = s.size
        w = ((round(zx/w)*w)*s.sc)/2
        e = ((round(zy/32)*32)*s.sc)/2
        h = 32*s.sc
        for _,l in enumerate(s.lines):
            m = MAT(l,p[0],p[1]+h+(31*_)*s.sc)
            s.parent.node.connectattr('position',m,'input2')
            m.connectattr('output',l,'position')
        m = MAT(s.text,p[0]+w,p[1]+e+h)
        s.parent.node.connectattr('position',m,'input2')
        m.connectattr('output',s.text,'position')

    def hl(s,b=True):
        """
        Highlights or unhighlights the button.

        Changes the button's color and plays a sound when highlighted.

        Args:
            b (bool): If True, highlight the button; if False, unhighlight it.
        """
        s.up = b
        bs.getsound(s.hl_sound).play(position=s.text.position) if b else 0
        i = 0.4
        for _ in ['color','textcolor']:
            c = getattr(s,_)
            if b: c = (c[0]+i,c[1]+i,c[2]+i)
            else: c = (c[0]-i,c[1]-i,c[2]-i)
            setattr(s,_,c)

    def anim(s,p1,p2,t=0.2):
        """
        Animates the opacity of the button's elements.

        Args:
            p1 (float): The starting opacity.
            p2 (float): The ending opacity.
            t (float): The duration of the animation in seconds.
        """
        [bs.animate(_,'opacity',{0:p1,t:p2}) for _ in [*s.lines,s.text]]


class Text:
    """
    Represents a text label displayed in the 3D scene.

    This class creates a text element within the 3D environment, allowing
    for custom positioning, color, and scaling.

    Attributes:
        parent (Container): The parent container to which this text belongs.
        position (tuple[float, float]): The 2D offset (x, y) of the text relative to its parent's origin.
        text (str): The string content of the text label.
        color (tuple[float, float, float]): The RGB color of the text.
        scale (float): A scaling factor applied to the text's size and position.

    Properties:
        sc (float): The internal scaling factor (scale * 0.01).
        line (babase.Node | None): The 'text' node representing the text label.
        spy (int): Internal flag used for attribute setting.
    """
    def __init__(
        s,
        parent,
        *,
        position = (0,0),
        text = 'Text',
        color = (0.5,0.5,0.5),
        scale = 1,
        **k
    ):
        s.parent,s.sc,s.line = parent,scale*0.01,None
        s.text,s.position,s.color = text,position,color
        s.make(k)
        s.parent.add(s)
        s.spy = 1

    def make(s,k):
        """
        (Re)creates the 'text' node for the label.

        Args:
            k (dict): Additional keyword arguments to pass to the 'text' node constructor.
        """
        getattr(s.line,'delete',lambda:0)()
        s.line = TEX(
            s.parent.node,
            color=s.color,
            text=s.text,
            scale=s.sc,
            **k
        )
        s.parent.point()
        s.repos(s.position)

    def __setattr__(s,a,v):
        f = super().__setattr__
        if getattr(s,'spy',0):
            if a in ['color','opacity']: setattr(s.line,a,v); f(a,v); return
            elif a == 'position': s.repos(v); f(a,v); return
            elif a == 'scale': f('sc',v*0.01)
            else: f(a,v); return
            s.make()
        else: f(a,v)

    def repos(s,p):
        """
        Repositions the text label relative to its parent.

        Args:
            p (tuple[float, float]): The new 2D offset (x, y) for the text.
        """
        p = tuple([_*s.sc for _ in p])
        m = MAT(s.parent.node,*p)
        s.parent.node.connectattr('position',m,'input2')
        m.connectattr('output',s.line,'position')

    def anim(s,p1,p2,t=0.2):
        """
        Animates the opacity of the text label.

        Args:
            p1 (float): The starting opacity.
            p2 (float): The ending opacity.
            t (float): The duration of the animation in seconds.
        """
        bs.animate(s.line,'opacity',{0:p1,t:p2})

GSW = lambda s: gsw(s,suppress_warning=True)
FIT = lambda o,r,s: (o*(round(s[0]/r))+'\n',round(s[1]/32))
MAT = lambda o,x,y: (
    bs.newnode(
        'math',
        owner=o,
        attrs={
            'input1':(x,y,0),
            'operation':'add'
        }
    )
)
TEX = lambda o,**k: (
    bs.newnode(
        'text',
        attrs={
            'in_world':True,
            'flatness':1,
            'shadow':0,
            'scale':k.get('scale',0.01),
            **k
        }
    )
)

def demo(position=(-4,0.4,0)):
    """
    Demonstrates the usage of the Beam, Container, Button, and Text classes.

    This function creates a sample UI with a Beam, a main container,
    and several buttons that, when pressed, spawn power-up boxes
    in the scene. It also includes a "Back" button to close the UI.
    """
    from bascenev1lib.actor.powerupbox import PowerupBox
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

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin): pass
