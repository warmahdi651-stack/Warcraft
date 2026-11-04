#!/usr/bin/env python3
"""
Procedural & Artwork Asset Pipeline for `(8) Crown of WarMahdi` v3.

Generates and validates 100% custom, non-vanilla Warcraft III binary assets:
  1. `war3mapPreview.tga` (256x256 uncompressed 24-bit TrueColor TGA derived from
     `web/public/crown_artwork.png` with ornate astral-gold frame & badge).
  2. 18 Custom `64x64` Paletted `BLP1` Command Icons (`BTN_WM_*.blp` + matching
     `DISBTN_WM_*.blp` = 36 `.blp` icons) for all 16 custom Hero skills, the
     Crown Crest icon, and the Faction Tome/Reroll icon — zero vanilla WC3 art!
  3. Custom Non-Classic UI Skin `.blp` textures (`UI\\CrownUI\\MenuBG.blp`,
     `IconGold.blp`, `IconLumber.blp`, `IconSupply.blp`) to replace classic dialog
     backgrounds and resource bar icons cleanly in 1.26a/1.27b & Reforged.
  4. 4 Custom `128x128` Additive Arcane/Runic Sigil `.blp` textures
     (`Textures\\WM_Sigil_*.blp`) + 4 Custom Multi-Geoset 3D `.mdx` (`Version 800`)
     spell VFX models (`WM_FX_Abyssal.mdx`, `WM_FX_Solar.mdx`, `WM_FX_Void.mdx`,
     `WM_FX_Runic.mdx`) compiled via `mdx-m3-viewer`.
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
MDX_MODEL_JS = Path("/tmp/wc3ref/node_modules/mdx-m3-viewer/dist/cjs/parsers/mdlx/model")


# ==============================================================================
# 1. LOSSLESS / MIPMAPPED PALETTED BLP1 & UNCOMPRESSED 24-BIT TGA WRITERS
# ==============================================================================

def encode_tga_24bit(img: Image.Image) -> bytes:
    """
    Encode an RGB PIL Image into a standard bottom-up 24-bit uncompressed TGA
    (`war3mapPreview.tga` format required by Warcraft III 1.26a/1.27b & Reforged).
    """
    rgb = img.convert("RGB")
    w, h = rgb.size
    header = struct.pack(
        "<BBBHHBHHHHBB",
        0,      # id_length
        0,      # color_map_type
        2,      # image_type = 2 (Uncompressed True-Color)
        0, 0, 0,
        0, 0,   # x_origin, y_origin
        w, h,
        24,     # 24 bits per pixel (BGR)
        0x00,   # bottom-up origin (standard WC3 TGA)
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
    texture with full mipmap chain (`max(w,h)` down to `1x1`) and 8-bit alpha.
    """
    rgba = img.convert("RGBA")
    w, h = rgba.size
    assert (w & (w - 1)) == 0 and (h & (h - 1)) == 0, f"BLP size must be power-of-2: {w}x{h}"

    # Quantize RGB across level-0 using Adaptive 256-color palette
    rgb0 = rgba.convert("RGB")
    pal_img = rgb0.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    raw_pal = pal_img.getpalette() or []
    # Pad palette to 256 * 3
    while len(raw_pal) < 768:
        raw_pal.extend((0, 0, 0))

    # Build 1024-byte BGRA palette
    palette_bytes = bytearray(1024)
    for i in range(256):
        r = raw_pal[i * 3]
        g = raw_pal[i * 3 + 1]
        b = raw_pal[i * 3 + 2]
        palette_bytes[i * 4 + 0] = b
        palette_bytes[i * 4 + 1] = g
        palette_bytes[i * 4 + 2] = r
        palette_bytes[i * 4 + 3] = 0

    # Generate full mipmap chain down to 1x1
    num_mips = int(math.log2(max(w, h))) + 1
    mip_blobs: List[bytes] = []
    for lvl in range(num_mips):
        mw = max(1, w >> lvl)
        mh = max(1, h >> lvl)
        m_rgba = rgba if lvl == 0 else rgba.resize((mw, mh), Image.Resampling.LANCZOS)
        m_rgb = m_rgba.convert("RGB")
        # Quantize against exact level-0 palette so indices match `palette_bytes`
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
        1,                      # content = 1 (Paletted)
        8 if alpha_bits == 8 else 0,
        w,
        h,
        5,                      # type = 5
        1,                      # hasMipmaps = 1
        *offsets,
        *sizes,
    )
    assert len(header) == 156
    return header + bytes(palette_bytes) + b"".join(mip_blobs)


# ==============================================================================
# 2. WC3 COMMAND BUTTON BEVEL & DISABLED (`DISBTN`) STYLING
# ==============================================================================

