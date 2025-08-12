# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> BroBordd

"""
Ender v1.0 - You're done.

A deadly bot that actively hunts any spaz nodes.
I wrote some cool pvp abilities into its core.
It spawns at a random player's location or at the center if no players are present.
Occasionally uses bubble_min to talk based on situations.

To spawn, just call Ender from dev console:
>>> __import__('ender').Ender()

Tested in football stadium. Read code to know more.
"""

from bascenev1lib.actor.spaz import Spaz
from babase import (
    get_string_height as gsh,
    get_string_width as gsw,
    Plugin
)
from bascenev1 import (
    get_foreground_host_activity as ga,
    OutOfBoundsMessage,
    getnodes as GN,
    timer as tick,
    Timer as tock,
    StandMessage,
    DieMessage,
    newnode,
    animate,
    time
)
from bauiv1 import (
    apptimer as teck
)
from math import dist, sqrt
from random import choice, random

class Bot:
    """
    The base class for all bot types.
    
    This class provides the fundamental functionality for a bot, including:
    - Initializing the Spaz actor and its associated node.
    - Creating a speech bubble for text display.
    - Methods for basic actions like waving, jumping, punching, picking up,
      and running.
    - Methods to control movement on the x and z axes.
    """
    def __init__(
        s,
        position: tuple = (0,0,0),
        color: tuple = (0,0,0),
        highlight: tuple = (0,0,0),
        character: str = 'Pixel'
    ):
        s.bot = Spaz(
            color=color,
            highlight=highlight,
            character=character
        )
        s.bot.handlemessage(StandMessage(position,0))
        s.node = s.bot.node
        s.node.name = s.__class__.__name__
        s.bub = Bubble(s.node)
    def wave(s):
        s.node.handlemessage('celebrate_r',1000)
    def on(s,i):
        for _ in [1,0]:
            getattr(s.bot,'on_'+['jump','bomb','pickup','punch'][i]+'_'+['release','press'][_])()
    def on_run(s, v: int):
        """New method to toggle running."""
        s.bot.on_run(v)
    def move(s,x,z):
        s.bot.on_move_left_right(x)
        s.bot.on_move_up_down(z)

class Bubble:
    """
    A class to create a speech bubble floating above a node.
    
    This bubble displays text and can be animated to appear and disappear.
    It consists of a background text block and a foreground text block
    to create a solid look.
    """
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
        try:
            [animate(_,'opacity',{0:p1,0.2:p2}) for _ in s.kids]
        except:
            pass

