# `(8) Crown of WarMahdi` — v6 Warcraft III 8-Empire Altered Melee

A **192×192, 8-player** Sunken-Astral map for Warcraft III TFT and Reforged. The update responds to in-client screenshots supplied by the user while retaining the map’s existing terrain, theme and UI.

## Download and preview

- **Map (`.w3x`):** [Download Crown of WarMahdi v6](https://github.com/warmahdi651-stack/Warcraft/raw/arena/483b840a-warcraft/maps/%288%29CrownOfWarMahdi.w3x)
- **Tactical map preview:** `maps/(8)CrownOfWarMahdi_Preview.png`
- **Web preview:** `python3 web/server.py` (port 8080); includes interactive map, archive manifest, static-check summary and download route.

Install into `Warcraft III/Maps/FrozenThrone/` for classic clients or `Documents/Warcraft III/Maps/Download/` for Reforged.

## What changed in v6

- **Building appearance:** Altar of the Sunwell now uses the native Human Altar of Kings model, matching its faction and role. Custom Naga buildings retain verified native Naga building models and matching stock buttons; Sunfury hall tiers retain Warcraft’s native Town Hall tier model/animations.
- **Hero level progression:** the correct `arlv` required-level field now gates every ultimate until hero level 6. Core skills have three ranks at levels 1, 3 and 5 (`alsk=2`); ultimates have one rank and `arlv=6`. The verifier checks every one of the 64 ability objects.
- **Signature Warcraft skills restored:** Illidan’s W is Mana Burn (mana removed becomes equal spell damage); Kael’thas’s ultimate summons the native Phoenix unit; Uther’s Resurrection revives the nearest fallen allied hero and adds three radiant pulses.
- **Smarter tactical AI:** custom heroes focus the lowest-health nearby opponent; Illidan seeks a mana-bearing target for Mana Burn; Uther saves Resurrection for a nearby fallen allied hero. Existing retreat, item-use and faction-specific macro AI remain in place.
- **Build and assets:** preserves all eight playable races, sixteen hero kits, custom UI, terrain, portraits and six VFX models. Map preview/export assets are regenerated from the same build.

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

The v6 build passed **all 15 automated static/binary verification stages**, including MPQ/TFT v25 structure, JASS typechecks against 1.27b and Reforged 1.32.8 APIs, the 1.26-era compatibility proxy, all four race-AI scripts, object tables, native icon/model references, pathing, D4 symmetry and balance bounds.

**Testing limitation:** the agent did not run Warcraft III. The screenshots show the user launched the previous build in-client; the updated map still needs a fresh client smoke test on 1.26a/1.27b and Reforged, especially for level-up UI behavior, model rendering, resurrection and AI spell orders. Static verification is not a substitute for that playtest, and no bug-free claim is made.