def apply_btn_frame(core: Image.Image, accent_rgb: Tuple[int, int, int]) -> Tuple[Image.Image, Image.Image]:
    """
    Wrap a `64x64` custom skill illustration in a sleek non-classic obsidian-metallic
    command button bevel (`BTN`) AND produce the darkened/desaturated Warcraft III
    disabled state (`DISBTN`) required for dialogs, pause screens & unlearned skills.
    """
    btn = core.convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(btn)
    ar, ag, ab = accent_rgb

    # Outer dark border + crisp metallic inner bevel tinted with faction accent
    draw.rectangle([0, 0, 63, 63], outline=(10, 12, 18, 255), width=1)
    draw.rectangle(
        [1, 1, 62, 62],
        outline=(min(255, int(ar * 0.55 + 55)), min(255, int(ag * 0.55 + 55)), min(255, int(ab * 0.55 + 55)), 255),
        width=1,
    )
    draw.rectangle(
        [2, 2, 61, 61],
        outline=(min(255, int(ar * 0.85 + 75)), min(255, int(ag * 0.85 + 75)), min(255, int(ab * 0.85 + 75)), 255),
        width=1,
    )
    draw.rectangle([3, 3, 60, 60], outline=(18, 22, 32, 230), width=1)
    # Subtle corner gem rivets
    for cx, cy in ((3, 3), (60, 3), (3, 60), (60, 60)):
        draw.point((cx, cy), fill=(245, 235, 195, 255))

    # Build DISBTN (borderless, desaturated 45%, darkened 48% with smooth 4px edge vignette)
    dis_rgb = ImageEnhance.Color(core.convert("RGB").resize((64, 64), Image.Resampling.LANCZOS)).enhance(0.38)
    dis_rgb = ImageEnhance.Brightness(dis_rgb).enhance(0.46)
    dis = dis_rgb.convert("RGBA")
    px = dis.load()
    for y in range(64):
        for x in range(64):
            edge = min(x, y, 63 - x, 63 - y)
            if edge < 4:
                fade = (edge + 0.5) / 4.5
                r, g, b, a = px[x, y]
                px[x, y] = (int(r * fade), int(g * fade), int(b * fade), 255)
    return btn, dis


# ==============================================================================
# 3. PROCEDURAL HIGH-CONTRAST DIGITAL ART PAINTER FOR ALL 18 CUSTOM ICONS
# ==============================================================================

