#!/usr/bin/env python3
"""
Custom Playable Races, Object Modifications & Pro-Level Melee AI Generator
for `(8) Crown of WarMahdi` (Warcraft III TFT 1.26a/1.27b & Reforged).

Implements two complete, strictly ladder-balanced Altered Melee factions alongside
the 4 unmodified standard Warcraft III races:
  5. Naga Empire (`RACE_NAGA = 5`)
  6. Campaign Human — Silvermoon & Alliance Expedition (`RACE_CAMPHUMAN = 6`)

Key v2 Engineering & Balance Guarantees:
  - Every unit, caster, siege engine, flying unit, hero, tower, and upgrade is
    placed in its authentic, dedicated production building with clean 4x3 button
    coordinates and Tier-1 / Tier-2 / Tier-3 tech gating (zero misplaced units!).
  - All inflated campaign stats (Couatl 29 DPS, Dragon Turtle Chaos + Devour,
    Royal Guard Chaos + 500 MP + Stun + Summon, armed Scout Tower, Lieutenant
    Spell Immunity, 400-MP campaign casters, 2.0-cooldown workers) are normalized
    to exact Frozen Throne 1.26a/1.27b melee EHP/DPS/cost curves.
  - Every `war3map.w3u`, `war3map.w3t`, and `war3map.w3q` modification uses exact
    `UnitMetaData.slk` / `UpgradeMetaData.slk` variable types (`VT_INT=0`,
    `VT_REAL=1`, `VT_UNREAL=2`, `VT_STR=3`) in cross-patch binary v2 format.
"""

from __future__ import annotations

import struct
from typing import Any, List, Tuple

# Variable types in WC3 Object Editor binary tables (w3u / w3t / w3q)
VT_INT = 0
VT_REAL = 1
VT_UNREAL = 2
VT_STR = 3

ModEntry = Tuple[str, int, Any]
LevelModEntry = Tuple[str, int, int, int, Any]


def _pack_fourcc(code: str) -> bytes:
    raw = code.encode("latin1")
    if len(raw) != 4:
        raise ValueError(f"Expected 4-char rawcode, got {code!r}")
    return raw


def _sort_obj_id_key(item: Tuple[str, str, List[Any]]) -> int:
    """
    Sort custom object IDs matching w3x2lni's backend_obj.lua order
    (uppercase Hero IDs before lowercase unit/building IDs).
    """
    orig_id, new_id, _ = item
    key_id = new_id if new_id != "\x00\x00\x00\x00" else orig_id
    b = key_id.encode("latin1")
    val = b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24)
    is_upper = 0 if (65 <= b[0] <= 90) else 1
    return (is_upper << 33) | val


def _pack_mod_table(
    objects: List[Tuple[str, str, List[Any]]],
    use_optional_ints: bool = False,
) -> bytes:
    buf = bytearray()
    ordered = sorted(objects, key=_sort_obj_id_key)
    buf += struct.pack("<I", len(ordered))
    for orig_id, new_id, mods in ordered:
        buf += _pack_fourcc(orig_id)
        buf += _pack_fourcc(new_id)
        buf += struct.pack("<I", len(mods))
        for m in mods:
            if use_optional_ints:
                field_id, vtype, level, data_ptr, val = m
            else:
                field_id, vtype, val = m
                level, data_ptr = 0, 0
            buf += _pack_fourcc(field_id)
            buf += struct.pack("<I", vtype)
            if use_optional_ints:
                buf += struct.pack("<iI", int(level), int(data_ptr))
            if vtype == VT_INT:
                buf += struct.pack("<i", int(val))
            elif vtype in (VT_REAL, VT_UNREAL):
                buf += struct.pack("<f", float(val))
            elif vtype == VT_STR:
                buf += str(val).encode("utf-8") + b"\x00"
            else:
                raise ValueError(f"Unsupported variableType {vtype}")
            buf += b"\x00\x00\x00\x00"
    return bytes(buf)


# ==============================================================================
# 1. UNIT, HERO & BUILDING OBJECT MODIFICATIONS (`war3map.w3u` v2)
# ==============================================================================

