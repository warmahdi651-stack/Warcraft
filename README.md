# `(8) Crown of WarMahdi` — v8 Warcraft III 8-Empire Altered Melee

A **192×192, 8-player** Sunken-Astral map for classic Warcraft III TFT (1.26a/1.27b). This source-backed gameplay/AI/art pass preserves the existing terrain, theme, and in-game UI.

## Download and preview

- **Map (`.w3x`):** [Download Crown of WarMahdi v8](https://raw.githubusercontent.com/warmahdi651-stack/Warcraft/arena/483b840a-warcraft/maps/%288%29CrownOfWarMahdi.w3x)
- **Tactical map preview:** `maps/(8)CrownOfWarMahdi_Preview.png`
- **Web preview:** `python3 web/server.py` (port 8080); includes the interactive map, archive manifest, verification summary, and download route. Manifest counts are computed from the current archive/generated metadata and checked by the verifier.
- **Classic client QA:** see [`CLASSIC_CLIENT_QA.md`](CLASSIC_CLIENT_QA.md) for the pending 1.26a/1.27b smoke-test, AI, spell, and match-balance checklist.

Install into `Warcraft III/Maps/FrozenThrone/` for classic TFT 1.26a/1.27b clients.

## v8 gameplay and AI pass

- **Custom AI has one controller:** standard Human, Orc, Undead, and Night Elf players retain native melee AI. Custom factions are directed by the guarded JASS controller; it no longer starts competing imported `.ai` scripts for the same workers, halls, altars, or production buildings.
- **Sequential, recoverable orders:** custom AI tracks one pending construction order per player and clears it on construction completion (with a timeout recovery path). Worker training, hall upgrades, altar heroes, research, and each production building have idle-order checks and cooldowns so a later order cannot replace the first one.
- **Workers and economy:** Mur'gul Slaves (`nmpe`), Silvermoon Workers (`nhew`), Void Thralls (`v010`), and Runeforged Automatons (`t010`) are explicitly recognized as workers. The Naga and Sunfury worker records now carry the Peon type tag; Naga has explicit Harvest/Repair abilities. Idle custom workers are assigned to the nearest gold mine or trees.
- **Faction-specific openings:**
  - **Sunfury Imperium:** adapts the selected Human fast-altar/faster-rifle archetype into an early Altar and Sunspire Barracks, then favors High Elven Archers before a swordsman/chaplain, siege, and air transition.
  - **Voidborn Legion:** opens with supply and the Rift Gate before its delayed Altar, emphasizing early ranged pressure before tier upgrades—an adaptation of Undead Fiend openings, not a copied Crypt/Fiend build.
  - **Abyssal Tideborn:** opens Coral Bed → Altar → Spawning Grounds and applies early Naga pressure, taking inspiration from Night Elf fast-Huntress tempo.
  - **Runeforged Bastion:** prioritizes its Altar and then ranged Thunder Arquebusiers, with a restrained early barracks/tech investment inspired by Orc fast-tech and Headhunter pressure.
- **Smarter army behavior:** the controller builds tier-aware mixed compositions, selects one hero order at a time, independently spends custom hero skill points, researches one available upgrade at a time, assigns idle workers, creeps, contests the central shrine, and pushes enemy bases. Tactical micro excludes custom workers explicitly.
- **Fair fog-of-war intelligence:** enemy-unit selection and composition reads are gated by `IsUnitVisible` for the AI player. It stores per-opponent last-seen army/base-area centroids with timestamps, expires those coordinates after 120 seconds for scouting, and never uses a hidden enemy unit's current position. Late scouting may use only the public map start location as a search prior.
- **Adaptive strategy and counter-production:** the commander chooses among visible creep camps, the Shrine, a visible enemy, home/expansion defense, a live expansion guard, a recent last-seen point, and public-start scouting. Visible air, caster, ranged-unit and town-hall-tier observations influence unit ratios and tech-order cadence; old air/caster/ranged estimates decay rather than granting permanent omniscience.
- **Natural expansion:** after Tier 3, at 5:00 or later, with an 8-unit army, 9 workers, and at least 850 gold / 320 lumber, the custom AI may build one extra hall only at a currently visible, unoccupied natural mine on buildable terrain. It then staffs the second mine with up to three workers. This keeps expansion scouting and site choice tied to the AI's vision.
- **Coordinated micro and hero spell decisions:** nearby visible ally/enemy counts guide group retreat and focus-fire. Custom heroes target dense visible clusters with point spells, prefer high-value/low-health targets for single-target attacks, reserve Mana Burn for targets with meaningful mana, gate Resurrection on a fallen ally, and weigh healing/offensive E skills against local injuries and enemy density.
- **Difficulty and measurement:** all four levels primarily improve decision thresholds. Novice has no income bonus; on custom races only, Veteran adds +2g/+1l, Grandmaster +4g/+2l, or Mythic +7g/+3l per four-second macro tick. The host sees these values before choosing. Type `-aistats` in-game to inspect objective, visible-contact, defense, retreat, focus-fire, spell-order, counter-order, and expansion counters.

These are strategy inspirations adapted to each custom tech tree. They are not literal standard-race order strings or guarantees of tournament-level decision-making. The verifier checks source/binary invariants only; the new AI behavior still needs classic-client testing and balance matches.

## Building model pass

- **Naga:** the original `nnfm`, `nntg`, `nntt`, `nnsg`, `nnsa`, and `nnad` structures keep their verified campaign-native models. The added Tidal Treasury (`n003`), Coral Forge (`n004`), and Abyssal Behemoth Pool (`n005`) now have three distinct version-800 MDX models and matching true-color textures, rather than reusing the Shrine of Ashjara, Altar of Depths, and Spawning Grounds models already used by other build-menu entries.
- **Sunfury:** Altar, Arcane Vault, Barracks, Workshop, Gryphon Aviary, Blacksmith, and Lumbermill are aligned to their role-matched native Human building models. **Voidborn** uses its Undead Altar, Ziggurat tower, and Bone Yard models; **Runeforged** uses Orc Altar of Storms, Voodoo Lounge, and Watch Tower models.
- Static checks resolve model assignments for the four audited custom-faction building sets against object data/native metadata and cross-check the classic Human, Orc, Undead, Night Elf, and Naga worker build lists. They reject duplicate models between distinct roles; reuse is allowed only in Blizzard’s native tier chains (Human/Orc/Undead/Night Elf halls and Undead Ziggurat) and the Naga/Sunfury hall tiers.

## Hero skills and spell visuals

- Preserves **16 heroes and 64 exclusive skills**. Core ranks remain learnable at levels 1/3/5; ultimates remain level-gated to 6. Existing selected signature skills, including Mana Burn, Phoenix, and Resurrection, are retained.
- Adds **64 separate skill-specific MDX effects and 64 true-color textures**, plus 64 individually illustrated 64×64 command-button icons with matching disabled-state twins. Each ability dispatches to its own model; the assets vary by geometric form (burst, bolt, shield, portal), proportions, rune pattern, and hero theme—not hue alone. Six faction-sigil models remain for other gameplay effects (**70 VFX MDX models**; 73 MDX files including the three Naga building models).
- Differentiates the ultimates' *play patterns*, not only their colors: Vashj's Tsunami moves through three damage/heal/push fronts; Akama's shadow dance is a tighter 300-AoE around the assassin; Mimiron's Omega Laser locks its cast-time aim, reveals all three 1040-unit lanes for 0.55 seconds, then hits those 144-wide lines sequentially. The laser markers are explicitly cleaned up after the sweep or if Mimiron dies.
- Timed summons now search for terrain- and occupancy-safe spawn points; pull/push displacement checks unit/building clearance and only moves to a nearby safe point, otherwise leaving the unit where it is. This avoids placing summons inside obstacles or shoving units through occupied cells.
- Palette-encoded BLP is restricted to command-button artwork: ten hero-portrait pairs and 64 custom skill BTN/DISBTN pairs (148 icons total). Skill VFX and building textures use true-color BLP.

## Melee fairness and objective pass

- **Exact neutral-object symmetry:** creep members and their item carriers now mirror with the terrain across all eight D4 transforms. Reflected camps preserve left/right member placement instead of silently shifting unique units or drops to the wrong side; diagonal camps use reflection-safe formations.
- **Creep economy audit:** the packed `.w3x` is checked against its 36 previewed camps, actual neutral unit rosters, reference unit levels, and exact drop codes/chances. The seven camp budgets remain 6, 13, 13, 12, 10, 21, and 23 levels; all 36 groups must match their stated tier and loot.
- **Lobby-aware Crown Shrine:** capture and gold rewards now follow Warcraft's actual lobby alliances, so 4v4, 2v2, and FFA no longer inherit an arbitrary player-slot split. An uncontested holder's active allies receive +3 gold per 2-second tick (only the captor in FFA); enemy presence stops the gold reward. The HUD shows the current controller, and the web description now matches the implemented reward/healing behavior.
- **Equal race-pick economy:** Random Custom no longer grants +50 starting gold, eliminating an exploitable bonus when players reopen the race picker during its allowed switch window.
- The verifier now has **17 static/binary stages**, including neutral-object D4 symmetry, camp rosters/loot/level budgets, shrine-alliance behavior, race-choice economy, fog-safe intel, adaptive AI, and telemetry hooks. It still does not simulate a live Warcraft III match.

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

**Testing limitation:** no in-client Warcraft III test or human match has been performed for this update. The map still needs a fresh client smoke test on TFT 1.26a/1.27b—especially build menus, the imported button pairs, safe summon/displacement behavior, the three revised ultimate geometries, worker harvesting, custom building paths, MDX rendering, and AI orders. Static checks cannot establish live gameplay balance or visual rendering.
