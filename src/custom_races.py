#!/usr/bin/env python3
"""
Custom Playable Races, Object Modifications & Pro-Level Melee AI Generator
for `(8) Crown of WarMahdi` v7 (Warcraft III TFT 1.26a/1.27b & Reforged).

Implements four ladder-bounded custom empires alongside the 4 classic Warcraft III races:
  5. Abyssal Tideborn / Naga (`RACE_NAGA = 5`, now includes Illidan Stormrage)
  6. Sunfury Imperium / Campaign Human (`RACE_CAMPHUMAN = 6`)
  7. Voidborn Legion
  8. Runeforged Bastion

Retained Engineering, Art & Balance Guarantees:
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
  - Ten original hero portraits are shipped as icon-only paletted BLP pairs; all
    other units/buildings inherit or receive verified native Warcraft III icons.
  - Naga structures use native Naga architecture; Sunfury halls use the native
    Human Town Hall model with inherited tier animations. UI/cursor/VFX BLPs stay truecolor.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path
from typing import Any, Iterable, List, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.custom_factions_v3 import (
    build_ability_modifications,
    build_voidborn_and_runeforged_units,
    generate_runeforged_ai_script,
    generate_voidborn_ai_script,
    serialize_war3map_skin,
)
from src.custom_gameplay import generate_custom_gameplay_jass

# Variable types in WC3 Object Editor binary tables (w3u / w3t / w3q)
VT_INT = 0
VT_REAL = 1
VT_UNREAL = 2
VT_STR = 3

ModEntry = Tuple[str, int, Any]
LevelModEntry = Tuple[str, int, int, int, Any]

# New high-resolution portrait BLPs for ten playable heroes. The remaining six
# explicitly use the matching Blizzard-native campaign/hero portrait.
HERO_ICON_OVERRIDES = {
    "Hvsh": "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_Hvsh.blp",
    "N004": "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_N004.blp",
    "N001": "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_N001.blp",
    "N002": "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_N002.blp",
    "Hkal": "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_Hkal.blp",
    "Hvwd": "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_Hvwd.blp",
    "Hlgr": "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_Hlgr.blp",
    "Huth": "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_Huth.blp",
    "V001": "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_V001.blp",
    "V002": "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_V002.blp",
    "V003": "ReplaceableTextures\\CommandButtons\\BTNDranaiAkama.blp",
    "V004": "ReplaceableTextures\\CommandButtons\\BTNHeroDreadLord.blp",
    "T001": "ReplaceableTextures\\CommandButtons\\BTNHeroMountainKing.blp",
    "T002": "ReplaceableTextures\\CommandButtons\\BTNHeroAvatarOfFlame.blp",
    "T003": "ReplaceableTextures\\CommandButtons\\BTNHeroTinker.blp",
    "T004": "ReplaceableTextures\\CommandButtons\\BTNHeroArchMage.blp",
}


def _stock_button(stem: str) -> str:
    return "ReplaceableTextures\\CommandButtons\\" + stem + ".blp"


# Custom models now use native buttons depicting those models/building roles;
# unchanged stock units and buildings inherit their original Warcraft III art.
OBJECT_ICON_OVERRIDES = {
    "n003": _stock_button("BTNShrineOfAszhara"),
    "n004": _stock_button("BTNAltarOfDepths"),
    "n005": _stock_button("BTNSpawningGrounds"),
    "v001": _stock_button("BTNNecropolis"),
    "v002": _stock_button("BTNDarkPortal"),
    "v003": _stock_button("BTNDarkPortal"),
    "v004": _stock_button("BTNNerubianZiggurat"),
    "v005": _stock_button("BTNDemonGate"),
    "v006": _stock_button("BTNSacrificialPit"),
    "v007": _stock_button("BTNBookOfSummoning"),
    "v008": _stock_button("BTNTombOfRelics"),
    "v009": _stock_button("BTNDalaranGuardTower"),
    "v010": _stock_button("BTNVoidWalker"),
    "v011": _stock_button("BTNFelGuardBlue"),
    "v012": _stock_button("BTNFacelessOne"),
    "v013": _stock_button("BTNpurpleDragonSpawn"),
    "v014": _stock_button("BTNEredarWarlockPurple"),
    "v015": _stock_button("BTNNetherDragon"),
    "v016": _stock_button("BTNInfernalFlameCannon"),
    "v017": _stock_button("BTNDoomGuard"),
    "v018": _stock_button("BTNTempleOfTheDamned"),
    "v019": _stock_button("BTNBlackDragonRoost"),
    "t001": _stock_button("BTNAmmoDump"),
    "t002": _stock_button("BTNArcaneObservatory"),
    "t003": _stock_button("BTNWaygate"),
    "t004": _stock_button("BTNPowerGenerator"),
    "t005": _stock_button("BTNPocketFactory"),
    "t007": _stock_button("BTNAltarOfStorms"),
    "t008": _stock_button("BTNMerchant"),
    "t009": _stock_button("BTNRockTower"),
    "t010": _stock_button("BTNClockWerkGoblin"),
    "t011": _stock_button("BTNJunkGolem"),
    "t012": _stock_button("BTNMarine"),
    "t013": _stock_button("BTNArmorGolem"),
    "t014": _stock_button("BTNHeroTinker"),
    "t017": _stock_button("BTNRockGolem"),
    "t018": _stock_button("BTNFountainOfLife"),
    "t019": _stock_button("BTNGoblinShipyard"),
}

# Keep custom Naga structures in their race-native model family. Sunfury town
# tiers use the native Human Town Hall model and its inherited tier-up animations.
OBJECT_MODEL_OVERRIDES = {
    "n003": r"buildings\naga\ShrineOfAshjara\ShrineOfAshjara.mdl",
    "n004": r"buildings\naga\AltarOfDepths\AltarOfDepths.mdl",
    "n005": r"buildings\naga\SpawningGrounds\SpawningGrounds.mdl",
    "h001": r"buildings\human\TownHall\TownHall.mdl",
    "h002": r"buildings\human\TownHall\TownHall.mdl",
    "h003": r"buildings\human\TownHall\TownHall.mdl",
    "h004": r"buildings\human\AltarOfKings\AltarOfKings.mdl",
    "h010": r"buildings\human\Blacksmith\Blacksmith.mdl",
}


def _normalize_object_icons(
    objects: List[Tuple[str, str, List[Any]]],
) -> List[Tuple[str, str, List[Any]]]:
    """Replace generated glyph buttons while preserving all faction model overrides."""
    normalized: List[Tuple[str, str, List[Any]]] = []
    null_id = "\\x00\\x00\\x00\\x00"
    for original_id, new_id, mods in objects:
        effective_id = new_id if new_id != null_id else original_id
        # Drop obsolete generated icon overrides, but do not erase the real/custom
        # models already assigned to Voidborn, Runeforged, Naga or Sunfury objects.
        clean_mods = [mod for mod in mods if mod[0] != "uico"]
        if effective_id in OBJECT_MODEL_OVERRIDES:
            clean_mods = [mod for mod in clean_mods if mod[0] != "umdl"]
            clean_mods.append(("umdl", VT_STR, OBJECT_MODEL_OVERRIDES[effective_id]))
        icon_path = HERO_ICON_OVERRIDES.get(effective_id) or OBJECT_ICON_OVERRIDES.get(effective_id)
        if icon_path:
            clean_mods.append(("uico", VT_STR, icon_path))
        normalized.append((original_id, new_id, clean_mods))
    return normalized


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
          * `nnad` Altar of the Depths: summons `Hvsh`, Illidan (`N004`), `N001`, and `N002`.
          * `n003` Tidal Treasury (Shop): sells scrolls, potions, TP, Orb of the Abyss.
          * `nntg` Tidal Guardian (Tower, req `nnsg`): `600 HP`, `25` Pierce damage.
          * `nnsg` Spawning Grounds (Barracks): trains `nnmg` Mur'gul Reaver (T1),
            `nsnp` Snap Dragon (T1), `nmyr` Naga Myrmidon (T2 req `n001`);
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
        ("hkee", NULL_ID, [("udep", VT_STR, "h002,v002,t002")]),
        ("hcas", NULL_ID, [("udep", VT_STR, "h003,v003,t003")]),
        ("halt", NULL_ID, [("udep", VT_STR, "h004,v007,t007")]),
        ("hvlt", NULL_ID, [("udep", VT_STR, "h005,v008,t008")]),
        ("hbar", NULL_ID, [("udep", VT_STR, "h007,v005,t005")]),
        ("harm", NULL_ID, [("udep", VT_STR, "h008,v019,t019")]),
        ("hgra", NULL_ID, [("udep", VT_STR, "h009")]),

        # Sunfury's campaign units use faction-owned race portraits, not stock Human icons.

        # ======================================================================
        # NAGA EMPIRE — ORIGINAL UNITS, BUILDINGS & HERO (`Hvsh`)
        # ======================================================================

        # Worker: Mur'gul Slave (`nmpe`) — Exact melee worker stats (75g, 230 HP, +0.25 HP/s)
        # Build Grid (9 structures, clean 4x3):
        #   Row 0: (0,0) nntt | (1,0) nnfm | (2,0) nnsg | (3,0) n004
        #   Row 1: (0,1) nnad | (1,1) n003 | (2,1) nntg
        #   Row 2: (0,2) nnsa | (1,2) n005
        ("nmpe", NULL_ID, [
            ("urac", VT_STR, "naga"),
            ("utyp", VT_STR, "Peon"),
            ("uabi", VT_STR, "Ahar,Ahrp,Aneu,Aihn"),
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

        # Altar: Altar of the Depths (`nnad`) — Summons 4 Naga Heroes (Vashj, Illidan, Naj'entus, Athissa!)
        ("nnad", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ugol", VT_INT, 180),
            ("ulum", VT_INT, 50),
            ("ubld", VT_INT, 58),
            ("uhpm", VT_INT, 950),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "Hvsh,N004,N001,N002"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Build |cffffcc00A|rltar of the Depths"),
            ("utub", VT_STR, "Summons Naga Heroes (Empress Lady Vashj, Illidan Stormrage, Leviathan Warlord Naj'entus, and Nazjatar Tideweaver Athissa) and revives fallen Heroes."),
        ]),

        # Defensive Tower: Tidal Guardian (`nntg`) — Requires Spawning Grounds (`nnsg`), 29.0 Pierce DPS
        ("nntg", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "nnsg"),
            ("ugol", VT_INT, 135),
            ("ulum", VT_INT, 80),
            ("ubld", VT_INT, 45),
            ("uhpm", VT_INT, 600),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "pierce"),
            ("ua1b", VT_INT, 25),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 7),
            ("ua1c", VT_UNREAL, 1.00),
            ("ua1r", VT_INT, 750),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "Abds,Adts"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "Build Tidal G|cffffcc00u|rardian"),
            ("utub", VT_STR, "Defensive coral spire that hurls abyssal lightning bolts at ground and air attackers. Has Magic Sentry to reveal invisible enemies."),
        ]),

        # Caster & Flyer Sanctum: Shrine of Azshara (`nnsa`) — Requires Tier 2 (`n001`)
        ("nnsa", NULL_ID, [
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 150),
            ("ulum", VT_INT, 140),
            ("ubld", VT_INT, 58),
            ("uhpm", VT_INT, 1050),
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

        # Tier 1 Light Melee: Mur'gul Reaver (`nnmg`) — v6 balanced Amphibious Vanguard!
        # 2 Food, 120g, 19s, 455 HP, +0.65 HP/s tidal regen, 2 Large armor, 12+1d5=15.0 Normal / 1.42s = 10.6 DPS
        ("nnmg", NULL_ID, [
            ("ugol", VT_INT, 120),
            ("ulum", VT_INT, 0),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 19),
            ("uhpm", VT_INT, 455),
            ("uhpr", VT_UNREAL, 0.65),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 2),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 285),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "normal"),
            ("ua1b", VT_INT, 12),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 5),
            ("ua1c", VT_UNREAL, 1.42),
            ("upgr", VT_STR, "Rnat,Rnam"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Train Mur'gul |cffffcc00R|reaver"),
            ("utub", VT_STR, "Swift amphibious Tier-1 vanguard with rapid tidal regeneration. Can traverse deep water and engage land forces."),
        ]),

        # Tier 1 Ranged Piercing: Snap Dragon (`nsnp`) — no structure prerequisite.
        # 3 Food, 195g/30L, 25s, 540 HP, 1 Medium armor, 19+1d7=23.0 Pierce / 1.75s = 13.1 DPS + Slow Poison
        ("nsnp", NULL_ID, [
            ("ureq", VT_STR, ""),
            ("ugol", VT_INT, 195),
            ("ulum", VT_INT, 30),
            ("ufoo", VT_INT, 3),
            ("ubld", VT_INT, 25),
            ("uhpm", VT_INT, 540),
            ("uhpr", VT_UNREAL, 0.50),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 1),
            ("udty", VT_STR, "medium"),
            ("umvs", VT_INT, 290),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "pierce"),
            ("ua1b", VT_INT, 19),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 7),
            ("ua1c", VT_UNREAL, 1.75),
            ("ua1r", VT_INT, 550),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "Aspo,Asb3"),
            ("upgr", VT_STR, "Rnat,Rnam,Rnsb"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "D"),
            ("utip", VT_STR, "Train Snap |cffffcc00D|rragon"),
            ("utub", VT_STR, "Venomous ranged reptile armed with Slow Poison spines that slow enemy attack and movement speed. Attacks land and air units."),
        ]),

        # Tier 2 Heavy Melee: Naga Myrmidon (`nmyr`) — v6 balanced Heavy Bruiser!
        # 4 Food, 235g/50L, 33s, 920 HP, 4 Large armor, 28+1d7=32.0 Normal / 1.60s = 20.0 DPS + Ensnare & Submerge
        ("nmyr", NULL_ID, [
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 235),
            ("ulum", VT_INT, 50),
            ("ufoo", VT_INT, 4),
            ("ubld", VT_INT, 33),
            ("uhpm", VT_INT, 920),
            ("uhpr", VT_UNREAL, 0.65),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 4),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 285),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "normal"),
            ("ua1b", VT_INT, 28),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 7),
            ("ua1c", VT_UNREAL, 1.60),
            ("uabi", VT_STR, "ANen,Asb1"),
            ("upgr", VT_STR, "Rnat,Rnam,Rnen,Rnsb"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "M"),
            ("utip", VT_STR, "Train Naga |cffffcc00M|ryrmidon"),
            ("utub", VT_STR, "Armored Tier-2 amphibious juggernaut. Wields Ensnare to pull down air units and Submerge to regenerate rapidly."),
        ]),

        # Tier 2 Spellcaster: Naga Siren (`nnsw`) — v6 balanced: 365 HP, 300 MP (150 start), Parasite + Frost Armor + Cyclone
        ("nnsw", NULL_ID, [
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 140),
            ("ulum", VT_INT, 30),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 26),
            ("uhpm", VT_INT, 365),
            ("uhpr", VT_UNREAL, 0.50),
            ("uhrt", VT_STR, "always"),
            ("umpm", VT_INT, 300),
            ("umpi", VT_INT, 150),
            ("umpr", VT_UNREAL, 1.05),
            ("udef", VT_INT, 1),
            ("udty", VT_STR, "none"),
            ("umvs", VT_INT, 280),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "magic"),
            ("ua1b", VT_INT, 11),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 5),
            ("ua1c", VT_UNREAL, 1.60),
            ("ua1r", VT_INT, 600),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "ANpa,ACfu,Acny"),
            ("udaa", VT_STR, "ACfu"),
            ("upgr", VT_STR, "Rnsw"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Train Naga |cffffcc00S|riren"),
            ("utub", VT_STR, "Mystic Naga spellcaster armed with Frost Armor, Parasite, and Cyclone (Master). Attacks land and air units."),
        ]),

        # Tier 2 Flying Anti-Caster: Couatl (`nwgs`) — v6 balanced: 460 HP, 2 Light armor, 11.5 Magic DPS + Abolish Magic
        ("nwgs", NULL_ID, [
            ("ureq", VT_STR, "n001"),
            ("ugol", VT_INT, 155),
            ("ulum", VT_INT, 35),
            ("ufoo", VT_INT, 2),
            ("ubld", VT_INT, 26),
            ("uhpm", VT_INT, 460),
            ("uhpr", VT_UNREAL, 0.50),
            ("uhrt", VT_STR, "always"),
            ("umpm", VT_INT, 250),
            ("umpi", VT_INT, 125),
            ("umpr", VT_UNREAL, 0.80),
            ("udef", VT_INT, 2),
            ("udty", VT_STR, "small"),
            ("umvs", VT_INT, 330),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "magic"),
            ("ua1b", VT_INT, 16),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 5),
            ("ua1c", VT_UNREAL, 1.65),
            ("ua1r", VT_INT, 500),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("uabi", VT_STR, "Andm"),
            ("udaa", VT_STR, "Andm"),
            ("upgr", VT_STR, "Rnat,Rnam,Rnsi"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Train |cffffcc00C|rouatl"),
            ("utub", VT_STR, "Swift sky-serpent dealing potent Magic damage to ground and air targets, with Abolish Magic to dispel buffs and shred summons."),
        ]),

        # Tier 2 Siege Beast: Dragon Turtle (`nhyc`) — v6 balanced: 840 HP, 3 Large armor, 23.6 Siege DPS + Spiked Shell & Hardened Skin
        ("nhyc", NULL_ID, [
            ("ureq", VT_STR, "n001,n004"),
            ("ugol", VT_INT, 230),
            ("ulum", VT_INT, 65),
            ("ufoo", VT_INT, 4),
            ("ubld", VT_INT, 36),
            ("uhpm", VT_INT, 840),
            ("uhpr", VT_UNREAL, 0.65),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 3),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 240),
            ("uaen", VT_INT, 3),
            ("ua1t", VT_STR, "pierce"),
            ("ua1b", VT_INT, 21),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 7),
            ("ua1c", VT_UNREAL, 1.65),
            ("ua1r", VT_INT, 480),
            ("ua1g", VT_STR, "ground,debris,item,ward"),
            ("ua2t", VT_STR, "siege"),
            ("ua2b", VT_INT, 53),
            ("ua2d", VT_INT, 1),
            ("ua2s", VT_INT, 11),
            ("ua2c", VT_UNREAL, 2.50),
            ("ua2r", VT_INT, 600),
            ("ua2g", VT_STR, "structure,tree,wall"),
            ("uabi", VT_STR, "ANth,Ansk"),
            ("upgr", VT_STR, "Rnat,Rnam"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Train Dragon |cffffcc00T|rurtle"),
            ("utub", VT_STR, "Colossal armored siege leviathan protected by Hardened Skin and Thorny Shield. Bombards enemy fortifications from range."),
        ]),

        # Tier 3 Elite Champion: Naga Royal Guard (`nnrg`) — v6 balanced Apex Champion!
        # 5 Food, 300g/90L, 1150 HP, 4 Large armor, 21.2 Normal DPS + Crushing Wave, Frost Bolt, Cleave, Resistant Skin & Submerge!
        ("nnrg", NULL_ID, [
            ("ureq", VT_STR, "n002"),
            ("ugol", VT_INT, 300),
            ("ulum", VT_INT, 90),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 42),
            ("uhpm", VT_INT, 1150),
            ("uhpr", VT_UNREAL, 0.65),
            ("uhrt", VT_STR, "always"),
            ("umpm", VT_INT, 300),
            ("umpi", VT_INT, 175),
            ("umpr", VT_UNREAL, 1.00),
            ("udef", VT_INT, 4),
            ("udty", VT_STR, "large"),
            ("umvs", VT_INT, 285),
            ("usca", VT_REAL, 1.06),
            ("uaen", VT_INT, 1),
            ("ua1t", VT_STR, "normal"),
            ("ua1b", VT_INT, 31),
            ("ua1d", VT_INT, 1),
            ("ua1s", VT_INT, 9),
            ("ua1c", VT_UNREAL, 1.70),
            ("uabi", VT_STR, "ACcv,ACcb,ACce,ACsk,Asb2"),
            ("upgr", VT_STR, "Rnat,Rnam,Rnsb"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Train Naga Royal |cffffcc00G|ruard"),
            ("utub", VT_STR, "Supreme Tier-3 Naga sovereign warrior armed with Crushing Wave, Frost Bolt, Cleaving Attack, Resistant Skin, and Submerge."),
        ]),

        # Naga Hero 1: Empress Lady Vashj (`Hvsh`, INT) — Exclusive Kit `A000..A003`!
        ("Hvsh", NULL_ID, [
            ("urac", VT_STR, "naga"),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 100),
            ("ustr", VT_INT, 17),
            ("uagi", VT_INT, 18),
            ("uint", VT_INT, 20),
            ("ustp", VT_UNREAL, 1.90),
            ("uagp", VT_UNREAL, 1.60),
            ("uinp", VT_UNREAL, 2.90),
            ("umvs", VT_INT, 295),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "n001"),
            ("urq2", VT_STR, "n002"),
            ("uhab", VT_STR, "A000,A001,A002,A003"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "V"),
            ("utip", VT_STR, "Summon Empress |cffffcc00V|rashj"),
            ("utpr", VT_STR, "Revive Empress |cffffcc00V|rashj"),
            ("utub", VT_STR, "Abyssal Tideborn Intelligence Sovereign. Exclusive kit: Maelstrom Vortex (Q), Forked Tempest Arc (W), Mana-Tide Aegis (E), and Cataclysmic Tsunami (R)."),
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
            ("utyp", VT_STR, "Peon"),
            ("ubui", VT_STR, "h001,nefm,h007,h011,h010,h004,h005,negt,nheb,h008,h009"),
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
            ("utub", VT_STR, "Provides 6 food, increasing the maximum number of Sunfury Imperium units that can be trained."),
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
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
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
            ("ubpx", VT_INT, 3),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "O"),
            ("utip", VT_STR, "Build Sunspire Sc|cffffcc00o|rut Tower"),
            ("utub", VT_STR, "Observation spire with Magic Sentry. Has no attack, but can be upgraded into a Sunspire Guard Tower or a Sunspire Arcane Tower."),
        ]),

        # Tower Upgrade 1: Sunspire Guard Tower (`negf`) — Exact Human Guard Tower parity!
        ("negf", NULL_ID, [
            ("unam", VT_STR, "Sunspire Guard Tower"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, "hlum"),
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

        # ---- Sunfury Imperium 4 Summonable Heroes (`Hkal`, `Hvwd`, `Hlgr`, `Huth`) — Exclusive Kits `A016..A031` & ZERO `urev`! ----
        ("Hkal", NULL_ID, [
            ("unam", VT_STR, "Sovereign Kael'thas"),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 100),
            ("ustr", VT_INT, 18),
            ("uagi", VT_INT, 15),
            ("uint", VT_INT, 22),
            ("ustp", VT_UNREAL, 2.00),
            ("uagp", VT_UNREAL, 1.30),
            ("uinp", VT_UNREAL, 3.05),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "h002"),
            ("urq2", VT_STR, "h003"),
            ("uhab", VT_STR, "A016,A017,A018,A019"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "K"),
            ("utip", VT_STR, "Summon Sovereign |cffffcc00K|rael'thas"),
            ("utpr", VT_STR, "Revive Sovereign |cffffcc00K|rael'thas"),
            ("utub", VT_STR, "Solar Archmage of the Sunfury Imperium. Signature skills: Flamestrike (Q), Verdant Gravity Lapse (W), Arcane Mana Siphon (E), and Summon Phoenix: Al'ar (R)."),
        ]),

        ("Hvwd", NULL_ID, [
            ("unam", VT_STR, "Sunstrider Sylvanas"),
            ("urac", VT_STR, "human"),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 100),
            ("ustr", VT_INT, 17),
            ("uagi", VT_INT, 22),
            ("uint", VT_INT, 16),
            ("ustp", VT_UNREAL, 1.85),
            ("uagp", VT_UNREAL, 2.65),
            ("uinp", VT_UNREAL, 1.95),
            ("umvs", VT_INT, 310),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "h002"),
            ("urq2", VT_STR, "h003"),
            ("uhab", VT_STR, "A020,A021,A022,A023"),
            ("uabi", VT_STR, "AInv"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Summon |cffffcc00S|runstrider Sylvanas"),
            ("utpr", VT_STR, "Revive |cffffcc00S|runstrider Sylvanas"),
            ("utub", VT_STR, "Ranger-General of Quel'Thalas. Exclusive kit: Sunhawk Volley (Q), Windrunner's Gale Vault (W), Heartseeker Mark (E), and Eclipse Starfall Arrow (R)."),
        ]),

        ("Hlgr", NULL_ID, [
            ("unam", VT_STR, "Grand Marshal Garithos"),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 100),
            ("ustr", VT_INT, 24),
            ("uagi", VT_INT, 14),
            ("uint", VT_INT, 17),
            ("ustp", VT_UNREAL, 2.90),
            ("uagp", VT_UNREAL, 1.35),
            ("uinp", VT_UNREAL, 1.80),
            ("umvs", VT_INT, 295),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "h002"),
            ("urq2", VT_STR, "h003"),
            ("uhab", VT_STR, "A024,A025,A026,A027"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Summon Grand Marshal |cffffcc00G|rarithos"),
            ("utpr", VT_STR, "Revive Grand Marshal |cffffcc00G|rarithos"),
            ("utub", VT_STR, "Armored War-Marshal of the Sunfury Expedition. Exclusive kit: Cavalry Shock Charge (Q), Marshal's Execution Axe (W), Iron Phalanx Decree (E), and Grand Crusade Stampede (R)."),
        ]),

        ("Huth", NULL_ID, [
            ("unam", VT_STR, "Highlord Uther"),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ufoo", VT_INT, 5),
            ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 100),
            ("ustr", VT_INT, 23),
            ("uagi", VT_INT, 13),
            ("uint", VT_INT, 19),
            ("ustp", VT_UNREAL, 2.75),
            ("uagp", VT_UNREAL, 1.50),
            ("uinp", VT_UNREAL, 1.95),
            ("umvs", VT_INT, 290),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "h002"),
            ("urq2", VT_STR, "h003"),
            ("uhab", VT_STR, "A028,A029,A030,A031"),
            ("ubpx", VT_INT, 3),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "Summon Highlord |cffffcc00U|rther"),
            ("utpr", VT_STR, "Revive Highlord |cffffcc00U|rther"),
            ("utub", VT_STR, "Radiant Sun-Paladin of the Imperium. Signature skills: Sunwell Consecration (Q), Hammer of Dawnlight (W), Golden Bastion Blessing (E), and Resurrection (R)."),
        ]),
    ]

    # ==========================================================================
    # CUSTOM UNITS, HEROES & BUILDINGS (`N004`, `N001..N002`, `n001..n005`, `h001..h009`,
    # PLUS `v001..v019`, `V001..V004`, `t001..t019`, `T001..T004`)
    # ==========================================================================
    custom: List[Tuple[str, str, List[ModEntry]]] = [
        # ---- NAGA CUSTOM HEROES (`N004` ILLIDAN + `N001..N002`) — ZERO `urev`! ----
        # N004: Illidan Stormrage, Betrayer of Tides (Balanced AGI Hero on `nnad` Slot (1,0)!)
        ("Eevi", "N004", [
            ("unam", VT_STR, "Betrayer of Tides"),
            ("upro", VT_STR, "Illidan Stormrage"),
            ("upru", VT_INT, 1),
            ("uhot", VT_STR, "I"),
            ("urac", VT_STR, "naga"),
            ("upra", VT_STR, "AGI"),
            ("ustr", VT_INT, 19),
            ("uagi", VT_INT, 21),
            ("uint", VT_INT, 15),
            ("ustp", VT_UNREAL, 2.10),
            ("uagp", VT_UNREAL, 2.65),
            ("uinp", VT_UNREAL, 1.75),
            ("umdl", VT_STR, r"units\nightelf\EvilIllidan\IllidanEvil.mdl"),
            ("usnd", VT_STR, "EvilIllidan"),
            ("usca", VT_REAL, 1.08),
            ("umvt", VT_STR, "amph"),
            ("umvs", VT_INT, 310),
            ("uhpm", VT_INT, 100),
            ("uhpr", VT_UNREAL, 0.35),
            ("uhrt", VT_STR, "always"),
            ("umpm", VT_INT, 100),
            ("umpi", VT_INT, 100),
            ("umpr", VT_UNREAL, 0.05),
            ("udef", VT_INT, 2),
            ("ua1b", VT_INT, 2),
            ("ua1d", VT_INT, 2),
            ("ua1s", VT_INT, 6),
            ("ua1c", VT_UNREAL, 1.65),
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "n001"),
            ("urq2", VT_STR, "n002"),
            ("uhab", VT_STR, "A004,A005,A006,A007"),
            ("uabi", VT_STR, "AInv"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 0),
            ("utip", VT_STR, "Summon |cffffcc00I|rllidan Stormrage"),
            ("utpr", VT_STR, "Revive |cffffcc00I|rllidan Stormrage"),
            ("utub", VT_STR, "Agile Warglaive Lord of the Abyssal Tideborn. Signature skills: Azzinoth Glaive Barrage (Q), Mana Burn (W), Immolation (E), and Metamorphosis (R)."),
        ]),

        ("Otch", "N001", [
            ("unam", VT_STR, "Leviathan Warlord"),
            ("upro", VT_STR, "Naj'entus,Zar'jira,Vash'kor,Skar'this"),
            ("upru", VT_INT, 4),
            ("uhot", VT_STR, "W"),
            ("urac", VT_STR, "naga"),
            ("upra", VT_STR, "STR"),
            ("ustr", VT_INT, 25),
            ("uagi", VT_INT, 14),
            ("uint", VT_INT, 16),
            ("ustp", VT_UNREAL, 2.95),
            ("uagp", VT_UNREAL, 1.50),
            ("uinp", VT_UNREAL, 1.75),
            ("umdl", VT_STR, r"units\naga\NagaRoyalGuard\NagaRoyalGuard.mdl"),
            ("usnd", VT_STR, "NagaRoyalGuard"),
            ("usca", VT_REAL, 1.15),
            ("umvt", VT_STR, "amph"),
            ("umvs", VT_INT, 290),
            ("uhpm", VT_INT, 100),
            ("uhpr", VT_UNREAL, 0.35),
            ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 2),
            ("ua1b", VT_INT, 0),
            ("ua1d", VT_INT, 2),
            ("ua1s", VT_INT, 5),
            ("ua1c", VT_UNREAL, 1.85),
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "n001"),
            ("urq2", VT_STR, "n002"),
            ("uhab", VT_STR, "A008,A009,A010,A011"),
            ("uabi", VT_STR, "AInv"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("utip", VT_STR, "Summon Leviathan |cffffcc00W|rarlord"),
            ("utpr", VT_STR, "Revive Leviathan |cffffcc00W|rarlord"),
            ("utub", VT_STR, "Colossal Abyssal Tideborn Strength commander. Exclusive kit: Crushing Trench Wave (Q), Impaling Spine Skewer (W), Tidal Bulwark Roar (E), and Wrath of Naj'entus (R)."),
        ]),

        ("Hamg", "N002", [
            ("unam", VT_STR, "Nazjatar Tideweaver"),
            ("upro", VT_STR, "Athissa,Sira'kess,Zin'azshari,Thal'issa"),
            ("upru", VT_INT, 4),
            ("uhot", VT_STR, "T"),
            ("urac", VT_STR, "naga"),
            ("upra", VT_STR, "INT"),
            ("ustr", VT_INT, 16),
            ("uagi", VT_INT, 16),
            ("uint", VT_INT, 23),
            ("ustp", VT_UNREAL, 1.80),
            ("uagp", VT_UNREAL, 1.45),
            ("uinp", VT_UNREAL, 3.10),
            ("umdl", VT_STR, r"Units\Naga\NagaSummoner\NagaSummoner.mdl"),
            ("usnd", VT_STR, "NagaSiren"),
            ("usca", VT_REAL, 1.15),
            ("umvt", VT_STR, "amph"),
            ("umvs", VT_INT, 290),
            ("uhpm", VT_INT, 100),
            ("uhpr", VT_UNREAL, 0.30),
            ("uhrt", VT_STR, "always"),
            ("ufoo", VT_INT, 5),
            ("ugol", VT_INT, 425),
            ("ulum", VT_INT, 100),
            ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3),
            ("urq1", VT_STR, "n001"),
            ("urq2", VT_STR, "n002"),
            ("uhab", VT_STR, "A012,A013,A014,A015"),
            ("uabi", VT_STR, "AInv"),
            ("ubpx", VT_INT, 3),
            ("ubpy", VT_INT, 0),
            ("utip", VT_STR, "Summon Nazjatar |cffffcc00T|rideweaver"),
            ("utpr", VT_STR, "Revive Nazjatar |cffffcc00T|rideweaver"),
            ("utub", VT_STR, "Highborne Arch-Siren of Nazjatar. Exclusive kit: Bioluminescent Geyser (Q), Pearl-frost Prison (W), Siren's Vital Chorus (E), and Summon Abyssal Kraken (R)."),
        ]),


        # ---- NAGA CUSTOM STRUCTURES (`n001..n005`) — Authentic Naga Icons & `utyp`! ----
        # n001: Sanctuary of Tides (Tier 2 Naga Town Hall — trains ONLY `nmpe`!)
        ("nntt", "n001", [
            ("unam", VT_STR, "Sanctuary of Tides"),
            ("urac", VT_STR, "naga"),
            ("utyp", VT_STR, "TownHall,Mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("usca", VT_REAL, 1.15),
            ("uclr", VT_INT, 175),
            ("uclg", VT_INT, 240),
            ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 320),
            ("ulum", VT_INT, 190),
            ("ubld", VT_INT, 115),
            ("ufma", VT_INT, 11),
            ("uhpm", VT_INT, 2000),
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
            ("urac", VT_STR, "naga"),
            ("utyp", VT_STR, "TownHall,Mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("usca", VT_REAL, 1.28),
            ("uclr", VT_INT, 130),
            ("uclg", VT_INT, 220),
            ("uclb", VT_INT, 255),
            ("ureq", VT_STR, "nnad"),
            ("ugol", VT_INT, 360),
            ("ulum", VT_INT, 210),
            ("ubld", VT_INT, 115),
            ("ufma", VT_INT, 11),
            ("uhpm", VT_INT, 2450),
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

        # n003: Tidal Treasury (Naga racial shop; native Shrine of Ashjara model/button).
        ("hvlt", "n003", [
            ("unam", VT_STR, "Tidal Treasury"),
            ("urac", VT_STR, "naga"),
            ("utyp", VT_STR, "mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "nnad"),
            ("umdl", VT_STR, r"buildings\other\MagicVault\MagicVault.mdl"),
            ("usca", VT_REAL, 0.92),
            ("uclr", VT_INT, 115),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 130),
            ("ulum", VT_INT, 30),
            ("ubld", VT_INT, 52),
            ("uhpm", VT_INT, 600),
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

        # n004: Coral Forge (Naga armory; native Altar of Depths model/button).
        ("hbla", "n004", [
            ("unam", VT_STR, "Coral Forge"),
            ("urac", VT_STR, "naga"),
            ("utyp", VT_STR, "mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "nntt"),
            ("umdl", VT_STR, r"buildings\other\FountainOfPower\FountainOfPower.mdl"),
            ("usca", VT_REAL, 0.88),
            ("uclr", VT_INT, 130),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 140),
            ("ulum", VT_INT, 60),
            ("ubld", VT_INT, 52),
            ("uhpm", VT_INT, 1150),
            ("udef", VT_INT, 5),
            ("udty", VT_STR, "fort"),
            ("uabi", VT_STR, "Abds,Arlm"),
            ("utra", VT_STR, ""),
            ("ures", VT_STR, "Rnat,Rnam"),
            ("upgr", VT_STR, ""),
            ("ubpx", VT_INT, 3),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "F"),
            ("utip", VT_STR, "Build Coral |cffffcc00F|rorge"),
            ("utub", VT_STR, "Abyssal coral armory where Coral, Chitinous, and Razorspine Blades and Scales are forged. Unlocks Dragon Turtles."),
        ]),

        # n005: Abyssal Behemoth Pool (Naga production building; native Spawning Grounds model/button).
        ("nnsg", "n005", [
            ("unam", VT_STR, "Abyssal Behemoth Pool"),
            ("urac", VT_STR, "naga"),
            ("utyp", VT_STR, "mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("ureq", VT_STR, "n001,n004"),
            ("umdl", VT_STR, r"buildings\other\DragonBuildingBlue\DragonBuildingBlue.mdl"),
            ("usca", VT_REAL, 0.92),
            ("uclr", VT_INT, 145),
            ("uclg", VT_INT, 225),
            ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 155),
            ("ulum", VT_INT, 140),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1200),
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

        # ---- SUNFURY IMPERIUM CUSTOM STRUCTURES & UNITS (`h001..h011`) ----
        # Sunfury structures retain recognizable stock buttons with their custom models.
        ("hbla", "h010", [
            ("unam", VT_STR, "Sunfury Forge of the Sunwell"),
            ("urac", VT_STR, "human"),
            ("umdl", VT_STR, r"buildings\other\FountainOfPower\FountainOfPower.mdl"),
            ("usca", VT_REAL, 0.92),
            ("uclr", VT_INT, 255), ("uclg", VT_INT, 210), ("uclb", VT_INT, 145),
            ("ugol", VT_INT, 140), ("ulum", VT_INT, 60), ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 1100), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("ureq", VT_STR, "h001"), ("uabi", VT_STR, "Abds,Arlm"),
            ("ures", VT_STR, "Rhme,Rhra,Rhar,Rhla"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "F"),
            ("utip", VT_STR, "Build Sunfury |cffffcc00F|rorge"),
            ("utub", VT_STR, "Sunfury armory and lumber drop-off. Forges melee, ranged, and armor upgrades for the Imperium's troops."),
        ]),

        ("hlum", "h011", [
            ("unam", VT_STR, "Sunspire Lumber Conservatory"),
            ("urac", VT_STR, "human"),
            ("umdl", VT_STR, r"buildings\other\ElvenVillageBuilding0\ElvenVillageBuilding0.mdl"),
            ("usca", VT_REAL, 0.98),
            ("uclr", VT_INT, 255), ("uclg", VT_INT, 225), ("uclb", VT_INT, 165),
            ("ugol", VT_INT, 120), ("ulum", VT_INT, 60), ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 900), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("uabi", VT_STR, "Arlm"), ("ures", VT_STR, "Rhac,Rhlh"),
            ("ubpx", VT_INT, 3), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "L"),
            ("utip", VT_STR, "Build Sunspire |cffffcc00L|rumber Conservatory"),
            ("utub", VT_STR, "Quel'Thalas timber guild and lumber drop-off. Supports Arcane Conservatory construction and advanced masonry."),
        ]),

        ("htow", "h001", [
            ("unam", VT_STR, "Silvermoon Sanctum"),
            ("umdl", VT_STR, r"buildings\other\ArcaneObservatory\ArcaneObservatory.mdl"),
            ("usca", VT_REAL, 0.92),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 235),
            ("uclb", VT_INT, 185),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("utra", VT_STR, "nhew"),
            ("ures", VT_STR, "Rhpm"),
            ("uupt", VT_STR, "h002"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "H"),
            ("utip", VT_STR, "Build Silvermoon |cffffcc00H|rall"),
            ("utub", VT_STR, "Primary Sunfury Imperium spire. Trains Silvermoon Workers, researches Backpack, and receives gathered Gold and Lumber. Upgrades to Sunwell Keep."),
        ]),

        ("hkee", "h002", [
            ("unam", VT_STR, "Sunwell Keep"),
            ("umdl", VT_STR, r"buildings\other\ArcaneObservatory\ArcaneObservatory.mdl"),
            ("usca", VT_REAL, 1.06),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 220),
            ("uclb", VT_INT, 145),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("utra", VT_STR, "nhew"),
            ("ures", VT_STR, "Rhpm"),
            ("uupt", VT_STR, "h003"),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Sunwell Keep"),
            ("utub", VT_STR, "Upgrade to Sunwell Keep (Tier 2) to unlock the High Elven Mage Tower, Sunfury Artificer Hall, Dragonhawk Sky-Roost, a 2nd Sunfury Hero, and Tier-2 upgrades."),
        ]),

        ("hcas", "h003", [
            ("unam", VT_STR, "Silvermoon Citadel"),
            ("umdl", VT_STR, r"buildings\other\ArcaneObservatory\ArcaneObservatory.mdl"),
            ("usca", VT_REAL, 1.20),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 195),
            ("uclb", VT_INT, 115),
            ("ureq", VT_STR, "h004"),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("utra", VT_STR, "nhew"),
            ("ures", VT_STR, "Rhpm"),
            ("uupt", VT_STR, ""),
            ("ubpx", VT_INT, 0),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Silvermoon Citadel"),
            ("utub", VT_STR, "Upgrade to Silvermoon Citadel (Tier 3) to unlock Alliance Captains, Blood Elf Lieutenants, Gryphon Riders, Orb of Fire, a 3rd Sunfury Hero, and Tier-3 upgrades."),
        ]),

        ("halt", "h004", [
            ("unam", VT_STR, "Altar of the Sunwell"),
            ("umdl", VT_STR, r"buildings\human\AltarOfKings\AltarOfKings.mdl"),
            ("usca", VT_REAL, 0.88),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 225),
            ("uclb", VT_INT, 165),
            ("utra", VT_STR, "Hkal,Hvwd,Hlgr,Huth"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Build |cffffcc00A|rltar of the Sunwell"),
            ("utub", VT_STR, "Summons Sunfury Imperium Heroes (Sovereign Kael'thas, Sunstrider Sylvanas, Grand Marshal Garithos, and Highlord Uther) and revives fallen Heroes."),
        ]),

        ("hvlt", "h005", [
            ("unam", VT_STR, "Sunwell Reliquary"),
            ("umdl", VT_STR, r"buildings\other\MagicVault\MagicVault.mdl"),
            ("usca", VT_REAL, 0.92),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 215),
            ("uclb", VT_INT, 145),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 1),
            ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Build Sunwell |cffffcc00R|reliquary"),
            ("utub", VT_STR, "Creates a Quel'Thalas reliquary stocked with Scrolls, Potions, Town Portals, Scout Towers, Staff of Sanctuary, and Orb of Fire."),
        ]),

        # h006: Silvermoon Ballista (Tier-2 siege engine; inherits the stock Ballista button).
        ("ebal", "h006", [
            ("unam", VT_STR, "Silvermoon Ballista"),
            ("urac", VT_STR, "human"),
            ("ureq", VT_STR, "h002,h010"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 220),
            ("uclb", VT_INT, 155),
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
            ("utub", VT_STR, "Long-range High Elven mechanical siege engine. Hurls giant sun-runed bolts to demolish enemy towers and fortifications from afar."),
        ]),

        # h007: Sunspire Barracks (Slot `(1,0)` — Quel'Thalas building model and native barracks button).
        ("hbar", "h007", [
            ("unam", VT_STR, "Sunspire Barracks"),
            ("umdl", VT_STR, r"buildings\other\ElvenVillageBuilding3\ElvenVillageBuilding3.mdl"),
            ("usca", VT_REAL, 1.35),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 225),
            ("uclb", VT_INT, 165),
            ("ugol", VT_INT, 160),
            ("ulum", VT_INT, 60),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1300),
            ("utra", VT_STR, "hhes,nhea,hcth"),
            ("ures", VT_STR, "Rhde,Rhan"),
            ("upgr", VT_STR, "Rhac"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 0),
            ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Build Sunspire |cffffcc00B|rarracks"),
            ("utub", VT_STR, "Primary Quel'Thalas troop bastion. Trains High Elven Swordsmen, High Elven Archers, and Alliance Captains (Tier 3). Also researches Defend and Veteran War Training."),
        ]),

        # h008: Sunfury Artificer Hall (Slot `(3,1)` — faction model and stock workshop button).
        ("harm", "h008", [
            ("unam", VT_STR, "Sunfury Artificer Hall"),
            ("ureq", VT_STR, "h002,h010"),
            ("umdl", VT_STR, r"buildings\other\ElvenVillageBuilding4\ElvenVillageBuilding4.mdl"),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 210),
            ("uclb", VT_INT, 135),
            ("ugol", VT_INT, 140),
            ("ulum", VT_INT, 140),
            ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1200),
            ("utra", VT_STR, "hgyr,h006,nbel"),
            ("ures", VT_STR, "Rhgb"),
            ("upgr", VT_STR, "Rhac"),
            ("ubpx", VT_INT, 1),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "W"),
            ("utip", VT_STR, "Build Sunfury Artificer |cffffcc00W|rorkshop"),
            ("utub", VT_STR, "Sun-forged war-machine hall. Produces Flying Machines, Silvermoon Ballistas, and Blood Elf Lieutenants (Tier 3). Also researches Flying Machine Bombs."),
        ]),

        # h009: Dragonhawk Sky-Roost (Slot `(1,2)` — native Dragon Roost model and stock aviary button).
        ("hgra", "h009", [
            ("unam", VT_STR, "Dragonhawk Sky-Roost"),
            ("ureq", VT_STR, "h002,h011"),
            ("umdl", VT_STR, r"buildings\other\DragonRoost\DragonRoost.mdl"),
            ("usca", VT_REAL, 0.90),
            ("uclr", VT_INT, 255),
            ("uclg", VT_INT, 220),
            ("uclb", VT_INT, 155),
            ("ugol", VT_INT, 140),
            ("ulum", VT_INT, 150),
            ("ubld", VT_INT, 65),
            ("uhpm", VT_INT, 1200),
            ("utra", VT_STR, "hdhw,hgry"),
            ("ures", VT_STR, "Rhcd,Rhhb"),
            ("upgr", VT_STR, "Rhac"),
            ("ubpx", VT_INT, 2),
            ("ubpy", VT_INT, 2),
            ("uhot", VT_STR, "V"),
            ("utip", VT_STR, "Build Dragonhawk Sky-A|cffffcc00v|riary"),
            ("utub", VT_STR, "Aerial roost for Dragonhawk Riders (Tier 2) and Wildhammer Gryphon Riders (Tier 3). Also researches Cloud and Storm Hammers."),
        ]),
    ]

    custom.extend(build_voidborn_and_runeforged_units())
    # Remove legacy generated glyph assignments; stock object buttons remain inherited,
    # while each hero receives either its portrait art or its matching native portrait.
    original = _normalize_object_icons(original)
    custom = _normalize_object_icons(custom)
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
    Serialize `war3map.w3t` (v2) with Racial Shop items for Abyssal, Voidborn & Runeforged:
      - `i001`: Orb of the Abyss (Tier 3 `n002`, 375g)
      - `i002`: Imperial Staff of Sanctuary (Tier 3 shared Sanctuary staff, 250g)
      - `i003`: Scroll of War Surge (Tier 1 Scroll of Speed, 50g)
      - `i004`: Orb of Oblivion (Tier 3 `v003` Voidborn Orb of Corruption, 375g)
      - `i005`: Orb of Storms (Tier 3 `t003` Runeforged Orb of Lightning, 375g)
    """
    cust: List[Tuple[str, str, List[ModEntry]]] = [
        ("ofro", "i001", [
            ("unam", VT_STR, "Orb of the Abyss"),
            ("utip", VT_STR, "Purchase |cffffcc00O|rrb of the Abyss"),
            ("utub", VT_STR, "Adds 6 bonus frost damage to a Hero's attacks, enables ranged air attacks, and chills enemies for 3 seconds."),
            ("uhot", VT_STR, "O"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2),
            ("ureq", VT_STR, "n002"),
            ("igol", VT_INT, 375), ("isel", VT_INT, 1), ("ipaw", VT_INT, 1),
            ("isto", VT_INT, 1), ("istr", VT_INT, 120), ("isst", VT_INT, 0), ("iprn", VT_INT, 0),
        ]),
        ("ssan", "i002", [
            ("unam", VT_STR, "Imperial Staff of Sanctuary"),
            ("utip", VT_STR, "Purchase Imperial |cffffcc00S|rtaff of Sanctuary"),
            ("uhot", VT_STR, "S"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 2),
            ("ureq", VT_STR, ""),
            ("igol", VT_INT, 250), ("isel", VT_INT, 1), ("ipaw", VT_INT, 1),
            ("isto", VT_INT, 1), ("istr", VT_INT, 120), ("isst", VT_INT, 210), ("iprn", VT_INT, 0),
        ]),
        ("shas", "i003", [
            ("unam", VT_STR, "Scroll of War Surge"),
            ("utip", VT_STR, "Purchase Scroll of War |cffffcc00S|rurge"),
            ("uhot", VT_STR, "T"),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0),
            ("ureq", VT_STR, ""),
            ("igol", VT_INT, 50), ("isel", VT_INT, 1), ("ipaw", VT_INT, 1),
            ("isto", VT_INT, 2), ("istr", VT_INT, 90), ("isst", VT_INT, 0), ("iprn", VT_INT, 0),
        ]),
        ("ocor", "i004", [
            ("unam", VT_STR, "Orb of Oblivion"),
            ("utip", VT_STR, "Purchase |cffffcc00O|rrb of Oblivion"),
            ("utub", VT_STR, "Adds 5 bonus void damage, enables ranged air attacks, and reduces enemy armor by 4 for 5 seconds."),
            ("uhot", VT_STR, "O"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2),
            ("ureq", VT_STR, "v003"),
            ("igol", VT_INT, 375), ("isel", VT_INT, 1), ("ipaw", VT_INT, 1),
            ("isto", VT_INT, 1), ("istr", VT_INT, 120), ("isst", VT_INT, 0), ("iprn", VT_INT, 0),
        ]),
        ("oli2", "i005", [
            ("unam", VT_STR, "Orb of Storms"),
            ("utip", VT_STR, "Purchase |cffffcc00O|rrb of Storms"),
            ("utub", VT_STR, "Adds 5 bonus plasma damage, enables ranged air attacks, and gives a chance to purge and slow enemies."),
            ("uhot", VT_STR, "O"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2),
            ("ureq", VT_STR, "t003"),
            ("igol", VT_INT, 375), ("isel", VT_INT, 1), ("ipaw", VT_INT, 1),
            ("isto", VT_INT, 1), ("istr", VT_INT, 120), ("isst", VT_INT, 0), ("iprn", VT_INT, 0),
        ]),
    ]
    return (
        struct.pack("<i", 2)
        + _pack_mod_table([], use_optional_ints=False)
        + _pack_mod_table(cust, use_optional_ints=False)
    )


