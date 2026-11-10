# Classic TFT client QA checklist

**Status:** Pending in-client testing. The current automated verifier is static/binary and does not establish runtime behavior or match balance. Do not mark an item complete without testing the `.w3x` in the named classic client and recording the result.

## Test record

| Field | 1.26a run | 1.27b run |
|---|---|---|
| Client build / distribution | Pending | Pending |
| Date and tester | Pending | Pending |
| Map SHA-256 | `06d17bc8728c3bb20f6ed5d0b63296dff71cb7f2a960279449e2fedcda89654d` | `06d17bc8728c3bb20f6ed5d0b63296dff71cb7f2a960279449e2fedcda89654d` |
| Result / evidence link | Pending | Pending |

Use a fresh copy of `maps/(8)CrownOfWarMahdi.w3x` in the classic TFT maps folder (`Warcraft III/Maps/FrozenThrone/`) and test separately on each client version listed above.

## A. Load, lobby, and UI

- [ ] Map appears in the custom-game list and loads without a crash, script error, or missing-file/model warning.
- [ ] Classic lobby displays the new crown-and-four-empires map emblem from the embedded `war3mapPreview.tga`; the in-game minimap remains the tactical layout.
- [ ] Eight player slots and the intended teams/forces are available; lobby race and handicap selections work.
- [ ] Host-first AI difficulty selection appears once, followed by the empire/race menu; dismissing or changing the selection does not duplicate units or grant extra starting resources.
- [ ] Test all four custom empire choices and all four classic races. Confirm the selected faction, hall, worker, and starting resources agree.
- [ ] Custom command-card buttons, disabled states, all 16 hero portraits, 64 skill-icon pairs, 12 faction/tier hall-icon pairs, tooltips, hotkeys, and imported building/unit icons render correctly.
- [ ] Classic UI remains readable at normal game resolution and the map description/install instructions identify classic TFT only.

## B. Economy, tech, and AI

For every custom AI faction, first confirm the correct imported `common.ai` script starts (Naga, Sunfury, Voidborn, or Runeforged); the JASS timer must not issue duplicate worker/build/production/march orders. Test Classic-race AIs separately against the stock melee scripts.

For each custom empire (Abyssal Tideborn, Sunfury Imperium, Voidborn Legion, Runeforged Bastion):

- [ ] Workers can gather gold and lumber, return resources to the correct drop-off, and resume after construction.
- [ ] **600-food ceiling:** build supply structures until the displayed cap exceeds 500 (up to 600), for Classic and each custom empire; confirm the appropriate supply building raises capacity and unit production still stops cleanly at the current cap. Test the 100–500 upkeep display in the Resource tooltip.
- [ ] Build menus contain the expected structures without duplicate/overlapping button positions; construction completes on valid terrain.
- [ ] Hall upgrades, unit production, research, altar heroes, and hero skill-point spending work without orders replacing one another or workers becoming idle indefinitely. Confirm the AI reserves food after each accepted order and does not train a 5-food hero when fewer than 5 supply remains.
- [ ] Run each custom AI for at least 15 minutes: observe opening build order, uninterrupted gold/wood collection, supply, hero/army production, tech progression, and recovery after workers/buildings/units are lost. Check that the custom melee script remains in charge rather than orders being overwritten by the JASS timer.
- [ ] Fog fairness: withhold vision of an enemy army, then reveal and hide it; confirm native melee AI attacks only detected targets and JASS hero spell micro/telemetry uses currently visible contacts rather than hidden unit positions.
- [ ] Creeping and objectives: confirm the AI actually attacks suitable neutral camps, re-engages a later camp after a clear, responds to threats near its base, contests the central Shrine, and moves an army toward an opponent instead of idling. Record the first creep, Shrine contest, and enemy attack times.
- [ ] Fair vision and response: hide/reveal an enemy army, flyer, caster, and upgraded hall. Confirm the JASS spell micro and telemetry react only to visible targets; compare each melee script’s unit mix/tech without assuming the fixed opening composition changes instantly.
- [ ] Expansion: for each faction, verify the melee script sends a worker to a free natural mine, completes the hall, transfers workers to mine it, and does not repeatedly issue failed builds at an occupied/blocked site. Record first-expansion time and mine count.
- [ ] Native army control and hero micro: verify ordinary custom-race soldiers remain under the melee AI attack group; test a threatened hero's local pathable retreat (including flyers), spell use, and focus target. Repeat with a large army and note frame-rate/order churn.
- [ ] Hero spell evaluation: test clustered and spread enemies, high-mana targets, a wounded allied group, and a nearby dead hero; check the bounded AoE centers, per-hero order throttle, mana-drain selection, healing/ultimate gates, and spell-order telemetry.
- [ ] Test all four host difficulty choices and the Warcraft lobby AI difficulty separately. Confirm the selected custom-race income support is +0/+0, +1/+1, +2/+1, or +3/+2 gold/lumber per 4 seconds and that the imported melee script reads the lobby difficulty.
- [ ] Type `-aistats` at 2, 5, 10, and 15 minutes. Confirm the displayed script-dispatch status and compare army/workers/halls/tier, attack orders, resources, visible contacts, and hero-spell count with what is on screen; a dispatch flag is not proof of runtime execution, and counts are telemetry rather than match-win guarantees.
- [ ] Run the native Human, Orc, Undead, and Night Elf melee AI at least once each.

