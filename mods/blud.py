# Copyright 2025 - Solely by BrotherBoard
# Feedback is appreciated - Telegram >> @GalaxyA14user

"""
Blud v1.0 - A simple Q-table learning bot

Blud aims to always move to the left
His memory is saved to mods folder. Advanced.
"""

from bascenev1lib.actor.spazbot import SpazBot
from babase import Plugin
from bascenev1 import (
    DieMessage,
    StandMessage,
    timer,
    newnode,
    Material,
    gettexture as gbt
)
import random
import math
import json
import os
import time

Q_TABLE_FILENAME = '/sdcard/Android/data/net.froemling.bombsquad/files/mods/blud.json' # Using blud.json as requested

# This dictionary will store the learned Q-values.
# It is GLOBAL and SHARED by all bot instances.
q_table = {}

# Configuration for the learning process
learning_rate = 0.15 # Adjusted learning rate
discount_factor = 0.95
epsilon = 1.0
epsilon_decay = 0.998 # Slightly faster epsilon decay
epsilon_min = 0.05 # Keep a small amount of exploration

# Mapping action indices to analog move values (x, y)
action_map = {
    0: (0, 0), # Stop
    1: (0, 32767), # Up (Positive Z)
    2: (0, -32767), # Down (Negative Z)
    3: (-32767, 0), # Left (Negative X)
    4: (32767, 0), # Right (Positive X)
    5: (-32767, 32767), # Up-Left (Negative X, Positive Z)
    6: (32767, 32767), # Up-Right (Positive X, Positive Z)
    7: (-32767, -32767), # Down-Left (Negative X, Negative Z)
    8: (32767, -32767), # Down-Right (Positive X, Negative Z)
}
action_space_size = len(action_map)

def save_q_table():
    """Saves the current GLOBAL Q-table to the specified JSON file."""
    try:
        # Convert tuple keys (pos_x_state, pos_z_state, vel_x_state, vel_z_state) to strings
        serializable_q_table = {f"{k[0]},{k[1]},{k[2]},{k[3]}": v for k, v in q_table.items()}
        with open(Q_TABLE_FILENAME, 'w') as f:
            json.dump(serializable_q_table, f)
    except Exception as e:
        print(f"Error saving GLOBAL Q-table to {Q_TABLE_FILENAME}: {e}")

def load_q_table():
    """Loads the GLOBAL Q-table from the specified JSON file."""
    global q_table
    if os.path.exists(Q_TABLE_FILENAME):
        try:
            with open(Q_TABLE_FILENAME, 'r') as f:
                serializable_q_table = json.load(f)
                # Convert string keys back to tuples (pos_x_state, pos_z_state, vel_x_state, vel_z_state)
                q_table = {tuple(map(int, k.split(','))): v for k, v in serializable_q_table.items()}
        except Exception as e:
            print(f"Error loading GLOBAL Q-table from {Q_TABLE_FILENAME}: {e}")
            q_table = {} # Start with empty table if loading fails
    else:
        print(f"No Q-table file found at {Q_TABLE_FILENAME}. Starting fresh.")
        q_table = {} # Start with empty table if file doesn't exist

# Load the GLOBAL Q-table when the script is first loaded
load_q_table()

