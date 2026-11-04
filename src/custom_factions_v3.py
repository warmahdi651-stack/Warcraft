#!/usr/bin/env python3
"""
v3 Expansion Module for `(8) Crown of WarMahdi`:
  - Two brand-new, complete, tournament-balanced Custom Playable Empires:
      7. Voidborn Legion (`v001..v019`, Heroes `V001..V004`, Upgrades `R000..R001`)
      8. Runeforged Bastion (`t001..t019`, Heroes `T001..T004`, Upgrades `R002..R003`)
  - `war3map.w3a` (v2) generator for all 16 Custom Hero Skills (`A000..A015`)
    with custom `.blp` icons, custom `.mdx` 3D sigil/crown VFX, AoE reticles, and
    clean native order strings (`flamestrike`, `chainlightning`, `blink`,
    `thunderclap`, `monsoon`).
  - `war3mapSkin.txt` Dark Astral-Gold non-classic UI skin (`[CustomSkin]` + `[FrameDef]`).
  - Dedicated `.ai` melee scripts (`voidborn_melee.ai` & `runeforged_melee.ai`).
"""

from __future__ import annotations

import struct
from typing import Any, Dict, List, Tuple

VT_INT = 0
VT_REAL = 1
VT_UNREAL = 2
VT_STR = 3

ModEntry = Tuple[str, int, Any]
LevelModEntry = Tuple[str, int, int, int, Any]


# ==============================================================================
# 1. VOIDBORN LEGION & RUNEFORGED BASTION (`war3map.w3u` CUSTOM TABLE ENTRIES)
# ==============================================================================

