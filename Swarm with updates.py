import pygame
import random
import math
import sys
from collections import deque
import time
import folium
import webbrowser

# =========================================================
# CONFIG
# =========================================================
WIDTH, HEIGHT = 1400, 800
PANEL_WIDTH = 440
OCEAN_WIDTH = WIDTH - PANEL_WIDTH
GLOBAL_AUTO_MODE = False

FPS = 60

# =========================================================
# BATTERY & ENERGY PARAMETERS
# =========================================================
BATTERY_CAPACITY_WH        = 168.0
MAX_BATTERY_WH             = 168.0
MOVEMENT_POWER_W           = 50.0
COLLECTION_POWER_W         = 100.0
IDLE_POWER_W               = 5.0
CHARGING_POWER_W           = 120.0
OVERHEAD_FACTOR            = 1.15
LOW_BATTERY_THRESHOLD      = 10.0   # was 20 — lowered so robots work past 50%
CRITICAL_BATTERY_THRESHOLD = 5.0
SAFETY_MARGIN_WH           = 0.5    # was 5.0 — was blocking pickups below 50%
BATTERY_VOLTAGE            = 12.0
BATTERY_MAH                = int((BATTERY_CAPACITY_WH / BATTERY_VOLTAGE) * 1000)

# =========================================================
# DETECTION / CLASSIFICATION CONFIG
# =========================================================
DETECTION_THRESHOLD      = 0.55   # Confidence above this → collect
POLLUTION_TYPES          = ["plastic", "oil", "debris"]
OBSTACLE_TYPES           = ["boat", "rock", "log", "wall"]

# RL Reward table (modular — extend as needed)
REWARD_TABLE = {
    "correct_collect":      +10,
    "collect_obstacle":      -5,
    "wrong_classification":  -3,
    "avoided_obstacle":      +1,
}