# Refined state discretization
def get_current_state_sim(bot_position, bot_velocity):
    x_pos = bot_position[0]
    z_pos = bot_position[2]
    vel_x, vel_y, vel_z = bot_velocity

    # X state based on position (more granular near center)
    if x_pos < -10:
        x_state = 0 # Far Left
    elif x_pos < -4:
        x_state = 1 # Mid Left
    elif x_pos < -1:
        x_state = 2 # Near Center Left
    elif x_pos < 1:
        x_state = 3 # Center
    elif x_pos < 4:
        x_state = 4 # Near Center Right
    elif x_pos < 10:
        x_state = 5 # Mid Right
    else:
        x_state = 6 # Far Right

    # Z state (still useful for path following along the zigzag)
    z_state = int(z_pos // 5) # Smaller bins for Z position

    # Discretize X and Z velocity components
    if vel_x < -3:
        vel_x_state = 0 # Fast Left (Decreasing X)
    elif vel_x < -0.5:
        vel_x_state = 1 # Slow Left (Decreasing X)
    elif vel_x < 0.5:
        vel_x_state = 2 # Near Zero X velocity
    elif vel_x < 3:
        vel_x_state = 3 # Slow Right (Increasing X)
    else:
        vel_x_state = 4 # Fast Right (Increasing X)

    if vel_z < -3:
        vel_z_state = 0 # Fast Backward (Decreasing Z)
    elif vel_z < -0.5:
        vel_z_state = 1 # Slow Backward (Decreasing Z)
    elif vel_z < 0.5:
        vel_z_state = 2 # Near Zero Z velocity
    elif vel_z < 3:
        vel_z_state = 3 # Slow Forward (Increasing Z)
    else:
        vel_z_state = 4 # Fast Forward (Increasing Z)

    # State is a 4-component tuple: (pos_x_state, pos_z_state, vel_x_state, vel_z_state)
    return (x_state, z_state, vel_x_state, vel_z_state)

# Corrected reward function prioritizing decreasing X-coordinate on the zigzag path
def get_reward_sim(fell_off_now, prev_state, current_state, action_taken):
    reward = 0
    if fell_off_now:
        reward = -10000 # Much larger penalty for falling off
    else:
        # Add a small time penalty to encourage faster progress (indirectly)
        reward = -0.1 # Small negative reward per time step

        current_x_state = current_state[0]
        prev_x_state = prev_state[0]
        current_vel_x_state = current_state[2] # Use X velocity state
        current_vel_z_state = current_state[3] # Use Z velocity state

        # --- Reward based on X position (Prioritize decreasing X) ---
        # Reward for being in Left states (lower X is better)
        if current_x_state == 0: # Far Left (Goal state proximity)
            reward += 500 # Very high reward for reaching the far left (end of the path)
        elif current_x_state == 1: # Mid Left
            reward += 200
        elif current_x_state == 2: # Near Center Left
            reward += 100
        elif current_x_state == 3: # Center (Still good, but less than left)
            reward += 50
        elif current_x_state == 4: # Near Center Right
            reward += 20
        elif current_x_state == 5: # Mid Right
            reward += 10
        else: # Far Right (6) (Starting area, less reward)
            reward += 1 # Small reward for just being alive here

        # --- Reward for actively decreasing X-coordinate (moving left) ---
        # Compare current X state to previous X state
        if current_x_state < prev_x_state:
            # Significantly increased reward for moving to a lower X state
            reward += (prev_x_state - current_x_state) * 300

        # Penalty for actively increasing X-coordinate (moving right)
        if current_x_state > prev_x_state:
            # Significantly increased penalty for moving to a higher X state
            reward -= (current_x_state - prev_x_state) * 300

        # Penalty for stopping, especially off-center
        if action_taken == 0:
             if current_x_state == 3: # Stopping in center
                  reward -= 5
             else: # Stopping off-center
                  reward -= 20 # Higher penalty for stopping when not centered

        # --- Z-axis related rewards (for path following, not directional progress) ---
        # No specific reward/penalty for Z direction (increasing/decreasing Z velocity)
        # The bot is implicitly rewarded for navigating the Z turns correctly by
        # successfully decreasing X and avoiding penalties.

        # --- Explicit Penalties for Moving Towards Edge (based on X velocity) ---
        # Penalty if in Left states (0, 1, 2) and trying to move further Left (Fast Left velocity)
        if current_x_state in (0, 1, 2) and current_vel_x_state == 0:
             reward -= 500 # Very heavy penalty

        # Penalty if in Right states (4, 5, 6) and trying to move further Right (Fast Right velocity)
        if current_x_state in (4, 5, 6) and current_vel_x_state == 4:
             reward -= 500 # Very heavy penalty


    return reward

class Blud(SpazBot):
    pos = (0,0,0)
    # ov = None # Commented out: Overlay attribute
    m = None
    @classmethod
    def spawn(c,p=None,col=None):
        if p: c.pos = p
        else: p = c.pos
        if c.m is None:
            c.m = Material()
            c.m.add_actions(
                conditions=(('they_have_material',c.m)),
                actions=(
                    ('modify_part_collision', 'collide', False),
                    ('modify_part_collision', 'physical', False),
                    ('modify_part_collision', 'friction', 0),
                    ('modify_part_collision', 'stiffness', 0),
                    ('modify_part_collision', 'damping', 0)
                )
            )
        # if c.ov is None or (hasattr(c.ov, 'nodes') and not c.ov.nodes()): # Commented out: Overlay creation
        #     c.ov = Overlay()
        r = c(col)
        n = r.node
        n.materials = [c.m]
        for i in ['materials', 'roller_materials', 'extras_material', 'punch_materials', 'pickup_materials']:
            j = getattr(n,i)
            setattr(n,i,j+(c.m,))
        n.color = n.name_color = col[0]
        n.highlight = col[1]
        n.name = c.__name__
        r.handlemessage(StandMessage(p,0)) if p else p
        r.on_run(1.0) # Changed from 1.3 to 1.0
        return r

    def __init__(s,col):
        SpazBot.__init__(s)
        s.held_count = 0
        s.col = col
        s.last_player_attacked_by = None
        s._last_state = None # Store state tuple from previous step for THIS bot instance
        s._last_action_index = None # Store action for THIS bot instance
        s._move_timer = None # Timer for THIS bot instance's movement
        # Commented out: Bubble timer and bubble instance attributes
        # s._bubble_timer = None
        # s._bubble = None

        s._move_timer = timer(0.05, call=s.move)

    def handlemessage(s,m):
        # Always call super().handlemessage(m) at the end
        if isinstance(m,StandMessage):
             # No bubble on spawn/stand
             pass # Keep this block if you might add other StandMessage logic later
        elif isinstance(m,DieMessage):
            # Removed print('ded') and epsilon decay print
            global epsilon, epsilon_decay, epsilon_min
            # q_table is global and shared
            global q_table

            # Cancel move timer for THIS bot instance
            if s._move_timer is not None:
                 s._move_timer.cancel()
                 s._move_timer = None

            # No bubble destruction needed as it's transient

            # Perform learning update using THIS bot instance's last state and action
            if s._last_state is not None and s._last_action_index is not None:
                 reward = get_reward_sim(True, s._last_state, s._last_state, s._last_action_index)

                 # Ensure state exists in GLOBAL Q-table before updating
                 if s._last_state not in q_table:
                     q_table[s._last_state] = [0.0] * action_space_size

                 current_q = q_table[s._last_state][s._last_action_index]
                 max_future_q = 0 # Terminal state has no future reward

                 # Q-learning update on the GLOBAL Q-table
                 new_q = current_q + learning_rate * (reward + discount_factor * max_future_q - current_q)
                 q_table[s._last_state][s._last_action_index] = new_q

                 # Epsilon decay is GLOBAL
                 epsilon = max(epsilon_min, epsilon * epsilon_decay)
                 # print(f"Bot died. Epsilon decayed to {epsilon:.2f}") # Removed print statement
                 s._last_state = None
                 s._last_action_index = None

                 # Save the GLOBAL Q-table when a bot dies
                 save_q_table()
                 # Respawn THIS bot instance
                 s.__class__.spawn(col=s.col) # Uncommented: Bot spawns itself after dying

        # Always call super().handlemessage(m) last
        super().handlemessage(m)

    # Commented out: _maybe_show_bubble method
    # def _maybe_show_bubble(s):
    #     """Shows a transient speech bubble occasionally based on bot's state."""
    #     if not s.is_alive() or s.node is None:
    #          return # Don't show bubble if bot is not alive or has no node

    #     # Only show a bubble occasionally (e.g., 1 in 20 chance per move call)
    #     if random.random() < 0.05: # Adjust this value (e.g., 0.02 to 0.1) for frequency
    #         current_state = get_current_state_sim(s.node.position, s.node.velocity)
    #         x_state = current_state[0]
    #         vel_z_state = current_state[3]

    #         # Define moods and corresponding phrases/colors
    #         moods = {
    #             'confident': {'phrases': ["Feeling good!", "On the right track!", "Smooth sailing!", "Watch this!", "Pro gamer move"], 'color': (0.2, 0.6, 0.2)}, # Green
    #             'nervous': {'phrases': ["Whoa, close one!", "Careful now...", "Almost!", "Left a bit!", "Right a bit!"], 'color': (0.6, 0.4, 0.0)}, # Orange
    #             'thinking': {'phrases': ["Hmm...", "What now?", "Let's try this...", "Calculating...", "Analyzing..."], 'color': (0.4, 0.2, 0.6)}, # Purple
    #             'stuck': {'phrases': ["Stuck!", "Help?", "Where do I go?", "Can't move!"], 'color': (0.3, 0.3, 0.3)}, # Grey
    #             'progress': {'phrases': ["Moving forward!", "Making progress!", "Getting there!"], 'color': (0.1, 0.4, 0.8)} # Blue
    #         }

    #         # Determine current mood based on state
    #         current_mood = 'thinking' # Default mood

    #         if x_state == 3: # Center
    #             if vel_z_state >= 3: # Moving forward
    #                 current_mood = 'confident'
    #             elif vel_z_state == 2: # Not moving forward/backward significantly
    #                  # Check if actually stuck based on low velocity
    #                  if abs(s.node.velocity[0]) < 0.1 and abs(s.node.velocity[2]) < 0.1 and s.node.position[1] < 0.5:
    #                       current_mood = 'stuck'
    #                  else:
    #                       current_mood = 'confident' # Still confident if in center but not moving forward (maybe turning)
    #             elif vel_z_state in (0,1): # Moving backward
    #                  current_mood = 'nervous'


    #         elif x_state in (2, 4): # Near Center Left/Right
    #              current_mood = 'progress' # Indicate trying to stay on path

    #         elif x_state in (1, 5): # Mid Left/Right
    #              current_mood = 'nervous' # Closer to edge

    #         elif x_state in (0, 6): # Far Left/Right
    #              current_mood = 'nervous' # Very close to edge

    #         # Select a random phrase and color for the determined mood
    #         phrases = moods[current_mood]['phrases']
    #         color = moods[current_mood]['color']
    #         text = random.choice(phrases)

    #         # Determine bubble display time based on text length
    #         # Simple heuristic: 0.15 seconds per character, minimum 1 second
    #         display_time = max(1.0, len(text) * 0.15)

    #         # Create and show the bubble (it will destroy itself)
    #         try:
    #             Bubble(text=text, color=color, node=s.node, time=display_time)
    #         except Exception as e:
    #             print(f"Error creating transient bubble: {e}")
    #     else:
    #         # If random chance fails, do nothing
    #         pass


    def move(s):
        # Epsilon is global and shared
        global epsilon, epsilon_decay, epsilon_min
        # q_table is global and shared
        global q_table

        if not s.is_alive():
             # Cancel move timer for THIS bot instance
             if s._move_timer is not None:
                  s._move_timer.cancel()
                  s._move_timer = None
             return

        # Get current state for THIS bot instance
        current_state = get_current_state_sim(s.node.position, s.node.velocity)

        # Perform learning update using THIS bot instance's last state and action
        if s._last_state is not None and s._last_action_index is not None:
            reward = get_reward_sim(False, s._last_state, current_state, s._last_action_index)

            # Ensure states exist in GLOBAL Q-table before updating
            if s._last_state not in q_table:
                q_table[s._last_state] = [0.0] * action_space_size
            if current_state not in q_table:
                q_table[current_state] = [0.0] * action_space_size

            current_q = q_table[s._last_state][s._last_action_index]
            max_future_q = max(q_table[current_state])

            # Q-learning update on the GLOBAL Q-table
            new_q = current_q + learning_rate * (reward + discount_factor * max_future_q - current_q)
            q_table[s._last_state][s._last_action_index] = new_q


        if s.is_alive():
            # Ensure current state exists in GLOBAL Q-table before action selection
            if current_state not in q_table:
                 q_table[current_state] = [0.0] * action_space_size

            # Choose action using epsilon-greedy based on GLOBAL Q-table
            if random.random() < epsilon:
                chosen_action_index = random.randrange(action_space_size)
            else:
                q_values = q_table[current_state]
                max_q = max(q_values)
                # Handle ties randomly
                best_actions = [i for i, q in enumerate(q_values) if q == max_q]
                # Safeguard (should not be needed if q_values is not empty)
                if not best_actions:
                     chosen_action_index = random.randrange(action_space_size)
                else:
                     chosen_action_index = random.choice(best_actions)


            # Store state and action for THIS bot instance for the next step
            s._last_state = current_state
            s._last_action_index = chosen_action_index

            analog_x, analog_y = action_map[chosen_action_index]

            super().on_move_left_right(analog_x)
            super().on_move_up_down(analog_y)
            # Commented out: Overlay update call
            # if s.__class__.ov is not None: # Add a check if overlay is None
            #     s.__class__.ov.up(analog_x,analog_y)


            # Epsilon decay is GLOBAL
            epsilon = max(epsilon_min, epsilon * epsilon_decay)

            # Commented out: Call to show bubble
            # s._maybe_show_bubble()

            # Reschedule move timer for THIS bot instance
            s._move_timer = timer(0.05, call=s.move)


    def key(s,i,j):
        if i != 0:
            getattr(
                s,
                f"on_{['jump','bomb','pickup','punch'][i]}"+
                f"_{['release','press'][j]}"
            )()
            # Commented out: Overlay key update call
            # if s.__class__.ov is not None: # Add a check if overlay is None
            #     getattr(s.__class__.ov,f"{['release','press'][j]}")(i)
        else:
            # Commented out: Overlay key update call for jump
            # if s.__class__.ov is not None: # Add a check if overlay is None
            #     getattr(s.__class__.ov,f"{['release','press'][j]}")(i)
            pass # Keep this pass if you might add other jump key logic later


# Commented out: Overlay class definition
# class Overlay:
#     def __init__(s):
#         s.colors = [
#             [(0.2,0.6,0.2),(0.4,1,0.4)],
#             [(0.6,0,0),(1,0,0)],
#             [(0.2,0.6,0.6),(0.4,1,1)],
#             [(0.6,0.6,0.2),(1,1,0.4)],
#             [(0.4,0.33,0.6),(0.2,0.13,0.3)]
#         ]
#         s.pics = []
#         s.nub = []
#         for i in range(4):
#             j = ['Jump','Bomb','PickUp','Punch'][i]
#             k = [600,650,600,550][i]
#             l = [170,220,270,220][i]
#             c = s.colors[i][0]
#             n = newnode(
#                 'image',
#                 attrs={
#                     'texture': gbt('button'+j),
#                     'absolute_scale': True,
#                     'position': (k,l),
#                     'opacity': 0.8,
#                     'scale': (60,60),
#                     'color': c
#                 }
#             )
#             s.pics.append(n)
#         s.np = (430,220)
#         for i in [0,1]:
#             j = [110,60][i]
#             n = newnode(
#                 'image',
#                 attrs={
#                     'texture': gbt('nub'),
#                     'absolute_scale': True,
#                     'position': s.np,
#                     'scale': (j,j),
#                     'opacity': [0.4,0.7][i],
#                     'color': s.colors[4][i]
#                 }
#             )
#             s.nub.append(n)
#     def set(s,i,c):
#         s.pics[i].color = c
#     def press(s,i):
#         s.set(i,s.colors[i][1])
#     def release(s,i):
#         s.set(i,s.colors[i][0])
#     def nodes(s):
#         return s.pics + s.nub
#     def up(s,lr,ud):
#         p = s.np
#         m = math.sqrt(lr**2+ud**2) or 1
#         d = 25*min(math.sqrt(lr**2+ud**2),1)
#         lr /= m
#         ud /= m
#         s.nub[1].position = (p[0]+lr*d,p[1]+udd)
#     def destroy(s):
#         for node in s.nodes():
#             if node.exists():
#                 node.delete()
#         s.pics = []
#         s.nub = []

# ba_meta require api 9
class byBordd(Plugin): pass