def build_voidborn_and_runeforged_units() -> List[Tuple[str, str, List[ModEntry]]]:
    """
    Return custom `war3map.w3u` entries for:
      - Voidborn Legion (`v001..v019`, Heroes `V001..V004`)
      - Runeforged Bastion (`t001..t019`, Heroes `T001..T004`)
    """
    entries: List[Tuple[str, str, List[ModEntry]]] = [
        # ======================================================================
        # FACTION 7: VOIDBORN LEGION (`v010` Void Thrall builds 9 structures)
        #   Row 0: (0,0) v001 | (1,0) v004 | (2,0) v005 | (3,0) v006
        #   Row 1: (0,1) v007 | (1,1) v008 | (2,1) v009
        #   Row 2: (0,2) v018 | (1,2) v019
        # ======================================================================

        # Worker: Void Thrall (`v010`, parent `nhew`)
        ("nhew", "v010", [
            ("unam", VT_STR, "Void Thrall"),
            ("umdl", VT_STR, "units\\creeps\\VoidWalker\\VoidWalker.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNVoidWalker.blp"),
            ("usnd", VT_STR, "ObsidianDestroyer"),
            ("usca", VT_REAL, 0.72),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 130), ("uclb", VT_INT, 255),
            ("ubui", VT_STR, "v001,v004,v005,v006,v007,v008,v009,v018,v019"),
            ("ugol", VT_INT, 75), ("ulum", VT_INT, 0), ("ufoo", VT_INT, 1), ("ubld", VT_INT, 15),
            ("uhpm", VT_INT, 230), ("uhpr", VT_UNREAL, 0.25), ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 0), ("udty", VT_STR, "medium"), ("umvs", VT_INT, 190),
            ("uabi", VT_STR, "Ahar,Ahrp,Aihn"),
            ("ua1b", VT_INT, 5), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 2), ("ua1c", VT_UNREAL, 2.0),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Summon Void |cffffcc00T|rhrall"),
            ("utub", VT_STR, "Astral worker spirit. Harvests Gold and Lumber, constructs Voidborn structures, and Repairs."),
        ]),

        # Tier 1/2/3 Void Halls (`v001 -> v002 -> v003`)
        ("htow", "v001", [
            ("unam", VT_STR, "Void Nexus"),
            ("umdl", VT_STR, "buildings\\undead\\Necropolis\\Necropolis.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNNecropolis.blp"),
            ("usnd", VT_STR, "Necropolis"),
            ("uclr", VT_INT, 170), ("uclg", VT_INT, 95), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 385), ("ulum", VT_INT, 185), ("ubld", VT_INT, 120),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 1500), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "v010"), ("ures", VT_STR, "Rhpm"), ("uupt", VT_STR, "v002"),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "N"),
            ("utip", VT_STR, "Build Void |cffffcc00N|rexus"),
            ("utub", VT_STR, "Primary citadel of the Voidborn Legion. Summons Void Thralls and receives harvested Gold and Lumber. Upgrades to Astral Riftcore."),
        ]),
        ("hkee", "v002", [
            ("unam", VT_STR, "Astral Riftcore"),
            ("umdl", VT_STR, "buildings\\undead\\Necropolis\\Necropolis.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNHallsOfTheDead.blp"),
            ("usnd", VT_STR, "Necropolis"),
            ("usca", VT_REAL, 1.08),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 320), ("ulum", VT_INT, 190), ("ubld", VT_INT, 120),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 1800), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "v010"), ("ures", VT_STR, "Rhpm"), ("uupt", VT_STR, "v003"), ("ureq", VT_STR, ""),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Astral Riftcore"),
            ("utub", VT_STR, "Tier-2 Void citadel. Unlocks Sanctum of Stars, Oblivion Pit, Dread Enforcers, and a 2nd Altar Hero."),
        ]),
        ("hcas", "v003", [
            ("unam", VT_STR, "Citadel of Oblivion"),
            ("umdl", VT_STR, "buildings\\other\\DarkPortal2\\DarkPortal2.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNBlackCitadel.blp"),
            ("usnd", VT_STR, "Necropolis"),
            ("usca", VT_REAL, 0.72),
            ("uclr", VT_INT, 205), ("uclg", VT_INT, 130), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 360), ("ulum", VT_INT, 210), ("ubld", VT_INT, 120),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 2100), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "v010"), ("ures", VT_STR, "Rhpm"), ("ureq", VT_STR, "v007"),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Citadel of Oblivion"),
            ("utub", VT_STR, "Tier-3 Void apex stronghold. Unlocks Oblivion Colossi, Tier-3 Void upgrades, Orb of Oblivion, and a 3rd Hero."),
        ]),

        # Supply: Astral Pylon (`v004`, +9 Food)
        ("hhou", "v004", [
            ("unam", VT_STR, "Astral Pylon"),
            ("umdl", VT_STR, "buildings\\undead\\Ziggurat\\Ziggurat.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNZiggurat.blp"),
            ("usnd", VT_STR, "Ziggurat"),
            ("usca", VT_REAL, 0.85),
            ("uclr", VT_INT, 175), ("uclg", VT_INT, 110), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 90), ("ulum", VT_INT, 25), ("ubld", VT_INT, 35),
            ("ufma", VT_INT, 9), ("uhpm", VT_INT, 500), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "P"),
            ("utip", VT_STR, "Build Astral |cffffcc00P|rylon"),
            ("utub", VT_STR, "Channels cosmic energy, providing 9 Food to sustain your Voidborn forces."),
        ]),

        # Barracks: Rift Gate (`v005`)
        ("hbar", "v005", [
            ("unam", VT_STR, "Rift Gate"),
            ("umdl", VT_STR, "buildings\\undead\\Crypt\\Crypt.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNCrypt.blp"),
            ("usnd", VT_STR, "Crypt"),
            ("uclr", VT_INT, 175), ("uclg", VT_INT, 105), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 160), ("ulum", VT_INT, 60), ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1300), ("udef", VT_INT, 5),
            ("utra", VT_STR, "v011,v012,v013"), ("ures", VT_STR, ""),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Build Rift |cffffcc00G|rate"),
            ("utub", VT_STR, "Primary troop portal. Summons Void Zealots (T1), Astral Arbalists (req Crucible), and Dread Enforcers (T2)."),
        ]),

        # Armory + Lumber Drop: Obsidian Crucible (`v006`)
        ("hbla", "v006", [
            ("unam", VT_STR, "Obsidian Crucible"),
            ("umdl", VT_STR, "buildings\\undead\\Graveyard\\Graveyard.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNGraveYard.blp"),
            ("usnd", VT_STR, "Graveyard"),
            ("uclr", VT_INT, 170), ("uclg", VT_INT, 95), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 140), ("ulum", VT_INT, 60), ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 1200), ("udef", VT_INT, 5),
            ("ures", VT_STR, "R000,R001"), ("ureq", VT_STR, "v001"),
            ("uabi", VT_STR, "Abds,Arlm"),
            ("ubpx", VT_INT, 3), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Build Obsidian |cffffcc00C|rrucible"),
            ("utub", VT_STR, "Void forge and Lumber return point. Researches Void Blades (+1/+2/+3 Attack) and Astral Plating (+1/+2/+3 Armor)."),
        ]),

        # Altar: Altar of the Void (`v007`) — `urev = 1` ONLY ON ALTAR!
        ("halt", "v007", [
            ("unam", VT_STR, "Altar of the Void"),
            ("umdl", VT_STR, "buildings\\undead\\AltarOfDarkness\\AltarOfDarkness.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNAltarOfDarkness.blp"),
            ("usnd", VT_STR, "AltarOfDarkness"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 110), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 180), ("ulum", VT_INT, 50), ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 900), ("udef", VT_INT, 5), ("urev", VT_INT, 1),
            ("utra", VT_STR, "V001,V002,V003,V004"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Build |cffffcc00A|rltar of the Void"),
            ("utub", VT_STR, "Summons Voidborn Heroes (Rift Sovereign, Nether Inquisitor, Abyssal Stalker-Lord, Entropy Archon) and revives fallen Heroes."),
        ]),

        # Shop: Reliquary of Shadows (`v008`)
        ("hvlt", "v008", [
            ("unam", VT_STR, "Reliquary of Shadows"),
            ("umdl", VT_STR, "buildings\\undead\\TombOfRelics\\TombOfRelics.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNTombOfRelics.blp"),
            ("usnd", VT_STR, "TombOfRelics"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 130), ("ulum", VT_INT, 30), ("ubld", VT_INT, 50),
            ("uhpm", VT_INT, 550), ("ureq", VT_STR, "v007"),
            ("umki", VT_STR, "sreg,plcl,i003,phea,pman,stwp,i004,i002"),
            ("usei", VT_STR, ""),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Build |cffffcc00R|reliquiaries of Shadows"),
            ("utub", VT_STR, "Mystic Void vault offering scrolls, healing & mana potions, Town Portals, and the Orb of Oblivion."),
        ]),

        # Tower: Entropy Obelisk (`v009`)
        ("hgtw", "v009", [
            ("unam", VT_STR, "Entropy Obelisk"),
            ("umdl", VT_STR, "buildings\\other\\DalaranGuardTower\\DalaranGuardTower.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNDalaranGuardTower.blp"),
            ("usnd", VT_STR, "ElvenGuardTower"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 110), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 135), ("ulum", VT_INT, 80), ("ubld", VT_INT, 45),
            ("uhpm", VT_INT, 500), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("ureq", VT_STR, "v006"), ("uabi", VT_STR, "Abds,Adts"),
            ("ua1b", VT_INT, 22), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 5),
            ("ua1c", VT_UNREAL, 1.0), ("ua1r", VT_INT, 700), ("ua1t", VT_STR, "pierce"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\AvengerMissile\\AvengerMissile.mdl"),
            ("ua1z", VT_INT, 1400),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "O"),
            ("utip", VT_STR, "Build Entropy |cffffcc00O|rbelisk"),
            ("utub", VT_STR, "Astral defense spire with True Sight. Fires piercing void bolts at ground and air invaders."),
        ]),

        # Caster/Flyer Sanctum: Sanctum of Stars (`v018`)
        ("hars", "v018", [
            ("unam", VT_STR, "Sanctum of Stars"),
            ("umdl", VT_STR, "buildings\\undead\\TempleOfTheDamned\\TempleOfTheDamned.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNTempleOfTheDamned.blp"),
            ("usnd", VT_STR, "TempleOfTheDamned"),
            ("uclr", VT_INT, 180), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 150), ("ulum", VT_INT, 140), ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1100), ("udef", VT_INT, 5),
            ("ureq", VT_STR, "v002"), ("utra", VT_STR, "v014,v015"), ("ures", VT_STR, ""),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Build |cffffcc00S|ranctum of Stars"),
            ("utub", VT_STR, "Tier-2 Astral spire. Trains Void Weavers (spellcasters) and Nether Drakelets (magic anti-caster flyers)."),
        ]),

        # Siege & T3 Champion Bay: Oblivion Pit (`v019`)
        ("harm", "v019", [
            ("unam", VT_STR, "Oblivion Pit"),
            ("umdl", VT_STR, "buildings\\other\\DragonBuildingBlack\\DragonBuildingBlack.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNBoneYard.blp"),
            ("usnd", VT_STR, "DragonRoost"),
            ("usca", VT_REAL, 0.85),
            ("uclr", VT_INT, 180), ("uclg", VT_INT, 100), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 180), ("ulum", VT_INT, 140), ("ubld", VT_INT, 65),
            ("uhpm", VT_INT, 1200), ("udef", VT_INT, 5),
            ("ureq", VT_STR, "v002,v006"), ("utra", VT_STR, "v016,v017"), ("ures", VT_STR, ""),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Build O|cffffcc00b|rlivion Pit"),
            ("utub", VT_STR, "Heavy war pit. Summons Rift Devastators (T2 Siege) and Oblivion Colossi (T3 Elite Champions)."),
        ]),

        # ---- VOIDBORN COMBAT UNITS (`v011..v017`) ----
        ("hfoo", "v011", [
            ("unam", VT_STR, "Void Zealot"),
            ("umdl", VT_STR, "units\\demon\\FelgaurdBlue\\FelgaurdBlue.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNFelGuardBlue.blp"),
            ("usnd", VT_STR, "DoomGuard"),
            ("usca", VT_REAL, 0.86),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 130), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 130), ("ulum", VT_INT, 0), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 20),
            ("uhpm", VT_INT, 425), ("udef", VT_INT, 2), ("udty", VT_STR, "large"), ("umvs", VT_INT, 275),
            ("ua1b", VT_INT, 12), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 3), ("ua1c", VT_UNREAL, 1.30),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "Z"),
            ("utip", VT_STR, "Summon Void |cffffcc00Z|realot"),
            ("utub", VT_STR, "Swift Tier-1 Rift bladesman with heavy armor. Attacks land units."),
        ]),
        ("hrif", "v012", [
            ("unam", VT_STR, "Astral Arbalist"),
            ("umdl", VT_STR, "Units\\Creeps\\FacelessOne\\FacelessOne.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNFacelessOne.blp"),
            ("usnd", VT_STR, "FacelessOne"),
            ("usca", VT_REAL, 0.84),
            ("uclr", VT_INT, 205), ("uclg", VT_INT, 145), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 200), ("ulum", VT_INT, 35), ("ufoo", VT_INT, 3), ("ubld", VT_INT, 26),
            ("uhpm", VT_INT, 530), ("udef", VT_INT, 0), ("udty", VT_STR, "medium"), ("umvs", VT_INT, 275),
            ("ureq", VT_STR, "v006"),
            ("ua1b", VT_INT, 21), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 6), ("ua1c", VT_UNREAL, 1.35),
            ("ua1r", VT_INT, 550), ("ua1w", VT_STR, "missile"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\AvengerMissile\\AvengerMissile.mdl"), ("ua1z", VT_INT, 1300),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Summon |cffffcc00A|rstral Arbalist"),
            ("utub", VT_STR, "Ranged Void marksman capable of hurling astral bolts at ground and air targets."),
        ]),
        ("hkni", "v013", [
            ("unam", VT_STR, "Dread Enforcer"),
            ("umdl", VT_STR, "Units\\Creeps\\DragonSpawnPurple\\DragonSpawnPurple.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNDragonSpawnPurple.blp"),
            ("usnd", VT_STR, "DragonSpawn"),
            ("usca", VT_REAL, 0.90),
            ("ugol", VT_INT, 240), ("ulum", VT_INT, 50), ("ufoo", VT_INT, 4), ("ubld", VT_INT, 32),
            ("uhpm", VT_INT, 850), ("udef", VT_INT, 3), ("udty", VT_STR, "large"), ("umvs", VT_INT, 295),
            ("ureq", VT_STR, "v002"),
            ("ua1b", VT_INT, 26), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 8), ("ua1c", VT_UNREAL, 1.55),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "E"),
            ("utip", VT_STR, "Summon Dread |cffffcc00E|rnforcer"),
            ("utub", VT_STR, "Tier-2 heavily armored Void bruiser with crushing melee strikes."),
        ]),
        ("hmpr", "v014", [
            ("unam", VT_STR, "Void Weaver"),
            ("umdl", VT_STR, "units\\demon\\EredarWarlockPurple\\EredarWarlockPurple.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNEredarWarlockPurple.blp"),
            ("usnd", VT_STR, "PitLord"),
            ("usca", VT_REAL, 0.76),
            ("ugol", VT_INT, 145), ("ulum", VT_INT, 30), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 26),
            ("uhpm", VT_INT, 325), ("umpi", VT_INT, 175), ("umpm", VT_INT, 300), ("umpr", VT_UNREAL, 1.1),
            ("ureq", VT_STR, "v002"),
            ("ua1b", VT_INT, 10), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 3), ("ua1c", VT_UNREAL, 1.65),
            ("ua1m", VT_STR, "Abilities\\Weapons\\NecromancerMissile\\NecromancerMissile.mdl"),
            ("uabi", VT_STR, "Aslo,Aadm,Aihn"), ("udaa", VT_STR, "Aslo"), ("upgr", VT_STR, "R001"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "W"),
            ("utip", VT_STR, "Summon Void |cffffcc00W|reaver"),
            ("utub", VT_STR, "Astral caster adept at Temporal Slow and Abolish Magic. Attacks ground and air units."),
        ]),
        ("hdhw", "v015", [
            ("unam", VT_STR, "Nether Drakelet"),
            ("umdl", VT_STR, "units\\creeps\\NetherDragon\\NetherDragon.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNNetherDragon.blp"),
            ("usnd", VT_STR, "NetherDragon"),
            ("usca", VT_REAL, 0.72),
            ("ugol", VT_INT, 165), ("ulum", VT_INT, 40), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 28),
            ("uhpm", VT_INT, 445), ("umpi", VT_INT, 0), ("umpm", VT_INT, 0),
            ("udef", VT_INT, 1), ("udty", VT_STR, "light"), ("umvs", VT_INT, 320),
            ("ureq", VT_STR, "v002"),
            ("ua1b", VT_INT, 16), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 4), ("ua1c", VT_UNREAL, 1.60),
            ("ua1r", VT_INT, 450), ("ua1t", VT_STR, "magic"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\AvengerMissile\\AvengerMissile.mdl"),
            ("uabi", VT_STR, ""), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "D"),
            ("utip", VT_STR, "Summon Nether |cffffcc00D|rrakelet"),
            ("utub", VT_STR, "Agile Void flyer dealing Magic damage to ground and air forces."),
        ]),
        ("hmtm", "v016", [
            ("unam", VT_STR, "Rift Devastator"),
            ("umdl", VT_STR, "units\\creeps\\InfernalCannonFlame\\InfernalCannonFlame.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNInfernalFlameCannon.blp"),
            ("usnd", VT_STR, "InfernalMachine"),
            ("usca", VT_REAL, 0.80),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 210), ("ulum", VT_INT, 65), ("ufoo", VT_INT, 4), ("ubld", VT_INT, 36),
            ("uhpm", VT_INT, 580), ("udef", VT_INT, 2), ("udty", VT_STR, "heavy"), ("umvs", VT_INT, 225),
            ("ureq", VT_STR, "v002,v006"),
            ("ua1b", VT_INT, 46), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 12), ("ua1c", VT_UNREAL, 2.7),
            ("ua1r", VT_INT, 900), ("ua1t", VT_STR, "siege"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\ObsidianStatueMissile\\ObsidianStatueMissile.mdl"),
            ("uabi", VT_STR, ""), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Summon |cffffcc00R|rift Devastator"),
            ("utub", VT_STR, "Long-range Void siege engine that obliterates enemy fortifications from afar."),
        ]),
        ("hkni", "v017", [
            ("unam", VT_STR, "Oblivion Colossus"),
            ("umdl", VT_STR, "units\\demon\\DoomGuard\\DoomGuard.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNDoomGuard.blp"),
            ("usnd", VT_STR, "DoomGuard"),
            ("usca", VT_REAL, 1.02),
            ("uclr", VT_INT, 190), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 300), ("ulum", VT_INT, 90), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 44),
            ("uhpm", VT_INT, 1080), ("udef", VT_INT, 4), ("udty", VT_STR, "large"), ("umvs", VT_INT, 285),
            ("ureq", VT_STR, "v003"),
            ("ua1b", VT_INT, 32), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 8), ("ua1c", VT_UNREAL, 1.70),
            ("uabi", VT_STR, "ACcv,ACrk,Aihn"), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Summon Oblivion |cffffcc00C|rolossus"),
            ("utub", VT_STR, "Tier-3 Void apex juggernaut armed with Cleaving Strike and Resistant Skin."),
        ]),

        # ---- 4 VOIDBORN HEROES (`V001..V004`) — ZERO `urev`! ----
        ("Nplh", "V001", [
            ("unam", VT_STR, "Rift Sovereign"),
            ("upro", VT_STR, "Xal'athor,Vael'gorath,Nihil'zar,Mal'korath"), ("upru", VT_INT, 4),
            ("uclr", VT_INT, 180), ("uclg", VT_INT, 105), ("uclb", VT_INT, 255),
            ("usca", VT_REAL, 0.92),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "v002"), ("urq2", VT_STR, "v003"),
            ("uhab", VT_STR, "A008,A009,A010,A011"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 24), ("uagi", VT_INT, 14), ("uint", VT_INT, 17),
            ("ustp", VT_UNREAL, 2.9), ("uagp", VT_UNREAL, 1.5), ("uinp", VT_UNREAL, 1.9),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Summon |cffffcc00R|rift Sovereign"),
            ("utpr", VT_STR, "Revive |cffffcc00R|rift Sovereign"),
            ("utub", VT_STR, "Colossal Void Strength Hero. Commands Event Horizon, Rift Sever, Entropy Shroud, and Cosmic Collapse."),
        ]),
        ("Ulic", "V002", [
            ("unam", VT_STR, "Nether Inquisitor"),
            ("upro", VT_STR, "Sargen'eth,Kael'vor,Ombros,Zurael"), ("upru", VT_INT, 4),
            ("umdl", VT_STR, "units\\demon\\EredarWarlockPurple\\EredarWarlockPurple.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNEredarWarlockPurple.blp"),
            ("usnd", VT_STR, "PitLord"), ("usca", VT_REAL, 0.96),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "v002"), ("urq2", VT_STR, "v003"),
            ("uhab", VT_STR, "A008,A009,A010,A011"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 16), ("uagi", VT_INT, 14), ("uint", VT_INT, 25),
            ("ustp", VT_UNREAL, 1.9), ("uagp", VT_UNREAL, 1.5), ("uinp", VT_UNREAL, 3.1),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "I"),
            ("utip", VT_STR, "Summon Nether |cffffcc00I|rnquisitor"),
            ("utpr", VT_STR, "Revive Nether |cffffcc00I|rnquisitor"),
            ("utub", VT_STR, "Ranged Void Intelligence Archmage. Amplifies Event Horizon, Rift Sever, Entropy Shroud, and Cosmic Collapse."),
        ]),
        ("Edem", "V003", [
            ("unam", VT_STR, "Abyssal Stalker-Lord"),
            ("upro", VT_STR, "Vex'aran,Noctis,Kzr'eth,Shadrel"), ("upru", VT_INT, 4),
            ("umdl", VT_STR, "units\\nightelf\\EvilIllidan\\IllidanEvil.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNEvilIllidan.blp"),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 125), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "v002"), ("urq2", VT_STR, "v003"),
            ("uhab", VT_STR, "A008,A009,A010,A011"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 18), ("uagi", VT_INT, 22), ("uint", VT_INT, 15),
            ("ustp", VT_UNREAL, 2.2), ("uagp", VT_UNREAL, 2.8), ("uinp", VT_UNREAL, 1.8),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Summon Abyssal |cffffcc00S|rtalker-Lord"),
            ("utpr", VT_STR, "Revive Abyssal |cffffcc00S|rtalker-Lord"),
            ("utub", VT_STR, "Winged Void Agility Assassin. Excels at high-tempo strikes with Rift Sever, Event Horizon, Entropy Shroud, and Cosmic Collapse."),
        ]),
        ("Udre", "V004", [
            ("unam", VT_STR, "Entropy Archon"),
            ("upro", VT_STR, "Aetheron,Val'kesh,Mor'duun,Xylar"), ("upru", VT_INT, 4),
            ("uclr", VT_INT, 175), ("uclg", VT_INT, 120), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "v002"), ("urq2", VT_STR, "v003"),
            ("uhab", VT_STR, "A008,A009,A010,A011"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 20), ("uagi", VT_INT, 16), ("uint", VT_INT, 19),
            ("ustp", VT_UNREAL, 2.5), ("uagp", VT_UNREAL, 1.8), ("uinp", VT_UNREAL, 2.4),
            ("ubpx", VT_INT, 3), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "E"),
            ("utip", VT_STR, "Summon |cffffcc00E|rntropy Archon"),
            ("utpr", VT_STR, "Revive |cffffcc00E|rntropy Archon"),
            ("utub", VT_STR, "Balanced Astral Warlord mastering Event Horizon, Rift Sever, Entropy Shroud, and Cosmic Collapse."),
        ]),

        # ======================================================================
        # FACTION 8: RUNEFORGED BASTION (`t010` Automaton builds 9 structures)
        #   Row 0: (0,0) t001 | (1,0) t004 | (2,0) t005 | (3,0) t006
        #   Row 1: (0,1) t007 | (1,1) t008 | (2,1) t009
        #   Row 2: (0,2) t018 | (1,2) t019
        # ======================================================================

        # Worker: Runeforged Automaton (`t010`, parent `nhew`)
        ("nhew", "t010", [
            ("unam", VT_STR, "Runeforged Automaton"),
            ("umdl", VT_STR, "Units\\Creeps\\HeroTinkerRobot\\HeroTinkerRobot.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNClockWerkGoblin.blp"),
            ("usnd", VT_STR, "ClockwerkGoblin"),
            ("usca", VT_REAL, 0.85),
            ("uclr", VT_INT, 235), ("uclg", VT_INT, 210), ("uclb", VT_INT, 165),
            ("ubui", VT_STR, "t001,t004,t005,t006,t007,t008,t009,t018,t019"),
            ("ugol", VT_INT, 75), ("ulum", VT_INT, 0), ("ufoo", VT_INT, 1), ("ubld", VT_INT, 15),
            ("uhpm", VT_INT, 230), ("uhpr", VT_UNREAL, 0.25), ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 0), ("udty", VT_STR, "medium"), ("umvs", VT_INT, 190),
            ("uabi", VT_STR, "Ahar,Ahrp,Aihn"),
            ("ua1b", VT_INT, 5), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 2), ("ua1c", VT_UNREAL, 2.0),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Assemble Runeforged |cffffcc00A|rutomaton"),
            ("utub", VT_STR, "Clockwork-runic builder unit. Harvests Gold and Lumber, constructs Runeforged structures, and Repairs."),
        ]),

        # Tier 1/2/3 Titan Halls (`t001 -> t002 -> t003`)
        ("htow", "t001", [
            ("unam", VT_STR, "Titan Foundry"),
            ("umdl", VT_STR, "buildings\\human\\TownHall\\TownHall.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNTownHall.blp"),
            ("usnd", VT_STR, "TownHall"),
            ("uclr", VT_INT, 205), ("uclg", VT_INT, 225), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 385), ("ulum", VT_INT, 185), ("ubld", VT_INT, 120),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 1500), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "t010"), ("ures", VT_STR, "Rhpm"), ("uupt", VT_STR, "t002"),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "F"),
            ("utip", VT_STR, "Build Titan |cffffcc00F|roundry"),
            ("utub", VT_STR, "Primary citadel of the Runeforged Bastion. Assembles Automatons and stores Gold and Lumber. Upgrades to Stormforge Hold."),
        ]),
        ("hkee", "t002", [
            ("unam", VT_STR, "Stormforge Hold"),
            ("umdl", VT_STR, "buildings\\human\\TownHall\\TownHall.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNKeep.blp"),
            ("usnd", VT_STR, "Keep"),
            ("uclr", VT_INT, 190), ("uclg", VT_INT, 230), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 320), ("ulum", VT_INT, 190), ("ubld", VT_INT, 120),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 1800), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "t010"), ("ures", VT_STR, "Rhpm"), ("uupt", VT_STR, "t003"), ("ureq", VT_STR, ""),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Stormforge Hold"),
            ("utub", VT_STR, "Tier-2 Titan citadel. Unlocks Arcane Conduit, Colossus Bay, Stormforged Juggernauts, and a 2nd Hero."),
        ]),
        ("hcas", "t003", [
            ("unam", VT_STR, "Apex Pantheon"),
            ("umdl", VT_STR, "buildings\\human\\TownHall\\TownHall.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNCastle.blp"),
            ("usnd", VT_STR, "Castle"),
            ("uclr", VT_INT, 180), ("uclg", VT_INT, 240), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 360), ("ulum", VT_INT, 210), ("ubld", VT_INT, 120),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 2100), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "t010"), ("ures", VT_STR, "Rhpm"), ("ureq", VT_STR, "t007"),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Apex Pantheon"),
            ("utub", VT_STR, "Tier-3 Titan stronghold. Unlocks Titan Constructs, Tier-3 Runic upgrades, Orb of Storms, and a 3rd Hero."),
        ]),

        # Supply: Dynamo Core (`t004`, +9 Food)
        ("hhou", "t004", [
            ("unam", VT_STR, "Dynamo Core"),
            ("umdl", VT_STR, "buildings\\other\\PowerGenerator\\PowerGenerator.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNPowerGenerator.blp"),
            ("usnd", VT_STR, "Farm"),
            ("usca", VT_REAL, 0.72),
            ("ugol", VT_INT, 90), ("ulum", VT_INT, 25), ("ubld", VT_INT, 35),
            ("ufma", VT_INT, 9), ("uhpm", VT_INT, 500), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "D"),
            ("utip", VT_STR, "Build |cffffcc00D|rynamo Core"),
            ("utub", VT_STR, "Arc-plasma power generator providing 9 Food supply to your Runeforged army."),
        ]),

        # Barracks: Iron Garrison (`t005`)
        ("hbar", "t005", [
            ("unam", VT_STR, "Iron Garrison"),
            ("umdl", VT_STR, "buildings\\human\\HumanBarracks\\HumanBarracks.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNHumanBarracks.blp"),
            ("usnd", VT_STR, "HumanBarracks"),
            ("uclr", VT_INT, 190), ("uclg", VT_INT, 225), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 160), ("ulum", VT_INT, 60), ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1300), ("udef", VT_INT, 5),
            ("utra", VT_STR, "t011,t012,t013"), ("ures", VT_STR, ""),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Build Iron |cffffcc00G|rarrison"),
            ("utub", VT_STR, "Primary war forge. Deploys Runic Sentinels (T1), Thunder Arquebusiers (req Runic Anvil), and Stormforged Juggernauts (T2)."),
        ]),

        # Armory + Lumber Drop: Runic Anvil (`t006`)
        ("hbla", "t006", [
            ("unam", VT_STR, "Runic Anvil"),
            ("umdl", VT_STR, "buildings\\human\\Blacksmith\\Blacksmith.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNBlacksmith.blp"),
            ("usnd", VT_STR, "Blacksmith"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 230), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 140), ("ulum", VT_INT, 60), ("ubld", VT_INT, 55),
            ("uhpm", VT_INT, 1200), ("udef", VT_INT, 5),
            ("ures", VT_STR, "R002,R003"), ("ureq", VT_STR, "t001"),
            ("uabi", VT_STR, "Abds,Arlm"),
            ("ubpx", VT_INT, 3), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Build |cffffcc00R|runic Anvil"),
            ("utub", VT_STR, "Titan armory and Lumber drop-off. Researches Runic Weapons (+1/+2/+3 Attack) and Titan Plating (+1/+2/+3 Armor)."),
        ]),

        # Altar: Altar of the Titans (`t007`) — `urev = 1` ONLY ON ALTAR!
        ("halt", "t007", [
            ("unam", VT_STR, "Altar of the Titans"),
            ("umdl", VT_STR, "buildings\\human\\AltarOfKings\\AltarOfKings.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNAltarOfKings.blp"),
            ("usnd", VT_STR, "AltarOfKings"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 230), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 180), ("ulum", VT_INT, 50), ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 900), ("udef", VT_INT, 5), ("urev", VT_INT, 1),
            ("utra", VT_STR, "T001,T002,T003,T004"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Build |cffffcc00A|rltar of the Titans"),
            ("utub", VT_STR, "Summons Runeforged Heroes (Stormforged Prime, Runesmith Highlord, Plasma Vanguard, Tempest Savant) and revives fallen Heroes."),
        ]),

        # Shop: Artificer Vault (`t008`)
        ("hvlt", "t008", [
            ("unam", VT_STR, "Artificer Vault"),
            ("umdl", VT_STR, "buildings\\other\\MagicVault\\MagicVault.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNArcaneVault.blp"),
            ("usnd", VT_STR, "ArcaneVault"),
            ("uclr", VT_INT, 190), ("uclg", VT_INT, 230), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 130), ("ulum", VT_INT, 30), ("ubld", VT_INT, 50),
            ("uhpm", VT_INT, 550), ("ureq", VT_STR, "t007"),
            ("umki", VT_STR, "sreg,plcl,i003,phea,pman,stwp,i005,i002"),
            ("usei", VT_STR, ""),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "V"),
            ("utip", VT_STR, "Build Artificer |cffffcc00V|rault"),
            ("utub", VT_STR, "Runic supply depot offering scrolls, potions, Town Portals, and the Orb of Storms."),
        ]),

        # Tower: Tesla Turret (`t009`)
        ("hgtw", "t009", [
            ("unam", VT_STR, "Tesla Turret"),
            ("umdl", VT_STR, "buildings\\other\\TowerDefenseTower\\TowerDefenseTower.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNHumanWatchTower.blp"),
            ("usnd", VT_STR, "ArcaneTower"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 135), ("ulum", VT_INT, 80), ("ubld", VT_INT, 45),
            ("uhpm", VT_INT, 500), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("ureq", VT_STR, "t006"), ("uabi", VT_STR, "Abds,Adts"),
            ("ua1b", VT_INT, 22), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 5),
            ("ua1c", VT_UNREAL, 1.0), ("ua1r", VT_INT, 700), ("ua1t", VT_STR, "pierce"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\FarseerMissile\\FarseerMissile.mdl"),
            ("ua1z", VT_INT, 1500),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Build |cffffcc00T|resla Turret"),
            ("utub", VT_STR, "Arc-lightning defense spire with True Sight. Strikes ground and air units."),
        ]),

        # Caster/Flyer Sanctum: Arcane Conduit (`t018`)
        ("hars", "t018", [
            ("unam", VT_STR, "Arcane Conduit"),
            ("umdl", VT_STR, "buildings\\human\\ArcaneSanctum\\ArcaneSanctum.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNArcaneSanctum.blp"),
            ("usnd", VT_STR, "ArcaneSanctum"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 150), ("ulum", VT_INT, 140), ("ubld", VT_INT, 60),
            ("uhpm", VT_INT, 1100), ("udef", VT_INT, 5),
            ("ureq", VT_STR, "t002"), ("utra", VT_STR, "t014,t015"), ("ures", VT_STR, ""),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Build Arcane |cffffcc00C|ronduit"),
            ("utub", VT_STR, "Tier-2 Runic spire. Trains Rune Diviners (storm casters) and Gyro-Interceptors (magic flyers)."),
        ]),

        # Siege & T3 Champion Bay: Colossus Bay (`t019`)
        ("harm", "t019", [
            ("unam", VT_STR, "Colossus Bay"),
            ("umdl", VT_STR, "buildings\\human\\Workshop\\Workshop.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNWorkshop.blp"),
            ("usnd", VT_STR, "Workshop"),
            ("uclr", VT_INT, 190), ("uclg", VT_INT, 225), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 180), ("ulum", VT_INT, 140), ("ubld", VT_INT, 65),
            ("uhpm", VT_INT, 1200), ("udef", VT_INT, 5),
            ("ureq", VT_STR, "t002,t006"), ("utra", VT_STR, "t016,t017"), ("ures", VT_STR, ""),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Build Colossus |cffffcc00B|ray"),
            ("utub", VT_STR, "Heavy assembly bay. Deploys Siege Behemoths (T2 Artillery) and Titan Constructs (T3 Champions)."),
        ]),

        # ---- RUNEFORGED COMBAT UNITS (`t011..t017`) ----
        ("hfoo", "t011", [
            ("unam", VT_STR, "Runic Sentinel"),
            ("umdl", VT_STR, "units\\creeps\\IronGolem\\IronGolem.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNArmorGolem.blp"),
            ("usnd", VT_STR, "IronGolem"),
            ("usca", VT_REAL, 0.74),
            ("uclr", VT_INT, 210), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 130), ("ulum", VT_INT, 0), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 20),
            ("uhpm", VT_INT, 430), ("udef", VT_INT, 2), ("udty", VT_STR, "large"), ("umvs", VT_INT, 270),
            ("ua1b", VT_INT, 12), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 3), ("ua1c", VT_UNREAL, 1.30),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Deploy Runic |cffffcc00S|rentinel"),
            ("utub", VT_STR, "Armored Tier-1 iron-rune vanguard. Attacks land units."),
        ]),
        ("hrif", "t012", [
            ("unam", VT_STR, "Thunder Arquebusier"),
            ("umdl", VT_STR, "units\\human\\Rifleman\\Rifleman.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNRifleman.blp"),
            ("usnd", VT_STR, "Rifleman"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 200), ("ulum", VT_INT, 35), ("ufoo", VT_INT, 3), ("ubld", VT_INT, 26),
            ("uhpm", VT_INT, 535), ("udef", VT_INT, 0), ("udty", VT_STR, "medium"), ("umvs", VT_INT, 270),
            ("ureq", VT_STR, "t006"),
            ("ua1b", VT_INT, 21), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 6), ("ua1c", VT_UNREAL, 1.35),
            ("ua1r", VT_INT, 550),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Deploy |cffffcc00T|rhunder Arquebusier"),
            ("utub", VT_STR, "Runic marksman firing ionized rounds at ground and air enemies."),
        ]),
        ("hkni", "t013", [
            ("unam", VT_STR, "Stormforged Juggernaut"),
            ("umdl", VT_STR, "units\\creeps\\GolemStatue\\GolemStatue.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNGolemStormbolt.blp"),
            ("usnd", VT_STR, "IronGolem"),
            ("usca", VT_REAL, 0.88),
            ("uclr", VT_INT, 230), ("uclg", VT_INT, 195), ("uclb", VT_INT, 130),
            ("ugol", VT_INT, 240), ("ulum", VT_INT, 50), ("ufoo", VT_INT, 4), ("ubld", VT_INT, 32),
            ("uhpm", VT_INT, 860), ("udef", VT_INT, 3), ("udty", VT_STR, "large"), ("umvs", VT_INT, 290),
            ("ureq", VT_STR, "t002"),
            ("ua1b", VT_INT, 26), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 8), ("ua1c", VT_UNREAL, 1.55),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "J"),
            ("utip", VT_STR, "Deploy Stormforged |cffffcc00J|ruggernaut"),
            ("utub", VT_STR, "Tier-2 bronze-steel war golem built to crush enemy frontlines."),
        ]),
        ("hmpr", "t014", [
            ("unam", VT_STR, "Rune Diviner"),
            ("umdl", VT_STR, "units\\creeps\\RevenantOfTheWaves\\RevenantOfTheWaves.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNRevenant.blp"),
            ("usnd", VT_STR, "Revenant"),
            ("usca", VT_REAL, 0.78),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 240), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 145), ("ulum", VT_INT, 30), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 26),
            ("uhpm", VT_INT, 330), ("umpi", VT_INT, 175), ("umpm", VT_INT, 300), ("umpr", VT_UNREAL, 1.1),
            ("ureq", VT_STR, "t002"),
            ("ua1b", VT_INT, 10), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 3), ("ua1c", VT_UNREAL, 1.65),
            ("ua1m", VT_STR, "Abilities\\Weapons\\FarseerMissile\\FarseerMissile.mdl"),
            ("uabi", VT_STR, "Ahea,Aadm,Aihn"), ("udaa", VT_STR, "Ahea"), ("upgr", VT_STR, "R003"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "D"),
            ("utip", VT_STR, "Train Rune |cffffcc00D|riviner"),
            ("utub", VT_STR, "Storm-rune support caster with Runic Mend (Heal) and Abolish Magic."),
        ]),
        ("hdhw", "t015", [
            ("unam", VT_STR, "Gyro-Interceptor"),
            ("umdl", VT_STR, "units\\creeps\\BronzeDragonWelp\\BronzeDragonWelp.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNBronzeDragon.blp"),
            ("usnd", VT_STR, "Gyrocopter"),
            ("usca", VT_REAL, 0.85),
            ("ugol", VT_INT, 165), ("ulum", VT_INT, 40), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 28),
            ("uhpm", VT_INT, 450), ("umpi", VT_INT, 0), ("umpm", VT_INT, 0),
            ("udef", VT_INT, 1), ("udty", VT_STR, "light"), ("umvs", VT_INT, 320),
            ("ureq", VT_STR, "t002"),
            ("ua1b", VT_INT, 16), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 4), ("ua1c", VT_UNREAL, 1.60),
            ("ua1r", VT_INT, 450), ("ua1t", VT_STR, "magic"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\FarseerMissile\\FarseerMissile.mdl"),
            ("uabi", VT_STR, ""), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "I"),
            ("utip", VT_STR, "Deploy Gyro-|cffffcc00I|rnterceptor"),
            ("utub", VT_STR, "Runeforged aerial drake-craft dealing Magic damage to ground and air targets."),
        ]),
        ("hmtm", "t016", [
            ("unam", VT_STR, "Siege Behemoth"),
            ("umdl", VT_STR, "units\\creeps\\InfernalCannonCannon\\InfernalCannonCannon.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNInfernalCannon.blp"),
            ("usnd", VT_STR, "InfernalMachine"),
            ("usca", VT_REAL, 0.82),
            ("uclr", VT_INT, 215), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 210), ("ulum", VT_INT, 65), ("ufoo", VT_INT, 4), ("ubld", VT_INT, 36),
            ("uhpm", VT_INT, 590), ("udef", VT_INT, 2), ("udty", VT_STR, "heavy"), ("umvs", VT_INT, 225),
            ("ureq", VT_STR, "t002,t006"),
            ("ua1b", VT_INT, 46), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 12), ("ua1c", VT_UNREAL, 2.7),
            ("ua1r", VT_INT, 900), ("ua1t", VT_STR, "siege"),
            ("uabi", VT_STR, ""), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Deploy Siege |cffffcc00B|rehemoth"),
            ("utub", VT_STR, "Heavy Titan artillery cannon engineered to demolish enemy strongholds."),
        ]),
        ("hkni", "t017", [
            ("unam", VT_STR, "Titan Construct"),
            ("umdl", VT_STR, "units\\creeps\\RockGolem\\RockGolem.mdl"),
            ("uico", VT_STR, "ReplaceableTextures\\CommandButtons\\BTNRockGolem.blp"),
            ("usnd", VT_STR, "RockGolem"),
            ("usca", VT_REAL, 1.15),
            ("uclr", VT_INT, 235), ("uclg", VT_INT, 205), ("uclb", VT_INT, 145),
            ("ugol", VT_INT, 300), ("ulum", VT_INT, 90), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 44),
            ("uhpm", VT_INT, 1100), ("udef", VT_INT, 4), ("udty", VT_STR, "large"), ("umvs", VT_INT, 280),
            ("ureq", VT_STR, "t003"),
            ("ua1b", VT_INT, 33), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 8), ("ua1c", VT_UNREAL, 1.70),
            ("uabi", VT_STR, "ACcv,ACrk,Aihn"), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Awaken Titan |cffffcc00C|ronstruct"),
            ("utub", VT_STR, "Tier-3 towering Titan champion with Cleaving Blows and Resistant Skin."),
        ]),

        # ---- 4 RUNEFORGED HEROES (`T001..T004`) — ZERO `urev`! ----
        ("Hmkg", "T001", [
            ("unam", VT_STR, "Stormforged Prime"),
            ("upro", VT_STR, "Thorim'gar,Kaelen-7,Val'durin,Bael'grim"), ("upru", VT_INT, 4),
            ("usca", VT_REAL, 1.16),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "t002"), ("urq2", VT_STR, "t003"),
            ("uhab", VT_STR, "A012,A013,A014,A015"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 24), ("uagi", VT_INT, 14), ("uint", VT_INT, 17),
            ("ustp", VT_UNREAL, 3.0), ("uagp", VT_UNREAL, 1.5), ("uinp", VT_UNREAL, 1.8),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "P"),
            ("utip", VT_STR, "Summon Stormforged |cffffcc00P|rrime"),
            ("utpr", VT_STR, "Revive Stormforged |cffffcc00P|rrime"),
            ("utub", VT_STR, "Mighty Titan Strength Hero. Wields Thunderous Tectonics, Arc-Reactor Overload, Runic Aegis, and Orbital Hammer Protocol."),
        ]),
        ("Ntin", "T002", [
            ("unam", VT_STR, "Runesmith Highlord"),
            ("upro", VT_STR, "Arkhon,Mekka'tor,Ferrus,Voltan"), ("upru", VT_INT, 4),
            ("uclr", VT_INT, 210), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "t002"), ("urq2", VT_STR, "t003"),
            ("uhab", VT_STR, "A012,A013,A014,A015"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 18), ("uagi", VT_INT, 14), ("uint", VT_INT, 23),
            ("ustp", VT_UNREAL, 2.2), ("uagp", VT_UNREAL, 1.6), ("uinp", VT_UNREAL, 2.9),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Summon |cffffcc00R|runesmith Highlord"),
            ("utpr", VT_STR, "Revive |cffffcc00R|runesmith Highlord"),
            ("utub", VT_STR, "Master Artificer Intelligence Hero specializing in Runic Aegis, Arc-Reactor Overload, Tectonics, and Orbital Hammer."),
        ]),
        ("Nfir", "T003", [
            ("unam", VT_STR, "Plasma Vanguard"),
            ("upro", VT_STR, "Ionis,Hyperion,Aegis-IX,Sol'kar"), ("upru", VT_INT, 4),
            ("uclr", VT_INT, 130), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "t002"), ("urq2", VT_STR, "t003"),
            ("uhab", VT_STR, "A012,A013,A014,A015"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 17), ("uagi", VT_INT, 22), ("uint", VT_INT, 16),
            ("ustp", VT_UNREAL, 2.0), ("uagp", VT_UNREAL, 2.9), ("uinp", VT_UNREAL, 1.9),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "V"),
            ("utip", VT_STR, "Summon Plasma |cffffcc00V|ranguard"),
            ("utpr", VT_STR, "Revive Plasma |cffffcc00V|ranguard"),
            ("utub", VT_STR, "Ranged Arc-Plasma Agility Carry combining rapid ionized attacks with Runeforged abilities."),
        ]),
        ("Hamg", "T004", [
            ("unam", VT_STR, "Tempest Savant"),
            ("upro", VT_STR, "Zephyrus,Caelum,Aurelius,Kor'vash"), ("upru", VT_INT, 4),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "t002"), ("urq2", VT_STR, "t003"),
            ("uhab", VT_STR, "A012,A013,A014,A015"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 15), ("uagi", VT_INT, 15), ("uint", VT_INT, 25),
            ("ustp", VT_UNREAL, 1.9), ("uagp", VT_UNREAL, 1.5), ("uinp", VT_UNREAL, 3.1),
            ("ubpx", VT_INT, 3), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Summon Tempest |cffffcc00S|ravant"),
            ("utpr", VT_STR, "Revive Tempest |cffffcc00S|ravant"),
            ("utub", VT_STR, "Ranged Storm Intelligence Conduit commanding maximum-output Orbital Hammer and Tectonics."),
        ]),
    ]
    return entries