def _make_radial_bg(
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
                u = t * 2.0
                r = int(inner_rgb[0] * (1 - u) + mid_rgb[0] * u)
                g = int(inner_rgb[1] * (1 - u) + mid_rgb[1] * u)
                b = int(inner_rgb[2] * (1 - u) + mid_rgb[2] * u)
            else:
                u = (t - 0.5) * 2.0
                r = int(mid_rgb[0] * (1 - u) + outer_rgb[0] * u)
                g = int(mid_rgb[1] * (1 - u) + outer_rgb[1] * u)
                b = int(mid_rgb[2] * (1 - u) + outer_rgb[2] * u)
            px[x, y] = (r, g, b, 255)
    return img


def paint_skill_icon(kind: str) -> Tuple[Image.Image, Tuple[int, int, int]]:
    """
    Paint a supersampled `128x128` original fantasy/arcane emblem for `kind`,
    then downsample cleanly to `64x64`. Zero Blizzard/WC3 icon assets used.
    """
    S = 128
    cx = cy = 64.0

    # Palettes per faction
    palettes = {
        "abyss": ((185, 255, 255), (14, 155, 195), (6, 20, 42), (56, 225, 248)),
        "solar": ((255, 252, 210), (235, 125, 18), (38, 12, 8), (251, 191, 36)),
        "void":  ((242, 210, 255), (138, 43, 226), (16, 6, 32), (192, 108, 255)),
        "runic": ((215, 248, 255), (195, 130, 42), (18, 22, 30), (96, 215, 255)),
    }

    if kind.startswith("Abyss"):
        inner, mid, outer, accent = palettes["abyss"]
    elif kind.startswith("Solar"):
        inner, mid, outer, accent = palettes["solar"]
    elif kind.startswith("Void"):
        inner, mid, outer, accent = palettes["void"]
    elif kind.startswith("Runic"):
        inner, mid, outer, accent = palettes["runic"]
    else:
        inner, mid, outer, accent = ((255, 245, 200), (168, 85, 247), (14, 16, 32), (245, 195, 66))

    base = _make_radial_bg(S, mid, outer, (5, 7, 14))
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    fg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)

    if kind == "AbyssVortex":
        # Spiraling bioluminescent cyan maelstrom vortex
        for arm in range(5):
            base_a = arm * (2 * math.pi / 5)
            pts = []
            for step in range(28):
                t = step / 27.0
                r = 8 + t * 48
                ang = base_a + t * 2.6
                pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
            gd.line(pts, fill=(34, 211, 238, 220), width=8)
            fd.line(pts, fill=(220, 255, 255, 255), width=3)
        gd.ellipse([44, 44, 84, 84], fill=(56, 235, 255, 235))
        fd.ellipse([52, 52, 76, 76], fill=(245, 255, 255, 255))

    elif kind == "AbyssLance":
        # Crystalline trident prism lance splitting into 3 cyan beams
        gd.line([(18, 110), (106, 22)], fill=(34, 211, 238, 240), width=14)
        fd.line([(18, 110), (106, 22)], fill=(235, 255, 255, 255), width=5)
        for dx, dy in ((-22, 4), (4, 22)):
            gd.line([(68, 60), (106 + dx, 22 + dy)], fill=(56, 189, 248, 210), width=9)
            fd.line([(68, 60), (106 + dx, 22 + dy)], fill=(225, 252, 255, 255), width=3)
        fd.polygon([(112, 16), (92, 24), (104, 36)], fill=(255, 255, 255, 255))

    elif kind == "AbyssCarapace":
        # Glowing hexagonal leviathan energy shield + pulse rings
        gd.ellipse([20, 20, 108, 108], outline=(34, 211, 238, 200), width=8)
        hex_pts = [(cx + math.cos(i * math.pi / 3 - math.pi / 2) * 38,
                    cy + math.sin(i * math.pi / 3 - math.pi / 2) * 38) for i in range(6)]
        gd.polygon(hex_pts, fill=(14, 165, 215, 190), outline=(125, 245, 255, 255))
        fd.line(hex_pts + [hex_pts[0]], fill=(235, 255, 255, 255), width=4)
        fd.polygon([(64, 38), (82, 64), (64, 90), (46, 64)], fill=(220, 255, 255, 245))

    elif kind == "AbyssTsunami":
        # Triple concentric tidal crown wave crest + lightning core
        for r, w_a in ((48, 7), (34, 6), (20, 5)):
            gd.arc([cx - r, cy - r, cx + r, cy + r], 195, 345, fill=(56, 235, 255, 235), width=w_a + 5)
            fd.arc([cx - r, cy - r, cx + r, cy + r], 195, 345, fill=(240, 255, 255, 255), width=w_a)
        crown = [(26, 86), (38, 48), (52, 70), (64, 30), (76, 70), (90, 48), (102, 86)]
        gd.line(crown, fill=(34, 211, 238, 240), width=9)
        fd.line(crown, fill=(255, 255, 255, 255), width=4)

    elif kind == "SolarSigil":
        # 8-pointed blazing golden sun mandala
        for i in range(8):
            ang = i * math.pi / 4
            p1 = (cx + math.cos(ang) * 52, cy + math.sin(ang) * 52)
            p2 = (cx + math.cos(ang + 0.24) * 26, cy + math.sin(ang + 0.24) * 26)
            p3 = (cx + math.cos(ang - 0.24) * 26, cy + math.sin(ang - 0.24) * 26)
            gd.polygon([p1, p2, p3], fill=(251, 146, 60, 235))
            fd.polygon([p1, p2, p3], fill=(255, 238, 170, 255))
        gd.ellipse([36, 36, 92, 92], fill=(245, 158, 11, 245))
        fd.ellipse([45, 45, 83, 83], fill=(255, 252, 225, 255))

    elif kind == "SolarDash":
        # Blazing golden phoenix wings surging upward
        left_wing = [(64, 78), (20, 34), (26, 68), (18, 92), (54, 88)]
        right_wing = [(64, 78), (108, 34), (102, 68), (110, 92), (74, 88)]
        gd.polygon(left_wing, fill=(249, 115, 22, 235))
        gd.polygon(right_wing, fill=(249, 115, 22, 235))
        fd.polygon(left_wing, fill=(253, 224, 71, 245))
        fd.polygon(right_wing, fill=(253, 224, 71, 245))
        fd.polygon([(64, 18), (76, 62), (64, 104), (52, 62)], fill=(255, 255, 235, 255))

    elif kind == "SolarJudgment":
        # Converging radiant golden sunblade cross
        gd.polygon([(64, 12), (75, 84), (64, 114), (53, 84)], fill=(251, 146, 60, 240))
        gd.line([(28, 52), (100, 52)], fill=(251, 146, 60, 240), width=14)
        fd.polygon([(64, 14), (71, 84), (64, 110), (57, 84)], fill=(255, 252, 220, 255))
        fd.line([(30, 52), (98, 52)], fill=(255, 245, 190, 255), width=6)
        fd.ellipse([54, 42, 74, 62], fill=(255, 255, 255, 255))

    elif kind == "SolarSupernova":
        # Multi-ring golden supernova crown explosion
        gd.ellipse([16, 16, 112, 112], outline=(249, 115, 22, 220), width=10)
        for i in range(12):
            ang = i * math.pi / 6
            r_out = 56 if i % 2 == 0 else 40
            gd.line([(cx, cy), (cx + math.cos(ang) * r_out, cy + math.sin(ang) * r_out)],
                    fill=(251, 191, 36, 240), width=8)
            fd.line([(cx, cy), (cx + math.cos(ang) * (r_out - 4), cy + math.sin(ang) * (r_out - 4))],
                    fill=(255, 253, 230, 255), width=3)
        fd.ellipse([42, 42, 86, 86], fill=(255, 250, 215, 255))

    elif kind == "VoidHorizon":
        # Accretion disc + black-violet event horizon singularity
        gd.ellipse([16, 36, 112, 92], outline=(192, 108, 255, 245), width=14)
        fd.ellipse([20, 40, 108, 88], outline=(245, 215, 255, 255), width=5)
        gd.ellipse([34, 34, 94, 94], outline=(168, 85, 247, 240), width=10)
        fd.ellipse([42, 42, 86, 86], fill=(8, 3, 18, 255), outline=(235, 195, 255, 255), width=4)

    elif kind == "VoidSever":
        # Dimensional X-slash tearing open a violet astral rift
        gd.polygon([(16, 22), (68, 56), (112, 106), (60, 72)], fill=(192, 108, 255, 245))
        gd.polygon([(108, 24), (68, 68), (20, 106), (58, 58)], fill=(147, 51, 234, 235))
        fd.line([(20, 24), (108, 104)], fill=(250, 235, 255, 255), width=6)
        fd.line([(104, 26), (24, 102)], fill=(240, 210, 255, 255), width=4)

    elif kind == "VoidShroud":
        # Rotating octagonal astral star-ring & void eye
        for rot in (0.0, math.pi / 4):
            sq = [(cx + math.cos(rot + i * math.pi / 2) * 44,
                   cy + math.sin(rot + i * math.pi / 2) * 44) for i in range(4)]
            gd.polygon(sq, outline=(192, 108, 255, 235), width=7)
            fd.line(sq + [sq[0]], fill=(242, 220, 255, 255), width=3)
        fd.ellipse([46, 52, 82, 76], fill=(235, 195, 255, 255))
        fd.ellipse([58, 56, 70, 72], fill=(22, 6, 42, 255))

    elif kind == "VoidCollapse":
        # Cosmic implosion — 8 inward converging void lances + bright star core
        for i in range(8):
            ang = i * math.pi / 4 + 0.2
            x0, y0 = cx + math.cos(ang) * 56, cy + math.sin(ang) * 56
            x1, y1 = cx + math.cos(ang) * 18, cy + math.sin(ang) * 18
            gd.line([(x0, y0), (x1, y1)], fill=(192, 108, 255, 245), width=9)
            fd.line([(x0, y0), (x1, y1)], fill=(250, 235, 255, 255), width=3)
        gd.ellipse([38, 38, 90, 90], fill=(168, 85, 247, 245))
        fd.ellipse([50, 50, 78, 78], fill=(255, 245, 255, 255))

    elif kind == "RunicTectonics":
        # Titan war-rune hammer + radial cyan-gold shockwave fractures
        for ang in (-2.4, -1.8, -0.9, -0.3, 0.4, 1.1):
            gd.line([(64, 80), (64 + math.cos(ang) * 50, 80 + math.sin(ang) * 44)],
                    fill=(56, 215, 255, 230), width=7)
            fd.line([(64, 80), (64 + math.cos(ang) * 48, 80 + math.sin(ang) * 42)],
                    fill=(225, 252, 255, 255), width=3)
        gd.rectangle([34, 26, 94, 58], fill=(217, 145, 42, 255), outline=(255, 235, 175, 255), width=3)
        fd.rectangle([58, 58, 70, 104], fill=(205, 155, 85, 255))
        fd.line([(44, 42), (84, 42)], fill=(180, 250, 255, 255), width=5)

    elif kind == "RunicOverload":
        # Glowing cyan-gold arc reactor core with 3 orbital lightning arcs
        gd.ellipse([24, 24, 104, 104], outline=(245, 178, 56, 240), width=10)
        gd.ellipse([38, 38, 90, 90], fill=(34, 211, 238, 245))
        fd.ellipse([46, 46, 82, 82], fill=(235, 255, 255, 255))
        for i in range(6):
            ang = i * math.pi / 3
            fd.line([(cx + math.cos(ang) * 26, cy + math.sin(ang) * 26),
                     (cx + math.cos(ang) * 48, cy + math.sin(ang) * 48)],
                    fill=(255, 225, 130, 255), width=5)

    elif kind == "RunicAegis":
        # Interlocking bronze-cyan runic gear & hexagonal forcefield
        for i in range(12):
            ang = i * math.pi / 6
            x1, y1 = cx + math.cos(ang) * 48, cy + math.sin(ang) * 48
            gd.ellipse([x1 - 7, y1 - 7, x1 + 7, y1 + 7], fill=(217, 145, 42, 245))
        gd.ellipse([24, 24, 104, 104], outline=(245, 195, 85, 255), width=9)
        hex_pts = [(cx + math.cos(i * math.pi / 3) * 30, cy + math.sin(i * math.pi / 3) * 30) for i in range(6)]
        gd.polygon(hex_pts, fill=(14, 165, 215, 220))
        fd.line(hex_pts + [hex_pts[0]], fill=(230, 255, 255, 255), width=4)

    elif kind == "RunicOrbital":
        # Orbital sky-beam pillar + concentric targeting reticle
        gd.ellipse([20, 62, 108, 110], outline=(56, 225, 255, 240), width=8)
        fd.ellipse([32, 70, 96, 102], outline=(255, 225, 140, 255), width=4)
        gd.rectangle([48, 8, 80, 92], fill=(56, 225, 255, 235))
        fd.rectangle([55, 8, 73, 90], fill=(245, 255, 255, 255))

    elif kind == "CrownCrest":
        # Crop & enhance center shrine/crown directly from our generated artwork if present
        if ARTWORK_PNG.exists():
            art = Image.open(ARTWORK_PNG).convert("RGBA")
            aw, ah = art.size
            crop = art.crop((int(aw * 0.22), int(ah * 0.04), int(aw * 0.78), int(ah * 0.60))).resize(
                (64, 64), Image.Resampling.LANCZOS
            )
            crop = ImageEnhance.Contrast(crop).enhance(1.18)
            return crop, (245, 195, 66)
        crown = [(20, 90), (28, 42), (48, 66), (64, 24), (80, 66), (100, 42), (108, 90)]
        gd.polygon(crown, fill=(245, 185, 42, 245))
        fd.line(crown + [crown[0]], fill=(255, 248, 210, 255), width=4)

    elif kind == "FactionTome":
        # Glowing 4-quadrant astral-solar-abyssal-runic crystal star
        quads = [
            ([(64, 14), (78, 52), (64, 64), (50, 52)], (251, 191, 36, 255)),
            ([(114, 64), (76, 78), (64, 64), (76, 50)], (192, 108, 255, 255)),
            ([(64, 114), (50, 76), (64, 64), (78, 76)], (34, 211, 238, 255)),
            ([(14, 64), (52, 50), (64, 64), (52, 78)], (245, 158, 11, 255)),
        ]
        for poly, col in quads:
            gd.polygon(poly, fill=col)
            fd.line(poly + [poly[0]], fill=(255, 255, 255, 240), width=3)
        fd.ellipse([54, 54, 74, 74], fill=(255, 255, 255, 255))

    glow = glow.filter(ImageFilter.GaussianBlur(radius=4.2))
    comp = Image.alpha_composite(base, glow)
    comp = Image.alpha_composite(comp, fg)
    return comp.resize((64, 64), Image.Resampling.LANCZOS), accent


