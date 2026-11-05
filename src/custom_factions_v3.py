#!/usr/bin/env python3
"""
v5 Master Expansion Module for `(8) Crown of WarMahdi`:
  - Two complete, tournament-balanced Custom Playable Empires with race-specific
    Build mechanics, faction-appropriate models, and model-matched native icons:
      7. Voidborn Legion (`v001..v019`, Heroes `V001..V004`, Upgrades `R000..R001`)
         -> Undead-style Dimensional Rift Build (`CommandBasicStructUndead`) on normal
            ground (`upar=""`, zero Blight required)!
      8. Runeforged Bastion (`t001..t019`, Heroes `T001..T004`, Upgrades `R002..R003`)
         -> Orc-style Internal Foundry Assembly (`CommandBasicStructOrc`) with authentic
            Clockwork/Titan/Arcane models and model-matched native icons.
  - `war3map.w3a` (v2) generator for ALL **64 Unique Custom Hero Skills (`A000..A063`)**
    (16 Custom Heroes x 4 Exclusive Skills = ZERO shared hero skills anywhere!), each
    paired with a stock Warcraft III command button selected for its actual effect.
  - `war3mapSkin.txt` Full Custom UI Overhaul (`[CustomSkin]` + `[FrameDef]`):
      * Custom Animated Mouse Cursor (`UI\\Cursor\\HumanCursor.mdl` + 4 racial BLPs)
      * Custom RPG Infocard Damage Type, Armor Type & Hero Attribute (`STR/AGI/INT`) icons
      * Custom Command Card Action Buttons + 5 Race-Specific Worker `Build` Buttons
      * Custom Resource Bar & Dark Obsidian-Gold Console / Tooltip styling
  - Updated `.ai` melee scripts (`voidborn_melee.ai` & `runeforged_melee.ai`) with
    per-hero unique skill learning tables.
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

BTN_PREFIX = "ReplaceableTextures\\CommandButtons\\"


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
        # FACTION 7: VOIDBORN LEGION (`v010` Void Thrall — Dimensional Rift Build!)
        #   Row 0: (0,0) v001 | (1,0) v004 | (2,0) v005 | (3,0) v006
        #   Row 1: (0,1) v007 | (1,1) v008 | (2,1) v009
        #   Row 2: (0,2) v018 | (1,2) v019
        # ======================================================================

        # Worker: Void Thrall (`v010`, parent `uaco` — `urac="undead"` so it uses our
        # custom Void-Rift Build icon `CommandBasicStructUndead` and opens dimensional
        # warp rifts without standing inside hammering!)
        ("uaco", "v010", [
            ("unam", VT_STR, "Void Thrall"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "Peon,undead"),
            ("umdl", VT_STR, "units\\creeps\\VoidWalker\\VoidWalker.mdl"),
            ("usnd", VT_STR, "ObsidianDestroyer"),
            ("usca", VT_REAL, 0.72),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 130), ("uclb", VT_INT, 255),
            ("ubui", VT_STR, "v001,v004,v005,v006,v007,v008,v009,v018,v019"),
            ("ugol", VT_INT, 75), ("ulum", VT_INT, 0), ("ufoo", VT_INT, 1), ("ubld", VT_INT, 15),
            ("uhpm", VT_INT, 230), ("uhpr", VT_UNREAL, 0.35), ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 0), ("udty", VT_STR, "medium"), ("umvs", VT_INT, 195),
            ("uabi", VT_STR, "Ahar,Arst,Aihn"),
            ("upgr", VT_STR, "Rhpm"),
            ("uaen", VT_INT, 1), ("ua1t", VT_STR, "normal"),
            ("ua1b", VT_INT, 6), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 2), ("ua1c", VT_UNREAL, 1.9),
            ("ua1g", VT_STR, "ground,structure,debris,item,ward"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Summon Void |cffffcc00T|rhrall"),
            ("utub", VT_STR, "Astral rift-worker. Harvests Gold and Lumber normally and warps Voidborn structures into reality through dimensional rifts without staying inside."),
        ]),

        # Tier 1/2/3 Void Halls (`v001 -> v002 -> v003` — `upar=""` so ZERO Blight needed, `Argl` returns Gold+Lumber!)
        ("unpl", "v001", [
            ("unam", VT_STR, "Void Nexus"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "TownHall,undead,Mechanical"),
            ("upar", VT_STR, ""), ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\undead\\Necropolis\\Necropolis.mdl"),
            ("usnd", VT_STR, "Necropolis"),
            ("uclr", VT_INT, 175), ("uclg", VT_INT, 100), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 385), ("ulum", VT_INT, 185), ("ubld", VT_INT, 115),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 1550), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "v010"), ("ures", VT_STR, "Rhpm"), ("uupt", VT_STR, "v002"),
            ("uabi", VT_STR, "Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "N"),
            ("utip", VT_STR, "Warp Void |cffffcc00N|rexus"),
            ("utub", VT_STR, "Primary citadel of the Voidborn Legion. Summons Void Thralls and receives harvested Gold and Lumber. Upgrades to Astral Riftcore."),
        ]),
        ("unp1", "v002", [
            ("unam", VT_STR, "Astral Riftcore"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "TownHall,undead,Mechanical"),
            ("upar", VT_STR, ""), ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\DarkPortal\\DarkPortal.mdl"),
            ("usnd", VT_STR, "Necropolis"),
            ("usca", VT_REAL, 0.68),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 320), ("ulum", VT_INT, 190), ("ubld", VT_INT, 115),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 1850), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "v010"), ("ures", VT_STR, "Rhpm"), ("uupt", VT_STR, "v003"), ("ureq", VT_STR, ""),
            ("uaen", VT_INT, 0),
            ("uabi", VT_STR, "Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Astral Riftcore"),
            ("utub", VT_STR, "Tier-2 Void citadel. Unlocks Sanctum of Stars, Oblivion Pit, Dread Enforcers, and a 2nd Altar Hero."),
        ]),
        ("unp2", "v003", [
            ("unam", VT_STR, "Citadel of Oblivion"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "TownHall,undead,Mechanical"),
            ("upar", VT_STR, ""), ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\DarkPortal2\\DarkPortal2.mdl"),
            ("usnd", VT_STR, "Necropolis"),
            ("usca", VT_REAL, 0.76),
            ("uclr", VT_INT, 210), ("uclg", VT_INT, 130), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 360), ("ulum", VT_INT, 210), ("ubld", VT_INT, 115),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 2200), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "v010"), ("ures", VT_STR, "Rhpm"), ("uupt", VT_STR, ""), ("ureq", VT_STR, "v007"),
            ("uaen", VT_INT, 0),
            ("uabi", VT_STR, "Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Citadel of Oblivion"),
            ("utub", VT_STR, "Tier-3 Void apex stronghold. Unlocks Oblivion Colossi, Tier-3 Void upgrades, Orb of Oblivion, and a 3rd Hero."),
        ]),

        # Supply: Astral Pylon (`v004`, +9 Food — Ancient Nerubian Obsidian Pylon!)
        ("uzig", "v004", [
            ("unam", VT_STR, "Astral Pylon"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "undead,mechanical"),
            ("upar", VT_STR, ""), ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\NerubianZiggurat\\NerubianZiggurat.mdl"),
            ("usnd", VT_STR, "Ziggurat"),
            ("usca", VT_REAL, 0.86),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 90), ("ulum", VT_INT, 25), ("ubld", VT_INT, 32),
            ("ufma", VT_INT, 9), ("uhpm", VT_INT, 520), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("uupt", VT_STR, ""), ("uabi", VT_STR, ""),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "P"),
            ("utip", VT_STR, "Warp Astral |cffffcc00P|rylon"),
            ("utub", VT_STR, "Channels cosmic rift energy, providing 9 Food to sustain your Voidborn forces."),
        ]),

        # Barracks: Rift Gate (`v005` — Blazing Dimensional Demon Gate!)
        ("usep", "v005", [
            ("unam", VT_STR, "Rift Gate"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "undead,mechanical"),
            ("upar", VT_STR, ""), ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\demon\\DemonGate\\DemonGate.mdl"),
            ("usnd", VT_STR, "Crypt"),
            ("usca", VT_REAL, 0.85),
            ("uclr", VT_INT, 190), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 160), ("ulum", VT_INT, 60), ("ubld", VT_INT, 58),
            ("uhpm", VT_INT, 1300), ("udef", VT_INT, 5),
            ("utra", VT_STR, "v011,v012,v013"), ("ures", VT_STR, ""), ("uabi", VT_STR, ""),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Warp Rift |cffffcc00G|rate"),
            ("utub", VT_STR, "Primary dimensional war-gate. Summons Void Zealots (T1), Astral Arbalists (req Crucible), and Dread Enforcers (T2)."),
        ]),

        # Armory + Lumber Drop: Obsidian Crucible (`v006` — Sacrificial Void Vortex!)
        ("ugrv", "v006", [
            ("unam", VT_STR, "Obsidian Crucible"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "undead,mechanical"),
            ("upar", VT_STR, ""), ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\undead\\SacrificialPit\\SacrificialPit.mdl"),
            ("usnd", VT_STR, "Graveyard"),
            ("uclr", VT_INT, 180), ("uclg", VT_INT, 105), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 140), ("ulum", VT_INT, 60), ("ubld", VT_INT, 52),
            ("uhpm", VT_INT, 1200), ("udef", VT_INT, 5),
            ("ures", VT_STR, "R000,R001"), ("ureq", VT_STR, "v001"),
            ("uabi", VT_STR, "Arlm"),
            ("ubpx", VT_INT, 3), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Warp Obsidian |cffffcc00C|rrucible"),
            ("utub", VT_STR, "Void forge and Lumber return point. Researches Void Blades (+1/+2/+3 Attack) and Astral Plating (+1/+2/+3 Armor)."),
        ]),

        # Altar: Altar of the Void (`v007` — Floating Arcane Book of Summoning Pedestal! `urev=1` ONLY HERE!)
        ("uaod", "v007", [
            ("unam", VT_STR, "Altar of the Void"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "undead,mechanical"),
            ("upar", VT_STR, ""), ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\BookOfSummoning\\BookOfSummoning.mdl"),
            ("usnd", VT_STR, "AltarOfDarkness"),
            ("usca", VT_REAL, 1.05),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 120), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 180), ("ulum", VT_INT, 50), ("ubld", VT_INT, 58),
            ("uhpm", VT_INT, 950), ("udef", VT_INT, 5), ("urev", VT_INT, 1), ("uabi", VT_STR, ""),
            ("utra", VT_STR, "V001,V002,V003,V004"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Warp |cffffcc00A|rltar of the Void"),
            ("utub", VT_STR, "Summons Voidborn Heroes (Rift Sovereign Xal'athor, Nether Inquisitor Sargen'eth, Shadowblade Akama, Entropy Archon Aetheron) and revives fallen Heroes."),
        ]),

        # Shop: Reliquary of Shadows (`v008`)
        ("utom", "v008", [
            ("unam", VT_STR, "Reliquary of Shadows"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "undead,mechanical"),
            ("upar", VT_STR, ""), ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\undead\\TombOfRelics\\TombOfRelics.mdl"),
            ("usnd", VT_STR, "TombOfRelics"),
            ("uclr", VT_INT, 190), ("uclg", VT_INT, 120), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 130), ("ulum", VT_INT, 30), ("ubld", VT_INT, 48),
            ("uhpm", VT_INT, 550), ("ureq", VT_STR, "v007"),
            ("uabi", VT_STR, "Aall,Apit"),
            ("umki", VT_STR, "sreg,plcl,i003,phea,pman,stwp,i004,i002"),
            ("usei", VT_STR, ""),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Warp |cffffcc00R|reliquiaries of Shadows"),
            ("utub", VT_STR, "Mystic Void vault offering scrolls, healing & mana potions, Town Portals, Staff of Sanctuary, and Orb of Oblivion."),
        ]),

        # Tower: Entropy Obelisk (`v009`)
        ("uzg1", "v009", [
            ("unam", VT_STR, "Entropy Obelisk"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "undead,mechanical"),
            ("upar", VT_STR, ""), ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\DalaranGuardTower\\DalaranGuardTower.mdl"),
            ("usnd", VT_STR, "ElvenGuardTower"),
            ("uclr", VT_INT, 190), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 135), ("ulum", VT_INT, 80), ("ubld", VT_INT, 45),
            ("ufma", VT_INT, 0),
            ("uhpm", VT_INT, 550), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("ureq", VT_STR, "v005"), ("uabi", VT_STR, "Adts"),
            ("uaen", VT_INT, 1),
            ("ua1b", VT_INT, 24), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 6),
            ("ua1c", VT_UNREAL, 1.00), ("ua1r", VT_INT, 750), ("ua1t", VT_STR, "pierce"),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\AvengerMissile\\AvengerMissile.mdl"),
            ("ua1z", VT_INT, 1450),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "O"),
            ("utip", VT_STR, "Warp Entropy |cffffcc00O|rbelisk"),
            ("utub", VT_STR, "Astral defense spire with True Sight. Fires piercing void bolts at ground and air invaders."),
        ]),

        # Caster/Flyer Sanctum: Sanctum of Stars (`v018`)
        ("utod", "v018", [
            ("unam", VT_STR, "Sanctum of Stars"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "undead,mechanical"),
            ("upar", VT_STR, ""), ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\undead\\TempleOfTheDamned\\TempleOfTheDamned.mdl"),
            ("usnd", VT_STR, "TempleOfTheDamned"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 150), ("ulum", VT_INT, 140), ("ubld", VT_INT, 58),
            ("uhpm", VT_INT, 1100), ("udef", VT_INT, 5),
            ("ureq", VT_STR, "v002"), ("utra", VT_STR, "v014,v015"), ("ures", VT_STR, ""), ("uabi", VT_STR, ""),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Warp |cffffcc00S|ranctum of Stars"),
            ("utub", VT_STR, "Tier-2 Astral spire. Trains Void Weavers (spellcasters) and Nether Drakelets (magic anti-caster flyers)."),
        ]),

        # Siege & T3 Champion Bay: Oblivion Pit (`v019`)
        ("ubon", "v019", [
            ("unam", VT_STR, "Oblivion Pit"),
            ("urac", VT_STR, "undead"),
            ("utyp", VT_STR, "undead,mechanical"),
            ("upar", VT_STR, ""), ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\DragonBuildingBlack\\DragonBuildingBlack.mdl"),
            ("usnd", VT_STR, "DragonRoost"),
            ("usca", VT_REAL, 0.85),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 105), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 180), ("ulum", VT_INT, 140), ("ubld", VT_INT, 62),
            ("uhpm", VT_INT, 1200), ("udef", VT_INT, 5),
            ("ureq", VT_STR, "v002,v006"), ("utra", VT_STR, "v016,v017"), ("ures", VT_STR, ""), ("uabi", VT_STR, ""),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Warp O|cffffcc00b|rlivion Pit"),
            ("utub", VT_STR, "Heavy dimensional war-pit. Summons Rift Devastators (T2 Siege) and Oblivion Colossi (T3 Elite Champions)."),
        ]),

        # ---- VOIDBORN COMBAT UNITS (`v011..v017`) ----
        ("hfoo", "v011", [
            ("unam", VT_STR, "Void Zealot"),
            ("urac", VT_STR, "undead"),
            ("umdl", VT_STR, "units\\demon\\FelgaurdBlue\\FelgaurdBlue.mdl"),
            ("usnd", VT_STR, "DoomGuard"),
            ("usca", VT_REAL, 0.86),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 130), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 130), ("ulum", VT_INT, 0), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 20),
            ("uhpm", VT_INT, 445), ("udef", VT_INT, 2), ("udty", VT_STR, "large"), ("umvs", VT_INT, 280),
            ("ua1b", VT_INT, 13), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 4), ("ua1c", VT_UNREAL, 1.32),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "Z"),
            ("utip", VT_STR, "Summon Void |cffffcc00Z|realot"),
            ("utub", VT_STR, "Swift Tier-1 Rift bladesman with heavy astral armor. Attacks land units."),
        ]),
        ("hrif", "v012", [
            ("unam", VT_STR, "Astral Arbalist"),
            ("urac", VT_STR, "undead"),
            ("umdl", VT_STR, "Units\\Creeps\\FacelessOne\\FacelessOne.mdl"),
            ("usnd", VT_STR, "FacelessOne"),
            ("usca", VT_REAL, 0.84),
            ("uclr", VT_INT, 205), ("uclg", VT_INT, 145), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 200), ("ulum", VT_INT, 35), ("ufoo", VT_INT, 3), ("ubld", VT_INT, 25),
            ("uhpm", VT_INT, 540), ("udef", VT_INT, 1), ("udty", VT_STR, "medium"), ("umvs", VT_INT, 280),
            ("ureq", VT_STR, ""),
            ("ua1b", VT_INT, 21), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 6), ("ua1c", VT_UNREAL, 1.38),
            ("ua1r", VT_INT, 550), ("ua1w", VT_STR, "missile"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\AvengerMissile\\AvengerMissile.mdl"), ("ua1z", VT_INT, 1350),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Summon |cffffcc00A|rstral Arbalist"),
            ("utub", VT_STR, "Ranged Void marksman hurling astral bolts at ground and air targets."),
        ]),
        ("hkni", "v013", [
            ("unam", VT_STR, "Dread Enforcer"),
            ("urac", VT_STR, "undead"),
            ("umdl", VT_STR, "Units\\Creeps\\DragonSpawnPurple\\DragonSpawnPurple.mdl"),
            ("usnd", VT_STR, "DragonSpawn"),
            ("usca", VT_REAL, 0.90),
            ("ugol", VT_INT, 240), ("ulum", VT_INT, 50), ("ufoo", VT_INT, 4), ("ubld", VT_INT, 32),
            ("uhpm", VT_INT, 880), ("udef", VT_INT, 4), ("udty", VT_STR, "large"), ("umvs", VT_INT, 295),
            ("ureq", VT_STR, "v002"),
            ("ua1b", VT_INT, 27), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 8), ("ua1c", VT_UNREAL, 1.55),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "E"),
            ("utip", VT_STR, "Summon Dread |cffffcc00E|rnforcer"),
            ("utub", VT_STR, "Tier-2 heavily armored Void bruiser with crushing melee strikes."),
        ]),
        ("hmpr", "v014", [
            ("unam", VT_STR, "Void Weaver"),
            ("urac", VT_STR, "undead"),
            ("umdl", VT_STR, "units\\demon\\EredarWarlockPurple\\EredarWarlockPurple.mdl"),
            ("usnd", VT_STR, "PitLord"),
            ("usca", VT_REAL, 0.76),
            ("ugol", VT_INT, 145), ("ulum", VT_INT, 30), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 26),
            ("uhpm", VT_INT, 345), ("umpi", VT_INT, 175), ("umpm", VT_INT, 300), ("umpr", VT_UNREAL, 1.15),
            ("ureq", VT_STR, "v002"),
            ("ua1b", VT_INT, 11), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 4), ("ua1c", VT_UNREAL, 1.60),
            ("ua1m", VT_STR, "Abilities\\Weapons\\NecromancerMissile\\NecromancerMissile.mdl"),
            ("uabi", VT_STR, "Aslo,Aadm,Aihn"), ("udaa", VT_STR, "Aslo"), ("upgr", VT_STR, "R001"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "W"),
            ("utip", VT_STR, "Summon Void |cffffcc00W|reaver"),
            ("utub", VT_STR, "Astral caster adept at Temporal Slow and Abolish Magic. Attacks ground and air units."),
        ]),
        ("hdhw", "v015", [
            ("unam", VT_STR, "Nether Drakelet"),
            ("urac", VT_STR, "undead"),
            ("umdl", VT_STR, "units\\creeps\\NetherDragon\\NetherDragon.mdl"),
            ("usnd", VT_STR, "NetherDragon"),
            ("usca", VT_REAL, 0.74),
            ("ugol", VT_INT, 165), ("ulum", VT_INT, 40), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 28),
            ("uhpm", VT_INT, 450), ("umpi", VT_INT, 0), ("umpm", VT_INT, 0),
            ("udef", VT_INT, 2), ("udty", VT_STR, "small"), ("umvs", VT_INT, 325),
            ("ureq", VT_STR, "v002"),
            ("ua1b", VT_INT, 16), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 5), ("ua1c", VT_UNREAL, 1.75),
            ("ua1r", VT_INT, 450), ("ua1t", VT_STR, "magic"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\AvengerMissile\\AvengerMissile.mdl"),
            ("uabi", VT_STR, ""), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "D"),
            ("utip", VT_STR, "Summon Nether |cffffcc00D|rrakelet"),
            ("utub", VT_STR, "Agile Void flyer dealing Magic damage to ground and air forces."),
        ]),
        ("hmtm", "v016", [
            ("unam", VT_STR, "Rift Devastator"),
            ("urac", VT_STR, "undead"),
            ("umdl", VT_STR, "units\\creeps\\InfernalCannonFlame\\InfernalCannonFlame.mdl"),
            ("usnd", VT_STR, "InfernalMachine"),
            ("usca", VT_REAL, 0.80),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 210), ("ulum", VT_INT, 65), ("ufoo", VT_INT, 4), ("ubld", VT_INT, 35),
            ("uhpm", VT_INT, 620), ("udef", VT_INT, 2), ("udty", VT_STR, "large"), ("umvs", VT_INT, 230),
            ("ureq", VT_STR, "v002,v006"),
            ("ua1b", VT_INT, 48), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 12), ("ua1c", VT_UNREAL, 2.55),
            ("ua1r", VT_INT, 900), ("ua1t", VT_STR, "siege"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\ObsidianStatueMissile\\ObsidianStatueMissile.mdl"),
            ("uabi", VT_STR, ""), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Summon |cffffcc00R|rift Devastator"),
            ("utub", VT_STR, "Long-range Void siege engine that obliterates enemy fortifications from afar."),
        ]),
        ("hkni", "v017", [
            ("unam", VT_STR, "Oblivion Colossus"),
            ("urac", VT_STR, "undead"),
            ("umdl", VT_STR, "units\\demon\\DoomGuard\\DoomGuard.mdl"),
            ("usnd", VT_STR, "DoomGuard"),
            ("usca", VT_REAL, 1.04),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 115), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 300), ("ulum", VT_INT, 90), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 42),
            ("uhpm", VT_INT, 1150), ("udef", VT_INT, 5), ("udty", VT_STR, "large"), ("umvs", VT_INT, 285),
            ("ureq", VT_STR, "v003"),
            ("ua1b", VT_INT, 35), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 9), ("ua1c", VT_UNREAL, 1.60),
            ("uabi", VT_STR, "ACce,ACsk,Aihn"), ("upgr", VT_STR, "R000,R001"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Summon Oblivion |cffffcc00C|rolossus"),
            ("utub", VT_STR, "Tier-3 Void apex juggernaut armed with Cleaving Attack and Resistant Skin."),
        ]),

        # ---- 4 VOIDBORN HEROES (`V001..V004`) — 16 EXCLUSIVE SKILLS (`A032..A047`), ZERO `urev`! ----
        ("Nplh", "V001", [
            ("unam", VT_STR, "Rift Sovereign"),
            ("upro", VT_STR, "Xal'athor,Vael'gorath,Nihil'zar,Mal'korath"), ("upru", VT_INT, 4),
            ("urac", VT_STR, "undead"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 105), ("uclb", VT_INT, 255),
            ("usca", VT_REAL, 0.92),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "v002"), ("urq2", VT_STR, "v003"),
            ("uhab", VT_STR, "A032,A033,A034,A035"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 24), ("uagi", VT_INT, 14), ("uint", VT_INT, 17),
            ("ustp", VT_UNREAL, 2.95), ("uagp", VT_UNREAL, 1.50), ("uinp", VT_UNREAL, 1.90),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Summon |cffffcc00R|rift Sovereign"),
            ("utpr", VT_STR, "Revive |cffffcc00R|rift Sovereign"),
            ("utub", VT_STR, "Colossal Void Strength Hero. Exclusive kit: Event Horizon Crater (Q), Oblivion Cleave Lance (W), Abyssal Dread Howl (E), and Dark Portal Cataclysm (R)."),
        ]),
        ("Ulic", "V002", [
            ("unam", VT_STR, "Nether Inquisitor"),
            ("upro", VT_STR, "Sargen'eth,Kael'vor,Ombros,Zurael"), ("upru", VT_INT, 4),
            ("urac", VT_STR, "undead"),
            ("umdl", VT_STR, "units\\demon\\EredarWarlockPurple\\EredarWarlockPurple.mdl"),
            ("usnd", VT_STR, "PitLord"), ("usca", VT_REAL, 0.96),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "v002"), ("urq2", VT_STR, "v003"),
            ("uhab", VT_STR, "A036,A037,A038,A039"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 16), ("uagi", VT_INT, 14), ("uint", VT_INT, 25),
            ("ustp", VT_UNREAL, 1.90), ("uagp", VT_UNREAL, 1.50), ("uinp", VT_UNREAL, 3.10),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "I"),
            ("utip", VT_STR, "Summon Nether |cffffcc00I|rnquisitor"),
            ("utpr", VT_STR, "Revive Nether |cffffcc00I|rnquisitor"),
            ("utub", VT_STR, "Void Intelligence Archmage. Exclusive kit: Entropy Rift Storm (Q), Soul Siphon Tether (W), Astral Phase Surge (E), and Singularity Collapse (R)."),
        ]),
        ("Edem", "V003", [
            ("unam", VT_STR, "Shadowblade Stalker"),
            ("upro", VT_STR, "Akama,Ashtongue,Kzr'eth,Shadrel"), ("upru", VT_INT, 4),
            ("urac", VT_STR, "undead"),
            ("umdl", VT_STR, "units\\other\\DranaiAkama\\DranaiAkama.mdl"),
            ("usnd", VT_STR, "Akama"),
            ("usca", VT_REAL, 1.05),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 155), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "v002"), ("urq2", VT_STR, "v003"),
            ("uhab", VT_STR, "A040,A041,A042,A043"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 18), ("uagi", VT_INT, 22), ("uint", VT_INT, 15),
            ("ustp", VT_UNREAL, 2.15), ("uagp", VT_UNREAL, 2.85), ("uinp", VT_UNREAL, 1.80),
            ("umvs", VT_INT, 315),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Summon |cffffcc00S|rhadowblade Stalker"),
            ("utpr", VT_STR, "Revive |cffffcc00S|rhadowblade Stalker"),
            ("utub", VT_STR, "Dual-sickle Void Agility Assassin. Exclusive kit: Umbral Shuriken Fan (Q), Phantom Ambush Backstab (W), Smoke Veil Shades (E), and Thousand-Shadow Omnislash (R)."),
        ]),
        ("Udre", "V004", [
            ("unam", VT_STR, "Entropy Archon"),
            ("upro", VT_STR, "Aetheron,Val'kesh,Mor'duun,Xylar"), ("upru", VT_INT, 4),
            ("urac", VT_STR, "undead"),
            ("uclr", VT_INT, 165), ("uclg", VT_INT, 145), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "v002"), ("urq2", VT_STR, "v003"),
            ("uhab", VT_STR, "A044,A045,A046,A047"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 20), ("uagi", VT_INT, 16), ("uint", VT_INT, 19),
            ("ustp", VT_UNREAL, 2.45), ("uagp", VT_UNREAL, 1.75), ("uinp", VT_UNREAL, 2.55),
            ("ubpx", VT_INT, 3), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "E"),
            ("utip", VT_STR, "Summon |cffffcc00E|rntropy Archon"),
            ("utpr", VT_STR, "Revive |cffffcc00E|rntropy Archon"),
            ("utub", VT_STR, "Cosmic Tactician Hero. Exclusive kit: Starfall Singularity (Q), Dimensional Banish Bolt (W), Null-Field Purge Barrier (E), and Twilight of the Cosmos (R)."),
        ]),

        # ======================================================================
        # FACTION 8: RUNEFORGED BASTION (`t010` Automaton — Internal Foundry Build!)
        #   Row 0: (0,0) t001 | (1,0) t004 | (2,0) t005 | (3,0) t006
        #   Row 1: (0,1) t007 | (1,1) t008 | (2,1) t009
        #   Row 2: (0,2) t018 | (1,2) t019
        # ======================================================================

        # Worker: Runeforged Automaton (`t010`, parent `opeo` — `urac="orc"` so it uses
        # our custom Titan Gear-Anvil Build icon `CommandBasicStructOrc` and enters
        # inside blueprints safely during assembly!)
        ("opeo", "t010", [
            ("unam", VT_STR, "Runeforged Automaton"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "Peon"),
            ("umdl", VT_STR, "Units\\Creeps\\HeroTinkerRobot\\HeroTinkerRobot.mdl"),
            ("usnd", VT_STR, "ClockwerkGoblin"),
            ("usca", VT_REAL, 0.85),
            ("uclr", VT_INT, 235), ("uclg", VT_INT, 215), ("uclb", VT_INT, 170),
            ("ubui", VT_STR, "t001,t004,t005,t006,t007,t008,t009,t018,t019"),
            ("ugol", VT_INT, 75), ("ulum", VT_INT, 0), ("ufoo", VT_INT, 1), ("ubld", VT_INT, 15),
            ("uhpm", VT_INT, 240), ("uhpr", VT_UNREAL, 0.35), ("uhrt", VT_STR, "always"),
            ("udef", VT_INT, 1), ("udty", VT_STR, "medium"), ("umvs", VT_INT, 195),
            ("uabi", VT_STR, "Ahar,Arep,Aihn"),
            ("upgr", VT_STR, "Rhpm"),
            ("ua1b", VT_INT, 6), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 2), ("ua1c", VT_UNREAL, 1.9),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Assemble Runeforged |cffffcc00A|rutomaton"),
            ("utub", VT_STR, "Clockwork-runic builder unit. Enters inside Runeforged blueprints to assemble Titan structures safely, harvests Gold & Lumber, and Repairs."),
        ]),

        # Tier 1/2/3 Titan Halls (`t001 -> t002 -> t003` — mechanical/arcane/portal models with native matched buttons).
        ("ogre", "t001", [
            ("unam", VT_STR, "Titan Foundry"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "TownHall,Mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\AmmoDump\\AmmoDump.mdl"),
            ("usnd", VT_STR, "Workshop"),
            ("usca", VT_REAL, 0.96),
            ("uclr", VT_INT, 200), ("uclg", VT_INT, 230), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 385), ("ulum", VT_INT, 185), ("ubld", VT_INT, 115),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 1550), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "t010"), ("ures", VT_STR, "Rhpm"), ("uupt", VT_STR, "t002"),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "F"),
            ("utip", VT_STR, "Forge Titan |cffffcc00F|roundry"),
            ("utub", VT_STR, "Primary clockwork-runic citadel of the Runeforged Bastion. Assembles Automatons and stores Gold and Lumber. Upgrades to Stormforge Hold."),
        ]),
        ("ostr", "t002", [
            ("unam", VT_STR, "Stormforge Hold"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "TownHall,Mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\ArcaneObservatory\\ArcaneObservatory.mdl"),
            ("usnd", VT_STR, "ArcaneSanctum"),
            ("usca", VT_REAL, 0.95),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 320), ("ulum", VT_INT, 190), ("ubld", VT_INT, 115),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 1850), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "t010"), ("ures", VT_STR, "Rhpm"), ("uupt", VT_STR, "t003"), ("ureq", VT_STR, ""),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Stormforge Hold"),
            ("utub", VT_STR, "Tier-2 Titan observatory-hold. Unlocks Arcane Conduit, Colossus Bay, Stormforged Juggernauts, and a 2nd Hero."),
        ]),
        ("ofrt", "t003", [
            ("unam", VT_STR, "Apex Pantheon"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "TownHall,Mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\Waygate\\Waygate.mdl"),
            ("usnd", VT_STR, "Castle"),
            ("usca", VT_REAL, 1.24),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 240), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 360), ("ulum", VT_INT, 210), ("ubld", VT_INT, 115),
            ("ufma", VT_INT, 11), ("uhpm", VT_INT, 2200), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("utra", VT_STR, "t010"), ("ures", VT_STR, "Rhpm"), ("uupt", VT_STR, ""), ("ureq", VT_STR, "t007"),
            ("uabi", VT_STR, "Abdl,Argl"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "U"),
            ("utip", VT_STR, "|cffffcc00U|rpgrade to Apex Pantheon"),
            ("utub", VT_STR, "Tier-3 Titan portal-citadel. Unlocks Titan Constructs, Tier-3 Runic upgrades, Orb of Storms, and a 3rd Hero."),
        ]),

        # Supply: Dynamo Core (`t004`, +9 Food)
        ("otrb", "t004", [
            ("unam", VT_STR, "Dynamo Core"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\PowerGenerator\\PowerGenerator.mdl"),
            ("usnd", VT_STR, "Workshop"),
            ("usca", VT_REAL, 0.72),
            ("ugol", VT_INT, 90), ("ulum", VT_INT, 25), ("ubld", VT_INT, 32),
            ("ufma", VT_INT, 9), ("uhpm", VT_INT, 520), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("uabi", VT_STR, "Abds"), ("uaen", VT_INT, 0),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "D"),
            ("utip", VT_STR, "Assemble |cffffcc00D|rynamo Core"),
            ("utub", VT_STR, "Arc-plasma power generator providing 9 Food supply to your Runeforged army."),
        ]),

        # Barracks: Iron Garrison (`t005` — Clockwork Pocket Factory!)
        ("obar", "t005", [
            ("unam", VT_STR, "Iron Garrison"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "Units\\Creeps\\HeroTinkerFactory\\HeroTinkerFactory.mdl"),
            ("usnd", VT_STR, "Workshop"),
            ("usca", VT_REAL, 1.25),
            ("uclr", VT_INT, 200), ("uclg", VT_INT, 230), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 160), ("ulum", VT_INT, 60), ("ubld", VT_INT, 58),
            ("uhpm", VT_INT, 1300), ("udef", VT_INT, 5),
            ("utra", VT_STR, "t011,t012,t013"), ("ures", VT_STR, ""), ("uabi", VT_STR, "Abds"),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "G"),
            ("utip", VT_STR, "Assemble Iron |cffffcc00G|rarrison"),
            ("utub", VT_STR, "Clockwork war-factory. Deploys Runic Sentinels (T1), Thunder Arquebusiers (T1 Ranged), and Stormforged Juggernauts (T2)."),
        ]),

        # Armory + Lumber Drop: Runic Anvil (`t006` — Spinning Gear-Blade Forge!)
        ("ofor", "t006", [
            ("unam", VT_STR, "Runic Anvil"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\orc\\WarMill\\WarMill.mdl"),
            ("usnd", VT_STR, "Blacksmith"),
            ("uclr", VT_INT, 180), ("uclg", VT_INT, 225), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 140), ("ulum", VT_INT, 60), ("ubld", VT_INT, 52),
            ("uhpm", VT_INT, 1200), ("udef", VT_INT, 5),
            ("ures", VT_STR, "R002,R003"), ("ureq", VT_STR, "t001"),
            ("uabi", VT_STR, "Abds,Arlm"),
            ("ubpx", VT_INT, 3), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Assemble |cffffcc00R|runic Anvil"),
            ("utub", VT_STR, "Titan gear-forge and Lumber drop-off. Researches Runic Weapons (+1/+2/+3 Attack) and Titan Plating (+1/+2/+3 Armor)."),
        ]),

        # Altar: Altar of the Titans (`t007` — Towering Titan Rune Obelisk! `urev=1` ONLY HERE!)
        ("oalt", "t007", [
            ("unam", VT_STR, "Altar of the Titans"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\BridgeObelisk\\BridgeObelisk.mdl"),
            ("usnd", VT_STR, "AltarOfKings"),
            ("usca", VT_REAL, 1.12),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 180), ("ulum", VT_INT, 50), ("ubld", VT_INT, 58),
            ("uhpm", VT_INT, 950), ("udef", VT_INT, 5), ("urev", VT_INT, 1), ("uabi", VT_STR, "Abds"),
            ("utra", VT_STR, "T001,T002,T003,T004"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "A"),
            ("utip", VT_STR, "Assemble |cffffcc00A|rltar of the Titans"),
            ("utub", VT_STR, "Summons Runeforged Heroes (Stormforged Prime Thorim, Runesmith Highlord Ignis, Clockwork Vanguard Mimiron, Tempest Savant Loken) and revives fallen Heroes."),
        ]),

        # Shop: Artificer Vault (`t008` — Mechanical Merchant Emporium!)
        ("ovln", "t008", [
            ("unam", VT_STR, "Artificer Vault"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\Merchant\\Merchant.mdl"),
            ("usnd", VT_STR, "ArcaneVault"),
            ("usca", VT_REAL, 0.88),
            ("uclr", VT_INT, 195), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 130), ("ulum", VT_INT, 30), ("ubld", VT_INT, 48),
            ("uhpm", VT_INT, 550), ("ureq", VT_STR, "t007"),
            ("uabi", VT_STR, "Abds,Aall,Apit"),
            ("umki", VT_STR, "sreg,plcl,i003,phea,pman,stwp,i005,i002"),
            ("usei", VT_STR, ""),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "V"),
            ("utip", VT_STR, "Assemble Artificer |cffffcc00V|rault"),
            ("utub", VT_STR, "Runic supply emporium offering scrolls, potions, Town Portals, Staff of Sanctuary, and Orb of Storms."),
        ]),

        # Tower: Tesla Turret (`t009`)
        ("owtw", "t009", [
            ("unam", VT_STR, "Tesla Turret"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\TowerDefenseTower\\TowerDefenseTower.mdl"),
            ("usnd", VT_STR, "ArcaneTower"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 135), ("ulum", VT_INT, 80), ("ubld", VT_INT, 45),
            ("uhpm", VT_INT, 550), ("udef", VT_INT, 5), ("udty", VT_STR, "fort"),
            ("ureq", VT_STR, "t005"), ("uabi", VT_STR, "Abds,Adts"),
            ("uaen", VT_INT, 1),
            ("ua1b", VT_INT, 24), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 6),
            ("ua1c", VT_UNREAL, 1.00), ("ua1r", VT_INT, 750), ("ua1t", VT_STR, "pierce"),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\FarseerMissile\\FarseerMissile.mdl"),
            ("ua1z", VT_INT, 1500),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 1), ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Assemble |cffffcc00T|resla Turret"),
            ("utub", VT_STR, "Arc-lightning defense spire with True Sight. Strikes ground and air units."),
        ]),

        # Caster/Flyer Sanctum: Arcane Conduit (`t018` — Glowing Runic Mana Conduit!)
        ("osld", "t018", [
            ("unam", VT_STR, "Arcane Conduit"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\FountainOfMana\\FountainOfMana.mdl"),
            ("usnd", VT_STR, "ArcaneSanctum"),
            ("usca", VT_REAL, 0.90),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 150), ("ulum", VT_INT, 140), ("ubld", VT_INT, 58),
            ("uhpm", VT_INT, 1100), ("udef", VT_INT, 5),
            ("ureq", VT_STR, "t002"), ("utra", VT_STR, "t014,t015"), ("ures", VT_STR, ""), ("uabi", VT_STR, "Abds"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Assemble Arcane |cffffcc00C|ronduit"),
            ("utub", VT_STR, "Tier-2 Runic conduit. Trains Rune Diviners (storm casters) and Gyro-Interceptors (magic flyers)."),
        ]),

        # Siege & T3 Champion Bay: Colossus Bay (`t019`)
        ("obea", "t019", [
            ("unam", VT_STR, "Colossus Bay"),
            ("urac", VT_STR, "orc"),
            ("utyp", VT_STR, "mechanical"),
            ("upap", VT_STR, "unbuildable"),
            ("umdl", VT_STR, "buildings\\other\\GoblinShipyard\\GoblinShipyard.mdl"),
            ("usnd", VT_STR, "Workshop"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 230), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 180), ("ulum", VT_INT, 140), ("ubld", VT_INT, 62),
            ("uhpm", VT_INT, 1200), ("udef", VT_INT, 5),
            ("ureq", VT_STR, "t002,t006"), ("utra", VT_STR, "t016,t017"), ("ures", VT_STR, ""), ("uabi", VT_STR, "Abds"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 2), ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Assemble Colossus |cffffcc00B|ray"),
            ("utub", VT_STR, "Heavy assembly bay. Deploys Siege Behemoths (T2 Artillery) and Titan Constructs (T3 Champions)."),
        ]),

        # ---- RUNEFORGED COMBAT UNITS (`t011..t017`) ----
        ("hfoo", "t011", [
            ("unam", VT_STR, "Runic Sentinel"),
            ("urac", VT_STR, "orc"),
            ("umdl", VT_STR, "units\\creeps\\IronGolem\\IronGolem.mdl"),
            ("usnd", VT_STR, "IronGolem"),
            ("usca", VT_REAL, 0.74),
            ("uclr", VT_INT, 210), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 130), ("ulum", VT_INT, 0), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 20),
            ("uhpm", VT_INT, 450), ("udef", VT_INT, 2), ("udty", VT_STR, "large"), ("umvs", VT_INT, 275),
            ("ua1b", VT_INT, 13), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 4), ("ua1c", VT_UNREAL, 1.32),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Deploy Runic |cffffcc00S|rentinel"),
            ("utub", VT_STR, "Armored Tier-1 iron-rune construct vanguard. Attacks land units."),
        ]),
        ("hrif", "t012", [
            ("unam", VT_STR, "Thunder Arquebusier"),
            ("urac", VT_STR, "orc"),
            ("umdl", VT_STR, "Units\\Critters\\Marine\\Marine.mdl"),
            ("usnd", VT_STR, "Rifleman"),
            ("usca", VT_REAL, 0.92),
            ("uclr", VT_INT, 190), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 200), ("ulum", VT_INT, 35), ("ufoo", VT_INT, 3), ("ubld", VT_INT, 25),
            ("uhpm", VT_INT, 545), ("udef", VT_INT, 1), ("udty", VT_STR, "medium"), ("umvs", VT_INT, 275),
            ("ureq", VT_STR, ""),
            ("ua1b", VT_INT, 21), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 6), ("ua1c", VT_UNREAL, 1.38),
            ("ua1r", VT_INT, 550),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "T"),
            ("utip", VT_STR, "Deploy |cffffcc00T|rhunder Arquebusier"),
            ("utub", VT_STR, "Power-armored Gauss gunner firing ionized rounds at ground and air enemies."),
        ]),
        ("hkni", "t013", [
            ("unam", VT_STR, "Stormforged Juggernaut"),
            ("urac", VT_STR, "orc"),
            ("umdl", VT_STR, "units\\creeps\\GolemStatue\\GolemStatue.mdl"),
            ("usnd", VT_STR, "IronGolem"),
            ("usca", VT_REAL, 0.88),
            ("uclr", VT_INT, 235), ("uclg", VT_INT, 200), ("uclb", VT_INT, 135),
            ("ugol", VT_INT, 240), ("ulum", VT_INT, 50), ("ufoo", VT_INT, 4), ("ubld", VT_INT, 32),
            ("uhpm", VT_INT, 890), ("udef", VT_INT, 4), ("udty", VT_STR, "large"), ("umvs", VT_INT, 290),
            ("ureq", VT_STR, "t002"),
            ("ua1b", VT_INT, 27), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 8), ("ua1c", VT_UNREAL, 1.55),
            ("uabi", VT_STR, "Aihn"), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "J"),
            ("utip", VT_STR, "Deploy Stormforged |cffffcc00J|ruggernaut"),
            ("utub", VT_STR, "Heavy Tier-2 bronze-rune colossus built to crush frontline infantry."),
        ]),
        ("hmpr", "t014", [
            ("unam", VT_STR, "Rune Diviner"),
            ("urac", VT_STR, "orc"),
            ("umdl", VT_STR, "Units\\Creeps\\HeroTinker\\HeroTinker.mdl"),
            ("usnd", VT_STR, "SpellBreaker"),
            ("usca", VT_REAL, 0.82),
            ("uclr", VT_INT, 175), ("uclg", VT_INT, 230), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 145), ("ulum", VT_INT, 30), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 26),
            ("uhpm", VT_INT, 355), ("umpi", VT_INT, 175), ("umpm", VT_INT, 300), ("umpr", VT_UNREAL, 1.15),
            ("ureq", VT_STR, "t002"),
            ("ua1b", VT_INT, 11), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 4), ("ua1c", VT_UNREAL, 1.60),
            ("ua1m", VT_STR, "Abilities\\Weapons\\FarseerMissile\\FarseerMissile.mdl"),
            ("uabi", VT_STR, "Ahea,Ainf,Aihn"), ("udaa", VT_STR, "Ahea"), ("upgr", VT_STR, "R003"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "D"),
            ("utip", VT_STR, "Deploy Rune |cffffcc00D|riviner"),
            ("utub", VT_STR, "Runic field-savant equipped with Runic Mend (Heal) and Inner Plating (Inner Fire)."),
        ]),
        ("hgyr", "t015", [
            ("unam", VT_STR, "Gyro-Interceptor"),
            ("urac", VT_STR, "orc"),
            ("uclr", VT_INT, 180), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("usca", VT_REAL, 1.05),
            ("ugol", VT_INT, 165), ("ulum", VT_INT, 40), ("ufoo", VT_INT, 2), ("ubld", VT_INT, 26),
            ("uhpm", VT_INT, 450), ("udef", VT_INT, 2), ("udty", VT_STR, "small"), ("umvs", VT_INT, 340),
            ("ureq", VT_STR, "t002"),
            ("uaen", VT_INT, 1),
            ("ua1b", VT_INT, 16), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 5), ("ua1c", VT_UNREAL, 1.75),
            ("ua1r", VT_INT, 450), ("ua1t", VT_STR, "magic"), ("ua1w", VT_STR, "missile"),
            ("ua1g", VT_STR, "ground,structure,debris,air,item,ward"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\FarseerMissile\\FarseerMissile.mdl"), ("ua1z", VT_INT, 1500),
            ("uabi", VT_STR, ""), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "I"),
            ("utip", VT_STR, "Deploy Gyro-|cffffcc00I|rnterceptor"),
            ("utub", VT_STR, "High-speed plasma aircraft firing Magic bolts at ground and air targets."),
        ]),
        ("hmtt", "t016", [
            ("unam", VT_STR, "Siege Behemoth"),
            ("urac", VT_STR, "orc"),
            ("uclr", VT_INT, 185), ("uclg", VT_INT, 230), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 215), ("ulum", VT_INT, 65), ("ufoo", VT_INT, 4), ("ubld", VT_INT, 35),
            ("uhpm", VT_INT, 740), ("udef", VT_INT, 3), ("udty", VT_STR, "large"), ("umvs", VT_INT, 225),
            ("ureq", VT_STR, "t002,t006"),
            ("uaen", VT_INT, 1),
            ("ua1b", VT_INT, 49), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 11), ("ua1c", VT_UNREAL, 2.50),
            ("ua1r", VT_INT, 850), ("ua1t", VT_STR, "siege"), ("ua1w", VT_STR, "artillery"),
            ("ua1g", VT_STR, "ground,structure,debris,tree,wall"),
            ("ua1m", VT_STR, "Abilities\\Weapons\\CannonTowerMissile\\CannonTowerMissile.mdl"), ("ua1z", VT_INT, 1200),
            ("uabi", VT_STR, ""), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "B"),
            ("utip", VT_STR, "Deploy Siege |cffffcc00B|rehemoth"),
            ("utub", VT_STR, "Armored steam-artillery tank firing long-range siege shells."),
        ]),
        ("hkni", "t017", [
            ("unam", VT_STR, "Titan Construct"),
            ("urac", VT_STR, "orc"),
            ("umdl", VT_STR, "units\\creeps\\RockGolem\\RockGolem.mdl"),
            ("usnd", VT_STR, "RockGolem"),
            ("usca", VT_REAL, 1.12),
            ("uclr", VT_INT, 180), ("uclg", VT_INT, 230), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 300), ("ulum", VT_INT, 90), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 42),
            ("uhpm", VT_INT, 1150), ("udef", VT_INT, 5), ("udty", VT_STR, "large"), ("umvs", VT_INT, 280),
            ("ureq", VT_STR, "t003"),
            ("ua1b", VT_INT, 36), ("ua1d", VT_INT, 1), ("ua1s", VT_INT, 9), ("ua1c", VT_UNREAL, 1.60),
            ("uabi", VT_STR, "ACce,ACsk,Aihn"), ("upgr", VT_STR, "R002,R003"),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "C"),
            ("utip", VT_STR, "Deploy Titan |cffffcc00C|ronstruct"),
            ("utub", VT_STR, "Tier-3 Runeforged apex war-colossus with Cleaving Strike and Resistant Skin."),
        ]),

        # ---- 4 RUNEFORGED HEROES (`T001..T004`) — 16 EXCLUSIVE SKILLS (`A048..A063`), ZERO `urev`! ----
        ("Hmkg", "T001", [
            ("unam", VT_STR, "Stormforged Prime"),
            ("upro", VT_STR, "Thorim,Ra-den,Odyn,Archaedas"), ("upru", VT_INT, 4),
            ("urac", VT_STR, "orc"),
            ("uclr", VT_INT, 180), ("uclg", VT_INT, 235), ("uclb", VT_INT, 255),
            ("usca", VT_REAL, 1.15),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "t002"), ("urq2", VT_STR, "t003"),
            ("uhab", VT_STR, "A048,A049,A050,A051"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 25), ("uagi", VT_INT, 13), ("uint", VT_INT, 17),
            ("ustp", VT_UNREAL, 3.00), ("uagp", VT_UNREAL, 1.40), ("uinp", VT_UNREAL, 1.90),
            ("ubpx", VT_INT, 0), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "P"),
            ("utip", VT_STR, "Summon Stormforged |cffffcc00P|rrime"),
            ("utpr", VT_STR, "Revive Stormforged |cffffcc00P|rrime"),
            ("utub", VT_STR, "Thunder-wielding Titan Strength Hero. Exclusive kit: Mjolnir Thunderfall (Q), Magnetic Titan Grip (W), Overcharged Aegis Core (E), and Wrath of the Pantheon (R)."),
        ]),
        ("Nfir", "T002", [
            ("unam", VT_STR, "Runesmith Highlord"),
            ("upro", VT_STR, "Ignis,Volcanus,Khaz'goroth,Pyrion"), ("upru", VT_INT, 4),
            ("urac", VT_STR, "orc"),
            ("upra", VT_STR, "STR"),
            ("uclr", VT_INT, 255), ("uclg", VT_INT, 195), ("uclb", VT_INT, 130),
            ("usca", VT_REAL, 1.06),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "t002"), ("urq2", VT_STR, "t003"),
            ("uhab", VT_STR, "A052,A053,A054,A055"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 23), ("uagi", VT_INT, 15), ("uint", VT_INT, 17),
            ("ustp", VT_UNREAL, 2.85), ("uagp", VT_UNREAL, 1.55), ("uinp", VT_UNREAL, 1.95),
            ("ubpx", VT_INT, 1), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "R"),
            ("utip", VT_STR, "Summon |cffffcc00R|runesmith Highlord"),
            ("utpr", VT_STR, "Revive |cffffcc00R|runesmith Highlord"),
            ("utub", VT_STR, "Master of Molten Runes. Exclusive kit: Molten Slag Eruption (Q), Forgehammer Sundering (W), Tempered Rune-Plating (E), and Awaken Forge Colossus (R)."),
        ]),
        ("Ntin", "T003", [
            ("unam", VT_STR, "Clockwork Vanguard"),
            ("upro", VT_STR, "Mimiron,Gearspark,Volt'ron,Mecha-Prime"), ("upru", VT_INT, 4),
            ("urac", VT_STR, "orc"),
            ("upra", VT_STR, "AGI"),
            ("usca", VT_REAL, 1.05),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "t002"), ("urq2", VT_STR, "t003"),
            ("uhab", VT_STR, "A056,A057,A058,A059"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 18), ("uagi", VT_INT, 21), ("uint", VT_INT, 16),
            ("ustp", VT_UNREAL, 2.15), ("uagp", VT_UNREAL, 2.75), ("uinp", VT_UNREAL, 1.85),
            ("umvs", VT_INT, 305),
            ("ubpx", VT_INT, 2), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "V"),
            ("utip", VT_STR, "Summon Clockwork |cffffcc00V|ranguard"),
            ("utpr", VT_STR, "Revive Clockwork |cffffcc00V|ranguard"),
            ("utub", VT_STR, "Artificer Agility Hero. Exclusive kit: Cluster Rocket Salvo (Q), Railgun Gauss Snipe (W), Pocket Auto-Turrets (E), and Omega Orbital Laser (R)."),
        ]),
        ("Hamg", "T004", [
            ("unam", VT_STR, "Tempest Savant"),
            ("upro", VT_STR, "Loken,Norgannon,Auriaya,Stormseer"), ("upru", VT_INT, 4),
            ("urac", VT_STR, "orc"),
            ("upra", VT_STR, "INT"),
            ("umdl", VT_STR, "units\\creeps\\RevenantOfTheWaves\\RevenantOfTheWaves.mdl"),
            ("usnd", VT_STR, "Revenant"),
            ("usca", VT_REAL, 1.12),
            ("uclr", VT_INT, 165), ("uclg", VT_INT, 245), ("uclb", VT_INT, 255),
            ("ugol", VT_INT, 425), ("ulum", VT_INT, 100), ("ufoo", VT_INT, 5), ("ubld", VT_INT, 55),
            ("urqc", VT_INT, 3), ("urq1", VT_STR, "t002"), ("urq2", VT_STR, "t003"),
            ("uhab", VT_STR, "A060,A061,A062,A063"), ("uabi", VT_STR, "AInv"),
            ("ustr", VT_INT, 16), ("uagi", VT_INT, 15), ("uint", VT_INT, 24),
            ("ustp", VT_UNREAL, 1.90), ("uagp", VT_UNREAL, 1.50), ("uinp", VT_UNREAL, 3.10),
            ("ubpx", VT_INT, 3), ("ubpy", VT_INT, 0), ("uhot", VT_STR, "S"),
            ("utip", VT_STR, "Summon Tempest |cffffcc00S|ravant"),
            ("utpr", VT_STR, "Revive Tempest |cffffcc00S|ravant"),
            ("utub", VT_STR, "Runic Intelligence Arch-Conduit. Exclusive kit: Ionosphere Plasma Field (Q), Arc-Conduit Chain Surge (W), Chrono-Dynamo Overdrive (E), and Stormcore Superconductor (R)."),
        ]),
    ]
    return entries


# ==============================================================================
# 2. ALL 64 UNIQUE HERO ABILITIES (`A000..A063` in `war3map.w3a` v2)
#    Targeting modes (`tgt`):
#      2 = Point + AoE Reticle (`Ncl2=2, Ncl3=3`, order `"flamestrike"` / `"monsoon"`)
#      1 = Unit Target (`Ncl2=1, Ncl3=1`, order `"chainlightning"`)
#      0 = Instant PBAoE / Self (`Ncl2=0, Ncl3=1`, order `"thunderclap"` / `"roar"`)
# ==============================================================================

# Tuple: (abil_id, slot_idx 0..3, tgt_mode 0|1|2, order_str, name, desc)
HERO_SKILL_SPECS_64: List[Tuple[str, int, int, str, str, str]] = [
    # ---- EMPIRE 5: ABYSSAL TIDEBORN (NAGA) ----
    # Hero 1: Hvsh — Empress Lady Vashj (`A000..A003`)
    ("A000", 0, 2, "flamestrike",    "Maelstrom Vortex",           "Point-targeted 275 AoE: deals damage scaled by ability level and Vashj's INT, and pulls nearby non-immune enemies toward the whirlpool."),
    ("A001", 1, 1, "chainlightning", "Forked Tempest Arc",         "Lightning jumps to up to 3 enemies within 300 range of one another; each later jump deals less damage. Vashj gains 12 Mana per ability level."),
    ("A002", 2, 0, "thunderclap",    "Mana-Tide Aegis",            "In 300 AoE, deals 18 + 18 per ability level damage to enemies and restores 65 + 25 per level HP to nearby allies, including Vashj."),
    ("A003", 3, 2, "monsoon",        "Cataclysmic Tsunami",        "Three expanding 390-AoE waves. Each pulse scales with Vashj's INT and hero level, heals allies for 18 HP, and pushes enemies outward."),

    # Hero 2: N004 — Illidan Stormrage, Betrayer of Tides (`A004..A007`)
    ("A004", 0, 2, "flamestrike",    "Azzinoth Glaive Barrage",    "Three crossing glaive lanes strike toward the target point; the side lanes hit harder than the center and a 150-AoE burst hits the endpoint. Damage scales with AGI."),
    ("A005", 1, 1, "chainlightning", "Shadowstep of the Betrayer", "Shadowsteps to a walkable point just beyond the target, deals 1.22x stat-scaled damage, and steals up to 20 Mana from the enemy."),
    ("A006", 2, 0, "thunderclap",    "Demon-Scale Immolation",     "Deals 0.82x stat-scaled damage in 270 AoE, pushes foes away, and heals Illidan for 55 + 35 per ability level. At levels 2-3, summons one Mur'gul Reaver for 12 seconds."),
    ("A007", 3, 0, "roar",           "Metamorphosis: Abyssal Overlord", "Three 380-AoE pulses scale with Illidan's AGI and hero level. Each heals nearby allies for 12 HP, heals Illidan for 28 HP, and pushes enemies outward."),

    # Hero 3: N001 — Leviathan Warlord Naj'entus (`A008..A011`)
    ("A008", 0, 2, "flamestrike",    "Impaling Spine Quake",       "Three coral shock rings converge on the target point; enemies within 285 take 1.18x stat-scaled damage and are pushed away."),
    ("A009", 1, 1, "chainlightning", "Harpoon Undertow",           "Harpoons one enemy for 1.16x stat-scaled damage and drags non-immune, non-giant targets 190 units toward Naj'entus."),
    ("A010", 2, 0, "thunderclap",    "Tidal Carapace Roar",        "Around Naj'entus, deals 0.64x stat-scaled damage, heals allies for 70 + 18 per level, and pushes enemies outward."),
    ("A011", 3, 2, "monsoon",        "Wrath of the Kraken",        "Three 390-AoE undertow pulses scale with Naj'entus's STR and hero level and pull enemies inward. The second pulse summons two Myrmidons for 12 seconds."),

    # Hero 4: N002 — Nazjatar Tideweaver Athissa (`A012..A015`)
    ("A012", 0, 2, "flamestrike",    "Bioluminescent Depthcharge", "Point-targeted 280 AoE: damages enemies with INT-scaled spell damage and heals nearby allies for 52 + 12 per ability level."),
    ("A013", 1, 1, "chainlightning", "Siren's Crushing Prison",    "The target and enemies within 190 take splash damage; the target also takes a direct hit and is pulled toward Athissa. Burns 26 Mana from nearby enemy casters."),
    ("A014", 2, 0, "thunderclap",    "Blessing of Azshara",        "Restores 48 + 15 per ability level HP and 42 + 18 Mana to nearby allies in 330 AoE."),
    ("A015", 3, 2, "monsoon",        "Eye of Nazjatar",            "Three 400-AoE pulses scale with Athissa's INT and hero level; each heals allies and restores Mana, drains enemy Mana, and pulls foes inward. The second pulse summons two Snap Dragons for 16 seconds."),

    # ---- EMPIRE 6: SUNFURY IMPERIUM (SILVERMOON) ----
    # Hero 5: Hkal — Sovereign Kael'thas (`A016..A019`)
    ("A016", 0, 2, "flamestrike",    "Verdant Sunfire Pillar",     "Point-targeted 275 AoE: deals 1.12x INT-scaled damage and burns 16 Mana per ability level from affected enemies."),
    ("A017", 1, 1, "chainlightning", "Arcane Gravity Lapse",       "Hits one target for 0.94x INT-scaled damage, drains 36 Mana and transfers 28 Mana to Kael, then pulls the target toward him."),
    ("A018", 2, 0, "thunderclap",    "Pyromancer's Molten Barrier","In 310 AoE, deals 0.44x INT-scaled damage, restores 68 + 16 per level HP and 24 Mana to allies, and burns 10 enemy Mana."),
    ("A019", 3, 2, "monsoon",        "Rebirth of Al'ar",           "Three 400-AoE pulses scale with Kael's INT and hero level. Each restores 12 HP and Mana to allies and pushes foes away; the second summons a Dragonhawk Rider for 18 seconds."),

    # Hero 6: Hvwd — Ranger-General Sylvanas (`A020..A023`)
    ("A020", 0, 2, "flamestrike",    "Rain of Starlight Arrows",   "Fires three arrow lanes toward the target point: the main lane deals 1.08x AGI-scaled damage and two angled lanes deal 0.55x each."),
    ("A021", 1, 1, "chainlightning", "Windrunner's Piercing Shot", "A piercing shot damages enemies along an 85-width line for 1.18x AGI-scaled damage; the selected target takes an additional 0.45x hit."),
    ("A022", 2, 0, "thunderclap",    "Elven Gale Stride",          "In 350 AoE, heals allies for 58 + 20 per ability level, grants 12 Mana, and summons two High Elven Archers for 16 seconds."),
    ("A023", 3, 2, "monsoon",        "Tempest of Quel'Thalas",     "Three expanding 410-AoE arrow volleys scale with Sylvanas's AGI and hero level and push enemies outward."),

    # Hero 7: Hlgr — Grand Marshal Garithos (`A024..A027`)
    ("A024", 0, 2, "flamestrike",    "Earthshaker Warhammer",      "A point-targeted seismic strike deals 1.08x STR-scaled damage in 245 AoE and pushes enemies away from the impact."),
    ("A025", 1, 1, "chainlightning", "Imperial Execution Decree",  "Execution blow: 48 + 1.15x Garithos's STR bonus, plus 16% of the target's missing HP (base damage capped at 280)."),
    ("A026", 2, 0, "thunderclap",    "Iron Phalanx Command",       "In 330 AoE, deals 0.48x STR-scaled damage, heals allies for 82 + 22 per level, and pushes enemies away."),
    ("A027", 3, 2, "monsoon",        "Grand Cavalry Charge",       "Three 390-AoE cavalry shockwaves scale with Garithos's STR and hero level; each heals allies and knocks enemies back. The second summons two Alliance Captains for 14 seconds."),

    # Hero 8: Huth — Highlord Uther (`A028..A031`)
    ("A028", 0, 2, "flamestrike",    "Consecrated Sunwell Ground", "Sanctifies a 285-AoE target area, dealing 0.72x STR-scaled damage to foes and healing allies for 70 + 10 per level."),
    ("A029", 1, 1, "chainlightning", "Hammer of Radiant Verdict",  "A radiant hammer hits the target for 1.2x STR-scaled damage, splashes 0.35x damage in 180 AoE, and pushes nearby enemies away."),
    ("A030", 2, 0, "thunderclap",    "Aegis of the Silver Hand",   "Restores 90 + 28 per ability level HP to nearby allies in 360 AoE."),
    ("A031", 3, 2, "monsoon",        "Dawnbringer Judgment",       "Three 410-AoE pulses scale with Uther's STR and hero level; each damages enemies, heals allies for 46 HP, and restores 8 Mana."),

    # ---- EMPIRE 7: VOIDBORN LEGION ----
    # Hero 9: V001 — Rift Sovereign Xal'athor (`A032..A035`)
    ("A032", 0, 2, "flamestrike",    "Event Horizon Crater",       "A point-targeted 285-AoE gravity well deals 1.04x STR-scaled damage, burns 18 Mana per ability level, and pulls enemies inward."),
    ("A033", 1, 1, "chainlightning", "Oblivion Cleave Lance",      "A void cleave deals 54 + 34 per ability level + 0.85x Xal'athor's STR bonus and heals him for 48% of its base damage."),
    ("A034", 2, 0, "thunderclap",    "Dreadlord's Abyssal Howl",   "In 295 AoE, deals 0.82x STR-scaled damage, heals allies for 42 + 14 per level, and burns 22 enemy Mana."),
    ("A035", 3, 2, "monsoon",        "Cataclysm of the Dark Portal","Three 400-AoE collapse pulses scale with Xal'athor's STR and hero level, drain enemy Mana, and pull foes inward. The second summons two Void Zealots for 18 seconds."),

    # Hero 10: V002 — Nether Inquisitor Sargen'eth (`A036..A039`)
    ("A036", 0, 2, "flamestrike",    "Entropy Rift Storm",         "A nether storm hits a 265-AoE center and two flanking 135-AoE zones. Center targets take 0.84x INT-scaled damage and lose 12 Mana per level; flanks take 0.36x damage."),
    ("A037", 1, 1, "chainlightning", "Soul Siphon Tether",         "Drains one target: 45 + 34 per ability level + 0.85x INT bonus damage, up to 45 Mana stolen and 32 returned to Sargen'eth, plus healing for 30% of base damage."),
    ("A038", 2, 0, "thunderclap",    "Astral Phase Surge",         "In 320 AoE, deals 0.55x INT-scaled damage, heals allies for 42 HP, and restores 55 + 20 per level Mana."),
    ("A039", 3, 2, "monsoon",        "Singularity Collapse",       "Three 410-AoE singularity pulses scale with Sargen'eth's INT and hero level, burn enemy Mana, and pull foes toward the center."),

    # Hero 11: V003 — Shadowblade Akama (`A040..A043`)
    ("A040", 0, 2, "flamestrike",    "Umbral Shuriken Fan",        "A forward fan of three piercing lanes reaches 700 range: the center deals 0.86x AGI-scaled damage and the two side lanes deal 0.56x each."),
    ("A041", 1, 1, "chainlightning", "Phantom Ambush Strike",      "Shadowsteps to a walkable point just beyond one enemy and strikes for 1.38x AGI-scaled damage."),
    ("A042", 2, 0, "thunderclap",    "Smoke Veil of Karabor",      "In 260 AoE around Akama, deals 0.72x AGI-scaled damage, pushes enemies away, and summons two Void Zealots for 14 seconds."),
    ("A043", 3, 0, "roar",           "Dance of a Thousand Shadows","Three 380-AoE shadow pulses around Akama scale with AGI and hero level. Each heals allies for 12 HP and Akama for 35 HP, while pushing foes away."),

    # Hero 12: V004 — Entropy Archon Aetheron (`A044..A047`)
    ("A044", 0, 2, "flamestrike",    "Starfall Singularity",       "Point-targeted starfall singularity deals 0.94x INT-scaled damage in 285 AoE and pulls enemies toward the center."),
    ("A045", 1, 1, "chainlightning", "Dimensional Banish Bolt",    "Banish bolt hits one enemy for 0.97x INT-scaled damage, pushes it away, and drains 26 Mana if it has Mana."),
    ("A046", 2, 0, "thunderclap",    "Null-Field Purge Barrier",   "In 330 AoE, deals 32 + 16 per level damage, heals allies for 62 + 18 per level, restores 22 Mana to allies, and burns 18 enemy Mana."),
    ("A047", 3, 2, "monsoon",        "Twilight of the Cosmos",     "Three 410-AoE cosmic pulses scale with Aetheron's INT and hero level and heal nearby allies for 24 HP per pulse."),

    # ---- EMPIRE 8: RUNEFORGED BASTION ----
    # Hero 13: T001 — Stormforged Prime Thorim (`A048..A051`)
    ("A048", 0, 2, "flamestrike",    "Mjolnir Thunderfall",        "A point-targeted 280-AoE hammer strike deals 1.12x STR-scaled damage and pushes enemies away."),
    ("A049", 1, 1, "chainlightning", "Titan's Magnetic Grip",      "Magnetically pulls one target 210 units toward Thorim and deals 1.06x STR-scaled damage."),
    ("A050", 2, 0, "thunderclap",    "Overcharged Aegis Core",     "In 310 AoE, deals 0.52x STR-scaled damage, heals allies for 66 + 18 per level, grants 20 Mana, and pushes enemies outward."),
    ("A051", 3, 2, "monsoon",        "Wrath of the Pantheon",      "Three 400-AoE storm pulses scale with Thorim's STR and hero level and push enemies away. The second summons two Runic Sentinels for 16 seconds."),

    # Hero 14: T002 — Runesmith Highlord Ignis (`A052..A055`)
    ("A052", 0, 2, "flamestrike",    "Molten Slag Eruption",       "A point-targeted 260-AoE magma eruption deals 1.12x STR-scaled damage and pushes enemies away."),
    ("A053", 1, 1, "chainlightning", "Forgehammer Sundering",      "Forgehammer strikes one target for 1.18x STR-scaled damage and heals Ignis for 55 + 18 per ability level."),
    ("A054", 2, 0, "thunderclap",    "Tempered Rune-Plating",      "In 335 AoE, deals 0.4x STR-scaled damage to enemies and heals allies for 76 + 18 per level."),
    ("A055", 3, 2, "monsoon",        "Awaken Forge Colossus",      "Three 390-AoE magma pulses scale with Ignis's STR and hero level and push enemies away. The second summons one Stormforged Juggernaut for 20 seconds."),

    # Hero 15: T003 — Clockwork Vanguard Mimiron (`A056..A059`)
    ("A056", 0, 2, "flamestrike",    "Cluster Rocket Salvo",       "Three rocket impact zones hit the target area: 0.78x AGI-scaled damage in 225 AoE and 0.36x in each flanking 150 AoE; the center pushes enemies outward."),
    ("A057", 1, 1, "chainlightning", "Railgun Gauss Snipe",        "Railgun slug pierces a 58-width line from Mimiron to the target, dealing 1.32x AGI-scaled damage to enemies along the path."),
    ("A058", 2, 0, "thunderclap",    "Deploy Pocket Auto-Turrets", "In 250 AoE, deals 0.48x AGI-scaled damage and heals allies for 48 + 16 per level. Summons two Runic Sentinels for 16 seconds."),
    ("A059", 3, 2, "monsoon",        "Omega Orbital Laser",        "Three expanding 420-AoE orbital laser pulses scale with Mimiron's AGI and hero level."),

    # Hero 16: T004 — Tempest Savant Loken (`A060..A063`)
    ("A060", 0, 2, "flamestrike",    "Ionosphere Plasma Field",    "Point-targeted 280 AoE: deals INT-scaled damage and burns 20 Mana per ability level from affected enemies."),
    ("A061", 1, 1, "chainlightning", "Arc-Conduit Chain Surge",    "Lightning jumps to up to 3 enemies within 300 range; later jumps deal less damage. Loken heals 26 HP when the chain is cast."),
    ("A062", 2, 0, "thunderclap",    "Chrono-Dynamo Overdrive",    "In 335 AoE, deals 0.58x INT-scaled damage, heals allies for 50 + 20 per level, and restores 65 + 18 per level Mana."),
    ("A063", 3, 2, "monsoon",        "Stormcore Superconductor",   "Three 410-AoE Tesla pulses scale with Loken's INT and hero level, heal allies, and burn enemy Mana. The second summons two Gyro-Interceptors for 18 seconds."),
]

# Stock Warcraft III command-button art, mapped one-to-one to the custom skills.
# Filenames are verified against 1.27.1 native object metadata and use the game's
# own BTN/DISBTN assets on 1.26a, 1.27b and Reforged.
_SKILL_BUTTON_STEMS = (
    "BTNMonsoon", "BTNChainLightning", "BTNHealingWave", "BTNCrushingWave",
    "BTNFanOfKnives", "BTNBlink", "BTNImmolationOn", "BTNMetamorphosis",
    "BTNImpale", "BTNEnsnare", "BTNFrostArmor", "BTNLocustSwarm",
    "BTNVolcano", "BTNCharm", "BTNRejuvenation", "BTNTornado",
    "BTNWallOfFire", "BTNManaDrain", "BTNHealingWard", "BTNMarkOfFire",
    "BTNSearingArrowsOn", "BTNTheBlackArrow", "BTNWindWalkOn", "BTNStarfall",
    "BTNWarStomp", "BTNCriticalStrike", "BTNBattleStations", "BTNStampede",
    "BTNHolyBolt", "BTNStormBolt", "BTNDivineIntervention", "BTNResurrection",
    "BTNDeathAndDecay", "BTNCarrionSwarm", "BTNAntiMagicShell", "BTNDarkSummoning",
    "BTNBlizzard", "BTNLifeDrain", "BTNDarkRitual", "BTNAbsorbMagic",
    "BTNShadowStrike", "BTNAmbush", "BTNEtherealFormOn", "BTNSpiritOfVengeance",
    "BTNMoonStone", "BTNBanish", "BTNSpellShieldAmulet", "BTNInfernal",
    "BTNHammer", "BTNShockWave", "BTNAvatarOn", "BTNEarthquake",
    "BTNFire", "BTNGolemStormBolt", "BTNRepairOn", "BTNMechanicalCritter",
    "BTNClusterRockets", "BTNFlare", "BTNPocketFactory", "BTNFireForTheCannon",
    "BTNManaFlare", "BTNOrbOfLightning", "BTNManaRechargeOn", "BTNStormEarth&Fire",
)
assert len(_SKILL_BUTTON_STEMS) == 64 and len(set(_SKILL_BUTTON_STEMS)) == 64
HERO_SKILL_ICON_PATHS = {
    spec[0]: f"{BTN_PREFIX}{stem}.blp"
    for spec, stem in zip(HERO_SKILL_SPECS_64, _SKILL_BUTTON_STEMS)
}


def _make_ancl_hero_skill(
    idx: int,
    new_id: str,
    slot_idx: int,
    tgt_mode: int,
    order_str: str,
    name: str,
    desc: str,
) -> Tuple[str, str, List[LevelModEntry]]:
    """
    Build a 100% compliant `ANcl` (Channel) custom Hero ability entry for `war3map.w3a`:
      - Every skill receives a distinct native Warcraft III button icon selected for its effect.
      - Sets `Ncl1..6` across EVERY level `1..levels` so levels 2 & 3 never revert!
    """
    icon = HERO_SKILL_ICON_PATHS[new_id]
    is_ult = (slot_idx == 3)
    levels = 1 if is_ult else 3
    btn_x = slot_idx
    hotkey = ("Q", "W", "E", "R")[slot_idx]
    if 4 <= idx < 8:
        fx = "WM_FX_FelGlaive.mdx"
    elif idx < 16:
        fx = "WM_FX_Abyssal.mdx"
    elif idx < 32:
        fx = "WM_FX_Solar.mdx"
    elif idx < 48:
        fx = "WM_FX_Void.mdx"
    elif idx < 60:
        fx = "WM_FX_Runic.mdx"
    else:
        fx = "WM_FX_Emerald.mdx"

    ncl2 = 2 if tgt_mode == 2 else (1 if tgt_mode == 1 else 0)
    ncl3 = 3 if tgt_mode == 2 else 1

    mods: List[LevelModEntry] = [
        ("anam", VT_STR, 0, 0, name),
        ("aart", VT_STR, 0, 0, icon),
        ("arar", VT_STR, 0, 0, icon),
        ("abpx", VT_INT, 0, 0, btn_x),
        ("abpy", VT_INT, 0, 0, 2),
        ("arpx", VT_INT, 0, 0, btn_x),
        ("arpy", VT_INT, 0, 0, 0),
        ("ahky", VT_STR, 0, 0, hotkey),
        ("arhk", VT_STR, 0, 0, hotkey),
        ("aher", VT_INT, 0, 0, 1),
        ("alev", VT_INT, 0, 0, levels),
        ("alsk", VT_INT, 0, 0, 6 if is_ult else 1),
        ("acat", VT_STR, 0, 0, fx),
        ("aeat", VT_STR, 0, 0, ""),
        ("atat", VT_STR, 0, 0, ""),
        ("aret", VT_STR, 0, 0, f"Learn {name} - [|cffffcc00Level %d|r] (|cffffcc00{hotkey}|r)"),
        ("arut", VT_STR, 0, 0, desc),
    ]

    for lv in range(1, levels + 1):
        cd = 85.0 if is_ult else (13.0 - (lv - 1) * 1.5 if slot_idx == 0 else (11.0 - (lv - 1) * 1.0 if slot_idx == 1 else 14.0 - (lv - 1) * 1.5))
        mp = 145 if is_ult else (75 + (lv - 1) * 10 if slot_idx == 0 else (65 + (lv - 1) * 10 if slot_idx == 1 else 70 + (lv - 1) * 10))
        rng = 750.0 if (is_ult and tgt_mode == 2) else (700.0 if tgt_mode == 2 else (625.0 if tgt_mode == 1 else 0.0))
        aoe = 390.0 if (is_ult and tgt_mode == 2) else (275.0 if tgt_mode == 2 else 0.0)
        tars = "air,enemies,ground,neutral,organic" if tgt_mode == 1 else ""

        mods.extend([
            ("Ncl1", VT_UNREAL, lv, 1, 0.0),
            ("Ncl2", VT_INT,    lv, 2, ncl2),
            ("Ncl3", VT_INT,    lv, 3, ncl3),
            ("Ncl4", VT_UNREAL, lv, 4, 0.0),
            ("Ncl5", VT_INT,    lv, 5, 0),
            ("Ncl6", VT_STR,    lv, 6, order_str),
            ("acdn", VT_UNREAL, lv, 0, cd),
            ("amcs", VT_INT,    lv, 0, mp),
            ("aran", VT_UNREAL, lv, 0, rng),
            ("aare", VT_UNREAL, lv, 0, aoe),
            ("atar", VT_STR,    lv, 0, tars),
            ("atp1", VT_STR,    lv, 0, f"{name} - [|cffffcc00Level {lv}|r] (|cffffcc00{hotkey}|r)"),
            ("aub1", VT_STR,    lv, 0, f"{desc}|n|cff38bdf8Cooldown:|r {cd:.0f}s   |cffc084fcMana:|r {mp}"),
        ])
    return ("ANcl", new_id, mods)


def build_ability_modifications() -> Tuple[
    List[Tuple[str, str, List[LevelModEntry]]],
    List[Tuple[str, str, List[LevelModEntry]]],
]:
    assert len(HERO_SKILL_SPECS_64) == 64
    seen_ids = set()
    cust: List[Tuple[str, str, List[LevelModEntry]]] = []
    for idx, (aid, slot_idx, tgt_mode, order_str, name, desc) in enumerate(HERO_SKILL_SPECS_64):
        assert aid not in seen_ids, f"Duplicate ability ID {aid}"
        seen_ids.add(aid)
        cust.append(_make_ancl_hero_skill(idx, aid, slot_idx, tgt_mode, order_str, name, desc))
    return [], cust


# ==============================================================================
# 3. FULL CUSTOM GAME INTERFACE & RPG INFOCARD SKIN (`war3mapSkin.txt`)
# ==============================================================================

def serialize_war3map_skin() -> bytes:
    """
    Generate `war3mapSkin.txt` (`[CustomSkin]` + `[FrameDef]`) replacing:
      - Mouse Cursor (`UI\\Cursor\\HumanCursor.mdl` + custom `256x128` Gauntlet/Reticle BLP)
      - All 16 Infocard Damage Type icons (Upgraded + Neutral)
      - All 16 Infocard Armor Type icons (Upgraded + Neutral)
      - All 6 Hero Primary Attribute icons (`STR`, `AGI`, `INT` on Infocard & Hero Panel)
      - Retains recognizable native Warcraft III command-card action buttons
      - Uses native race-appropriate construction buttons for Naga, Human, Undead, Orc and Night Elf
      - Resource bar icons, inventory filler, dark obsidian dialog/tooltip/multiboard backgrounds, and RPG Damage/Armor text styling!
    """
    IC = "UI\\CrownUI\\Infocard\\"
    lines = [
        "[CustomSkin]",
        # Custom Animated Sovereign Gauntlet & Runic Reticle Mouse Cursor
        "Cursor=UI\\Cursor\\HumanCursor.mdl",
        # Custom Top-Bar & Tooltip Resource Icons
        "GoldIcon=UI\\CrownUI\\IconGold.blp",
        "LumberIcon=UI\\CrownUI\\IconLumber.blp",
        "SupplyIcon=UI\\CrownUI\\IconSupply.blp",
        "UpkeepIcon=UI\\CrownUI\\IconUpkeep.blp",
        "InfoPanelIconGold=UI\\CrownUI\\IconGold.blp",
        "InfoPanelIconFood=UI\\CrownUI\\IconSupply.blp",
        "ToolTipGoldIcon=UI\\CrownUI\\IconGold.blp",
        "ToolTipLumberIcon=UI\\CrownUI\\IconLumber.blp",
        "ToolTipSupplyIcon=UI\\CrownUI\\IconSupply.blp",
        "ConsoleInventoryNoCapacity=UI\\CrownUI\\SlotFiller.blp",
        # Dark Obsidian-Gold Non-Classic Dialog, Tooltip & Multiboard Backdrops
        "ToolTipBackground=UI\\CrownUI\\MenuBG.blp",
        "UnitTipBackground=UI\\CrownUI\\MenuBG.blp",
        "EscMenuBackground=UI\\CrownUI\\MenuBG.blp",
        "QuestDialogBackground=UI\\CrownUI\\MenuBG.blp",
        "MultiboardBackground=UI\\CrownUI\\MenuBG.blp",
        f"MultiboardDefaultIcon={BTN_PREFIX}BTN_WM_Portrait_Hvsh.blp",
        f"IdlePeon={BTN_PREFIX}BTNPeasant.blp",

        # ---- Badass RPG Infocard Damage Type Icons (Upgraded + Neutral) ----
        f"InfoPanelIconDamageUnknown={IC}DmgNormal.blp",
        f"InfoPanelIconDamageNormal={IC}DmgNormal.blp",
        f"InfoPanelIconDamageMelee={IC}DmgNormal.blp",
        f"InfoPanelIconDamagePierce={IC}DmgPierce.blp",
        f"InfoPanelIconDamageSiege={IC}DmgSiege.blp",
        f"InfoPanelIconDamageMagic={IC}DmgMagic.blp",
        f"InfoPanelIconDamageChaos={IC}DmgChaos.blp",
        f"InfoPanelIconDamageHero={IC}DmgHero.blp",

        f"InfoPanelIconDamageUnknownNeutral={IC}DmgNormalNeutral.blp",
        f"InfoPanelIconDamageNormalNeutral={IC}DmgNormalNeutral.blp",
        f"InfoPanelIconDamageMeleeNeutral={IC}DmgNormalNeutral.blp",
        f"InfoPanelIconDamagePierceNeutral={IC}DmgPierceNeutral.blp",
        f"InfoPanelIconDamageSiegeNeutral={IC}DmgSiegeNeutral.blp",
        f"InfoPanelIconDamageMagicNeutral={IC}DmgMagicNeutral.blp",
        f"InfoPanelIconDamageChaosNeutral={IC}DmgChaosNeutral.blp",
        f"InfoPanelIconDamageHeroNeutral={IC}DmgHeroNeutral.blp",

        # ---- Badass RPG Infocard Armor Type Icons (Upgraded + Neutral) ----
        f"InfoPanelIconArmorUnknown={IC}ArmSmall.blp",
        f"InfoPanelIconArmorSmall={IC}ArmSmall.blp",
        f"InfoPanelIconArmorMedium={IC}ArmMedium.blp",
        f"InfoPanelIconArmorLarge={IC}ArmLarge.blp",
        f"InfoPanelIconArmorFort={IC}ArmFort.blp",
        f"InfoPanelIconArmorNormal={IC}ArmMedium.blp",
        f"InfoPanelIconArmorHero={IC}ArmHero.blp",
        f"InfoPanelIconArmorDivine={IC}ArmDivine.blp",
        f"InfoPanelIconArmorNone={IC}ArmNone.blp",

        f"InfoPanelIconArmorUnknownNeutral={IC}ArmSmallNeutral.blp",
        f"InfoPanelIconArmorSmallNeutral={IC}ArmSmallNeutral.blp",
        f"InfoPanelIconArmorMediumNeutral={IC}ArmMediumNeutral.blp",
        f"InfoPanelIconArmorLargeNeutral={IC}ArmLargeNeutral.blp",
        f"InfoPanelIconArmorFortNeutral={IC}ArmFortNeutral.blp",
        f"InfoPanelIconArmorNormalNeutral={IC}ArmMediumNeutral.blp",
        f"InfoPanelIconArmorHeroNeutral={IC}ArmHeroNeutral.blp",
        f"InfoPanelIconArmorDivineNeutral={IC}ArmDivineNeutral.blp",
        f"InfoPanelIconArmorNoneNeutral={IC}ArmNoneNeutral.blp",

        # ---- Custom Hero Primary Attribute Icons (`STR`, `AGI`, `INT`) ----
        f"InfoPanelIconHeroIconSTR={IC}AttrSTR.blp",
        f"InfoPanelIconHeroIconAGI={IC}AttrAGI.blp",
        f"InfoPanelIconHeroIconINT={IC}AttrINT.blp",
        f"HeroStrengthIcon={IC}AttrSTR.blp",
        f"HeroAgilityIcon={IC}AttrAGI.blp",
        f"HeroIntelligenceIcon={IC}AttrINT.blp",

        # Keep Warcraft III's recognizable native attack/move/stop/patrol/skill buttons.
        # Race-specific construction buttons use stock faction art, not generated glyphs.
        f"CommandBasicStruct={BTN_PREFIX}BTNAltarOfDepths.blp",
        f"CommandBasicStructHuman={BTN_PREFIX}BTNHumanBuild.blp",
        f"CommandBasicStructUndead={BTN_PREFIX}BTNScourgeBuild.blp",
        f"CommandBasicStructOrc={BTN_PREFIX}BTNBasicStruct.blp",
        f"CommandBasicStructNightElf={BTN_PREFIX}BTNNightElfBuild.blp",
        "",
        "[FrameDef]",
        "UPKEEP_NONE=|cff38bdf8WarMahdi Crown|r",
        "UPKEEP_LOW=|cffffd166Imperial Tax (Low)|r",
        "UPKEEP_HIGH=|cffff5566War Levy (High)|r",
        "COLON_GOLD=|cffffd166Imperial Gold:|r",
        "COLON_LUMBER=|cff34d399Arcane Timber:|r",
        "COLON_FOOD_TOTAL=|cffffcc00Empire Supply:|r",
        "COLON_DAMAGE=|cffffd166Attack Power:|r",
        "COLON_ARMOR=|cff93c5fdDefense Rating:|r",
        "COLON_STRENGTH=|cffff6b6bStrength:|r",
        "COLON_AGILITY=|cff4ade80Agility:|r",
        "COLON_INTELLECT=|cff60a5faIntelligence:|r",
        "DAMAGE_HERO=Class: |cffffcc00Sovereign Hero|r",
        "DAMAGE_CHAOS=Class: |cffd977ffChaos Oblivion|r",
        "DAMAGE_MAGIC=Class: |cff38bdf8Arcane Spell|r",
        "DAMAGE_SIEGE=Class: |cffff8c42Siege Ordinance|r",
        "DAMAGE_PIERCE=Class: |cff4ade80Piercing Volley|r",
        "DAMAGE_NORMAL=Class: |cffe2e8f0Tempered Cleave|r",
        "DAMAGE_MELEE=Class: |cffe2e8f0Tempered Cleave|r",
        "ARMOR_HERO=Aegis: |cffffcc00Sovereign Ward|r",
        "ARMOR_DIVINE=Aegis: |cfffff3b0Celestial Divine|r",
        "ARMOR_FORT=Aegis: |cfffbbf24Citadel Bastion|r",
        "ARMOR_LARGE=Aegis: |cffff7b72Heavy Plate|r",
        "ARMOR_MEDIUM=Aegis: |cff7dd3fcTempered Scale|r",
        "ARMOR_NORMAL=Aegis: |cff7dd3fcTempered Scale|r",
        "ARMOR_SMALL=Aegis: |cff6ee7b7Agile Guard|r",
        "ARMOR_NONE=Aegis: |cffc084fcAstral Shroud|r",
        "UPPER_BUTTON_QUEST_TIP=|cffffcc00WarMahdi Codex & Guide|r (|cffffcc00F9|r)",
        "RESOURCE_UBERTIP_UPKEEP=|cffffcc00Crown of WarMahdi v5 — 8 Playable Empires|r|n|cff6ee7b70-50 Supply:|r 100% Gold Income|n|cffffd16651-80 Supply:|r 70% Gold Income|n|cffff666681-100 Supply:|r 40% Gold Income",
        "",
    ]
    return "\r\n".join(lines).encode("utf-8")


# ==============================================================================
# 4. CUSTOM FACTION `.AI` SCRIPTS (`voidborn_melee.ai` & `runeforged_melee.ai`)
# ==============================================================================

def _build_custom_faction_ai(
    title_comment: str,
    ai_display_name: str,
    worker: str, hall1: str, hall2: str, hall3: str,
    supply: str, rax: str, armory: str, altar: str, shop: str, tower: str,
    sanctum: str, heavy_bay: str,
    u_melee: str, u_range: str, u_heavy: str, u_caster: str, u_flyer: str, u_siege: str, u_champ: str,
    h1: str, h2: str, h3: str, h4: str,
    h1_skills: Tuple[str, str, str, str],
    h2_skills: Tuple[str, str, str, str],
    h3_skills: Tuple[str, str, str, str],
    h4_skills: Tuple[str, str, str, str],
    upg_atk: str, upg_arm: str,
) -> str:
    return f"""//============================================================================