# ==============================================================================
# 3. UPGRADE MODIFICATIONS (`war3map.w3q` v2) & ABILITIES (`war3map.w3a` v2)
# ==============================================================================

def _make_3tier_upgrade(
    parent_id: str,
    new_id: str,
    names: Tuple[str, str, str],
    hotkey: str,
    btn_x: int,
    t2_hall: str,
    t3_hall: str,
    is_armor: bool,
) -> Tuple[str, str, List[LevelModEntry]]:
    mods: List[LevelModEntry] = [
        ("gglb", VT_INT, 0, 0, 125),
        ("gglm", VT_INT, 0, 0, 50 if is_armor else 75),
        ("glmb", VT_INT, 0, 0, 75),
        ("glmm", VT_INT, 0, 0, 100),
        ("gbpx", VT_INT, 0, 0, btn_x),
        ("gbpy", VT_INT, 0, 0, 0),
        ("greq", VT_STR, 1, 0, ""),
        ("greq", VT_STR, 2, 0, t2_hall),
        ("greq", VT_STR, 3, 0, t3_hall),
    ]
    stat_word = "armor" if is_armor else "attack power"
    for lv in (1, 2, 3):
        nm = names[lv - 1]
        mods.extend([
            ("gnam", VT_STR, lv, 0, nm),
            ("ghk1", VT_STR, lv, 0, hotkey),
            ("gtp1", VT_STR, lv, 0, f"Upgrade to {nm} [|cffffcc00{hotkey}|r]"),
            ("gub1", VT_STR, lv, 0, f"Increases the {stat_word} of your empire's combat forces (Tier {lv})."),
        ])
    return (parent_id, new_id, mods)