# ==============================================================================
# 4. CUSTOM UI SKIN TEXTURES + ADDITIVE 3D SPELL SIGIL TEXTURES + `.mdx` COMPILER
# ==============================================================================

def build_ui_textures() -> Dict[str, bytes]:
    """
    Generate non-classic Dark Astral-Obsidian UI background & resource bar icons
    referenced by `war3mapSkin.txt`.
    """
    out: Dict[str, bytes] = {}

    # 1. `UI\CrownUI\MenuBG.blp` (128x128 seamless dark obsidian-astral runic panel)
    bg = Image.new("RGBA", (128, 128), (11, 15, 28, 248))
    d = ImageDraw.Draw(bg)
    for y in range(0, 128, 16):
        col = (18, 25, 44, 248) if (y // 16) % 2 == 0 else (13, 18, 33, 248)
        d.rectangle([0, y, 127, y + 15], fill=col)
    # Subtle geometric diamond filigree so tiled dialogs look sleek & regal
    for gy in (32, 96):
        for gx in (32, 96):
            pts = [(gx, gy - 22), (gx + 22, gy), (gx, gy + 22), (gx - 22, gy)]
            d.polygon(pts, outline=(46, 68, 112, 150), width=1)
            pts2 = [(gx, gy - 10), (gx + 10, gy), (gx, gy + 10), (gx - 10, gy)]
            d.polygon(pts2, outline=(168, 132, 56, 115), width=1)
    out["UI\\CrownUI\\MenuBG.blp"] = encode_blp1_paletted(bg, alpha_bits=8)

    # 2. Custom Resource Header Icons (`32x32` crisp transparent icons)
    # Gold Coin -> Astral Sun-Crown Coin
    gold = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gold)
    gd.ellipse([3, 3, 28, 28], fill=(217, 119, 6, 255), outline=(254, 240, 138, 255), width=2)
    gd.polygon([(9, 20), (11, 11), (16, 15), (21, 11), (23, 20)], fill=(255, 251, 215, 255))
    out["UI\\CrownUI\\IconGold.blp"] = encode_blp1_paletted(gold, alpha_bits=8)

    # Lumber -> Bioluminescent Cyan-Emerald Rune Crystal
    lum = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lum)
    ld.polygon([(16, 2), (27, 12), (23, 29), (9, 29), (5, 12)],
               fill=(16, 185, 129, 255), outline=(167, 243, 208, 255), width=2)
    ld.polygon([(16, 6), (22, 14), (16, 25), (10, 14)], fill=(165, 243, 252, 245))
    out["UI\\CrownUI\\IconLumber.blp"] = encode_blp1_paletted(lum, alpha_bits=8)

    # Supply / Upkeep -> Violet-Gold Imperial Star Crest
    sup = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sup)
    sd.polygon([(16, 2), (28, 9), (25, 24), (16, 30), (7, 24), (4, 9)],
               fill=(124, 58, 237, 255), outline=(253, 224, 71, 255), width=2)
    sd.polygon([(16, 7), (20, 15), (16, 24), (12, 15)], fill=(254, 249, 195, 255))
    out["UI\\CrownUI\\IconSupply.blp"] = encode_blp1_paletted(sup, alpha_bits=8)

    return out