class Ender(Bot):
    """
    The main AI bot class.
    
    This bot actively seeks out and attacks other players. Its AI is built on a
    fast-acting protective thread for immediate reactions and a slower main
    thinking loop for strategic decisions. It has several distinct behaviors:
    - Spawning: The bot spawns at a random player's location or at the
      center of the map if there are no players.
    - Combat: It uses a punch-grab combo when a target is in close proximity.
    - Messaging: It "talks" using a speech bubble, with specific messages for
      pursuing a target, acquiring it, releasing it, or being left alone.
    - Urgent Message: The "Don't hold me!" message has top priority and
      can be triggered even if a normal message cooldown is active.
    """
    def __init__(
        s,
        position: tuple = None, # Position is now None by default
        color: tuple = (0, 0, 0), # Color is now black
        highlight: tuple = (0, 0, 0),
        character: str = 'Agent Johnson'
    ):
        # Determine spawn position based on the presence of other players
        player_nodes = [
            n for n in GN() if n.exists() and n.getnodetype() == 'spaz'
        ]
        
        if not player_nodes:
            # If no players, spawn at (0, 0.1, 0)
            initial_position = (0, 0.1, 0)
        else:
            # If players exist, spawn at a random one's position
            target_node = choice(player_nodes)
            initial_position = target_node.position
            
        # Call the parent class constructor with the determined position
        super().__init__(initial_position, color, highlight, character)

        s.last_skill_time = 0.0 # Cooldown for skill2
        s.speech_cooldown = 1.5 # Cooldown for messages
        s.last_speech_time = 0.0
        s.last_idle_chat_time = 0.0 # New cooldown for idle messages
        s.last_held_message_time = 0.0 # New cooldown for held messages
        s.held_message_cooldown = 1.0 # The "irreplaceable" message cooldown
        
        # Main think timer for general strategy (slower)
        s._think_timer = tock(0.15, s._think, repeat=True)

        # Protective thread for fast, defensive reactions
        s._protective_timer = tock(0.001, s._protective_think, repeat=True)

        s.is_shaking = False
        s._skill1_timer = None
        s._shake_timer = None
        
        # New state variable to prevent message spam
        s._has_announced_target = False

        # Funny messages
        s.pursuit_messages = [
            'Come here',
            'You can\'t get too far',
            'I\'m coming for ya',
            'Got my eyes on you',
            'Hello there, friendo'
        ]
        s.acquire_messages = [
            'Gotcha, now become cake',
            'Heheheh... got you',
            'My turn',
            'I\'ve got a present for you',
            'Don\'t worry, this will only hurt a lot'
        ]
        s.release_messages = [
            'He\'s DEAD',
            'WHO\'S NEXT',
            'Oops, I dropped it',
            'Target neutralized',
            'That was fun'
        ]
        s.idle_messages = [
            'Is anyone out there',
            'Boring...',
            'Time to find a new friend',
            'Where did everyone go',
            'Hmm, I sense a disturbance in the force'
        ]
    
    def _say(s, message: str):
        """Handles speaking with a cooldown to prevent spam."""
        now = time()
        if now - s.last_speech_time > s.speech_cooldown:
            s.bub.push(message)
            s.last_speech_time = now

    def _say_held(s):
        """Urgent message with its own cooldown, overriding normal speech."""
        now = time()
        if now - s.last_held_message_time > s.held_message_cooldown:
            s.bub.push(choice(["You've got some nerve to hold me","Get your hands off me","Let go of me","Did you just hold me"]))
            s.last_held_message_time = now

    def _protective_think(s):
        """
        The fast-acting protective thread. Executes a combo if the target
        is too close or if the bot is being grabbed.
        """
        if not s.node.exists():
            return

        target = s._get_target()
        now = time()
        
        # Check if we are being held. If so, try to break free and say the urgent message.
        if target and target.hold_node == s.node and now - s.last_skill_time > 0.4:
            s._say_held()
            s.skill2()
            s.last_skill_time = now
            return

        # Only activate if a target exists and we are running (chasing)
        if target and s.node.run and now - s.last_skill_time > 0.4:
            my_pos = s.node.position
            target_pos = target.position
            distance = dist(my_pos, target_pos)

            # If the target is within a close range, use skill2 (punch + grab)
            if distance < 1.6:
                s.skill2()
                s.last_skill_time = now
        
    def _start_combos(s):
        """Starts the skill1 and shake combos on a regular timer."""
        s._say(choice(s.acquire_messages))
        s._skill1_timer = tock(0.4, s.skill1, repeat=True)
        s._shake_timer = tock(0.05, s._shake, repeat=True)
    
    def _stop_combos(s):
        """Stops the combos and resets the state."""
        if hasattr(s, '_skill1_timer') and s._skill1_timer: s._skill1_timer = None
        if hasattr(s, '_shake_timer') and s._shake_timer: s._shake_timer = None

    def skill1(s):
        """Executes a combo of button presses with delays, starting with jump and bomb."""
        s.on(0) # jump
        s.on(1) # bomb
        tick(0.04,lambda:s.on(2)) # pickup
        tick(0.07,lambda:s.on(3)) # punch

    def skill2(s):
        """Performs a punch-grab combo."""
        s.on(3) # punch
        tick(0.05, lambda: s.on(2)) # pickup after a delay

    def _get_target(s) -> 'Node | None':
        """Finds the closest 'spaz' node that is not itself and is not dead."""
        if not s.node.exists(): return None
        my_pos = s.node.position

        player_nodes = [
            n for n in GN() if n.exists() and n.getnodetype() == 'spaz' and n.hurt < 1.0
        ]
        potential_targets = [p for p in player_nodes if p is not s.node]

        if not potential_targets:
            return None

        # Find the closest valid target
        return min(
            potential_targets,
            key=lambda n: dist(my_pos, n.position)
        )
    
    def _shake(s):
        """Handles the rapid left/right shaking movement."""
        s.is_shaking = not s.is_shaking
        if s.is_shaking:
            s.move(0.5, 0.1) 
        else:
            s.move(-0.5, 0.1)

    def _think(s):
        """
        The main AI logic loop for the Ender bot.
        """
        if not s.node.exists():
            s._think_timer = None
            s._protective_timer = None
            s._stop_combos()
            return

        target = s._get_target()
        now = time()
        
        # Check for holding an incorrect or dead target
        if s.node.hold_node and (s.node.hold_node != target or (target and target.hurt == 1.0)):
            s._stop_combos()
            
            # Say a funny line and throw the held item
            if s.node.hold_node and s.node.hold_node != target and target:
                s._say(f"Wait... this isn't {str(target.name)}")
            elif target and target.hurt == 1.0:
                s._say(choice(s.release_messages))
            
            s.on(2) # Release pickup
            s.move(0, 0) # Stop moving for a moment
            s._has_announced_target = False # Reset the flag
            return

        # Shaking logic for when the *correct* player is held and they are still alive
        if s.node.hold_node == target:
            s.on_run(0) # Stop moving forward
            
            # Start combos if not already running
            if not s._skill1_timer:
                s._start_combos()
            return
        
        # If we get here, we are not holding the target, so stop any combos
        s._stop_combos()

        if target and target.exists():
            # If we just found a new target, announce it.
            if not s._has_announced_target:
                # Instantly clear the 'lonely' message
                s.bub.push('')
                s._say(choice(s.pursuit_messages))
                s._has_announced_target = True

            my_pos = s.node.position
            target_pos = target.position
            distance = dist(my_pos, target_pos)

            # Calculate direction vector to the target (normalized)
            dx = target_pos[0] - my_pos[0]
            dz = target_pos[2] - my_pos[2]
            vector_length = (dx**2 + dz**2)**0.5

            if vector_length == 0:
                s.move(0, 0)
                return

            move_x = dx / vector_length
            move_z = dz / vector_length
            
            # Apply the run-reset logic to ensure responsive movement
            s.on_run(0)
            tick(0.02,lambda:s.on_run(1))
            
            # Occasionally say a pursuit message
            if random() < 0.05 and now - s.last_speech_time > s.speech_cooldown:
                s._say(choice(s.pursuit_messages))

            # Move towards the target. The protective thread handles the close-range grab.
            s.move(move_x, -move_z)

        else:
            # No targets? Stop and chill.
            if s._has_announced_target:
                s._say(choice(s.idle_messages))
                s._has_announced_target = False
                s.last_idle_chat_time = now # Reset timer
            # Cooldown is 7.5 seconds
            elif now - s.last_idle_chat_time > 7.5: 
                s._say(choice(s.idle_messages))
                s.last_idle_chat_time = now
            s.on_run(0) # Stop running
            s.move(0, 0)

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
# brobord collide grass
# ba_meta export babase.Plugin
class byBordd(Plugin): pass