# ==============================================================================
# 2. 16 CUSTOM HERO ABILITIES (`war3map.w3a` v2 — `A000 .. A015`)
# ==============================================================================

def _make_ancl_skill(
    new_id: str,
    name: str,
    hotkey: str,
    slot_x: int,
    icon_stem: str,
    caster_mdx: str,
    target_type: int,     # 0=Instant, 1=Unit, 2=Point
    options_flags: int,   # 1=Visible, 3=Visible+AoECircle
    order_str: str,
    is_ult: bool,
    mana: Tuple[int, ...],
    cd: Tuple[float, ...],
    rng: Tuple[float, ...],
    area: Tuple[float, ...],
    research_desc: str,
    level_descs: Tuple[str, ...],
) -> Tuple[str, str, List[LevelModEntry]]:
    icon_path = f"ReplaceableTextures\\CommandButtons\\{icon_stem}.blp"
    levels = 1 if is_ult else 3
    mods: List[LevelModEntry] = [
        ("anam", VT_STR, 0, 0, name),
        ("aher", VT_INT, 0, 0, 1),
        ("aite", VT_INT, 0, 0, 0),
        ("alev", VT_INT, 0, 0, levels),
        ("arlv", VT_INT, 0, 0, 6 if is_ult else 1),
        ("alsk", VT_INT, 0, 0, 0 if is_ult else 2),
        ("abpx", VT_INT, 0, 0, slot_x),
        ("abpy", VT_INT, 0, 0, 2),
        ("arpx", VT_INT, 0, 0, slot_x),
        ("arpy", VT_INT, 0, 0, 0),
        ("aart", VT_STR, 0, 0, icon_path),
        ("arar", VT_STR, 0, 0, icon_path),
        ("acat", VT_STR, 0, 0, caster_mdx),
        ("atat", VT_STR, 0, 0, ""),
        ("aeat", VT_STR, 0, 0, ""),
        ("asat", VT_STR, 0, 0, ""),
        ("aani", VT_STR, 0, 0, "spell"),
        ("ahky", VT_STR, 0, 0, hotkey),
        ("arhk", VT_STR, 0, 0, hotkey),
        ("aret", VT_STR, 0, 0, f"Learn {name} [|cffffcc00{hotkey}|r] - [|cffffcc00Level %d|r]"),
        ("arut", VT_STR, 0, 0, research_desc),
    ]
    targs = "air,ground,enemy,neutral" if target_type == 1 else ""
    for lv in range(1, levels + 1):
        idx = lv - 1
        lvl_tag = "" if is_ult else f" - [|cffffcc00Level {lv}|r]"
        mods.extend([
            ("atp1", VT_STR,    lv, 0, f"{name} [|cffffcc00{hotkey}|r]{lvl_tag}"),
            ("aub1", VT_STR,    lv, 0, level_descs[idx]),
            ("amcs", VT_INT,    lv, 0, mana[idx]),
            ("acdn", VT_UNREAL, lv, 0, cd[idx]),
            ("aran", VT_UNREAL, lv, 0, rng[idx]),
            ("aare", VT_UNREAL, lv, 0, area[idx]),
            ("acas", VT_UNREAL, lv, 0, 0.0),
            ("adur", VT_UNREAL, lv, 0, 0.01),
            ("ahdu", VT_UNREAL, lv, 0, 0.01),
            ("atar", VT_STR,    lv, 0, targs),
            # `ANcl` DataA..DataF MUST set `data_ptr = 1..6` on EVERY level!
            ("Ncl1", VT_UNREAL, lv, 1, 0.28),           # Follow-through time
            ("Ncl2", VT_INT,    lv, 2, target_type),    # 0=Instant, 1=Unit, 2=Point
            ("Ncl3", VT_INT,    lv, 3, options_flags),  # 1=Visible, 3=Visible+AoE
            ("Ncl4", VT_UNREAL, lv, 4, 0.0),            # Art duration
            ("Ncl5", VT_INT,    lv, 5, 0),              # Disable other abilities = False!
            ("Ncl6", VT_STR,    lv, 6, order_str),      # Distinct native base order ID
        ])
    return ("ANcl", new_id, mods)


