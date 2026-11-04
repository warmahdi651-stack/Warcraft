#!/usr/bin/env python3
"""
Procedural & Artwork Asset Pipeline for `(8) Crown of WarMahdi` v4.

Generates and validates 100% custom, non-vanilla Warcraft III binary assets:
  1. `war3mapPreview.tga` (256x256 uncompressed 24-bit TrueColor TGA derived from
     `web/public/crown_artwork.png` with ornate astral-gold frame & v4 badge).
  2. Custom Animated Multi-State Mouse Cursor (`256x128` 8-bit alpha `BLP1` on the
     exact 8x4 `32x32` `War3CursorCatalog` UV grid: Sovereign Obsidian-Gold Gauntlet,
     8-frame Emerald Friendly Hover, 8-frame Crimson Attack Hover, 8-frame Rotating
     Runic Crosshair Reticle, Invalid Seal, Gauntlet Grip, and 3-frame Winged Scroll
     Chevron) packed at `UI\\Cursor\\HumanCursor.blp`, `OrcCursor.blp`,
     `UndeadCursor.blp`, and `NightElfCursor.blp`.
  3. Badass RPG-Style Custom Infocard Icons (`64x64` 8-bit alpha `BLP1`):
       - 6 Damage Type Icons x 2 (`Upgraded` w/ metallic +badge & `Neutral`):
         Normal/Melee, Piercing, Siege, Magic, Chaos, Hero
       - 7 Armor Type Icons x 2 (`Upgraded` & `Neutral`):
         Light/Small, Medium/Normal, Heavy/Large, Fortified, Hero, Divine, Unarmored
       - 3 Hero Primary Attribute Icons (`STR`, `AGI`, `INT`)
       - Custom Resource & Console Textures (`MenuBG`, `IconGold`, `IconLumber`,
         `IconSupply`, `IconUpkeep`, `SlotFiller`)
  4. Custom Command Card Action Icons (`CmdAttack`, `CmdMove`, `CmdStop`, `CmdHold`,
     `CmdPatrol`, `CmdSkill`, `CmdRally`, `CmdCancel`) + 5 Race-Specific Worker
     `Build` Icons (`BuildNaga`, `BuildSunfury`, `BuildVoidborn`, `BuildRuneforged`,
     `BuildNightElf`).
  5. Custom Race-Specific Structure, Hero & Unit Icons (`BTN` + `DISBTN` pairs) for
     Abyssal Tideborn (including Hero Illidan!), Sunfury Imperium, Voidborn Legion,
     and Runeforged Bastion — zero Human leftover icons on non-Human races!
  6. 64 Unique Custom Hero Skill Icons (`BTN_WM_S00..S63` + `DISBTN_WM_S00..S63` =
     128 skill BLPs, 16 heroes x 4 unique skills, zero shared icons!) + `CrownCrest`
     & `FactionTome`.
  7. 6 Custom Additive Sigil `.blp` textures + 6 Custom Multi-Geoset 3D `.mdx`
     (`Version 800`) spell VFX models compiled & roundtrip-verified via `mdx-m3-viewer`.
"""

from __future__ import annotations

import math
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


REPO_ROOT = Path(__file__).resolve().parent.parent
ARTWORK_PNG = REPO_ROOT / "web" / "public" / "crown_artwork.png"
PREVIEW_SHEET_PNG = REPO_ROOT / "web" / "public" / "custom_icons_preview.png"
MDX_MODEL_JS = Path("/tmp/wc3ref/node_modules/mdx-m3-viewer/dist/cjs/parsers/mdlx/model")


# ==============================================================================
# 1. LOSSLESS / MIPMAPPED PALETTED BLP1 & UNCOMPRESSED 24-BIT TGA WRITERS
# ==============================================================================

