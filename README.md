# `(8) Crown of WarMahdi` — v7 Warcraft III 8-Empire Altered Melee

A **192×192, 8-player** Sunken-Astral map for Warcraft III TFT and Reforged. This source-only gameplay/AI/VFX pass preserves the existing terrain, theme, and in-game UI.

## Download and preview

- **Map (`.w3x`):** [Download Crown of WarMahdi v7](https://raw.githubusercontent.com/warmahdi651-stack/Warcraft/arena/483b840a-warcraft/maps/%288%29CrownOfWarMahdi.w3x)
- **Tactical map preview:** `maps/(8)CrownOfWarMahdi_Preview.png`
- **Web preview:** `python3 web/server.py` (port 8080); includes the interactive map, archive manifest, verification summary, and download route.

Install into `Warcraft III/Maps/FrozenThrone/` for classic clients or `Documents/Warcraft III/Maps/Download/` for Reforged.

## v7 gameplay and AI pass

- **Custom AI has one controller:** standard Human, Orc, Undead, and Night Elf players retain native melee AI. Custom factions are directed by the guarded JASS controller; it no longer starts competing imported `.ai` scripts for the same workers, halls, altars, or production buildings.
- **Sequential, recoverable orders:** custom AI tracks one pending construction order per player and clears it on construction completion (with a timeout recovery path). Worker training, hall upgrades, altar heroes, research, and each production building have idle-order checks and cooldowns so a later order cannot replace the first one.
- **Workers and economy:** Mur'gul Slaves (`nmpe`), Silvermoon Workers (`nhew`), Void Thralls (`v010`), and Runeforged Automatons (`t010`) are explicitly recognized as workers. The Naga and Sunfury worker records now carry the Peon type tag; Naga has explicit Harvest/Repair abilities. Idle custom workers are assigned to the nearest gold mine or trees.
- **Faction-specific openings:**
  - **Sunfury Imperium:** adapts the selected Human fast-altar/faster-rifle archetype into an early Altar and Sunspire Barracks, then favors High Elven Archers before a swordsman/chaplain, siege, and air transition.
  - **Voidborn Legion:** opens with supply and the Rift Gate before its delayed Altar, emphasizing early ranged pressure before tier upgrades—an adaptation of Undead Fiend openings, not a copied Crypt/Fiend build.
  - **Abyssal Tideborn:** opens Coral Bed → Altar → Spawning Grounds and applies early Naga pressure, taking inspiration from Night Elf fast-Huntress tempo.
  - **Runeforged Bastion:** prioritizes its Altar and then ranged Thunder Arquebusiers, with a restrained early barracks/tech investment inspired by Orc fast-tech and Headhunter pressure.
- **Smarter army behavior:** the controller builds tier-aware mixed compositions, selects one hero order at a time, independently spends custom hero skill points, researches one available upgrade at a time, assigns idle workers, creeps, contests the central shrine, and pushes enemy bases. Tactical micro excludes custom workers explicitly.

These are strategy inspirations adapted to each custom tech tree. They are not literal standard-race order strings or guarantees of tournament-level decision-making.

## Hero skills and spell visuals

- Preserves **16 heroes and 64 exclusive skills**. Core ranks remain learnable at levels 1/3/5; ultimates remain level-gated to 6. Existing selected signature skills, including Mana Burn, Phoenix, and Resurrection, are retained.
- Adds **64 separate skill-specific MDX effects and 64 true-color textures**. Each ability dispatches to its own model; the assets vary by geometric form (burst, bolt, shield, portal), proportions, rune pattern, and hero theme—not hue alone. Six faction-sigil models remain for other gameplay effects (**70 custom MDX models total**).
- Palette-encoded BLP remains restricted to command-button portrait icons. Skill VFX textures use true-color BLP.

## Build and verification

```bash
python3 -m venv .venv
.venv/bin/pip install Pillow
mkdir -p /tmp/wc3ref
git clone --depth 1 https://github.com/sumneko/w3x2lni /tmp/wc3ref/w3x2lni
git clone --depth 1 https://github.com/lep/jassdoc /tmp/wc3ref/jassdoc
npm install --prefix /tmp/wc3ref mdx-m3-viewer@5.12.0
.venv/bin/python src/build_map.py
.venv/bin/python src/verify_map.py
```

Verification is static/binary; it does not launch Warcraft III.

**Testing limitation:** the agent did not run an in-client Warcraft III test. The previous screenshots were supplied by the user. The updated map still needs a fresh client smoke test on 1.26a/1.27b and Reforged, especially for build menus, worker harvesting, custom building paths, MDX rendering, and AI order behavior. Static checks cannot establish gameplay balance or compatibility beyond the checked files/APIs.
