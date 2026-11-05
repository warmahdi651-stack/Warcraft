#!/usr/bin/env python3
"""
Artwork and UI asset pipeline for `(8) Crown of WarMahdi` v7.

Generates Warcraft III binary assets while keeping gameplay art recognizable and
patch-safe:
  1. A 256x256 lobby preview TGA derived from the map's custom artwork.
  2. Four compatible animated cursor texture atlases.
  3. RPG infocard, resource and console textures for the existing in-game UI.
  4. Ten AI-generated 64x64 hero portrait BLPs from source art in
     `src/assets/hero_portraits/`; other heroes use authentic native WC3 portraits.
  5. Six additive faction sigils plus 64 individually themed, geometrically distinct
     skill textures and version-800 MDX models, compiled and roundtrip-checked with
     `mdx-m3-viewer`.

Hero/unit/building buttons inherit recognizable stock Warcraft III artwork. The 64
custom skills use native command-button icons selected to match their effects; no
procedurally drawn geometric icons are imported for those gameplay objects.
"""

from __future__ import annotations

import math
import re
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

try:
    from .blp_codec import encode_blp1_jpeg
except ImportError:  # Allow `python src/custom_assets.py` as a standalone command.
    from blp_codec import encode_blp1_jpeg


REPO_ROOT = Path(__file__).resolve().parent.parent
ARTWORK_PNG = REPO_ROOT / "web" / "public" / "crown_artwork.png"
PREVIEW_SHEET_PNG = REPO_ROOT / "web" / "public" / "custom_icons_preview.png"
MDX_MODEL_JS = Path("/tmp/wc3ref/node_modules/mdx-m3-viewer/dist/cjs/parsers/mdlx/model")


# ==============================================================================
# 1. ICON-ONLY PALETTED BLP1, TRUECOLOR BLP1, AND TGA WRITERS
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
    Encode an RGBA PIL Image into a paletted BLP1 command-button icon (`content=1`)
    with a full mipmap chain and 8-bit or zero-bit alpha. Keep it icon-only.
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


def encode_blp1_truecolor(img: Image.Image, quality_scale: float = 0.35) -> bytes:
    """Encode non-icon textures as 4-channel JPEG-compressed BLP1, never paletted."""
    rgba = img.convert("RGBA")
    width, height = rgba.size
    if width % 8 or height % 8:
        raise ValueError(f"JPEG BLP dimensions must be multiples of 8: {width}x{height}")
    return encode_blp1_jpeg(rgba.tobytes(), width, height, quality_scale)


# ==============================================================================
# 2. CUSTOM ANIMATED MULTI-STATE MOUSE CURSOR ATLAS (`256x128` 8x4 x 32x32)
# ==============================================================================

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
        out[f"UI\\CrownUI\\Infocard\\{name}.blp"] = encode_blp1_truecolor(upg_im)
        out[f"UI\\CrownUI\\Infocard\\{name}Neutral.blp"] = encode_blp1_truecolor(neu_im)

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
        out[f"UI\\CrownUI\\Infocard\\{name}.blp"] = encode_blp1_truecolor(upg_im)
        out[f"UI\\CrownUI\\Infocard\\{name}Neutral.blp"] = encode_blp1_truecolor(neu_im)

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
        out[f"UI\\CrownUI\\Infocard\\{code}.blp"] = encode_blp1_truecolor(at_im)

    return out, samples


# ==============================================================================
# 5. RECOGNIZABLE CUSTOM HERO PORTRAITS (STOCK GAME ART FOR THE REST)
# ==============================================================================

HERO_PORTRAITS = (
    ("Hvsh", "vashj", "VASHJ"),
    ("N004", "illidan", "ILLIDAN"),
    ("N001", "najentus", "NAJ'ENTUS"),
    ("N002", "athissa", "ATHISSA"),
    ("Hkal", "kael", "KAEL'THAS"),
    ("Hvwd", "sylvanas", "SYLVANAS"),
    ("Hlgr", "garithos", "GARITHOS"),
    ("Huth", "uther", "UTHER"),
    ("V001", "xalathor", "XAL'ATHOR"),
    ("V002", "sargeneth", "SARGEN'ETH"),
)
HERO_PORTRAIT_SOURCE_DIR = REPO_ROOT / "src" / "assets" / "hero_portraits"


def build_hero_portrait_assets() -> Tuple[Dict[str, bytes], List[Tuple[str, Image.Image]]]:
    """Create full-bleed 64x64 BLP portraits and muted disabled-button twins."""
    out: Dict[str, bytes] = {}
    samples: List[Tuple[str, Image.Image]] = []
    for rawcode, slug, label in HERO_PORTRAITS:
        source = HERO_PORTRAIT_SOURCE_DIR / f"{slug}.png"
        if not source.is_file():
            raise FileNotFoundError(f"Missing generated hero portrait source: {source}")
        with Image.open(source) as img:
            portrait = ImageOps.fit(
                img.convert("RGB"),
                (64, 64),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.48),
            ).convert("RGBA")
        disabled_gray = ImageOps.grayscale(portrait.convert("RGB"))
        disabled = ImageOps.colorize(disabled_gray, black=(20, 22, 30), white=(160, 160, 168)).convert("RGBA")
        btn = f"BTN_WM_Portrait_{rawcode}"
        out[f"ReplaceableTextures\\CommandButtons\\{btn}.blp"] = encode_blp1_paletted(portrait, alpha_bits=0)
        out[f"ReplaceableTextures\\CommandButtonsDisabled\\DIS{btn}.blp"] = encode_blp1_paletted(disabled, alpha_bits=0)
        samples.append((label, portrait.convert("RGB")))
    return out, samples


