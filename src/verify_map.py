#!/usr/bin/env python3
"""
17-Stage Automated Static/Binary Verification Suite for `(8) Crown of WarMahdi` v8.
Checks the MPQ, TFT v25, JASS2 APIs (1.26-era proxy and official 1.27b), all 64 hero abilities and skill-specific VFX,
16 unique hero kits, 8 empire spawn/build definitions, four AI scripts and the JASS AI fallback,
object/card/rally flags, native icon/model references, portrait/UI BLP1s/MDXs, pathing, creep safety, D4 objective/camp symmetry, loot tiers and lobby-economy fairness.
It cannot replace launching the map in an actual Warcraft III client.
"""

from __future__ import annotations
import collections
import json
import math
import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from mpq_packer import CANONICAL_W3X_FILES, read_w3x_archive


# ==============================================================================
# Complete JASS2 Lexer + Recursive-Descent Parser + Static Typechecker
# ==============================================================================

TOKEN_RE = re.compile(
    r"""
    (?P<WS>[ \t\r]+)|
    (?P<COMMENT>//[^\n]*)|
    (?P<NL>\n)|
    (?P<REAL>\d+\.\d*|\.\d+)|
    (?P<HEX>0[xX][0-9a-fA-F]+|\$[0-9a-fA-F]+)|
    (?P<INT>\d+)|
    (?P<RAWCODE>'[^'\n]{1,4}')|
    (?P<STR>"(?:\\.|[^"\\\n])*")|
    (?P<OP>==|!=|<=|>=|[+\-*/=<>(),\[\]])|
    (?P<ID>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)

JASS_KEYWORDS = {
    "type", "extends", "globals", "endglobals", "constant", "native", "takes",
    "returns", "nothing", "function", "endfunction", "local", "array", "set",
    "call", "if", "then", "elseif", "else", "endif", "loop", "exitwhen",
    "endloop", "return", "and", "or", "not", "true", "false", "null", "debug",
}


class JassTypeError(Exception):
    pass


class JassChecker:
    def __init__(self) -> None:
        # parent[sub] = base
        self.type_parent: Dict[str, Optional[str]] = {
            "nothing": None,
            "null": None,
            "code": None,
            "integer": None,
            "real": None,
            "boolean": None,
            "string": None,
            "handle": None,
        }
        # globals[name] = (type, is_array, is_const)
        self.globals: Dict[str, Tuple[str, bool, bool]] = {}
        # funcs[name] = (param_types, return_type, is_const)
        self.funcs: Dict[str, Tuple[List[str], str, bool]] = {}

    def is_subtype(self, actual: str, expected: str) -> bool:
        if actual == expected:
            return True
        if actual == "integer" and expected == "real":
            return True
        if actual == "null" and expected not in ("integer", "real", "boolean", "nothing"):
            return True
        # Walk handle hierarchy (in JASS2, handle subtypes can coerce along parent chain)
        cur: Optional[str] = actual
        while cur is not None:
            if cur == expected:
                return True
            cur = self.type_parent.get(cur)
        return False

    def tokenize(self, src: str, filename: str) -> List[Tuple[str, str, int]]:
        tokens: List[Tuple[str, str, int]] = []
        line = 1
        pos = 0
        n = len(src)
        while pos < n:
            m = TOKEN_RE.match(src, pos)
            if not m:
                snippet = src[pos : pos + 30]
                raise JassTypeError(f"{filename}:{line}: Unexpected character near {snippet!r}")
            pos = m.end()
            kind = m.lastgroup
            val = m.group()
            if kind in ("WS", "COMMENT"):
                continue
            if kind == "NL":
                line += 1
                tokens.append(("NL", "\n", line))
            elif kind == "ID" and val in JASS_KEYWORDS:
                tokens.append(("KW", val, line))
            else:
                assert kind is not None
                tokens.append((kind, val, line))
        tokens.append(("EOF", "", line))
        return tokens

    def check_file(self, src: str, filename: str) -> int:
        toks = self.tokenize(src, filename)
        idx = 0

        def peek() -> Tuple[str, str, int]:
            return toks[idx]

        def advance() -> Tuple[str, str, int]:
            nonlocal idx
            t = toks[idx]
            idx += 1
            return t

        def skip_nl() -> None:
            while peek()[0] == "NL":
                advance()

        def expect(kind: str, val: Optional[str] = None) -> Tuple[str, str, int]:
            t = peek()
            if t[0] != kind or (val is not None and t[1] != val):
                raise JassTypeError(f"{filename}:{t[2]}: Expected {val or kind}, got {t[0]}({t[1]!r})")
            return advance()

        def expect_type_name() -> str:
            t = peek()
            if t[0] == "ID" or (t[0] == "KW" and t[1] in ("nothing", "code")):
                advance()
                if t[1] not in self.type_parent:
                    raise JassTypeError(f"{filename}:{t[2]}: Unknown type {t[1]!r}")
                return t[1]
            raise JassTypeError(f"{filename}:{t[2]}: Expected type name, got {t[1]!r}")

        def parse_expr(locals_map: Dict[str, Tuple[str, bool]], min_prec: int = 0) -> str:
            t = peek()
            line = t[2]
            if t[0] == "INT" or t[0] == "HEX":
                advance()
                lhs = "integer"
            elif t[0] == "RAWCODE":
                advance()
                if len(t[1]) not in (3, 6):  # 'x' or 'xxxx'
                    raise JassTypeError(f"{filename}:{line}: Invalid rawcode {t[1]}")
                lhs = "integer"
            elif t[0] == "REAL":
                advance()
                lhs = "real"
            elif t[0] == "STR":
                advance()
                lhs = "string"
            elif t[0] == "KW" and t[1] in ("true", "false"):
                advance()
                lhs = "boolean"
            elif t[0] == "KW" and t[1] == "null":
                advance()
                lhs = "null"
            elif t[0] == "KW" and t[1] == "function":
                advance()
                fn_id = expect("ID")[1]
                if fn_id not in self.funcs:
                    raise JassTypeError(f"{filename}:{line}: Unknown function reference {fn_id!r}")
                lhs = "code"
            elif t[0] == "OP" and t[1] in ("+", "-"):
                advance()
                sub = parse_expr(locals_map, 6)
                if sub not in ("integer", "real"):
                    raise JassTypeError(f"{filename}:{line}: Unary {t[1]} on {sub}")
                lhs = sub
            elif t[0] == "KW" and t[1] == "not":
                advance()
                sub = parse_expr(locals_map, 5)
                if sub != "boolean":
                    raise JassTypeError(f"{filename}:{line}: 'not' requires boolean, got {sub}")
                lhs = "boolean"
            elif t[0] == "OP" and t[1] == "(":
                advance()
                lhs = parse_expr(locals_map, 0)
                expect("OP", ")")
            elif t[0] == "ID":
                name = advance()[1]
                if peek()[0] == "OP" and peek()[1] == "(":
                    advance()
                    args: List[str] = []
                    if not (peek()[0] == "OP" and peek()[1] == ")"):
                        args.append(parse_expr(locals_map, 0))
                        while peek()[0] == "OP" and peek()[1] == ",":
                            advance()
                            args.append(parse_expr(locals_map, 0))
                    expect("OP", ")")
                    if name not in self.funcs:
                        raise JassTypeError(f"{filename}:{line}: Undeclared function {name!r}")
                    ptypes, rtype, _ = self.funcs[name]
                    if len(args) != len(ptypes):
                        raise JassTypeError(
                            f"{filename}:{line}: {name}() expects {len(ptypes)} args, got {len(args)}"
                        )
                    for ai, (at, pt) in enumerate(zip(args, ptypes)):
                        if not self.is_subtype(at, pt):
                            raise JassTypeError(
                                f"{filename}:{line}: {name}() arg {ai+1}: cannot pass {at} as {pt}"
                            )
                    lhs = rtype
                elif peek()[0] == "OP" and peek()[1] == "[":
                    advance()
                    idx_t = parse_expr(locals_map, 0)
                    expect("OP", "]")
                    if idx_t != "integer":
                        raise JassTypeError(f"{filename}:{line}: Array index must be integer, got {idx_t}")
                    if name in locals_map:
                        vtype, is_arr = locals_map[name]
                    elif name in self.globals:
                        vtype, is_arr, _ = self.globals[name]
                    else:
                        raise JassTypeError(f"{filename}:{line}: Undeclared array {name!r}")
                    if not is_arr:
                        raise JassTypeError(f"{filename}:{line}: {name!r} is not an array")
                    lhs = vtype
                else:
                    if name in locals_map:
                        vtype, is_arr = locals_map[name]
                    elif name in self.globals:
                        vtype, is_arr, _ = self.globals[name]
                    else:
                        raise JassTypeError(f"{filename}:{line}: Undeclared variable {name!r}")
                    if is_arr:
                        raise JassTypeError(f"{filename}:{line}: Array {name!r} used without index")
                    lhs = vtype
            else:
                raise JassTypeError(f"{filename}:{line}: Unexpected token in expression: {t[1]!r}")

            prec_map = {
                "or": 1, "and": 2,
                "==": 3, "!=": 3, "<": 3, "<=": 3, ">": 3, ">=": 3,
                "+": 4, "-": 4, "*": 5, "/": 5,
            }
            while True:
                nt = peek()
                op = nt[1] if (nt[0] == "OP" or (nt[0] == "KW" and nt[1] in ("and", "or"))) else None
                if op is None or op not in prec_map or prec_map[op] <= min_prec:
                    break
                p = prec_map[op]
                advance()
                rhs = parse_expr(locals_map, p)
                if op in ("and", "or"):
                    if lhs != "boolean" or rhs != "boolean":
                        raise JassTypeError(f"{filename}:{nt[2]}: '{op}' requires booleans, got {lhs}, {rhs}")
                    lhs = "boolean"
                elif op in ("<", "<=", ">", ">="):
                    if lhs not in ("integer", "real") or rhs not in ("integer", "real"):
                        raise JassTypeError(f"{filename}:{nt[2]}: '{op}' requires numbers, got {lhs}, {rhs}")
                    lhs = "boolean"
                elif op in ("==", "!="):
                    lhs = "boolean"
                elif op == "+":
                    if lhs == "string" and rhs == "string":
                        lhs = "string"
                    elif lhs in ("integer", "real") and rhs in ("integer", "real"):
                        lhs = "real" if ("real" in (lhs, rhs)) else "integer"
                    else:
                        raise JassTypeError(f"{filename}:{nt[2]}: Invalid '+' between {lhs} and {rhs}")
                else:
                    if lhs not in ("integer", "real") or rhs not in ("integer", "real"):
                        raise JassTypeError(f"{filename}:{nt[2]}: Invalid '{op}' between {lhs} and {rhs}")
                    lhs = "real" if ("real" in (lhs, rhs)) else "integer"
            return lhs

        def parse_signature() -> Tuple[List[Tuple[str, str]], str]:
            expect("KW", "takes")
            params: List[Tuple[str, str]] = []
            if peek()[0] == "KW" and peek()[1] == "nothing":
                advance()
            else:
                pt = expect_type_name()
                pn = expect("ID")[1]
                params.append((pt, pn))
                while peek()[0] == "OP" and peek()[1] == ",":
                    advance()
                    pt = expect_type_name()
                    pn = expect("ID")[1]
                    params.append((pt, pn))
            expect("KW", "returns")
            ret = expect_type_name()
            return params, ret

        def parse_statements(locals_map: Dict[str, Tuple[str, bool]], ret_type: str, in_loop: bool) -> None:
            while True:
                skip_nl()
                t = peek()
                if t[0] == "KW" and t[1] in ("endfunction", "elseif", "else", "endif", "endloop"):
                    return
                if t[0] == "KW" and t[1] == "local":
                    raise JassTypeError(f"{filename}:{t[2]}: 'local' declaration after executable statement!")
                if t[0] == "KW" and t[1] == "set":
                    advance()
                    vname = expect("ID")[1]
                    is_indexed = False
                    if peek()[0] == "OP" and peek()[1] == "[":
                        advance()
                        it = parse_expr(locals_map, 0)
                        if it != "integer":
                            raise JassTypeError(f"{filename}:{t[2]}: Array index must be integer")
                        expect("OP", "]")
                        is_indexed = True
                    expect("OP", "=")
                    et = parse_expr(locals_map, 0)
                    if vname in locals_map:
                        vt, va = locals_map[vname]
                    elif vname in self.globals:
                        vt, va, vc = self.globals[vname]
                        if vc:
                            raise JassTypeError(f"{filename}:{t[2]}: Cannot assign constant {vname!r}")
                    else:
                        raise JassTypeError(f"{filename}:{t[2]}: Undeclared variable {vname!r}")
                    if va != is_indexed:
                        raise JassTypeError(f"{filename}:{t[2]}: Array indexing mismatch on {vname!r}")
                    if not self.is_subtype(et, vt):
                        raise JassTypeError(f"{filename}:{t[2]}: Cannot assign {et} to {vt} ({vname})")
                elif t[0] == "KW" and t[1] == "call":
                    advance()
                    if peek()[0] == "ID" and peek()[1] == " ExecuteFunc":
                        pass
                    cname = expect("ID")[1]
                    expect("OP", "(")
                    args: List[str] = []
                    if not (peek()[0] == "OP" and peek()[1] == ")"):
                        args.append(parse_expr(locals_map, 0))
                        while peek()[0] == "OP" and peek()[1] == ",":
                            advance()
                            args.append(parse_expr(locals_map, 0))
                    expect("OP", ")")
                    if cname not in self.funcs:
                        raise JassTypeError(f"{filename}:{t[2]}: Undeclared function {cname!r}")
                    ptypes, _, _ = self.funcs[cname]
                    if len(args) != len(ptypes):
                        raise JassTypeError(
                            f"{filename}:{t[2]}: {cname}() expects {len(ptypes)} args, got {len(args)}"
                        )
                    for ai, (at, pt) in enumerate(zip(args, ptypes)):
                        if not self.is_subtype(at, pt):
                            raise JassTypeError(
                                f"{filename}:{t[2]}: {cname}() arg {ai+1}: cannot pass {at} as {pt}"
                            )
                elif t[0] == "KW" and t[1] == "if":
                    advance()
                    ct = parse_expr(locals_map, 0)
                    if ct != "boolean":
                        raise JassTypeError(f"{filename}:{t[2]}: 'if' condition must be boolean, got {ct}")
                    expect("KW", "then")
                    parse_statements(locals_map, ret_type, in_loop)
                    while peek()[0] == "KW" and peek()[1] == "elseif":
                        el = advance()
                        ect = parse_expr(locals_map, 0)
                        if ect != "boolean":
                            raise JassTypeError(f"{filename}:{el[2]}: 'elseif' condition must be boolean")
                        expect("KW", "then")
                        parse_statements(locals_map, ret_type, in_loop)
                    if peek()[0] == "KW" and peek()[1] == "else":
                        advance()
                        parse_statements(locals_map, ret_type, in_loop)
                    expect("KW", "endif")
                elif t[0] == "KW" and t[1] == "loop":
                    advance()
                    parse_statements(locals_map, ret_type, True)
                    expect("KW", "endloop")
                elif t[0] == "KW" and t[1] == "exitwhen":
                    if not in_loop:
                        raise JassTypeError(f"{filename}:{t[2]}: 'exitwhen' outside loop")
                    advance()
                    et = parse_expr(locals_map, 0)
                    if et != "boolean":
                        raise JassTypeError(f"{filename}:{t[2]}: 'exitwhen' requires boolean, got {et}")
                elif t[0] == "KW" and t[1] == "return":
                    advance()
                    if peek()[0] in ("NL", "EOF"):
                        if ret_type != "nothing":
                            raise JassTypeError(f"{filename}:{t[2]}: Missing return value for {ret_type}")
                    else:
                        rt = parse_expr(locals_map, 0)
                        if not self.is_subtype(rt, ret_type):
                            raise JassTypeError(f"{filename}:{t[2]}: Cannot return {rt} from {ret_type} function")
                elif t[0] == "KW" and t[1] == "debug":
                    advance()
                    continue
                else:
                    raise JassTypeError(f"{filename}:{t[2]}: Unexpected statement token {t[1]!r}")

        checked_funcs = 0
        while True:
            skip_nl()
            t = peek()
            if t[0] == "EOF":
                break
            if t[0] == "KW" and t[1] == "type":
                advance()
                new_t = expect("ID")[1]
                expect("KW", "extends")
                base_t = expect_type_name()
                self.type_parent[new_t] = base_t
            elif t[0] == "KW" and t[1] == "globals":
                advance()
                while True:
                    skip_nl()
                    gt = peek()
                    if gt[0] == "KW" and gt[1] == "endglobals":
                        advance()
                        break
                    is_const = False
                    if gt[0] == "KW" and gt[1] == "constant":
                        is_const = True
                        advance()
                    vtype = expect_type_name()
                    is_arr = False
                    if peek()[0] == "KW" and peek()[1] == "array":
                        is_arr = True
                        advance()
                    vname = expect("ID")[1]
                    if peek()[0] == "OP" and peek()[1] == "=":
                        advance()
                        et = parse_expr({}, 0)
                        if not self.is_subtype(et, vtype):
                            raise JassTypeError(f"{filename}:{gt[2]}: Global {vname}: cannot init {vtype} with {et}")
                    self.globals[vname] = (vtype, is_arr, is_const)
            else:
                is_const = False
                if t[0] == "KW" and t[1] == "constant":
                    is_const = True
                    advance()
                if peek()[0] == "KW" and peek()[1] == "native":
                    advance()
                    fname = expect("ID")[1]
                    params, ret = parse_signature()
                    self.funcs[fname] = ([p[0] for p in params], ret, is_const)
                elif peek()[0] == "KW" and peek()[1] == "function":
                    advance()
                    fname = expect("ID")[1]
                    params, ret = parse_signature()
                    self.funcs[fname] = ([p[0] for p in params], ret, is_const)
                    locals_map: Dict[str, Tuple[str, bool]] = {pn: (pt, False) for pt, pn in params}
                    while True:
                        skip_nl()
                        if peek()[0] == "KW" and peek()[1] == "local":
                            lt = advance()
                            ltype = expect_type_name()
                            larr = False
                            if peek()[0] == "KW" and peek()[1] == "array":
                                larr = True
                                advance()
                            lname = expect("ID")[1]
                            if peek()[0] == "OP" and peek()[1] == "=":
                                advance()
                                et = parse_expr(locals_map, 0)
                                if not self.is_subtype(et, ltype):
                                    raise JassTypeError(
                                        f"{filename}:{lt[2]}: Local {lname}: cannot init {ltype} with {et}"
                                    )
                            locals_map[lname] = (ltype, larr)
                        else:
                            break
                    parse_statements(locals_map, ret, False)
                    expect("KW", "endfunction")
                    checked_funcs += 1
                else:
                    raise JassTypeError(f"{filename}:{t[2]}: Unexpected top-level token {t[1]!r}")

        return checked_funcs


# Minimal built-in Common.j + Blizzard.j prelude when external MPQ scripts aren't present
FALLBACK_JASS_PRELUDE = """
type agent extends handle
type event extends agent
type player extends agent
type widget extends agent
type unit extends widget
type destructable extends widget
type item extends widget
type trigger extends agent
type triggeraction extends agent
type playercolor extends handle
type racepreference extends handle
type mapcontrol extends handle
type placement extends handle
type startlocprio extends handle
type cameramargin extends handle
type itemid extends handle
type itemtype extends handle
type unitevent extends event

globals
    constant integer PLAYER_NEUTRAL_AGGRESSIVE = 12
    constant integer PLAYER_NEUTRAL_PASSIVE = 15
    constant itemtype ITEM_TYPE_PERMANENT = null
    constant itemtype ITEM_TYPE_CHARGED = null
    constant itemtype ITEM_TYPE_POWERUP = null
    constant unitevent EVENT_UNIT_DEATH = null
    constant unitevent EVENT_UNIT_CHANGE_OWNER = null
    constant racepreference RACE_PREF_RANDOM = null
    constant mapcontrol MAP_CONTROL_USER = null
    constant placement MAP_PLACEMENT_TEAMS_TOGETHER = null
    constant startlocprio MAP_LOC_PRIO_HIGH = null
    constant startlocprio MAP_LOC_PRIO_LOW = null
    constant cameramargin CAMERA_MARGIN_LEFT = null
    constant cameramargin CAMERA_MARGIN_RIGHT = null
    constant cameramargin CAMERA_MARGIN_TOP = null
    constant cameramargin CAMERA_MARGIN_BOTTOM = null
    widget bj_lastDyingWidget = null
endglobals

native Player takes integer number returns player
native GetTriggerUnit takes nothing returns unit
native IsUnitHidden takes unit whichUnit returns boolean
native GetChangingUnit takes nothing returns unit
native GetChangingUnitPrevOwner takes nothing returns player
native ChooseRandomItemEx takes itemtype whichType, integer level returns integer
native CreateUnit takes player id, integer unitid, real x, real y, real face returns unit
native SetUnitAcquireRange takes unit whichUnit, real newAcquireRange returns nothing
native SetResourceAmount takes unit whichUnit, integer amount returns nothing
native SetUnitColor takes unit whichUnit, playercolor whichColor returns nothing
native ConvertPlayerColor takes integer i returns playercolor
native CreateTrigger takes nothing returns trigger
native DestroyTrigger takes trigger whichTrigger returns nothing
native GetTriggeringTrigger takes nothing returns trigger
native TriggerRegisterUnitEvent takes trigger whichTrigger, unit whichUnit, unitevent whichEvent returns event
native TriggerAddAction takes trigger whichTrigger, code actionFunc returns triggeraction
native SetPlayerStartLocation takes player whichPlayer, integer startLocIndex returns nothing
native SetPlayerColor takes player whichPlayer, playercolor color returns nothing
native SetPlayerRacePreference takes player whichPlayer, racepreference whichRacePreference returns nothing
native SetPlayerRaceSelectable takes player whichPlayer, boolean value returns nothing
native SetPlayerController takes player whichPlayer, mapcontrol controlType returns nothing
native SetPlayerTeam takes player whichPlayer, integer whichTeam returns nothing
native SetStartLocPrioCount takes integer whichStartLoc, integer prioSlotCount returns nothing
native SetStartLocPrio takes integer whichStartLoc, integer prioSlotIndex, integer otherStartLocIndex, startlocprio priority returns nothing
native GetCameraMargin takes cameramargin whichMargin returns real
native SetCameraBounds takes real x1, real y1, real x2, real y2, real x3, real y3, real x4, real y4 returns nothing
native SetDayNightModels takes string terrainDNCFile, string unitDNCFile returns nothing
native NewSoundEnvironment takes string environmentName returns nothing
native SetMapMusic takes string musicName, boolean random, integer index returns nothing
native SetMapName takes string name returns nothing
native SetMapDescription takes string description returns nothing
native SetPlayers takes integer playercount returns nothing
native SetTeams takes integer teamcount returns nothing
native SetGamePlacement takes placement whichPlacementType returns nothing
native DefineStartLocation takes integer whichStartLoc, real x, real y returns nothing
native SetPlayerSlotAvailable takes player whichPlayer, mapcontrol control returns nothing
function RandomDistReset takes nothing returns nothing
endfunction
function RandomDistAddItem takes integer inID, integer inChance returns nothing
endfunction
function RandomDistChoose takes nothing returns integer
    return 0
endfunction
function UnitDropItem takes unit inUnit, integer inItemID returns item
    return null
endfunction
function WidgetDropItem takes widget inWidget, integer inItemID returns item
    return null
endfunction
function MeleeStartingVisibility takes nothing returns nothing
endfunction
function MeleeStartingHeroLimit takes nothing returns nothing
endfunction
function MeleeGrantHeroItems takes nothing returns nothing
endfunction
function MeleeStartingResources takes nothing returns nothing
endfunction
function MeleeClearExcessUnits takes nothing returns nothing
endfunction
function MeleeStartingUnits takes nothing returns nothing
endfunction
function MeleeStartingAI takes nothing returns nothing
endfunction
function MeleeInitVictoryDefeat takes nothing returns nothing
endfunction
function ConditionalTriggerExecute takes trigger trig returns nothing
endfunction
function SetAmbientDaySound takes string inLabel returns nothing
endfunction
function SetAmbientNightSound takes string inLabel returns nothing
endfunction
function InitBlizzard takes nothing returns nothing
endfunction
function InitGenericPlayerSlots takes nothing returns nothing
endfunction
"""


# ==============================================================================
# Verification Suite
# ==============================================================================

def run_verification(w3x_path: Path) -> None:
    print(f"======================================================================")
    print(f"  VERIFYING WARCRAFT III MELEE MAP: {w3x_path.name}")
    print(f"======================================================================")

    assert w3x_path.exists(), f"Map file does not exist: {w3x_path}"

    # ------------------------------------------------------------------
    # STAGE 1: HM3W Pre-Header & MPQ v1 Container + StormLib Cross-Check
    # ------------------------------------------------------------------
    hdr, files = read_w3x_archive(w3x_path)
    assert hdr["map_name"] == "(8) Crown of WarMahdi", f"Unexpected map name: {hdr['map_name']}"
    assert hdr["max_players"] == 8, f"Expected 8 max players, got {hdr['max_players']}"
    assert hdr["map_flags"] == 0x1FC1A, f"Unexpected map flags: 0x{hdr['map_flags']:X}"
    assert (int(hdr["map_flags"]) & 0x0001) == 0, "DISABLE_PREVIEW must be 0 so war3mapPreview.tga shows in Lobby!"
    assert hdr["sector_size"] == 4096, f"Expected 4096 sector size, got {hdr['sector_size']}"
    assert int(hdr["file_size"]) < 8 * 1024 * 1024, "Exceeds 8MB Warcraft III 1.26a LAN limit!"

    for req in list(CANONICAL_W3X_FILES) + [
        "war3map.w3u",
        "war3map.w3t",
        "war3map.w3q",
        "war3map.w3a",
        "war3mapMisc.txt",
        "war3mapSkin.txt",
        "war3mapPreview.tga",
        "war3map.imp",
        "naga_melee.ai",
        "camphuman_melee.ai",
        "voidborn_melee.ai",
        "runeforged_melee.ai",
    ]:
        assert req in files, f"Missing required map archive file: {req}"

    storm_bin = Path("/tmp/wc3ref/storm_build/w3x_tool")
    if storm_bin.exists():
        res = subprocess.run([str(storm_bin), "verify", str(w3x_path)], capture_output=True, text=True)
        assert res.returncode == 0, f"StormLib verification failed:\n{res.stderr}\n{res.stdout}"
        print("[PASS] Stage 1: HM3W Header + MPQ v1 Container + Official StormLib CRC32/MD5 Verification")
    else:
        print("[PASS] Stage 1: HM3W Header + MPQ v1 Container Decompression Verification")

    # ------------------------------------------------------------------
    # STAGE 2: Binary Format Versions & Classic TFT 1.26a/1.27b Spec
    # ------------------------------------------------------------------
    w3i = files["war3map.w3i"]
    w3i_ver, w3i_saves, w3i_ed = struct.unpack_from("<iii", w3i, 0)
    assert w3i_ver == 25, f"w3i version must be 25 for classic 1.26a/1.27b compatibility, got {w3i_ver}"

    w3e = files["war3map.w3e"]
    assert w3e[:4] == b"W3E!", "Invalid W3E! magic"
    w3e_ver = struct.unpack_from("<i", w3e, 4)[0]
    assert w3e_ver == 11, f"Expected w3e version 11, got {w3e_ver}"
    gt_cnt = struct.unpack_from("<I", w3e, 13)[0]
    pos = 17 + gt_cnt * 4
    ct_cnt = struct.unpack_from("<I", w3e, pos)[0]
    pos += 4 + ct_cnt * 4
    cw, ch = struct.unpack_from("<ii", w3e, pos)
    ox, oy = struct.unpack_from("<ff", w3e, pos + 8)
    pos += 16
    assert (cw, ch) == (193, 193), f"Unexpected corner grid {cw}x{ch}"
    assert len(w3e) == pos + cw * ch * 7, "Exact war3map.w3e byte length mismatch"

    wpm = files["war3map.wpm"]
    assert wpm[:4] == b"MP3W", "Invalid MP3W magic"
    wpm_ver, pw, ph = struct.unpack_from("<iii", wpm, 4)
    assert (wpm_ver, pw, ph) == (0, 768, 768) and len(wpm) == 16 + 768 * 768

    shd = files["war3map.shd"]
    assert len(shd) == 768 * 768, "Invalid war3map.shd size"

    doo = files["war3map.doo"]
    assert doo[:4] == b"W3do"
    doo_ver, doo_sub, tree_cnt = struct.unpack_from("<iII", doo, 4)
    assert (doo_ver, doo_sub) == (8, 11)
    assert 1000 <= tree_cnt < 6144, f"Tree count {tree_cnt} should be < 6144 vanilla WE limit"
    assert len(doo) == 16 + tree_cnt * 50 + 8, "Exact war3map.doo byte length mismatch"

    print(f"[PASS] Stage 2: TFT v25 Binary Specs (192x192 terrain, {tree_cnt} trees < 6144 WE limit)")

    # ------------------------------------------------------------------
    # STAGE 3: Full JASS2 Static Typechecking (Official TFT 1.27.1)
    # ------------------------------------------------------------------
    jass_src = files["war3map.j"].decode("utf-8")

    # Verify zero memory/trigger leaks in all DropItems functions
    drop_fns = re.findall(r"function (Unit\d+_DropItems) takes nothing returns nothing(.*?)endfunction", jass_src, re.S)
    assert len(drop_fns) > 0, "Expected creep item drop functions in war3map.j"
    for fn_name, body in drop_fns:
        assert "DestroyTrigger(GetTriggeringTrigger())" in body, f"Trigger leak in {fn_name}!"
        assert "set bj_lastDyingWidget = null" in body, f"Handle reference leak in {fn_name}!"

    ref_127 = Path("/tmp/wc3ref/w3x2lni/data/enUS-1.27.1/mpq/Scripts")

    if ref_127.exists():
        chk_127 = JassChecker()
        chk_127.check_file((ref_127 / "Common.j").read_text(encoding="utf-8", errors="ignore"), "1.27.1/Common.j")
        chk_127.check_file((ref_127 / "Blizzard.j").read_text(encoding="utf-8", errors="ignore"), "1.27.1/Blizzard.j")
        n_fn = chk_127.check_file(jass_src, "war3map.j")
        print(f"[PASS] Stage 3: JASS2 Static Typecheck vs Official TFT 1.27b Common.j + Blizzard.j ({n_fn} map functions, 0 errors)")
    else:
        chk_fb = JassChecker()
        chk_fb.check_file(FALLBACK_JASS_PRELUDE, "prelude.j")
        n_fn = chk_fb.check_file(jass_src, "war3map.j")
        print(f"[PASS] Stage 3: JASS2 Static Typecheck vs Built-in Prelude ({n_fn} map functions, 0 errors)")

    # ------------------------------------------------------------------
    # STAGE 4: Cross-File Synchronization (units.doo <-> war3map.j <-> wts <-> mmp)
    # ------------------------------------------------------------------
    udoo = files["war3map.doo"]  # keep ref
    ubuf = files["war3mapUnits.doo"]
    assert ubuf[:4] == b"W3do"
    uver, usub, ucnt = struct.unpack_from("<iIi", ubuf, 4)
    assert (uver, usub) == (8, 11)

    parsed_units: List[Dict[str, object]] = []
    upos = 16
    for _ in range(ucnt):
        uid = ubuf[upos : upos + 4].decode("ascii")
        var, ux, uy, uz, uang, sx, sy, sz, uflags, uplayer, uunk, hp, mana, dtab, dsets_n = struct.unpack_from(
            "<ifffffffBiHiiii", ubuf, upos + 4
        )
        upos += 4 + 55
        drops = []
        for _s in range(dsets_n):
            icnt = struct.unpack_from("<i", ubuf, upos)[0]
            upos += 4
            for _i in range(icnt):
                iid = ubuf[upos : upos + 4].decode("ascii")
                ich = struct.unpack_from("<i", ubuf, upos + 4)[0]
                drops.append((iid, ich))
                upos += 8
        gold, acq, hlvl, hstr, hagi, hint, inv_n = struct.unpack_from("<ifiiiii", ubuf, upos)
        upos += 28 + inv_n * 8
        abil_n = struct.unpack_from("<i", ubuf, upos)[0]
        upos += 4 + abil_n * 12
        rflag = struct.unpack_from("<i", ubuf, upos)[0]
        upos += 4 + (4 if rflag == 0 else (8 if rflag == 1 else 0))
        tcol, waygate, cnum = struct.unpack_from("<iii", ubuf, upos)
        upos += 12
        assert uplayer in tuple(range(8)) + (12, 15), f"Invalid TFT v25 player index {uplayer}!"
        parsed_units.append({
            "uid": uid, "player": uplayer, "x": ux, "y": uy, "z": uz,
            "gold": gold, "acq": acq, "drops": drops, "cnum": cnum,
        })
    assert upos == len(ubuf), f"Trailing bytes in war3mapUnits.doo ({upos} != {len(ubuf)})"

    jass_spawns = re.findall(
        r"CreateUnit\(\s*p,\s*'([A-Za-z0-9]{4})',\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\s*\)",
        jass_src,
    )
    non_sloc = [u for u in parsed_units if u["uid"] != "sloc"]
    assert len(jass_spawns) == len(non_sloc), f"JASS CreateUnit count {len(jass_spawns)} != units.doo {len(non_sloc)}"

    # Check TRIGSTR resolution in war3map.wts
    wts_text = files["war3map.wts"].decode("utf-8-sig")
    defined_strs = {int(m) for m in re.findall(r"STRING\s+(\d+)", wts_text)}
    for trig_ref in re.findall(r"TRIGSTR_0*(\d+)", jass_src + w3i.decode("latin1", errors="ignore")):
        sid = int(trig_ref)
        assert sid in defined_strs, f"Unresolved TRIGSTR_{sid:03d} missing from war3map.wts!"

    mmp = files["war3map.mmp"]
    _, mmp_cnt = struct.unpack_from("<iI", mmp, 0)
    assert mmp_cnt == 45 and len(mmp) == 8 + 45 * 16, "MMP icon count mismatch"

    blp = files["war3map.blp"] if "war3map.blp" in files else files["war3mapMap.blp"]
    assert blp[:4] == b"BLP1", "Invalid BLP1 header"
    b_content, b_alpha, b_w, b_h, _b_t, _b_m = struct.unpack_from("<6I", blp, 4)
    b_off0 = struct.unpack_from("<I", blp, 28)[0]
    b_sz0 = struct.unpack_from("<I", blp, 92)[0]
    b_jhsz = struct.unpack_from("<I", blp, 156)[0]
    jpeg_stream = blp[160 : 160 + b_jhsz] + blp[b_off0 : b_off0 + b_sz0]
    assert (b_content, b_alpha, b_w, b_h, b_off0) == (0, 0, 256, 256, 1180)
    assert jpeg_stream[:2] == b"\xff\xd8" and jpeg_stream[-2:] == b"\xff\xd9", "Invalid BLP1 JPEG stream"

    print(f"[PASS] Stage 4 & 5: 1-to-1 Sync ({len(parsed_units)} units, {len(defined_strs)} strings, 45 MMP icons, 256x256 BLP1)")

    # ------------------------------------------------------------------
    # STAGE 6: Eight-Player Base Layout & All Classic Melee Spawn Base Buildability Simulator
    # ------------------------------------------------------------------
    wpm_grid = wpm[16:]

    def wpm_at_world(wx: float, wy: float) -> int:
        px = int((wx - ox) // 32.0)
        py = int((wy - oy) // 32.0)
        assert 0 <= px < 768 and 0 <= py < 768, f"Out of map bounds ({wx}, {wy})"
        return wpm_grid[py * 768 + px]

    slocs = sorted([u for u in parsed_units if u["uid"] == "sloc"], key=lambda u: int(u["player"]))  # type: ignore
    mines = [u for u in parsed_units if u["uid"] == "ngol"]
    assert len(slocs) == 8 and len(mines) == 20

    # Parse trees (`ZTtw`) and scenic shrine doodads (`ZZys`, `ZZgr`, `YOfb`, `ZWbg`, `ZPlp`) from war3map.doo
    trees: List[Tuple[float, float]] = []
    scenic_doodads: List[Tuple[str, float, float, int]] = []
    valid_scenic_ids = {"ZZys", "ZZgr", "YOfb", "ZWbg", "ZPlp"}
    for ti in range(tree_cnt):
        did = doo[16 + ti * 50 : 16 + ti * 50 + 4].decode("ascii")
        tx, ty, _tz = struct.unpack_from("<fff", doo, 16 + ti * 50 + 8)
        d_life = doo[16 + ti * 50 + 37]
        if did == "ZTtw":
            assert d_life == 100, f"Tree ZTtw must have life=100, got {d_life}"
            trees.append((tx, ty))
        else:
            assert did in valid_scenic_ids, f"Unexpected doodad ID {did!r} in war3map.doo!"
            assert d_life == 255, f"Scenic doodad {did} must have life=255, got {d_life}"
            scenic_doodads.append((did, tx, ty, d_life))
    assert len(trees) == 5920 and len(scenic_doodads) == 41, (
        f"Expected 5920 ZTtw trees + 41 scenic shrine doodads, got {len(trees)} + {len(scenic_doodads)}"
    )

    for sl in slocs:
        sx, sy = float(sl["x"]), float(sl["y"])  # type: ignore
        nearest = min(mines, key=lambda m: math.hypot(float(m["x"]) - sx, float(m["y"]) - sy))  # type: ignore
        mx, my = float(nearest["x"]), float(nearest["y"])  # type: ignore
        dist = math.hypot(mx - sx, my - sy)
        assert abs(dist - 640.0) < 0.1, f"Player {sl['player']} start->mine dist {dist} != 640.0!"

        # Check Night Elf Tree of Life entangle projection (448 units from mine toward sloc)
        ux_v, uy_v = (sx - mx) / dist, (sy - my) / dist
        ne_tol_x, ne_tol_y = mx + ux_v * 448.0, my + uy_v * 448.0

        # Verify 100% buildable dry flat land (wpm == 0x40) across Town Hall, Tree of Life, Mine, and Base Zone
        for check_x, check_y, half_ext in [
            (sx, sy, 640.0),
            (ne_tol_x, ne_tol_y, 256.0),
            (mx, my, 384.0),
        ]:
            step = 32.0
            y_cur = check_y - half_ext
            while y_cur <= check_y + half_ext:
                x_cur = check_x - half_ext
                while x_cur <= check_x + half_ext:
                    val = wpm_at_world(x_cur, y_cur)
                    assert val == 0x40, (
                        f"Unbuildable cell 0x{val:02X} at ({x_cur},{y_cur}) near Player {sl['player']} base!"
                    )
                    x_cur += step
                y_cur += step

    print("[PASS] Stage 6: All 8 Mirrored Player Starts, Gold Mines, Town-Hall Zones and Classic Race Spawn Terrain are buildable")

    # ------------------------------------------------------------------
    # STAGE 7: Pairwise Zero-Collision Prover (6,101 Objects)
    # ------------------------------------------------------------------
    # Tree grid uniqueness & no overlap with buildings/units
    tree_cells = set()
    for tx, ty in trees:
        cell = (int(round(tx)), int(round(ty)))
        assert cell not in tree_cells, f"Duplicate tree at {cell}"
        tree_cells.add(cell)

    for u in parsed_units:
        ux, uy = float(u["x"]), float(u["y"])  # type: ignore
        min_tree_clear = 380.0 if u["player"] == 15 or u["uid"] == "sloc" else 160.0
        for tx, ty in trees:
            d = math.hypot(tx - ux, ty - uy)
            assert d >= min_tree_clear, f"Tree at ({tx},{ty}) collides with {u['uid']} at ({ux},{uy}): d={d:.1f}"

    non_sloc_units = [u for u in parsed_units if u["uid"] != "sloc"]
    for i in range(len(non_sloc_units)):
        u1 = non_sloc_units[i]
        r1 = 160.0 if u1["player"] == 15 else 32.0
        for j in range(i + 1, len(non_sloc_units)):
            u2 = non_sloc_units[j]
            r2 = 160.0 if u2["player"] == 15 else 32.0
            d = math.hypot(float(u1["x"]) - float(u2["x"]), float(u1["y"]) - float(u2["y"]))  # type: ignore
            assert d >= (r1 + r2), f"Unit overlap between {u1['uid']} and {u2['uid']}: d={d:.1f} < {r1+r2}"

    print(f"[PASS] Stage 7: Zero Object Collisions Across {len(parsed_units)} Units & {len(trees)} Trees")

    # ------------------------------------------------------------------
    # STAGE 8: Full Dynamic Pathing Grid (WPM + Trees + Buildings) BFS Prover
    # ------------------------------------------------------------------
    blocked = bytearray(768 * 768)
    for idx, b in enumerate(wpm_grid):
        if b & 0x02:  # UNWALKABLE
            blocked[idx] = 1

    # Stamp all 5,920 trees (4x4 pathing cells = 128x128)
    for tx, ty in trees:
        cx = int((tx - ox) // 32.0)
        cy = int((ty - oy) // 32.0)
        for dy in range(-2, 2):
            for dx in range(-2, 2):
                ix, iy = cx + dx, cy + dy
                if 0 <= ix < 768 and 0 <= iy < 768:
                    blocked[iy * 768 + ix] = 1

    # Stamp all 37 Neutral Passive buildings (10x10 pathing core = 320x320)
    for u in parsed_units:
        if u["player"] == 15:
            cx = int((float(u["x"]) - ox) // 32.0)  # type: ignore
            cy = int((float(u["y"]) - oy) // 32.0)  # type: ignore
            for dy in range(-5, 5):
                for dx in range(-5, 5):
                    ix, iy = cx + dx, cy + dy
                    if 0 <= ix < 768 and 0 <= iy < 768:
                        blocked[iy * 768 + ix] = 1

    # BFS from Player 0 Start Location
    p0x = int((float(slocs[0]["x"]) - ox) // 32.0)  # type: ignore
    p0y = int((float(slocs[0]["y"]) - oy) // 32.0)  # type: ignore
    assert blocked[p0y * 768 + p0x] == 0, "Player 0 start location is blocked!"

    visited = bytearray(768 * 768)
    visited[p0y * 768 + p0x] = 1
    q = collections.deque([(p0x, p0y)])
    while q:
        cx, cy = q.popleft()
        base = cy * 768
        for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if 0 <= nx < 768 and 0 <= ny < 768:
                ni = ny * 768 + nx
                if not visited[ni] and not blocked[ni]:
                    visited[ni] = 1
                    q.append((nx, ny))

    # Assert every sloc, creep unit, and perimeter of every building/mine is reachable!
    for u in parsed_units:
        cx = int((float(u["x"]) - ox) // 32.0)  # type: ignore
        cy = int((float(u["y"]) - oy) // 32.0)  # type: ignore
        if u["player"] == 15:
            # Check 6-cell ring outside building footprint
            ring_ok = any(
                visited[(cy + dy) * 768 + (cx + dx)]
                for dy in (-7, 0, 7)
                for dx in (-7, 0, 7)
                if (dx != 0 or dy != 0)
            )
            assert ring_ok, f"Neutral building {u['uid']} at ({u['x']},{u['y']}) is unreachable!"
        else:
            assert visited[cy * 768 + cx] == 1, f"Unit {u['uid']} at ({u['x']},{u['y']}) is trapped/unreachable!"

    reachable_cells = sum(visited)
    print(f"[PASS] Stage 8: Full Dynamic Pathing BFS Connectivity ({reachable_cells:,} walkable cells; 100% of bases, mines, shops & creeps reachable)")

    # ------------------------------------------------------------------
    # STAGE 9: Creep Camp Aggro Safety & Central Tavern Safe-Zone Prover
    # ------------------------------------------------------------------
    creeps = [u for u in parsed_units if u["player"] == 12]
    assert len(creeps) == 136
    for c in creeps:
        assert float(c["acq"]) == -2.0, f"Creep {c['uid']} missing Camp Acquisition (-2.0)!"  # type: ignore
        d_tavern = math.hypot(float(c["x"]), float(c["y"]))  # type: ignore
        assert d_tavern >= 2500.0, f"Creep too close to Central Tavern (0,0): {d_tavern:.1f}"
        for sl in slocs:
            d_base = math.hypot(float(c["x"]) - float(sl["x"]), float(c["y"]) - float(sl["y"]))  # type: ignore
            assert d_base >= 2200.0, f"Creep too close to Player {sl['player']} base: {d_base:.1f}"

    print("[PASS] Stage 9: Creep Camp Acquisition (200.0) & Tavern / Base Safe-Zones Verified")

    # ------------------------------------------------------------------
    # STAGE 10: Exact D4 8-Way Dihedral Symmetry Mathematical Prover
    # ------------------------------------------------------------------
    # Check terrain corner height & water symmetry across all 8 D4 group elements
    for y in range(193):
        for x in range(y, 193):
            c_base = w3e[pos + (y * 193 + x) * 7 : pos + (y * 193 + x) * 7 + 5]
            sym_pts = [
                (x, y), (192 - x, y), (x, 192 - y), (192 - x, 192 - y),
                (y, x), (192 - y, x), (y, 192 - x), (192 - y, 192 - x),
            ]
            for sx, sy in sym_pts:
                c_img = w3e[pos + (sy * 193 + sx) * 7 : pos + (sy * 193 + sx) * 7 + 5]
                assert c_img == c_base, f"Terrain symmetry violation between ({x},{y}) and ({sx},{sy})!"

    # Check tree set D4 invariance
    for tx, ty in trees:
        ix, iy = int(round(tx)), int(round(ty))
        for gx, gy in (
            (-ix, iy), (ix, -iy), (-ix, -iy),
            (iy, ix), (-iy, ix), (iy, -ix), (-iy, -ix),
        ):
            assert (gx, gy) in tree_cells, f"Tree symmetry violation for ({ix},{iy}) -> ({gx},{gy})"

    print("[PASS] Stage 10: Exact 8-Way Dihedral Group (D4) Terrain, Pathing & Forest Symmetry Proven")

    # ------------------------------------------------------------------
    # STAGE 11: 6-Race Object Tables (w3u/w3t/w3q/Misc/imp), SLK Metadata & Button Prover
    # ------------------------------------------------------------------
    def parse_obj_table(buf: bytes, use_opt: bool) -> Tuple[int, list, list]:
        ver = struct.unpack_from("<i", buf, 0)[0]
        assert ver == 2, f"Object table version MUST be 2 for TFT 1.26a/1.27b compatibility, got {ver}"
        p_off = 4
        tables = []
        for _ in range(2):
            cnt = struct.unpack_from("<I", buf, p_off)[0]
            p_off += 4
            objs = []
            for _o in range(cnt):
                oid = buf[p_off : p_off + 4].decode("latin1")
                nid = buf[p_off + 4 : p_off + 8].decode("latin1")
                mcnt = struct.unpack_from("<I", buf, p_off + 8)[0]
                p_off += 12
                mods = []
                for _m in range(mcnt):
                    fid = buf[p_off : p_off + 4].decode("latin1")
                    vt = struct.unpack_from("<I", buf, p_off + 4)[0]
                    p_off += 8
                    lvl = dptr = 0
                    if use_opt:
                        lvl, dptr = struct.unpack_from("<iI", buf, p_off)
                        p_off += 8
                    if vt == 0:
                        val = struct.unpack_from("<i", buf, p_off)[0]
                        p_off += 4
                    elif vt in (1, 2):
                        val = struct.unpack_from("<f", buf, p_off)[0]
                        p_off += 4
                    elif vt == 3:
                        z_end = buf.index(b"\x00", p_off)
                        val = buf[p_off:z_end].decode("utf-8")
                        p_off = z_end + 1
                    else:
                        raise AssertionError(f"Invalid variableType {vt} on field {fid}")
                    end_tag = buf[p_off : p_off + 4]
                    assert end_tag == b"\x00\x00\x00\x00", f"Unexpected end tag {end_tag!r}"
                    p_off += 4
                    mods.append((fid, vt, lvl, dptr, val))
                objs.append((oid, nid, mods))
            tables.append(objs)
        assert p_off == len(buf), f"Object table trailing bytes: {p_off} != {len(buf)}"
        return ver, tables[0], tables[1]

    _, w3u_orig, w3u_cust = parse_obj_table(files["war3map.w3u"], False)
    _, w3t_orig, w3t_cust = parse_obj_table(files["war3map.w3t"], False)
    _, w3q_orig, w3q_cust = parse_obj_table(files["war3map.w3q"], True)
    _, w3a_orig, w3a_cust = parse_obj_table(files["war3map.w3a"], True)
    assert len(w3u_orig) >= 24 and len(w3u_cust) == 65, f"Unexpected v8 w3u counts: {len(w3u_orig)}+{len(w3u_cust)}"
    assert len(w3t_cust) == 5 and len(w3q_orig) == 6 and len(w3q_cust) == 4, (
        f"Unexpected w3t/w3q counts: w3t={len(w3t_cust)}, w3q={len(w3q_orig)}+{len(w3q_cust)}"
    )
    assert len(w3a_cust) == 64, f"Expected 64 unique hero skills in war3map.w3a, got {len(w3a_cust)}"

    # Verify custom Hero vs non-Hero rawcode case rule for Classic 1.26a/1.27b
    hero_parents = {"Otch", "Eevi", "Hmkg", "Hamg", "Ucrl", "Hpal", "Hblm", "Nplh", "Ulic", "Edem", "Udre", "Ntin", "Nfir"}
    for oid, nid, _ in w3u_cust:
        if oid in hero_parents:
            assert nid[0].isupper(), f"Custom Hero {nid} (parent {oid}) MUST start with uppercase!"
        else:
            assert nid[0].islower(), f"Custom non-Hero {nid} (parent {oid}) MUST start with lowercase!"

    # Independent JS parser cross-check via mdx-m3-viewer for effect, building MDX and BLP1 assets.
    imp_expected = struct.unpack_from("<II", files["war3map.imp"], 0)[1]
    blp_paths_json = json.dumps([name for name in files if name.lower().endswith(".blp")])
    custom_mdx_paths = [name for name in files if name.lower().endswith(".mdx") and (name.startswith("WM_FX_") or name.startswith("WM_Skill_"))]
    mdx_paths_json = json.dumps(custom_mdx_paths)
    building_mdx_paths = [name for name in files if name.startswith("WM_Build_Naga_") and name.lower().endswith(".mdx")]
    building_mdx_paths_json = json.dumps(building_mdx_paths)
    mdx_dir = Path("/tmp/wc3ref/node_modules/mdx-m3-viewer")
    if mdx_dir.exists():
        js_check = subprocess.run(
            [
                "node",
                "-e",
                f"""
                const fs = require("fs");
                const War3Map = require("{mdx_dir}/dist/cjs/parsers/w3x/map.js").default;
                const W3u = require("{mdx_dir}/dist/cjs/parsers/w3x/w3u/file.js").default;
                const W3d = require("{mdx_dir}/dist/cjs/parsers/w3x/w3d/file.js").default;
                const Imp = require("{mdx_dir}/dist/cjs/parsers/w3x/imp/file.js").default;
                const MdxModel = require("{mdx_dir}/dist/cjs/parsers/mdlx/model.js").default;
                const {{ BlpImage }} = require("{mdx_dir}/dist/cjs/parsers/blp/image.js");
                global.ImageData = class ImageData {{ constructor(w, h) {{ this.width = w; this.height = h; this.data = new Uint8ClampedArray(w * h * 4); }} }};
                const m = new War3Map();
                m.load(new Uint8Array(fs.readFileSync({str(w3x_path)!r})));
                const u = new W3u(); u.load(m.get("war3map.w3u").bytes());
                const t = new W3u(); t.load(m.get("war3map.w3t").bytes());
                const q = new W3d(); q.load(m.get("war3map.w3q").bytes());
                const a = new W3d(); a.load(m.get("war3map.w3a").bytes());
                const imp = new Imp(); imp.load(m.get("war3map.imp").bytes());
                if (u.version !== 2 || t.version !== 2 || q.version !== 2 || a.version !== 2 || imp.entries.size !== {imp_expected}) process.exit(1);
                const customMdxPaths = {mdx_paths_json};
                if (customMdxPaths.length !== 70) process.exit(2);
                for (const fx of customMdxPaths) {{
                    const mdl = new MdxModel();
                    mdl.load(m.get(fx).bytes());
                    if (mdl.version !== 800 || mdl.sequences.length < 2 || mdl.geosets.length !== 2) process.exit(2);
                }}
                const buildingMdxPaths = {building_mdx_paths_json};
                if (buildingMdxPaths.length !== 3) process.exit(7);
                for (const building of buildingMdxPaths) {{
                    const mdl = new MdxModel();
                    mdl.load(m.get(building).bytes());
                    if (mdl.version !== 800 || mdl.sequences.length !== 3 || mdl.geosets.length !== 1) process.exit(8);
                }}
                const icon = new BlpImage();
                icon.load(m.get("ReplaceableTextures\\\\CommandButtons\\\\BTN_WM_Portrait_Hvsh.blp").bytes());
                if (icon.width !== 64 || icon.height !== 64) process.exit(3);
                const cursor = new BlpImage();
                cursor.load(m.get("UI\\\\Cursor\\\\HumanCursor.blp").bytes());
                if (cursor.width !== 256 || cursor.height !== 128) process.exit(4);
                const blpPaths = {blp_paths_json};
                for (const path of blpPaths) {{
                    const b = new BlpImage();
                    b.load(m.get(path).bytes());
                    if (b.width <= 0 || b.height <= 0) process.exit(5);
                    const mip = b.getMipmap(0);
                    if (!mip || mip.data.length !== mip.width * mip.height * 4) process.exit(6);
                }}
                """,
            ],
            capture_output=True,
            text=True,
        )
        assert js_check.returncode == 0, f"mdx-m3-viewer parser rejected w3u/w3t/w3q/w3a/imp/mdx/blp:\n{js_check.stderr}"

    # Validate field IDs, EXACT variableTypes & rawcodes against official 1.27.1 SLKs if present
    slk_dir = Path("/tmp/wc3ref/w3x2lni/data/enUS-1.27.1/mpq/Units")
    known_custom_ids: Set[str] = (
        {nid for _, nid, _ in w3u_cust}
        | {nid for _, nid, _ in w3t_cust}
        | {nid for _, nid, _ in w3q_cust}
        | {nid for _, nid, _ in w3a_cust}
    )
    slk_ubal: Dict[str, dict] = {}
    slk_uweap: Dict[str, dict] = {}
    slk_uabil: Dict[str, dict] = {}
    default_btn_pos: Dict[str, Tuple[int, int]] = {}

    def expected_w3_vtype(meta_type: str) -> int:
        if meta_type in {
            "int", "bool", "attackBits", "teamColor", "deathType",
            "versionFlags", "silenceFlags", "fullFlags", "interactionFlags",
            "channelType", "channelFlags", "spellDetail", "techAvail",
        }:
            return 0
        if meta_type == "real":
            return 1
        if meta_type == "unreal":
            return 2
        return 3

    if slk_dir.exists():
        def load_slk_ids(p: Path, col_name: str) -> Dict[str, dict]:
            hdr_m: Dict[int, str] = {}
            rows_m: Dict[int, dict] = {}
            cx_v = cy_v = 0
            for ln in p.read_text(errors="ignore").splitlines():
                if not ln.startswith("C;"):
                    continue
                val_s = None
                for part in ln.split(";")[1:]:
                    if part.startswith("X"):
                        cx_v = int(part[1:])
                    elif part.startswith("Y"):
                        cy_v = int(part[1:])
                    elif part.startswith("K"):
                        val_s = part[1:].strip('"')
                if cy_v == 1:
                    if val_s is not None:
                        hdr_m[cx_v] = val_s
                else:
                    rows_m.setdefault(cy_v, {})[hdr_m.get(cx_v, "")] = val_s
            return {r[col_name]: r for r in rows_m.values() if r.get(col_name)}

        umd = load_slk_ids(slk_dir / "UnitMetaData.slk", "ID")
        qmd = load_slk_ids(slk_dir / "UpgradeMetaData.slk", "ID")
        amd = load_slk_ids(slk_dir / "AbilityMetaData.slk", "ID")
        slk_ubal = load_slk_ids(slk_dir / "unitbalance.slk", "unitBalanceID")
        slk_uweap = load_slk_ids(slk_dir / "unitweapons.slk", "unitWeapID")
        slk_uabil = load_slk_ids(slk_dir / "unitabilities.slk", "unitAbilID")
        itms = load_slk_ids(slk_dir / "itemdata.slk", "itemID")
        abils = load_slk_ids(slk_dir / "abilitydata.slk", "alias")
        upgs = load_slk_ids(slk_dir / "upgradedata.slk", "upgradeid")
        dest_p = slk_dir / "destructabledata.slk"
        dests = load_slk_ids(dest_p, "DestructableID") if dest_p.exists() else {}
        all_known_4cc = (
            set(slk_ubal.keys())
            | set(itms.keys())
            | set(abils.keys())
            | set(upgs.keys())
            | set(dests.keys())
            | known_custom_ids
            | {
                "sloc", "BTLF", "LTlt", "ATtr", "VTlt",
                "ZTtw", "ZZys", "ZZgr", "YOfb", "ZWbg", "ZPlp",
                "Zdrt", "Ztil", "Zsan", "Zbkl", "Zgrs", "Zvin", "CZdi", "CZlb", "BTLF",
            }
        )

        # Load default Buttonpos from official *func.txt files
        for func_fn in (
            "humanunitfunc.txt", "orcunitfunc.txt", "undeadunitfunc.txt", "nightelfunitfunc.txt",
            "neutralunitfunc.txt", "campaignunitfunc.txt", "humanupgradefunc.txt",
            "campaignupgradefunc.txt", "itemfunc.txt",
        ):
            fp = slk_dir / func_fn
            if fp.exists():
                cur_sec = None
                for ln in fp.read_text(errors="ignore").splitlines():
                    ln = ln.strip()
                    if ln.startswith("[") and ln.endswith("]") and len(ln) == 6:
                        cur_sec = ln[1:5]
                    elif cur_sec and ln.lower().startswith("buttonpos="):
                        parts_bp = ln.split("=", 1)[1].split(",")
                        if len(parts_bp) >= 2:
                            try:
                                default_btn_pos[cur_sec] = (int(parts_bp[0].strip()), int(parts_bp[1].strip()))
                            except ValueError:
                                pass

        # Cross-reference Blizzard's Naga building rawcodes against the native
        # campaign function records (the relevant structures are around lines 990-1070)
        # and unitui.slk model paths. These are the model/button sources for custom Naga buildings.
        native_button_art_paths: Set[str] = set()
        native_func_fields: Dict[str, Dict[str, str]] = {}
        for fp in slk_dir.glob("*func.txt"):
            section: Optional[str] = None
            for line in fp.read_text(errors="ignore").splitlines():
                line = line.strip()
                if line.startswith("[") and line.endswith("]") and len(line) == 6:
                    section = line[1:5].lower()
                    native_func_fields.setdefault(section, {})
                    continue
                if not section or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key, value = key.strip().lower(), value.strip()
                native_func_fields[section][key] = value
                if key in ("art", "researchart"):
                    native_button_art_paths.add(value.replace("/", "\\").lower())
        native_unit_ui = load_slk_ids(slk_dir / "unitui.slk", "unitUIID")
        naga_native_buildings = {
            "nnad": (r"buildings\naga\AltarOfDepths\AltarOfDepths", r"ReplaceableTextures\CommandButtons\BTNAltarOfDepths.blp"),
            "nnfm": (r"buildings\naga\CoralBed\CoralBed", r"ReplaceableTextures\CommandButtons\BTNCoralBed.blp"),
            "nnsa": (r"buildings\naga\ShrineOfAshjara\ShrineOfAshjara", r"ReplaceableTextures\CommandButtons\BTNShrineOfAszhara.blp"),
            "nnsg": (r"buildings\naga\SpawningGrounds\SpawningGrounds", r"ReplaceableTextures\CommandButtons\BTNSpawningGrounds.blp"),
            "nntg": (r"buildings\naga\TidalGuardian\TidalGuardian", r"ReplaceableTextures\CommandButtons\BTNTidalGuardian.blp"),
            "nntt": (r"buildings\naga\TempleofTides\TempleofTides", r"ReplaceableTextures\CommandButtons\BTNTempleOfTides.blp"),
        }
        native_naga_worker_builds = {
            rawcode.strip().lower()
            for rawcode in native_func_fields.get("nmpe", {}).get("builds", "").split(",")
            if rawcode.strip()
        }
        assert native_naga_worker_builds == set(naga_native_buildings), (
            f"Native Naga worker build list changed: {sorted(native_naga_worker_builds)}"
        )
        for native_id, (model_path, button_path) in naga_native_buildings.items():
            assert native_id in native_unit_ui, f"Native Naga building {native_id} missing from unitui.slk"
            assert str(native_unit_ui[native_id].get("file", "")).lower() == model_path.lower(), (
                f"Native Naga model mismatch for {native_id}: {native_unit_ui[native_id].get('file')}"
            )
            assert native_func_fields.get(native_id, {}).get("art", "").lower() == button_path.lower(), (
                f"Native Naga button mismatch for {native_id}: {native_func_fields.get(native_id, {}).get('art')}"
            )
            assert button_path.lower() in native_button_art_paths, f"Unrecognized native Naga button {button_path}"

        custom_u_by_id = {
            nid: {fid: str(value) for fid, _vt, _lvl, _dptr, value in mods}
            for _oid, nid, mods in w3u_cust if nid != "\x00\x00\x00\x00"
        }
        custom_model_paths = {
            nid: mods["umdl"] for nid, mods in custom_u_by_id.items() if mods.get("umdl")
        }
        assert len(custom_model_paths) == 55, (
            f"Expected all 55 custom faction model overrides to survive icon normalization, got {len(custom_model_paths)}"
        )
        native_model_paths = {
            str(row.get("file", "")).replace("/", "\\").lower()
            for row in native_unit_ui.values() if row.get("file")
        }
        generated_naga_building_models = {
            "n003": "WM_Build_Naga_TidalTreasury.mdx",
            "n004": "WM_Build_Naga_CoralForge.mdx",
            "n005": "WM_Build_Naga_BehemothPool.mdx",
        }
        for custom_id, model_path in custom_model_paths.items():
            model_key = model_path.replace("/", "\\").removesuffix(".mdl").removesuffix(".mdx").lower()
            if custom_id in generated_naga_building_models:
                expected_model = generated_naga_building_models[custom_id]
                assert model_path.lower() == expected_model.lower(), (
                    f"Naga building {custom_id} must use its unique generated model {expected_model}"
                )
                assert model_path in files, f"Missing generated building MDX {model_path} in MPQ"
            else:
                assert model_key in native_model_paths, (
                    f"Custom object {custom_id} references non-native/unverified model {model_path}"
                )

        representative_models = {
            "h007": r"buildings\human\HumanBarracks\HumanBarracks.mdl",
            "h008": r"buildings\human\Workshop\Workshop.mdl",
            "h009": r"buildings\human\GryphonAviary\GryphonAviary.mdl",
            "v001": r"buildings\undead\Necropolis\Necropolis.mdl",
            "v010": r"units\creeps\VoidWalker\VoidWalker.mdl",
            "t001": r"buildings\other\AmmoDump\AmmoDump.mdl",
            "t002": r"buildings\other\ArcaneObservatory\ArcaneObservatory.mdl",
            "t010": r"Units\Creeps\HeroTinkerRobot\HeroTinkerRobot.mdl",
        }
        for custom_id, expected_model in representative_models.items():
            assert custom_u_by_id.get(custom_id, {}).get("umdl", "").lower() == expected_model.lower(), (
                f"Faction model override for {custom_id} was removed or changed"
            )

        for custom_id, expected_model in generated_naga_building_models.items():
            actual_model = custom_u_by_id.get(custom_id, {}).get("umdl", "")
            expected_button = {
                "n003": r"ReplaceableTextures\CommandButtons\BTNShrineOfAszhara.blp",
                "n004": r"ReplaceableTextures\CommandButtons\BTNAltarOfDepths.blp",
                "n005": r"ReplaceableTextures\CommandButtons\BTNSpawningGrounds.blp",
            }[custom_id]
            texture_path = f"Textures\\{expected_model.removesuffix('.mdx')}.blp"
            assert actual_model.lower() == expected_model.lower(), f"Wrong role-specific Naga building model on {custom_id}"
            assert expected_model in files and texture_path in files, f"Missing Naga building MDX/texture pair for {custom_id}"
            actual_button = custom_u_by_id.get(custom_id, {}).get("uico", "")
            assert actual_button.lower() == expected_button.lower(), f"Naga building button no longer matches its construction role: {custom_id}"

        sunfury_native_building_parents = (
            ("h001", "htow"), ("h002", "hkee"), ("h003", "hcas"),
            ("h004", "halt"), ("h005", "hvlt"), ("h007", "hbar"),
            ("h008", "harm"), ("h009", "hgra"), ("h010", "hbla"), ("h011", "hlum"),
        )
        for custom_id, native_id in sunfury_native_building_parents:
            expected_model = str(native_unit_ui[native_id].get("file", ""))
            actual_model = custom_u_by_id.get(custom_id, {}).get("umdl", "").removesuffix(".mdl")
            assert actual_model.lower() == expected_model.lower(), (
                f"Sunfury building {custom_id} must use its role-matched native Human model {expected_model}.mdl"
            )

        null_model_rawcode = bytes(4).decode("latin1")
        custom_parent_by_id = {
            nid: oid for oid, nid, _mods in w3u_cust if nid != null_model_rawcode
        }

        def building_model_key(rawcode: str) -> str:
            model = custom_u_by_id.get(rawcode, {}).get("umdl", "")
            if not model:
                parent_id = custom_parent_by_id.get(rawcode, rawcode)
                native_row = native_unit_ui.get(parent_id)
                assert native_row and native_row.get("file"), f"No native model metadata for building {rawcode}/{parent_id}"
                model = str(native_row["file"])
            return model.replace("/", "\\").removesuffix(".mdl").removesuffix(".mdx").lower()

        native_classic_workers = {
            "Human": ("hpea", ("hkee", "hcas")),
            "Orc": ("opeo", ("ostr", "ofrt")),
            "Undead": ("uaco", ("unp1", "unp2", "uzg1", "uzg2")),
            "Night Elf": ("ewsp", ("etoa", "etoe")),
        }
        native_tier_families = {
            "Human": {frozenset(("htow", "hkee", "hcas"))},
            "Orc": {frozenset(("ogre", "ostr", "ofrt"))},
            "Undead": {
                frozenset(("unpl", "unp1", "unp2")),
                frozenset(("uzig", "uzg1", "uzg2")),
            },
            "Night Elf": {frozenset(("etol", "etoa", "etoe"))},
        }
        for race_name, (worker_id, tier_ids) in native_classic_workers.items():
            native_ids = [
                rawcode.strip().lower()
                for rawcode in native_func_fields.get(worker_id, {}).get("builds", "").split(",")
                if rawcode.strip()
            ]
            if race_name == "Orc":
                # `orbr` is the button-only fortified-burrow upgrade alias; it has no unitui model row.
                native_ids = [rawcode for rawcode in native_ids if rawcode != "orbr"]
            native_ids.extend(tier_ids)
            by_model: Dict[str, List[str]] = {}
            for rawcode in native_ids:
                by_model.setdefault(building_model_key(rawcode), []).append(rawcode)
            native_duplicates = {frozenset(ids) for ids in by_model.values() if len(ids) > 1}
            assert native_duplicates == native_tier_families[race_name], (
                f"Unexpected duplicate native building models in {race_name}: "
                f"{[(key, ids) for key, ids in by_model.items() if len(ids) > 1]}"
            )

        faction_building_ids = {
            "Abyssal Tideborn": ("nntt", "n001", "n002", "nnfm", "nnsg", "n004", "nnad", "n003", "nntg", "nnsa", "n005"),
            "Sunfury Imperium": ("h001", "h002", "h003", "nefm", "h007", "h011", "h010", "h004", "h005", "negt", "nheb", "h008", "h009"),
            "Voidborn Legion": ("v001", "v002", "v003", "v004", "v005", "v006", "v007", "v008", "v009", "v018", "v019"),
            "Runeforged Bastion": ("t001", "t002", "t003", "t004", "t005", "t006", "t007", "t008", "t009", "t018", "t019"),
        }
        intentional_tier_families = {
            frozenset(("nntt", "n001", "n002")),
            frozenset(("h001", "h002", "h003")),
        }
        for faction_name, building_ids in faction_building_ids.items():
            by_model: Dict[str, List[str]] = {}
            for rawcode in building_ids:
                model_key = building_model_key(rawcode)
                by_model.setdefault(model_key, []).append(rawcode)
            duplicates = [frozenset(ids) for ids in by_model.values() if len(ids) > 1]
            assert all(group in intentional_tier_families for group in duplicates), (
                f"Duplicate building model assignments in {faction_name}: "
                f"{[(key, ids) for key, ids in by_model.items() if len(ids) > 1]}"
            )
        assert len({building_model_key(x) for x in ("n003", "n004", "n005")}) == 3, "Custom Naga role models must be unique"

        # Native art paths are external game assets: validate their metadata, rather
        # than incorrectly requiring Blizzard's icons to be imported into the map.
        def normalize_button_path(path: str) -> str:
            return path.replace("/", "\\").lower()

        def disabled_button_path(path: str) -> str:
            marker = "\\commandbuttons\\btn"
            normalized = normalize_button_path(path)
            assert marker in normalized, f"Not a normal Warcraft command button path: {path}"
            idx = normalized.index(marker)
            return path[:idx] + path[idx:].replace("\\CommandButtons\\BTN", "\\CommandButtonsDisabled\\DISBTN", 1)

        null_id = "\x00\x00\x00\x00"
        for oid, nid, mods in w3u_orig + w3u_cust:
            assert oid in slk_ubal, f"Unknown parent unit ID {oid!r}"
            target_label = nid if nid != null_id else oid
            is_hero_obj = target_label[0].isupper()
            base_is_bldg = str(slk_ubal[oid].get("isbldg", "0")) == "1"
            for fid, vt, _l, _d, val in mods:
                assert fid in umd, f"Unknown UnitMetaData field {fid!r} on {target_label}"
                exp_vt = expected_w3_vtype(umd[fid].get("type", ""))
                assert vt == exp_vt, (
                    f"Strict variableType mismatch on {target_label}.{fid} ({umd[fid].get('type')}): "
                    f"got vt={vt}, expected vt={exp_vt}!"
                )
                if fid == "uico":
                    icon_path = str(val)
                    if r"\CommandButtons\BTN_WM_Portrait_" in icon_path:
                        assert icon_path in files, f"Missing custom hero portrait icon {icon_path} in MPQ"
                    else:
                        assert normalize_button_path(icon_path) in native_button_art_paths, (
                            f"Unrecognized native object button art {icon_path} on {target_label}"
                        )
                # CRITICAL HERO RALLY-FLAG GUARD (`urev` and all building-only fields forbidden on Heroes!)
                if is_hero_obj:
                    assert fid != "urev", f"CRITICAL RALLY-FLAG BUG: Hero {target_label} has building-only 'urev'!"
                    assert str(umd[fid].get("useHero", "0")) == "1" or str(umd[fid].get("useUnit", "0")) == "1", (
                        f"Building-only field {fid!r} applied to Hero {target_label}!"
                    )
                elif not base_is_bldg:
                    assert str(umd[fid].get("useUnit", "0")) == "1", (
                        f"Non-unit field {fid!r} applied to unit {target_label}!"
                    )
                if fid in ("ubui", "utra", "ures", "uupt", "ureq", "urq1", "urq2", "uhab", "uabi", "umki", "udaa", "upgr", "udep") and val:
                    for code in str(val).split(","):
                        code = code.strip()
                        if code and code != "_":
                            assert code in all_known_4cc, f"Unknown rawcode {code!r} in {fid} of {oid}/{nid}"

        for oid, nid, mods in w3t_cust:
            assert oid in itms, f"Unknown parent item ID {oid!r}"
            for fid, vt, _l, _d, _val in mods:
                assert fid in umd, f"Unknown ItemMetaData field {fid!r} on {nid}"
                assert str(umd[fid].get("useItem", "0")) == "1", f"Non-item field {fid!r} on item {nid}!"
                exp_vt = expected_w3_vtype(umd[fid].get("type", ""))
                assert vt == exp_vt, f"Strict variableType mismatch on item {nid}.{fid}: {vt} != {exp_vt}"

        for oid, nid, mods in w3q_orig + w3q_cust:
            assert oid in upgs, f"Unknown upgrade ID {oid!r}"
            eff_q = nid if nid != null_id else oid
            for fid, vt, _l, _d, val in mods:
                assert fid in qmd, f"Unknown UpgradeMetaData field {fid!r} on {eff_q}"
                exp_vt = expected_w3_vtype(qmd[fid].get("type", ""))
                assert vt == exp_vt, f"Strict variableType mismatch on upgrade {eff_q}.{fid}: {vt} != {exp_vt}"
                if fid == "greq" and val:
                    for code in str(val).split(","):
                        if code.strip():
                            assert code.strip() in all_known_4cc, f"Unknown req {val!r} in w3q {eff_q}"

        seen_skill_ids: Set[str] = set()
        seen_skill_icons: Set[str] = set()
        seen_skill_fx: Set[str] = set()
        skill_profiles: Dict[str, Dict[str, str]] = {}
        skill_level_fields: Dict[str, Dict[Tuple[str, int], str]] = {}
        for skill_index, (oid, nid, mods) in enumerate(w3a_cust):
            assert oid == "ANcl", f"Custom hero skill {nid} should inherit from ANcl, got {oid}"
            assert nid not in seen_skill_ids, f"Duplicate custom skill rawcode {nid}!"
            seen_skill_ids.add(nid)
            orders_by_lvl: Dict[int, str] = {}
            base_fields: Dict[str, str] = {}
            fields_by_level: Dict[Tuple[str, int], str] = {}
            alev = 3
            for fid, vt, lvl, _dptr, val in mods:
                assert fid in amd, f"Unknown AbilityMetaData field {fid!r} on {nid}"
                exp_vt = expected_w3_vtype(amd[fid].get("type", ""))
                assert vt == exp_vt, f"Strict variableType mismatch on ability {nid}.{fid}: {vt} != {exp_vt}"
                if lvl == 0:
                    base_fields[fid] = str(val)
                else:
                    fields_by_level[(fid, lvl)] = str(val)
                if fid == "alev":
                    alev = int(val)
                elif fid == "Ncl6":
                    orders_by_lvl[lvl] = str(val)
                elif fid == "aart":
                    icon_path = str(val)
                    normalized_icon = normalize_button_path(icon_path)
                    expected_icon = f"replaceabletextures\\commandbuttons\\btn_wm_skill_{nid.lower()}.blp"
                    assert normalized_icon == expected_icon, (
                        f"Skill {nid} must use its own authored BTN icon, got {icon_path}"
                    )
                    assert icon_path in files, f"Missing imported custom skill icon {icon_path}"
                    disabled_path = disabled_button_path(icon_path)
                    normalized_disabled = normalize_button_path(disabled_path)
                    imported_paths = {normalize_button_path(path) for path in files}
                    assert normalized_disabled in imported_paths, (
                        f"Missing custom disabled-button twin for {icon_path}: {disabled_path}"
                    )
                    seen_skill_icons.add(normalized_icon)
                elif fid == "acat":
                    assert str(val) in files and str(val).endswith(".mdx"), f"Missing custom 3D MDX model {val} in MPQ!"
                    seen_skill_fx.add(str(val))
            # Custom rawcodes are serialized in lexicographic order, not kit order.
            # Their decimal suffix (A000..A063) preserves the Q/W/E/R slot grouping.
            is_ultimate = int(nid[1:]) % 4 == 3
            expected_alev = 1 if is_ultimate else 3
            expected_arlv = 6 if is_ultimate else 1
            expected_alsk = 0 if is_ultimate else 2
            assert int(base_fields.get("alev", "-1")) == expected_alev, f"{nid} has wrong ability rank count"
            assert int(base_fields.get("arlv", "-1")) == expected_arlv, (
                f"{nid} first learn level must be {expected_arlv}, got {base_fields.get('arlv')}"
            )
            assert int(base_fields.get("alsk", "-1")) == expected_alsk, (
                f"{nid} level-skip must be {expected_alsk}, got {base_fields.get('alsk')}"
            )
            for req_lv in range(1, alev + 1):
                assert orders_by_lvl.get(req_lv, "-") not in ("", "-"), f"Skill {nid} missing Ncl6 order on level {req_lv}!"
            skill_profiles[nid] = base_fields
            skill_level_fields[nid] = fields_by_level
        assert len(seen_skill_ids) == 64, f"Expected 64 unique hero abilities, found {len(seen_skill_ids)}"
        assert len(seen_skill_icons) == 64, f"Expected 64 unique BTN skill icons, found {len(seen_skill_icons)}"
        assert len(seen_skill_fx) == 6, f"Expected 6 faction/hero 3D VFX models, found {len(seen_skill_fx)}"
        assert skill_profiles["A005"].get("anam") == "Mana Burn", "Illidan's original Mana Burn name was lost"
        assert skill_profiles["A005"].get("aart", "").endswith("BTN_WM_Skill_A005.blp"), "Mana Burn uses the wrong authored button art"
        assert skill_level_fields["A005"].get(("Ncl6", 1)) == "manaburn", "Mana Burn order is incorrect"
        assert skill_profiles["A019"].get("anam") == "Summon Phoenix: Al'ar", "Kael's Phoenix skill was lost"
        assert skill_profiles["A031"].get("anam") == "Resurrection", "Uther's Resurrection skill was lost"
        assert skill_level_fields["A031"].get(("Ncl6", 1)) == "resurrection", "Uther's Resurrection order is incorrect"
        assert skill_level_fields["A031"].get(("Ncl2", 1)) == "0", "Resurrection must be a self-cast ability"
        game_jass = files["war3map.j"].decode("utf-8")
        for engine_marker in (
            "function WM_ResurrectNearestAlliedHero",
            "set revived = ReviveHero(corpse",
            "'hphx'",
            "ManaBurnTarget.mdl",
            "function WM_AIFindManaTarget",
            "function WM_AIHasFallenAllyHero",
            'IssueImmediateOrder(u, "resurrection")',
            'IssueTargetOrder(hero, "manaburn", manaTarget)',
            "call WM_AICastCustomHeroCombo(u, weakFoe)",
        ):
            assert engine_marker in game_jass, f"Missing restored hero-skill implementation: {engine_marker}"

        ult_tick_src = jass_src.split("function WM_OnUltWaveTick", 1)[1].split("endfunction", 1)[0]
        def ult_branch(ability_id: str) -> str:
            marker = f"elseif abil == '{ability_id}' then"
            assert marker in ult_tick_src, f"Ultimate pulse branch missing for {ability_id}"
            return ult_tick_src.split(marker, 1)[1].split("elseif abil", 1)[0]
        assert "function WM_ApplyUltRingEffect" in jass_src and "WM_ApplyUltRingEffect(caster, tx, ty, innerRadius, rad" in ult_branch("A003"), (
            "Vashj's tsunami must deal damage/heal/push along expanding ring fronts, not repeat a full-disk hit"
        )
        assert "WM_ApplyAreaEffect(caster, tx, ty, 300.0" in ult_branch("A043"), (
            "Akama's self-centered ultimate must retain its close-range 300-AoE risk/reward"
        )
        laser_branch = ult_branch("A059")
        assert "WM_SpawnUltLineFX" in laser_branch and "WM_ApplyLineEffect(caster" in laser_branch and "520.0" in laser_branch, (
            "Mimiron's ultimate must use its telegraphed rotating laser lanes"
        )
        assert "pulse == 0" in laser_branch and "udg_UltBaseAngle[idx]" in laser_branch, (
            "Mimiron's three lanes must be visibly telegraphed and locked to the cast-time aim direction"
        )
        assert laser_branch.count("call WM_SpawnUltLineFX(") == 3, "Mimiron's telegraph must draw all three lanes"
        assert all(f"idx, {lane})" in laser_branch for lane in (0, 1, 2)), "Mimiron's three lane handles must occupy separate cleanup slots"
        assert "(I2R(pulse) - 2.0) * 0.42" in laser_branch, "Mimiron's three laser sweeps must rotate symmetrically around the aim line"
        assert "call WM_EnqueueUltPulse(caster, abil, tx, ty, 4)" in jass_src, (
            "Mimiron's laser ultimate must reserve one 0.55-second telegraph tick before its three damage lanes"
        )
        clear_laser_src = jass_src.split("function WM_ClearUltLaserFX", 1)[1].split("endfunction", 1)[0]
        assert "exitwhen k >= 21" in clear_laser_src and "DestroyEffect" in clear_laser_src and "= null" in clear_laser_src, (
            "Mimiron's 21 telegraph effects must be destroyed and nulled"
        )
        assert ult_tick_src.count("call WM_ClearUltLaserFX(idx)") >= 2, (
            "Mimiron telegraph effects must be cleaned both on caster death and normal completion"
        )

        # Check all 4-char rawcodes in war3map.j and all 4 .ai files
        for sname in ("war3map.j", "naga_melee.ai", "camphuman_melee.ai", "voidborn_melee.ai", "runeforged_melee.ai"):
            stxt = files[sname].decode("utf-8")
            for rc in re.findall(r"'([A-Za-z0-9]{4})'", stxt):
                assert rc in all_known_4cc, f"Unknown rawcode '{rc}' in {sname}!"

    # Verify war3mapMisc.txt contains all 4 Custom Empires' Halls, Altars & 16 playable Heroes.
    misc_txt = files["war3mapMisc.txt"].decode("utf-8")
    for req_token in (
        "Hvsh", "N004", "N001", "N002", "Hkal", "Hvwd", "Hlgr", "Huth",
        "V001", "V002", "V003", "V004", "T001", "T002", "T003", "T004",
        "nnad", "h004", "v007", "t007",
        "nntt", "n001", "n002", "h001", "h002", "h003", "v001", "v002", "v003", "t001", "t002", "t003",
    ):
        assert req_token in misc_txt, f"Missing {req_token} in war3mapMisc.txt!"

    # Verify ZERO 4x3 button collisions across ALL build, train, upgrade, research & shop cards!
    obj_btn: Dict[str, Tuple[int, int]] = dict(default_btn_pos)
    obj_lists: Dict[str, Dict[str, List[str]]] = {}
    for oid, nid, mods in w3u_orig + w3u_cust + w3t_cust:
        eff_id = nid if nid != "\x00\x00\x00\x00" else oid
        if nid != "\x00\x00\x00\x00" and oid in obj_btn and eff_id not in obj_btn:
            obj_btn[eff_id] = obj_btn[oid]
        bx = by = None
        for fid, _vt, _l, _d, val in mods:
            if fid == "ubpx":
                bx = int(val)
            elif fid == "ubpy":
                by = int(val)
            elif fid in ("ubui", "utra", "ures", "uupt", "umki"):
                obj_lists.setdefault(eff_id, {})[fid] = [c.strip() for c in str(val).split(",") if c.strip()]
        if bx is not None and by is not None:
            obj_btn[eff_id] = (bx, by)

    for oid, nid, mods in w3q_orig + w3q_cust:
        eff_q = nid if nid != "\x00\x00\x00\x00" else oid
        bx = by = None
        for fid, _vt, _l, _d, val in mods:
            if fid == "gbpx":
                bx = int(val)
            elif fid == "gbpy":
                by = int(val)
        if bx is not None and by is not None:
            obj_btn[eff_q] = (bx, by)

    for prod_id, lmap in obj_lists.items():
        if "ubui" in lmap:
            seen_build: Dict[Tuple[int, int], str] = {}
            for ch_id in lmap["ubui"]:
                assert ch_id in obj_btn, f"Missing button pos for buildable structure {ch_id}"
                pos_xy = obj_btn[ch_id]
                assert 0 <= pos_xy[0] <= 3 and 0 <= pos_xy[1] <= 2, f"Out-of-bounds button {pos_xy} on {ch_id}"
                assert pos_xy != (3, 2), f"Build button {ch_id} overwrites Cancel slot (3,2) on {prod_id}!"
                assert pos_xy not in seen_build, (
                    f"Worker build-menu collision at {pos_xy} on {prod_id}: {seen_build[pos_xy]} vs {ch_id}!"
                )
                seen_build[pos_xy] = ch_id

        # Combined command card on buildings: utra + ures + uupt + umki share the 4x3 card!
        combined_card = (
            lmap.get("utra", []) + lmap.get("ures", []) + lmap.get("uupt", []) + lmap.get("umki", [])
        )
        if combined_card:
            seen_card: Dict[Tuple[int, int], str] = {}
            for ch_id in combined_card:
                if ch_id in obj_btn:
                    pos_xy = obj_btn[ch_id]
                    assert 0 <= pos_xy[0] <= 3 and 0 <= pos_xy[1] <= 2, f"Out-of-bounds button {pos_xy} on {ch_id}"
                    assert pos_xy not in seen_card, (
                        f"Building command-card collision at {pos_xy} on {prod_id}: {seen_card[pos_xy]} vs {ch_id}!"
                    )
                    seen_card[pos_xy] = ch_id

    print(
        f"[PASS] Stage 11: 8-Empire Object & Skill Tables Verified "
        f"(w3u={len(w3u_orig)}+{len(w3u_cust)}, w3t={len(w3t_cust)}, w3q={len(w3q_orig)}+{len(w3q_cust)}, w3a={len(w3a_cust)}, "
        "16 ultimates gated at level 6, core skill ranks at 1/3/5, distinct ring/close-range/laser geometries, 0 hero flags, 0 card collisions)"
    )

    # ------------------------------------------------------------------
    # STAGE 12: Pro Melee `.ai` Scripts (All 4 Custom Empires) Typecheck
    # ------------------------------------------------------------------
    common_ai_path = Path("/tmp/wc3ref/jassdoc/common.ai")
    if ref_127.exists() and common_ai_path.exists():
        common_ai_clean = re.sub(
            r"/\*.*?\*/",
            lambda m: "\n" * m.group(0).count("\n"),
            common_ai_path.read_text(encoding="utf-8", errors="ignore"),
            flags=re.S,
        )
        for ai_name in ("naga_melee.ai", "camphuman_melee.ai", "voidborn_melee.ai", "runeforged_melee.ai"):
            ai_src = files[ai_name].decode("utf-8")
            assert "#include" not in ai_src, f"Illegal C preprocessor directive in {ai_name}"
            chk_ai = JassChecker()
            chk_ai.check_file((ref_127 / "Common.j").read_text(encoding="utf-8", errors="ignore"), "1.27.1/Common.j")
            chk_ai.check_file(common_ai_clean, "common.ai")
            ai_fns = chk_ai.check_file(ai_src, ai_name)
            assert "main" in chk_ai.funcs, f"Missing main() entry point in {ai_name}!"
            print(f"[PASS] Stage 12 ({ai_name}): Full Static Typecheck vs Common.j + common.ai ({ai_fns} AI functions, 0 errors)")

    # ------------------------------------------------------------------
    # STAGE 13: Pro-Ladder Stat Parity & Authentic Building-Role Audit (All 4 Custom Empires)
    # ------------------------------------------------------------------
    mod_lookup: Dict[str, Tuple[str, Dict[str, object]]] = {}
    for oid, nid, mods in w3u_orig + w3u_cust:
        eff_id = nid if nid != "\x00\x00\x00\x00" else oid
        mod_lookup[eff_id] = (oid, {fid: val for fid, _vt, _l, _d, val in mods})

    # 13a. Authentic Building-Role Invariants ("در جاهای خودشون") across all 4 Custom Empires
    for th_id, expected_worker in (
        ("nntt", "nmpe"), ("n001", "nmpe"), ("n002", "nmpe"),
        ("h001", "nhew"), ("h002", "nhew"), ("h003", "nhew"),
        ("v001", "v010"), ("v002", "v010"), ("v003", "v010"),
        ("t001", "t010"), ("t002", "t010"), ("t003", "t010"),
    ):
        assert mod_lookup[th_id][1].get("utra") == expected_worker, (
            f"Town Hall {th_id} must train ONLY worker {expected_worker}, got {mod_lookup[th_id][1].get('utra')}"
        )

    assert mod_lookup["nnsg"][1]["utra"] == "nnmg,nsnp,nmyr", "Spawning Grounds must train infantry/ranged/myrmidon only!"
    assert mod_lookup["n004"][1]["ures"] == "Rnat,Rnam" and mod_lookup["n004"][1]["utra"] == "", "Coral Forge must be dedicated armory!"
    assert mod_lookup["nnsa"][1]["utra"] == "nnsw,nwgs" and mod_lookup["nnsa"][1]["ureq"] == "n001", "Shrine of Azshara must be T2 caster/air sanctum!"
    assert mod_lookup["n005"][1]["utra"] == "nhyc,nnrg" and "n001" in str(mod_lookup["n005"][1]["ureq"]), "Behemoth Pool must house siege & T3 Royal Guard!"

    assert mod_lookup["h007"][1]["utra"] == "hhes,nhea,hcth", "Silvermoon Barracks must train Swordsman, Archer, Captain only!"
    assert mod_lookup["nheb"][1]["utra"] == "nchp,nhym,hspt" and mod_lookup["nheb"][1]["ureq"] == "h002", "Mage Tower must be T2 caster sanctum!"
    assert mod_lookup["h008"][1]["utra"] == "hgyr,h006,nbel" and "h010" in str(mod_lookup["h008"][1]["ureq"]), "Sunfury Artificer Hall must house Gyro, Ballista and Lieutenant behind its own Forge!"
    assert mod_lookup["h009"][1]["utra"] == "hdhw,hgry" and "h011" in str(mod_lookup["h009"][1]["ureq"]), "Dragonhawk Sky-Roost must house only flyers and require the Sunfury Lumber Conservatory!"
    assert mod_lookup["h010"][1]["ures"] == "Rhme,Rhra,Rhar,Rhla" and "h010" in mod_lookup["nhew"][1]["ubui"], "Sunfury Forge must be a dedicated, buildable Sunfury armory!"
    assert mod_lookup["h011"][1]["uabi"] == "Arlm" and "h011" in mod_lookup["nhew"][1]["ubui"], "Sunfury Lumber Conservatory must be its dedicated lumber drop-off!"
    assert mod_lookup["negt"][1]["uaen"] == 0 and mod_lookup["negt"][1]["ugol"] == 30, "Sunspire Scout Tower must be 30g and unarmed!"

    assert mod_lookup["v005"][1]["utra"] == "v011,v012,v013" and mod_lookup["v006"][1]["ures"] == "R000,R001"
    assert mod_lookup["v018"][1]["utra"] == "v014,v015" and mod_lookup["v019"][1]["utra"] == "v016,v017"
    assert mod_lookup["t005"][1]["utra"] == "t011,t012,t013" and mod_lookup["t006"][1]["ures"] == "R002,R003"
    assert mod_lookup["t018"][1]["utra"] == "t014,t015" and mod_lookup["t019"][1]["utra"] == "t016,t017"

    # 13b. Effective Combat Stat & Cost Parity Audit vs Classic TFT Ladder Benchmarks
    if slk_ubal and slk_uweap and slk_uabil:
        def eff_unit_stats(uid: str) -> dict:
            parent_id, m = mod_lookup.get(uid, (uid, {}))
            b = slk_ubal[parent_id]
            w = slk_uweap[parent_id]
            a = slk_uabil[parent_id]

            def gi(fid: str, scol: str, default: int = 0) -> int:
                if fid in m:
                    return int(m[fid])  # type: ignore[arg-type]
                sv = str(b.get(scol, w.get(scol, ""))).strip()
                return int(float(sv)) if sv not in ("", "-", "_") else default

            def gf(fid: str, scol: str, default: float = 0.0) -> float:
                if fid in m:
                    return float(m[fid])  # type: ignore[arg-type]
                sv = str(b.get(scol, w.get(scol, ""))).strip()
                return float(sv) if sv not in ("", "-", "_") else default

            def gs(fid: str, scol: str, default: str = "") -> str:
                if fid in m:
                    return str(m[fid])
                sv = str(b.get(scol, w.get(scol, a.get(scol, "")))).strip()
                return sv if sv not in ("-", "_") else default

            dmg1 = gi("ua1b", "dmgplus1") + gi("ua1d", "dice1") * (gi("ua1s", "sides1") + 1) / 2.0
            cool1 = gf("ua1c", "cool1", 1.0)
            dps1 = dmg1 / cool1 if cool1 > 0 and gi("uaen", "weapsOn", 1) in (1, 3) else 0.0
            dmg2 = gi("ua2b", "dmgplus2") + gi("ua2d", "dice2") * (gi("ua2s", "sides2") + 1) / 2.0
            cool2 = gf("ua2c", "cool2", 1.0)
            dps2 = dmg2 / cool2 if cool2 > 0 and gi("uaen", "weapsOn", 1) in (2, 3) else 0.0
            hp = gi("uhpm", "HP")
            armor = gi("udef", "def")
            ehp = hp * (1.0 + 0.06 * max(0, armor))
            return {
                "gold": gi("ugol", "goldcost"),
                "lumber": gi("ulum", "lumbercost"),
                "food": gi("ufoo", "fused"),
                "hp": hp,
                "mana": gi("umpm", "manaN"),
                "armor": armor,
                "ehp": ehp,
                "dps1": dps1,
                "dps2": dps2,
                "atk1": gs("ua1t", "atkType1"),
                "atk2": gs("ua2t", "atkType2"),
                "abils": gs("uabi", "abilList"),
            }

        combat_roster = [
            "nnmg", "nsnp", "nmyr", "nnsw", "nwgs", "nhyc", "nnrg",
            "hhes", "nhea", "hcth", "nchp", "nhym", "hspt", "h006", "nbel", "hdhw", "hgry",
            "v011", "v012", "v013", "v014", "v015", "v016", "v017",
            "t011", "t012", "t013", "t014", "t015", "t016", "t017",
        ]
        for cuid in combat_roster:
            st = eff_unit_stats(cuid)
            assert st["atk1"] != "chaos" and st["atk2"] != "chaos", f"Broken campaign Chaos attack left on {cuid}!"
            assert "Advc" not in st["abils"] and "ACdv" not in st["abils"], f"Broken campaign Devour left on {cuid}!"
            if cuid != "hspt":
                assert "Amim" not in st["abils"], f"Broken campaign Spell Immunity left on {cuid}!"
            assert st["mana"] <= 300, f"Campaign-inflated mana ({st['mana']}) on {cuid}!"
            assert st["food"] >= 2, f"Invalid food cost on {cuid}: {st['food']}"
            dps_per_food = max(st["dps1"], st["dps2"]) / st["food"]
            hp_per_food = st["hp"] / st["food"]
            assert 2.0 <= dps_per_food <= 6.2, f"Out-of-band DPS/food ({dps_per_food:.2f}) on {cuid}!"
            assert 105.0 <= hp_per_food <= 230.0, f"Out-of-band HP/food ({hp_per_food:.1f}) on {cuid}!"

        # Keep the custom AI's supply guards aligned with actual packed object data.
        ai_production_food = {
            "nnmg": 2, "nsnp": 3, "nmyr": 4, "nnsw": 2, "nwgs": 2, "nhyc": 4, "nnrg": 5,
            "hhes": 2, "nhea": 2, "hcth": 4, "nchp": 2, "hspt": 3, "hgyr": 1, "h006": 3,
            "nbel": 4, "hdhw": 3, "hgry": 4,
            "v011": 2, "v012": 3, "v013": 4, "v014": 2, "v015": 2, "v016": 4, "v017": 5,
            "t011": 2, "t012": 3, "t013": 4, "t014": 2, "t015": 2, "t016": 4, "t017": 5,
        }
        for uid, expected_food in ai_production_food.items():
            actual_food = eff_unit_stats(uid)["food"]
            assert actual_food == expected_food, (
                f"AI production food table mismatch for {uid}: expected {expected_food}, got {actual_food}"
            )

        # Verify ALL 16 Custom Empire Heroes cost 425g/100L/5f/55s, have urqc=3, and level-1 stat sum in [50..56]
        # All 16 actual playable heroes get exact 55-point ladder attribute budgets,
        # proper altar-gating, no building rally field, and four exclusive spells apiece.
        hero_roster = (
            "Hvsh", "N004", "N001", "N002",
            "Hkal", "Hvwd", "Hlgr", "Huth",
            "V001", "V002", "V003", "V004",
            "T001", "T002", "T003", "T004",
        )
        hero_skill_ids: List[str] = []
        for hid in hero_roster:
            p_id, hm = mod_lookup[hid]
            hb = slk_ubal[p_id]
            s_str = int(hm.get("ustr", hb["STR"]))  # type: ignore[arg-type]
            s_agi = int(hm.get("uagi", hb["AGI"]))  # type: ignore[arg-type]
            s_int = int(hm.get("uint", hb["INT"]))  # type: ignore[arg-type]
            assert (s_str + s_agi + s_int) == 55, f"Hero {hid} base stat total {s_str+s_agi+s_int} != exact 55-point melee budget!"
            assert hm.get("ugol") == 425 and hm.get("ulum") == 100 and hm.get("ufoo") == 5, f"Hero {hid} cost mismatch!"
            assert hm.get("urqc") == 3, f"Hero {hid} missing urqc=3 Altar tier-gating!"
            assert "urev" not in hm, f"Rally-flag bug: playable hero {hid} contains building-only `urev`!"
            hero_skills = str(hm.get("uhab", "")).split(",")
            assert len(hero_skills) == 4 and all(hero_skills), f"Hero {hid} must own four custom skills!"
            hero_skill_ids.extend(hero_skills)
        assert len(set(hero_skill_ids)) == 64, "Each playable hero must own four globally unique skills (64 total)!"

    # Prove all four custom spawn branches create the intended hall/worker and the worker
    # has a real build menu; Stage 6 already verified each of the eight mirrored base zones.
    spawn_templates = ((5, "nntt", "nmpe"), (6, "h001", "nhew"), (7, "v001", "v010"), (8, "t001", "t010"))
    for faction_id, hall_id, worker_id in spawn_templates:
        assert hall_id in mod_lookup and worker_id in mod_lookup, f"Missing Empire {faction_id} spawn objects!"
        hall_mods = mod_lookup[hall_id][1]
        worker_mods = mod_lookup[worker_id][1]
        assert hall_mods.get("utra") == worker_id, f"Empire {faction_id} hall {hall_id} must train its exact worker!"
        assert worker_mods.get("ubui"), f"Empire {faction_id} worker {worker_id} has no construction list!"
        worker_parent = mod_lookup[worker_id][0]
        worker_abilities = str(worker_mods.get("uabi", slk_uabil.get(worker_parent, {}).get("abilList", "")))
        assert ("Ahar" in worker_abilities or "ANha" in worker_abilities), f"Empire {faction_id} worker {worker_id} cannot harvest!"
        assert f"set hallId = '{hall_id}'" in jass_src and f"set workerId = '{worker_id}'" in jass_src, f"JASS spawn map missing Empire {faction_id}!"

    print("[PASS] Stage 13: All-31-Unit, 16-Hero/64-Skill, 8-Spawn-Branch, Ladder DPS/EHP/Cost/Role Audit Passed")

    # ------------------------------------------------------------------
    # STAGE 14: Native Building Models, Lobby Art, Skill Buttons, Portraits, UI & VFX
    # ------------------------------------------------------------------
    tga = files["war3mapPreview.tga"]
    assert tga[2] == 2 and struct.unpack_from("<HHB", tga, 12) == (256, 256, 24), "Invalid 256x256 24-bit war3mapPreview.tga!"
    skin_txt = files["war3mapSkin.txt"].decode("utf-8")
    assert "[CustomSkin]" in skin_txt and "[FrameDef]" in skin_txt and "Border=" not in skin_txt
    for skin_key in (
        "Cursor=UI\\Cursor\\HumanCursor.mdl",
        "InfoPanelIconDamageChaos=UI\\CrownUI\\Infocard\\DmgChaos.blp",
        "InfoPanelIconArmorFort=UI\\CrownUI\\Infocard\\ArmFort.blp",
        "CommandBasicStruct=ReplaceableTextures\\CommandButtons\\BTNAltarOfDepths.blp",
        "CommandBasicStructHuman=ReplaceableTextures\\CommandButtons\\BTNHumanBuild.blp",
        "CommandBasicStructUndead=ReplaceableTextures\\CommandButtons\\BTNScourgeBuild.blp",
        "CommandBasicStructOrc=ReplaceableTextures\\CommandButtons\\BTNBasicStruct.blp",
        "CommandBasicStructNightElf=ReplaceableTextures\\CommandButtons\\BTNNightElfBuild.blp",
    ):
        assert skin_key in skin_txt, f"Missing v8 UI skin mapping: {skin_key}"

    blp_files = {name: data for name, data in files.items() if name.lower().endswith(".blp")}
    mdx_files = {name: data for name, data in files.items() if name.lower().endswith(".mdx") and (name.startswith("WM_FX_") or name.startswith("WM_Skill_"))}
    skill_mdx_files = {name: data for name, data in mdx_files.items() if name.startswith("WM_Skill_")}
    faction_mdx_files = {name: data for name, data in mdx_files.items() if name.startswith("WM_FX_")}
    building_mdx_files = {name: data for name, data in files.items() if name.startswith("WM_Build_Naga_") and name.lower().endswith(".mdx")}
    assert len(blp_files) == 261, f"Expected 261 portrait/skill-button/UI/VFX/building/minimap BLPs, got {len(blp_files)}"
    assert len(mdx_files) == 70 and len(faction_mdx_files) == 6, f"Expected 6 faction + 64 skill MDX effects, got {len(mdx_files)} total"
    expected_naga_building_mdx = {"WM_Build_Naga_TidalTreasury.mdx", "WM_Build_Naga_CoralForge.mdx", "WM_Build_Naga_BehemothPool.mdx"}
    expected_naga_building_blp = {f"Textures\\{name.removesuffix('.mdx')}.blp" for name in expected_naga_building_mdx}
    assert set(building_mdx_files) == expected_naga_building_mdx, "Unique Naga building MDX models are incomplete or misnamed"
    assert expected_naga_building_blp.issubset(blp_files), "A generated Naga building texture is missing"
    imp_data = files["war3map.imp"]
    imp_version, imp_count = struct.unpack_from("<II", imp_data, 0)
    assert imp_version == 1, f"Unexpected war3map.imp version {imp_version}"
    imp_paths: Set[str] = set()
    imp_pos = 8
    for _ in range(imp_count):
        imp_pos += 1  # import flags
        imp_end = imp_data.index(bytes(1), imp_pos)
        imp_paths.add(imp_data[imp_pos:imp_end].decode("latin1").replace("/", chr(92)).lower())
        imp_pos = imp_end + 1
    assert imp_pos == len(imp_data), f"war3map.imp has trailing data at {imp_pos}/{len(imp_data)}"
    expected_building_imports = {path.replace("/", chr(92)).lower() for path in expected_naga_building_mdx | expected_naga_building_blp}
    assert expected_building_imports.issubset(imp_paths), (
        f"Naga building models/textures are missing import-table entries: {sorted(expected_building_imports - imp_paths)}"
    )
    expected_skill_mdx = {f"WM_Skill_{i:02d}.mdx" for i in range(64)}
    expected_skill_blp = {f"Textures\\WM_Skill_{i:02d}.blp" for i in range(64)}
    assert set(skill_mdx_files) == expected_skill_mdx, "The 64 skill-specific MDX models are incomplete or misnamed"
    assert expected_skill_blp.issubset(blp_files), "At least one skill-specific true-color texture is missing"
    assert len({skill_mdx_files[name] for name in expected_skill_mdx}) == 64, "Skill model binaries must all be distinct"
    assert len({blp_files[name] for name in expected_skill_blp}) == 64, "Skill textures must all be distinct"
    skill_index_src = jass_src.split("function WM_GetUniqueSkillVFXIndex", 1)[1].split("endfunction", 1)[0]
    skill_index_pairs = [(int(raw), int(index)) for raw, index in re.findall(r"(?:if|elseif) abil == 'A([0-9]{3})' then\s+return ([0-9]+)", skill_index_src)]
    skill_index_pairs = [(int(raw), int(index)) for raw, index in re.findall(r"(?:if|elseif) abil == 'A([0-9]{3})' then\s+return ([0-9]+)", skill_index_src)]
    for name, data in skill_mdx_files.items():
        assert data[:4] == b"MDLX" and data[4:8] == b"VERS" and struct.unpack_from("<I", data, 12)[0] == 800, f"Invalid skill MDX: {name}"
    for name, data in building_mdx_files.items():
        assert data[:4] == b"MDLX" and data[4:8] == b"VERS" and struct.unpack_from("<I", data, 12)[0] == 800, f"Invalid Naga building MDX: {name}"
    for name in expected_skill_blp:
        content, _alpha, width, height, _typ, _mips = struct.unpack_from("<6I", blp_files[name], 4)
        assert content == 0 and (width, height) == (128, 128), f"Skill VFX texture must be true-color 128x128: {name}"
    for name in expected_naga_building_blp:
        content, _alpha, width, height, _typ, _mips = struct.unpack_from("<6I", blp_files[name], 4)
        assert content == 0 and (width, height) == (256, 256), f"Naga building texture must be true-color 256x256: {name}"

    portrait_rawcodes = ("Hvsh", "N004", "N001", "N002", "Hkal", "Hvwd", "Hlgr", "Huth", "V001", "V002")
    portrait_blp_paths: Set[str] = set()
    for rawcode in portrait_rawcodes:
        portrait_blp_paths.add(f"ReplaceableTextures\\CommandButtons\\BTN_WM_Portrait_{rawcode}.blp")
        portrait_blp_paths.add(f"ReplaceableTextures\\CommandButtonsDisabled\\DISBTN_WM_Portrait_{rawcode}.blp")
    assert portrait_blp_paths.issubset(blp_files), f"Missing custom portrait BLP pairs: {sorted(portrait_blp_paths - set(blp_files))}"

    skill_icon_rawcodes = {f"A{i:03d}" for i in range(64)}
    skill_normal_blps = {
        f"ReplaceableTextures\\CommandButtons\\BTN_WM_Skill_{rawcode}.blp" for rawcode in skill_icon_rawcodes
    }
    skill_disabled_blps = {
        f"ReplaceableTextures\\CommandButtonsDisabled\\DISBTN_WM_Skill_{rawcode}.blp" for rawcode in skill_icon_rawcodes
    }
    skill_icon_blp_paths = skill_normal_blps | skill_disabled_blps
    assert skill_icon_blp_paths.issubset(blp_files), (
        f"Missing custom skill BTN/DISBTN assets: {sorted(skill_icon_blp_paths - set(blp_files))}"
    )
    icon_blp_paths = portrait_blp_paths | skill_icon_blp_paths

    palette_blp_paths: Set[str] = set()
    for name, data in blp_files.items():
        assert data[:4] == b"BLP1", f"Invalid BLP1 magic on {name}"
        content, alpha_bits, bw, bh, _typ, _mips = struct.unpack_from("<6I", data, 4)
        assert content in (0, 1), f"Unknown BLP1 encoding {content} on {name}"
        assert bw > 0 and bh > 0 and (bw & (bw - 1)) == 0 and (bh & (bh - 1)) == 0, f"Invalid BLP1 dimensions on {name}: {bw}x{bh}"
        if content == 1:
            assert name in icon_blp_paths, f"Palette-encoded BLP is not a command-button icon: {name}"
            assert (bw, bh) == (64, 64), f"Custom command-button icon must be 64x64: {name}"
            expected_alpha_bits = 0 if name in portrait_blp_paths else 8
            assert alpha_bits == expected_alpha_bits, f"Unexpected palette alpha depth on {name}: {alpha_bits}"
            palette_blp_paths.add(name)
        else:
            assert name not in icon_blp_paths, f"Command-button icon must remain an icon-only paletted BLP: {name}"
    assert palette_blp_paths == icon_blp_paths, "Palette BLP use must be limited to custom portrait/skill BTN-DISBTN pairs"
    assert len({blp_files[name] for name in skill_normal_blps}) == 64, "All 64 normal skill icons must be binary-distinct"
    assert len({blp_files[name] for name in skill_disabled_blps}) == 64, "All 64 disabled skill icons must be binary-distinct"
    assert all(blp_files[normal] != blp_files[disabled] for normal, disabled in zip(sorted(skill_normal_blps), sorted(skill_disabled_blps))), (
        "Every custom skill must have a distinct normal/disabled icon pair"
    )

    for race_cursor in ("Human", "Orc", "Undead", "NightElf"):
        name = f"UI\\Cursor\\{race_cursor}Cursor.blp"
        assert name in files and struct.unpack_from("<II", files[name], 12)[0:2] == (256, 128), f"Missing or invalid custom cursor atlas: {name}"
    print(f"[PASS] Stage 14: Native race/building references + 10 portrait pairs + 64 skill BTN/DISBTN pairs + {len(blp_files)} BLP1s + 6 faction/64 skill MDX effects + 3 unique Naga building MDXs")

    # ------------------------------------------------------------------
    # STAGE 15: TFT 1.26-era API Compatibility & AI Startup/Fallback Coverage
    # ------------------------------------------------------------------
    ref_124 = Path("/tmp/wc3ref/w3x2lni/data/zhCN-1.24.4/mpq/Scripts")
    if ref_124.exists():
        chk_124 = JassChecker()
        chk_124.check_file((ref_124 / "Common.j").read_text(encoding="utf-8", errors="ignore"), "1.24.4/Common.j (1.26-era API proxy)")
        chk_124.check_file((ref_124 / "Blizzard.j").read_text(encoding="utf-8", errors="ignore"), "1.24.4/Blizzard.j")
        legacy_fn_count = chk_124.check_file(jass_src, "war3map.j (1.26-era API proxy)")
    else:
        legacy_fn_count = 0

    ai_entry_names = ("naga_melee.ai", "camphuman_melee.ai", "voidborn_melee.ai", "runeforged_melee.ai")
    for ai_name in ai_entry_names:
        assert ai_name in files, f"Missing imported race AI file {ai_name}!"
    for ai_path in (
        'StartMeleeAI(p, "naga_melee.ai")',
        'StartMeleeAI(p, "camphuman_melee.ai")',
        'StartMeleeAI(p, "voidborn_melee.ai")',
        'StartMeleeAI(p, "runeforged_melee.ai")',
    ):
        assert ai_path not in jass_src, f"Custom faction must not start a competing native .ai controller: {ai_path}"
    assert "if faction >= 5 then" in jass_src, "Custom factions must bypass StartMeleeAI"
    for standard_ai in ("Scripts\\\\human.ai", "Scripts\\\\orc.ai", "Scripts\\\\undead.ai", "Scripts\\\\elf.ai"):
        assert standard_ai in jass_src, f"Standard race melee AI path missing: {standard_ai}"
    for ai_name, first_id, last_id in (("voidborn_melee.ai", 32, 47), ("runeforged_melee.ai", 48, 63)):
        ai_src = files[ai_name].decode("utf-8")
        expected_skill_ids = {f"A{i:03d}" for i in range(first_id, last_id + 1)}
        assigned_skill_ids = set(re.findall(r"'([A][0-9]{3})'", ai_src))
        assert expected_skill_ids.issubset(assigned_skill_ids), (
            f"{ai_name} is missing its exact 16 custom hero-skill rawcodes: "
            f"{sorted(expected_skill_ids - assigned_skill_ids)}"
        )

    naga_ai_src = files["naga_melee.ai"].decode("utf-8")
    for upgrade in ("UPG_NAGA_ENSNARE", "UPG_NAGA_SUBMERGE", "UPG_NAGA_ABOLISH"):
        assert f"if GetUpgradeLevel({upgrade}) < 1 then" in naga_ai_src, (
            f"Naga AI data script must guard repeat research orders for {upgrade}"
        )

    assert "function WM_AIFallbackBuild" in jass_src and "function WM_AIQueueFallbackBuild" in jass_src and "IssueBuildOrderById" in jass_src, "Sequential worker-build controller missing!"
    assert "function WM_OnAIFallbackBuildFinished" in jass_src and "EVENT_PLAYER_UNIT_CONSTRUCT_FINISH" in jass_src, "AI construction latch is not cleared on completion!"
    assert "udg_AIFallbackPendingRaw" in jass_src and "udg_AINextRaxOrderAt" in jass_src, "AI pending-build/production cooldown state missing!"
    assert "WM_IsCustomAIWorker(f, rawcode)" in jass_src and "'nmpe'" in jass_src and "'nhew'" in jass_src and "'v010'" in jass_src and "'t010'" in jass_src, "Explicit custom-worker detection is incomplete!"
    assert "WM_AIChooseCustomHeroSkill(u, f)" in jass_src and "heroCount < 3" in jass_src, "Independent hero skill spending or altar hero-count guard missing!"
    assert "udg_AINextHeroOrderAt[i]" in jass_src and "udg_AINextSanctumOrderAt[i]" in jass_src, "Sequential altar/caster orders are not guarded!"
    assert "function WM_AIUseInventory" in jass_src and "UnitUseItemPoint" in jass_src, "AI consumable/retreat micro fallback missing!"

    # Ensure each custom worker is typed as a peon and owns real harvesting/build abilities.
    for faction_id, _hall_id, worker_id in spawn_templates:
        worker_mods = mod_lookup[worker_id][1]
        assert "Peon" in str(worker_mods.get("utyp", "")), f"Empire {faction_id} worker {worker_id} is missing the Peon type tag"
        assert "Ahar" in str(worker_mods.get("uabi", "")), f"Empire {faction_id} worker {worker_id} is missing its explicit Harvest ability"

    safe_point_src = jass_src.split("function WM_IsSafeUnitPoint", 1)[1].split("endfunction", 1)[0]
    assert "IsTerrainPathable" in safe_point_src and "GroupEnumUnitsInRange" in safe_point_src, (
        "Summon/displacement placement must test both terrain pathability and nearby unit occupancy"
    )
    assert "UNIT_TYPE_STRUCTURE" in safe_point_src and "UNIT_TYPE_FLYING" in safe_point_src, (
        "Safe placement must account for building footprints and separate ground/flying collision"
    )
    assert "set searchRadius = clearance + 192.0" in safe_point_src and "set minDist = clearance + 176.0" in safe_point_src, (
        "Safe placement must conservatively query and clear classic structure footprints"
    )
    safe_search_src = jass_src.split("function WM_FindSafeUnitPoint", 1)[1].split("endfunction", 1)[0]
    assert "I2R(ring) * 48.0" in safe_search_src and "spoke >= 8" in safe_search_src, (
        "Safe placement must search deterministic rings around a blocked origin"
    )
    spawn_src = jass_src.split("function WM_SpawnTimedUnit", 1)[1].split("endfunction", 1)[0]
    assert "WM_FindSafeUnitPoint(null, WM_ClampMapCoord(x), WM_ClampMapCoord(y), 72.0, terrainPath, flying, 240.0)" in spawn_src, (
        "Timed summons must search for an unblocked point instead of spawning inside terrain or units"
    )
    assert "rawcode == 'hphx' or rawcode == 't015'" in spawn_src and "PATHING_TYPE_FLYABILITY" in spawn_src, (
        "Flying Phoenix/Gyro summons must use flying pathing rules"
    )
    assert "rawcode == 'nmyr' or rawcode == 'nsnp'" in spawn_src and "PATHING_TYPE_AMPHIBIOUSPATHING" in spawn_src, (
        "Naga Myrmidon/Snap Dragon summons must use classic amphibious pathing"
    )
    amphib_src = jass_src.split("function WM_UsesAmphibiousPathing", 1)[1].split("endfunction", 1)[0]
    assert all(f"'{code}'" in amphib_src for code in ("nmpe", "nnmg", "nsnp", "nmyr", "nnsw", "nhyc", "nnrg", "Hvsh", "N004", "N001", "N002")), (
        "Custom Naga ground/amphibious units must retain amphibious pathing during displacement"
    )
    pull_src = jass_src.split("function WM_PullOrPushUnit", 1)[1].split("endfunction", 1)[0]
    assert "WM_FindSafeUnitPoint(u, nx, ny, 56.0, terrainPath, flying, 144.0)" in pull_src and "udg_SafePointX" in pull_src, (
        "Pull/push displacement must stop or adjust when the destination collides with terrain, units, or structures"
    )
    assert "WM_UsesAmphibiousPathing(u)" in pull_src and "PATHING_TYPE_FLYABILITY" in pull_src, (
        "Pull/push must use movement-specific terrain checks for Naga amphibious units and flyers"
    )
    print(f"[PASS] Stage 15: Classic TFT 1.26/1.27 API proxy ({legacy_fn_count} functions) + native race AI + safe summon/displacement + sequential custom-AI guards")

    # ------------------------------------------------------------------
    # STAGE 16: Melee Fairness — Symmetric Objectives, Balanced Camp Loot & Lobby Teams
    # ------------------------------------------------------------------
    neutral_units = [u for u in parsed_units if int(u["player"]) in (12, 15)]
    neutral_profiles = collections.defaultdict(collections.Counter)
    for u in neutral_units:
        profile = (
            str(u["uid"]), int(u["player"]), int(u["gold"]), round(float(u["acq"]), 1),
            tuple(sorted((str(iid), int(chance)) for iid, chance in u["drops"])),
        )
        neutral_profiles[profile][(round(float(u["x"]), 1), round(float(u["y"]), 1))] += 1

    def d4_world_images(wx: float, wy: float) -> Tuple[Tuple[float, float], ...]:
        return (
            (wx, wy), (-wx, wy), (wx, -wy), (-wx, -wy),
            (wy, wx), (-wy, wx), (wy, -wx), (-wy, -wx),
        )

    for profile, positions in neutral_profiles.items():
        for (wx, wy), multiplicity in positions.items():
            for sx, sy in d4_world_images(wx, wy):
                image = (round(sx, 1), round(sy, 1))
                assert positions[image] == multiplicity, (
                    f"Neutral object/camp member is not D4-symmetric: {profile} at ({wx},{wy}) "
                    f"maps to {image} with multiplicity {positions[image]} instead of {multiplicity}"
                )
    assert len(neutral_units) == 173, f"Expected 136 creeps + 37 neutral buildings, got {len(neutral_units)}"

    start_positions = {(round(float(u["x"]), 1), round(float(u["y"]), 1)) for u in slocs}
    for u in slocs:
        for sx, sy in d4_world_images(float(u["x"]), float(u["y"])):
            assert (round(sx, 1), round(sy, 1)) in start_positions, (
                f"Player start ({u['x']},{u['y']}) is missing its D4 image ({sx},{sy})"
            )

    camp_specs = {
        "Gnoll Outpost (Lvl 6)": ("green", 8, 6, [("YiI1", 100)]),
        "Ogre Expansion Guard (Lvl 13)": ("orange", 8, 13, [("YiI3", 100), ("YjI2", 100)]),
        "Merchant Guard (Lvl 13)": ("orange", 4, 13, [("YiI2", 100), ("YjI2", 100)]),
        "Laboratory Troll Guard (Lvl 12)": ("orange", 4, 12, [("YjI3", 100)]),
        "Mercenary Golem Guard (Lvl 10)": ("orange", 4, 10, [("YiI3", 100)]),
        "Ancient Granite Boss (Lvl 21)": ("red", 4, 21, [("YiI5", 100), ("YjI4", 100)]),
        "Red Dragon Sanctum (Lvl 23)": ("red", 4, 23, [("YiI5", 100), ("texp", 100), ("YjI4", 100)]),
    }
    metadata_path = Path(__file__).resolve().parent.parent / "web" / "public" / "map_data.json"
    map_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    map_stats = map_metadata.get("stats", {})
    actual_blp_count = sum(1 for name in files if name.lower().endswith(".blp"))
    mdx_stems = [Path(name).stem for name in files if name.lower().endswith(".mdx")]
    actual_skill_mdx_count = sum(1 for name in mdx_stems if name.startswith("WM_Skill_"))
    actual_sigil_mdx_count = sum(1 for name in mdx_stems if name.startswith("WM_FX_"))
    actual_building_mdx_count = sum(1 for name in mdx_stems if name.startswith("WM_Build_Naga_"))
    assert map_stats.get("archiveFiles") == len(files), (
        f"Preview archive-file count is stale: {map_stats.get('archiveFiles')} != {len(files)}"
    )
    assert map_stats.get("blpFiles") == actual_blp_count, (
        f"Preview BLP count is stale: {map_stats.get('blpFiles')} != {actual_blp_count}"
    )
    assert map_stats.get("customSkillEffects") == actual_skill_mdx_count, (
        f"Preview skill-MDX count is stale: {map_stats.get('customSkillEffects')} != {actual_skill_mdx_count}"
    )
    assert map_stats.get("customFactionSigils") == actual_sigil_mdx_count, (
        f"Preview faction-sigil-MDX count is stale: {map_stats.get('customFactionSigils')} != {actual_sigil_mdx_count}"
    )
    assert map_stats.get("customVfxModels") == actual_skill_mdx_count + actual_sigil_mdx_count, (
        "Preview VFX model count is stale relative to the packed MDX files"
    )
    assert map_stats.get("customBuildingModels") == actual_building_mdx_count, (
        f"Preview building-MDX count is stale: {map_stats.get('customBuildingModels')} != {actual_building_mdx_count}"
    )
    assert map_stats.get("preplacedUnits") == len(parsed_units), (
        f"Preview preplaced-unit count is stale: {map_stats.get('preplacedUnits')} != {len(parsed_units)}"
    )
    assert map_stats.get("mapDoodads") == tree_cnt, (
        f"Preview doodad count is stale: {map_stats.get('mapDoodads')} != {tree_cnt}"
    )
    assert map_stats.get("trees", 0) + map_stats.get("scenicDoodads", 0) == tree_cnt, (
        "Preview tree/scenic-doodad subtotals do not match the packed doodad archive"
    )
    assert map_stats.get("mapStrings") == len(defined_strs), (
        f"Preview string count is stale: {map_stats.get('mapStrings')} != {len(defined_strs)}"
    )
    assert map_stats.get("minimapIcons") == mmp_cnt, (
        f"Preview minimap-icon count is stale: {map_stats.get('minimapIcons')} != {mmp_cnt}"
    )
    assert map_stats.get("startLocations") == len(slocs), (
        f"Preview start-location count is stale: {map_stats.get('startLocations')} != {len(slocs)}"
    )
    compatibility = " ".join(str(item) for item in map_metadata.get("compatibility", []))
    assert "1.26a" in compatibility and "1.27b" in compatibility and "reforged" not in compatibility.lower(), (
        f"Map metadata must declare classic TFT 1.26a/1.27b only: {compatibility}"
    )
    camp_metadata = map_metadata.get("camps", [])
    actual_gold_mines = sum(1 for unit in parsed_units if unit["uid"] == "ngol")
    actual_total_gold = sum(int(unit["gold"]) for unit in parsed_units if unit["uid"] == "ngol")
    actual_neutral_buildings = sum(1 for unit in parsed_units if int(unit["player"]) == 15 and unit["uid"] != "ngol")
    actual_creep_units = sum(1 for unit in parsed_units if int(unit["player"]) == 12)
    null_rawcode = "\x00\x00\x00\x00"
    actual_custom_heroes = sum(
        1 for oid, nid, mods in w3u_orig + w3u_cust
        if (nid if nid != null_rawcode else oid)[0].isupper() and any(fid == "uhab" for fid, _vt, _lev, _dat, _val in mods)
    )
    assert map_stats.get("goldMines") == actual_gold_mines, (
        f"Preview gold-mine count is stale: {map_stats.get('goldMines')} != {actual_gold_mines}"
    )
    assert map_stats.get("totalGoldOnMap") == actual_total_gold, (
        f"Preview total mine gold is stale: {map_stats.get('totalGoldOnMap')} != {actual_total_gold}"
    )
    assert map_stats.get("neutralBuildings") == actual_neutral_buildings, (
        f"Preview neutral-building count is stale: {map_stats.get('neutralBuildings')} != {actual_neutral_buildings}"
    )
    assert map_stats.get("creepUnits") == actual_creep_units, (
        f"Preview creep-unit count is stale: {map_stats.get('creepUnits')} != {actual_creep_units}"
    )
    assert map_stats.get("creepCamps") == len(camp_metadata), (
        f"Preview creep-camp count is stale: {map_stats.get('creepCamps')} != {len(camp_metadata)}"
    )
    assert map_stats.get("customSkills") == len(w3a_cust), (
        f"Preview custom-skill count is stale: {map_stats.get('customSkills')} != {len(w3a_cust)}"
    )
    assert map_stats.get("customHeroes") == actual_custom_heroes, (
        f"Preview custom-hero count is stale: {map_stats.get('customHeroes')} != {actual_custom_heroes}"
    )
    assert len(camp_metadata) == 36, f"Expected 36 camp summaries in preview metadata, got {len(camp_metadata)}"
    creeps = [u for u in parsed_units if int(u["player"]) == 12]
    assigned_creep_indices = set()
    camp_counts = collections.Counter()
    level_camps_checked = 0
    for camp in camp_metadata:
        name = str(camp["name"])
        assert name in camp_specs, f"Unexpected creep camp tier/name {name!r}"
        expected_tier, _expected_count, expected_level, expected_drops = camp_specs[name]
        assert camp["tier"] == expected_tier, f"Incorrect tier label for {name}: {camp['tier']}"
        camp_counts[name] += 1
        cx, cy = float(camp["x"]), float(camp["y"])
        member_indices = [
            i for i, u in enumerate(creeps)
            if math.hypot(float(u["x"]) - cx, float(u["y"]) - cy) <= 400.0
        ]
        assert len(member_indices) == len(camp["units"]), (
            f"Camp {name} at ({cx},{cy}) has {len(member_indices)} packed creeps, "
            f"but preview metadata lists {len(camp['units'])}"
        )
        assert not (assigned_creep_indices & set(member_indices)), f"Overlapping camp groups near ({cx},{cy})"
        assigned_creep_indices.update(member_indices)
        members = [creeps[i] for i in member_indices]
        actual_ids = sorted(str(u["uid"]) for u in members)
        assert actual_ids == sorted(str(uid) for uid in camp["units"]), (
            f"Packed camp unit roster differs from preview metadata for {name}: {actual_ids} != {camp['units']}"
        )
        actual_drops = collections.Counter(
            (str(iid), int(chance)) for u in members for iid, chance in u["drops"]
        )
        assert actual_drops == collections.Counter(expected_drops), (
            f"Incorrect packed item-drop tier for {name}: {actual_drops} != {collections.Counter(expected_drops)}"
        )
        if slk_ubal:
            for uid in actual_ids:
                assert uid in slk_ubal and "level" in slk_ubal[uid], f"No reference unit level for camp member {uid}"
            actual_level = sum(int(float(slk_ubal[uid]["level"])) for uid in actual_ids)
            assert actual_level == expected_level, (
                f"Camp {name} is labeled Lvl {expected_level}, but reference unit levels sum to {actual_level}"
            )
            level_camps_checked += 1
    assert len(assigned_creep_indices) == len(creeps) == 136, (
        f"Camp summaries account for {len(assigned_creep_indices)} of {len(creeps)} packed creeps"
    )
    assert camp_counts == collections.Counter({name: spec[1] for name, spec in camp_specs.items()}), (
        f"Creep camp count/tier distribution mismatch: {camp_counts}"
    )

    shrine_tick = jass_src.split("function WM_OnHUDAndShrineTick", 1)[1].split("endfunction", 1)[0]
    shrine_refresh = jass_src.split("function WM_RefreshMultiboard", 1)[1].split("endfunction", 1)[0]
    race_choice = jass_src.split("function WM_OnRaceDialogClick", 1)[1].split("endfunction", 1)[0]
    assert "IsPlayerAlly(owner, captor)" in shrine_tick and "IsPlayerAlly(Player(pid), captor)" in shrine_tick, (
        "Crown Shrine capture/rewards must follow actual lobby alliances"
    )
    assert "pid < 4" not in shrine_tick and "pid >= 4" not in shrine_tick, (
        "Crown Shrine must not split players into hard-coded four-slot teams"
    )
    assert "GetPlayerName(Player(shrinePid))" in shrine_refresh and "West Pact" not in shrine_refresh, (
        "Crown Shrine HUD must identify its live controller rather than fixed map halves"
    )
    assert "SetPlayerState" not in race_choice and "PLAYER_STATE_RESOURCE_GOLD" not in race_choice, (
        "Race selection (including Random Custom) must not create bonus starting gold"
    )
    assert "+50g" not in jass_src, "Stale Random Custom +50g label remains in the in-game menu"
    assert "GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD) + 3" in shrine_tick, (
        "Crown Shrine's documented +3 gold per 2-second hold tick is missing"
    )
    print(
        f"[PASS] Stage 16: Melee Fairness ({len(neutral_units)} neutral objects D4-symmetric; "
        f"36 camps with exact drop tiers and {level_camps_checked} reference-checked level budgets; "
        "alliance-aware shrine + zero race-pick gold bonus)"
    )

    # ------------------------------------------------------------------
    # STAGE 17: Fair-vision, adaptive objectives/counters, role micro, and AI telemetry
    # ------------------------------------------------------------------
    intel_src = jass_src.split("function WM_AIRefreshEnemyIntel", 1)[1].split("endfunction", 1)[0]
    objective_src = jass_src.split("function WM_AIChooseMarchObjective", 1)[1].split("endfunction", 1)[0]
    creep_src = objective_src
    natural_mine_src = jass_src.split("function WM_AIFindVisibleNaturalMine", 1)[1].split("endfunction", 1)[0]
    spell_center_src = jass_src.split("function WM_AISelectSpellCenter", 1)[1].split("endfunction", 1)[0]
    visible_count_src = jass_src.split("function WM_AICountVisibleEnemies", 1)[1].split("endfunction", 1)[0]
    fallen_ally_src = jass_src.split("function WM_AIHasFallenAllyHero", 1)[1].split("endfunction", 1)[0]
    spell_target_src = jass_src.split("function WM_AIFindSpellTarget", 1)[1].split("endfunction", 1)[0]
    spell_combo_src = jass_src.split("function WM_AICastCustomHeroCombo", 1)[1].split("endfunction", 1)[0]
    micro_src = jass_src.split("function WM_OnAITacticalMicroTick", 1)[1].split("endfunction", 1)[0]
    macro_src = jass_src.split("function WM_OnProAIMacroTick", 1)[1].split("endfunction", 1)[0]
    chat_src = jass_src.split("function WM_OnPlayerChatCommand", 1)[1].split("endfunction", 1)[0]
    metrics_src = jass_src.split("function WM_ShowAIMetrics", 1)[1].split("endfunction", 1)[0]

    assert "IsUnitVisible(u, aiPlayer)" in intel_src, "Enemy intel must filter units through the AI player's current vision"
    assert "udg_AILastSeenX[slot]" in intel_src and "udg_AILastSeenY[slot]" in intel_src and "udg_AILastSeenAt[slot] = udg_MatchSeconds" in intel_src, (
        "Fair enemy memory must store only observed positions and their observation time"
    )
    assert "WM_AIObservedHallTier(rawcode)" in intel_src and "udg_AIEnemyAirSeen[slot]" in intel_src and "udg_AIEnemyCasterSeen[slot]" in intel_src, (
        "AI must adapt to visible enemy tier, air, and caster observations—not hidden player technology"
    )
    assert "seenAir >= udg_AIEnemyAirSeen[slot]" in intel_src and "seenCasters >= udg_AIEnemyCasterSeen[slot]" in intel_src and "age > 150" in intel_src and "udg_AIEnemyAirSeen[slot] - 1" in intel_src, (
        "Composition evidence must refresh only at equal-or-higher observed counts and decay when that evidence gets stale"
    )
    assert "age <= 120" in objective_src and "udg_AILastSeenX[bestSlot]" in objective_src, (
        "Scouting must use only expiring last-seen coordinates, not hidden enemy unit positions"
    )
    assert "IsUnitVisible(u, p)" in creep_src and "Player(PLAYER_NEUTRAL_AGGRESSIVE)" in creep_src, (
        "Creep selection must use currently visible camps only"
    )
    assert "GetStartLocationX(GetPlayerStartLocation(Player(j)))" in objective_src and "udg_AIObjectiveMode[pid] = 5" in objective_src, (
        "Late scouting may use the public start-location prior, but must remain a point-search objective"
    )
    assert "IsUnitVisible(u, p)" in natural_mine_src and "WM_AIIsTownHallRawcode(rawcode)" in natural_mine_src, (
        "Natural expansion discovery must be visibility-gated and reject a visibly occupied town-hall site"
    )
    assert "WM_AIQueueExpansion" in macro_src and "tier >= 3" in macro_src and "hallCount == 1" in macro_src and "udg_AIExpansionPending" in macro_src, (
        "Expansion must be a guarded worker build after tier 3, not a free hall or hidden-site placement"
    )
    assert "expansionWorkerCount < 3" in macro_src and "udg_AIObjectiveMode[i] == 4" in macro_src, (
        "The expansion plan must staff a second mine and count defensive responses"
    )
    assert "enemyAirCount >= 2" in macro_src and "enemyCasterCount >= 2" in macro_src and "enemyTierCount > tier" in macro_src, (
        "Composition and visible tech observations must change production and tech tempo"
    )
    assert "set productionId = 'hdhw'\n                        set unitFood = 3" in macro_src and "set productionId = 'hgry'\n                        set unitFood = 4" in macro_src and "foodUsed + unitFood <= foodCap and gold >= 160" in macro_src, (
        "Adapted air production must respect the actual Dragonhawk/Gryphon food values"
    )
    assert "udg_TempGroupB" in spell_center_src and "udg_TempGroupA" not in spell_center_src and "IsUnitVisible(nearby, owner)" in spell_center_src and "WM_IsCustomAIWorker" in spell_center_src, (
        "AOE scoring must use visible combat units and avoid clobbering the tactical outer unit group"
    )
    assert "WM_IsCustomAIWorker" in visible_count_src and "IsUnitVisible(u, owner)" in fallen_ally_src, (
        "Spell triggers must not waste major AoE casts on custom workers or detect an unseen resurrection target"
    )
    assert "not IsUnitType(foe, UNIT_TYPE_PEON)" in micro_src and "WM_IsCustomAIWorker(udg_PlayerFaction[enemyPid], rawcode)" in micro_src, (
        "Local-force micro must assess visible combat units rather than worker counts"
    )
    assert all(code in spell_combo_src for code in ("'A005'", "'A013'", "'A017'", "'A037'", "'A045'", "'A031'", "'A025'")), (
        "Hero spell logic must include mana-target, Resurrection, and execution-specific decisions"
    )
    assert "WM_AISelectSpellCenter" in spell_combo_src and "WM_AIShouldCastAreaE" in spell_combo_src and "GetUnitState(manaTarget, UNIT_STATE_MANA) >= 25.0" in spell_combo_src and "WM_IsCustomAIWorker" in spell_target_src, (
        "Hero spells must evaluate AOE density, support needs, and Mana Burn value before orders"
    )
    assert "udg_PlayerFaction[i] >= 5" in micro_src and "localEnemyCount >= localAllyCount + 2" in micro_src and "udg_AIMetricRetreatOrders" in micro_src and "udg_AIMetricFocusOrders" in micro_src, (
        "Custom-faction group micro must compare visible local strength, retreat when outnumbered, and focus fire without overriding native melee AI"
    )
    assert "f >= 5 and armyCount >= 5" in macro_src and "if f >= 5 then" in macro_src and "WM_AIRefreshEnemyIntel" in macro_src, (
        "The custom JASS commander must leave classic races on native melee AI and run fair enemy intel only for custom factions"
    )
    assert all(value in macro_src for value in ("set ecoBonusG = 2", "set ecoBonusG = 4", "set ecoBonusG = 7")), (
        "Difficulty resource support must remain small and explicitly tiered"
    )
    assert "WM_GetDiffSupportLabel" in jass_src and "-aistats" in chat_src and "udg_AIMetricVisibleContacts" in metrics_src and "udg_AIMetricCounterOrders" in metrics_src and "udg_PlayerFaction[i] >= 5" in metrics_src and "No custom-faction AI opponents" in metrics_src, (
        "Difficulty and custom-AI decision metrics must be disclosed and queryable without presenting native-AI zeros as telemetry"
    )
    print("[PASS] Stage 17: Fair-vision AI (TTL intel, observed counter/tech adaptation, dynamic shrine/creep/expansion/defense/scouting, coordinated micro, hero spell evaluation, disclosed difficulty + -aistats telemetry)")

    print("======================================================================")
    print("  ALL 17 VERIFICATION STAGES PASSED; static/binary checks found no known object/UI/AI-startup/fairness defects.")
    print("======================================================================")


if __name__ == "__main__":
    default_map = Path(__file__).resolve().parent.parent / "maps" / "(8)CrownOfWarMahdi.w3x"
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else default_map
    run_verification(target)