def serialize_w3q() -> bytes:
    """
    Serialize `war3map.w3q` (v2, `use_optional_ints = True`) for Naga (`Rnat`..`Rnsi`),
    Voidborn (`R000`, `R001`), and Runeforged (`R002`, `R003`).
    """
    NULL_ID = "\x00\x00\x00\x00"
    orig: List[Tuple[str, str, List[LevelModEntry]]] = [
        ("Rnat", NULL_ID, [
            ("gglb", VT_INT, 0, 0, 125), ("gglm", VT_INT, 0, 0, 75),
            ("glmb", VT_INT, 0, 0, 75),  ("glmm", VT_INT, 0, 0, 100),
            ("greq", VT_STR, 2, 0, "n001"), ("greq", VT_STR, 3, 0, "n002"),
        ]),
        ("Rnam", NULL_ID, [
            ("gglb", VT_INT, 0, 0, 125), ("gglm", VT_INT, 0, 0, 50),
            ("glmb", VT_INT, 0, 0, 75),  ("glmm", VT_INT, 0, 0, 100),
            ("greq", VT_STR, 2, 0, "n001"), ("greq", VT_STR, 3, 0, "n002"),
        ]),
        ("Rnen", NULL_ID, [
            ("gglb", VT_INT, 0, 0, 50), ("glmb", VT_INT, 0, 0, 50), ("gtib", VT_INT, 0, 0, 25),
            ("greq", VT_STR, 1, 0, "n001"),
        ]),
        ("Rnsb", NULL_ID, [
            ("gglb", VT_INT, 0, 0, 60), ("glmb", VT_INT, 0, 0, 60), ("gtib", VT_INT, 0, 0, 30),
            ("gbpx", VT_INT, 0, 0, 1), ("gbpy", VT_INT, 0, 0, 2), ("greq", VT_STR, 1, 0, "n001"),
        ]),
        ("Rnsw", NULL_ID, [("greq", VT_STR, 1, 0, "n001"), ("greq", VT_STR, 2, 0, "n002")]),
        ("Rnsi", NULL_ID, [
            ("gglb", VT_INT, 0, 0, 50), ("glmb", VT_INT, 0, 0, 50), ("gtib", VT_INT, 0, 0, 25),
            ("greq", VT_STR, 1, 0, "n001"),
        ]),
    ]
    cust: List[Tuple[str, str, List[LevelModEntry]]] = [
        _make_3tier_upgrade("Rnat", "R000", ("Void Blades", "Riftforged Blades", "Oblivion Blades"), "B", 0, "v002", "v003", False),
        _make_3tier_upgrade("Rnam", "R001", ("Astral Plating", "Nether Plating", "Oblivion Carapace"), "P", 1, "v002", "v003", True),
        _make_3tier_upgrade("Rnat", "R002", ("Runic Weapons", "Stormsteel Weapons", "Titanforged Weapons"), "W", 0, "t002", "t003", False),
        _make_3tier_upgrade("Rnam", "R003", ("Titan Plating", "Stormsteel Plating", "Pantheon Aegis"), "P", 1, "t002", "t003", True),
    ]
    return (
        struct.pack("<i", 2)
        + _pack_mod_table(orig, use_optional_ints=True)
        + _pack_mod_table(cust, use_optional_ints=True)
    )