def save_hero_portrait_preview(samples: List[Tuple[str, Image.Image]]) -> None:
    """Render a web-only contact sheet of the ten custom hero portraits."""
    cols = 5
    cell_w = 176
    cell_h = 194
    margin = 16
    title_h = 44
    footer_h = 38
    rows = (len(samples) + cols - 1) // cols
    sheet = Image.new("RGB", (margin * 2 + cols * cell_w, title_h + rows * cell_h + footer_h), (9, 13, 24))
    draw = ImageDraw.Draw(sheet)
    try:
        font_title = ImageFont.truetype("DejaVuSans.ttf", 16)
        font_label = ImageFont.truetype("DejaVuSans.ttf", 12)
        font_footer = ImageFont.truetype("DejaVuSans.ttf", 10)
    except OSError:
        font_title = font_label = font_footer = ImageFont.load_default()
    draw.text((margin, 13), "CUSTOM HERO PORTRAITS  |  10 ORIGINAL ARTWORKS", font=font_title, fill=(239, 205, 122))
    for idx, (label, portrait) in enumerate(samples):
        x = margin + (idx % cols) * cell_w
        y = title_h + (idx // cols) * cell_h
        image = portrait.resize((148, 148), Image.Resampling.LANCZOS)
        sheet.paste(image, (x, y))
        draw.rectangle((x, y, x + 147, y + 147), outline=(92, 132, 154), width=1)
        box = draw.textbbox((0, 0), label, font=font_label)
        text_x = x + (148 - (box[2] - box[0])) // 2
        draw.text((text_x, y + 155), label, font=font_label, fill=(231, 235, 242))
    footer = "Other heroes use authentic native Warcraft III portraits; all 64 skills use effect-matched native buttons."
    draw.text((margin, title_h + rows * cell_h + 9), footer, font=font_footer, fill=(151, 171, 190))
    PREVIEW_SHEET_PNG.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW_SHEET_PNG, optimize=True)


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
    out["UI\\CrownUI\\MenuBG.blp"] = encode_blp1_truecolor(bg)

    # Inventory Empty Slot Filler (`64x64` dark runic socket)
    slot = _radial_canvas(64, (20, 24, 42), (12, 14, 26), (6, 8, 14))
    sd = ImageDraw.Draw(slot)
    sd.rectangle([2, 2, 61, 61], outline=(120, 95, 42, 200), width=1)
    sd.polygon([(32, 14), (48, 32), (32, 50), (16, 32)], outline=(56, 145, 195, 130))
    out["UI\\CrownUI\\SlotFiller.blp"] = encode_blp1_truecolor(slot)

    # 32x32 Top-Bar Resource Icons (Gold Sun-Coin, Emerald Crystal-Timber, Sovereign Crown Supply, Upkeep)
    g_img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g_img)
    gd.ellipse([2, 2, 29, 29], fill=(245, 185, 32, 255), outline=(255, 245, 175, 255), width=2)
    gd.polygon([(16, 7), (22, 16), (16, 25), (10, 16)], fill=(255, 252, 210, 255))
    out["UI\\CrownUI\\IconGold.blp"] = encode_blp1_truecolor(g_img)

    l_img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    ld = ImageDraw.Draw(l_img)
    ld.polygon([(16, 2), (28, 12), (23, 29), (9, 29), (4, 12)], fill=(36, 205, 125, 255), outline=(195, 255, 225, 255))
    out["UI\\CrownUI\\IconLumber.blp"] = encode_blp1_truecolor(l_img)

    s_img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    s_d = ImageDraw.Draw(s_img)
    s_d.polygon([(4, 24), (6, 9), (12, 16), (16, 5), (20, 16), (26, 9), (28, 24)], fill=(248, 198, 56, 255), outline=(255, 248, 210, 255))
    out["UI\\CrownUI\\IconSupply.blp"] = encode_blp1_truecolor(s_img)

    u_img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    ud = ImageDraw.Draw(u_img)
    ud.polygon([(16, 3), (29, 16), (16, 29), (3, 16)], fill=(72, 195, 255, 255), outline=(235, 250, 255, 255))
    out["UI\\CrownUI\\IconUpkeep.blp"] = encode_blp1_truecolor(u_img)

    return out


def build_sigil_texture(main_rgb: Tuple[int, int, int], core_rgb: Tuple[int, int, int], spikes: int = 8) -> bytes:
    """Create a true-color additive faction-sigil texture (never used for icons)."""
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
    # Fade the perimeter so the additive quad does not clip at its bounds.
    px = img.load()
    for y in range(S):
        for x in range(S):
            dist = math.hypot(x - cx, y - cy)
            if dist > 60:
                fade = max(0.0, (63.0 - dist) / 3.0)
                r, g, b, _ = px[x, y]
                px[x, y] = (int(r * fade), int(g * fade), int(b * fade), 255)
    return encode_blp1_truecolor(img)


# Each four-skill kit has a visual family, while hero palette, geometry variation,
# and rune placement make every one of the 64 textures/models individually distinct.
SPELL_FX_SHAPES = ("burst", "bolt", "shield", "portal")
SPELL_HERO_PALETTES: Tuple[Tuple[Tuple[int, int, int], Tuple[int, int, int]], ...] = (
    ((24, 208, 238), (220, 255, 255)),   # Vashj - tidal aqua
    ((70, 242, 125), (242, 255, 185)),   # Illidan - fel jade
    ((15, 128, 194), (180, 248, 255)),  # Naj'entus - deep coral
    ((90, 224, 210), (255, 246, 216)),  # Athissa - pearl tide
    ((249, 130, 34), (255, 242, 175)),  # Kael'thas - sunfire
    ((234, 73, 94), (255, 226, 140)),   # Sylvanas - blood moon
    ((210, 164, 79), (255, 238, 180)),  # Garithos - bronze
    ((248, 220, 158), (255, 255, 238)), # Uther - holy gold
    ((139, 71, 244), (229, 208, 255)),  # Xal'athor - void violet
    ((221, 55, 194), (255, 205, 246)),  # Sargen'eth - entropy magenta
    ((69, 111, 222), (196, 224, 255)),  # Akama - shadow blue
    ((83, 211, 245), (237, 244, 255)),  # Aetheron - astral ice
    ((75, 205, 255), (255, 240, 160)),  # Thorim - stormsteel
    ((255, 101, 35), (255, 226, 120)),  # Ignis - molten rune
    ((192, 149, 92), (148, 230, 255)),  # Mimiron - brass/arc
    ((91, 91, 235), (185, 255, 190)),   # Loken - lightning indigo
)


