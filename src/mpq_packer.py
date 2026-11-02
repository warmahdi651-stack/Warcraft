#!/usr/bin/env python3
"""
MPQ v1 + HM3W (.w3x) Archive Builder & Reader for Warcraft III Maps.

Supports two packing backends:
1. Official StormLib binary (if available) for full zlib sector compression + (attributes) CRC32/MD5.
2. Self-contained pure-Python MPQ v1 packer/reader with authentic Blizzard MPQ cryptography
   (hash table + block table encryption + zlib sector compression + (listfile)), requiring zero
   third-party dependencies.
"""

from __future__ import annotations
import os
import struct
import subprocess
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Canonical World Editor file order inside .w3x archives
CANONICAL_W3X_FILES: List[str] = [
    "war3map.w3e",
    "war3map.w3i",
    "war3map.wtg",
    "war3map.wct",
    "war3map.wts",
    "war3map.j",
    "war3map.shd",
    "war3mapMap.blp",
    "war3map.mmp",
    "war3map.wpm",
    "war3map.doo",
    "war3mapUnits.doo",
    "war3map.w3r",
    "war3map.w3c",
]

MPQ_HASH_TABLE_INDEX = 0x000
MPQ_HASH_NAME_A = 0x100
MPQ_HASH_NAME_B = 0x200
MPQ_HASH_FILE_KEY = 0x300
MPQ_HASH_KEY2_MIX = 0x400

MPQ_FILE_COMPRESS = 0x00000200
MPQ_FILE_EXISTS = 0x80000000
MPQ_COMPRESSION_ZLIB = 0x02


def _build_crypt_table() -> List[int]:
    seed = 0x00100001
    table = [0] * 0x500
    for index1 in range(0x100):
        index2 = index1
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            temp1 = (seed & 0xFFFF) << 16
            seed = (seed * 125 + 3) % 0x2AAAAB
            temp2 = seed & 0xFFFF
            table[index2] = (temp1 | temp2) & 0xFFFFFFFF
            index2 += 0x100
    return table


CRYPT_TABLE = _build_crypt_table()