def build_ability_modifications() -> List[Tuple[str, str, List[LevelModEntry]]]:
    """Build all 16 Custom Hero Skills (`A000..A015`) across all 4 Custom Empires."""
    return [
        # ---- ABYSSAL TIDEBORN (`A000..A003`) ----
        _make_ancl_skill(
            "A000", "Maelstrom Vortex", "Q", 0, "BTN_WM_AbyssVortex", "WM_FX_Abyssal.mdx",
            2, 3, "flamestrike", False, (75, 85, 95), (11.0, 10.0, 9.0), (650.0, 650.0, 650.0), (275.0, 275.0, 275.0),
            "Summons a 3D Abyssal Maelstrom that pulls nearby enemies inward and deals vortex spell damage (+Primary Stat scaling).",
            (
                "Pulls enemies inward in 275 AoE and deals 88 (+Stat) spell damage.",
                "Pulls enemies inward in 275 AoE and deals 146 (+Stat) spell damage.",
                "Pulls enemies inward in 275 AoE and deals 204 (+Stat) spell damage.",
            ),
        ),
        _make_ancl_skill(
            "A001", "Riptide Prism Lance", "W", 1, "BTN_WM_AbyssLance", "WM_FX_Abyssal.mdx",
            1, 1, "chainlightning", False, (70, 80, 90), (9.0, 8.5, 8.0), (600.0, 600.0, 600.0), (0.0, 0.0, 0.0),
            "Hurls a crystalline prism lance that splits onto 2 nearby foes for 55% damage and heals the Hero.",
            (
                "Deals 107 (+Stat) damage, splits to 2 foes, and restores 45 HP.",
                "Deals 169 (+Stat) damage, splits to 2 foes, and restores 70 HP.",
                "Deals 231 (+Stat) damage, splits to 2 foes, and restores 95 HP.",
            ),
        ),
        _make_ancl_skill(
            "A002", "Abyssal Carapace Pulse", "E", 2, "BTN_WM_AbyssCarapace", "WM_FX_Abyssal.mdx",
            0, 1, "thunderclap", False, (65, 75, 85), (12.0, 11.0, 10.0), (0.0, 0.0, 0.0), (300.0, 300.0, 300.0),
            "Envelops the Hero in a glowing leviathan carapace, healing the Hero and blasting surrounding enemies.",
            (
                "Restores 100 (+Stat) HP and deals 70 (+Stat) AoE tidal damage.",
                "Restores 155 (+Stat) HP and deals 115 (+Stat) AoE tidal damage.",
                "Restores 210 (+Stat) HP and deals 160 (+Stat) AoE tidal damage.",
            ),
        ),
        _make_ancl_skill(
            "A003", "Cataclysmic Tsunami", "R", 3, "BTN_WM_AbyssTsunami", "WM_FX_Abyssal.mdx",
            2, 3, "monsoon", True, (150,), (115.0,), (700.0,), (380.0,),
            "Ultimate: Unleashes 3 expanding Abyssal Tsunami waves dealing 285 total AoE damage to foes and healing allies for 138 HP.",
            ("3 Tsunami pulses deal 285 total AoE damage to enemies and restore 138 HP to allies in 380 AoE.",),
        ),

        # ---- SUNFURY IMPERIUM (`A004..A007`) ----
        _make_ancl_skill(
            "A004", "Solar Flare Sigil", "Q", 0, "BTN_WM_SolarSigil", "WM_FX_Solar.mdx",
            2, 3, "flamestrike", False, (75, 85, 95), (11.0, 10.0, 9.0), (650.0, 650.0, 650.0), (265.0, 265.0, 265.0),
            "Engraves a blazing 3D Solar Mandala that scorches enemies and burns enemy mana.",
            (
                "Deals 95 (+Stat) AoE damage and burns 33 Mana in 265 radius.",
                "Deals 155 (+Stat) AoE damage and burns 51 Mana in 265 radius.",
                "Deals 215 (+Stat) AoE damage and burns 69 Mana in 265 radius.",
            ),
        ),
        _make_ancl_skill(
            "A005", "Phoenix Wing Dash", "W", 1, "BTN_WM_SolarDash", "WM_FX_Solar.mdx",
            2, 1, "blink", False, (65, 70, 75), (11.0, 9.5, 8.0), (550.0, 550.0, 550.0), (260.0, 260.0, 260.0),
            "Surges on blazing Phoenix wings to the target location, healing the Hero and scorching nearby enemies on arrival.",
            (
                "Teleports up to 550 range, restores 110 HP, and deals 75 (+Stat) arrival damage.",
                "Teleports up to 550 range, restores 165 HP, and deals 125 (+Stat) arrival damage.",
                "Teleports up to 550 range, restores 220 HP, and deals 175 (+Stat) arrival damage.",
            ),
        ),
        _make_ancl_skill(
            "A006", "Sunblade Judgment", "E", 2, "BTN_WM_SolarJudgment", "WM_FX_Solar.mdx",
            1, 1, "chainlightning", False, (70, 80, 90), (9.5, 9.0, 8.5), (575.0, 575.0, 575.0), (195.0, 195.0, 195.0),
            "Calls down a radiant 4-pillar Sunblade cross on an enemy, dealing heavy burst damage plus 45% AoE splash.",
            (
                "Deals 115 (+Stat) primary damage and 45% splash in 195 AoE.",
                "Deals 180 (+Stat) primary damage and 45% splash in 195 AoE.",
                "Deals 245 (+Stat) primary damage and 45% splash in 195 AoE.",
            ),
        ),
        _make_ancl_skill(
            "A007", "Supernova Crown", "R", 3, "BTN_WM_SolarSupernova", "WM_FX_Solar.mdx",
            2, 3, "monsoon", True, (155,), (115.0,), (700.0,), (400.0,),
            "Ultimate: Ignites a 3-wave Solar Supernova dealing 300 AoE damage to enemies and restoring 165 HP + 75 Mana to allies.",
            ("3 Supernova pulses deal 300 total AoE damage to enemies and restore 165 HP & 75 Mana to allies.",),
        ),

        # ---- VOIDBORN LEGION (`A008..A011`) ----
        _make_ancl_skill(
            "A008", "Event Horizon", "Q", 0, "BTN_WM_VoidHorizon", "WM_FX_Void.mdx",
            2, 3, "flamestrike", False, (75, 85, 95), (11.0, 10.0, 9.0), (650.0, 650.0, 650.0), (280.0, 280.0, 280.0),
            "Rips open a black-violet singularity that implodes enemies 110u inward and deals astral damage.",
            (
                "Implodes enemies inward in 280 AoE and deals 90 (+Stat) damage.",
                "Implodes enemies inward in 280 AoE and deals 148 (+Stat) damage.",
                "Implodes enemies inward in 280 AoE and deals 206 (+Stat) damage.",
            ),
        ),
        _make_ancl_skill(
            "A009", "Rift Sever", "W", 1, "BTN_WM_VoidSever", "WM_FX_Void.mdx",
            2, 1, "blink", False, (70, 80, 90), (9.5, 8.5, 8.0), (550.0, 550.0, 550.0), (200.0, 200.0, 200.0),
            "Slashes a 5-node dimensional rift corridor forward, dealing astral damage and siphoning 12 Mana per enemy struck.",
            (
                "Tears a 525-range void corridor dealing 98 (+Stat) damage and siphoning Mana.",
                "Tears a 525-range void corridor dealing 158 (+Stat) damage and siphoning Mana.",
                "Tears a 525-range void corridor dealing 218 (+Stat) damage and siphoning Mana.",
            ),
        ),
        _make_ancl_skill(
            "A010", "Entropy Shroud", "E", 2, "BTN_WM_VoidShroud", "WM_FX_Void.mdx",
            0, 1, "thunderclap", False, (60, 70, 80), (12.0, 11.0, 10.0), (0.0, 0.0, 0.0), (290.0, 290.0, 290.0),
            "Surrounds the Hero in an octagonal star-ring, restoring both HP and Mana while shocking nearby foes.",
            (
                "Restores 95 (+Stat) HP & 45 Mana and deals 68 (+Stat) AoE damage.",
                "Restores 145 (+Stat) HP & 65 Mana and deals 112 (+Stat) AoE damage.",
                "Restores 195 (+Stat) HP & 85 Mana and deals 156 (+Stat) AoE damage.",
            ),
        ),
        _make_ancl_skill(
            "A011", "Cosmic Collapse", "R", 3, "BTN_WM_VoidCollapse", "WM_FX_Void.mdx",
            2, 3, "monsoon", True, (155,), (115.0,), (700.0,), (390.0,),
            "Ultimate: 3 collapsing Void star-waves pull enemies inward, deal 294 AoE damage, and drain 90 Mana.",
            ("3 Cosmic Collapse waves pull enemies inward, deal 294 AoE damage, and drain 90 Mana.",),
        ),

        # ---- RUNEFORGED BASTION (`A012..A015`) ----
        _make_ancl_skill(
            "A012", "Thunderous Tectonics", "Q", 0, "BTN_WM_RunicTectonics", "WM_FX_Runic.mdx",
            2, 3, "flamestrike", False, (75, 85, 95), (11.0, 10.0, 9.0), (625.0, 625.0, 625.0), (275.0, 275.0, 275.0),
            "Slams a 3D Runic Matrix onto the battlefield, dealing tectonic damage and knocking enemies outward.",
            (
                "Deals 92 (+Stat) AoE damage and blasts enemies outward in 275 radius.",
                "Deals 150 (+Stat) AoE damage and blasts enemies outward in 275 radius.",
                "Deals 208 (+Stat) AoE damage and blasts enemies outward in 275 radius.",
            ),
        ),
        _make_ancl_skill(
            "A013", "Arc-Reactor Overload", "W", 1, "BTN_WM_RunicOverload", "WM_FX_Runic.mdx",
            1, 1, "chainlightning", False, (70, 80, 90), (9.5, 9.0, 8.5), (575.0, 575.0, 575.0), (0.0, 0.0, 0.0),
            "Strikes an enemy with an ionized orbital bolt while energizing nearby allied units around the Hero.",
            (
                "Deals 112 (+Stat) target damage and restores 42 HP to nearby allies.",
                "Deals 176 (+Stat) target damage and restores 64 HP to nearby allies.",
                "Deals 240 (+Stat) target damage and restores 86 HP to nearby allies.",
            ),
        ),
        _make_ancl_skill(
            "A014", "Runic Aegis Matrix", "E", 2, "BTN_WM_RunicAegis", "WM_FX_Runic.mdx",
            0, 1, "thunderclap", False, (65, 75, 85), (12.0, 11.0, 10.0), (0.0, 0.0, 0.0), (285.0, 285.0, 285.0),
            "Activates an interlocking bronze-cyan Runic forcefield, repairing the Hero and discharging arc lightning.",
            (
                "Restores 113 (+Stat) HP and deals 66 (+Stat) AoE shock damage.",
                "Restores 171 (+Stat) HP and deals 108 (+Stat) AoE shock damage.",
                "Restores 229 (+Stat) HP and deals 150 (+Stat) AoE shock damage.",
            ),
        ),
        _make_ancl_skill(
            "A015", "Orbital Hammer Protocol", "R", 3, "BTN_WM_RunicOrbital", "WM_FX_Runic.mdx",
            2, 3, "monsoon", True, (155,), (115.0,), (700.0,), (400.0,),
            "Ultimate: Locks 3 concentric Titan targeting matrices onto a 400-AoE zone, calling down 300 orbital plasma damage.",
            ("Calls down 3 Orbital Hammer plasma strikes dealing 300 total AoE damage in 400 radius.",),
        ),
    ]