def build_spell_vfx_texture(ability_index: int) -> bytes:
    """Draw a unique hero-and-skill motif into a true-color additive BLP1 texture."""
    if not 0 <= ability_index < 64:
        raise ValueError(f"spell-effect index out of range: {ability_index}")
    hero_index = ability_index // 4
    slot = ability_index % 4
    variant = ability_index
    main_rgb, core_rgb = SPELL_HERO_PALETTES[hero_index]
    shape = SPELL_FX_SHAPES[slot]
    S = 256
    c = (S - 1) / 2.0
    angle = math.radians((hero_index * 19 + variant * 11) % 360)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    gd = ImageDraw.Draw(glow)
    d = ImageDraw.Draw(img)
    outer = 88 + (variant % 8) * 4
    inner = 30 + (variant % 6) * 3
    glow_rgb = tuple(min(255, int(c0 * 0.72 + 60)) for c0 in main_rgb)

    if shape == "burst":
        points = []
        teeth = 7 + (variant % 6)
        for k in range(teeth * 2):
            radius = outer if k % 2 == 0 else inner + (variant % 9)
            theta = angle + math.tau * k / (teeth * 2)
            points.append((c + math.cos(theta) * radius, c + math.sin(theta) * radius))
        gd.line(points + [points[0]], fill=(*glow_rgb, 190), width=20, joint="curve")
        gd.ellipse([c-outer, c-outer, c+outer, c+outer], outline=(*glow_rgb, 105), width=15)
        d.polygon(points, outline=(*main_rgb, 255), width=5)
        d.ellipse([c-inner, c-inner, c+inner, c+inner], outline=(*core_rgb, 255), width=5)
        for k in range(5 + hero_index % 5):
            theta = angle + math.tau * k / (5 + hero_index % 5)
            r0, r1 = inner + 10, outer - 8
            line = [(c + math.cos(theta) * r0, c + math.sin(theta) * r0),
                    (c + math.cos(theta) * r1, c + math.sin(theta) * r1)]
            gd.line(line, fill=(*glow_rgb, 180), width=10)
            d.line(line, fill=(*core_rgb, 220), width=3)
    elif shape == "bolt":
        length = 84 + (variant % 9) * 5
        jag = 18 + (variant % 7) * 3
        path = []
        for k in range(7):
            along = -length + k * length / 3.0
            across = (0 if k in (0, 6) else (-1 if k % 2 else 1) * jag)
            xx = along * math.cos(angle) - across * math.sin(angle)
            yy = along * math.sin(angle) + across * math.cos(angle)
            path.append((c + xx, c + yy))
        gd.line(path, fill=(*glow_rgb, 220), width=28, joint="curve")
        d.line(path, fill=(*core_rgb, 255), width=10, joint="curve")
        d.line(path, fill=(*main_rgb, 255), width=5, joint="curve")
        for k in range(3 + variant % 4):
            theta = angle + math.pi * (0.55 + 0.25 * k)
            r = inner + (k * 13)
            x0, y0 = c + math.cos(theta) * r, c + math.sin(theta) * r
            x1, y1 = c + math.cos(theta) * (r + 18), c + math.sin(theta) * (r + 18)
            gd.line([(x0,y0),(x1,y1)], fill=(*glow_rgb, 170), width=10)
            d.line([(x0,y0),(x1,y1)], fill=(*main_rgb, 255), width=4)
    elif shape == "shield":
        w = 74 + (variant % 7) * 4
        h = 95 + (variant % 8) * 3
        local = [(-w, -h*0.62), (0, -h), (w, -h*0.62), (w*0.78, h*0.15),
                 (0, h), (-w*0.78, h*0.15)]
        points = [(c + x*math.cos(angle) - y*math.sin(angle),
                   c + x*math.sin(angle) + y*math.cos(angle)) for x,y in local]
        gd.line(points + [points[0]], fill=(*glow_rgb, 205), width=22, joint="curve")
        d.polygon(points, outline=(*main_rgb, 255), width=6)
        inner_pts = []
        for x,y in local:
            xx, yy = x*0.55, y*0.56
            inner_pts.append((c + xx*math.cos(angle) - yy*math.sin(angle),
                              c + xx*math.sin(angle) + yy*math.cos(angle)))
        d.polygon(inner_pts, outline=(*core_rgb, 255), width=4)
        d.line([points[1], points[4]], fill=(*core_rgb, 230), width=4)
        for k in range(3 + hero_index % 4):
            theta = angle + math.tau * k / (3 + hero_index % 4)
            x, y = c + math.cos(theta) * (outer - 10), c + math.sin(theta) * (outer - 10)
            r = 5 + (variant % 4)
            d.polygon([(x,y-r),(x+r,y),(x,y+r),(x-r,y)], fill=(*core_rgb,255))
    else:  # portal / ultimate
        count = 8 + (variant % 7)
        gd.ellipse([c-outer-8,c-outer-8,c+outer+8,c+outer+8], outline=(*glow_rgb,175), width=22)
        d.ellipse([c-outer,c-outer,c+outer,c+outer], outline=(*main_rgb,255), width=8)
        d.ellipse([c-inner-8,c-inner-8,c+inner+8,c+inner+8], outline=(*core_rgb,255), width=5)
        d.ellipse([c-inner*0.55,c-inner*0.55,c+inner*0.55,c+inner*0.55], outline=(*main_rgb,255), width=4)
        for k in range(count):
            theta = angle + math.tau * k / count
            r0 = inner + 10
            r1 = outer - (7 if k % 2 else 0)
            a = (c + math.cos(theta) * r0, c + math.sin(theta) * r0)
            b = (c + math.cos(theta) * r1, c + math.sin(theta) * r1)
            gd.line([a,b], fill=(*glow_rgb,185), width=11)
            d.line([a,b], fill=(*main_rgb,255), width=4)
            x,y = b
            dot = 4 + (variant % 4)
            d.ellipse([x-dot,y-dot,x+dot,y+dot], fill=(*core_rgb,255))

    # A hero-specific orbiting rune cadence differentiates the sixteen kits beyond hue.
    rune_count = 3 + (hero_index % 6)
    rune_radius = 48 + (variant % 5) * 5
    for k in range(rune_count):
        theta = angle + math.tau * k / rune_count
        x = c + math.cos(theta) * rune_radius
        y = c + math.sin(theta) * rune_radius
        r = 5 + ((hero_index + k) % 4)
        d.polygon([(x,y-r*1.4),(x+r,y),(x,y+r*1.4),(x-r,y)], outline=(*core_rgb,220), width=2)

    glow = glow.filter(ImageFilter.GaussianBlur(12))
    img = Image.alpha_composite(glow, img)
    img = img.resize((128,128), Image.Resampling.LANCZOS)
    # Keep the outer additive edge near black for clean fades on older renderers.
    px = img.load()
    for y in range(128):
        for x in range(128):
            dist = math.hypot(x - 63.5, y - 63.5)
            if dist > 60:
                fade = max(0.0, min(1.0, (66.0 - dist) / 6.0))
                r,g,b,a = px[x,y]
                px[x,y] = (int(r*fade), int(g*fade), int(b*fade), a)
    return encode_blp1_truecolor(img)