## C. Summon placement and displacement

Test the following in open terrain, near a crowded army, next to large structures, near the map edge, and on/near water where possible:

- [ ] Timed summons appear on a valid, unoccupied point; they do not overlap buildings or units. If no safe point is available, they are skipped rather than created inside an obstacle.
- [ ] Test the Naga Myrmidon and Snap Dragon summons on both land and water; confirm the conservative walkability check does not move them to an unintended location or suppress a valid aquatic summon.
- [ ] Test the Phoenix and Gyro summons; confirm flying pathing/collision behavior is appropriate.
- [ ] Pull/push spells do not move units through structures, off the playable area, or into impassable terrain. Confirm giants and structures remain immune as intended.
- [ ] Temporary summons expire on time and leave no lingering unit/effect.

## D. Revised ultimates and visual effects

- [ ] Vashj's Tsunami visibly advances through three ring fronts; each front's damage/healing/push matches its displayed area and does not repeatedly hit the whole disk.
- [ ] Akama's ultimate is centered on Akama and its 300-unit close-range area is clear and usable without hiding the fight.
- [ ] Mimiron's Omega Laser keeps the cast-time aim direction, reveals all three lanes for roughly 0.55 seconds, then damages the three 144-wide lanes sequentially.
- [ ] Confirm all 21 Mimiron telegraph effects are visible, cleaned up after the sweep, and cleaned up if Mimiron dies during the telegraph or sweep.
- [ ] Trigger several ultimates at once (including two Mimirons if possible); check for missing/reused effects, excess visual clutter, and a frame-rate spike.
- [ ] Inspect the Crown Shrine marker, eight-spoke courtyard, moat bubbles/lilies, and surrounding D4-symmetric decorations for overlap, waterline errors, or visual clutter.
- [ ] Upgrade the Naga hall through all three tiers and inspect the six unique Naga MDXs; inspect Sunfury's native Town Hall → Keep → Castle progression and custom tier icons.
- [ ] Inspect the remaining custom skills and faction-specific unit/building models for correct classic-client BLP/MDX rendering and orientation.

## E. Match and balance checks

- [ ] Play at least one 4v4, one 2v2, and one FFA match; include all four custom empires across the sample.
- [ ] Record hero levels, first expansion/tech timing, army composition, resource float, and whether any faction dominates through a repeatable rush or ultimate combo.
- [ ] Confirm mirrored starts, mines, creep camps, shops, shrine rewards, and lobby alliances behave as expected in live games.
- [ ] Repeat any apparent imbalance before changing values; distinguish execution/AI issues from a systematic faction advantage.

## Issue log

| Client / scenario | Expected | Observed | Repro steps / evidence | Follow-up |
|---|---|---|---|---|
| Pending | — | — | — | — |
