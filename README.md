# `(8) Crown of WarMahdi` — 6-Race Warcraft III Altered Melee Map (`.w3x`)

A tournament-grade, 8-player D4-symmetric **6-Race Altered Melee** map (`192×192`, `4v4` / `2v2v2v2` / `FFA`) featuring **Naga Empire** and **Campaign Human (Silvermoon & Alliance Expedition)** alongside all 4 classic races, complete with **Pro-Level Custom Melee AI (`naga_melee.ai` & `camphuman_melee.ai`)**.

## Direct Download

- **Playable `.w3x` Map (`258,792` bytes — Rebalanced v2):** [`maps/(8)CrownOfWarMahdi.w3x`](https://github.com/warmahdi651-stack/Warcraft/raw/arena/483b840a-warcraft/maps/%288%29CrownOfWarMahdi.w3x)
- **High-Resolution Tactical Preview (`1024×1024`):** `maps/(8)CrownOfWarMahdi_Preview.png`

## 6 Balanced Playable Races & Authentic Building Roles (v2)

1. **Naga Empire (`naga_melee.ai` — 9 Dedicated Structures)**
   - **Town Halls (Workers Only):** Temple of Tides (`nntt`) ➔ Sanctuary of Tides (`n001`) ➔ Abyssal Citadel (`n002`) — trains `nmpe` Mur'gul Slave.
   - **Coral Forge (`n004`):** Researches `+1/+2/+3` Coral/Chitinous/Razorspine Blades (`Rnat`) & Scales (`Rnam`).
   - **Spawning Grounds (`nnsg` — Barracks):** `nnmg` Mur'gul Reaver (T1), `nsnp` Snap Dragon (T1.5 Ranged), `nmyr` Naga Myrmidon (T2 Heavy Melee); researches Ensnare & Submerge.
   - **Shrine of Azshara (`nnsa` — Caster & Flyer Sanctum, T2):** `nnsw` Naga Siren & `nwgs` Couatl; researches Siren Training & Abolish Magic.
   - **Abyssal Behemoth Pool (`n005` — Siege & T3 Elite Sanctum, T2):** `nhyc` Dragon Turtle (T2 Siege) & `nnrg` Naga Royal Guard (T3 Champion).
   - **Altar, Shop & Defense:** Altar of the Depths (`Hvsh`, `N001`, `N002`, `N003`), Tidal Treasury (`Orb of the Abyss`), Coral Bed (`+9` Food), Tidal Guardian Tower.
2. **Campaign Human — Silvermoon & Alliance Expedition (`camphuman_melee.ai` — 11 Dedicated Structures)**
   - **Town Halls (Workers & Backpack):** Silvermoon Town Hall (`h001`) ➔ Sunwell Keep (`h002`) ➔ Silvermoon Citadel (`h003`) — trains `nhew` Silvermoon Worker.
   - **Silvermoon Barracks (`h007` — Infantry & Archers):** `hhes` High Elven Swordsman (T1), `nhea` High Elven Archer (T1), `hcth` Alliance Captain (T3 Plate Officer); researches Defend & Veteran War Training.
   - **High Elven Mage Tower (`nheb` — Spellcaster Sanctum, T2):** `nchp` Silvermoon Chaplain, `nhym` Dalaran Hydromancer, `hspt` Blood Elf Spell Breaker; researches Chaplain/Hydromancer Training & Control Magic.
   - **Silvermoon Siege Workshop (`h008` — Siege & T3 Champion, T2):** `hgyr` Flying Machine, `h006` Silvermoon Ballista (T2 Siege), `nbel` Blood Elf Lieutenant (T3 Champion); researches Bombs.
   - **Silvermoon Dragonhawk Aviary (`h009` — Aerial Units, T2):** `hdhw` Dragonhawk Rider (T2) & `hgry` Wildhammer Gryphon Rider (T3); researches Cloud & Storm Hammers.
   - **Altar, Forge, Shop & Towers:** Altar of Silvermoon (`Hkal`, `Hvwd`, `Hlgr`, `Huth`), Blacksmith, Lumber Mill, High Elven Farm (`+6` Food), Sunwell Reliquary (`Orb of Fire`), Sunspire Scout ➔ Guard / Arcane Towers.
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
