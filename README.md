# `(8) Crown of WarMahdi` — v4 8-Empire Warcraft III Altered Melee (`.w3x`)

A large **192×192, 8-player** Sunken-Astral Altered Melee map for Warcraft III TFT / Reforged, with 4 classic races plus four custom empires. v4 focuses on the issues from the latest playtest: hero kits no longer share the same four spells, custom races have their own worker/build/unit/building icons, Naga gains a balanced Illidan hero and a measured army buff, damage/armor infocards and the mouse cursor are reskinned, and a JASS worker-build fallback backs up the imported race AIs.

## Download

- **Map:** [`(8) Crown of WarMahdi.w3x` (2,128,366 bytes)](https://github.com/warmahdi651-stack/Warcraft/raw/arena/483b840a-warcraft/maps/%288%29CrownOfWarMahdi.w3x)
- **Tactical preview:** `maps/(8)CrownOfWarMahdi_Preview.png`
- **Web preview:** run `python3 web/server.py` and open the Arena preview on port 8080.

Install the map in `Warcraft III/Maps/FrozenThrone/` for classic clients or `Documents/Warcraft III/Maps/Download/` for Reforged.

## v4 roster and systems

### Eight playable empires

1. Human
2. Orc
3. Undead
4. Night Elf
5. **Abyssal Tideborn** — four Naga heroes: Lady Vashj, Illidan Stormrage, Naj'entus, and Athissa. The Naga frontline, ranged units, casters, flyers and siege unit received a measured stat pass.
6. **Sunfury Imperium** — four Highborne/Silvermoon heroes and faction-specific halls, a forge, lumber conservatory, buildings and unit portraits.
7. **Voidborn Legion** — four Void heroes, a race-themed worker and dimensional-rift building set.
8. **Runeforged Bastion** — four Titan/clockwork heroes, a race-themed worker and mechanical building/unit icon set.

Each faction's structures have distinct build-card positions. The 8 player starts remain D4-symmetric and have clear mirrored build zones.

### 16 heroes with 64 exclusive skills

The 16 custom heroes each have their own Q/W/E/R names, effects, icons and 3D visual theme. The MPQ contains 64 individual `BTN_WM_S00..S63` icons and matching disabled icons, plus six original `WM_FX_*.mdx` effects and supporting textures. Hero abilities are serialized into `war3map.w3a` as 64 `ANcl` abilities and handled by the JASS spell engine.

### UI, AI and map theme

- A host-first AI difficulty dialog, followed by the custom-empires picker; `[A]` chooses randomly from all eight races.
- Custom cursor atlases, RPG-style Damage/Armor/Strength/Agility/Intelligence infocards, action buttons, race build icons, and astral resource/tooltip textures.
- Four imported melee AI scripts plus JASS tactical macro/micro. The JASS fallback can issue actual construction orders for the four custom empires, and AI heroes can use carried healing/mana items, pick up nearby items, retreat, learn their own skill kits and attack.
- Sunken-Astral `Z` tiles, Ashenvale twilight lighting, Outland sky, the embedded lobby art, and the central Crown Shrine.

## Verification and build

```bash
python3 src/build_map.py
python3 src/verify_map.py
```

The current generated archive passed **15 automated static/binary verification stages**, including StormLib archive checks, TFT v25 structure checks, JASS2 static typechecks against 1.27b and Reforged 1.32.8 APIs plus a 1.24.4-era API compatibility proxy, AI-script typechecks, object/hero/rally-flag checks, 64-skill/icon checks, D4 symmetry, pathing, and ladder stat bounds.

These checks are not a substitute for launching Warcraft III. Please run a short LAN/local-client smoke test on the intended 1.26a/1.27b and Reforged clients—especially AI construction, cursor rendering, and hero spell targeting—and share any game log or screenshot if something behaves differently in a client.
