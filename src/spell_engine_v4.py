#!/usr/bin/env python3
"""Patch-safe JASS2 spell engine for 64 exclusive WarMahdi hero abilities."""

SPELL_ENGINE_V4 = r"""
// ============================================================================
// V4: CUSTOM 3D / GEOMETRIC SPELL ENGINE — 64 HERO-SPECIFIC SKILLS (`A000..A063`)
// Each hero has a private Q/W/E/R kit, custom BLP icons, faction-tinted VFX,
// its own point/target/self mechanics, and its own balanced cooldown/mana data.
// ============================================================================

function WM_ApplyAreaEffect takes unit caster, real cx, real cy, real radius, real damage, real allyHeal, real manaGain, real manaBurn, real impulse returns nothing
    local player owner = GetOwningPlayer(caster)
    local unit u = null
    local real maxMana = 0.0
    call GroupClear(udg_SpellGroup)
    call GroupEnumUnitsInRange(udg_SpellGroup, cx, cy, radius, null)
    loop
        set u = FirstOfGroup(udg_SpellGroup)
        exitwhen u == null
        call GroupRemoveUnit(udg_SpellGroup, u)
        if WM_IsValidSpellEnemy(u, owner) then
            if damage > 0.0 then
                call WM_DealSpellDamage(caster, u, damage)
            endif
            if manaBurn > 0.0 and GetUnitState(u, UNIT_STATE_MAX_MANA) > 0.0 then
                call SetUnitState(u, UNIT_STATE_MANA, RMaxBJ(0.0, GetUnitState(u, UNIT_STATE_MANA) - manaBurn))
            endif
            if impulse != 0.0 then
                call WM_PullOrPushUnit(u, cx, cy, impulse)
            endif
        elseif IsUnitAlly(u, owner) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and GetWidgetLife(u) > 0.405 then
            if allyHeal > 0.0 then
                call SetWidgetLife(u, GetWidgetLife(u) + allyHeal)
            endif
            if manaGain > 0.0 then
                set maxMana = GetUnitState(u, UNIT_STATE_MAX_MANA)
                if maxMana > 0.0 then
                    call SetUnitState(u, UNIT_STATE_MANA, RMinBJ(maxMana, GetUnitState(u, UNIT_STATE_MANA) + manaGain))
                endif
            endif
        endif
    endloop
    set u = null
    set owner = null
endfunction

function WM_ApplyLineEffect takes unit caster, real sx, real sy, real tx, real ty, real width, real damage returns nothing
    local player owner = GetOwningPlayer(caster)
    local unit u = null
    local real vx = tx - sx
    local real vy = ty - sy
    local real lenSq = vx * vx + vy * vy
    local real midX = 0.0
    local real midY = 0.0
    local real searchR = 0.0
    local real ux = 0.0
    local real uy = 0.0
    local real proj = 0.0
    local real cross = 0.0
    if lenSq < 1.0 then
        set lenSq = 1.0
    endif
    set midX = (sx + tx) * 0.5
    set midY = (sy + ty) * 0.5
    set searchR = SquareRoot(lenSq) * 0.5 + width
    call GroupClear(udg_SpellGroup)
    call GroupEnumUnitsInRange(udg_SpellGroup, midX, midY, searchR, null)
    loop
        set u = FirstOfGroup(udg_SpellGroup)
        exitwhen u == null
        call GroupRemoveUnit(udg_SpellGroup, u)
        if WM_IsValidSpellEnemy(u, owner) then
            set ux = GetUnitX(u) - sx
            set uy = GetUnitY(u) - sy
            set proj = ux * vx + uy * vy
            set cross = ux * vy - uy * vx
            if proj >= 0.0 and proj <= lenSq and cross * cross <= width * width * lenSq then
                call WM_DealSpellDamage(caster, u, damage)
            endif
        endif
    endloop
    set u = null
    set owner = null
endfunction

function WM_SpawnTimedUnit takes player owner, integer rawcode, real x, real y, real duration returns nothing
    local unit summoned = CreateUnit(owner, rawcode, WM_ClampMapCoord(x), WM_ClampMapCoord(y), GetRandomReal(0.0, 360.0))
    if summoned != null then
        call UnitApplyTimedLife(summoned, 'BTLF', duration)
    endif
    set summoned = null
    set owner = null
endfunction

function WM_CastChainLightning takes unit caster, unit firstTarget, integer jumps, real damage, string fxPath returns nothing
    local player owner = GetOwningPlayer(caster)
    local unit current = firstTarget
    local unit u = null
    local unit best = null
    local group hit = CreateGroup()
    local real bestD = 99999999.0
    local real dx = 0.0
    local real dy = 0.0
    local real d = 0.0
    local integer hop = 0
    loop
        exitwhen current == null or hop >= jumps
        if WM_IsValidSpellEnemy(current, owner) and not IsUnitInGroup(current, hit) then
            call GroupAddUnit(hit, current)
            call DestroyEffect(AddSpecialEffect(fxPath, GetUnitX(current), GetUnitY(current)))
            call WM_DealSpellDamage(caster, current, damage / (1.0 + I2R(hop) * 0.32))
            set best = null
            set bestD = 99999999.0
            call GroupClear(udg_TempGroupB)
            call GroupEnumUnitsInRange(udg_TempGroupB, GetUnitX(current), GetUnitY(current), 300.0, null)
            loop
                set u = FirstOfGroup(udg_TempGroupB)
                exitwhen u == null
                call GroupRemoveUnit(udg_TempGroupB, u)
                if not IsUnitInGroup(u, hit) and WM_IsValidSpellEnemy(u, owner) then
                    set dx = GetUnitX(u) - GetUnitX(current)
                    set dy = GetUnitY(u) - GetUnitY(current)
                    set d = dx * dx + dy * dy
                    if d < bestD then
                        set bestD = d
                        set best = u
                    endif
                endif
            endloop
            set current = best
        else
            set current = null
        endif
        set hop = hop + 1
    endloop
    call DestroyGroup(hit)
    set hit = null
    set owner = null
    set current = null
    set u = null
    set best = null
endfunction

function WM_EnqueueUltPulse takes unit caster, integer abilId, real tx, real ty, integer pulses returns nothing
    local integer idx = 0
    if pulses <= 0 or caster == null then
        return
    endif

    // Reuse expired entries; never overwrite slot zero while its ultimate is active.
    loop
        exitwhen idx >= 48 or udg_UltCaster[idx] == null or udg_UltTicksLeft[idx] <= 0
        set idx = idx + 1
    endloop
    if idx >= 48 then
        return
    endif

    set udg_UltCaster[idx] = caster
    set udg_UltAbil[idx] = abilId
    set udg_UltX[idx] = tx
    set udg_UltY[idx] = ty
    set udg_UltTicksLeft[idx] = pulses
    if idx >= udg_UltCount then
        set udg_UltCount = idx + 1
    endif
endfunction

function WM_GetUltPulseDamage takes unit caster, real baseDamage returns real
    local integer heroLevel = GetHeroLevel(caster)
    local real levelBonus = I2R(heroLevel - 6) * 2.0
    if levelBonus < 0.0 then
        set levelBonus = 0.0
    endif
    return baseDamage + 0.25 * WM_HeroPrimaryBonus(caster) + levelBonus
endfunction

function WM_ResurrectNearestAlliedHero takes unit caster, real cx, real cy, real radius returns boolean
    local player owner = GetOwningPlayer(caster)
    local unit u = null
    local unit corpse = null
    local real dx = 0.0
    local real dy = 0.0
    local real distSq = 0.0
    local real bestDistSq = radius * radius
    local boolean revived = false
    call GroupClear(udg_SpellGroup)
    call GroupEnumUnitsInRange(udg_SpellGroup, cx, cy, radius, null)
    loop
        set u = FirstOfGroup(udg_SpellGroup)
        exitwhen u == null
        call GroupRemoveUnit(udg_SpellGroup, u)
        if u != caster and GetUnitTypeId(u) != 0 and IsUnitType(u, UNIT_TYPE_HERO) and IsUnitAlly(u, owner) and GetWidgetLife(u) <= 0.405 then
            set dx = GetUnitX(u) - cx
            set dy = GetUnitY(u) - cy
            set distSq = dx * dx + dy * dy
            if distSq <= bestDistSq then
                set bestDistSq = distSq
                set corpse = u
            endif
        endif
    endloop
    if corpse != null then
        call DestroyEffect(AddSpecialEffect("Abilities\\Spells\\Human\\Resurrect\\ResurrectTarget.mdl", GetUnitX(corpse), GetUnitY(corpse)))
        set revived = ReviveHero(corpse, GetUnitX(corpse), GetUnitY(corpse), true)
        if revived then
            call SetWidgetLife(corpse, GetUnitState(corpse, UNIT_STATE_MAX_LIFE))
        endif
    endif
    set owner = null
    set u = null
    set corpse = null
    return revived
endfunction

function WM_OnUltWaveTick takes nothing returns nothing
    local integer idx = 0
    local unit caster = null
    local player owner = null
    local integer abil = 0
    local real tx = 0.0
    local real ty = 0.0
    local real rad = 0.0
    local integer pulse = 0
    loop
        exitwhen idx >= udg_UltCount
        if udg_UltTicksLeft[idx] > 0 and udg_UltCaster[idx] != null then
            set caster = udg_UltCaster[idx]
            set owner = GetOwningPlayer(caster)
            set abil = udg_UltAbil[idx]
            set tx = udg_UltX[idx]
            set ty = udg_UltY[idx]
            set pulse = 4 - udg_UltTicksLeft[idx]
            set rad = 150.0 + I2R(pulse) * 92.0
            if GetWidgetLife(caster) <= 0.405 then
                set udg_UltTicksLeft[idx] = 0
                set udg_UltCaster[idx] = null
            elseif abil == 'A003' then
                // Vashj: three advancing Tsunami fronts, healing friendlies behind the wave.
                call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Other\\CrushingWave\\CrushingWaveDamage.mdl", tx, ty, rad, 10, I2R(pulse) * 0.18)
                call WM_ApplyAreaEffect(caster, tx, ty, 390.0, WM_GetUltPulseDamage(caster, 49.0), 18.0, 0.0, 0.0, 42.0)
            elseif abil == 'A007' then
                // Illidan: fel-tidal metamorphosis orbit and twin-glaive shock pulses.
                call DestroyEffect(AddSpecialEffect("WM_FX_FelGlaive.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\NightElf\\Immolation\\ImmolationDamage.mdl", tx, ty, rad, 8, I2R(pulse) * 0.42)
                call WM_ApplyAreaEffect(caster, tx, ty, 380.0, WM_GetUltPulseDamage(caster, 52.0), 12.0, 0.0, 0.0, 36.0)
                call SetWidgetLife(caster, GetWidgetLife(caster) + 28.0)
            elseif abil == 'A011' then
                // Naj'entus: Kraken undertow pulls the enemy formation into the trench.
                call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Other\\CrushingWave\\CrushingWaveDamage.mdl", tx, ty, rad, 8, I2R(pulse) * 0.26)
                call WM_ApplyAreaEffect(caster, tx, ty, 390.0, WM_GetUltPulseDamage(caster, 54.0), 0.0, 0.0, 0.0, -48.0)
                if pulse == 2 then
                    call WM_SpawnTimedUnit(owner, 'nmyr', tx + 145.0, ty + 70.0, 12.0)
                    call WM_SpawnTimedUnit(owner, 'nmyr', tx - 145.0, ty - 70.0, 12.0)
                endif
            elseif abil == 'A015' then
                // Athissa: pearl-surge ring, mana drain, and the final undertow.
                call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Other\\Monsoon\\MonsoonBoltTarget.mdl", tx, ty, rad, 8, I2R(pulse) * 0.34)
                call WM_ApplyAreaEffect(caster, tx, ty, 400.0, WM_GetUltPulseDamage(caster, 48.0), 16.0, 10.0, 18.0, -32.0)
                if pulse == 2 then
                    call WM_SpawnTimedUnit(owner, 'nsnp', tx + 145.0, ty + 70.0, 16.0)
                    call WM_SpawnTimedUnit(owner, 'nsnp', tx - 145.0, ty - 70.0, 16.0)
                endif
            elseif abil == 'A019' then
                // Kael: the original Phoenix joins the custom solar shockwaves.
                call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Human\\MarkOfChaos\\MarkOfChaosTarget.mdl", tx, ty, rad, 8, I2R(pulse) * 0.48)
                call WM_ApplyAreaEffect(caster, tx, ty, 400.0, WM_GetUltPulseDamage(caster, 56.0), 12.0, 12.0, 0.0, 30.0)
                if pulse == 2 then
                    call DestroyEffect(AddSpecialEffect("Abilities\\Spells\\Human\\MarkOfChaos\\MarkOfChaosTarget.mdl", tx, ty))
                    call WM_SpawnTimedUnit(owner, 'hphx', tx - 170.0, ty, 18.0)
                endif
            elseif abil == 'A023' then
                // Sylvanas: three volleys of spectral arrows in expanding rings.
                call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Weapons\\Arrow\\ArrowMissile.mdl", tx, ty, rad, 12, I2R(pulse) * 0.15)
                call WM_ApplyAreaEffect(caster, tx, ty, 410.0, WM_GetUltPulseDamage(caster, 54.0), 0.0, 0.0, 0.0, 18.0)
            elseif abil == 'A027' then
                // Garithos: Imperial cavalry shockwaves knock the formation aside.
                call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Human\\Thunderclap\\ThunderClapCaster.mdl", tx, ty, rad, 6, I2R(pulse) * 0.35)
                call WM_ApplyAreaEffect(caster, tx, ty, 390.0, WM_GetUltPulseDamage(caster, 56.0), 8.0, 0.0, 0.0, 48.0)
                if pulse == 2 then
                    call WM_SpawnTimedUnit(owner, 'hcth', tx + 145.0, ty + 70.0, 14.0)
                    call WM_SpawnTimedUnit(owner, 'hcth', tx - 145.0, ty - 70.0, 14.0)
                endif
            elseif abil == 'A031' then
                // Uther restores the nearest fallen ally, then pulses the battlefield with Holy Light.
                call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Human\\Resurrect\\ResurrectTarget.mdl", tx, ty, rad, 8, I2R(pulse) * 0.25)
                if pulse == 1 then
                    call WM_ResurrectNearestAlliedHero(caster, tx, ty, 520.0)
                endif
                call WM_ApplyAreaEffect(caster, tx, ty, 410.0, WM_GetUltPulseDamage(caster, 48.0), 46.0, 8.0, 0.0, 0.0)
            elseif abil == 'A035' then
                // Xal'athor: Dark Portal meteor + inward collapse.
                call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Undead\\DarkRitual\\DarkRitualTarget.mdl", tx, ty, rad, 7, I2R(pulse) * 0.30)
                call WM_ApplyAreaEffect(caster, tx, ty, 400.0, WM_GetUltPulseDamage(caster, 58.0), 0.0, 0.0, 20.0, -46.0)
                if pulse == 2 then
                    call WM_SpawnTimedUnit(owner, 'v011', tx + 140.0, ty + 80.0, 18.0)
                    call WM_SpawnTimedUnit(owner, 'v011', tx - 140.0, ty - 80.0, 18.0)
                endif
            elseif abil == 'A039' then
                // Sargen'eth: singularity pulses vacuum enemies and burn their mana.
                call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Undead\\Possession\\PossessionMissile.mdl", tx, ty, rad, 8, I2R(pulse) * 0.22)
                call WM_ApplyAreaEffect(caster, tx, ty, 410.0, WM_GetUltPulseDamage(caster, 56.0), 0.0, 0.0, 24.0, -58.0)
            elseif abil == 'A043' then
                // Akama: close-range shadow-dance orbit, healing the assassin between strikes.
                set tx = GetUnitX(caster)
                set ty = GetUnitY(caster)
                call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\NightElf\\Blink\\BlinkCaster.mdl", tx, ty, rad * 0.72, 8, I2R(pulse) * 0.50)
                call WM_ApplyAreaEffect(caster, tx, ty, 380.0, WM_GetUltPulseDamage(caster, 61.0), 12.0, 0.0, 0.0, 34.0)
                call SetWidgetLife(caster, GetWidgetLife(caster) + 35.0)
            elseif abil == 'A047' then
                // Aetheron: starfall-and-barrier over the cosmic field.
                call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\NightElf\\Starfall\\StarfallCaster.mdl", tx, ty, rad, 10, I2R(pulse) * 0.18)
                call WM_ApplyAreaEffect(caster, tx, ty, 410.0, WM_GetUltPulseDamage(caster, 56.0), 24.0, 0.0, 0.0, 0.0)
            elseif abil == 'A051' then
                // Thorim: sequential Pantheon bolts strike a widening runic circle.
                call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Other\\Monsoon\\MonsoonBoltTarget.mdl", tx, ty, rad, 8, I2R(pulse) * 0.4)
                call WM_ApplyAreaEffect(caster, tx, ty, 400.0, WM_GetUltPulseDamage(caster, 59.0), 0.0, 0.0, 0.0, 38.0)
                if pulse == 2 then
                    call WM_SpawnTimedUnit(owner, 't011', tx + 145.0, ty + 70.0, 16.0)
                    call WM_SpawnTimedUnit(owner, 't011', tx - 145.0, ty - 70.0, 16.0)
                endif
            elseif abil == 'A055' then
                // Ignis: magma implosions awaken one temporary Stormforged Juggernaut.
                call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Other\\Volcano\\VolcanoMissile.mdl", tx, ty, rad, 6, I2R(pulse) * 0.22)
                call WM_ApplyAreaEffect(caster, tx, ty, 390.0, WM_GetUltPulseDamage(caster, 58.0), 0.0, 0.0, 0.0, 24.0)
                if pulse == 2 then
                    call WM_SpawnTimedUnit(owner, 't013', tx + 150.0, ty, 20.0)
                endif
            elseif abil == 'A059' then
                // Mimiron: an orbital laser sweeps 3 successive circles.
                call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Spells\\Other\\Doom\\DoomDeath.mdl", tx, ty, rad * 0.8, 8, I2R(pulse) * 0.38)
                call WM_ApplyAreaEffect(caster, tx, ty, 420.0, WM_GetUltPulseDamage(caster, 60.0), 0.0, 0.0, 0.0, 0.0)
            elseif abil == 'A063' then
                // Loken: Tesla overcharge steals mana and calls two short-lived interceptors.
                call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", tx, ty))
                call WM_SpawnRingFX("Abilities\\Weapons\\FarseerMissile\\FarseerMissile.mdl", tx, ty, rad, 8, I2R(pulse) * 0.33)
                call WM_ApplyAreaEffect(caster, tx, ty, 410.0, WM_GetUltPulseDamage(caster, 56.0), 8.0, 0.0, 22.0, 0.0)
                if pulse == 2 then
                    call WM_SpawnTimedUnit(owner, 't015', tx + 160.0, ty, 18.0)
                    call WM_SpawnTimedUnit(owner, 't015', tx - 160.0, ty, 18.0)
                endif
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
endfunction

function WM_OnCustomHeroSpellEffect takes nothing returns boolean
    local integer abil = GetSpellAbilityId()
    local unit caster = null
    local unit targ = null
    local unit u = null
    local player owner = null
    local integer lvl = 1
    local integer pid = 0
    local integer chainCount = 0
    local real cx = 0.0
    local real cy = 0.0
    local real tx = 0.0
    local real ty = 0.0
    local real dx = 0.0
    local real dy = 0.0
    local real dist = 0.0
    local real dmg = 0.0
    local real missingLife = 0.0
    local real manaTaken = 0.0
    local real ang = 0.0

    if abil < 'A000' or abil > 'A063' then
        return false
    endif
    set caster = GetTriggerUnit()
    if caster == null then
        return false
    endif
    set owner = GetOwningPlayer(caster)
    set pid = GetPlayerId(owner)
    set lvl = GetUnitAbilityLevel(caster, abil)
    if lvl < 1 then
        set lvl = 1
    endif
    set cx = GetUnitX(caster)
    set cy = GetUnitY(caster)
    set tx = GetSpellTargetX()
    set ty = GetSpellTargetY()
    set dmg = 42.0 + 34.0 * I2R(lvl) + WM_HeroPrimaryBonus(caster)

    // ---- Q: 16 distinct point-target signatures ----
    if abil == 'A000' then
        // Vashj — Maelstrom: inward whirlpool.
        call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\CrushingWave\\CrushingWaveDamage.mdl", tx, ty, 235.0, 8, 0.32)
        call WM_ApplyAreaEffect(caster, tx, ty, 275.0, dmg, 0.0, 0.0, 0.0, -90.0)
    elseif abil == 'A004' then
        // Illidan — Azzinoth Glaive Barrage: narrow 3-blade lanes + endpoint burst.
        call DestroyEffect(AddSpecialEffect("WM_FX_FelGlaive.mdx", tx, ty))
        set ang = Atan2(ty - cy, tx - cx)
        call WM_ApplyLineEffect(caster, cx, cy, WM_ClampMapCoord(tx + Cos(ang + 0.16) * 100.0), WM_ClampMapCoord(ty + Sin(ang + 0.16) * 100.0), 72.0, dmg)
        call WM_ApplyLineEffect(caster, cx, cy, tx, ty, 72.0, dmg * 0.75)
        call WM_ApplyLineEffect(caster, cx, cy, WM_ClampMapCoord(tx + Cos(ang - 0.16) * 100.0), WM_ClampMapCoord(ty + Sin(ang - 0.16) * 100.0), 72.0, dmg)
        call WM_ApplyAreaEffect(caster, tx, ty, 150.0, dmg * 0.35, 0.0, 0.0, 0.0, 0.0)
    elseif abil == 'A008' then
        // Naj'entus — Spine Quake: three sequential coral fissures.
        call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\CrushingWave\\CrushingWaveDamage.mdl", tx, ty, 170.0, 3, 0.0)
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\CrushingWave\\CrushingWaveDamage.mdl", tx, ty, 260.0, 3, 1.05)
        call WM_ApplyAreaEffect(caster, tx, ty, 285.0, dmg * 1.18, 0.0, 0.0, 0.0, 55.0)
    elseif abil == 'A012' then
        // Athissa — Geyser: enemy burst plus pearl-pool healing for allies.
        call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\Monsoon\\MonsoonBoltTarget.mdl", tx, ty, 220.0, 6, 0.25)
        call WM_ApplyAreaEffect(caster, tx, ty, 280.0, dmg, 52.0 + 12.0 * I2R(lvl), 0.0, 0.0, 0.0)
    elseif abil == 'A016' then
        // Kael'thas — Verdant Pyre: solar pillar and controlled mana ignition.
        call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Human\\FlameStrike\\FlameStrikeEmbers.mdl", tx, ty, 220.0, 6, 0.0)
        call WM_ApplyAreaEffect(caster, tx, ty, 275.0, dmg * 1.12, 0.0, 0.0, 16.0 * I2R(lvl), 0.0)
    elseif abil == 'A020' then
        // Sylvanas — Sunhawk Volley: three forward arrows, each a narrow piercing lane.
        call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
        set ang = Atan2(ty - cy, tx - cx)
        call WM_ApplyLineEffect(caster, cx, cy, tx, ty, 110.0, dmg * 1.08)
        call WM_ApplyLineEffect(caster, cx, cy, WM_ClampMapCoord(tx + Cos(ang + 0.22) * 85.0), WM_ClampMapCoord(ty + Sin(ang + 0.22) * 85.0), 55.0, dmg * 0.55)
        call WM_ApplyLineEffect(caster, cx, cy, WM_ClampMapCoord(tx + Cos(ang - 0.22) * 85.0), WM_ClampMapCoord(ty + Sin(ang - 0.22) * 85.0), 55.0, dmg * 0.55)
    elseif abil == 'A024' then
        // Garithos — Earthshaker Warhammer: a point-targeted ground shock, not a hero dash.
        call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Human\\Thunderclap\\ThunderClapCaster.mdl", tx, ty, 190.0, 8, 0.0)
        call WM_ApplyAreaEffect(caster, tx, ty, 245.0, dmg * 1.08, 0.0, 0.0, 0.0, 65.0)
    elseif abil == 'A028' then
        // Uther — Consecration: radiant AoE damages foes and heals allies.
        call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Human\\HolyBolt\\HolyBoltSpecialArt.mdl", tx, ty, 220.0, 8, 0.0)
        call WM_ApplyAreaEffect(caster, tx, ty, 285.0, dmg * 0.72, 70.0 + 10.0 * I2R(lvl), 0.0, 0.0, 0.0)
    elseif abil == 'A032' then
        // Xal'athor — Event Horizon: inward gravity well that also drains mana.
        call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Undead\\Possession\\PossessionMissile.mdl", tx, ty, 235.0, 8, 0.20)
        call WM_ApplyAreaEffect(caster, tx, ty, 285.0, dmg * 1.04, 0.0, 0.0, 18.0 * I2R(lvl), -68.0)
    elseif abil == 'A036' then
        // Sargen'eth — Entropy Rift Storm: five localized bolts on a staggered grid.
        call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\Monsoon\\MonsoonBoltTarget.mdl", tx, ty, 190.0, 5, 0.25)
        call WM_ApplyAreaEffect(caster, tx, ty, 265.0, dmg * 0.84, 0.0, 0.0, 12.0 * I2R(lvl), 0.0)
        call WM_ApplyAreaEffect(caster, tx + 150.0, ty + 70.0, 135.0, dmg * 0.36, 0.0, 0.0, 0.0, 0.0)
        call WM_ApplyAreaEffect(caster, tx - 150.0, ty - 70.0, 135.0, dmg * 0.36, 0.0, 0.0, 0.0, 0.0)
    elseif abil == 'A040' then
        // Akama — Umbral Shuriken Fan: five-blade fan of crossing shadow lanes.
        call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", tx, ty))
        set ang = Atan2(ty - cy, tx - cx)
        call WM_ApplyLineEffect(caster, cx, cy, tx, ty, 80.0, dmg * 0.86)
        call WM_ApplyLineEffect(caster, cx, cy, WM_ClampMapCoord(cx + Cos(ang + 0.28) * 700.0), WM_ClampMapCoord(cy + Sin(ang + 0.28) * 700.0), 48.0, dmg * 0.56)
        call WM_ApplyLineEffect(caster, cx, cy, WM_ClampMapCoord(cx + Cos(ang - 0.28) * 700.0), WM_ClampMapCoord(cy + Sin(ang - 0.28) * 700.0), 48.0, dmg * 0.56)
    elseif abil == 'A044' then
        // Aetheron — Starfall Singularity: astral shards and a small centripetal pull.
        call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\NightElf\\Starfall\\StarfallCaster.mdl", tx, ty, 225.0, 9, 0.1)
        call WM_ApplyAreaEffect(caster, tx, ty, 285.0, dmg * 0.94, 0.0, 0.0, 0.0, -30.0)
    elseif abil == 'A048' then
        // Thorim — Mjolnir Thunderfall: thunder hammer impact and outward shock ring.
        call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\Monsoon\\MonsoonBoltTarget.mdl", tx, ty, 230.0, 6, 0.0)
        call WM_ApplyAreaEffect(caster, tx, ty, 280.0, dmg * 1.12, 0.0, 0.0, 0.0, 44.0)
    elseif abil == 'A052' then
        // Ignis — Molten Slag Eruption: magma pocket with a short, heavy pulse.
        call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\Volcano\\VolcanoMissile.mdl", tx, ty, 185.0, 5, 0.0)
        call WM_ApplyAreaEffect(caster, tx, ty, 260.0, dmg * 1.12, 0.0, 0.0, 0.0, 35.0)
    elseif abil == 'A056' then
        // Mimiron — Cluster Rocket Salvo: three separated blast markers, lower per-target burst.
        call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Weapons\\RocketMissile\\RocketMissile.mdl", tx, ty, 210.0, 7, 0.0)
        call WM_ApplyAreaEffect(caster, tx, ty, 225.0, dmg * 0.78, 0.0, 0.0, 0.0, 24.0)
        call WM_ApplyAreaEffect(caster, tx + 140.0, ty, 150.0, dmg * 0.36, 0.0, 0.0, 0.0, 0.0)
        call WM_ApplyAreaEffect(caster, tx - 140.0, ty, 150.0, dmg * 0.36, 0.0, 0.0, 0.0, 0.0)
    elseif abil == 'A060' then
        // Loken — Ionosphere Plasma Field: focused storm zone with a mana-burn field.
        call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", tx, ty))
        call WM_SpawnRingFX("Abilities\\Weapons\\FarseerMissile\\FarseerMissile.mdl", tx, ty, 220.0, 8, 0.14)
        call WM_ApplyAreaEffect(caster, tx, ty, 280.0, dmg, 0.0, 0.0, 20.0 * I2R(lvl), 0.0)
    endif

    // ---- W: 16 distinct unit-target signatures ----
    if abil == 'A001' then
        set targ = GetSpellTargetUnit()
        if targ != null then
            call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", GetUnitX(targ), GetUnitY(targ)))
            call WM_CastChainLightning(caster, targ, 3, 58.0 + 34.0 * I2R(lvl) + WM_HeroPrimaryBonus(caster), "WM_FX_Abyssal.mdx")
            call SetUnitState(caster, UNIT_STATE_MANA, RMinBJ(GetUnitState(caster, UNIT_STATE_MAX_MANA), GetUnitState(caster, UNIT_STATE_MANA) + 12.0 * I2R(lvl)))
        endif
    elseif abil == 'A005' then
        // Illidan's restored Mana Burn: drain enemy mana and convert every point to spell damage.
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) and GetUnitState(targ, UNIT_STATE_MAX_MANA) > 0.0 then
            set tx = GetUnitX(targ)
            set ty = GetUnitY(targ)
            set manaTaken = RMinBJ(35.0 + 25.0 * I2R(lvl - 1), GetUnitState(targ, UNIT_STATE_MANA))
            call DestroyEffect(AddSpecialEffect("WM_FX_FelGlaive.mdx", tx, ty))
            call DestroyEffect(AddSpecialEffectTarget("Abilities\\Spells\\NightElf\\ManaBurn\\ManaBurnTarget.mdl", targ, "origin"))
            if manaTaken > 0.0 then
                call SetUnitState(targ, UNIT_STATE_MANA, GetUnitState(targ, UNIT_STATE_MANA) - manaTaken)
                call WM_DealSpellDamage(caster, targ, manaTaken)
            endif
        endif
    elseif abil == 'A009' then
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) then
            set tx = GetUnitX(targ)
            set ty = GetUnitY(targ)
            call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", tx, ty))
            call WM_DealSpellDamage(caster, targ, dmg * 1.16)
            call WM_PullOrPushUnit(targ, cx, cy, -190.0)
        endif
    elseif abil == 'A013' then
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) then
            call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", GetUnitX(targ), GetUnitY(targ)))
            call WM_ApplyAreaEffect(caster, GetUnitX(targ), GetUnitY(targ), 190.0, dmg * 0.50, 0.0, 0.0, 26.0, 0.0)
            call WM_DealSpellDamage(caster, targ, dmg * 0.85)
            // Athissa's pressure cage draws its trapped target inward instead of knocking it away.
            call WM_PullOrPushUnit(targ, cx, cy, -150.0)
        endif
    elseif abil == 'A017' then
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) then
            set tx = GetUnitX(targ)
            set ty = GetUnitY(targ)
            call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
            call WM_DealSpellDamage(caster, targ, dmg * 0.94)
            if GetUnitState(targ, UNIT_STATE_MAX_MANA) > 0.0 then
                call SetUnitState(targ, UNIT_STATE_MANA, RMaxBJ(0.0, GetUnitState(targ, UNIT_STATE_MANA) - 36.0))
                call SetUnitState(caster, UNIT_STATE_MANA, RMinBJ(GetUnitState(caster, UNIT_STATE_MAX_MANA), GetUnitState(caster, UNIT_STATE_MANA) + 28.0))
            endif
            call WM_PullOrPushUnit(targ, cx, cy, -85.0)
        endif
    elseif abil == 'A021' then
        set targ = GetSpellTargetUnit()
        if targ != null then
            set tx = GetUnitX(targ)
            set ty = GetUnitY(targ)
            call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", cx, cy))
            call DestroyEffect(AddSpecialEffectTarget("Abilities\\Weapons\\Arrow\\ArrowMissile.mdl", targ, "chest"))
            call WM_ApplyLineEffect(caster, cx, cy, tx, ty, 85.0, dmg * 1.18)
            if WM_IsValidSpellEnemy(targ, owner) then
                call WM_DealSpellDamage(caster, targ, dmg * 0.45)
            endif
        endif
    elseif abil == 'A025' then
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) then
            set missingLife = GetUnitState(targ, UNIT_STATE_MAX_LIFE) - GetWidgetLife(targ)
            set dmg = 48.0 + 1.15 * WM_HeroPrimaryBonus(caster) + missingLife * 0.16
            if dmg > 280.0 then
                set dmg = 280.0
            endif
            call DestroyEffect(AddSpecialEffectTarget("WM_FX_Solar.mdx", targ, "origin"))
            call WM_DealSpellDamage(caster, targ, dmg)
        endif
    elseif abil == 'A029' then
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) then
            set tx = GetUnitX(targ)
            set ty = GetUnitY(targ)
            call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", tx, ty))
            call WM_DealSpellDamage(caster, targ, dmg * 1.20)
            call WM_ApplyAreaEffect(caster, tx, ty, 180.0, dmg * 0.35, 0.0, 0.0, 0.0, 42.0)
        endif
    elseif abil == 'A033' then
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) then
            set dmg = 54.0 + 34.0 * I2R(lvl) + WM_HeroPrimaryBonus(caster)
            call DestroyEffect(AddSpecialEffectTarget("WM_FX_Void.mdx", targ, "chest"))
            call WM_DealSpellDamage(caster, targ, dmg)
            call SetWidgetLife(caster, GetWidgetLife(caster) + dmg * 0.48)
        endif
    elseif abil == 'A037' then
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) then
            set dmg = 45.0 + 34.0 * I2R(lvl) + WM_HeroPrimaryBonus(caster)
            call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", GetUnitX(targ), GetUnitY(targ)))
            call WM_DealSpellDamage(caster, targ, dmg)
            if GetUnitState(targ, UNIT_STATE_MAX_MANA) > 0.0 then
                call SetUnitState(targ, UNIT_STATE_MANA, RMaxBJ(0.0, GetUnitState(targ, UNIT_STATE_MANA) - 45.0))
                call SetUnitState(caster, UNIT_STATE_MANA, RMinBJ(GetUnitState(caster, UNIT_STATE_MAX_MANA), GetUnitState(caster, UNIT_STATE_MANA) + 32.0))
            endif
            call SetWidgetLife(caster, GetWidgetLife(caster) + dmg * 0.30)
        endif
    elseif abil == 'A041' then
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) then
            set tx = GetUnitX(targ)
            set ty = GetUnitY(targ)
            set dx = tx - cx
            set dy = ty - cy
            set dist = SquareRoot(dx * dx + dy * dy)
            if dist < 1.0 then
                set dist = 1.0
            endif
            set tx = WM_ClampMapCoord(tx + dx / dist * 90.0)
            set ty = WM_ClampMapCoord(ty + dy / dist * 90.0)
            if not IsTerrainPathable(tx, ty, PATHING_TYPE_WALKABILITY) then
                call SetUnitPosition(caster, tx, ty)
            endif
            call DestroyEffect(AddSpecialEffectTarget("WM_FX_Void.mdx", targ, "origin"))
            call WM_DealSpellDamage(caster, targ, dmg * 1.38)
        endif
    elseif abil == 'A045' then
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) then
            call DestroyEffect(AddSpecialEffectTarget("WM_FX_Void.mdx", targ, "chest"))
            call WM_DealSpellDamage(caster, targ, dmg * 0.97)
            call WM_PullOrPushUnit(targ, cx, cy, 180.0)
            if GetUnitState(targ, UNIT_STATE_MAX_MANA) > 0.0 then
                call SetUnitState(targ, UNIT_STATE_MANA, RMaxBJ(0.0, GetUnitState(targ, UNIT_STATE_MANA) - 26.0))
            endif
        endif
    elseif abil == 'A049' then
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) then
            call DestroyEffect(AddSpecialEffectTarget("WM_FX_Runic.mdx", targ, "origin"))
            call WM_PullOrPushUnit(targ, cx, cy, -210.0)
            call WM_DealSpellDamage(caster, targ, dmg * 1.06)
        endif
    elseif abil == 'A053' then
        set targ = GetSpellTargetUnit()
        if targ != null and WM_IsValidSpellEnemy(targ, owner) then
            call DestroyEffect(AddSpecialEffectTarget("WM_FX_Runic.mdx", targ, "chest"))
            call WM_DealSpellDamage(caster, targ, dmg * 1.18)
            call SetWidgetLife(caster, GetWidgetLife(caster) + 55.0 + I2R(lvl) * 18.0)
        endif
    elseif abil == 'A057' then
        set targ = GetSpellTargetUnit()
        if targ != null then
            set tx = GetUnitX(targ)
            set ty = GetUnitY(targ)
            call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", cx, cy))
            call WM_ApplyLineEffect(caster, cx, cy, tx, ty, 58.0, dmg * 1.32)
            call DestroyEffect(AddSpecialEffectTarget("Abilities\\Weapons\\FarseerMissile\\FarseerMissile.mdl", targ, "chest"))
        endif
    elseif abil == 'A061' then
        set targ = GetSpellTargetUnit()
        if targ != null then
            call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", GetUnitX(targ), GetUnitY(targ)))
            call WM_CastChainLightning(caster, targ, 3, 54.0 + 34.0 * I2R(lvl) + WM_HeroPrimaryBonus(caster), "WM_FX_Runic.mdx")
            call SetWidgetLife(caster, GetWidgetLife(caster) + 26.0)
        endif
    endif

    // ---- E: 16 distinct self-cast / instant support signatures ----
    if abil == 'A002' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\CrushingWave\\CrushingWaveDamage.mdl", cx, cy, 190.0, 6, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 300.0, 18.0 + 18.0 * I2R(lvl), 65.0 + 25.0 * I2R(lvl), 0.0, 0.0, 0.0)
    elseif abil == 'A006' then
        call DestroyEffect(AddSpecialEffect("WM_FX_FelGlaive.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\NightElf\\Immolation\\ImmolationDamage.mdl", cx, cy, 220.0, 6, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 270.0, dmg * 0.82, 0.0, 0.0, 0.0, 34.0)
        call SetWidgetLife(caster, GetWidgetLife(caster) + 55.0 + 35.0 * I2R(lvl))
        if lvl >= 2 then
            call WM_SpawnTimedUnit(owner, 'nnmg', cx + 105.0, cy, 12.0)
        endif
    elseif abil == 'A010' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\CrushingWave\\CrushingWaveDamage.mdl", cx, cy, 180.0, 5, 0.3)
        call WM_ApplyAreaEffect(caster, cx, cy, 295.0, dmg * 0.64, 70.0 + 18.0 * I2R(lvl), 0.0, 0.0, 35.0)
    elseif abil == 'A014' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Abyssal.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\Monsoon\\MonsoonBoltTarget.mdl", cx, cy, 220.0, 8, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 330.0, 0.0, 48.0 + 15.0 * I2R(lvl), 42.0 + 18.0 * I2R(lvl), 0.0, 0.0)
    elseif abil == 'A018' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Human\\HolyBolt\\HolyBoltSpecialArt.mdl", cx, cy, 205.0, 6, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 310.0, dmg * 0.44, 68.0 + 16.0 * I2R(lvl), 24.0, 10.0, 0.0)
    elseif abil == 'A022' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Human\\Heal\\HealTarget.mdl", cx, cy, 250.0, 6, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 350.0, 0.0, 58.0 + 20.0 * I2R(lvl), 12.0, 0.0, 0.0)
        call WM_SpawnTimedUnit(owner, 'nhea', cx + 130.0, cy + 60.0, 16.0)
        call WM_SpawnTimedUnit(owner, 'nhea', cx - 130.0, cy - 60.0, 16.0)
    elseif abil == 'A026' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Human\\Thunderclap\\ThunderClapCaster.mdl", cx, cy, 170.0, 6, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 330.0, dmg * 0.48, 82.0 + 22.0 * I2R(lvl), 0.0, 0.0, 50.0)
    elseif abil == 'A030' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Solar.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Human\\HolyBolt\\HolyBoltSpecialArt.mdl", cx, cy, 260.0, 8, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 360.0, 0.0, 90.0 + 28.0 * I2R(lvl), 0.0, 0.0, 0.0)
    elseif abil == 'A034' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Undead\\Possession\\PossessionMissile.mdl", cx, cy, 220.0, 7, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 295.0, dmg * 0.82, 42.0 + 14.0 * I2R(lvl), 0.0, 22.0, 0.0)
    elseif abil == 'A038' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Undead\\DarkRitual\\DarkRitualTarget.mdl", cx, cy, 215.0, 6, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 320.0, dmg * 0.55, 42.0, 55.0 + 20.0 * I2R(lvl), 0.0, 0.0)
    elseif abil == 'A042' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\NightElf\\Blink\\BlinkCaster.mdl", cx, cy, 180.0, 7, 0.1)
        call WM_ApplyAreaEffect(caster, cx, cy, 260.0, dmg * 0.72, 0.0, 0.0, 0.0, 48.0)
        call WM_SpawnTimedUnit(owner, 'v011', cx + 100.0, cy + 80.0, 14.0)
        call WM_SpawnTimedUnit(owner, 'v011', cx - 100.0, cy - 80.0, 14.0)
    elseif abil == 'A046' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Void.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Undead\\AntiMagicShell\\AntiMagicShell.mdl", cx, cy, 210.0, 8, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 330.0, 32.0 + 16.0 * I2R(lvl), 62.0 + 18.0 * I2R(lvl), 22.0, 18.0, 0.0)
    elseif abil == 'A050' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Human\\Thunderclap\\ThunderClapCaster.mdl", cx, cy, 195.0, 6, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 310.0, dmg * 0.52, 66.0 + 18.0 * I2R(lvl), 20.0, 0.0, 36.0)
    elseif abil == 'A054' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Human\\InnerFire\\InnerFireTarget.mdl", cx, cy, 250.0, 7, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 335.0, dmg * 0.40, 76.0 + 18.0 * I2R(lvl), 0.0, 0.0, 0.0)
    elseif abil == 'A058' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Spells\\Other\\TinkerRocketBarrage\\TinkerRocketBarrage.mdl", cx, cy, 180.0, 6, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 250.0, dmg * 0.48, 48.0 + 16.0 * I2R(lvl), 0.0, 0.0, 0.0)
        call WM_SpawnTimedUnit(owner, 't011', cx + 115.0, cy + 40.0, 16.0)
        call WM_SpawnTimedUnit(owner, 't011', cx - 115.0, cy - 40.0, 16.0)
    elseif abil == 'A062' then
        call DestroyEffect(AddSpecialEffect("WM_FX_Runic.mdx", cx, cy))
        call WM_SpawnRingFX("Abilities\\Weapons\\FarseerMissile\\FarseerMissile.mdl", cx, cy, 205.0, 7, 0.0)
        call WM_ApplyAreaEffect(caster, cx, cy, 335.0, dmg * 0.58, 50.0 + 20.0 * I2R(lvl), 65.0 + 18.0 * I2R(lvl), 0.0, 0.0)
    endif

    // ---- R: all 16 unique, expanding multi-pulse Hero Ultimates ----
    if abil == 'A003' or abil == 'A007' or abil == 'A011' or abil == 'A015' or abil == 'A019' or abil == 'A023' or abil == 'A027' or abil == 'A031' or abil == 'A035' or abil == 'A039' or abil == 'A043' or abil == 'A047' or abil == 'A051' or abil == 'A055' or abil == 'A059' or abil == 'A063' then
        if abil == 'A007' or abil == 'A031' or abil == 'A043' then
            set tx = cx
            set ty = cy
        endif
        call WM_EnqueueUltPulse(caster, abil, tx, ty, 3)
    endif

    set caster = null
    set targ = null
    set u = null
    set owner = null
    return false
endfunction
"""
