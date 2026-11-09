# Classic TFT client QA checklist

**Status:** Pending in-client testing. The current automated verifier is static/binary and does not establish runtime behavior or match balance. Do not mark an item complete without testing the `.w3x` in the named classic client and recording the result.

## Test record

| Field | 1.26a run | 1.27b run |
|---|---|---|
| Client build / distribution | Pending | Pending |
| Date and tester | Pending | Pending |
| Map SHA-256 | `7c6d038ba0522ff0a12472081cfbc95b5c7004c3ead00c49858090daafe5c8b7` | `7c6d038ba0522ff0a12472081cfbc95b5c7004c3ead00c49858090daafe5c8b7` |
| Result / evidence link | Pending | Pending |

Use a fresh copy of `maps/(8)CrownOfWarMahdi.w3x` in the classic TFT maps folder (`Warcraft III/Maps/FrozenThrone/`) and test separately on each client version listed above.

## A. Load, lobby, and UI

- [ ] Map appears in the custom-game list and loads without a crash, script error, or missing-file/model warning.
- [ ] Eight player slots and the intended teams/forces are available; lobby race and handicap selections work.
- [ ] Host-first AI difficulty selection appears once, followed by the empire/race menu; dismissing or changing the selection does not duplicate units or grant extra starting resources.
- [ ] Test all four custom empire choices and all four classic races. Confirm the selected faction, hall, worker, and starting resources agree.
- [ ] Custom command-card buttons, disabled states, hero portraits, tooltips, hotkeys, and imported building/unit icons render correctly.
- [ ] Classic UI remains readable at normal game resolution and the map description/install instructions identify classic TFT only.

## B. Economy, tech, and AI

For each custom empire (Abyssal Tideborn, Sunfury Imperium, Voidborn Legion, Runeforged Bastion):

- [ ] Workers can gather gold and lumber, return resources to the correct drop-off, and resume after construction.
- [ ] Build menus contain the expected structures without duplicate/overlapping button positions; construction completes on valid terrain.
- [ ] Hall upgrades, unit production, research, altar heroes, and hero skill-point spending work without orders replacing one another or workers becoming idle indefinitely.
- [ ] Run the custom AI long enough to observe its opening, tech progression, army production, and recovery after a blocked/failed build order.
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