def _fmt_v3(v: Tuple[float, float, float]) -> str:
    return f"{{ {v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f} }}"


def _make_vfx_geoset(
    vertices: List[Tuple[float, float, float]],
    normals: List[Tuple[float, float, float]],
    uvs: List[Tuple[float, float]],
    faces: List[int],
    min_extent: Tuple[float, float, float],
    max_extent: Tuple[float, float, float],
    radius: float,
) -> str:
    if len(vertices) != len(normals) or len(vertices) != len(uvs) or len(faces) % 3:
        raise ValueError("invalid custom VFX geoset topology")
    vertex_lines = ",\n".join(f"        {_fmt_v3(v)}" for v in vertices)
    normal_lines = ",\n".join(f"        {_fmt_v3(n)}" for n in normals)
    uv_lines = ",\n".join(f"        {{ {uv[0]:.5f}, {uv[1]:.5f} }}" for uv in uvs)
    face_line = ", ".join(str(i) for i in faces)
    groups = ", ".join("0" for _ in vertices)
    return f"""Geoset {{
    Vertices {len(vertices)} {{
{vertex_lines},
    }}
    Normals {len(normals)} {{
{normal_lines},
    }}
    TVertices {len(uvs)} {{
{uv_lines},
    }}
    VertexGroup {{
        {groups},
    }}
    Faces 1 {len(faces)} {{
        Triangles {{
            {{ {face_line} }},
        }}
    }}
    Groups 1 1 {{
        Matrices {{ 0 }},
    }}
    MinimumExtent {{ {_fmt_v3(min_extent)[2:-2]} }},
    MaximumExtent {{ {_fmt_v3(max_extent)[2:-2]} }},
    BoundsRadius {radius:.3f},
    MaterialID 0,
    SelectionGroup 0,
}}"""


# Three Naga-only structures were formerly assigned the same Shrine/Altar/Spawning
# Grounds models already used by nnsa/nnad/nnsg. These bespoke, low-poly buildings
# keep the Warcraft III 1.26-compatible v800 MDX format while giving each role its own
# silhouette and true-color texture.
NAGA_BUILDING_MODEL_DEFS = (
    ("WM_Build_Naga_TidalTreasury.mdx", "treasury"),
    ("WM_Build_Naga_CoralForge.mdx", "forge"),
    ("WM_Build_Naga_BehemothPool.mdx", "pool"),
)

NAGA_BUILDING_PALETTES = {
    "treasury": ((13, 63, 86), (23, 116, 133), (87, 203, 198), (229, 205, 137), (216, 250, 233)),
    "forge": ((27, 43, 65), (93, 83, 93), (178, 103, 79), (246, 164, 74), (174, 237, 227)),
    "pool": ((7, 44, 78), (16, 92, 126), (33, 168, 177), (122, 213, 209), (227, 246, 222)),
}


def build_naga_building_texture(kind: str) -> bytes:
    """Create a 256-square opaque, true-color BLP atlas for a custom Naga building."""
    if kind not in NAGA_BUILDING_PALETTES:
        raise ValueError(f"unknown Naga building theme: {kind}")
    deep, mid, bright, trim, pearl = NAGA_BUILDING_PALETTES[kind]
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 255))
    pixels = image.load()
    for y in range(256):
        t = y / 255.0
        if t < 0.58:
            a, b, u = deep, mid, t / 0.58
        else:
            a, b, u = mid, bright, (t - 0.58) / 0.42
        for x in range(256):
            grain = ((x * 13 + y * 7 + (x * y) % 19) % 9) - 4
            pixels[x, y] = tuple(max(0, min(255, int(a[c] * (1.0 - u) + b[c] * u) + grain)) for c in range(3)) + (255,)

    draw = ImageDraw.Draw(image)
    # Hand-cut block courses and thin pearl-inlaid seams read clearly at game zoom.
    for y in (30, 64, 98, 132, 166, 200, 234):
        draw.line((0, y, 255, y), fill=(*trim, 245), width=3)
    for row, y in enumerate((15, 49, 83, 117, 151, 185, 219, 247)):
        offset = 16 if row % 2 else 0
        for x in range(offset, 256, 32):
            draw.line((x, y - 11, x, y + 11), fill=(*deep, 245), width=3)

    if kind == "treasury":
        # Shell-scaled walls, arch windows, and a pearl-and-coral merchant crest.
        for x in range(18, 256, 32):
            draw.arc((x - 15, 42, x + 15, 83), 195, 345, fill=(*pearl, 230), width=3)
            draw.line((x, 54, x, 79), fill=(*trim, 230), width=2)
        for x in (44, 92, 140, 188, 236):
            draw.rounded_rectangle((x - 9, 112, x + 9, 158), radius=8, fill=(*deep, 255), outline=(*pearl, 245), width=3)
        draw.ellipse((82, 177, 174, 241), fill=(*mid, 255), outline=(*trim, 255), width=5)
        draw.ellipse((110, 194, 146, 230), fill=(*pearl, 255), outline=(*bright, 255), width=3)
        draw.arc((87, 182, 169, 240), 205, 335, fill=(*pearl, 255), width=4)
    elif kind == "forge":
        # Dark coral plates around a hot inner crucible; the orange accent is forge heat.
        for x in (18, 58, 98, 138, 178, 218):
            draw.polygon(((x, 28), (x + 13, 48), (x + 8, 79), (x - 5, 63)), fill=(*bright, 255), outline=(*trim, 255))
        draw.rectangle((40, 105, 216, 225), fill=(*deep, 255), outline=(*trim, 255), width=5)
        draw.rounded_rectangle((86, 132, 170, 221), radius=16, fill=(*bright, 255), outline=(*pearl, 255), width=4)
        draw.polygon(((107, 194), (119, 151), (128, 174), (141, 144), (153, 194)), fill=(*trim, 255), outline=(*pearl, 255))
        draw.line((54, 117, 202, 117), fill=(*pearl, 255), width=4)
        for x in (62, 194):
            draw.ellipse((x - 8, 82, x + 8, 98), fill=(*trim, 255), outline=(*pearl, 255), width=2)
    else:  # pool
        # Concentric tide rings, hatchery scales, and four bright reef markers.
        for r, color, width in ((102, pearl, 4), (76, bright, 5), (44, trim, 4)):
            draw.ellipse((128 - r, 128 - r, 128 + r, 128 + r), outline=(*color, 255), width=width)
        draw.ellipse((108, 108, 148, 148), fill=(*deep, 255), outline=(*pearl, 255), width=4)
        draw.arc((20, 18, 236, 236), 190, 350, fill=(*pearl, 230), width=5)
        for x, y in ((128, 28), (228, 128), (128, 228), (28, 128)):
            draw.polygon(((x, y - 18), (x + 9, y), (x, y + 18), (x - 9, y)), fill=(*bright, 255), outline=(*trim, 255))
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(*pearl, 255))

    image = image.filter(ImageFilter.GaussianBlur(0.35))
    return encode_blp1_truecolor(image)


