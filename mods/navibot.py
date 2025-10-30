# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
NaviBot v1.0 - Mission: Navigate.

NaviBot uses A* pathfinding using a navigation graph of walkable triangles.
Relies on mapLevelCollide cob mesh, baked as a json using pathmaker.

To convert any map collision mesh (cob) to a path json,
or get premade json files for game's builtin maps,
see my pathmaker:
https://github.com/BroBordd/pathmaker
"""

from bascenev1lib.actor.spaz import Spaz
from babase import app
import bascenev1 as bs
from math import sqrt
import json
import os

try:
    from bubble import Bubble
    HAS_BUBBLE = True
except ImportError:
    HAS_BUBBLE = False

DEBUG = False

def log(msg):
    if DEBUG:
        print(f"[NaviBot] {msg}")

class NavGraph:
    """Handles navigation mesh loading and pathfinding"""

    # ADJUSTABLE: How much to penalize steep climbs (higher = avoid steep paths more)
    CLIMB_PENALTY = 5.0  # Multiply edge cost by this when climbing

    def __init__(self, filename):
        self.nodes = []
        self.edges = {}
        self.loaded = False
        self._load(filename)

    def _load(self, filename):
        try:
            filepath = os.path.join(app.env.python_directory_user, 'Paths', filename)

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
                        if height_diff > 0.2:  # Going uphill
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

        return best_id

    def find_path(self, start_pos, goal_pos):
        """A* pathfinding between two positions"""
        start_id = self.find_nearest_node(start_pos)
        goal_id = self.find_nearest_node(goal_pos)

        if start_id is None or goal_id is None:
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

        while open_set:
            current = min(open_set, key=lambda n: f_score.get(n, float('inf')))

            if current == goal_id:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(self.nodes[current]['position'])
                    current = came_from[current]
                path.reverse()
                path.append(goal_pos)
                return path

            open_set.remove(current)

            for neighbor_id, edge_cost in self.edges.get(current, []):
                tentative_g = g_score[current] + edge_cost

                if neighbor_id not in g_score or tentative_g < g_score[neighbor_id]:
                    came_from[neighbor_id] = current
                    g_score[neighbor_id] = tentative_g
                    f_score[neighbor_id] = tentative_g + heuristic(neighbor_id)
                    open_set.add(neighbor_id)

        return []


class NaviBot:
    """Smart navigation bot for BombSquad"""

    NAV_FILE = "cragCastleLevelCollide_path.json"

    def __init__(self, position=(0,0,0), color=(0,0,0), highlight=(0.1,0.1,0.1), character='Pixel'):
        # Spawn bot
        self.bot = Spaz(color=color, highlight=highlight, character=character)
        self.bot.handlemessage(bs.StandMessage(position, 0))
        self.node = self.bot.node

        # Load navigation graph
        self.nav = NavGraph(self.NAV_FILE)
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

        self._speak("NaviBot online")
        log("Initialized")

    def _speak(self, text):
        """Display dialogue bubble if available"""
        if HAS_BUBBLE and self.node and self.node.exists():
            Bubble(node=self.node, text=text, time=2.0, color=self.node.color)

    def move_to_point(self, x, y, z):
        """Command bot to navigate to target position"""
        self.target = (x, y, z)
        self.path = []
        self.current_waypoint = 0
        self.stuck_counter = 0
        self.vertical_progress_start = None
        self.last_height = None

        log(f"New target: {self.target}")
        self._speak("Moving out!")

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
        """Abuse timer for 90 degree breaks (mandatory)"""
        if self.bot.exists():
            self.bot.on_run(0)
            bs.timer(0.02, lambda: self.bot.on_run(1))

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

        # Check if we reached the target
        dist_to_target = sqrt(
            (pos[0] - self.target[0])**2 +
            (pos[1] - self.target[1])**2 +
            (pos[2] - self.target[2])**2
        )

        if dist_to_target < 0.5:
            log("Target reached!")
            self._speak("Target acquired")
            self.stop()
            return

        # Generate path if needed
        if not self.path or self._should_replan(pos):
            self.path = self.nav.find_path(pos, self.target)
            self.current_waypoint = 0
            self.vertical_progress_start = None

            if not self.path:
                log("No path found")
                self._speak("Path blocked")
                self._move(0, 0)
                return

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

        if dist > 0.01:
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
            self.bot.on_run(1 if (x != 0 or z != 0) else 0)

    def _should_replan(self, pos):
        """Check if path needs recalculation"""
        if not self.path:
            return True

        # Replan if bot has drifted far from path
        if self.current_waypoint < len(self.path):
            wp = self.path[self.current_waypoint]
            dist = sqrt((pos[0]-wp[0])**2 + (pos[2]-wp[2])**2)
            if dist > 5.0:
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


# Test function
def spawn_test_bot():
    """Spawn a test bot for debugging"""
    bot = NaviBot(
        position=(0, 5, 0),
        color=(0, 0, 0),
        highlight=(0.1, 0.1, 0.1),
        character='Pixel'
    )

    # Command it to move somewhere
    bot.move_to_point(10, 5, -5)

    print("[Test] NaviBot spawned")
    return bot