def mpq_hash_string(text: str, hash_type: int) -> int:
    seed1 = 0x7FED7FED
    seed2 = 0xEEEEEEEE
    for ch in text.upper().encode("latin1"):
        val = CRYPT_TABLE[hash_type + ch]
        seed1 = (val ^ ((seed1 + seed2) & 0xFFFFFFFF)) & 0xFFFFFFFF
        seed2 = (ch + seed1 + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return seed1


def mpq_encrypt_block(data: bytes, key: int) -> bytes:
    assert len(data) % 4 == 0
    seed = 0xEEEEEEEE
    out = bytearray(len(data))
    for i in range(0, len(data), 4):
        seed = (seed + CRYPT_TABLE[MPQ_HASH_KEY2_MIX + (key & 0xFF)]) & 0xFFFFFFFF
        plain = struct.unpack_from("<I", data, i)[0]
        cipher = (plain ^ ((key + seed) & 0xFFFFFFFF)) & 0xFFFFFFFF
        struct.pack_into("<I", out, i, cipher)
        key = ((((~key) << 0x15) + 0x11111111) | (key >> 0x0B)) & 0xFFFFFFFF
        seed = (plain + seed + (seed << 5) + 3) & 0xFFFFFFFF
    return bytes(out)


def mpq_decrypt_block(data: bytes, key: int) -> bytes:
    assert len(data) % 4 == 0
    seed = 0xEEEEEEEE
    out = bytearray(len(data))
    for i in range(0, len(data), 4):
        seed = (seed + CRYPT_TABLE[MPQ_HASH_KEY2_MIX + (key & 0xFF)]) & 0xFFFFFFFF
        cipher = struct.unpack_from("<I", data, i)[0]
        plain = (cipher ^ ((key + seed) & 0xFFFFFFFF)) & 0xFFFFFFFF
        struct.pack_into("<I", out, i, plain)
        key = ((((~key) << 0x15) + 0x11111111) | (key >> 0x0B)) & 0xFFFFFFFF
        seed = (plain + seed + (seed << 5) + 3) & 0xFFFFFFFF
    return bytes(out)


def build_hm3w_header(map_name: str, map_flags: int, max_players: int) -> bytes:
    """Build the 512-byte HM3W pre-header required by Warcraft III 1.26a/1.27b & World Editor."""
    hdr = bytearray(512)
    name_bytes = map_name.encode("utf-8") + b"\x00"
    hdr[0:4] = b"HM3W"
    struct.pack_into("<I", hdr, 4, 0)
    hdr[8 : 8 + len(name_bytes)] = name_bytes
    pos = 8 + len(name_bytes)
    struct.pack_into("<II", hdr, pos, map_flags & 0xFFFFFFFF, max_players & 0xFFFFFFFF)
    return bytes(hdr)


def _compress_mpq_sectors(raw: bytes, sector_size: int = 4096) -> Tuple[bytes, int]:
    """Compress a file into standard MPQ v1 zlib sectors with sector offset table."""
    if len(raw) == 0:
        return b"", MPQ_FILE_EXISTS

    num_sectors = (len(raw) + sector_size - 1) // sector_size
    table_size = (num_sectors + 1) * 4
    sectors_out = bytearray()
    offsets = [table_size]

    for i in range(num_sectors):
        chunk = raw[i * sector_size : (i + 1) * sector_size]
        comp = bytes([MPQ_COMPRESSION_ZLIB]) + zlib.compress(chunk, 9)
        if len(comp) < len(chunk):
            sectors_out += comp
        else:
            sectors_out += chunk
        offsets.append(table_size + len(sectors_out))

    compressed_total = table_size + len(sectors_out)
    if compressed_total >= len(raw):
        return raw, MPQ_FILE_EXISTS

    offset_table = struct.pack(f"<{len(offsets)}I", *offsets)
    return offset_table + bytes(sectors_out), MPQ_FILE_EXISTS | MPQ_FILE_COMPRESS


def pack_w3x_python(hm3w_header: bytes, files: Dict[str, bytes], out_path: Path) -> None:
    """Pure-Python MPQ v1 writer with zlib sector compression & encrypted hash/block tables."""
    assert len(hm3w_header) == 512 and hm3w_header[:4] == b"HM3W"

    ordered_names = [n for n in CANONICAL_W3X_FILES if n in files]
    for extra in files:
        if extra not in ordered_names and extra != "(listfile)":
            ordered_names.append(extra)

    listfile_bytes = ("\r\n".join(ordered_names) + "\r\n").encode("utf-8")
    all_entries: List[Tuple[str, bytes]] = [(n, files[n]) for n in ordered_names]
    all_entries.append(("(listfile)", listfile_bytes))

    hash_table_entries = 64  # Power of 2 >= len(all_entries)*2
    sector_size_shift = 3    # 512 << 3 = 4096 bytes

    mpq_body = bytearray()
    block_entries: List[Tuple[int, int, int, int]] = []
    hash_slots: List[Optional[Tuple[int, int, int, int, int]]] = [None] * hash_table_entries

    data_offset = 32  # Right after 32-byte MPQ v1 header
    for block_idx, (name, raw_bytes) in enumerate(all_entries):
        comp_bytes, flags = _compress_mpq_sectors(raw_bytes, 512 << sector_size_shift)
        file_pos = data_offset + len(mpq_body)
        mpq_body += comp_bytes
        block_entries.append((file_pos, len(comp_bytes), len(raw_bytes), flags))

        start_slot = mpq_hash_string(name, MPQ_HASH_TABLE_INDEX) & (hash_table_entries - 1)
        name_a = mpq_hash_string(name, MPQ_HASH_NAME_A)
        name_b = mpq_hash_string(name, MPQ_HASH_NAME_B)
        slot = start_slot
        while hash_slots[slot] is not None:
            slot = (slot + 1) & (hash_table_entries - 1)
        hash_slots[slot] = (name_a, name_b, 0, 0, block_idx)

    raw_hash_table = bytearray(hash_table_entries * 16)
    for idx, entry in enumerate(hash_slots):
        if entry is None:
            struct.pack_into("<IIHHI", raw_hash_table, idx * 16, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFF, 0xFFFF, 0xFFFFFFFF)
        else:
            struct.pack_into("<IIHHI", raw_hash_table, idx * 16, *entry)

    raw_block_table = bytearray(len(block_entries) * 16)
    for idx, bentry in enumerate(block_entries):
        struct.pack_into("<IIII", raw_block_table, idx * 16, *bentry)

    enc_hash = mpq_encrypt_block(bytes(raw_hash_table), mpq_hash_string("(hash table)", MPQ_HASH_FILE_KEY))
    enc_block = mpq_encrypt_block(bytes(raw_block_table), mpq_hash_string("(block table)", MPQ_HASH_FILE_KEY))

    hash_pos = 32 + len(mpq_body)
    block_pos = hash_pos + len(enc_hash)
    archive_size = block_pos + len(enc_block)

    mpq_header = struct.pack(
        "<4sIIHHIIII",
        b"MPQ\x1a",
        32,
        archive_size,
        0,  # MPQ format v1
        sector_size_shift,
        hash_pos,
        block_pos,
        hash_table_entries,
        len(block_entries),
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(hm3w_header + mpq_header + bytes(mpq_body) + enc_hash + enc_block)


def pack_w3x(
    hm3w_header: bytes,
    files: Dict[str, bytes],
    out_path: Path,
    work_dir: Path,
    storm_tool: Optional[Path] = Path("/tmp/wc3ref/storm_build/w3x_tool"),
) -> str:
    """Pack a .w3x file using official StormLib if available, else pure-Python MPQ v1."""
    work_dir.mkdir(parents=True, exist_ok=True)
    hdr_file = work_dir / "_hm3w_header.bin"
    hdr_file.write_bytes(hm3w_header)
    raw_dir = work_dir / "raw_files"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (raw_dir / name).write_bytes(content)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if storm_tool and storm_tool.exists():
        res = subprocess.run(
            [str(storm_tool), "pack", str(hdr_file), str(raw_dir), str(out_path)],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            return "StormLib"

    pack_w3x_python(hm3w_header, files, out_path)
    return "PurePythonMPQv1"


def read_w3x_archive(w3x_path: Path) -> Tuple[Dict[str, object], Dict[str, bytes]]:
    """Independent pure-Python MPQ v1 + HM3W reader for verification."""
    raw = w3x_path.read_bytes()
    assert len(raw) > 544, "Archive too small"
    assert raw[:4] == b"HM3W", "Missing HM3W magic at 0x000"
    u1 = struct.unpack_from("<I", raw, 4)[0]
    end_str = raw.index(0, 8)
    map_name = raw[8:end_str].decode("utf-8")
    map_flags, max_players = struct.unpack_from("<II", raw, end_str + 1)

    mpq_off = 512
    magic, hdr_size, archive_size, fmt_ver, sec_shift, hash_pos, block_pos, hash_cnt, block_cnt = struct.unpack_from(
        "<4sIIHHIIII", raw, mpq_off
    )
    assert magic == b"MPQ\x1a", "Missing MPQ\\x1a header at 0x200"
    assert hdr_size == 32 and fmt_ver == 0, f"Unexpected MPQ format version {fmt_ver}"
    sector_size = 512 << sec_shift

    enc_hash = raw[mpq_off + hash_pos : mpq_off + hash_pos + hash_cnt * 16]
    enc_block = raw[mpq_off + block_pos : mpq_off + block_pos + block_cnt * 16]
    dec_hash = mpq_decrypt_block(enc_hash, mpq_hash_string("(hash table)", MPQ_HASH_FILE_KEY))
    dec_block = mpq_decrypt_block(enc_block, mpq_hash_string("(block table)", MPQ_HASH_FILE_KEY))

    blocks: List[Tuple[int, int, int, int]] = [
        struct.unpack_from("<IIII", dec_block, i * 16) for i in range(block_cnt)
    ]
    hashes: List[Tuple[int, int, int, int, int]] = [
        struct.unpack_from("<IIHHI", dec_hash, i * 16) for i in range(hash_cnt)
    ]

    def read_entry(filename: str) -> Optional[bytes]:
        slot = mpq_hash_string(filename, MPQ_HASH_TABLE_INDEX) & (hash_cnt - 1)
        na = mpq_hash_string(filename, MPQ_HASH_NAME_A)
        nb = mpq_hash_string(filename, MPQ_HASH_NAME_B)
        for _ in range(hash_cnt):
            ha, hb, _loc, _plat, bidx = hashes[slot]
            if bidx == 0xFFFFFFFF:
                return None
            if ha == na and hb == nb and bidx < len(blocks):
                fpos, csize, fsize, flags = blocks[bidx]
                if not (flags & MPQ_FILE_EXISTS):
                    return None
                fdata = raw[mpq_off + fpos : mpq_off + fpos + csize]
                if fsize == 0:
                    return b""
                if not (flags & MPQ_FILE_COMPRESS) or csize == fsize:
                    return fdata[:fsize]
                # Single-unit Check
                if flags & 0x01000000:
                    ctype = fdata[0]
                    assert ctype == MPQ_COMPRESSION_ZLIB
                    return zlib.decompress(fdata[1:])
                num_sec = (fsize + sector_size - 1) // sector_size
                offs = struct.unpack_from(f"<{num_sec + 1}I", fdata, 0)
                out = bytearray()
                for s in range(num_sec):
                    expected = min(sector_size, fsize - s * sector_size)
                    chunk = fdata[offs[s] : offs[s + 1]]
                    if len(chunk) == expected:
                        out += chunk
                    else:
                        ctype = chunk[0]
                        if ctype == MPQ_COMPRESSION_ZLIB:
                            out += zlib.decompress(chunk[1:])
                        else:
                            raise ValueError(f"Unsupported compression 0x{ctype:02X} in {filename}")
                assert len(out) == fsize
                return bytes(out)
            slot = (slot + 1) & (hash_cnt - 1)
        return None

    listfile_raw = read_entry("(listfile)")
    assert listfile_raw is not None, "Missing (listfile) in MPQ"
    names = [ln.strip() for ln in listfile_raw.decode("utf-8").splitlines() if ln.strip()]
    extracted: Dict[str, bytes] = {}
    for nm in names:
        content = read_entry(nm)
        assert content is not None, f"Failed to read {nm} listed in (listfile)"
        extracted[nm] = content

    header_info = {
        "u1": u1,
        "map_name": map_name,
        "map_flags": map_flags,
        "max_players": max_players,
        "sector_size": sector_size,
        "archive_size": archive_size,
        "file_size": len(raw),
    }
    return header_info, extracted