def _building_add_triangle(
    mesh: Dict[str, list],
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
    c: Tuple[float, float, float],
    uv_a: Tuple[float, float],
    uv_b: Tuple[float, float],
    uv_c: Tuple[float, float],
) -> None:
    """Append one flat-shaded triangle; duplicate vertices keep normals/UVs precise."""
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    normal = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    length = math.sqrt(sum(v * v for v in normal)) or 1.0
    normal = tuple(v / length for v in normal)
    base = len(mesh["vertices"])
    mesh["vertices"].extend((a, b, c))
    mesh["normals"].extend((normal, normal, normal))
    mesh["uvs"].extend((uv_a, uv_b, uv_c))
    mesh["faces"].extend((base, base + 1, base + 2))


def _building_add_quad(
    mesh: Dict[str, list],
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
    c: Tuple[float, float, float],
    d: Tuple[float, float, float],
    uv_a: Tuple[float, float] = (0.0, 0.0),
    uv_b: Tuple[float, float] = (1.0, 0.0),
    uv_c: Tuple[float, float] = (1.0, 1.0),
    uv_d: Tuple[float, float] = (0.0, 1.0),
) -> None:
    _building_add_triangle(mesh, a, b, c, uv_a, uv_b, uv_c)
    _building_add_triangle(mesh, a, c, d, uv_a, uv_c, uv_d)


def _building_add_frustum(
    mesh: Dict[str, list],
    cx: float,
    cy: float,
    z0: float,
    z1: float,
    r0: float,
    r1: float,
    sides: int = 12,
    phase: float = 0.0,
) -> None:
    """Add a closed, UV-mapped polygonal tower, ring, or cone to the building mesh."""
    ring0 = []
    ring1 = []
    for k in range(sides):
        angle = phase + math.tau * k / sides
        ring0.append((cx + math.cos(angle) * r0, cy + math.sin(angle) * r0, z0))
        ring1.append((cx + math.cos(angle) * r1, cy + math.sin(angle) * r1, z1))
    for k in range(sides):
        nxt = (k + 1) % sides
        u0, u1 = k / sides, (k + 1) / sides
        a, b = ring0[k], ring0[nxt]
        if r1 < 0.01:
            apex = (cx, cy, z1)
            _building_add_triangle(mesh, a, b, apex, (u0, 0.0), (u1, 0.0), ((u0 + u1) * 0.5, 1.0))
        else:
            d, c = ring1[k], ring1[nxt]
            _building_add_quad(mesh, a, b, c, d, (u0, 0.0), (u1, 0.0), (u1, 1.0), (u0, 1.0))
    # Close horizontal caps so each tower is a watertight solid, not a two-sided sheet.
    bottom_center = (cx, cy, z0)
    for k in range(sides):
        nxt = (k + 1) % sides
        p0, p1 = ring0[k], ring0[nxt]
        uv0 = (0.5 + (p0[0] - cx) / (2.0 * r0), 0.5 + (p0[1] - cy) / (2.0 * r0))
        uv1 = (0.5 + (p1[0] - cx) / (2.0 * r0), 0.5 + (p1[1] - cy) / (2.0 * r0))
        _building_add_triangle(mesh, bottom_center, p1, p0, (0.5, 0.5), uv1, uv0)
    if r1 > 0.01:
        top_center = (cx, cy, z1)
        for k in range(sides):
            nxt = (k + 1) % sides
            p0, p1 = ring1[k], ring1[nxt]
            uv0 = (0.5 + (p0[0] - cx) / (2.0 * r1), 0.5 + (p0[1] - cy) / (2.0 * r1))
            uv1 = (0.5 + (p1[0] - cx) / (2.0 * r1), 0.5 + (p1[1] - cy) / (2.0 * r1))
            _building_add_triangle(mesh, top_center, p0, p1, (0.5, 0.5), uv0, uv1)


def _building_add_octahedron(
    mesh: Dict[str, list], cx: float, cy: float, z: float, radius: float, height: float
) -> None:
    top = (cx, cy, z + height)
    bottom = (cx, cy, z - height)
    points = [
        (cx + radius, cy, z), (cx, cy + radius, z),
        (cx - radius, cy, z), (cx, cy - radius, z),
    ]
    uvs = [(1.0, 0.5), (0.5, 1.0), (0.0, 0.5), (0.5, 0.0)]
    for k in range(4):
        nxt = (k + 1) % 4
        _building_add_triangle(mesh, top, points[k], points[nxt], (0.5, 1.0), uvs[k], uvs[nxt])
        _building_add_triangle(mesh, bottom, points[nxt], points[k], (0.5, 0.0), uvs[nxt], uvs[k])