//  {title_comment}
//  Tournament Melee AI for `(8) Crown of WarMahdi` v5
//============================================================================
globals
    integer CF_WORKER    = '{worker}'
    integer CF_HALL_T1   = '{hall1}'
    integer CF_HALL_T2   = '{hall2}'
    integer CF_HALL_T3   = '{hall3}'
    integer CF_SUPPLY    = '{supply}'
    integer CF_RAX       = '{rax}'
    integer CF_ARMORY    = '{armory}'
    integer CF_ALTAR     = '{altar}'
    integer CF_SHOP      = '{shop}'
    integer CF_TOWER     = '{tower}'
    integer CF_SANCTUM   = '{sanctum}'
    integer CF_HEAVY_BAY = '{heavy_bay}'

    integer CF_MELEE     = '{u_melee}'
    integer CF_RANGE     = '{u_range}'
    integer CF_HEAVY     = '{u_heavy}'
    integer CF_CASTER    = '{u_caster}'
    integer CF_FLYER     = '{u_flyer}'
    integer CF_SIEGE     = '{u_siege}'
    integer CF_CHAMP     = '{u_champ}'

    integer CF_HERO_1    = '{h1}'
    integer CF_HERO_2    = '{h2}'
    integer CF_HERO_3    = '{h3}'
    integer CF_HERO_4    = '{h4}'

    integer CF_UPG_ATK   = '{upg_atk}'
    integer CF_UPG_ARM   = '{upg_arm}'

    boolean cf_tier2_done = false
    boolean cf_tier3_done = false
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

