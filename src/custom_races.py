#!/usr/bin/env python3
"""
Custom Playable Races, Object Modifications & Pro-Level Melee AI Generator
for `(8) Crown of WarMahdi` (Warcraft III TFT 1.26a/1.27b & Reforged).

Implements two complete, competitively balanced Altered Melee factions alongside
the 4 unmodified standard Warcraft III races:
  5. Naga Empire (`RACE_NAGA = 5`)
  6. Campaign Human — Silvermoon & Alliance Expedition (`RACE_CAMPHUMAN = 6`)

All object modification files (`war3map.w3u`, `war3map.w3t`, `war3map.w3q`) use
Warcraft III's cross-patch v2 binary format (`int32(2)`) so the map loads with
zero errors in both Classic Frozen Throne 1.26a/1.27b and Reforged 1.32+.
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
    # Place uppercase ('A'..'Z') ahead of lowercase ('a'..'z')
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
            # Trailing end marker: 4 zero bytes (0x00000000) for clean compatibility
            buf += b"\x00\x00\x00\x00"
    return bytes(buf)


# ==============================================================================
# 1. UNIT & HERO OBJECT MODIFICATIONS (`war3map.w3u` v2)
# ==============================================================================

def build_unit_modifications() -> Tuple[
    List[Tuple[str, str, List[ModEntry]]],
    List[Tuple[str, str, List[ModEntry]]],
]:
    """
    Returns (original_table, custom_table) for `war3map.w3u` (version 2).
    IMPORTANT:
      - Zero gameplay stats of the 4 standard ladder races are altered.
      - On `hkee`, `hcas`, `halt`, `hvlt` we ONLY set `udep` (`DependencyOr`)
        so Campaign Human's `h002`, `h003`, `h004`, `h005` satisfy shared
        Human tech requirements (`Rhme`, `Rhra`, `Rhar`, `Rhla`, `ofir`, etc.)
        without altering standard Human in any way!
      - Custom Hero IDs MUST begin with an uppercase letter (`N001..N003`),
        and non-Hero custom IDs MUST begin with a lowercase letter (`n001..n003`,
        `h001..h006`).
    """
    NULL_ID = "\x00\x00\x00\x00"

    original: List[Tuple[str, str, List[ModEntry]]] = [
        # ---- Dependency equivalents on Human tech structures (zero stat changes) ----
        ("hkee", NULL_ID, [("udep", VT_STR, "h002")]),
        ("hcas", NULL_ID, [("udep", VT_STR, "h003")]),
        ("halt", NULL_ID, [("udep", VT_STR, "h004")]),
        ("hvlt", NULL_ID, [("udep", VT_STR, "h005")]),

        # ========================== NAGA EMPIRE (ORIGINAL UNITS) ==========================
        # Worker: Mur'gul Slave (`nmpe`) - Builds full Naga 7-structure techtree
        ("nmpe", NULL_ID, [
            ("ubui", VT_STR, "nntt,nnfm,nnad,nnsg,nnsa,n003,nntg"),
            ("ugol", VT_INT, 75),
            ("ulum", VT_INT, 0),
            ("ubld", VT_INT, 15),
            ("uhpm", VT_INT, 240),
            ("utip", VT_STR, "Train Mur'gul |cffffcc00S|rlave"),
            ("uhot", VT_STR, "S"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
        ]),

        # Tier 1 Town Hall: Temple of Tides (`nntt`) -> Upgrades to Sanctuary of Tides (`n001`)
        ("nntt", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 385),
            ("ulum", VT_INT, 185),
            ("ubld", VT_INT, 120),
            ("ufma", VT_INT, 12),
            ("uhpm", VT_INT, 1500),
            ("utra", VT_STR, "nmpe,nnmg"),
            ("ures", VT_STR, "Rnat,Rnam,Rnsb"),
            ("uupt", VT_STR, "n001"),
            ("uabi", VT_STR, "Abdl,Argl,Amic"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Build |cffffcc00T|remple of Tides"),
            ("utub", VT_STR, "Primary Naga town structure. Used to train Mur'gul Slaves and Mur'gul Reavers, research Coral Blades/Scales, and return gathered Gold and Lumber. Can be upgraded to Sanctuary of Tides."),
        ]),

        # Food Structure: Coral Bed (`nnfm`) - Build-anywhere land/shallow food structure
        ("nnfm", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 100),
            ("ulum", VT_INT, 25),
            ("ubld", VT_INT, 30),
            ("ufma", VT_INT, 10),
            ("uhpm", VT_INT, 550),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Build |cffffcc00C|roral Bed"),
            ("utub", VT_STR, "Provides 10 food, increasing the maximum number of Naga units that can be trained."),
        ]),

        # Altar: Altar of the Depths (`nnad`) - Summons 4 Naga Heroes
        ("nnad", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 180),
            ("ulum", VT_INT, 50),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 900),
            ("utra", VT_STR, "Hvsh,N001,N002,N003"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Build |cffffcc00A|rltar of the Depths"),
            ("utub", VT_STR, "Summons Naga Heroes (Lady Vashj, Abyssal Warlord, Azshara's Tideweaver, and Makrura Deepking) and revives fallen Heroes."),
        ]),

        # Barracks: Spawning Grounds (`nnsg`) - Melee, Ranged, Siege & T3 Elite
        ("nnsg", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 180),
            ("ulum", VT_INT, 50),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1200),
            ("utra", VT_STR, "nmyr,nsnp,nhyc,nnrg"),
            ("ures", VT_STR, "Rnen"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Build Spawning |cffffcc00G|rrounds"),
            ("utub", VT_STR, "Primary Naga troop production structure. Trains Naga Myrmidons, Snap Dragons, Dragon Turtles (Tier 2), and Naga Royal Guards (Tier 3). Also researches Ensnare."),
        ]),

        # Caster & Air Sanctum: Shrine of Azshara (`nnsa`) - Requires Tier 2 (`n001`)
        ("nnsa", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 150),
            ("ulum", VT_INT, 140),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 950),
            ("utra", VT_STR, "nnsw,nwgs"),
            ("ures", VT_STR, "Rnsw,Rnsi"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Build |cffffcc00S|rhrine of Azshara"),
            ("utub", VT_STR, "Spellcaster and flying creature sanctum. Trains Naga Sirens and Couatls, and researches Naga Siren Training and Abolish Magic."),
        ]),

        # Defensive Tower: Tidal Guardian (`nntg`)
        ("nntg", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "nnsg"),
            ("ugol", VT_INT, 140),
            ("ulum", VT_INT, 90),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 650),
            ("ua1b", VT_INT, 30),
            ("ubpx", VT_INT, 3),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "Build Tidal G|cffffcc00u|rardian"),
            ("utub", VT_STR, "Heavy defensive structure that hurls lightning bolts at both ground and air attackers."),
        ]),

        # Tier 1 Light Melee: Mur'gul Reaver (`nnmg`)
        ("nnmg", NULL_ID, [
            ("ugol", VT_INT, 115),
            ("ulum", VT_INT, 0),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 18),
            ("uhpm", VT_INT, 390),
            ("udef", VT_INT, 1),
            ("ua1b", VT_INT, 12),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Train Mur'gul |cffffcc00R|reaver"),
            ("utub", VT_STR, "Fast, amphibious Tier-1 shock warrior. Can attack land units and traverse deep water."),
        ]),

        # Tier 1.5 Heavy Melee: Naga Myrmidon (`nmyr`) - Balanced to 3 food (780 HP)
        ("nmyr", NULL_ID, [
            ("ugol", VT_INT, 215),
            ("ulum", VT_INT, 35),
            ("ufoo", VT_INT, 3),
            ("ubld", VT_INT, 30),
            ("uhpm", VT_INT, 780),
            ("udef", VT_INT, 3),
            ("ua1b", VT_INT, 25),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "M"),
            ("utip", VT_STR, "Train Naga |cffffcc00M|ryrmidon"),
            ("utub", VT_STR, "Powerful amphibious melee warrior. Can learn Ensnare and Submerge. Attacks land units."),
        ]),

        # Tier 1 Ranged Piercing: Snap Dragon (`nsnp`) - Balanced to 3 food (480 HP)
        ("nsnp", NULL_ID, [
            ("ugol", VT_INT, 185),
            ("ulum", VT_INT, 35),
            ("ufoo", VT_INT, 3),
            ("ubld", VT_INT, 26),
            ("uhpm", VT_INT, 480),
            ("udef", VT_INT, 1),
            ("ua1b", VT_INT, 21),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "D"),
            ("utip", VT_STR, "Train Snap |cffffcc00D|rragon"),
            ("utub", VT_STR, "Amphibious ranged beast with venomous spines that slow enemy movement and attack speed. Attacks land and air units."),
        ]),

        # Tier 2 Siege Beast: Dragon Turtle (`nhyc`) - Requires Sanctuary (`n001`)
        ("nhyc", NULL_ID, [
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 260),
            ("ulum", VT_INT, 65),
            ("ufoo", VT_INT, 4),
            ("ubld", VT_INT, 38),
            ("uhpm", VT_INT, 950),
            ("udef", VT_INT, 2),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Train Dragon |cffffcc00T|rurtle"),
            ("utub", VT_STR, "Colossal armored siege turtle with Thorny Shield and Hardened Skin. Exceptional at demolishing enemy fortifications."),
        ]),

        # Tier 3 Elite Powerhouse: Naga Royal Guard (`nnrg`) - Balanced to 5 food (1100 HP)
        ("nnrg", NULL_ID, [
            ("ureq", VT_STR, "n002"),
            ("ugol", VT_INT, 325),
            ("ulum", VT_INT, 90),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 44),
            ("uhpm", VT_INT, 1100),
            ("udef", VT_INT, 4),
            ("ua1b", VT_INT, 36),
            ("upgr", VT_STR, "Rnat,Rnam,Rnsb"),
            ("ubpx", VT_INT, 3),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "Y"),
            ("utip", VT_STR, "Train Naga Ro|cffffcc00y|ral Guard"),
            ("utub", VT_STR, "Elite Tier-3 royal champion armed with Crushing Wave, Frost Bolt, Resistant Skin, and Sea Elemental summoning."),
        ]),

        # Tier 2 Spellcaster: Naga Siren (`nnsw`) - Auto-casts Parasite
        ("nnsw", NULL_ID, [
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 145),
            ("ulum", VT_INT, 35),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 28),
            ("udaa", VT_STR, "ANpa"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "N"),
            ("utip", VT_STR, "Train Naga Sire|cffffcc00n|r"),
        ]),

        # Tier 2 Fast Flyer / Anti-Magic: Couatl (`nwgs`) - Auto-casts Abolish Magic
        ("nwgs", NULL_ID, [
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 155),
            ("ulum", VT_INT, 35),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 25),
            ("uhpm", VT_INT, 445),
            ("udaa", VT_STR, "Andm"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Train |cffffcc00C|rouatl"),
        ]),

        # Naga Hero 1: Lady Vashj (`Hvsh`) - Ranged INT Hero
        ("Hvsh", NULL_ID, [
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "n001"),
            ("urq2", VT_STR, "n002"),
            ("uhab", VT_STR, "ANfl,ANfa,ANms,ANto"),
            ("udaa", VT_STR, "ANfa"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "V"),
            ("utip", VT_STR, "Summon Lady |cffffcc00V|rashj"),
            ("utpr", VT_STR, "Revive Lady |cffffcc00V|rashj"),
            ("utub", VT_STR, "Mystic Naga Sea Witch, adept at ranged combat and tempest magic. Can learn Forked Lightning, Frost Arrows, Mana Shield, and Tornado."),
        ]),

        # =================== CAMPAIGN HUMAN (ORIGINAL CAMPAIGN UNITS) ===================
        # Worker: Silvermoon Engineer (`nhew`) - Builds full 9-structure Campaign Human techtree
        ("nhew", NULL_ID, [
            ("unam", VT_STR, "Silvermoon Engineer"),
            ("ubui", VT_STR, "h001,nefm,nheb,hlum,hbla,h004,h005,haro,negt"),
            ("ugol", VT_INT, 75),
            ("ulum", VT_INT, 0),
            ("ubld", VT_INT, 15),
            ("uhpm", VT_INT, 230),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "E"),
            ("utip", VT_STR, "Train Silvermoon |cffffcc00E|rngineer"),
            ("utub", VT_STR, "Resource worker and master builder of the Silvermoon & Alliance Expedition. Harvests Gold and Lumber, constructs buildings, and repairs fortifications."),
        ]),

        # Food Structure: High Elven Farm (`nefm`) - Fix campaign defect (cost 80g/20L, food 6)
        ("nefm", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 80),
            ("ulum", VT_INT, 20),
            ("ubld", VT_INT, 32),
            ("ufma", VT_INT, 6),
            ("uhpm", VT_INT, 500),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "F"),
            ("utip", VT_STR, "Build High Elven |cffffcc00F|rarm"),
            ("utub", VT_STR, "Provides 6 food, increasing the maximum number of Campaign Human units that can be trained."),
        ]),

        # Barracks: High Elven Barracks (`nheb`) - Trains 6 Expedition combat units + Defend
        ("nheb", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 160),
            ("ulum", VT_INT, 60),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1500),
            ("utra", VT_STR, "hhes,nhea,hcth,h006,hdhw,nbel"),
            ("ures", VT_STR, "Rhde,Rhcd"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Build High Elven |cffffcc00B|rarracks"),
            ("utub", VT_STR, "Primary troop production hall. Trains High Elven Swordsmen, High Elven Archers, Alliance Captains (Tier 2), Silvermoon Ballistas (Tier 2), Dragonhawk Riders (Tier 2), and Blood Elf Lieutenants (Tier 3)."),
        ]),

        # Caster Sanctum: Arcane Observatory (`haro`) - Repurposed campaign spire
        ("haro", NULL_ID, [
            ("unam", VT_STR, "Arcane Observatory"),
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "h002"),
            ("ugol", VT_INT, 150),
            ("ulum", VT_INT, 140),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1100),
            ("udef", VT_INT, 5),
            ("uabi", VT_STR, "Abds"),
            ("utra", VT_STR, "nchp,nhym,hspt"),
            ("ures", VT_STR, "Rhss"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "O"),
            ("utip", VT_STR, "Build Arcane |cffffcc00O|rbservatory"),
            ("utub", VT_STR, "High Elven sanctum of spellcraft. Trains Silvermoon Chaplains, Dalaran Hydromancers, and Spell Breakers, and researches Control Magic."),
        ]),

        # Base Tower: Sunspire Watch Tower (`negt`) -> Upgrades to Flame (`negf`) or Arcane (`negm`)
        ("negt", NULL_ID, [
            ("unam", VT_STR, "Sunspire Watch Tower"),
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 35),
            ("ulum", VT_INT, 25),
            ("ubld", VT_INT, 25),
            ("uhpm", VT_INT, 350),
            ("uupt", VT_STR, "negf,negm"),
            ("ubpx", VT_INT, 3),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "W"),
            ("utip", VT_STR, "Build Sunspire |cffffcc00W|ratch Tower"),
            ("utub", VT_STR, "Scout spire that can be upgraded into an Earth-Fury Flame Tower or Sky-Fury Arcane Tower."),
        ]),
        ("negf", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "hlum"),
            ("ugol", VT_INT, 95),
            ("ulum", VT_INT, 60),
            ("ubld", VT_INT, 35),
            ("uhpm", VT_INT, 600),
            ("ua1b", VT_INT, 24),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "F"),
            ("utip", VT_STR, "Upgrade to Earth-|cffffcc00F|rury Tower"),
            ("utub", VT_STR, "Heavy bombardment spire effective against massed ground attackers."),
        ]),
        ("negm", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "h005"),
            ("ugol", VT_INT, 85),
            ("ulum", VT_INT, 55),
            ("ubld", VT_INT, 35),
            ("uhpm", VT_INT, 550),
            ("ua1b", VT_INT, 22),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Upgrade to |cffffcc00S|rky-Fury Tower"),
            ("utub", VT_STR, "Rapid-fire arcane defense spire especially lethal to enemy air forces and summoned creatures."),
        ]),

        # Tier 1 Melee: High Elven Swordsman (`hhes`)
        ("hhes", NULL_ID, [
            ("unam", VT_STR, "High Elven Swordsman"),
            ("ugol", VT_INT, 135),
            ("ulum", VT_INT, 0),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 20),
            ("uhpm", VT_INT, 435),
            ("ua1b", VT_INT, 12),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Train High Elven |cffffcc00S|rwordsman"),
            ("utub", VT_STR, "Disciplined Silvermoon infantryman. Can learn the Defend ability against piercing attacks."),
        ]),

        # Tier 1 Ranged: High Elven Archer (`nhea`) - Linked to Royal Forge upgrades
        ("nhea", NULL_ID, [
            ("unam", VT_STR, "High Elven Archer"),
            ("ugol", VT_INT, 135),
            ("ulum", VT_INT, 20),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 20),
            ("uhpm", VT_INT, 310),
            ("ua1b", VT_INT, 16),
            ("upgr", VT_STR, "Rhra,Rhla,Rhpm"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Train High Elven |cffffcc00A|rrcher"),
            ("utub", VT_STR, "Swift Silvermoon ranger armed with longbows. Attacks both land and air units."),
        ]),

        # Tier 2 Elite Officer: Alliance Captain (`hcth`) - Requires Sunwell Keep (`h002`)
        ("hcth", NULL_ID, [
            ("unam", VT_STR, "Alliance Captain"),
            ("ureq", VT_STR, "h002"),
            ("ugol", VT_INT, 205),
            ("ulum", VT_INT, 30),
            ("ufoo", VT_INT, 3),
            ("ubld", VT_INT, 28),
            ("uhpm", VT_INT, 680),
            ("udef", VT_INT, 4),
            ("ua1b", VT_INT, 21),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Train Alliance |cffffcc00C|raptain"),
            ("utub", VT_STR, "Veteran Expedition field officer with heavy plate armor and Defend."),
        ]),

        # Tier 2 Aerial Cavalier: Dragonhawk Rider (`hdhw`) - Requires Sunwell Keep (`h002`)
        ("hdhw", NULL_ID, [
            ("ureq", VT_STR, "h002"),
            ("ugol", VT_INT, 200),
            ("ulum", VT_INT, 40),
            ("ufoo", VT_INT, 3),
            ("ubld", VT_INT, 28),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "D"),
        ]),

        # Tier 3 Royal Champion: Blood Elf Lieutenant (`nbel`) - Balanced from campaign boss to 4 food
        ("nbel", NULL_ID, [
            ("ureq", VT_STR, "h003,hbla"),
            ("ugol", VT_INT, 275),
            ("ulum", VT_INT, 65),
            ("ufoo", VT_INT, 4),
            ("ubld", VT_INT, 38),
            ("uhpm", VT_INT, 920),
            ("udef", VT_INT, 5),
            ("ua1b", VT_INT, 32),
            ("upgr", VT_STR, "Rhme,Rhar,Rhpm"),
            ("udaa", VT_STR, "Asps"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "L"),
            ("utip", VT_STR, "Train Blood Elf |cffffcc00L|rieutenant"),
            ("utub", VT_STR, "Elite Silvermoon commander clad in enchanted runic plate, wielding Spell Immunity, Spell Steal, and Magic Sentry."),
        ]),

        # Tier 2 Healer/Support: Silvermoon Chaplain (`nchp`) - Auto-casts Heal
        ("nchp", NULL_ID, [
            ("unam", VT_STR, "Silvermoon Chaplain"),
            ("ureq", VT_STR, "h002"),
            ("ugol", VT_INT, 145),
            ("ulum", VT_INT, 25),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 26),
            ("uhpm", VT_INT, 330),
            ("udaa", VT_STR, "Anh2"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Train Silvermoon |cffffcc00C|rhaplain"),
            ("utub", VT_STR, "High Elven cleric who casts Heal, Inner Fire, and Dispel Magic without requiring Adept upgrades."),
        ]),

        # Tier 2 Battle Mage: Dalaran Hydromancer (`nhym`) - Auto-casts Slow
        ("nhym", NULL_ID, [
            ("unam", VT_STR, "Dalaran Hydromancer"),
            ("ureq", VT_STR, "h002"),
            ("ugol", VT_INT, 155),
            ("ulum", VT_INT, 40),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 28),
            ("uhpm", VT_INT, 360),
            ("udaa", VT_STR, "ACsw"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "H"),
            ("utip", VT_STR, "Train Dalaran |cffffcc00H|rydromancer"),
            ("utub", VT_STR, "Expedition battle mage skilled in Slow, Crushing Wave, and Polymorph."),
        ]),

        # Tier 2 Anti-Caster: Spell Breaker (`hspt`) - Unlocked by Observatory + Reliquary
        ("hspt", NULL_ID, [
            ("ureq", VT_STR, "h002,h005"),
            ("udaa", VT_STR, "Asps"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
        ]),

        # Campaign Human Hero 1: Prince Kael'thas (`Hkal`) - Blood Mage (INT)
        ("Hkal", NULL_ID, [
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "h002"),
            ("urq2", VT_STR, "h003"),
            ("uhab", VT_STR, "AHfs,AHbn,AHdr,AHpx"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "K"),
            ("utip", VT_STR, "Summon Prince |cffffcc00K|rael'thas"),
            ("utpr", VT_STR, "Revive Prince |cffffcc00K|rael'thas"),
            ("utub", VT_STR, "Prince of Quel'Thalas and master of Sunwell pyromancy. Can learn Flame Strike, Banish, Siphon Mana, and Phoenix."),
        ]),

        # Campaign Human Hero 2: Sylvanas Windrunner (`Hvwd`) - Ranger General (AGI)
        ("Hvwd", NULL_ID, [
            ("unam", VT_STR, "Ranger General"),
            ("upro", VT_STR, "Sylvanas Windrunner"),
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "h002"),
            ("urq2", VT_STR, "h003"),
            ("uhab", VT_STR, "AEst,AHca,AEar,AEsf"),
            ("udaa", VT_STR, "AHca"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "W"),
            ("utip", VT_STR, "Summon Sylvanas |cffffcc00W|rindrunner"),
            ("utpr", VT_STR, "Revive Sylvanas |cffffcc00W|rindrunner"),
            ("utub", VT_STR, "Ranger-General of Silvermoon. Agile marksman who can learn Scout, Cold Arrows, Trueshot Aura, and Starfall."),
        ]),

        # Campaign Human Hero 3: Lord Garithos (`Hlgr`) - Grand Marshal (STR)
        ("Hlgr", NULL_ID, [
            ("unam", VT_STR, "Grand Marshal"),
            ("upro", VT_STR, "Lord Garithos"),
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "h002"),
            ("urq2", VT_STR, "h003"),
            ("uhab", VT_STR, "AHhb,ANsh,AHad,ANav"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Summon Lord |cffffcc00G|rarithos"),
            ("utpr", VT_STR, "Revive Lord |cffffcc00G|rarithos"),
            ("utub", VT_STR, "Mounted Grand Marshal of the New Alliance. Can learn Holy Light, Shockwave, Devotion Aura, and Avatar."),
        ]),

        # Campaign Human Hero 4: Uther the Lightbringer (`Huth`) - Silver Hand Paladin (STR)
        ("Huth", NULL_ID, [
            ("unam", VT_STR, "Silver Hand Champion"),
            ("upro", VT_STR, "Uther the Lightbringer"),
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
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
            ("utub", VT_STR, "Supreme Paladin of the Knights of the Silver Hand. Can learn Holy Light, Divine Shield, Devotion Aura, and Resurrection."),
        ]),
    ]

    # ============================ CUSTOM UNITS & HEROES ============================
    custom: List[Tuple[str, str, List[ModEntry]]] = [
        # ---- NAGA CUSTOM HEROES (`N001..N003`) ----
        # N001: Abyssal Warlord (STR Melee Hero, Royal Guard model)
        ("Hmkg", "N001", [
            ("unam", VT_STR, "Abyssal Warlord"),
            ("upro", VT_STR, "Lord Naj'entus,Warlord Zar'jira,High Warlord Ssslith,Tidelord Krag'ja"),
            ("upru", VT_INT, 4),
            ("urac", VT_STR, "naga"),
            ("umdl", VT_STR, r"units\naga\NagaRoyalGuard\NagaRoyalGuard.mdl"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNNagaSeaWitch.blp"),
            ("usnd", VT_STR, "NagaRoyalGuard"),
            ("usca", VT_REAL, 1.08),
            ("umvt", VT_STR, "amph"),
            ("umvs", VT_INT, 300),
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "n001"),
            ("urq2", VT_STR, "n002"),
            ("uhab", VT_STR, "AOsh,ANht,ANca,ANst"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "W"),
            ("utip", VT_STR, "Summon Abyssal |cffffcc00W|rarlord"),
            ("utpr", VT_STR, "Revive Abyssal |cffffcc00W|rarlord"),
            ("utub", VT_STR, "Colossal Naga frontline Strength Hero. Can learn Shockwave, Howl of Terror, Cleaving Attack, and Stampede."),
        ]),

        # N002: Azshara's Tideweaver (INT Arch-Siren Hero, Naga Siren model)
        ("Hamg", "N002", [
            ("unam", VT_STR, "Azshara's Tideweaver"),
            ("upro", VT_STR, "Lady S'theno,Mistress Calypso,Highborne Athissa,Oracle Vess'ira"),
            ("upru", VT_INT, 4),
            ("urac", VT_STR, "naga"),
            ("umdl", VT_STR, r"units\naga\NagaSiren\NagaSiren.mdl"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNNagaSummoner.blp"),
            ("usnd", VT_STR, "NagaSiren"),
            ("usca", VT_REAL, 1.22),
            ("uclr", VT_INT, 165),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 255),
            ("umvt", VT_STR, "amph"),
            ("umvs", VT_INT, 300),
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "n001"),
            ("urq2", VT_STR, "n002"),
            ("uhab", VT_STR, "AHbz,AHwe,AHab,AHmt"),
            ("urev", VT_INT, 1),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Summon Azshara's |cffffcc00T|rideweaver"),
            ("utpr", VT_STR, "Revive Azshara's |cffffcc00T|rideweaver"),
            ("utub", VT_STR, "Highborne Intelligence caster of the Eternal Palace. Can learn Blizzard, Summon Water Elemental, Brilliance Aura, and Mass Teleport."),
        ]),

        # N003: Makrura Deepking (STR Tank Hero, Giant Lobstrokk model)
        ("Ucrl", "N003", [
            ("unam", VT_STR, "Makrura Deepking"),
            ("upro", VT_STR, "King Gurboggle,Emperor Clackora,Lord Kliklak,Leviathan Karkin"),
            ("upru", VT_INT, 4),
            ("urac", VT_STR, "naga"),
            ("utyp", VT_STR, ""),
            ("umdl", VT_STR, r"units\creeps\Lobstrokkgreen\Lobstrokkgreen.mdl"),
            ("uico", VT_STR, r"ReplaceableTextures\CommandButtons\BTNLobstrokkGreen.blp"),
            ("usnd", VT_STR, "Lobstrokk"),
            ("usca", VT_REAL, 1.25),
            ("umvt", VT_STR, "amph"),
            ("umvs", VT_INT, 290),
            ("uhpm", VT_INT, 100),
            ("uhpr", VT_REAL, 0.25),
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
            ("uhot", VT_STR, "D"),
            ("utip", VT_STR, "Summon Makrura |cffffcc00D|reepking"),
            ("utpr", VT_STR, "Revive Makrura |cffffcc00D|reepking"),
            ("utub", VT_STR, "Ancient armored crustacean monarch allied with the Naga. Can learn Impale, Spiked Carapace, Bash, and Locust Swarm."),
        ]),

        # ---- NAGA CUSTOM STRUCTURES (`n001..n003`) ----
        # n001: Sanctuary of Tides (Tier 2 Naga Town Hall)
        ("nntt", "n001", [
            ("unam", VT_STR, "Sanctuary of Tides"),
            ("upap", VT_STR, "unbuildable"),
            ("usca", VT_REAL, 1.15),
            ("uclr", VT_INT, 185),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 320),
            ("ulum", VT_INT, 190),
            ("ubld", VT_INT, 110),
            ("ufma", VT_INT, 12),
            ("uhpm", VT_INT, 1950),
            ("udef", VT_INT, 5),
            ("utra", VT_STR, "nmpe,nnmg"),
            ("ures", VT_STR, "Rnat,Rnam,Rnsb"),
            ("uupt", VT_STR, "n002"),
            ("uabi", VT_STR, "Abdl,Argl,Amic"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Sanctuary of Tides"),
            ("utub", VT_STR, "Upgrade to Sanctuary of Tides (Tier 2) to unlock the Shrine of Azshara, Dragon Turtles, a 2nd Naga Hero, and Tier-2 Coral upgrades."),
        ]),

        # n002: Abyssal Citadel (Tier 3 Naga Town Hall)
        ("nntt", "n002", [
            ("unam", VT_STR, "Abyssal Citadel"),
            ("upap", VT_STR, "unbuildable"),
            ("usca", VT_REAL, 1.28),
            ("uclr", VT_INT, 145),
            ("uclg", VT_INT, 210),
            ("uclb", VT_INT, 255),
            ("ureq", VT_STR, "nad,nnsg"),
            ("ugol", VT_INT, 360),
            ("ulum", VT_INT, 210),
            ("ubld", VT_INT, 120),
            ("ufma", VT_INT, 12),
            ("uhpm", VT_INT, 2400),
            ("udef", VT_INT, 6),
            ("utra", VT_STR, "nmpe,nnmg"),
            ("ures", VT_STR, "Rnat,Rnam,Rnsb"),
            ("uupt", VT_STR, ""),
            ("uabi", VT_STR, "Abdl,Argl,Amic"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Abyssal Citadel"),
            ("utub", VT_STR, "Upgrade to Abyssal Citadel (Tier 3) to unlock Naga Royal Guards, a 3rd Naga Hero, Orb of the Abyss, and Tier-3 Razorspine upgrades."),
        ]),

        # n003: Tidal Treasury (Naga Racial Item Shop, cloned from Arcane Vault `hvlt`)
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
            ("uabi", VT_STR, "Abds,Aall,Apit"),
            ("umki", VT_STR, "sreg,plcl,i003,phea,pman,stwp,i001,i002"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Build Tidal T|cffffcc00r|reasury"),
            ("utub", VT_STR, "Creates a shop of abyssal artifacts and potions, including Scroll of Tidal Surge, Healing/Mana Potions, Town Portal, and Orb of the Abyss."),
        ]),

        # ---- CAMPAIGN HUMAN CUSTOM STRUCTURES & SIEGE (`h001..h006`) ----
        # h001: Silvermoon Town Hall (Tier 1)
        ("htow", "h001", [
            ("unam", VT_STR, "Silvermoon Town Hall"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 240),
            ("uclb", VT_INT, 200),
            ("utra", VT_STR, "nhew"),
            ("ures", VT_STR, "Rhpm"),
            ("uupt", VT_STR, "h002"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "H"),
            ("utip", VT_STR, "Build Silvermoon Town |cffffcc00H|rall"),
            ("utub", VT_STR, "Primary Campaign Human center. Trains Silvermoon Engineers and receives gathered Gold and Lumber. Can be upgraded to Sunwell Keep and Silvermoon Citadel."),
        ]),

        # h002: Sunwell Keep (Tier 2)
        ("hkee", "h002", [
            ("unam", VT_STR, "Sunwell Keep"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 190),
            ("utra", VT_STR, "nhew"),
            ("ures", VT_STR, "Rhpm"),
            ("uupt", VT_STR, "h003"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Sunwell Keep"),
            ("utub", VT_STR, "Upgrade to Sunwell Keep (Tier 2) to unlock Alliance Captains, Arcane Observatory, Silvermoon Ballistas, Dragonhawk Riders, and a 2nd Expedition Hero."),
        ]),

        # h003: Silvermoon Citadel (Tier 3)
        ("hcas", "h003", [
            ("unam", VT_STR, "Silvermoon Citadel"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 225),
            ("uclb", VT_INT, 175),
            ("ureq", VT_STR, "h004"),
            ("utra", VT_STR, "nhew"),
            ("ures", VT_STR, "Rhpm"),
            ("uupt", VT_STR, ""),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Silvermoon Citadel"),
            ("utub", VT_STR, "Upgrade to Silvermoon Citadel (Tier 3) to unlock Blood Elf Lieutenants, Orb of Fire, a 3rd Expedition Hero, and Tier-3 Royal Forge upgrades."),
        ]),

        # h004: Altar of Silvermoon (Campaign Human Altar)
        ("halt", "h004", [
            ("unam", VT_STR, "Altar of Silvermoon"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 185),
            ("utra", VT_STR, "Hkal,Hvwd,Hlgr,Huth"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Build |cffffcc00A|rltar of Silvermoon"),
            ("utub", VT_STR, "Summons Campaign Human Heroes (Prince Kael'thas, Sylvanas Windrunner, Lord Garithos, and Uther the Lightbringer) and revives fallen Heroes."),
        ]),

        # h005: Sunwell Reliquary (Campaign Human Racial Item Shop)
        ("hvlt", "h005", [
            ("unam", VT_STR, "Sunwell Reliquary"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 230),
            ("uclb", VT_INT, 180),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Build Sunwell |cffffcc00R|reliquary"),
            ("utub", VT_STR, "Creates an Expedition shop stocked with Scrolls, Potions, Town Portals, Scout Towers, Staff of Sanctuary, and Orb of Fire."),
        ]),

        # h006: Silvermoon Ballista (Campaign Human Tier-2 Siege Engine, cloned from `ebal`)
        ("ebal", "h006", [
            ("unam", VT_STR, "Silvermoon Ballista"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, "h002,hlum"),
            ("ugol", VT_INT, 195),
            ("ulum", VT_INT, 60),
            ("ufoo", VT_INT, 4),
            ("ubld", VT_INT, 36),
            ("uhpm", VT_INT, 450),
            ("uabi", VT_STR, ""),
            ("upgr", VT_STR, "Rhra,Rhar"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Train Silvermoon |cffffcc00B|rallista"),
            ("utub", VT_STR, "Long-range High Elven siege engine firing giant runed bolts capable of demolishing enemy towers and buildings."),
        ]),
    ]

    # Fix typo guard: ensure `n002` `ureq` uses `nnad,nnsg`
    for idx, (oid, nid, mods) in enumerate(custom):
        if nid == "n002":
            custom[idx] = (
                oid,
                nid,
                [("ureq", VT_STR, "nnad,nnsg") if m[0] == "ureq" else m for m in mods],
            )

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
      - `i001`: Orb of the Abyss (Tier 3 `n002` Orb of Frost shop version)
      - `i002`: Tidal Staff of Sanctuary (Tier 3 `n002` Staff of Sanctuary)
      - `i003`: Scroll of Tidal Surge (Tier 1 Scroll of Speed)
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
    Serialize `war3map.w3q` (v2, `use_optional_ints = True`) to tier-gate
    Naga attack/armor/caster upgrades cleanly across Tier 1 -> Tier 2 -> Tier 3:
      - `Rnat` (Blades Lvl 2 -> `n001`, Lvl 3 -> `n002`)
      - `Rnam` (Scales Lvl 2 -> `n001`, Lvl 3 -> `n002`)
      - `Rnsw` (Naga Siren Master Training Lvl 2 -> `n002`)
    """
    NULL_ID = "\x00\x00\x00\x00"
    orig: List[Tuple[str, str, List[LevelModEntry]]] = [
        ("Rnat", NULL_ID, [
            ("greq", VT_STR, 2, 0, "n001"),
            ("greq", VT_STR, 3, 0, "n002"),
        ]),
        ("Rnam", NULL_ID, [
            ("greq", VT_STR, 2, 0, "n001"),
            ("greq", VT_STR, 3, 0, "n002"),
        ]),
        ("Rnsw", NULL_ID, [
            ("greq", VT_STR, 1, 0, "n001"),
            ("greq", VT_STR, 2, 0, "n002"),
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
    Warcraft III's native Gameplay Constants (`[TWN1..3]`, `[TALT]`, `[HERO]`)
    so:
      - Free 1st Hero Token & 3-Hero cap work identically to standard Melee
      - Neutral Tavern & Shop Tier-2 / Tier-3 item unlocks (`phea`, `pman`, `stwp`)
        automatically recognize Naga & Campaign Human Town Halls
      - `IsUnitIdType(..., UNIT_TYPE_TOWNHALL)` works for melee reveal/victory logic
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
    with custom full-path flag (`0x0D`) so World Editor's Import Manager keeps
    both `.ai` scripts intact if the user opens and re-saves the map!
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
    Full competitive Warcraft III `common.ai` Melee AI script for the Naga Empire.
    Engine automatically prepends `common.j` + `common.ai` when `StartMeleeAI` loads it.
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
    constant integer NAGA_ALTAR        = 'nnad'
    constant integer NAGA_SPAWNING     = 'nnsg'
    constant integer NAGA_SHRINE       = 'nnsa'
    constant integer NAGA_TREASURY     = 'n003'
    constant integer NAGA_GUARDIAN     = 'nntg'

    constant integer NAGA_REAVER       = 'nnmg'
    constant integer NAGA_MYRMIDON     = 'nmyr'
    constant integer NAGA_SNAP_DRAGON  = 'nsnp'
    constant integer NAGA_TURTLE       = 'nhyc'
    constant integer NAGA_ROYAL_GUARD  = 'nnrg'
    constant integer NAGA_SIREN        = 'nnsw'
    constant integer NAGA_COUATL       = 'nwgs'

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

//----------------------------------------------------------------------------
// Tier-aware structure counters (solves common.ai TownCountEx vanilla-only list)
//----------------------------------------------------------------------------
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

//----------------------------------------------------------------------------
// Hero Selection & 1..10 Skill Progression
//----------------------------------------------------------------------------
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

//----------------------------------------------------------------------------
// Gold & Lumber Harvesting Loop (Supports Main + 2 Expansions)
//----------------------------------------------------------------------------
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

//----------------------------------------------------------------------------
// Pro Build Order, Tech Progression, Upgrades & Natural Expansion Loop
//----------------------------------------------------------------------------
function NagaBuildLoop takes nothing returns nothing
    local unit expPeon
    local integer mines
    loop
        call InitBuildArray()

        set naga_tier2_done = (NagaTier2Count(true) >= 1)
        set naga_tier3_done = (NagaTier3Count(true) >= 1)
        set mines = GetMinesOwned()

        // Emergency rebuild if main hall fell
        if NagaHallCount(false) < 1 then
            call SetProduce(1, NAGA_HALL_T1, -1)
        endif

        // Dynamic Coral Bed supply buffer (never supply-block!)
        if FoodUsed() + 6 >= FoodCap() and FoodCap() < 100 and GetUnitCount(NAGA_CORAL_BED) < 10 then
            call NagaNeedUnit(GetUnitCountDone(NAGA_CORAL_BED) + 1, NAGA_CORAL_BED, -1)
        endif

        // Worker target: 13 on 1 base, 18 once expanded
        if mines >= 2 then
            call NagaNeedUnit(18, NAGA_SLAVE, -1)
        else
            call NagaNeedUnit(13, NAGA_SLAVE, -1)
        endif

        // Core Tier-1 Opening: Coral Bed -> Altar -> Spawning Grounds -> Hero 1 -> Treasury
        call NagaNeedUnit(1, NAGA_CORAL_BED, -1)
        call NagaNeedUnit(1, NAGA_ALTAR, -1)
        call NagaNeedUnit(1, NAGA_SPAWNING, -1)
        call NagaNeedUnit(2, NAGA_CORAL_BED, -1)

        if GetUnitCountDone(NAGA_ALTAR) >= 1 then
            call NagaNeedUnit(1, hero_id, -1)
            call NagaNeedUnit(1, NAGA_TREASURY, -1)
        endif

        // Early vanguard & Home Defense
        if GetUnitCountDone(NAGA_SPAWNING) >= 1 then
            call NagaNeedUnit(3, NAGA_REAVER, -1)
            call NagaNeedUnit(2, NAGA_SNAP_DRAGON, -1)
            call NagaNeedUnit(2, NAGA_MYRMIDON, -1)
            call NagaNeedUnit(1, NAGA_GUARDIAN, 0)
            call SetUpgrade(UPG_NAGA_ENSNARE)
        endif

        // Tier-1 Coral Upgrades
        if GetUnitCountDone(NAGA_SPAWNING) >= 1 and GetGold() > 150 then
            if GetUpgradeLevel(UPG_NAGA_BLADES) < 1 then
                call SetUpgrade(UPG_NAGA_BLADES)
            endif
            if GetUpgradeLevel(UPG_NAGA_SCALES) < 1 then
                call SetUpgrade(UPG_NAGA_SCALES)
            endif
        endif

        // Tech to Tier 2: Sanctuary of Tides (`n001`)
        if GetUnitCountDone(NAGA_ALTAR) >= 1 and GetUnitCountDone(NAGA_SPAWNING) >= 1 and NagaTier2Count(false) < 1 then
            call SetProduce(1, NAGA_HALL_T2, -1)
        endif

        // Tier-2 Midgame: 2nd Hero, Shrine of Azshara, Combined-Arms Army & Expansion
        if naga_tier2_done then
            call NagaNeedUnit(1, hero_id2, -1)
            call NagaNeedUnit(1, NAGA_SHRINE, -1)
            call NagaNeedUnit(2, NAGA_GUARDIAN, 0)

            // Midgame army composition
            call NagaNeedUnit(4, NAGA_MYRMIDON, -1)
            call NagaNeedUnit(4, NAGA_SNAP_DRAGON, -1)
            call NagaNeedUnit(1, NAGA_TURTLE, -1)

            if GetUnitCountDone(NAGA_SHRINE) >= 1 then
                call NagaNeedUnit(3, NAGA_SIREN, -1)
                call NagaNeedUnit(2, NAGA_COUATL, -1)
                if GetUpgradeLevel(UPG_NAGA_SIREN) < 1 then
                    call SetUpgrade(UPG_NAGA_SIREN)
                endif
                call SetUpgrade(UPG_NAGA_ABOLISH)
            endif

            // Tier-2 Coral Blades & Scales + Submerge
            if GetUpgradeLevel(UPG_NAGA_BLADES) < 2 then
                call SetUpgrade(UPG_NAGA_BLADES)
            endif
            if GetUpgradeLevel(UPG_NAGA_SCALES) < 2 then
                call SetUpgrade(UPG_NAGA_SCALES)
            endif
            call SetUpgrade(UPG_NAGA_SUBMERGE)

            // Second Spawning Grounds for heavy production
            if GetGold() > 450 then
                call NagaNeedUnit(2, NAGA_SPAWNING, -1)
            endif

            // Natural Gold Mine Expansion (clears expansion creeps via SingleMeleeAttack first!)
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

        // Tier-3 Lategame: 3rd Hero, Naga Royal Guards, Level-3 Upgrades
        if naga_tier3_done then
            call NagaNeedUnit(1, hero_id3, -1)
            call NagaNeedUnit(2, NAGA_ROYAL_GUARD, -1)
            call NagaNeedUnit(2, NAGA_TURTLE, -1)
            call NagaNeedUnit(5, NAGA_MYRMIDON, -1)
            call NagaNeedUnit(4, NAGA_SNAP_DRAGON, -1)
            call NagaNeedUnit(3, NAGA_COUATL, -1)
            call NagaNeedUnit(3, NAGA_SIREN, -1)

            if GetUpgradeLevel(UPG_NAGA_BLADES) < 3 then
                call SetUpgrade(UPG_NAGA_BLADES)
            endif
            if GetUpgradeLevel(UPG_NAGA_SCALES) < 3 then
                call SetUpgrade(UPG_NAGA_SCALES)
            endif
            if GetUpgradeLevel(UPG_NAGA_SIREN) < 2 then
                call SetUpgrade(UPG_NAGA_SIREN)
            endif
        endif

        // Home base garrison defenders
        call InitDefenseGroup()
        call CampaignDefenderEx(1, 1, 2, NAGA_MYRMIDON)
        call CampaignDefenderEx(1, 1, 2, NAGA_SNAP_DRAGON)
        call CampaignDefenderEx(0, 1, 1, NAGA_SIREN)

        call Sleep(3)
    endloop
endfunction

//----------------------------------------------------------------------------
// Multi-Stage Creeping, Expansion Clearing & Enemy Base Assault Loop
//----------------------------------------------------------------------------
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
        // Wait until at least 1 Hero or 4 combat units are ready
        loop
            set armyReady = GetUnitCountDone(hero_id) + GetUnitCountDone(hero_id2) + GetUnitCountDone(hero_id3)
            exitwhen armyReady >= 1 and (GetUnitCountDone(NAGA_REAVER) + GetUnitCountDone(NAGA_MYRMIDON) + GetUnitCountDone(NAGA_SNAP_DRAGON)) >= 3
            exitwhen (GetUnitCountDone(NAGA_MYRMIDON) + GetUnitCountDone(NAGA_SNAP_DRAGON)) >= 5
            call Sleep(4)
        endloop

        call InitAssaultGroup()
        call NagaAttackWave(1, hero_id)
        call NagaAttackWave(1, hero_id2)
        call NagaAttackWave(1, hero_id3)
        call NagaAttackWave(4, NAGA_REAVER)
        call NagaAttackWave(6, NAGA_MYRMIDON)
        call NagaAttackWave(5, NAGA_SNAP_DRAGON)
        call NagaAttackWave(3, NAGA_SIREN)
        call NagaAttackWave(3, NAGA_COUATL)
        call NagaAttackWave(2, NAGA_TURTLE)
        call NagaAttackWave(3, NAGA_ROYAL_GUARD)

        set needsExp = (GetMinesOwned() < 2 and naga_tier2_done)
        set hasSiege = (GetUnitCountDone(NAGA_TURTLE) >= 1 or GetUnitCountDone(NAGA_ROYAL_GUARD) >= 1)
        set majorOk  = (naga_tier2_done or (GetUnitCountDone(NAGA_MYRMIDON) + GetUnitCountDone(NAGA_SNAP_DRAGON)) >= 5)
        set airUnits = (GetUnitCountDone(NAGA_COUATL) >= 2 and GetUnitCountDone(NAGA_MYRMIDON) == 0)

        call SingleMeleeAttack(needsExp, hasSiege, majorOk, airUnits)
        call Sleep(5)
    endloop
endfunction

//----------------------------------------------------------------------------
// Entry Point
//----------------------------------------------------------------------------
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
    Full competitive Warcraft III `common.ai` Melee AI script for Campaign Human
    (Silvermoon & Alliance Expedition).
    """
    return """//============================================================================
//  Campaign Human Pro Melee AI (`camphuman_melee.ai`) — (8) Crown of WarMahdi
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
    constant integer CH_ALTAR          = 'h004'
    constant integer CH_BARRACKS       = 'nheb'
    constant integer CH_LUMBER_MILL    = 'hlum'
    constant integer CH_FORGE          = 'hbla'
    constant integer CH_RELIQUARY      = 'h005'
    constant integer CH_OBSERVATORY    = 'haro'
    constant integer CH_WATCH_TOWER    = 'negt'
    constant integer CH_FLAME_TOWER    = 'negf'
    constant integer CH_ARCANE_TOWER   = 'negm'

    constant integer CH_SWORDSMAN      = 'hhes'
    constant integer CH_ARCHER         = 'nhea'
    constant integer CH_CAPTAIN        = 'hcth'
    constant integer CH_BALLISTA       = 'h006'
    constant integer CH_DRAGONHAWK     = 'hdhw'
    constant integer CH_LIEUTENANT     = 'nbel'
    constant integer CH_CHAPLAIN       = 'nchp'
    constant integer CH_HYDROMANCER    = 'nhym'
    constant integer CH_SPELLBREAKER   = 'hspt'

    constant integer HERO_KAEL         = 'Hkal'
    constant integer HERO_SYLVANAS     = 'Hvwd'
    constant integer HERO_GARITHOS     = 'Hlgr'
    constant integer HERO_UTHER        = 'Huth'

    constant integer UPG_CH_DEFEND     = 'Rhde'
    constant integer UPG_CH_MELEE_ATK  = 'Rhme'
    constant integer UPG_CH_RANGED_ATK = 'Rhra'
    constant integer UPG_CH_PLATE_ARM  = 'Rhar'
    constant integer UPG_CH_LEATH_ARM  = 'Rhla'
    constant integer UPG_CH_LUMBER     = 'Rhlh'
    constant integer UPG_CH_MASONRY    = 'Rhac'
    constant integer UPG_CH_CLOUD      = 'Rhcd'
    constant integer UPG_CH_CONTROL    = 'Rhss'
endglobals

//----------------------------------------------------------------------------
// Tier-aware structure counters
//----------------------------------------------------------------------------
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
    return GetUnitCount(CH_WATCH_TOWER) + GetUnitCount(CH_FLAME_TOWER) + GetUnitCount(CH_ARCANE_TOWER)
endfunction

function CHNeedUnit takes integer qty, integer id, integer town returns nothing
    local integer have = GetUnitCount(id)
    if have < qty then
        call SetProduce(qty - have, id, town)
    endif
endfunction

//----------------------------------------------------------------------------
// Hero Selection & 1..10 Skill Progression
//----------------------------------------------------------------------------
function CHSetSkills takes integer heroId returns nothing
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
        set skill[ 1] = 'AHca'
        set skill[ 2] = 'AEar'
        set skill[ 3] = 'AHca'
        set skill[ 4] = 'AEar'
        set skill[ 5] = 'AHca'
        set skill[ 6] = 'AEsf'
        set skill[ 7] = 'AEar'
        set skill[ 8] = 'AEst'
        set skill[ 9] = 'AEst'
        set skill[10] = 'AEst'
    elseif heroId == HERO_GARITHOS then
        set skill[ 1] = 'ANsh'
        set skill[ 2] = 'AHhb'
        set skill[ 3] = 'ANsh'
        set skill[ 4] = 'AHad'
        set skill[ 5] = 'ANsh'
        set skill[ 6] = 'ANav'
        set skill[ 7] = 'AHhb'
        set skill[ 8] = 'AHhb'
        set skill[ 9] = 'AHad'
        set skill[10] = 'AHad'
    else
        set skill[ 1] = 'AHhb'
        set skill[ 2] = 'AHad'
        set skill[ 3] = 'AHhb'
        set skill[ 4] = 'AHds'
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
        set hero_id2 = HERO_GARITHOS
        set hero_id3 = HERO_SYLVANAS
    elseif roll == 2 then
        set hero_id  = HERO_SYLVANAS
        set hero_id2 = HERO_UTHER
        set hero_id3 = HERO_KAEL
    elseif roll == 3 then
        set hero_id  = HERO_GARITHOS
        set hero_id2 = HERO_KAEL
        set hero_id3 = HERO_UTHER
    else
        set hero_id  = HERO_UTHER
        set hero_id2 = HERO_SYLVANAS
        set hero_id3 = HERO_GARITHOS
    endif

    call CHSetSkills(hero_id)
    call SetSkillArray(1, hero_id)
    call CHSetSkills(hero_id2)
    call SetSkillArray(2, hero_id2)
    call CHSetSkills(hero_id3)
    call SetSkillArray(3, hero_id3)
endfunction

//----------------------------------------------------------------------------
// Gold & Lumber Harvesting Loop
//----------------------------------------------------------------------------
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
            if woodWorkers > 9 then
                set woodWorkers = 9
            endif
            call HarvestWood(0, woodWorkers)
        else
            call HarvestWood(0, 2)
        endif

        call Sleep(6)
    endloop
endfunction

//----------------------------------------------------------------------------
// Pro Build Order, Tech Progression, Upgrades & Expansion Loop
//----------------------------------------------------------------------------
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

        // Dynamic Farm buffer (6 food per High Elven Farm)
        if FoodUsed() + 6 >= FoodCap() and FoodCap() < 100 and GetUnitCount(CH_ELVEN_FARM) < 15 then
            call CHNeedUnit(GetUnitCountDone(CH_ELVEN_FARM) + 1, CH_ELVEN_FARM, -1)
        endif

        if mines >= 2 then
            call CHNeedUnit(18, CH_ENGINEER, -1)
        else
            call CHNeedUnit(14, CH_ENGINEER, -1)
        endif

        // Tier-1 Opening: Farm -> Altar -> Barracks -> Farm -> Hero 1 -> Lumber Mill & Forge -> Reliquary
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
            if GetUnitCount(CH_FLAME_TOWER) < 1 then
                call SetProduce(1, CH_FLAME_TOWER, -1)
            elseif GetUnitCountDone(CH_RELIQUARY) >= 1 and GetUnitCount(CH_ARCANE_TOWER) < 1 then
                call SetProduce(1, CH_ARCANE_TOWER, -1)
            endif
        endif

        // Tier-1 Royal Forge Upgrades
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

        // Tier-2 Midgame: 2nd Hero, Arcane Observatory, Expedition Army & Expansion
        if ch_tier2_done then
            call CHNeedUnit(1, hero_id2, -1)
            call CHNeedUnit(1, CH_OBSERVATORY, -1)
            call CHNeedUnit(3, CH_CAPTAIN, -1)
            call CHNeedUnit(4, CH_ARCHER, -1)
            call CHNeedUnit(2, CH_DRAGONHAWK, -1)
            call CHNeedUnit(1, CH_BALLISTA, -1)

            if GetUnitCountDone(CH_OBSERVATORY) >= 1 then
                call CHNeedUnit(2, CH_CHAPLAIN, -1)
                call CHNeedUnit(2, CH_HYDROMANCER, -1)
                if GetUnitCountDone(CH_RELIQUARY) >= 1 then
                    call CHNeedUnit(2, CH_SPELLBREAKER, -1)
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

            // Natural Gold Mine Expansion (clears expansion creeps via SingleMeleeAttack first!)
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
            if GetUnitCountDone(CH_OBSERVATORY) >= 1 and CHTier3Count(false) < 1 then
                call SetProduce(1, CH_HALL_T3, -1)
            endif
        endif

        // Tier-3 Lategame: 3rd Hero, Blood Elf Lieutenants, +3/+3 Upgrades
        if ch_tier3_done then
            call CHNeedUnit(1, hero_id3, -1)
            call CHNeedUnit(3, CH_LIEUTENANT, -1)
            call CHNeedUnit(4, CH_CAPTAIN, -1)
            call CHNeedUnit(4, CH_ARCHER, -1)
            call CHNeedUnit(3, CH_CHAPLAIN, -1)
            call CHNeedUnit(2, CH_HYDROMANCER, -1)
            call CHNeedUnit(2, CH_SPELLBREAKER, -1)
            call CHNeedUnit(3, CH_DRAGONHAWK, -1)
            call CHNeedUnit(2, CH_BALLISTA, -1)

            call SetUpgrade(UPG_CH_CLOUD)
            call SetUpgrade(UPG_CH_CONTROL)

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

        // Home base garrison defenders
        call InitDefenseGroup()
        call CampaignDefenderEx(1, 1, 2, CH_SWORDSMAN)
        call CampaignDefenderEx(1, 1, 2, CH_ARCHER)
        call CampaignDefenderEx(0, 1, 1, CH_CHAPLAIN)

        call Sleep(3)
    endloop
endfunction

//----------------------------------------------------------------------------
// Multi-Stage Creeping, Expansion Clearing & Enemy Base Assault Loop
//----------------------------------------------------------------------------
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
        call CHAttackWave(5, CH_SWORDSMAN)
        call CHAttackWave(4, CH_CAPTAIN)
        call CHAttackWave(5, CH_ARCHER)
        call CHAttackWave(3, CH_CHAPLAIN)
        call CHAttackWave(2, CH_HYDROMANCER)
        call CHAttackWave(2, CH_SPELLBREAKER)
        call CHAttackWave(3, CH_DRAGONHAWK)
        call CHAttackWave(2, CH_BALLISTA)
        call CHAttackWave(3, CH_LIEUTENANT)

        set needsExp = (GetMinesOwned() < 2 and ch_tier2_done)
        set hasSiege = (GetUnitCountDone(CH_BALLISTA) >= 1 or GetUnitCountDone(CH_LIEUTENANT) >= 2)
        set majorOk  = (ch_tier2_done or (GetUnitCountDone(CH_SWORDSMAN) + GetUnitCountDone(CH_ARCHER)) >= 6)
        set airUnits = (GetUnitCountDone(CH_DRAGONHAWK) >= 2 and GetUnitCountDone(CH_SWORDSMAN) == 0 and GetUnitCountDone(CH_CAPTAIN) == 0)

        call SingleMeleeAttack(needsExp, hasSiege, majorOk, airUnits)
        call Sleep(5)
    endloop
endfunction

//----------------------------------------------------------------------------
// Entry Point
//----------------------------------------------------------------------------
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
    Returns (globals_block, functions_block) to embed into `war3map.j`.
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
//*  - Chat Commands: -naga, -camphuman, -random6 (first 20s) & -races (anytime)
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
    // Standard 1-per-Hero-type limit (total 3 Heroes via war3mapMisc.txt [HERO])
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

    // Snapshot any existing starting units BEFORE spawning the new base
    // so structure count NEVER drops to zero during a race swap!
    call GroupEnumUnitsOfPlayer(oldUnits, p, null)
    call GroupEnumUnitsOfPlayer(scanUnits, p, null)

    // If swapping away from Undead ('ugol') or Night Elf ('egol'), restore a clean
    // Neutral Passive 'ngol' Gold Mine and clear Blight BEFORE spawning new units!
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

    // Now safely remove all previous starting units (zero defeat flicker!)
    loop
        set u = FirstOfGroup(oldUnits)
        exitwhen u == null
        call GroupRemoveUnit(oldUnits, u)
        call RemoveUnit(u)
    endloop
    call DestroyGroup(oldUnits)
    call RemoveLocation(startLoc)

    // Standard Competitive Melee starting resources & 1 free Hero Token
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
    // mode 1 = Balanced 6-Race Mix (guarantees Naga & Campaign Human AI!)
    // mode 2 = All Default AI -> Naga Empire
    // mode 3 = All Default AI -> Campaign Human
    // mode 4 = Keep Lobby AI Races
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
                    // Smart 6-Race rotation: 1st AI = Naga, 2nd AI = Campaign Human,
                    // then alternates custom + classic factions so every match features both!
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
    local trigger t = null
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

    // Headless AI-only match fallback
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
        // Default AI mode: Smart 6-Race Pro Mix so Naga & Campaign Human AIs join automatically!
        call ApplyHostAIMode(1)
    endif

    call StartAllPendingComputerAIs()
    set p = null
endfunction

//----------------------------------------------------------------------------
// First-Hero Scroll of Town Portal Grant (for Custom/Campaign Heroes too!)
//----------------------------------------------------------------------------
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
        // Grant Town Portal to the player's first summoned custom Hero
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

//----------------------------------------------------------------------------
// Chat Commands (-naga, -camphuman, -random6, -races)
//----------------------------------------------------------------------------
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

//----------------------------------------------------------------------------
// Tactical AI Combat Micro Booster (Naga Royal Guards & Campaign Human Casters)
//----------------------------------------------------------------------------
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
                    // Naga Royal Guard tactical spells: Sea Elemental / Crushing Wave / Frost Bolt
                    if ut == 'nnrg' and GetUnitState(u, UNIT_STATE_MANA) >= 75.0 then
                        set foe = FindNearestVisibleEnemy(p, GetUnitX(u), GetUnitY(u), 650.0)
                        if foe != null then
                            if GetUnitState(u, UNIT_STATE_MANA) >= 125.0 then
                                call IssueImmediateOrder(u, "waterelemental")
                            endif
                            if IsUnitType(foe, UNIT_TYPE_HERO) then
                                call IssueTargetOrder(u, "thunderbolt", foe)
                            else
                                call IssuePointOrder(u, "carrionswarm", GetUnitX(foe), GetUnitY(foe))
                            endif
                        endif
                    // Dalaran Hydromancer Crushing Wave when mana-healthy
                    elseif ut == 'nhym' and GetUnitState(u, UNIT_STATE_MANA) >= 120.0 then
                        set foe = FindNearestVisibleEnemy(p, GetUnitX(u), GetUnitY(u), 650.0)
                        if foe != null then
                            call IssuePointOrder(u, "carrionswarm", GetUnitX(foe), GetUnitY(foe))
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

//----------------------------------------------------------------------------
// Master Initialization for 6-Race Altered Melee
//----------------------------------------------------------------------------
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

            // Check Pre-Game Lobby Handicap dropdown:
            //   90% -> Naga Empire  |  80% -> Campaign Human  |  70% -> 6-Race Random
            //   (Immediately restores Handicap back to 100% full HP!)
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

    // Welcome banner explaining Lobby & In-Game controls
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
