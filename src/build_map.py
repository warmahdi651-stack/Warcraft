#!/usr/bin/env python3
"""
Deterministic Procedural Generator for `(8) Crown of WarMahdi` v9.
An 8-player D4-symmetric Sunken-Astral Altered Melee map with 8 playable empires,
64 exclusive hero skills, custom cursor/RPG UI, four imported custom-race melee-AI scripts and native standard-race melee AI.
Targets classic Warcraft III: The Frozen Throne 1.26a/1.27b-era APIs only.
"""

from __future__ import annotations
import json
import math
import struct
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from mpq_packer import build_hm3w_header, pack_w3x
from src.custom_assets import generate_all_custom_assets
from src.blp_codec import encode_blp1_jpeg
from src.custom_factions_v3 import HERO_SKILL_SPECS_64
from custom_races import (
    generate_camphuman_ai_script,
    generate_custom_races_jass,
    generate_naga_ai_script,
    generate_runeforged_ai_script,
    generate_voidborn_ai_script,
    serialize_imp,
    serialize_w3a,
    serialize_w3q,
    serialize_w3t,
    serialize_w3u,
    serialize_war3map_misc,
    serialize_war3map_skin,
)

# ==============================================================================
# Map Constants & Coordinate System
# ==============================================================================

MAP_FILENAME = "(8)CrownOfWarMahdi.w3x"
MAP_DISPLAY_NAME = "(8) Crown of WarMahdi"
MAP_AUTHOR = "WarMahdi Studio"
MAP_RECOMMENDED_PLAYERS = "8 Empires • Host AI Menu"
MAP_DESCRIPTION = (
    "|cffffd700★ (8) Crown of WarMahdi v9 ★|r — 8-Empire Sunken-Astral Altered Melee (4v4 / 2v2 / FFA). "
    "4 Classic Races + 4 Custom Empires, with a 600 food ceiling: |cff22d3eeAbyssal Tideborn (with Illidan)|r, |cfffbbf24Sunfury Imperium|r, "
    "|cfff97316Voidborn Legion|r & |cff38bdf8Runeforged Bastion|r! "
    "Features 16 heroes with original portraits, 64 original custom skill icons and distinct spell VFX; core ranks unlock at levels 1/3/5 and ultimates at level 6. "
    "Restored Mana Burn, Phoenix and Resurrection; added twelve faction/tier hall icon pairs and six unique Naga hall/role building models, alongside four faction-specific Classic melee-AI scripts with harvesting, expansion calls, and assault-group routines. "
    "Includes 64 skill-specific, geometrically varied spell MDX effects plus six faction sigils, custom cursor/RPG UI, and the preserved Sunken-Astral terrain."
)

# 192x192 tiles => 193x193 terrain corners; 1 tile = 128 world units; 1 pathing cell = 32 world units
TILES_W = 192
TILES_H = 192
CORNERS_W = TILES_W + 1  # 193
CORNERS_H = TILES_H + 1  # 193
PATH_W = TILES_W * 4     # 768
PATH_H = TILES_H * 4     # 768

TILE_SIZE = 128.0
PATH_CELL = 32.0
CENTER_OFFSET_X = -12288.0  # -96 * 128
CENTER_OFFSET_Y = -12288.0  # -96 * 128

# Camera / playable complements: [left=6, right=6, bottom=6, top=6] -> 180x180 playable
COMPLEMENTS = (6, 6, 6, 6)
PLAYABLE_TILES_W = TILES_W - COMPLEMENTS[0] - COMPLEMENTS[1]  # 180
PLAYABLE_TILES_H = TILES_H - COMPLEMENTS[2] - COMPLEMENTS[3]  # 180
PLAYABLE_MIN_X = CENTER_OFFSET_X + COMPLEMENTS[0] * TILE_SIZE  # -11520.0
PLAYABLE_MAX_X = -PLAYABLE_MIN_X                               # +11520.0
PLAYABLE_MIN_Y = CENTER_OFFSET_Y + COMPLEMENTS[2] * TILE_SIZE  # -11520.0
PLAYABLE_MAX_Y = -PLAYABLE_MIN_Y                               # +11520.0
PLAYABLE_SPAN = PLAYABLE_MAX_X - PLAYABLE_MIN_X                # 23040.0

# Warcraft III Standard Camera Margins: Left=512, Right=512, Top=256, Bottom=256
CAM_LEFT = PLAYABLE_MIN_X + 512.0    # -11008.0
CAM_RIGHT = PLAYABLE_MAX_X - 512.0   # +11008.0
CAM_BOTTOM = PLAYABLE_MIN_Y + 256.0  # -11264.0
CAM_TOP = PLAYABLE_MAX_Y - 256.0     # +11264.0

# Altered Melee w3i flags:
# 0x0002 modifyAllyPriorities | 0x0008 largeMap | 0x0010 maskedPartiallyVisible |
# 0x0400 mapPropertiesOpened | 0x0800 waterWavesOnCliffShores | 0x1000 waterWavesOnRollingShores |
# 0x2000 useTerrainFog | 0x4000 requiresExpansion | 0x8000 useItemClassificationSystem |
# 0x10000 customWaterTinting (`0x0001` DISABLE_PREVIEW kept `0` so `war3mapPreview.tga` renders in Lobby!)
MAP_FLAGS = 0x0002 | 0x0008 | 0x0010 | 0x0400 | 0x0800 | 0x1000 | 0x2000 | 0x4000 | 0x8000 | 0x10000  # 0x1FC1A

# Sunken-Astral Ancient Temple Citadel Ground Tilesets (index 0..5, 100% buildability parity!)
GROUND_TILESETS = ["Zdrt", "Ztil", "Zsan", "Zbkl", "Zgrs", "Zvin"]
CLIFF_TILESETS = ["CZdi", "CZlb"]

TEX_DIRT = 0         # Zdrt (buildable ancient earth, base of CZdi)
TEX_ROUGH_DIRT = 1   # Ztil (buildable carved astral temple tiles — highways & shrine!)
TEX_GRASSY_DIRT = 2  # Zsan (buildable luminous coastal stone/sand transition)
TEX_ROCK = 3         # Zbkl (UNBUILDABLE decorative carved temple brick, base of CZlb)
TEX_GRASS = 4        # Zgrs (buildable emerald sanctuary turf)
TEX_DARK_GRASS = 5   # Zvin (buildable vine-covered ancient ruins)

# Water surface level: waterWorldZ = 0.70 * 128 - 89.6 = 0.0 world units
WATER_HEIGHT_CONST = 0.70

# Exact Warcraft III Player Colors in BGRA for war3map.mmp
PLAYER_COLORS_BGRA = [
    (3, 3, 255, 255),      # 0 Red
    (255, 66, 0, 255),     # 1 Blue
    (185, 230, 28, 255),   # 2 Teal
    (129, 0, 84, 255),     # 3 Purple
    (1, 252, 255, 255),    # 4 Yellow
    (14, 138, 254, 255),   # 5 Orange
    (0, 192, 32, 255),     # 6 Green
    (176, 91, 229, 255),   # 7 Pink
]

PLAYER_COLOR_NAMES = ["Red", "Blue", "Teal", "Purple", "Yellow", "Orange", "Green", "Pink"]


# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class ItemDropSpec:
    raw_doo_id: str      # 4-char code for war3mapUnits.doo (e.g. 'YiI3' or 'texp')
    jass_expr: str       # JASS expression yielding item rawcode (e.g. "ChooseRandomItemEx( ITEM_TYPE_PERMANENT, 3 )" or "'texp'")
    label: str           # Human-readable description for web inspector


@dataclass
class PlacedUnit:
    uid: str
    player: int          # 0..7 player, 12 Neutral Hostile, 15 Neutral Passive
    x: float
    y: float
    z: float
    angle_deg: float
    gold: int = 12500
    acq_range: float = -1.0  # -1 normal, -2 camp (200 range)
    drops: List[ItemDropSpec] = field(default_factory=list)
    creation_num: int = 0
    camp_id: Optional[int] = None
    role: str = ""


@dataclass
class PlacedTree:
    did: str
    variation: int
    x: float
    y: float
    z: float
    angle_deg: float
    scale: float
    editor_id: int
    life: int = 100


# ==============================================================================
# D4 Dihedral Symmetry Group Helpers
# ==============================================================================

def d4_transforms(x: float, y: float) -> List[Tuple[float, float]]:
    """
    Returns the 8 images of (x, y) under D4 ordered clockwise when x=3840, y=8960:
      0: (-x, +y) NNW
      1: (+x, +y) NNE
      2: (+y, +x) ENE
      3: (+y, -x) ESE
      4: (+x, -y) SSE
      5: (-x, -y) SSW
      6: (-y, -x) WSW
      7: (-y, +x) WNW
    """
    return [
        (-x, +y),
        (+x, +y),
        (+y, +x),
        (+y, -x),
        (+x, -y),
        (-x, -y),
        (-y, -x),
        (-y, +x),
    ]


# Determinant of each transform returned by d4_transforms, in the same order.
# Camp side-offset orientation must flip under reflections or member placements drift out of symmetry.
D4_DETERMINANTS = (-1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0)


def d4_canonical(x: float, y: float) -> Tuple[float, float]:
    """Maps any (x, y) into the fundamental wedge 0 <= u <= v."""
    ax, ay = abs(x), abs(y)
    return (ax, ay) if ax <= ay else (ay, ax)


def dist_point_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    c1 = vx * wx + vy * wy
    if c1 <= 0.0:
        return math.hypot(px - ax, py - ay)
    c2 = vx * vx + vy * vy
    if c2 <= c1:
        return math.hypot(px - bx, py - by)
    t = c1 / c2
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if x <= edge0:
        return 0.0
    if x >= edge1:
        return 1.0
    t = (x - edge0) / (edge1 - edge0)
    return t * t * (3.0 - 2.0 * t)


# ==============================================================================
# Map Layout Specification (Orbits, Roads, Bases, Camps)
# ==============================================================================

PLAYER_BASES = d4_transforms(3840.0, 8960.0)
MAIN_MINES = d4_transforms(3840.0, 9600.0)
NATURAL_MINES = d4_transforms(2304.0, 6272.0)
CORNER_MINES = [(-9472.0, +9472.0), (+9472.0, +9472.0), (+9472.0, -9472.0), (-9472.0, -9472.0)]

GOBLIN_MERCHANTS = [(0.0, +8704.0), (+8704.0, 0.0), (0.0, -8704.0), (-8704.0, 0.0)]
GOBLIN_LABS = [(-7424.0, +7424.0), (+7424.0, +7424.0), (+7424.0, -7424.0), (-7424.0, -7424.0)]
MERC_CAMPS = [(0.0, +4992.0), (+4992.0, 0.0), (0.0, -4992.0), (-4992.0, 0.0)]
HEALTH_FOUNTAINS = [(-4608.0, +4608.0), (+4608.0, +4608.0), (+4608.0, -4608.0), (-4608.0, -4608.0)]
CENTRAL_TAVERN = (0.0, 0.0)

GREEN_GNOLL_CENTERS = d4_transforms(6400.0, 9600.0)


def build_road_segments() -> List[Tuple[float, float, float, float, float]]:
    """
    Build D4-symmetric highway network where EVERY neutral objective & creep camp sits
    in a recessed alcove or twin-boulevard island (>= 750 units clear of through-highways!).
    """
    fundamental = [
        # Main base front exit -> Outer Highway Hub (3584, 7424)
        (3840.0, 8704.0, 3584.0, 7424.0, 360.0),
        # Outer Ring Highway: Hub (3584, 7424) -> Cardinal Plaza (0, 7424) [Merchant recessed at (0, 8704)]
        (3584.0, 7424.0, 0.0, 7424.0, 340.0),
        # Short T-spur from Cardinal Plaza (0, 7424) toward Goblin Merchant alcove
        (0.0, 7424.0, 0.0, 8192.0, 260.0),
        # Outer Flank Highway: Hub (3584, 7424) -> Flank Junction (5760, 8064) -> Diagonal Plaza (6016, 6016)
        (3584.0, 7424.0, 5760.0, 8064.0, 330.0),
        (5760.0, 8064.0, 6016.0, 6016.0, 330.0),
        # Short spur toward Green Gnoll Outpost alcove (6400, 9600)
        (5760.0, 8064.0, 6208.0, 9024.0, 250.0),
        # Bypass road around Goblin Lab (7424, 7424) to Corner Expansion (9472, 9472)
        (5760.0, 8064.0, 8192.0, 8832.0, 290.0),
        (8192.0, 8832.0, 9088.0, 9088.0, 280.0),
        # Hub (3584, 7424) -> Natural Expansion approach (2816, 6528) [Mine recessed at (2304, 6272)]
        (3584.0, 7424.0, 2816.0, 6528.0, 320.0),
        # Twin Boulevard sweeping safely around Cardinal Mercenary Shrine (0, 4992):
        # Passes through (1280, 4864) -> >= 1,280 units clear of Mercenary Camp & Golem Guards!
        (0.0, 7424.0, 1280.0, 5888.0, 310.0),
        (2816.0, 6528.0, 1280.0, 5888.0, 310.0),
        (1280.0, 5888.0, 1280.0, 3968.0, 320.0),
        (1280.0, 3968.0, 0.0, 3200.0, 350.0),
        # Cardinal Grand Causeway across Silverwater Moat into Central Tavern (0, 0)
        (0.0, 3200.0, 0.0, 0.0, 420.0),
        # Twin Boulevard sweeping safely around Diagonal Fountain/Dragon Shrine (4608, 4608):
        # Passes through (3456, 5504) & (5504, 3456) -> >= 1,250 units clear of Red Dragon!
        (6016.0, 6016.0, 3840.0, 5632.0, 310.0),
        (2816.0, 6528.0, 3840.0, 5632.0, 300.0),
        (3840.0, 5632.0, 2432.0, 3456.0, 310.0),
        (2432.0, 3456.0, 2304.0, 2304.0, 350.0),
        # Diagonal Shallow Water Ford across Silverwater Moat into Central Tavern (0, 0)
        (2304.0, 2304.0, 0.0, 0.0, 380.0),
    ]
    segs: List[Tuple[float, float, float, float, float]] = []
    seen = set()
    for ax, ay, bx, by, w in fundamental:
        imgs_a = d4_transforms(ax, ay)
        imgs_b = d4_transforms(bx, by)
        for (x1, y1), (x2, y2) in zip(imgs_a, imgs_b):
            key = tuple(sorted([(round(x1, 1), round(y1, 1)), (round(x2, 1), round(y2, 1))]))
            if key not in seen:
                seen.add(key)
                segs.append((x1, y1, x2, y2, w))
    return segs


