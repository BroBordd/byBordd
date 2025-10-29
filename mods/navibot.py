# Copyright 2025 - Modified for COB Navigation Guide
# NaviBot v3.2 - Node-based navigation with enhanced stability and momentum control

"""
NaviBot v3.2 - Node-based navigation with COB collision guide

Key fixes:
- Edge pruning added to prevent skipping stairs/cliffs (MAX_VERTICAL_STEP).
- Dot product check implemented for sharp, non-smoothed cornering.
- Progress-based stuck check added to prevent infinite walking toward walls (NO_PROGRESS_TIME).
- Velocity check added to prevent falling off cliffs/paths during sharp turns (MAX_TURN_VELOCITY).
"""

from bascenev1lib.actor.spaz import Spaz
from babase import app
import bascenev1 as bs
from math import sqrt
import json
import os


class NaviBot:
    """
    Navigation-enabled bot using COB collision guide nodes.
    """
    
    # Configuration
    NAV_GUIDE_FILE = "cragCastleLevelCollide_path.json"
    
    # Pushed thresholds for better behavior (per user request):
    WAYPOINT_REACH_DIST = 0.70
    PATH_RECALC_DIST = 4.0
    UPDATE_INTERVAL = 0.05
    STUCK_THRESHOLD = 0.40
    STUCK_TIME = 1.5
    
    # Vertical Fix Thresholds:
    # UPDATED: Reduced to 0.40 to safely prevent skipping individual steps.
    MAX_VERTICAL_STEP = 0.40     
    
    # Progress Check Thresholds:
    NO_PROGRESS_TIME = 1.0
    
    # NEW: Velocity check threshold for sharp turns (Momentum control)
    # Velocity is checked in units/second. 4.0 is the recommended max.
    MAX_TURN_VELOCITY = 4.0      
    
    def __init__(
        self,
        position: tuple = (0, 0, 0),
        color: tuple = (0, 0, 0),
        highlight: tuple = (0, 0, 0),
        character: str = 'Pixel'
    ):
        print(f"[NaviBot] Initializing v3.2 (COB Node-Based)")
        
        # Create bot
        self.bot = Spaz(color=color, highlight=highlight, character=character)
        self.bot.handlemessage(bs.StandMessage(position, 0))
        self.node = self.bot.node
        self.node.name = self.__class__.__name__
        
        # Load navigation guide
        self._nav_nodes = []
        self._nav_edges = {}
        self._bounds = {}
        self._metadata = {}
        
        if self._load_nav_guide():
            self._build_edge_map()
        
        # Movement state
        self._target_pos = None
        self._path = []
        self._path_index = 0
        self._last_path_calc_pos = None
        self._update_timer = None
        
        # Stuck detection
        self._last_pos = None
        self._stuck_timer = 0.0
        
        # Waypoint progress tracking
        self._last_wp_dist_sq = float('inf') 
        self._no_progress_timer = 0.0        
        
        print(f"[NaviBot] Initialization complete")
    
    # ==================== PUBLIC API ====================
    
    def move_to_point(self, x: float, y: float, z: float):
        """Command bot to navigate to target position."""
        print(f"\n[NaviBot] New target: ({x:.1f}, {y:.1f}, {z:.1f})")
        
        self._target_pos = (x, y, z)
        self._path = []
        self._path_index = 0
        self._last_path_calc_pos = None
        self._stuck_timer = 0.0
        self._no_progress_timer = 0.0
        self._last_wp_dist_sq = float('inf')
        
        if self._update_timer is None:
            self._update_timer = bs.Timer(
                self.UPDATE_INTERVAL,
                self._update,
                repeat=True
            )
            print(f"[NaviBot] Movement timer started")
        
        return self._update_timer
    
    def stop_movement(self):
        """Stop all movement and clear path."""
        print(f"[NaviBot] Stopping movement")
        
        self._update_timer = None
        self._target_pos = None
        self._path = []
        self._path_index = 0
        
        if self.bot.exists():
            self.bot.on_move_left_right(0)
            self.bot.on_move_up_down(0)
            self.bot.on_run(0)
    
    # ==================== BASIC MOVEMENT ====================
    
    def _set_movement(self, x: float, z: float):
        """Set movement direction (normalized -1 to 1)."""
        if self.bot.exists():
            self.bot.on_move_left_right(x)
            self.bot.on_move_up_down(-z)
    
    def _set_running(self, running: bool):
        """Set running state."""
        if self.bot.exists():
            self.bot.on_run(1 if running else 0)
    
    # ==================== NAVIGATION GUIDE LOADING ====================
    
    def _load_nav_guide(self):
        """Load navigation guide JSON from COB collision mesh."""
        try:
            filepath = os.path.join(
                app.env.python_directory_user,
                'Paths',
                self.NAV_GUIDE_FILE
            )
            
            if not os.path.exists(filepath):
                print(f"[NaviBot] ERROR: Navigation guide not found: {filepath}")
                return False
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Extract data
            self._nav_nodes = data.get('nodes', [])
            edges_list = data.get('edges', [])
            self._bounds = data.get('bounds', {})
            self._metadata = data.get('metadata', {})
            
            print(f"[NaviBot] Navigation guide loaded: {filepath}")
            
            return len(self._nav_nodes) > 0
            
        except Exception as e:
            print(f"[NaviBot] ERROR loading navigation guide: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _build_edge_map(self):
        """Build adjacency map from nodes for fast pathfinding (incorporates MAX_VERTICAL_STEP fix)."""
        self._nav_edges = {node['id']: [] for node in self._nav_nodes}
        
        pruned_edges = 0
        
        for node in self._nav_nodes:
            node_id = node['id']
            neighbors = node.get('neighbors', [])
            pos1 = node['position']
            
            for neighbor_id in neighbors:
                if neighbor_id < len(self._nav_nodes):
                    pos2 = self._nav_nodes[neighbor_id]['position']
                    
                    # --- STAIRS/CLIFF FIX (Pruning steep edges) ---
                    vertical_distance = abs(pos1[1] - pos2[1])
                    
                    if vertical_distance > self.MAX_VERTICAL_STEP:
                        pruned_edges += 1
                        continue
                    # --- END FIX ---
                        
                    # Calculate distance
                    distance = sqrt(
                        (pos1[0] - pos2[0])**2 +
                        (pos1[1] - pos2[1])**2 +
                        (pos1[2] - pos2[2])**2
                    )
                    self._nav_edges[node_id].append((neighbor_id, distance))
        
        print(f"[NaviBot] Edge map built (Pruned {pruned_edges} steep edges)")
    
    # ==================== NODE FINDING ====================
    
    def _find_nearest_node(self, pos: tuple):
        """Find nearest navigation node to a world position."""
        if not self._nav_nodes:
            return None
        
        best_node_id = None
        best_distance = float('inf')
        
        for node in self._nav_nodes:
            node_pos = node['position']
            distance = sqrt(
                (pos[0] - node_pos[0])**2 +
                (pos[1] - node_pos[1])**2 +
                (pos[2] - node_pos[2])**2
            )
            
            if distance < best_distance:
                best_distance = distance
                best_node_id = node['id']
        
        return best_node_id
    
    # ==================== A* PATHFINDING ====================
    
    def _heuristic(self, node_id_a: int, node_id_b: int):
        """Heuristic: 3D Euclidean distance between nodes."""
        pos_a = self._nav_nodes[node_id_a]['position']
        pos_b = self._nav_nodes[node_id_b]['position']
        
        return sqrt(
            (pos_a[0] - pos_b[0])**2 +
            (pos_a[1] - pos_b[1])**2 +
            (pos_a[2] - pos_b[2])**2
        )
    
    def _reconstruct_path(self, came_from: dict, start_id: int, goal_id: int):
        """Build path by following parent pointers."""
        path = []
        current = goal_id
        
        while current != start_id:
            if current not in came_from:
                break
            node_pos = self._nav_nodes[current]['position']
            path.append(tuple(node_pos))
            current = came_from[current]
        
        path.reverse()
        return path
    
    def _find_path(self, start_pos: tuple, goal_pos: tuple):
        """A* pathfinding from start to goal using navigation nodes."""
        start_node_id = self._find_nearest_node(start_pos)
        goal_node_id = self._find_nearest_node(goal_pos)
        
        if start_node_id is None or goal_node_id is None:
            print(f"[NaviBot] Cannot find navigation nodes")
            return []
        
        if start_node_id == goal_node_id:
            return [goal_pos]
        
        start_node_pos = self._nav_nodes[start_node_id]['position']
        goal_node_pos = self._nav_nodes[goal_node_id]['position']
        
        print(f"[NaviBot] A* search: Node {start_node_id} -> Node {goal_node_id}")
        
        # A* algorithm
        open_set = {start_node_id}
        came_from = {}
        
        g_score = {start_node_id: 0}
        f_score = {start_node_id: self._heuristic(start_node_id, goal_node_id)}
        
        iterations = 0
        max_iterations = 5000
        
        while open_set and iterations < max_iterations:
            iterations += 1
            
            # Find node with lowest f_score
            current = min(open_set, key=lambda k: f_score.get(k, float('inf')))
            
            if current == goal_node_id:
                path = self._reconstruct_path(came_from, start_node_id, goal_node_id)
                path.append(goal_pos)
                
                print(f"[NaviBot] ✓ Path found: {len(path)} waypoints ({iterations} iterations)")
                return path
            
            open_set.remove(current)
            
            # Check all neighbors
            for neighbor_id, edge_distance in self._nav_edges.get(current, []):
                tentative_g = g_score[current] + edge_distance
                
                if neighbor_id not in g_score or tentative_g < g_score[neighbor_id]:
                    came_from[neighbor_id] = current
                    g_score[neighbor_id] = tentative_g
                    f_score[neighbor_id] = tentative_g + self._heuristic(neighbor_id, goal_node_id)
                    
                    if neighbor_id not in open_set:
                        open_set.add(neighbor_id)
        
        print(f"[NaviBot] ✗ No path found ({iterations} iterations)")
        return []
    
    # ==================== MOVEMENT UPDATE ====================
    
    def _update(self):
        """Main update loop."""
        
        # Safety checks
        if (not self._target_pos or
            not self.node or
            not self.node.exists() or
            not self._nav_nodes):
            self.stop_movement()
            return
        
        try:
            current_pos = tuple(self.node.position)
        except:
            self.stop_movement()
            return
        
        # Check if reached final destination
        dist_to_target = sqrt(
            (current_pos[0] - self._target_pos[0])**2 +
            (current_pos[1] - self._target_pos[1])**2 +
            (current_pos[2] - self._target_pos[2])**2
        )
        
        if dist_to_target < self.WAYPOINT_REACH_DIST:
            print(f"[NaviBot] ✓ Destination reached!")
            self.stop_movement()
            return
        
        # --- ORIGINAL STUCK DETECTION (checks for minimal movement) ---
        if self._last_pos:
            move_dist = sqrt(
                (current_pos[0] - self._last_pos[0])**2 +
                (current_pos[2] - self._last_pos[2])**2
            )
            
            if move_dist < self.STUCK_THRESHOLD * self.UPDATE_INTERVAL:
                self._stuck_timer += self.UPDATE_INTERVAL
                if self._stuck_timer > self.STUCK_TIME:
                    print(f"[NaviBot] ⚠ Stuck detected (no movement), recalculating path")
                    self._path = []
                    self._stuck_timer = 0.0
            else:
                self._stuck_timer = 0.0
        
        self._last_pos = current_pos
        # --- END ORIGINAL STUCK DETECTION ---
        
        # Calculate path if needed
        need_path = (
            len(self._path) == 0 or
            self._path_index >= len(self._path) or
            (self._last_path_calc_pos and
             sqrt((current_pos[0] - self._last_path_calc_pos[0])**2 +
                  (current_pos[2] - self._last_path_calc_pos[2])**2) > self.PATH_RECALC_DIST)
        )
        
        if need_path:
            self._path = self._find_path(current_pos, self._target_pos)
            self._path_index = 0
            self._last_path_calc_pos = current_pos
            
            if not self._path:
                print(f"[NaviBot] ⏸ No path available")
                self._set_movement(0, 0)
                self._set_running(False)
                return
        
        # Follow path
        if self._path_index >= len(self._path):
            self._set_movement(0, 0)
            self._set_running(False)
            return
        
        waypoint = self._path[self._path_index]
        
        # Calculate distance to current waypoint (squared is faster)
        dist_sq_to_wp = (current_pos[0] - waypoint[0])**2 + \
                        (current_pos[1] - waypoint[1])**2 + \
                        (current_pos[2] - waypoint[2])**2
        
        # --- WAYPOINT PROGRESS CHECK (solves infinite wall-walking) ---
        if dist_sq_to_wp > self._last_wp_dist_sq:
            self._no_progress_timer += self.UPDATE_INTERVAL
        else:
            self._no_progress_timer = 0.0
            
        self._last_wp_dist_sq = dist_sq_to_wp
        
        if self._no_progress_timer > self.NO_PROGRESS_TIME:
            print(f"[NaviBot] 🛑 No progress to waypoint for {self.NO_PROGRESS_TIME}s. Forcing repath.")
            self._path = []
            self._no_progress_timer = 0.0
            self._last_wp_dist_sq = float('inf')
            return # Skip movement logic this cycle
            
        # --- END PROGRESS CHECK ---
        
        # Get actual distance for movement logic
        dist_to_wp = sqrt(dist_sq_to_wp) 

        # --- SHARP TURN / WAYPOINT ADVANCE LOGIC (Dot Product) ---
        should_advance = False
        
        # 1. Fallback: If bot is close
        if dist_to_wp < self.WAYPOINT_REACH_DIST:
            should_advance = True
            
        # 2. Main Check: Directional Overshoot (Dot Product)
        if self._path_index > 0:
            prev_waypoint = self._path[self._path_index - 1]
            
            path_vec_x = waypoint[0] - prev_waypoint[0]
            path_vec_z = waypoint[2] - prev_waypoint[2]
            
            bot_rel_x = current_pos[0] - waypoint[0]
            bot_rel_z = current_pos[2] - waypoint[2]
            
            dot_product = path_vec_x * bot_rel_x + path_vec_z * bot_rel_z
            
            if dot_product > 0.1: 
                should_advance = True
        
        
        if should_advance:
            # --- NEW: VELOCITY CHECK FOR SHARP TURNS (Momentum Fix) ---
            vx, vy, vz = self.node.velocity
            horizontal_vel_sq = vx**2 + vz**2
            
            if horizontal_vel_sq > self.MAX_TURN_VELOCITY**2:
                # Bot is moving too fast into a turn, force a temporary stop
                self._set_movement(0, 0)
                self._set_running(False)
                print(f"[NaviBot] 🐌 Decelerating for turn: Vel={sqrt(horizontal_vel_sq):.1f}")
                
                # We do NOT advance the waypoint here, we wait for the next cycle
                # once the bot has slowed down.
                return 
            # --- END VELOCITY CHECK ---
            
            # If velocity is safe, advance the waypoint
            self._path_index += 1
            if self._path_index >= len(self._path):
                return
            waypoint = self._path[self._path_index]
        
        # Calculate movement direction (2D on X-Z plane)
        dx = waypoint[0] - current_pos[0]
        dz = waypoint[2] - current_pos[2]
        dist_2d = sqrt(dx**2 + dz**2)
        
        if dist_2d > 0.01:
            # Normalize direction
            move_x = dx / dist_2d
            move_z = dz / dist_2d
            
            self._set_movement(move_x, move_z)
            self._set_running(True)
        else:
            self._set_movement(0, 0)
            self._set_running(False)


# ==================== USAGE EXAMPLE ====================

def spawn_navibot_test():
    """
    Example usage - spawn a NaviBot and make it navigate to a point.
    
    Usage in BombSquad console:
    >>> from navibot import spawn_navibot_test
    >>> spawn_navibot_test()
    """
    
    # Create bot at spawn position
    bot = NaviBot(
        position=(0, 5, 0),
        color=(0.3, 0.3, 1.0),
        highlight=(0.7, 0.7, 1.0),
        character='Kronk'
    )
    
    # Command bot to navigate to a point
    # (adjust coordinates based on your map)
    bot.move_to_point(10, 5, -5)
    
    print("[Test] NaviBot spawned and commanded to move")
    
    return bot
