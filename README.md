# `(8) Crown of WarMahdi` — v5 Warcraft III 8-Empire Altered Melee

A **192×192, 8-player** Sunken-Astral map for Warcraft III TFT and Reforged. It preserves the existing terrain, theme and in-game UI while addressing playtest feedback on repetitive/buggy hero skills, mismatched art and custom-race AI—especially Naga.

## Download and preview

- **Map (`.w3x`, 1,087,822 bytes):** [Download from GitHub](https://github.com/warmahdi651-stack/Warcraft/raw/arena/483b840a-warcraft/maps/%288%29CrownOfWarMahdi.w3x)
- **Tactical map preview:** `maps/(8)CrownOfWarMahdi_Preview.png`
- **Web preview:** run `python3 web/server.py` and open the preview on port 8080. The page includes the archive manifest, static-check summary and download route.

Install into `Warcraft III/Maps/FrozenThrone/` for classic clients or `Documents/Warcraft III/Maps/Download/` for Reforged.

## What changed in v5

- **Eight playable races:** Human, Orc, Undead, Night Elf, Abyssal Tideborn (Naga), Sunfury Imperium, Voidborn Legion and Runeforged Bastion.
- **Hero skills:** all 64 custom abilities have unique, effect-matched native Warcraft III command-button art. The skill art is referenced from the game rather than repackaged as procedurally drawn icons. Ability logic/tooltips were retuned; notable fixes include a mana-drain/transfer skill, a point-targeted Earthshaker strike, a corrected inward pull and primary-stat/level scaling for ultimate pulses.
- **Recognizable portraits and object art:** ten custom heroes have portrait BTN/DISBTN pairs; the other six retain recognizable stock portraits. Native stock buttons are selected for the altered units/buildings. Naga building rawcodes were cross-referenced against the 1.27.1 campaign unit function data and `unitui.slk`; custom Naga structures use native Naga models. Sunfury hall tiers retain the native Human Town Hall model and tier animations.
- **AI:** Naga research requests are guarded against repeated queueing; hero spell orders fall through to other available skills when an order fails. The four custom race AIs retain their faction-specific production and hero skill tables, backed by the JASS construction/item-use safeguards.
- **Assets and UI:** the archive contains 97 MPQ entries, 66 BLP1 files and six MDX VFX models. The 20 paletted BLP1s are limited to the ten custom portrait icon pairs; UI, cursor and effect textures use four-channel JPEG BLP1 encoding.

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

The current build passed **all 15 automated static/binary verification stages**, including MPQ/TFT v25 structure, JASS typechecks against 1.27b and Reforged 1.32.8 APIs, a 1.26-era compatibility proxy, all four race-AI scripts, object tables, icon/model references, portrait BLP encoding, pathing, D4 symmetry and balance bounds.

**Testing limitation:** no Warcraft III client was available here, so this is not an in-game playtest and “bug-free” cannot be guaranteed. A short LAN/local-client smoke test on 1.26a/1.27b and Reforged is still recommended—especially for model/portrait rendering, cursor/UI appearance, AI construction and spell targeting.