# ==============================================================================
# 3. CUSTOM NON-CLASSIC UI SKIN (`war3mapSkin.txt`)
# ==============================================================================

def serialize_war3map_skin() -> bytes:
    """
    Generate `war3mapSkin.txt` replacing classic WC3 brown dialog backgrounds,
    resource bar icons, and header strings with our Dark Astral-Gold theme.
    Safe 100% across Classic 1.26a/1.27b & Reforged (never overrides 9-slice borders!).
    """
    lines = [
        "[CustomSkin]",
        "EscMenuBackground=UI\\CrownUI\\MenuBG.blp",
        "QuestDialogBackground=UI\\CrownUI\\MenuBG.blp",
        "GoldIcon=UI\\CrownUI\\IconGold.blp",
        "LumberIcon=UI\\CrownUI\\IconLumber.blp",
        "SupplyIcon=UI\\CrownUI\\IconSupply.blp",
        "UpkeepIcon=UI\\CrownUI\\IconSupply.blp",
        "",
        "[FrameDef]",
        "UPKEEP_NONE=|cff38bdf8★ CROWN OF WARMAHDI ★|r",
        "UPKEEP_LOW=|cfffbbf24⚡ LOW WAR TAX (50+)|r",
        "UPKEEP_HIGH=|cfff43f5e🔥 HIGH WAR TAX (80+)|r",
        "RESOURCE_UBERTIP_GOLD=|cffffd700Imperial Gold|r — Harvested from Gold Mines & the Central Crown Shrine.",
        "RESOURCE_UBERTIP_LUMBER=|cff34d399Astral Timber|r — Harvested from Bioluminescent Canopy Forests.",
        "RESOURCE_UBERTIP_UPKEEP=|cffc084fcEmpire Supply|r — Build Pylons / Farms / Coral Beds / Dynamo Cores to expand your Legions.",
        "COLON_GOLD=|cffffd700Gold:|r",
        "COLON_LUMBER=|cff34d399Timber:|r",
        "COLON_FOOD=|cffc084fcSupply:|r",
        "UPPER_BUTTON_QUEST_TIP=|cffffd700Imperial Codex|r (|cffffcc00F9|r)",
        "UPPER_BUTTON_MENU_TIP=|cff38bdf8Command Menu|r (|cffffcc00F10|r)",
        "UPPER_BUTTON_ALLIES_TIP=|cffc084fcWar Pact & Tribute|r (|cffffcc00F11|r)",
        "UPPER_BUTTON_CHAT_TIP=|cff94a3b8Battle Log|r (|cffffcc00F12|r)",
        "",
    ]
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