# =========================================================
# ECODOT CONFIG
# =========================================================
ECODOT_CAPACITY  = 100          # % full
ECODOT1_POS      = (OCEAN_WIDTH // 4,       HEIGHT // 2)
ECODOT2_POS      = (OCEAN_WIDTH * 3 // 4,   HEIGHT // 2)
OILTANK_POS      = (OCEAN_WIDTH // 2,        HEIGHT - 100)  # bottom-centre of ocean
OILTANK_CAPACITY = 100

# =========================================================
# COLORS
# =========================================================
BG            = (11, 20, 38)
PANEL         = (18, 28, 45)
CARD          = (30, 45, 72)
CARD_HI       = (42, 65, 105)
TEXT          = (220, 240, 255)
TEXT_DARK     = (10, 20, 40)
MUTED         = (180, 200, 220)
BTN           = (70, 120, 180)
BTN_HOVER     = (100, 160, 230)
BTN_ACTIVE    = (90, 140, 200)
ACCENT        = (0, 230, 200)
SHADOW        = (5, 10, 15)
BORDER        = (80, 110, 150)
SELECTED      = (150, 200, 255)
HIGHLIGHT     = (120, 160, 220)

ROBOT_IDLE      = (0, 220, 150)
ROBOT_WORK      = (255, 200, 50)
ROBOT_DUMP      = (255, 100, 100)
ROBOT_CHARGING  = (80, 160, 255)
ROBOT_RETURN    = (255, 140, 0)
ROBOT_AVOID     = (200, 80, 200)

PLASTIC_COLOR   = (255, 120, 120)
OIL_COLOR       = (160, 80,  160)
DEBRIS_COLOR    = (200, 150,  60)
BOAT_COLOR      = (180, 180, 200)
ROCK_COLOR      = (130, 130, 150)
LOG_COLOR       = (160, 120,  80)
WALL_COLOR      = (200, 200, 220)
OBSTACLE_COLOR  = (180, 180, 200)

# Fallback aliases used by WaterObject.color property
POLLUTION_COLOR = PLASTIC_COLOR   # generic fallback for unknown pollution types

DUMP_COLOR      = (120, 255, 180)
ECODOT2_COLOR   = (80,  200, 255)
OILTANK_COLOR   = (255, 180,   0)   # amber -- dedicated oil container
TRAIL           = (100, 150, 220)

GRADIENT_TOP    = (16, 26, 43)
GRADIENT_BOTTOM = (11, 19, 32)

# =========================================================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("HYDROSWARM FLEET — Marine Autonomous Swarm System")
clock = pygame.time.Clock()

FONT       = pygame.font.SysFont("consolas", 13)
FONT_BIG   = pygame.font.SysFont("consolas", 20, bold=True)
FONT_HUGE  = pygame.font.SysFont("consolas", 26, bold=True)
FONT_SMALL = pygame.font.SysFont("consolas", 11)
FONT_TINY  = pygame.font.SysFont("consolas", 9)

# =========================================================
TOTAL_POLLUTION   = 0
DISPOSED_POLLUTION = 0
SELECTED_ROBOT    = None
SELECTED_POLLUTION = None
ALERT_MESSAGE     = ""
ALERT_TIME        = 0
START_TIME        = time.time()

# =========================================================
# RICH STATE DATA
# =========================================================
COASTAL_STATES = {
    "Gujarat":            {"pollution": 145, "locations": ["Kandla","Mundra","Jamnagar","Okha","Dwarka"],         "industries": 28, "marine_life": "High",      "cleanup": 35},
    "Maharashtra":        {"pollution": 189, "locations": ["Mumbai","Ratnagiri","Sindhudurg","Alibag"],            "industries": 42, "marine_life": "Very High",  "cleanup": 28},
    "Goa":                {"pollution":  78, "locations": ["Panaji","Vasco","Margao","Calangute"],                  "industries": 15, "marine_life": "Moderate",   "cleanup": 52},
    "Karnataka":          {"pollution": 112, "locations": ["Mangalore","Karwar","Udupi"],                          "industries": 21, "marine_life": "High",       "cleanup": 41},
    "Kerala":             {"pollution": 156, "locations": ["Kochi","Kollam","Kozhikode","Alappuzha"],              "industries": 25, "marine_life": "High",       "cleanup": 38},
    "Tamil Nadu":         {"pollution": 203, "locations": ["Chennai","Tuticorin","Rameswaram","Ennore"],           "industries": 48, "marine_life": "Critical",   "cleanup": 22},
    "Andhra Pradesh":     {"pollution": 134, "locations": ["Visakhapatnam","Kakinada","Machilipatnam"],            "industries": 31, "marine_life": "High",       "cleanup": 33},
    "Odisha":             {"pollution": 167, "locations": ["Paradip","Gopalpur","Puri","Chandipur"],               "industries": 35, "marine_life": "Very High",  "cleanup": 29},
    "West Bengal":        {"pollution": 198, "locations": ["Kolkata","Haldia","Digha","Sundarbans"],               "industries": 44, "marine_life": "Critical",   "cleanup": 24},
    "Puducherry":         {"pollution":  92, "locations": ["Puducherry","Karaikal"],                               "industries": 12, "marine_life": "Moderate",   "cleanup": 45},
    "Daman and Diu":      {"pollution":  68, "locations": ["Daman","Diu"],                                         "industries":  8, "marine_life": "Moderate",   "cleanup": 58},
    "Lakshadweep":        {"pollution":  45, "locations": ["Kavaratti","Agatti"],                                  "industries":  3, "marine_life": "Low",        "cleanup": 75},
    "Andaman and Nicobar":{"pollution":  52, "locations": ["Port Blair","Havelock"],                               "industries":  5, "marine_life": "Low",        "cleanup": 68},
}

NON_COASTAL_STATES = {
    "Jammu & Kashmir": {"capital": "Srinagar / Jammu", "population": "12.5M", "area": "42,241 km²"},
    "Ladakh":          {"capital": "Leh",              "population": "0.3M",  "area": "59,146 km²"},
    "Himachal Pradesh":{"capital": "Shimla",           "population": "6.9M",  "area": "55,673 km²"},
    "Punjab":          {"capital": "Chandigarh",       "population": "27.7M", "area": "50,362 km²"},
    "Chandigarh":      {"capital": "Chandigarh",       "population": "1.1M",  "area": "114 km²"},
    "Uttarakhand":     {"capital": "Dehradun",         "population": "10.1M", "area": "53,483 km²"},
    "Haryana":         {"capital": "Chandigarh",       "population": "25.4M", "area": "44,212 km²"},
    "Delhi":           {"capital": "New Delhi",        "population": "16.8M", "area": "1,484 km²"},
    "Rajasthan":       {"capital": "Jaipur",           "population": "68.5M", "area": "342,239 km²"},
    "Uttar Pradesh":   {"capital": "Lucknow",          "population": "199.6M","area": "240,928 km²"},
    "Bihar":           {"capital": "Patna",            "population": "104.1M","area": "94,163 km²"},
    "Jharkhand":       {"capital": "Ranchi",           "population": "33.0M", "area": "79,716 km²"},
    "Chhattisgarh":    {"capital": "Raipur",           "population": "25.5M", "area": "135,192 km²"},
    "Madhya Pradesh":  {"capital": "Bhopal",           "population": "72.6M", "area": "308,252 km²"},
    "Telangana":       {"capital": "Hyderabad",        "population": "35.2M", "area": "112,077 km²"},
    "Assam":           {"capital": "Dispur",           "population": "31.2M", "area": "78,438 km²"},
}

# =========================================================
# FOLIUM MAP
# =========================================================
def draw_india_map():
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles='CartoDB positron')
    state_centers = {
        "Gujarat": [22.3, 71.6], "Maharashtra": [19.0, 76.0], "Goa": [15.4, 73.9],
        "Karnataka": [14.8, 75.4], "Kerala": [10.0, 76.3], "Tamil Nadu": [11.0, 78.7],
        "Andhra Pradesh": [16.0, 80.0], "Odisha": [20.3, 85.8], "West Bengal": [22.9, 88.0],
        "Puducherry": [11.9, 79.8], "Daman and Diu": [20.4, 72.8],
        "Lakshadweep": [10.6, 72.6], "Andaman and Nicobar": [11.7, 92.7],
    }
    for state, data in COASTAL_STATES.items():
        center = state_centers.get(state, [20.0, 80.0])
        pollution = data["pollution"]
        color = "#d32f2f" if pollution > 180 else "#f57c00" if pollution > 130 else "#fbc02d" if pollution > 80 else "#388e3c"
        status = "Critical" if pollution > 180 else "High" if pollution > 130 else "Moderate" if pollution > 80 else "Low"
        popup_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:300px;">
          <h3 style="margin:0;color:#1565c0;border-bottom:1px solid #ddd;padding-bottom:5px;">{state}</h3>
          <p><b>Pollution Level:</b> {pollution} units | <b>Status:</b> {status}</p>
          <p><b>Industries:</b> {data["industries"]} | <b>Marine Life:</b> {data["marine_life"]}</p>
          <p><b>Cleanup:</b> {data["cleanup"]}% | <b>Areas:</b> {', '.join(data["locations"])}</p>
        </div>"""
        folium.CircleMarker(location=center, radius=max(8, pollution//12), color=color,
                            fill=True, fill_color=color, fill_opacity=0.7,
                            popup=folium.Popup(popup_html, max_width=320)).add_to(m)
    try:
        m.save("india_coastal_pollution_map.html")
        webbrowser.open("india_coastal_pollution_map.html")
    except Exception as e:
        print("Map error:", e)

# =========================================================
# UTILITIES
# =========================================================
def clamp(v, a, b):
    return max(a, min(b, v))

def dist(a, b, c, d):
    return math.hypot(a - c, b - d)

def check_overlap(x, y, radius, objects, exclude=None):
    for obj in objects:
        if obj == exclude:
            continue
        if dist(x, y, obj.x, obj.y) < (radius + obj.radius + 15):
            return True
    return False

# =========================================================
# MODULE 1: DETECTION & CLASSIFICATION SYSTEM
# =========================================================
class DetectionSystem:
    """
    Simulated AI object detection module.
    Classifies water objects as pollution (collectable) or obstacles (avoidable).
    Expandable for real ML models or RL reward integration.
    """

    # Per-type base confidence ranges (simulates sensor+AI variance)
    _CONFIDENCE_PROFILE = {
        "plastic": (0.70, 0.98),
        "oil":     (0.60, 0.92),
        "debris":  (0.55, 0.90),
        "boat":    (0.75, 0.99),
        "rock":    (0.80, 0.99),
        "log":     (0.65, 0.95),
        "wall":    (0.85, 0.99),
    }

    @staticmethod
    def simulate_detection(water_object):
        """
        Simulate AI classification of a WaterObject.
        Returns: dict with keys: detected_type, confidence, decision, reward_hint
        """
        true_type = water_object.obj_type
        lo, hi    = DetectionSystem._CONFIDENCE_PROFILE.get(true_type, (0.50, 0.85))
        confidence = random.uniform(lo, hi)

        # Occasionally simulate misclassification (sensor noise)
        misclassify = random.random() < 0.06   # 6% error rate
        if misclassify:
            all_types = POLLUTION_TYPES + OBSTACLE_TYPES
            all_types = [t for t in all_types if t != true_type]
            detected_type = random.choice(all_types)
        else:
            detected_type = true_type

        is_pollution = detected_type in POLLUTION_TYPES
        is_collectible = is_pollution and confidence >= DETECTION_THRESHOLD

        # Reward hint for RL integration
        if is_collectible and true_type in POLLUTION_TYPES:
            reward_hint = REWARD_TABLE["correct_collect"]
        elif is_collectible and true_type in OBSTACLE_TYPES:
            reward_hint = REWARD_TABLE["collect_obstacle"]
        elif misclassify:
            reward_hint = REWARD_TABLE["wrong_classification"]
        else:
            reward_hint = REWARD_TABLE["avoided_obstacle"]

        return {
            "detected_type": detected_type,
            "confidence":    round(confidence, 3),
            "decision":      "COLLECT" if is_collectible else "AVOID",
            "reward_hint":   reward_hint,
            "misclassified": misclassify,
        }

    @staticmethod
    def classify_batch(water_objects):
        """Run detection on a list of WaterObjects. Returns list of result dicts."""
        return [DetectionSystem.simulate_detection(o) for o in water_objects]


# =========================================================
# MODULE 2: WATER OBJECT BASE CLASS
# =========================================================
class WaterObject:
    """
    Unified base class for all water-surface objects.
    Replaces the old Pollution + Obstacle classes with a rich,
    typed, AI-detectable structure.
    """
    _id_counter = 0

    # Visual color map
    TYPE_COLORS = {
        "plastic": PLASTIC_COLOR,
        "oil":     OIL_COLOR,
        "debris":  DEBRIS_COLOR,
        "boat":    BOAT_COLOR,
        "rock":    ROCK_COLOR,
        "log":     LOG_COLOR,
        "wall":    WALL_COLOR,
    }

    TYPE_SYMBOLS = {
        "plastic": "♻", "oil": "◉", "debris": "★",
        "boat": "⛵", "rock": "▲", "log": "═", "wall": "█",
    }

    def __init__(self, obj_type, x=None, y=None, size=None, existing_objects=None):
        self.obj_id   = WaterObject._id_counter
        WaterObject._id_counter += 1

        self.obj_type = obj_type
        self.is_pollution = obj_type in POLLUTION_TYPES
        self.size = size if size is not None else round(random.uniform(0.3, 1.0), 2)

        # Radius derived from size
        if self.is_pollution:
            self.radius = int(12 + self.size * 16)   # 12–28 px
        else:
            self.radius = int(20 + self.size * 20)   # 20–40 px

        # Placement
        existing = existing_objects or []
        max_attempts = 100
        if x is None or y is None:
            for _ in range(max_attempts):
                self.x = random.randint(70, OCEAN_WIDTH - 70)
                self.y = random.randint(70, HEIGHT - 70)
                if not check_overlap(self.x, self.y, self.radius, existing):
                    break
        else:
            self.x, self.y = x, y
            for _ in range(max_attempts):
                if not check_overlap(self.x, self.y, self.radius, existing, exclude=self):
                    break
                self.x += random.randint(-20, 20)
                self.y += random.randint(-20, 20)
                self.x = clamp(self.x, 50, OCEAN_WIDTH - 50)
                self.y = clamp(self.y, 50, HEIGHT - 50)

        # Pollution-specific state
        self.active   = True
        self.assigned = None     # assigned robot (pollution only)
        self.pulse    = 0.0

        # Last detection result cache (updated by DetectionSystem)
        self.last_detection = None

        # For display purposes (legacy compat)
        self.id = self.obj_id
        self.vx = 0
        self.vy = 0

        if self.is_pollution:
            global TOTAL_POLLUTION
            TOTAL_POLLUTION += 1

    @property
    def color(self):
        return self.TYPE_COLORS.get(self.obj_type, POLLUTION_COLOR if self.is_pollution else OBSTACLE_COLOR)

    @property
    def symbol(self):
        return self.TYPE_SYMBOLS.get(self.obj_type, "?")

    def run_detection(self):
        """Trigger AI classification on this object. Caches result."""
        self.last_detection = DetectionSystem.simulate_detection(self)
        return self.last_detection

    def update(self):
        pass

    def draw(self):
        if not self.active:
            return
        self.pulse = (self.pulse + 0.08) % (2 * math.pi)

        if self.is_pollution:
            # Animated glow ring
            glow_r = self.radius + int(3 * math.sin(self.pulse))
            pygame.draw.circle(screen, self.color, (self.x, self.y), glow_r, 1)
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius, 2)

            # Type label
            label = f"{self.symbol}{self.obj_type[:3].upper()}#{self.obj_id}"
            screen.blit(FONT_TINY.render(label, True, self.color),
                        (self.x - 18, self.y - self.radius - 13))

            # Confidence badge if detected recently
            if self.last_detection:
                conf  = self.last_detection["confidence"]
                badge_color = (0, 200, 100) if self.last_detection["decision"] == "COLLECT" else (220, 60, 60)
                conf_surf = FONT_TINY.render(f"{conf:.0%}", True, badge_color)
                screen.blit(conf_surf, (self.x - 10, self.y + self.radius + 2))

            if self == SELECTED_POLLUTION:
                pygame.draw.circle(screen, SELECTED, (self.x, self.y), self.radius + 6, 2)

        else:
            # Obstacle drawing
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
            pygame.draw.circle(screen, BORDER, (self.x, self.y), self.radius, 2)
            sym_surf = FONT_SMALL.render(self.symbol, True, TEXT_DARK)
            screen.blit(sym_surf, (self.x - sym_surf.get_width() // 2,
                                   self.y - sym_surf.get_height() // 2))
            # Type label above
            lbl = FONT_TINY.render(self.obj_type.upper(), True, self.color)
            screen.blit(lbl, (self.x - lbl.get_width() // 2, self.y - self.radius - 12))


# Thin wrappers for backward-compatible spawning
def make_pollution(existing_objects=None, obj_type=None):
    t = obj_type or random.choice(POLLUTION_TYPES)
    return WaterObject(t, existing_objects=existing_objects)

def make_obstacle(x, y, existing_objects=None, obj_type=None):
    t = obj_type or random.choice(OBSTACLE_TYPES)
    return WaterObject(t, x=x, y=y, existing_objects=existing_objects)


# =========================================================
# MODULE 3: DUAL ECODOT MANAGEMENT SYSTEM
# =========================================================
class EcoDot:
    """
    Fixed-position pollution dump station.
    Coordinates are set at init and NEVER change, even after cleaning.
    """
    def __init__(self, dot_id, x, y, status="Active"):
        self.dot_id    = dot_id
        self.name      = f"EcoDot_{dot_id}"

        # ── Fixed coordinates (immutable) ──────────────────────
        self._origin_x = x
        self._origin_y = y
        self.x         = x
        self.y         = y
        # ────────────────────────────────────────────────────────

        self.radius    = 45
        self.capacity  = ECODOT_CAPACITY   # 100 %
        self.load      = 0.0               # current fill %
        self.target_load = 0.0
        self.animation_progress = 0.0

        # State flags
        self.status    = status            # "Active" | "Standby" | "Full"

        # Convenience booleans (used by robots / notification system)
        self.is_full   = False
        self.is_active = (status == "Active")
        self.is_standby= (status == "Standby")

    # ── State helpers ─────────────────────────────────────
    def set_active(self):
        self.status     = "Active"
        self.is_active  = True
        self.is_standby = False

    def set_standby(self):
        self.status     = "Standby"
        self.is_active  = False
        self.is_standby = True

    def set_full(self):
        self.status     = "Full"
        self.is_full    = True
        self.is_active  = False
        self.is_standby = False

    def clean(self):
        """Reset load. Coordinates are NOT touched."""
        self.load        = 0.0
        self.target_load = 0.0
        self.is_full     = False

    def add_pollution(self, amount=10):
        """Deposit collected pollution. Returns True if this deposit caused it to become full."""
        if self.is_full or not self.is_active:
            return False
        self.target_load = min(self.capacity, self.load + amount)
        if self.target_load >= self.capacity:
            self.set_full()
            return True           # ← full event
        return False

    def can_accept(self):
        return self.is_active and not self.is_full

    def update(self):
        if self.load < self.target_load:
            self.load = min(self.target_load, self.load + 0.5)
        self.animation_progress = (self.animation_progress + 0.05) % (2 * math.pi)

    def draw(self):
        # Colour depends on status
        if self.status == "Full":
            ring_color = (255, 80, 80)
        elif self.status == "Standby":
            ring_color = ECODOT2_COLOR
        else:
            ring_color = DUMP_COLOR

        pygame.draw.circle(screen, ring_color, (self.x, self.y), self.radius, 3)

        # Fill visualisation
        if self.load > 0:
            fill_r = max(1, int((self.load / self.capacity) * (self.radius - 5)))
            ratio  = self.load / self.capacity
            red_v  = int(ratio * 155)   # 0–155, so 100+red_v stays ≤ 255
            fill_c = (
                min(255, max(0, 100 + red_v)),
                min(255, max(0, 180 - red_v)),
                min(255, max(0, 100 - red_v)),
            )
            pygame.draw.circle(screen, fill_c, (self.x, self.y), fill_r)
            wave   = math.sin(self.animation_progress) * 2
            pygame.draw.circle(screen, ring_color, (self.x, int(self.y + wave)), fill_r, 1)

        # Percentage text
        pct_surf = FONT_BIG.render(f"{int(self.load)}%", True, TEXT if self.load < 60 else TEXT_DARK)
        screen.blit(pct_surf, (self.x - pct_surf.get_width() // 2, self.y - 12))

        # Name + status badge
        name_surf = FONT.render(self.name, True, ring_color)
        screen.blit(name_surf, (self.x - name_surf.get_width() // 2, self.y + 26))

        status_color = (255, 80, 80) if self.status == "Full" else \
                       (80, 200, 255) if self.status == "Standby" else (0, 200, 100)
        st_surf = FONT_TINY.render(f"[{self.status.upper()}]", True, status_color)
        screen.blit(st_surf, (self.x - st_surf.get_width() // 2, self.y + 38))


class EcoDotManager:
    """
    Smart Dual EcoDot Manager.

    STATE MACHINE:
      Normal          → robots dump into EcoDot_1
      EcoDot_1 full   → show CLEAN DOT-1 button; robots automatically use EcoDot_2; work continues
      EcoDot_1 cleaned→ EcoDot_1 becomes primary again immediately
      EcoDot_2 full   → show CLEAN DOT-2 button; robots WAIT (hold position); no new collection
      Either cleaned  → resume dumping into whichever dot is available
    """
    def __init__(self):
        self.dot1 = EcoDot(1, *ECODOT1_POS, status="Active")
        self.dot2 = EcoDot(2, *ECODOT2_POS, status="Standby")

        # Public state flags
        self.eco1_full   = False
        self.eco2_full   = False
        self.eco1_active = True
        self.eco2_active = False

        # dump_paused = True only when the CURRENTLY ACTIVE dot is full and
        # no other dot can accept (i.e. both are full at the same time).
        self.dump_paused = False

        # Which dots need cleaning (drives UI button visibility)
        self.need_clean_dot1 = False
        self.need_clean_dot2 = False

        self._notifications = deque()

    # ── Routing ───────────────────────────────────────────
    def best_dump_target(self, robot_x=0, robot_y=0):
        """
        Return best EcoDot for dumping right now.
        Priority: EcoDot_1 first if available, then EcoDot_2.
        Returns None only if both are full (robots must wait).
        """
        if self.dot1.can_accept():
            return self.dot1
        if self.dot2.can_accept():
            return self.dot2
        return None  # both full — robots hold position

    # ── Dump recording ────────────────────────────────────
    def record_dump(self, ecodot, amount=10):
        """Called by a robot after reaching an EcoDot and dumping."""
        became_full = ecodot.add_pollution(amount)
        if not became_full:
            return

        if ecodot is self.dot1:
            self.eco1_full        = True
            self.eco1_active      = False
            self.need_clean_dot1  = True
            # Immediately activate EcoDot_2 so work continues without pause
            self.dot2.set_active()
            self.eco2_active = True
            self._notify(
                "⚠ EcoDot 1 FULL — Please clean it. EcoDot 2 is now ACTIVE.",
                level="warn"
            )
            # No dump_paused — EcoDot_2 is now accepting

        elif ecodot is self.dot2:
            self.eco2_full        = True
            self.eco2_active      = False
            self.need_clean_dot2  = True
            # Only pause if EcoDot_1 is also still full
            if self.eco1_full:
                self.dump_paused = True
                self._notify(
                    "🚨 EcoDot 2 FULL — Please clean a EcoDot. Robots are waiting.",
                    level="critical"
                )
            else:
                # EcoDot_1 was already cleaned; it can accept again
                self.dot1.set_active()
                self.eco1_active = True
                self._notify(
                    "⚠ EcoDot 2 FULL — Robots redirected back to EcoDot 1.",
                    level="warn"
                )

    # ── Individual clean actions ───────────────────────────
    def clean_dot1(self):
        """
        User cleans EcoDot_1.
        - Resets its load.
        - If EcoDot_2 is currently active and not full → EcoDot_1 goes Standby.
        - If EcoDot_2 is full (paused state) → EcoDot_1 becomes primary again; resume.
        - Coordinates NEVER change.
        """
        self.dot1.clean()
        self.eco1_full       = False
        self.need_clean_dot1 = False

        if self.eco2_full:
            # EcoDot_2 is full and was waiting; EcoDot_1 now takes over → resume
            self.dot1.set_active()
            self.eco1_active  = True
            self.dump_paused  = False
            self._notify("✓ EcoDot 1 cleaned — Now PRIMARY. Robots resuming.", level="ok")
        else:
            # EcoDot_2 is still active and healthy; EcoDot_1 goes standby
            self.dot1.set_standby()
            self.eco1_active = False
            self._notify("✓ EcoDot 1 cleaned — Standby (EcoDot 2 still active).", level="ok")

    def clean_dot2(self):
        """
        User cleans EcoDot_2.
        - Resets its load.
        - EcoDot_2 goes Standby (EcoDot_1 is primary unless it is also full).
        - Coordinates NEVER change.
        """
        self.dot2.clean()
        self.eco2_full       = False
        self.need_clean_dot2 = False

        if self.eco1_full:
            # EcoDot_1 still full; keep EcoDot_2 active to continue work
            self.dot2.set_active()
            self.eco2_active = True
            self.dump_paused = False
            self._notify("✓ EcoDot 2 cleaned — Remains ACTIVE (EcoDot 1 still full).", level="ok")
        else:
            # EcoDot_1 is healthy; EcoDot_2 goes back to standby
            self.dot2.set_standby()
            self.eco2_active = False
            if self.dump_paused:
                self.dump_paused = False
            self._notify("✓ EcoDot 2 cleaned — Back to STANDBY.", level="ok")

    # ── Update / Draw ─────────────────────────────────────
    def update(self):
        self.dot1.update()
        self.dot2.update()

    def draw(self):
        self.dot1.draw()
        self.dot2.draw()

    # ── Notifications ─────────────────────────────────────
    def _notify(self, message, level="info"):
        self._notifications.append({"msg": message, "level": level, "ts": time.time()})
        print(f"[EcoDotManager | {level.upper()}] {message}")

    def poll_notification(self):
        return self._notifications.popleft() if self._notifications else None

    @property
    def both_full(self):
        return self.eco1_full and self.eco2_full

    @property
    def available_dots(self):
        return [d for d in (self.dot1, self.dot2) if d.can_accept()]


# =========================================================
# OIL TANK — dedicated container for oil-type pollution only
# =========================================================
class OilTank:
    """
    Dedicated collection vessel for OIL pollution.
    Robots carrying oil bypass the EcoDots and dump here instead.
    Has its own capacity / full state and a DRAIN button when full.
    Coordinates are fixed at init — never relocated.
    """
    def __init__(self):
        self._origin_x, self._origin_y = OILTANK_POS
        self.x, self.y = self._origin_x, self._origin_y
        self.radius   = 42
        self.capacity = OILTANK_CAPACITY
        self.load     = 0.0
        self.target_load = 0.0
        self.is_full  = False
        self.need_drain = False
        self.animation_progress = 0.0
        self._notifications = deque()

    # ── API ───────────────────────────────────────────────
    def can_accept(self):
        return not self.is_full

    def add_oil(self, amount=10):
        """Returns True if this deposit caused it to become full."""
        if self.is_full:
            return False
        self.target_load = min(self.capacity, self.load + amount)
        if self.target_load >= self.capacity:
            self.is_full   = True
            self.need_drain = True
            self._notify("⚠ OilTank FULL — Please drain it!")
            return True
        return False

    def drain(self):
        """User drains the tank. Position never changes."""
        self.load        = 0.0
        self.target_load = 0.0
        self.is_full     = False
        self.need_drain  = False
        self._notify("✓ OilTank drained and ready.")

    def poll_notification(self):
        return self._notifications.popleft() if self._notifications else None

    def _notify(self, msg):
        self._notifications.append({"msg": msg, "level": "warn", "ts": time.time()})
        print(f"[OilTank] {msg}")

    # ── Update / Draw ─────────────────────────────────────
    def update(self):
        if self.load < self.target_load:
            self.load = min(self.target_load, self.load + 0.5)
        self.animation_progress = (self.animation_progress + 0.04) % (2 * math.pi)

    def draw(self):
        ring_color = (255, 60, 60) if self.is_full else OILTANK_COLOR

        # Outer hexagon shape to distinguish from circular EcoDots
        cx, cy = self.x, self.y
        r = self.radius
        pts = [(int(cx + r * math.cos(math.pi / 6 + i * math.pi / 3)),
                int(cy + r * math.sin(math.pi / 6 + i * math.pi / 3)))
               for i in range(6)]
        pygame.draw.polygon(screen, (20, 18, 12), pts)          # dark fill
        pygame.draw.polygon(screen, ring_color, pts, 3)         # coloured border

        # Oil fill level
        if self.load > 0:
            fill_ratio = self.load / self.capacity
            fill_r     = max(1, int(fill_ratio * (r - 8)))
            # Dark amber oil colour that deepens as it fills
            amber = (
                min(255, max(0, int(180 + 60 * fill_ratio))),
                min(255, max(0, int(120 - 80 * fill_ratio))),
                0,
            )
            pygame.draw.circle(screen, amber, (cx, cy), fill_r)
            wave = math.sin(self.animation_progress) * 2
            pygame.draw.circle(screen, ring_color, (cx, int(cy + wave)), fill_r, 1)

        # Percentage + label
        pct_surf  = FONT_BIG.render(f"{int(self.load)}%", True,
                                     TEXT_DARK if self.load > 50 else TEXT)
        screen.blit(pct_surf, (cx - pct_surf.get_width() // 2, cy - 12))

        name_surf = FONT.render("OilTank", True, ring_color)
        screen.blit(name_surf, (cx - name_surf.get_width() // 2, cy + 24))

        status_txt = "[FULL]" if self.is_full else "[READY]"
        st_color   = (255, 60, 60) if self.is_full else (0, 200, 100)
        st_surf    = FONT_TINY.render(status_txt, True, st_color)
        screen.blit(st_surf, (cx - st_surf.get_width() // 2, cy + 37))


# =========================================================
# CHARGING DOCK
# =========================================================
class ChargingDock:
    def __init__(self, x=None, y=None):
        self.x      = x if x is not None else 80
        self.y      = y if y is not None else HEIGHT - 80
        self.radius = 28
        self.pulse  = 0

    def draw(self):
        self.pulse = (self.pulse + 0.08) % (2 * math.pi)
        glow = int(self.radius + 5 * math.sin(self.pulse))
        pygame.draw.circle(screen, (40, 80, 160), (self.x, self.y), glow, 1)
        pygame.draw.circle(screen, ROBOT_CHARGING, (self.x, self.y), self.radius, 3)
        label = FONT.render("⚡DOCK", True, ROBOT_CHARGING)
        screen.blit(label, (self.x - label.get_width() // 2, self.y - 8))


# =========================================================
# ROBOT DRAW HELPER
# =========================================================
def draw_robot(screen, x, y, color, size=14):
    body_rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
    pygame.draw.rect(screen, color, body_rect, border_radius=3)
    pygame.draw.rect(screen, (255, 255, 255), body_rect, 1, border_radius=3)
    head_y = y - size // 2 - 3
    pygame.draw.circle(screen, color, (int(x), int(head_y)), size // 4)
    pygame.draw.circle(screen, (255, 255, 255), (int(x - 2), int(head_y)), 1)
    pygame.draw.circle(screen, (255, 255, 255), (int(x + 2), int(head_y)), 1)
    pygame.draw.line(screen, color, (x, head_y - size // 4), (x, head_y - size // 4 - 3), 1)
    pygame.draw.circle(screen, ACCENT, (int(x), int(head_y - size // 4 - 3)), 2)


# =========================================================
# MODULE 4: ROBOT DECISION ENGINE
# =========================================================
class Robot:
    SPEED       = 1.8
    PICK_RADIUS = 18
    AVOID_RADIUS = 20
    AVOID_FORCE  = 1.0

    def __init__(self, rid):
        self.id   = rid
        self.name = f"AquaBot-{rid + 1}"
        self.x = random.randint(80, OCEAN_WIDTH - 80)
        self.y = random.randint(80, HEIGHT - 80)
        self.vx = self.vy = 0
        self.state  = "IDLE"
        self.mode   = "AUTO"
        self.target = None                # WaterObject (pollution only)
        self.manual_target = None
        self.trail  = deque(maxlen=35)
        self.tasks_completed = 0
        self.efficiency      = 0.0
        self.glow_pulse      = 0
        self.radius = 7
        self.stuck_counter   = 0
        self.last_pos        = (self.x, self.y)

        # RL/reward tracking
        self.total_reward    = 0
        self.misclassify_count = 0
        self.collected_type  = None   # tracks what pollution type robot is currently carrying

        # Battery
        self.battery_wh            = BATTERY_CAPACITY_WH
        self.max_battery_wh        = MAX_BATTERY_WH
        self.low_battery_threshold = LOW_BATTERY_THRESHOLD
        self.critical_battery_threshold = CRITICAL_BATTERY_THRESHOLD
        self.total_energy_consumed_wh = 0.0
        self.energy_per_cycle     = 0.0
        self.cycle_start_battery  = BATTERY_CAPACITY_WH
        self.last_update_time     = time.time()

    # ── Battery properties ────────────────────────────────
    @property
    def battery_percentage(self):
        return (self.battery_wh / self.max_battery_wh) * 100.0

    @property
    def battery_color(self):
        pct = self.battery_percentage
        return (0, 200, 80) if pct > 60 else (255, 200, 0) if pct > 30 else (220, 50, 50)

    def estimated_cycles_remaining(self):
        avg = self.energy_per_cycle if self.energy_per_cycle > 0 else 1.5
        return int(self.battery_wh / avg)

    def energy_needed_for_target(self, tx, ty, dock_x, dock_y):
        """
        Realistic Wh estimate: travel to target + collect + travel to dock.
        Uses actual pixel distances at robot speed (pixels/frame * FPS = pixels/sec).
        """
        d_to   = dist(self.x, self.y, tx, ty)
        d_back = dist(tx, ty, dock_x, dock_y)
        speed_pps = self.SPEED * FPS           # pixels per second
        t_go   = d_to   / max(speed_pps, 1.0) # seconds
        t_ret  = d_back / max(speed_pps, 1.0)
        t_col  = 2.0                           # virtual collection time (seconds)
        e = (MOVEMENT_POWER_W * (t_go + t_ret) + COLLECTION_POWER_W * t_col) / 3600.0
        return e * OVERHEAD_FACTOR

    def _drain_battery(self, wh):
        wh = max(0.0, wh)
        self.battery_wh = max(0.0, self.battery_wh - wh)
        self.total_energy_consumed_wh += wh

    # ── Assignment ────────────────────────────────────────
    def assign(self, water_obj):
        if not water_obj.is_pollution:
            return False
        if water_obj.assigned and water_obj.assigned != self:
            water_obj.assigned.cancel_assignment()
        self.mode   = "MANUAL"
        self.target = water_obj
        water_obj.assigned = self
        self.state  = "GOING_TO_POLLUTION"
        return True

    def cancel_assignment(self):
        if self.target:
            if getattr(self.target, "assigned", None) == self:
                self.target.assigned = None
        self.target = None
        self.manual_target = None
        self.collected_type = None
        self.vx = self.vy = 0
        self.state = "IDLE"
        self.mode  = "AUTO"

    def auto_assign(self, water_objects, charging_dock=None):
        """
        MODULE 4: Robot Decision Engine — auto-assign with detection + energy check.
        """
        if self.state != "IDLE" or self.mode == "MANUAL":
            return
        if self.battery_percentage <= self.low_battery_threshold:
            return

        # Only consider active, unassigned pollution objects
        candidates = [o for o in water_objects
                      if o.is_pollution and o.active and o.assigned is None]
        if not candidates:
            return

        dock_x = charging_dock.x if charging_dock else self.x
        dock_y = charging_dock.y if charging_dock else self.y

        viable = []
        for obj in candidates:
            # Run detection before committing
            detection = obj.run_detection()
            if detection["decision"] != "COLLECT":
                # Log misclassification penalty
                if detection["misclassified"]:
                    self.misclassify_count += 1
                    self.total_reward += REWARD_TABLE["wrong_classification"]
                continue
            needed = self.energy_needed_for_target(obj.x, obj.y, dock_x, dock_y)
            if self.battery_wh >= needed + SAFETY_MARGIN_WH:
                viable.append(obj)

        if viable:
            best = min(viable, key=lambda o: dist(self.x, self.y, o.x, o.y))
            self.assign(best)
            self.mode = "AUTO"

    # ── Steering & avoidance ──────────────────────────────
    def steer(self, tx, ty, speed=None):
        if speed is None:
            speed = self.SPEED
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy) + 0.001
        self.vx = (dx / d) * speed
        self.vy = (dy / d) * speed

    def avoid_obstacles(self, obstacles):
        for o in obstacles:
            if o.is_pollution:
                continue                 # never avoid pollution
            d = dist(self.x, self.y, o.x, o.y)
            safe = o.radius + self.radius + 50
            if d < safe:
                away_x = (self.x - o.x) / (d + 0.001)
                away_y = (self.y - o.y) / (d + 0.001)
                strength = self.AVOID_FORCE * (1 - d / safe) * 3
                self.vx += away_x * strength
                self.vy += away_y * strength
                tan_x = -away_y;  tan_y = away_x
                if self.vx * tan_x + self.vy * tan_y < 0:
                    tan_x, tan_y = -tan_x, -tan_y
                self.vx += tan_x * strength * 0.5
                self.vy += tan_y * strength * 0.5

    def update(self, water_objects, ecodot_manager, obstacles_list, charging_dock=None, oil_tank=None):
        global DISPOSED_POLLUTION
        now    = time.time()
        dt_sec = min(now - self.last_update_time, 0.1)
        self.last_update_time = now

        # Dead battery
        if self.battery_wh <= 0:
            self.battery_wh = 0
            self.vx = self.vy = 0
            self.state = "IDLE"
            if self.target and getattr(self.target, "assigned", None) == self:
                self.target.assigned = None
            self.target = None
            return

        # Low battery → return to charge
        if (self.state not in ("RETURN_TO_CHARGING", "CHARGING")
                and self.battery_percentage <= self.low_battery_threshold
                and charging_dock is not None):
            if self.target and getattr(self.target, "assigned", None) == self:
                self.target.assigned = None
            self.target = None
            self.state = "RETURN_TO_CHARGING"
            self.mode  = "AUTO"

        # Charging
        if self.state == "CHARGING" and charging_dock:
            charge_wh = CHARGING_POWER_W * (dt_sec / 3600.0)
            self.battery_wh = min(self.max_battery_wh, self.battery_wh + charge_wh)
            if self.battery_wh >= self.max_battery_wh:
                self.battery_wh = self.max_battery_wh
                self.state = "IDLE"
            self.vx = self.vy = 0
            return

        # ── Stuck detection ────────────────────────────────
        moved = dist(self.x, self.y, self.last_pos[0], self.last_pos[1])
        self.stuck_counter = self.stuck_counter + 1 if moved < 0.4 else 0
        self.last_pos = (self.x, self.y)

        if self.stuck_counter > 18:
            self.stuck_counter = 0
            escape_angle = random.uniform(0, 2 * math.pi)
            near_obs = [o for o in obstacles_list
                        if not o.is_pollution and
                        dist(self.x, self.y, o.x, o.y) < o.radius + self.radius + 70]
            if near_obs:
                avg_x = sum((self.x - o.x) / (dist(self.x, self.y, o.x, o.y) + 0.001) for o in near_obs) / len(near_obs)
                avg_y = sum((self.y - o.y) / (dist(self.x, self.y, o.x, o.y) + 0.001) for o in near_obs) / len(near_obs)
                escape_angle = math.atan2(avg_y, avg_x) + random.uniform(-0.8, 0.8)
            self.vx += math.cos(escape_angle) * 4.0
            self.vy += math.sin(escape_angle) * 4.0
            self.vx *= 0.6;  self.vy *= 0.6

        # ── State machine ─────────────────────────────────
        is_moving = False
        is_collecting = False

        if self.state == "RETURN_TO_CHARGING" and charging_dock:
            self.steer(charging_dock.x, charging_dock.y)
            is_moving = True
            if dist(self.x, self.y, charging_dock.x, charging_dock.y) < charging_dock.radius:
                self.state = "CHARGING"
                self.vx = self.vy = 0

        elif self.state == "GOING_TO_POLLUTION" and self.target:
            self.steer(self.target.x, self.target.y)
            is_moving = True
            if dist(self.x, self.y, self.target.x, self.target.y) < self.PICK_RADIUS:
                # Re-classify at point of collection
                det = self.target.run_detection()
                if det["decision"] == "COLLECT":
                    coll_wh = COLLECTION_POWER_W * (20.0 / 3600.0) * OVERHEAD_FACTOR
                    self._drain_battery(coll_wh)
                    is_collecting = True
                    self.collected_type = self.target.obj_type   # remember what we picked up
                    self.target.active = False
                    self.total_reward += det["reward_hint"]
                    self.state = "GOING_TO_DUMP"
                else:
                    # Reclassified as obstacle — abort
                    self.total_reward += REWARD_TABLE["wrong_classification"]
                    if getattr(self.target, "assigned", None) == self:
                        self.target.assigned = None
                    self.target = None
                    self.collected_type = None
                    self.state = "IDLE"

        elif self.state == "GOING_TO_DUMP":
            # Decide destination: oil → OilTank, everything else → EcoDot
            carrying_oil = (self.collected_type == "oil")

            if carrying_oil:
                # Oil destination
                if oil_tank is None or not oil_tank.can_accept():
                    # OilTank full or not available — hold position
                    self.vx *= 0.8; self.vy *= 0.8
                else:
                    self.steer(oil_tank.x, oil_tank.y)
                    is_moving = True
                    if dist(self.x, self.y, oil_tank.x, oil_tank.y) < oil_tank.radius:
                        DISPOSED_POLLUTION += 1
                        oil_tank.add_oil(amount=10)
                        self.energy_per_cycle = self.cycle_start_battery - self.battery_wh
                        self.total_energy_consumed_wh += self.energy_per_cycle
                        self.cycle_start_battery = self.battery_wh
                        self.target = None
                        self.collected_type = None
                        self.state  = "IDLE"
                        self.tasks_completed += 1
                        self.efficiency = self.tasks_completed / max(1, (time.time() - START_TIME) / 60.0)
            else:
                # Plastic / debris destination — EcoDots
                dump_target = ecodot_manager.best_dump_target(self.x, self.y)
                if dump_target is None:
                    # Both EcoDots full — hold position
                    self.vx *= 0.8; self.vy *= 0.8
                else:
                    self.steer(dump_target.x, dump_target.y)
                    is_moving = True
                    if dist(self.x, self.y, dump_target.x, dump_target.y) < dump_target.radius:
                        DISPOSED_POLLUTION += 1
                        ecodot_manager.record_dump(dump_target, amount=10)
                        self.energy_per_cycle = self.cycle_start_battery - self.battery_wh
                        self.total_energy_consumed_wh += self.energy_per_cycle
                        self.cycle_start_battery = self.battery_wh
                        self.target = None
                        self.collected_type = None
                        self.state  = "IDLE"
                        self.tasks_completed += 1
                        self.efficiency = self.tasks_completed / max(1, (time.time() - START_TIME) / 60.0)

        elif self.state == "MANUAL_MOVE" and self.manual_target:
            self.steer(self.manual_target[0], self.manual_target[1])
            is_moving = True
            if dist(self.x, self.y, self.manual_target[0], self.manual_target[1]) < 10:
                self.manual_target = None
                self.state = "IDLE"

        elif GLOBAL_AUTO_MODE and self.mode == "AUTO" and self.state == "IDLE":
            self.auto_assign(water_objects, charging_dock)

        # Battery drain
        drain = MOVEMENT_POWER_W if is_moving else IDLE_POWER_W
        self._drain_battery(drain * (dt_sec / 3600.0) * (OVERHEAD_FACTOR if is_moving else 1.0))

        # Obstacle avoidance
        self.avoid_obstacles(obstacles_list)

        # Velocity clamp
        max_vel = self.SPEED * 2.5
        vel_mag = math.hypot(self.vx, self.vy)
        if vel_mag > max_vel:
            self.vx = (self.vx / vel_mag) * max_vel
            self.vy = (self.vy / vel_mag) * max_vel

        new_x = self.x + self.vx
        new_y = self.y + self.vy
        can_move = all(dist(new_x, new_y, o.x, o.y) >= (self.radius + o.radius + 2)
                       for o in obstacles_list if not o.is_pollution)
        if can_move:
            self.x = clamp(new_x, 20, OCEAN_WIDTH - 20)
            self.y = clamp(new_y, 20, HEIGHT - 20)
        else:
            self.vx *= 0.8; self.vy *= 0.8

        self.trail.append((self.x, self.y))

    def draw(self):
        # Trail
        for i in range(len(self.trail) - 1):
            pygame.draw.line(screen, TRAIL, self.trail[i], self.trail[i + 1], 1)

        # Body color by state — oil-carrying gets amber tint
        if self.state == "GOING_TO_DUMP" and self.collected_type == "oil":
            color = OILTANK_COLOR
        else:
            color = {
                "CHARGING":           ROBOT_CHARGING,
                "RETURN_TO_CHARGING": ROBOT_RETURN,
                "GOING_TO_POLLUTION": ROBOT_WORK,
                "GOING_TO_DUMP":      ROBOT_DUMP,
            }.get(self.state, ROBOT_IDLE)

        self.glow_pulse = (self.glow_pulse + 0.05) % (2 * math.pi)
        glow_r = int(10 + 2 * math.sin(self.glow_pulse))
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), glow_r, 1)
        draw_robot(screen, self.x, self.y, color)

        # Battery ring
        pygame.draw.circle(screen, self.battery_color, (int(self.x), int(self.y)), 16, 2)

        name_color = TEXT_DARK if self == SELECTED_ROBOT else TEXT
        screen.blit(FONT.render(self.name, True, name_color), (self.x + 9, self.y - 9))

        if self == SELECTED_ROBOT:
            pygame.draw.circle(screen, SELECTED, (int(self.x), int(self.y)), 18, 2)
        if self.stuck_counter > 12:
            pygame.draw.circle(screen, (255, 60, 60), (int(self.x), int(self.y)), 22, 2)

        # Destination tag when dumping
        if self.state == "GOING_TO_DUMP" and self.collected_type:
            dest = "→OilTank" if self.collected_type == "oil" else "→EcoDot"
            dest_c = OILTANK_COLOR if self.collected_type == "oil" else DUMP_COLOR
            dest_surf = FONT_TINY.render(dest, True, dest_c)
            screen.blit(dest_surf, (int(self.x) - dest_surf.get_width() // 2, int(self.y) - 24))

        bat_label = FONT_TINY.render(f"{self.battery_percentage:.0f}%", True, self.battery_color)
        screen.blit(bat_label, (int(self.x) - bat_label.get_width() // 2, int(self.y) + 14))


# =========================================================
# UI HELPERS
# =========================================================
def draw_button(rect, text, mx, my, active=False, color=TEXT):
    hover = rect.collidepoint(mx, my)
    shadow = pygame.Rect(rect.x + 2, rect.y + 2, rect.width, rect.height)
    pygame.draw.rect(screen, SHADOW, shadow, border_radius=5)
    bg = BTN_HOVER if hover else (BTN_ACTIVE if active else BTN)
    pygame.draw.rect(screen, bg, rect, border_radius=5)
    pygame.draw.rect(screen, BORDER, rect, 1, border_radius=5)
    surf = FONT_SMALL.render(text, True, color)
    screen.blit(surf, (rect.x + (rect.width - surf.get_width()) // 2,
                        rect.y + (rect.height - surf.get_height()) // 2))
    return hover


def draw_radar(robots, water_objects, ecodot_mgr, obstacles, oil_tank=None):
    radar_rect = pygame.Rect(OCEAN_WIDTH + 20, 200, 200, 200)
    pygame.draw.rect(screen, CARD, radar_rect, border_radius=6)
    pygame.draw.rect(screen, BORDER, radar_rect, 1, border_radius=6)
    screen.blit(FONT_SMALL.render("RADAR", True, TEXT), (radar_rect.x + 10, radar_rect.y + 5))

    sx = radar_rect.width / OCEAN_WIDTH
    sy = radar_rect.height / HEIGHT

    for dot in (ecodot_mgr.dot1, ecodot_mgr.dot2):
        dx = int(radar_rect.x + dot.x * sx)
        dy = int(radar_rect.y + 10 + dot.y * sy)
        c  = DUMP_COLOR if dot.status == "Active" else ECODOT2_COLOR if dot.status == "Standby" else (255, 80, 80)
        pygame.draw.circle(screen, c, (dx, dy), 4)

    if oil_tank:
        ox = int(radar_rect.x + oil_tank.x * sx)
        oy = int(radar_rect.y + 10 + oil_tank.y * sy)
        pygame.draw.circle(screen, OILTANK_COLOR, (ox, oy), 4)

    for o in water_objects:
        if o.active:
            px = int(radar_rect.x + o.x * sx)
            py = int(radar_rect.y + 10 + o.y * sy)
            c  = o.color if o.is_pollution else OBSTACLE_COLOR
            pygame.draw.circle(screen, c, (px, py), 2)

    for r in robots:
        rx = int(radar_rect.x + r.x * sx)
        ry = int(radar_rect.y + 10 + r.y * sy)
        c  = ROBOT_WORK if r.state == "GOING_TO_POLLUTION" else ROBOT_DUMP if r.state == "GOING_TO_DUMP" else ROBOT_IDLE
        pygame.draw.circle(screen, c, (rx, ry), 2)


def draw_ecodot_status_bar(ecodot_mgr, oil_tank):
    """Thin status bar at very bottom of the ocean area showing live container states."""
    panel = pygame.Rect(10, HEIGHT - 22, OCEAN_WIDTH - 20, 18)
    pygame.draw.rect(screen, CARD, panel, border_radius=4)
    pygame.draw.rect(screen, BORDER, panel, 1, border_radius=4)
    items = [
        (ecodot_mgr.dot1, ecodot_mgr.dot1.status),
        (ecodot_mgr.dot2, ecodot_mgr.dot2.status),
        (oil_tank, "Full" if oil_tank.is_full else "Ready"),
    ]
    col_w = (OCEAN_WIDTH - 40) // 3
    for i, (obj, status) in enumerate(items):
        sc = (0, 200, 100) if status in ("Active", "Ready") else \
             (80, 200, 255) if status == "Standby" else (255, 80, 80)
        name = getattr(obj, "name", "OilTank")
        txt  = f"{name}: {int(obj.load)}%  [{status}]"
        surf = FONT_TINY.render(txt, True, sc)
        screen.blit(surf, (panel.x + 10 + i * col_w, panel.y + 3))


# =========================================================
# MAIN
# =========================================================
def main():
    global GLOBAL_AUTO_MODE, SELECTED_ROBOT, SELECTED_POLLUTION
    global START_TIME, ALERT_MESSAGE, ALERT_TIME
    global TOTAL_POLLUTION, DISPOSED_POLLUTION

    # ── Init objects ──────────────────────────────────────
    robots = [Robot(i) for i in range(10)]
    all_objects = []

    # Initial pollution (mixed types)
    water_objects = []
    for _ in range(6):
        obj = make_pollution(existing_objects=all_objects)
        water_objects.append(obj)
        all_objects.append(obj)

    ecodot_mgr   = EcoDotManager()
    oil_tank     = OilTank()
    charging_dock = ChargingDock(x=80, y=HEIGHT - 80)

    # Add fixed container positions as phantom obstacles so nothing spawns on them
    class _Phantom:
        def __init__(self, x, y, r=50):
            self.x=x; self.y=y; self.radius=r
    all_objects.append(_Phantom(*ECODOT1_POS))
    all_objects.append(_Phantom(*ECODOT2_POS))
    all_objects.append(_Phantom(*OILTANK_POS))

    START_TIME = time.time()

    scroll_y       = 0
    pollution_scroll = 0
    max_scroll     = 1650
    scroll_dragging = False
    scroll_drag_start = 0
    placing_obstacle  = False
    obstacle_preview_pos = None

    # Buttons
    auto_btn         = pygame.Rect(OCEAN_WIDTH + 20,  60, 120, 35)
    erp_btn          = pygame.Rect(OCEAN_WIDTH + 150, 60, 120, 35)
    map_btn          = pygame.Rect(OCEAN_WIDTH + 280, 60, 120, 35)
    reset_btn        = pygame.Rect(OCEAN_WIDTH + 20, 105, 120, 35)
    clear_btn        = pygame.Rect(OCEAN_WIDTH + 150,105, 120, 35)
    add_obstacle_btn = pygame.Rect(OCEAN_WIDTH + 280,105, 120, 35)

    # Per-dot clean buttons — shown ONLY when that dot is full
    # Placed above each EcoDot on the ocean canvas
    clean1_btn = pygame.Rect(ECODOT1_POS[0] - 60, ECODOT1_POS[1] - 75, 120, 30)
    clean2_btn = pygame.Rect(ECODOT2_POS[0] - 60, ECODOT2_POS[1] - 75, 120, 30)
    # OilTank drain button — shown above the OilTank when full
    drain_btn  = pygame.Rect(OILTANK_POS[0] - 55, OILTANK_POS[1] - 68, 110, 28)

    # ── Main loop ─────────────────────────────────────────
    while True:
        clock.tick(FPS)
        screen.fill(BG)

        # Animated ocean background
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            wave  = math.sin(y * 0.01 + pygame.time.get_ticks() * 0.001) * 5
            r_ = int(GRADIENT_TOP[0] * (1 - ratio) + GRADIENT_BOTTOM[0] * ratio)
            g_ = int(GRADIENT_TOP[1] * (1 - ratio) + GRADIENT_BOTTOM[1] * ratio)
            b_ = int(GRADIENT_TOP[2] * (1 - ratio) + GRADIENT_BOTTOM[2] * ratio)
            pygame.draw.line(screen, (r_, g_, b_), (0, y), (OCEAN_WIDTH, y))
            if y % 20 == 0:
                pygame.draw.line(screen, (r_+10, g_+10, b_+10),
                                 (0, y + wave), (OCEAN_WIDTH, y + wave), 1)

        for y in range(HEIGHT):
            ratio = y / HEIGHT * 0.1
            c = (int(PANEL[0]*(1-ratio)+(PANEL[0]-5)*ratio),
                 int(PANEL[1]*(1-ratio)+(PANEL[1]-5)*ratio),
                 int(PANEL[2]*(1-ratio)+(PANEL[2]-5)*ratio))
            pygame.draw.line(screen, c, (OCEAN_WIDTH, y), (WIDTH, y))

        pygame.draw.line(screen, BORDER, (OCEAN_WIDTH, 0), (OCEAN_WIDTH, HEIGHT), 3)

        mx, my = pygame.mouse.get_pos()

        # ── Events ────────────────────────────────────────
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                cx, cy = e.pos

                # Scroll bar
                sb = pygame.Rect(OCEAN_WIDTH + 405, 200, 10, HEIGHT - 200)
                if sb.collidepoint(cx, cy):
                    scroll_dragging   = True
                    scroll_drag_start = cy
                    continue

                # Per-dot clean buttons
                if ecodot_mgr.need_clean_dot1 and clean1_btn.collidepoint(cx, cy):
                    ecodot_mgr.clean_dot1()
                    continue
                if ecodot_mgr.need_clean_dot2 and clean2_btn.collidepoint(cx, cy):
                    ecodot_mgr.clean_dot2()
                    continue
                # OilTank drain button
                if oil_tank.need_drain and drain_btn.collidepoint(cx, cy):
                    oil_tank.drain()
                    continue

                # Control buttons
                if auto_btn.collidepoint(cx, cy):
                    GLOBAL_AUTO_MODE = not GLOBAL_AUTO_MODE
                    if GLOBAL_AUTO_MODE:
                        for r in robots:
                            if r.state == "IDLE":
                                r.mode = "AUTO"
                    continue

                if erp_btn.collidepoint(cx, cy):
                    obj = make_pollution([o for o in water_objects if o.active] + all_objects)
                    water_objects.append(obj)
                    all_objects.append(obj)
                    continue

                if map_btn.collidepoint(cx, cy):
                    draw_india_map(); continue

                if reset_btn.collidepoint(cx, cy):
                    robots          = [Robot(i) for i in range(10)]
                    water_objects   = []
                    all_objects     = []
                    for _ in range(6):
                        obj = make_pollution(all_objects)
                        water_objects.append(obj); all_objects.append(obj)
                    ecodot_mgr      = EcoDotManager()
                    oil_tank        = OilTank()
                    charging_dock   = ChargingDock(x=80, y=HEIGHT - 80)
                    all_objects.append(_Phantom(*ECODOT1_POS))
                    all_objects.append(_Phantom(*ECODOT2_POS))
                    all_objects.append(_Phantom(*OILTANK_POS))
                    TOTAL_POLLUTION = len(water_objects)
                    DISPOSED_POLLUTION = 0
                    START_TIME      = time.time()
                    scroll_y = pollution_scroll = 0
                    ALERT_MESSAGE   = ""
                    ALERT_TIME      = 0
                    GLOBAL_AUTO_MODE = False
                    SELECTED_ROBOT  = None
                    SELECTED_POLLUTION = None
                    continue

                if clear_btn.collidepoint(cx, cy):
                    water_objects = [o for o in water_objects if o.is_pollution]
                    continue

                if add_obstacle_btn.collidepoint(cx, cy):
                    placing_obstacle = not placing_obstacle
                    if not placing_obstacle:
                        obstacle_preview_pos = None
                    continue

                # Ocean clicks
                if cx < OCEAN_WIDTH:
                    if placing_obstacle:
                        obs = make_obstacle(cx, cy,
                                            [o for o in water_objects if o.active] + robots)
                        overlap = check_overlap(obs.x, obs.y, obs.radius + 2,
                                                [o for o in water_objects if o.active] + robots)
                        if not overlap:
                            water_objects.append(obs)
                            all_objects.append(obs)
                        continue

                    # Click robot / pollution selection
                    clicked_robot = next((r for r in robots
                                          if dist(cx, cy, r.x, r.y) < 15), None)
                    clicked_poll  = next((o for o in water_objects
                                          if o.is_pollution and o.active and
                                          dist(cx, cy, o.x, o.y) < o.radius), None)
                    if clicked_robot:
                        SELECTED_ROBOT    = clicked_robot
                        SELECTED_POLLUTION = None; continue
                    if clicked_poll:
                        if SELECTED_ROBOT:
                            SELECTED_ROBOT.assign(clicked_poll)
                        else:
                            SELECTED_POLLUTION = clicked_poll
                        continue

                # Panel — robot card clicks
                panel_y = 230 + scroll_y
                for r in robots:
                    rect = pygame.Rect(OCEAN_WIDTH + 20, panel_y, 380, 145)
                    btn_start_y = rect.y + 114
                    active_poll = [o for o in water_objects if o.is_pollution and o.active]
                    vis = active_poll[pollution_scroll:pollution_scroll + 14]
                    assigned_clicked = False
                    for i, p in enumerate(vis):
                        br = pygame.Rect(rect.x + 25 + i * 25, btn_start_y, 23, 20)
                        is_disabled = GLOBAL_AUTO_MODE or (p.assigned and p.assigned != r)
                        if br.collidepoint(cx, cy) and not is_disabled:
                            r.assign(p); SELECTED_ROBOT = r
                            SELECTED_POLLUTION = None; assigned_clicked = True; break
                    if assigned_clicked: break
                    if rect.collidepoint(cx, cy):
                        SELECTED_ROBOT = r; SELECTED_POLLUTION = None; break
                    panel_y += 150

            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                scroll_dragging = False

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                if mx < OCEAN_WIDTH and SELECTED_ROBOT:
                    SELECTED_ROBOT.mode = "MANUAL"
                    SELECTED_ROBOT.manual_target = (mx, my)
                    SELECTED_ROBOT.state = "MANUAL_MOVE"

            elif e.type == pygame.MOUSEWHEEL:
                scroll_y = clamp(scroll_y + e.y * 30, -max_scroll, 0)

            if e.type == pygame.MOUSEMOTION:
                if scroll_dragging:
                    delta = e.pos[1] - scroll_drag_start
                    scroll_drag_start = e.pos[1]
                    scroll_y = clamp(scroll_y - delta * 3, -max_scroll, 0)
                if placing_obstacle and mx < OCEAN_WIDTH:
                    obstacle_preview_pos = (mx, my)

        # ── Poll EcoDot + OilTank notifications ───────────
        notif = ecodot_mgr.poll_notification()
        if not notif:
            notif = oil_tank.poll_notification()
        if notif:
            ALERT_MESSAGE = notif["msg"]
            ALERT_TIME    = time.time()

        # ── Update & Draw ──────────────────────────────────
        ecodot_mgr.update()
        oil_tank.update()
        obstacles_list = [o for o in water_objects if not o.is_pollution]

        charging_dock.draw()
        ecodot_mgr.draw()
        oil_tank.draw()
        for o in water_objects:
            o.draw()
        for r in robots:
            r.update(water_objects, ecodot_mgr, obstacles_list, charging_dock, oil_tank)
            r.draw()

        # ── Per-dot CLEAN buttons (float above each EcoDot) ──
        if ecodot_mgr.need_clean_dot1:
            flash = abs(math.sin(time.time() * 4))
            fc1 = (int(180 + 75 * flash), 30, 30)
            pygame.draw.rect(screen, fc1, clean1_btn, border_radius=6)
            pygame.draw.rect(screen, TEXT, clean1_btn, 2, border_radius=6)
            lbl = FONT_SMALL.render("CLEAN ECODOT 1", True, TEXT)
            screen.blit(lbl, (clean1_btn.x + (clean1_btn.w - lbl.get_width()) // 2,
                               clean1_btn.y + (clean1_btn.h - lbl.get_height()) // 2))

        if ecodot_mgr.need_clean_dot2:
            flash = abs(math.sin(time.time() * 4))
            fc2 = (int(180 + 75 * flash), 30, 30)
            pygame.draw.rect(screen, fc2, clean2_btn, border_radius=6)
            pygame.draw.rect(screen, TEXT, clean2_btn, 2, border_radius=6)
            lbl = FONT_SMALL.render("CLEAN ECODOT 2", True, TEXT)
            screen.blit(lbl, (clean2_btn.x + (clean2_btn.w - lbl.get_width()) // 2,
                               clean2_btn.y + (clean2_btn.h - lbl.get_height()) // 2))

        # ── OilTank DRAIN button (floats above OilTank) ───
        if oil_tank.need_drain:
            flash = abs(math.sin(time.time() * 4))
            fc_oil = (int(200 + 55 * flash), int(120 + 60 * flash), 0)
            pygame.draw.rect(screen, fc_oil, drain_btn, border_radius=6)
            pygame.draw.rect(screen, TEXT, drain_btn, 2, border_radius=6)
            lbl = FONT_SMALL.render("DRAIN OILTANK", True, TEXT)
            screen.blit(lbl, (drain_btn.x + (drain_btn.w - lbl.get_width()) // 2,
                               drain_btn.y + (drain_btn.h - lbl.get_height()) // 2))

        # Obstacle placement preview
        if placing_obstacle and obstacle_preview_pos:
            collision = check_overlap(obstacle_preview_pos[0], obstacle_preview_pos[1], 30 + 10,
                                      [o for o in water_objects if o.active] + robots)
            c = (255, 100, 100) if collision else OBSTACLE_COLOR
            pygame.draw.circle(screen, c, obstacle_preview_pos, 35, 2)
            screen.blit(FONT_SMALL.render("Click to place", True, TEXT),
                        (obstacle_preview_pos[0] - 40, obstacle_preview_pos[1] - 60))

        # ── Alert banner (centred, below top edge) ────────
        if ALERT_MESSAGE and time.time() - ALERT_TIME < 6:
            alert_bg = pygame.Rect(OCEAN_WIDTH // 2 - 290, 8, 580, 36)
            bc = (180, 30, 30) if ecodot_mgr.dump_paused else \
                 (180, 100, 10) if (ecodot_mgr.eco1_full or ecodot_mgr.eco2_full) else (20, 110, 50)
            pygame.draw.rect(screen, bc, alert_bg, border_radius=8)
            pygame.draw.rect(screen, TEXT, alert_bg, 2, border_radius=8)
            surf = FONT_SMALL.render(ALERT_MESSAGE[:70], True, TEXT)
            screen.blit(surf, (OCEAN_WIDTH // 2 - surf.get_width() // 2, alert_bg.y + 10))

        # ── Status bar at bottom of ocean ────────────────
        draw_ecodot_status_bar(ecodot_mgr, oil_tank)

        # ── Radar (panel side only) ───────────────────────
        draw_radar(robots, water_objects, ecodot_mgr, obstacles_list, oil_tank)

        # ── HUD / Stats ───────────────────────────────────
        active_poll = [o for o in water_objects if o.is_pollution and o.active]
        elapsed     = time.time() - START_TIME
        stats_lines = [
            f"TIME: {int(elapsed//60):02d}:{int(elapsed%60):02d}",
            f"ACTIVE POLL: {len(active_poll)}",
            f"DISPOSED:    {DISPOSED_POLLUTION}",
            f"TOTAL:       {TOTAL_POLLUTION}",
            f"AUTO MODE:   {'ON' if GLOBAL_AUTO_MODE else 'OFF'}",
            f"DUMP PAUSED: {'YES' if ecodot_mgr.dump_paused else 'NO'}",
            f"OILTANK:     {int(oil_tank.load)}%{'  [FULL]' if oil_tank.is_full else ''}",
        ]
        sx_hud, sy_hud = OCEAN_WIDTH + 235, 215
        for i, line in enumerate(stats_lines):
            color = (255, 80, 80) if "YES" in line or "FULL" in line else \
                    OILTANK_COLOR if "OILTANK" in line else TEXT
            screen.blit(FONT_SMALL.render(line, True, color), (sx_hud, sy_hud + i * 14))

        # ── Command center title ──────────────────────────
        title_bg = pygame.Rect(OCEAN_WIDTH + 15, 10, PANEL_WIDTH - 30, 35)
        pygame.draw.rect(screen, CARD_HI, title_bg, border_radius=8)
        pygame.draw.rect(screen, ACCENT, title_bg, 2, border_radius=8)
        ts = FONT_HUGE.render("COMMAND CENTER", True, TEXT)
        screen.blit(ts, (OCEAN_WIDTH + (PANEL_WIDTH - ts.get_width()) // 2, 17))

        # ── Control buttons ───────────────────────────────
        draw_button(auto_btn,         "AUTO MODE" if GLOBAL_AUTO_MODE else "MANUAL", mx, my, GLOBAL_AUTO_MODE)
        draw_button(erp_btn,          "ADD POLL",    mx, my)
        draw_button(map_btn,          "INDIA MAP",   mx, my)
        draw_button(reset_btn,        "RESET",       mx, my)
        draw_button(clear_btn,        "CLEAR OBS",   mx, my)
        draw_button(add_obstacle_btn, "PLACING" if placing_obstacle else "OBSTACLES", mx, my, placing_obstacle)

        # ── Robot panel (scrollable) ───────────────────────
        scrollable_rect = pygame.Rect(OCEAN_WIDTH, 420, PANEL_WIDTH - 15, HEIGHT - 420)
        screen.set_clip(scrollable_rect)
        py = 425 + scroll_y

        header = pygame.Rect(OCEAN_WIDTH + 20, py, 380, 26)
        pygame.draw.rect(screen, CARD_HI, header, border_radius=6)
        pygame.draw.rect(screen, ACCENT, header, 1, border_radius=6)
        screen.blit(FONT_BIG.render("ROBOT MANUAL CONTROL", True, TEXT_DARK), (OCEAN_WIDTH + 30, py + 4))
        py += 30

        for r in robots:
            rect = pygame.Rect(OCEAN_WIDTH + 20, py, 380, 148)
            color_ = SELECTED if r == SELECTED_ROBOT else CARD
            pygame.draw.rect(screen, color_, rect, border_radius=6)
            pygame.draw.rect(screen, BORDER, rect, 1, border_radius=6)

            sc = {
                "CHARGING": ROBOT_CHARGING, "RETURN_TO_CHARGING": ROBOT_RETURN,
                "GOING_TO_POLLUTION": ROBOT_WORK, "GOING_TO_DUMP": ROBOT_DUMP
            }.get(r.state, ROBOT_IDLE)
            pygame.draw.circle(screen, sc, (rect.x + 12, rect.y + 12), 7)

            nc = TEXT_DARK if r == SELECTED_ROBOT else TEXT
            screen.blit(FONT_BIG.render(r.name, True, nc), (rect.x + 25, rect.y + 5))
            screen.blit(FONT_SMALL.render(f"{r.mode} | {r.state[:16]}", True,
                                           TEXT_DARK if r == SELECTED_ROBOT else MUTED),
                        (rect.x + 10, rect.y + 28))

            # Target info + reward
            tc = ACCENT if r.target else MUTED
            nc2 = TEXT_DARK if r == SELECTED_ROBOT else tc
            tgt_txt = (f"→ {r.target.obj_type.upper()}#{r.target.obj_id} "
                       f"Dist:{int(dist(r.x,r.y,r.target.x,r.target.y))}"
                       if r.target else "No Target")
            screen.blit(FONT_SMALL.render(tgt_txt, True, nc2), (rect.x + 10, rect.y + 42))

            reward_txt = f"Reward: {r.total_reward:+}  Misclassify: {r.misclassify_count}"
            screen.blit(FONT_TINY.render(reward_txt, True, TEXT_DARK if r == SELECTED_ROBOT else MUTED),
                        (rect.x + 10, rect.y + 55))

            # Battery bar
            bar_x, bar_y, bar_w, bar_h = rect.x + 10, rect.y + 68, 240, 10
            pygame.draw.rect(screen, (40, 55, 80), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            fw = int(bar_w * r.battery_percentage / 100.0)
            if fw > 0:
                pygame.draw.rect(screen, r.battery_color, (bar_x, bar_y, fw, bar_h), border_radius=4)
            pygame.draw.rect(screen, BORDER, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
            bat_c = TEXT_DARK if r == SELECTED_ROBOT else r.battery_color
            screen.blit(FONT_SMALL.render(
                f"{r.battery_percentage:.0f}%  {r.battery_wh:.1f}Wh  ~{r.estimated_cycles_remaining()} cyc",
                True, bat_c), (rect.x + 10, rect.y + 82))
            screen.blit(FONT_SMALL.render(
                f"Cycle: {r.energy_per_cycle:.2f}Wh  Total: {r.total_energy_consumed_wh:.1f}Wh",
                True, TEXT_DARK if r == SELECTED_ROBOT else MUTED), (rect.x + 10, rect.y + 96))

            # Assign buttons
            screen.blit(FONT_SMALL.render("Assign:", True, TEXT_DARK if r == SELECTED_ROBOT else MUTED),
                        (rect.x + 10, rect.y + 110))
            btn_sy = rect.y + 124
            act_poll = [o for o in water_objects if o.is_pollution and o.active]
            if len(act_poll) > 14:
                la = pygame.Rect(rect.x + 5, btn_sy, 15, 20)
                pygame.draw.rect(screen, BTN if pollution_scroll > 0 else MUTED, la, border_radius=3)
                ra = pygame.Rect(rect.x + 365, btn_sy, 15, 20)
                pygame.draw.rect(screen, BTN if pollution_scroll < len(act_poll)-14 else MUTED, ra, border_radius=3)
            vis = act_poll[pollution_scroll:pollution_scroll + 14]
            for i, p in enumerate(vis):
                br = pygame.Rect(rect.x + 25 + i * 25, btn_sy, 23, 20)
                disabled = GLOBAL_AUTO_MODE or (p.assigned and p.assigned != r)
                if disabled:
                    pygame.draw.rect(screen, MUTED, br, border_radius=4)
                else:
                    bc2 = BTN_ACTIVE if p.assigned == r else BTN_HOVER if br.collidepoint(mx, my) else BTN
                    pygame.draw.rect(screen, bc2, br, border_radius=4)
                    pygame.draw.rect(screen, BORDER, br, 1, border_radius=4)
                screen.blit(FONT_TINY.render(f"#{p.obj_id}", True, TEXT), (br.x + 1, br.y + 6))

            screen.blit(FONT_SMALL.render(f"Pos:({int(r.x)},{int(r.y)}) Tasks:{r.tasks_completed}",
                                           True, TEXT_DARK if r == SELECTED_ROBOT else MUTED),
                        (rect.x + 10, rect.y + 134))
            py += 153

        screen.set_clip(None)

        # Scroll bar
        sbr = pygame.Rect(OCEAN_WIDTH + 405, 420, 10, HEIGHT - 420)
        pygame.draw.rect(screen, BORDER, sbr, border_radius=5)
        if max_scroll > 0:
            sh = max(30, (HEIGHT - 420) ** 2 / (HEIGHT - 420 + max_scroll))
            sy2 = 420 + (-scroll_y / max_scroll) * (HEIGHT - 420 - sh)
            pygame.draw.rect(screen, HIGHLIGHT, pygame.Rect(OCEAN_WIDTH + 405, sy2, 10, sh), border_radius=5)

        pygame.display.flip()


if __name__ == "__main__":
    main()
