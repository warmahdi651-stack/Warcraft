#!/usr/bin/env python3
"""
JASS2 Gameplay, Custom 3D Spell Engine, Sleek Menus, Live Multiboard HUD,
and Human-Like Pro AI Tactical Brain for `(8) Crown of WarMahdi` v8.

Classic TFT 1.26a/1.27b JASS2 compatibility targets:
  - Every `local` variable is declared at the top of its `function`.
  - Uses classic JASS2 natives only; no `Blz*` natives are required.
  - Zero handle leaks (`GroupClear` on reusable global groups, `DestroyEffect` on all
    one-shot VFX, local handle nulling before `return`/`endfunction`).
  - Host sees AI Difficulty Menu FIRST (`t = 0.20s`), then all Humans get the sleek
    1-click Empire Picker (`Abyssal Tideborn`, `Sunfury Imperium`, `Voidborn Legion`,
    `Runeforged Bastion`, `Random Custom`, or `Keep Classic Race`).
"""

from __future__ import annotations

from typing import Tuple

from src.spell_engine_v4 import SPELL_ENGINE_V4


def generate_custom_gameplay_jass() -> Tuple[str, str]:
    """
    Return `(globals_jass_lines, functions_jass_code)` to embed inside `war3map.j`.
    """
    globals_jass = """
    // ---- Crown of WarMahdi v8: 8 Empires, 16 Exclusive Heroes, 64 Skills, Dark UI & Pro AI ----
    integer array udg_PlayerFaction
    boolean array udg_PlayerChoseRace
    boolean array udg_PlayerLockedInLobby
    boolean array udg_AIStarted
    integer array udg_PlayerKills
    integer array udg_AIStage

    // Fair-vision intelligence: slots are aiPlayerId * 8 + enemyPlayerId.
    real array udg_AILastSeenX
    real array udg_AILastSeenY
    integer array udg_AILastSeenAt
    integer array udg_AIEnemyAirSeen
    integer array udg_AIEnemyAirSeenAt
    integer array udg_AIEnemyCasterSeen
    integer array udg_AIEnemyCasterSeenAt
    integer array udg_AIEnemyRangedSeen
    integer array udg_AIEnemyRangedSeenAt
    integer array udg_AIEnemyTierSeen
    real array udg_AIObjectiveX
    real array udg_AIObjectiveY
    integer array udg_AIVisibleEnemyCount
    integer array udg_AIEnemyAirCount
    integer array udg_AIEnemyCasterCount
    integer array udg_AIEnemyRangedCount
    integer array udg_AIEnemyTierCount
    integer array udg_AIObjectiveMode
    integer array udg_AILastMarchObjectiveMode
    integer array udg_AILastMarchObjectiveAt
    real array udg_AILastMarchObjectiveX
    real array udg_AILastMarchObjectiveY

    // Compact live telemetry, exposed to players with `-aistats`.
    integer array udg_AIMetricVisibleContacts
    integer array udg_AIMetricObjectiveOrders
    integer array udg_AIMetricDefenseOrders
    integer array udg_AIMetricRetreatOrders
    integer array udg_AIMetricFocusOrders
    integer array udg_AIMetricSpellOrders
    integer array udg_AIMetricCounterOrders
    integer array udg_AIMetricExpansionOrders

    // A second town hall is built only at a currently visible, unclaimed natural.
    boolean array udg_AIExpansionPending
    boolean array udg_AIExpansionActive
    real array udg_AIExpansionX
    real array udg_AIExpansionY
    integer array udg_AIExpansionOrderAt
    integer array udg_AINextExpansionTryAt

    // One construction order per custom AI at a time; construct-finish clears the latch.
    integer array udg_AIFallbackPendingRaw
    integer array udg_AIFallbackPendingUntil
    integer array udg_AINextWorkerOrderAt
    integer array udg_AINextHallOrderAt
    integer array udg_AINextHeroOrderAt
    integer array udg_AINextRaxOrderAt
    integer array udg_AINextSanctumOrderAt
    integer array udg_AINextHeavyOrderAt
    integer array udg_AINextAirOrderAt
    integer array udg_AINextUpgradeOrderAt

    integer udg_HostPlayerId = -1
    integer udg_AIDiff = 3
    boolean udg_DiffChosen = false
    boolean udg_RacePhaseStarted = false
    boolean udg_AllowChatSwitch = true
    integer udg_MatchSeconds = 0
    integer udg_ShrineControllerPid = -1

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
    button array udg_BtnPickRandomAll

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
    real udg_AISpellAimX = 0.0
    real udg_AISpellAimY = 0.0
    real udg_SafePointX = 0.0
    real udg_SafePointY = 0.0
    unit udg_ItemPickupHero = null
    item udg_ItemPickupCandidate = null
    real udg_ItemPickupDistance = 99999999.0

    // Multi-wave Ultimate pulse queue (supports simultaneous Ultimates cleanly)
    integer udg_UltCount = 0
    unit array udg_UltCaster
    integer array udg_UltAbil
    real array udg_UltX
    real array udg_UltY
    real array udg_UltBaseAngle
    effect array udg_UltLaserFX
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

function WM_IsCustomAIWorker takes integer faction, integer rawcode returns boolean
    // Custom worker rawcodes are explicit because several campaign-derived workers
    // do not inherit UNIT_TYPE_PEON reliably in every supported Warcraft version.
    if faction == 5 and rawcode == 'nmpe' then
        return true
    elseif faction == 6 and rawcode == 'nhew' then
        return true
    elseif faction == 7 and rawcode == 'v010' then
        return true
    elseif faction == 8 and rawcode == 't010' then
        return true
    endif
    return false
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

function WM_GetDiffSupportLabel takes integer d returns string
    if d == 1 then
        return "|cff94a3b8no income bonus|r"
    elseif d == 2 then
        return "|cff94a3b8+2g/+1l per 4s|r"
    elseif d == 3 then
        return "|cff94a3b8+4g/+2l per 4s|r"
    endif
    return "|cff94a3b8+7g/+3l per 4s|r"
endfunction

function WM_HeroPrimaryBonus takes unit u returns real
    local integer heroId = GetUnitTypeId(u)
    local integer stat = 0

    // Use the hero's declared primary attribute, not whichever attribute happens
    // to be highest after items/levels. This keeps INT, AGI and STR kits coherent.
    if heroId == 'Hvsh' or heroId == 'N002' or heroId == 'Hkal' or heroId == 'V002' or heroId == 'V004' or heroId == 'T004' then
        set stat = GetHeroInt(u, true)
    elseif heroId == 'N004' or heroId == 'Hvwd' or heroId == 'V003' or heroId == 'T003' then
        set stat = GetHeroAgi(u, true)
    elseif heroId == 'N001' or heroId == 'Hlgr' or heroId == 'Huth' or heroId == 'V001' or heroId == 'T001' or heroId == 'T002' then
        set stat = GetHeroStr(u, true)
    else
        set stat = GetHeroStr(u, true)
        if GetHeroAgi(u, true) > stat then
            set stat = GetHeroAgi(u, true)
        endif
        if GetHeroInt(u, true) > stat then
            set stat = GetHeroInt(u, true)
        endif
    endif

    if stat > 90 then
        set stat = 90
    endif
    return I2R(stat) * 0.85
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

function WM_IsSafeUnitPoint takes unit moving, real px, real py, real clearance, pathingtype terrainPath, boolean flying returns boolean
    local unit other = null
    local real dx = 0.0
    local real dy = 0.0
    local real distSq = 0.0
    local real minDist = 0.0
    local real searchRadius = 0.0
    if IsTerrainPathable(px, py, terrainPath) then
        set moving = null
        return false
    endif
    set searchRadius = clearance + 192.0
    call GroupClear(udg_TempGroupB)
    call GroupEnumUnitsInRange(udg_TempGroupB, px, py, searchRadius, null)
    loop
        set other = FirstOfGroup(udg_TempGroupB)
        exitwhen other == null
        call GroupRemoveUnit(udg_TempGroupB, other)
        if other != moving and GetUnitTypeId(other) != 0 and GetWidgetLife(other) > 0.405 then
            if (not flying and not IsUnitType(other, UNIT_TYPE_FLYING)) or (flying and IsUnitType(other, UNIT_TYPE_FLYING)) then
                set minDist = clearance
                if not flying and IsUnitType(other, UNIT_TYPE_STRUCTURE) then
                    // Conservative 176u building radius for classic structure footprints.
                    set minDist = clearance + 176.0
                elseif IsUnitType(other, UNIT_TYPE_GIANT) then
                    set minDist = clearance + 48.0
                endif
                set dx = GetUnitX(other) - px
                set dy = GetUnitY(other) - py
                set distSq = dx * dx + dy * dy
                if distSq < minDist * minDist then
                    set other = null
                    set moving = null
                    return false
                endif
            endif
        endif
    endloop
    set other = null
    set moving = null
    return true
endfunction

function WM_FindSafeUnitPoint takes unit moving, real originX, real originY, real clearance, pathingtype terrainPath, boolean flying, real maxRadius returns boolean
    local integer ring = 1
    local integer spoke = 0
    local real distance = 0.0
    local real angle = 0.0
    local real px = WM_ClampMapCoord(originX)
    local real py = WM_ClampMapCoord(originY)
    if WM_IsSafeUnitPoint(moving, px, py, clearance, terrainPath, flying) then
        set udg_SafePointX = px
        set udg_SafePointY = py
        set moving = null
        return true
    endif
    loop
        exitwhen I2R(ring) * 48.0 > maxRadius
        set distance = I2R(ring) * 48.0
        set spoke = 0
        loop
            exitwhen spoke >= 8
            set angle = I2R(spoke) * 0.78539816339
            set px = WM_ClampMapCoord(originX + Cos(angle) * distance)
            set py = WM_ClampMapCoord(originY + Sin(angle) * distance)
            if WM_IsSafeUnitPoint(moving, px, py, clearance, terrainPath, flying) then
                set udg_SafePointX = px
                set udg_SafePointY = py
                set moving = null
                return true
            endif
            set spoke = spoke + 1
        endloop
        set ring = ring + 1
    endloop
    set moving = null
    return false
endfunction

function WM_UsesAmphibiousPathing takes unit u returns boolean
    local integer rawcode = GetUnitTypeId(u)
    if rawcode == 'nmpe' or rawcode == 'nnmg' or rawcode == 'nsnp' or rawcode == 'nmyr' or rawcode == 'nnsw' or rawcode == 'nhyc' or rawcode == 'nnrg' or rawcode == 'nmys' or rawcode == 'nsbs' or rawcode == 'nnrs' then
        set u = null
        return true
    endif
    if rawcode == 'nnsu' or rawcode == 'Hvsh' or rawcode == 'N004' or rawcode == 'N001' or rawcode == 'N002' then
        set u = null
        return true
    endif
    set u = null
    return false
endfunction

function WM_PullOrPushUnit takes unit u, real cx, real cy, real deltaDist returns nothing
    local real ux = GetUnitX(u)
    local real uy = GetUnitY(u)
    local real dx = ux - cx
    local real dy = uy - cy
    local real dist = SquareRoot(dx * dx + dy * dy)
    local real nx = 0.0
    local real ny = 0.0
    local pathingtype terrainPath = PATHING_TYPE_WALKABILITY
    local boolean flying = false
    if IsUnitType(u, UNIT_TYPE_GIANT) or IsUnitType(u, UNIT_TYPE_STRUCTURE) then
        set u = null
        return
    endif
    if IsUnitType(u, UNIT_TYPE_FLYING) then
        set terrainPath = PATHING_TYPE_FLYABILITY
        set flying = true
    elseif WM_UsesAmphibiousPathing(u) then
        set terrainPath = PATHING_TYPE_AMPHIBIOUSPATHING
    endif
    if dist < 12.0 then
        set dist = 12.0
    endif
    set nx = WM_ClampMapCoord(ux + (dx / dist) * deltaDist)
    set ny = WM_ClampMapCoord(uy + (dy / dist) * deltaDist)
    if WM_FindSafeUnitPoint(u, nx, ny, 56.0, terrainPath, flying, 144.0) then
        call SetUnitPosition(u, udg_SafePointX, udg_SafePointY)
    endif
    set u = null
endfunction

// ============================================================================
// CUSTOM 3D `.mdx` + GEOMETRIC SPELL ENGINE (ALL 16 CUSTOM HERO SKILLS `A000..A015`)
// ============================================================================

""" + SPELL_ENGINE_V4 + r"""
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
    call SetPlayerTechMaxAllowed(p, 'N004', 1)
    call SetPlayerTechMaxAllowed(p, 'N001', 1)
    call SetPlayerTechMaxAllowed(p, 'N002', 1)
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
    local integer shrinePid = udg_ShrineControllerPid
    local integer heroLvl = 0
    local unit u = null

    if udg_CrownBoard == null then
        return
    endif
    if secs < 10 then
        set secStr = "0" + secStr
    endif

    call MultiboardSetTitleText(udg_CrownBoard, "|cffffd700★ CROWN OF WARMAHDI|r  |cff38bdf8[" + I2S(mins) + ":" + secStr + "]|r")

    // Row 0: AI Difficulty + Shrine Status (actual lobby alliances, not fixed player-index teams)
    if shrinePid >= 0 and shrinePid < 8 then
        set shrineTxt = "|cff38bdf8" + GetPlayerName(Player(shrinePid)) + "|r"
    elseif shrinePid == 99 then
        set shrineTxt = "|cfffbbf24Contested!|r"
    endif

    set mbitem = MultiboardGetItem(udg_CrownBoard, 0, 0)
    call MultiboardSetItemValue(mbitem, "|cffcbd5e1AI:|r " + WM_GetDiffLabel(udg_AIDiff) + " " + WM_GetDiffSupportLabel(udg_AIDiff))
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
            call MultiboardSetItemIcon(mbitem, "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_Hvsh.blp")
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
    local player captor = null
    local integer pid = 0
    local integer captorPid = -1
    local boolean contested = false

    set udg_MatchSeconds = udg_MatchSeconds + 2

    // Central Crown Shrine `(0, 0)` control check (`radius = 650`). Resolve ownership
    // from the lobby's real alliances so 4v4, 2v2, and FFA all behave correctly.
    call GroupClear(udg_TempGroupA)
    call GroupEnumUnitsInRange(udg_TempGroupA, 0.0, 0.0, 650.0, null)
    loop
        set u = FirstOfGroup(udg_TempGroupA)
        exitwhen u == null
        call GroupRemoveUnit(udg_TempGroupA, u)
        if GetWidgetLife(u) > 0.405 and not IsUnitType(u, UNIT_TYPE_STRUCTURE) then
            set owner = GetOwningPlayer(u)
            set pid = GetPlayerId(owner)
            if pid >= 0 and pid < 8 and GetPlayerSlotState(owner) == PLAYER_SLOT_STATE_PLAYING then
                call SetWidgetLife(u, GetWidgetLife(u) + 6.0)
                if captor == null then
                    set captor = owner
                    set captorPid = pid
                elseif pid != captorPid and not IsPlayerAlly(owner, captor) then
                    set contested = true
                elseif IsPlayerAlly(owner, captor) and pid < captorPid then
                    set captor = owner
                    set captorPid = pid
                endif
            endif
        endif
    endloop

    if contested then
        set udg_ShrineControllerPid = 99
    elseif captor != null then
        set udg_ShrineControllerPid = captorPid
    else
        set udg_ShrineControllerPid = -1
    endif

    // A held shrine grants +3 gold every 2 seconds to the controlling player's
    // actual allies. In FFA this naturally rewards only the captor.
    if captor != null and not contested then
        set pid = 0
        loop
            exitwhen pid >= 8
            if GetPlayerSlotState(Player(pid)) == PLAYER_SLOT_STATE_PLAYING and (Player(pid) == captor or IsPlayerAlly(Player(pid), captor)) then
                call SetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD, GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD) + 3)
            endif
            set pid = pid + 1
        endloop
    endif

    call WM_RefreshMultiboard()
    set u = null
    set owner = null
    set captor = null
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

    // Custom-race .ai files were competing with the generated JASS macro for the
    // same halls, altars, and workers. The guarded JASS controller is authoritative.
    if faction >= 5 then
        return
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

function WM_AIChooseHeroSkill takes unit hero, integer q, integer w, integer e, integer r returns nothing
    local integer heroLevel = GetHeroLevel(hero)
    local integer learnedQ = GetUnitAbilityLevel(hero, q)
    local integer learnedW = GetUnitAbilityLevel(hero, w)
    local integer learnedE = GetUnitAbilityLevel(hero, e)
    local integer learnedR = GetUnitAbilityLevel(hero, r)
    if GetHeroSkillPoints(hero) <= 0 then
        return
    endif
    if heroLevel >= 6 and learnedR == 0 then
        call SelectHeroSkill(hero, r)
    elseif (heroLevel == 1 or heroLevel == 3 or heroLevel == 5) and learnedQ < 3 then
        call SelectHeroSkill(hero, q)
    elseif (heroLevel == 2 or heroLevel == 7 or heroLevel == 8) and learnedW < 3 then
        call SelectHeroSkill(hero, w)
    elseif learnedE < 3 then
        call SelectHeroSkill(hero, e)
    elseif learnedQ < 3 then
        call SelectHeroSkill(hero, q)
    elseif learnedW < 3 then
        call SelectHeroSkill(hero, w)
    else
        call SelectHeroSkill(hero, e)
    endif
endfunction

function WM_AIChooseCustomHeroSkill takes unit hero, integer faction returns nothing
    local integer heroId = GetUnitTypeId(hero)
    if faction == 5 then
        if heroId == 'Hvsh' then
            call WM_AIChooseHeroSkill(hero, 'A000', 'A001', 'A002', 'A003')
        elseif heroId == 'N004' then
            call WM_AIChooseHeroSkill(hero, 'A004', 'A005', 'A006', 'A007')
        elseif heroId == 'N001' then
            call WM_AIChooseHeroSkill(hero, 'A008', 'A009', 'A010', 'A011')
        elseif heroId == 'N002' then
            call WM_AIChooseHeroSkill(hero, 'A012', 'A013', 'A014', 'A015')
        endif
    elseif faction == 6 then
        if heroId == 'Hkal' then
            call WM_AIChooseHeroSkill(hero, 'A016', 'A017', 'A018', 'A019')
        elseif heroId == 'Hvwd' then
            call WM_AIChooseHeroSkill(hero, 'A020', 'A021', 'A022', 'A023')
        elseif heroId == 'Hlgr' then
            call WM_AIChooseHeroSkill(hero, 'A024', 'A025', 'A026', 'A027')
        elseif heroId == 'Huth' then
            call WM_AIChooseHeroSkill(hero, 'A028', 'A029', 'A030', 'A031')
        endif
    elseif faction == 7 then
        if heroId == 'V001' then
            call WM_AIChooseHeroSkill(hero, 'A032', 'A033', 'A034', 'A035')
        elseif heroId == 'V002' then
            call WM_AIChooseHeroSkill(hero, 'A036', 'A037', 'A038', 'A039')
        elseif heroId == 'V003' then
            call WM_AIChooseHeroSkill(hero, 'A040', 'A041', 'A042', 'A043')
        elseif heroId == 'V004' then
            call WM_AIChooseHeroSkill(hero, 'A044', 'A045', 'A046', 'A047')
        endif
    elseif faction == 8 then
        if heroId == 'T001' then
            call WM_AIChooseHeroSkill(hero, 'A048', 'A049', 'A050', 'A051')
        elseif heroId == 'T002' then
            call WM_AIChooseHeroSkill(hero, 'A052', 'A053', 'A054', 'A055')
        elseif heroId == 'T003' then
            call WM_AIChooseHeroSkill(hero, 'A056', 'A057', 'A058', 'A059')
        elseif heroId == 'T004' then
            call WM_AIChooseHeroSkill(hero, 'A060', 'A061', 'A062', 'A063')
        endif
    endif
    set hero = null
endfunction

function WM_AIObservedHallTier takes integer rawcode returns integer
    // Intel is recorded only when the building is visible to the AI player.
    if rawcode == 'hcas' or rawcode == 'ofrt' or rawcode == 'unp2' or rawcode == 'etoe' or rawcode == 'n002' or rawcode == 'h003' or rawcode == 'v003' or rawcode == 't003' then
        return 3
    elseif rawcode == 'hkee' or rawcode == 'ostr' or rawcode == 'unp1' or rawcode == 'etoa' or rawcode == 'n001' or rawcode == 'h002' or rawcode == 'v002' or rawcode == 't002' then
        return 2
    endif
    return 0
endfunction

function WM_AIIsTownHallRawcode takes integer rawcode returns boolean
    if rawcode == 'htow' or rawcode == 'hkee' or rawcode == 'hcas' or rawcode == 'ogre' or rawcode == 'ostr' or rawcode == 'ofrt' or rawcode == 'unpl' or rawcode == 'unp1' or rawcode == 'unp2' or rawcode == 'etol' or rawcode == 'etoa' or rawcode == 'etoe' or rawcode == 'nntt' or rawcode == 'n001' or rawcode == 'n002' or rawcode == 'h001' or rawcode == 'h002' or rawcode == 'h003' or rawcode == 'v001' or rawcode == 'v002' or rawcode == 'v003' or rawcode == 't001' or rawcode == 't002' or rawcode == 't003' then
        return true
    endif
    return false
endfunction

function WM_AIRefreshEnemyIntel takes player aiPlayer, integer aiPid, real homeX, real homeY returns unit
    local integer enemyId = 0
    local integer slot = 0
    local integer rawcode = 0
    local integer seenCount = 0
    local integer visibleContactCount = 0
    local integer seenAir = 0
    local integer seenCasters = 0
    local integer seenRanged = 0
    local integer seenTier = 0
    local integer knownAirTotal = 0
    local integer knownCasterTotal = 0
    local integer knownRangedTotal = 0
    local integer knownTierMax = 0
    local integer observedTier = 0
    local integer age = 0
    local unit u = null
    local unit best = null
    local unit bestStructure = null
    local real sumX = 0.0
    local real sumY = 0.0
    local real dx = 0.0
    local real dy = 0.0
    local real distSq = 0.0
    local real dist = 0.0
    local real hpPct = 0.0
    local real score = 0.0
    local real bestScore = -999999.0
    local real buildingScore = 0.0
    local real bestBuildingScore = -999999.0

    set udg_AIVisibleEnemyCount[aiPid] = 0
    set udg_AIEnemyAirCount[aiPid] = 0
    set udg_AIEnemyCasterCount[aiPid] = 0
    set udg_AIEnemyRangedCount[aiPid] = 0
    set udg_AIEnemyTierCount[aiPid] = 0

    loop
        exitwhen enemyId >= 8
        if enemyId != aiPid and GetPlayerSlotState(Player(enemyId)) == PLAYER_SLOT_STATE_PLAYING and IsPlayerEnemy(aiPlayer, Player(enemyId)) then
            set slot = aiPid * 8 + enemyId
            set seenCount = 0
            set seenAir = 0
            set seenCasters = 0
            set seenRanged = 0
            set seenTier = 0
            set sumX = 0.0
            set sumY = 0.0
            call GroupClear(udg_TempGroupB)
            call GroupEnumUnitsOfPlayer(udg_TempGroupB, Player(enemyId), null)
            loop
                set u = FirstOfGroup(udg_TempGroupB)
                exitwhen u == null
                call GroupRemoveUnit(udg_TempGroupB, u)
                if GetWidgetLife(u) > 0.405 and IsUnitVisible(u, aiPlayer) then
                    set rawcode = GetUnitTypeId(u)
                    if not IsUnitType(u, UNIT_TYPE_PEON) and not WM_IsCustomAIWorker(udg_PlayerFaction[enemyId], rawcode) then
                        set seenCount = seenCount + 1
                        set sumX = sumX + GetUnitX(u)
                        set sumY = sumY + GetUnitY(u)
                        if IsUnitType(u, UNIT_TYPE_FLYING) then
                            set seenAir = seenAir + 1
                        endif
                        if GetUnitState(u, UNIT_STATE_MAX_MANA) > 0.0 then
                            set seenCasters = seenCasters + 1
                        endif
                        if IsUnitType(u, UNIT_TYPE_RANGED_ATTACKER) then
                            set seenRanged = seenRanged + 1
                        endif
                        if IsUnitType(u, UNIT_TYPE_STRUCTURE) then
                            set observedTier = WM_AIObservedHallTier(rawcode)
                            if observedTier > seenTier then
                                set seenTier = observedTier
                            endif
                            set dx = GetUnitX(u) - homeX
                            set dy = GetUnitY(u) - homeY
                            set dist = SquareRoot(dx * dx + dy * dy)
                            set buildingScore = 35.0 + 90000.0 / (900.0 + dist)
                            if buildingScore > bestBuildingScore then
                                set bestBuildingScore = buildingScore
                                set bestStructure = u
                            endif
                        else
                            set dx = GetUnitX(u) - homeX
                            set dy = GetUnitY(u) - homeY
                            set distSq = dx * dx + dy * dy
                            set dist = SquareRoot(distSq)
                            set hpPct = GetWidgetLife(u) / RMaxBJ(1.0, GetUnitState(u, UNIT_STATE_MAX_LIFE))
                            set score = 90.0 + 180000.0 / (900.0 + dist)
                            if IsUnitType(u, UNIT_TYPE_HERO) then
                                set score = score + 260.0
                            endif
                            if GetUnitState(u, UNIT_STATE_MAX_MANA) > 0.0 then
                                set score = score + 100.0
                            endif
                            if IsUnitType(u, UNIT_TYPE_RANGED_ATTACKER) then
                                set score = score + 35.0
                            endif
                            if hpPct < 0.35 then
                                set score = score + 145.0
                            elseif hpPct < 0.62 then
                                set score = score + 65.0
                            endif
                            if distSq < 1960000.0 then
                                set score = score + 400.0
                            endif
                            if udg_AIExpansionActive[aiPid] then
                                set dx = GetUnitX(u) - udg_AIExpansionX[aiPid]
                                set dy = GetUnitY(u) - udg_AIExpansionY[aiPid]
                                if dx * dx + dy * dy < 2250000.0 then
                                    set score = score + 320.0
                                endif
                            endif
                            if score > bestScore then
                                set bestScore = score
                                set best = u
                            endif
                        endif
                    endif
                endif
            endloop

            if seenCount > 0 then
                set udg_AILastSeenX[slot] = sumX / I2R(seenCount)
                set udg_AILastSeenY[slot] = sumY / I2R(seenCount)
                set udg_AILastSeenAt[slot] = udg_MatchSeconds
                set visibleContactCount = visibleContactCount + seenCount
            endif
            if seenAir > 0 and seenAir >= udg_AIEnemyAirSeen[slot] then
                set udg_AIEnemyAirSeen[slot] = seenAir
                set udg_AIEnemyAirSeenAt[slot] = udg_MatchSeconds
            endif
            if seenCasters > 0 and seenCasters >= udg_AIEnemyCasterSeen[slot] then
                set udg_AIEnemyCasterSeen[slot] = seenCasters
                set udg_AIEnemyCasterSeenAt[slot] = udg_MatchSeconds
            endif
            if seenRanged > 0 and seenRanged >= udg_AIEnemyRangedSeen[slot] then
                set udg_AIEnemyRangedSeen[slot] = seenRanged
                set udg_AIEnemyRangedSeenAt[slot] = udg_MatchSeconds
            endif
            if seenTier > udg_AIEnemyTierSeen[slot] then
                set udg_AIEnemyTierSeen[slot] = seenTier
            endif

            set age = udg_MatchSeconds - udg_AIEnemyAirSeenAt[slot]
            if udg_AIEnemyAirSeen[slot] > 0 and age > 150 and ModuloInteger(udg_MatchSeconds, 30) == 0 then
                set udg_AIEnemyAirSeen[slot] = udg_AIEnemyAirSeen[slot] - 1
                set udg_AIEnemyAirSeenAt[slot] = udg_MatchSeconds
            endif
            set age = udg_MatchSeconds - udg_AIEnemyCasterSeenAt[slot]
            if udg_AIEnemyCasterSeen[slot] > 0 and age > 150 and ModuloInteger(udg_MatchSeconds, 30) == 0 then
                set udg_AIEnemyCasterSeen[slot] = udg_AIEnemyCasterSeen[slot] - 1
                set udg_AIEnemyCasterSeenAt[slot] = udg_MatchSeconds
            endif
            set age = udg_MatchSeconds - udg_AIEnemyRangedSeenAt[slot]
            if udg_AIEnemyRangedSeen[slot] > 0 and age > 150 and ModuloInteger(udg_MatchSeconds, 30) == 0 then
                set udg_AIEnemyRangedSeen[slot] = udg_AIEnemyRangedSeen[slot] - 1
                set udg_AIEnemyRangedSeenAt[slot] = udg_MatchSeconds
            endif

            if udg_MatchSeconds - udg_AIEnemyAirSeenAt[slot] <= 240 then
                set knownAirTotal = knownAirTotal + udg_AIEnemyAirSeen[slot]
            endif
            if udg_MatchSeconds - udg_AIEnemyCasterSeenAt[slot] <= 240 then
                set knownCasterTotal = knownCasterTotal + udg_AIEnemyCasterSeen[slot]
            endif
            if udg_MatchSeconds - udg_AIEnemyRangedSeenAt[slot] <= 240 then
                set knownRangedTotal = knownRangedTotal + udg_AIEnemyRangedSeen[slot]
            endif
            if udg_AIEnemyTierSeen[slot] > knownTierMax then
                set knownTierMax = udg_AIEnemyTierSeen[slot]
            endif
        endif
        set enemyId = enemyId + 1
    endloop

    set udg_AIVisibleEnemyCount[aiPid] = visibleContactCount
    set udg_AIEnemyAirCount[aiPid] = knownAirTotal
    set udg_AIEnemyCasterCount[aiPid] = knownCasterTotal
    set udg_AIEnemyRangedCount[aiPid] = knownRangedTotal
    set udg_AIEnemyTierCount[aiPid] = knownTierMax
    set udg_AIMetricVisibleContacts[aiPid] = udg_AIMetricVisibleContacts[aiPid] + visibleContactCount

    if best == null then
        set best = bestStructure
    endif
    set u = null
    set bestStructure = null
    return best
endfunction

function WM_AIFindManaTarget takes unit hero, real radius returns unit
    local player owner = GetOwningPlayer(hero)
    local unit u = null
    local unit best = null
    local integer enemyPid = 0
    local integer rawcode = 0
    local real mana = 0.0
    local real bestMana = -1.0
    local real targetScore = 0.0
    local real bestScore = -1.0
    call GroupClear(udg_SpellGroup)
    call GroupEnumUnitsInRange(udg_SpellGroup, GetUnitX(hero), GetUnitY(hero), radius, null)
    loop
        set u = FirstOfGroup(udg_SpellGroup)
        exitwhen u == null
        call GroupRemoveUnit(udg_SpellGroup, u)
        set enemyPid = GetPlayerId(GetOwningPlayer(u))
        set rawcode = GetUnitTypeId(u)
        if GetWidgetLife(u) > 0.405 and IsUnitEnemy(u, owner) and IsUnitVisible(u, owner) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and not IsUnitType(u, UNIT_TYPE_PEON) and not WM_IsCustomAIWorker(udg_PlayerFaction[enemyPid], rawcode) and GetUnitState(u, UNIT_STATE_MAX_MANA) > 0.0 then
            set mana = GetUnitState(u, UNIT_STATE_MANA)
            set targetScore = mana
            if IsUnitType(u, UNIT_TYPE_HERO) then
                set targetScore = targetScore + 40.0
            endif
            if targetScore > bestScore then
                set best = u
                set bestMana = mana
                set bestScore = targetScore
            endif
        endif
    endloop
    set owner = null
    set u = null
    return best
endfunction

function WM_AICountVisibleEnemies takes unit hero, real radius returns integer
    local player owner = GetOwningPlayer(hero)
    local unit u = null
    local integer enemyPid = 0
    local integer rawcode = 0
    local integer count = 0
    call GroupClear(udg_SpellGroup)
    call GroupEnumUnitsInRange(udg_SpellGroup, GetUnitX(hero), GetUnitY(hero), radius, null)
    loop
        set u = FirstOfGroup(udg_SpellGroup)
        exitwhen u == null
        call GroupRemoveUnit(udg_SpellGroup, u)
        set enemyPid = GetPlayerId(GetOwningPlayer(u))
        set rawcode = GetUnitTypeId(u)
        if GetWidgetLife(u) > 0.405 and IsUnitEnemy(u, owner) and IsUnitVisible(u, owner) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and not IsUnitType(u, UNIT_TYPE_PEON) and not WM_IsCustomAIWorker(udg_PlayerFaction[enemyPid], rawcode) then
            set count = count + 1
        endif
    endloop
    set owner = null
    set u = null
    return count
endfunction

function WM_AICountInjuredAllies takes unit hero, real radius, real healthCutoff returns integer
    local player owner = GetOwningPlayer(hero)
    local unit u = null
    local real hpPct = 1.0
    local integer count = 0
    call GroupClear(udg_SpellGroup)
    call GroupEnumUnitsInRange(udg_SpellGroup, GetUnitX(hero), GetUnitY(hero), radius, null)
    loop
        set u = FirstOfGroup(udg_SpellGroup)
        exitwhen u == null
        call GroupRemoveUnit(udg_SpellGroup, u)
        if GetWidgetLife(u) > 0.405 and IsUnitAlly(u, owner) and IsUnitVisible(u, owner) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) then
            set hpPct = GetWidgetLife(u) / RMaxBJ(1.0, GetUnitState(u, UNIT_STATE_MAX_LIFE))
            if hpPct < healthCutoff then
                set count = count + 1
            endif
        endif
    endloop
    set owner = null
    set u = null
    return count
endfunction

function WM_AIShouldCastAreaE takes integer abil, integer enemyCount, integer injuredCount returns boolean
    if injuredCount > 0 then
        return true
    endif
    if abil == 'A014' or abil == 'A030' then
        return false
    elseif abil == 'A006' or abil == 'A022' or abil == 'A042' or abil == 'A058' then
        return enemyCount >= 1
    endif
    return enemyCount >= 2
endfunction

function WM_AISelectSpellCenter takes unit hero, unit fallback, real radius returns nothing
    local player owner = GetOwningPlayer(hero)
    local unit candidate = null
    local unit nearby = null
    local integer enemyPid = 0
    local integer rawcode = 0
    local real hx = GetUnitX(hero)
    local real hy = GetUnitY(hero)
    local real cx = GetUnitX(fallback)
    local real cy = GetUnitY(fallback)
    local real score = 0.0
    local real bestScore = -1.0
    local integer hits = 0
    local integer bestHits = 0
    set udg_AISpellAimX = cx
    set udg_AISpellAimY = cy
    call GroupClear(udg_SpellGroup)
    call GroupEnumUnitsInRange(udg_SpellGroup, hx, hy, 700.0, null)
    loop
        set candidate = FirstOfGroup(udg_SpellGroup)
        exitwhen candidate == null
        call GroupRemoveUnit(udg_SpellGroup, candidate)
        set enemyPid = GetPlayerId(GetOwningPlayer(candidate))
        set rawcode = GetUnitTypeId(candidate)
        if GetWidgetLife(candidate) > 0.405 and IsUnitEnemy(candidate, owner) and IsUnitVisible(candidate, owner) and not IsUnitType(candidate, UNIT_TYPE_STRUCTURE) and not IsUnitType(candidate, UNIT_TYPE_PEON) and not WM_IsCustomAIWorker(udg_PlayerFaction[enemyPid], rawcode) then
            set cx = GetUnitX(candidate)
            set cy = GetUnitY(candidate)
            set hits = 0
            set score = 0.0
            call GroupClear(udg_TempGroupB)
            call GroupEnumUnitsInRange(udg_TempGroupB, cx, cy, radius, null)
            loop
                set nearby = FirstOfGroup(udg_TempGroupB)
                exitwhen nearby == null
                call GroupRemoveUnit(udg_TempGroupB, nearby)
                set enemyPid = GetPlayerId(GetOwningPlayer(nearby))
                set rawcode = GetUnitTypeId(nearby)
                if GetWidgetLife(nearby) > 0.405 and IsUnitEnemy(nearby, owner) and IsUnitVisible(nearby, owner) and not IsUnitType(nearby, UNIT_TYPE_STRUCTURE) and not IsUnitType(nearby, UNIT_TYPE_PEON) and not WM_IsCustomAIWorker(udg_PlayerFaction[enemyPid], rawcode) then
                    set hits = hits + 1
                    set score = score + 100.0
                    if IsUnitType(nearby, UNIT_TYPE_HERO) then
                        set score = score + 18.0
                    endif
                    if GetUnitState(nearby, UNIT_STATE_MAX_MANA) > 0.0 then
                        set score = score + 8.0
                    endif
                endif
            endloop
            if IsUnitType(candidate, UNIT_TYPE_HERO) then
                set score = score + 12.0
            endif
            if hits > bestHits or (hits == bestHits and score > bestScore) then
                set bestHits = hits
                set bestScore = score
                set udg_AISpellAimX = cx
                set udg_AISpellAimY = cy
            endif
        endif
    endloop
    set owner = null
    set candidate = null
    set nearby = null
endfunction

function WM_AIFindSpellTarget takes unit hero, integer abil, real radius returns unit
    local player owner = GetOwningPlayer(hero)
    local unit u = null
    local unit best = null
    local integer enemyPid = 0
    local integer rawcode = 0
    local real mana = 0.0
    local real maxMana = 0.0
    local real hpPct = 1.0
    local real missingLife = 0.0
    local real score = 0.0
    local real bestScore = -1.0
    call GroupClear(udg_SpellGroup)
    call GroupEnumUnitsInRange(udg_SpellGroup, GetUnitX(hero), GetUnitY(hero), radius, null)
    loop
        set u = FirstOfGroup(udg_SpellGroup)
        exitwhen u == null
        call GroupRemoveUnit(udg_SpellGroup, u)
        set enemyPid = GetPlayerId(GetOwningPlayer(u))
        set rawcode = GetUnitTypeId(u)
        if GetWidgetLife(u) > 0.405 and IsUnitEnemy(u, owner) and IsUnitVisible(u, owner) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and not IsUnitType(u, UNIT_TYPE_PEON) and not WM_IsCustomAIWorker(udg_PlayerFaction[enemyPid], rawcode) then
            set mana = GetUnitState(u, UNIT_STATE_MANA)
            set maxMana = GetUnitState(u, UNIT_STATE_MAX_MANA)
            set hpPct = GetWidgetLife(u) / RMaxBJ(1.0, GetUnitState(u, UNIT_STATE_MAX_LIFE))
            set missingLife = GetUnitState(u, UNIT_STATE_MAX_LIFE) - GetWidgetLife(u)
            set score = 100.0 - hpPct * 55.0
            if IsUnitType(u, UNIT_TYPE_HERO) then
                set score = score + 115.0
            endif
            if maxMana > 0.0 then
                set score = score + 50.0
            endif
            if IsUnitType(u, UNIT_TYPE_RANGED_ATTACKER) then
                set score = score + 25.0
            endif
            if hpPct < 0.35 then
                set score = score + 85.0
            endif
            if abil == 'A005' or abil == 'A013' or abil == 'A017' or abil == 'A037' or abil == 'A045' then
                set score = score + mana * 0.55
                if maxMana > 0.0 and mana < 18.0 and abil == 'A005' then
                    set score = score - 240.0
                endif
            endif
            if abil == 'A025' then
                set score = score + missingLife * 0.12
            endif
            if score > bestScore then
                set bestScore = score
                set best = u
            endif
        endif
    endloop
    set owner = null
    set u = null
    return best
endfunction

function WM_AIHasFallenAllyHero takes unit hero, real radius returns boolean
    local player owner = GetOwningPlayer(hero)
    local unit u = null
    local boolean found = false
    call GroupClear(udg_SpellGroup)
    call GroupEnumUnitsInRange(udg_SpellGroup, GetUnitX(hero), GetUnitY(hero), radius, null)
    loop
        set u = FirstOfGroup(udg_SpellGroup)
        exitwhen u == null or found
        call GroupRemoveUnit(udg_SpellGroup, u)
        if u != hero and GetUnitTypeId(u) != 0 and IsUnitType(u, UNIT_TYPE_HERO) and IsUnitAlly(u, owner) and IsUnitVisible(u, owner) and GetWidgetLife(u) <= 0.405 then
            set found = true
        endif
    endloop
    set owner = null
    set u = null
    return found
endfunction

function WM_AICastCustomHeroCombo takes unit hero, unit enemy returns nothing
    local integer hid = GetUnitTypeId(hero)
    local integer q = 0
    local integer w = 0
    local integer e = 0
    local integer r = 0
    local unit manaTarget = null
    local unit focusTarget = null
    local real ex = GetUnitX(enemy)
    local real ey = GetUnitY(enemy)
    local real hpPct = GetWidgetLife(hero) / RMaxBJ(1.0, GetUnitState(hero, UNIT_STATE_MAX_LIFE))
    local integer nearbyEnemies = 0
    local integer injuredAllies = 0
    local real ultRadius = 410.0
    local integer pid = GetPlayerId(GetOwningPlayer(hero))

    // Each of the sixteen custom heroes learns its own four exclusive skills.
    if hid == 'Hvsh' then
        set q = 'A000'
        set w = 'A001'
        set e = 'A002'
        set r = 'A003'
    elseif hid == 'N004' then
        set q = 'A004'
        set w = 'A005'
        set e = 'A006'
        set r = 'A007'
    elseif hid == 'N001' then
        set q = 'A008'
        set w = 'A009'
        set e = 'A010'
        set r = 'A011'
    elseif hid == 'N002' then
        set q = 'A012'
        set w = 'A013'
        set e = 'A014'
        set r = 'A015'
    elseif hid == 'Hkal' then
        set q = 'A016'
        set w = 'A017'
        set e = 'A018'
        set r = 'A019'
    elseif hid == 'Hvwd' then
        set q = 'A020'
        set w = 'A021'
        set e = 'A022'
        set r = 'A023'
    elseif hid == 'Hlgr' then
        set q = 'A024'
        set w = 'A025'
        set e = 'A026'
        set r = 'A027'
    elseif hid == 'Huth' then
        set q = 'A028'
        set w = 'A029'
        set e = 'A030'
        set r = 'A031'
    elseif hid == 'V001' then
        set q = 'A032'
        set w = 'A033'
        set e = 'A034'
        set r = 'A035'
    elseif hid == 'V002' then
        set q = 'A036'
        set w = 'A037'
        set e = 'A038'
        set r = 'A039'
    elseif hid == 'V003' then
        set q = 'A040'
        set w = 'A041'
        set e = 'A042'
        set r = 'A043'
    elseif hid == 'V004' then
        set q = 'A044'
        set w = 'A045'
        set e = 'A046'
        set r = 'A047'
    elseif hid == 'T001' then
        set q = 'A048'
        set w = 'A049'
        set e = 'A050'
        set r = 'A051'
    elseif hid == 'T002' then
        set q = 'A052'
        set w = 'A053'
        set e = 'A054'
        set r = 'A055'
    elseif hid == 'T003' then
        set q = 'A056'
        set w = 'A057'
        set e = 'A058'
        set r = 'A059'
    elseif hid == 'T004' then
        set q = 'A060'
        set w = 'A061'
        set e = 'A062'
        set r = 'A063'
    endif

    if q == 0 then
        return
    endif
    call WM_AIChooseHeroSkill(hero, q, w, e, r)
    if GetUnitState(hero, UNIT_STATE_MANA) < 50.0 then
        return
    endif

    set nearbyEnemies = WM_AICountVisibleEnemies(hero, 450.0)
    set injuredAllies = WM_AICountInjuredAllies(hero, 360.0, 0.72)

    // Resurrection is gated on a real nearby fallen ally; supportive E spells
    // are used when they can save an injured friend rather than on cooldown.
    if r == 'A031' and GetUnitAbilityLevel(hero, r) > 0 and WM_AIHasFallenAllyHero(hero, 520.0) then
        if IssueImmediateOrder(hero, "resurrection") then
            set udg_AIMetricSpellOrders[pid] = udg_AIMetricSpellOrders[pid] + 1
            return
        endif
    endif
    if GetUnitAbilityLevel(hero, e) > 0 and (hpPct < 0.58 or injuredAllies > 0) then
        if IssueImmediateOrder(hero, "thunderclap") then
            set udg_AIMetricSpellOrders[pid] = udg_AIMetricSpellOrders[pid] + 1
            return
        endif
    endif

    // Mana-drain skills actively seek a visible, mana-rich target. A005 (Mana
    // Burn) is never spent on a target with no meaningful mana to burn.
    if GetUnitAbilityLevel(hero, w) > 0 and (w == 'A005' or w == 'A013' or w == 'A017' or w == 'A037' or w == 'A045') then
        set manaTarget = WM_AIFindManaTarget(hero, 650.0)
        if manaTarget != null and (w != 'A005' or GetUnitState(manaTarget, UNIT_STATE_MANA) >= 25.0) then
            if w == 'A005' and IssueTargetOrder(hero, "manaburn", manaTarget) then
                set udg_AIMetricSpellOrders[pid] = udg_AIMetricSpellOrders[pid] + 1
                set manaTarget = null
                return
            elseif w != 'A005' and IssueTargetOrder(hero, "chainlightning", manaTarget) then
                set udg_AIMetricSpellOrders[pid] = udg_AIMetricSpellOrders[pid] + 1
                set manaTarget = null
                return
            endif
        endif
    endif

    // R spells need a worthwhile visible fight. A Roar ultimate is self-centered;
    // Mimiron's laser evaluates a wider lane footprint before choosing its point.
    if udg_AIDiff >= 2 and GetUnitAbilityLevel(hero, r) > 0 then
        if r == 'A007' or r == 'A043' then
            if nearbyEnemies >= 1 and IssueImmediateOrder(hero, "roar") then
                set udg_AIMetricSpellOrders[pid] = udg_AIMetricSpellOrders[pid] + 1
                return
            endif
        elseif r != 'A031' and (nearbyEnemies >= 2 or (udg_AIDiff >= 4 and nearbyEnemies >= 1)) then
            if r == 'A059' then
                set ultRadius = 560.0
            endif
            call WM_AISelectSpellCenter(hero, enemy, ultRadius)
            set ex = udg_AISpellAimX
            set ey = udg_AISpellAimY
            if IssuePointOrder(hero, "monsoon", ex, ey) then
                set udg_AIMetricSpellOrders[pid] = udg_AIMetricSpellOrders[pid] + 1
                return
            endif
        endif
    endif

    // Point AoE skills aim at the densest cluster of currently visible enemies.
    if GetUnitAbilityLevel(hero, q) > 0 then
        call WM_AISelectSpellCenter(hero, enemy, 325.0)
        set ex = udg_AISpellAimX
        set ey = udg_AISpellAimY
        if IssuePointOrder(hero, "flamestrike", ex, ey) then
            set udg_AIMetricSpellOrders[pid] = udg_AIMetricSpellOrders[pid] + 1
            return
        endif
    endif

    if GetUnitAbilityLevel(hero, w) > 0 then
        set focusTarget = WM_AIFindSpellTarget(hero, w, 650.0)
        if focusTarget == null then
            set focusTarget = enemy
        endif
        if w == 'A005' then
            set manaTarget = WM_AIFindManaTarget(hero, 650.0)
            if manaTarget != null and GetUnitState(manaTarget, UNIT_STATE_MANA) >= 25.0 then
                if IssueTargetOrder(hero, "manaburn", manaTarget) then
                    set udg_AIMetricSpellOrders[pid] = udg_AIMetricSpellOrders[pid] + 1
                    set manaTarget = null
                    set focusTarget = null
                    return
                endif
            endif
        elseif focusTarget != null and IssueTargetOrder(hero, "chainlightning", focusTarget) then
            set udg_AIMetricSpellOrders[pid] = udg_AIMetricSpellOrders[pid] + 1
            set manaTarget = null
            set focusTarget = null
            return
        endif
    endif

    // Remaining self-area E abilities are evaluated by role: heal when allies
    // are hurt, spend offensive/summon effects only into an actual engagement.
    if GetUnitAbilityLevel(hero, e) > 0 and WM_AIShouldCastAreaE(e, nearbyEnemies, injuredAllies) then
        if IssueImmediateOrder(hero, "thunderclap") then
            set udg_AIMetricSpellOrders[pid] = udg_AIMetricSpellOrders[pid] + 1
        endif
    endif
    set manaTarget = null
    set focusTarget = null
endfunction
function WM_EnumAIItemPickup takes nothing returns nothing
    local item it = GetEnumItem()
    local real dx = 0.0
    local real dy = 0.0
    local real dist = 0.0
    if it != null and IsItemVisible(it) and GetItemTypeId(it) != 0 then
        set dx = GetItemX(it) - GetUnitX(udg_ItemPickupHero)
        set dy = GetItemY(it) - GetUnitY(udg_ItemPickupHero)
        set dist = dx * dx + dy * dy
        if dist < udg_ItemPickupDistance then
            set udg_ItemPickupDistance = dist
            set udg_ItemPickupCandidate = it
        endif
    endif
    set it = null
endfunction

function WM_AIPickupNearbyItems takes unit hero returns nothing
    local rect r = null
    local real hx = GetUnitX(hero)
    local real hy = GetUnitY(hero)
    if UnitInventoryCount(hero) >= 6 or GetUnitCurrentOrder(hero) != 0 then
        return
    endif
    set udg_ItemPickupHero = hero
    set udg_ItemPickupCandidate = null
    set udg_ItemPickupDistance = 420.0 * 420.0
    set r = Rect(hx - 420.0, hy - 420.0, hx + 420.0, hy + 420.0)
    call EnumItemsInRect(r, null, function WM_EnumAIItemPickup)
    call RemoveRect(r)
    set r = null
    if udg_ItemPickupCandidate != null then
        call IssueTargetOrder(hero, "smart", udg_ItemPickupCandidate)
    endif
    set udg_ItemPickupHero = null
    set udg_ItemPickupCandidate = null
endfunction

function WM_AIUseInventory takes unit hero, real homeX, real homeY returns nothing
    local integer slot = 0
    local integer itemId = 0
    local item it = null
    local real hpPct = GetWidgetLife(hero) / RMaxBJ(1.0, GetUnitState(hero, UNIT_STATE_MAX_LIFE))
    local real manaMax = GetUnitState(hero, UNIT_STATE_MAX_MANA)
    local real manaPct = 1.0
    if manaMax > 0.0 then
        set manaPct = GetUnitState(hero, UNIT_STATE_MANA) / manaMax
    endif

    if hpPct < 0.45 then
        loop
            exitwhen slot >= 6
            set it = UnitItemInSlot(hero, slot)
            if it != null then
                set itemId = GetItemTypeId(it)
                if itemId == 'phea' or itemId == 'sreg' then
                    call UnitUseItem(hero, it)
                    set slot = 6
                endif
            endif
            set slot = slot + 1
        endloop
    endif

    if manaPct < 0.28 and manaMax > 0.0 then
        set slot = 0
        loop
            exitwhen slot >= 6
            set it = UnitItemInSlot(hero, slot)
            if it != null then
                set itemId = GetItemTypeId(it)
                if itemId == 'pman' or itemId == 'plcl' then
                    call UnitUseItem(hero, it)
                    set slot = 6
                endif
            endif
            set slot = slot + 1
        endloop
    endif

    if hpPct < 0.20 then
        set slot = 0
        loop
            exitwhen slot >= 6
            set it = UnitItemInSlot(hero, slot)
            if it != null and GetItemTypeId(it) == 'stwp' then
                call UnitUseItemPoint(hero, it, homeX, homeY)
                set slot = 6
            endif
            set slot = slot + 1
        endloop
    endif
    set it = null
endfunction

function WM_OnAITacticalMicroTick takes nothing returns nothing
    local integer i = 0
    local player p = null
    local unit u = null
    local unit foe = null
    local unit allyUnit = null
    local unit weakFoe = null
    local unit nearFoe = null
    local real ux = 0.0
    local real uy = 0.0
    local real hpPct = 0.0
    local real foePct = 0.0
    local real lowestPct = 2.0
    local real nearDistSq = 99999999.0
    local real candidateDistSq = 0.0
    local real dx = 0.0
    local real dy = 0.0
    local real dlen = 1.0
    local integer localAllyCount = 0
    local integer localEnemyCount = 0
    local integer enemyPid = 0
    local integer rawcode = 0
    local integer attackOrder = 0
    local boolean issued = false
    local integer sLoc = 0
    local real homeX = 0.0
    local real homeY = 0.0

    set attackOrder = OrderId("attack")
    loop
        exitwhen i >= 8
        set p = Player(i)
        if GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING and GetPlayerController(p) == MAP_CONTROL_COMPUTER and udg_PlayerFaction[i] >= 5 then
            set sLoc = GetPlayerStartLocation(p)
            set homeX = GetStartLocationX(sLoc)
            set homeY = GetStartLocationY(sLoc)

            call GroupClear(udg_TempGroupA)
            call GroupEnumUnitsOfPlayer(udg_TempGroupA, p, null)
            loop
                set u = FirstOfGroup(udg_TempGroupA)
                exitwhen u == null
                call GroupRemoveUnit(udg_TempGroupA, u)

                if GetWidgetLife(u) > 0.405 and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and not IsUnitType(u, UNIT_TYPE_PEON) and not WM_IsCustomAIWorker(udg_PlayerFaction[i], GetUnitTypeId(u)) then
                    set ux = GetUnitX(u)
                    set uy = GetUnitY(u)
                    set hpPct = GetWidgetLife(u) / RMaxBJ(1.0, GetUnitState(u, UNIT_STATE_MAX_LIFE))
                    if IsUnitType(u, UNIT_TYPE_HERO) then
                        call WM_AIUseInventory(u, homeX, homeY)
                        call WM_AIPickupNearbyItems(u)
                    endif

                    // Local force comparison uses only currently visible allied units.
                    set localAllyCount = 0
                    call GroupClear(udg_SpellGroup)
                    call GroupEnumUnitsInRange(udg_SpellGroup, ux, uy, 850.0, null)
                    loop
                        set allyUnit = FirstOfGroup(udg_SpellGroup)
                        exitwhen allyUnit == null
                        call GroupRemoveUnit(udg_SpellGroup, allyUnit)
                        if GetWidgetLife(allyUnit) > 0.405 and IsUnitAlly(allyUnit, p) and IsUnitVisible(allyUnit, p) and not IsUnitType(allyUnit, UNIT_TYPE_STRUCTURE) and not IsUnitType(allyUnit, UNIT_TYPE_PEON) and not WM_IsCustomAIWorker(udg_PlayerFaction[i], GetUnitTypeId(allyUnit)) then
                            set localAllyCount = localAllyCount + 1
                        endif
                    endloop

                    // Scan visible enemy units within 650 range and select nearest + weakest.
                    set nearFoe = null
                    set weakFoe = null
                    set lowestPct = 2.0
                    set nearDistSq = 99999999.0
                    set localEnemyCount = 0
                    call GroupClear(udg_TempGroupB)
                    call GroupEnumUnitsInRange(udg_TempGroupB, ux, uy, 650.0, null)
                    loop
                        set foe = FirstOfGroup(udg_TempGroupB)
                        exitwhen foe == null
                        call GroupRemoveUnit(udg_TempGroupB, foe)
                        set enemyPid = GetPlayerId(GetOwningPlayer(foe))
                        set rawcode = GetUnitTypeId(foe)
                        if GetWidgetLife(foe) > 0.405 and IsUnitEnemy(foe, p) and IsUnitVisible(foe, p) and not IsUnitType(foe, UNIT_TYPE_STRUCTURE) and not IsUnitType(foe, UNIT_TYPE_PEON) and not WM_IsCustomAIWorker(udg_PlayerFaction[enemyPid], rawcode) then
                            set localEnemyCount = localEnemyCount + 1
                            set dx = GetUnitX(foe) - ux
                            set dy = GetUnitY(foe) - uy
                            set candidateDistSq = dx * dx + dy * dy
                            if nearFoe == null or candidateDistSq < nearDistSq then
                                set nearDistSq = candidateDistSq
                                set nearFoe = foe
                            endif
                            set foePct = GetWidgetLife(foe) / RMaxBJ(1.0, GetUnitState(foe, UNIT_STATE_MAX_LIFE))
                            if foePct < lowestPct then
                                set lowestPct = foePct
                                set weakFoe = foe
                            endif
                        endif
                    endloop

                    if IsUnitType(u, UNIT_TYPE_HERO) and GetUnitTypeId(u) == 'Huth' and hpPct >= 0.26 and udg_AIDiff >= 2 and GetUnitAbilityLevel(u, 'A031') > 0 and WM_AIHasFallenAllyHero(u, 520.0) then
                        // Uther can restore a fallen ally even when no enemy is currently in spell range.
                        if IssueImmediateOrder(u, "resurrection") then
                            set udg_AIMetricSpellOrders[i] = udg_AIMetricSpellOrders[i] + 1
                        endif
                    elseif nearFoe != null then
                        // Local force assessment enables a coordinated fallback instead of
                        // leaving wounded units isolated against a visible numerical advantage.
                        if IsUnitType(u, UNIT_TYPE_HERO) and hpPct < 0.26 and udg_AIDiff >= 2 then
                            call WM_AIUseInventory(u, homeX, homeY)
                            set issued = IssuePointOrder(u, "move", homeX, homeY)
                            if issued then
                                set udg_AIMetricRetreatOrders[i] = udg_AIMetricRetreatOrders[i] + 1
                            endif
                        elseif udg_AIDiff >= 3 and localEnemyCount >= localAllyCount + 2 and (hpPct < 0.55 or localEnemyCount >= localAllyCount * 2) and (GetUnitCurrentOrder(u) == 0 or GetUnitCurrentOrder(u) == attackOrder) then
                            set issued = IssuePointOrder(u, "move", homeX, homeY)
                            if issued then
                                set udg_AIMetricRetreatOrders[i] = udg_AIMetricRetreatOrders[i] + 1
                            endif
                        // Wounded units kite away from their nearest currently visible threat.
                        elseif hpPct < 0.33 and udg_AIDiff >= 2 then
                            set dx = ux - GetUnitX(nearFoe)
                            set dy = uy - GetUnitY(nearFoe)
                            set dlen = SquareRoot(dx * dx + dy * dy)
                            if dlen < 1.0 then
                                set dlen = 1.0
                            endif
                            set issued = IssuePointOrder(u, "move", WM_ClampMapCoord(ux + (dx / dlen) * 265.0), WM_ClampMapCoord(uy + (dy / dlen) * 265.0))
                            if issued then
                                set udg_AIMetricRetreatOrders[i] = udg_AIMetricRetreatOrders[i] + 1
                            endif
                        // Hero spell evaluation uses visible clusters and ability-specific targets.
                        elseif IsUnitType(u, UNIT_TYPE_HERO) then
                            if weakFoe != null then
                                call WM_AICastCustomHeroCombo(u, weakFoe)
                            else
                                call WM_AICastCustomHeroCombo(u, nearFoe)
                            endif
                        // Equal-or-better local numbers focus a finishable target as a group.
                        elseif weakFoe != null and localAllyCount >= localEnemyCount and ((udg_AIDiff >= 4 and lowestPct < 0.58) or (udg_AIDiff >= 3 and lowestPct < 0.38)) and (GetUnitCurrentOrder(u) == 0 or GetUnitCurrentOrder(u) == attackOrder) then
                            set issued = IssueTargetOrder(u, "attack", weakFoe)
                            if issued then
                                set udg_AIMetricFocusOrders[i] = udg_AIMetricFocusOrders[i] + 1
                            endif
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
    set allyUnit = null
    set weakFoe = null
    set nearFoe = null
endfunction

// ---------------------------------------------------------------------------
// Custom-faction CPU commander: the generated JASS macro is authoritative for
// factions 5..8; classic races retain their native melee AI. The fallback uses
// real worker build orders and guarded production, not free unit spawns.
// ---------------------------------------------------------------------------
function WM_CountOwnedType takes player p, integer rawcode returns integer
    local unit u = null
    local integer count = 0
    call GroupClear(udg_TempGroupB)
    call GroupEnumUnitsOfPlayer(udg_TempGroupB, p, null)
    loop
        set u = FirstOfGroup(udg_TempGroupB)
        exitwhen u == null
        call GroupRemoveUnit(udg_TempGroupB, u)
        if GetUnitTypeId(u) == rawcode and GetWidgetLife(u) > 0.405 then
            set count = count + 1
        endif
    endloop
    set u = null
    return count
endfunction

function WM_CountLivingHeroes takes player p returns integer
    local unit u = null
    local integer total = 0
    call GroupClear(udg_TempGroupB)
    call GroupEnumUnitsOfPlayer(udg_TempGroupB, p, null)
    loop
        set u = FirstOfGroup(udg_TempGroupB)
        exitwhen u == null
        call GroupRemoveUnit(udg_TempGroupB, u)
        if GetWidgetLife(u) > 0.405 and IsUnitType(u, UNIT_TYPE_HERO) then
            set total = total + 1
        endif
    endloop
    set u = null
    return total
endfunction

function WM_AITryBuild takes unit worker, integer rawcode, real sx, real sy, integer slot returns boolean
    local integer attempt = 0
    local real baseAngle = Atan2(sy, sx)
    local real angle = 0.0
    local real radius = 820.0
    local real bx = 0.0
    local real by = 0.0
    local real dx = 0.0
    local real dy = 0.0
    local real mineD = 99999999.0
    local unit mine = WM_FindNearestGoldMine(sx, sy)
    if worker == null then
        set mine = null
        return false
    endif
    // Orbit the base but avoid the nearest gold mine; only accepted build orders count.
    loop
        exitwhen attempt >= 12
        set angle = baseAngle + 0.392699 + I2R(slot + attempt) * 0.785398
        set radius = 820.0 + I2R(attempt / 4) * 95.0
        set bx = WM_ClampMapCoord(sx + Cos(angle) * radius)
        set by = WM_ClampMapCoord(sy + Sin(angle) * radius)
        set mineD = 99999999.0
        if mine != null then
            set dx = bx - GetUnitX(mine)
            set dy = by - GetUnitY(mine)
            set mineD = dx * dx + dy * dy
        endif
        if mineD >= 600.0 * 600.0 and not IsTerrainPathable(bx, by, PATHING_TYPE_BUILDABILITY) then
            if IssueBuildOrderById(worker, rawcode, bx, by) then
                set worker = null
                set mine = null
                return true
            endif
        endif
        set attempt = attempt + 1
    endloop
    set worker = null
    set mine = null
    return false
endfunction

function WM_AIFindVisibleNaturalMine takes player p, real sx, real sy returns unit
    local unit u = null
    local unit nearby = null
    local unit best = null
    local integer rawcode = 0
    local real dx = 0.0
    local real dy = 0.0
    local real distSq = 0.0
    local real bestDistSq = 99999999.0
    local boolean occupied = false
    call GroupClear(udg_TempGroupB)
    call GroupEnumUnitsInRange(udg_TempGroupB, sx, sy, 7000.0, null)
    loop
        set u = FirstOfGroup(udg_TempGroupB)
        exitwhen u == null
        call GroupRemoveUnit(udg_TempGroupB, u)
        if GetUnitTypeId(u) == 'ngol' and GetResourceAmount(u) > 2000 and IsUnitVisible(u, p) then
            set dx = GetUnitX(u) - sx
            set dy = GetUnitY(u) - sy
            set distSq = dx * dx + dy * dy
            if distSq > 4840000.0 and distSq < 49000000.0 and distSq < bestDistSq then
                set occupied = false
                call GroupClear(udg_TempGroupA)
                call GroupEnumUnitsInRange(udg_TempGroupA, GetUnitX(u), GetUnitY(u), 1550.0, null)
                loop
                    set nearby = FirstOfGroup(udg_TempGroupA)
                    exitwhen nearby == null or occupied
                    call GroupRemoveUnit(udg_TempGroupA, nearby)
                    set rawcode = GetUnitTypeId(nearby)
                    if GetWidgetLife(nearby) > 0.405 and IsUnitType(nearby, UNIT_TYPE_STRUCTURE) and IsUnitVisible(nearby, p) and WM_AIIsTownHallRawcode(rawcode) then
                        set occupied = true
                    endif
                endloop
                if not occupied then
                    set best = u
                    set bestDistSq = distSq
                endif
            endif
        endif
    endloop
    set nearby = null
    set u = null
    return best
endfunction

function WM_AITryBuildAtPoint takes unit worker, integer rawcode, real sx, real sy, real mineX, real mineY returns boolean
    local integer attempt = 0
    local real baseAngle = Atan2(sy - mineY, sx - mineX)
    local real angle = 0.0
    local real radius = 820.0
    local real bx = 0.0
    local real by = 0.0
    local real dx = 0.0
    local real dy = 0.0
    if worker == null then
        return false
    endif
    loop
        exitwhen attempt >= 16
        set angle = baseAngle + I2R(attempt) * 0.392699
        if attempt >= 8 then
            set radius = 980.0
        else
            set radius = 790.0
        endif
        set bx = WM_ClampMapCoord(mineX + Cos(angle) * radius)
        set by = WM_ClampMapCoord(mineY + Sin(angle) * radius)
        set dx = bx - mineX
        set dy = by - mineY
        if dx * dx + dy * dy >= 610000.0 and not IsTerrainPathable(bx, by, PATHING_TYPE_BUILDABILITY) then
            if IssueBuildOrderById(worker, rawcode, bx, by) then
                set worker = null
                return true
            endif
        endif
        set attempt = attempt + 1
    endloop
    set worker = null
    return false
endfunction

function WM_AIQueueExpansion takes player p, unit worker, integer hallRawcode, real sx, real sy, real mineX, real mineY returns boolean
    local integer pid = GetPlayerId(p)
    if pid < 0 or pid >= 8 or worker == null or hallRawcode == 0 or udg_AIFallbackPendingRaw[pid] != 0 then
        set p = null
        set worker = null
        return false
    endif
    if WM_AITryBuildAtPoint(worker, hallRawcode, sx, sy, mineX, mineY) then
        set udg_AIFallbackPendingRaw[pid] = hallRawcode
        set udg_AIFallbackPendingUntil[pid] = udg_MatchSeconds + 240
        set udg_AIExpansionPending[pid] = true
        set udg_AIExpansionActive[pid] = false
        set udg_AIExpansionX[pid] = mineX
        set udg_AIExpansionY[pid] = mineY
        set udg_AIExpansionOrderAt[pid] = udg_MatchSeconds
        set udg_AIMetricExpansionOrders[pid] = udg_AIMetricExpansionOrders[pid] + 1
        set p = null
        set worker = null
        return true
    endif
    set p = null
    set worker = null
    return false
endfunction

function WM_AIQueueFallbackBuild takes player p, unit worker, integer rawcode, real sx, real sy, integer slot returns boolean
    local integer pid = GetPlayerId(p)
    if pid < 0 or pid >= 8 or rawcode == 0 or worker == null then
        return false
    endif
    if udg_AIFallbackPendingRaw[pid] != 0 then
        return false
    endif
    if WM_AITryBuild(worker, rawcode, sx, sy, slot) then
        set udg_AIFallbackPendingRaw[pid] = rawcode
        set udg_AIFallbackPendingUntil[pid] = udg_MatchSeconds + 90
        return true
    endif
    return false
endfunction

function WM_AIFallbackBuild takes player p, integer faction, unit worker, real sx, real sy returns boolean
    // Distinct build orders adapt standard-race ideas to each custom tech tree:
    // Naga = fast Altar/Spawning-Grounds pressure; Sunfury = fast Altar then Archer
    // production; Voidborn = Fiend-like early Rift Gate before its delayed Altar;
    // Runeforged = early Altar + low-cost tech path inspired by Orc fast-tech.
    if faction == 5 then
        if WM_CountOwnedType(p, 'nnfm') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'nnfm', sx, sy, 0)
        elseif WM_CountOwnedType(p, 'nnad') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'nnad', sx, sy, 1)
        elseif WM_CountOwnedType(p, 'nnsg') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'nnsg', sx, sy, 2)
        elseif WM_CountOwnedType(p, 'n004') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'n004', sx, sy, 3)
        elseif WM_CountOwnedType(p, 'n003') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'n003', sx, sy, 4)
        elseif WM_CountOwnedType(p, 'nntg') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'nntg', sx, sy, 5)
        elseif WM_CountOwnedType(p, 'n001') > 0 and WM_CountOwnedType(p, 'nnsa') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'nnsa', sx, sy, 6)
        elseif WM_CountOwnedType(p, 'n001') > 0 and WM_CountOwnedType(p, 'n005') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'n005', sx, sy, 7)
        endif
    elseif faction == 6 then
        if WM_CountOwnedType(p, 'nefm') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'nefm', sx, sy, 0)
        elseif WM_CountOwnedType(p, 'h004') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'h004', sx, sy, 1)
        elseif WM_CountOwnedType(p, 'h007') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'h007', sx, sy, 2)
        elseif WM_CountOwnedType(p, 'h011') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'h011', sx, sy, 3)
        elseif WM_CountOwnedType(p, 'h010') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'h010', sx, sy, 4)
        elseif WM_CountOwnedType(p, 'h005') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'h005', sx, sy, 5)
        elseif WM_CountOwnedType(p, 'negt') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'negt', sx, sy, 6)
        elseif WM_CountOwnedType(p, 'h002') > 0 and WM_CountOwnedType(p, 'nheb') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'nheb', sx, sy, 7)
        elseif WM_CountOwnedType(p, 'h002') > 0 and WM_CountOwnedType(p, 'h008') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'h008', sx, sy, 1)
        elseif WM_CountOwnedType(p, 'h002') > 0 and WM_CountOwnedType(p, 'h009') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'h009', sx, sy, 2)
        endif
    elseif faction == 7 then
        if WM_CountOwnedType(p, 'v004') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'v004', sx, sy, 0)
        elseif WM_CountOwnedType(p, 'v005') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'v005', sx, sy, 1)
        elseif WM_CountOwnedType(p, 'v007') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'v007', sx, sy, 2)
        elseif WM_CountOwnedType(p, 'v006') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'v006', sx, sy, 3)
        elseif WM_CountOwnedType(p, 'v008') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'v008', sx, sy, 4)
        elseif WM_CountOwnedType(p, 'v009') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'v009', sx, sy, 5)
        elseif WM_CountOwnedType(p, 'v002') > 0 and WM_CountOwnedType(p, 'v018') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'v018', sx, sy, 6)
        elseif WM_CountOwnedType(p, 'v002') > 0 and WM_CountOwnedType(p, 'v019') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 'v019', sx, sy, 7)
        endif
    elseif faction == 8 then
        if WM_CountOwnedType(p, 't007') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 't007', sx, sy, 0)
        elseif WM_CountOwnedType(p, 't004') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 't004', sx, sy, 1)
        elseif WM_CountOwnedType(p, 't005') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 't005', sx, sy, 2)
        elseif WM_CountOwnedType(p, 't006') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 't006', sx, sy, 3)
        elseif WM_CountOwnedType(p, 't008') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 't008', sx, sy, 4)
        elseif WM_CountOwnedType(p, 't009') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 't009', sx, sy, 5)
        elseif WM_CountOwnedType(p, 't002') > 0 and WM_CountOwnedType(p, 't018') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 't018', sx, sy, 6)
        elseif WM_CountOwnedType(p, 't002') > 0 and WM_CountOwnedType(p, 't019') == 0 then
            return WM_AIQueueFallbackBuild(p, worker, 't019', sx, sy, 7)
        endif
    endif
    set p = null
    set worker = null
    return false
endfunction

function WM_AIFallbackSupply takes player p, integer faction, unit worker, real sx, real sy returns boolean
    local integer supplyId = 0
    if faction == 5 then
        set supplyId = 'nnfm'
    elseif faction == 6 then
        set supplyId = 'nefm'
    elseif faction == 7 then
        set supplyId = 'v004'
    elseif faction == 8 then
        set supplyId = 't004'
    endif
    if supplyId != 0 then
        return WM_AIQueueFallbackBuild(p, worker, supplyId, sx, sy, 9)
    endif
    return false
endfunction

function WM_OnAIFallbackBuildFinished takes nothing returns boolean
    local unit built = GetTriggerUnit()
    local player owner = null
    local integer pid = -1
    if built != null then
        set owner = GetOwningPlayer(built)
        set pid = GetPlayerId(owner)
        if pid >= 0 and pid < 8 and GetUnitTypeId(built) == udg_AIFallbackPendingRaw[pid] then
            set udg_AIFallbackPendingRaw[pid] = 0
            set udg_AIFallbackPendingUntil[pid] = 0
            if udg_AIExpansionPending[pid] then
                set udg_AIExpansionPending[pid] = false
                set udg_AIExpansionActive[pid] = true
                set udg_AIExpansionX[pid] = GetUnitX(built)
                set udg_AIExpansionY[pid] = GetUnitY(built)
            endif
        endif
    endif
    set built = null
    set owner = null
    return false
endfunction

function WM_AIChooseMarchObjective takes player p, integer pid, integer armyCount, real homeX, real homeY, unit visibleEnemy returns nothing
    local integer j = 0
    local integer slot = 0
    local integer bestSlot = -1
    local integer age = 0
    local integer bestAge = 999999
    local unit u = null
    local real enemyX = 0.0
    local real enemyY = 0.0
    local real dx = 0.0
    local real dy = 0.0
    local real distSq = 0.0
    local real bestDistSq = 99999999.0
    local real creepX = 0.0
    local real creepY = 0.0
    local real startX = 0.0
    local real startY = 0.0
    local boolean decided = false
    local boolean shrineAllied = false

    set udg_AIObjectiveX[pid] = 0.0
    set udg_AIObjectiveY[pid] = 0.0
    set udg_AIObjectiveMode[pid] = 2

    if visibleEnemy != null then
        set enemyX = GetUnitX(visibleEnemy)
        set enemyY = GetUnitY(visibleEnemy)
        if udg_AIExpansionActive[pid] then
            set dx = enemyX - udg_AIExpansionX[pid]
            set dy = enemyY - udg_AIExpansionY[pid]
            if dx * dx + dy * dy < 2250000.0 then
                set udg_AIObjectiveX[pid] = enemyX
                set udg_AIObjectiveY[pid] = enemyY
                set udg_AIObjectiveMode[pid] = 4
                set decided = true
            endif
        endif
        if not decided then
            set dx = enemyX - homeX
            set dy = enemyY - homeY
            if dx * dx + dy * dy < 1960000.0 then
                set udg_AIObjectiveX[pid] = enemyX
                set udg_AIObjectiveY[pid] = enemyY
                set udg_AIObjectiveMode[pid] = 4
                set decided = true
            elseif armyCount >= 8 and udg_MatchSeconds >= 100 then
                set udg_AIObjectiveX[pid] = enemyX
                set udg_AIObjectiveY[pid] = enemyY
                set udg_AIObjectiveMode[pid] = 3
                set decided = true
            endif
        endif
    endif

    // A live expansion is a temporary rally/guard objective, not a source of
    // hidden enemy data. The builder's known site is recorded when the order lands.
    if not decided and udg_AIExpansionPending[pid] and armyCount >= 8 and udg_MatchSeconds - udg_AIExpansionOrderAt[pid] <= 240 then
        set udg_AIObjectiveX[pid] = udg_AIExpansionX[pid]
        set udg_AIObjectiveY[pid] = udg_AIExpansionY[pid]
        set udg_AIObjectiveMode[pid] = 6
        set decided = true
    endif

    // Early creep choice uses only currently visible neutral units.
    if not decided and visibleEnemy == null and udg_MatchSeconds < 240 and armyCount < 10 then
        set bestDistSq = 27000000.0
        call GroupClear(udg_TempGroupB)
        call GroupEnumUnitsOfPlayer(udg_TempGroupB, Player(PLAYER_NEUTRAL_AGGRESSIVE), null)
        loop
            set u = FirstOfGroup(udg_TempGroupB)
            exitwhen u == null
            call GroupRemoveUnit(udg_TempGroupB, u)
            if GetWidgetLife(u) > 0.405 and IsUnitVisible(u, p) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) then
                set dx = GetUnitX(u) - homeX
                set dy = GetUnitY(u) - homeY
                set distSq = dx * dx + dy * dy
                if distSq < bestDistSq then
                    set bestDistSq = distSq
                    set creepX = GetUnitX(u)
                    set creepY = GetUnitY(u)
                endif
            endif
        endloop
        if bestDistSq < 27000000.0 then
            set udg_AIObjectiveX[pid] = creepX
            set udg_AIObjectiveY[pid] = creepY
            set udg_AIObjectiveMode[pid] = 1
            set decided = true
        endif
    endif

    // Contest the Shrine unless it is held by this AI's actual alliance.
    if not decided then
        if udg_ShrineControllerPid >= 0 and udg_ShrineControllerPid < 8 then
            if Player(udg_ShrineControllerPid) == p or IsPlayerAlly(p, Player(udg_ShrineControllerPid)) then
                set shrineAllied = true
            endif
        endif
        if not shrineAllied then
            set udg_AIObjectiveX[pid] = 0.0
            set udg_AIObjectiveY[pid] = 0.0
            set udg_AIObjectiveMode[pid] = 2
            set decided = true
        endif
    endif

    // Revisit a recent last-seen location, never a hidden unit's current position.
    if not decided then
        set j = 0
        loop
            exitwhen j >= 8
            if j != pid and GetPlayerSlotState(Player(j)) == PLAYER_SLOT_STATE_PLAYING and IsPlayerEnemy(p, Player(j)) then
                set slot = pid * 8 + j
                set age = udg_MatchSeconds - udg_AILastSeenAt[slot]
                if udg_AILastSeenAt[slot] > 0 and age >= 0 and age <= 120 and age < bestAge then
                    set bestAge = age
                    set bestSlot = slot
                endif
            endif
            set j = j + 1
        endloop
        if bestSlot >= 0 and armyCount >= 8 then
            set udg_AIObjectiveX[pid] = udg_AILastSeenX[bestSlot]
            set udg_AIObjectiveY[pid] = udg_AILastSeenY[bestSlot]
            set udg_AIObjectiveMode[pid] = 5
            set decided = true
        endif
    endif

    // Public start locations are a fair late-game scouting prior when no recent
    // contact exists; the AI still has to see the base before targeting its units.
    if not decided and armyCount >= 8 and udg_MatchSeconds >= 180 then
        set bestDistSq = 99999999.0
        set j = 0
        loop
            exitwhen j >= 8
            if GetPlayerSlotState(Player(j)) == PLAYER_SLOT_STATE_PLAYING and IsPlayerEnemy(p, Player(j)) then
                set startX = GetStartLocationX(GetPlayerStartLocation(Player(j)))
                set startY = GetStartLocationY(GetPlayerStartLocation(Player(j)))
                set dx = startX - homeX
                set dy = startY - homeY
                set distSq = dx * dx + dy * dy
                if distSq < bestDistSq then
                    set bestDistSq = distSq
                    set udg_AIObjectiveX[pid] = startX
                    set udg_AIObjectiveY[pid] = startY
                endif
            endif
            set j = j + 1
        endloop
        if bestDistSq < 99999999.0 then
            set udg_AIObjectiveMode[pid] = 5
            set decided = true
        endif
    endif

    if not decided then
        set udg_AIObjectiveX[pid] = 0.0
        set udg_AIObjectiveY[pid] = 0.0
        set udg_AIObjectiveMode[pid] = 2
    endif
    set u = null
endfunction

function WM_AIObjectiveLabel takes integer mode returns string
    if mode == 1 then
        return "creep"
    elseif mode == 2 then
        return "shrine"
    elseif mode == 3 then
        return "attack"
    elseif mode == 4 then
        return "defend"
    elseif mode == 5 then
        return "scout"
    elseif mode == 6 then
        return "expand"
    endif
    return "rally"
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
    local integer goldWorkerCount = 0
    local integer expansionWorkerCount = 0
    local integer heroCount = 0
    local integer desiredWorkers = 0
    local integer workerId = 0
    local integer tier = 0
    local integer productionId = 0
    local integer productionWait = 0
    local integer unitFood = 0
    local integer weaponUpgrade = 0
    local integer armorUpgrade = 0
    local integer weaponLevel = 0
    local integer armorLevel = 0
    local integer techOrder = 0
    local integer techWait = 125
    local integer j = 0
    local integer rawcode = 0
    local integer hallCount = 0
    local integer expansionHallId = 0
    local integer enemyAirCount = 0
    local integer enemyCasterCount = 0
    local integer enemyRangedCount = 0
    local integer enemyTierCount = 0
    local integer attackOrder = 0
    local integer currentOrder = 0
    local integer ecoBonusG = 0
    local integer ecoBonusL = 0
    local unit u = null
    local unit hall = null
    local unit altar = null
    local unit rax = null
    local unit sanctum = null
    local unit heavyBay = null
    local unit airBay = null
    local unit armory = null
    local unit idleWorker = null
    local unit aiBuilder = null
    local unit mine = null
    local unit expansionMine = null
    local unit targetEnemy = null
    local destructable tree = null
    local rect treeRect = null
    local real sx = 0.0
    local real sy = 0.0
    local real tx = 0.0
    local real ty = 0.0
    local real dx = 0.0
    local real dy = 0.0
    local real candidateDist = 0.0
    local real targetDist = 99999999.0
    local boolean issued = false
    local boolean didBuild = false
    local boolean productionAdapted = false
    local boolean expansionSafe = true
    local boolean objectiveChanged = false

    // Small, disclosed custom-race support only; tactical quality does most of the scaling.
    // The macro runs every 4s: Veteran +30g/+15l, Grandmaster +60g/+30l,
    // Mythic +105g/+45l per minute. Novice receives no economic assistance.
    if udg_AIDiff == 2 then
        set ecoBonusG = 2
        set ecoBonusL = 1
    elseif udg_AIDiff == 3 then
        set ecoBonusG = 4
        set ecoBonusL = 2
    elseif udg_AIDiff >= 4 then
        set ecoBonusG = 7
        set ecoBonusL = 3
    endif
    set attackOrder = OrderId("attack")

    loop
        exitwhen i >= 8
        set p = Player(i)
        if GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING and GetPlayerController(p) == MAP_CONTROL_COMPUTER then
            set f = udg_PlayerFaction[i]
            if f >= 5 and ecoBonusG > 0 then
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
            set airBay = null
            set armory = null
            set idleWorker = null
            set aiBuilder = null
            set mine = null
            set tree = null
            set armyCount = 0
            set workerCount = 0
            set goldWorkerCount = 0
            set expansionWorkerCount = 0
            set heroCount = 0
            set hallCount = 0
            set expansionMine = null
            set targetEnemy = null
            set udg_AIObjectiveMode[i] = 0

            if f >= 5 then
                set mine = WM_FindNearestGoldMine(sx, sy)
                if udg_AIExpansionActive[i] then
                    set expansionMine = WM_FindNearestGoldMine(udg_AIExpansionX[i], udg_AIExpansionY[i])
                endif
                set udg_SearchX = sx
                set udg_SearchY = sy
                set udg_NearestTree = null
                set udg_NearestTreeDist = 99999999.0
                set treeRect = Rect(sx - 1350.0, sy - 1350.0, sx + 1350.0, sy + 1350.0)
                call EnumDestructablesInRect(treeRect, null, function WM_EnumNearestTree)
                call RemoveRect(treeRect)
                set treeRect = null
                set tree = udg_NearestTree
            endif

            call GroupClear(udg_TempGroupA)
            call GroupEnumUnitsOfPlayer(udg_TempGroupA, p, null)
            loop
                set u = FirstOfGroup(udg_TempGroupA)
                exitwhen u == null
                call GroupRemoveUnit(udg_TempGroupA, u)
                if GetWidgetLife(u) > 0.405 then
                    set rawcode = GetUnitTypeId(u)
                    if IsUnitType(u, UNIT_TYPE_PEON) or WM_IsCustomAIWorker(f, rawcode) then
                        set workerCount = workerCount + 1
                        if aiBuilder == null then
                            set aiBuilder = u
                        endif
                        if idleWorker == null and GetUnitCurrentOrder(u) == 0 then
                            set idleWorker = u
                        endif
                        if f >= 5 and mine != null and GetUnitCurrentOrder(u) != 0 then
                            set dx = GetUnitX(u) - GetUnitX(mine)
                            set dy = GetUnitY(u) - GetUnitY(mine)
                            if dx * dx + dy * dy < 390000.0 then
                                set goldWorkerCount = goldWorkerCount + 1
                            endif
                        endif
                        if f >= 5 and expansionMine != null and GetUnitCurrentOrder(u) != 0 then
                            set dx = GetUnitX(u) - GetUnitX(expansionMine)
                            set dy = GetUnitY(u) - GetUnitY(expansionMine)
                            if dx * dx + dy * dy < 390000.0 then
                                set expansionWorkerCount = expansionWorkerCount + 1
                            endif
                        endif
                    elseif IsUnitType(u, UNIT_TYPE_HERO) then
                        set armyCount = armyCount + 1
                        set heroCount = heroCount + 1
                        if f >= 5 then
                            call WM_AIChooseCustomHeroSkill(u, f)
                        endif
                    elseif IsUnitType(u, UNIT_TYPE_STRUCTURE) then
                        if f >= 5 and WM_AIIsTownHallRawcode(rawcode) then
                            set hallCount = hallCount + 1
                        endif
                        if f == 5 then
                            if rawcode == 'nntt' or rawcode == 'n001' or rawcode == 'n002' then
                                set hall = u
                            elseif rawcode == 'nnad' then
                                set altar = u
                            elseif rawcode == 'nnsg' then
                                set rax = u
                            elseif rawcode == 'nnsa' then
                                set sanctum = u
                            elseif rawcode == 'n005' then
                                set heavyBay = u
                            elseif rawcode == 'n004' then
                                set armory = u
                            endif
                        elseif f == 6 then
                            if rawcode == 'h001' or rawcode == 'h002' or rawcode == 'h003' then
                                set hall = u
                            elseif rawcode == 'h004' then
                                set altar = u
                            elseif rawcode == 'h007' then
                                set rax = u
                            elseif rawcode == 'nheb' then
                                set sanctum = u
                            elseif rawcode == 'h008' then
                                set heavyBay = u
                            elseif rawcode == 'h009' then
                                set airBay = u
                            elseif rawcode == 'h010' then
                                set armory = u
                            endif
                        elseif f == 7 then
                            if rawcode == 'v001' or rawcode == 'v002' or rawcode == 'v003' then
                                set hall = u
                            elseif rawcode == 'v007' then
                                set altar = u
                            elseif rawcode == 'v005' then
                                set rax = u
                            elseif rawcode == 'v018' then
                                set sanctum = u
                            elseif rawcode == 'v019' then
                                set heavyBay = u
                            elseif rawcode == 'v006' then
                                set armory = u
                            endif
                        elseif f == 8 then
                            if rawcode == 't001' or rawcode == 't002' or rawcode == 't003' then
                                set hall = u
                            elseif rawcode == 't007' then
                                set altar = u
                            elseif rawcode == 't005' then
                                set rax = u
                            elseif rawcode == 't018' then
                                set sanctum = u
                            elseif rawcode == 't019' then
                                set heavyBay = u
                            elseif rawcode == 't006' then
                                set armory = u
                            endif
                        endif
                    else
                        set armyCount = armyCount + 1
                    endif
                endif
            endloop

            set targetEnemy = null
            set enemyAirCount = 0
            set enemyCasterCount = 0
            set enemyRangedCount = 0
            set enemyTierCount = 0
            if f >= 5 then
                set targetEnemy = WM_AIRefreshEnemyIntel(p, i, sx, sy)
                set enemyAirCount = udg_AIEnemyAirCount[i]
                set enemyCasterCount = udg_AIEnemyCasterCount[i]
                set enemyRangedCount = udg_AIEnemyRangedCount[i]
                set enemyTierCount = udg_AIEnemyTierCount[i]
                if hallCount < 2 then
                    set udg_AIExpansionActive[i] = false
                    set expansionMine = null
                endif
            endif

            if f >= 5 then
                // A timeout is a recovery path if a build order is interrupted or the
                // client does not deliver CONSTRUCT_FINISH; normal completion clears it.
                if udg_AIFallbackPendingRaw[i] != 0 and udg_MatchSeconds >= udg_AIFallbackPendingUntil[i] then
                    set udg_AIFallbackPendingRaw[i] = 0
                    set udg_AIFallbackPendingUntil[i] = 0
                    if udg_AIExpansionPending[i] then
                        set udg_AIExpansionPending[i] = false
                    endif
                endif
                if idleWorker != null then
                    set aiBuilder = idleWorker
                endif

                if aiBuilder != null and udg_AIFallbackPendingRaw[i] == 0 then
                    if foodCap < 90 and foodUsed + 2 >= foodCap then
                        set didBuild = WM_AIFallbackSupply(p, f, aiBuilder, sx, sy)
                    else
                        set didBuild = WM_AIFallbackBuild(p, f, aiBuilder, sx, sy)
                    endif
                    if didBuild then
                        set idleWorker = null
                    endif
                endif

                // Keep roughly three workers on Gold; direct all other idle custom workers
                // to a nearby tree. nmpe/nhew/v010/t010 are recognized explicitly above.
                if idleWorker != null then
                    if expansionMine != null and expansionWorkerCount < 3 then
                        call IssueTargetOrder(idleWorker, "harvest", expansionMine)
                    elseif goldWorkerCount < 3 and mine != null then
                        call IssueTargetOrder(idleWorker, "harvest", mine)
                    elseif tree != null then
                        call IssueTargetOrder(idleWorker, "harvest", tree)
                    endif
                endif

                if f == 5 then
                    set workerId = 'nmpe'
                    set desiredWorkers = 13
                elseif f == 6 then
                    set workerId = 'nhew'
                    set desiredWorkers = 14
                elseif f == 7 then
                    set workerId = 'v010'
                    set desiredWorkers = 12
                else
                    set workerId = 't010'
                    set desiredWorkers = 11
                endif
                if expansionMine != null then
                    set desiredWorkers = desiredWorkers + 4
                endif
                if hall != null and GetUnitCurrentOrder(hall) == 0 and udg_MatchSeconds >= udg_AINextWorkerOrderAt[i] and workerCount < desiredWorkers and foodUsed + 1 < foodCap and gold >= 75 then
                    set issued = IssueImmediateOrderById(hall, workerId)
                    if issued then
                        set udg_AINextWorkerOrderAt[i] = udg_MatchSeconds + 16
                    endif
                endif

                // Custom-tier number drives building, hero, army, and research availability.
                set tier = 0
                if f == 5 then
                    if WM_CountOwnedType(p, 'n002') > 0 then
                        set tier = 3
                    elseif WM_CountOwnedType(p, 'n001') > 0 then
                        set tier = 2
                    elseif WM_CountOwnedType(p, 'nntt') > 0 then
                        set tier = 1
                    endif
                elseif f == 6 then
                    if WM_CountOwnedType(p, 'h003') > 0 then
                        set tier = 3
                    elseif WM_CountOwnedType(p, 'h002') > 0 then
                        set tier = 2
                    elseif WM_CountOwnedType(p, 'h001') > 0 then
                        set tier = 1
                    endif
                elseif f == 7 then
                    if WM_CountOwnedType(p, 'v003') > 0 then
                        set tier = 3
                    elseif WM_CountOwnedType(p, 'v002') > 0 then
                        set tier = 2
                    elseif WM_CountOwnedType(p, 'v001') > 0 then
                        set tier = 1
                    endif
                elseif f == 8 then
                    if WM_CountOwnedType(p, 't003') > 0 then
                        set tier = 3
                    elseif WM_CountOwnedType(p, 't002') > 0 then
                        set tier = 2
                    elseif WM_CountOwnedType(p, 't001') > 0 then
                        set tier = 1
                    endif
                endif

                // Sequential town-hall tech: prerequisites + idle state + cooldown prevent
                // a second command from replacing the first while an upgrade is running.
                set techOrder = 0
                if f == 5 then
                    if tier == 1 and WM_CountOwnedType(p, 'nnad') > 0 and WM_CountOwnedType(p, 'nnsg') > 0 then
                        set techOrder = 'n001'
                    elseif tier == 2 and WM_CountOwnedType(p, 'nnsa') > 0 and WM_CountOwnedType(p, 'n005') > 0 then
                        set techOrder = 'n002'
                    endif
                elseif f == 6 then
                    if tier == 1 and WM_CountOwnedType(p, 'h004') > 0 and WM_CountOwnedType(p, 'h007') > 0 and WM_CountOwnedType(p, 'h010') > 0 then
                        set techOrder = 'h002'
                    elseif tier == 2 and WM_CountOwnedType(p, 'nheb') > 0 and WM_CountOwnedType(p, 'h008') > 0 then
                        set techOrder = 'h003'
                    endif
                elseif f == 7 then
                    if tier == 1 and WM_CountOwnedType(p, 'v007') > 0 and WM_CountOwnedType(p, 'v005') > 0 and WM_CountOwnedType(p, 'v006') > 0 then
                        set techOrder = 'v002'
                    elseif tier == 2 and WM_CountOwnedType(p, 'v018') > 0 and WM_CountOwnedType(p, 'v019') > 0 then
                        set techOrder = 'v003'
                    endif
                elseif f == 8 then
                    if tier == 1 and WM_CountOwnedType(p, 't007') > 0 and WM_CountOwnedType(p, 't005') > 0 and WM_CountOwnedType(p, 't006') > 0 then
                        set techOrder = 't002'
                    elseif tier == 2 and WM_CountOwnedType(p, 't018') > 0 and WM_CountOwnedType(p, 't019') > 0 then
                        set techOrder = 't003'
                    endif
                endif
                set techWait = 125
                if enemyTierCount > tier and udg_AIDiff >= 3 then
                    set techWait = 70
                elseif enemyTierCount > tier then
                    set techWait = 95
                elseif udg_AIDiff >= 4 then
                    set techWait = 105
                endif
                if hall != null and techOrder != 0 and GetUnitCurrentOrder(hall) == 0 and udg_MatchSeconds >= udg_AINextHallOrderAt[i] and gold >= 340 and lum >= 190 then
                    set issued = IssueImmediateOrderById(hall, techOrder)
                    if issued then
                        set udg_AINextHallOrderAt[i] = udg_MatchSeconds + techWait
                    endif
                endif

                // A fair natural expansion needs current vision, a completed T3 main,
                // a healthy field army, safe home-front intel, and a large resource reserve.
                set expansionHallId = 0
                if f == 5 then
                    set expansionHallId = 'nntt'
                elseif f == 6 then
                    set expansionHallId = 'h001'
                elseif f == 7 then
                    set expansionHallId = 'v001'
                elseif f == 8 then
                    set expansionHallId = 't001'
                endif
                set expansionSafe = true
                if targetEnemy != null then
                    set dx = GetUnitX(targetEnemy) - sx
                    set dy = GetUnitY(targetEnemy) - sy
                    if dx * dx + dy * dy < 6250000.0 then
                        set expansionSafe = false
                    endif
                endif
                if expansionHallId != 0 and hallCount == 1 and tier >= 3 and armyCount >= 8 and workerCount >= 9 and udg_MatchSeconds >= 300 and udg_MatchSeconds >= udg_AINextExpansionTryAt[i] and not udg_AIExpansionPending[i] and udg_AIFallbackPendingRaw[i] == 0 and expansionSafe and hall != null and GetUnitCurrentOrder(hall) == 0 and GetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD) >= 850 and GetPlayerState(p, PLAYER_STATE_RESOURCE_LUMBER) >= 320 then
                    set expansionMine = WM_AIFindVisibleNaturalMine(p, sx, sy)
                    set udg_AINextExpansionTryAt[i] = udg_MatchSeconds + 24
                    if expansionMine != null then
                        set didBuild = WM_AIQueueExpansion(p, aiBuilder, expansionHallId, sx, sy, GetUnitX(expansionMine), GetUnitY(expansionMine))
                        if didBuild then
                            set aiBuilder = null
                            set idleWorker = null
                        endif
                    endif
                endif

                // One hero order per altar at a time; the third pick is delayed until Tier 3.
                if altar != null and GetUnitCurrentOrder(altar) == 0 and udg_MatchSeconds >= udg_AINextHeroOrderAt[i] and heroCount < 3 then
                    set productionId = 0
                    if f == 5 then
                        if WM_CountOwnedType(p, 'Hvsh') == 0 then
                            set productionId = 'Hvsh'
                        elseif tier >= 2 and WM_CountOwnedType(p, 'N004') == 0 then
                            set productionId = 'N004'
                        elseif tier >= 3 and WM_CountOwnedType(p, 'N001') == 0 then
                            set productionId = 'N001'
                        endif
                    elseif f == 6 then
                        if WM_CountOwnedType(p, 'Hkal') == 0 then
                            set productionId = 'Hkal'
                        elseif tier >= 2 and WM_CountOwnedType(p, 'Hvwd') == 0 then
                            set productionId = 'Hvwd'
                        elseif tier >= 3 and WM_CountOwnedType(p, 'Hlgr') == 0 then
                            set productionId = 'Hlgr'
                        endif
                    elseif f == 7 then
                        if WM_CountOwnedType(p, 'V001') == 0 then
                            set productionId = 'V001'
                        elseif tier >= 2 and WM_CountOwnedType(p, 'V002') == 0 then
                            set productionId = 'V002'
                        elseif tier >= 3 and WM_CountOwnedType(p, 'V003') == 0 then
                            set productionId = 'V003'
                        endif
                    elseif f == 8 then
                        if WM_CountOwnedType(p, 'T001') == 0 then
                            set productionId = 'T001'
                        elseif tier >= 2 and WM_CountOwnedType(p, 'T003') == 0 then
                            set productionId = 'T003'
                        elseif tier >= 3 and WM_CountOwnedType(p, 'T002') == 0 then
                            set productionId = 'T002'
                        endif
                    endif
                    if productionId != 0 and gold >= 425 and lum >= 100 then
                        set issued = IssueImmediateOrderById(altar, productionId)
                        if issued then
                            set udg_AINextHeroOrderAt[i] = udg_MatchSeconds + 58
                        endif
                    endif
                endif

                // Faction-specific equipment research: choose only one accepted order per tick.
                set weaponUpgrade = 0
                set armorUpgrade = 0
                if f == 5 then
                    set weaponUpgrade = 'Rnat'
                    set armorUpgrade = 'Rnam'
                elseif f == 6 then
                    set weaponUpgrade = 'Rhra'
                    set armorUpgrade = 'Rhar'
                elseif f == 7 then
                    set weaponUpgrade = 'R000'
                    set armorUpgrade = 'R001'
                elseif f == 8 then
                    set weaponUpgrade = 'R002'
                    set armorUpgrade = 'R003'
                endif
                if weaponUpgrade != 0 and armory != null and GetUnitCurrentOrder(armory) == 0 and udg_MatchSeconds >= udg_AINextUpgradeOrderAt[i] and tier >= 1 and gold >= 160 and lum >= 100 then
                    set weaponLevel = GetPlayerTechCount(p, weaponUpgrade, true)
                    set armorLevel = GetPlayerTechCount(p, armorUpgrade, true)
                    set productionId = 0
                    if weaponLevel < tier and (weaponLevel <= armorLevel or armorLevel >= tier) then
                        set productionId = weaponUpgrade
                    elseif armorLevel < tier then
                        set productionId = armorUpgrade
                    endif
                    if productionId != 0 then
                        set issued = IssueImmediateOrderById(armory, productionId)
                        if issued then
                            set udg_AINextUpgradeOrderAt[i] = udg_MatchSeconds + 42
                        endif
                    endif
                endif

                // District-specific unit mixes react to observed air/ranged pressure while
                // preserving each faction's baseline frontline and tech-gated roster.
                set productionId = 0
                set productionWait = 0
                set unitFood = 2
                set productionAdapted = false
                if rax != null and GetUnitCurrentOrder(rax) == 0 and udg_MatchSeconds >= udg_AINextRaxOrderAt[i] then
                    if f == 5 then
                        if enemyAirCount >= 2 and WM_CountOwnedType(p, 'nsnp') < WM_CountOwnedType(p, 'nnmg') + 3 then
                            set productionId = 'nsnp'
                            set unitFood = 3
                            set productionWait = 25
                            set productionAdapted = true
                        elseif enemyRangedCount >= 4 and tier >= 2 and WM_CountOwnedType(p, 'nmyr') < (armyCount / 4 + 2) then
                            set productionId = 'nmyr'
                            set unitFood = 4
                            set productionWait = 33
                            set productionAdapted = true
                        elseif tier >= 3 and WM_CountOwnedType(p, 'nnrg') < 1 then
                            set productionId = 'nnrg'
                            set unitFood = 5
                            set productionWait = 42
                        elseif tier >= 2 and WM_CountOwnedType(p, 'nmyr') < (armyCount / 5 + 1) then
                            set productionId = 'nmyr'
                            set unitFood = 4
                            set productionWait = 33
                        elseif WM_CountOwnedType(p, 'nsnp') < 2 or WM_CountOwnedType(p, 'nsnp') <= WM_CountOwnedType(p, 'nnmg') then
                            set productionId = 'nsnp'
                            set unitFood = 3
                            set productionWait = 25
                        else
                            set productionId = 'nnmg'
                            set productionWait = 19
                        endif
                    elseif f == 6 then
                        if enemyAirCount >= 2 and WM_CountOwnedType(p, 'nhea') < WM_CountOwnedType(p, 'hhes') + 3 then
                            set productionId = 'nhea'
                            set productionWait = 20
                            set productionAdapted = true
                        elseif enemyRangedCount >= 4 and WM_CountOwnedType(p, 'hhes') < WM_CountOwnedType(p, 'nhea') + 3 then
                            set productionId = 'hhes'
                            set productionWait = 20
                            set productionAdapted = true
                        elseif tier >= 3 and WM_CountOwnedType(p, 'hcth') < 1 then
                            set productionId = 'hcth'
                            set unitFood = 4
                            set productionWait = 38
                        elseif WM_CountOwnedType(p, 'nhea') < 2 or WM_CountOwnedType(p, 'nhea') <= WM_CountOwnedType(p, 'hhes') then
                            set productionId = 'nhea'
                            set productionWait = 20
                        else
                            set productionId = 'hhes'
                            set productionWait = 20
                        endif
                    elseif f == 7 then
                        if enemyAirCount >= 2 and WM_CountOwnedType(p, 'v012') < WM_CountOwnedType(p, 'v011') + 3 then
                            set productionId = 'v012'
                            set unitFood = 3
                            set productionWait = 25
                            set productionAdapted = true
                        elseif enemyRangedCount >= 4 and tier >= 2 and WM_CountOwnedType(p, 'v013') < (armyCount / 4 + 2) then
                            set productionId = 'v013'
                            set unitFood = 4
                            set productionWait = 32
                            set productionAdapted = true
                        elseif tier >= 2 and WM_CountOwnedType(p, 'v013') < (armyCount / 5 + 1) then
                            set productionId = 'v013'
                            set unitFood = 4
                            set productionWait = 32
                        elseif WM_CountOwnedType(p, 'v012') < 2 or WM_CountOwnedType(p, 'v012') <= WM_CountOwnedType(p, 'v011') then
                            set productionId = 'v012'
                            set unitFood = 3
                            set productionWait = 25
                        else
                            set productionId = 'v011'
                            set productionWait = 20
                        endif
                    elseif f == 8 then
                        if enemyAirCount >= 2 and WM_CountOwnedType(p, 't012') < WM_CountOwnedType(p, 't011') + 3 then
                            set productionId = 't012'
                            set unitFood = 3
                            set productionWait = 25
                            set productionAdapted = true
                        elseif enemyRangedCount >= 4 and tier >= 2 and WM_CountOwnedType(p, 't013') < (armyCount / 4 + 2) then
                            set productionId = 't013'
                            set unitFood = 4
                            set productionWait = 32
                            set productionAdapted = true
                        elseif tier >= 2 and WM_CountOwnedType(p, 't013') < (armyCount / 5 + 1) then
                            set productionId = 't013'
                            set unitFood = 4
                            set productionWait = 32
                        elseif WM_CountOwnedType(p, 't012') < 2 or WM_CountOwnedType(p, 't012') <= WM_CountOwnedType(p, 't011') then
                            set productionId = 't012'
                            set unitFood = 3
                            set productionWait = 25
                        else
                            set productionId = 't011'
                            set productionWait = 20
                        endif
                    endif
                    if productionId != 0 and foodUsed + unitFood <= foodCap and gold >= 120 then
                        set issued = IssueImmediateOrderById(rax, productionId)
                        if issued then
                            set udg_AINextRaxOrderAt[i] = udg_MatchSeconds + productionWait
                            if productionAdapted then
                                set udg_AIMetricCounterOrders[i] = udg_AIMetricCounterOrders[i] + 1
                            endif
                        endif
                    endif
                endif

                set productionId = 0
                set productionWait = 0
                set unitFood = 2
                set productionAdapted = false
                if sanctum != null and GetUnitCurrentOrder(sanctum) == 0 and udg_MatchSeconds >= udg_AINextSanctumOrderAt[i] and tier >= 2 then
                    if f == 5 then
                        if (enemyAirCount >= 2 or enemyCasterCount >= 2) and WM_CountOwnedType(p, 'nwgs') < WM_CountOwnedType(p, 'nnsw') + 3 then
                            set productionId = 'nwgs'
                            set productionAdapted = true
                        elseif WM_CountOwnedType(p, 'nnsw') < 1 then
                            set productionId = 'nnsw'
                        else
                            set productionId = 'nwgs'
                        endif
                    elseif f == 6 then
                        if enemyCasterCount >= 2 and WM_CountOwnedType(p, 'hspt') < WM_CountOwnedType(p, 'nchp') + 2 then
                            set productionId = 'hspt'
                            set unitFood = 3
                            set productionAdapted = true
                        elseif WM_CountOwnedType(p, 'nchp') < 1 then
                            set productionId = 'nchp'
                        else
                            set productionId = 'hspt'
                            set unitFood = 3
                        endif
                    elseif f == 7 then
                        if enemyAirCount >= 2 and WM_CountOwnedType(p, 'v015') < WM_CountOwnedType(p, 'v014') + 2 then
                            set productionId = 'v015'
                            set productionAdapted = true
                        elseif enemyCasterCount >= 2 and WM_CountOwnedType(p, 'v014') < WM_CountOwnedType(p, 'v015') + 2 then
                            set productionId = 'v014'
                            set productionAdapted = true
                        elseif WM_CountOwnedType(p, 'v014') <= WM_CountOwnedType(p, 'v015') then
                            set productionId = 'v014'
                        else
                            set productionId = 'v015'
                        endif
                    elseif f == 8 then
                        if enemyAirCount >= 2 and WM_CountOwnedType(p, 't015') < WM_CountOwnedType(p, 't014') + 2 then
                            set productionId = 't015'
                            set productionAdapted = true
                        elseif enemyCasterCount >= 2 and WM_CountOwnedType(p, 't014') < WM_CountOwnedType(p, 't015') + 2 then
                            set productionId = 't014'
                            set productionAdapted = true
                        elseif WM_CountOwnedType(p, 't014') <= WM_CountOwnedType(p, 't015') then
                            set productionId = 't014'
                        else
                            set productionId = 't015'
                        endif
                    endif
                    if productionId != 0 and foodUsed + unitFood <= foodCap and gold >= 135 then
                        set issued = IssueImmediateOrderById(sanctum, productionId)
                        if issued then
                            set udg_AINextSanctumOrderAt[i] = udg_MatchSeconds + 28
                            if productionAdapted then
                                set udg_AIMetricCounterOrders[i] = udg_AIMetricCounterOrders[i] + 1
                            endif
                        endif
                    endif
                endif

                set productionId = 0
                set productionWait = 0
                if heavyBay != null and GetUnitCurrentOrder(heavyBay) == 0 and udg_MatchSeconds >= udg_AINextHeavyOrderAt[i] and tier >= 2 then
                    if f == 5 then
                        if tier >= 3 and WM_CountOwnedType(p, 'nnrg') == 0 then
                            set productionId = 'nnrg'
                            set unitFood = 5
                            set productionWait = 42
                        elseif WM_CountOwnedType(p, 'nhyc') < 1 then
                            set productionId = 'nhyc'
                            set unitFood = 4
                            set productionWait = 36
                        endif
                    elseif f == 6 then
                        if tier >= 3 and WM_CountOwnedType(p, 'nbel') < 1 then
                            set productionId = 'nbel'
                            set unitFood = 4
                            set productionWait = 38
                        elseif WM_CountOwnedType(p, 'h006') < 1 then
                            set productionId = 'h006'
                            set unitFood = 3
                            set productionWait = 36
                        else
                            set productionId = 'hgyr'
                            set unitFood = 1
                            set productionWait = 26
                        endif
                    elseif f == 7 then
                        if tier >= 3 and WM_CountOwnedType(p, 'v017') < 1 then
                            set productionId = 'v017'
                            set unitFood = 5
                            set productionWait = 42
                        else
                            set productionId = 'v016'
                            set unitFood = 4
                            set productionWait = 35
                        endif
                    elseif f == 8 then
                        if tier >= 3 and WM_CountOwnedType(p, 't017') < 1 then
                            set productionId = 't017'
                            set unitFood = 5
                            set productionWait = 42
                        else
                            set productionId = 't016'
                            set unitFood = 4
                            set productionWait = 35
                        endif
                    endif
                    if productionId != 0 and foodUsed + unitFood <= foodCap and gold >= 180 then
                        set issued = IssueImmediateOrderById(heavyBay, productionId)
                        if issued then
                            set udg_AINextHeavyOrderAt[i] = udg_MatchSeconds + productionWait
                        endif
                    endif
                endif

                if airBay != null and GetUnitCurrentOrder(airBay) == 0 and udg_MatchSeconds >= udg_AINextAirOrderAt[i] and tier >= 2 and f == 6 then
                    set productionAdapted = false
                    if enemyAirCount >= 2 and WM_CountOwnedType(p, 'hdhw') < WM_CountOwnedType(p, 'hgry') + 3 then
                        set productionId = 'hdhw'
                        set unitFood = 3
                        set productionAdapted = true
                    elseif WM_CountOwnedType(p, 'hdhw') <= WM_CountOwnedType(p, 'hgry') then
                        set productionId = 'hdhw'
                        set unitFood = 3
                    else
                        set productionId = 'hgry'
                        set unitFood = 4
                    endif
                    if foodUsed + unitFood <= foodCap and gold >= 160 then
                        set issued = IssueImmediateOrderById(airBay, productionId)
                        if issued then
                            set udg_AINextAirOrderAt[i] = udg_MatchSeconds + 32
                            if productionAdapted then
                                set udg_AIMetricCounterOrders[i] = udg_AIMetricCounterOrders[i] + 1
                            endif
                        endif
                    endif
                endif
            endif

            // Dynamic commander: visible threats and defense first, then creep/shrine,
            // expansion guard, recent last-seen scouting, and finally public start-location scouting.
            if f >= 5 and armyCount >= 5 and udg_MatchSeconds >= 70 then
                call WM_AIChooseMarchObjective(p, i, armyCount, sx, sy, targetEnemy)
                set tx = udg_AIObjectiveX[i]
                set ty = udg_AIObjectiveY[i]
                set objectiveChanged = false
                if udg_AIObjectiveMode[i] != udg_AILastMarchObjectiveMode[i] then
                    set objectiveChanged = true
                else
                    set dx = tx - udg_AILastMarchObjectiveX[i]
                    set dy = ty - udg_AILastMarchObjectiveY[i]
                    if dx * dx + dy * dy > 640000.0 or udg_MatchSeconds - udg_AILastMarchObjectiveAt[i] >= 45 then
                        set objectiveChanged = true
                    endif
                endif
                if objectiveChanged then
                    set udg_AILastMarchObjectiveMode[i] = udg_AIObjectiveMode[i]
                    set udg_AILastMarchObjectiveX[i] = tx
                    set udg_AILastMarchObjectiveY[i] = ty
                    set udg_AILastMarchObjectiveAt[i] = udg_MatchSeconds
                endif
                if armyCount >= 6 or (udg_AIDiff >= 4 and armyCount >= 5) then
                    call GroupClear(udg_TempGroupA)
                    call GroupEnumUnitsOfPlayer(udg_TempGroupA, p, null)
                    loop
                        set u = FirstOfGroup(udg_TempGroupA)
                        exitwhen u == null
                        call GroupRemoveUnit(udg_TempGroupA, u)
                        if GetWidgetLife(u) > 0.405 and not IsUnitType(u, UNIT_TYPE_PEON) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and not WM_IsCustomAIWorker(f, GetUnitTypeId(u)) then
                            set currentOrder = GetUnitCurrentOrder(u)
                            if currentOrder == 0 or (objectiveChanged and currentOrder == attackOrder) then
                                set issued = IssuePointOrder(u, "attack", tx, ty)
                                if issued then
                                    set udg_AIMetricObjectiveOrders[i] = udg_AIMetricObjectiveOrders[i] + 1
                                    if udg_AIObjectiveMode[i] == 4 then
                                        set udg_AIMetricDefenseOrders[i] = udg_AIMetricDefenseOrders[i] + 1
                                    endif
                                endif
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
    set airBay = null
    set armory = null
    set idleWorker = null
    set aiBuilder = null
    set mine = null
    set expansionMine = null
    set targetEnemy = null
    set tree = null
    set treeRect = null
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
                call DialogSetMessage(udg_RaceDialog[i], "|cffffd700★ SELECT YOUR EMPIRE ★|r\n|cff94a3b8AI:|r " + WM_GetDiffLabel(udg_AIDiff) + " " + WM_GetDiffSupportLabel(udg_AIDiff) + "  |cff64748b•  1-Click Instant Start|r")
                set udg_BtnPickAbyss[i]  = DialogAddButton(udg_RaceDialog[i], "|cff22d3ee[1] Abyssal Tideborn|r  |cff94a3b8(Naga Leviathans)|r", '1')
                set udg_BtnPickSolar[i]  = DialogAddButton(udg_RaceDialog[i], "|cfffbbf24[2] Sunfury Imperium|r  |cff94a3b8(Solar Phoenix)|r", '2')
                set udg_BtnPickVoid[i]   = DialogAddButton(udg_RaceDialog[i], "|cffc084fc[3] Voidborn Legion|r  |cfff43f5e[NEW]|r", '3')
                set udg_BtnPickRunic[i]  = DialogAddButton(udg_RaceDialog[i], "|cfff97316[4] Runeforged Bastion|r  |cfff43f5e[NEW]|r", '4')
                set udg_BtnPickRandom[i] = DialogAddButton(udg_RaceDialog[i], "|cff4ade80[R] Random Custom Empire|r", 'R')
                set udg_BtnPickRandomAll[i] = DialogAddButton(udg_RaceDialog[i], "|cffffd166[A] Random Any of 8 Races|r", 'A')
                set udg_BtnKeepClassic[i] = DialogAddButton(udg_RaceDialog[i], "|cffe2e8f0[K] Keep Lobby Race|r", 'K')
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
    call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 8.0, "|cffffd700[Crown of WarMahdi]|r Host selected AI Difficulty: " + WM_GetDiffLabel(udg_AIDiff) + " " + WM_GetDiffSupportLabel(udg_AIDiff))
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
        call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 7.0, "|cffffd700[Crown of WarMahdi]|r AI Difficulty defaulted to " + WM_GetDiffLabel(udg_AIDiff) + " " + WM_GetDiffSupportLabel(udg_AIDiff))
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
        call DialogSetMessage(udg_HostAIDialog, "|cffffd700★ CROWN OF WARMAHDI — AI DIFFICULTY ★|r\n|cff94a3b8Host: Decision quality rises by level; custom AI income support is shown on each option.|r")
        set udg_BtnDiff1 = DialogAddButton(udg_HostAIDialog, "|cff4ade80[1] Novice Commander|r  |cff94a3b8(Relaxed • no income bonus)|r", '1')
        set udg_BtnDiff2 = DialogAddButton(udg_HostAIDialog, "|cff38bdf8[2] Veteran Tactician|r  |cff94a3b8(Improved micro • +2g/+1l per 4s)|r", '2')
        set udg_BtnDiff3 = DialogAddButton(udg_HostAIDialog, "|cffa855f7[3] Grandmaster Pro|r  |cff94a3b8(Adaptive counters • +4g/+2l per 4s)|r", '3')
        set udg_BtnDiff4 = DialogAddButton(udg_HostAIDialog, "|cfff43f5e[4] ★ WarMahdi Mythic ★|r  |cffd1d5db(Full micro • +7g/+3l per 4s)|r", '4')
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
    elseif b == udg_BtnPickRandomAll[pid] then
        set chosen = GetRandomInt(1, 8)
    else
        set chosen = 0
    endif

    if chosen > 0 then
        call WM_SpawnPlayerEmpire(p, chosen)
    endif
    call DisplayTimedTextToPlayer(p, 0.0, 0.0, 8.0, "|cffffd700★ Empire Ready:|r " + WM_GetFactionLabel(udg_PlayerFaction[pid]) + " |cff94a3b8(Type |r|cff38bdf8-race|r|cff94a3b8 within 35s to switch)|r")
    call WM_RefreshMultiboard()

    set p = null
    set b = null
    return false
endfunction

function WM_ShowAIMetrics takes player viewer returns nothing
    local integer i = 0
    local boolean found = false
    loop
        exitwhen i >= 8
        if GetPlayerSlotState(Player(i)) == PLAYER_SLOT_STATE_PLAYING and GetPlayerController(Player(i)) == MAP_CONTROL_COMPUTER and udg_PlayerFaction[i] >= 5 then
            set found = true
            call DisplayTimedTextToPlayer(viewer, 0.0, 0.0, 12.0, "|cff38bdf8[AI]|r " + GetPlayerName(Player(i)) + " — " + WM_GetDiffLabel(udg_AIDiff) + " | plan: " + WM_AIObjectiveLabel(udg_AIObjectiveMode[i]) + " | seen: " + I2S(udg_AIMetricVisibleContacts[i]) + " | orders: " + I2S(udg_AIMetricObjectiveOrders[i]) + " | defend: " + I2S(udg_AIMetricDefenseOrders[i]))
            call DisplayTimedTextToPlayer(viewer, 0.0, 0.0, 12.0, "  retreat: " + I2S(udg_AIMetricRetreatOrders[i]) + " | focus: " + I2S(udg_AIMetricFocusOrders[i]) + " | spell orders: " + I2S(udg_AIMetricSpellOrders[i]) + " | counter orders: " + I2S(udg_AIMetricCounterOrders[i]) + " | expansions: " + I2S(udg_AIMetricExpansionOrders[i]))
        endif
        set i = i + 1
    endloop
    if not found then
        call DisplayTimedTextToPlayer(viewer, 0.0, 0.0, 8.0, "|cff38bdf8[AI]|r No custom-faction AI opponents are active in this match.")
    endif
    set viewer = null
endfunction

function WM_OnPlayerChatCommand takes nothing returns boolean
    local player p = GetTriggerPlayer()
    local integer pid = GetPlayerId(p)
    local string msg = StringCase(GetEventPlayerChatString(), false)

    if msg == "-aistats" or msg == "-ai" then
        call WM_ShowAIMetrics(p)
    elseif msg == "-race" or msg == "-races" then
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
    call QuestSetTitle(q1, "Crown of WarMahdi — 16 Exclusive Heroes / 64 Skills")
    call QuestSetIconPath(q1, "ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_Hvsh.blp")
    call QuestSetDescription(q1, "4 Original Empires join the 4 Classic Races. Every one of the 16 custom Heroes now has a private Q/W/E/R kit (64 distinct skills, buttons, and spell shapes).\n• Abyssal Tideborn: Vashj, Illidan Stormrage, Naj'entus, Athissa.\n• Sunfury Imperium: Kael'thas, Sylvanas, Garithos, Uther.\n• Voidborn Legion: Xal'athor, Sargen'eth, Akama, Aetheron.\n• Runeforged Bastion: Thorim, Ignis, Mimiron, Loken.\n\nHold the Central Crown Shrine for resources, healing, and a live HUD.")
    call QuestSetRequired(q1, true)

    call QuestSetTitle(q2, "Quick Commands & Pro AI")
    call QuestSetIconPath(q2, "ReplaceableTextures\\CommandButtons\\BTNHeroTinker.blp")
    call QuestSetDescription(q2, "• Host picks AI Difficulty at 0:00; each custom-race income bonus is shown before selection.\n• Type -aistats during play to inspect AI objectives, visible contacts, defense, retreat, spell and counter-order counts.\n• Type -race (or -abyss / -sun / -void / -titan) in the opening 40s to switch empire.")
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
    local trigger buildTrig = CreateTrigger()
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
        call TriggerRegisterPlayerUnitEvent(buildTrig, p, EVENT_PLAYER_UNIT_CONSTRUCT_FINISH, null)

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
    call TriggerAddCondition(buildTrig, Condition(function WM_OnAIFallbackBuildFinished))

    call WM_CreateImperialCodexQuests()

    call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 12.0, "|cffffd700★ (8) Crown of WarMahdi v8 ★|r — |cff22d3ee8 Playable Empires|r • |cffc084fc64 Hero-Specific Skills|r • |cfff97316Pro AI|r")

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
    set buildTrig = null
endfunction
"""
    return globals_jass, functions_jass