def encode_tga_24bit(img: Image.Image) -> bytes:
    """Encode an RGB PIL Image into a standard bottom-up 24-bit uncompressed TGA."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    header = struct.pack(
        "<BBBHHBHHHHBB",
        0, 0, 2,
        0, 0, 0,
        0, 0,
        w, h,
        24,
        0x00,
    )
    px = rgb.load()
    rows = bytearray()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            r, g, b = px[x, y]
            rows.extend((b, g, r))
    return header + bytes(rows)


def encode_blp1_paletted(img: Image.Image, alpha_bits: int = 8) -> bytes:
    """
    Encode an RGBA PIL Image into a Warcraft III `BLP1` Paletted (`content=1`)
    texture with full mipmap chain down to `1x1` and 8-bit or 0-bit alpha.
    """
    rgba = img.convert("RGBA")
    w, h = rgba.size
    assert (w & (w - 1)) == 0 and (h & (h - 1)) == 0, f"BLP size must be power-of-2: {w}x{h}"

    rgb0 = rgba.convert("RGB")
    pal_img = rgb0.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    raw_pal = pal_img.getpalette() or []
    while len(raw_pal) < 768:
        raw_pal.extend((0, 0, 0))

    palette_bytes = bytearray(1024)
    for i in range(256):
        palette_bytes[i * 4 + 0] = raw_pal[i * 3 + 2]
        palette_bytes[i * 4 + 1] = raw_pal[i * 3 + 1]
        palette_bytes[i * 4 + 2] = raw_pal[i * 3 + 0]
        palette_bytes[i * 4 + 3] = 0

    num_mips = int(math.log2(max(w, h))) + 1
    mip_blobs: List[bytes] = []
    for lvl in range(num_mips):
        mw = max(1, w >> lvl)
        mh = max(1, h >> lvl)
        m_rgba = rgba if lvl == 0 else rgba.resize((mw, mh), Image.Resampling.LANCZOS)
        m_rgb = m_rgba.convert("RGB")
        m_idx_img = m_rgb.quantize(palette=pal_img, dither=Image.Dither.NONE)
        idx_bytes = m_idx_img.tobytes()
        assert len(idx_bytes) == mw * mh
        if alpha_bits == 8:
            a_bytes = m_rgba.getchannel("A").tobytes()
            assert len(a_bytes) == mw * mh
            mip_blobs.append(idx_bytes + a_bytes)
        else:
            mip_blobs.append(idx_bytes)

    offsets = [0] * 16
    sizes = [0] * 16
    cursor = 156 + 1024
    for i, blob in enumerate(mip_blobs):
        offsets[i] = cursor
        sizes[i] = len(blob)
        cursor += len(blob)

    header = struct.pack(
        "<4s6I16I16I",
        b"BLP1",
        1,
        8 if alpha_bits == 8 else 0,
        w,
        h,
        5,
        1,
        *offsets,
        *sizes,
    )
    return header + bytes(palette_bytes) + b"".join(mip_blobs)


# ==============================================================================
# 2. COMMAND BUTTON BEVEL & DISABLED (`DISBTN`) STYLING
# ==============================================================================

def apply_btn_frame(core: Image.Image, accent_rgb: Tuple[int, int, int]) -> Tuple[Image.Image, Image.Image]:
    """
    Wrap a supersampled icon in an ornate dark-obsidian & gold/faction-accent
    command button bevel (`BTN`) and generate its matching `DISBTN`.
    """
    btn = core.convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(btn)
    ar, ag, ab = accent_rgb

    draw.rectangle([0, 0, 63, 63], outline=(8, 10, 16, 255), width=1)
    draw.rectangle(
        [1, 1, 62, 62],
        outline=(min(255, int(ar * 0.50 + 50)), min(255, int(ag * 0.50 + 50)), min(255, int(ab * 0.50 + 50)), 255),
        width=1,
    )
    draw.rectangle(
        [2, 2, 61, 61],
        outline=(min(255, int(ar * 0.85 + 80)), min(255, int(ag * 0.85 + 80)), min(255, int(ab * 0.85 + 80)), 255),
        width=1,
    )
    draw.rectangle([3, 3, 60, 60], outline=(16, 20, 30, 235), width=1)
    for cx, cy in ((3, 3), (60, 3), (3, 60), (60, 60)):
        draw.point((cx, cy), fill=(255, 240, 195, 255))

    dis_rgb = ImageEnhance.Color(core.convert("RGB").resize((64, 64), Image.Resampling.LANCZOS)).enhance(0.36)
    dis_rgb = ImageEnhance.Brightness(dis_rgb).enhance(0.45)
    dis = dis_rgb.convert("RGBA")
    px = dis.load()
    for y in range(64):
        for x in range(64):
            edge = min(x, y, 63 - x, 63 - y)
            if edge < 4:
                fade = (edge + 0.5) / 4.5
                r, g, b, _ = px[x, y]
                px[x, y] = (int(r * fade), int(g * fade), int(b * fade), 255)
    return btn, dis


def _radial_canvas(
    size: int,
    inner_rgb: Tuple[int, int, int],
    mid_rgb: Tuple[int, int, int],
    outer_rgb: Tuple[int, int, int],
) -> Image.Image:
    img = Image.new("RGBA", (size, size), (*outer_rgb, 255))
    px = img.load()
    cx = cy = (size - 1) / 2.0
    max_r = size * 0.72
    for y in range(size):
        for x in range(size):
            t = min(1.0, math.hypot(x - cx, y - cy) / max_r)
            if t < 0.5:
                u = t / 0.5
                c = tuple(int(inner_rgb[k] * (1 - u) + mid_rgb[k] * u) for k in range(3))
            else:
                u = (t - 0.5) / 0.5
                c = tuple(int(mid_rgb[k] * (1 - u) + outer_rgb[k] * u) for k in range(3))
            px[x, y] = (*c, 255)
    return img


# ==============================================================================
# 3. CUSTOM ANIMATED MULTI-STATE MOUSE CURSOR ATLAS (`256x128` 8x4 x 32x32)
# ==============================================================================

def _draw_sovereign_gauntlet_cell(
    tint_main: Tuple[int, int, int],
    tint_glow: Tuple[int, int, int],
    pulse: float = 0.5,
    grip: bool = False,
) -> Image.Image:
    """
    Render one `32x32` cursor cell at `128x128` supersampled resolution and
    downsample cleanly to `32x32` RGBA so the hotspot at `(3, 3)` is razor-sharp!
    """
    S = 128
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    glow_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    d = ImageDraw.Draw(img)

    # Tip at (12, 12) -> maps to (3, 3) in 32x32!
    r_glow = int(18 + 8 * pulse)
    gd.ellipse([12 - r_glow, 12 - r_glow, 12 + r_glow, 12 + r_glow], fill=(*tint_glow, int(115 + 75 * pulse)))

    if not grip:
        # Sculpted Sovereign Dragon-Talon Gauntlet Blade
        blade_outer = [(10, 10), (96, 38), (68, 56), (108, 96), (92, 112), (52, 72), (36, 98)]
        blade_gold = [(14, 14), (88, 40), (62, 54), (100, 92), (90, 102), (52, 64), (38, 88)]
        blade_core = [(18, 18), (74, 41), (54, 52), (40, 74)]
        gd.polygon(blade_outer, fill=(*tint_glow, int(90 + 60 * pulse)))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(4))
        img = Image.alpha_composite(img, glow_layer)
        d = ImageDraw.Draw(img)

        # Crisp dark silhouette + armored gold bevel + glowing runic energy spine
        d.polygon(blade_outer, fill=(14, 16, 24, 255), outline=(6, 8, 12, 255))
        d.polygon(blade_gold, fill=(*tint_main, 255), outline=(255, 244, 200, 255))
        d.polygon(blade_core, fill=(*tint_glow, 245))
        # Faceted pommel gem & runic wing notches
        d.polygon([(50, 44), (64, 50), (58, 64), (44, 58)], fill=(255, 255, 255, 255), outline=(24, 28, 40, 255))
        d.line([(14, 14), (60, 60)], fill=(255, 255, 255, 240), width=4)
        d.ellipse([84, 84, 104, 104], fill=(*tint_glow, 255), outline=(14, 16, 24, 255), width=3)
    else:
        # Clawed Golden Gauntlet Grip (HoldItem state)
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(4))
        img = Image.alpha_composite(img, glow_layer)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([18, 22, 98, 102], radius=18, fill=(18, 20, 30, 255), outline=(255, 215, 95, 255), width=5)
        for fx in (28, 48, 68):
            d.rounded_rectangle([fx, 14, fx + 16, 56], radius=6, fill=(*tint_main, 255), outline=(14, 16, 24, 255), width=3)
        d.ellipse([44, 54, 78, 88], fill=(*tint_glow, 255), outline=(255, 250, 220, 255), width=3)

    return img.resize((32, 32), Image.Resampling.LANCZOS)


def _draw_reticle_cell(
    ring_rgb: Tuple[int, int, int],
    core_rgb: Tuple[int, int, int],
    angle_deg: float = 0.0,
    invalid: bool = False,
) -> Image.Image:
    """Render a `32x32` spell/attack reticle centered at hotspot `(16, 16)`."""
    S = 128
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = 64.0

    # Outer dark halo + glowing runic ring
    d.ellipse([14, 14, 114, 114], outline=(10, 12, 18, 235), width=9)
    d.ellipse([16, 16, 112, 112], outline=(*ring_rgb, 255), width=5)
    d.ellipse([32, 32, 96, 96], outline=(*core_rgb, 210), width=3)

    if invalid:
        d.line([(26, 26), (102, 102)], fill=(12, 12, 16, 255), width=14)
        d.line([(102, 26), (26, 102)], fill=(12, 12, 16, 255), width=14)
        d.line([(28, 28), (100, 100)], fill=(255, 58, 58, 255), width=8)
        d.line([(100, 28), (28, 100)], fill=(255, 58, 58, 255), width=8)
    else:
        for k in range(4):
            ang = math.radians(angle_deg + k * 90.0)
            x0 = cx + math.cos(ang) * 20
            y0 = cy + math.sin(ang) * 20
            x1 = cx + math.cos(ang) * 58
            y1 = cy + math.sin(ang) * 58
            px_ang = ang + math.pi / 2.0
            pts = [
                (x0, y0),
                (cx + math.cos(ang) * 42 + math.cos(px_ang) * 8, cy + math.sin(ang) * 42 + math.sin(px_ang) * 8),
                (x1, y1),
                (cx + math.cos(ang) * 42 - math.cos(px_ang) * 8, cy + math.sin(ang) * 42 - math.sin(px_ang) * 8),
            ]
            d.polygon(pts, fill=(*core_rgb, 255), outline=(12, 14, 22, 255))
        d.ellipse([56, 56, 72, 72], fill=(255, 255, 255, 255), outline=(*ring_rgb, 255), width=3)

    return img.resize((32, 32), Image.Resampling.LANCZOS)


def _draw_scroll_chevron_cell(step: int) -> Image.Image:
    """
    Render a `32x32` winged golden scroll arrow pointing RIGHT `(1, 0)` at center `(16, 16)`
    (Warcraft III rotates this mesh in 45-degree increments for all 8 edge-scroll directions).
    """
    S = 128
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    shift = (step - 1) * 6
    pts = [
        (108 + shift, 64),
        (52 + shift, 20),
        (66 + shift, 48),
        (20 + shift, 48),
        (20 + shift, 80),
        (66 + shift, 80),
        (52 + shift, 108),
    ]
    d.polygon(pts, fill=(245, 192, 58, 255), outline=(12, 14, 22, 255))
    d.line([(30 + shift, 64), (96 + shift, 64)], fill=(120, 245, 255, 255), width=6)
    return img.resize((32, 32), Image.Resampling.LANCZOS)


def build_custom_cursor_atlas_img() -> Image.Image:
    """
    Build the complete `256x128` (`8x4` cells of `32x32`) Sovereign Astral Gauntlet
    cursor texture matching Blizzard's `HumanCursor.mdx` / `OrcCursor.mdx` UV layout.
    """
    atlas = Image.new("RGBA", (256, 128), (0, 0, 0, 0))

    # Row 0 (cols 0..7): Friendly / Button Select animated shimmer (Gold + Emerald-Cyan)
    for col in range(8):
        pulse = 0.5 + 0.5 * math.sin(col * math.pi / 4.0)
        cell = _draw_sovereign_gauntlet_cell((235, 190, 68), (64, 245, 200), pulse=pulse)
        atlas.paste(cell, (col * 32, 0))

    # Row 1 (cols 0..7): Enemy Hover animated blaze (Crimson-Gold + Flame)
    for col in range(8):
        pulse = 0.5 + 0.5 * math.sin(col * math.pi / 4.0)
        cell = _draw_sovereign_gauntlet_cell((235, 110, 52), (255, 68, 82), pulse=pulse)
        atlas.paste(cell, (col * 32, 32))

    # Row 2 (cols 0..7): TargetSelect rotating runic crosshair reticle
    for col in range(8):
        cell = _draw_reticle_cell((255, 185, 48), (95, 245, 255), angle_deg=col * 22.5)
        atlas.paste(cell, (col * 32, 64))

    # Row 3:
    #   Col 0: Normal default Sovereign Gauntlet-Blade (Obsidian-Gold + Astral Cyan)
    atlas.paste(_draw_sovereign_gauntlet_cell((238, 188, 62), (72, 220, 255), pulse=0.45), (0, 96))
    #   Col 1: Target static crosshair reticle
    atlas.paste(_draw_reticle_cell((255, 85, 65), (255, 220, 95), angle_deg=0.0), (32, 96))
    #   Col 2: InvalidTarget red seal reticle
    atlas.paste(_draw_reticle_cell((190, 35, 35), (255, 80, 80), invalid=True), (64, 96))
    #   Col 3 & 4: HoldItem clawed golden grip
    atlas.paste(_draw_sovereign_gauntlet_cell((238, 188, 62), (175, 110, 255), pulse=0.35, grip=True), (96, 96))
    atlas.paste(_draw_sovereign_gauntlet_cell((248, 208, 88), (205, 145, 255), pulse=0.85, grip=True), (128, 96))
    #   Col 5, 6, 7: 8-way edge-scroll animated chevron
    for s in range(3):
        atlas.paste(_draw_scroll_chevron_cell(s), ((5 + s) * 32, 96))

    return atlas


# ==============================================================================
# 4. BADASS RPG INFOCARD ICONS (DAMAGE TYPES, ARMOR TYPES & HERO ATTRIBUTES)
# ==============================================================================

def _draw_infocard_badge_frame(
    emblem_fn,
    glow_rgb: Tuple[int, int, int],
    rim_rgb: Tuple[int, int, int],
    with_upgrade_slot: bool = False,
) -> Image.Image:
    """
    Render a `64x64` dark-fantasy RPG Infocard emblem (supersampled at `128x128`)
    with sculpted octagonal obsidian-gold framing, radial aura, crisp weapon/shield
    art, and optional bottom-right upgrade counter plaque (matching WC3's `+1/+2/+3`
    upgrade text overlay on upgraded units).
    """
    S = 128
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Ornate octagonal dark-obsidian RPG plaque (transparent outside corners!)
    oct_outer = [(24, 4), (104, 4), (124, 24), (124, 104), (104, 124), (24, 124), (4, 104), (4, 24)]
    oct_mid   = [(27, 8), (101, 8), (120, 27), (120, 101), (101, 120), (27, 120), (8, 101), (8, 27)]
    oct_inner = [(31, 13), (97, 13), (115, 31), (115, 97), (97, 115), (31, 115), (13, 97), (13, 31)]

    d.polygon(oct_outer, fill=(10, 12, 20, 255), outline=(4, 6, 10, 255))
    d.polygon(oct_mid, fill=(*rim_rgb, 255))
    d.polygon(oct_inner, fill=(14, 18, 30, 255))

    # Soft elemental glow behind the emblem
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([22, 22, 106, 106], fill=(*glow_rgb, 145))
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)

    # Corner rivets
    for rx, ry in ((28, 14), (100, 14), (14, 28), (114, 28), (28, 114), (100, 114)):
        d.ellipse([rx - 3, ry - 3, rx + 3, ry + 3], fill=(255, 240, 195, 255))

    # Draw the specific weapon / shield / stat emblem
    emblem_fn(d, S)

    # Optional bottom-right metallic plaque for +1/+2/+3 upgrade counter
    if with_upgrade_slot:
        d.rounded_rectangle([78, 82, 122, 122], radius=8, fill=(12, 14, 22, 248), outline=(238, 190, 68, 255), width=3)

    return img.resize((64, 64), Image.Resampling.LANCZOS)


def build_infocard_icons() -> Tuple[Dict[str, bytes], List[Image.Image]]:
    """Generate all custom Damage Type, Armor Type, and Hero Attribute `.blp` icons."""
    out: Dict[str, bytes] = {}
    samples: List[Image.Image] = []

    # ---- 6 Damage Type Emblem Painters ----
    def dmg_normal(d: ImageDraw.ImageDraw, S: int) -> None:
        # Crossed Silver-Gold Runeblades + Steel Impact Star
        for sgn in (-1, 1):
            x0, y0 = (64 - 36 * sgn, 98)
            x1, y1 = (64 + 36 * sgn, 24)
            d.line([(x0, y0), (x1, y1)], fill=(14, 18, 26, 255), width=18)
            d.line([(x0, y0), (x1, y1)], fill=(225, 238, 255, 255), width=10)
            d.line([(x0, y0), (x1, y1)], fill=(255, 255, 255, 255), width=4)
            # Crossguard
            gx, gy = (64 - 16 * sgn, 78)
            d.line([(gx - 14, gy - 10 * sgn), (gx + 14, gy + 10 * sgn)], fill=(245, 195, 65, 255), width=7)
        d.polygon([(64, 42), (70, 56), (84, 62), (70, 68), (64, 82), (58, 68), (44, 62), (58, 56)], fill=(255, 235, 130, 255))

    def dmg_pierce(d: ImageDraw.ImageDraw, S: int) -> None:
        # Twin Emerald-Cyan Astral Wind-Arrows piercing a target ring
        d.ellipse([30, 30, 98, 98], outline=(95, 255, 190, 210), width=4)
        for off in (-12, 12):
            d.line([(22, 96 + off // 2), (96, 26 + off // 2)], fill=(12, 20, 18, 255), width=12)
            d.line([(22, 96 + off // 2), (96, 26 + off // 2)], fill=(110, 255, 205, 255), width=6)
            tx, ty = 102, 22 + off // 2
            d.polygon([(tx, ty), (tx - 24, ty + 6), (tx - 6, ty + 24)], fill=(235, 255, 245, 255), outline=(20, 40, 32, 255))

    def dmg_siege(d: ImageDraw.ImageDraw, S: int) -> None:
        # Blazing Magma Meteor-Bombard shattering fortifications
        for ang in range(0, 360, 45):
            rad = math.radians(ang)
            d.line([(64, 64), (64 + math.cos(rad) * 46, 64 + math.sin(rad) * 46)], fill=(255, 135, 32, 235), width=6)
        d.polygon([(20, 24), (72, 42), (42, 72)], fill=(255, 185, 55, 255))
        d.ellipse([34, 34, 98, 98], fill=(42, 24, 20, 255), outline=(255, 125, 28, 255), width=6)
        #Glowing magma cracks across meteor core
        d.line([(44, 56), (66, 68), (88, 52)], fill=(255, 235, 110, 255), width=5)
        d.line([(56, 86), (66, 68), (76, 90)], fill=(255, 165, 42, 255), width=5)

    def dmg_magic(d: ImageDraw.ImageDraw, S: int) -> None:
        # Radiant Sapphire-Cyan Arcane Starburst Scepter & Rune Circle
        d.ellipse([24, 24, 104, 104], outline=(85, 210, 255, 235), width=4)
        pts = []
        for i in range(16):
            r = 44 if i % 2 == 0 else 18
            a = math.radians(i * 22.5 - 90)
            pts.append((64 + math.cos(a) * r, 64 + math.sin(a) * r))
        d.polygon(pts, fill=(75, 195, 255, 255), outline=(225, 250, 255, 255))
        d.ellipse([48, 48, 80, 80], fill=(245, 252, 255, 255), outline=(38, 120, 255, 255), width=4)

    def dmg_chaos(d: ImageDraw.ImageDraw, S: int) -> None:
        # Abyssal Fel-Amethyst Vortex Scythe + Burning Eye of Oblivion
        for i in range(6):
            a0 = i * 60
            d.arc([20, 20, 108, 108], start=a0, end=a0 + 42, fill=(215, 85, 255, 255), width=7)
        d.polygon([(24, 64), (64, 34), (104, 64), (64, 94)], fill=(65, 14, 95, 255), outline=(240, 145, 255, 255))
        d.ellipse([48, 48, 80, 80], fill=(255, 72, 165, 255), outline=(255, 235, 255, 255), width=3)
        d.polygon([(62, 50), (68, 64), (62, 78), (58, 64)], fill=(255, 255, 255, 255))

    def dmg_hero(d: ImageDraw.ImageDraw, S: int) -> None:
        # Sovereign Golden Crown-Blade w/ Twin Wings & Sunburst Halo
        d.ellipse([24, 24, 104, 104], outline=(255, 215, 85, 225), width=4)
        # Wings
        d.polygon([(18, 56), (48, 46), (44, 76), (22, 82)], fill=(255, 198, 62, 255), outline=(255, 248, 205, 255))
        d.polygon([(110, 56), (80, 46), (84, 76), (106, 82)], fill=(255, 198, 62, 255), outline=(255, 248, 205, 255))
        # Sovereign Crown + Vertical Greatsword
        d.polygon([(36, 44), (48, 24), (64, 38), (80, 24), (92, 44), (86, 58), (42, 58)], fill=(255, 215, 72, 255), outline=(255, 252, 220, 255))
        d.polygon([(58, 20), (70, 20), (68, 106), (64, 114), (60, 106)], fill=(245, 250, 255, 255), outline=(185, 130, 28, 255))

    dmg_specs = [
        ("DmgNormal", dmg_normal, (145, 185, 235), (175, 192, 215)),
        ("DmgPierce", dmg_pierce, (52, 225, 155),  (88, 215, 165)),
        ("DmgSiege",  dmg_siege,  (245, 110, 28),  (225, 135, 58)),
        ("DmgMagic",  dmg_magic,  (55, 175, 255),  (95, 195, 255)),
        ("DmgChaos",  dmg_chaos,  (188, 58, 250),  (198, 105, 255)),
        ("DmgHero",   dmg_hero,   (250, 195, 48),  (245, 205, 82)),
    ]
    for name, fn, glow_c, rim_c in dmg_specs:
        upg_im = _draw_infocard_badge_frame(fn, glow_c, rim_c, with_upgrade_slot=True)
        neu_im = _draw_infocard_badge_frame(fn, glow_c, rim_c, with_upgrade_slot=False)
        samples.append(neu_im)
        out[f"UI\\CrownUI\\Infocard\\{name}.blp"] = encode_blp1_paletted(upg_im, alpha_bits=8)
        out[f"UI\\CrownUI\\Infocard\\{name}Neutral.blp"] = encode_blp1_paletted(neu_im, alpha_bits=8)

    # ---- 7 Armor Type Emblem Painters ----
    def _shield_poly(d: ImageDraw.ImageDraw, fill_c, rim_c) -> None:
        pts = [(30, 24), (98, 24), (102, 66), (64, 108), (26, 66)]
        d.polygon(pts, fill=(*fill_c, 255), outline=(12, 16, 24, 255))
        pts_in = [(35, 30), (93, 30), (96, 64), (64, 100), (32, 64)]
        d.polygon(pts_in, outline=(*rim_c, 255), width=5)

    def arm_small(d: ImageDraw.ImageDraw, S: int) -> None:
        _shield_poly(d, (28, 95, 68), (110, 245, 175))
        d.polygon([(64, 36), (82, 62), (64, 88), (46, 62)], fill=(155, 255, 205, 255))

    def arm_medium(d: ImageDraw.ImageDraw, S: int) -> None:
        _shield_poly(d, (38, 78, 128), (145, 205, 255))
        for ry in (44, 60, 76):
            d.line([(40, ry), (88, ry)], fill=(215, 238, 255, 255), width=5)

    def arm_large(d: ImageDraw.ImageDraw, S: int) -> None:
        _shield_poly(d, (118, 36, 42), (245, 185, 78))
        d.line([(64, 30), (64, 98)], fill=(255, 225, 125, 255), width=7)
        d.line([(34, 58), (94, 58)], fill=(255, 225, 125, 255), width=7)

    def arm_fort(d: ImageDraw.ImageDraw, S: int) -> None:
        # Battlement Citadel Bastion Wall + Turret
        d.polygon([(24, 38), (40, 38), (40, 26), (56, 26), (56, 38), (72, 38), (72, 26), (88, 26), (88, 38), (104, 38), (98, 102), (30, 102)],
                  fill=(88, 96, 114, 255), outline=(238, 192, 72, 255))
        d.rounded_rectangle([50, 64, 78, 102], radius=10, fill=(24, 28, 38, 255), outline=(255, 215, 95, 255), width=4)

    def arm_hero(d: ImageDraw.ImageDraw, S: int) -> None:
        _shield_poly(d, (145, 95, 18), (255, 232, 115))
        d.polygon([(42, 58), (50, 38), (64, 50), (78, 38), (86, 58), (82, 72), (46, 72)], fill=(255, 245, 175, 255), outline=(90, 52, 10, 255))

    def arm_divine(d: ImageDraw.ImageDraw, S: int) -> None:
        _shield_poly(d, (115, 125, 165), (255, 250, 210))
        d.ellipse([42, 40, 86, 84], fill=(255, 250, 205, 255), outline=(255, 205, 75, 255), width=5)

    def arm_none(d: ImageDraw.ImageDraw, S: int) -> None:
        # Mystic Astral Cloak Hood
        d.polygon([(64, 22), (98, 52), (88, 102), (40, 102), (30, 52)], fill=(78, 48, 125, 255), outline=(205, 165, 255, 255))
        d.polygon([(64, 38), (80, 58), (74, 92), (54, 92), (48, 58)], fill=(22, 16, 38, 255))

    arm_specs = [
        ("ArmSmall",  arm_small,  (48, 215, 145),  (82, 210, 155)),
        ("ArmMedium", arm_medium, (65, 155, 235),  (115, 178, 235)),
        ("ArmLarge",  arm_large,  (225, 78, 68),   (235, 168, 72)),
        ("ArmFort",   arm_fort,   (215, 168, 58),  (195, 182, 145)),
        ("ArmHero",   arm_hero,   (255, 200, 52),  (250, 212, 88)),
        ("ArmDivine", arm_divine, (255, 242, 165), (255, 235, 155)),
        ("ArmNone",   arm_none,   (165, 98, 245),  (182, 132, 245)),
    ]
    for name, fn, glow_c, rim_c in arm_specs:
        upg_im = _draw_infocard_badge_frame(fn, glow_c, rim_c, with_upgrade_slot=True)
        neu_im = _draw_infocard_badge_frame(fn, glow_c, rim_c, with_upgrade_slot=False)
        samples.append(neu_im)
        out[f"UI\\CrownUI\\Infocard\\{name}.blp"] = encode_blp1_paletted(upg_im, alpha_bits=8)
        out[f"UI\\CrownUI\\Infocard\\{name}Neutral.blp"] = encode_blp1_paletted(neu_im, alpha_bits=8)

    # ---- 3 Hero Primary Attribute Icons (`STR`, `AGI`, `INT`) ----
    def attr_str(d: ImageDraw.ImageDraw, S: int) -> None:
        d.rounded_rectangle([32, 34, 96, 96], radius=14, fill=(185, 32, 38, 255), outline=(255, 205, 95, 255), width=5)
        for fx in (38, 54, 70):
            d.rounded_rectangle([fx, 24, fx + 14, 54], radius=5, fill=(245, 78, 68, 255), outline=(255, 235, 165, 255), width=3)
        d.polygon([(64, 56), (76, 72), (64, 88), (52, 72)], fill=(255, 242, 175, 255))

    def attr_agi(d: ImageDraw.ImageDraw, S: int) -> None:
        for sgn in (-1, 1):
            d.polygon([(64 + 8 * sgn, 22), (64 + 40 * sgn, 54), (64 + 12 * sgn, 104), (64 - 4 * sgn, 68)],
                      fill=(45, 225, 125, 255), outline=(225, 255, 235, 255))

    def attr_int(d: ImageDraw.ImageDraw, S: int) -> None:
        d.ellipse([26, 26, 102, 102], outline=(115, 225, 255, 255), width=4)
        d.polygon([(64, 20), (96, 64), (64, 108), (32, 64)], fill=(48, 155, 255, 255), outline=(235, 250, 255, 255))
        d.ellipse([50, 50, 78, 78], fill=(245, 252, 255, 255))

    for code, fn, glow_c, rim_c in [
        ("AttrSTR", attr_str, (245, 62, 58),  (245, 155, 72)),
        ("AttrAGI", attr_agi, (48, 235, 132), (98, 238, 162)),
        ("AttrINT", attr_int, (55, 175, 255), (118, 208, 255)),
    ]:
        at_im = _draw_infocard_badge_frame(fn, glow_c, rim_c, with_upgrade_slot=False)
        samples.append(at_im)
        out[f"UI\\CrownUI\\Infocard\\{code}.blp"] = encode_blp1_paletted(at_im, alpha_bits=8)

    return out, samples


# ==============================================================================
# 5. COMMAND CARD ACTIONS, RACIAL BUILD BUTTONS, RACIAL BUILDINGS & 64 SKILLS
# ==============================================================================

def _paint_emblem_icon(
    bg_inner: Tuple[int, int, int],
    bg_mid: Tuple[int, int, int],
    bg_outer: Tuple[int, int, int],
    accent: Tuple[int, int, int],
    highlight: Tuple[int, int, int],
    motif: str,
    seed: int = 0,
) -> Tuple[Image.Image, Tuple[int, int, int]]:
    """
    High-detail `128x128` supersampled procedural painter producing distinct,
    crisp fantasy icons across 16 geometric motifs + rune rings + faction palettes.
    """
    S = 128
    img = _radial_canvas(S, bg_inner, bg_mid, bg_outer)
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    d = ImageDraw.Draw(img)
    cx = cy = 64.0

    # Subtle arcane background ring
    ring_r = 44 + (seed % 3) * 3
    gd.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], outline=(*accent, 150), width=4)

    if motif == "vortex":
        for arm in range(3 + (seed % 3)):
            base_a = arm * (360.0 / (3 + (seed % 3))) + seed * 17
            pts = []
            for st in range(16):
                t = st / 15.0
                r = 8 + t * 44
                a = math.radians(base_a + t * 145)
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
            gd.line(pts, fill=(*accent, 235), width=9)
            d.line(pts, fill=(*highlight, 255), width=4)
        d.ellipse([50, 50, 78, 78], fill=(*highlight, 255), outline=(*accent, 255), width=4)

    elif motif == "glaives":
        # Twin curved Azzinoth / Crescent blades
        for sgn in (-1, 1):
            gd.arc([18, 18, 110, 110], start=200 if sgn < 0 else 20, end=340 if sgn < 0 else 160, fill=(*accent, 255), width=14)
            d.arc([22, 22, 106, 106], start=205 if sgn < 0 else 25, end=335 if sgn < 0 else 155, fill=(*highlight, 255), width=6)
        d.polygon([(64, 28), (78, 64), (64, 100), (50, 64)], fill=(*highlight, 255), outline=(*accent, 255))

    elif motif == "lightning":
        pts = [(74, 12), (40, 62), (66, 62), (46, 116), (92, 56), (66, 56)]
        gd.polygon(pts, fill=(*accent, 240))
        d.polygon(pts, fill=(*highlight, 255), outline=(*accent, 255))
        for b in range(3):
            ay = 34 + b * 28
            d.line([(64, ay), (24 if b % 2 == 0 else 104, ay + 16)], fill=(*highlight, 230), width=4)

    elif motif == "spear":
        ang = math.radians(-45 + (seed % 3 - 1) * 12)
        dx, dy = math.cos(ang), math.sin(ang)
        px_a, py_a = -dy, dx
        tip = (cx + dx * 48, cy + dy * 48)
        tail = (cx - dx * 46, cy - dy * 46)
        d.line([tail, tip], fill=(*accent, 255), width=10)
        d.line([tail, tip], fill=(*highlight, 255), width=4)
        head = [
            tip,
            (cx + dx * 14 + px_a * 18, cy + dy * 14 + py_a * 18),
            (cx + dx * 24, cy + dy * 24),
            (cx + dx * 14 - px_a * 18, cy + dy * 14 - py_a * 18),
        ]
        gd.polygon(head, fill=(*accent, 255))
        d.polygon(head, fill=(*highlight, 255), outline=(*accent, 255))

    elif motif == "shield":
        pts = [(28, 22), (100, 22), (104, 68), (64, 110), (24, 68)]
        gd.polygon(pts, fill=(*accent, 220))
        d.polygon(pts, fill=(*bg_mid, 255), outline=(*highlight, 255))
        d.polygon([(38, 32), (90, 32), (92, 66), (64, 98), (36, 66)], fill=(*accent, 235), outline=(*highlight, 255))
        d.ellipse([50, 48, 78, 76], fill=(*highlight, 255))

    elif motif == "nova":
        spikes = 8 + (seed % 4) * 2
        pts = []
        for i in range(spikes * 2):
            r = 50 if i % 2 == 0 else 20
            a = math.radians(i * (180.0 / spikes) + seed * 11)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        gd.polygon(pts, fill=(*accent, 240))
        d.polygon(pts, fill=(*highlight, 255), outline=(*accent, 255))
        d.ellipse([48, 48, 80, 80], fill=(255, 255, 255, 255), outline=(*accent, 255), width=4)

    elif motif == "hammer":
        d.line([(28, 102), (82, 48)], fill=(195, 160, 95, 255), width=11)
        head = [(56, 22), (108, 48), (92, 78), (40, 52)]
        gd.polygon(head, fill=(*accent, 240))
        d.polygon(head, fill=(*highlight, 255), outline=(*accent, 255))

    elif motif == "bow":
        d.arc([20, 16, 98, 112], start=295, end=65, fill=(*highlight, 255), width=8)
        d.line([(56, 20), (56, 108)], fill=(*accent, 220), width=3)
        for oy in (-14, 0, 14):
            d.line([(24, 64 + oy), (108, 64 + oy // 2)], fill=(*highlight, 255), width=5)

    elif motif == "skull_eye":
        d.polygon([(20, 64), (64, 28), (108, 64), (64, 100)], fill=(18, 12, 28, 255), outline=(*highlight, 255))
        gd.ellipse([42, 42, 86, 86], fill=(*accent, 255))
        d.ellipse([46, 46, 82, 82], fill=(*accent, 255), outline=(*highlight, 255), width=4)
        d.polygon([(62, 48), (68, 64), (62, 80), (58, 64)], fill=(255, 255, 255, 255))

    elif motif == "crown":
        pts = [(20, 86), (26, 38), (46, 58), (64, 24), (82, 58), (102, 38), (108, 86)]
        gd.polygon(pts, fill=(*accent, 240))
        d.polygon(pts, fill=(*highlight, 255), outline=(*accent, 255))
        d.rectangle([24, 86, 104, 98], fill=(*accent, 255), outline=(*highlight, 255), width=3)

    elif motif == "turret_gear":
        # Interlocking Runeforged Gear + Core
        for i in range(8):
            a = math.radians(i * 45 + seed * 7)
            gx, gy = cx + math.cos(a) * 40, cy + math.sin(a) * 40
            d.ellipse([gx - 10, gy - 10, gx + 10, gy + 10], fill=(*highlight, 255), outline=(*accent, 255), width=3)
        d.ellipse([30, 30, 98, 98], fill=(*bg_mid, 255), outline=(*highlight, 255), width=7)
        d.ellipse([46, 46, 82, 82], fill=(*accent, 255), outline=(255, 255, 255, 255), width=4)

    elif motif == "spire":
        # Architectural Citadel / Temple / Obelisk
        tier = (seed % 3) + 1
        d.polygon([(64, 14), (96, 54), (88, 108), (40, 108), (32, 54)], fill=(*accent, 240), outline=(*highlight, 255))
        if tier >= 2:
            d.polygon([(22, 44), (38, 62), (34, 108), (16, 108)], fill=(*highlight, 225), outline=(*accent, 255))
            d.polygon([(106, 44), (90, 62), (94, 108), (112, 108)], fill=(*highlight, 225), outline=(*accent, 255))
        if tier >= 3:
            d.ellipse([48, 16, 80, 48], fill=(255, 255, 255, 245), outline=(*highlight, 255), width=4)
        d.rounded_rectangle([52, 74, 76, 108], radius=8, fill=(255, 252, 220, 255))

    elif motif == "portal":
        gd.ellipse([20, 16, 108, 112], outline=(*accent, 255), width=16)
        d.ellipse([24, 20, 104, 108], outline=(*highlight, 255), width=6)
        d.ellipse([38, 34, 90, 94], fill=(10, 8, 22, 255), outline=(*accent, 255), width=5)
        d.polygon([(64, 42), (76, 64), (64, 86), (52, 64)], fill=(*highlight, 255))

    elif motif == "wings":
        d.polygon([(14, 32), (56, 52), (48, 96), (18, 76)], fill=(*highlight, 255), outline=(*accent, 255))
        d.polygon([(114, 32), (72, 52), (80, 96), (110, 76)], fill=(*highlight, 255), outline=(*accent, 255))
        d.polygon([(64, 20), (76, 64), (64, 108), (52, 64)], fill=(255, 255, 255, 255), outline=(*accent, 255))

    elif motif == "claws":
        for k in (-24, 0, 24):
            pts = [(24 + k // 2, 22), (68 + k, 62), (98 + k // 2, 106), (56 + k, 68)]
            gd.polygon(pts, fill=(*accent, 240))
            d.polygon(pts, fill=(*highlight, 255), outline=(*accent, 255))

    else:  # "chalice_tome"
        d.rounded_rectangle([28, 24, 100, 104], radius=10, fill=(*bg_mid, 255), outline=(*highlight, 255), width=5)
        d.line([(64, 24), (64, 104)], fill=(*accent, 255), width=5)
        d.ellipse([44, 44, 84, 84], fill=(*highlight, 255), outline=(*accent, 255), width=4)

    glow = glow.filter(ImageFilter.GaussianBlur(6))
    merged = Image.alpha_composite(img, glow)

    # Seed-driven secondary ornate details + metallic diagonal sheen so every
    # single skill icon out of all 64 has a unique silhouette & inner filigree!
    md = ImageDraw.Draw(merged)
    orb_cnt = 2 + (seed % 4)
    for k in range(orb_cnt):
        oa = math.radians(seed * 37 + k * (360.0 / orb_cnt))
        ox = cx + math.cos(oa) * 48
        oy = cy + math.sin(oa) * 48
        md.polygon(
            [(ox, oy - 5), (ox + 5, oy), (ox, oy + 5), (ox - 5, oy)],
            fill=(*highlight, 235),
            outline=(*accent, 255),
        )
    if seed % 3 == 1:
        md.arc([12, 12, 116, 116], start=seed * 23, end=seed * 23 + 110, fill=(*highlight, 185), width=3)
    elif seed % 3 == 2:
        md.arc([14, 14, 114, 114], start=180 + seed * 19, end=310 + seed * 19, fill=(*accent, 210), width=4)

    return merged.resize((64, 64), Image.Resampling.LANCZOS), accent


# 16 Hero-Specific Sub-Palettes so EVERY Hero has its own unmistakable visual signature!
PAL_VASHJ    = ((18, 95, 138),  (10, 46, 82),  (6, 18, 38),  (32, 218, 250),  (210, 255, 255))
PAL_ILLIDAN  = ((28, 115, 62),  (24, 42, 56),  (10, 14, 26), (78, 255, 128),  (230, 255, 190))
PAL_NAJENTUS = ((110, 38, 52),  (18, 52, 74),  (8, 20, 34),  (255, 108, 92),  (190, 250, 255))
PAL_ATHISSA  = ((68, 42, 132),  (16, 58, 92),  (8, 20, 42),  (145, 225, 255), (245, 215, 255))

PAL_KAEL     = ((158, 58, 18),  (84, 22, 16),  (34, 10, 12), (255, 165, 36),  (255, 248, 190))
PAL_SYLVANAS = ((34, 72, 124),  (22, 36, 74),  (10, 16, 34), (125, 232, 255), (235, 255, 245))
PAL_GARITHOS = ((118, 52, 36),  (54, 34, 32),  (22, 14, 16), (235, 178, 88),  (245, 242, 235))
PAL_UTHER    = ((148, 112, 26), (76, 54, 18),  (28, 20, 12), (255, 222, 78),  (255, 255, 230))

PAL_XALATHOR = ((108, 24, 98),  (48, 14, 62),  (18, 6, 28),  (235, 68, 168),  (255, 210, 245))
PAL_SARGEN   = ((78, 28, 148),  (36, 14, 84),  (14, 8, 36),  (178, 92, 255),  (235, 220, 255))
PAL_AKAMA    = ((36, 86, 74),   (28, 22, 56),  (10, 10, 24), (118, 245, 185), (238, 210, 255))
PAL_AETHERON = ((42, 64, 148),  (26, 24, 82),  (10, 10, 36), (110, 195, 255), (245, 225, 255))

PAL_THORIM   = ((28, 92, 148),  (20, 46, 84),  (10, 20, 38), (82, 220, 255),  (245, 250, 255))
PAL_IGNIS    = ((148, 64, 18),  (68, 30, 16),  (26, 14, 12), (255, 138, 36),  (255, 238, 175))
PAL_MIMIRON  = ((118, 92, 24),  (48, 46, 26),  (18, 20, 16), (155, 248, 95),  (255, 242, 170))
PAL_LOKEN    = ((22, 108, 118), (16, 52, 68),  (8, 22, 32),  (64, 248, 222),  (255, 232, 150))

PAL_ABYSSAL = PAL_VASHJ
PAL_FELNAGA = PAL_ILLIDAN
PAL_SUNFURY = PAL_KAEL
PAL_HOLYSUN = PAL_UTHER
PAL_VOID    = PAL_SARGEN
PAL_SHADOW  = PAL_XALATHOR
PAL_RUNIC   = PAL_THORIM
PAL_FORGE   = PAL_IGNIS


# 64 Unique Hero Skill Icon Specs (`BTN_WM_S00` .. `BTN_WM_S63`) — 16 Heroes x 4 Distinct Motifs & Palettes!
SKILL_64_MOTIFS: List[Tuple[Tuple, str]] = [
    # 0..3: Hvsh (Empress Lady Vashj)
    (PAL_VASHJ,    "vortex"), (PAL_VASHJ,    "lightning"), (PAL_VASHJ,    "shield"),       (PAL_VASHJ,    "nova"),
    # 4..7: N004 (Illidan Stormrage — Fel-Tidal Twin Glaives & Metamorphosis!)
    (PAL_ILLIDAN,  "glaives"),(PAL_ILLIDAN,  "claws"),     (PAL_ILLIDAN,  "skull_eye"),    (PAL_ILLIDAN,  "wings"),
    # 8..11: N001 (Leviathan Warlord Naj'entus)
    (PAL_NAJENTUS, "spear"),  (PAL_NAJENTUS, "hammer"),    (PAL_NAJENTUS, "shield"),       (PAL_NAJENTUS, "crown"),
    # 12..15: N002 (Nazjatar Tideweaver Athissa)
    (PAL_ATHISSA,  "nova"),   (PAL_ATHISSA,  "portal"),    (PAL_ATHISSA,  "chalice_tome"), (PAL_ATHISSA,  "vortex"),

    # 16..19: Hkal (Sovereign Kael'thas)
    (PAL_KAEL,     "nova"),   (PAL_KAEL,     "vortex"),    (PAL_KAEL,     "shield"),       (PAL_KAEL,     "wings"),
    # 20..23: Hvwd (Ranger-General Sylvanas)
    (PAL_SYLVANAS, "bow"),    (PAL_SYLVANAS, "spear"),     (PAL_SYLVANAS, "wings"),        (PAL_SYLVANAS, "nova"),
    # 24..27: Hlgr (Grand Marshal Garithos)
    (PAL_GARITHOS, "hammer"), (PAL_GARITHOS, "glaives"),   (PAL_GARITHOS, "shield"),       (PAL_GARITHOS, "crown"),
    # 28..31: Huth (Highlord Uther)
    (PAL_UTHER,    "spire"),  (PAL_UTHER,    "hammer"),    (PAL_UTHER,    "chalice_tome"), (PAL_UTHER,    "crown"),

    # 32..35: V001 (Rift Sovereign Xal'athor)
    (PAL_XALATHOR, "vortex"), (PAL_XALATHOR, "spear"),     (PAL_XALATHOR, "skull_eye"),    (PAL_XALATHOR, "portal"),
    # 36..39: V002 (Nether Inquisitor Sargen'eth)
    (PAL_SARGEN,   "lightning"),(PAL_SARGEN, "skull_eye"), (PAL_SARGEN,   "chalice_tome"), (PAL_SARGEN,   "nova"),
    # 40..43: V003 (Shadowblade Akama)
    (PAL_AKAMA,    "glaives"),(PAL_AKAMA,    "claws"),     (PAL_AKAMA,    "portal"),       (PAL_AKAMA,    "wings"),
    # 44..47: V004 (Entropy Archon Aetheron)
    (PAL_AETHERON, "nova"),   (PAL_AETHERON, "portal"),    (PAL_AETHERON, "shield"),       (PAL_AETHERON, "crown"),

    # 48..51: T001 (Stormforged Prime Thorim)
    (PAL_THORIM,   "hammer"), (PAL_THORIM,   "lightning"), (PAL_THORIM,   "shield"),       (PAL_THORIM,   "crown"),
    # 52..55: T002 (Runesmith Highlord Ignis)
    (PAL_IGNIS,    "nova"),   (PAL_IGNIS,    "hammer"),    (PAL_IGNIS,    "spire"),        (PAL_IGNIS,    "turret_gear"),
    # 56..59: T003 (Clockwork Vanguard Mimiron)
    (PAL_MIMIRON,  "bow"),    (PAL_MIMIRON,  "spear"),     (PAL_MIMIRON,  "turret_gear"),  (PAL_MIMIRON,  "nova"),
    # 60..63: T004 (Tempest Savant Loken)
    (PAL_LOKEN,    "vortex"), (PAL_LOKEN,    "lightning"), (PAL_LOKEN,    "chalice_tome"), (PAL_LOKEN,    "turret_gear"),
]


# Custom Command Card, Racial Build & Racial Building/Unit/Hero Icons
EXTRA_CUSTOM_ICONS: List[Tuple[str, Tuple, str, int]] = [
    # Map Crest & Empire Tome
    ("BTN_WM_CrownCrest",      PAL_HOLYSUN, "crown",        1),
    ("BTN_WM_FactionTome",     PAL_VOID,    "chalice_tome", 2),

    # 8 Custom Command Card Action Buttons
    ("BTN_WM_CmdAttack",       PAL_SUNFURY, "glaives",      3),
    ("BTN_WM_CmdMove",         PAL_ABYSSAL, "wings",        4),
    ("BTN_WM_CmdStop",         PAL_SUNFURY, "shield",       5),
    ("BTN_WM_CmdHold",         PAL_HOLYSUN, "shield",       6),
    ("BTN_WM_CmdPatrol",       PAL_RUNIC,   "spear",        7),
    ("BTN_WM_CmdSkill",        PAL_HOLYSUN, "crown",        8),
    ("BTN_WM_CmdRally",        PAL_HOLYSUN, "spire",        9),
    ("BTN_WM_CmdCancel",       PAL_SHADOW,  "nova",         10),

    # 5 Race-Specific Worker `Build` Icons!
    ("BTN_WM_BuildNaga",       PAL_ABYSSAL, "vortex",       11),
    ("BTN_WM_BuildSunfury",    PAL_HOLYSUN, "spire",        12),
    ("BTN_WM_BuildVoidborn",   PAL_VOID,    "portal",       13),
    ("BTN_WM_BuildRuneforged", PAL_RUNIC,   "turret_gear",  14),
    ("BTN_WM_BuildNightElf",   PAL_FELNAGA, "wings",        15),

    # Naga Custom Hero Illidan + Naga Custom Structures
    ("BTN_WM_HeroIllidan",     PAL_FELNAGA, "glaives",      20),
    ("BTN_WM_NagaHall2",       PAL_ABYSSAL, "spire",        2),
    ("BTN_WM_NagaHall3",       PAL_ABYSSAL, "spire",        3),
    ("BTN_WM_NagaForge",       PAL_ABYSSAL, "hammer",       21),
    ("BTN_WM_NagaVault",       PAL_ABYSSAL, "chalice_tome", 22),
    ("BTN_WM_NagaPool",        PAL_ABYSSAL, "portal",       23),

    # Sunfury Imperium Custom Structures & Siege
    ("BTN_WM_SunHall1",        PAL_HOLYSUN, "spire",        1),
    ("BTN_WM_SunHall2",        PAL_HOLYSUN, "spire",        2),
    ("BTN_WM_SunHall3",        PAL_HOLYSUN, "spire",        3),
    ("BTN_WM_SunBarracks",     PAL_SUNFURY, "shield",       24),
    ("BTN_WM_SunAltar",        PAL_HOLYSUN, "crown",        25),
    ("BTN_WM_SunVault",        PAL_SUNFURY, "chalice_tome", 26),
    ("BTN_WM_SunWorkshop",     PAL_SUNFURY, "turret_gear",  27),
    ("BTN_WM_SunAviary",       PAL_HOLYSUN, "wings",        28),
    ("BTN_WM_SunBallista",     PAL_SUNFURY, "bow",          29),

    # Voidborn Legion Custom Structures & Akama Hero
    ("BTN_WM_VoidHall1",       PAL_VOID,    "spire",        1),
    ("BTN_WM_VoidHall2",       PAL_VOID,    "spire",        2),
    ("BTN_WM_VoidHall3",       PAL_VOID,    "spire",        3),
    ("BTN_WM_VoidPylon",       PAL_VOID,    "nova",         30),
    ("BTN_WM_VoidGate",        PAL_VOID,    "portal",       31),
    ("BTN_WM_VoidCrucible",    PAL_SHADOW,  "vortex",       32),
    ("BTN_WM_VoidAltar",       PAL_VOID,    "crown",        33),
    ("BTN_WM_VoidVault",       PAL_VOID,    "chalice_tome", 34),
    ("BTN_WM_VoidTower",       PAL_SHADOW,  "skull_eye",    35),
    ("BTN_WM_VoidSanctum",     PAL_VOID,    "wings",        36),
    ("BTN_WM_VoidPit",         PAL_SHADOW,  "claws",        37),
    ("BTN_WM_HeroAkama",       PAL_SHADOW,  "glaives",      38),

    # Runeforged Bastion Custom Structures, Units & Heroes (ZERO Human icons!)
    ("BTN_WM_RuneWorker",      PAL_RUNIC,   "turret_gear",  40),
    ("BTN_WM_RuneHall1",       PAL_RUNIC,   "spire",        1),
    ("BTN_WM_RuneHall2",       PAL_RUNIC,   "spire",        2),
    ("BTN_WM_RuneHall3",       PAL_RUNIC,   "spire",        3),
    ("BTN_WM_RuneCore",        PAL_RUNIC,   "nova",         41),
    ("BTN_WM_RuneGarrison",    PAL_FORGE,   "turret_gear",  42),
    ("BTN_WM_RuneAnvil",       PAL_FORGE,   "hammer",       43),
    ("BTN_WM_RuneAltar",       PAL_RUNIC,   "crown",        44),
    ("BTN_WM_RuneVault",       PAL_RUNIC,   "chalice_tome", 45),
    ("BTN_WM_RuneTurret",      PAL_RUNIC,   "lightning",    46),
    ("BTN_WM_RuneConduit",     PAL_RUNIC,   "portal",       47),
    ("BTN_WM_RuneBay",         PAL_FORGE,   "shield",       48),
    ("BTN_WM_RuneRifle",       PAL_RUNIC,   "bow",          49),
    ("BTN_WM_RuneHero1",       PAL_RUNIC,   "hammer",       50),
    ("BTN_WM_RuneHero2",       PAL_FORGE,   "crown",        51),
    ("BTN_WM_RuneHero3",       PAL_FORGE,   "turret_gear",  52),
    ("BTN_WM_RuneHero4",       PAL_LOKEN,   "lightning",    53),

    # ---- Abyssal Tideborn: custom-worker, hall, building, unit & hero portraits ----
    ("BTN_WM_NagaWorker",       PAL_ABYSSAL, "claws",        60),
    ("BTN_WM_NagaHall1",        PAL_ABYSSAL, "spire",        61),
    ("BTN_WM_NagaFarm",         PAL_ABYSSAL, "chalice_tome", 113),
    ("BTN_WM_NagaBarracks",     PAL_NAJENTUS,"shield",      62),
    ("BTN_WM_NagaAltar",        PAL_ATHISSA, "crown",       63),
    ("BTN_WM_NagaTower",        PAL_NAJENTUS,"lightning",   64),
    ("BTN_WM_NagaSanctum",      PAL_ATHISSA, "portal",      65),
    ("BTN_WM_NagaSiege",        PAL_NAJENTUS,"hammer",      66),
    ("BTN_WM_NagaHeroVashj",    PAL_VASHJ,   "nova",        67),
    ("BTN_WM_NagaHeroNaj",      PAL_NAJENTUS,"spear",       68),
    ("BTN_WM_NagaHeroAthissa",  PAL_ATHISSA, "chalice_tome",69),
    ("BTN_WM_NagaReaver",       PAL_ABYSSAL, "claws",       70),
    ("BTN_WM_NagaSnap",         PAL_NAJENTUS,"spear",       71),
    ("BTN_WM_NagaMyrmidon",     PAL_NAJENTUS,"shield",      72),
    ("BTN_WM_NagaSiren",        PAL_ATHISSA, "vortex",      73),
    ("BTN_WM_NagaCouatl",       PAL_ATHISSA, "wings",       74),
    ("BTN_WM_NagaTurtle",       PAL_NAJENTUS,"turret_gear", 75),
    ("BTN_WM_NagaRoyalGuard",   PAL_NAJENTUS,"crown",       76),

    # ---- Sunfury Imperium: goldglass worker, buildings, army & four heroes ----
    ("BTN_WM_SunWorker",        PAL_KAEL,    "chalice_tome",77),
    ("BTN_WM_SunFarm",          PAL_UTHER,   "spire",       78),
    ("BTN_WM_SunForge",         PAL_KAEL,    "hammer",      79),
    ("BTN_WM_SunLumberMill",    PAL_SYLVANAS,"chalice_tome",114),
    ("BTN_WM_SunTower",         PAL_KAEL,    "turret_gear",115),
    ("BTN_WM_SunGuardTower",    PAL_GARITHOS,"shield",     116),
    ("BTN_WM_SunArcaneTower",   PAL_KAEL,    "lightning",  117),
    ("BTN_WM_SunMageTower",     PAL_SYLVANAS,"nova",        80),
    ("BTN_WM_SunHeroKael",      PAL_KAEL,    "nova",        81),
    ("BTN_WM_SunHeroSylvanas",  PAL_SYLVANAS,"bow",         82),
    ("BTN_WM_SunHeroGarithos",  PAL_GARITHOS,"hammer",      83),
    ("BTN_WM_SunHeroUther",     PAL_UTHER,   "crown",       84),
    ("BTN_WM_SunSwordsman",     PAL_GARITHOS,"glaives",     85),
    ("BTN_WM_SunArcher",        PAL_SYLVANAS,"bow",         86),
    ("BTN_WM_SunCaptain",       PAL_GARITHOS,"shield",      87),
    ("BTN_WM_SunChaplain",      PAL_UTHER,   "chalice_tome",88),
    ("BTN_WM_SunHydromancer",   PAL_SYLVANAS,"vortex",      89),
    ("BTN_WM_SunSpellbreaker",  PAL_KAEL,    "shield",      90),
    ("BTN_WM_SunGyro",          PAL_KAEL,    "turret_gear", 91),
    ("BTN_WM_SunLieutenant",    PAL_GARITHOS,"spear",       92),
    ("BTN_WM_SunDragonhawk",    PAL_SYLVANAS,"wings",       93),
    ("BTN_WM_SunGryphon",       PAL_UTHER,   "wings",       94),

    # ---- Voidborn Legion: custom rift-worker, portraits, troops & siege ----
    ("BTN_WM_VoidWorker",       PAL_XALATHOR,"skull_eye",   95),
    ("BTN_WM_VoidHeroXalathor", PAL_XALATHOR,"crown",       96),
    ("BTN_WM_VoidHeroSargen",   PAL_SARGEN,  "skull_eye",   97),
    ("BTN_WM_VoidHeroAetheron", PAL_AETHERON,"nova",       112),
    ("BTN_WM_VoidZealot",       PAL_XALATHOR,"glaives",     98),
    ("BTN_WM_VoidArbalist",     PAL_SARGEN,  "bow",         99),
    ("BTN_WM_VoidEnforcer",     PAL_XALATHOR,"hammer",      100),
    ("BTN_WM_VoidWeaver",       PAL_SARGEN,  "chalice_tome",101),
    ("BTN_WM_VoidDrake",        PAL_AETHERON,"wings",       102),
    ("BTN_WM_VoidDevastator",   PAL_XALATHOR,"turret_gear",103),
    ("BTN_WM_VoidColossus",     PAL_AETHERON,"claws",       104),

    # ---- Runeforged Bastion: custom component icon for every war machine & hero ----
    ("BTN_WM_RuneSentinel",     PAL_THORIM,  "shield",      105),
    ("BTN_WM_RuneArquebusier",  PAL_MIMIRON, "bow",         106),
    ("BTN_WM_RuneJuggernaut",   PAL_IGNIS,   "turret_gear", 107),
    ("BTN_WM_RuneDiviner",      PAL_LOKEN,   "chalice_tome",108),
    ("BTN_WM_RuneInterceptor",  PAL_THORIM,  "wings",       109),
    ("BTN_WM_RuneSiege",        PAL_IGNIS,   "hammer",      110),
    ("BTN_WM_RuneTitan",        PAL_MIMIRON, "claws",       111),
]


# ==============================================================================
# 6. CUSTOM RESOURCE / CONSOLE UI TEXTURES & 3D `.MDX` SPELL MODELS
# ==============================================================================

def build_ui_resource_textures() -> Dict[str, bytes]:
    out: Dict[str, bytes] = {}

    # Dark Obsidian-Gold Astral Dialog / Tooltip Background (`128x128`)
    bg = _radial_canvas(128, (22, 28, 52), (12, 16, 30), (6, 8, 16))
    d = ImageDraw.Draw(bg)
    d.rectangle([2, 2, 125, 125], outline=(218, 172, 62, 220), width=2)
    d.rectangle([6, 6, 121, 121], outline=(56, 189, 248, 140), width=1)
    out["UI\\CrownUI\\MenuBG.blp"] = encode_blp1_paletted(bg, alpha_bits=8)

    # Inventory Empty Slot Filler (`64x64` dark runic socket)
    slot = _radial_canvas(64, (20, 24, 42), (12, 14, 26), (6, 8, 14))
    sd = ImageDraw.Draw(slot)
    sd.rectangle([2, 2, 61, 61], outline=(120, 95, 42, 200), width=1)
    sd.polygon([(32, 14), (48, 32), (32, 50), (16, 32)], outline=(56, 145, 195, 130))
    out["UI\\CrownUI\\SlotFiller.blp"] = encode_blp1_paletted(slot, alpha_bits=8)

    # 32x32 Top-Bar Resource Icons (Gold Sun-Coin, Emerald Crystal-Timber, Sovereign Crown Supply, Upkeep)
    g_img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g_img)
    gd.ellipse([2, 2, 29, 29], fill=(245, 185, 32, 255), outline=(255, 245, 175, 255), width=2)
    gd.polygon([(16, 7), (22, 16), (16, 25), (10, 16)], fill=(255, 252, 210, 255))
    out["UI\\CrownUI\\IconGold.blp"] = encode_blp1_paletted(g_img, alpha_bits=8)

    l_img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    ld = ImageDraw.Draw(l_img)
    ld.polygon([(16, 2), (28, 12), (23, 29), (9, 29), (4, 12)], fill=(36, 205, 125, 255), outline=(195, 255, 225, 255))
    out["UI\\CrownUI\\IconLumber.blp"] = encode_blp1_paletted(l_img, alpha_bits=8)

    s_img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    s_d = ImageDraw.Draw(s_img)
    s_d.polygon([(4, 24), (6, 9), (12, 16), (16, 5), (20, 16), (26, 9), (28, 24)], fill=(248, 198, 56, 255), outline=(255, 248, 210, 255))
    out["UI\\CrownUI\\IconSupply.blp"] = encode_blp1_paletted(s_img, alpha_bits=8)

    u_img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    ud = ImageDraw.Draw(u_img)
    ud.polygon([(16, 3), (29, 16), (16, 29), (3, 16)], fill=(72, 195, 255, 255), outline=(235, 250, 255, 255))
    out["UI\\CrownUI\\IconUpkeep.blp"] = encode_blp1_paletted(u_img, alpha_bits=8)

    return out


def build_sigil_texture(main_rgb: Tuple[int, int, int], core_rgb: Tuple[int, int, int], spikes: int = 8) -> bytes:
    S = 128
    img = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    cx = cy = 63.5
    d.ellipse([8, 8, 119, 119], outline=(*main_rgb, 255), width=4)
    d.ellipse([18, 18, 109, 109], outline=(*core_rgb, 255), width=2)
    pts = []
    for i in range(spikes * 2):
        r = 54 if i % 2 == 0 else 24
        a = math.radians(i * (180.0 / spikes))
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    d.polygon(pts, outline=(*main_rgb, 255), width=3)
    d.ellipse([44, 44, 83, 83], fill=(*core_rgb, 255), outline=(*main_rgb, 255), width=4)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    # Zero out outer border so additive quad never clips visibly
    px = img.load()
    for y in range(S):
        for x in range(S):
            dist = math.hypot(x - cx, y - cy)
            if dist > 60:
                fade = max(0.0, (63.0 - dist) / 3.0)
                r, g, b, _ = px[x, y]
                px[x, y] = (int(r * fade), int(g * fade), int(b * fade), 255)
    return encode_blp1_paletted(img, alpha_bits=8)


def _generate_vfx_mdl(model_name: str, tex_path: str) -> str:
    return f"""Version {{
    FormatVersion 800,
}}
Model "{model_name}" {{
    NumGeosets 2,
    NumGeosetAnims 2,
    NumBones 2,
    BlendTime 150,
    MinimumExtent {{ -160, -160, 0 }},
    MaximumExtent {{ 160, 160, 220 }},
    BoundsRadius 220,
}}
Sequences 3 {{
    Anim "Birth" {{
        Interval {{ 0, 450 }},
        NonLooping,
        MinimumExtent {{ -160, -160, 0 }},
        MaximumExtent {{ 160, 160, 220 }},
        BoundsRadius 220,
    }}
    Anim "Stand" {{
        Interval {{ 500, 1500 }},
        MinimumExtent {{ -160, -160, 0 }},
        MaximumExtent {{ 160, 160, 220 }},
        BoundsRadius 220,
    }}
    Anim "Death" {{
        Interval {{ 1600, 2200 }},
        NonLooping,
        MinimumExtent {{ -160, -160, 0 }},
        MaximumExtent {{ 160, 160, 220 }},
        BoundsRadius 220,
    }}
}}
Textures 1 {{
    Bitmap {{
        Image "{tex_path}",
    }}
}}
Materials 1 {{
    Material {{
        Layer {{
            FilterMode Additive,
            Unshaded,
            TwoSided,
            static TextureID 0,
        }}
    }}
}}
Geoset {{
    Vertices 4 {{
        {{ -128, -128, 8 }},
        {{ 128, -128, 8 }},
        {{ 128, 128, 8 }},
        {{ -128, 128, 8 }},
    }}
    Normals 4 {{
        {{ 0, 0, 1 }},
        {{ 0, 0, 1 }},
        {{ 0, 0, 1 }},
        {{ 0, 0, 1 }},
    }}
    TVertices 4 {{
        {{ 0, 0 }},
        {{ 1, 0 }},
        {{ 1, 1 }},
        {{ 0, 1 }},
    }}
    VertexGroup {{
        0, 0, 0, 0,
    }}
    Faces 1 6 {{
        Triangles {{
            {{ 0, 1, 2, 0, 2, 3 }},
        }}
    }}
    Groups 1 1 {{
        Matrices {{ 0 }},
    }}
    MinimumExtent {{ -128, -128, 8 }},
    MaximumExtent {{ 128, 128, 8 }},
    BoundsRadius 182,
    MaterialID 0,
    SelectionGroup 0,
}}
Geoset {{
    Vertices 8 {{
        {{ -85, 0, 14 }},
        {{ 85, 0, 14 }},
        {{ 85, 0, 190 }},
        {{ -85, 0, 190 }},
        {{ 0, -85, 14 }},
        {{ 0, 85, 14 }},
        {{ 0, 85, 190 }},
        {{ 0, -85, 190 }},
    }}
    Normals 8 {{
        {{ 0, 1, 0 }}, {{ 0, 1, 0 }}, {{ 0, 1, 0 }}, {{ 0, 1, 0 }},
        {{ 1, 0, 0 }}, {{ 1, 0, 0 }}, {{ 1, 0, 0 }}, {{ 1, 0, 0 }},
    }}
    TVertices 8 {{
        {{ 0, 0 }}, {{ 1, 0 }}, {{ 1, 1 }}, {{ 0, 1 }},
        {{ 0, 0 }}, {{ 1, 0 }}, {{ 1, 1 }}, {{ 0, 1 }},
    }}
    VertexGroup {{
        0, 0, 0, 0, 0, 0, 0, 0,
    }}
    Faces 1 12 {{
        Triangles {{
            {{ 0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7 }},
        }}
    }}
    Groups 1 1 {{
        Matrices {{ 1 }},
    }}
    MinimumExtent {{ -85, -85, 14 }},
    MaximumExtent {{ 85, 85, 190 }},
    BoundsRadius 205,
    MaterialID 0,
    SelectionGroup 0,
}}
GeosetAnim {{
    Alpha 5 {{
        Linear,
        0: 0,
        450: 1,
        500: 1,
        1600: 1,
        2200: 0,
    }}
    GeosetId 0,
}}
GeosetAnim {{
    Alpha 5 {{
        Linear,
        0: 0,
        450: 0.9,
        500: 0.9,
        1600: 0.9,
        2200: 0,
    }}
    GeosetId 1,
}}
Bone "Bone_Ring" {{
    ObjectId 0,
    GeosetId 0,
    GeosetAnimId 0,
    Rotation 5 {{
        Linear,
        0: {{ 0, 0, 0, 1 }},
        450: {{ 0, 0, 0.382683, 0.92388 }},
        500: {{ 0, 0, 0, 1 }},
        1500: {{ 0, 0, 0.707107, 0.707107 }},
        2200: {{ 0, 0, 0.92388, 0.382683 }},
    }}
    Scaling 5 {{
        Linear,
        0: {{ 0.2, 0.2, 0.2 }},
        450: {{ 1.15, 1.15, 1.0 }},
        500: {{ 1.0, 1.0, 1.0 }},
        1600: {{ 1.05, 1.05, 1.0 }},
        2200: {{ 1.45, 1.45, 0.1 }},
    }}
}}
Bone "Bone_Crown" {{
    ObjectId 1,
    GeosetId 1,
    GeosetAnimId 1,
    Scaling 5 {{
        Linear,
        0: {{ 0.25, 0.25, 0.1 }},
        450: {{ 1.0, 1.0, 1.15 }},
        500: {{ 1.0, 1.0, 1.0 }},
        1600: {{ 1.0, 1.0, 1.0 }},
        2200: {{ 0.15, 0.15, 1.6 }},
    }}
}}
PivotPoints 2 {{
    {{ 0, 0, 8 }},
    {{ 0, 0, 14 }},
}}
"""


def compile_vfx_mdx_models(mdl_map: Dict[str, str]) -> Dict[str, bytes]:
    out: Dict[str, bytes] = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        js_lines = [
            'const fs = require("fs");',
            f'const Model = require("{MDX_MODEL_JS}").default;',
        ]
        for idx, (mpq_name, mdl_text) in enumerate(mdl_map.items()):
            in_p = tmp_dir / f"in_{idx}.mdl"
            out_p = tmp_dir / f"out_{idx}.mdx"
            in_p.write_text(mdl_text, encoding="utf-8")
            js_lines.append(f"""
            {{
                const m = new Model();
                m.loadMdl(fs.readFileSync({str(in_p)!r}, "utf8"));
                const buf = Buffer.from(m.saveMdx());
                const check = new Model();
                check.loadMdx(buf);
                if (check.version !== 800 || check.sequences.length !== 3 || check.geosets.length !== 2) {{
                    throw new Error("MDX roundtrip check failed for {mpq_name}");
                }}
                fs.writeFileSync({str(out_p)!r}, buf);
            }}
            """)
        script_p = tmp_dir / "compile.js"
        script_p.write_text("\n".join(js_lines), encoding="utf-8")
        subprocess.run(["node", str(script_p)], check=True)
        for idx, mpq_name in enumerate(mdl_map.keys()):
            out[mpq_name] = (tmp_dir / f"out_{idx}.mdx").read_bytes()
    return out


# ==============================================================================
# 7. MASTER ASSET BUNDLE & WEB PREVIEW SHOWCASE SHEET
# ==============================================================================

def build_war3map_preview_tga() -> bytes:
    assert ARTWORK_PNG.exists(), f"Missing custom artwork at {ARTWORK_PNG}"
    img = Image.open(ARTWORK_PNG).convert("RGB").resize((256, 256), Image.Resampling.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.10)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 255, 255], outline=(10, 12, 22), width=2)
    draw.rectangle([2, 2, 253, 253], outline=(232, 185, 64), width=2)
    draw.rectangle([4, 4, 251, 251], outline=(64, 205, 255), width=1)
    return encode_tga_24bit(img)


def generate_all_custom_assets(save_web_sheet: bool = True) -> Dict[str, bytes]:
    """
    Build and return `{mpq_archive_path: binary_bytes}` for all v4 custom assets.
    """
    files: Dict[str, bytes] = {}
    preview_samples: List[Image.Image] = []

    # 1. Lobby Map Preview Artwork (`war3mapPreview.tga`)
    files["war3mapPreview.tga"] = build_war3map_preview_tga()

    # 2. Custom Animated Multi-State Mouse Cursor (`256x128` 8-bit alpha BLP1)
    #    Installed across ALL 4 racial cursor texture paths so every Lobby race gets it!
    cursor_img = build_custom_cursor_atlas_img()
    cursor_blp = encode_blp1_paletted(cursor_img, alpha_bits=8)
    for race_cur in ("HumanCursor", "OrcCursor", "UndeadCursor", "NightElfCursor"):
        files[f"UI\\Cursor\\{race_cur}.blp"] = cursor_blp

    # 3. Custom RPG Infocard Icons (Damage Types, Armor Types, Hero Attributes)
    infocard_blps, infocard_samples = build_infocard_icons()
    files.update(infocard_blps)
    preview_samples.extend(infocard_samples)

    # 4. Custom Console / Resource Icons
    files.update(build_ui_resource_textures())

    # 5. 64 Unique Hero Skill Icons (`BTN_WM_S00..S63` + `DISBTN_WM_S00..S63`, 0-bit alpha compact BLP1!)
    for idx, (pal, motif) in enumerate(SKILL_64_MOTIFS):
        btn_stem = f"BTN_WM_S{idx:02d}"
        core_img, accent = _paint_emblem_icon(*pal, motif=motif, seed=idx + 1)
        btn_img, dis_img = apply_btn_frame(core_img, accent)
        # Include all 64 unique hero-specific ability icons in the web preview sheet.
        preview_samples.append(btn_img)
        files[f"ReplaceableTextures\\CommandButtons\\{btn_stem}.blp"] = encode_blp1_paletted(btn_img, alpha_bits=0)
        files[f"ReplaceableTextures\\CommandButtonsDisabled\\DIS{btn_stem}.blp"] = encode_blp1_paletted(dis_img, alpha_bits=0)

    # 6. Command Card, 5 Racial Build Icons, Hero Illidan/Akama & Racial Building/Unit Icons
    for btn_stem, pal, motif, seed in EXTRA_CUSTOM_ICONS:
        core_img, accent = _paint_emblem_icon(*pal, motif=motif, seed=seed)
        btn_img, dis_img = apply_btn_frame(core_img, accent)
        if "Build" in btn_stem or "Illidan" in btn_stem or "CmdAttack" in btn_stem or "CrownCrest" in btn_stem:
            preview_samples.append(btn_img)
        files[f"ReplaceableTextures\\CommandButtons\\{btn_stem}.blp"] = encode_blp1_paletted(btn_img, alpha_bits=0)
        files[f"ReplaceableTextures\\CommandButtonsDisabled\\DIS{btn_stem}.blp"] = encode_blp1_paletted(dis_img, alpha_bits=0)

    # 7. 6 Custom Additive Sigil BLP1 Textures + 6 Custom 3D `.mdx` Spell Models
    sigil_defs = [
        ("WM_Sigil_Abyssal", (18, 205, 245),  (210, 255, 255), 8, "WM_FX_Abyssal.mdx"),
        ("WM_Sigil_Fel",     (58, 250, 128),  (220, 255, 195), 6, "WM_FX_FelGlaive.mdx"),
        ("WM_Sigil_Solar",   (250, 150, 25),  (255, 250, 205), 8, "WM_FX_Solar.mdx"),
        ("WM_Sigil_Void",    (175, 72, 255),  (245, 215, 255), 8, "WM_FX_Void.mdx"),
        ("WM_Sigil_Runic",   (78, 210, 255),  (255, 232, 150), 6, "WM_FX_Runic.mdx"),
        ("WM_Sigil_Emerald", (48, 230, 165),  (220, 255, 235), 8, "WM_FX_Emerald.mdx"),
    ]
    mdl_specs: Dict[str, str] = {}
    for sig_name, c_main, c_core, spk, mdx_name in sigil_defs:
        tex_path = f"Textures\\{sig_name}.blp"
        files[tex_path] = build_sigil_texture(c_main, c_core, spikes=spk)
        mdl_specs[mdx_name] = _generate_vfx_mdl(mdx_name[:-4], tex_path)
    files.update(compile_vfx_mdx_models(mdl_specs))

    # 8. Save Web Showcase Preview Sheet (`web/public/custom_icons_preview.png`)
    if save_web_sheet and preview_samples:
        cols = 8
        rows_cnt = math.ceil(len(preview_samples) / cols) + 1
        sheet = Image.new("RGBA", (cols * 72 + 16, rows_cnt * 72 + 16), (9, 13, 24, 255))
        # Paste 24 sample icons + cursor strip on bottom row
        for idx, ic in enumerate(preview_samples[: cols * (rows_cnt - 1)]):
            gx = 12 + (idx % cols) * 72
            gy = 12 + (idx // cols) * 72
            sheet.paste(ic, (gx, gy), ic)
        cur_strip = cursor_img.resize((256, 64), Image.Resampling.NEAREST)
        sheet.paste(cur_strip, (12, 12 + (rows_cnt - 1) * 72), cur_strip)
        PREVIEW_SHEET_PNG.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(PREVIEW_SHEET_PNG)

    return files


if __name__ == "__main__":
    bundle = generate_all_custom_assets()
    total = sum(len(v) for v in bundle.values())
    print(f"Generated {len(bundle)} custom v4 assets ({total:,} bytes raw)")