def serialize_w3a() -> bytes:
    """
    Serialize `war3map.w3a` (v2, `use_optional_ints = True`) containing all 64
    Unique Custom Hero Skills (`A000..A063`), 16 exclusive four-skill kits, and
    zero shared abilities across the playable custom heroes.
    """
    orig, cust = build_ability_modifications()
    return (
        struct.pack("<i", 2)
        + _pack_mod_table(orig, use_optional_ints=True)
        + _pack_mod_table(cust, use_optional_ints=True)
    )


# ==============================================================================
# 4. GAMEPLAY CONSTANTS (`war3mapMisc.txt`) & IMPORT TABLE (`war3map.imp`)
# ==============================================================================

def serialize_war3map_misc() -> bytes:
    """
    Registers all 8 Playable Empires' Town Halls, Altars, and Heroes (including `N004` Illidan!)
    in Warcraft III's native Gameplay Constants (`[TWN1..3]`, `[TALT]`, `[HERO]`).
    """
    lines = [
        "[HERO]",
        "DependencyOr=Hamg,Hmkg,Hpal,Hblm,Obla,Ofar,Otch,Oshd,Udea,Udre,Ulic,Ucrl,Edem,Ekee,Emoo,Ewar,Nbrn,Nbst,Nngs,Npbm,Nalc,Ntin,Nfir,Nplh,Hvsh,N004,N001,N002,Hkal,Hvwd,Hlgr,Huth,V001,V002,V003,V004,T001,T002,T003,T004",
        "",
        "[TALT]",
        "DependencyOr=halt,oalt,uaod,eate,nnad,h004,v007,t007",
        "",
        "[TWN1]",
        "DependencyOr=htow,ogre,unpl,etol,nntt,h001,v001,t001",
        "",
        "[TWN2]",
        "DependencyOr=hkee,ostr,unp1,etoa,n001,h002,v002,t002",
        "",
        "[TWN3]",
        "DependencyOr=hcas,ofrt,unp2,etoe,n002,h003,v003,t003",
        "",
    ]
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def serialize_imp(extra_paths: Iterable[str] = ()) -> bytes:
    """
    Serialize `war3map.imp` (v1) listing all `.ai` scripts plus all custom `.blp`
    icons/textures and `.mdx` VFX models (excluding `war3mapPreview.tga` which is
    a standard root map file) with full-path flag `0x0D` (`13`).
    """
    base_entries = [
        "naga_melee.ai",
        "camphuman_melee.ai",
        "voidborn_melee.ai",
        "runeforged_melee.ai",
    ]
    seen = set(base_entries)
    for p in sorted(extra_paths):
        if p == "war3mapPreview.tga" or p in seen:
            continue
        seen.add(p)
        base_entries.append(p)
    buf = bytearray(struct.pack("<II", 1, len(base_entries)))
    for path in base_entries:
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
    constant integer HERO_ILLIDAN      = 'N004'
    constant integer HERO_WARLORD      = 'N001'
    constant integer HERO_TIDEWEAVER   = 'N002'

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
        set skill[ 1] = 'A000'
        set skill[ 2] = 'A001'
        set skill[ 3] = 'A000'
        set skill[ 4] = 'A002'
        set skill[ 5] = 'A000'
        set skill[ 6] = 'A003'
        set skill[ 7] = 'A001'
        set skill[ 8] = 'A001'
        set skill[ 9] = 'A002'
        set skill[10] = 'A002'
    elseif heroId == HERO_ILLIDAN then
        set skill[ 1] = 'A004'
        set skill[ 2] = 'A005'
        set skill[ 3] = 'A004'
        set skill[ 4] = 'A006'
        set skill[ 5] = 'A004'
        set skill[ 6] = 'A007'
        set skill[ 7] = 'A005'
        set skill[ 8] = 'A005'
        set skill[ 9] = 'A006'
        set skill[10] = 'A006'
    elseif heroId == HERO_WARLORD then
        set skill[ 1] = 'A008'
        set skill[ 2] = 'A009'
        set skill[ 3] = 'A008'
        set skill[ 4] = 'A010'
        set skill[ 5] = 'A008'
        set skill[ 6] = 'A011'
        set skill[ 7] = 'A009'
        set skill[ 8] = 'A009'
        set skill[ 9] = 'A010'
        set skill[10] = 'A010'
    else
        set skill[ 1] = 'A012'
        set skill[ 2] = 'A013'
        set skill[ 3] = 'A012'
        set skill[ 4] = 'A014'
        set skill[ 5] = 'A012'
        set skill[ 6] = 'A015'
        set skill[ 7] = 'A013'
        set skill[ 8] = 'A013'
        set skill[ 9] = 'A014'
        set skill[10] = 'A014'
    endif