# ==============================================================================
# 4. DEDICATED `.ai` SCRIPTS FOR VOIDBORN LEGION & RUNEFORGED BASTION
# ==============================================================================

def _build_custom_faction_ai(
    title: str,
    ai_display_name: str,
    worker: str,
    h1: str, h2: str, h3: str,
    supply: str, rax: str, armory: str, altar: str, shop: str, tower: str,
    sanctum: str, heavy_bay: str,
    u_melee: str, u_range: str, u_heavy: str, u_caster: str, u_flyer: str, u_siege: str, u_champ: str,
    hero1: str, hero2: str, hero3: str, hero4: str,
    sk_q: str, sk_w: str, sk_e: str, sk_r: str,
    upg_atk: str, upg_arm: str,
) -> str:
    return f"""// ============================================================================
// {title} — Pro-Level 8-Player Melee AI (`common.ai` State Machine)
// ============================================================================
globals
    boolean cf_tier2_done = false
    boolean cf_tier3_done = false

    constant integer CF_WORKER    = '{worker}'
    constant integer CF_HALL_T1   = '{h1}'
    constant integer CF_HALL_T2   = '{h2}'
    constant integer CF_HALL_T3   = '{h3}'
    constant integer CF_SUPPLY    = '{supply}'
    constant integer CF_RAX       = '{rax}'
    constant integer CF_ARMORY    = '{armory}'
    constant integer CF_ALTAR     = '{altar}'
    constant integer CF_SHOP      = '{shop}'
    constant integer CF_TOWER     = '{tower}'
    constant integer CF_SANCTUM   = '{sanctum}'
    constant integer CF_HEAVY_BAY = '{heavy_bay}'

    constant integer CF_MELEE     = '{u_melee}'
    constant integer CF_RANGE     = '{u_range}'
    constant integer CF_HEAVY     = '{u_heavy}'
    constant integer CF_CASTER    = '{u_caster}'
    constant integer CF_FLYER     = '{u_flyer}'
    constant integer CF_SIEGE     = '{u_siege}'
    constant integer CF_CHAMP     = '{u_champ}'

    constant integer CF_HERO_1    = '{hero1}'
    constant integer CF_HERO_2    = '{hero2}'
    constant integer CF_HERO_3    = '{hero3}'
    constant integer CF_HERO_4    = '{hero4}'

    constant integer CF_UPG_ATK   = '{upg_atk}'
    constant integer CF_UPG_ARM   = '{upg_arm}'
endglobals

function CFHallCount takes boolean doneOnly returns integer
    if doneOnly then
        return GetUnitCountDone(CF_HALL_T1) + GetUnitCountDone(CF_HALL_T2) + GetUnitCountDone(CF_HALL_T3)
    endif
    return GetUnitCount(CF_HALL_T1) + GetUnitCount(CF_HALL_T2) + GetUnitCount(CF_HALL_T3)
endfunction

function CFTier2Count takes boolean doneOnly returns integer
    if doneOnly then
        return GetUnitCountDone(CF_HALL_T2) + GetUnitCountDone(CF_HALL_T3)
    endif
    return GetUnitCount(CF_HALL_T2) + GetUnitCount(CF_HALL_T3)
endfunction

function CFTier3Count takes boolean doneOnly returns integer
    if doneOnly then
        return GetUnitCountDone(CF_HALL_T3)
    endif
    return GetUnitCount(CF_HALL_T3)
endfunction

function CFNeedUnit takes integer qty, integer id, integer town returns nothing
    local integer have = GetUnitCount(id)
    if have < qty then
        call SetProduce(qty - have, id, town)
    endif
endfunction

function CFNeedUpgrade takes integer lvl, integer id returns nothing
    if GetUpgradeLevel(id) < lvl then
        call SetUpgrade(id)
    endif
endfunction

function CFSetSkills takes nothing returns nothing
    set skill[ 1] = '{sk_q}'
    set skill[ 2] = '{sk_w}'
    set skill[ 3] = '{sk_q}'
    set skill[ 4] = '{sk_e}'
    set skill[ 5] = '{sk_q}'
    set skill[ 6] = '{sk_r}'
    set skill[ 7] = '{sk_w}'
    set skill[ 8] = '{sk_w}'
    set skill[ 9] = '{sk_e}'
    set skill[10] = '{sk_e}'
endfunction

function ChooseCFHeroes takes nothing returns nothing
    local integer roll = GetRandomInt(1, 4)
    if roll == 1 then
        set hero_id  = CF_HERO_1
        set hero_id2 = CF_HERO_2
        set hero_id3 = CF_HERO_3
    elseif roll == 2 then
        set hero_id  = CF_HERO_2
        set hero_id2 = CF_HERO_4
        set hero_id3 = CF_HERO_1
    elseif roll == 3 then
        set hero_id  = CF_HERO_3
        set hero_id2 = CF_HERO_1
        set hero_id3 = CF_HERO_4
    else
        set hero_id  = CF_HERO_4
        set hero_id2 = CF_HERO_3
        set hero_id3 = CF_HERO_2
    endif

    call CFSetSkills()
    call SetSkillArray(1, hero_id)
    call CFSetSkills()
    call SetSkillArray(2, hero_id2)
    call CFSetSkills()
    call SetSkillArray(3, hero_id3)
endfunction

function CFHarvestLoop takes nothing returns nothing
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

        set workers = GetUnitCountDone(CF_WORKER)
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

function CFBuildLoop takes nothing returns nothing
    local unit expPeon
    local integer mines
    loop
        call InitBuildArray()

        set cf_tier2_done = (CFTier2Count(true) >= 1)
        set cf_tier3_done = (CFTier3Count(true) >= 1)
        set mines = GetMinesOwned()

        if CFHallCount(false) < 1 then
            call SetProduce(1, CF_HALL_T1, -1)
        endif

        if FoodUsed() + 6 >= FoodCap() and FoodCap() < 100 and GetUnitCount(CF_SUPPLY) < 11 then
            call CFNeedUnit(GetUnitCountDone(CF_SUPPLY) + 1, CF_SUPPLY, -1)
        endif

        if mines >= 2 then
            call CFNeedUnit(18, CF_WORKER, -1)
        else
            call CFNeedUnit(13, CF_WORKER, -1)
        endif

        call CFNeedUnit(1, CF_SUPPLY, -1)
        call CFNeedUnit(1, CF_ALTAR, -1)
        call CFNeedUnit(1, CF_RAX, -1)
        call CFNeedUnit(2, CF_SUPPLY, -1)

        if GetUnitCountDone(CF_ALTAR) >= 1 then
            call CFNeedUnit(1, hero_id, -1)
            call CFNeedUnit(1, CF_SHOP, -1)
        endif

        if GetUnitCountDone(CF_RAX) >= 1 then
            call CFNeedUnit(4, CF_MELEE, -1)
            call CFNeedUnit(3, CF_RANGE, -1)
            call CFNeedUnit(1, CF_ARMORY, -1)
            call CFNeedUnit(1, CF_TOWER, 0)
        endif

        if GetUnitCountDone(CF_ARMORY) >= 1 then
            call CFNeedUpgrade(1, CF_UPG_ATK)
            call CFNeedUpgrade(1, CF_UPG_ARM)
        endif

        if GetUnitCountDone(CF_HALL_T1) >= 1 and CFTier2Count(false) == 0 and GetUnitCountDone(CF_RAX) >= 1 then
            call SetProduce(1, CF_HALL_T2, -1)
        endif

        if cf_tier2_done then
            call CFNeedUnit(1, hero_id2, -1)
            call CFNeedUnit(3, CF_SUPPLY, -1)
            call CFNeedUnit(1, CF_SANCTUM, -1)
            call CFNeedUnit(1, CF_HEAVY_BAY, -1)
            call CFNeedUnit(3, CF_HEAVY, -1)
            call CFNeedUnit(2, CF_RAX, -1)

            if GetUnitCountDone(CF_SANCTUM) >= 1 then
                call CFNeedUnit(3, CF_CASTER, -1)
                call CFNeedUnit(2, CF_FLYER, -1)
            endif
            if GetUnitCountDone(CF_HEAVY_BAY) >= 1 then
                call CFNeedUnit(2, CF_SIEGE, -1)
            endif
            if GetUnitCountDone(CF_ARMORY) >= 1 then
                call CFNeedUpgrade(2, CF_UPG_ATK)
                call CFNeedUpgrade(2, CF_UPG_ARM)
            endif

            if mines < 2 and CFHallCount(false) < 2 and GetGold() >= 340 then
                set expPeon = GetExpansionPeon()
                if expPeon != null then
                    call SetExpansion(expPeon, CF_HALL_T1)
                endif
            endif

            if GetUnitCountDone(CF_HALL_T2) >= 1 and CFTier3Count(false) == 0 and GetUnitCountDone(CF_SANCTUM) >= 1 then
                call SetProduce(1, CF_HALL_T3, -1)
            endif
        endif

        if cf_tier3_done then
            call CFNeedUnit(1, hero_id3, -1)
            call CFNeedUnit(5, CF_SUPPLY, -1)
            if GetUnitCountDone(CF_HEAVY_BAY) >= 1 then
                call CFNeedUnit(2, CF_CHAMP, -1)
            endif
            if GetUnitCountDone(CF_ARMORY) >= 1 then
                call CFNeedUpgrade(3, CF_UPG_ATK)
                call CFNeedUpgrade(3, CF_UPG_ARM)
            endif
        endif

        call Sleep(3)
    endloop
endfunction

function CFAttackWave takes integer maxQty, integer unitId returns nothing
    local integer have = GetUnitCountDone(unitId)
    if have <= 0 then
        return
    endif
    if have > maxQty then
        set have = maxQty
    endif
    call SetAssaultGroup(have, have, unitId)
endfunction

function CFAttackLoop takes nothing returns nothing
    local boolean needsExp
    local boolean hasSiege
    local boolean majorOk
    local boolean airUnits
    local integer armyReady

    call Sleep(24)
    loop
        loop
            set armyReady = GetUnitCountDone(hero_id) + GetUnitCountDone(hero_id2) + GetUnitCountDone(hero_id3)
            exitwhen armyReady >= 1 and (GetUnitCountDone(CF_MELEE) + GetUnitCountDone(CF_HEAVY) + GetUnitCountDone(CF_RANGE)) >= 4
            exitwhen (GetUnitCountDone(CF_MELEE) + GetUnitCountDone(CF_HEAVY) + GetUnitCountDone(CF_RANGE)) >= 6
            call Sleep(4)
        endloop

        call InitAssaultGroup()
        call CFAttackWave(1, hero_id)
        call CFAttackWave(1, hero_id2)
        call CFAttackWave(1, hero_id3)
        call CFAttackWave(4, CF_MELEE)
        call CFAttackWave(4, CF_RANGE)
        call CFAttackWave(3, CF_HEAVY)
        call CFAttackWave(3, CF_CASTER)
        call CFAttackWave(2, CF_FLYER)
        call CFAttackWave(2, CF_SIEGE)
        call CFAttackWave(2, CF_CHAMP)

        set needsExp = (GetMinesOwned() < 2 and cf_tier2_done)
        set hasSiege = (GetUnitCountDone(CF_SIEGE) >= 1 or GetUnitCountDone(CF_CHAMP) >= 1)
        set majorOk  = (cf_tier2_done or (GetUnitCountDone(CF_MELEE) + GetUnitCountDone(CF_RANGE)) >= 6)
        set airUnits = (GetUnitCountDone(CF_FLYER) >= 2 and GetUnitCountDone(CF_MELEE) == 0 and GetUnitCountDone(CF_HEAVY) == 0)

        call SingleMeleeAttack(needsExp, hasSiege, majorOk, airUnits)
        call Sleep(5)
    endloop
endfunction

function main takes nothing returns nothing
    local boolean isNewbie = (MeleeDifficulty() == MELEE_NEWBIE)

    call InitAI()
    call SetPlayerName(ai_player, "{ai_display_name}")
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

    set racial_farm = CF_SUPPLY
    call ChooseCFHeroes()
    call SetHeroLevels(function SkillArrays)

    call CreateCaptains()
    call Sleep(0.1)

    call StartThread(function CFHarvestLoop)
    call StartThread(function CFBuildLoop)
    call CFAttackLoop()
endfunction
"""


def generate_voidborn_ai_script() -> str:
    return _build_custom_faction_ai(
        "Voidborn Legion (`voidborn_melee.ai`)",
        "Voidborn Legion AI",
        "v010", "v001", "v002", "v003",
        "v004", "v005", "v006", "v007", "v008", "v009", "v018", "v019",
        "v011", "v012", "v013", "v014", "v015", "v016", "v017",
        "V001", "V002", "V003", "V004",
        "A008", "A009", "A010", "A011",
        "R000", "R001",
    )


def generate_runeforged_ai_script() -> str:
    return _build_custom_faction_ai(
        "Runeforged Bastion (`runeforged_melee.ai`)",
        "Runeforged Bastion AI",
        "t010", "t001", "t002", "t003",
        "t004", "t005", "t006", "t007", "t008", "t009", "t018", "t019",
        "t011", "t012", "t013", "t014", "t015", "t016", "t017",
        "T001", "T002", "T003", "T004",
        "A012", "A013", "A014", "A015",
        "R002", "R003",
    )