def build_sigil_texture(primary: Tuple[int, int, int], core_col: Tuple[int, int, int], spikes: int) -> bytes:
    """
    Create a `128x128` radial sacred-geometry sigil texture (`FilterMode Additive`,
    black edge = 100% transparent in WC3 Additive blending!) for custom `.mdx` VFX.
    """
    S = 128
    cx = cy = 63.5
    img = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)

    # Outer & inner concentric runic rings
    d.ellipse([6, 6, 121, 121], outline=(*primary, 255), width=5)
    d.ellipse([18, 18, 109, 109], outline=(*core_col, 255), width=3)
    d.ellipse([36, 36, 91, 91], outline=(*primary, 255), width=4)

    # Sacred star polygon + radial glyphs
    for i in range(spikes):
        a0 = i * (2 * math.pi / spikes)
        a1 = ((i + 2) % spikes) * (2 * math.pi / spikes)
        p0 = (cx + math.cos(a0) * 54, cy + math.sin(a0) * 54)
        p1 = (cx + math.cos(a1) * 54, cy + math.sin(a1) * 54)
        d.line([p0, p1], fill=(*primary, 255), width=3)
        pm = (cx + math.cos(a0) * 59, cy + math.sin(a0) * 59)
        pi = (cx + math.cos(a0) * 20, cy + math.sin(a0) * 20)
        d.line([pi, pm], fill=(*core_col, 255), width=3)

    d.ellipse([50, 50, 77, 77], fill=(*core_col, 255))
    # Smooth radial falloff to pure black at border so additive quad never clips
    img = img.filter(ImageFilter.GaussianBlur(radius=1.1))
    px = img.load()
    for y in range(S):
        for x in range(S):
            dist = math.hypot(x - cx, y - cy) / 62.0
            fade = max(0.0, min(1.0, (1.0 - dist) * 4.5)) if dist > 0.78 else 1.0
            r, g, b, _ = px[x, y]
            px[x, y] = (int(r * fade), int(g * fade), int(b * fade), 255)
    return encode_blp1_paletted(img, alpha_bits=0)