ROAD_SEGMENTS = build_road_segments()


def min_road_margin(px: float, py: float) -> float:
    """Returns signed distance inside road (<0 means on road, >0 means outside road)."""
    best = 1e9
    for ax, ay, bx, by, hw in ROAD_SEGMENTS:
        d = dist_point_to_segment(px, py, ax, ay, bx, by) - hw
        if d < best:
            best = d
    return best


# ==============================================================================
# Terrain Field Evaluation (100% D4-Symmetric)
# ==============================================================================

def evaluate_corner(cx: int, cy: int) -> Tuple[float, float, int, int, int, int]:
    """
    Evaluate terrain corner (cx, cy) in [0..192] x [0..192].
    Returns: (ground_height, water_height, is_water, ground_tex, ground_var, is_boundary_edge)
    """
    wx = CENTER_OFFSET_X + cx * TILE_SIZE
    wy = CENTER_OFFSET_Y + cy * TILE_SIZE
    u, v = d4_canonical(wx, wy)  # 0 <= u <= v <= 12288
    r = math.hypot(u, v)

    # Check map boundary margin
    in_camera_margin = (abs(wx) > PLAYABLE_MAX_X) or (abs(wy) > PLAYABLE_MAX_Y)
    is_outer_edge = (cx == 0 or cy == 0 or cx == CORNERS_W - 1 or cy == CORNERS_H - 1)

    # 1. Base & Expansion flat buildable zones (100% flat +0.25 height!)
    d_base = min(math.hypot(u - 3840.0, v - 8960.0), math.hypot(u - 3840.0, v - 9600.0) + 180.0)
    d_nat = math.hypot(u - 2304.0, v - 6272.0)
    d_corner_mine = math.hypot(u - 9472.0, v - 9472.0)

    flat_weight = max(
        1.0 - smoothstep(1150.0, 1650.0, d_base),
        1.0 - smoothstep(780.0, 1200.0, d_nat),
        1.0 - smoothstep(780.0, 1200.0, d_corner_mine),
    )

    # 2. General rolling Lordaeron landscape height
    # Gentle symmetric cosine waves + raised central Crown Island + outer border ridge
    wave = 0.08 * math.cos(u * math.pi / 2048.0) * math.cos(v * math.pi / 2048.0)
    gh = 0.25 + wave * (1.0 - flat_weight)

    # Raised Central Crown Sanctum (r <= 1920)
    if r < 2100.0:
        crown_t = 1.0 - smoothstep(1550.0, 2080.0, r)
        gh = gh * (1.0 - crown_t) + 0.46 * crown_t

    # Raised Inner Bastions around Mercenary Camps (0, 4992) & Health Fountains (4608, 4608)
    d_merc = math.hypot(u - 0.0, v - 4992.0)
    d_fount = math.hypot(u - 4608.0, v - 4608.0)
    bastion_t = max(
        1.0 - smoothstep(650.0, 1150.0, d_merc),
        1.0 - smoothstep(650.0, 1150.0, d_fount),
    )
    if bastion_t > 0.0:
        gh = gh * (1.0 - bastion_t) + 0.36 * bastion_t

    # Outer border scenic mountain rim outside playable area (v > 11136)
    if v > 10880.0:
        rim_t = smoothstep(10880.0, 12032.0, v)
        gh += 0.95 * rim_t * (1.0 - flat_weight)

    # 3. Silverwater Moat Ring: r in [1980, 3140]
    # Crossed by:
    #  - 4 Cardinal Dry Causeways (u <= 520, smooth ramp up to 740)
    #  - 4 Diagonal Shallow Walkable Fords (|v - u| / sqrt(2) <= 520)
    #  - 8 Deep Turquoise Lagoons in between!
    is_water = 0
    diag_perp = abs(v - u) / math.sqrt(2.0)  # distance to diagonal y = x
    card_perp = u                            # distance to cardinal x = 0

    if 1860.0 <= r <= 3260.0:
        # Normalized radial profile of moat (1.0 inside [2120, 3000], smooth banks outside)
        moat_radial = smoothstep(1860.0, 2140.0, r) * (1.0 - smoothstep(2980.0, 3260.0, r))
        causeway_mask = 1.0 - smoothstep(480.0, 760.0, card_perp)  # 1 on dry bridge, 0 in water

        if moat_radial > 0.02 and causeway_mask < 0.98:
            ford_mask = 1.0 - smoothstep(460.0, 780.0, diag_perp)  # 1 on shallow ford, 0 in deep lagoon
            # Target floor: -0.28 for shallow walkable ford (~36 depth), -1.12 for deep lagoon (~143 depth)
            target_floor = -0.28 * ford_mask + (-1.12) * (1.0 - ford_mask)
            water_blend = moat_radial * (1.0 - causeway_mask)
            gh = gh * (1.0 - water_blend) + target_floor * water_blend
            if gh < 0.06:
                is_water = 1

    # Enforce strict flatness inside base/expansion zones
    if flat_weight >= 0.999:
        gh = 0.25
        is_water = 0

    # 4. Ground Texture Selection (100% D4-Symmetric)
    road_d = min_road_margin(wx, wy)
    # Canonical hash for symmetric organic variation
    cu, cv = int(round(u / 128.0)), int(round(v / 128.0))
    sym_hash = ((cu * 73856093) ^ (cv * 19349663)) & 0xFFFF

    if is_water:
        if gh < -0.58:
            tex = TEX_ROCK  # Deep lagoon rocky floor
        else:
            tex = TEX_DIRT  # Sandy/pebble shallow ford & shoreline
    elif r <= 820.0:
        # Crown Shrine courtyard: the raised stone dais stays unchanged, while eight
        # buildable pale-stone spokes tie it visually into the cardinal/diagonal roads.
        if 360.0 <= r <= 620.0:
            tex = TEX_ROCK
        elif 620.0 < r <= 820.0:
            shrine_angle = math.atan2(u, v) if v else 0.0
            tex = TEX_GRASSY_DIRT if math.cos(8.0 * shrine_angle) > 0.18 else TEX_ROUGH_DIRT
        else:
            tex = TEX_ROUGH_DIRT
    elif road_d < -60.0 and flat_weight < 0.7:
        tex = TEX_ROUGH_DIRT
    elif road_d < 90.0 and flat_weight < 0.7:
        tex = TEX_GRASSY_DIRT
    elif v > 11392.0 and flat_weight < 0.2:
        tex = TEX_ROCK  # Unbuildable outer rim cliffs
    elif flat_weight > 0.65:
        # Clean buildable grass in bases & expansions (NEVER TEX_ROCK!)
        tex = TEX_GRASS if (sym_hash % 5 != 0) else TEX_GRASSY_DIRT
    else:
        # Natural Lordaeron meadows & dark forest floor
        tex = TEX_DARK_GRASS if (sym_hash % 3 == 0) else TEX_GRASS

    # Ground texture variation (0..31, mostly 0..15)
    r_var = sym_hash % 100
    if r_var < 75:
        gvar = sym_hash % 8
    elif r_var < 95:
        gvar = 8 + (sym_hash % 8)
    else:
        gvar = 16 + (sym_hash % 16)

    boundary_flag = 1 if in_camera_margin else 0
    edge_flag = 1 if is_outer_edge else 0
    return gh, WATER_HEIGHT_CONST, is_water, tex, gvar, (boundary_flag | (edge_flag << 1))


# ==============================================================================
# Units, Buildings, Creeps & Trees Placement
# ==============================================================================