def _naga_building_mesh(kind: str) -> Dict[str, list]:
    mesh: Dict[str, list] = {"vertices": [], "normals": [], "uvs": [], "faces": []}
    if kind == "treasury":
        # Low market platform + scallop-roofed central hall + four pearl sentinels.
        _building_add_frustum(mesh, 0, 0, 0, 28, 158, 150, 16)
        _building_add_frustum(mesh, 0, 0, 28, 112, 126, 116, 12, math.pi / 12)
        _building_add_frustum(mesh, 0, 0, 102, 120, 140, 132, 12, math.pi / 12)
        _building_add_frustum(mesh, 0, 0, 118, 218, 132, 18, 12, math.pi / 12)
        _building_add_frustum(mesh, 0, 0, 205, 292, 38, 0, 8, math.pi / 8)
        for x in (-92, 92):
            for y in (-92, 92):
                _building_add_frustum(mesh, x, y, 20, 138, 24, 20, 8, math.pi / 8)
                _building_add_frustum(mesh, x, y, 132, 205, 30, 0, 8, math.pi / 8)
        _building_add_octahedron(mesh, 0, 0, 300, 27, 34)
    elif kind == "forge":
        # Broad anvil foundation, furnace chamber, rising flue, and four venting coral fins.
        _building_add_frustum(mesh, 0, 0, 0, 30, 164, 154, 12, math.pi / 12)
        _building_add_frustum(mesh, 0, 0, 30, 122, 132, 116, 10, math.pi / 10)
        _building_add_frustum(mesh, 0, 0, 116, 178, 102, 68, 10, math.pi / 10)
        _building_add_frustum(mesh, 0, 0, 170, 275, 66, 28, 8, math.pi / 8)
        _building_add_frustum(mesh, 0, 0, 267, 300, 34, 0, 8)
        for x, y, angle in ((-105, 0, 0), (105, 0, math.pi / 2), (0, -105, 0), (0, 105, math.pi / 2)):
            _building_add_frustum(mesh, x, y, 18, 142, 26, 22, 8, angle)
            _building_add_frustum(mesh, x, y, 136, 198, 32, 0, 8, angle)
        _building_add_frustum(mesh, 0, -112, 26, 76, 62, 45, 6, math.pi / 6)
        _building_add_octahedron(mesh, 0, 0, 305, 23, 28)
    elif kind == "pool":
        # A wide, tiered hatchery basin with a recessed water plate and four dorsal fins.
        _building_add_frustum(mesh, 0, 0, 0, 24, 180, 168, 16)
        _building_add_frustum(mesh, 0, 0, 22, 82, 164, 122, 16, math.pi / 16)
        _building_add_frustum(mesh, 0, 0, 76, 90, 139, 134, 16, math.pi / 16)
        _building_add_frustum(mesh, 0, 0, 82, 88, 112, 112, 16, math.pi / 16)
        for x, y, phase in ((0, -128, 0), (128, 0, math.pi / 2), (0, 128, 0), (-128, 0, math.pi / 2)):
            _building_add_frustum(mesh, x, y, 18, 132, 30, 22, 8, phase)
            _building_add_frustum(mesh, x, y, 126, 215, 36, 0, 8, phase)
        for x, y in ((-62, -62), (62, -62), (-62, 62), (62, 62)):
            _building_add_octahedron(mesh, x, y, 88, 13, 19)
    else:
        raise ValueError(f"unknown Naga building mesh: {kind}")
    return mesh


def _generate_naga_building_mdl(model_filename: str, texture_path: str, kind: str) -> str:
    """Create an opaque, animated, one-geoset version-800 Warcraft III building."""
    mesh = _naga_building_mesh(kind)
    vertices = mesh["vertices"]
    extent = max(max(abs(v[0]), abs(v[1])) for v in vertices)
    max_z = max(v[2] for v in vertices)
    min_z = min(v[2] for v in vertices)
    min_extent = (-extent, -extent, min_z)
    max_extent = (extent, extent, max_z)
    bounds = math.sqrt(2.0 * extent * extent + max_z * max_z)
    geoset = _make_vfx_geoset(
        vertices, mesh["normals"], mesh["uvs"], mesh["faces"],
        min_extent, max_extent, bounds,
    )
    model_name = model_filename.rsplit(".", 1)[0]
    seq_extent = f"MinimumExtent {{ {_fmt_v3(min_extent)[2:-2]} }},\n        MaximumExtent {{ {_fmt_v3(max_extent)[2:-2]} }},\n        BoundsRadius {bounds:.3f},"
    return f"""Version {{
    FormatVersion 800,
}}
Model "{model_name}" {{
    NumGeosets 1,
    NumGeosetAnims 1,
    NumBones 1,
    BlendTime 150,
    {seq_extent}
}}
Sequences 3 {{
    Anim "Birth" {{
        Interval {{ 0, 800 }},
        NonLooping,
        {seq_extent}
    }}
    Anim "Stand" {{
        Interval {{ 1000, 1800 }},
        {seq_extent}
    }}
    Anim "Death" {{
        Interval {{ 2000, 2800 }},
        NonLooping,
        {seq_extent}
    }}
}}
Textures 1 {{
    Bitmap {{
        Image "{texture_path}",
    }}
}}
Materials 1 {{
    Material {{
        Layer {{
            FilterMode None,
            TwoSided,
            static TextureID 0,
        }}
    }}
}}
{geoset}
GeosetAnim {{
    Alpha 6 {{
        Linear,
        0: 0,
        400: 0.3,
        800: 1,
        1000: 1,
        2000: 1,
        2800: 0,
    }}
    GeosetId 0,
}}
Bone "NagaBuildingRoot" {{
    ObjectId 0,
    GeosetId 0,
    GeosetAnimId 0,
    Scaling 6 {{
        Linear,
        0: {{ 0.85, 0.85, 0.85 }},
        400: {{ 0.94, 0.94, 0.94 }},
        800: {{ 1, 1, 1 }},
        1000: {{ 1, 1, 1 }},
        2000: {{ 1, 1, 1 }},
        2800: {{ 0.75, 0.75, 0.75 }},
    }}
}}
PivotPoints 1 {{
    {{ 0, 0, 0 }},
}}
"""


def build_naga_building_model_specs() -> Tuple[Dict[str, str], Dict[str, bytes]]:
    """Return three distinct custom MDL specs and matching true-color BLP1 textures."""
    mdl_specs: Dict[str, str] = {}
    textures: Dict[str, bytes] = {}
    for model_name, kind in NAGA_BUILDING_MODEL_DEFS:
        texture_path = f"Textures\\{model_name.removesuffix('.mdx')}.blp"
        mdl_specs[model_name] = _generate_naga_building_mdl(model_name, texture_path, kind)
        textures[texture_path] = build_naga_building_texture(kind)
    geometry_signatures = {
        name: re.search(r"Geoset \{.*?\n\}", text, re.DOTALL).group(0)
        for name, text in mdl_specs.items()
    }
    if len(set(geometry_signatures.values())) != len(NAGA_BUILDING_MODEL_DEFS):
        raise AssertionError("Naga building models must have distinct geometric meshes")
    return mdl_specs, textures


def _rotate_xy(x: float, y: float, angle: float) -> Tuple[float, float]:
    return (x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle))