def _generate_vfx_mdl(model_name: str, tex_mpq_path: str) -> str:
    """
    Generate a 2-Geoset counter-rotating 3D Warcraft III `FormatVersion 800` MDL:
      - Geoset 0 (`Bone_Disc`): Rotating `320x320` Sacred Star-Sigil Disc (`Z = 18`)
      - Geoset 1 (`Bone_Crown`): Counter-rotating 8-sided 3D Flared Energy Crown
        rising from `Z = 12` (`R = 88`) to `Z = 148` (`R = 142`)!
      - Sequences: `Birth` (0..300ms), `Stand` (400..1400ms), `Death` (1500..2350ms
        expanding shockwave + smooth Alpha 1->0 fadeout so `DestroyEffect` plays cleanly!).
    """
    # Build 8-sided flared crown cylinder vertices (16 vertices: 8 bottom, 8 top)
    crown_verts = []
    crown_norms = []
    crown_uvs = []
    crown_tris = []
    N = 8
    for i in range(N):
        ang = i * (2 * math.pi / N)
        ca, sa = math.cos(ang), math.sin(ang)
        crown_verts.append(f"{{ {ca * 86:.2f}, {sa * 86:.2f}, 12.00 }}")
        crown_verts.append(f"{{ {ca * 142:.2f}, {sa * 142:.2f}, 146.00 }}")
        crown_norms.append(f"{{ {ca:.3f}, {sa:.3f}, 0.150 }}")
        crown_norms.append(f"{{ {ca:.3f}, {sa:.3f}, 0.150 }}")
        u = (i % 2) * 0.8 + 0.1
        crown_uvs.append(f"{{ {u:.2f}, 0.88 }}")
        crown_uvs.append(f"{{ {u:.2f}, 0.12 }}")
        b0 = i * 2
        t0 = i * 2 + 1
        b1 = ((i + 1) % N) * 2
        t1 = ((i + 1) % N) * 2 + 1
        crown_tris.extend([str(b0), str(b1), str(t1), str(b0), str(t1), str(t0)])

    v_str = ",\n        ".join(crown_verts)
    n_str = ",\n        ".join(crown_norms)
    uv_str = ",\n        ".join(crown_uvs)
    vg_str = ", ".join(["0"] * (2 * N))
    tri_str = ", ".join(crown_tris)

    return f"""Version {{
    FormatVersion 800,
}}
Model "{model_name}" {{
    BlendTime 120,
    MinimumExtent {{ -220, -220, 0 }},
    MaximumExtent {{ 220, 220, 200 }},
    BoundsRadius 260,
}}
Sequences 3 {{
    Anim "Birth" {{
        Interval {{ 0, 300 }},
        NonLooping,
        MinimumExtent {{ -220, -220, 0 }},
        MaximumExtent {{ 220, 220, 200 }},
        BoundsRadius 260,
    }}
    Anim "Stand" {{
        Interval {{ 400, 1400 }},
        MinimumExtent {{ -220, -220, 0 }},
        MaximumExtent {{ 220, 220, 200 }},
        BoundsRadius 260,
    }}
    Anim "Death" {{
        Interval {{ 1500, 2350 }},
        NonLooping,
        MinimumExtent {{ -220, -220, 0 }},
        MaximumExtent {{ 220, 220, 200 }},
        BoundsRadius 260,
    }}
}}
Textures 1 {{
    Bitmap {{
        Image "{tex_mpq_path}",
    }}
}}
Materials 1 {{
    Material {{
        Layer {{
            FilterMode Additive,
            Unshaded,
            TwoSided,
            NoDepthSet,
            static TextureID 0,
        }}
    }}
}}
Geoset {{
    Vertices 4 {{
        {{ -165, -165, 18 }},
        {{ 165, -165, 18 }},
        {{ 165, 165, 18 }},
        {{ -165, 165, 18 }},
    }}
    Normals 4 {{
        {{ 0, 0, 1 }},
        {{ 0, 0, 1 }},
        {{ 0, 0, 1 }},
        {{ 0, 0, 1 }},
    }}
    TVertices 4 {{
        {{ 0, 1 }},
        {{ 1, 1 }},
        {{ 1, 0 }},
        {{ 0, 0 }},
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
    MinimumExtent {{ -165, -165, 18 }},
    MaximumExtent {{ 165, 165, 18 }},
    BoundsRadius 235,
    MaterialID 0,
    SelectionGroup 0,
}}
Geoset {{
    Vertices {2 * N} {{
        {v_str},
    }}
    Normals {2 * N} {{
        {n_str},
    }}
    TVertices {2 * N} {{
        {uv_str},
    }}
    VertexGroup {{
        {vg_str},
    }}
    Faces 1 {len(crown_tris)} {{
        Triangles {{
            {{ {tri_str} }},
        }}
    }}
    Groups 1 1 {{
        Matrices {{ 1 }},
    }}
    MinimumExtent {{ -145, -145, 12 }},
    MaximumExtent {{ 145, 145, 146 }},
    BoundsRadius 210,
    MaterialID 0,
    SelectionGroup 0,
}}
GeosetAnim {{
    Alpha 5 {{
        Linear,
        0: 0,
        280: 1,
        1400: 1,
        1500: 1,
        2350: 0,
    }}
    GeosetId 0,
}}
GeosetAnim {{
    Alpha 5 {{
        Linear,
        0: 0,
        280: 0.9,
        1400: 0.9,
        1500: 0.95,
        2350: 0,
    }}
    GeosetId 1,
}}
Bone "Bone_Disc" {{
    ObjectId 0,
    GeosetId 0,
    GeosetAnimId 0,
    Rotation 7 {{
        Linear,
        0: {{ 0, 0, 0, 1 }},
        300: {{ 0, 0, 0.7071, 0.7071 }},
        400: {{ 0, 0, 0, 1 }},
        900: {{ 0, 0, 1, 0 }},
        1400: {{ 0, 0, 0, -1 }},
        1500: {{ 0, 0, 0, 1 }},
        2350: {{ 0, 0, 0.9659, 0.2588 }},
    }}
    Scaling 5 {{
        Linear,
        0: {{ 0.25, 0.25, 0.25 }},
        300: {{ 1, 1, 1 }},
        1400: {{ 1.05, 1.05, 1 }},
        1500: {{ 0.42, 0.42, 0.42 }},
        2350: {{ 1.55, 1.55, 1.25 }},
    }}
}}
Bone "Bone_Crown" {{
    ObjectId 1,
    GeosetId 1,
    GeosetAnimId 1,
    Rotation 7 {{
        Linear,
        0: {{ 0, 0, 0, 1 }},
        300: {{ 0, 0, -0.7071, 0.7071 }},
        400: {{ 0, 0, 0, 1 }},
        900: {{ 0, 0, -1, 0 }},
        1400: {{ 0, 0, 0, -1 }},
        1500: {{ 0, 0, 0, 1 }},
        2350: {{ 0, 0, -0.9659, 0.2588 }},
    }}
    Scaling 5 {{
        Linear,
        0: {{ 0.3, 0.3, 0.2 }},
        300: {{ 1, 1, 1 }},
        1400: {{ 0.95, 0.95, 1.15 }},
        1500: {{ 0.45, 0.45, 0.4 }},
        2350: {{ 1.4, 1.4, 1.65 }},
    }}
}}
PivotPoints 2 {{
    {{ 0, 0, 0 }},
    {{ 0, 0, 0 }},
}}
"""


