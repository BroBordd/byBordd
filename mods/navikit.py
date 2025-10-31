# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
NaviKit v1.0 - Smart Navigation & Combat AI

NaviKit provides intelligent bot classes using A* pathfinding:
- NaviBot: Smart navigation bot that can move to any point
- KillBot: Aggressive hunter combining pathfinding with combat skills

Uses navigation graphs from walkable triangles.
Relies on mapLevelCollide cob mesh, baked as a json using pathmaker.

To convert any map collision mesh (cob) to a path json,
or get premade json files for game's builtin maps,
see my pathmaker:
https://github.com/BroBordd/pathmaker
"""

from bascenev1lib.actor.spaz import Spaz
from babase import app, get_string_height as gsh, get_string_width as gsw
import bascenev1 as bs
from math import sqrt
import json
import os
from random import choice, random

try:
    from bubble import Bubble
    HAS_BUBBLE = True
except ImportError:
    HAS_BUBBLE = False

DEBUG = False

def log(msg):
    if DEBUG:
        print(f"[NaviKit] {msg}")


class Stream:
    """
    A class to create a speech bubble floating above a node.
    
    This bubble displays text and can be animated to appear and disappear.
    It consists of a background text block and a foreground text block
    to create a solid look.
    """
    def __init__(s, head, res='\u2588', resw=19.0):
        s.head = head
        s.res = res
        s.resw = resw
        s.text = ''
        s.kids = []
        s.bye = None
        s.node = bs.newnode(
            'math',
            delegate=s,
            attrs={
                'input1': (0, 0, 0),
                'operation': 'add'
            }
        )
        head.connectattr('position', s.node, 'input2')
        for _ in [0, 0.85]:
            n = _TEX(s.node, color=(_, _, _))
            s.kids.append(n)
            s.node.connectattr('output', n, 'position')
    
    def push(s, text=''):
        s.bye = None
        if not text:
            s.anim(1, 0)
            s.text = text
            return
        ls = len(text.splitlines())
        s.node.input1 = (0, 1.3 + 0.32 * ls, 0)
        bg, t = s.kids
        bg.text = (round(_GSW(text) / s.resw + 1) * s.res + '\n') * ls
        t.text = text
        if not s.text:
            s.anim(0, 1)
        s.text = text
        s.bye = bs.Timer(3.5, s.push)
    
    def anim(s, p1, p2):
        try:
            [bs.animate(_, 'opacity', {0: p1, 0.2: p2}) for _ in s.kids]
        except:
            pass


def _GSW(s):
    return gsw(s, suppress_warning=True)


def _GSH(s):
    return gsh(s, suppress_warning=True)


def _TEX(o, **k):
    return bs.newnode(
        'text',
        owner=o,
        attrs={
            'in_world': True,
            'scale': 0.01,
            'flatness': 1,
            'h_align': 'center',
            **k
        }
    )

class NavGraph:
    """Handles navigation mesh loading and pathfinding"""

    CLIMB_PENALTY = 4

    def __init__(self, filepath):
        self.nodes = []
        self.edges = {}
        self.loaded = False
        self._load(filepath)

    def _load(self, filepath):
        try:

            if not os.path.exists(filepath):
                print(f"[NavGraph] File not found: {filepath}")
                return

            with open(filepath, 'r') as f:
                data = json.load(f)

            self.nodes = data.get('nodes', [])

            # Build adjacency list from node neighbors
            self.edges = {}
            for node in self.nodes:
                node_id = node['id']
                self.edges[node_id] = []

                pos = node['position']
                for neighbor_id in node.get('neighbors', []):
                    if neighbor_id < len(self.nodes):
                        neighbor_pos = self.nodes[neighbor_id]['position']
                        dist = self._distance(pos, neighbor_pos)

                        # PENALIZE UPHILL EDGES
                        height_diff = neighbor_pos[1] - pos[1]
                        if height_diff > 0:
                            dist *= self.CLIMB_PENALTY  # Make steep paths "longer"

                        self.edges[node_id].append((neighbor_id, dist))

            self.loaded = len(self.nodes) > 0
            log(f"Loaded {len(self.nodes)} nodes with climb penalty {self.CLIMB_PENALTY}x")

        except Exception as e:
            print(f"[NavGraph] Load error: {e}")

    @staticmethod
    def _distance(a, b):
        return sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)

    def find_nearest_node(self, pos):
        """Find closest navigation node to position"""
        if not self.nodes:
            return None

        best_id = 0
        best_dist = float('inf')

        for node in self.nodes:
            dist = self._distance(pos, node['position'])
            if dist < best_dist:
                best_dist = dist
                best_id = node['id']

        # Check if nearest node is too far
        if best_dist > 10.0:
            log(f"Nearest node too far: {best_dist:.2f} from pos {pos}")
            return None

        log(f"Nearest node: {best_id} at distance {best_dist:.2f}")
        return best_id

    def find_path(self, start_pos, goal_pos):
        """A* pathfinding between two positions"""
        start_id = self.find_nearest_node(start_pos)
        goal_id = self.find_nearest_node(goal_pos)

        log(f"Pathfinding: start_id={start_id}, goal_id={goal_id}")

        if start_id is None or goal_id is None:
            log(f"Cannot find nodes - start_pos={start_pos}, goal_pos={goal_pos}")
            return []

        if start_id == goal_id:
            return [goal_pos]

        # A* algorithm
        open_set = {start_id}
        came_from = {}
        g_score = {start_id: 0}

        def heuristic(node_id):
            pos = self.nodes[node_id]['position']
            return self._distance(pos, self.nodes[goal_id]['position'])

        f_score = {start_id: heuristic(start_id)}

        iterations = 0
        max_iterations = 10000

        while open_set and iterations < max_iterations:
            iterations += 1
            current = min(open_set, key=lambda n: f_score.get(n, float('inf')))

            if current == goal_id:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(self.nodes[current]['position'])
                    current = came_from[current]
                path.reverse()
                path.append(goal_pos)
                log(f"Path found: {len(path)} waypoints, {iterations} iterations")
                return path

            open_set.remove(current)

            for neighbor_id, edge_cost in self.edges.get(current, []):
                tentative_g = g_score[current] + edge_cost

                if neighbor_id not in g_score or tentative_g < g_score[neighbor_id]:
                    came_from[neighbor_id] = current
                    g_score[neighbor_id] = tentative_g
                    f_score[neighbor_id] = tentative_g + heuristic(neighbor_id)
                    open_set.add(neighbor_id)

        log(f"No path found after {iterations} iterations")
        return []


class NaviBot:
    """Smart navigation bot for BombSquad"""

    MAX_VELOCITY = 6

    def __init__(self, navguide: str, position=(0,0,0), color=(0,0,0), highlight=(0.1,0.1,0.1), character='Pixel'):
        # Spawn bot
        self.bot = Spaz(color=color, highlight=highlight, character=character)
        self.bot.handlemessage(bs.StandMessage(position, 0))
        self.node = self.bot.node
        self.node.name = self.__class__.__name__

        # Load navigation graph
        self.nav = NavGraph(navguide)
        if not self.nav.loaded:
            print("[NaviBot] Failed to load navigation data")
            return

        # Navigation state
        self.target = None
        self.path = []
        self.current_waypoint = 0

        # Timers
        self.update_timer = None
        self.abuse_timer = None

        # Movement state
        self.last_pos = None
        self.stuck_counter = 0

        # Height tracking for vertical movement
        self.vertical_progress_start = None
        self.last_height = None

        # Velocity control
        self.run_multiplier = 1.0  # Controls run intensity (0 to 1)
        self.pinch = False
        self._speak("NaviBot online")
        log("Initialized")

    def _speak(self, text):
        """Display dialogue bubble if available"""
        if HAS_BUBBLE and self.node and self.node.exists():
            Bubble(node=self.node, text=text, time=3.0, color=self.node.name_color)

    def yay(self):
        """Yay"""
        self.node.handlemessage('celebrate',200)

    def move_to_point(self, x, y, z):
        """Command bot to navigate to target position"""
        self.target = (x, y, z)
        self.path = []
        self.pinch = False
        self.current_waypoint = 0
        self.stuck_counter = 0
        self.vertical_progress_start = None
        self.last_height = None
        self.run_multiplier = 1.0

        log(f"New target: {self.target}")
        
        # Only NaviBot says "Moving!" - subclasses can override this message
        if self.__class__.__name__ == 'NaviBot':
            self._speak("Moving!")

        # Start update loops
        if self.update_timer is None:
            self.update_timer = bs.Timer(0.05, self._update, repeat=True)
            self.abuse_timer = bs.Timer(0.15, self._abuse_movement, repeat=True)

    def stop(self):
        """Stop all movement"""
        self.target = None
        self.path = []
        self.update_timer = None
        self.abuse_timer = None

        if self.bot.exists():
            self.bot.on_move_left_right(0)
            self.bot.on_move_up_down(0)
            self.bot.on_run(0)

    def _abuse_movement(self):
        """Abuse timer for 90 degree breaks (mandatory) - uses run_multiplier"""
        if self.bot.exists():
            self.bot.on_run(0)
            bs.timer(0.02, lambda: self.bot.on_run(self.run_multiplier))

    def _check_velocity(self):
        """Monitor velocity and adjust run_multiplier to prevent falling"""
        if not self.node or not self.node.exists():
            return

        try:
            vx, vy, vz = self.node.velocity
            horizontal_speed = sqrt(vx**2 + vz**2)

            if horizontal_speed > self.MAX_VELOCITY:
                # Too fast! Stop running to slow down
                self.run_multiplier = 0.0
                log(f"Velocity too high: {horizontal_speed:.2f}, cooling down")
            else:
                # Safe speed, resume running
                if self.run_multiplier < 1.0:
                    self.run_multiplier = 1.0
                    log(f"Velocity safe: {horizontal_speed:.2f}, resuming")
        except:
            pass

    def _update(self):
        """Main navigation update loop"""
        # Safety checks
        if not self.target or not self.node or not self.node.exists():
            self.stop()
            return

        try:
            pos = tuple(self.node.position)
        except:
            self.stop()
            return

        # Check velocity to prevent falling from momentum
        self._check_velocity()

        # Check if we reached the target
        dist_to_target = sqrt(
            (pos[0] - self.target[0])**2 +
            (pos[1] - self.target[1])**2 +
            (pos[2] - self.target[2])**2
        )

        if dist_to_target < 0.6:
            log("Target reached!")
            self._speak("Target acquired")
            # KillBot doesn't celebrate - just keeps hunting
            self.stop()
            return

        # Generate path if needed
        if not self.path or self._should_replan(pos):
            self.path = self.nav.find_path(pos, self.target)
            self.current_waypoint = 0
            self.vertical_progress_start = None

            if not self.path:
                if not self.pinch:
                    log("No path found")
                    self._speak("Path blocked")
                    self.pinch = True
                self._move(0, 0)
                return
            self.pinch = False
            log(f"Path calculated: {len(self.path)} waypoints")

        # Check for being stuck
        if self._is_stuck(pos):
            log("Stuck detected, replanning")
            self._speak("Recalculating")
            self.path = []
            self.stuck_counter = 0
            self.vertical_progress_start = None
            return

        # Navigate to current waypoint
        if self.current_waypoint >= len(self.path):
            self._move(0, 0)
            return

        waypoint = self.path[self.current_waypoint]

        # Calculate distances
        dist_2d = sqrt(
            (pos[0] - waypoint[0])**2 +
            (pos[2] - waypoint[2])**2
        )

        height_diff = waypoint[1] - pos[1]

        # CRITICAL: Handle vertical movement specially
        # If waypoint is significantly above us, we're climbing
        if height_diff > 0.3:
            # We're going uphill - TINY distance threshold

            if self.vertical_progress_start is None:
                self.vertical_progress_start = pos[1]
                self.last_height = pos[1]

            # Calculate FULL 3D distance to waypoint
            dist_3d = sqrt(
                (pos[0] - waypoint[0])**2 +
                (pos[1] - waypoint[1])**2 +
                (pos[2] - waypoint[2])**2
            )

            # TINY THRESHOLD - must be basically ON TOP of the waypoint
            can_advance = dist_3d < 0.1

            if can_advance:
                log(f"Climb complete: 3D distance {dist_3d:.3f}")
                self.current_waypoint += 1
                self.vertical_progress_start = None
                self.last_height = None
                if self.current_waypoint < len(self.path):
                    waypoint = self.path[self.current_waypoint]
                else:
                    return
        else:
            # Normal horizontal movement or downhill - standard distance check
            if dist_2d < 0.4:
                self.current_waypoint += 1
                self.vertical_progress_start = None
                self.last_height = None
                if self.current_waypoint < len(self.path):
                    waypoint = self.path[self.current_waypoint]
                else:
                    return

        # Move towards waypoint
        dx = waypoint[0] - pos[0]
        dz = waypoint[2] - pos[2]
        dist = sqrt(dx*dx + dz*dz)

        if dist > 0.1:
            move_x = dx / dist
            move_z = dz / dist
            self._move(move_x, move_z)
        else:
            self._move(0, 0)

        self.last_pos = pos
        self.last_height = pos[1]

    def _move(self, x, z):
        """Set bot movement direction"""
        if self.bot.exists():
            self.bot.on_move_left_right(x)
            self.bot.on_move_up_down(-z)
            # Always call on_run with run_multiplier (controlled by velocity check)
            self.bot.on_run(self.run_multiplier if (x != 0 or z != 0) else 0)

    def _should_replan(self, pos):
        """Check if path needs recalculation"""
        if not self.path:
            return True

        # Replan if bot has drifted far from path
        if self.current_waypoint < len(self.path):
            wp = self.path[self.current_waypoint]
            dist = sqrt((pos[0]-wp[0])**2 + (pos[2]-wp[2])**2)
            if dist > 1:
                return True

        return False

    def _is_stuck(self, pos):
        """Detect if bot is stuck"""
        if self.last_pos is None:
            return False

        movement = sqrt(
            (pos[0] - self.last_pos[0])**2 +
            (pos[2] - self.last_pos[2])**2
        )

        if movement < 0.02:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0

        return self.stuck_counter > 30  # ~1.5 seconds of no movement


class KillBot(NaviBot):
    """
    NaviBot + Ender combat abilities.
    Intelligently hunts players using pathfinding and combat skills.
    """

    def __init__(self, navguide: str, position=None, color=(0,0,0), highlight=(0,0,0), character='Agent Johnson'):
        # Get spawn positions dynamically from map
        try:
            map_obj = bs.getactivity().map
            spawn_points = map_obj.ffa_spawn_points
            initial_position = choice(spawn_points)
        except:
            initial_position = (0, 0.1, 0)
        
        # Temporarily set stream to None to prevent errors during parent init
        self.stream = None
        
        # Initialize parent NaviBot
        super().__init__(navguide, initial_position, color, highlight, character)
        
        # Now properly initialize Stream bubble for KillBot
        self.stream = Stream(self.node)
        
        # Ender combat attributes
        self.last_skill_time = 0.0
        self.speech_cooldown = 1.5
        self.last_speech_time = 0.0
        self.last_idle_chat_time = 0.0
        self.last_held_message_time = 0.0
        self.held_message_cooldown = 1.0
        
        self.is_shaking = False
        self._skill1_timer = None
        self._shake_timer = None
        self._has_announced_target = False
        
        # Combat AI timers
        self._hunt_timer = bs.Timer(0.3, self._hunt_think, repeat=True)  # Slower update rate
        self._protective_timer = bs.Timer(0.001, self._protective_think, repeat=True)
        
        # Ender messages
        self.greed_messages = [
            'Upgrading my arsenal',
            'Tools of the trade acquired',
            'Enhancement detected, claiming it',
            'Professional always upgrades',
            'Better equipment, better kills',
            'Agency-approved enhancement',
            'Tactical advantage secured',
            'Power increase: authorized',
            'Optimizing my lethality',
            'Every edge counts in this business',
            'Collecting professional perks',
            'Weapon upgrade in progress',
            'Enhancing operational capability',
            'Time to improve my kill rate',
            'Death just got an upgrade',
            'More power, more contracts',
            'The agency provides the best gear',
            'Efficiency boost acquired',
            'Maximizing my potential',
            'Superior firepower obtained'
        ]

        self.pursuit_messages = [
            'Target locked and pursuing',
            'You can run, but you can\'t hide',
            'Contract initiated',
            'Time to kill',
            'No escape from the shadows',
            'Professional courtesy: you\'re dead',
            'The hunt is on',
            'Moving to intercept',
            'Your time has come',
            'Surrender to your death',
            'Tracking device activated',
            'Distance closing rapidly',
            'You\'ve been marked',
            'The reaper approaches',
            'Nowhere to run now',
            'My scope has found you',
            'Target in sight, engaging',
            'Death wears sunglasses',
            'The shadows have eyes',
            'Running only delays the inevitable'
        ]

        self.acquire_messages = [
            'Contract fulfilled',
            'Nothing personal, just business',
            'Target terminated',
            'Clean execution',
            'Job well done',
            'Payment collected',
            'Another satisfied client',
            'Precision strike complete',
            'Mission accomplished',
            'Professional service delivered',
            'Direct hit confirmed',
            'Lights out, game over',
            'Another one bites the dust',
            'The agency trained me well',
            'One shot, one kill',
            'Consider yourself retired',
            'Welcome to the afterlife',
            'Efficiency at its finest',
            'Target down, objective complete',
            'Another name crossed off the list',
            'Next target please'
        ]

        self.release_messages = [
            'Target eliminated',
            'Contract completed successfully',
            'Clean kill, no witnesses',
            'Another day at the office',
            'Professional standards maintained',
            'Mission status: success',
            'Package delivered',
            'Work is done here',
            'Next contract, please',
            'The agency will be pleased',
            'File closed permanently',
            'Invoice sent to client',
            'Quality work, as always',
            'Time to find the next mark',
            'Job satisfaction: maximum',
            'The shadows claim another',
            'Case closed with extreme prejudice',
            'Retirement plan activated',
            'Service with a smile... and a scope',
            'Professional courtesy extended'
        ]

        self.idle_messages = [
            'Server feels empty...',
            'Where did everyone go?',
            'Waiting for targets to arrive',
            'Ghost town out here',
            'Even assassins get lonely',
            'No contracts available',
            'Silence... too much silence',
            'The hunt begins when they return',
            'Empty servers, empty clips',
            'Sharpening skills in the shadows',
            'This place needs more action',
            'Even pros need someone to eliminate',
            'Scanning... no life signs detected',
            'The agency didn\'t mention this downtime',
            'Population: zero. Boring.',
            'Come out, come out, wherever you are',
            'A killer without prey is just... waiting',
            'Time to attract some fresh meat',
            'Server population critically low',
            'The darkness grows restless',
            'Maintenance mode: activated',
            'Solo missions are overrated',
            'The void stares back',
            'Recruiting new victims...',
            'Echo... echo... echo...',
            'My trigger finger is getting itchy',
            'Quality over quantity, but still...',
            'The calm before someone joins',
            'Broadcasting on all frequencies',
            'Time to update the kill count... oh wait'
        ]

        self.held_messages = [
            "You're holding the wrong guy",
            "Grabbing me was a bad idea",
            "You think holding me will help?",
            "Wrong target to grab, pal",
            "Hands off the professional",
            "That grip won't save you",
            "You're holding a loaded weapon",
            "Bad move grabbing an agent",
            "Your hold won't last long",
            "Holding me just delays your death",
            "Nice grip, shame you have to die",
            "You're clutching at straws now",
            "That grasp is about to slip",
            "Holding me? How unprofessional",
            "Your grip is weaker than your chances",
            "You grabbed death itself",
            "Restraining me won't restrain fate",
            "That hold is temporary, your death isn't",
            "Grabbing me just made this personal",
            "You've got nerves touching the reaper"
        ]
        
        self._speak("KillBot online - Hunt mode active")

    def _speak(self, text):
        """Override parent _speak to use Stream instead of Bubble"""
        if self.stream and self.node and self.node.exists():
            self.stream.push(text)

    def _say(self, message: str):
        """Handles speaking with cooldown using Stream"""
        now = bs.time()
        if now - self.last_speech_time > self.speech_cooldown:
            self._speak(message)
            self.last_speech_time = now

    def _say_held(self):
        """Urgent message with own cooldown using Stream"""
        now = bs.time()
        if now - self.last_held_message_time > self.held_message_cooldown:
            self._speak(choice(self.held_messages))
            self.last_held_message_time = now

    def on(self, i):
        """Execute bot action (Ender method)"""
        for _ in [1, 0]:
            getattr(self.bot, 'on_' + ['jump','bomb','pickup','punch'][i] + '_' + ['release','press'][_])()

    def skill1(self):
        """Jump-bomb-pickup-punch combo"""
        self.on(0)  # jump
        self.on(1)  # bomb
        bs.timer(0.04, lambda: self.on(2))  # pickup
        bs.timer(0.07, lambda: self.on(3))  # punch

    def skill2(self):
        """Punch-grab combo"""
        self.on(3)  # punch
        bs.timer(0.05, lambda: self.on(2))  # pickup

    def _get_target(self):
        """Find closest player or powerup - PRIORITIZE PLAYERS"""
        if not self.node.exists():
            return None
        
        my_pos = self.node.position
        
        player_nodes = []
        pup_nodes = []
        
        for n in bs.getnodes():
            try:
                if n.exists() and n.getnodetype() == 'spaz' and n.hurt < 1.0 and n is not self.node:
                    player_nodes.append(n)
                    continue
                
                ty = getattr(n.getdelegate(object), 'poweruptype', 0)
                if ty and sqrt((n.position[0]-my_pos[0])**2 + (n.position[2]-my_pos[2])**2) > 5.5 or self.node.hold_node:
                    continue
                    
                if ty == 'health' and self.node.hurt < 0.3:
                    continue
                elif ty == 'punch' and self.node.getdelegate(object)._has_boxing_gloves:
                    continue
                elif ty == 'shield' and (self.node.getdelegate(object).shield_hitpoints or 0) > 200:
                    continue
                    
                if ty:
                    pup_nodes.append((ty, n))
            except:
                pass
        
        # PRIORITIZE PLAYERS - only go for powerups if no players exist
        self.greed = False
        if player_nodes:
            return min(player_nodes, key=lambda n: sqrt(
                (my_pos[0]-n.position[0])**2 + 
                (my_pos[1]-n.position[1])**2 + 
                (my_pos[2]-n.position[2])**2
            ))
        
        if pup_nodes:
            self.greed = True
            return min(pup_nodes, key=lambda _: sqrt(
                (my_pos[0]-_[1].position[0])**2 + 
                (my_pos[1]-_[1].position[1])**2 + 
                (my_pos[2]-_[1].position[2])**2
            ))

    def _protective_think(self):
        """Fast defensive reactions"""
        if not self.node.exists():
            return

        target = self._get_target()
        if isinstance(target, tuple):
            return
        
        now = bs.time()
        
        # Break free if held
        if target and target.hold_node == self.node and now - self.last_skill_time > 0.4:
            self._say_held()
            self.skill2()
            self.last_skill_time = now
            return
        
        # Close-range combo
        if target and self.node.run and now - self.last_skill_time > 0.4:
            my_pos = self.node.position
            target_pos = target.position
            distance = sqrt(
                (my_pos[0]-target_pos[0])**2 + 
                (my_pos[1]-target_pos[1])**2 + 
                (my_pos[2]-target_pos[2])**2
            )
            
            if distance < 1.6:
                self.skill2()
                self.last_skill_time = now

    def _start_combos(self):
        """Start skill combos on held target"""
        self._say(choice(self.acquire_messages))
        self._skill1_timer = bs.Timer(0.4, self.skill1, repeat=True)
        self._shake_timer = bs.Timer(0.05, self._shake, repeat=True)

    def _stop_combos(self):
        """Stop all combos"""
        if hasattr(self, '_skill1_timer') and self._skill1_timer:
            self._skill1_timer = None
        if hasattr(self, '_shake_timer') and self._shake_timer:
            self._shake_timer = None

    def _shake(self):
        """Rapid shaking movement"""
        self.is_shaking = not self.is_shaking
        if self.bot.exists():
            if self.is_shaking:
                self.bot.on_move_left_right(0.5)
                self.bot.on_move_up_down(0.1)
            else:
                self.bot.on_move_left_right(-0.5)
                self.bot.on_move_up_down(0.1)

    def _hunt_think(self):
        """Main hunting AI loop using pathfinding"""
        if not self.node.exists():
            self._hunt_timer = None
            self._protective_timer = None
            self._stop_combos()
            return

        now = bs.time()
        target = self._get_target()
        
        if isinstance(target, tuple):
            ty, target = target
        else:
            # Check for wrong/dead target in hold
            if self.node.hold_node and (self.node.hold_node != target or (target and target.hurt == 1.0)):
                self._stop_combos()
                
                if self.node.hold_node and self.node.hold_node != target and target:
                    self._say("Why am I holding this")
                elif target and target.hurt == 1.0:
                    self._say(choice(self.release_messages))
                
                self.on(2)  # Release
                if self.bot.exists():
                    self.bot.on_move_left_right(0)
                    self.bot.on_move_up_down(0)
                self._has_announced_target = False
                return
            
            # Shaking when holding correct target
            if self.node.hold_node == target:
                self.bot.on_run(0)
                
                if not self._skill1_timer:
                    self._start_combos()
                return
            
            self._stop_combos()

        # Hunt the target using pathfinding
        if target and target.exists():
            if not self._has_announced_target:
                self._speak('')  # Clear bubble
                if self.greed:
                    self._say(choice(self.greed_messages))
                else:
                    self._say(choice(self.pursuit_messages))
                self._has_announced_target = True

            target_pos = tuple(target.position)
            
            # Only recalculate path if target moved significantly (3 units) or we have no path
            if not hasattr(self, '_last_target_pos') or not self.path:
                self._last_target_pos = target_pos
                self.move_to_point(target_pos[0], target_pos[1], target_pos[2])
            else:
                # Check distance moved
                dist_moved = sqrt(
                    (target_pos[0] - self._last_target_pos[0])**2 +
                    (target_pos[1] - self._last_target_pos[1])**2 +
                    (target_pos[2] - self._last_target_pos[2])**2
                )
                
                # Only replan if target moved significantly
                if dist_moved > 1.2:
                    self._last_target_pos = target_pos
                    self.move_to_point(target_pos[0], target_pos[1], target_pos[2])
            
            # Occasional pursuit message
            if random() < 0.05 and now - self.last_speech_time > self.speech_cooldown:
                self._say(choice(self.greed_messages if self.greed else self.pursuit_messages))

        else:
            # No targets - idle
            if self._has_announced_target:
                self._has_announced_target = False
                self.last_idle_chat_time = now + 2
                self._last_target_pos = None  # Clear cached position
            elif now - self.last_idle_chat_time > 5:
                self._say(choice(self.idle_messages))
                self.last_idle_chat_time = now
            
            self.stop()


def debug_navi(pos=None):
    """Debug spawn for NaviBot"""
    map = bs.getactivity().map
    pos = pos or map.ffa_spawn_points[0]
    filename = str(map.node.collision_mesh).split('"')[1]+"_navguide.json"
    filepath = os.path.join(app.env.python_directory_user, 'Paths', filename)
    bot = NaviBot(
        position=pos,
        color=(0,0,0),
        highlight=(0.1,0.1,0.1),
        character='Pixel',
        navguide=filepath
    )

    return bot


def debug_kill():
    """Debug spawn for KillBot - spawns at random spawn point and hunts players"""
    map = bs.getactivity().map
    filename = str(map.node.collision_mesh).split('"')[1]+"_navguide.json"
    filepath = os.path.join(app.env.python_directory_user, 'Paths', filename)
    bot = KillBot(
        color=(0,0,0),
        highlight=(0,0,0),
        character='Agent Johnson',
        navguide=filepath
    )

    return bot