def build_unit_modifications() -> Tuple[
    List[Tuple[str, str, List[ModEntry]]],
    List[Tuple[str, str, List[ModEntry]]],
]:
    """
    Returns `(original_table, custom_table)` for `war3map.w3u` (version 2).

    Architecture & Proper Unit Placement ("در جاهای خودشون"):
      - NAGA EMPIRE (`nmpe` builds 9 structures):
          * `nntt` -> `n001` -> `n002` (Town Hall T1/T2/T3): trains ONLY `nmpe` Slave.
          * `nnfm` Coral Bed: +9 Food (`90g/25L`, `500 HP`).
          * `n004` Coral Forge (Armory): researches `Rnat` Blades & `Rnam` Scales.
          * `nnad` Altar of the Depths: summons `Hvsh`, `N001`, `N002`, `N003`.
          * `n003` Tidal Treasury (Shop): sells scrolls, potions, TP, Orb of the Abyss.
          * `nntg` Tidal Guardian (Tower, req `n004`): `500 HP`, `24.1` Pierce DPS.
          * `nnsg` Spawning Grounds (Barracks): trains `nnmg` Mur'gul Reaver (T1),
            `nsnp` Snap Dragon (req `n004`), `nmyr` Naga Myrmidon (T2 req `n001`);
            researches `Rnen` Ensnare & `Rnsb` Submerge.
          * `nnsa` Shrine of Azshara (Caster/Air Sanctum, req `n001`): trains `nnsw`
            Naga Siren & `nwgs` Couatl; researches `Rnsw` Siren Training & `Rnsi` Abolish.
          * `n005` Abyssal Behemoth Pool (Siege & T3 Elite Sanctum, req `n001,n004`):
            trains `nhyc` Dragon Turtle (T2 Siege) & `nnrg` Naga Royal Guard (T3 Elite).

      - CAMPAIGN HUMAN — SILVERMOON (`nhew` builds 11 structures):
          * `h001` -> `h002` -> `h003` (Town Hall T1/T2/T3): trains `nhew` Worker &
            researches `Rhpm` Backpack.
          * `nefm` High Elven Farm: +6 Food (`80g/20L`, `500 HP`).
          * `h007` Silvermoon Barracks (`HumanBarracks.mdl`): trains `hhes` Swordsman (T1),
            `nhea` High Elven Archer (T1), `hcth` Alliance Captain (T3 Knight-tier);
            researches `Rhde` Defend & `Rhan` Veteran War Training.
          * `hlum` Lumber Mill & `hbla` Blacksmith: standard Human lumber/masonry &
            +1/+2/+3 weapon/armor upgrades (unlocked at T2/T3 via `udep` equivalents).
          * `h004` Altar of Silvermoon: summons `Hkal`, `Hvwd`, `Hlgr`, `Huth`.
          * `h005` Sunwell Reliquary (Shop): sells scrolls, potions, Sanctuary, Orb of Fire.
          * `negt` Sunspire Scout Tower (`30g/20L`, `300 HP`, unarmed) -> upgrades to
            `negf` Sunspire Guard Tower (`70g/50L`, `26.3` Pierce DPS) or
            `negm` Sunspire Arcane Tower (`70g/50L`, Feedback + Reveal + Magic Sentry).
          * `nheb` High Elven Mage Tower (`MageTower.mdl`, req `h002`): trains `nchp`
            Silvermoon Chaplain, `nhym` Dalaran Hydromancer, `hspt` Spell Breaker;
            researches `Rhst`, `Rhpt`, `Rhss`.
          * `h008` Silvermoon Siege Workshop (`Workshop.mdl`, req `h002,hbla`): trains
            `hgyr` Flying Machine, `h006` Silvermoon Ballista, `nbel` Blood Elf
            Lieutenant (T3 Runeblade Champion); researches `Rhgb` Bombs.
          * `h009` Silvermoon Dragonhawk Aviary (`GryphonAviary.mdl`, req `h002,hlum`):
            trains `hdhw` Dragonhawk Rider (T2) & `hgry` Gryphon Rider (T3);
            researches `Rhcd` Cloud & `Rhhb` Storm Hammers.
    """
    NULL_ID = "\x00\x00\x00\x00"

    original: List[Tuple[str, str, List[ModEntry]]] = [
        # ---- Dependency equivalents on Human tech structures (ZERO stat changes to Human!) ----
        ("hkee", NULL_ID, [("udep", VT_STR, "h002")]),
        ("hcas", NULL_ID, [("udep", VT_STR, "h003")]),
        ("halt", NULL_ID, [("udep", VT_STR, "h004")]),
        ("hvlt", NULL_ID, [("udep", VT_STR, "h005")]),
        ("hbar", NULL_ID, [("udep", VT_STR, "h007")]),
        ("harm", NULL_ID, [("udep", VT_STR, "h008")]),
        ("hgra", NULL_ID, [("udep", VT_STR, "h009")]),

        # ======================================================================
        # NAGA EMPIRE — ORIGINAL UNITS, BUILDINGS & HERO (`Hvsh`)
        # ======================================================================

        # Worker: Mur'gul Slave (`nmpe`) — Exact melee worker stats (75g, 230 HP, +0.25 HP/s)
        # Build Grid (9 structures, clean 4x3):
        #   Row 0: (0,0) nntt | (1,0) nnfm | (2,0) nnsg | (3,0) n004
        #   Row 1: (0,1) nnad | (1,1) n003 | (2,1) nntg
        #   Row 2: (0,2) nnsa | (1,2) n005
        ("nmpe", NULL_ID, [
            ("ubui", VT_STR, "nntt,nnfm,nnsg,n004,nnad,n003,nntg,nnsa,n005"),
            ("ugol", VT_INT, 75),
            ("ulum", VT_INT, 0),
            ("ufoo", VT_INT, 1),
            ("ubld", VT_INT, 15),
            ("uhpm", VT_INT, 230),
            ("uhpr", VT_UNREAL, 0.25),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 0),
            ("udty", VT_STR, "medium"),
            ("umvs", VT_INT, 190),
            ("ua1b", VT_INT, 5),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 2),
            ("ua1c", VT_UNREAL, 2.0),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Train Mur'gul |cffffcc00S|rlave"),
            ("utub", VT_STR, "Amphibious worker unit. Can harvest Gold and Lumber, construct Naga structures, and Repair. Attacks land units and trees."),
        ]),

        # Tier 1 Town Hall: Temple of Tides (`nntt`) — Worker production & resource drop-off ONLY
        ("nntt", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 385),
            ("ulum", VT_INT, 185),
            ("ubld", VT_INT, 120),
            ("ufma", VT_INT, 11),
            ("uhpm", VT_INT, 1500),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "nmpe"),
            ("ures", VT_STR, ""),
            ("uupt", VT_STR, "n001"),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Build |cffffcc00T|remple of Tides"),
            ("utub", VT_STR, "Primary Naga town structure. Trains Mur'gul Slaves and receives gathered Gold and Lumber. Can be upgraded to Sanctuary of Tides and Abyssal Citadel."),
        ]),

        # Food Structure: Coral Bed (`nnfm`) — 90g/25L, +9 Food, 500 HP (matches Burrow/Ziggurat/Moon Well)
        ("nnfm", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 90),
            ("ulum", VT_INT, 25),
            ("ubld", VT_INT, 30),
            ("ufma", VT_INT, 9),
            ("uhpm", VT_INT, 500),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Build |cffffcc00C|roral Bed"),
            ("utub", VT_STR, "Provides 9 food, increasing the maximum number of Naga units that can be trained."),
        ]),

        # Barracks: Spawning Grounds (`nnsg`) — Infantry, Ranged & Heavy Melee ONLY
        ("nnsg", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 180),
            ("ulum", VT_INT, 50),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1300),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "nnmg,nsnp,nmyr"),
            ("ures", VT_STR, "Rnen,Rnsb"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Build Spawning |cffffcc00G|rrounds"),
            ("utub", VT_STR, "Primary Naga troop production structure. Trains Mur'gul Reavers, Snap Dragons, and Naga Myrmidons. Also researches Ensnare and Submerge."),
        ]),

        # Altar: Altar of the Depths (`nnad`) — Summons 4 Naga Heroes
        ("nnad", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 180),
            ("ulum", VT_INT, 50),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 900),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "Hvsh,N001,N002,N003"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Build |cffffcc00A|rltar of the Depths"),
            ("utub", VT_STR, "Summons Naga Heroes (Lady Vashj, Abyssal Warlord, Azshara's Tideweaver, and Makrura Deepking) and revives fallen Heroes."),
        ]),

        # Defensive Tower: Tidal Guardian (`nntg`) — Requires Coral Forge (`n004`), Pierce 24.1 DPS
        ("nntg", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "n004"),
            ("ugol", VT_INT, 135),
            ("ulum", VT_INT, 80),
            ("ubld", VT_INT, 50),
            ("uhpm", VT_INT, 500),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "pierce"),
            ("ua1b", VT_INT, 22),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 8),
            ("ua1c", VT_UNREAL, 1.10),
            ("ua1r", VT_INT, 700),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "Abds,Adts"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "Build Tidal G|cffffcc00u|rardian"),
            ("utub", VT_STR, "Defensive coral spire that hurls lightning bolts at ground and air attackers. Has Magic Sentry to reveal invisible enemies."),
        ]),

        # Caster & Flyer Sanctum: Shrine of Azshara (`nnsa`) — Requires Tier 2 (`n001`)
        ("nnsa", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 150),
            ("ulum", VT_INT, 140),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 950),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "nnsw,nwgs"),
            ("ures", VT_STR, "Rnsw,Rnsi"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Build |cffffcc00S|rhrine of Azshara"),
            ("utub", VT_STR, "Spellcaster and flying creature sanctum. Trains Naga Sirens and Couatls, and researches Naga Siren Training and Abolish Magic."),
        ]),

        # Tier 1 Light Melee: Mur'gul Reaver (`nnmg`) — Trained at Spawning Grounds (`nnsg`) (0,0)
        # 2 Food, 125g, 20s, 410 HP, 1 Large armor, 11+1d5=14.0 Normal / 1.45s = 9.7 DPS
        ("nnmg", NULL_ID, [
            ("ugol", VT_INT, 125),
            ("ulum", VT_INT, 0),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 20),
            ("uhpm", VT_INT, 410),
            ("uhpr", VT_UNREAL, 0.50),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 1),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 270),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "normal"),
            ("ua1b", VT_INT, 11),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 5),
            ("ua1c", VT_UNREAL, 1.45),
            ("upgr", VT_STR, "Rnat,Rnam"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Train Mur'gul |cffffcc00R|reaver"),
            ("utub", VT_STR, "Agile amphibious Tier-1 shock infantry. Can traverse deep water and engage land forces."),
        ]),

        # Tier 1.5 Ranged Piercing: Snap Dragon (`nsnp`) — Trained at Spawning Grounds (`nnsg`) (1,0)
        # Requires Coral Forge (`n004`) — matches Crypt Fiend / Rifleman timing & EHP/DPS!
        # 3 Food, 205g/35L, 28s, 520 HP, 0 Medium armor, 19+1d7=23.0 Pierce / 2.0s = 11.5 DPS + Slow Poison
        ("nsnp", NULL_ID, [
            ("ureq", VT_STR, "n004"),
            ("ugol", VT_INT, 205),
            ("ulum", VT_INT, 35),
            ("ufoo", VT_INT, 3),
            ("ubld", VT_INT, 28),
            ("uhpm", VT_INT, 520),
            ("uhpr", VT_UNREAL, 0.50),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 0),
            ("udty", VT_STR, "medium"),
            ("umvs", VT_INT, 280),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "pierce"),
            ("ua1b", VT_INT, 19),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 7),
            ("ua1c", VT_UNREAL, 2.00),
            ("ua1r", VT_INT, 500),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "Aspo,Asb3"),
            ("upgr", VT_STR, "Rnat,Rnam,Rnsb"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "D"),
            ("utip", VT_STR, "Train Snap |cffffcc00D|rragon"),
            ("utub", VT_STR, "Venomous ranged reptile armed with Slow Poison spines. Can learn Submerge. Attacks land and air units."),
        ]),

        # Tier 2 Heavy Melee: Naga Myrmidon (`nmyr`) — Trained at Spawning Grounds (`nnsg`) (2,0)
        # Requires Sanctuary of Tides (`n001`) — matches Druid of the Claw / Knight / Abomination tier!
        # 4 Food, 235g/50L, 36s, 860 HP, 3 Large armor, 26+1d7=30.0 Normal / 1.75s = 17.1 DPS
        ("nmyr", NULL_ID, [
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 235),
            ("ulum", VT_INT, 50),
            ("ufoo", VT_INT, 4),
            ("ubld", VT_INT, 36),
            ("uhpm", VT_INT, 860),
            ("uhpr", VT_UNREAL, 0.50),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 3),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 270),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "normal"),
            ("ua1b", VT_INT, 26),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 7),
            ("ua1c", VT_UNREAL, 1.75),
            ("uabi", VT_STR, "ANen,Asb1"),
            ("upgr", VT_STR, "Rnat,Rnam,Rnen,Rnsb"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "M"),
            ("utip", VT_STR, "Train Naga |cffffcc00M|ryrmidon"),
            ("utub", VT_STR, "Heavy Tier-2 amphibious warrior. Can learn Ensnare to pull down air units and Submerge to regenerate underwater. Attacks land units."),
        ]),

        # Tier 2 Spellcaster: Naga Siren (`nnsw`) — Trained at Shrine of Azshara (`nnsa`) (0,0)
        # Normalized from 400 campaign MP -> 200 base MP (75 initial), 310 HP, 2 Food, 140g/25L
        ("nnsw", NULL_ID, [
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 140),
            ("ulum", VT_INT, 25),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 28),
            ("uhpm", VT_INT, 310),
            ("uhpr", VT_UNREAL, 0.35),
            ("uhrt", VT_STR, "always"),
            ("umpm", VT_INT, 200),
            ("umpi", VT_INT, 75),
            ("umpr", VT_UNREAL, 0.67),
            ("udef", VT_INT, 0),
            ("udty", VT_STR, "none"),
            ("umvs", VT_INT, 270),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "magic"),
            ("ua1b", VT_INT, 8),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 4),
            ("ua1c", VT_UNREAL, 1.75),
            ("ua1r", VT_INT, 600),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "ANpa,ACfu,Acny"),
            ("udaa", VT_STR, "ANpa"),
            ("upgr", VT_STR, "Rnsw"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Train Naga |cffffcc00S|riren"),
            ("utub", VT_STR, "Mystic Naga spellcaster. Initially casts Parasite; can learn Frost Armor (Adept) and Cyclone (Master). Attacks land and air units."),
        ]),

        # Tier 2 Flying Anti-Caster: Couatl (`nwgs`) — Trained at Shrine of Azshara (`nnsa`) (1,0)
        # FIXED campaign 29.0 DPS -> 9.4 Magic DPS (matches Faerie Dragon / Destroyer per food!)
        # 2 Food, 150g/35L, 28s, 430 HP, 1 Small (Light) armor, 200 MP, Abolish Magic (`Andm`)
        ("nwgs", NULL_ID, [
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 150),
            ("ulum", VT_INT, 35),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 28),
            ("uhpm", VT_INT, 430),
            ("uhpr", VT_UNREAL, 0.35),
            ("uhrt", VT_STR, "always"),
            ("umpm", VT_INT, 200),
            ("umpi", VT_INT, 75),
            ("umpr", VT_UNREAL, 0.67),
            ("udef", VT_INT, 1),
            ("udty", VT_STR, "small"),
            ("umvs", VT_INT, 320),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "magic"),
            ("ua1b", VT_INT, 14),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 5),
            ("ua1c", VT_UNREAL, 1.80),
            ("ua1r", VT_INT, 450),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "Andm"),
            ("udaa", VT_STR, "Andm"),
            ("upgr", VT_STR, "Rnat,Rnam,Rnsi"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Train |cffffcc00C|rouatl"),
            ("utub", VT_STR, "Swift flying sky-serpent. Deals Magic damage to ground and air targets and can learn Abolish Magic to dispel buffs and damage summons."),
        ]),

        # Tier 2 Siege Beast: Dragon Turtle (`nhyc`) — Trained at Abyssal Behemoth Pool (`n005`) (0,0)
        # FIXED campaign Chaos + 1150 HP + Devour -> 650 HP, Pierce vs units + 18.6 Siege DPS vs buildings!
        ("nhyc", NULL_ID, [
            ("ureq", VT_STR, "n001,n004"),
            ("ugol", VT_INT, 230),
            ("ulum", VT_INT, 65),
            ("ufoo", VT_INT, 4),
            ("ubld", VT_INT, 38),
            ("uhpm", VT_INT, 650),
            ("uhpr", VT_UNREAL, 0.50),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 2),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 230),
            ("uaen", VT_INT, 3),
            ("ua1t", VT_STR, "pierce"),
            ("ua1b", VT_INT, 16),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 6),
            ("ua1c", VT_UNREAL, 1.80),
            ("ua1r", VT_INT, 450),
            ("ua1g", VT_STR, "ground,debris,item,ward"),
            ("ua2t", VT_STR, "siege"),
            ("ua2b", VT_INT, 47),
            ("ua2d", VT_INT, 1),
            ("ua2s", VT_INT, 9),
            ("ua2c", VT_UNREAL, 2.80),
            ("ua2r", VT_INT, 550),
            ("ua2g", VT_STR, "structure,tree,wall"),
            ("uabi", VT_STR, "ANth,Ansk"),
            ("upgr", VT_STR, "Rnat,Rnam"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Train Dragon |cffffcc00T|rurtle"),
            ("utub", VT_STR, "Armored amphibious siege beast protected by Hardened Skin and Thorny Shield. Bombards enemy structures from range."),
        ]),

        # Tier 3 Elite Champion: Naga Royal Guard (`nnrg`) — Trained at Abyssal Behemoth Pool (`n005`) (1,0)
        # FIXED campaign Chaos + 1350 HP + 500 MP + Stun + Summon -> 5 Food, 300g/90L, 1100 HP,
        # 4 Large armor, 20.6 Normal DPS (exact Tauren / Mountain Giant / Frost Wyrm Tier-3 budget!)
        ("nnrg", NULL_ID, [
            ("ureq", VT_STR, "n002"),
            ("ugol", VT_INT, 300),
            ("ulum", VT_INT, 90),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 44),
            ("uhpm", VT_INT, 1100),
            ("uhpr", VT_UNREAL, 0.50),
            ("uhrt", VT_STR, "always"),
            ("umpm", VT_INT, 250),
            ("umpi", VT_INT, 100),
            ("umpr", VT_UNREAL, 0.75),
            ("udef", VT_INT, 4),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 280),
            ("usca", VT_REAL, 1.05),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "normal"),
            ("ua1b", VT_INT, 31),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 9),
            ("ua1c", VT_UNREAL, 1.75),
            ("uabi", VT_STR, "ACcv,ACsk,Asb2"),
            ("upgr", VT_STR, "Rnat,Rnam,Rnsb"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Train Naga Royal |cffffcc00G|ruard"),
            ("utub", VT_STR, "Supreme Tier-3 Naga champion. Has Resistant Skin, Submerge, and Crushing Wave to devastate enemy formations."),
        ]),

        # Naga Hero 1: Lady Vashj (`Hvsh`, INT) — Exact melee Hero cost/supply/tier gating
        ("Hvsh", NULL_ID, [
            ("urac", VT_STR, "naga"),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 100),
            ("ustr", VT_INT, 16),
            ("uagi", VT_INT, 19),
            ("uint", VT_INT, 21),
            ("ustp", VT_UNREAL, 1.80),
            ("uagp", VT_UNREAL, 1.50),
            ("uinp", VT_UNREAL, 2.70),
            ("umvs", VT_INT, 290),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "n001"),
            ("urq2", VT_STR, "n002"),
            ("uhab", VT_STR, "ANfl,ANfa,ANms,ANto"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "V"),
            ("utip", VT_STR, "Summon Lady |cffffcc00V|rashj"),
            ("utpr", VT_STR, "Revive Lady |cffffcc00V|rashj"),
            ("utub", VT_STR, "Mystic Naga Sea Witch Hero, adept at ranged attrition and spellcasting. Can learn Forked Lightning, Frost Arrows, Mana Shield, and Tornado."),
        ]),

        # ======================================================================
        # CAMPAIGN HUMAN (SILVERMOON & ALLIANCE EXPEDITION) — ORIGINAL UNITS & HEROES
        # ======================================================================

        # Worker: Silvermoon Worker (`nhew`) — Exact Human Peasant stats!
        # Build Grid (11 structures, leaves (3,2) Cancel free!):
        #   Row 0: (0,0) h001 Hall | (1,0) nefm Farm | (2,0) h007 Barracks | (3,0) hlum Mill
        #   Row 1: (0,1) hbla Smith| (1,1) h004 Altar| (2,1) h005 Reliquary| (3,1) negt Tower
        #   Row 2: (0,2) nheb Mage | (1,2) h008 Siege| (2,2) h009 Aviary
        ("nhew", NULL_ID, [
            ("unam", VT_STR, "Silvermoon Worker"),
            ("urac", VT_STR, "human"),
            ("ubui", VT_STR, "h001,nefm,h007,hlum,hbla,h004,h005,negt,nheb,h008,h009"),
            ("uabi", VT_STR, "Ahar,Ahrp,Aneu,Aihn"),
            ("upgr", VT_STR, "Rhpm"),
            ("ugol", VT_INT, 75),
            ("ulum", VT_INT, 0),
            ("ufoo", VT_INT, 1),
            ("ubld", VT_INT, 15),
            ("uhpm", VT_INT, 220),
            ("uhpr", VT_UNREAL, 0.25),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 0),
            ("udty", VT_STR, "medium"),
            ("umvs", VT_INT, 190),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "normal"),
            ("ua1b", VT_INT, 4),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 2),
            ("ua1c", VT_UNREAL, 2.00),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "W"),
            ("utip", VT_STR, "Train Silvermoon |cffffcc00W|rorker"),
            ("utub", VT_STR, "Basic High Elven worker unit. Harvesters of Gold and Lumber who construct and repair Silvermoon structures."),
        ]),

        # Food Structure: High Elven Farm (`nefm`) — Exact Human Farm stats (80g/20L, +6 Food, 500 HP)
        ("nefm", NULL_ID, [
            ("unam", VT_STR, "High Elven Farm"),
            ("urac", VT_STR, "human"),
            ("ugol", VT_INT, 80),
            ("ulum", VT_INT, 20),
            ("ubld", VT_INT, 35),
            ("ufma", VT_INT, 6),
            ("uhpm", VT_INT, 500),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("upgr", VT_STR, "Rhac"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "F"),
            ("utip", VT_STR, "Build High Elven |cffffcc00F|rarm"),
            ("utub", VT_STR, "Provides 6 food, increasing the maximum number of Expedition units that can be trained."),
        ]),

        # Tier-2 Caster Sanctum: High Elven Mage Tower (`nheb`, `MageTower.mdl`!)
        # FIXED: `nheb` is visually a Silvermoon Mage Tower (`MageTower.mdl`), so it now
        # authentically trains ONLY Casters & Spell Breakers (just like Arcane Sanctum!),
        # while Infantry & Archers train at `h007` Silvermoon Barracks (`HumanBarracks.mdl`)!
        ("nheb", NULL_ID, [
            ("unam", VT_STR, "High Elven Mage Tower"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, "h002"),
            ("ugol", VT_INT, 150),
            ("ulum", VT_INT, 140),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1050),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "nchp,nhym,hspt"),
            ("ures", VT_STR, "Rhst,Rhpt,Rhss"),
            ("upgr", VT_STR, "Rhac"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Build High Elven Mage |cffffcc00T|rower"),
            ("utub", VT_STR, "Silvermoon spellcaster sanctum. Trains Silvermoon Chaplains, Dalaran Hydromancers, and Blood Elf Spell Breakers. Also researches Hydromancer Training, Chaplain Training, and Control Magic."),
        ]),

        # Base Tower: Sunspire Scout Tower (`negt`) — FIXED: 30g/20L, 300 HP, UNARMED (`uaen = 0`)!
        ("negt", NULL_ID, [
            ("unam", VT_STR, "Sunspire Scout Tower"),
            ("urac", VT_STR, "human"),
            ("ugol", VT_INT, 30),
            ("ulum", VT_INT, 20),
            ("ubld", VT_INT, 25),
            ("uhpm", VT_INT, 300),
            ("udef", VT_INT, 0),
            ("udty", VT_STR, "fort"),
            ("uaen", VT_INT, 0),
            ("uupt", VT_STR, "negf,negm"),
            ("uabi", VT_STR, "Abds,Adts"),
            ("upgr", VT_STR, "Rhac"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "O"),
            ("utip", VT_STR, "Build Sunspire Sc|cffffcc00o|rut Tower"),
            ("utub", VT_STR, "Observation spire with Magic Sentry. Has no attack, but can be upgraded into a Sunspire Guard Tower or a Sunspire Arcane Tower."),
        ]),

        # Tower Upgrade 1: Sunspire Guard Tower (`negf`) — Exact Human Guard Tower parity!
        ("negf", NULL_ID, [
            ("unam", VT_STR, "Sunspire Guard Tower"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, "hlum"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNGuardTower.blp"),
            ("ugol", VT_INT, 70),
            ("ulum", VT_INT, 50),
            ("ubld", VT_INT, 50),
            ("uhpm", VT_INT, 500),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "pierce"),
            ("ua1b", VT_INT, 22),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 5),
            ("ua1c", VT_UNREAL, 0.95),
            ("ua1r", VT_INT, 700),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "Abds,Adts"),
            ("upgr", VT_STR, "Rhac"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Upgrade to Sunspire |cffffcc00G|ruard Tower"),
            ("utub", VT_STR, "Primary defensive tower firing rapid sun-forged bolts at ground and air attackers."),
        ]),

        # Tower Upgrade 2: Sunspire Arcane Tower (`negm`) — Exact Human Arcane Tower parity!
        ("negm", NULL_ID, [
            ("unam", VT_STR, "Sunspire Arcane Tower"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, "h005"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNHumanArcaneTower.blp"),
            ("ugol", VT_INT, 70),
            ("ulum", VT_INT, 50),
            ("ubld", VT_INT, 50),
            ("uhpm", VT_INT, 500),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "pierce"),
            ("ua1b", VT_INT, 9),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 3),
            ("ua1c", VT_UNREAL, 1.00),
            ("ua1r", VT_INT, 800),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "Abds,Afbt,AHta,Adts"),
            ("upgr", VT_STR, "Rhac"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "N"),
            ("utip", VT_STR, "Upgrade to Sunspire Arca|cffffcc00n|re Tower"),
            ("utub", VT_STR, "Magical defense spire with Arcane Feedback (destroys enemy Hero and caster mana, dealing bonus damage to summons) and Reveal."),
        ]),

        # Tier 1 Infantry: High Elven Swordsman (`hhes`) — Trained at Silvermoon Barracks (`h007`) (0,0)
        # Distinct `BTNFootman.blp` icon (so `hcth` keeps `BTNTheCaptain.blp`!), exact Footman parity
        ("hhes", NULL_ID, [
            ("unam", VT_STR, "High Elven Swordsman"),
            ("urac", VT_STR, "human"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNFootman.blp"),
            ("ugol", VT_INT, 135),
            ("ulum", VT_INT, 0),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 20),
            ("uhpm", VT_INT, 420),
            ("uhpr", VT_UNREAL, 0.25),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 2),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 270),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "normal"),
            ("ua1b", VT_INT, 11),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 2),
            ("ua1c", VT_UNREAL, 1.35),
            ("uabi", VT_STR, "Adef,Aihn"),
            ("upgr", VT_STR, "Rhme,Rhar,Rhde,Rhpm"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Train High Elven |cffffcc00S|rwordsman"),
            ("utub", VT_STR, "Versatile Silvermoon foot soldier. Can learn the Defend ability to reflect Piercing attacks. Attacks land units."),
        ]),

        # Tier 1 Ranged: High Elven Archer (`nhea`) — Trained at Silvermoon Barracks (`h007`) (1,0)
        # Balanced 2-food ranged ranger: 135g/15L, 20s, 320 HP, +0.25 HP/s always, 11.3 Pierce DPS
        ("nhea", NULL_ID, [
            ("unam", VT_STR, "High Elven Archer"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, ""),
            ("ugol", VT_INT, 135),
            ("ulum", VT_INT, 15),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 20),
            ("uhpm", VT_INT, 320),
            ("uhpr", VT_UNREAL, 0.25),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 0),
            ("udty", VT_STR, "medium"),
            ("umvs", VT_INT, 270),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "pierce"),
            ("ua1b", VT_INT, 15),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 3),
            ("ua1c", VT_UNREAL, 1.50),
            ("ua1r", VT_INT, 500),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "Aihn"),
            ("upgr", VT_STR, "Rhra,Rhla,Rhpm"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Train High Elven |cffffcc00A|rrcher"),
            ("utub", VT_STR, "Nimble Silvermoon longbow ranger. Excels at focus-firing air units and enemy spellcasters. Benefits from Ranged Weapons and Leather Armor upgrades."),
        ]),

        # Tier 3 Heavy Plate Officer: Alliance Captain (`hcth`) — Trained at Silvermoon Barracks (`h007`) (2,0)
        # Exact Human Knight Tier-3 parity (`h003,hbla,hlum`): 4 Food, 245g/60L, 38s, 840 HP (+150 w/ Rhan = 990 HP!),
        # 5 Large armor, 29+2d3=33.0 Normal / 1.45s = 22.8 DPS + Defend!
        ("hcth", NULL_ID, [
            ("unam", VT_STR, "Alliance Captain"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, "h003,hbla,hlum"),
            ("ugol", VT_INT, 245),
            ("ulum", VT_INT, 60),
            ("ufoo", VT_INT, 4),
            ("ubld", VT_INT, 38),
            ("uhpm", VT_INT, 840),
            ("uhpr", VT_UNREAL, 0.25),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 290),
            ("usca", VT_REAL, 1.12),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "normal"),
            ("ua1b", VT_INT, 29),
            ("ua1d", VT_INT, 2),
            ("ua1s", VT_INT, 3),
            ("ua1c", VT_UNREAL, 1.45),
            ("uabi", VT_STR, "Adef,Aihn"),
            ("upgr", VT_STR, "Rhme,Rhar,Rhde,Rhan,Rhpm"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Train Alliance |cffffcc00C|raptain"),
            ("utub", VT_STR, "Elite Tier-3 heavy plate officer. Commands the frontline with high armor, Defend, and Veteran War Training (+150 HP). Attacks land units."),
        ]),

        # Tier 2 Healer: Silvermoon Chaplain (`nchp`) — Trained at High Elven Mage Tower (`nheb`) (0,0)
        # Distinct `BTNPriest.blp` icon + exact Priest melee stats (135g/10L, 290 HP, 200 MP, Heal/Dispel/Inner Fire gated by `Rhpt`!)
        ("nchp", NULL_ID, [
            ("unam", VT_STR, "Silvermoon Chaplain"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, "h002"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNPriest.blp"),
            ("ugol", VT_INT, 135),
            ("ulum", VT_INT, 10),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 28),
            ("uhpm", VT_INT, 290),
            ("uhpr", VT_UNREAL, 0.25),
            ("uhrt", VT_STR, "always"),
            ("umpm", VT_INT, 200),
            ("umpi", VT_INT, 75),
            ("umpr", VT_UNREAL, 0.67),
            ("udef", VT_INT, 0),
            ("udty", VT_STR, "none"),
            ("umvs", VT_INT, 270),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "magic"),
            ("ua1b", VT_INT, 7),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 2),
            ("ua1c", VT_UNREAL, 2.00),
            ("ua1r", VT_INT, 600),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "Ahea,Adis,Ainf,Aihn"),
            ("udaa", VT_STR, "Ahea"),
            ("upgr", VT_STR, "Rhpt,Rhpm"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Train Silvermoon |cffffcc00C|rhaplain"),
            ("utub", VT_STR, "Supporting cleric. Initially casts Heal; can learn Dispel Magic (Adept) and Inner Fire (Master). Attacks land and air units."),
        ]),

        # Tier 2 Arcane Caster: Dalaran Hydromancer (`nhym`) — Trained at High Elven Mage Tower (`nheb`) (1,0)
        # Distinct `BTNSorceress.blp` icon + exact Sorceress melee stats (155g/20L, 325 HP, 200 MP, Slow/Invisibility/Polymorph gated by `Rhst`!)
        ("nhym", NULL_ID, [
            ("unam", VT_STR, "Dalaran Hydromancer"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, "h002"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNSorceress.blp"),
            ("ugol", VT_INT, 155),
            ("ulum", VT_INT, 20),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 30),
            ("uhpm", VT_INT, 325),
            ("uhpr", VT_UNREAL, 0.25),
            ("uhrt", VT_STR, "always"),
            ("umpm", VT_INT, 200),
            ("umpi", VT_INT, 75),
            ("umpr", VT_UNREAL, 0.67),
            ("udef", VT_INT, 0),
            ("udty", VT_STR, "none"),
            ("umvs", VT_INT, 270),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "magic"),
            ("ua1b", VT_INT, 9),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 3),
            ("ua1c", VT_UNREAL, 1.75),
            ("ua1r", VT_INT, 600),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "Aslo,Aivs,Aply,Aihn"),
            ("udaa", VT_STR, "Aslo"),
            ("upgr", VT_STR, "Rhst,Rhpm"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "H"),
            ("utip", VT_STR, "Train Dalaran |cffffcc00H|rydromancer"),
            ("utub", VT_STR, "Arcane Kirin Tor battle-mage. Initially casts Slow; can learn Invisibility (Adept) and Polymorph (Master). Attacks land and air units."),
        ]),

        # Tier 3 Runeblade Champion: Blood Elf Lieutenant (`nbel`) — Trained at Siege Workshop (`h008`) (2,0)
        # FIXED campaign Spell Immunity (`Amim`) + 950 HP -> Resistant Skin (`ACsk`) + Feedback (`Afbk`) + Magic Sentry (`Adts`),
        # 4 Food, 260g/60L, 38s, 780 HP, 4 Large armor, 24+1d6=27.5 Normal / 1.65s = 16.7 DPS (180 rng)
        ("nbel", NULL_ID, [
            ("unam", VT_STR, "Blood Elf Lieutenant"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, "h003,h005"),
            ("ugol", VT_INT, 260),
            ("ulum", VT_INT, 60),
            ("ufoo", VT_INT, 4),
            ("ubld", VT_INT, 38),
            ("uhpm", VT_INT, 780),
            ("uhpr", VT_UNREAL, 0.50),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 4),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 290),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "normal"),
            ("ua1b", VT_INT, 24),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 6),
            ("ua1c", VT_UNREAL, 1.65),
            ("ua1r", VT_INT, 180),
            ("uabi", VT_STR, "ACsk,Afbk,Adts,Aihn"),
            ("upgr", VT_STR, "Rhme,Rhar,Rhpm"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "L"),
            ("utip", VT_STR, "Train Blood Elf |cffffcc00L|rieutenant"),
            ("utub", VT_STR, "Elite Tier-3 runeblade officer with Resistant Skin, Arcane Feedback (burns enemy mana on hit), and Magic Sentry. Attacks land units."),
        ]),

        # ---- Campaign Human 4 Summonable Heroes (`Hkal`, `Hvwd`, `Hlgr`, `Huth`) ----
        # Hero 1: Prince Kael'thas (`Hkal`, INT — Flame Strike, Banish, Siphon Mana, Phoenix)
        ("Hkal", NULL_ID, [
            ("unam", VT_STR, "Prince Kael'thas"),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 100),
            ("ustr", VT_INT, 18),
            ("uagi", VT_INT, 14),
            ("uint", VT_INT, 19),
            ("ustp", VT_UNREAL, 2.00),
            ("uagp", VT_UNREAL, 1.00),
            ("uinp", VT_UNREAL, 3.00),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "h002"),
            ("urq2", VT_STR, "h003"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "K"),
            ("utip", VT_STR, "Summon Prince |cffffcc00K|rael'thas"),
            ("utpr", VT_STR, "Revive Prince |cffffcc00K|rael'thas"),
            ("utub", VT_STR, "Royal Sunwell Archmage of Quel'Thalas. Can learn Flame Strike, Banish, Siphon Mana, and Phoenix."),
        ]),

        # Hero 2: Sylvanas Windrunner (`Hvwd`, AGI — Searing Arrows, Trueshot Aura, Scout Owl, Starfall)
        ("Hvwd", NULL_ID, [
            ("unam", VT_STR, "Sylvanas Windrunner"),
            ("urac", VT_STR, "human"),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 100),
            ("ustr", VT_INT, 17),
            ("uagi", VT_INT, 21),
            ("uint", VT_INT, 16),
            ("ustp", VT_UNREAL, 1.85),
            ("uagp", VT_UNREAL, 2.40),
            ("uinp", VT_UNREAL, 1.95),
            ("umvs", VT_INT, 310),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "h002"),
            ("urq2", VT_STR, "h003"),
            ("uhab", VT_STR, "AHfa,AEar,AEst,AEsf"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Summon |cffffcc00S|rylvanas Windrunner"),
            ("utpr", VT_STR, "Revive |cffffcc00S|rylvanas Windrunner"),
            ("utub", VT_STR, "Ranger-General of Silvermoon. Master marksman who can learn Searing Arrows, Trueshot Aura, Scout, and Starfall."),
        ]),

        # Hero 3: Lord Garithos (`Hlgr`, STR — Shockwave, Holy Light, Devotion Aura, Avatar)
        ("Hlgr", NULL_ID, [
            ("unam", VT_STR, "Lord Garithos"),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 100),
            ("ustr", VT_INT, 24),
            ("uagi", VT_INT, 13),
            ("uint", VT_INT, 16),
            ("ustp", VT_UNREAL, 2.80),
            ("uagp", VT_UNREAL, 1.30),
            ("uinp", VT_UNREAL, 1.80),
            ("umvs", VT_INT, 290),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "h002"),
            ("urq2", VT_STR, "h003"),
            ("uhab", VT_STR, "AOsh,AHhb,AHad,AHav"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Summon Lord |cffffcc00G|rarithos"),
            ("utpr", VT_STR, "Revive Lord |cffffcc00G|rarithos"),
            ("utub", VT_STR, "Grand Marshal of the New Alliance. Armored cavalry commander who can learn Shockwave, Holy Light, Devotion Aura, and Avatar."),
        ]),

        # Hero 4: Uther the Lightbringer (`Huth`, STR — Holy Light, Divine Shield, Devotion Aura, Resurrection)
        ("Huth", NULL_ID, [
            ("unam", VT_STR, "Uther the Lightbringer"),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 100),
            ("ustr", VT_INT, 22),
            ("uagi", VT_INT, 13),
            ("uint", VT_INT, 17),
            ("ustp", VT_UNREAL, 2.70),
            ("uagp", VT_UNREAL, 1.50),
            ("uinp", VT_UNREAL, 1.80),
            ("umvs", VT_INT, 290),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "h002"),
            ("urq2", VT_STR, "h003"),
            ("uhab", VT_STR, "AHhb,AHds,AHad,AHre"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 3),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "Summon |cffffcc00U|rther the Lightbringer"),
            ("utpr", VT_STR, "Revive |cffffcc00U|rther the Lightbringer"),
            ("utub", VT_STR, "Supreme Paladin of the Silver Hand. Can learn Holy Light, Divine Shield, Devotion Aura, and Resurrection."),
        ]),
    ]

    # ==========================================================================
    # CUSTOM UNITS, HEROES & BUILDINGS (`N001..N003`, `n001..n005`, `h001..h009`)
    # ==========================================================================
    custom: List[Tuple[str, str, List[ModEntry]]] = [
        # ---- NAGA CUSTOM HEROES (`N001..N003`) — Distinct Models & Icons! ----
        # N001: Abyssal Warlord (STR Frontline Hero — Royal Guard model + `BTNNagaMyrmidonRoyalGuard.blp`!)
        ("Otch", "N001", [
            ("unam", VT_STR, "Abyssal Warlord"),
            ("uhot", VT_STR, "W"),
            ("urac", VT_STR, "naga"),
            ("upra", VT_STR, "STR"),
            ("ustr", VT_INT, 24),
            ("uagi", VT_INT, 14),
            ("uint", VT_INT, 15),
            ("ustp", VT_UNREAL, 2.90),
            ("uagp", VT_UNREAL, 1.50),
            ("uinp", VT_UNREAL, 1.60),
            ("umdl", VT_STR, r"units\naga\NagaRoyalGuard\NagaRoyalGuard.mdl"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNNagaMyrmidonRoyalGuard.blp"),
            ("usnd", VT_STR, "NagaRoyalGuard"),
            ("usca", VT_REAL, 1.15),
            ("umvt", VT_STR, "amph"),
            ("umvs", VT_INT, 290),
            ("uhpm", VT_INT, 100),
            ("uhpr", VT_UNREAL, 0.25),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 2),
            ("ua1b", VT_INT, 0),
            ("ua1d", VT_INT, 2),
            ("ua1s", VT_INT, 5),
            ("ua1c", VT_UNREAL, 1.90),
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "n001"),
            ("urq2", VT_STR, "n002"),
            ("uhab", VT_STR, "AOsh,ANca,ANht,ANst"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("utip", VT_STR, "Summon Abyssal |cffffcc00W|rarlord"),
            ("utpr", VT_STR, "Revive Abyssal |cffffcc00W|rarlord"),
            ("utub", VT_STR, "Colossal Naga frontline commander. Can learn Shockwave, Cleaving Attack, Howl of Terror, and Stampede."),
        ]),

        # N002: Azshara's Tideweaver (INT Arch-Siren — Distinct `NagaSummoner.mdl` + `BTNNagaSummoner.blp`!)
        ("Hamg", "N002", [
            ("unam", VT_STR, "Azshara's Tideweaver"),
            ("uhot", VT_STR, "T"),
            ("urac", VT_STR, "naga"),
            ("upra", VT_STR, "INT"),
            ("ustr", VT_INT, 15),
            ("uagi", VT_INT, 16),
            ("uint", VT_INT, 22),
            ("ustp", VT_UNREAL, 1.80),
            ("uagp", VT_UNREAL, 1.30),
            ("uinp", VT_UNREAL, 3.00),
            ("umdl", VT_STR, r"Units\Naga\NagaSummoner\NagaSummoner.mdl"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNNagaSummoner.blp"),
            ("usnd", VT_STR, "NagaSiren"),
            ("usca", VT_REAL, 1.15),
            ("umvt", VT_STR, "amph"),
            ("umvs", VT_INT, 290),
            ("uhpm", VT_INT, 100),
            ("uhpr", VT_UNREAL, 0.25),
            ("uhrt", VT_STR, "always"),
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "n001"),
            ("urq2", VT_STR, "n002"),
            ("uhab", VT_STR, "AHwe,AHbz,AHab,AHmt"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("utip", VT_STR, "Summon Azshara's |cffffcc00T|rideweaver"),
            ("utpr", VT_STR, "Revive Azshara's |cffffcc00T|rideweaver"),
            ("utub", VT_STR, "Highborne Arch-Summoner of Nazjatar. Can learn Summon Water Elemental, Blizzard, Brilliance Aura, and Mass Teleport."),
        ]),

        # N003: Makrura Deepking (STR Armored Tank — `Lobstrokkred.mdl`, `uhpr` FIXED to `VT_UNREAL`!)
        ("Ucrl", "N003", [
            ("unam", VT_STR, "Makrura Deepking"),
            ("uhot", VT_STR, "D"),
            ("urac", VT_STR, "naga"),
            ("upra", VT_STR, "STR"),
            ("ustr", VT_INT, 25),
            ("uagi", VT_INT, 13),
            ("uint", VT_INT, 15),
            ("ustp", VT_UNREAL, 3.10),
            ("uagp", VT_UNREAL, 1.20),
            ("uinp", VT_UNREAL, 1.70),
            ("umdl", VT_STR, r"units\creeps\Lobstrokkred\Lobstrokkred.mdl"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNLobstrokkRed.blp"),
            ("usnd", VT_STR, "Lobstrokk"),
            ("usca", VT_REAL, 1.25),
            ("umvt", VT_STR, "amph"),
            ("umvs", VT_INT, 290),
            ("uhpm", VT_INT, 100),
            ("uhpr", VT_UNREAL, 0.25),
            ("uhrt", VT_STR, "always"),
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "n001"),
            ("urq2", VT_STR, "n002"),
            ("uhab", VT_STR, "AUim,AUts,AHbh,AUls"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 3),
            ("ubpy", VT_INT, 0),
            ("utip", VT_STR, "Summon Makrura |cffffcc00D|reepking"),
            ("utpr", VT_STR, "Revive Makrura |cffffcc00D|reepking"),
            ("utub", VT_STR, "Ancient armored crustacean monarch allied with the Naga. Can learn Impale, Spiked Carapace, Bash, and Locust Swarm."),
        ]),

        # ---- NAGA CUSTOM STRUCTURES (`n001..n005`) ----
        # n001: Sanctuary of Tides (Tier 2 Naga Town Hall — trains ONLY `nmpe`!)
        ("nntt", "n001", [
            ("unam", VT_STR, "Sanctuary of Tides"),
            ("upap", VT_STR, "unbuildable"),
            ("usca", VT_REAL, 1.15),
            ("uclr", VT_INT, 185),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 320),
            ("ulum", VT_INT, 190),
            ("ubld", VT_INT, 120),
            ("ufma", VT_INT, 11),
            ("uhpm", VT_INT, 1950),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "nmpe"),
            ("ures", VT_STR, ""),
            ("uupt", VT_STR, "n002"),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Sanctuary of Tides"),
            ("utub", VT_STR, "Upgrade to Sanctuary of Tides (Tier 2) to unlock Naga Myrmidons, Shrine of Azshara, Abyssal Behemoth Pool, a 2nd Naga Hero, and Tier-2 Coral upgrades."),
        ]),

        # n002: Abyssal Citadel (Tier 3 Naga Town Hall — trains ONLY `nmpe`!)
        ("nntt", "n002", [
            ("unam", VT_STR, "Abyssal Citadel"),
            ("upap", VT_STR, "unbuildable"),
            ("usca", VT_REAL, 1.28),
            ("uclr", VT_INT, 145),
            ("uclg", VT_INT, 210),
            ("uclb", VT_INT, 255),
            ("ureq", VT_STR, "nnad"),
            ("ugol", VT_INT, 360),
            ("ulum", VT_INT, 210),
            ("ubld", VT_INT, 120),
            ("ufma", VT_INT, 11),
            ("uhpm", VT_INT, 2350),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "nmpe"),
            ("ures", VT_STR, ""),
            ("uupt", VT_STR, ""),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Abyssal Citadel"),
            ("utub", VT_STR, "Upgrade to Abyssal Citadel (Tier 3) to unlock Naga Royal Guards, Master Sirens, Orb of the Abyss, a 3rd Naga Hero, and Tier-3 Razorspine upgrades."),
        ]),

        # n003: Tidal Treasury (Naga Racial Item Shop)
        ("hvlt", "n003", [
            ("unam", VT_STR, "Tidal Treasury"),
            ("urac", VT_STR, "naga"),
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "nnad"),
            ("umdl", VT_STR, r"buildings\other\MagicVault\MagicVault.mdl"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNArcaneVault.blp"),
            ("usca", VT_REAL, 0.90),
            ("uclr", VT_INT, 130),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 130),
            ("ulum", VT_INT, 30),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 550),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("uabi", VT_STR, "Abds,Aall,Apit"),
            ("umki", VT_STR, "sreg,plcl,i003,phea,pman,stwp,i001,i002"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Build Tidal T|cffffcc00r|reasury"),
            ("utub", VT_STR, "Creates an abyssal shop stocked with Scroll of Regeneration, Lesser Clarity, Scroll of Tidal Surge, Potions, Town Portal, Staff of Sanctuary, and Orb of the Abyss."),
        ]),

        # n004: Coral Forge (Dedicated Naga Armory/Blacksmith — `FountainOfPower.mdl`!)
        # Houses `Rnat` (Coral/Chitinous/Razorspine Blades) & `Rnam` (Scales), and unlocks Snap Dragons & Tidal Guardians!
        ("hbla", "n004", [
            ("unam", VT_STR, "Coral Forge"),
            ("urac", VT_STR, "naga"),
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "nntt"),
            ("umdl", VT_STR, r"buildings\other\FountainOfPower\FountainOfPower.mdl"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNNagaWeaponUp1.blp"),
            ("usca", VT_REAL, 0.85),
            ("uclr", VT_INT, 150),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 140),
            ("ulum", VT_INT, 60),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 1100),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("uabi", VT_STR, "Abds"),
            ("utra", VT_STR, ""),
            ("ures", VT_STR, "Rnat,Rnam"),
            ("upgr", VT_STR, ""),
            ("ubpx", VT_INT, 3),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "F"),
            ("utip", VT_STR, "Build Coral |cffffcc00F|rorge"),
            ("utub", VT_STR, "Abyssal armory where Coral, Chitinous, and Razorspine Blades and Scales are forged. Also required for Snap Dragons and Tidal Guardians."),
        ]),

        # n005: Abyssal Behemoth Pool (Dedicated Naga Siege & T3 Elite Sanctum — `DragonBuildingBlue.mdl`!)
        # Houses `nhyc` Dragon Turtle (T2 Siege) and `nnrg` Naga Royal Guard (T3 Elite)!
        ("nnsg", "n005", [
            ("unam", VT_STR, "Abyssal Behemoth Pool"),
            ("urac", VT_STR, "naga"),
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "n001,n004"),
            ("umdl", VT_STR, r"buildings\other\DragonBuildingBlue\DragonBuildingBlue.mdl"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNDragonRoost.blp"),
            ("usca", VT_REAL, 0.90),
            ("uclr", VT_INT, 155),
            ("uclg", VT_INT, 225),
            ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 160),
            ("ulum", VT_INT, 150),
            ("ubld", VT_INT, 65),
            ("uhpm", VT_INT, 1150),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "nhyc,nnrg"),
            ("ures", VT_STR, ""),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Build Abyssal |cffffcc00B|rehemoth Pool"),
            ("utub", VT_STR, "Deep-sea spawning sanctum for heavy war beasts and royal champions. Trains Dragon Turtles (Tier 2 Siege) and Naga Royal Guards (Tier 3 Elite)."),
        ]),

        # ---- CAMPAIGN HUMAN CUSTOM STRUCTURES & UNITS (`h001..h009`) ----
        # NOTE: `h001..h003` explicitly strip `Amic` (Call to Arms) so Silvermoon Workers
        # never exhibit Militia bell issues while preserving 100% Town Hall drop-off & Backpack!
        ("htow", "h001", [
            ("unam", VT_STR, "Silvermoon Town Hall"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 240),
            ("uclb", VT_INT, 200),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("utra", VT_STR, "nhew"),
            ("ures", VT_STR, "Rhpm"),
            ("uupt", VT_STR, "h002"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "H"),
            ("utip", VT_STR, "Build Silvermoon Town |cffffcc00H|rall"),
            ("utub", VT_STR, "Primary Campaign Human center. Trains Silvermoon Workers, researches Backpack, and receives gathered Gold and Lumber. Upgrades to Sunwell Keep."),
        ]),

        ("hkee", "h002", [
            ("unam", VT_STR, "Sunwell Keep"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 190),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("utra", VT_STR, "nhew"),
            ("ures", VT_STR, "Rhpm"),
            ("uupt", VT_STR, "h003"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Sunwell Keep"),
            ("utub", VT_STR, "Upgrade to Sunwell Keep (Tier 2) to unlock the High Elven Mage Tower, Siege Workshop, Dragonhawk Aviary, a 2nd Expedition Hero, and Tier-2 upgrades."),
        ]),

        ("hcas", "h003", [
            ("unam", VT_STR, "Silvermoon Citadel"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 225),
            ("uclb", VT_INT, 175),
            ("ureq", VT_STR, "h004"),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("utra", VT_STR, "nhew"),
            ("ures", VT_STR, "Rhpm"),
            ("uupt", VT_STR, ""),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Silvermoon Citadel"),
            ("utub", VT_STR, "Upgrade to Silvermoon Citadel (Tier 3) to unlock Alliance Captains, Blood Elf Lieutenants, Gryphon Riders, Orb of Fire, a 3rd Hero, and Tier-3 upgrades."),
        ]),

        ("halt", "h004", [
            ("unam", VT_STR, "Altar of Silvermoon"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 185),
            ("utra", VT_STR, "Hkal,Hvwd,Hlgr,Huth"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Build |cffffcc00A|rltar of Silvermoon"),
            ("utub", VT_STR, "Summons Campaign Human Heroes (Prince Kael'thas, Sylvanas Windrunner, Lord Garithos, and Uther the Lightbringer) and revives fallen Heroes."),
        ]),

        ("hvlt", "h005", [
            ("unam", VT_STR, "Sunwell Reliquary"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 230),
            ("uclb", VT_INT, 180),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Build Sunwell |cffffcc00R|reliquary"),
            ("utub", VT_STR, "Creates an Expedition shop stocked with Scrolls, Potions, Town Portals, Scout Towers, Staff of Sanctuary, and Orb of Fire."),
        ]),

        # h006: Silvermoon Ballista (Tier-2 Siege Engine — Trained at Siege Workshop `h008`!)
        # Exact Mortar Team / Glaive Thrower parity: 3 Food, 195g/65L, 36s, 340 HP, 2 Large armor,
        # 49+1d9=54.0 Siege dmg / 3.5s = 15.4 Siege DPS at 1150 range!
        ("ebal", "h006", [
            ("unam", VT_STR, "Silvermoon Ballista"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, "h002,hbla"),
            ("ugol", VT_INT, 195),
            ("ulum", VT_INT, 65),
            ("ufoo", VT_INT, 3),
            ("ubld", VT_INT, 36),
            ("uhpm", VT_INT, 340),
            ("udef", VT_INT, 2),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 220),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "siege"),
            ("ua1b", VT_INT, 49),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 9),
            ("ua1c", VT_UNREAL, 3.50),
            ("ua1r", VT_INT, 1150),
            ("uabi", VT_STR, ""),
            ("upgr", VT_STR, "Rhra,Rhar"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Train Silvermoon |cffffcc00B|rallista"),
            ("utub", VT_STR, "Long-range High Elven mechanical siege engine. Hurls giant runed bolts to demolish enemy towers and fortifications from afar."),
        ]),

        # h007: Silvermoon Barracks (Authentic Barracks `HumanBarracks.mdl` for Infantry & Archers!)
        ("hbar", "h007", [
            ("unam", VT_STR, "Silvermoon Barracks"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 195),
            ("ugol", VT_INT, 160),
            ("ulum", VT_INT, 60),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1300),
            ("utra", VT_STR, "hhes,nhea,hcth"),
            ("ures", VT_STR, "Rhde,Rhan"),
            ("upgr", VT_STR, "Rhac"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Build Silvermoon |cffffcc00B|rarracks"),
            ("utub", VT_STR, "Primary troop production building. Trains High Elven Swordsmen, High Elven Archers, and Alliance Captains (Tier 3). Also researches Defend and Veteran War Training."),
        ]),

        # h008: Silvermoon Siege Workshop (Authentic `Workshop.mdl` for Siege, Scout Air & T3 Lieutenant!)
        ("harm", "h008", [
            ("unam", VT_STR, "Silvermoon Siege Workshop"),
            ("ureq", VT_STR, "h002,hbla"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 195),
            ("ugol", VT_INT, 140),
            ("ulum", VT_INT, 140),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1200),
            ("utra", VT_STR, "hgyr,h006,nbel"),
            ("ures", VT_STR, "Rhgb"),
            ("upgr", VT_STR, "Rhac"),
            ("ubpx", VT_INT, 3),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "W"),
            ("utip", VT_STR, "Build Silvermoon Siege |cffffcc00W|rorkshop"),
            ("utub", VT_STR, "Heavy war-machine and armory workshop. Produces Flying Machines, Silvermoon Ballistas, and Blood Elf Lieutenants (Tier 3). Also researches Flying Machine Bombs."),
        ]),

        # h009: Silvermoon Dragonhawk Aviary (Authentic `GryphonAviary.mdl` for Flying Units ONLY!)
        ("hgra", "h009", [
            ("unam", VT_STR, "Silvermoon Dragonhawk Aviary"),
            ("ureq", VT_STR, "h002,hlum"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 238),
            ("uclb", VT_INT, 195),
            ("ugol", VT_INT, 140),
            ("ulum", VT_INT, 150),
            ("ubld", VT_INT, 65),
            ("uhpm", VT_INT, 1200),
            ("utra", VT_STR, "hdhw,hgry"),
            ("ures", VT_STR, "Rhcd,Rhhb"),
            ("upgr", VT_STR, "Rhac"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "V"),
            ("utip", VT_STR, "Build Silvermoon Dragonhawk A|cffffcc00v|riary"),
            ("utub", VT_STR, "Aerial roost for Dragonhawk Riders (Tier 2) and Wildhammer Gryphon Riders (Tier 3). Also researches Cloud and Storm Hammers."),
        ]),
    ]

    return original, custom


