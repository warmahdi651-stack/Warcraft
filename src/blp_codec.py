#!/usr/bin/env python3
"""Patch-compatible Warcraft III BLP1 four-channel JPEG encoder."""

from __future__ import annotations

import math
import struct
from typing import Dict, List, Tuple


STD_LUM_QT = [
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99,
]

SCAN_ORDER = [
     0,  1,  8, 16,  9,  2,  3, 10,
    17, 24, 32, 25, 18, 11,  4,  5,
    12, 19, 26, 33, 40, 48, 41, 34,
    27, 20, 13,  6,  7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36,
    29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46,
    53, 60, 61, 54, 47, 55, 62, 63,
]

DC_LUM_BITS = [0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
DC_LUM_VALS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
AC_LUM_BITS = [0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 0x7D]
AC_LUM_VALS = [
    0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12,
    0x21, 0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07,
    0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
    0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0,
    0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0A, 0x16,
    0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
    0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
    0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49,
    0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
    0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69,
    0x6A, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79,
    0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
    0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98,
    0x99, 0x9A, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7,
    0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
    0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5,
    0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4,
    0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
    0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA,
    0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8,
    0xF9, 0xFA,
]


def _build_huff(bits: List[int], vals: List[int]) -> Dict[int, Tuple[int, int]]:
    tab: Dict[int, Tuple[int, int]] = {}
    code = 0
    idx = 0
    for length in range(1, 17):
        for _ in range(bits[length - 1]):
            tab[vals[idx]] = (code, length)
            code += 1
            idx += 1
        code <<= 1
    return tab


DC_TAB = _build_huff(DC_LUM_BITS, DC_LUM_VALS)
AC_TAB = _build_huff(AC_LUM_BITS, AC_LUM_VALS)
COS_TAB = [
    [math.cos((2 * x + 1) * u * math.pi / 16.0) * (1.0 / math.sqrt(2.0) if u == 0 else 1.0) for u in range(8)]
    for x in range(8)
]


def encode_blp1_jpeg(rgba: bytes, width: int = 256, height: int = 256, quality_scale: float = 0.35) -> bytes:
    """Encode 256x256 RGBA pixels into a genuine Warcraft III BLP1 (4-channel BGRA Baseline JPEG)."""
    qt = [max(1, min(255, int(round(v * quality_scale)))) for v in STD_LUM_QT]
    qt_zz = [qt[SCAN_ORDER[i]] for i in range(64)]

    hdr = bytearray()
    hdr += b"\xff\xd8"
    hdr += b"\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    hdr += b"\xff\xdb\x00\x43\x00" + bytes(qt_zz)
    hdr += b"\xff\xc4" + struct.pack(">HB", 3 + 16 + len(DC_LUM_VALS), 0x00) + bytes(DC_LUM_BITS) + bytes(DC_LUM_VALS)
    hdr += b"\xff\xc4" + struct.pack(">HB", 3 + 16 + len(AC_LUM_VALS), 0x10) + bytes(AC_LUM_BITS) + bytes(AC_LUM_VALS)
    hdr += b"\xff\xc0"

    body = bytearray()
    body += struct.pack(">HBHHB", 20, 8, height, width, 4)
    for cid in (1, 2, 3, 4):
        body += struct.pack(">BBB", cid, 0x11, 0)
    body += b"\xff\xda" + struct.pack(">HB", 14, 4)
    for cid in (1, 2, 3, 4):
        body += struct.pack(">BB", cid, 0x00)
    body += b"\x00\x3f\x00"

    bit_buf = 0
    bit_cnt = 0
    scan = bytearray()
    prev_dc = [0, 0, 0, 0]

    def put_bits(val: int, nbits: int) -> None:
        nonlocal bit_buf, bit_cnt
        bit_buf = (bit_buf << nbits) | (val & ((1 << nbits) - 1))
        bit_cnt += nbits
        while bit_cnt >= 8:
            bit_cnt -= 8
            b = (bit_buf >> bit_cnt) & 0xFF
            scan.append(b)
            if b == 0xFF:
                scan.append(0x00)

    def mag_cat(v: int) -> Tuple[int, int]:
        if v == 0:
            return 0, 0
        av = abs(v)
        cat = av.bit_length()
        return cat, (v if v > 0 else ((1 << cat) - 1 + v))

    for by in range(0, height, 8):
        for bx in range(0, width, 8):
            for ch_idx, rgba_off in enumerate((2, 1, 0, 3)):  # B, G, R, A
                tmp = [[0.0] * 8 for _ in range(8)]
                dct = [[0] * 8 for _ in range(8)]
                for y in range(8):
                    row_base = ((by + y) * width + bx) * 4 + rgba_off
                    for u in range(8):
                        s = 0.0
                        for x in range(8):
                            s += (rgba[row_base + x * 4] - 128.0) * COS_TAB[x][u]
                        tmp[y][u] = s
                for v in range(8):
                    for u in range(8):
                        s = 0.0
                        for y in range(8):
                            s += tmp[y][u] * COS_TAB[y][v]
                        dct[v][u] = int(round((s * 0.25) / qt[v * 8 + u]))

                zz = [dct[SCAN_ORDER[i] >> 3][SCAN_ORDER[i] & 7] for i in range(64)]

                diff = zz[0] - prev_dc[ch_idx]
                prev_dc[ch_idx] = zz[0]
                cat, vbits = mag_cat(diff)
                hc, hl = DC_TAB[cat]
                put_bits(hc, hl)
                if cat > 0:
                    put_bits(vbits, cat)

                zero_run = 0
                for k in range(1, 64):
                    ac = zz[k]
                    if ac == 0:
                        zero_run += 1
                    else:
                        while zero_run >= 16:
                            hc, hl = AC_TAB[0xF0]
                            put_bits(hc, hl)
                            zero_run -= 16
                        cat, vbits = mag_cat(ac)
                        hc, hl = AC_TAB[(zero_run << 4) | cat]
                        put_bits(hc, hl)
                        put_bits(vbits, cat)
                        zero_run = 0
                if zero_run > 0:
                    hc, hl = AC_TAB[0x00]
                    put_bits(hc, hl)

    if bit_cnt > 0:
        put_bits((1 << (8 - bit_cnt)) - 1, 8 - bit_cnt)
    body += scan + b"\xff\xd9"

    blp = bytearray(1180)
    offsets = [0] * 16
    sizes = [0] * 16
    offsets[0] = 1180
    sizes[0] = len(body)
    struct.pack_into("<4s6I16I16II", blp, 0, b"BLP1", 0, 0, width, height, 3, 0, *offsets, *sizes, len(hdr))
    blp[160 : 160 + len(hdr)] = hdr
    return bytes(blp) + bytes(body)