def compile_vfx_mdx_models(mdl_map: Dict[str, str]) -> Dict[str, bytes]:
    """
    Compile MDL strings into verified binary Warcraft III `MDLX v800` `.mdx` files
    using `/tmp/wc3ref/node_modules/mdx-m3-viewer`.
    """
    out: Dict[str, bytes] = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        js_lines = [
            f'const fs = require("fs");',
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
# 5. MASTER ASSET BUNDLE GENERATOR FOR `.w3x` MPQ PACKING
# ==============================================================================

CUSTOM_ICON_SPECS: List[Tuple[str, str]] = [
    # Abyssal Tideborn (Naga) 4 Custom Skills
    ("BTN_WM_AbyssVortex",   "AbyssVortex"),
    ("BTN_WM_AbyssLance",    "AbyssLance"),
    ("BTN_WM_AbyssCarapace", "AbyssCarapace"),
    ("BTN_WM_AbyssTsunami",  "AbyssTsunami"),
    # Sunfury Imperium 4 Custom Skills
    ("BTN_WM_SolarSigil",     "SolarSigil"),
    ("BTN_WM_SolarDash",      "SolarDash"),
    ("BTN_WM_SolarJudgment",  "SolarJudgment"),
    ("BTN_WM_SolarSupernova", "SolarSupernova"),
    # Voidborn Astral Legion 4 Custom Skills
    ("BTN_WM_VoidHorizon",  "VoidHorizon"),
    ("BTN_WM_VoidSever",    "VoidSever"),
    ("BTN_WM_VoidShroud",   "VoidShroud"),
    ("BTN_WM_VoidCollapse", "VoidCollapse"),
    # Runeforged Titan Bastion 4 Custom Skills
    ("BTN_WM_RunicTectonics", "RunicTectonics"),
    ("BTN_WM_RunicOverload",  "RunicOverload"),
    ("BTN_WM_RunicAegis",     "RunicAegis"),
    ("BTN_WM_RunicOrbital",   "RunicOrbital"),
    # Map Crest & Faction Selector Icons
    ("BTN_WM_CrownCrest",  "CrownCrest"),
    ("BTN_WM_FactionTome", "FactionTome"),
]


def build_war3map_preview_tga() -> bytes:
    """
    Build `war3mapPreview.tga` (256x256 uncompressed 24-bit TGA) from our custom
    `web/public/crown_artwork.png` with an astral-gold inner border so the Warcraft III
    Lobby Map Preview displays our custom key-art cleanly.
    """
    assert ARTWORK_PNG.exists(), f"Missing custom artwork at {ARTWORK_PNG}"
    img = Image.open(ARTWORK_PNG).convert("RGB").resize((256, 256), Image.Resampling.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.08)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 255, 255], outline=(12, 14, 24), width=2)
    draw.rectangle([2, 2, 253, 253], outline=(218, 172, 62), width=2)
    draw.rectangle([4, 4, 251, 251], outline=(56, 189, 248), width=1)
    return encode_tga_24bit(img)


