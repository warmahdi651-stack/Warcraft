# `(8) Crown of WarMahdi` — v9 Warcraft III 8-Empire Altered Melee

A **192×192, 8-player** Sunken-Astral map for classic Warcraft III TFT (1.26a/1.27b), with a 600-supply ceiling. This source-backed gameplay/AI/art pass preserves the terrain, overall theme, and HUD layout while refreshing the requested portraits, icons, building tiers, and shrine dressing.

## Download and preview

- **Map (`.w3x`):** [Download Crown of WarMahdi v9](https://raw.githubusercontent.com/warmahdi651-stack/Warcraft/arena/483b840a-warcraft/maps/%288%29CrownOfWarMahdi.w3x)
- **Tactical map preview:** `maps/(8)CrownOfWarMahdi_Preview.png`
- **Map lobby icon:** 1024px source at `src/assets/map_art/crown_map_icon.png`; the build embeds it as `war3mapPreview.tga` and serves an optimized 512px copy from `web/public/`. Four 1024px faction-emblem sources have optimized 256px web copies; the tactical map preview remains separate.
- **Web preview:** `python3 web/server.py` (port 8080); includes the interactive map, archive manifest, verification summary, and download route. Manifest counts are computed from the current archive/generated metadata and checked by the verifier.
- **Classic client QA:** see [`CLASSIC_CLIENT_QA.md`](CLASSIC_CLIENT_QA.md) for the pending 1.26a/1.27b smoke-test, AI, spell, and match-balance checklist.

Install into `Warcraft III/Maps/FrozenThrone/` for classic TFT 1.26a/1.27b clients.

## v9 AI controller correction

- **The custom-AI dispatch omission is corrected in source:** the matching imported custom-race melee-AI script is now passed to `StartMeleeAI` for each of the four empires. Static verification confirms the dispatch and packaged scripts; only a Classic-client match can confirm they execute as intended.
- **One intended macro controller per AI:** the custom scripts contain faction-specific worker harvesting, construction, tech, army production, expansion calls, creep/defense setup and assault/attack waves. The JASS build/train/march fallback has been removed, so it cannot cancel or compete with those orders. Classic Human, Orc, Undead, and Night Elf AIs still use their stock melee scripts.
- **JASS remains the tactical supplement:** visible-target/fair-vision scans, bounded custom-hero spell decisions, safe retreats, consumable use, and item pickup are retained. For custom factions, unit-level JASS orders are restricted to the AI heroes so ordinary soldiers stay under the melee commander.
- **Difficulty and diagnosis:** the host-selected Novice/Veteran/Grandmaster/Mythic setting continues to apply the disclosed custom-race income support (+0/+0, +1/+1, +2/+1, +3/+2 gold/lumber per four-second tick). Use `-aistats` to see which dispatch path was issued, plus army/workers, halls/tier, units currently on attack orders, resources, visible contacts, and hero-spell orders; a dispatch flag is not proof of runtime execution. The imported melee scripts also read the actual computer difficulty selected in the Warcraft lobby.
- **AI scripts and safety:** the four custom scripts have their own faction-specific build orders, worker/economy loops, tier progression, supply limits, expansion calls, hero leveling, and attack loops. They are packaged and statically type-checked against the Classic melee-AI API.
- **600-supply ceiling:** every player still receives the 600 ceiling; custom melee scripts continue building the appropriate supply structures.

The routing change is intended to make the standard melee-AI systems and the custom scripts’ creep/expansion/attack routines reachable without a competing JASS macro. Automated verification confirms packaging, dispatch, and source invariants; it does not prove in-match creeping, expansion, attacks, or balance. Classic 1.26a/1.27b in-client testing is still required, especially to measure those behaviors at each difficulty.

## Building models, hall progression, and command icons

- **Abyssal / Naga:** the empire halls now progress through three distinct custom version-800 MDXs (`nntt` / T1, `n001` / T2, `n002` / T3). Tidal Treasury (`n003`), Coral Forge (`n004`), and Abyssal Behemoth Pool (`n005`) each retain their own low-poly model and true-color texture. This is six unique building models across the hall chain and three role buildings.
- **Sunfury:** its halls follow the native Human Town Hall → Keep → Castle upgrade chain and model family, with Sunfury-specific scale/tint. Altar, Arcane Vault, Barracks, Workshop, Gryphon Aviary, Blacksmith, and Lumbermill remain aligned to role-matched native Human models. **Voidborn** uses its Undead Altar, Ziggurat tower, and Bone Yard models; **Runeforged** uses Orc Altar of Storms, Voodoo Lounge, and Watch Tower models.
- All **12 custom empire halls** have distinct faction- and tier-coded normal/disabled command-button pairs. These are visual identifiers only; gameplay costs, tech requirements, and the four custom race rules are unchanged by this art pass.
- Static checks resolve model assignments for the four custom-faction building sets against object data/native metadata and cross-check the classic Human, Orc, Undead, Night Elf, and Naga worker build lists. They reject duplicate models between distinct roles and require the three Naga hall tiers and three Naga role buildings to be unique.

## Visual art pass

- All **16 custom heroes** now have coordinated original portrait art with normal/disabled button pairs. The 64 skill icons were redrawn with more distinct silhouettes and spell motifs while retaining their existing ability identities and faction palettes.
- Added a dedicated crown-and-four-empires map emblem for the Classic lobby preview, plus separate Abyssal, Sunfury, Voidborn, and Runeforged crests on the web faction tabs. The tactical terrain preview remains a separate image.
- The central Crown Shrine receives a clearer, tighter-scaled marker; its surrounding shrine/moat dressing adds **57 decorative doodads** in a D4-symmetric layout, with varied tree scales. The Sunken-Astral terrain, HUD, competitive routes, pathing, creep camps, and gameplay rules remain intact.
- `maps/(8)CrownOfWarMahdi_Preview.png`, the hero-portrait sheet, the hall-tier sheet, and the four skill galleries are generated from the same source assets as the archive and web preview.

## Hero skills and spell visuals

- Preserves **16 heroes and 64 exclusive skills**. Core ranks remain learnable at levels 1/3/5; ultimates remain level-gated to 6. Existing selected signature skills, including Mana Burn, Phoenix, and Resurrection, are retained.
- Adds **64 separate skill-specific MDX effects and 64 true-color textures**, plus 64 individually illustrated 64×64 command-button icons with matching disabled-state twins. Each ability dispatches to its own model; the assets vary by geometric form (burst, bolt, shield, portal), proportions, rune pattern, and hero theme—not hue alone. Six faction-sigil models remain for other gameplay effects (**70 VFX MDX models**; 76 MDX files including the six Naga hall/role building models).
- Differentiates the ultimates' *play patterns*, not only their colors: Vashj's Tsunami moves through three damage/heal/push fronts; Akama's shadow dance is a tighter 300-AoE around the assassin; Mimiron's Omega Laser locks its cast-time aim, reveals all three 1040-unit lanes for 0.55 seconds, then hits those 144-wide lines sequentially. The laser markers are explicitly cleaned up after the sweep or if Mimiron dies.
- Timed summons now search for terrain- and occupancy-safe spawn points; pull/push displacement checks unit/building clearance and only moves to a nearby safe point, otherwise leaving the unit where it is. This avoids placing summons inside obstacles or shoving units through occupied cells.
- Palette-encoded BLP is restricted to command-button artwork: 16 hero-portrait pairs, 64 custom skill BTN/DISBTN pairs, and 12 hall-tier pairs (184 individual icons / 92 pairs). Skill VFX and building textures use true-color BLP.

## Melee fairness and objective pass

- **Exact neutral-object symmetry:** creep members and their item carriers now mirror with the terrain across all eight D4 transforms. Reflected camps preserve left/right member placement instead of silently shifting unique units or drops to the wrong side; diagonal camps use reflection-safe formations.
- **Creep economy audit:** the packed `.w3x` is checked against its 36 previewed camps, actual neutral unit rosters, reference unit levels, and exact drop codes/chances. The seven camp budgets remain 6, 13, 13, 12, 10, 21, and 23 levels; all 36 groups must match their stated tier and loot.
- **Lobby-aware Crown Shrine:** capture and gold rewards now follow Warcraft's actual lobby alliances, so 4v4, 2v2, and FFA no longer inherit an arbitrary player-slot split. An uncontested holder's active allies receive +3 gold per 2-second tick (only the captor in FFA); enemy presence stops the gold reward. The HUD shows the current controller, and the web description now matches the implemented reward/healing behavior.
- **Equal race-pick economy:** Random Custom no longer grants +50 starting gold, eliminating an exploitable bonus when players reopen the race picker during its allowed switch window.
- The verifier now has **18 static/binary stages**, including neutral-object D4 symmetry, camp rosters/loot/level budgets, shrine-alliance behavior, race-choice economy, the 600-supply ceiling, custom-AI dispatch/supply checks, bounded tactical scans, and AI vision safeguards. Stage 14 also decodes the browser download payload and confirms byte-for-byte equality with the final W3X, matching SHA/size metadata, QA record, and published map/faction/icon galleries. It still does not simulate a live Warcraft III match.

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