def serialize_w3u() -> bytes:
    """Serialize `war3map.w3u` in cross-patch binary v2 format."""
    orig, cust = build_unit_modifications()
    return (
        struct.pack("<i", 2)
        + _pack_mod_table(orig, use_optional_ints=False)
        + _pack_mod_table(cust, use_optional_ints=False)
    )


# ==============================================================================
# 2. ITEM OBJECT MODIFICATIONS (`war3map.w3t` v2)
# ==============================================================================

def serialize_w3t() -> bytes:
    """
    Serialize `war3map.w3t` (v2) with Naga Tidal Treasury items:
      - `i001`: Orb of the Abyss (Tier 3 `n002` Orb of Frost shop version, 375g)
      - `i002`: Tidal Staff of Sanctuary (Tier 3 `n002` Staff of Sanctuary, 250g)
      - `i003`: Scroll of Tidal Surge (Tier 1 Scroll of Speed, 50g)
    """
    cust: List[Tuple[str, str, List[ModEntry]]] = [
        ("ofro", "i001", [
            ("unam", VT_STR, "Orb of the Abyss"),
            ("utip", VT_STR, "Purchase |cffffcc00O|rrb of the Abyss"),
            ("utub", VT_STR, "Adds 6 bonus frost damage to a Hero's attacks, enables ranged air attacks, and slows enemy movement and attack speed for 3 seconds."),
            ("uhot", VT_STR, "O"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("ureq", VT_STR, "n002"),
            ("igol", VT_INT, 375),
            ("isel", VT_INT, 1),
            ("ipaw", VT_INT, 1),
            ("isto", VT_INT, 1),
            ("istr", VT_INT, 120),
            ("isst", VT_INT, 0),
            ("iprn", VT_INT, 0),
        ]),
        ("ssan", "i002", [
            ("unam", VT_STR, "Tidal Staff of Sanctuary"),
            ("utip", VT_STR, "Purchase Tidal |cffffcc00S|rtaff of Sanctuary"),
            ("uhot", VT_STR, "S"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 2),
            ("ureq", VT_STR, "n002"),
            ("igol", VT_INT, 250),
            ("isel", VT_INT, 1),
            ("ipaw", VT_INT, 1),
            ("isto", VT_INT, 1),
            ("istr", VT_INT, 120),
            ("isst", VT_INT, 0),
            ("iprn", VT_INT, 0),
        ]),
        ("shas", "i003", [
            ("unam", VT_STR, "Scroll of Tidal Surge"),
            ("utip", VT_STR, "Purchase Scroll of |cffffcc00T|ridal Surge"),
            ("uhot", VT_STR, "T"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("ureq", VT_STR, ""),
            ("igol", VT_INT, 50),
            ("isel", VT_INT, 1),
            ("ipaw", VT_INT, 1),
            ("isto", VT_INT, 2),
            ("istr", VT_INT, 90),
            ("isst", VT_INT, 0),
            ("iprn", VT_INT, 0),
        ]),
    ]
    return (
        struct.pack("<i", 2)
        + _pack_mod_table([], use_optional_ints=False)
        + _pack_mod_table(cust, use_optional_ints=False)
    )


# ==============================================================================
# 3. UPGRADE MODIFICATIONS (`war3map.w3q` v2)
# ==============================================================================

def serialize_w3q() -> bytes:
    """
    Serialize `war3map.w3q` (v2, `use_optional_ints = True`) to tier-gate and
    cost-balance Naga upgrades identically to standard ladder races:
      - `Rnat` (Blades): 125/200/275g, 75/175/275L; Lvl 2 -> `n001`, Lvl 3 -> `n002`
      - `Rnam` (Scales): 125/175/225g, 75/175/275L; Lvl 2 -> `n001`, Lvl 3 -> `n002`
      - `Rnen` (Ensnare): Lvl 1 -> `n001` (Tier 2 Myrmidon upgrade)
      - `Rnsb` (Submerge): 75g/75L/40s (matches Crypt Fiend Burrow!), Lvl 1 -> `n001`
      - `Rnsw` (Siren Training): Lvl 1 -> `n001`, Lvl 2 -> `n002`
      - `Rnsi` (Abolish Magic): Lvl 1 -> `n001`
    """
    NULL_ID = "\x00\x00\x00\x00"
    orig: List[Tuple[str, str, List[LevelModEntry]]] = [
        ("Rnat", NULL_ID, [
            ("gglb", VT_INT, 0, 0, 125),
            ("gglm", VT_INT, 0, 0, 75),
            ("glmb", VT_INT, 0, 0, 75),
            ("glmm", VT_INT, 0, 0, 100),
            ("greq", VT_STR, 2, 0, "n001"),
            ("greq", VT_STR, 3, 0, "n002"),
        ]),
        ("Rnam", NULL_ID, [
            ("gglb", VT_INT, 0, 0, 125),
            ("gglm", VT_INT, 0, 0, 50),
            ("glmb", VT_INT, 0, 0, 75),
            ("glmm", VT_INT, 0, 0, 100),
            ("greq", VT_STR, 2, 0, "n001"),
            ("greq", VT_STR, 3, 0, "n002"),
        ]),
        ("Rnen", NULL_ID, [
            ("greq", VT_STR, 1, 0, "n001"),
        ]),
        ("Rnsb", NULL_ID, [
            ("gglb", VT_INT, 0, 0, 75),
            ("glmb", VT_INT, 0, 0, 75),
            ("gtib", VT_INT, 0, 0, 40),
            ("gbpx", VT_INT, 0, 0, 1),
            ("gbpy", VT_INT, 0, 0, 2),
            ("greq", VT_STR, 1, 0, "n001"),
        ]),
        ("Rnsw", NULL_ID, [
            ("greq", VT_STR, 1, 0, "n001"),
            ("greq", VT_STR, 2, 0, "n002"),
        ]),
        ("Rnsi", NULL_ID, [
            ("greq", VT_STR, 1, 0, "n001"),
        ]),
    ]
    return (
        struct.pack("<i", 2)
        + _pack_mod_table(orig, use_optional_ints=True)
        + _pack_mod_table([], use_optional_ints=True)
    )


# ==============================================================================
# 4. GAMEPLAY CONSTANTS (`war3mapMisc.txt`) & IMPORT TABLE (`war3map.imp`)
# ==============================================================================

def serialize_war3map_misc() -> bytes:
    """
    Registers all Naga & Campaign Human Town Halls, Altars, and Heroes in
    Warcraft III's native Gameplay Constants (`[TWN1..3]`, `[TALT]`, `[HERO]`).
    """
    lines = [
        "[HERO]",
        "DependencyOr=Hamg,Hmkg,Hpal,Hblm,Obla,Ofar,Otch,Oshd,Udea,Udre,Ulic,Ucrl,Edem,Ekee,Emoo,Ewar,Nbrn,Nbst,Nngs,Npbm,Nalc,Ntin,Nfir,Nplh,Hvsh,N001,N002,N003,Hkal,Hvwd,Hlgr,Huth",
        "",
        "[TALT]",
        "DependencyOr=halt,oalt,uaod,eate,nnad,h004",
        "",
        "[TWN1]",
        "DependencyOr=htow,ogre,unpl,etol,nntt,h001",
        "",
        "[TWN2]",
        "DependencyOr=hkee,ostr,unp1,etoa,n001,h002",
        "",
        "[TWN3]",
        "DependencyOr=hcas,ofrt,unp2,etoe,n002,h003",
        "",
    ]
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def serialize_imp() -> bytes:
    """
    Serialize `war3map.imp` (v1) listing `naga_melee.ai` and `camphuman_melee.ai`
    with custom full-path flag (`0x0D`) so World Editor keeps both `.ai` scripts intact.
    """
    entries = ["naga_melee.ai", "camphuman_melee.ai"]
    buf = bytearray(struct.pack("<II", 1, len(entries)))
    for path in entries:
        buf += struct.pack("<B", 13) + path.encode("utf-8") + b"\x00"
    return bytes(buf)


# ==============================================================================
# 5. PRO-LEVEL CUSTOM MELEE `.ai` SCRIPTS (`naga_melee.ai` & `camphuman_melee.ai`)
# ==============================================================================

def generate_naga_ai_script() -> str:
    """
    Full competitive Warcraft III `common.ai` Melee AI script for the Naga Empire,
    updated for the proper v2 9-building techtree (`nnsg`, `n004`, `nnsa`, `n005`).
    """
    return """//============================================================================
//  Naga Empire Pro Melee AI (`naga_melee.ai`) — (8) Crown of WarMahdi
//  Compatible with Warcraft III TFT 1.26a/1.27b & Reforged
//============================================================================
globals
    boolean naga_tier2_done = false
    boolean naga_tier3_done = false

    constant integer NAGA_SLAVE        = 'nmpe'
    constant integer NAGA_HALL_T1      = 'nntt'
    constant integer NAGA_HALL_T2      = 'n001'
    constant integer NAGA_HALL_T3      = 'n002'
    constant integer NAGA_CORAL_BED    = 'nnfm'
    constant integer NAGA_SPAWNING     = 'nnsg'
    constant integer NAGA_FORGE        = 'n004'
    constant integer NAGA_ALTAR        = 'nnad'
    constant integer NAGA_TREASURY     = 'n003'
    constant integer NAGA_GUARDIAN     = 'nntg'
    constant integer NAGA_SHRINE       = 'nnsa'
    constant integer NAGA_BEHEMOTH     = 'n005'

    constant integer NAGA_REAVER       = 'nnmg'
    constant integer NAGA_SNAP_DRAGON  = 'nsnp'
    constant integer NAGA_MYRMIDON     = 'nmyr'
    constant integer NAGA_SIREN        = 'nnsw'
    constant integer NAGA_COUATL       = 'nwgs'
    constant integer NAGA_TURTLE       = 'nhyc'
    constant integer NAGA_ROYAL_GUARD  = 'nnrg'

    constant integer HERO_VASHJ        = 'Hvsh'
    constant integer HERO_WARLORD      = 'N001'
    constant integer HERO_TIDEWEAVER   = 'N002'
    constant integer HERO_DEEPKING     = 'N003'

    constant integer UPG_NAGA_BLADES   = 'Rnat'
    constant integer UPG_NAGA_SCALES   = 'Rnam'
    constant integer UPG_NAGA_SUBMERGE = 'Rnsb'
    constant integer UPG_NAGA_ENSNARE  = 'Rnen'
    constant integer UPG_NAGA_SIREN    = 'Rnsw'
    constant integer UPG_NAGA_ABOLISH  = 'Rnsi'
endglobals

function NagaHallCount takes boolean doneOnly returns integer
    if doneOnly then
        return GetUnitCountDone(NAGA_HALL_T1) + GetUnitCountDone(NAGA_HALL_T2) + GetUnitCountDone(NAGA_HALL_T3)
    endif
    return GetUnitCount(NAGA_HALL_T1) + GetUnitCount(NAGA_HALL_T2) + GetUnitCount(NAGA_HALL_T3)
endfunction

function NagaTier2Count takes boolean doneOnly returns integer
    if doneOnly then
        return GetUnitCountDone(NAGA_HALL_T2) + GetUnitCountDone(NAGA_HALL_T3)
    endif
    return GetUnitCount(NAGA_HALL_T2) + GetUnitCount(NAGA_HALL_T3)
endfunction

function NagaTier3Count takes boolean doneOnly returns integer
    if doneOnly then
        return GetUnitCountDone(NAGA_HALL_T3)
    endif
    return GetUnitCount(NAGA_HALL_T3)
endfunction

function NagaNeedUnit takes integer qty, integer id, integer town returns nothing
    local integer have = GetUnitCount(id)
    if have < qty then
        call SetProduce(qty - have, id, town)
    endif
endfunction

function NagaSetSkills takes integer heroId, integer slot returns nothing
    if heroId == HERO_VASHJ then
        if slot == 1 then
            set skill[ 1] = 'ANfl'
            set skill[ 2] = 'ANfa'
            set skill[ 3] = 'ANfl'
            set skill[ 4] = 'ANms'
            set skill[ 5] = 'ANfl'
            set skill[ 6] = 'ANto'
            set skill[ 7] = 'ANfa'
            set skill[ 8] = 'ANfa'
            set skill[ 9] = 'ANms'
            set skill[10] = 'ANms'
        else
            set skill[ 1] = 'ANfa'
            set skill[ 2] = 'ANfl'
            set skill[ 3] = 'ANfl'
            set skill[ 4] = 'ANms'
            set skill[ 5] = 'ANfl'
            set skill[ 6] = 'ANto'
            set skill[ 7] = 'ANfa'
            set skill[ 8] = 'ANfa'
            set skill[ 9] = 'ANms'
            set skill[10] = 'ANms'
        endif
    elseif heroId == HERO_WARLORD then
        set skill[ 1] = 'AOsh'
        set skill[ 2] = 'ANca'
        set skill[ 3] = 'AOsh'
        set skill[ 4] = 'ANht'
        set skill[ 5] = 'AOsh'
        set skill[ 6] = 'ANst'
        set skill[ 7] = 'ANca'
        set skill[ 8] = 'ANca'
        set skill[ 9] = 'ANht'
        set skill[10] = 'ANht'
    elseif heroId == HERO_TIDEWEAVER then
        set skill[ 1] = 'AHwe'
        set skill[ 2] = 'AHab'
        set skill[ 3] = 'AHwe'
        set skill[ 4] = 'AHbz'
        set skill[ 5] = 'AHwe'
        set skill[ 6] = 'AHmt'
        set skill[ 7] = 'AHab'
        set skill[ 8] = 'AHab'
        set skill[ 9] = 'AHbz'
        set skill[10] = 'AHbz'
    else
        set skill[ 1] = 'AUim'
        set skill[ 2] = 'AUts'
        set skill[ 3] = 'AUim'
        set skill[ 4] = 'AHbh'
        set skill[ 5] = 'AUim'
        set skill[ 6] = 'AUls'
        set skill[ 7] = 'AUts'
        set skill[ 8] = 'AHbh'
        set skill[ 9] = 'AUts'
        set skill[10] = 'AHbh'
    endif
endfunction

function ChooseNagaHeroes takes nothing returns nothing
    local integer roll = GetRandomInt(1, 4)
    if roll == 1 then
        set hero_id  = HERO_VASHJ
        set hero_id2 = HERO_WARLORD
        set hero_id3 = HERO_TIDEWEAVER
    elseif roll == 2 then
        set hero_id  = HERO_WARLORD
        set hero_id2 = HERO_VASHJ
        set hero_id3 = HERO_DEEPKING
    elseif roll == 3 then
        set hero_id  = HERO_TIDEWEAVER
        set hero_id2 = HERO_DEEPKING
        set hero_id3 = HERO_VASHJ
    else
        set hero_id  = HERO_DEEPKING
        set hero_id2 = HERO_VASHJ
        set hero_id3 = HERO_WARLORD
    endif

    call NagaSetSkills(hero_id, 1)
    call SetSkillArray(1, hero_id)
    call NagaSetSkills(hero_id2, 2)
    call SetSkillArray(2, hero_id2)
    call NagaSetSkills(hero_id3, 3)
    call SetSkillArray(3, hero_id3)
endfunction

function NagaHarvestLoop takes nothing returns nothing
    local integer slaves
    local integer woodSlaves
    loop
        call ClearHarvestAI()

        if TownHasMine(0) and TownHasHall(0) then
            call HarvestGold(0, 5)
        endif
        if TownHasMine(1) and TownHasHall(1) then
            call HarvestGold(1, 5)
        endif
        if TownHasMine(2) and TownHasHall(2) then
            call HarvestGold(2, 5)
        endif

        set slaves = GetUnitCountDone(NAGA_SLAVE)
        if slaves > 6 then
            set woodSlaves = slaves - 5
            if woodSlaves > 9 then
                set woodSlaves = 9
            endif
            call HarvestWood(0, woodSlaves)
        else
            call HarvestWood(0, 2)
        endif

        call Sleep(6)
    endloop
endfunction

function NagaBuildLoop takes nothing returns nothing
    local unit expPeon
    local integer mines
    loop
        call InitBuildArray()

        set naga_tier2_done = (NagaTier2Count(true) >= 1)
        set naga_tier3_done = (NagaTier3Count(true) >= 1)
        set mines = GetMinesOwned()

        if NagaHallCount(false) < 1 then
            call SetProduce(1, NAGA_HALL_T1, -1)
        endif

        if FoodUsed() + 6 >= FoodCap() and FoodCap() < 100 and GetUnitCount(NAGA_CORAL_BED) < 11 then
            call NagaNeedUnit(GetUnitCountDone(NAGA_CORAL_BED) + 1, NAGA_CORAL_BED, -1)
        endif

        if mines >= 2 then
            call NagaNeedUnit(18, NAGA_SLAVE, -1)
        else
            call NagaNeedUnit(13, NAGA_SLAVE, -1)
        endif

        // Tier-1 Opening: Coral Bed -> Altar -> Spawning Grounds -> Coral Forge -> Hero 1 -> Treasury
        call NagaNeedUnit(1, NAGA_CORAL_BED, -1)
        call NagaNeedUnit(1, NAGA_ALTAR, -1)
        call NagaNeedUnit(1, NAGA_SPAWNING, -1)
        call NagaNeedUnit(2, NAGA_CORAL_BED, -1)

        if GetUnitCountDone(NAGA_ALTAR) >= 1 then
            call NagaNeedUnit(1, hero_id, -1)
            call NagaNeedUnit(1, NAGA_TREASURY, -1)
        endif

        if GetUnitCountDone(NAGA_SPAWNING) >= 1 then
            call NagaNeedUnit(4, NAGA_REAVER, -1)
            call NagaNeedUnit(1, NAGA_FORGE, -1)
        endif

        if GetUnitCountDone(NAGA_FORGE) >= 1 then
            call NagaNeedUnit(3, NAGA_SNAP_DRAGON, -1)
            call NagaNeedUnit(1, NAGA_GUARDIAN, 0)
            if GetGold() > 150 then
                if GetUpgradeLevel(UPG_NAGA_BLADES) < 1 then
                    call SetUpgrade(UPG_NAGA_BLADES)
                endif
                if GetUpgradeLevel(UPG_NAGA_SCALES) < 1 then
                    call SetUpgrade(UPG_NAGA_SCALES)
                endif
            endif
        endif

        // Tech to Tier 2: Sanctuary of Tides (`n001`)
        if GetUnitCountDone(NAGA_ALTAR) >= 1 and GetUnitCountDone(NAGA_SPAWNING) >= 1 and NagaTier2Count(false) < 1 then
            call SetProduce(1, NAGA_HALL_T2, -1)
        endif

        // Tier-2 Midgame: 2nd Hero, Myrmidons, Shrine of Azshara, Abyssal Behemoth Pool & Expansion
        if naga_tier2_done then
            call NagaNeedUnit(1, hero_id2, -1)
            call NagaNeedUnit(3, NAGA_MYRMIDON, -1)
            call NagaNeedUnit(4, NAGA_SNAP_DRAGON, -1)
            call NagaNeedUnit(1, NAGA_SHRINE, -1)
            call NagaNeedUnit(1, NAGA_BEHEMOTH, -1)
            call NagaNeedUnit(2, NAGA_GUARDIAN, 0)

            call SetUpgrade(UPG_NAGA_ENSNARE)
            call SetUpgrade(UPG_NAGA_SUBMERGE)

            if GetUnitCountDone(NAGA_SHRINE) >= 1 then
                call NagaNeedUnit(3, NAGA_SIREN, -1)
                call NagaNeedUnit(2, NAGA_COUATL, -1)
                if GetUpgradeLevel(UPG_NAGA_SIREN) < 1 then
                    call SetUpgrade(UPG_NAGA_SIREN)
                endif
                call SetUpgrade(UPG_NAGA_ABOLISH)
            endif

            if GetUnitCountDone(NAGA_BEHEMOTH) >= 1 then
                call NagaNeedUnit(2, NAGA_TURTLE, -1)
            endif

            if GetUnitCountDone(NAGA_FORGE) >= 1 then
                if GetUpgradeLevel(UPG_NAGA_BLADES) < 2 then
                    call SetUpgrade(UPG_NAGA_BLADES)
                endif
                if GetUpgradeLevel(UPG_NAGA_SCALES) < 2 then
                    call SetUpgrade(UPG_NAGA_SCALES)
                endif
            endif

            if GetGold() > 450 then
                call NagaNeedUnit(2, NAGA_SPAWNING, -1)
            endif

            if mines < 2 and NagaHallCount(false) < 2 and GetGold() > 320 then
                set take_exp = true
                if GetExpansionFoe() == null then
                    set expPeon = GetExpansionPeon()
                    if expPeon != null then
                        call SetExpansion(expPeon, NAGA_HALL_T1)
                    endif
                endif
            endif
            if TownHasHall(1) then
                call NagaNeedUnit(2, NAGA_GUARDIAN, 1)
            endif

            // Tech to Tier 3: Abyssal Citadel (`n002`)
            if GetUnitCountDone(NAGA_SHRINE) >= 1 and NagaTier3Count(false) < 1 then
                call SetProduce(1, NAGA_HALL_T3, -1)
            endif
        endif

        // Tier-3 Lategame: 3rd Hero, Naga Royal Guards (from Behemoth Pool), Master Sirens, +3/+3
        if naga_tier3_done then
            call NagaNeedUnit(1, hero_id3, -1)
            if GetUnitCountDone(NAGA_BEHEMOTH) >= 1 then
                call NagaNeedUnit(2, NAGA_ROYAL_GUARD, -1)
                call NagaNeedUnit(2, NAGA_TURTLE, -1)
            endif
            call NagaNeedUnit(4, NAGA_MYRMIDON, -1)
            call NagaNeedUnit(4, NAGA_SNAP_DRAGON, -1)
            call NagaNeedUnit(3, NAGA_SIREN, -1)
            call NagaNeedUnit(3, NAGA_COUATL, -1)

            if GetUnitCountDone(NAGA_SHRINE) >= 1 and GetUpgradeLevel(UPG_NAGA_SIREN) < 2 then
                call SetUpgrade(UPG_NAGA_SIREN)
            endif
            if GetUnitCountDone(NAGA_FORGE) >= 1 then
                if GetUpgradeLevel(UPG_NAGA_BLADES) < 3 then
                    call SetUpgrade(UPG_NAGA_BLADES)
                endif
                if GetUpgradeLevel(UPG_NAGA_SCALES) < 3 then
                    call SetUpgrade(UPG_NAGA_SCALES)
                endif
            endif
        endif

        call InitDefenseGroup()
        call CampaignDefenderEx(1, 1, 2, NAGA_MYRMIDON)
        call CampaignDefenderEx(1, 1, 2, NAGA_SNAP_DRAGON)
        call CampaignDefenderEx(0, 1, 1, NAGA_SIREN)

        call Sleep(3)
    endloop
endfunction

function NagaAttackWave takes integer qty, integer id returns nothing
    local integer have = GetUnitCountDone(id)
    if have > 0 then
        if have > qty then
            set have = qty
        endif
        call AddAssault(have, id)
    endif
endfunction

function NagaAttackLoop takes nothing returns nothing
    local boolean needsExp
    local boolean hasSiege
    local boolean majorOk
    local boolean airUnits
    local integer armyReady

    call Sleep(25)
    loop
        loop
            set armyReady = GetUnitCountDone(hero_id) + GetUnitCountDone(hero_id2) + GetUnitCountDone(hero_id3)
            exitwhen armyReady >= 1 and (GetUnitCountDone(NAGA_REAVER) + GetUnitCountDone(NAGA_MYRMIDON) + GetUnitCountDone(NAGA_SNAP_DRAGON)) >= 4
            exitwhen (GetUnitCountDone(NAGA_REAVER) + GetUnitCountDone(NAGA_MYRMIDON) + GetUnitCountDone(NAGA_SNAP_DRAGON)) >= 6
            call Sleep(4)
        endloop

        call InitAssaultGroup()
        call NagaAttackWave(1, hero_id)
        call NagaAttackWave(1, hero_id2)
        call NagaAttackWave(1, hero_id3)
        call NagaAttackWave(4, NAGA_REAVER)
        call NagaAttackWave(4, NAGA_MYRMIDON)
        call NagaAttackWave(4, NAGA_SNAP_DRAGON)
        call NagaAttackWave(3, NAGA_SIREN)
        call NagaAttackWave(3, NAGA_COUATL)
        call NagaAttackWave(2, NAGA_TURTLE)
        call NagaAttackWave(2, NAGA_ROYAL_GUARD)

        set needsExp = (GetMinesOwned() < 2 and naga_tier2_done)
        set hasSiege = (GetUnitCountDone(NAGA_TURTLE) >= 1 or GetUnitCountDone(NAGA_ROYAL_GUARD) >= 1)
        set majorOk  = (naga_tier2_done or (GetUnitCountDone(NAGA_REAVER) + GetUnitCountDone(NAGA_SNAP_DRAGON)) >= 6)
        set airUnits = (GetUnitCountDone(NAGA_COUATL) >= 2 and GetUnitCountDone(NAGA_REAVER) == 0 and GetUnitCountDone(NAGA_MYRMIDON) == 0)

        call SingleMeleeAttack(needsExp, hasSiege, majorOk, airUnits)
        call Sleep(5)
    endloop
endfunction

function main takes nothing returns nothing
    local boolean isNewbie = (MeleeDifficulty() == MELEE_NEWBIE)

    call InitAI()
    call SetPlayerName(ai_player, "Naga Empire AI")
    call SetMeleeAI()
    call SetDefendPlayer(true)
    call SetRandomPaths(false)
    call SetTargetHeroes(not isNewbie)
    call SetPeonsRepair(true)
    call SetHeroesFlee(not isNewbie)
    call SetHeroesBuyItems(not isNewbie)
    call SetUnitsFlee(not isNewbie)
    call SetGroupsFlee(not isNewbie)
    call SetIgnoreInjured(true)
    call SetHeroesTakeItems(true)
    call SetSmartArtillery(not isNewbie)
    call SetWatchMegaTargets(true)

    set racial_farm = NAGA_CORAL_BED
    call ChooseNagaHeroes()
    call SetHeroLevels(function SkillArrays)

    call CreateCaptains()
    call Sleep(0.1)

    call StartThread(function NagaHarvestLoop)
    call StartThread(function NagaBuildLoop)
    call NagaAttackLoop()
endfunction
"""


def generate_camphuman_ai_script() -> str:
    """
    Full competitive Warcraft III `common.ai` Melee AI script for Campaign Human,
    updated for the proper v2 11-building techtree (`h007` Barracks, `nheb` Mage Tower,
    `h008` Siege Workshop, `h009` Dragonhawk Aviary).
    """
    return """//============================================================================
//  Campaign Human (Silvermoon) Pro Melee AI (`camphuman_melee.ai`)
//  Compatible with Warcraft III TFT 1.26a/1.27b & Reforged
//============================================================================
globals
    boolean ch_tier2_done = false
    boolean ch_tier3_done = false

    constant integer CH_ENGINEER       = 'nhew'
    constant integer CH_HALL_T1        = 'h001'
    constant integer CH_HALL_T2        = 'h002'
    constant integer CH_HALL_T3        = 'h003'
    constant integer CH_ELVEN_FARM     = 'nefm'
    constant integer CH_BARRACKS       = 'h007'
    constant integer CH_LUMBER_MILL    = 'hlum'
    constant integer CH_FORGE          = 'hbla'
    constant integer CH_ALTAR          = 'h004'
    constant integer CH_RELIQUARY      = 'h005'
    constant integer CH_MAGE_TOWER     = 'nheb'
    constant integer CH_WORKSHOP       = 'h008'
    constant integer CH_AVIARY         = 'h009'
    constant integer CH_WATCH_TOWER    = 'negt'
    constant integer CH_GUARD_TOWER    = 'negf'
    constant integer CH_ARCANE_TOWER   = 'negm'

    constant integer CH_SWORDSMAN      = 'hhes'
    constant integer CH_ARCHER         = 'nhea'
    constant integer CH_CAPTAIN        = 'hcth'
    constant integer CH_CHAPLAIN       = 'nchp'
    constant integer CH_HYDROMANCER    = 'nhym'
    constant integer CH_SPELLBREAKER   = 'hspt'
    constant integer CH_GYRO           = 'hgyr'
    constant integer CH_BALLISTA       = 'h006'
    constant integer CH_LIEUTENANT     = 'nbel'
    constant integer CH_DRAGONHAWK     = 'hdhw'
    constant integer CH_GRYPHON        = 'hgry'

    constant integer HERO_KAEL         = 'Hkal'
    constant integer HERO_SYLVANAS     = 'Hvwd'
    constant integer HERO_GARITHOS     = 'Hlgr'
    constant integer HERO_UTHER        = 'Huth'

    constant integer UPG_CH_DEFEND     = 'Rhde'
    constant integer UPG_CH_WAR_TRAIN  = 'Rhan'
    constant integer UPG_CH_MELEE_ATK  = 'Rhme'
    constant integer UPG_CH_RANGED_ATK = 'Rhra'
    constant integer UPG_CH_PLATE_ARM  = 'Rhar'
    constant integer UPG_CH_LEATH_ARM  = 'Rhla'
    constant integer UPG_CH_LUMBER     = 'Rhlh'
    constant integer UPG_CH_MASONRY    = 'Rhac'
    constant integer UPG_CH_PRIEST     = 'Rhpt'
    constant integer UPG_CH_SORC       = 'Rhst'
    constant integer UPG_CH_CONTROL    = 'Rhss'
    constant integer UPG_CH_CLOUD      = 'Rhcd'
    constant integer UPG_CH_HAMMERS    = 'Rhhb'
endglobals

function CHHallCount takes boolean doneOnly returns integer
    if doneOnly then
        return GetUnitCountDone(CH_HALL_T1) + GetUnitCountDone(CH_HALL_T2) + GetUnitCountDone(CH_HALL_T3)
    endif
    return GetUnitCount(CH_HALL_T1) + GetUnitCount(CH_HALL_T2) + GetUnitCount(CH_HALL_T3)
endfunction

function CHTier2Count takes boolean doneOnly returns integer
    if doneOnly then
        return GetUnitCountDone(CH_HALL_T2) + GetUnitCountDone(CH_HALL_T3)
    endif
    return GetUnitCount(CH_HALL_T2) + GetUnitCount(CH_HALL_T3)
endfunction

function CHTier3Count takes boolean doneOnly returns integer
    if doneOnly then
        return GetUnitCountDone(CH_HALL_T3)
    endif
    return GetUnitCount(CH_HALL_T3)
endfunction

function CHTowerCount takes nothing returns integer
    return GetUnitCount(CH_WATCH_TOWER) + GetUnitCount(CH_GUARD_TOWER) + GetUnitCount(CH_ARCANE_TOWER)
endfunction

function CHNeedUnit takes integer qty, integer id, integer town returns nothing
    local integer have = GetUnitCount(id)
    if have < qty then
        call SetProduce(qty - have, id, town)
    endif
endfunction

function CHSetSkills takes integer heroId, integer slot returns nothing
    if heroId == HERO_KAEL then
        set skill[ 1] = 'AHfs'
        set skill[ 2] = 'AHdr'
        set skill[ 3] = 'AHfs'
        set skill[ 4] = 'AHbn'
        set skill[ 5] = 'AHfs'
        set skill[ 6] = 'AHpx'
        set skill[ 7] = 'AHdr'
        set skill[ 8] = 'AHdr'
        set skill[ 9] = 'AHbn'
        set skill[10] = 'AHbn'
    elseif heroId == HERO_SYLVANAS then
        set skill[ 1] = 'AHfa'
        set skill[ 2] = 'AEar'
        set skill[ 3] = 'AHfa'
        set skill[ 4] = 'AEar'
        set skill[ 5] = 'AHfa'
        set skill[ 6] = 'AEsf'
        set skill[ 7] = 'AEar'
        set skill[ 8] = 'AEst'
        set skill[ 9] = 'AEst'
        set skill[10] = 'AEst'
    elseif heroId == HERO_GARITHOS then
        set skill[ 1] = 'AOsh'
        set skill[ 2] = 'AHhb'
        set skill[ 3] = 'AOsh'
        set skill[ 4] = 'AHad'
        set skill[ 5] = 'AOsh'
        set skill[ 6] = 'AHav'
        set skill[ 7] = 'AHhb'
        set skill[ 8] = 'AHhb'
        set skill[ 9] = 'AHad'
        set skill[10] = 'AHad'
    else
        set skill[ 1] = 'AHhb'
        set skill[ 2] = 'AHds'
        set skill[ 3] = 'AHhb'
        set skill[ 4] = 'AHad'
        set skill[ 5] = 'AHhb'
        set skill[ 6] = 'AHre'
        set skill[ 7] = 'AHad'
        set skill[ 8] = 'AHad'
        set skill[ 9] = 'AHds'
        set skill[10] = 'AHds'
    endif
endfunction

function ChooseCHHeroes takes nothing returns nothing
    local integer roll = GetRandomInt(1, 4)
    if roll == 1 then
        set hero_id  = HERO_KAEL
        set hero_id2 = HERO_UTHER
        set hero_id3 = HERO_SYLVANAS
    elseif roll == 2 then
        set hero_id  = HERO_SYLVANAS
        set hero_id2 = HERO_GARITHOS
        set hero_id3 = HERO_UTHER
    elseif roll == 3 then
        set hero_id  = HERO_GARITHOS
        set hero_id2 = HERO_KAEL
        set hero_id3 = HERO_UTHER
    else
        set hero_id  = HERO_UTHER
        set hero_id2 = HERO_SYLVANAS
        set hero_id3 = HERO_KAEL
    endif

    call CHSetSkills(hero_id, 1)
    call SetSkillArray(1, hero_id)
    call CHSetSkills(hero_id2, 2)
    call SetSkillArray(2, hero_id2)
    call CHSetSkills(hero_id3, 3)
    call SetSkillArray(3, hero_id3)
endfunction

function CHHarvestLoop takes nothing returns nothing
    local integer workers
    local integer woodWorkers
    loop
        call ClearHarvestAI()

        if TownHasMine(0) and TownHasHall(0) then
            call HarvestGold(0, 5)
        endif
        if TownHasMine(1) and TownHasHall(1) then
            call HarvestGold(1, 5)
        endif
        if TownHasMine(2) and TownHasHall(2) then
            call HarvestGold(2, 5)
        endif

        set workers = GetUnitCountDone(CH_ENGINEER)
        if workers > 6 then
            set woodWorkers = workers - 5
            if woodWorkers > 10 then
                set woodWorkers = 10
            endif
            call HarvestWood(0, woodWorkers)
        else
            call HarvestWood(0, 2)
        endif

        call Sleep(6)
    endloop
endfunction

function CHBuildLoop takes nothing returns nothing
    local unit expPeon
    local integer mines
    loop
        call InitBuildArray()

        set ch_tier2_done = (CHTier2Count(true) >= 1)
        set ch_tier3_done = (CHTier3Count(true) >= 1)
        set mines = GetMinesOwned()

        if CHHallCount(false) < 1 then
            call SetProduce(1, CH_HALL_T1, -1)
        endif

        if FoodUsed() + 5 >= FoodCap() and FoodCap() < 100 and GetUnitCount(CH_ELVEN_FARM) < 16 then
            call CHNeedUnit(GetUnitCountDone(CH_ELVEN_FARM) + 1, CH_ELVEN_FARM, -1)
        endif

        if mines >= 2 then
            call CHNeedUnit(19, CH_ENGINEER, -1)
        else
            call CHNeedUnit(14, CH_ENGINEER, -1)
        endif

        // Tier-1 Opening: Farm -> Altar -> Silvermoon Barracks (`h007`) -> Farm -> Hero 1 -> Reliquary
        call CHNeedUnit(1, CH_ELVEN_FARM, -1)
        call CHNeedUnit(1, CH_ALTAR, -1)
        call CHNeedUnit(1, CH_BARRACKS, -1)
        call CHNeedUnit(2, CH_ELVEN_FARM, -1)

        if GetUnitCountDone(CH_ALTAR) >= 1 then
            call CHNeedUnit(1, hero_id, -1)
            call CHNeedUnit(1, CH_RELIQUARY, -1)
        endif

        if GetUnitCountDone(CH_BARRACKS) >= 1 then
            call CHNeedUnit(4, CH_SWORDSMAN, -1)
            call CHNeedUnit(3, CH_ARCHER, -1)
            call CHNeedUnit(3, CH_ELVEN_FARM, -1)
            call CHNeedUnit(1, CH_LUMBER_MILL, -1)
            call CHNeedUnit(1, CH_FORGE, -1)
            call SetUpgrade(UPG_CH_DEFEND)
        endif

        // Build & Upgrade Sunspire Defense Towers
        if GetUnitCountDone(CH_LUMBER_MILL) >= 1 and CHTowerCount() < 2 then
            call SetProduce(1, CH_WATCH_TOWER, 0)
        endif
        if GetUnitCountDone(CH_WATCH_TOWER) >= 1 and GetUnitCountDone(CH_LUMBER_MILL) >= 1 then
            if GetUnitCount(CH_GUARD_TOWER) < 1 then
                call SetProduce(1, CH_GUARD_TOWER, -1)
            elseif GetUnitCountDone(CH_RELIQUARY) >= 1 and GetUnitCount(CH_ARCANE_TOWER) < 1 then
                call SetProduce(1, CH_ARCANE_TOWER, -1)
            endif
        endif

        // Tier-1 Blacksmith Upgrades
        if GetUnitCountDone(CH_FORGE) >= 1 and GetGold() > 140 then
            if GetUpgradeLevel(UPG_CH_MELEE_ATK) < 1 then
                call SetUpgrade(UPG_CH_MELEE_ATK)
            endif
            if GetUpgradeLevel(UPG_CH_PLATE_ARM) < 1 then
                call SetUpgrade(UPG_CH_PLATE_ARM)
            endif
            if GetUpgradeLevel(UPG_CH_RANGED_ATK) < 1 then
                call SetUpgrade(UPG_CH_RANGED_ATK)
            endif
        endif

        // Tech to Tier 2: Sunwell Keep (`h002`)
        if GetUnitCountDone(CH_ALTAR) >= 1 and GetUnitCountDone(CH_BARRACKS) >= 1 and CHTier2Count(false) < 1 then
            call SetProduce(1, CH_HALL_T2, -1)
        endif

        // Tier-2 Midgame: 2nd Hero, Mage Tower (`nheb`), Siege Workshop (`h008`), Aviary (`h009`) & Expansion
        if ch_tier2_done then
            call CHNeedUnit(1, hero_id2, -1)
            call CHNeedUnit(1, CH_MAGE_TOWER, -1)
            if GetUnitCountDone(CH_FORGE) >= 1 then
                call CHNeedUnit(1, CH_WORKSHOP, -1)
            endif
            if GetUnitCountDone(CH_LUMBER_MILL) >= 1 then
                call CHNeedUnit(1, CH_AVIARY, -1)
            endif

            if GetUnitCountDone(CH_MAGE_TOWER) >= 1 then
                call CHNeedUnit(2, CH_CHAPLAIN, -1)
                call CHNeedUnit(2, CH_HYDROMANCER, -1)
                if GetUnitCountDone(CH_RELIQUARY) >= 1 then
                    call CHNeedUnit(2, CH_SPELLBREAKER, -1)
                endif
                if GetUpgradeLevel(UPG_CH_PRIEST) < 1 then
                    call SetUpgrade(UPG_CH_PRIEST)
                endif
                if GetUpgradeLevel(UPG_CH_SORC) < 1 then
                    call SetUpgrade(UPG_CH_SORC)
                endif
            endif

            if GetUnitCountDone(CH_WORKSHOP) >= 1 then
                call CHNeedUnit(2, CH_BALLISTA, -1)
            endif
            if GetUnitCountDone(CH_AVIARY) >= 1 then
                call CHNeedUnit(2, CH_DRAGONHAWK, -1)
                if GetUnitCountDone(CH_RELIQUARY) >= 1 then
                    call SetUpgrade(UPG_CH_CLOUD)
                endif
            endif

            if GetUnitCountDone(CH_FORGE) >= 1 then
                if GetUpgradeLevel(UPG_CH_MELEE_ATK) < 2 then
                    call SetUpgrade(UPG_CH_MELEE_ATK)
                endif
                if GetUpgradeLevel(UPG_CH_PLATE_ARM) < 2 then
                    call SetUpgrade(UPG_CH_PLATE_ARM)
                endif
                if GetUpgradeLevel(UPG_CH_RANGED_ATK) < 2 then
                    call SetUpgrade(UPG_CH_RANGED_ATK)
                endif
                if GetUpgradeLevel(UPG_CH_LEATH_ARM) < 1 then
                    call SetUpgrade(UPG_CH_LEATH_ARM)
                endif
            endif
            if GetUnitCountDone(CH_LUMBER_MILL) >= 1 and GetUpgradeLevel(UPG_CH_LUMBER) < 1 then
                call SetUpgrade(UPG_CH_LUMBER)
            endif

            if GetGold() > 450 then
                call CHNeedUnit(2, CH_BARRACKS, -1)
            endif

            if mines < 2 and CHHallCount(false) < 2 and GetGold() > 320 then
                set take_exp = true
                if GetExpansionFoe() == null then
                    set expPeon = GetExpansionPeon()
                    if expPeon != null then
                        call SetExpansion(expPeon, CH_HALL_T1)
                    endif
                endif
            endif
            if TownHasHall(1) and CHTowerCount() < 4 then
                call SetProduce(1, CH_WATCH_TOWER, 1)
            endif

            // Tech to Tier 3: Silvermoon Citadel (`h003`)
            if GetUnitCountDone(CH_MAGE_TOWER) >= 1 and CHTier3Count(false) < 1 then
                call SetProduce(1, CH_HALL_T3, -1)
            endif
        endif

        // Tier-3 Lategame: 3rd Hero, Alliance Captains (`h007`), Lieutenants (`h008`), Gryphons (`h009`), +3/+3
        if ch_tier3_done then
            call CHNeedUnit(1, hero_id3, -1)
            if GetUnitCountDone(CH_FORGE) >= 1 and GetUnitCountDone(CH_LUMBER_MILL) >= 1 then
                call CHNeedUnit(3, CH_CAPTAIN, -1)
                call SetUpgrade(UPG_CH_WAR_TRAIN)
            endif
            if GetUnitCountDone(CH_WORKSHOP) >= 1 and GetUnitCountDone(CH_RELIQUARY) >= 1 then
                call CHNeedUnit(2, CH_LIEUTENANT, -1)
                call CHNeedUnit(2, CH_BALLISTA, -1)
            endif
            if GetUnitCountDone(CH_AVIARY) >= 1 then
                call CHNeedUnit(2, CH_GRYPHON, -1)
                call CHNeedUnit(2, CH_DRAGONHAWK, -1)
                call SetUpgrade(UPG_CH_HAMMERS)
            endif

            if GetUnitCountDone(CH_MAGE_TOWER) >= 1 then
                call CHNeedUnit(3, CH_CHAPLAIN, -1)
                call CHNeedUnit(2, CH_HYDROMANCER, -1)
                call CHNeedUnit(2, CH_SPELLBREAKER, -1)
                if GetUpgradeLevel(UPG_CH_PRIEST) < 2 then
                    call SetUpgrade(UPG_CH_PRIEST)
                endif
                if GetUpgradeLevel(UPG_CH_SORC) < 2 then
                    call SetUpgrade(UPG_CH_SORC)
                endif
                call SetUpgrade(UPG_CH_CONTROL)
            endif

            if GetUnitCountDone(CH_FORGE) >= 1 then
                if GetUpgradeLevel(UPG_CH_MELEE_ATK) < 3 then
                    call SetUpgrade(UPG_CH_MELEE_ATK)
                endif
                if GetUpgradeLevel(UPG_CH_PLATE_ARM) < 3 then
                    call SetUpgrade(UPG_CH_PLATE_ARM)
                endif
                if GetUpgradeLevel(UPG_CH_RANGED_ATK) < 3 then
                    call SetUpgrade(UPG_CH_RANGED_ATK)
                endif
                if GetUpgradeLevel(UPG_CH_LEATH_ARM) < 2 then
                    call SetUpgrade(UPG_CH_LEATH_ARM)
                endif
            endif
            if GetUnitCountDone(CH_LUMBER_MILL) >= 1 then
                if GetUpgradeLevel(UPG_CH_LUMBER) < 2 then
                    call SetUpgrade(UPG_CH_LUMBER)
                endif
                if GetUpgradeLevel(UPG_CH_MASONRY) < 2 then
                    call SetUpgrade(UPG_CH_MASONRY)
                endif
            endif
        endif

        call InitDefenseGroup()
        call CampaignDefenderEx(1, 1, 2, CH_SWORDSMAN)
        call CampaignDefenderEx(1, 1, 2, CH_ARCHER)
        call CampaignDefenderEx(0, 1, 1, CH_CHAPLAIN)

        call Sleep(3)
    endloop
endfunction

function CHAttackWave takes integer qty, integer id returns nothing
    local integer have = GetUnitCountDone(id)
    if have > 0 then
        if have > qty then
            set have = qty
        endif
        call AddAssault(have, id)
    endif
endfunction

function CHAttackLoop takes nothing returns nothing
    local boolean needsExp
    local boolean hasSiege
    local boolean majorOk
    local boolean airUnits
    local integer armyReady

    call Sleep(25)
    loop
        loop
            set armyReady = GetUnitCountDone(hero_id) + GetUnitCountDone(hero_id2) + GetUnitCountDone(hero_id3)
            exitwhen armyReady >= 1 and (GetUnitCountDone(CH_SWORDSMAN) + GetUnitCountDone(CH_ARCHER) + GetUnitCountDone(CH_CAPTAIN)) >= 4
            exitwhen (GetUnitCountDone(CH_SWORDSMAN) + GetUnitCountDone(CH_ARCHER) + GetUnitCountDone(CH_CAPTAIN)) >= 6
            call Sleep(4)
        endloop

        call InitAssaultGroup()
        call CHAttackWave(1, hero_id)
        call CHAttackWave(1, hero_id2)
        call CHAttackWave(1, hero_id3)
        call CHAttackWave(4, CH_SWORDSMAN)
        call CHAttackWave(3, CH_CAPTAIN)
        call CHAttackWave(4, CH_ARCHER)
        call CHAttackWave(3, CH_CHAPLAIN)
        call CHAttackWave(2, CH_HYDROMANCER)
        call CHAttackWave(2, CH_SPELLBREAKER)
        call CHAttackWave(2, CH_DRAGONHAWK)
        call CHAttackWave(2, CH_GRYPHON)
        call CHAttackWave(2, CH_BALLISTA)
        call CHAttackWave(2, CH_LIEUTENANT)

        set needsExp = (GetMinesOwned() < 2 and ch_tier2_done)
        set hasSiege = (GetUnitCountDone(CH_BALLISTA) >= 1 or GetUnitCountDone(CH_GRYPHON) >= 2)
        set majorOk  = (ch_tier2_done or (GetUnitCountDone(CH_SWORDSMAN) + GetUnitCountDone(CH_ARCHER)) >= 6)
        set airUnits = ((GetUnitCountDone(CH_DRAGONHAWK) + GetUnitCountDone(CH_GRYPHON)) >= 2 and GetUnitCountDone(CH_SWORDSMAN) == 0 and GetUnitCountDone(CH_CAPTAIN) == 0)

        call SingleMeleeAttack(needsExp, hasSiege, majorOk, airUnits)
        call Sleep(5)
    endloop
endfunction

function main takes nothing returns nothing
    local boolean isNewbie = (MeleeDifficulty() == MELEE_NEWBIE)

    call InitAI()
    call SetPlayerName(ai_player, "Silvermoon Expedition AI")
    call SetMeleeAI()
    call SetDefendPlayer(true)
    call SetRandomPaths(false)
    call SetTargetHeroes(not isNewbie)
    call SetPeonsRepair(true)
    call SetHeroesFlee(not isNewbie)
    call SetHeroesBuyItems(not isNewbie)
    call SetUnitsFlee(not isNewbie)
    call SetGroupsFlee(not isNewbie)
    call SetIgnoreInjured(true)
    call SetHeroesTakeItems(true)
    call SetSmartArtillery(not isNewbie)
    call SetWatchMegaTargets(true)

    set racial_farm = CH_ELVEN_FARM
    call ChooseCHHeroes()
    call SetHeroLevels(function SkillArrays)

    call CreateCaptains()
    call Sleep(0.1)

    call StartThread(function CHHarvestLoop)
    call StartThread(function CHBuildLoop)
    call CHAttackLoop()
endfunction
"""


# ==============================================================================
# 6. JASS2 6-RACE SELECTION (LOBBY + DIALOG + CHAT) & AI TACTICAL MICRO SYSTEM
# ==============================================================================

def generate_custom_races_jass() -> Tuple[str, str]:
    """
    Returns `(globals_block, functions_block)` to embed into `war3map.j`.
    Guaranteed leak-free and 100% compliant with TFT 1.26a/1.27b & Reforged JASS2.
    """
    globals_jass = """    // ---- 6-Race Altered Melee Globals ((8) Crown of WarMahdi) ----
    integer array udg_PlayerFaction
    boolean array udg_PlayerLockedInLobby
    boolean array udg_PlayerChoseRace
    boolean array udg_AIStarted

    dialog array udg_RaceDialog
    button array udg_BtnKeepLobby
    button array udg_BtnNaga
    button array udg_BtnCampHuman
    button array udg_BtnRandom6
    button array udg_BtnHuman
    button array udg_BtnOrc
    button array udg_BtnUndead
    button array udg_BtnNightElf

    dialog udg_HostAIDialog = null
    button udg_BtnAIMix = null
    button udg_BtnAINaga = null
    button udg_BtnAICampHuman = null
    button udg_BtnAIKeepLobby = null
    integer udg_HostPlayerId = -1
    boolean udg_HostAIChose = false
    boolean udg_HasDefaultAI = false
    boolean udg_SelectionPhaseOpen = true

    timer udg_DialogOpenTimer = null
    timer udg_DialogExpireTimer = null
    timer udg_AIMicroTimer = null
    trigger udg_ChatRaceTrig = null
    trigger udg_TownPortalTrig = null
"""

    functions_jass = """//***************************************************************************
//*
//*  6-Race Altered Melee Core (Human, Orc, Undead, Night Elf, Naga, Campaign Human)
//*  - Pre-Game Lobby Handicap Selector:
//*      90% Handicap in Lobby -> Naga Empire (restores to 100% HP at 0.00s!)
//*      80% Handicap in Lobby -> Campaign Human (restores to 100% HP at 0.00s!)
//*      70% Handicap in Lobby -> Random (All 6 Races, restores to 100% HP!)
//*  - Instant t=0.10s Clickable Race Selection Dialog + Host AI Mode Dialog
//*  - Chat Commands: -naga, -camphuman, -random6 (first 15s) & -races (anytime)
//*  - Safe Zero-Flicker Base Spawner + Native Pro AI + Tactical Spell Micro
//*
//***************************************************************************

function GetVanillaFactionCode takes player p returns integer
    local race r = GetPlayerRace(p)
    if r == RACE_HUMAN then
        return 1
    elseif r == RACE_ORC then
        return 2
    elseif r == RACE_UNDEAD then
        return 3
    elseif r == RACE_NIGHTELF then
        return 4
    endif
    return 1
endfunction

function GetFactionDisplayName takes integer faction returns string
    if faction == 1 then
        return "|cff60a5faHuman Alliance|r"
    elseif faction == 2 then
        return "|cfff87171Orcish Horde|r"
    elseif faction == 3 then
        return "|cffc084fcUndead Scourge|r"
    elseif faction == 4 then
        return "|cff4ade80Night Elf Sentinel|r"
    elseif faction == 5 then
        return "|cff22d3eeNaga Empire|r"
    elseif faction == 6 then
        return "|cfffbbf24Campaign Human (Silvermoon)|r"
    endif
    return "Unknown"
endfunction

function RegisterCustomHeroLimitsForPlayer takes player p returns nothing
    call SetPlayerTechMaxAllowed(p, 'Hvsh', 1)
    call SetPlayerTechMaxAllowed(p, 'N001', 1)
    call SetPlayerTechMaxAllowed(p, 'N002', 1)
    call SetPlayerTechMaxAllowed(p, 'N003', 1)
    call SetPlayerTechMaxAllowed(p, 'Hkal', 1)
    call SetPlayerTechMaxAllowed(p, 'Hvwd', 1)
    call SetPlayerTechMaxAllowed(p, 'Hlgr', 1)
    call SetPlayerTechMaxAllowed(p, 'Huth', 1)
endfunction

function SpawnFactionStartingUnits takes player p, integer faction returns nothing
    local integer pid = GetPlayerId(p)
    local integer startLocIdx = GetPlayerStartLocation(p)
    local location startLoc = GetStartLocationLoc(startLocIdx)
    local real sx = GetStartLocationX(startLocIdx)
    local real sy = GetStartLocationY(startLocIdx)
    local unit nearestMine = null
    local unit restoredMine = null
    local real mx = 0.0
    local real my = 0.0
    local integer mgold = 12500
    local real wx = sx
    local real wy = sy
    local real dx = 0.0
    local real dy = 0.0
    local real dist = 0.0
    local real angle = 270.0
    local group oldUnits = CreateGroup()
    local group scanUnits = CreateGroup()
    local unit u = null
    local unit newHall = null
    local integer ut = 0
    local integer hallId = 'htow'
    local integer workerId = 'hpea'
    local integer w = 0

    call GroupEnumUnitsOfPlayer(oldUnits, p, null)
    call GroupEnumUnitsOfPlayer(scanUnits, p, null)

    // Restore clean Neutral Passive 'ngol' Gold Mine & clear Blight if swapping from UD/NE
    loop
        set u = FirstOfGroup(scanUnits)
        exitwhen u == null
        call GroupRemoveUnit(scanUnits, u)
        set ut = GetUnitTypeId(u)
        if ut == 'ugol' or ut == 'egol' then
            set mx = GetUnitX(u)
            set my = GetUnitY(u)
            set mgold = GetResourceAmount(u)
            if mgold <= 0 then
                set mgold = 12500
            endif
            call GroupRemoveUnit(oldUnits, u)
            call RemoveUnit(u)
            set restoredMine = CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE), 'ngol', mx, my, bj_UNIT_FACING)
            call SetResourceAmount(restoredMine, mgold)
            call SetBlight(p, mx, my, 960.0, false)
            call SetBlight(p, sx, sy, 960.0, false)
        endif
    endloop
    call DestroyGroup(scanUnits)

    set nearestMine = MeleeFindNearestMine(startLoc, bj_MELEE_MINE_SEARCH_RADIUS)
    if nearestMine != null then
        set dx = GetUnitX(nearestMine) - sx
        set dy = GetUnitY(nearestMine) - sy
        set dist = SquareRoot(dx * dx + dy * dy)
        if dist > 1.0 then
            set wx = sx + 320.0 * (dx / dist)
            set wy = sy + 320.0 * (dy / dist)
            set angle = bj_RADTODEG * Atan2(dy, dx)
        endif
    endif

    if faction == 1 then
        call MeleeStartingUnitsHuman(p, startLoc, true, true, true)
    elseif faction == 2 then
        call MeleeStartingUnitsOrc(p, startLoc, true, true, true)
    elseif faction == 3 then
        call MeleeStartingUnitsUndead(p, startLoc, true, true, true)
    elseif faction == 4 then
        call MeleeStartingUnitsNightElf(p, startLoc, true, true, true)
    else
        if faction == 5 then
            set hallId = 'nntt'
            set workerId = 'nmpe'
        else
            set hallId = 'h001'
            set workerId = 'nhew'
        endif

        set newHall = CreateUnit(p, hallId, sx, sy, bj_UNIT_FACING)
        set w = 0
        loop
            exitwhen w >= 5
            set u = CreateUnit(p, workerId, wx + 44.0 * Cos(I2R(w) * 1.2566), wy + 44.0 * Sin(I2R(w) * 1.2566), angle)
            if GetLocalPlayer() == p and w == 0 then
                call ClearSelection()
                call SelectUnit(newHall, true)
            endif
            set w = w + 1
        endloop
    endif

    loop
        set u = FirstOfGroup(oldUnits)
        exitwhen u == null
        call GroupRemoveUnit(oldUnits, u)
        call RemoveUnit(u)
    endloop
    call DestroyGroup(oldUnits)
    call RemoveLocation(startLoc)

    call SetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD, bj_MELEE_STARTING_GOLD_V1)
    call SetPlayerState(p, PLAYER_STATE_RESOURCE_LUMBER, bj_MELEE_STARTING_LUMBER_V1)
    call SetPlayerState(p, PLAYER_STATE_RESOURCE_HERO_TOKENS, bj_MELEE_STARTING_HERO_TOKENS)
    call RegisterCustomHeroLimitsForPlayer(p)

    set udg_PlayerFaction[pid] = faction

    if GetLocalPlayer() == p then
        call SetCameraPosition(sx, sy)
    endif

    set startLoc = null
    set oldUnits = null
    set scanUnits = null
    set nearestMine = null
    set restoredMine = null
    set newHall = null
    set u = null
endfunction

function LaunchMeleeAIForPlayer takes integer pid returns nothing
    local player p = Player(pid)
    local integer faction = udg_PlayerFaction[pid]
    if udg_AIStarted[pid] then
        set p = null
        return
    endif
    if GetPlayerSlotState(p) != PLAYER_SLOT_STATE_PLAYING or GetPlayerController(p) != MAP_CONTROL_COMPUTER then
        set p = null
        return
    endif

    set udg_AIStarted[pid] = true
    call ShareEverythingWithTeamAI(p)

    if faction == 5 then
        call StartMeleeAI(p, "naga_melee.ai")
    elseif faction == 6 then
        call StartMeleeAI(p, "camphuman_melee.ai")
    elseif faction == 1 then
        call StartMeleeAI(p, "human.ai")
    elseif faction == 2 then
        call StartMeleeAI(p, "orc.ai")
    elseif faction == 3 then
        call StartMeleeAI(p, "undead.ai")
    else
        call StartMeleeAI(p, "elf.ai")
    endif
    set p = null
endfunction

function StartAllPendingComputerAIs takes nothing returns nothing
    local integer i = 0
    loop
        exitwhen i >= 8
        call LaunchMeleeAIForPlayer(i)
        set i = i + 1
    endloop
endfunction

function ApplyHostAIMode takes integer mode returns nothing
    local integer i = 0
    local integer aiIdx = 0
    local integer targetFaction = 1
    local player p = null

    if udg_HostAIChose then
        return
    endif
    set udg_HostAIChose = true

    if mode != 4 then
        loop
            exitwhen i >= 8
            set p = Player(i)
            if GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING and GetPlayerController(p) == MAP_CONTROL_COMPUTER and (not udg_PlayerLockedInLobby[i]) then
                if mode == 2 then
                    set targetFaction = 5
                elseif mode == 3 then
                    set targetFaction = 6
                else
                    if ModuloInteger(aiIdx, 4) == 0 then
                        set targetFaction = 5
                    elseif ModuloInteger(aiIdx, 4) == 1 then
                        set targetFaction = 6
                    elseif ModuloInteger(aiIdx, 4) == 2 then
                        set targetFaction = GetVanillaFactionCode(p)
                    else
                        set targetFaction = GetRandomInt(5, 6)
                    endif
                    set aiIdx = aiIdx + 1
                endif

                if targetFaction != udg_PlayerFaction[i] then
                    call SpawnFactionStartingUnits(p, targetFaction)
                endif
                call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 10.0, "|cff94a3b8[AI Slot " + I2S(i + 1) + "]|r -> " + GetFactionDisplayName(udg_PlayerFaction[i]))
            endif
            set i = i + 1
        endloop
    endif

    call StartAllPendingComputerAIs()
    set p = null
endfunction

function ShowHostAIDialogIfNeeded takes nothing returns nothing
    if udg_HostPlayerId < 0 or (not udg_HasDefaultAI) or udg_HostAIChose then
        call StartAllPendingComputerAIs()
        return
    endif

    call DialogClear(udg_HostAIDialog)
    call DialogSetMessage(udg_HostAIDialog, "Crown of WarMahdi — Select Computer AI Races:")
    set udg_BtnAIMix       = DialogAddButton(udg_HostAIDialog, "|cff22d3ee6-Race Pro Mix|r (Add Naga & Campaign Human AI)", 49)
    set udg_BtnAINaga      = DialogAddButton(udg_HostAIDialog, "All Unassigned AI -> |cff22d3eeNaga Empire|r", 50)
    set udg_BtnAICampHuman = DialogAddButton(udg_HostAIDialog, "All Unassigned AI -> |cfffbbf24Campaign Human|r", 51)
    set udg_BtnAIKeepLobby = DialogAddButton(udg_HostAIDialog, "Keep Lobby AI Races Only", 52)
    call DialogDisplay(Player(udg_HostPlayerId), udg_HostAIDialog, true)
endfunction

function OnHostAIDialogClick takes nothing returns boolean
    local button clicked = GetClickedButton()
    call DialogDisplay(Player(udg_HostPlayerId), udg_HostAIDialog, false)
    if clicked == udg_BtnAIMix then
        call ApplyHostAIMode(1)
    elseif clicked == udg_BtnAINaga then
        call ApplyHostAIMode(2)
    elseif clicked == udg_BtnAICampHuman then
        call ApplyHostAIMode(3)
    else
        call ApplyHostAIMode(4)
    endif
    set clicked = null
    return false
endfunction

function OnPlayerRaceDialogClick takes nothing returns boolean
    local dialog d = GetClickedDialog()
    local button b = GetClickedButton()
    local integer pid = -1
    local integer i = 0
    local integer newFaction = 0
    local player p = null

    loop
        exitwhen i >= 8
        if d == udg_RaceDialog[i] then
            set pid = i
        endif
        set i = i + 1
    endloop

    if pid < 0 then
        set d = null
        set b = null
        return false
    endif

    set p = Player(pid)
    call DialogDisplay(p, d, false)
    set udg_PlayerChoseRace[pid] = true

    if b == udg_BtnKeepLobby[pid] then
        set newFaction = udg_PlayerFaction[pid]
    elseif b == udg_BtnNaga[pid] then
        set newFaction = 5
    elseif b == udg_BtnCampHuman[pid] then
        set newFaction = 6
    elseif b == udg_BtnRandom6[pid] then
        set newFaction = GetRandomInt(1, 6)
    elseif b == udg_BtnHuman[pid] then
        set newFaction = 1
    elseif b == udg_BtnOrc[pid] then
        set newFaction = 2
    elseif b == udg_BtnUndead[pid] then
        set newFaction = 3
    elseif b == udg_BtnNightElf[pid] then
        set newFaction = 4
    endif

    if newFaction >= 1 and newFaction != udg_PlayerFaction[pid] then
        call SpawnFactionStartingUnits(p, newFaction)
    endif

    call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 10.0, "|cffffd700" + GetPlayerName(p) + "|r plays as " + GetFactionDisplayName(udg_PlayerFaction[pid]) + "!")

    if pid == udg_HostPlayerId then
        call ShowHostAIDialogIfNeeded()
    endif

    set d = null
    set b = null
    set p = null
    return false
endfunction

function OnOpenRaceDialogs takes nothing returns nothing
    local integer i = 0
    local player p = null
    local string curName = ""

    loop
        exitwhen i >= 8
        set p = Player(i)
        if GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING and GetPlayerController(p) == MAP_CONTROL_USER then
            if udg_PlayerLockedInLobby[i] then
                set udg_PlayerChoseRace[i] = true
                call DisplayTimedTextToPlayer(p, 0.0, 0.0, 12.0, "|cff38bdf8[Crown of WarMahdi]|r Lobby faction locked: " + GetFactionDisplayName(udg_PlayerFaction[i]) + " (HP Handicap restored to 100%).")
                if i == udg_HostPlayerId then
                    call ShowHostAIDialogIfNeeded()
                endif
            else
                set curName = GetFactionDisplayName(udg_PlayerFaction[i])
                call DialogClear(udg_RaceDialog[i])
                call DialogSetMessage(udg_RaceDialog[i], "Crown of WarMahdi — Choose Your Race (15s):")
                set udg_BtnKeepLobby[i] = DialogAddButton(udg_RaceDialog[i], "Keep Lobby Race (" + curName + ")", 32)
                set udg_BtnNaga[i]      = DialogAddButton(udg_RaceDialog[i], "|cff22d3eeNaga Empire|r  [N]", 78)
                set udg_BtnCampHuman[i] = DialogAddButton(udg_RaceDialog[i], "|cfffbbf24Campaign Human (Silvermoon)|r  [C]", 67)
                set udg_BtnRandom6[i]   = DialogAddButton(udg_RaceDialog[i], "Random (All 6 Balanced Races)  [R]", 82)
                set udg_BtnHuman[i]     = DialogAddButton(udg_RaceDialog[i], "Standard Human", 72)
                set udg_BtnOrc[i]       = DialogAddButton(udg_RaceDialog[i], "Orcish Horde", 79)
                set udg_BtnUndead[i]    = DialogAddButton(udg_RaceDialog[i], "Undead Scourge", 85)
                set udg_BtnNightElf[i]  = DialogAddButton(udg_RaceDialog[i], "Night Elf Sentinel", 69)
                call DialogDisplay(p, udg_RaceDialog[i], true)
            endif
        endif
        set i = i + 1
    endloop

    if udg_HostPlayerId < 0 then
        call ApplyHostAIMode(1)
    endif

    set p = null
endfunction

function OnExpireRaceDialogs takes nothing returns nothing
    local integer i = 0
    local player p = null

    set udg_SelectionPhaseOpen = false
    loop
        exitwhen i >= 8
        set p = Player(i)
        if GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING and GetPlayerController(p) == MAP_CONTROL_USER then
            if not udg_PlayerChoseRace[i] then
                set udg_PlayerChoseRace[i] = true
                call DialogDisplay(p, udg_RaceDialog[i], false)
            endif
        endif
        set i = i + 1
    endloop

    if not udg_HostAIChose then
        if udg_HostPlayerId >= 0 then
            call DialogDisplay(Player(udg_HostPlayerId), udg_HostAIDialog, false)
        endif
        call ApplyHostAIMode(1)
    endif

    call StartAllPendingComputerAIs()
    set p = null
endfunction

function OnHeroSummonedGrantTP takes nothing returns boolean
    local unit u = GetTrainedUnit()
    local player p = null
    local integer ut = 0
    if u == null then
        return false
    endif
    set p = GetOwningPlayer(u)
    set ut = GetUnitTypeId(u)
    if ut == 'Hvsh' or ut == 'N001' or ut == 'N002' or ut == 'N003' or ut == 'Hkal' or ut == 'Hvwd' or ut == 'Hlgr' or ut == 'Huth' then
        if not bj_meleeGrantHeroItems then
            set u = null
            set p = null
            return false
        endif
        if GetPlayerState(p, PLAYER_STATE_RESOURCE_HERO_TOKENS) >= 0 then
            if UnitInventoryCount(u) == 0 then
                call UnitAddItemById(u, 'stwp')
            endif
        endif
    endif
    set u = null
    set p = null
    return false
endfunction

function OnPlayerChatRaceCmd takes nothing returns boolean
    local player p = GetTriggerPlayer()
    local integer pid = GetPlayerId(p)
    local string msg = StringCase(GetEventPlayerChatString(), false)
    local integer i = 0
    local player slotP = null

    if msg == "-races" then
        call DisplayTimedTextToPlayer(p, 0.0, 0.0, 12.0, "|cffffd700=== (8) Crown of WarMahdi — Active Factions ===|r")
        loop
            exitwhen i >= 8
            set slotP = Player(i)
            if GetPlayerSlotState(slotP) == PLAYER_SLOT_STATE_PLAYING then
                call DisplayTimedTextToPlayer(p, 0.0, 0.0, 12.0, "  Slot " + I2S(i + 1) + " (" + GetPlayerName(slotP) + "): " + GetFactionDisplayName(udg_PlayerFaction[i]))
            endif
            set i = i + 1
        endloop
        set p = null
        set slotP = null
        return false
    endif

    if not udg_SelectionPhaseOpen then
        set p = null
        return false
    endif

    if msg == "-naga" then
        call DialogDisplay(p, udg_RaceDialog[pid], false)
        set udg_PlayerChoseRace[pid] = true
        call SpawnFactionStartingUnits(p, 5)
        call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 10.0, "|cffffd700" + GetPlayerName(p) + "|r switched to " + GetFactionDisplayName(5) + "!")
    elseif msg == "-camphuman" or msg == "-human2" or msg == "-silvermoon" then
        call DialogDisplay(p, udg_RaceDialog[pid], false)
        set udg_PlayerChoseRace[pid] = true
        call SpawnFactionStartingUnits(p, 6)
        call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 10.0, "|cffffd700" + GetPlayerName(p) + "|r switched to " + GetFactionDisplayName(6) + "!")
    elseif msg == "-random6" then
        call DialogDisplay(p, udg_RaceDialog[pid], false)
        set udg_PlayerChoseRace[pid] = true
        call SpawnFactionStartingUnits(p, GetRandomInt(1, 6))
        call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 10.0, "|cffffd700" + GetPlayerName(p) + "|r rolled " + GetFactionDisplayName(udg_PlayerFaction[pid]) + "!")
    endif

    set p = null
    return false
endfunction

function FindNearestVisibleEnemy takes player owner, real x, real y, real radius returns unit
    local group g = CreateGroup()
    local unit u = null
    local unit best = null
    local real bestDistSq = radius * radius
    local real dx = 0.0
    local real dy = 0.0
    local real d2 = 0.0

    call GroupEnumUnitsInRange(g, x, y, radius, null)
    loop
        set u = FirstOfGroup(g)
        exitwhen u == null
        call GroupRemoveUnit(g, u)
        if IsUnitEnemy(u, owner) and GetWidgetLife(u) > 0.405 and (not IsUnitType(u, UNIT_TYPE_STRUCTURE)) and (not IsUnitInvisible(u, owner)) then
            set dx = GetUnitX(u) - x
            set dy = GetUnitY(u) - y
            set d2 = dx * dx + dy * dy
            if d2 < bestDistSq then
                set bestDistSq = d2
                set best = u
            endif
        endif
    endloop
    call DestroyGroup(g)
    set g = null
    set u = null
    return best
endfunction

function OnAITacticalMicroTick takes nothing returns nothing
    local integer i = 0
    local player p = null
    local group g = CreateGroup()
    local unit u = null
    local unit foe = null
    local integer ut = 0

    loop
        exitwhen i >= 8
        set p = Player(i)
        if udg_AIStarted[i] and (udg_PlayerFaction[i] == 5 or udg_PlayerFaction[i] == 6) and GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING then
            call GroupClear(g)
            call GroupEnumUnitsOfPlayer(g, p, null)
            loop
                set u = FirstOfGroup(g)
                exitwhen u == null
                call GroupRemoveUnit(g, u)
                if GetWidgetLife(u) > 0.405 then
                    set ut = GetUnitTypeId(u)
                    // Naga Royal Guard Crushing Wave on enemy formations
                    if ut == 'nnrg' and GetUnitState(u, UNIT_STATE_MANA) >= 90.0 then
                        set foe = FindNearestVisibleEnemy(p, GetUnitX(u), GetUnitY(u), 650.0)
                        if foe != null then
                            call IssuePointOrder(u, "carrionswarm", GetUnitX(foe), GetUnitY(foe))
                        endif
                    // Master Naga Siren Cyclone on heavy enemy frontline units
                    elseif ut == 'nnsw' and GetUnitState(u, UNIT_STATE_MANA) >= 125.0 and GetPlayerTechCount(p, 'Rnsw', true) >= 2 then
                        set foe = FindNearestVisibleEnemy(p, GetUnitX(u), GetUnitY(u), 550.0)
                        if foe != null and GetWidgetLife(foe) >= 550.0 and (not IsUnitType(foe, UNIT_TYPE_HERO)) then
                            call IssueTargetOrder(u, "cyclone", foe)
                        endif
                    // Master Dalaran Hydromancer Polymorph on heavy enemy non-Hero units
                    elseif ut == 'nhym' and GetUnitState(u, UNIT_STATE_MANA) >= 150.0 and GetPlayerTechCount(p, 'Rhst', true) >= 2 then
                        set foe = FindNearestVisibleEnemy(p, GetUnitX(u), GetUnitY(u), 550.0)
                        if foe != null and GetWidgetLife(foe) >= 600.0 and (not IsUnitType(foe, UNIT_TYPE_HERO)) then
                            call IssueTargetOrder(u, "polymorph", foe)
                        endif
                    endif
                endif
            endloop
        endif
        set i = i + 1
    endloop

    call DestroyGroup(g)
    set g = null
    set p = null
    set u = null
    set foe = null
endfunction

function InitSixRaceAlteredMelee takes nothing returns nothing
    local integer i = 0
    local player p = null
    local real hcap = 1.0
    local integer initFaction = 1
    local trigger raceTrig = CreateTrigger()
    local trigger hostAITrig = CreateTrigger()

    set udg_HostAIDialog = DialogCreate()
    call TriggerRegisterDialogEvent(hostAITrig, udg_HostAIDialog)
    call TriggerAddCondition(hostAITrig, Condition(function OnHostAIDialogClick))

    set udg_ChatRaceTrig = CreateTrigger()
    set udg_TownPortalTrig = CreateTrigger()

    loop
        exitwhen i >= 8
        set p = Player(i)
        set udg_RaceDialog[i] = DialogCreate()
        call TriggerRegisterDialogEvent(raceTrig, udg_RaceDialog[i])
        call TriggerRegisterPlayerChatEvent(udg_ChatRaceTrig, p, "-", false)
        call TriggerRegisterPlayerUnitEvent(udg_TownPortalTrig, p, EVENT_PLAYER_UNIT_TRAIN_FINISH, null)

        set udg_PlayerLockedInLobby[i] = false
        set udg_PlayerChoseRace[i] = false
        set udg_AIStarted[i] = false

        if GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING then
            if GetPlayerController(p) == MAP_CONTROL_USER and udg_HostPlayerId < 0 then
                set udg_HostPlayerId = i
            endif

            set hcap = GetPlayerHandicap(p)
            if hcap >= 0.88 and hcap <= 0.92 then
                set initFaction = 5
                set udg_PlayerLockedInLobby[i] = true
                call SetPlayerHandicap(p, 1.00)
            elseif hcap >= 0.78 and hcap <= 0.82 then
                set initFaction = 6
                set udg_PlayerLockedInLobby[i] = true
                call SetPlayerHandicap(p, 1.00)
            elseif hcap >= 0.68 and hcap <= 0.72 then
                set initFaction = GetRandomInt(1, 6)
                set udg_PlayerLockedInLobby[i] = true
                call SetPlayerHandicap(p, 1.00)
            else
                set initFaction = GetVanillaFactionCode(p)
                if GetPlayerController(p) == MAP_CONTROL_COMPUTER then
                    set udg_HasDefaultAI = true
                endif
            endif

            call SpawnFactionStartingUnits(p, initFaction)
        endif
        set i = i + 1
    endloop

    call TriggerAddCondition(raceTrig, Condition(function OnPlayerRaceDialogClick))
    call TriggerAddCondition(udg_ChatRaceTrig, Condition(function OnPlayerChatRaceCmd))
    call TriggerAddCondition(udg_TownPortalTrig, Condition(function OnHeroSummonedGrantTP))

    call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 14.0, "|cffffd700(8) Crown of WarMahdi|r — |cff22d3ee6 Balanced Races|r (Human, Orc, Undead, Night Elf, |cff22d3eeNaga|r, |cfffbbf24Campaign Human|r) | Type |cff38bdf8-races|r anytime.")

    set udg_DialogOpenTimer = CreateTimer()
    call TimerStart(udg_DialogOpenTimer, 0.10, false, function OnOpenRaceDialogs)

    set udg_DialogExpireTimer = CreateTimer()
    call TimerStart(udg_DialogExpireTimer, 15.00, false, function OnExpireRaceDialogs)

    set udg_AIMicroTimer = CreateTimer()
    call TimerStart(udg_AIMicroTimer, 3.00, true, function OnAITacticalMicroTick)

    set p = null
    set raceTrig = null
    set hostAITrig = null
endfunction
"""
    return globals_jass, functions_jass
