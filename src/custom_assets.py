#!/usr/bin/env python3
"""
Artwork and UI asset pipeline for `(8) Crown of WarMahdi` v5.

Generates Warcraft III binary assets while keeping gameplay art recognizable and
patch-safe:
  1. A 256x256 lobby preview TGA derived from the map's custom artwork.
  2. Four compatible animated cursor texture atlases.
  3. RPG infocard, resource and console textures for the existing in-game UI.
  4. Ten AI-generated 64x64 hero portrait BLPs from source art in
     `src/assets/hero_portraits/`; other heroes use authentic native WC3 portraits.
  5. Six additive sigil textures and six version-800 spell-effect MDX models,
     compiled and roundtrip-checked with `mdx-m3-viewer`.

Hero/unit/building buttons inherit recognizable stock Warcraft III artwork. The 64
custom skills use native command-button icons selected to match their effects; no
procedurally drawn geometric icons are imported for those gameplay objects.
"""

from __future__ import annotations

import math
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
    return encode_blp1_truecolor(img)


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
    """Build `{mpq_archive_path: binary_bytes}` for the v5 custom asset bundle."""
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

    # 4. Additive faction sigils and their six compiled, roundtrip-verified MDX effects.
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

    # 5. The web preview showcases the custom portrait work, not licensed stock icons.
    if save_web_sheet:
        save_hero_portrait_preview(hero_samples)

    return files

if __name__ == "__main__":
    bundle = generate_all_custom_assets()
    total = sum(len(v) for v in bundle.values())
    print(f"Generated {len(bundle)} custom v5 assets ({total:,} bytes raw)")