def _generate_vfx_mdl(
    model_name: str,
    tex_path: str,
    shape: str = "sigil",
    variation: int = 0,
) -> str:
    """Generate a version-800 additive MDL with shape-specific, varied 3D geometry."""
    if shape not in ("sigil", "burst", "bolt", "shield", "portal"):
        raise ValueError(f"unsupported VFX geometry: {shape}")
    hero_index = variation // 4
    phase = math.radians((hero_index * 17 + variation * 13) % 360)
    outer = 112.0 + (variation % 13) * 4.0
    inner = outer * (0.42 + (variation % 5) * 0.035)
    geo0_vertices: List[Tuple[float, float, float]] = []
    geo0_uvs: List[Tuple[float, float]] = []
    geo0_faces: List[int] = []
    if shape in ("burst", "sigil"):
        n = 7 + (variation % 8)
        geo0_vertices.append((0.0, 0.0, 8.0))
        geo0_uvs.append((0.5,0.5))
        boundary = []
        for k in range(n * 2):
            radius = outer if k % 2 == 0 else inner
            theta = phase + math.tau * k / (n * 2)
            boundary.append((math.cos(theta)*radius, math.sin(theta)*radius, 8.0))
        geo0_vertices.extend(boundary)
        for x,y,_ in boundary:
            u = max(0.0, min(1.0, 0.5 + x/(2*outer)))
            v = max(0.0, min(1.0, 0.5 + y/(2*outer)))
            geo0_uvs.append((u, v))
        for k in range(len(boundary)):
            geo0_faces.extend((0, 1+k, 1+((k+1)%len(boundary))))
    elif shape == "bolt":
        length = outer * (1.30 + (variation % 7) * 0.07)
        width = 18.0 + (variation % 9) * 4.0
        local = [(-length,-width),(-length*0.45,-width*0.58),(length*0.72,-width*0.44),(length,width),
                 (length*0.25,width*0.52),(-length*0.62,width*0.42)]
        points = [_rotate_xy(x,y,phase) for x,y in local]
        geo0_vertices = [(0.0,0.0,8.0)] + [(x,y,8.0) for x,y in points]
        geo0_uvs = [(0.5,0.5)] + [(max(0.0,min(1.0,0.5+x/(2*length))),max(0.0,min(1.0,0.5+y/(2*length)))) for x,y in points]
        for k in range(len(points)):
            geo0_faces.extend((0,1+k,1+((k+1)%len(points))))
    elif shape == "shield":
        w = outer * (0.70 + (variation % 5) * 0.04)
        h = outer * (0.92 + (variation % 7) * 0.055)
        local = [(-w,-h*0.58),(0.0,-h),(w,-h*0.58),(w*0.72,h*0.16),(0.0,h),(-w*0.72,h*0.16)]
        points = [_rotate_xy(x,y,phase*0.35) for x,y in local]
        geo0_vertices = [(0.0,0.0,8.0)] + [(x,y,8.0) for x,y in points]
        geo0_uvs = [(0.5,0.5)] + [(max(0.0,min(1.0,0.5+x/(2*w))),max(0.0,min(1.0,0.5+y/(2*h)))) for x,y in points]
        for k in range(len(points)):
            geo0_faces.extend((0,1+k,1+((k+1)%len(points))))
    else:  # portal: a real annulus, not a flat square with a new hue
        n = 8 + (variation % 7)
        rot = phase * 0.5
        for radius in (outer, inner):
            for k in range(n):
                theta = rot + math.tau*k/n
                x, y = math.cos(theta)*radius, math.sin(theta)*radius
                geo0_vertices.append((x,y,8.0))
                geo0_uvs.append((0.5+x/(2*outer),0.5+y/(2*outer)))
        for k in range(n):
            nxt = (k+1)%n
            geo0_faces.extend((k,nxt,n+nxt,k,n+nxt,n+k))

    # Geoset 1 is a 3D beam, shield wall, or portal ring according to the skill slot.
    geo1_vertices: List[Tuple[float, float, float]] = []
    geo1_uvs: List[Tuple[float, float]] = []
    geo1_faces: List[int] = []
    geo1_normal = (0.0,-1.0,0.0)
    height = 154.0 + (variation % 17) * 8.0
    if shape in ("burst", "sigil", "bolt"):
        planes = 3 if shape in ("burst", "sigil") else 2
        for plane in range(planes):
            theta = phase + math.pi*plane/planes
            half = (28.0 + (variation % 11)*2.1) if shape != "bolt" else (12.0 + (variation % 9)*1.7)
            h = height if shape != "bolt" else height * (0.62 + (variation % 5)*0.04)
            dx,dy = -math.sin(theta), math.cos(theta)
            cx,cy = math.cos(theta)*12.0, math.sin(theta)*12.0
            local_verts = [
                (cx-dx*half,cy-dy*half,12.0), (cx+dx*half,cy+dy*half,12.0),
                (cx+dx*half*0.42,cy+dy*half*0.42,h), (cx-dx*half*0.42,cy-dy*half*0.42,h),
            ]
            base = len(geo1_vertices)
            geo1_vertices.extend(local_verts)
            geo1_uvs.extend(((0,0),(1,0),(1,1),(0,1)))
            geo1_faces.extend((base,base+1,base+2,base,base+2,base+3))
    elif shape == "shield":
        n = 6
        for plane in range(2):
            theta = phase*0.35 + math.pi*plane/2
            half_w = outer*0.55
            half_h = height*0.48
            local = [(-half_w,-half_h*0.58),(0,-half_h),(half_w,-half_h*0.58),
                     (half_w*0.72,half_h*0.16),(0,half_h),(-half_w*0.72,half_h*0.16)]
            base = len(geo1_vertices)
            geo1_vertices.append((math.cos(theta)*10.0,math.sin(theta)*10.0,height*0.52))
            geo1_uvs.append((0.5,0.5))
            for x,z in local:
                geo1_vertices.append((x*math.cos(theta),x*math.sin(theta),height*0.52+z))
                u = max(0.0, min(1.0, 0.5 + x/(2*half_w)))
                v = max(0.0, min(1.0, 0.5 + z/(2*half_h)))
                geo1_uvs.append((u, v))
            for k in range(n):
                geo1_faces.extend((base,base+1+k,base+1+((k+1)%n)))
    else:
        n = 8 + (variation % 7)
        outer_r = 50.0 + (variation % 11)*4.0
        inner_r = outer_r*(0.58 + (variation % 5)*0.035)
        for plane in range(2):
            theta0 = phase*0.5 + math.pi*plane/2
            base = len(geo1_vertices)
            for radius in (outer_r,inner_r):
                for k in range(n):
                    a = math.tau*k/n
                    horizontal = math.sin(a)*radius
                    z = height*0.55 + math.cos(a)*radius
                    geo1_vertices.append((math.cos(theta0)*horizontal,math.sin(theta0)*horizontal,z))
                    geo1_uvs.append((0.5+math.sin(a)*0.46,0.5+math.cos(a)*0.46))
            for k in range(n):
                nxt=(k+1)%n
                geo1_faces.extend((base+k,base+nxt,base+n+nxt,base+k,base+n+nxt,base+n+k))

    # Normals are planar; additive two-sided layers make every silhouette visible from either side.
    geo0_normals = [(0.0,0.0,1.0)] * len(geo0_vertices)
    geo1_normals = [geo1_normal] * len(geo1_vertices)
    extent_xy = max(outer * 1.8, 300.0 if shape == "bolt" else outer * 1.4)
    max_z = max(height + 20.0, 250.0)
    min0 = (-extent_xy,-extent_xy,0.0)
    max0 = (extent_xy,extent_xy,12.0)
    min1 = (-extent_xy,-extent_xy,0.0)
    max1 = (extent_xy,extent_xy,max_z)
    model_extent = max(extent_xy,max_z)
    geoset0 = _make_vfx_geoset(geo0_vertices,geo0_normals,geo0_uvs,geo0_faces,min0,max0,model_extent)
    geoset1 = _make_vfx_geoset(geo1_vertices,geo1_normals,geo1_uvs,geo1_faces,min1,max1,model_extent)
    return f"""Version {{
    FormatVersion 800,
}}
Model "{model_name}" {{
    NumGeosets 2,
    NumGeosetAnims 2,
    NumBones 2,
    BlendTime 150,
    MinimumExtent {{ {-extent_xy:.3f}, {-extent_xy:.3f}, 0 }},
    MaximumExtent {{ {extent_xy:.3f}, {extent_xy:.3f}, {max_z:.3f} }},
    BoundsRadius {model_extent:.3f},
}}
Sequences 3 {{
    Anim "Birth" {{
        Interval {{ 0, 450 }},
        NonLooping,
        MinimumExtent {{ {-extent_xy:.3f}, {-extent_xy:.3f}, 0 }},
        MaximumExtent {{ {extent_xy:.3f}, {extent_xy:.3f}, {max_z:.3f} }},
        BoundsRadius {model_extent:.3f},
    }}
    Anim "Stand" {{
        Interval {{ 500, 1500 }},
        MinimumExtent {{ {-extent_xy:.3f}, {-extent_xy:.3f}, 0 }},
        MaximumExtent {{ {extent_xy:.3f}, {extent_xy:.3f}, {max_z:.3f} }},
        BoundsRadius {model_extent:.3f},
    }}
    Anim "Death" {{
        Interval {{ 1600, 2200 }},
        NonLooping,
        MinimumExtent {{ {-extent_xy:.3f}, {-extent_xy:.3f}, 0 }},
        MaximumExtent {{ {extent_xy:.3f}, {extent_xy:.3f}, {max_z:.3f} }},
        BoundsRadius {model_extent:.3f},
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
{geoset0}
{geoset1}
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

def compile_vfx_mdx_models(mdl_map: Dict[str, str], expected_geosets: int = 2) -> Dict[str, bytes]:
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
                if (check.version !== 800 || check.sequences.length !== 3 || check.geosets.length !== {expected_geosets}) {{
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
    """Build `{mpq_archive_path: binary_bytes}` for the v7 custom asset bundle."""
    files: Dict[str, bytes] = {}

    # 1. Lobby map preview and patch-safe custom cursor atlases.
    files["war3mapPreview.tga"] = build_war3map_preview_tga()
    cursor_img = build_custom_cursor_atlas_img()
    cursor_blp = encode_blp1_truecolor(cursor_img)
    for race_cur in ("HumanCursor", "OrcCursor", "UndeadCursor", "NightElfCursor"):
        files[f"UI\\Cursor\\{race_cur}.blp"] = cursor_blp

    # 2. Existing custom RPG infocard and console/resource textures.
    infocard_blps, _infocard_samples = build_infocard_icons()
    files.update(infocard_blps)
    files.update(build_ui_resource_textures())

    # 3. Ten full-bleed hero portraits; all remaining unit buttons use native WC3 art.
    hero_blps, hero_samples = build_hero_portrait_assets()
    files.update(hero_blps)

    # 4. Additive faction sigils plus 64 distinct skill-specific spell models.
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

    spell_geometry_signatures = set()
    for ability_index in range(64):
        suffix = f"{ability_index:02d}"
        mdx_name = f"WM_Skill_{suffix}.mdx"
        tex_path = f"Textures\\WM_Skill_{suffix}.blp"
        shape = SPELL_FX_SHAPES[ability_index % 4]
        files[tex_path] = build_spell_vfx_texture(ability_index)
        mdl_text = _generate_vfx_mdl(mdx_name[:-4], tex_path, shape=shape, variation=ability_index)
        geo_start = mdl_text.index("Geoset {")
        geo_end = mdl_text.index("GeosetAnim", geo_start)
        spell_geometry_signatures.add(mdl_text[geo_start:geo_end])
        mdl_specs[mdx_name] = mdl_text
    if len(spell_geometry_signatures) != 64:
        raise AssertionError(f"skill VFX geometry is not unique ({len(spell_geometry_signatures)}/64)")
    files.update(compile_vfx_mdx_models(mdl_specs))

    # 4.5. Naga role-specific buildings replace the old duplicate Shrine/Altar/Spawning models.
    building_mdl_specs, building_textures = build_naga_building_model_specs()
    files.update(building_textures)
    files.update(compile_vfx_mdx_models(building_mdl_specs, expected_geosets=1))

    # 5. The web preview showcases the custom portrait work, not licensed stock icons.
    if save_web_sheet:
        save_hero_portrait_preview(hero_samples)

    return files

if __name__ == "__main__":
    bundle = generate_all_custom_assets()
    total = sum(len(v) for v in bundle.values())
    print(f"Generated {len(bundle)} custom v7 assets ({total:,} bytes raw)")