endfunction

function ChooseNagaHeroes takes nothing returns nothing
    local integer roll = GetRandomInt(1, 4)
    if roll == 1 then
        set hero_id  = HERO_ILLIDAN
        set hero_id2 = HERO_VASHJ
        set hero_id3 = HERO_WARLORD
    elseif roll == 2 then
        set hero_id  = HERO_VASHJ
        set hero_id2 = HERO_ILLIDAN
        set hero_id3 = HERO_TIDEWEAVER
    elseif roll == 3 then
        set hero_id  = HERO_WARLORD
        set hero_id2 = HERO_ILLIDAN
        set hero_id3 = HERO_VASHJ
    else
        set hero_id  = HERO_TIDEWEAVER
        set hero_id2 = HERO_VASHJ
        set hero_id3 = HERO_ILLIDAN
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
            call NagaNeedUnit(3, NAGA_SNAP_DRAGON, -1)
            call NagaNeedUnit(1, NAGA_GUARDIAN, 0)
            call NagaNeedUnit(1, NAGA_FORGE, -1)
        endif

        if GetUnitCountDone(NAGA_FORGE) >= 1 then
            call NagaNeedUnit(4, NAGA_SNAP_DRAGON, -1)
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

            if GetUpgradeLevel(UPG_NAGA_ENSNARE) < 1 then
                call SetUpgrade(UPG_NAGA_ENSNARE)
            endif
            if GetUpgradeLevel(UPG_NAGA_SUBMERGE) < 1 then
                call SetUpgrade(UPG_NAGA_SUBMERGE)
            endif

            if GetUnitCountDone(NAGA_SHRINE) >= 1 then
                call NagaNeedUnit(3, NAGA_SIREN, -1)
                call NagaNeedUnit(2, NAGA_COUATL, -1)
                if GetUpgradeLevel(UPG_NAGA_SIREN) < 1 then
                    call SetUpgrade(UPG_NAGA_SIREN)
                endif
                if GetUpgradeLevel(UPG_NAGA_ABOLISH) < 1 then
                    call SetUpgrade(UPG_NAGA_ABOLISH)
                endif
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
    constant integer CH_LUMBER_MILL    = 'h011'
    constant integer CH_FORGE          = 'h010'
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
        set skill[ 1] = 'A016'
        set skill[ 2] = 'A017'
        set skill[ 3] = 'A016'
        set skill[ 4] = 'A018'
        set skill[ 5] = 'A016'
        set skill[ 6] = 'A019'
        set skill[ 7] = 'A017'
        set skill[ 8] = 'A017'
        set skill[ 9] = 'A018'
        set skill[10] = 'A018'
    elseif heroId == HERO_SYLVANAS then
        set skill[ 1] = 'A020'
        set skill[ 2] = 'A021'
        set skill[ 3] = 'A020'
        set skill[ 4] = 'A022'
        set skill[ 5] = 'A020'
        set skill[ 6] = 'A023'
        set skill[ 7] = 'A021'
        set skill[ 8] = 'A021'
        set skill[ 9] = 'A022'
        set skill[10] = 'A022'
    elseif heroId == HERO_GARITHOS then
        set skill[ 1] = 'A024'
        set skill[ 2] = 'A025'
        set skill[ 3] = 'A024'
        set skill[ 4] = 'A026'
        set skill[ 5] = 'A024'
        set skill[ 6] = 'A027'
        set skill[ 7] = 'A025'
        set skill[ 8] = 'A025'
        set skill[ 9] = 'A026'
        set skill[10] = 'A026'
    else
        set skill[ 1] = 'A028'
        set skill[ 2] = 'A029'
        set skill[ 3] = 'A028'
        set skill[ 4] = 'A030'
        set skill[ 5] = 'A028'
        set skill[ 6] = 'A031'
        set skill[ 7] = 'A029'
        set skill[ 8] = 'A029'
        set skill[ 9] = 'A030'
        set skill[10] = 'A030'
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
# 6. JASS2 8-EMPIRE SELECTION (LOBBY + DIALOG + CHAT) & AI TACTICAL MICRO SYSTEM
# ==============================================================================

def generate_custom_races_jass() -> Tuple[str, str]:
    """
    Returns `(globals_block, functions_block)` to embed into `war3map.j`
    (v7: 8 Playable Empires, Host-first AI Difficulty, 16 exclusive Heroes with 64
    level-gated skills and individual MDX spell effects, RPG UI/cursor skins, Live Multiboard
    HUD, native standard-race AI and an authoritative sequential JASS custom-faction controller).
    """
    return generate_custom_gameplay_jass()