function CFNeedUnit takes integer qty, integer unitId, integer town returns nothing
    local integer have = GetUnitCount(unitId)
    if have < qty then
        call SetProduce(qty - have, unitId, town)
    endif
endfunction

function CFNeedUpgrade takes integer lvl, integer upgId returns nothing
    if GetUpgradeLevel(upgId) < lvl then
        call SetUpgrade(upgId)
    endif
endfunction

function CFSetSkillsFor takes integer hid returns nothing
    local integer q = '{h1_skills[0]}'
    local integer w = '{h1_skills[1]}'
    local integer e = '{h1_skills[2]}'
    local integer r = '{h1_skills[3]}'
    if hid == CF_HERO_2 then
        set q = '{h2_skills[0]}'
        set w = '{h2_skills[1]}'
        set e = '{h2_skills[2]}'
        set r = '{h2_skills[3]}'
    elseif hid == CF_HERO_3 then
        set q = '{h3_skills[0]}'
        set w = '{h3_skills[1]}'
        set e = '{h3_skills[2]}'
        set r = '{h3_skills[3]}'
    elseif hid == CF_HERO_4 then
        set q = '{h4_skills[0]}'
        set w = '{h4_skills[1]}'
        set e = '{h4_skills[2]}'
        set r = '{h4_skills[3]}'
    endif
    set skill[ 1] = q
    set skill[ 2] = w
    set skill[ 3] = q
    set skill[ 4] = e
    set skill[ 5] = q
    set skill[ 6] = r
    set skill[ 7] = w
    set skill[ 8] = w
    set skill[ 9] = e
    set skill[10] = e
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

    call CFSetSkillsFor(hero_id)
    call SetSkillArray(1, hero_id)
    call CFSetSkillsFor(hero_id2)
    call SetSkillArray(2, hero_id2)
    call CFSetSkillsFor(hero_id3)
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
        call Sleep(5)
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
            call CFNeedUnit(12, CF_WORKER, -1)
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

    call Sleep(20)
    loop
        loop
            set armyReady = GetUnitCountDone(hero_id) + GetUnitCountDone(hero_id2) + GetUnitCountDone(hero_id3)
            exitwhen armyReady >= 1 and (GetUnitCountDone(CF_MELEE) + GetUnitCountDone(CF_HEAVY) + GetUnitCountDone(CF_RANGE)) >= 3
            exitwhen (GetUnitCountDone(CF_MELEE) + GetUnitCountDone(CF_HEAVY) + GetUnitCountDone(CF_RANGE)) >= 5
            call Sleep(4)
        endloop

        call InitAssaultGroup()
        call CFAttackWave(1, hero_id)
        call CFAttackWave(1, hero_id2)
        call CFAttackWave(1, hero_id3)
        call CFAttackWave(5, CF_MELEE)
        call CFAttackWave(4, CF_RANGE)
        call CFAttackWave(3, CF_HEAVY)
        call CFAttackWave(3, CF_CASTER)
        call CFAttackWave(2, CF_FLYER)
        call CFAttackWave(2, CF_SIEGE)
        call CFAttackWave(2, CF_CHAMP)

        set needsExp = (GetMinesOwned() < 2 and cf_tier2_done)
        set hasSiege = (GetUnitCountDone(CF_SIEGE) >= 1 or GetUnitCountDone(CF_CHAMP) >= 1)
        set majorOk  = (cf_tier2_done or (GetUnitCountDone(CF_MELEE) + GetUnitCountDone(CF_RANGE)) >= 5)
        set airUnits = (GetUnitCountDone(CF_FLYER) >= 2 and GetUnitCountDone(CF_MELEE) == 0 and GetUnitCountDone(CF_HEAVY) == 0)

        call SingleMeleeAttack(needsExp, hasSiege, majorOk, airUnits)
        call Sleep(4)
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
        ("A032", "A033", "A034", "A035"),
        ("A036", "A037", "A038", "A039"),
        ("A040", "A041", "A042", "A043"),
        ("A044", "A045", "A046", "A047"),
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
        ("A048", "A049", "A050", "A051"),
        ("A052", "A053", "A054", "A055"),
        ("A056", "A057", "A058", "A059"),
        ("A060", "A061", "A062", "A063"),
        "R002", "R003",
    )
