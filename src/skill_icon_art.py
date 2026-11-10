#!/usr/bin/env python3
"""Original, per-skill command-button artwork for the 64 Crown of WarMahdi hero skills.

The renderer deliberately uses authored silhouettes and family-specific frames rather than
color-shifting one generic icon. It runs with Pillow only and emits reusable RGBA artwork;
custom_assets.py encodes the result as Classic-compatible BLP1 command buttons.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    from .custom_factions_v3 import HERO_SKILL_SPECS_64
except ImportError:  # `python src/skill_icon_art.py`
    from custom_factions_v3 import HERO_SKILL_SPECS_64

REPO_ROOT = Path(__file__).resolve().parent.parent
GALLERY_PATHS = (
    REPO_ROOT / "web/public/skill_icons_abyssal.png",
    REPO_ROOT / "web/public/skill_icons_sunfury.png",
    REPO_ROOT / "web/public/skill_icons_voidborn.png",
    REPO_ROOT / "web/public/skill_icons_runeforged.png",
)

FACTION_NAMES = ("ABYSSAL TIDEBORN", "SUNFURY IMPERIUM", "VOIDBORN LEGION", "RUNEFORGED BASTION")
HERO_NAMES = (
    "Empress Vashj", "Illidan Stormrage", "Naj'entus", "Athissa",
    "Kael'thas", "Sylvanas", "Garithos", "Uther",
    "Xal'athor", "Sargen'eth", "Akama", "Aetheron",
    "Thorim", "Ignis", "Mimiron", "Loken",
)

# One authored silhouette per skill, in the same order as HERO_SKILL_SPECS_64.
# Several share an artistic family, but no two skills share a motif identifier.
SKILL_MOTIFS = (
    "maelstrom", "forked_arc", "tide_aegis", "cataclysm_wave",
    "azzinoth_glaives", "mana_burn", "demon_immolation", "abyssal_metamorphosis",
    "spine_quake", "harpoon_undertow", "carapace_roar", "kraken_wrath",
    "biolume_geyser", "siren_prison", "azshara_blessing", "nazjatar_eye",
    "sunfire_pillar", "gravity_lapse", "molten_barrier", "phoenix_alar",
    "starlight_arrows", "piercing_shot", "gale_stride", "quelthalas_tempest",
    "earthshaker_hammer", "execution_decree", "iron_phalanx", "cavalry_charge",
    "sunwell_consecration", "radiant_verdict", "silverhand_aegis", "resurrection",
    "event_horizon", "oblivion_cleave", "dreadlord_howl", "dark_portal",
    "entropy_rift", "soul_siphon", "astral_phase", "singularity_collapse",
    "shuriken_fan", "phantom_ambush", "smoke_veil", "thousand_shadows",
    "starfall_singularity", "dimensional_banish", "null_field", "cosmic_twilight",
    "mjolnir_fall", "magnetic_grip", "aegis_core", "pantheon_wrath",
    "molten_slag", "forgehammer", "rune_plating", "forge_colossus",
    "cluster_rockets", "gauss_rail", "pocket_turrets", "orbital_laser",
    "ionosphere_field", "arc_conduit", "chrono_dynamo", "superconductor",
)
assert len(HERO_SKILL_SPECS_64) == len(SKILL_MOTIFS) == 64
assert len(set(SKILL_MOTIFS)) == 64, "Each custom skill must own its own icon silhouette."

# Each hero has a distinct enamel/glow pairing; faction families share only their frame language.
HERO_COLORS: Tuple[Tuple[Tuple[int, int, int], Tuple[int, int, int]], ...] = (
    ((22, 186, 212), (184, 255, 242)), ((52, 213, 167), (224, 255, 205)),
    ((38, 126, 190), (150, 238, 255)), ((70, 227, 194), (236, 255, 227)),
    ((222, 141, 38), (255, 234, 142)), ((190, 62, 59), (255, 195, 115)),
    ((190, 147, 53), (255, 238, 173)), ((231, 193, 91), (255, 255, 222)),
    ((113, 52, 199), (222, 164, 255)), ((68, 76, 179), (195, 203, 255)),
    ((136, 53, 169), (242, 163, 255)), ((90, 91, 220), (201, 202, 255)),
    ((67, 142, 187), (190, 242, 255)), ((207, 82, 40), (255, 188, 103)),
    ((111, 151, 178), (226, 246, 255)), ((54, 151, 178), (180, 247, 255)),
)

DARK_INK = (7, 11, 20)
PALE_GOLD = (255, 226, 151)
WHITE_HOT = (255, 255, 239)
S = 192
K = 3  # authored in 192x192, downsampled to WC3's 64x64 button art


def _mix(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] * (1.0 - t) + b[i] * t) for i in range(3))


def _point(cx: float, cy: float, x: float, y: float) -> Tuple[int, int]:
    return (int(round(cx + x * K)), int(round(cy + y * K)))


def _line(d: ImageDraw.ImageDraw, cx: float, cy: float, points: List[Tuple[float, float]], color: Tuple[int, int, int], width: int = 5) -> None:
    d.line([_point(cx, cy, x, y) for x, y in points], fill=(*color, 255), width=width, joint="curve")


def _poly(d: ImageDraw.ImageDraw, cx: float, cy: float, points: List[Tuple[float, float]], fill: Tuple[int, int, int], outline: Tuple[int, int, int], width: int = 4) -> None:
    pts = [_point(cx, cy, x, y) for x, y in points]
    d.polygon(pts, fill=(*fill, 238))
    d.line(pts + [pts[0]], fill=(*outline, 255), width=width, joint="curve")


def _ellipse(d: ImageDraw.ImageDraw, cx: float, cy: float, box: Tuple[float, float, float, float], outline: Tuple[int, int, int], width: int = 4, fill: Tuple[int, int, int, int] | None = None) -> None:
    x0, y0, x1, y1 = box
    rect = (int((cx + x0) * K), int((cy + y0) * K), int((cx + x1) * K), int((cy + y1) * K))
    d.ellipse(rect, outline=(*outline, 255), width=width, fill=fill)


def _bezier(p0: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float], steps: int = 16) -> List[Tuple[float, float]]:
    points = []
    for i in range(steps + 1):
        t = i / steps
        q = 1.0 - t
        points.append((
            q*q*q*p0[0] + 3*q*q*t*p1[0] + 3*q*t*t*p2[0] + t*t*t*p3[0],
            q*q*q*p0[1] + 3*q*q*t*p1[1] + 3*q*t*t*p2[1] + t*t*t*p3[1],
        ))
    return points


def _star(radius: float, points: int, rotation: float = -math.pi / 2) -> List[Tuple[float, float]]:
    out = []
    for i in range(points * 2):
        r = radius if i % 2 == 0 else radius * 0.40
        a = rotation + i * math.pi / points
        out.append((math.cos(a) * r, math.sin(a) * r))
    return out


def _draw_motif(d: ImageDraw.ImageDraw, cx: float, cy: float, motif: str, idx: int, main: Tuple[int, int, int], glow: Tuple[int, int, int], second: Tuple[int, int, int]) -> None:
    """Draw a 64-way authored center glyph; all coordinates are in final 64px units."""
    ink = (12, 17, 27)
    gold = _mix(PALE_GOLD, glow, 0.24)
    w = 5

    if motif == "maelstrom":
        for ring in range(3):
            r = 18 - ring * 5
            pts = [(math.cos(t) * (r * (0.38 + 0.62 * j / 26)), math.sin(t) * (r * (0.38 + 0.62 * j / 26))) for j, t in enumerate([i * 2.0 * math.pi / 26 + ring * 1.15 for i in range(27)])]
            _line(d, cx, cy, pts, (glow, main, gold)[ring], 5 - ring)
        _ellipse(d, cx, cy, (-3, -3, 3, 3), WHITE_HOT, 2, (14, 34, 45, 255))
    elif motif == "forked_arc":
        _line(d, cx, cy, [(-16, -18), (-4, -5), (-12, 2), (3, 5), (-3, 18), (16, -3), (7, -5), (15, -18)], glow, 7)
        _line(d, cx, cy, [(-5, -4), (-17, -8), (-21, -15)], second, 4)
        _line(d, cx, cy, [(4, 3), (16, 8), (20, 15)], WHITE_HOT, 3)
    elif motif == "tide_aegis":
        _poly(d, cx, cy, [(0,-22),(17,-15),(15,5),(0,22),(-15,5),(-17,-15)], main, gold, 5)
        _line(d, cx, cy, [(-13,1),(-7,-3),(0,1),(7,-3),(13,1)], glow, 4)
        _line(d, cx, cy, [(-10,7),(-4,4),(2,7),(9,4)], WHITE_HOT, 2)
    elif motif == "cataclysm_wave":
        for y, amp, col in [(-8,5,glow),(0,7,main),(9,4,second)]:
            pts = [(x, y + math.sin((x + idx) * 0.20) * amp) for x in range(-21, 22, 2)]
            _line(d, cx, cy, pts, col, 4)
        _poly(d, cx, cy, [(12,-14),(21,-9),(13,-4)], glow, WHITE_HOT, 2)
    elif motif == "azzinoth_glaives":
        for off, col in [(-9,glow),(0,main),(9,second)]:
            pts = _bezier((-20, off+12), (-4, off-21), (11, off-16), (20, off+8), 14)
            _line(d, cx, cy, pts, col, 5)
        _line(d, cx, cy, [(-17,14),(0,4),(17,-12)], WHITE_HOT, 2)
    elif motif == "mana_burn":
        _poly(d, cx, cy, [(0,-23),(7,-10),(5,-5),(15,2),(12,14),(4,21),(-9,18),(-15,8),(-10,-3),(-5,-8)], main, gold, 4)
        _poly(d, cx, cy, [(1,-8),(8,2),(2,4),(6,12),(-4,9),(-7,3)], glow, WHITE_HOT, 2)
        _ellipse(d, cx, cy, (-3,-18,3,-12), WHITE_HOT, 1, (255,255,239,255))
    elif motif == "demon_immolation":
        _ellipse(d, cx, cy, (-17,-17,17,17), main, 4)
        for a in (-2.7,-1.6,-0.5,0.7,1.8,2.7):
            _line(d, cx, cy, [(math.cos(a)*15,math.sin(a)*15),(math.cos(a)*23,math.sin(a)*23)], glow, 4)
        _poly(d, cx, cy, [(-7,4),(0,-10),(8,4),(6,14),(0,18),(-6,12)], second, WHITE_HOT, 2)
    elif motif == "abyssal_metamorphosis":
        _poly(d, cx, cy, [(-2,-7),(-21,-21),(-15,-3),(-21,10),(-8,6),(-2,20),(2,20),(8,6),(21,10),(15,-3),(21,-21),(2,-7)], main, gold, 4)
        _ellipse(d, cx, cy, (-3,-6,3,0), glow, 2, (255,255,255,255))
        _line(d, cx, cy, [(-14,2),(-7,10),(0,4),(7,10),(14,2)], WHITE_HOT, 2)
    elif motif == "spine_quake":
        _line(d, cx, cy, [(0,-23),(0,23)], glow, 7)
        for y in (-17,-9,-1,7,15):
            side = 1 if (y // 8) % 2 == 0 else -1
            _poly(d, cx, cy, [(0,y-3),(side*12,y-8),(side*7,y+2)], main, gold, 2)
        _ellipse(d, cx, cy, (-4,-25,4,-17), WHITE_HOT, 2, (255,255,255,255))
    elif motif == "harpoon_undertow":
        _line(d, cx, cy, [(-19,18),(15,-17)], glow, 6)
        _poly(d, cx, cy, [(13,-21),(22,-24),(19,-14),(15,-17)], main, WHITE_HOT, 2)
        _line(d, cx, cy, [(-17,10),(-7,15),(-14,20)], second, 4)
        for x,y in [(-10,10),(-4,4),(2,-2)]: _ellipse(d,cx,cy,(x-2,y-2,x+2,y+2),gold,2)
    elif motif == "carapace_roar":
        # Segmented shell with side-claws: intentionally not another shield silhouette.
        _poly(d, cx, cy, [(-19,10),(-18,-2),(-13,-13),(-5,-20),(5,-20),(13,-13),(18,-2),(19,10),(10,18),(-10,18)], main, gold, 5)
        _line(d, cx, cy, [(0,-16),(0,11)], glow, 4)
        _line(d, cx, cy, [(-12,-12),(-8,-4),(-9,9)], second, 3)
        _line(d, cx, cy, [(12,-12),(8,-4),(9,9)], second, 3)
        _poly(d, cx, cy, [(-17,7),(-24,2),(-21,14),(-12,18)], second, WHITE_HOT, 2)
        _poly(d, cx, cy, [(17,7),(24,2),(21,14),(12,18)], second, WHITE_HOT, 2)
        _line(d, cx, cy, _bezier((-23,-8),(-20,-15),(-16,-15),(-14,-17)), glow, 3)
        _line(d, cx, cy, _bezier((23,-8),(20,-15),(16,-15),(14,-17)), glow, 3)
    elif motif == "kraken_wrath":
        for pts, col in [
            (_bezier((0,8),(-6,-1),(-3,-13),(-12,-21)),glow),
            (_bezier((0,8),(7,-3),(7,-13),(16,-18)),main),
            (_bezier((-2,5),(-14,2),(-18,12),(-22,17)),second),
            (_bezier((3,7),(15,7),(17,15),(22,20)),gold),
        ]: _line(d,cx,cy,pts,col,5)
        _ellipse(d,cx,cy,(-6,-1,6,11),WHITE_HOT,2,(11,29,42,255))
    elif motif == "biolume_geyser":
        _line(d,cx,cy,[(-18,18),(-13,6),(-8,18)],second,4)
        _line(d,cx,cy,[(-8,18),(-2,-17),(5,18)],glow,6)
        _line(d,cx,cy,[(5,18),(12,-5),(18,18)],main,4)
        for x,y in [(-5,-20),(2,-24),(10,-14)]: _ellipse(d,cx,cy,(x-2,y-2,x+2,y+2),WHITE_HOT,2,(255,255,255,255))
    elif motif == "siren_prison":
        _poly(d,cx,cy,[(-19,-16),(19,-16),(15,17),(0,23),(-15,17)],(17,34,47),gold,3)
        for x in (-12,-5,2,9,15): _line(d,cx,cy,[(x,-15),(x*0.72,15)],main if x%2 else glow,3)
        _ellipse(d,cx,cy,(-5,-5,5,5),WHITE_HOT,2,(32,94,117,255))
    elif motif == "azshara_blessing":
        # Royal tide-crown/diadem, separated from the ring and vortex motifs.
        _poly(d,cx,cy,[(-22,12),(-18,-8),(-8,2),(0,-22),(8,2),(18,-8),(22,12),(15,19),(-15,19)],main,gold,4)
        _line(d,cx,cy,[(-18,11),(-10,7),(0,11),(10,7),(18,11)],glow,4)
        for x,y,r in [(-17,-5,3),(0,-17,4),(17,-5,3)]:
            _poly(d,cx,cy,[(x,y-r),(x+r,y),(x,y+r),(x-r,y)],WHITE_HOT,glow,2)
        _line(d,cx,cy,[(-12,15),(12,15)],second,3)
    elif motif == "nazjatar_eye":
        _line(d,cx,cy,_bezier((-22,0),(-10,-18),(10,-18),(22,0)),glow,4)
        _line(d,cx,cy,_bezier((-22,0),(-10,18),(10,18),(22,0)),main,4)
        _ellipse(d,cx,cy,(-8,-9,8,9),gold,2,(13,27,39,255))
        _ellipse(d,cx,cy,(-3,-5,3,5),WHITE_HOT,1,(43,222,210,255))
        _line(d,cx,cy,[(-17,-7),(-22,-14)],second,3); _line(d,cx,cy,[(17,-7),(22,-14)],second,3)
    elif motif == "sunfire_pillar":
        _ellipse(d,cx,cy,(-19,12,19,22),gold,3)
        _poly(d,cx,cy,[(-12,13),(-7,-4),(0,-23),(8,-4),(13,13)],main,gold,3)
        _poly(d,cx,cy,[(-4,11),(0,-11),(6,11)],glow,WHITE_HOT,2)
        for x in (-17,17): _line(d,cx,cy,[(x,6),(x*1.2,-2)],second,3)
    elif motif == "gravity_lapse":
        _ellipse(d,cx,cy,(-9,-9,9,9),main,4,(14,18,37,255))
        for ang in (0.15,1.12,2.24):
            pts=[(math.cos(t)*20,math.sin(t)*9) for t in [ang+i*math.pi/32 for i in range(65)]]
            _line(d,cx,cy,pts,glow,2)
        for x,y in [(-19,0),(0,-15),(17,4)]: _ellipse(d,cx,cy,(x-3,y-3,x+3,y+3),WHITE_HOT,2,(248,224,151,255))
    elif motif == "molten_barrier":
        # A wall of raised magma columns, clearly distinct from the shield skills.
        for x,height,col in [(-15,20,second),(0,27,main),(15,18,second)]:
            _poly(d,cx,cy,[(x-7,19),(x-7,-height+5),(x-2,-height),(x+2,-height+4),(x+7,-height+1),(x+7,19)],col,gold,3)
        _line(d,cx,cy,[(-23,20),(23,20)],glow,4)
        _line(d,cx,cy,[(-10,3),(-4,-4),(0,2),(5,-7),(11,-1)],WHITE_HOT,3)
        _ellipse(d,cx,cy,(-3,-24,3,-18),WHITE_HOT,1,(255,255,239,255))
    elif motif == "phoenix_alar":
        _poly(d,cx,cy,[(0,18),(-5,7),(-20,-1),(-13,-4),(-21,-14),(-6,-9),(0,-20),(6,-9),(21,-14),(13,-4),(20,-1),(5,7)],main,gold,4)
        _line(d,cx,cy,[(-12,1),(-4,6),(0,2),(4,6),(12,1)],glow,4)
        _ellipse(d,cx,cy,(-2,-15,2,-11),WHITE_HOT,1,(255,255,255,255))
    elif motif == "starlight_arrows":
        for x,tilt,col in [(-13,-7,second),(0,0,glow),(13,7,main)]:
            _line(d,cx,cy,[(x-tilt,-21),(x+tilt,16)],col,4)
            _poly(d,cx,cy,[(x+tilt,16),(x+tilt-5,8),(x+tilt+5,8)],col,WHITE_HOT,2)
            _line(d,cx,cy,[(x+tilt,16),(x+tilt-4,22)],gold,2)
    elif motif == "piercing_shot":
        _line(d,cx,cy,[(-18,0),(18,0)],glow,5)
        _poly(d,cx,cy,[(18,0),(8,-7),(9,0),(8,7)],main,WHITE_HOT,2)
        _line(d,cx,cy,[(-14,-17),(-19,-8),(-20,0),(-19,8),(-14,17)],gold,3)
        _line(d,cx,cy,[(-14,-17),(-3,-9)],second,2); _line(d,cx,cy,[(-14,17),(-3,9)],second,2)
    elif motif == "gale_stride":
        _poly(d,cx,cy,[(-18,8),(-8,8),(-1,0),(9,3),(20,12),(13,17),(-4,15),(-15,19)],main,gold,3)
        for y in (-13,-5,4): _line(d,cx,cy,[(-21,y),(0,y-2),(14,y-5)],glow if y==-5 else second,3)
        _ellipse(d,cx,cy,(8,4,12,8),WHITE_HOT,1,(255,255,255,255))
    elif motif == "quelthalas_tempest":
        _poly(d,cx,cy,_star(22,8,0.1),main,gold,3)
        for x,y in [(-16,-16),(16,-16),(-16,16),(16,16)]: _line(d,cx,cy,[(x,y),(x*0.55,y*0.55)],glow,3)
        _ellipse(d,cx,cy,(-4,-4,4,4),WHITE_HOT,1,(255,255,255,255))
    elif motif == "earthshaker_hammer":
        _line(d,cx,cy,[(-4,19),(4,-7)],gold,7)
        _poly(d,cx,cy,[(-15,-16),(12,-18),(18,-8),(12,-2),(-13,-3)],main,WHITE_HOT,3)
        _line(d,cx,cy,[(-20,12),(-11,7),(-2,12),(7,7),(17,11)],glow,3)
    elif motif == "execution_decree":
        _ellipse(d,cx,cy,(-19,-19,19,19),gold,3)
        _poly(d,cx,cy,[(0,-20),(8,-2),(4,2),(7,13),(0,22),(-7,13),(-4,2),(-8,-2)],main,WHITE_HOT,3)
        _line(d,cx,cy,[(-13,0),(-7,-2)],second,2); _line(d,cx,cy,[(13,0),(7,-2)],second,2)
    elif motif == "iron_phalanx":
        # Three upright lances and a shared crossbar read as a formation, not shields.
        for x,col in [(-14,second),(0,glow),(14,main)]:
            _line(d,cx,cy,[(x,18),(x,-13)],gold,4)
            _poly(d,cx,cy,[(x,-23),(x+5,-11),(x,-7),(x-5,-11)],col,WHITE_HOT,2)
            _line(d,cx,cy,[(x-5,5),(x+5,5)],col,3)
        _line(d,cx,cy,[(-22,20),(22,20)],WHITE_HOT,3)
    elif motif == "cavalry_charge":
        _line(d,cx,cy,[(-21,-11),(21,5)],gold,4)
        _poly(d,cx,cy,[(-14,-6),(-5,-17),(4,-12),(13,-15),(18,-7),(9,-1),(4,10),(-7,13),(-17,5)],main,WHITE_HOT,3)
        _line(d,cx,cy,[(-9,-15),(-15,-22),(-3,-17)],second,3)
        _ellipse(d,cx,cy,(7,-8,11,-4),WHITE_HOT,1,(255,255,255,255))
    elif motif == "sunwell_consecration":
        _ellipse(d,cx,cy,(-19,-19,19,19),gold,3)
        _line(d,cx,cy,[(0,-16),(0,16)],glow,5); _line(d,cx,cy,[(-15,0),(15,0)],glow,5)
        _poly(d,cx,cy,[(0,-8),(6,0),(0,8),(-6,0)],WHITE_HOT,gold,2)
        for x,y in [(-23,-23),(23,-23),(-23,23),(23,23)]: _ellipse(d,cx,cy,(x-2,y-2,x+2,y+2),second,1,(255,255,255,255))
    elif motif == "radiant_verdict":
        _line(d,cx,cy,[(0,20),(2,-6)],gold,6)
        _poly(d,cx,cy,[(-15,-14),(12,-17),(18,-7),(11,-1),(-12,-2)],main,WHITE_HOT,3)
        _poly(d,cx,cy,[(0,-25),(3,-17),(0,-12),(-3,-17)],glow,WHITE_HOT,1)
        _line(d,cx,cy,[(-18,2),(-12,7)],second,3); _line(d,cx,cy,[(18,2),(12,7)],second,3)
    elif motif == "silverhand_aegis":
        # Open gauntleted hand with a radiant palm-gem, rather than a second shield.
        _poly(d,cx,cy,[(-8,19),(-11,10),(-18,4),(-18,-2),(-14,-5),(-8,1),(-8,-15),(-4,-20),(-1,-17),(0,-3),(2,-21),(6,-21),(8,-17),(7,-2),(11,-15),(15,-14),(15,-10),(12,1),(17,-5),(21,-2),(19,4),(12,12),(8,19)],main,gold,3)
        _line(d,cx,cy,[(-8,7),(-1,10),(7,7),(12,10)],glow,3)
        _poly(d,cx,cy,[(2,2),(7,7),(2,12),(-3,7)],WHITE_HOT,gold,2)
        for x in (-14,-5,5,14): _line(d,cx,cy,[(x,-23),(x,-18)],second,2)
    elif motif == "resurrection":
        _line(d,cx,cy,[(0,20),(0,-13)],gold,5)
        _line(d,cx,cy,[(-13,-4),(0,-16),(13,-4)],glow,5)
        _poly(d,cx,cy,[(0,-8),(8,2),(0,12),(-8,2)],main,WHITE_HOT,3)
        _line(d,cx,cy,[(0,-22),(0,-27)],WHITE_HOT,3)
        _line(d,cx,cy,[(-18,-17),(-12,-12)],second,3); _line(d,cx,cy,[(18,-17),(12,-12)],second,3)
    elif motif == "event_horizon":
        _ellipse(d,cx,cy,(-18,-18,18,18),main,4,(7,8,20,255))
        for r in (13,8): _ellipse(d,cx,cy,(-r,-r,r,r),glow if r==13 else second,2)
        _poly(d,cx,cy,_star(7,4,math.pi/4),DARK_INK,WHITE_HOT,2)
        _line(d,cx,cy,[(-23,-4),(-17,-1)],gold,2); _line(d,cx,cy,[(17,1),(23,4)],gold,2)
    elif motif == "oblivion_cleave":
        _line(d,cx,cy,_bezier((-21,14),(-7,12),(3,-18),(22,-18)),glow,7)
        _line(d,cx,cy,[(-5,16),(5,3),(8,-7),(18,-19)],main,4)
        _poly(d,cx,cy,[(17,-21),(24,-24),(22,-16)],gold,WHITE_HOT,2)
        _ellipse(d,cx,cy,(-13,-8,-8,-3),second,1,(255,255,255,255))
    elif motif == "dreadlord_howl":
        _poly(d,cx,cy,[(-17,14),(-18,-7),(-10,-19),(-5,-7),(2,-19),(8,-9),(18,-10),(15,9),(6,20),(-5,16)],main,gold,4)
        _line(d,cx,cy,[(-7,2),(-3,6)],WHITE_HOT,3); _line(d,cx,cy,[(6,2),(10,5)],WHITE_HOT,3)
        _poly(d,cx,cy,[(-4,11),(4,11),(0,17)],second,WHITE_HOT,2)
    elif motif == "dark_portal":
        _poly(d,cx,cy,[(-15,-22),(10,-22),(19,-12),(17,16),(5,23),(-17,16),(-20,-10)],main,gold,4)
        _poly(d,cx,cy,[(-7,-13),(4,-17),(12,-8),(8,9),(0,15),(-9,7)],(8,8,19),glow,3)
        _line(d,cx,cy,[(-17,-11),(-7,-5),(-15,1)],WHITE_HOT,2)
        _ellipse(d,cx,cy,(13,-19,17,-15),second,1,(255,255,255,255))
    elif motif == "entropy_rift":
        _line(d,cx,cy,[(-19,-15),(-6,-8),(-12,1),(5,7),(-1,16),(19,20)],glow,5)
        _line(d,cx,cy,[(14,-20),(7,-11),(15,-4),(0,2)],main,4)
        _poly(d,cx,cy,[(-1,-19),(5,-13),(-1,-8),(-5,-13)],gold,WHITE_HOT,2)
        _ellipse(d,cx,cy,(-4,2,4,10),second,1,(255,255,255,255))
    elif motif == "soul_siphon":
        _ellipse(d,cx,cy,(-21,-12,-5,4),main,3,(13,21,39,255))
        _ellipse(d,cx,cy,(5,-4,21,12),second,3,(32,14,45,255))
        _line(d,cx,cy,_bezier((-7,-4),(-19,12),(20,-17),(7,4)),glow,5)
        _poly(d,cx,cy,[(7,3),(14,1),(11,8)],WHITE_HOT,gold,2)
    elif motif == "astral_phase":
        _poly(d,cx,cy,[(-20,-10),(-4,-20),(11,-13),(20,0),(6,19),(-12,16)],second,gold,3)
        _poly(d,cx,cy,[(-9,-15),(8,-17),(16,-5),(7,10),(-8,18),(-17,4)],main,WHITE_HOT,3)
        _ellipse(d,cx,cy,(-3,-4,3,2),glow,1,(255,255,255,255))
    elif motif == "singularity_collapse":
        _ellipse(d,cx,cy,(-18,-18,18,18),main,3,(6,8,18,255))
        for a in (0.0,2.1,4.2):
            x0,y0=math.cos(a)*24,math.sin(a)*24; x1,y1=math.cos(a)*9,math.sin(a)*9
            _line(d,cx,cy,[(x0,y0),(x1,y1)],glow,3)
            _poly(d,cx,cy,[(x1,y1),(x1+math.cos(a+2.5)*4,y1+math.sin(a+2.5)*4),(x1+math.cos(a-2.5)*4,y1+math.sin(a-2.5)*4)],gold,WHITE_HOT,1)
        _ellipse(d,cx,cy,(-5,-5,5,5),WHITE_HOT,2,(9,8,17,255))
    elif motif == "shuriken_fan":
        for a in (-0.42,0,0.42):
            pts=[(math.cos(a)*r, math.sin(a)*r) for r in (-19,19)]
            _line(d,cx,cy,pts,glow if a==0 else main,4)
            x,y=pts[1]
            _poly(d,cx,cy,[(x,y),(x-math.cos(a+0.55)*8,y-math.sin(a+0.55)*8),(x-math.cos(a-0.55)*8,y-math.sin(a-0.55)*8)],second,WHITE_HOT,2)
        _ellipse(d,cx,cy,(-4,-4,4,4),gold,2,(13,15,22,255))
    elif motif == "phantom_ambush":
        _poly(d,cx,cy,[(-16,20),(-9,-3),(0,-21),(9,-3),(16,20),(0,11)],main,gold,4)
        _line(d,cx,cy,[(-23,13),(-12,6),(0,8),(14,2),(23,5)],second,4)
        _ellipse(d,cx,cy,(-3,-7,3,-1),WHITE_HOT,1,(255,255,255,255))
    elif motif == "smoke_veil":
        for y,offset,col in [(-12,-8,second),(0,7,glow),(12,-3,main)]:
            _line(d,cx,cy,_bezier((-22,y+4),(-12,y-12),(3,y+12),(22,y+offset)),col,4)
        _poly(d,cx,cy,[(0,-17),(6,-4),(0,4),(-6,-4)],WHITE_HOT,gold,2)
    elif motif == "thousand_shadows":
        # Three offset phantom blades/afterimages; deliberately avoids another ring glyph.
        for off,col in [(-13,second),(0,glow),(13,main)]:
            _poly(d,cx,cy,[(off-5,17),(off-2,2),(off+1,-8),(off+6,-19),(off+7,-4),(off+4,7),(off+5,19)],col,gold,2)
        _line(d,cx,cy,[(-22,13),(-12,6),(-2,10),(8,1),(21,5)],WHITE_HOT,3)
        _poly(d,cx,cy,[(-5,-4),(0,-12),(5,-4),(2,1),(-3,1)],(16,12,25),glow,2)
        _line(d,cx,cy,[(-16,-14),(-9,-8)],second,2)
        _line(d,cx,cy,[(16,-14),(9,-8)],main,2)
    elif motif == "starfall_singularity":
        for x,y,rot,col in [(-14,-16,0.2,glow),(0,-22,0.0,WHITE_HOT),(15,-13,-0.3,main)]:
            _poly(d,cx,cy,[(x+sx,y+sy) for sx,sy in _star(7,4,rot)],col,gold,2)
            _line(d,cx,cy,[(x,y+7),(x*0.65,y+17)],second,2)
        _ellipse(d,cx,cy,(-8,8,8,24),main,3,(11,10,22,255))
    elif motif == "dimensional_banish":
        _poly(d,cx,cy,[(0,-22),(15,-8),(11,12),(0,22),(-11,12),(-15,-8)],main,gold,4)
        _poly(d,cx,cy,[(0,-13),(8,-3),(0,8),(-8,-3)],glow,WHITE_HOT,2)
        _line(d,cx,cy,[(-22,18),(18,-18)],second,4)
    elif motif == "null_field":
        _ellipse(d,cx,cy,(-21,-21,21,21),glow,4)
        _ellipse(d,cx,cy,(-12,-12,12,12),main,3)
        _line(d,cx,cy,[(-16,16),(16,-16)],WHITE_HOT,5)
        _poly(d,cx,cy,[(0,-8),(8,0),(0,8),(-8,0)],second,gold,2)
    elif motif == "cosmic_twilight":
        _ellipse(d,cx,cy,(-20,-20,20,20),main,3)
        d.rectangle((cx,cy-20*K,cx+20*K,cy+20*K),fill=(9,12,24,255))
        _ellipse(d,cx,cy,(-20,-20,20,20),glow,3)
        _poly(d,cx,cy,[(10+sx,-10+sy) for sx,sy in _star(6,5)],WHITE_HOT,gold,1)
        _line(d,cx,cy,[(-13,15),(-4,7),(3,14)],second,3)
    elif motif == "mjolnir_fall":
        _line(d,cx,cy,[(0,20),(2,-6)],gold,6)
        _poly(d,cx,cy,[(-16,-17),(13,-17),(18,-6),(12,1),(-14,0)],main,WHITE_HOT,3)
        _line(d,cx,cy,[(-22,-19),(-15,-11),(-20,-4)],glow,3)
        _line(d,cx,cy,[(21,-18),(15,-10),(20,-3)],second,3)
    elif motif == "magnetic_grip":
        _line(d,cx,cy,_bezier((-16,-15),(-25,15),(-16,23),(0,20)),main,7)
        _line(d,cx,cy,_bezier((16,-15),(25,15),(16,23),(0,20)),glow,7)
        _line(d,cx,cy,[(-16,-15),(-8,-21)],WHITE_HOT,5); _line(d,cx,cy,[(16,-15),(8,-21)],gold,5)
        for x,y in [(-8,-4),(9,0),(0,10)]: _poly(d,cx,cy,[(x,y-4),(x+4,y),(x,y+4),(x-4,y)],second,WHITE_HOT,2)
    elif motif == "aegis_core":
        # Runeforged turbine gear: radial teeth and a bright reactor iris, no shield outline.
        gear=[]
        for i in range(16):
            ang=-math.pi/2+i*math.pi/8
            r=23 if i%2==0 else 17
            gear.append((math.cos(ang)*r,math.sin(ang)*r))
        _poly(d,cx,cy,gear,main,gold,3)
        _ellipse(d,cx,cy,(-13,-13,13,13),second,3,(9,27,39,255))
        _ellipse(d,cx,cy,(-8,-8,8,8),glow,3,(14,42,56,255))
        for a in range(6):
            ang=a*math.pi/3
            _line(d,cx,cy,[(math.cos(ang)*9,math.sin(ang)*9),(math.cos(ang)*15,math.sin(ang)*15)],WHITE_HOT,2)
        _ellipse(d,cx,cy,(-3,-3,3,3),WHITE_HOT,1,(255,255,255,255))
    elif motif == "pantheon_wrath":
        for x,h,col in [(-14,18,second),(0,27,glow),(14,18,main)]:
            _poly(d,cx,cy,[(x-5,17),(x-5,17-h),(x,12-h),(x+5,17-h),(x+5,17)],col,gold,2)
        _line(d,cx,cy,[(-22,20),(22,20)],WHITE_HOT,3)
        _poly(d,cx,cy,[(0,-18),(5,-8),(0,1),(-5,-8)],gold,WHITE_HOT,2)
    elif motif == "molten_slag":
        _poly(d,cx,cy,[(-20,17),(-15,-3),(-7,6),(0,-21),(6,4),(14,-7),(20,17)],main,gold,3)
        _poly(d,cx,cy,[(-9,15),(-4,1),(1,10),(8,-1),(12,15)],glow,WHITE_HOT,2)
        for x,y in [(-15,-16),(15,-18),(20,1)]: _ellipse(d,cx,cy,(x-2,y-2,x+2,y+2),second,1,(255,255,255,255))
    elif motif == "forgehammer":
        _poly(d,cx,cy,[(-14,8),(13,8),(19,15),(12,20),(-18,20)],second,gold,3)
        _line(d,cx,cy,[(-3,10),(8,-12)],gold,7)
        _poly(d,cx,cy,[(-10,-17),(15,-19),(20,-10),(14,-3),(-12,-4)],main,WHITE_HOT,3)
        _line(d,cx,cy,[(-20,-2),(20,-2)],glow,2)
    elif motif == "rune_plating":
        # Rectangular articulated armor plate with stamped runes, unlike a hero shield.
        _poly(d,cx,cy,[(-17,-21),(17,-21),(22,-15),(22,15),(17,21),(-17,21),(-22,15),(-22,-15)],main,gold,4)
        _line(d,cx,cy,[(-15,-9),(15,-9)],second,3)
        _line(d,cx,cy,[(-15,9),(15,9)],second,3)
        for x,y in [(-12,-15),(12,-15),(-12,15),(12,15)]:
            _poly(d,cx,cy,[(x,y-2),(x+2,y),(x,y+2),(x-2,y)],WHITE_HOT,gold,1)
        _poly(d,cx,cy,[(-4,-5),(0,-11),(4,-5),(0,5)],glow,WHITE_HOT,2)
        _line(d,cx,cy,[(0,5),(0,12)],glow,3)
    elif motif == "forge_colossus":
        _poly(d,cx,cy,[(-17,19),(-16,1),(-22,-6),(-15,-14),(-7,-10),(-5,-22),(5,-22),(7,-10),(15,-14),(22,-6),(16,1),(17,19)],main,gold,4)
        _ellipse(d,cx,cy,(-6,-7,6,3),glow,2,(10,21,31,255))
        _line(d,cx,cy,[(-13,11),(13,11)],WHITE_HOT,3)
    elif motif == "cluster_rockets":
        for x,tilt,col in [(-13,-5,second),(0,0,glow),(13,5,main)]:
            _poly(d,cx,cy,[(x-4,-17+tilt),(x+4,-17+tilt),(x+4,9),(x,16),(x-4,9)],col,WHITE_HOT,2)
            _line(d,cx,cy,[(x,16),(x-3,23)],gold,3)
        _line(d,cx,cy,[(-19,-7),(-11,-12)],gold,2); _line(d,cx,cy,[(19,-7),(11,-12)],gold,2)
    elif motif == "gauss_rail":
        _poly(d,cx,cy,[(-22,-4),(17,-4),(22,0),(17,4),(-22,4)],main,gold,3)
        _line(d,cx,cy,[(-14,-12),(14,-12)],glow,3); _line(d,cx,cy,[(-14,12),(14,12)],second,3)
        _line(d,cx,cy,[(-21,0),(22,0)],WHITE_HOT,2)
        _ellipse(d,cx,cy,(14,-3,20,3),gold,1,(255,255,255,255))
    elif motif == "pocket_turrets":
        _poly(d,cx,cy,[(-20,12),(20,12),(15,20),(-15,20)],second,gold,3)
        _poly(d,cx,cy,[(-10,11),(-8,-3),(-1,-10),(7,-5),(8,11)],main,WHITE_HOT,3)
        _poly(d,cx,cy,[(3,-8),(20,-17),(22,-11),(8,-1)],glow,gold,3)
        _ellipse(d,cx,cy,(-3,-5,2,0),WHITE_HOT,1,(255,255,255,255))
    elif motif == "orbital_laser":
        _ellipse(d,cx,cy,(-17,-17,17,17),main,3)
        _ellipse(d,cx,cy,(-4,-4,4,4),glow,2,(255,255,255,255))
        _line(d,cx,cy,[(-12,12),(10,-10)],WHITE_HOT,4)
        _line(d,cx,cy,[(10,-10),(2,18)],second,5)
        _poly(d,cx,cy,[(2,18),(-3,9),(6,12)],gold,WHITE_HOT,2)
    elif motif == "ionosphere_field":
        for r,col in [(20,main),(15,glow),(8,second)]: _ellipse(d,cx,cy,(-r,-r,r,r),col,3)
        _line(d,cx,cy,[(-21,4),(-10,-5),(0,6),(10,-7),(21,1)],WHITE_HOT,3)
        _ellipse(d,cx,cy,(-3,-3,3,3),gold,1,(255,255,255,255))
    elif motif == "arc_conduit":
        nodes=[(-19,-14),(0,-3),(18,-17),(15,16),(-15,15)]
        for (x0,y0),(x1,y1) in zip(nodes,nodes[1:]):
            mx=(x0+x1)/2; my=(y0+y1)/2
            _line(d,cx,cy,[(x0,y0),(mx+((idx%3)-1)*3,my-4),(x1,y1)],glow,3)
        for j,(x,y) in enumerate(nodes): _ellipse(d,cx,cy,(x-3,y-3,x+3,y+3),main if j%2 else WHITE_HOT,2,(11,21,32,255))
    elif motif == "chrono_dynamo":
        _ellipse(d,cx,cy,(-19,-19,19,19),main,4)
        _ellipse(d,cx,cy,(-11,-11,11,11),glow,2)
        _line(d,cx,cy,[(0,0),(0,-8),(8,-8)],WHITE_HOT,4)
        for a in range(8):
            ang=a*math.pi/4
            _line(d,cx,cy,[(math.cos(ang)*20,math.sin(ang)*20),(math.cos(ang)*25,math.sin(ang)*25)],second,3)
    elif motif == "superconductor":
        for x in (-12,-4,4,12): _line(d,cx,cy,[(x,-17),(x+((idx%3)-1)*3,17)],main if x<0 else glow,3)
        _line(d,cx,cy,[(-20,10),(-10,4),(0,11),(10,-4),(20,-11)],WHITE_HOT,4)
        _ellipse(d,cx,cy,(-4,-4,4,4),gold,2,(15,28,39,255))
    else:
        raise ValueError(f"No authored icon renderer for {motif!r}")


def build_skill_icon(ability_index: int) -> Image.Image:
    """Render one original 64x64 icon with a faction frame and skill-specific silhouette."""
    aid, slot, _tgt, _order, _name, _desc = HERO_SKILL_SPECS_64[ability_index]
    hero = ability_index // 4
    faction = hero // 4
    main, glow = HERO_COLORS[hero]
    second = _mix(main, (255, 255, 255), 0.36)
    motif = SKILL_MOTIFS[ability_index]
    cx = cy = S // 2

    # Vignetted enamel field; the left/right light differs by hero, not just hue.
    dark = _mix(DARK_INK, main, 0.17)
    img = Image.new("RGBA", (S, S), (*dark, 255))
    px = img.load()
    for y in range(S):
        for x in range(S):
            dx, dy = x - cx, y - cy
            r = math.sqrt(dx * dx + dy * dy) / (S * 0.78)
            radial = max(0.0, 1.0 - r)
            directional = max(0.0, (dx * (1 if hero % 2 == 0 else -1) - dy * 0.48) / S)
            t = min(0.70, radial * 0.42 + directional * 0.17)
            px[x, y] = (*_mix(dark, main, t), 255)
    d = ImageDraw.Draw(img, "RGBA")

    # A different frame grammar for each empire: tide-cut octagon, sunburst, rift facets, gear rim.
    if faction == 0:
        sides, rotation = 8, math.pi / 8
        frame = (31, 209, 211)
    elif faction == 1:
        sides, rotation = 12, math.pi / 12
        frame = (243, 186, 86)
    elif faction == 2:
        sides, rotation = 6, math.pi / 6
        frame = (175, 103, 234)
    else:
        sides, rotation = 10, math.pi / 10
        frame = (107, 190, 211)
    outer = [(cx + math.cos(rotation + i * 2 * math.pi / sides) * 92, cy + math.sin(rotation + i * 2 * math.pi / sides) * 92) for i in range(sides)]
    inner = [(cx + math.cos(rotation + i * 2 * math.pi / sides) * 82, cy + math.sin(rotation + i * 2 * math.pi / sides) * 82) for i in range(sides)]
    d.polygon(outer, fill=(5, 8, 17, 255), outline=(2, 4, 11, 255))
    d.line(outer + [outer[0]], fill=(*frame, 255), width=5, joint="curve")
    d.polygon(inner, fill=(*_mix(DARK_INK, main, 0.20), 255), outline=(*_mix(frame, glow, 0.35), 255))
    d.line(inner + [inner[0]], fill=(11, 15, 25, 255), width=3, joint="curve")

    # Hero-specific radial crest and 64-way rim cuts are recessed behind the glyph.
    crest_rotation = (hero * 0.23 + slot * 0.11) % (2 * math.pi)
    for ray in range(6 + hero % 5):
        a = crest_rotation + ray * 2 * math.pi / (6 + hero % 5)
        r0 = 53 + (ray % 2) * 4
        r1 = 70 if (ray + hero) % 3 else 76
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0)
        p1 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1)
        d.line([p0, p1], fill=(*_mix(main, glow, 0.3), 190), width=3)
        d.ellipse((p1[0]-3, p1[1]-3, p1[0]+3, p1[1]+3), fill=(*glow, 210))
    pip_count = 4 + (ability_index % 9)
    for pip in range(pip_count):
        a = crest_rotation + pip * 2 * math.pi / pip_count
        rr = 76
        xx, yy = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        d.ellipse((xx-2.6, yy-2.6, xx+2.6, yy+2.6), fill=(*PALE_GOLD, 235))

    # Skill-specific silhouette is left unobstructed so the core shape survives 64px scaling.
    _draw_motif(d, cx, cy, motif, ability_index, main, glow, second)

    # Small Q/W/E/R jewel is consistent for discoverability, while the main glyph stays unique.
    key = ("Q", "W", "E", "R")[slot]
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    d.rounded_rectangle((13, 13, 38, 39), radius=5, fill=(5, 8, 14, 235), outline=(*frame, 255), width=2)
    key_box = d.textbbox((0, 0), key, font=font)
    key_w, key_h = key_box[2] - key_box[0], key_box[3] - key_box[1]
    key_x = 25.5 - key_w / 2 - key_box[0]
    key_y = 25.5 - key_h / 2 - key_box[1]
    d.text((key_x, key_y), key, font=font, fill=(*WHITE_HOT, 255), stroke_width=0)

    # A clean lacquer border survives BLP mipmaps and matches WC3's command-card framing.
    d.rounded_rectangle((4, 4, 188, 188), radius=18, outline=(2, 3, 8, 255), width=7)
    d.rounded_rectangle((8, 8, 184, 184), radius=15, outline=(*_mix(frame, glow, 0.20), 245), width=2)
    return img.resize((64, 64), Image.Resampling.LANCZOS).convert("RGBA")


def build_skill_icon_images() -> Dict[str, Image.Image]:
    """Return all 64 authored, distinct 64x64 RGBA command icons keyed by A000..A063."""
    out = {spec[0]: build_skill_icon(index) for index, spec in enumerate(HERO_SKILL_SPECS_64)}
    assert len(out) == 64 and len({img.tobytes() for img in out.values()}) == 64
    return out


def build_disabled_skill_icon(image: Image.Image) -> Image.Image:
    """Create a deliberately muted disabled twin while retaining the same icon silhouette."""
    rgba = image.convert("RGBA")
    gray = ImageOps.grayscale(rgba).convert("RGB")
    dark = Image.new("RGB", rgba.size, (9, 12, 19))
    gray = Image.blend(dark, gray, 0.52)
    out = gray.convert("RGBA")
    out.putalpha(rgba.getchannel("A"))
    overlay = Image.new("RGBA", rgba.size, (12, 16, 24, 50))
    muted = Image.alpha_composite(out, overlay)
    muted.putalpha(rgba.getchannel("A"))
    return muted


def save_skill_icon_galleries(icons: Dict[str, Image.Image]) -> None:
    """Write one readable 4-hero x 4-skill gallery for each custom empire to web/public."""
    font = ImageFont.load_default()
    small = ImageFont.load_default()
    sheet_w, sheet_h = 744, 552
    label_w, cell_w, row_h = 172, 137, 112
    for faction in range(4):
        sheet = Image.new("RGB", (sheet_w, sheet_h), (8, 12, 22))
        d = ImageDraw.Draw(sheet)
        d.rounded_rectangle((8, 8, sheet_w-9, sheet_h-9), radius=18, fill=(14, 20, 34), outline=(65, 82, 112), width=2)
        d.text((24, 19), FACTION_NAMES[faction], font=font, fill=(240, 213, 143))
        d.text((24, 39), "16 original buttons • Q / W / E / R", font=small, fill=(157, 185, 206))
        headers = ("Q", "W", "E", "R")
        for slot, label in enumerate(headers):
            x = label_w + slot * cell_w + 50
            d.text((x, 49), label, font=font, fill=(94, 217, 234) if slot < 3 else (255, 205, 107))
        for row in range(4):
            hero = faction * 4 + row
            y = 70 + row * row_h
            main, glow = HERO_COLORS[hero]
            d.line((20, y + row_h - 5, sheet_w-20, y + row_h - 5), fill=(39, 52, 72), width=1)
            d.text((22, y + 13), f"{hero+1:02d}  {HERO_NAMES[hero]}", font=font, fill=(*glow, 255))
            d.text((22, y + 31), FACTION_NAMES[faction].split()[0], font=small, fill=(*main, 255))
            for slot in range(4):
                aid = f"A{hero*4+slot:03d}"
                x = label_w + slot * cell_w + 31
                d.rounded_rectangle((x-3, y+2, x+87, y+91), radius=9, fill=(7, 11, 20), outline=(*_mix(main, glow, 0.28), 220), width=1)
                sheet.paste(icons[aid].resize((80, 80), Image.Resampling.LANCZOS), (x, y+5), icons[aid].resize((80, 80), Image.Resampling.LANCZOS))
                name = HERO_SKILL_SPECS_64[hero*4+slot][4]
                label = name if len(name) <= 18 else name[:17] + "…"
                d.text((x-1, y+91), label, font=small, fill=(197, 207, 221))
        path = GALLERY_PATHS[faction]
        path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(path, format="PNG", optimize=True)
