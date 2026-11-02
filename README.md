# `(8) Crown of WarMahdi` — 6-Race Warcraft III Altered Melee Map (`.w3x`)

A tournament-grade, 8-player D4-symmetric **6-Race Altered Melee** map (`192×192`, `4v4` / `2v2v2v2` / `FFA`) featuring **Naga Empire** and **Campaign Human (Silvermoon & Alliance Expedition)** alongside all 4 classic races, complete with **Pro-Level Custom Melee AI (`naga_melee.ai` & `camphuman_melee.ai`)**.

## Direct Download

- **Playable `.w3x` Map (`256,614` bytes):** [`maps/(8)CrownOfWarMahdi.w3x`](https://github.com/warmahdi651-stack/Warcraft/raw/arena/483b840a-warcraft/maps/%288%29CrownOfWarMahdi.w3x)
- **High-Resolution Tactical Preview (`1024×1024`):** `maps/(8)CrownOfWarMahdi_Preview.png`

## 6 Balanced Playable Races & Pro AI

1. **Naga Empire (`naga_melee.ai`)**
   - **3-Tier Town Halls:** Temple of Tides (`nntt`) ➔ Sanctuary of Tides (`n001`) ➔ Abyssal Citadel (`n002`)
   - **4 Heroes:** Lady Vashj (`Hvsh`), Abyssal Warlord (`N001`), Azshara's Tideweaver (`N002`), Makrura Deepking (`N003`)
   - **Units & Buildings:** Mur'gul Slave, Mur'gul Reaver, Naga Myrmidon, Snap Dragon, Naga Siren, Couatl, Dragon Turtle, Naga Royal Guard, Coral Bed, Altar of the Depths, Spawning Grounds, Shrine of Azshara, Tidal Treasury (`Orb of the Abyss`), Tidal Guardian Tower.
2. **Campaign Human — Silvermoon & Alliance Expedition (`camphuman_melee.ai`)**
   - **3-Tier Town Halls:** Silvermoon Town Hall (`h001`) ➔ Sunwell Keep (`h002`) ➔ Silvermoon Citadel (`h003`)
   - **4 Heroes:** Prince Kael'thas (`Hkal`), Sylvanas Windrunner (`Hvwd`), Lord Garithos (`Hlgr`), Uther the Lightbringer (`Huth`)
   - **Units & Buildings:** Silvermoon Engineer, High Elven Swordsman, High Elven Archer, Alliance Captain, Silvermoon Chaplain, Dalaran Hydromancer, Spell Breaker, Silvermoon Ballista, Dragonhawk Rider, Blood Elf Lieutenant, High Elven Farm, Altar of Silvermoon, High Elven Barracks, Arcane Observatory, Sunwell Reliquary (`Orb of Fire`), Sunspire Watch / Earth-Fury / Sky-Fury Towers.
3. **Classic 4 Ladder Races:** Human, Orc, Undead, Night Elf (100% unmodified ladder stats & AI).

## How to Select Naga & Campaign Human (Lobby + In-Game)

- **Method 1 — Directly in the Pre-Game Lobby (`Handicap` dropdown on any Human or Computer AI row):**
  - `90%` ➔ **Naga Empire** *(automatically restores HP back to `100%` at `0.00s`!)*
  - `80%` ➔ **Campaign Human** *(automatically restores HP back to `100%` at `0.00s`!)*
  - `70%` ➔ **Random (All 6 Balanced Races)** *(restores HP to `100%`!)*
- **Method 2 — Instant In-Game Clickable Menu (`t = 0.10s`):**
  - Pops up automatically for Human players left at `100%`, plus a 1-click **Computer AI Race Mode** menu (`6-Race Pro Mix`, `All AI Naga`, `All AI Campaign Human`, or `Keep Lobby AI`).
- **Method 3 — Chat Commands:** `-naga`, `-camphuman`, `-random6` (first 15s) and `-races` (anytime).

## Build & 12-Stage Verification

```bash
python3 src/build_map.py
python3 src/verify_map.py
```
