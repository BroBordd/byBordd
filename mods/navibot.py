# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only

"""
NaviBot v2.0 - Intelligent Pathfinding
"""

from bascenev1lib.actor.spaz import Spaz
import bascenev1 as bs
import json
import math
import heapq
import os

try:
    from bubble import Bubble
    HAS_BUBBLE = True
except ImportError:
    HAS_BUBBLE = False

DEBUG = True

def log(msg):
    if DEBUG:
        print(f"[NaviBot] {msg}")

class NaviBot:
    """
    Advanced bot with A* pathfinding and run-abuse physics.
    """

    def __init__(self, position=(0,0,0), color=(0,0,0), highlight=(0.1,0.1,0.1), character='Pixel'):
        # Spawn bot
        self.bot = Spaz(color=color, highlight=highlight, character=character)
        self.bot.handlemessage(bs.StandMessage(position, 0))
        self.node = self.bot.node
        self.node.name = self.__class__.__name__

        # Movement Configuration
        self.run_multiplier = 1.0
        self.waypoint_threshold = 1.2  # Distance to node before switching to next
        
        # Navigation State
        self.nav_graph = None # { 'nodes': [], 'adj': {} }
        self.current_path = [] # List of coordinate tuples (x,y,z)
        self.target_node_idx = None
        self.move_timer = None
        
        # Run Abuse Timer (The "Cut Turn" mechanic)
        # We keep this running to allow sharp turns physics
        self.abuse_timer = bs.Timer(0.15, self._abuse_movement, repeat=True)

        self._speak("NaviBot v2 Online")
        log("Initialized")

    def load_map(self, json_path):
        """Loads the pathmaker_v2.py output JSON."""
        try:
            # In a real mod, you might need to adjust the path to where BombSquad stores mods
            with open(json_path, 'r') as f:
                self.nav_graph = json.load(f)
            
            # Convert adjacency keys to int because JSON makes them strings
            self.nav_graph['adj'] = {int(k): v for k, v in self.nav_graph['adj'].items()}
            log(f"Map loaded: {len(self.nav_graph['nodes'])} nodes.")
        except Exception as e:
            log(f"Failed to load map: {e}")
            self._speak("Map Load Error!")

    def move_to(self, x, y, z):
        """
        Public API: Commands the bot to go to a coordinate.
        """
        if not self.nav_graph:
            log("No nav graph loaded!")
            return

        # 1. Find Start Node (closest to bot)
        start_node = self._get_closest_node(self.node.position)
        
        # 2. Find End Node (closest to target)
        target_node = self._get_closest_node((x, y, z))

        if start_node is None or target_node is None:
            self._speak("Cannot find path logic")
            return

        # 3. A* Pathfinding
        path_indices = self._astar(start_node, target_node)
        
        if not path_indices:
            self._speak("No path found!")
            return

        # 4. Convert indices to coordinates
        self.current_path = [self.nav_graph['nodes'][i]['p'] for i in path_indices]
        
        # Add the exact final coordinate as the very last step
        self.current_path.append((x, y, z))
        
        log(f"Path computed: {len(self.current_path)} steps.")
        
        # 5. Start Control Loop if not running
        if self.move_timer is None:
            self.move_timer = bs.Timer(0.05, self._update_movement, repeat=True)

    def stop(self):
        """Stop all movement and clear path."""
        self.current_path = []
        if self.bot.exists():
            self.bot.on_move_left_right(0)
            self.bot.on_move_up_down(0)
            self.bot.on_run(0)

    def _update_movement(self):
        """
        Called every 50ms. Handles steering along the path.
        """
        if not self.bot.exists():
            self.move_timer = None
            return

        if not self.current_path:
            self.stop()
            return

        # Get current target waypoint
        target = self.current_path[0]
        pos = self.node.position

        # Vector to target
        dx = target[0] - pos[0]
        dy = target[1] - pos[1] # Used for 3D distance check
        dz = target[2] - pos[2]
        
        dist_sq = dx*dx + dy*dy + dz*dz

        # Check if we reached the waypoint
        # Note: We use 3D distance. On cliffs, dy matters.
        if dist_sq < (self.waypoint_threshold ** 2):
            self.current_path.pop(0)
            if not self.current_path:
                self.stop()
                self.yay() # Celebration on arrival
                return
            # Recalculate for next point immediately to avoid stutter
            target = self.current_path[0]
            dx = target[0] - pos[0]
            dz = target[2] - pos[2]

        # Normalize 2D vector for input
        # We ignore Y for input because characters can't fly, they just walk
        length = math.sqrt(dx*dx + dz*dz)
        if length > 0.01:
            vx = dx / length
            vz = dz / length
        else:
            vx, vz = 0, 0

        # Apply Input
        self.bot.on_move_left_right(vx)
        self.bot.on_move_up_down(-vz) # BS uses negative Z for forward usually
        
        # Run is handled by _abuse_movement, but we ensure multiplier is set
        self.run_multiplier = 1.0

    def _abuse_movement(self):
        """
        Toggles run on/off rapidly to allow sharp turns without inertia.
        This is the 'Cut Turn' feature.
        """
        if self.bot.exists() and self.current_path:
            # Momentarily cut throttle
            self.bot.on_run(0)
            # Re-apply throttle in 20ms
            bs.timer(0.02, lambda: self.bot.on_run(self.run_multiplier) if self.bot.exists() else None)

    def _get_closest_node(self, pos):
        """Brute force closest node (Fast enough for <1000 nodes)."""
        best_dist = float('inf')
        best_idx = None
        px, py, pz = pos
        
        for node in self.nav_graph['nodes']:
            nx, ny, nz = node['p']
            # Weighted distance: Y distance penalizes more to differentiate floors
            dist = (nx-px)**2 + (ny-py)**2 * 4.0 + (nz-pz)**2
            if dist < best_dist:
                best_dist = dist
                best_idx = node['id']
        return best_idx

    def _astar(self, start_id, goal_id):
        """Standard A* implementation."""
        open_set = []
        heapq.heappush(open_set, (0, start_id))
        
        came_from = {}
        g_score = {node['id']: float('inf') for node in self.nav_graph['nodes']}
        g_score[start_id] = 0
        
        f_score = {node['id']: float('inf') for node in self.nav_graph['nodes']}
        f_score[start_id] = self._heuristic(start_id, goal_id)
        
        open_set_hash = {start_id} # For O(1) lookup

        while open_set:
            current = heapq.heappop(open_set)[1]
            open_set_hash.discard(current)

            if current == goal_id:
                return self._reconstruct_path(came_from, current)

            # Get neighbors from adjacency dict
            neighbors = self.nav_graph['adj'].get(current, [])
            
            for neighbor in neighbors:
                # Distance between current and neighbor
                d = self._dist(current, neighbor)
                tentative_g = g_score[current] + d

                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal_id)
                    
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
        
        return None # Path not found

    def _heuristic(self, a_id, b_id):
        return self._dist(a_id, b_id)

    def _dist(self, id1, id2):
        p1 = self.nav_graph['nodes'][id1]['p']
        p2 = self.nav_graph['nodes'][id2]['p']
        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)

    def _reconstruct_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        return total_path[::-1]

    def _speak(self, text):
        """Display dialogue bubble if available"""
        if HAS_BUBBLE and self.node and self.node.exists():
            Bubble(node=self.node, text=text, time=3.0, color=self.node.name_color)

    def yay(self):
        """Celebration animation"""
        self.node.handlemessage('celebrate', 2000)

def getme():
    for p in bs.get_foreground_host_activity().players:
        if p.sessionplayer.inputdevice.client_id == -1:
            return p.actor

# Helper to test in game
def spawn_with_path(cob_json_path):
    """Spawn a bot and load the specific map JSON."""
    map_obj = bs.getactivity().map
    pos = map_obj.ffa_spawn_points[0]
    
    bot = NaviBot(position=pos)
    bot.load_map(cob_json_path)
    return bot

def debug():
    from babase import app
    map_obj = bs.getactivity().map
    return spawn_with_path(
        os.path.join(
            app.env.python_directory_user,
            'Paths',
            str(map_obj.node.collision_mesh).split('"')[1]+'.json'
        )
    )