def generate_units_and_camps(terrain_heights: List[List[float]]) -> Tuple[List[PlacedUnit], List[Dict[str, object]]]:
    """Generate all D4-symmetric Start Locations, Gold Mines, Neutral Buildings, and 36 Creep Camps."""
    units: List[PlacedUnit] = []
    camp_summaries: List[Dict[str, object]] = []
    next_creation = 0

    def sample_z(wx: float, wy: float) -> float:
        fx = (wx - CENTER_OFFSET_X) / TILE_SIZE
        fy = (wy - CENTER_OFFSET_Y) / TILE_SIZE
        ix = max(0, min(CORNERS_W - 2, int(fx)))
        iy = max(0, min(CORNERS_H - 2, int(fy)))
        tx, ty = fx - ix, fy - iy
        h00 = terrain_heights[iy][ix]
        h10 = terrain_heights[iy][ix + 1]
        h01 = terrain_heights[iy + 1][ix]
        h11 = terrain_heights[iy + 1][ix + 1]
        h = (h00 * (1 - tx) + h10 * tx) * (1 - ty) + (h01 * (1 - tx) + h11 * tx) * ty
        return h * 128.0

    def add_unit(
        uid: str,
        player: int,
        x: float,
        y: float,
        angle_deg: float = 270.0,
        gold: int = 12500,
        acq_range: float = -1.0,
        drops: Optional[List[ItemDropSpec]] = None,
        camp_id: Optional[int] = None,
        role: str = "",
    ) -> PlacedUnit:
        nonlocal next_creation
        u = PlacedUnit(
            uid=uid,
            player=player,
            x=x,
            y=y,
            z=sample_z(x, y),
            angle_deg=angle_deg % 360.0,
            gold=gold,
            acq_range=acq_range,
            drops=list(drops) if drops else [],
            creation_num=next_creation,
            camp_id=camp_id,
            role=role,
        )
        next_creation += 1
        units.append(u)
        return u

    # 1. 8 Player Start Locations (`sloc`)
    for pid, (sx, sy) in enumerate(PLAYER_BASES):
        add_unit("sloc", pid, sx, sy, 270.0, gold=0, acq_range=0.0, role=f"Player {pid + 1} Start")

    # 2. 8 Main Base Gold Mines (`ngol`, 12,500 gold)
    for idx, (mx, my) in enumerate(MAIN_MINES):
        add_unit("ngol", 15, mx, my, 270.0, gold=12500, role=f"Main Gold Mine P{idx + 1}")

    # 3. 8 Natural Expansion Gold Mines (`ngol`, 12,500 gold)
    for idx, (mx, my) in enumerate(NATURAL_MINES):
        add_unit("ngol", 15, mx, my, 270.0, gold=12500, role=f"Natural Expansion Mine {idx + 1}")

    # 4. 4 Contested Corner Rich Gold Mines (`ngol`, 15,000 gold)
    for idx, (mx, my) in enumerate(CORNER_MINES):
        add_unit("ngol", 15, mx, my, 270.0, gold=15000, role=f"Corner High-Yield Mine {idx + 1}")

    # 5. Neutral Passive Buildings: 1 Central Tavern, 4 Merchants, 4 Labs, 4 Mercenary Camps, 4 Health Fountains
    add_unit("ntav", 15, CENTRAL_TAVERN[0], CENTRAL_TAVERN[1], 270.0, role="Central Royal Tavern")
    for x, y in GOBLIN_MERCHANTS:
        add_unit("ngme", 15, x, y, 270.0, role="Goblin Merchant")
    for x, y in GOBLIN_LABS:
        add_unit("ngad", 15, x, y, 270.0, role="Goblin Laboratory")
    for x, y in MERC_CAMPS:
        add_unit("nmer", 15, x, y, 270.0, role="Mercenary Camp (Lordaeron)")
    for x, y in HEALTH_FOUNTAINS:
        add_unit("nfoh", 15, x, y, 270.0, role="Fountain of Health")

    # 6. Hostile Creep Camps (All 36 symmetric camps, acq_range = -2.0 => 200.0 Camp Mode!)
    camp_counter = 0

    def spawn_camp_group(
        tier: str,
        title: str,
        center: Tuple[float, float],
        look_target: Tuple[float, float],
        members: List[Tuple[str, float, float, List[ItemDropSpec]]],
        handedness: float = 1.0,
    ) -> None:
        """
        members: list of (uid, forward_offset, right_offset, drops) relative to camp facing direction.
        """
        nonlocal camp_counter
        cid = camp_counter
        camp_counter += 1
        cx, cy = center
        dx, dy = look_target[0] - cx, look_target[1] - cy
        norm = math.hypot(dx, dy) or 1.0
        fx, fy = dx / norm, dy / norm
        # The sign is the determinant of the D4 transform. Reflections reverse handedness;
        # without this, asymmetric camp members/items shift to the wrong side of mirrored starts.
        rx, ry = handedness * fy, -handedness * fx
        facing_deg = (math.degrees(math.atan2(fy, fx)) + 360.0) % 360.0

        unit_ids = []
        drop_labels = []
        for uid, f_off, r_off, drops in members:
            ux = cx + fx * f_off + rx * r_off
            uy = cy + fy * f_off + ry * r_off
            add_unit(uid, 12, ux, uy, facing_deg, gold=12500, acq_range=-2.0, drops=drops, camp_id=cid, role=title)
            unit_ids.append(uid)
            for d in drops:
                drop_labels.append(d.label)

        camp_summaries.append({
            "id": cid,
            "tier": tier,
            "name": title,
            "x": round(cx, 1),
            "y": round(cy, 1),
            "units": unit_ids,
            "drops": drop_labels,
        })

    # Reusable Blizzard Melee Item Drop Specs
    DROP_PERM_1 = ItemDropSpec("YiI1", "ChooseRandomItemEx( ITEM_TYPE_PERMANENT, 1 )", "Permanent Lvl 1")
    DROP_PERM_2 = ItemDropSpec("YiI2", "ChooseRandomItemEx( ITEM_TYPE_PERMANENT, 2 )", "Permanent Lvl 2")
    DROP_PERM_3 = ItemDropSpec("YiI3", "ChooseRandomItemEx( ITEM_TYPE_PERMANENT, 3 )", "Permanent Lvl 3")
    DROP_PERM_5 = ItemDropSpec("YiI5", "ChooseRandomItemEx( ITEM_TYPE_PERMANENT, 5 )", "Permanent Lvl 5")
    DROP_CHRG_2 = ItemDropSpec("YjI2", "ChooseRandomItemEx( ITEM_TYPE_CHARGED, 2 )", "Charged Lvl 2")
    DROP_CHRG_3 = ItemDropSpec("YjI3", "ChooseRandomItemEx( ITEM_TYPE_CHARGED, 3 )", "Charged Lvl 3")
    DROP_CHRG_4 = ItemDropSpec("YjI4", "ChooseRandomItemEx( ITEM_TYPE_CHARGED, 4 )", "Charged Lvl 4")
    DROP_TOME_XP = ItemDropSpec("texp", "'texp'", "Tome of Experience")

    # (A) 8 Green Gnoll Outposts (Orbit of (6400, 9600), recessed off flank junction (5760, 8064))
    for transform_id, (center, target) in enumerate(zip(GREEN_GNOLL_CENTERS, d4_transforms(5760.0, 8064.0))):
        spawn_camp_group(
            "green",
            "Gnoll Outpost (Lvl 6)",
            center,
            target,
            [
                ("ngnw", -40.0, 0.0, [DROP_PERM_1]),
                ("ngna", 20.0, -110.0, []),
                ("ngno", 55.0, 0.0, []),
                ("ngno", 20.0, +110.0, []),
            ],
            handedness=D4_DETERMINANTS[transform_id],
        )

    # (B) 8 Orange Natural Expansion Ogre Magi Camps (Orbit in front of (2304, 6272))
    for transform_id, (mine_pt, hub_pt) in enumerate(zip(NATURAL_MINES, d4_transforms(2816.0, 6528.0))):
        vx, vy = hub_pt[0] - mine_pt[0], hub_pt[1] - mine_pt[1]
        vn = math.hypot(vx, vy)
        cx, cy = mine_pt[0] + vx / vn * 340.0, mine_pt[1] + vy / vn * 340.0
        spawn_camp_group(
            "orange",
            "Ogre Expansion Guard (Lvl 13)",
            (cx, cy),
            hub_pt,
            [
                ("nomg", -35.0, -55.0, [DROP_PERM_3]),
                ("nfsp", -35.0, +55.0, [DROP_CHRG_2]),
                ("nogr", +65.0, -95.0, []),
                ("nogr", +65.0, +95.0, []),
            ],
            handedness=D4_DETERMINANTS[transform_id],
        )

    # (C) 4 Orange Goblin Merchant Camps (350 units inward from recessed (0, +-8704), (+-8704, 0))
    for sx, sy in GOBLIN_MERCHANTS:
        sn = math.hypot(sx, sy)
        nx, ny = -sx / sn, -sy / sn
        cx, cy = sx + nx * 350.0, sy + ny * 350.0
        spawn_camp_group(
            "orange",
            "Merchant Guard (Lvl 13)",
            (cx, cy),
            (0.0, 0.0),
            [
                ("ngnv", -30.0, 0.0, [DROP_PERM_2, DROP_CHRG_2]),
                ("nftb", +45.0, 0.0, []),
                ("nftr", +30.0, -120.0, []),
                ("nftr", +30.0, +120.0, []),
            ],
        )

    # (D) 4 Orange Goblin Laboratory Camps (370 units inward along diagonal from (+-7424, +-7424))
    for lx, ly in GOBLIN_LABS:
        ln = math.hypot(lx, ly)
        cx, cy = lx - (lx / ln) * 370.0, ly - (ly / ln) * 370.0
        spawn_camp_group(
            "orange",
            "Laboratory Troll Guard (Lvl 12)",
            (cx, cy),
            (0.0, 0.0),
            [
                # The diagonal center is fixed by a D4 reflection, so place its two
                # different troll types on the forward axis instead of swapping sides.
                ("nftb", -75.0, 0.0, [DROP_CHRG_3]),
                ("nfsh", +75.0, 0.0, []),
                ("nftr", +60.0, -105.0, []),
                ("nftr", +60.0, +105.0, []),
            ],
        )

    # (E) 4 Orange Mercenary Camp Rock Golem Guards (in Twin-Boulevard Shrine Island at (0, +-4992))
    for mx, my in MERC_CAMPS:
        mn = math.hypot(mx, my)
        cx, cy = mx + (mx / mn) * 360.0, my + (my / mn) * 360.0
        spawn_camp_group(
            "orange",
            "Mercenary Golem Guard (Lvl 10)",
            (cx, cy),
            (mx * 2.0, my * 2.0),
            [
                ("ngst", -20.0, 0.0, [DROP_PERM_3]),
                ("ngrk", +55.0, -110.0, []),
                ("ngrk", +55.0, +110.0, []),
            ],
        )

    # (F) 4 Red Corner Rich Gold Mine Granite Golem Boss Camps (390 units inward from (+-9472, +-9472))
    for mx, my in CORNER_MINES:
        mn = math.hypot(mx, my)
        cx, cy = mx - (mx / mn) * 390.0, my - (my / mn) * 390.0
        spawn_camp_group(
            "red",
            "Ancient Granite Boss (Lvl 21)",
            (cx, cy),
            (0.0, 0.0),
            [
                ("nggr", -35.0, 0.0, [DROP_PERM_5, DROP_CHRG_4]),
                ("ngst", +60.0, -115.0, []),
                ("ngst", +60.0, +115.0, []),
            ],
        )

    # (G) 4 Red Fountain Dragon & Ogre Lord Camps (in Twin-Boulevard Dragon Island at (+-4608, +-4608))
    for fx, fy in HEALTH_FOUNTAINS:
        fn = math.hypot(fx, fy)
        cx, cy = fx + (fx / fn) * 370.0, fy + (fy / fn) * 370.0
        spawn_camp_group(
            "red",
            "Red Dragon Sanctum (Lvl 23)",
            (cx, cy),
            (fx * 2.0, fy * 2.0),
            [
                # The diagonal island is fixed by a D4 reflection: keep each unique
                # drop-carrying guard on-axis and mirror the two identical dark knights.
                ("nrwm", -60.0, 0.0, [DROP_PERM_5, DROP_TOME_XP]),
                ("nogl", +60.0, 0.0, [DROP_CHRG_4]),
                ("nrdk", +65.0, -115.0, []),
                ("nrdk", +65.0, +115.0, []),
            ],
        )

    return units, camp_summaries


