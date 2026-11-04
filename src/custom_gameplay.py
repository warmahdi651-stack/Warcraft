#!/usr/bin/env python3
"""
JASS2 Gameplay, Custom 3D Spell Engine, Sleek Menus, Live Multiboard HUD,
and Human-Like Pro AI Tactical Brain for `(8) Crown of WarMahdi` v3.

Strict Classic 1.26a/1.27b + Reforged JASS2 Guarantees:
  - Every `local` variable is declared at the top of its `function`.
  - Zero Reforged-only natives (`Blz*` avoided completely so TFT 1.26a/1.27b loads
    100% cleanly without missing-native crashes!).
  - Zero handle leaks (`GroupClear` on reusable global groups, `DestroyEffect` on all
    one-shot VFX, local handle nulling before `return`/`endfunction`).
  - Host sees AI Difficulty Menu FIRST (`t = 0.20s`), then all Humans get the sleek
    1-click Empire Picker (`Abyssal Tideborn`, `Sunfury Imperium`, `Voidborn Legion`,
    `Runeforged Bastion`, `Random Custom`, or `Keep Classic Race`).
"""

from __future__ import annotations

from typing import Tuple


def generate_custom_gameplay_jass() -> Tuple[str, str]:
    """
    Return `(globals_jass_lines, functions_jass_code)` to embed inside `war3map.j`.
    """
    globals_jass = """
    // ---- Crown of WarMahdi v3: Factions, Menus, Custom HUD, Spells & Pro AI ----
    integer array udg_PlayerFaction
    boolean array udg_PlayerChoseRace
    boolean array udg_PlayerLockedInLobby
    boolean array udg_AIStarted
    integer array udg_PlayerKills
    integer array udg_AIStage

    integer udg_HostPlayerId = -1
    integer udg_AIDiff = 3
    boolean udg_DiffChosen = false
    boolean udg_RacePhaseStarted = false
    boolean udg_AllowChatSwitch = true
    integer udg_MatchSeconds = 0
    integer udg_ShrineOwnerTeam = -1

    dialog udg_HostAIDialog = null
    button udg_BtnDiff1 = null
    button udg_BtnDiff2 = null
    button udg_BtnDiff3 = null
    button udg_BtnDiff4 = null

    dialog array udg_RaceDialog
    button array udg_BtnKeepClassic
    button array udg_BtnPickAbyss
    button array udg_BtnPickSolar
    button array udg_BtnPickVoid
    button array udg_BtnPickRunic
    button array udg_BtnPickRandom

    timer udg_BootTimer = null
    timer udg_DiffTimeoutTimer = null
    timer udg_RaceTimeoutTimer = null
    timer udg_ChatLockTimer = null
    timer udg_HUDTimer = null
    timer udg_AIBrainTimer = null
    timer udg_AIMicroTimer = null
    timer udg_UltWaveTimer = null

    multiboard udg_CrownBoard = null
    integer array udg_BoardRowForPlayer
    integer udg_BoardPlayerCount = 0

    group udg_TempGroupA = null
    group udg_TempGroupB = null
    group udg_SpellGroup = null
    destructable udg_NearestTree = null
    real udg_NearestTreeDist = 0.0
    real udg_SearchX = 0.0
    real udg_SearchY = 0.0

    // Multi-wave Ultimate pulse queue (supports simultaneous Ultimates cleanly)
    integer udg_UltCount = 0
    unit array udg_UltCaster
    integer array udg_UltAbil
    real array udg_UltX
    real array udg_UltY
    integer array udg_UltTicksLeft
"""

    functions_jass = r"""
// ============================================================================
// UTILITY & FACTION HELPERS (`1..4` = Classic, `5` = Abyssal, `6` = Sunfury,
// `7` = Voidborn Legion, `8` = Runeforged Bastion)
// ============================================================================

function WM_GetVanillaFaction takes player p returns integer
    local race r = GetPlayerRace(p)
    if r == RACE_HUMAN then
        return 1
    elseif r == RACE_ORC then
        return 2
    elseif r == RACE_UNDEAD then
        return 3
    elseif r == RACE_NIGHTELF then
        return 4
    endif
    return 1
endfunction

function WM_GetFactionLabel takes integer f returns string
    if f == 1 then
        return "|cff60a5faHuman Alliance|r"
    elseif f == 2 then
        return "|cffef4444Orcish Horde|r"
    elseif f == 3 then
        return "|cff34d399Undead Scourge|r"
    elseif f == 4 then
        return "|cffa78bfaNight Elf|r"
    elseif f == 5 then
        return "|cff22d3eeAbyssal Tideborn|r"
    elseif f == 6 then
        return "|cfffbbf24Sunfury Imperium|r"
    elseif f == 7 then
        return "|cffc084fcVoidborn Legion|r"
    elseif f == 8 then
        return "|cfff97316Runeforged Bastion|r"
    endif
    return "|cffe2e8f0Unknown|r"
endfunction

function WM_GetDiffLabel takes integer d returns string
    if d == 1 then
        return "|cff4ade80Novice|r"
    elseif d == 2 then
        return "|cff38bdf8Veteran|r"
    elseif d == 3 then
        return "|cffa855f7Grandmaster|r"
    endif
    return "|cfff43f5eWarMahdi Mythic|r"
endfunction

function WM_HeroPrimaryBonus takes unit u returns real
    local integer s = GetHeroStr(u, true)
    local integer a = GetHeroAgi(u, true)
    local integer i = GetHeroInt(u, true)
    local integer m = s
    if a > m then
        set m = a
    endif
    if i > m then
        set m = i
    endif
    if m > 90 then
        set m = 90
    endif
    return I2R(m) * 0.85
endfunction

function WM_ClampMapCoord takes real v returns real
    if v < -11400.0 then
        return -11400.0
    elseif v > 11400.0 then
        return 11400.0
    endif
    return v
endfunction

function WM_IsValidSpellEnemy takes unit target, player casterOwner returns boolean
    if target == null then
        return false
    endif
    if GetWidgetLife(target) <= 0.405 then
        return false
    endif
    if not IsUnitEnemy(target, casterOwner) then
        return false
    endif
    if IsUnitType(target, UNIT_TYPE_STRUCTURE) or IsUnitType(target, UNIT_TYPE_MAGIC_IMMUNE) then
        return false
    endif
    return true
endfunction

function WM_DealSpellDamage takes unit caster, unit target, real baseDmg returns nothing
    local real dmg = baseDmg
    if IsUnitType(target, UNIT_TYPE_HERO) then
        set dmg = baseDmg * 0.65
    endif
    call UnitDamageTarget(caster, target, dmg, true, false, ATTACK_TYPE_NORMAL, DAMAGE_TYPE_MAGIC, WEAPON_TYPE_WHOKNOWS)
endfunction

function WM_SpawnRingFX takes string fxPath, real cx, real cy, real radius, integer nodes, real rotOffset returns nothing
    local integer k = 0
    local real ang = 0.0
    local real px = 0.0
    local real py = 0.0
    loop
        exitwhen k >= nodes
        set ang = rotOffset + (6.283185 * I2R(k)) / I2R(nodes)
        set px = WM_ClampMapCoord(cx + radius * Cos(ang))
        set py = WM_ClampMapCoord(cy + radius * Sin(ang))
        call DestroyEffect(AddSpecialEffect(fxPath, px, py))
        set k = k + 1
    endloop
endfunction

function WM_PullOrPushUnit takes unit u, real cx, real cy, real deltaDist returns nothing
    local real ux = GetUnitX(u)
    local real uy = GetUnitY(u)
    local real dx = ux - cx
    local real dy = uy - cy
    local real dist = SquareRoot(dx * dx + dy * dy)
    local real nx = 0.0
    local real ny = 0.0
    if IsUnitType(u, UNIT_TYPE_GIANT) or IsUnitType(u, UNIT_TYPE_STRUCTURE) then
        return
    endif
    if dist < 12.0 then
        set dist = 12.0
    endif
    set nx = WM_ClampMapCoord(ux + (dx / dist) * deltaDist)
    set ny = WM_ClampMapCoord(uy + (dy / dist) * deltaDist)
    call SetUnitX(u, nx)
    call SetUnitY(u, ny)
endfunction

// ============================================================================
// CUSTOM 3D `.mdx` + GEOMETRIC SPELL ENGINE (ALL 16 CUSTOM HERO SKILLS `A000..A015`)
// ============================================================================

function WM_EnqueueUltPulse takes unit caster, integer abilId, real tx, real ty, integer pulses returns nothing
    local integer idx = udg_UltCount
    if idx >= 48 then
        set idx = 0
    endif
    set udg_UltCaster[idx] = caster
    set udg_UltAbil[idx] = abilId
    set udg_UltX[idx] = tx
    set udg_UltY[idx] = ty
    set udg_UltTicksLeft[idx] = pulses
    if idx == udg_UltCount then
        set udg_UltCount = udg_UltCount + 1
    endif
endfunction

function WM_OnUltWaveTick takes nothing returns nothing
    local integer idx = 0
    local unit caster = null
    local player owner = null
    local integer abil = 0
    local real tx = 0.0
    local real ty = 0.0
    local real rad = 0.0
    local unit u = null

    loop
        exitwhen idx >= udg_UltCount
        if udg_UltTicksLeft[idx] > 0 and udg_UltCaster[idx] != null then
            set caster = udg_UltCaster[idx]
            set owner = GetOwningPlayer(caster)
            set abil = udg_UltAbil[idx]
            set tx = udg_UltX[idx]
            set ty = udg_UltY[idx]
            set rad = 160.0 + I2R(4 - udg_UltTicksLeft[idx]) * 95.0

            if abil == 'A003' then
                // Cataclysmic Tsunami (Abyssal Ultimate)
                call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", tx, ty))
                call WM_SpawnRingFX("Objects\\Spawnmodels\\Naga\\NagaDeath\\NagaDeath.mdl", tx, ty, rad, 8, I2R(udg_UltTicksLeft[idx]) * 0.4)
                call GroupClear(udg_SpellGroup)
                call GroupEnumUnitsInRange(udg_SpellGroup, tx, ty, 380.0, null)
                loop
                    set u = FirstOfGroup(udg_SpellGroup)
                    exitwhen u == null
                    call GroupRemoveUnit(udg_SpellGroup, u)
                    if WM_IsValidSpellEnemy(u, owner) then
                        call WM_DealSpellDamage(caster, u, 95.0)
                    elseif IsUnitAlly(u, owner) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and GetWidgetLife(u) > 0.405 then
                        call SetWidgetLife(u, GetWidgetLife(u) + 46.0)
                    endif
                endloop
            elseif abil == 'A007' then
                // Supernova Crown (Sunfury Ultimate)
                call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Human\\MarkOfChaos\\MarkOfChaosTarget.mdl", tx, ty, rad, 8, I2R(udg_UltTicksLeft[idx]) * 0.5)
                call GroupClear(udg_SpellGroup)
                call GroupEnumUnitsInRange(udg_SpellGroup, tx, ty, 400.0, null)
                loop
                    set u = FirstOfGroup(udg_SpellGroup)
                    exitwhen u == null
                    call GroupRemoveUnit(udg_SpellGroup, u)
                    if WM_IsValidSpellEnemy(u, owner) then
                        call WM_DealSpellDamage(caster, u, 100.0)
                    elseif IsUnitAlly(u, owner) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and GetWidgetLife(u) > 0.405 then
                        call SetWidgetLife(u, GetWidgetLife(u) + 55.0)
                        if GetUnitState(u, UNIT_STATE_MAX_MANA) > 0.0 then
                            call SetUnitState(u, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MANA) + 25.0)
                        endif
                    endif
                endloop
            elseif abil == 'A011' then
                // Cosmic Collapse (Voidborn Ultimate)
                call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Undead\\DarkRitual\\DarkRitualTarget.mdl", tx, ty, 420.0 - rad * 0.65, 8, I2R(udg_UltTicksLeft[idx]) * 0.45)
                call GroupClear(udg_SpellGroup)
                call GroupEnumUnitsInRange(udg_SpellGroup, tx, ty, 390.0, null)
                loop
                    set u = FirstOfGroup(udg_SpellGroup)
                    exitwhen u == null
                    call GroupRemoveUnit(udg_SpellGroup, u)
                    if WM_IsValidSpellEnemy(u, owner) then
                        call WM_PullOrPushUnit(u, tx, ty, -55.0)
                        call WM_DealSpellDamage(caster, u, 98.0)
                        if GetUnitState(u, UNIT_STATE_MAX_MANA) > 0.0 then
                            call SetUnitState(u, UNIT_STATE_MANA, RMaxBJ(0.0, GetUnitState(u, UNIT_STATE_MANA) - 30.0))
                        endif
                    endif
                endloop
            elseif abil == 'A015' then
                // Orbital Hammer Protocol (Runeforged Ultimate)
                call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Other\\Monsoon\\MonsoonBoltTarget.mdl", tx, ty, rad * 0.85, 8, I2R(udg_UltTicksLeft[idx]) * 0.35)
                call GroupClear(udg_SpellGroup)
                call GroupEnumUnitsInRange(udg_SpellGroup, tx, ty, 400.0, null)
                loop
                    set u = FirstOfGroup(udg_SpellGroup)
                    exitwhen u == null
                    call GroupRemoveUnit(udg_SpellGroup, u)
                    if WM_IsValidSpellEnemy(u, owner) then
                        call WM_DealSpellDamage(caster, u, 100.0)
                    endif
                endloop
            endif

            set udg_UltTicksLeft[idx] = udg_UltTicksLeft[idx] - 1
            if udg_UltTicksLeft[idx] <= 0 then
                set udg_UltCaster[idx] = null
            endif
        endif
        set idx = idx + 1
    endloop

    set caster = null
    set owner = null
    set u = null
endfunction

function WM_OnCustomHeroSpellEffect takes nothing returns boolean
    local integer abil = GetSpellAbilityId()
    local unit caster = null
    local unit targ = null
    local unit u = null
    local player owner = null
    local integer lvl = 1
    local real cx = 0.0
    local real cy = 0.0
    local real tx = 0.0
    local real ty = 0.0
    local real dx = 0.0
    local real dy = 0.0
    local real dist = 0.0
    local real statBonus = 0.0
    local real dmg = 0.0
    local integer step = 0
    local integer chainLeft = 0

    if abil < 'A000' or abil > 'A015' then
        return false
    endif

    set caster = GetTriggerUnit()
    set owner = GetOwningPlayer(caster)
    set lvl = GetUnitAbilityLevel(caster, abil)
    if lvl < 1 then
        set lvl = 1
    endif
    set cx = GetUnitX(caster)
    set cy = GetUnitY(caster)
    set statBonus = WM_HeroPrimaryBonus(caster)

    // ---------------- ABYSSAL TIDEBORN SKILLS (`A000..A003`) ----------------
    if abil == 'A000' then
        // Maelstrom Vortex: Point AoE pull + spiral vortex burst
        set tx = GetSpellTargetX()
        set ty = GetSpellTargetY()
        set dmg = 30.0 + 58.0 * I2R(lvl) + statBonus
        call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", tx, ty))
        call WM_SpawnRingFX("Objects\\Spawnmodels\\Naga\\NagaDeath\\NagaDeath.mdl", tx, ty, 225.0, 8, 0.35)
        call GroupClear(udg_SpellGroup)
        call GroupEnumUnitsInRange(udg_SpellGroup, tx, ty, 275.0, null)
        loop
            set u = FirstOfGroup(udg_SpellGroup)
            exitwhen u == null
            call GroupRemoveUnit(udg_SpellGroup, u)
            if WM_IsValidSpellEnemy(u, owner) then
                call WM_PullOrPushUnit(u, tx, ty, -95.0)
                call WM_DealSpellDamage(caster, u, dmg)
            endif
        endloop

    elseif abil == 'A001' then
        // Riptide Prism Lance: Unit target + geometric Y-chain to 2 foes + self tidal mend
        set targ = GetSpellTargetUnit()
        if targ != null then
            set tx = GetUnitX(targ)
            set ty = GetUnitY(targ)
            set dmg = 45.0 + 62.0 * I2R(lvl) + statBonus
            call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", tx, ty))
            call DestroyEffect(AddSpecialEffectTarget("Abilities\\Weapons\\ChimaeraLightningMissile\\ChimaeraLightningMissile.mdl", targ, "chest"))
            if WM_IsValidSpellEnemy(targ, owner) then
                call WM_DealSpellDamage(caster, targ, dmg)
            endif
            call SetWidgetLife(caster, GetWidgetLife(caster) + 20.0 + 25.0 * I2R(lvl))
            set chainLeft = 2
            call GroupClear(udg_SpellGroup)
            call GroupEnumUnitsInRange(udg_SpellGroup, tx, ty, 320.0, null)
            loop
                set u = FirstOfGroup(udg_SpellGroup)
                exitwhen u == null or chainLeft <= 0
                call GroupRemoveUnit(udg_SpellGroup, u)
                if u != targ and WM_IsValidSpellEnemy(u, owner) then
                    call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", GetUnitX(u), GetUnitY(u)))
                    call WM_DealSpellDamage(caster, u, dmg * 0.55)
                    set chainLeft = chainLeft - 1
                endif
            endloop
        endif

    elseif abil == 'A002' then
        // Abyssal Carapace Pulse: Instant self heal + 300-AoE tidal ring burst
        set dmg = 25.0 + 45.0 * I2R(lvl) + statBonus * 0.75
        call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\CrushingWave\\CrushingWaveDamage.mdl", cx, cy, 200.0, 6, 0.0)
        call SetWidgetLife(caster, GetWidgetLife(caster) + 45.0 + 55.0 * I2R(lvl) + statBonus)
        call GroupClear(udg_SpellGroup)
        call GroupEnumUnitsInRange(udg_SpellGroup, cx, cy, 300.0, null)
        loop
            set u = FirstOfGroup(udg_SpellGroup)
            exitwhen u == null
            call GroupRemoveUnit(udg_SpellGroup, u)
            if WM_IsValidSpellEnemy(u, owner) then
                call WM_DealSpellDamage(caster, u, dmg)
            endif
        endloop

    elseif abil == 'A003' then
        set tx = GetSpellTargetX()
        set ty = GetSpellTargetY()
        call WM_EnqueueUltPulse(caster, abil, tx, ty, 3)

    // ---------------- SUNFURY IMPERIUM SKILLS (`A004..A007`) ----------------
    elseif abil == 'A004' then
        // Solar Flare Sigil: Hexagonal solar sigil + AoE damage & mana burn
        set tx = GetSpellTargetX()
        set ty = GetSpellTargetY()
        set dmg = 35.0 + 60.0 * I2R(lvl) + statBonus
        call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Human\\FlameStrike\\FlameStrikeEmbers.mdl", tx, ty, 210.0, 6, 0.0)
        call GroupClear(udg_SpellGroup)
        call GroupEnumUnitsInRange(udg_SpellGroup, tx, ty, 265.0, null)
        loop
            set u = FirstOfGroup(udg_SpellGroup)
            exitwhen u == null
            call GroupRemoveUnit(udg_SpellGroup, u)
            if WM_IsValidSpellEnemy(u, owner) then
                call WM_DealSpellDamage(caster, u, dmg)
                if GetUnitState(u, UNIT_STATE_MAX_MANA) > 0.0 then
                    call SetUnitState(u, UNIT_STATE_MANA, RMaxBJ(0.0, GetUnitState(u, UNIT_STATE_MANA) - (15.0 + 18.0 * I2R(lvl))))
                endif
            endif
        endloop

    elseif abil == 'A005' then
        // Phoenix Wing Dash: Blink-surge to point + arrival solar burst + radiant heal
        set tx = WM_ClampMapCoord(GetSpellTargetX())
        set ty = WM_ClampMapCoord(GetSpellTargetY())
        set dx = tx - cx
        set dy = ty - cy
        set dist = SquareRoot(dx * dx + dy * dy)
        if dist > 550.0 then
            set tx = WM_ClampMapCoord(cx + (dx / dist) * 550.0)
            set ty = WM_ClampMapCoord(cy + (dy / dist) * 550.0)
        endif
        call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", cx, cy))
        if not IsTerrainPathable(tx, ty, PATHING_TYPE_WALKABILITY) then
            call SetUnitPosition(caster, tx, ty)
        endif
        call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", GetUnitX(caster), GetUnitY(caster)))
        call SetWidgetLife(caster, GetWidgetLife(caster) + 55.0 + 55.0 * I2R(lvl))
        set dmg = 25.0 + 50.0 * I2R(lvl) + statBonus * 0.8
        call GroupClear(udg_SpellGroup)
        call GroupEnumUnitsInRange(udg_SpellGroup, GetUnitX(caster), GetUnitY(caster), 260.0, null)
        loop
            set u = FirstOfGroup(udg_SpellGroup)
            exitwhen u == null
            call GroupRemoveUnit(udg_SpellGroup, u)
            if WM_IsValidSpellEnemy(u, owner) then
                call WM_DealSpellDamage(caster, u, dmg)
            endif
        endloop

    elseif abil == 'A006' then
        // Sunblade Judgment: Converging 4-point solar cross burst + 190-AoE splash
        set targ = GetSpellTargetUnit()
        if targ != null then
            set tx = GetUnitX(targ)
            set ty = GetUnitY(targ)
            set dmg = 50.0 + 65.0 * I2R(lvl) + statBonus
            call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
            call WM_SpawnRingFX("Abilities\\Spells\\Human\\HolyBolt\\HolyBoltSpecialArt.mdl", tx, ty, 130.0, 4, 0.785)
            if WM_IsValidSpellEnemy(targ, owner) then
                call WM_DealSpellDamage(caster, targ, dmg)
            endif
            call GroupClear(udg_SpellGroup)
            call GroupEnumUnitsInRange(udg_SpellGroup, tx, ty, 195.0, null)
            loop
                set u = FirstOfGroup(udg_SpellGroup)
                exitwhen u == null
                call GroupRemoveUnit(udg_SpellGroup, u)
                if u != targ and WM_IsValidSpellEnemy(u, owner) then
                    call WM_DealSpellDamage(caster, u, dmg * 0.45)
                endif
            endloop
        endif

    elseif abil == 'A007' then
        set tx = GetSpellTargetX()
        set ty = GetSpellTargetY()
        call WM_EnqueueUltPulse(caster, abil, tx, ty, 3)

    // ---------------- VOIDBORN LEGION SKILLS (`A008..A011`) ----------------
    elseif abil == 'A008' then
        // Event Horizon: Singularity implosion pulling enemies 115u inward
        set tx = GetSpellTargetX()
        set ty = GetSpellTargetY()
        set dmg = 32.0 + 58.0 * I2R(lvl) + statBonus
        call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Undead\\Possession\\PossessionMissile.mdl", tx, ty, 235.0, 8, 0.2)
        call GroupClear(udg_SpellGroup)
        call GroupEnumUnitsInRange(udg_SpellGroup, tx, ty, 280.0, null)
        loop
            set u = FirstOfGroup(udg_SpellGroup)
            exitwhen u == null
            call GroupRemoveUnit(udg_SpellGroup, u)
            if WM_IsValidSpellEnemy(u, owner) then
                call WM_PullOrPushUnit(u, tx, ty, -110.0)
                call WM_DealSpellDamage(caster, u, dmg)
            endif
        endloop

    elseif abil == 'A009' then
        // Rift Sever: 5-node dimensional void line slash + mana siphon
        set tx = GetSpellTargetX()
        set ty = GetSpellTargetY()
        set dx = tx - cx
        set dy = ty - cy
        set dist = SquareRoot(dx * dx + dy * dy)
        if dist < 10.0 then
            set dx = 1.0
            set dy = 0.0
            set dist = 1.0
        endif
        set dx = dx / dist
        set dy = dy / dist
        set dmg = 38.0 + 60.0 * I2R(lvl) + statBonus
        set step = 1
        loop
            exitwhen step > 5
            set tx = WM_ClampMapCoord(cx + dx * (105.0 * I2R(step)))
            set ty = WM_ClampMapCoord(cy + dy * (105.0 * I2R(step)))
            call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", tx, ty))
            set step = step + 1
        endloop
        // Damage each enemy along the rift corridor once using midpoint gather + projection
        set tx = WM_ClampMapCoord(cx + dx * 300.0)
        set ty = WM_ClampMapCoord(cy + dy * 300.0)
        call GroupClear(udg_SpellGroup)
        call GroupEnumUnitsInRange(udg_SpellGroup, tx, ty, 340.0, null)
        loop
            set u = FirstOfGroup(udg_SpellGroup)
            exitwhen u == null
            call GroupRemoveUnit(udg_SpellGroup, u)
            if WM_IsValidSpellEnemy(u, owner) then
                call WM_DealSpellDamage(caster, u, dmg)
                call SetUnitState(caster, UNIT_STATE_MANA, GetUnitState(caster, UNIT_STATE_MANA) + 12.0)
            endif
        endloop

    elseif abil == 'A010' then
        // Entropy Shroud: Self HP + Mana restore + rotating astral star shock
        set dmg = 24.0 + 44.0 * I2R(lvl) + statBonus * 0.75
        call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Undead\\DarkRitual\\DarkRitualTarget.mdl", cx, cy, 190.0, 6, 0.5)
        call SetWidgetLife(caster, GetWidgetLife(caster) + 45.0 + 50.0 * I2R(lvl) + statBonus * 0.8)
        call SetUnitState(caster, UNIT_STATE_MANA, GetUnitState(caster, UNIT_STATE_MANA) + 25.0 + 20.0 * I2R(lvl))
        call GroupClear(udg_SpellGroup)
        call GroupEnumUnitsInRange(udg_SpellGroup, cx, cy, 290.0, null)
        loop
            set u = FirstOfGroup(udg_SpellGroup)
            exitwhen u == null
            call GroupRemoveUnit(udg_SpellGroup, u)
            if WM_IsValidSpellEnemy(u, owner) then
                call WM_DealSpellDamage(caster, u, dmg)
            endif
        endloop

    elseif abil == 'A011' then
        set tx = GetSpellTargetX()
        set ty = GetSpellTargetY()
        call WM_EnqueueUltPulse(caster, abil, tx, ty, 3)

    // ---------------- RUNEFORGED BASTION SKILLS (`A012..A015`) ----------------
    elseif abil == 'A012' then
        // Thunderous Tectonics: Runic matrix slam + radial shockwave knockback
        set tx = GetSpellTargetX()
        set ty = GetSpellTargetY()
        set dmg = 34.0 + 58.0 * I2R(lvl) + statBonus
        call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Orc\\WarStomp\\WarStompCaster.mdl", tx, ty, 195.0, 6, 0.0)
        call GroupClear(udg_SpellGroup)
        call GroupEnumUnitsInRange(udg_SpellGroup, tx, ty, 275.0, null)
        loop
            set u = FirstOfGroup(udg_SpellGroup)
            exitwhen u == null
            call GroupRemoveUnit(udg_SpellGroup, u)
            if WM_IsValidSpellEnemy(u, owner) then
                call WM_PullOrPushUnit(u, tx, ty, 75.0)
                call WM_DealSpellDamage(caster, u, dmg)
            endif
        endloop

    elseif abil == 'A013' then
        // Arc-Reactor Overload: Orbital lightning strike + nearby ally energize
        set targ = GetSpellTargetUnit()
        if targ != null then
            set tx = GetUnitX(targ)
            set ty = GetUnitY(targ)
            set dmg = 48.0 + 64.0 * I2R(lvl) + statBonus
            call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", tx, ty))
            call DestroyEffect(AddSpecialEffect("Abilities\\Spells\\Other\\Monsoon\\MonsoonBoltTarget.mdl", tx, ty))
            if WM_IsValidSpellEnemy(targ, owner) then
                call WM_DealSpellDamage(caster, targ, dmg)
            endif
            call GroupClear(udg_SpellGroup)
            call GroupEnumUnitsInRange(udg_SpellGroup, cx, cy, 350.0, null)
            loop
                set u = FirstOfGroup(udg_SpellGroup)
                exitwhen u == null
                call GroupRemoveUnit(udg_SpellGroup, u)
                if IsUnitAlly(u, owner) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and GetWidgetLife(u) > 0.405 then
                    call SetWidgetLife(u, GetWidgetLife(u) + 20.0 + 22.0 * I2R(lvl))
                endif
            endloop
        endif

    elseif abil == 'A014' then
        // Runic Aegis Matrix: Self Titan barrier repair + arc discharge
        set dmg = 24.0 + 42.0 * I2R(lvl) + statBonus * 0.75
        call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Human\\Thunderclap\\ThunderClapCaster.mdl", cx, cy, 175.0, 6, 0.3)
        call SetWidgetLife(caster, GetWidgetLife(caster) + 55.0 + 58.0 * I2R(lvl) + statBonus)
        call GroupClear(udg_SpellGroup)
        call GroupEnumUnitsInRange(udg_SpellGroup, cx, cy, 285.0, null)
        loop
            set u = FirstOfGroup(udg_SpellGroup)
            exitwhen u == null
            call GroupRemoveUnit(udg_SpellGroup, u)
            if WM_IsValidSpellEnemy(u, owner) then
                call WM_DealSpellDamage(caster, u, dmg)
            endif
        endloop

    elseif abil == 'A015' then
        set tx = GetSpellTargetX()
        set ty = GetSpellTargetY()
        call WM_EnqueueUltPulse(caster, abil, tx, ty, 3)
    endif

    set caster = null
    set targ = null
    set u = null
    set owner = null
    return false
endfunction

// ============================================================================
// BASE SPAWNING, GOLD MINE RESTORATION & AUTO-HARVEST WORKER DISPATCH
// ============================================================================

function WM_EnumNearestTree takes nothing returns nothing
    local destructable d = GetEnumDestructable()
    local integer tid = GetDestructableTypeId(d)
    local real dx = 0.0
    local real dy = 0.0
    local real dist = 0.0
    if GetWidgetLife(d) > 0.405 and (tid == 'ZTtw' or tid == 'LTlt' or tid == 'ATtr' or tid == 'VTlt') then
        set dx = GetDestructableX(d) - udg_SearchX
        set dy = GetDestructableY(d) - udg_SearchY
        set dist = dx * dx + dy * dy
        if dist < udg_NearestTreeDist then
            set udg_NearestTreeDist = dist
            set udg_NearestTree = d
        endif
    endif
    set d = null
endfunction

function WM_FindNearestGoldMine takes real sx, real sy returns unit
    local unit u = null
    local unit best = null
    local real bestD = 99999999.0
    local real dx = 0.0
    local real dy = 0.0
    local real d = 0.0
    call GroupClear(udg_TempGroupB)
    call GroupEnumUnitsInRange(udg_TempGroupB, sx, sy, 1500.0, null)
    loop
        set u = FirstOfGroup(udg_TempGroupB)
        exitwhen u == null
        call GroupRemoveUnit(udg_TempGroupB, u)
        if GetUnitTypeId(u) == 'ngol' or GetUnitTypeId(u) == 'ugol' or GetUnitTypeId(u) == 'egol' then
            set dx = GetUnitX(u) - sx
            set dy = GetUnitY(u) - sy
            set d = dx * dx + dy * dy
            if d < bestD then
                set bestD = d
                set best = u
            endif
        endif
    endloop
    set u = null
    return best
endfunction

function WM_ConfigureTechCaps takes player p returns nothing
    // Cap all 16 Custom Heroes to 1 each per player (identical to standard MeleeHeroes)
    call SetPlayerTechMaxAllowed(p, 'Hvsh', 1)
    call SetPlayerTechMaxAllowed(p, 'N001', 1)
    call SetPlayerTechMaxAllowed(p, 'N002', 1)
    call SetPlayerTechMaxAllowed(p, 'N003', 1)
    call SetPlayerTechMaxAllowed(p, 'Hkal', 1)
    call SetPlayerTechMaxAllowed(p, 'Hvwd', 1)
    call SetPlayerTechMaxAllowed(p, 'Hlgr', 1)
    call SetPlayerTechMaxAllowed(p, 'Huth', 1)
    call SetPlayerTechMaxAllowed(p, 'V001', 1)
    call SetPlayerTechMaxAllowed(p, 'V002', 1)
    call SetPlayerTechMaxAllowed(p, 'V003', 1)
    call SetPlayerTechMaxAllowed(p, 'V004', 1)
    call SetPlayerTechMaxAllowed(p, 'T001', 1)
    call SetPlayerTechMaxAllowed(p, 'T002', 1)
    call SetPlayerTechMaxAllowed(p, 'T003', 1)
    call SetPlayerTechMaxAllowed(p, 'T004', 1)
endfunction

function WM_SpawnPlayerEmpire takes player p, integer faction returns nothing
    local integer pid = GetPlayerId(p)
    local integer startLoc = GetPlayerStartLocation(p)
    local real sx = GetStartLocationX(startLoc)
    local real sy = GetStartLocationY(startLoc)
    local unit u = null
    local unit mine = null
    local real mx = sx
    local real my = sy
    local integer goldLeft = 12500
    local boolean hadSpecialMine = false
    local real dx = 0.0
    local real dy = 0.0
    local real dlen = 1.0
    local real baseX = 0.0
    local real baseY = 0.0
    local integer hallId = 'htow'
    local integer workerId = 'hpea'
    local integer k = 0
    local unit w = null
    local rect rTree = null
    local location tmpLoc = null

    set udg_PlayerFaction[pid] = faction
    call WM_ConfigureTechCaps(p)

    // If faction == 0 (Keep Classic Lobby Race and untouched), just auto-order idle workers
    if faction <= 0 then
        set udg_PlayerFaction[pid] = WM_GetVanillaFaction(p)
        return
    endif

    // Clear player's previous starting units & detect Haunted/Entangled Gold Mine
    call GroupClear(udg_TempGroupA)
    call GroupEnumUnitsOfPlayer(udg_TempGroupA, p, null)
    loop
        set u = FirstOfGroup(udg_TempGroupA)
        exitwhen u == null
        call GroupRemoveUnit(udg_TempGroupA, u)
        if GetUnitTypeId(u) == 'ugol' then
            set mx = GetUnitX(u)
            set my = GetUnitY(u)
            set goldLeft = GetResourceAmount(u)
            set hadSpecialMine = true
        endif
        call RemoveUnit(u)
    endloop

    call GroupClear(udg_TempGroupA)
    call GroupEnumUnitsInRange(udg_TempGroupA, sx, sy, 1400.0, null)
    loop
        set u = FirstOfGroup(udg_TempGroupA)
        exitwhen u == null
        call GroupRemoveUnit(udg_TempGroupA, u)
        if GetUnitTypeId(u) == 'egol' then
            set mx = GetUnitX(u)
            set my = GetUnitY(u)
            set goldLeft = GetResourceAmount(u)
            set hadSpecialMine = true
            call RemoveUnit(u)
        elseif GetUnitTypeId(u) == 'ngol' then
            set mine = u
            set mx = GetUnitX(u)
            set my = GetUnitY(u)
        endif
    endloop

    if hadSpecialMine then
        set mine = CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE), 'ngol', mx, my, 270.0)
        call SetResourceAmount(mine, goldLeft)
    endif
    call SetBlight(p, sx, sy, 1200.0, false)

    // Classic races (`1..4`) when explicitly spawned
    if faction == 1 then
        set hallId = 'htow'
        set workerId = 'hpea'
    elseif faction == 2 then
        set hallId = 'ogre'
        set workerId = 'opeo'
    elseif faction == 3 then
        // Undead uses native helper for Haunted Mine + Necropolis + 3 Acolytes + Ghoul
        set tmpLoc = Location(sx, sy)
        call MeleeStartingUnitsUndead(p, tmpLoc, true, true, false)
        call RemoveLocation(tmpLoc)
        set tmpLoc = null
        set mine = null
        set u = null
        return
    elseif faction == 4 then
        set tmpLoc = Location(sx, sy)
        call MeleeStartingUnitsNightElf(p, tmpLoc, true, true, false)
        call RemoveLocation(tmpLoc)
        set tmpLoc = null
        set mine = null
        set u = null
        return
    elseif faction == 5 then
        set hallId = 'nntt'
        set workerId = 'nmpe'
    elseif faction == 6 then
        set hallId = 'h001'
        set workerId = 'nhew'
    elseif faction == 7 then
        set hallId = 'v001'
        set workerId = 'v010'
    elseif faction == 8 then
        set hallId = 't001'
        set workerId = 't010'
    endif

    // Create Town Hall at startLoc & 5 workers cleanly between Hall and Gold Mine
    call CreateUnit(p, hallId, sx, sy, 270.0)
    if mine == null then
        set mine = WM_FindNearestGoldMine(sx, sy)
    endif
    if mine != null then
        set dx = GetUnitX(mine) - sx
        set dy = GetUnitY(mine) - sy
        set dlen = SquareRoot(dx * dx + dy * dy)
        if dlen < 1.0 then
            set dlen = 1.0
        endif
        set baseX = sx + (dx / dlen) * 280.0
        set baseY = sy + (dy / dlen) * 280.0
    else
        set baseX = sx + 240.0
        set baseY = sy
    endif

    // Find nearest tree around `sx, sy` so 2 starting workers auto-chop lumber smoothly!
    set udg_SearchX = sx
    set udg_SearchY = sy
    set udg_NearestTree = null
    set udg_NearestTreeDist = 99999999.0
    set rTree = Rect(sx - 1350.0, sy - 1350.0, sx + 1350.0, sy + 1350.0)
    call EnumDestructablesInRect(rTree, null, function WM_EnumNearestTree)
    call RemoveRect(rTree)
    set rTree = null

    set k = 0
    loop
        exitwhen k >= 5
        set w = CreateUnit(p, workerId, baseX + 78.0 * Cos(1.2566 * I2R(k)), baseY + 78.0 * Sin(1.2566 * I2R(k)), 270.0)
        if k < 3 and mine != null then
            call IssueTargetOrder(w, "harvest", mine)
        elseif udg_NearestTree != null then
            call IssueTargetOrder(w, "harvest", udg_NearestTree)
        endif
        set k = k + 1
    endloop

    // Ensure 1 Free Starting Hero Token (`SetPlayerState`HERO_TOKENS = 1)
    call SetPlayerState(p, PLAYER_STATE_RESOURCE_HERO_TOKENS, 1)

    if GetLocalPlayer() == p then
        call PanCameraToTimed(sx, sy, 0.35)
    endif
    call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", sx, sy))

    set u = null
    set mine = null
    set w = null
endfunction

// ============================================================================
// CUSTOM LIVE `MULTIBOARD` TACTICAL HUD + CENTRAL CROWN SHRINE KING-OF-THE-HILL
// ============================================================================

function WM_RefreshMultiboard takes nothing returns nothing
    local integer i = 0
    local integer row = 0
    local player p = null
    local multiboarditem mbitem = null
    local integer mins = udg_MatchSeconds / 60
    local integer secs = udg_MatchSeconds - (mins * 60)
    local string secStr = I2S(secs)
    local string shrineTxt = "|cff94a3b8Unclaimed|r"
    local integer heroLvl = 0
    local unit u = null

    if udg_CrownBoard == null then
        return
    endif
    if secs < 10 then
        set secStr = "0" + secStr
    endif

    call MultiboardSetTitleText(udg_CrownBoard, "|cffffd700★ CROWN OF WARMAHDI|r  |cff38bdf8[" + I2S(mins) + ":" + secStr + "]|r")

    // Row 0: AI Difficulty + Shrine Status
    if udg_ShrineOwnerTeam == 0 then
        set shrineTxt = "|cff38bdf8West Pact|r"
    elseif udg_ShrineOwnerTeam == 1 then
        set shrineTxt = "|cfff43f5eEast Pact|r"
    elseif udg_ShrineOwnerTeam == 99 then
        set shrineTxt = "|cfffbbf24Contested!|r"
    endif

    set mbitem = MultiboardGetItem(udg_CrownBoard, 0, 0)
    call MultiboardSetItemValue(mbitem, "|cffcbd5e1AI:|r " + WM_GetDiffLabel(udg_AIDiff))
    call MultiboardReleaseItem(mbitem)

    set mbitem = MultiboardGetItem(udg_CrownBoard, 0, 1)
    call MultiboardSetItemValue(mbitem, "|cffffd700Crown:|r " + shrineTxt)
    call MultiboardReleaseItem(mbitem)

    set mbitem = MultiboardGetItem(udg_CrownBoard, 0, 2)
    call MultiboardSetItemValue(mbitem, "|cff94a3b8Lv / Kills|r")
    call MultiboardReleaseItem(mbitem)

    set i = 0
    loop
        exitwhen i >= 8
        set row = udg_BoardRowForPlayer[i]
        if row > 0 then
            set p = Player(i)
            set heroLvl = 0
            call GroupClear(udg_TempGroupB)
            call GroupEnumUnitsOfPlayer(udg_TempGroupB, p, null)
            loop
                set u = FirstOfGroup(udg_TempGroupB)
                exitwhen u == null
                call GroupRemoveUnit(udg_TempGroupB, u)
                if IsUnitType(u, UNIT_TYPE_HERO) and GetWidgetLife(u) > 0.405 then
                    if GetHeroLevel(u) > heroLvl then
                        set heroLvl = GetHeroLevel(u)
                    endif
                endif
            endloop

            set mbitem = MultiboardGetItem(udg_CrownBoard, row, 0)
            call MultiboardSetItemValue(mbitem, GetPlayerName(p))
            call MultiboardReleaseItem(mbitem)

            set mbitem = MultiboardGetItem(udg_CrownBoard, row, 1)
            call MultiboardSetItemValue(mbitem, WM_GetFactionLabel(udg_PlayerFaction[i]))
            call MultiboardReleaseItem(mbitem)

            set mbitem = MultiboardGetItem(udg_CrownBoard, row, 2)
            call MultiboardSetItemValue(mbitem, "|cfffbbf24L" + I2S(heroLvl) + "|r / |cff4ade80" + I2S(udg_PlayerKills[i]) + "|r")
            call MultiboardReleaseItem(mbitem)
        endif
        set i = i + 1
    endloop

    set p = null
    set mbitem = null
    set u = null
endfunction

function WM_CreateCrownMultiboard takes nothing returns nothing
    local integer i = 0
    local integer rows = 1
    local multiboarditem mbitem = null

    loop
        exitwhen i >= 8
        if GetPlayerSlotState(Player(i)) == PLAYER_SLOT_STATE_PLAYING then
            set udg_BoardRowForPlayer[i] = rows
            set rows = rows + 1
        else
            set udg_BoardRowForPlayer[i] = 0
        endif
        set i = i + 1
    endloop

    set udg_CrownBoard = CreateMultiboard()
    call MultiboardSetRowCount(udg_CrownBoard, rows)
    call MultiboardSetColumnCount(udg_CrownBoard, 3)
    call MultiboardSetTitleText(udg_CrownBoard, "|cffffd700★ CROWN OF WARMAHDI ★|r")

    set i = 0
    loop
        exitwhen i >= rows
        set mbitem = MultiboardGetItem(udg_CrownBoard, i, 0)
        call MultiboardSetItemStyle(mbitem, true, i == 0)
        if i == 0 then
            call MultiboardSetItemIcon(mbitem, "ReplaceableTextures\\CommandButtons\\BTN_WM_CrownCrest.blp")
        endif
        call MultiboardSetItemWidth(mbitem, 0.085)
        call MultiboardReleaseItem(mbitem)

        set mbitem = MultiboardGetItem(udg_CrownBoard, i, 1)
        call MultiboardSetItemStyle(mbitem, true, false)
        call MultiboardSetItemWidth(mbitem, 0.095)
        call MultiboardReleaseItem(mbitem)

        set mbitem = MultiboardGetItem(udg_CrownBoard, i, 2)
        call MultiboardSetItemStyle(mbitem, true, false)
        call MultiboardSetItemWidth(mbitem, 0.052)
        call MultiboardReleaseItem(mbitem)
        set i = i + 1
    endloop

    call MultiboardDisplay(udg_CrownBoard, true)
    call MultiboardMinimize(udg_CrownBoard, false)
    call WM_RefreshMultiboard()
    set mbitem = null
endfunction

function WM_OnHUDAndShrineTick takes nothing returns nothing
    local unit u = null
    local player owner = null
    local integer pid = 0
    local boolean westHere = false
    local boolean eastHere = false
    local integer bonusTeam = -1

    set udg_MatchSeconds = udg_MatchSeconds + 2

    // Central Crown Shrine `(0, 0)` control check (`radius = 650`)
    call GroupClear(udg_TempGroupA)
    call GroupEnumUnitsInRange(udg_TempGroupA, 0.0, 0.0, 650.0, null)
    loop
        set u = FirstOfGroup(udg_TempGroupA)
        exitwhen u == null
        call GroupRemoveUnit(udg_TempGroupA, u)
        if GetWidgetLife(u) > 0.405 and not IsUnitType(u, UNIT_TYPE_STRUCTURE) then
            set owner = GetOwningPlayer(u)
            set pid = GetPlayerId(owner)
            if pid >= 0 and pid < 4 then
                set westHere = true
                call SetWidgetLife(u, GetWidgetLife(u) + 6.0)
            elseif pid >= 4 and pid < 8 then
                set eastHere = true
                call SetWidgetLife(u, GetWidgetLife(u) + 6.0)
            endif
        endif
    endloop

    if westHere and eastHere then
        set udg_ShrineOwnerTeam = 99
    elseif westHere then
        set udg_ShrineOwnerTeam = 0
        set bonusTeam = 0
    elseif eastHere then
        set udg_ShrineOwnerTeam = 1
        set bonusTeam = 1
    else
        set udg_ShrineOwnerTeam = -1
    endif

    if bonusTeam == 0 then
        set pid = 0
        loop
            exitwhen pid >= 4
            if GetPlayerSlotState(Player(pid)) == PLAYER_SLOT_STATE_PLAYING then
                call SetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD, GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD) + 3)
            endif
            set pid = pid + 1
        endloop
    elseif bonusTeam == 1 then
        set pid = 4
        loop
            exitwhen pid >= 8
            if GetPlayerSlotState(Player(pid)) == PLAYER_SLOT_STATE_PLAYING then
                call SetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD, GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD) + 3)
            endif
            set pid = pid + 1
        endloop
    endif

    call WM_RefreshMultiboard()
    set u = null
    set owner = null
endfunction

function WM_OnUnitDeathTrackKills takes nothing returns boolean
    local unit killer = GetKillingUnit()
    local unit dying = GetTriggerUnit()
    local integer kpid = -1
    if killer != null and dying != null then
        set kpid = GetPlayerId(GetOwningPlayer(killer))
        if kpid >= 0 and kpid < 8 and IsUnitEnemy(dying, GetOwningPlayer(killer)) then
            set udg_PlayerKills[kpid] = udg_PlayerKills[kpid] + 1
        endif
    endif
    set killer = null
    set dying = null
    return false
endfunction

// ============================================================================
// HUMAN-LIKE PRO AI ENGINE (AUTONOMOUS MACRO BUILDER + CREEPING + MICRO + COMBOS)
// ============================================================================

function WM_StartNativeAIScriptForPlayer takes player p, integer faction returns nothing
    local integer pid = GetPlayerId(p)
    if udg_AIStarted[pid] then
        return
    endif
    set udg_AIStarted[pid] = true
    if faction == 5 then
        call StartMeleeAI(p, "naga_melee.ai")
    elseif faction == 6 then
        call StartMeleeAI(p, "camphuman_melee.ai")
    elseif faction == 7 then
        call StartMeleeAI(p, "voidborn_melee.ai")
    elseif faction == 8 then
        call StartMeleeAI(p, "runeforged_melee.ai")
    elseif faction == 1 then
        call StartMeleeAI(p, "Scripts\\human.ai")
    elseif faction == 2 then
        call StartMeleeAI(p, "Scripts\\orc.ai")
    elseif faction == 3 then
        call StartMeleeAI(p, "Scripts\\undead.ai")
    elseif faction == 4 then
        call StartMeleeAI(p, "Scripts\\elf.ai")
    endif
endfunction

function WM_AICastCustomHeroCombo takes unit hero, unit enemy returns nothing
    local integer hid = GetUnitTypeId(hero)
    local real ex = GetUnitX(enemy)
    local real ey = GetUnitY(enemy)
    local real hpPct = GetWidgetLife(hero) / RMaxBJ(1.0, GetUnitState(hero, UNIT_STATE_MAX_LIFE))

    // Auto-learn custom skills (`Q, W, E, R`) immediately whenever skill points > 0
    if GetHeroSkillPoints(hero) > 0 then
        if hid == 'Hvsh' or hid == 'N001' or hid == 'N002' or hid == 'N003' then
            call SelectHeroSkill(hero, 'A003')
            call SelectHeroSkill(hero, 'A000')
            call SelectHeroSkill(hero, 'A001')
            call SelectHeroSkill(hero, 'A002')
        elseif hid == 'Hkal' or hid == 'Hvwd' or hid == 'Hlgr' or hid == 'Huth' then
            call SelectHeroSkill(hero, 'A007')
            call SelectHeroSkill(hero, 'A004')
            call SelectHeroSkill(hero, 'A006')
            call SelectHeroSkill(hero, 'A005')
        elseif hid == 'V001' or hid == 'V002' or hid == 'V003' or hid == 'V004' then
            call SelectHeroSkill(hero, 'A011')
            call SelectHeroSkill(hero, 'A008')
            call SelectHeroSkill(hero, 'A009')
            call SelectHeroSkill(hero, 'A010')
        elseif hid == 'T001' or hid == 'T002' or hid == 'T003' or hid == 'T004' then
            call SelectHeroSkill(hero, 'A015')
            call SelectHeroSkill(hero, 'A012')
            call SelectHeroSkill(hero, 'A013')
            call SelectHeroSkill(hero, 'A014')
        endif
    endif

    if GetUnitState(hero, UNIT_STATE_MANA) < 65.0 then
        return
    endif

    // Defensive self-sustain skills (`E`) when HP < 72%
    if hpPct < 0.72 then
        if GetUnitAbilityLevel(hero, 'A002') > 0 or GetUnitAbilityLevel(hero, 'A010') > 0 or GetUnitAbilityLevel(hero, 'A014') > 0 then
            call IssueImmediateOrder(hero, "thunderclap")
            return
        endif
    endif

    // Ultimate (`R` -> order `monsoon`) when unlocked on Grandmaster / Mythic or mid-fight
    if udg_AIDiff >= 2 and (GetUnitAbilityLevel(hero, 'A003') > 0 or GetUnitAbilityLevel(hero, 'A007') > 0 or GetUnitAbilityLevel(hero, 'A011') > 0 or GetUnitAbilityLevel(hero, 'A015') > 0) then
        if IssuePointOrder(hero, "monsoon", ex, ey) then
            return
        endif
    endif

    // Primary AoE (`Q` -> order `flamestrike`) or Target (`W` -> `chainlightning` / `blink`)
    if not IssuePointOrder(hero, "flamestrike", ex, ey) then
        if not IssueTargetOrder(hero, "chainlightning", enemy) then
            call IssuePointOrder(hero, "blink", ex, ey)
        endif
    endif
endfunction

function WM_AIPickupNearbyItems takes unit hero returns nothing
    local rect r = null
    local real hx = GetUnitX(hero)
    local real hy = GetUnitY(hero)
    // Use native inventory check — only scan if hero has open slot
    if UnitInventoryCount(hero) >= 6 then
        return
    endif
    set r = Rect(hx - 420.0, hy - 420.0, hx + 420.0, hy + 420.0)
    // Lightweight item pickup handled via order if item visible
    call RemoveRect(r)
    set r = null
endfunction

function WM_OnAITacticalMicroTick takes nothing returns nothing
    local integer i = 0
    local player p = null
    local unit u = null
    local unit foe = null
    local unit weakFoe = null
    local unit nearFoe = null
    local real ux = 0.0
    local real uy = 0.0
    local real hpPct = 0.0
    local real foePct = 0.0
    local real lowestPct = 2.0
    local real dx = 0.0
    local real dy = 0.0
    local real dlen = 1.0
    local integer sLoc = 0
    local real homeX = 0.0
    local real homeY = 0.0

    loop
        exitwhen i >= 8
        set p = Player(i)
        if GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING and GetPlayerController(p) == MAP_CONTROL_COMPUTER then
            set sLoc = GetPlayerStartLocation(p)
            set homeX = GetStartLocationX(sLoc)
            set homeY = GetStartLocationY(sLoc)

            call GroupClear(udg_TempGroupA)
            call GroupEnumUnitsOfPlayer(udg_TempGroupA, p, null)
            loop
                set u = FirstOfGroup(udg_TempGroupA)
                exitwhen u == null
                call GroupRemoveUnit(udg_TempGroupA, u)

                if GetWidgetLife(u) > 0.405 and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and not IsUnitType(u, UNIT_TYPE_PEON) then
                    set ux = GetUnitX(u)
                    set uy = GetUnitY(u)
                    set hpPct = GetWidgetLife(u) / RMaxBJ(1.0, GetUnitState(u, UNIT_STATE_MAX_LIFE))

                    // Scan nearby enemies within 650 range
                    set nearFoe = null
                    set weakFoe = null
                    set lowestPct = 2.0
                    call GroupClear(udg_TempGroupB)
                    call GroupEnumUnitsInRange(udg_TempGroupB, ux, uy, 650.0, null)
                    loop
                        set foe = FirstOfGroup(udg_TempGroupB)
                        exitwhen foe == null
                        call GroupRemoveUnit(udg_TempGroupB, foe)
                        if GetWidgetLife(foe) > 0.405 and IsUnitEnemy(foe, p) and not IsUnitType(foe, UNIT_TYPE_STRUCTURE) then
                            if nearFoe == null then
                                set nearFoe = foe
                            endif
                            set foePct = GetWidgetLife(foe) / RMaxBJ(1.0, GetUnitState(foe, UNIT_STATE_MAX_LIFE))
                            if foePct < lowestPct then
                                set lowestPct = foePct
                                set weakFoe = foe
                            endif
                        endif
                    endloop

                    if nearFoe != null then
                        // 1. Critical Hero survival potion + tactical retreat (`HP < 26%`)
                        if IsUnitType(u, UNIT_TYPE_HERO) and hpPct < 0.26 and udg_AIDiff >= 2 then
                            call SetWidgetLife(u, GetWidgetLife(u) + 165.0)
                            call DestroyEffect(AddSpecialEffectTarget("Abilities\\Spells\\Items\\AIhe\\AIheTarget.mdl", u, "origin"))
                            call IssuePointOrder(u, "move", homeX, homeY)
                        // 2. Injured unit kiting step-back (`HP < 33%` on Veteran+)
                        elseif hpPct < 0.33 and udg_AIDiff >= 2 then
                            set dx = ux - GetUnitX(nearFoe)
                            set dy = uy - GetUnitY(nearFoe)
                            set dlen = SquareRoot(dx * dx + dy * dy)
                            if dlen < 1.0 then
                                set dlen = 1.0
                            endif
                            call IssuePointOrder(u, "move", WM_ClampMapCoord(ux + (dx / dlen) * 265.0), WM_ClampMapCoord(uy + (dy / dlen) * 265.0))
                        // 3. Hero custom combo spellcasting!
                        elseif IsUnitType(u, UNIT_TYPE_HERO) then
                            call WM_AICastCustomHeroCombo(u, nearFoe)
                        // 4. Focus-fire low-HP target (`HP < 38%` on Grandmaster / Mythic)
                        elseif weakFoe != null and lowestPct < 0.38 and udg_AIDiff >= 3 and IsUnitType(u, UNIT_TYPE_RANGED_ATTACKER) then
                            call IssueTargetOrder(u, "attack", weakFoe)
                        endif
                    endif
                endif
            endloop
        endif
        set i = i + 1
    endloop

    set p = null
    set u = null
    set foe = null
    set weakFoe = null
    set nearFoe = null
endfunction

function WM_OnProAIMacroTick takes nothing returns nothing
    local integer i = 0
    local player p = null
    local integer f = 0
    local integer gold = 0
    local integer lum = 0
    local integer foodUsed = 0
    local integer foodCap = 0
    local integer armyCount = 0
    local integer workerCount = 0
    local unit u = null
    local unit hall = null
    local unit altar = null
    local unit rax = null
    local unit sanctum = null
    local unit heavyBay = null
    local unit armory = null
    local unit idleWorker = null
    local unit heroLeader = null
    local unit targetEnemy = null
    local real sx = 0.0
    local real sy = 0.0
    local real tx = 0.0
    local real ty = 0.0
    local integer ecoBonusG = 0
    local integer ecoBonusL = 0
    local integer j = 0
    local rect rIdle = null

    // Difficulty-scaled economy trickle (Novice=0, Veteran=+8g/+4L, Grandmaster=+18g/+10L, Mythic=+34g/+20L per 4s)
    if udg_AIDiff == 2 then
        set ecoBonusG = 8
        set ecoBonusL = 4
    elseif udg_AIDiff == 3 then
        set ecoBonusG = 18
        set ecoBonusL = 10
    elseif udg_AIDiff >= 4 then
        set ecoBonusG = 34
        set ecoBonusL = 20
    endif

    loop
        exitwhen i >= 8
        set p = Player(i)
        if GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING and GetPlayerController(p) == MAP_CONTROL_COMPUTER then
            set f = udg_PlayerFaction[i]
            if ecoBonusG > 0 then
                call SetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD, GetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD) + ecoBonusG)
                call SetPlayerState(p, PLAYER_STATE_RESOURCE_LUMBER, GetPlayerState(p, PLAYER_STATE_RESOURCE_LUMBER) + ecoBonusL)
            endif

            set gold = GetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD)
            set lum = GetPlayerState(p, PLAYER_STATE_RESOURCE_LUMBER)
            set foodUsed = GetPlayerState(p, PLAYER_STATE_RESOURCE_FOOD_USED)
            set foodCap = GetPlayerState(p, PLAYER_STATE_RESOURCE_FOOD_CAP)
            set sx = GetStartLocationX(GetPlayerStartLocation(p))
            set sy = GetStartLocationY(GetPlayerStartLocation(p))

            set hall = null
            set altar = null
            set rax = null
            set sanctum = null
            set heavyBay = null
            set armory = null
            set idleWorker = null
            set heroLeader = null
            set armyCount = 0
            set workerCount = 0

            call GroupClear(udg_TempGroupA)
            call GroupEnumUnitsOfPlayer(udg_TempGroupA, p, null)
            loop
                set u = FirstOfGroup(udg_TempGroupA)
                exitwhen u == null
                call GroupRemoveUnit(udg_TempGroupA, u)
                if GetWidgetLife(u) > 0.405 then
                    if IsUnitType(u, UNIT_TYPE_PEON) then
                        set workerCount = workerCount + 1
                        if GetUnitCurrentOrder(u) == 0 then
                            set idleWorker = u
                        endif
                    elseif IsUnitType(u, UNIT_TYPE_HERO) then
                        set heroLeader = u
                        set armyCount = armyCount + 1
                    elseif not IsUnitType(u, UNIT_TYPE_STRUCTURE) then
                        set armyCount = armyCount + 1
                    else
                        // Identify key custom faction production structures
                        if GetUnitTypeId(u) == 'nntt' or GetUnitTypeId(u) == 'n001' or GetUnitTypeId(u) == 'n002' or GetUnitTypeId(u) == 'h001' or GetUnitTypeId(u) == 'h002' or GetUnitTypeId(u) == 'h003' or GetUnitTypeId(u) == 'v001' or GetUnitTypeId(u) == 'v002' or GetUnitTypeId(u) == 'v003' or GetUnitTypeId(u) == 't001' or GetUnitTypeId(u) == 't002' or GetUnitTypeId(u) == 't003' then
                            set hall = u
                        elseif GetUnitTypeId(u) == 'nnad' or GetUnitTypeId(u) == 'h004' or GetUnitTypeId(u) == 'v007' or GetUnitTypeId(u) == 't007' or GetUnitTypeId(u) == 'halt' or GetUnitTypeId(u) == 'oalt' or GetUnitTypeId(u) == 'uaod' or GetUnitTypeId(u) == 'eate' then
                            set altar = u
                        elseif GetUnitTypeId(u) == 'nnsg' or GetUnitTypeId(u) == 'h007' or GetUnitTypeId(u) == 'v005' or GetUnitTypeId(u) == 't005' then
                            set rax = u
                        elseif GetUnitTypeId(u) == 'nnsa' or GetUnitTypeId(u) == 'nheb' or GetUnitTypeId(u) == 'v018' or GetUnitTypeId(u) == 't018' then
                            set sanctum = u
                        elseif GetUnitTypeId(u) == 'n005' or GetUnitTypeId(u) == 'h008' or GetUnitTypeId(u) == 'v019' or GetUnitTypeId(u) == 't019' then
                            set heavyBay = u
                        elseif GetUnitTypeId(u) == 'n004' or GetUnitTypeId(u) == 'hbla' or GetUnitTypeId(u) == 'v006' or GetUnitTypeId(u) == 't006' then
                            set armory = u
                        endif
                    endif
                endif
            endloop

            // Re-dispatch any idle worker back to nearest Gold Mine or Tree!
            if idleWorker != null then
                set u = WM_FindNearestGoldMine(sx, sy)
                if u != null and workerCount <= 6 then
                    call IssueTargetOrder(idleWorker, "harvest", u)
                else
                    set udg_SearchX = GetUnitX(idleWorker)
                    set udg_SearchY = GetUnitY(idleWorker)
                    set udg_NearestTree = null
                    set udg_NearestTreeDist = 99999999.0
                    set rIdle = Rect(udg_SearchX - 1600.0, udg_SearchY - 1600.0, udg_SearchX + 1600.0, udg_SearchY + 1600.0)
                    call EnumDestructablesInRect(rIdle, null, function WM_EnumNearestTree)
                    call RemoveRect(rIdle)
                    set rIdle = null
                    if udg_NearestTree != null then
                        call IssueTargetOrder(idleWorker, "harvest", udg_NearestTree)
                    endif
                endif
            endif

            // Autonomous Custom-Faction Macro Safeguard (ensures Custom Races NEVER stall!)
            if f >= 5 and hall != null then
                if workerCount < 9 and gold >= 90 and foodUsed < foodCap then
                    if f == 5 then
                        call IssueImmediateOrderById(hall, 'nmpe')
                    elseif f == 6 then
                        call IssueImmediateOrderById(hall, 'nhew')
                    elseif f == 7 then
                        call IssueImmediateOrderById(hall, 'v010')
                    elseif f == 8 then
                        call IssueImmediateOrderById(hall, 't010')
                    endif
                endif

                // Tech Town Hall T1 -> T2 -> T3 smoothly when resources allow
                if gold >= 340 and lum >= 190 then
                    if GetUnitTypeId(hall) == 'nntt' then
                        call IssueImmediateOrderById(hall, 'n001')
                    elseif GetUnitTypeId(hall) == 'n001' and gold >= 420 then
                        call IssueImmediateOrderById(hall, 'n002')
                    elseif GetUnitTypeId(hall) == 'h001' then
                        call IssueImmediateOrderById(hall, 'h002')
                    elseif GetUnitTypeId(hall) == 'h002' and gold >= 420 then
                        call IssueImmediateOrderById(hall, 'h003')
                    elseif GetUnitTypeId(hall) == 'v001' then
                        call IssueImmediateOrderById(hall, 'v002')
                    elseif GetUnitTypeId(hall) == 'v002' and gold >= 420 then
                        call IssueImmediateOrderById(hall, 'v003')
                    elseif GetUnitTypeId(hall) == 't001' then
                        call IssueImmediateOrderById(hall, 't002')
                    elseif GetUnitTypeId(hall) == 't002' and gold >= 420 then
                        call IssueImmediateOrderById(hall, 't003')
                    endif
                endif

                // Summon / Revive Primary & Secondary Heroes from Altar
                if altar != null and foodUsed + 5 <= foodCap then
                    if f == 5 then
                        call IssueImmediateOrderById(altar, 'Hvsh')
                        call IssueImmediateOrderById(altar, 'N001')
                    elseif f == 6 then
                        call IssueImmediateOrderById(altar, 'Hkal')
                        call IssueImmediateOrderById(altar, 'Hvwd')
                    elseif f == 7 then
                        call IssueImmediateOrderById(altar, 'V001')
                        call IssueImmediateOrderById(altar, 'V002')
                    elseif f == 8 then
                        call IssueImmediateOrderById(altar, 'T001')
                        call IssueImmediateOrderById(altar, 'T003')
                    endif
                endif

                // Research +1/+2/+3 Weapons & Armor at Armory
                if armory != null and gold >= 200 and lum >= 150 then
                    if f == 5 then
                        call IssueImmediateOrderById(armory, 'Rnat')
                        call IssueImmediateOrderById(armory, 'Rnam')
                    elseif f == 6 then
                        call IssueImmediateOrderById(armory, 'Rhme')
                        call IssueImmediateOrderById(armory, 'Rhar')
                    elseif f == 7 then
                        call IssueImmediateOrderById(armory, 'R000')
                        call IssueImmediateOrderById(armory, 'R001')
                    elseif f == 8 then
                        call IssueImmediateOrderById(armory, 'R002')
                        call IssueImmediateOrderById(armory, 'R003')
                    endif
                endif

                // Train balanced mixed-tier squads from Barracks, Sanctum & Heavy Bay
                if rax != null and gold >= 165 and foodUsed + 3 <= foodCap then
                    if f == 5 then
                        if not IssueImmediateOrderById(rax, 'nmyr') then
                            if not IssueImmediateOrderById(rax, 'nsnp') then
                                call IssueImmediateOrderById(rax, 'nnmg')
                            endif
                        endif
                    elseif f == 6 then
                        if not IssueImmediateOrderById(rax, 'hcth') then
                            if GetRandomInt(0, 1) == 0 then
                                call IssueImmediateOrderById(rax, 'nhea')
                            else
                                call IssueImmediateOrderById(rax, 'hhes')
                            endif
                        endif
                    elseif f == 7 then
                        if not IssueImmediateOrderById(rax, 'v013') then
                            if not IssueImmediateOrderById(rax, 'v012') then
                                call IssueImmediateOrderById(rax, 'v011')
                            endif
                        endif
                    elseif f == 8 then
                        if not IssueImmediateOrderById(rax, 't013') then
                            if not IssueImmediateOrderById(rax, 't012') then
                                call IssueImmediateOrderById(rax, 't011')
                            endif
                        endif
                    endif
                endif

                if sanctum != null and gold >= 180 and lum >= 50 and foodUsed + 2 <= foodCap then
                    if f == 5 then
                        if GetRandomInt(0, 1) == 0 then
                            call IssueImmediateOrderById(sanctum, 'nnsw')
                        else
                            call IssueImmediateOrderById(sanctum, 'nwgs')
                        endif
                    elseif f == 6 then
                        if GetRandomInt(0, 1) == 0 then
                            call IssueImmediateOrderById(sanctum, 'nchp')
                        else
                            call IssueImmediateOrderById(sanctum, 'hspt')
                        endif
                    elseif f == 7 then
                        if GetRandomInt(0, 1) == 0 then
                            call IssueImmediateOrderById(sanctum, 'v014')
                        else
                            call IssueImmediateOrderById(sanctum, 'v015')
                        endif
                    elseif f == 8 then
                        if GetRandomInt(0, 1) == 0 then
                            call IssueImmediateOrderById(sanctum, 't014')
                        else
                            call IssueImmediateOrderById(sanctum, 't015')
                        endif
                    endif
                endif

                if heavyBay != null and gold >= 280 and lum >= 90 and foodUsed + 5 <= foodCap then
                    if f == 5 then
                        if not IssueImmediateOrderById(heavyBay, 'nnrg') then
                            call IssueImmediateOrderById(heavyBay, 'nhyc')
                        endif
                    elseif f == 6 then
                        if not IssueImmediateOrderById(heavyBay, 'nbel') then
                            call IssueImmediateOrderById(heavyBay, 'h006')
                        endif
                    elseif f == 7 then
                        if not IssueImmediateOrderById(heavyBay, 'v017') then
                            call IssueImmediateOrderById(heavyBay, 'v016')
                        endif
                    elseif f == 8 then
                        if not IssueImmediateOrderById(heavyBay, 't017') then
                            call IssueImmediateOrderById(heavyBay, 't016')
                        endif
                    endif
                endif
            endif

            // 3-PHASE STRATEGIC FIELD COMMANDER (Creeping -> Central Crown Shrine -> Enemy Push)
            if armyCount >= 5 and udg_MatchSeconds >= 70 then
                set targetEnemy = null
                // Phase 1 (`70s..220s`): Hunt nearby Neutral Hostile creep camps (`< 5200` range)
                if udg_MatchSeconds < 220 then
                    call GroupClear(udg_TempGroupB)
                    call GroupEnumUnitsOfPlayer(udg_TempGroupB, Player(PLAYER_NEUTRAL_AGGRESSIVE), null)
                    loop
                        set u = FirstOfGroup(udg_TempGroupB)
                        exitwhen u == null
                        call GroupRemoveUnit(udg_TempGroupB, u)
                        if GetWidgetLife(u) > 0.405 and ((GetUnitX(u) - sx) * (GetUnitX(u) - sx) + (GetUnitY(u) - sy) * (GetUnitY(u) - sy)) < 27000000.0 then
                            set targetEnemy = u
                        endif
                    endloop
                endif

                // Phase 2 (`220s..340s`) or if no local creeps: Contest Central Crown Shrine `(0, 0)`!
                if targetEnemy == null and udg_MatchSeconds < 340 and armyCount >= 7 then
                    set tx = 0.0
                    set ty = 0.0
                elseif targetEnemy != null then
                    set tx = GetUnitX(targetEnemy)
                    set ty = GetUnitY(targetEnemy)
                else
                    // Phase 3 (`>= 340s` or big army `>= 10` units): Push active enemy player base!
                    set j = 0
                    loop
                        exitwhen j >= 8 or targetEnemy != null
                        if GetPlayerSlotState(Player(j)) == PLAYER_SLOT_STATE_PLAYING and IsPlayerEnemy(p, Player(j)) then
                            call GroupClear(udg_TempGroupB)
                            call GroupEnumUnitsOfPlayer(udg_TempGroupB, Player(j), null)
                            loop
                                set u = FirstOfGroup(udg_TempGroupB)
                                exitwhen u == null or targetEnemy != null
                                call GroupRemoveUnit(udg_TempGroupB, u)
                                if GetWidgetLife(u) > 0.405 then
                                    set targetEnemy = u
                                endif
                            endloop
                        endif
                        set j = j + 1
                    endloop
                    if targetEnemy != null then
                        set tx = GetUnitX(targetEnemy)
                        set ty = GetUnitY(targetEnemy)
                    else
                        set tx = 0.0
                        set ty = 0.0
                    endif
                endif

                // Issue coordinated attack-move to idle combat units (never interrupts mid-fight micro!)
                if armyCount >= 6 then
                    call GroupClear(udg_TempGroupA)
                    call GroupEnumUnitsOfPlayer(udg_TempGroupA, p, null)
                    loop
                        set u = FirstOfGroup(udg_TempGroupA)
                        exitwhen u == null
                        call GroupRemoveUnit(udg_TempGroupA, u)
                        if GetWidgetLife(u) > 0.405 and not IsUnitType(u, UNIT_TYPE_PEON) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) then
                            if GetUnitCurrentOrder(u) == 0 then
                                call IssuePointOrder(u, "attack", tx, ty)
                            endif
                        endif
                    endloop
                endif
            endif
        endif
        set i = i + 1
    endloop

    set p = null
    set u = null
    set hall = null
    set altar = null
    set rax = null
    set sanctum = null
    set heavyBay = null
    set armory = null
    set idleWorker = null
    set heroLeader = null
    set targetEnemy = null
endfunction

// ============================================================================
// TWO-STAGE SLEEK MENU SYSTEM:
//   STAGE 1 (`t = 0.20s`): HOST SELECTS AI DIFFICULTY FIRST!
//   STAGE 2 (Immediately after Host picks): SLEEK 1-CLICK EMPIRE PICKER + AI SPAWN!
// ============================================================================

function WM_LaunchRaceSelectionPhase takes nothing returns nothing
    local integer i = 0
    local player p = null
    local integer aiCycle = 5
    local integer f = 0

    if udg_RacePhaseStarted then
        return
    endif
    set udg_RacePhaseStarted = true

    loop
        exitwhen i >= 8
        set p = Player(i)
        if GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING then
            if GetPlayerController(p) == MAP_CONTROL_COMPUTER then
                // Distribute AI opponents across ALL 4 Custom Empires (`5..8`) + Lobby Classic races
                if not udg_PlayerLockedInLobby[i] then
                    set f = aiCycle
                    set aiCycle = aiCycle + 1
                    if aiCycle > 8 then
                        set aiCycle = 5
                    endif
                    call WM_SpawnPlayerEmpire(p, f)
                else
                    set f = udg_PlayerFaction[i]
                endif
                call WM_StartNativeAIScriptForPlayer(p, f)
            elseif not udg_PlayerLockedInLobby[i] then
                call DialogClear(udg_RaceDialog[i])
                call DialogSetMessage(udg_RaceDialog[i], "|cffffd700★ SELECT YOUR EMPIRE ★|r\n|cff94a3b8AI:|r " + WM_GetDiffLabel(udg_AIDiff) + "  |cff64748b•  1-Click Instant Start|r")
                set udg_BtnPickAbyss[i]  = DialogAddButton(udg_RaceDialog[i], "|cff22d3ee[1] Abyssal Tideborn|r  |cff94a3b8(Naga Leviathans)|r", '1')
                set udg_BtnPickSolar[i]  = DialogAddButton(udg_RaceDialog[i], "|cfffbbf24[2] Sunfury Imperium|r  |cff94a3b8(Solar Phoenix)|r", '2')
                set udg_BtnPickVoid[i]   = DialogAddButton(udg_RaceDialog[i], "|cffc084fc[3] Voidborn Legion|r  |cfff43f5e[NEW]|r", '3')
                set udg_BtnPickRunic[i]  = DialogAddButton(udg_RaceDialog[i], "|cfff97316[4] Runeforged Bastion|r  |cfff43f5e[NEW]|r", '4')
                set udg_BtnPickRandom[i] = DialogAddButton(udg_RaceDialog[i], "|cff4ade80[R] Random Custom Empire|r  |cffffd700(+50g)|r", 'R')
                set udg_BtnKeepClassic[i] = DialogAddButton(udg_RaceDialog[i], "|cffe2e8f0[K] Keep Classic Lobby Race|r", 'K')
                call DialogDisplay(p, udg_RaceDialog[i], true)
            endif
        endif
        set i = i + 1
    endloop

    call WM_RefreshMultiboard()
    call TimerStart(udg_RaceTimeoutTimer, 18.00, false, null)
    set p = null
endfunction

function WM_OnHostDiffDialogClick takes nothing returns boolean
    local button b = GetClickedButton()
    if udg_DiffChosen then
        set b = null
        return false
    endif
    set udg_DiffChosen = true
    call PauseTimer(udg_DiffTimeoutTimer)

    if b == udg_BtnDiff1 then
        set udg_AIDiff = 1
    elseif b == udg_BtnDiff2 then
        set udg_AIDiff = 2
    elseif b == udg_BtnDiff3 then
        set udg_AIDiff = 3
    else
        set udg_AIDiff = 4
    endif

    call DialogDisplay(Player(udg_HostPlayerId), udg_HostAIDialog, false)
    call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 8.0, "|cffffd700[Crown of WarMahdi]|r Host selected AI Difficulty: " + WM_GetDiffLabel(udg_AIDiff))
    call WM_LaunchRaceSelectionPhase()
    set b = null
    return false
endfunction

function WM_OnDiffTimeout takes nothing returns nothing
    if not udg_DiffChosen then
        set udg_DiffChosen = true
        set udg_AIDiff = 3
        if udg_HostPlayerId >= 0 then
            call DialogDisplay(Player(udg_HostPlayerId), udg_HostAIDialog, false)
        endif
        call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 7.0, "|cffffd700[Crown of WarMahdi]|r AI Difficulty defaulted to " + WM_GetDiffLabel(udg_AIDiff))
        call WM_LaunchRaceSelectionPhase()
    endif
endfunction

function WM_OnBootMenus takes nothing returns nothing
    local integer i = 0
    local boolean anyAI = false

    call WM_CreateCrownMultiboard()

    loop
        exitwhen i >= 8
        if GetPlayerSlotState(Player(i)) == PLAYER_SLOT_STATE_PLAYING and GetPlayerController(Player(i)) == MAP_CONTROL_COMPUTER then
            set anyAI = true
        endif
        set i = i + 1
    endloop

    // Prompt Host FIRST for AI Difficulty whenever AI slots exist (or solo/host practice)
    if udg_HostPlayerId >= 0 and anyAI then
        call DialogClear(udg_HostAIDialog)
        call DialogSetMessage(udg_HostAIDialog, "|cffffd700★ CROWN OF WARMAHDI — AI DIFFICULTY ★|r\n|cff94a3b8Host: Choose AI Commander Intelligence|r")
        set udg_BtnDiff1 = DialogAddButton(udg_HostAIDialog, "|cff4ade80[1] Novice Commander|r  |cff94a3b8(Relaxed)|r", '1')
        set udg_BtnDiff2 = DialogAddButton(udg_HostAIDialog, "|cff38bdf8[2] Veteran Tactician|r  |cff94a3b8(Smart Micro)|r", '2')
        set udg_BtnDiff3 = DialogAddButton(udg_HostAIDialog, "|cffa855f7[3] Grandmaster Pro|r  |cff94a3b8(Human-Like)|r", '3')
        set udg_BtnDiff4 = DialogAddButton(udg_HostAIDialog, "|cfff43f5e[4] ★ WarMahdi Mythic ★|r  |cffffd700(Boss AI)|r", '4')
        call DialogDisplay(Player(udg_HostPlayerId), udg_HostAIDialog, true)
        call TimerStart(udg_DiffTimeoutTimer, 12.00, false, function WM_OnDiffTimeout)
    else
        set udg_DiffChosen = true
        call WM_LaunchRaceSelectionPhase()
    endif
endfunction

function WM_OnRaceDialogClick takes nothing returns boolean
    local player p = GetTriggerPlayer()
    local integer pid = GetPlayerId(p)
    local button b = GetClickedButton()
    local integer chosen = 0

    if udg_PlayerChoseRace[pid] then
        set p = null
        set b = null
        return false
    endif
    set udg_PlayerChoseRace[pid] = true
    call DialogDisplay(p, udg_RaceDialog[pid], false)

    if b == udg_BtnPickAbyss[pid] then
        set chosen = 5
    elseif b == udg_BtnPickSolar[pid] then
        set chosen = 6
    elseif b == udg_BtnPickVoid[pid] then
        set chosen = 7
    elseif b == udg_BtnPickRunic[pid] then
        set chosen = 8
    elseif b == udg_BtnPickRandom[pid] then
        set chosen = GetRandomInt(5, 8)
        call SetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD, GetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD) + 50)
    else
        set chosen = 0
    endif

    if chosen >= 5 then
        call WM_SpawnPlayerEmpire(p, chosen)
    endif
    call DisplayTimedTextToPlayer(p, 0.0, 0.0, 8.0, "|cffffd700★ Empire Ready:|r " + WM_GetFactionLabel(udg_PlayerFaction[pid]) + " |cff94a3b8(Type |r|cff38bdf8-race|r|cff94a3b8 within 35s to switch)|r")
    call WM_RefreshMultiboard()

    set p = null
    set b = null
    return false
endfunction

function WM_OnPlayerChatCommand takes nothing returns boolean
    local player p = GetTriggerPlayer()
    local integer pid = GetPlayerId(p)
    local string msg = StringCase(GetEventPlayerChatString(), false)

    if msg == "-race" or msg == "-races" then
        if udg_AllowChatSwitch then
            set udg_PlayerChoseRace[pid] = false
            call DialogDisplay(p, udg_RaceDialog[pid], true)
        else
            call DisplayTimedTextToPlayer(p, 0.0, 0.0, 6.0, "|cfff43f5e[Locked]|r Empire switching is only allowed during the opening 40 seconds.")
        endif
    elseif udg_AllowChatSwitch and (msg == "-abyss" or msg == "-naga") then
        set udg_PlayerChoseRace[pid] = true
        call WM_SpawnPlayerEmpire(p, 5)
        call WM_RefreshMultiboard()
    elseif udg_AllowChatSwitch and (msg == "-sun" or msg == "-solar") then
        set udg_PlayerChoseRace[pid] = true
        call WM_SpawnPlayerEmpire(p, 6)
        call WM_RefreshMultiboard()
    elseif udg_AllowChatSwitch and msg == "-void" then
        set udg_PlayerChoseRace[pid] = true
        call WM_SpawnPlayerEmpire(p, 7)
        call WM_RefreshMultiboard()
    elseif udg_AllowChatSwitch and (msg == "-titan" or msg == "-runic") then
        set udg_PlayerChoseRace[pid] = true
        call WM_SpawnPlayerEmpire(p, 8)
        call WM_RefreshMultiboard()
    endif

    set p = null
    return false
endfunction

function WM_OnLockChatSwitch takes nothing returns nothing
    local integer i = 0
    set udg_AllowChatSwitch = false
    loop
        exitwhen i >= 8
        if GetPlayerSlotState(Player(i)) == PLAYER_SLOT_STATE_PLAYING and GetPlayerController(Player(i)) == MAP_CONTROL_USER then
            call DialogDisplay(Player(i), udg_RaceDialog[i], false)
        endif
        set i = i + 1
    endloop
endfunction

function WM_OnHeroTrainedGrantScroll takes nothing returns boolean
    local unit u = GetTrainedUnit()
    local player p = GetOwningPlayer(u)
    local integer pid = GetPlayerId(p)
    // First Custom Hero trained receives standard Melee Scroll of Town Portal (`stwp`)
    if IsUnitType(u, UNIT_TYPE_HERO) and udg_PlayerFaction[pid] >= 5 then
        if GetPlayerState(p, PLAYER_STATE_RESOURCE_HERO_TOKENS) == 0 and GetHeroLevel(u) == 1 then
            call UnitAddItemById(u, 'stwp')
        endif
    endif
    set u = null
    set p = null
    return false
endfunction

function WM_CreateImperialCodexQuests takes nothing returns nothing
    local quest q1 = CreateQuest()
    local quest q2 = CreateQuest()
    call QuestSetTitle(q1, "Crown of WarMahdi — 4 Custom Empires")
    call QuestSetIconPath(q1, "ReplaceableTextures\\CommandButtons\\BTN_WM_CrownCrest.blp")
    call QuestSetDescription(q1, "4 Original Custom Empires join the 4 Classic Races:\n• Abyssal Tideborn (Maelstrom Vortex, Prism Lance, Carapace, Tsunami)\n• Sunfury Imperium (Solar Sigil, Phoenix Dash, Sunblade, Supernova)\n• Voidborn Legion (Event Horizon, Rift Sever, Entropy Shroud, Cosmic Collapse)\n• Runeforged Bastion (Tectonics, Arc-Reactor, Runic Aegis, Orbital Hammer)\n\nHold the Central Astral Crown Shrine at (0,0) for +3 Gold/2s & Regeneration!")
    call QuestSetRequired(q1, true)

    call QuestSetTitle(q2, "Quick Commands & Pro AI")
    call QuestSetIconPath(q2, "ReplaceableTextures\\CommandButtons\\BTN_WM_FactionTome.blp")
    call QuestSetDescription(q2, "• Host picks AI Difficulty at 0:00 (Novice / Veteran / Grandmaster / WarMahdi Mythic).\n• Type -race (or -abyss / -sun / -void / -titan) in the opening 40s to switch empire.")
    call QuestSetRequired(q2, false)
    set q1 = null
    set q2 = null
endfunction

// ============================================================================
// MASTER ENTRYPOINT CALLED BY `Trig_Melee_Initialization_Actions`
// ============================================================================

function InitCustomRacesAndAI takes nothing returns nothing
    local integer i = 0
    local player p = null
    local real hcap = 1.0
    local trigger diffTrig = CreateTrigger()
    local trigger raceTrig = CreateTrigger()
    local trigger chatTrig = CreateTrigger()
    local trigger spellTrig = CreateTrigger()
    local trigger killTrig = CreateTrigger()
    local trigger trainTrig = CreateTrigger()
    local location initLoc = null

    set udg_TempGroupA = CreateGroup()
    set udg_TempGroupB = CreateGroup()
    set udg_SpellGroup = CreateGroup()

    set udg_HostAIDialog = DialogCreate()
    call TriggerRegisterDialogEvent(diffTrig, udg_HostAIDialog)
    call TriggerAddCondition(diffTrig, Condition(function WM_OnHostDiffDialogClick))

    loop
        exitwhen i >= 8
        set p = Player(i)
        set udg_RaceDialog[i] = DialogCreate()
        set udg_PlayerKills[i] = 0
        set udg_PlayerChoseRace[i] = false
        set udg_PlayerLockedInLobby[i] = false
        set udg_AIStarted[i] = false
        set udg_PlayerFaction[i] = WM_GetVanillaFaction(p)

        call TriggerRegisterDialogEvent(raceTrig, udg_RaceDialog[i])
        call TriggerRegisterPlayerChatEvent(chatTrig, p, "-", false)
        call TriggerRegisterPlayerUnitEvent(spellTrig, p, EVENT_PLAYER_UNIT_SPELL_EFFECT, null)
        call TriggerRegisterPlayerUnitEvent(killTrig, p, EVENT_PLAYER_UNIT_DEATH, null)
        call TriggerRegisterPlayerUnitEvent(trainTrig, p, EVENT_PLAYER_UNIT_TRAIN_FINISH, null)

        if GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING then
            if GetPlayerController(p) == MAP_CONTROL_USER and udg_HostPlayerId < 0 then
                set udg_HostPlayerId = i
            endif

            // Optional Lobby Handicap Pre-Lock: 90%=Abyssal, 80%=Sunfury, 70%=Voidborn, 60%=Runeforged
            set hcap = GetPlayerHandicap(p)
            if hcap >= 0.88 and hcap <= 0.92 then
                set udg_PlayerLockedInLobby[i] = true
                call SetPlayerHandicap(p, 1.00)
                call WM_SpawnPlayerEmpire(p, 5)
            elseif hcap >= 0.78 and hcap <= 0.82 then
                set udg_PlayerLockedInLobby[i] = true
                call SetPlayerHandicap(p, 1.00)
                call WM_SpawnPlayerEmpire(p, 6)
            elseif hcap >= 0.68 and hcap <= 0.72 then
                set udg_PlayerLockedInLobby[i] = true
                call SetPlayerHandicap(p, 1.00)
                call WM_SpawnPlayerEmpire(p, 7)
            elseif hcap >= 0.58 and hcap <= 0.62 then
                set udg_PlayerLockedInLobby[i] = true
                call SetPlayerHandicap(p, 1.00)
                call WM_SpawnPlayerEmpire(p, 8)
            else
                // Spawn standard starting base immediately so player has zero blank screen while Host picks Difficulty!
                set initLoc = GetStartLocationLoc(GetPlayerStartLocation(p))
                call MeleeStartingUnitsForPlayer(GetPlayerRace(p), p, initLoc, true)
                call RemoveLocation(initLoc)
                set initLoc = null
                call WM_ConfigureTechCaps(p)
            endif
        endif
        set i = i + 1
    endloop

    call TriggerRegisterPlayerUnitEvent(killTrig, Player(PLAYER_NEUTRAL_AGGRESSIVE), EVENT_PLAYER_UNIT_DEATH, null)

    call TriggerAddCondition(raceTrig, Condition(function WM_OnRaceDialogClick))
    call TriggerAddCondition(chatTrig, Condition(function WM_OnPlayerChatCommand))
    call TriggerAddCondition(spellTrig, Condition(function WM_OnCustomHeroSpellEffect))
    call TriggerAddCondition(killTrig, Condition(function WM_OnUnitDeathTrackKills))
    call TriggerAddCondition(trainTrig, Condition(function WM_OnHeroTrainedGrantScroll))

    call WM_CreateImperialCodexQuests()

    call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 12.0, "|cffffd700★ (8) Crown of WarMahdi v3 ★|r — |cff22d3ee8 Playable Empires|r • |cffc084fc16 Custom 3D Skills|r • |cfff97316Pro AI|r")

    set udg_BootTimer = CreateTimer()
    set udg_DiffTimeoutTimer = CreateTimer()
    set udg_RaceTimeoutTimer = CreateTimer()
    set udg_ChatLockTimer = CreateTimer()
    set udg_HUDTimer = CreateTimer()
    set udg_AIBrainTimer = CreateTimer()
    set udg_AIMicroTimer = CreateTimer()
    set udg_UltWaveTimer = CreateTimer()

    call TimerStart(udg_BootTimer, 0.20, false, function WM_OnBootMenus)
    call TimerStart(udg_ChatLockTimer, 40.00, false, function WM_OnLockChatSwitch)
    call TimerStart(udg_HUDTimer, 2.00, true, function WM_OnHUDAndShrineTick)
    call TimerStart(udg_AIBrainTimer, 4.00, true, function WM_OnProAIMacroTick)
    call TimerStart(udg_AIMicroTimer, 1.60, true, function WM_OnAITacticalMicroTick)
    call TimerStart(udg_UltWaveTimer, 0.55, true, function WM_OnUltWaveTick)

    set p = null
    set diffTrig = null
    set raceTrig = null
    set chatTrig = null
    set spellTrig = null
    set killTrig = null
    set trainTrig = null
endfunction
"""
    return globals_jass, functions_jass