def generate_all_custom_assets() -> Dict[str, bytes]:
    """
    Return `{mpq_archive_path: binary_bytes}` for all custom `.tga`, `.blp`, and `.mdx`
    assets to pack into `(8)CrownOfWarMahdi.w3x` and register in `war3map.imp`.
    Note: `war3mapPreview.tga` is a standard root map file (not listed in `war3map.imp`),
    whereas all `ReplaceableTextures\\*`, `UI\\*`, `Textures\\*`, and `WM_FX_*.mdx`
    files ARE listed in `war3map.imp`.
    """
    files: Dict[str, bytes] = {}

    # 1. Lobby Map Preview Artwork (`war3mapPreview.tga`)
    files["war3mapPreview.tga"] = build_war3map_preview_tga()

    # 2. 18 Custom `BTN` + 18 `DISBTN` Command Button Icons (`64x64` BLP1)
    for btn_stem, kind in CUSTOM_ICON_SPECS:
        core_img, accent = paint_skill_icon(kind)
        btn_img, dis_img = apply_btn_frame(core_img, accent)
        dis_stem = "DIS" + btn_stem
        files[f"ReplaceableTextures\\CommandButtons\\{btn_stem}.blp"] = encode_blp1_paletted(btn_img, alpha_bits=8)
        files[f"ReplaceableTextures\\CommandButtonsDisabled\\{dis_stem}.blp"] = encode_blp1_paletted(dis_img, alpha_bits=8)

    # 3. Custom UI Skin Textures (`UI\CrownUI\*.blp`)
    files.update(build_ui_textures())

    # 4. 4 Custom Additive Sigil BLP1 Textures + 4 Custom 3D `.mdx` Spell Models
    files["Textures\\WM_Sigil_Abyssal.blp"] = build_sigil_texture((18, 195, 240), (215, 255, 255), spikes=8)
    files["Textures\\WM_Sigil_Solar.blp"]   = build_sigil_texture((245, 145, 22), (255, 250, 205), spikes=8)
    files["Textures\\WM_Sigil_Void.blp"]    = build_sigil_texture((168, 72, 250), (245, 215, 255), spikes=8)
    files["Textures\\WM_Sigil_Runic.blp"]   = build_sigil_texture((225, 165, 48), (165, 248, 255), spikes=6)

    mdl_specs = {
        "WM_FX_Abyssal.mdx": _generate_vfx_mdl("WM_FX_Abyssal", "Textures\\WM_Sigil_Abyssal.blp"),
        "WM_FX_Solar.mdx":   _generate_vfx_mdl("WM_FX_Solar",   "Textures\\WM_Sigil_Solar.blp"),
        "WM_FX_Void.mdx":    _generate_vfx_mdl("WM_FX_Void",    "Textures\\WM_Sigil_Void.blp"),
        "WM_FX_Runic.mdx":   _generate_vfx_mdl("WM_FX_Runic",   "Textures\\WM_Sigil_Runic.blp"),
    }
    files.update(compile_vfx_mdx_models(mdl_specs))

    return files


if __name__ == "__main__":
    bundle = generate_all_custom_assets()
    total = sum(len(v) for v in bundle.values())
    print(f"Generated {len(bundle)} custom assets ({total:,} bytes total)")
    for k in sorted(bundle):
        print(f"  {k:68s} {len(bundle[k]):7,d} B")