def generate_trees(
    terrain_heights: List[List[float]],
    terrain_water: List[List[int]],
    units: List[PlacedUnit],
) -> List[PlacedTree]:
    """
    Place D4-symmetric harvestable Lordaeron Summer Trees (`LTlt`) on exact 128-unit tile centers,
    guaranteeing zero overlap with bases, mines, neutral buildings, creeps, water, and roads.
    """
    # Build fast spatial exclusion list from units
    exclusions: List[Tuple[float, float, float]] = []
    for u in units:
        if u.uid == "sloc":
            exclusions.append((u.x, u.y, 1024.0))  # Spacious buildable town hall plaza
        elif u.uid == "ngol":
            exclusions.append((u.x, u.y, 500.0))   # Crisp clearance all around gold mine, close back lumber!
        elif u.player == 15:
            exclusions.append((u.x, u.y, 580.0))   # Tavern, Merchants, Labs, MercCamps, Fountains
        else:
            exclusions.append((u.x, u.y, 340.0))   # Creep camp clearing

    trees: List[PlacedTree] = []
    editor_id = 1000
    seen_coords = set()

    # Iterate over fundamental wedge 0 <= tx <= ty in tile coordinates around center (96, 96)
    for ty in range(96, TILES_H - 2):
        for tx in range(96, ty + 1):
            wx = CENTER_OFFSET_X + (tx + 0.5) * TILE_SIZE
            wy = CENTER_OFFSET_Y + (ty + 0.5) * TILE_SIZE
            u, v = d4_canonical(wx, wy)
            r = math.hypot(u, v)

            # Never place trees in water or shoreline
            if (
                terrain_water[ty][tx]
                or terrain_water[ty][tx + 1]
                or terrain_water[ty + 1][tx]
                or terrain_water[ty + 1][tx + 1]
            ):
                continue
            if 1820.0 <= r <= 3320.0:
                continue  # Keep Silverwater Moat banks scenic and open

            # Keep roads wide and clear (extra 180-unit tree buffer outside road edges)
            if min_road_margin(wx, wy) < 180.0:
                continue

            # Determine desired forest zones (100% D4-invariant function of (u, v)):
            want_tree = False

            # 1) Crisp Map Perimeter Forest Border (playable edge 11008..11392)
            if v >= 11008.0 and v <= 11392.0 and u <= 11392.0:
                want_tree = True

            # 2) Continuous U-Shaped Fortress Treeline around each Main Base (3840, 8960..9600)
            d_base_ring = math.hypot(u - 3840.0, (v - 9152.0) * 0.92)
            if 1120.0 <= d_base_ring <= 1450.0 and v >= 8384.0:
                want_tree = True
            # Close-in back lumber behind Gold Mine (>= 512 clearance from mine)
            d_mine = math.hypot(u - 3840.0, v - 9600.0)
            if 512.0 <= d_mine <= 1120.0 and v >= 9728.0:
                want_tree = True

            # 3) Natural Expansion Lumber Grove behind (2304, 6272)
            d_nat = math.hypot(u - 2304.0, v - 6272.0)
            if 540.0 <= d_nat <= 980.0 and (u < 2048.0 or v < 6016.0):
                want_tree = True

            # 4) Alcove Horseshoes & Tactical Sight-Blocker Forest Islands
            # Behind Goblin Merchant alcove (0, 8704)
            d_merch = math.hypot(u - 0.0, v - 8704.0)
            if 600.0 <= d_merch <= 1040.0 and v >= 8576.0:
                want_tree = True
            # Behind Corner Gold Mine (9472, 9472)
            d_cmine = math.hypot(u - 9472.0, v - 9472.0)
            if 560.0 <= d_cmine <= 1150.0 and (u >= 9344.0 or v >= 9344.0):
                want_tree = True
            # Mid-map tactical islands between twin boulevards
            if math.hypot(u - 1664.0, v - 8320.0) <= 480.0:
                want_tree = True
            if math.hypot(u - 4864.0, v - 6912.0) <= 500.0:
                want_tree = True
            if math.hypot(u - 2304.0, v - 4864.0) <= 420.0:
                want_tree = True
            if math.hypot(u - 7808.0, v - 9984.0) <= 480.0:
                want_tree = True

            # 5) 8 Ornamental Royal Groves framing Central Crown Island (r in [1120, 1520] off bridges)
            if 1120.0 <= r <= 1520.0 and u >= 560.0 and abs(v - u) / math.sqrt(2.0) >= 560.0:
                want_tree = True

            if not want_tree:
                continue

            # Deterministic organic edge-thinning hash
            cu, cv = int(round((u - 64.0) / 128.0)), int(round((v - 64.0) / 128.0))
            thash = ((cu * 2654435761) ^ (cv * 2246822519)) & 0xFFFFFFFF

            # Check all 8 symmetric images against exclusions
            pts = d4_transforms(wx, wy)
            blocked = False
            for px, py in pts:
                if abs(px) > PLAYABLE_MAX_X - 128.0 or abs(py) > PLAYABLE_MAX_Y - 128.0:
                    blocked = True
                    break
                for ex, ey, er in exclusions:
                    if (px - ex) ** 2 + (py - ey) ** 2 < er * er:
                        blocked = True
                        break
                if blocked:
                    break
            if blocked:
                continue

            variation = thash % 10
            scale = 0.86 + (thash % 29) * 0.012  # 0.86 .. 1.20; organic canopy variation (no pathing changes)
            angle_deg = float((thash >> 8) % 360)

            for px, py in pts:
                key = (int(round(px)), int(round(py)))
                if key in seen_coords:
                    continue
                seen_coords.add(key)
                gx = int((px - CENTER_OFFSET_X) // TILE_SIZE)
                gy = int((py - CENTER_OFFSET_Y) // TILE_SIZE)
                gz = (
                    terrain_heights[gy][gx]
                    + terrain_heights[gy][gx + 1]
                    + terrain_heights[gy + 1][gx]
                    + terrain_heights[gy + 1][gx + 1]
                ) * 0.25 * 128.0
                trees.append(
                    PlacedTree(
                        did="ZTtw",
                        variation=variation,
                        x=px,
                        y=py,
                        z=gz,
                        angle_deg=angle_deg,
                        scale=scale,
                        editor_id=editor_id,
                        life=100,
                    )
                )
                editor_id += 1

    # Add non-blocking (`pathTex = none`!) Scenic Astral Shrine & Bioluminescent Doodads!
    def _ground_z(wx_p: float, wy_p: float) -> float:
        gx_p = max(0, min(TILES_W - 1, int((wx_p - CENTER_OFFSET_X) // TILE_SIZE)))
        gy_p = max(0, min(TILES_H - 1, int((wy_p - CENTER_OFFSET_Y) // TILE_SIZE)))
        return (
            terrain_heights[gy_p][gx_p]
            + terrain_heights[gy_p][gx_p + 1]
            + terrain_heights[gy_p + 1][gx_p]
            + terrain_heights[gy_p + 1][gx_p + 1]
        ) * 0.25 * 128.0

    # 1) Floating Astral Crown Artifact (`ZZys`) and a brighter eight-rune courtyard.
    trees.append(PlacedTree("ZZys", 0, 0.0, 0.0, _ground_z(0.0, 0.0) + 68.0, 270.0, 1.82, editor_id, 255))
    editor_id += 1
    for k in range(8):
        ang = k * (math.pi / 4.0)
        rx, ry = 430.0 * math.cos(ang), 430.0 * math.sin(ang)
        trees.append(PlacedTree("ZZgr", k % 2, rx, ry, _ground_z(rx, ry), k * 45.0, 1.32, editor_id, 255))
        editor_id += 1
        # Bioluminescent flames form an exact eightfold ring between the shrine avenues.
        bx, by = 920.0 * math.cos(ang + math.pi / 8.0), 920.0 * math.sin(ang + math.pi / 8.0)
        trees.append(PlacedTree("YOfb", 0, bx, by, _ground_z(bx, by), 0.0, 1.24, editor_id, 255))
        editor_id += 1
        # Two D4-matched bands of bubbles and lilies give each moat lagoon more depth.
        for ring_index, radius in enumerate((2050.0, 2700.0)):
            water_angle = ang + math.pi / 8.0
            wx_m, wy_m = radius * math.cos(water_angle), radius * math.sin(water_angle)
            trees.append(PlacedTree("ZWbg", 0, wx_m, wy_m, 0.0, 0.0, 1.10 if ring_index == 0 else 0.92, editor_id, 255))
            editor_id += 1
            pad_radius = radius + (96.0 if ring_index == 0 else -112.0)
            px_m, py_m = pad_radius * math.cos(water_angle), pad_radius * math.sin(water_angle)
            trees.append(PlacedTree("ZPlp", k % 2, px_m, py_m, 0.0, k * 45.0, 1.08 if ring_index == 0 else 0.96, editor_id, 255))
            editor_id += 1

    # 2) Sacred Runic Circles (`ZZgr`) + Blue Astral Flames (`YOfb`) at all 8 Player Citadels!
    for idx_b, (sx_b, sy_b) in enumerate(PLAYER_BASES):
        trees.append(PlacedTree("ZZgr", idx_b % 2, sx_b * 0.94, sy_b * 0.94, _ground_z(sx_b * 0.94, sy_b * 0.94), idx_b * 45.0, 1.10, editor_id, 255))
        editor_id += 1

    return trees


# ==============================================================================
# Binary Format Serializers (All Standard & Altered Melee Map Files)
# ==============================================================================

def serialize_w3e(corners_data: List[List[Tuple[float, float, int, int, int, int]]]) -> bytes:
    """Serialize war3map.w3e (version 11, Sunken-Astral Ruins tileset 'Z')."""
    out = bytearray()
    out += b"W3E!"
    out += struct.pack("<i", 11)
    out += b"Z"
    out += struct.pack("<i", 0)  # haveCustomTileset = 0 (authentic Sunken Ruins Z palette)
    out += struct.pack("<I", len(GROUND_TILESETS))
    for gt in GROUND_TILESETS:
        out += gt.encode("ascii")
    out += struct.pack("<I", len(CLIFF_TILESETS))
    for ct in CLIFF_TILESETS:
        out += ct.encode("ascii")
    out += struct.pack("<ii", CORNERS_W, CORNERS_H)
    out += struct.pack("<ff", CENTER_OFFSET_X, CENTER_OFFSET_Y)

    for cy in range(CORNERS_H):
        row = corners_data[cy]
        for cx in range(CORNERS_W):
            gh, wh, is_water, tex, gvar, bflags = row[cx]
            gh_raw = max(0, min(16383, int(round(gh * 512.0 + 8192.0))))
            wh_raw = max(0, min(16383, int(round(wh * 512.0 + 8192.0))))
            map_edge_bit = 0x4000 if (bflags & 2) else 0
            water_and_edge = (wh_raw & 0x3FFF) | map_edge_bit
            boundary_bit = 0x80 if (bflags & 1) else 0
            water_bit = 0x40 if is_water else 0
            tex_flags = (tex & 0x0F) | water_bit | boundary_bit
            variation_byte = gvar & 0x1F  # cliffVariation = 0
            cliff_layer_byte = (0x0F << 4) | 2  # cliffTexture = 15 (none), layerHeight = 2
            out += struct.pack("<hHBBB", gh_raw, water_and_edge, tex_flags, variation_byte, cliff_layer_byte)

    return bytes(out)


def serialize_wpm(corners_data: List[List[Tuple[float, float, int, int, int, int]]]) -> bytes:
    """
    Serialize war3map.wpm (MP3W version 0, 768x768 static terrain pathing cells).
    Bitflags verified against Blizzard World Editor:
      0x02 = UNWALKABLE
      0x04 = UNFLYABLE
      0x08 = UNBUILDABLE
      0x20 = BLIGHT
      0x40 = NOWATER (set on all dry land!)
      0x80 = BOUNDARY / CAMERA MARGIN
    """
    path = bytearray(PATH_W * PATH_H)
    for py in range(PATH_H):
        ty = py // 4
        fy = (py % 4 + 0.5) / 4.0
        wy = CENTER_OFFSET_Y + (py + 0.5) * PATH_CELL
        for px in range(PATH_W):
            tx = px // 4
            fx = (px % 4 + 0.5) / 4.0
            wx = CENTER_OFFSET_X + (px + 0.5) * PATH_CELL

            # Outer 2-tile border (unflyable + boundary + unwalkable + unbuildable + dry)
            if px < 8 or py < 8 or px >= PATH_W - 8 or py >= PATH_H - 8:
                path[py * PATH_W + px] = 0xCE  # 206
                continue

            # Camera margin boundary (outside playable 180x180 area)
            if wx < PLAYABLE_MIN_X or wx > PLAYABLE_MAX_X or wy < PLAYABLE_MIN_Y or wy > PLAYABLE_MAX_Y:
                path[py * PATH_W + px] = 0xCA  # 202
                continue

            c00 = corners_data[ty][tx]
            c10 = corners_data[ty][tx + 1]
            c01 = corners_data[ty + 1][tx]
            c11 = corners_data[ty + 1][tx + 1]

            gh = (c00[0] * (1 - fx) + c10[0] * fx) * (1 - fy) + (c01[0] * (1 - fx) + c11[0] * fx) * fy
            any_water = c00[2] or c10[2] or c01[2] or c11[2]
            all_water = c00[2] and c10[2] and c01[2] and c11[2]
            any_rock = (c00[3] == TEX_ROCK) or (c10[3] == TEX_ROCK) or (c01[3] == TEX_ROCK) or (c11[3] == TEX_ROCK)
            slope = max(c00[0], c10[0], c01[0], c11[0]) - min(c00[0], c10[0], c01[0], c11[0])

            if all_water or (any_water and gh < 0.02):
                # Water cell: surface at 0.0 world Z; ground at gh * 128.0 world Z
                depth_world = -gh * 128.0
                if depth_world > 64.0:
                    path[py * PATH_W + px] = 0x0A  # Deep water: UNWALKABLE | UNBUILDABLE
                else:
                    path[py * PATH_W + px] = 0x08  # Shallow walkable ford: UNBUILDABLE
            else:
                # Dry land: NOWATER (0x40)
                if any_rock or any_water or slope > 0.32:
                    path[py * PATH_W + px] = 0x48  # Walkable, unbuildable dry ground (72)
                else:
                    path[py * PATH_W + px] = 0x40  # Walkable & buildable dry ground (64)

    out = bytearray(16 + len(path))
    struct.pack_into("<4siii", out, 0, b"MP3W", 0, PATH_W, PATH_H)
    out[16:] = path
    return bytes(out)


def serialize_shd(
    corners_data: List[List[Tuple[float, float, int, int, int, int]]],
    trees: List[PlacedTree],
) -> bytes:
    """Serialize war3map.shd (768x768 bytes: 0x00 lit, 0xFF soft shadow)."""
    shd = bytearray(PATH_W * PATH_H)

    # Subtle hillside directional shadow
    for py in range(1, PATH_H - 1):
        ty = py // 4
        for px in range(1, PATH_W - 1):
            tx = px // 4
            dx = corners_data[ty][min(CORNERS_W - 1, tx + 1)][0] - corners_data[ty][tx][0]
            dy = corners_data[min(CORNERS_H - 1, ty + 1)][tx][0] - corners_data[ty][tx][0]
            if dx + dy < -0.22:
                shd[py * PATH_W + px] = 0xFF

    # Tree canopy shadows offset +2 cells East, +1 cell North (trees only)
    for t in trees:
        if t.did != "ZTtw":
            continue
        cpx = int((t.x - CENTER_OFFSET_X) // PATH_CELL) + 2
        cpy = int((t.y - CENTER_OFFSET_Y) // PATH_CELL) + 1
        for oy in range(-1, 2):
            for ox in range(-1, 2):
                sx, sy = cpx + ox, cpy + oy
                if 0 <= sx < PATH_W and 0 <= sy < PATH_H:
                    shd[sy * PATH_W + sx] = 0xFF

    return bytes(shd)


def serialize_doo(trees: List[PlacedTree]) -> bytes:
    """Serialize war3map.doo (TFT version 8, subversion 11, trees + scenic shrine doodads)."""
    out = bytearray()
    out += b"W3do"
    out += struct.pack("<i", 8)
    out += bytes([11, 0, 0, 0])  # subversion 11
    out += struct.pack("<I", len(trees))
    for t in trees:
        out += t.did.encode("ascii")
        out += struct.pack("<i", t.variation)
        out += struct.pack("<fff", t.x, t.y, t.z)
        out += struct.pack("<f", math.radians(t.angle_deg))
        out += struct.pack("<fff", t.scale, t.scale, t.scale)
        out += struct.pack("<BB", 2, t.life)  # flags=2 (visible), life=100 (tree) or 255 (doodad)
        out += struct.pack("<II", 0xFFFFFFFF, 0)  # itemTable=-1, itemSets.length=0
        out += struct.pack("<i", t.editor_id)
    out += bytes([0, 0, 0, 0])  # special terrain doodads version 0
    out += struct.pack("<I", 0)  # 0 special terrain doodads
    return bytes(out)


def serialize_units_doo(units: List[PlacedUnit]) -> bytes:
    """Serialize war3mapUnits.doo (TFT version 8, subversion 11)."""
    out = bytearray()
    out += b"W3do"
    out += struct.pack("<iI", 8, 11)
    out += struct.pack("<i", len(units))

    for u in units:
        is_sloc = u.uid == "sloc"
        out += u.uid.encode("ascii")
        out += struct.pack("<i", 0)  # variation
        out += struct.pack("<fff", u.x, u.y, u.z)
        out += struct.pack("<f", math.radians(u.angle_deg))
        out += struct.pack("<fff", 1.0, 1.0, 1.0)
        out += struct.pack("<B", 2)  # flags = 2
        out += struct.pack("<i", u.player)
        out += struct.pack("<H", 0)  # unknown = 0
        out += struct.pack("<ii", 0 if is_sloc else -1, 0 if is_sloc else -1)  # hp, mana
        out += struct.pack("<i", -1)  # droppedItemTable = -1

        # droppedItemSets
        out += struct.pack("<i", len(u.drops))
        for d in u.drops:
            out += struct.pack("<i", 1)  # 1 item option with 100% chance in this set
            out += d.raw_doo_id.encode("ascii")
            out += struct.pack("<i", 100)

        out += struct.pack("<if", 0 if is_sloc else u.gold, 0.0 if is_sloc else u.acq_range)
        out += struct.pack("<iiii", 0 if is_sloc else 1, 0, 0, 0)  # heroLevel, Str, Agi, Int
        out += struct.pack("<ii", 0, 0)  # 0 inventory items, 0 modified abilities
        out += struct.pack("<i", 0)      # randomFlag = 0
        out += bytes([1, 0, 0])          # level = [1, 0, 0]
        out += struct.pack("<B", 0)      # itemClass = 0
        out += struct.pack("<iii", -1, -1, u.creation_num)  # customTeamColor=-1, waygate=-1, creationNumber

    return bytes(out)


def serialize_w3i() -> bytes:
    """Serialize war3map.w3i (Frozen Throne version 25 for classic 1.26a/1.27b clients)."""
    def cstr(s: str) -> bytes:
        return s.encode("utf-8") + b"\x00"

    out = bytearray()
    out += struct.pack("<iii", 25, 1, 6059)  # version=25, saves=1, editorVersion=6059 (TFT WE)
    out += cstr("TRIGSTR_001")  # Map Name
    out += cstr("TRIGSTR_002")  # Author
    out += cstr("TRIGSTR_003")  # Description
    out += cstr("TRIGSTR_004")  # Recommended Players

    # Camera bounds (8 floats: BL.x, BL.y, TR.x, TR.y, TL.x, TL.y, BR.x, BR.y)
    out += struct.pack(
        "<8f",
        CAM_LEFT, CAM_BOTTOM,
        CAM_RIGHT, CAM_TOP,
        CAM_LEFT, CAM_TOP,
        CAM_RIGHT, CAM_BOTTOM,
    )
    out += struct.pack("<4i", *COMPLEMENTS)
    out += struct.pack("<2i", PLAYABLE_TILES_W, PLAYABLE_TILES_H)
    out += struct.pack("<I", MAP_FLAGS)
    out += b"Z"                  # Sunken-Astral Ruins tileset ('Z')
    out += struct.pack("<i", -1) # loadingScreenId = -1 (8-player loading screen + custom Lobby war3mapPreview.tga)
    out += cstr("")              # loadingScreenModel
    out += cstr("TRIGSTR_007")   # loadingScreenText
    out += cstr("TRIGSTR_001")   # loadingScreenTitle
    out += cstr("TRIGSTR_006")   # loadingScreenSubtitle
    out += struct.pack("<i", 0)  # gameDataSet = 0 (Default TFT)
    out += cstr("")              # prologueScreenModel
    out += cstr("")              # prologueScreenText
    out += cstr("")              # prologueScreenTitle
    out += cstr("")              # prologueScreenSubtitle

    # Terrain fog & Astral-Cyan atmosphere
    out += struct.pack("<i", 1)  # useTerrainFog = 1 (Linear distance haze)
    out += struct.pack("<ff", 3200.0, 9600.0)
    out += struct.pack("<f", 0.0)
    out += bytes([36, 56, 108, 255])    # Deep Astral Sapphire distance fog
    out += struct.pack("<i", 0)         # globalWeather = 0
    out += cstr("")                     # soundEnvironment
    out += b"A"                         # lightEnvironmentTileset = 'A' (Ashenvale twilight lighting!)
    out += bytes([45, 215, 245, 225])   # Bioluminescent Cyan-Turquoise waterVertexColor

    # 8 Human/User Player Slots
    out += struct.pack("<I", 8)
    for pid, (sx, sy) in enumerate(PLAYER_BASES):
        prev_p = (pid + 7) % 8
        next_p = (pid + 1) % 8
        low_mask = (1 << ((pid + 6) % 8)) | (1 << ((pid + 2) % 8))
        high_mask = (1 << prev_p) | (1 << next_p)
        # race: 0 = selectable/random in standard melee; isFixedStartPosition = 0
        default_race = (pid % 4) + 1
        out += struct.pack("<iiii", pid, 1, default_race, 0)
        out += cstr(f"TRIGSTR_{10 + pid:03d}")
        out += struct.pack("<ff", sx, sy)
        out += struct.pack("<II", low_mask, high_mask)

    # 1 Default Melee Force containing all 8 players (unlocks Team 1..8 selector in WC3 lobby!)
    out += struct.pack("<I", 1)
    out += struct.pack("<II", 0, 0xFF)
    out += cstr("TRIGSTR_005")

    # 0 custom upgrades, 0 custom tech, 0 random unit tables, 0 random item tables
    out += struct.pack("<IIII", 0, 0, 0, 0)
    return bytes(out)


def serialize_wts() -> bytes:
    """Serialize war3map.wts (UTF-8 BOM + World Editor STRING table)."""
    entries = [
        (1, MAP_DISPLAY_NAME),
        (2, MAP_AUTHOR),
        (3, MAP_DESCRIPTION),
        (4, MAP_RECOMMENDED_PLAYERS),
        (5, "Forces"),
        (6, "8-Empire Sunken-Astral Altered Melee • v9"),
        (7, "4 Custom Empires + 4 Classic Races, 16 Heroes with 64 unique skills and 64 distinct spell MDX effects, host-first AI difficulty, faction-specific build strategies, and four dispatched custom melee-AI scripts with JASS hero micro and telemetry."),
    ]
    for pid in range(8):
        entries.append((10 + pid, f"Player {pid + 1}"))

    lines = ["\ufeff"]
    for num, val in entries:
        lines.append(f"STRING {num}\r\n{{\r\n{val}\r\n}}\r\n\r\n")
    return "".join(lines).encode("utf-8")


def serialize_wtg_and_wct() -> Tuple[bytes, bytes, bytes, bytes]:
    """
    Exact byte-for-byte World Editor GUI `Melee Initialization` trigger (war3map.wtg + war3map.wct)
    and empty war3map.w3r / war3map.w3c so World Editor opens and saves the map cleanly.
    """
    wtg_hex = (
        "57544721070000000100000000000000"
        "496e697469616c697a6174696f6e0000"
        "0000000200000000000000010000004d"
        "656c656520496e697469616c697a6174"
        "696f6e0044656661756c74206d656c65"
        "652067616d6520696e697469616c697a"
        "6174696f6e20666f7220616c6c20706c"
        "61796572730000000000010000000000"
        "00000000000000000000000000000900"
        "0000000000004d6170496e697469616c"
        "697a6174696f6e4576656e7400010000"
        "0000000000020000004d656c65655374"
        "617274696e675669736962696c697479"
        "000100000000000000020000004d656c"
        "65655374617274696e674865726f4c69"
        "6d697400010000000000000002000000"
        "4d656c65654772616e744865726f4974"
        "656d7300010000000000000002000000"
        "4d656c65655374617274696e67526573"
        "6f757263657300010000000000000002"
        "0000004d656c6565436c656172457863"
        "657373556e6974730001000000000000"
        "00020000004d656c6565537461727469"
        "6e67556e697473000100000000000000"
        "020000004d656c65655374617274696e"
        "67414900010000000000000002000000"
        "4d656c6565496e6974566963746f7279"
        "446566656174000100000000000000"
    )
    wct_hex = "0100000000000000000100000000000000"
    w3r_hex = "0500000000000000"
    w3c_hex = "0000000000000000"
    return (
        bytes.fromhex(wtg_hex),
        bytes.fromhex(wct_hex),
        bytes.fromhex(w3r_hex),
        bytes.fromhex(w3c_hex),
    )


def serialize_mmp(units: List[PlacedUnit]) -> bytes:
    """
    Serialize war3map.mmp (Minimap Icons):
      type 0 = Gold Mine
      type 1 = Neutral Building (Tavern, Goblin Merchant, Goblin Lab, Mercenary Camp, Fountain)
      type 2 = Player Start Location (colored in exact BGRA player colors 0..7)
    """
    icons: List[Tuple[int, int, int, Tuple[int, int, int, int]]] = []

    def world_to_mmp(wx: float, wy: float) -> Tuple[int, int]:
        mx = max(0, min(255, int(math.floor((wx - PLAYABLE_MIN_X) / PLAYABLE_SPAN * 256.0))))
        my = max(0, min(255, int(math.floor((PLAYABLE_MAX_Y - wy) / PLAYABLE_SPAN * 256.0))))
        return mx, my

    for u in units:
        if u.uid == "ngol":
            mx, my = world_to_mmp(u.x, u.y)
            icons.append((0, mx, my, (255, 255, 255, 255)))
        elif u.player == 15 and u.uid in ("ntav", "ngme", "ngad", "nmer", "nfoh"):
            mx, my = world_to_mmp(u.x, u.y)
            icons.append((1, mx, my, (255, 255, 255, 255)))

    for u in units:
        if u.uid == "sloc" and 0 <= u.player < 8:
            mx, my = world_to_mmp(u.x, u.y)
            icons.append((2, mx, my, PLAYER_COLORS_BGRA[u.player]))

    out = bytearray(8 + len(icons) * 16)
    struct.pack_into("<iI", out, 0, 0, len(icons))
    for idx, (itype, mx, my, bgra) in enumerate(icons):
        struct.pack_into("<iiiBBBB", out, 8 + idx * 16, itype, mx, my, *bgra)
    return bytes(out)


def generate_jass_script(units: List[PlacedUnit]) -> str:
    """
    Generate 100% World-Editor-compliant JASS2 war3map.j script.
    Verified leak-clean and compatible with classic TFT 1.26a/1.27b-era JASS APIs.
    """
    lines: List[str] = []
    lines.append("//===========================================================================")
    lines.append("// ")
    lines.append(f"// {MAP_DISPLAY_NAME}")
    lines.append("// ")
    lines.append("//   Warcraft III Melee map script")
    lines.append(f"//   Map Author: {MAP_AUTHOR}")
    lines.append("// ")
    lines.append("//===========================================================================")
    lines.append("")
    lines.append("//***************************************************************************")
    lines.append("//*")
    lines.append("//*  Global Variables")
    lines.append("//*")
    lines.append("//***************************************************************************")
    lines.append("")
    custom_globals_jass, custom_funcs_jass = generate_custom_races_jass()

    lines.append("globals")
    lines.append("    // Generated")
    lines.append("    trigger                 gg_trg_Melee_Initialization = null")
    lines.append(custom_globals_jass.rstrip("\r\n"))
    lines.append("endglobals")
    lines.append("")
    lines.append("function InitGlobals takes nothing returns nothing")
    lines.append("endfunction")
    lines.append("")
    lines.append("//***************************************************************************")
    lines.append("//*")
    lines.append("//*  Unit Item Tables")
    lines.append("//*")
    lines.append("//***************************************************************************")
    lines.append("")

    for u in units:
        if u.player == 12 and u.drops:
            fn_name = f"Unit{u.creation_num:06d}_DropItems"
            lines.append(f"function {fn_name} takes nothing returns nothing")
            lines.append("    local widget  trigWidget = null")
            lines.append("    local unit    trigUnit   = null")
            lines.append("    local integer itemID     = 0")
            lines.append("    local boolean canDrop    = true")
            lines.append("")
            lines.append("    set trigWidget = bj_lastDyingWidget")
            lines.append("    if (trigWidget == null) then")
            lines.append("        set trigUnit = GetTriggerUnit()")
            lines.append("    endif")
            lines.append("")
            lines.append("    if (trigUnit != null) then")
            lines.append("        set canDrop = not IsUnitHidden(trigUnit)")
            lines.append("        if (canDrop and GetChangingUnit() != null) then")
            lines.append("            set canDrop = (GetChangingUnitPrevOwner() == Player(PLAYER_NEUTRAL_AGGRESSIVE))")
            lines.append("        endif")
            lines.append("    endif")
            lines.append("")
            lines.append("    if (canDrop) then")
            for idx, d in enumerate(u.drops):
                lines.append(f"        // Item set {idx}")
                lines.append("        call RandomDistReset(  )")
                lines.append(f"        call RandomDistAddItem( {d.jass_expr}, 100 )")
                lines.append("        set itemID = RandomDistChoose(  )")
                lines.append("        if (trigUnit != null) then")
                lines.append("            call UnitDropItem( trigUnit, itemID )")
                lines.append("        else")
                lines.append("            call WidgetDropItem( trigWidget, itemID )")
                lines.append("        endif")
                lines.append("")
            lines.append("    endif")
            lines.append("")
            lines.append("    set bj_lastDyingWidget = null")
            lines.append("    call DestroyTrigger(GetTriggeringTrigger())")
            lines.append("endfunction")
            lines.append("")

    lines.append("//***************************************************************************")
    lines.append("//*")
    lines.append("//*  Unit Creation")
    lines.append("//*")
    lines.append("//***************************************************************************")
    lines.append("")
    lines.append("//===========================================================================")
    lines.append("function CreateNeutralHostile takes nothing returns nothing")
    lines.append("    local player p = Player(PLAYER_NEUTRAL_AGGRESSIVE)")
    lines.append("    local unit u")
    lines.append("    local trigger t")
    lines.append("")
    for u in units:
        if u.player == 12:
            lines.append(f"    set u = CreateUnit( p, '{u.uid}', {u.x:.1f}, {u.y:.1f}, {u.angle_deg:.3f} )")
            if u.acq_range == -2.0:
                lines.append("    call SetUnitAcquireRange( u, 200.0 )")
            if u.drops:
                fn_name = f"Unit{u.creation_num:06d}_DropItems"
                lines.append("    set t = CreateTrigger(  )")
                lines.append("    call TriggerRegisterUnitEvent( t, u, EVENT_UNIT_DEATH )")
                lines.append("    call TriggerRegisterUnitEvent( t, u, EVENT_UNIT_CHANGE_OWNER )")
                lines.append(f"    call TriggerAddAction( t, function {fn_name} )")
    lines.append("endfunction")
    lines.append("")

    lines.append("//===========================================================================")
    lines.append("function CreateNeutralPassiveBuildings takes nothing returns nothing")
    lines.append("    local player p = Player(PLAYER_NEUTRAL_PASSIVE)")
    lines.append("    local unit u")
    lines.append("")
    for u in units:
        if u.player == 15:
            lines.append(f"    set u = CreateUnit( p, '{u.uid}', {u.x:.1f}, {u.y:.1f}, {u.angle_deg:.3f} )")
            if u.uid == "ngol":
                lines.append(f"    call SetResourceAmount( u, {u.gold} )")
            elif u.uid in ("ntav", "nmer"):
                lines.append("    call SetUnitColor( u, ConvertPlayerColor(0) )")
    lines.append("endfunction")
    lines.append("")

    lines.append("//===========================================================================")
    lines.append("function CreatePlayerBuildings takes nothing returns nothing")
    lines.append("endfunction")
    lines.append("")
    lines.append("//===========================================================================")
    lines.append("function CreatePlayerUnits takes nothing returns nothing")
    lines.append("endfunction")
    lines.append("")
    lines.append("//===========================================================================")
    lines.append("function CreateAllUnits takes nothing returns nothing")
    lines.append("    call CreateNeutralPassiveBuildings(  )")
    lines.append("    call CreatePlayerBuildings(  )")
    lines.append("    call CreateNeutralHostile(  )")
    lines.append("    call CreatePlayerUnits(  )")
    lines.append("endfunction")
    lines.append("")

    lines.append(custom_funcs_jass.rstrip("\r\n"))
    lines.append("")
    lines.append("//***************************************************************************")
    lines.append("//*")
    lines.append("//*  Triggers")
    lines.append("//*")
    lines.append("//***************************************************************************")
    lines.append("")
    lines.append("//===========================================================================")
    lines.append("// Trigger: Melee Initialization")
    lines.append("//")
    lines.append("// 6-Race Altered Melee game initialization for all players")
    lines.append("//===========================================================================")
    lines.append("function Trig_Melee_Initialization_Actions takes nothing returns nothing")
    lines.append('    call SetSkyModel( "Environment\\\\Sky\\\\Outland_Sky\\\\Outland_Sky.mdl" )')
    lines.append("    call SetTerrainFogEx( 0, 3200.0, 9600.0, 0.0, 0.14, 0.22, 0.42 )")
    lines.append("    call SetWaterBaseColor( 45, 215, 245, 225 )")
    lines.append("    call MeleeStartingVisibility(  )")
    lines.append("    call MeleeStartingHeroLimit(  )")
    lines.append("    call MeleeGrantHeroItems(  )")
    lines.append("    call MeleeStartingResources(  )")
    lines.append("    call MeleeClearExcessUnits(  )")
    lines.append("    call InitCustomRacesAndAI(  )")
    lines.append("    call MeleeInitVictoryDefeat(  )")
    lines.append("endfunction")
    lines.append("")
    lines.append("//===========================================================================")
    lines.append("function InitTrig_Melee_Initialization takes nothing returns nothing")
    lines.append("    set gg_trg_Melee_Initialization = CreateTrigger(  )")
    lines.append("    call TriggerAddAction( gg_trg_Melee_Initialization, function Trig_Melee_Initialization_Actions )")
    lines.append("endfunction")
    lines.append("")
    lines.append("//===========================================================================")
    lines.append("function InitCustomTriggers takes nothing returns nothing")
    lines.append("    call InitTrig_Melee_Initialization(  )")
    lines.append("endfunction")
    lines.append("")
    lines.append("//===========================================================================")
    lines.append("function RunInitializationTriggers takes nothing returns nothing")
    lines.append("    call ConditionalTriggerExecute( gg_trg_Melee_Initialization )")
    lines.append("endfunction")
    lines.append("")

    lines.append("//***************************************************************************")
    lines.append("//*")
    lines.append("//*  Players")
    lines.append("//*")
    lines.append("//***************************************************************************")
    lines.append("")
    lines.append("function InitCustomPlayerSlots takes nothing returns nothing")
    lines.append("")
    for pid in range(8):
        lines.append(f"    // Player {pid}")
        lines.append(f"    call SetPlayerStartLocation( Player({pid}), {pid} )")
        lines.append(f"    call SetPlayerColor( Player({pid}), ConvertPlayerColor({pid}) )")
        lines.append(f"    call SetPlayerRacePreference( Player({pid}), RACE_PREF_RANDOM )")
        lines.append(f"    call SetPlayerRaceSelectable( Player({pid}), true )")
        lines.append(f"    call SetPlayerController( Player({pid}), MAP_CONTROL_USER )")
        lines.append("")
    lines.append("endfunction")
    lines.append("")
    lines.append("function InitCustomTeams takes nothing returns nothing")
    lines.append("    // Force: TRIGSTR_005")
    for pid in range(8):
        lines.append(f"    call SetPlayerTeam( Player({pid}), 0 )")
    lines.append("endfunction")
    lines.append("")
    lines.append("function InitAllyPriorities takes nothing returns nothing")
    for pid in range(8):
        prev1 = (pid + 7) % 8
        next1 = (pid + 1) % 8
        prev2 = (pid + 6) % 8
        next2 = (pid + 2) % 8
        lines.append("")
        lines.append(f"    call SetStartLocPrioCount( {pid}, 4 )")
        lines.append(f"    call SetStartLocPrio( {pid}, 0, {prev1}, MAP_LOC_PRIO_HIGH )")
        lines.append(f"    call SetStartLocPrio( {pid}, 1, {next1}, MAP_LOC_PRIO_HIGH )")
        lines.append(f"    call SetStartLocPrio( {pid}, 2, {prev2}, MAP_LOC_PRIO_LOW )")
        lines.append(f"    call SetStartLocPrio( {pid}, 3, {next2}, MAP_LOC_PRIO_LOW )")
    lines.append("endfunction")
    lines.append("")

    lines.append("//***************************************************************************")
    lines.append("//*")
    lines.append("//*  Main Initialization")
    lines.append("//*")
    lines.append("//***************************************************************************")
    lines.append("")
    lines.append("//===========================================================================")
    lines.append("function main takes nothing returns nothing")
    lines.append(
        f"    call SetCameraBounds( {PLAYABLE_MIN_X:.1f} + GetCameraMargin(CAMERA_MARGIN_LEFT), "
        f"{PLAYABLE_MIN_Y:.1f} + GetCameraMargin(CAMERA_MARGIN_BOTTOM), "
        f"{PLAYABLE_MAX_X:.1f} - GetCameraMargin(CAMERA_MARGIN_RIGHT), "
        f"{PLAYABLE_MAX_Y:.1f} - GetCameraMargin(CAMERA_MARGIN_TOP), "
        f"{PLAYABLE_MIN_X:.1f} + GetCameraMargin(CAMERA_MARGIN_LEFT), "
        f"{PLAYABLE_MAX_Y:.1f} - GetCameraMargin(CAMERA_MARGIN_TOP), "
        f"{PLAYABLE_MAX_X:.1f} - GetCameraMargin(CAMERA_MARGIN_RIGHT), "
        f"{PLAYABLE_MIN_Y:.1f} + GetCameraMargin(CAMERA_MARGIN_BOTTOM) )"
    )
    lines.append(
        '    call SetDayNightModels( "Environment\\\\DNC\\\\DNCAshenvale\\\\DNCAshenvaleTerrain\\\\DNCAshenvaleTerrain.mdl", '
        '"Environment\\\\DNC\\\\DNCAshenvale\\\\DNCAshenvaleUnit\\\\DNCAshenvaleUnit.mdl" )'
    )
    lines.append('    call NewSoundEnvironment( "Default" )')
    lines.append('    call SetAmbientDaySound( "SunkenRuinsDay" )')
    lines.append('    call SetAmbientNightSound( "SunkenRuinsNight" )')
    lines.append('    call SetMapMusic( "Music", true, 0 )')
    lines.append("    call CreateAllUnits(  )")
    lines.append("    call InitBlizzard(  )")
    lines.append("    call InitGlobals(  )")
    lines.append("    call InitCustomTriggers(  )")
    lines.append("    call RunInitializationTriggers(  )")
    lines.append("endfunction")
    lines.append("")

    lines.append("//***************************************************************************")
    lines.append("//*")
    lines.append("//*  Map Configuration")
    lines.append("//*")
    lines.append("//***************************************************************************")
    lines.append("")
    lines.append("function config takes nothing returns nothing")
    lines.append('    call SetMapName( "TRIGSTR_001" )')
    lines.append('    call SetMapDescription( "TRIGSTR_003" )')
    lines.append("    call SetPlayers( 8 )")
    lines.append("    call SetTeams( 8 )")
    lines.append("    call SetGamePlacement( MAP_PLACEMENT_TEAMS_TOGETHER )")
    lines.append("")
    for pid, (sx, sy) in enumerate(PLAYER_BASES):
        lines.append(f"    call DefineStartLocation( {pid}, {sx:.1f}, {sy:.1f} )")
    lines.append("")
    lines.append("    // Player setup")
    lines.append("    call InitCustomPlayerSlots(  )")
    for pid in range(8):
        lines.append(f"    call SetPlayerSlotAvailable( Player({pid}), MAP_CONTROL_USER )")
    lines.append("    call InitGenericPlayerSlots(  )")
    lines.append("    call InitAllyPriorities(  )")
    lines.append("endfunction")
    lines.append("")
    return "\r\n".join(lines)


# ==============================================================================
# Minimap Texture Renderer -> Authentic BLP1 (BGRA Baseline JPEG) + 1024px PNG
# ==============================================================================


def write_png_rgba(path: Path, rgba: bytes, width: int, height: int) -> None:
    """Zero-dependency pure-Python PNG encoder for high-res preview images."""
    raw_rows = bytearray()
    stride = width * 4
    for y in range(height):
        raw_rows.append(0)  # Filter type 0 (None)
        raw_rows += rgba[y * stride : (y + 1) * stride]

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw_rows), 9))
    png += chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(png))


def render_map_raster(
    corners_data: List[List[Tuple[float, float, int, int, int, int]]],
    trees: List[PlacedTree],
    units: Optional[List[PlacedUnit]],
    size: int,
    draw_overlays: bool = False,
) -> bytes:
    """Render hill-shaded terrain + rivers + forests (+ optional tactical icons) to RGBA buffer."""
    tex_colors = {
        TEX_DIRT: (88, 80, 102),
        TEX_ROUGH_DIRT: (146, 136, 174),
        TEX_GRASSY_DIRT: (98, 138, 146),
        TEX_ROCK: (62, 56, 86),
        TEX_GRASS: (46, 118, 102),
        TEX_DARK_GRASS: (32, 88, 86),
    }
    rgba = bytearray(size * size * 4)

    for py in range(size):
        wy = PLAYABLE_MAX_Y - (py + 0.5) / size * PLAYABLE_SPAN
        fy = (wy - CENTER_OFFSET_Y) / TILE_SIZE
        iy = max(0, min(CORNERS_H - 2, int(fy)))
        for px in range(size):
            wx = PLAYABLE_MIN_X + (px + 0.5) / size * PLAYABLE_SPAN
            fx = (wx - CENTER_OFFSET_X) / TILE_SIZE
            ix = max(0, min(CORNERS_W - 2, int(fx)))

            c = corners_data[iy][ix]
            c_r = corners_data[iy][min(CORNERS_W - 1, ix + 1)]
            c_u = corners_data[min(CORNERS_H - 1, iy + 1)][ix]

            gh, _wh, is_w, tex, _gv, _bf = c
            slope_shade = 1.0 + (c_r[0] - gh) * 0.45 + (c_u[0] - gh) * 0.45
            elev_boost = (gh - 0.25) * 35.0

            if is_w or gh < 0.04:
                depth = max(0.0, -gh)
                if depth < 0.48:
                    # Bioluminescent cyan walkable ford
                    r_c, g_c, b_c = 58, 222, 246
                else:
                    # Deep astral cyan-sapphire temple lagoon
                    t = min(1.0, (depth - 0.48) / 0.75)
                    r_c = int(28 * (1 - t) + 14 * t)
                    g_c = int(148 * (1 - t) + 64 * t)
                    b_c = int(212 * (1 - t) + 148 * t)
            else:
                br, bg, bb = tex_colors.get(tex, (46, 118, 102))
                r_c = max(0, min(255, int(br * slope_shade + elev_boost)))
                g_c = max(0, min(255, int(bg * slope_shade + elev_boost)))
                b_c = max(0, min(255, int(bb * slope_shade + elev_boost)))

            off = (py * size + px) * 4
            rgba[off] = r_c
            rgba[off + 1] = g_c
            rgba[off + 2] = b_c
            rgba[off + 3] = 255

    # Paint tree canopies with their authored variation and scale so forests read less tiled.
    canopy_colors = ((18, 92, 78), (16, 84, 76), (21, 100, 79), (13, 82, 75), (23, 94, 81))
    for t in trees:
        if t.did != "ZTtw":
            continue
        cx = int((t.x - PLAYABLE_MIN_X) / PLAYABLE_SPAN * size)
        cy = int((PLAYABLE_MAX_Y - t.y) / PLAYABLE_SPAN * size)
        tree_rad = max(1, int(round(size / 256.0 * 1.35 * t.scale)))
        canopy_kind = t.variation % len(canopy_colors)
        base_color = canopy_colors[canopy_kind]
        for dy in range(-tree_rad, tree_rad + 1):
            for dx in range(-tree_rad, tree_rad + 1):
                dist2 = dx * dx + dy * dy
                if canopy_kind == 0:
                    inside = dist2 <= tree_rad * tree_rad + 1
                elif canopy_kind == 1:
                    inside = abs(dx) + abs(dy) <= tree_rad * 1.45
                elif canopy_kind == 2:
                    inside = dx * dx * 0.78 + dy * dy <= tree_rad * tree_rad + 1
                elif canopy_kind == 3:
                    inside = dist2 <= tree_rad * tree_rad + 1 and not (dx > 0 and dy > 0 and dx + dy > tree_rad)
                else:
                    inside = dist2 <= tree_rad * tree_rad + 1 and (dx == 0 or dy == 0 or dist2 <= tree_rad * tree_rad * 0.86)
                if inside:
                    ix, iy = cx + dx, cy + dy
                    if 0 <= ix < size and 0 <= iy < size:
                        off = (iy * size + ix) * 4
                        shade = 0.82 if (dx > 0 or dy > 0) else 1.13
                        rgba[off] = max(0, min(255, int(base_color[0] * shade)))
                        rgba[off + 1] = max(0, min(255, int(base_color[1] * shade)))
                        rgba[off + 2] = max(0, min(255, int(base_color[2] * shade)))

    # Tiny palette dots represent the actual non-blocking water flora and Shrine ornaments.
    def paint_scenic(wx: float, wy: float, radius: int, color: Tuple[int, int, int], kind: str) -> None:
        cx = int((wx - PLAYABLE_MIN_X) / PLAYABLE_SPAN * size)
        cy = int((PLAYABLE_MAX_Y - wy) / PLAYABLE_SPAN * size)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if kind == "diamond":
                    inside = abs(dx) + abs(dy) <= radius + 0.5
                else:
                    inside = dx * dx + dy * dy <= radius * radius + 1
                if inside and 0 <= cx + dx < size and 0 <= cy + dy < size:
                    off = ((cy + dy) * size + cx + dx) * 4
                    rgba[off:off + 3] = bytes(color)

    for t in trees:
        if t.did == "ZZys":
            r = max(4, int(round(size / 256.0 * 2.2 * t.scale)))
            paint_scenic(t.x, t.y, r, (250, 216, 128), "circle")
            paint_scenic(t.x, t.y, max(2, r - 2), (109, 68, 163), "circle")
            paint_scenic(t.x, t.y, max(1, r // 3), (226, 250, 245), "diamond")
        elif t.did == "ZZgr":
            paint_scenic(t.x, t.y, max(1, int(round(size / 256.0 * 1.55 * t.scale))), (76, 221, 224), "diamond")
        elif t.did == "YOfb":
            paint_scenic(t.x, t.y, max(1, int(round(size / 256.0 * 1.15 * t.scale))), (47, 213, 239), "diamond")
        elif t.did == "ZWbg":
            paint_scenic(t.x, t.y, max(1, int(round(size / 256.0 * 1.25 * t.scale))), (139, 244, 242), "circle")
        elif t.did == "ZPlp":
            paint_scenic(t.x, t.y, max(1, int(round(size / 256.0 * 1.65 * t.scale))), (40, 145, 126), "circle")

    if draw_overlays and units:
        def draw_disc(wx: float, wy: float, rad: int, col: Tuple[int, int, int], ring: Tuple[int, int, int]) -> None:
            cx = int((wx - PLAYABLE_MIN_X) / PLAYABLE_SPAN * size)
            cy = int((PLAYABLE_MAX_Y - wy) / PLAYABLE_SPAN * size)
            for dy in range(-rad - 2, rad + 3):
                for dx in range(-rad - 2, rad + 3):
                    d2 = dx * dx + dy * dy
                    if d2 <= (rad + 2) ** 2:
                        ix, iy = cx + dx, cy + dy
                        if 0 <= ix < size and 0 <= iy < size:
                            off = (iy * size + ix) * 4
                            c_use = ring if d2 >= (rad - 1) ** 2 else col
                            rgba[off : off + 3] = bytes(c_use)

        # Creep camps
        seen_camps = set()
        for u in units:
            if u.player == 12 and u.camp_id is not None and u.camp_id not in seen_camps:
                seen_camps.add(u.camp_id)
                if "Lvl 6" in u.role:
                    col = (46, 214, 72)
                elif "Lvl 2" in u.role:
                    col = (232, 56, 56)
                else:
                    col = (242, 156, 38)
                draw_disc(u.x, u.y, max(4, size // 140), col, (18, 18, 18))

        # Neutral buildings & Gold Mines. Crown Shrine gets a deliberate double-ring marker.
        for u in units:
            if u.uid == "ngol":
                draw_disc(u.x, u.y, max(5, size // 105), (255, 216, 48), (64, 42, 0))
            elif u.uid == "ntav":
                draw_disc(u.x, u.y, max(9, size // 88), (64, 205, 224), (255, 219, 127))
                draw_disc(u.x, u.y, max(5, size // 175), (112, 73, 172), (244, 246, 237))
            elif u.player == 15:
                draw_disc(u.x, u.y, max(5, size // 115), (72, 224, 255), (20, 24, 36))

        # Player start locations
        for u in units:
            if u.uid == "sloc":
                b, g, r, _a = PLAYER_COLORS_BGRA[u.player]
                draw_disc(u.x, u.y, max(7, size // 82), (r, g, b), (255, 255, 255))

    return bytes(rgba)


# ==============================================================================
# Export Web Inspector Telemetry JSON
# ==============================================================================

def export_web_metadata(
    out_json: Path,
    corners_data: List[List[Tuple[float, float, int, int, int, int]]],
    wpm_bytes: bytes,
    units: List[PlacedUnit],
    trees: List[PlacedTree],
    camps: List[Dict[str, object]],
    w3x_size: int,
    packer_used: str,
    custom_assets_count: int,
    archive_files_count: int,
    blp_files_count: int,
    map_strings_count: int,
    minimap_icons_count: int,
    skill_mdx_count: int,
    faction_sigil_mdx_count: int,
    building_mdx_count: int,
) -> None:
    """Export compact JSON telemetry for the interactive Warcraft III Map Studio web preview."""
    # Downsample 193x193 terrain & 192x192 pathing summary for instant 60fps HTML5 canvas rendering
    grid_h = [[round(corners_data[y][x][0], 3) for x in range(CORNERS_W)] for y in range(CORNERS_H)]
    grid_tex = [[corners_data[y][x][3] | (8 if corners_data[y][x][2] else 0) for x in range(CORNERS_W)] for y in range(CORNERS_H)]

    # 192x192 tile-level pathing summary from war3map.wpm (offset 16)
    wpm_grid = []
    raw_p = wpm_bytes[16:]
    for ty in range(TILES_H):
        row = []
        for tx in range(TILES_W):
            # Sample center subcell (2, 2)
            row.append(raw_p[(ty * 4 + 2) * PATH_W + (tx * 4 + 2)])
        wpm_grid.append(row)

    payload = {
        "mapName": MAP_DISPLAY_NAME,
        "fileName": MAP_FILENAME,
        "author": MAP_AUTHOR,
        "description": MAP_DESCRIPTION,
        "recommendedPlayers": MAP_RECOMMENDED_PLAYERS,
        "fileSizeBytes": w3x_size,
        "packerBackend": packer_used,
        "w3iVersion": 25,
        "compatibility": [
            "Warcraft III: The Frozen Throne 1.26a / 1.27b (Atinad, GameRanger, LAN)",
        ],
        "dimensions": {
            "tilesW": TILES_W,
            "tilesH": TILES_H,
            "playableW": PLAYABLE_TILES_W,
            "playableH": PLAYABLE_TILES_H,
            "minWorld": PLAYABLE_MIN_X,
            "maxWorld": PLAYABLE_MAX_X,
            "centerOffset": CENTER_OFFSET_X,
        },
        "stats": {
            "players": 8,
            "playableRaces": 8,
            "customSkills": len(HERO_SKILL_SPECS_64),
            "customHeroes": len(HERO_SKILL_SPECS_64) // 4,
            "customAssets": custom_assets_count,
            "archiveFiles": archive_files_count,
            "blpFiles": blp_files_count,
            "preplacedUnits": len(units),
            "mapDoodads": len(trees),
            "mapStrings": map_strings_count,
            "minimapIcons": minimap_icons_count,
            "startLocations": sum(1 for u in units if u.uid == "sloc"),
            "customSkillEffects": skill_mdx_count,
            "customFactionSigils": faction_sigil_mdx_count,
            "customVfxModels": skill_mdx_count + faction_sigil_mdx_count,
            "customBuildingModels": building_mdx_count,
            "goldMines": sum(1 for u in units if u.uid == "ngol"),
            "totalGoldOnMap": sum(u.gold for u in units if u.uid == "ngol"),
            "neutralBuildings": sum(1 for u in units if u.player == 15 and u.uid != "ngol"),
            "creepCamps": len(camps),
            "creepUnits": sum(1 for u in units if u.player == 12),
            "trees": sum(1 for t in trees if t.did == "ZTtw"),
            "scenicDoodads": sum(1 for t in trees if t.did != "ZTtw"),
        },
        "races": [
            {
                "id": "abyssal",
                "name": "Abyssal Tideborn (Naga Empire)",
                "badge": "v9 • 16 Hero-Specific Skills • Level-6 Ultimates • 64 Unique Spell VFX",
                "lobbyHandicap": "Menu [1] or 90% Handicap",
                "color": "#22d3ee",
                "halls": ["Temple of Tides (T1)", "Sanctuary of Tides (T2)", "Abyssal Citadel (T3)"],
                "heroes": [
                    "Empress Vashj • Q Maelstrom Vortex • W Forked Tempest Arc • E Mana-Tide Aegis • R Cataclysmic Tsunami",
                    "Illidan Stormrage • Q Azzinoth Glaive Barrage • W Mana Burn • E Immolation • R Metamorphosis",
                    "Leviathan Warlord Naj'entus • Q Spine Quake • W Harpoon Undertow • E Tidal Bulwark • R Wrath of Naj'entus",
                    "Nazjatar Tideweaver Athissa • Q Bioluminescent Geyser • W Pearl-frost Prison • E Siren's Vital Chorus • R Abyssal Kraken",
                ],
                "units": [
                    "Buffed Mur'gul Reaver and Tier-1 Snap Dragon; faster Naga Myrmidon frontline",
                    "Enhanced Siren, Couatl, Dragon Turtle and Royal Guard with classic-style food/DPS budget",
                ],
                "buildings": [
                    "Temple / Sanctuary / Citadel • Coral Bed • Spawning Grounds • Coral Forge • Altar of Depths",
                    "Tidal Treasury • Shrine of Azshara • Behemoth Pool • Tidal Guardian; 11 distinct race icons",
                ],
            },
            {
                "id": "sunfury",
                "name": "Sunfury Imperium (Solar Highborne)",
                "badge": "v9 • Fast Altar/Ranged Opening • 64 Unique Spell VFX",
                "lobbyHandicap": "Menu [2] or 80% Handicap",
                "color": "#fbbf24",
                "halls": ["Silvermoon Sanctum (T1)", "Sunwell Keep (T2)", "Silvermoon Citadel (T3)"],
                "heroes": [
                    "Kael'thas • Verdant Sunfire Pillar • Arcane Gravity Lapse • Molten Barrier • Summon Phoenix: Al'ar",
                    "Sylvanas • Sunhawk Volley • Windrunner's Piercing Shot • Gale Stride • Eclipse Starfall",
                    "Garithos • Shock Charge • Execution Decree • Iron Phalanx • Grand Crusade",
                    "Uther • Sunwell Consecration • Dawnlight Hammer • Golden Bastion • Resurrection",
                ],
                "units": [
                    "Silvermoon Worker • Swordsman • Archer • Alliance Captain • Chaplain • Hydromancer • Spell Breaker",
                    "Ballista • Gyro • Blood Elf Lieutenant • Dragonhawk • Gryphon; recognizable native unit buttons",
                ],
                "buildings": [
                    "Three Sunwell halls • High Elven Farm • Sunspire Barracks • Lumber Conservatory • Sunfury Forge",
                    "Altar • Reliquary • Scout/Guard/Arcane Towers • Mage Tower • Artificer Hall • Sky-Roost",
                ],
            },
            {
                "id": "voidborn",
                "name": "Voidborn Legion [NEW]",
                "badge": "v9 • Fiend-Inspired Ranged Tech Opening • Unique Spell VFX",
                "lobbyHandicap": "Menu [3] or 70% Handicap",
                "color": "#c084fc",
                "halls": ["Void Nexus (T1)", "Astral Riftcore (T2)", "Citadel of Oblivion (T3)"],
                "heroes": [
                    "Rift Sovereign • Event Horizon Crater • Oblivion Cleave • Dread Howl • Dark Portal Cataclysm",
                    "Nether Inquisitor • Entropy Rift Storm • Soul Siphon • Astral Phase • Singularity Collapse",
                    "Shadowblade Akama • Shuriken Fan • Phantom Ambush • Smoke Veil • Thousand-Shadow Dance",
                    "Entropy Archon • Starfall Singularity • Banish Bolt • Null-Field Barrier • Twilight of the Cosmos",
                ],
                "units": [
                    "Void Thrall • Void Zealot • Astral Arbalist • Dread Enforcer • Void Weaver • Nether Drakelet",
                    "Rift Devastator siege engine • Oblivion Colossus • stock buttons matched to unit art",
                ],
                "buildings": [
                    "Void Nexus / Riftcore / Citadel • Pylon • Rift Gate • Obsidian Crucible • Altar",
                    "Reliquary • Entropy Obelisk • Sanctum • Oblivion Pit; rift build on normal ground",
                ],
            },
            {
                "id": "runeforged",
                "name": "Runeforged Bastion [NEW]",
                "badge": "v9 • Fast Altar/Tech Opening • Unique Spell VFX",
                "lobbyHandicap": "Menu [4] or 60% Handicap",
                "color": "#f97316",
                "halls": ["Titan Foundry (T1)", "Stormforge Hold (T2)", "Apex Pantheon (T3)"],
                "heroes": [
                    "Thorim • Mjolnir Thunderfall • Magnetic Titan Grip • Overcharged Aegis • Pantheon Wrath",
                    "Ignis • Molten Slag • Forgehammer • Tempered Runic Plating • Awaken Forge Colossus",
                    "Mimiron • Cluster Rockets • Railgun Snipe • Pocket Turrets • Omega Orbital Laser",
                    "Loken • Ionosphere Field • Arc-Conduit Surge • Chrono-Dynamo • Stormcore Superconductor",
                ],
                "units": [
                    "Runeforged Automaton • Runic Sentinel • Thunder Arquebusier • Stormforged Juggernaut",
                    "Rune Diviner • Gyro-Interceptor • Siege Behemoth • Titan Construct; native buttons match the models",
                ],
                "buildings": [
                    "Titan Foundry / Stormforge Hold / Apex Pantheon • Dynamo Core • Iron Garrison • Runic Anvil",
                    "Altar • Artificer Vault • Tesla Turret • Arcane Conduit • Colossus Bay",
                ],
            },
            {
                "id": "classic4",
                "name": "Human • Orc • Undead • Night Elf",
                "badge": "4 Classic Ladder Races (Balanced) + Updated Damage/Armor UI",
                "lobbyHandicap": "Menu [K] Keep Lobby Race",
                "color": "#38bdf8",
                "halls": ["Town Hall / Great Hall / Necropolis / Tree of Life (T1-T3)"],
                "heroes": ["All original classic melee heroes; the 16 custom heroes have individual spell kits"],
                "units": ["Authentic Frozen Throne melee techtrees, upgrades, items and native AI"],
                "buildings": ["Classic race-specific building lists, damage types and armor classes"],
            },
        ],
        "players": [
            {
                "id": pid,
                "name": f"Player {pid + 1}",
                "colorName": PLAYER_COLOR_NAMES[pid],
                "rgb": [PLAYER_COLORS_BGRA[pid][2], PLAYER_COLORS_BGRA[pid][1], PLAYER_COLORS_BGRA[pid][0]],
                "x": sx,
                "y": sy,
                "mineX": MAIN_MINES[pid][0],
                "mineY": MAIN_MINES[pid][1],
            }
            for pid, (sx, sy) in enumerate(PLAYER_BASES)
        ],
        "neutralBuildings": [
            {
                "uid": u.uid,
                "role": u.role,
                "x": u.x,
                "y": u.y,
                "gold": u.gold if u.uid == "ngol" else 0,
            }
            for u in units
            if u.player == 15
        ],
        "camps": camps,
        "trees": [[int(t.x), int(t.y), round(t.scale, 2)] for t in trees],
        "roads": ROAD_SEGMENTS,
        "heightGrid": grid_h,
        "texGrid": grid_tex,
        "wpmGrid": wpm_grid,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")


# ==============================================================================
# Main Build Pipeline
# ==============================================================================

def build_all(repo_root: Path) -> Path:
    print(f"[1/6] Sculpting D4-symmetric 192x192 Sunken-Astral Ruins terrain for {MAP_DISPLAY_NAME}...")
    corners_data: List[List[Tuple[float, float, int, int, int, int]]] = []
    terrain_heights: List[List[float]] = []
    terrain_water: List[List[int]] = []

    for cy in range(CORNERS_H):
        row = []
        hrow = []
        wrow = []
        for cx in range(CORNERS_W):
            c = evaluate_corner(cx, cy)
            row.append(c)
            hrow.append(c[0])
            wrow.append(c[2])
        corners_data.append(row)
        terrain_heights.append(hrow)
        terrain_water.append(wrow)

    print("[2/6] Placing 8 Player Bases, 20 Gold Mines, 17 Neutral Buildings, and 36 Creep Camps...")
    units, camp_summaries = generate_units_and_camps(terrain_heights)

    print("[3/6] Growing D4-symmetric Lordaeron forests (LTlt) with guaranteed road & base clearance...")
    trees = generate_trees(terrain_heights, terrain_water, units)
    print(f"      Placed {len(units)} preplaced units/buildings and {len(trees)} harvestable trees.")

    print("[4/6] Serializing all 21 Warcraft III binary map files, Object Tables, JASS2 & Pro .ai scripts...")
    w3e_bytes = serialize_w3e(corners_data)
    wpm_bytes = serialize_wpm(corners_data)
    shd_bytes = serialize_shd(corners_data, trees)
    doo_bytes = serialize_doo(trees)
    udoo_bytes = serialize_units_doo(units)
    w3i_bytes = serialize_w3i()
    wts_bytes = serialize_wts()
    wtg_bytes, wct_bytes, w3r_bytes, w3c_bytes = serialize_wtg_and_wct()
    mmp_bytes = serialize_mmp(units)
    w3u_bytes = serialize_w3u()
    w3t_bytes = serialize_w3t()
    w3q_bytes = serialize_w3q()
    w3a_bytes = serialize_w3a()
    misc_bytes = serialize_war3map_misc()
    skin_bytes = serialize_war3map_skin()

    print("[4.5/6] Generating 16 hero portrait pairs, 12 hall-tier icon pairs, 64 skill BTN/DISBTN pairs, cursor/RPG UI, 70 VFX MDXs, and 6 Naga hall/role building MDXs...")
    custom_assets_map = generate_all_custom_assets()
    imp_bytes = serialize_imp(list(custom_assets_map.keys()))

    naga_ai_bytes = generate_naga_ai_script().encode("utf-8")
    camphuman_ai_bytes = generate_camphuman_ai_script().encode("utf-8")
    voidborn_ai_bytes = generate_voidborn_ai_script().encode("utf-8")
    runeforged_ai_bytes = generate_runeforged_ai_script().encode("utf-8")
    jass_bytes = generate_jass_script(units).encode("utf-8")

    print("[5/6] Rendering 256x256 BLP1 minimap texture & 1024x1024 tactical preview PNG...")
    minimap_rgba = render_map_raster(corners_data, trees, units=None, size=256, draw_overlays=False)
    blp_bytes = encode_blp1_jpeg(minimap_rgba, 256, 256, quality_scale=0.35)

    preview_rgba = render_map_raster(corners_data, trees, units=units, size=1024, draw_overlays=True)
    preview_path = repo_root / "maps" / "(8)CrownOfWarMahdi_Preview.png"
    write_png_rgba(preview_path, preview_rgba, 1024, 1024)

    map_files: Dict[str, bytes] = {
        "war3map.w3e": w3e_bytes,
        "war3map.w3i": w3i_bytes,
        "war3map.wtg": wtg_bytes,
        "war3map.wct": wct_bytes,
        "war3map.wts": wts_bytes,
        "war3map.j": jass_bytes,
        "war3map.shd": shd_bytes,
        "war3mapMap.blp": blp_bytes,
        "war3map.mmp": mmp_bytes,
        "war3map.wpm": wpm_bytes,
        "war3map.doo": doo_bytes,
        "war3mapUnits.doo": udoo_bytes,
        "war3map.w3r": w3r_bytes,
        "war3map.w3c": w3c_bytes,
        "war3map.w3u": w3u_bytes,
        "war3map.w3t": w3t_bytes,
        "war3map.w3q": w3q_bytes,
        "war3map.w3a": w3a_bytes,
        "war3mapMisc.txt": misc_bytes,
        "war3mapSkin.txt": skin_bytes,
        "war3map.imp": imp_bytes,
        "naga_melee.ai": naga_ai_bytes,
        "camphuman_melee.ai": camphuman_ai_bytes,
        "voidborn_melee.ai": voidborn_ai_bytes,
        "runeforged_melee.ai": runeforged_ai_bytes,
    }
    map_files.update(custom_assets_map)

    hm3w_header = build_hm3w_header(MAP_DISPLAY_NAME, MAP_FLAGS, 8)
    out_w3x = repo_root / "maps" / MAP_FILENAME

    print("[6/6] Packing compressed MPQ v1 .w3x archive...")
    packer_used = pack_w3x(hm3w_header, map_files, out_w3x, Path("/tmp/wc3_build_work"))
    w3x_size = out_w3x.stat().st_size

    export_web_metadata(
        repo_root / "web" / "public" / "map_data.json",
        corners_data,
        wpm_bytes,
        units,
        trees,
        camp_summaries,
        w3x_size,
        packer_used,
        len(custom_assets_map),
        len(map_files),
        sum(1 for internal_name in map_files if internal_name.lower().endswith(".blp")),
        wts_bytes.count(b"STRING "),
        struct.unpack_from("<I", mmp_bytes, 4)[0],
        sum(1 for name in map_files if name.lower().endswith(".mdx") and Path(name).stem.startswith("WM_Skill_")),
        sum(1 for name in map_files if name.lower().endswith(".mdx") and Path(name).stem.startswith("WM_FX_")),
        sum(1 for name in map_files if name.lower().endswith(".mdx") and Path(name).stem.startswith("WM_Build_Naga_")),
    )
    import base64
    import hashlib
    raw_w3x = out_w3x.read_bytes()
    sha_hex = hashlib.sha256(raw_w3x).hexdigest()
    b64_str = base64.b64encode(raw_w3x).decode("ascii")
    (repo_root / "web" / "public" / "w3x_b64.js").write_text(
        f'window.W3X_MAP_FILENAME = "{MAP_FILENAME}";\n'
        f"window.W3X_MAP_BYTES = {len(raw_w3x)};\n"
        f'window.W3X_MAP_SHA256 = "{sha_hex}";\n'
        f'window.W3X_MAP_B64 = "{b64_str}";\n',
        encoding="utf-8",
    )
    print(f"DONE! Built {out_w3x} ({w3x_size:,} bytes via {packer_used}).")
    return out_w3x


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    build_all(root)
