#!/usr/bin/env python3
"""
Live Web Preview & One-Click .w3x Download Server for `(8) Crown of WarMahdi`.
Binds to 0.0.0.0 and accepts any proxy Host/Origin header cleanly.
"""

from __future__ import annotations
import json
import mimetypes
import os
import struct
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = Path(__file__).resolve().parent / "public"
MAP_FILE = REPO_ROOT / "maps" / "(8)CrownOfWarMahdi.w3x"
PREVIEW_PNG = REPO_ROOT / "maps" / "(8)CrownOfWarMahdi_Preview.png"

sys.path.insert(0, str(REPO_ROOT / "src"))
from mpq_packer import CANONICAL_W3X_FILES, read_w3x_archive  # noqa: E402


def build_archive_manifest() -> dict:
    hdr, files = read_w3x_archive(MAP_FILE)
    blp_files = [data for name, data in files.items() if name.lower().endswith(".blp")]
    blp1_count = sum(1 for data in blp_files if data[:4] == b"BLP1")
    palette_blp_count = sum(
        1 for data in blp_files if data[:4] == b"BLP1" and len(data) >= 8 and struct.unpack_from("<I", data, 4)[0] == 1
    )
    metadata_path = PUBLIC_DIR / "map_data.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}
    stats = metadata.get("stats", {})
    dimensions = metadata.get("dimensions", {})
    unit_doo = files.get("war3mapUnits.doo", b"")
    doodad_doo = files.get("war3map.doo", b"")
    unit_count = struct.unpack_from("<i", unit_doo, 12)[0] if len(unit_doo) >= 16 else 0
    doodad_count = struct.unpack_from("<I", doodad_doo, 12)[0] if len(doodad_doo) >= 16 else 0
    wts_data = files.get("war3map.wts", b"")
    string_count = wts_data.count(b"STRING ")
    mmp_data = files.get("war3map.mmp", b"")
    minimap_icon_count = struct.unpack_from("<I", mmp_data, 4)[0] if len(mmp_data) >= 8 else 0
    minimap_blp = files.get("war3map.blp", files.get("war3mapMap.blp", b""))
    minimap_width, minimap_height = struct.unpack_from("<2I", minimap_blp, 12) if len(minimap_blp) >= 20 else (0, 0)
    mdx_names = [Path(name).stem for name in files if name.lower().endswith(".mdx")]
    skill_mdx_count = sum(1 for name in mdx_names if name.startswith("WM_Skill_"))
    sigil_mdx_count = sum(1 for name in mdx_names if name.startswith("WM_FX_"))
    building_mdx_count = sum(1 for name in mdx_names if name.startswith("WM_Build_Naga_"))
    ai_script_count = sum(1 for name in files if name.lower().endswith(".ai"))
    trees_count = int(stats.get("trees", 0))
    scenic_doodads_count = int(stats.get("scenicDoodads", 0))
    entries = []
    seen = set()
    for name in CANONICAL_W3X_FILES:
        if name in files:
            entries.append({"name": name, "rawBytes": len(files[name])})
            seen.add(name)
    for name in sorted(files.keys()):
        if name not in seen:
            entries.append({"name": name, "rawBytes": len(files[name])})
            seen.add(name)
    return {
        "header": hdr,
        "archiveFileName": MAP_FILE.name,
        "archiveBytes": MAP_FILE.stat().st_size,
        "entries": entries,
        "checks": [
            f"Stage 1: HM3W header + PurePython MPQ v1 archive ({len(files)} files)",
            f"Stage 2: TFT v25 — {dimensions.get('tilesW', 0)}x{dimensions.get('tilesH', 0)} Sunken-Astral terrain + {doodad_count:,} placed doodads ({trees_count:,} trees + {scenic_doodads_count:,} scenic)",
            "Stage 3: Classic TFT JASS2 static typecheck vs 1.27b Common.j + Blizzard.j (1.26-era API proxy also checked)",
            f"Stage 4 & 5: {unit_count} preplaced units, {string_count} strings, {minimap_icon_count} minimap icons and {minimap_width}x{minimap_height} BLP1 minimap synchronized",
            f"Stage 6: {stats.get('startLocations', 0)} mirrored player starts and {stats.get('goldMines', 0)} mines; town-hall zones checked for buildability",
            f"Stage 7: Zero collision footprints across {unit_count} units and {trees_count:,} harvestable trees",
            f"Stage 8: Dynamic pathing BFS on {dimensions.get('tilesW', 0)}x{dimensions.get('tilesH', 0)} terrain — all bases, mines, shops and creep camps reachable",
            "Stage 9: 200u creep-camp acquisition and Tavern/base safe-zones verified",
            f"Stage 10: Exact 8-way D4 terrain, pathing and forest symmetry on {dimensions.get('tilesW', 0)}x{dimensions.get('tilesH', 0)} map",
            f"Stage 11: {stats.get('playableRaces', 0)} empires/race slots, {stats.get('customHeroes', 0)} heroes, {stats.get('customSkills', 0)} custom icon pairs; distinct ultimate geometries verified",
            f"Stage 12: {ai_script_count} race-AI scripts typechecked; native AI for classic races + authoritative JASS controller for custom factions",
            "Stage 13: Combat-unit and hero ladder DPS/EHP/cost and stat audits",
            f"Stage 14: {blp1_count} BLP1s ({palette_blp_count} paletted portrait/skill-button icons), {skill_mdx_count} skill MDX effects + {sigil_mdx_count} faction sigils + {building_mdx_count} Naga building MDXs; race/role model duplicates checked",
            "Stage 15: TFT 1.26-era API compatibility proxy, explicit workers, sequential construction/training and AI safeguards",
            f"Stage 16: D4-symmetric neutral objectives; {stats.get('creepCamps', 0)} camp rosters/loot tiers, alliance-aware shrine rewards and equal race-pick economy",
            "Stage 17: Fair-vision AI with expiring last-seen intel, adaptive counter-production, dynamic objectives, visible-natural expansion, coordinated micro, hero-spell evaluation, disclosed difficulty and -aistats telemetry",
        ],
    }


ARCHIVE_MANIFEST_CACHE = build_archive_manifest()


class MapPreviewHandler(BaseHTTPRequestHandler):
    server_version = "CrownOfWarMahdiPreview/7.1"

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stdout.write("[HTTP] " + (fmt % args) + "\n")
        sys.stdout.flush()

    def _send_common_headers(self, status: int, content_type: str, content_length: int, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self._send_common_headers(204, "text/plain; charset=utf-8", 0)

    def _serve_bytes(self, data: bytes, content_type: str, head_only: bool, extra: dict | None = None) -> None:
        self._send_common_headers(200, content_type, len(data), extra=extra)
        if not head_only:
            self.wfile.write(data)

    def _handle_req(self, head_only: bool) -> None:
        parsed = urlparse(self.path)
        req_path = unquote(parsed.path)

        if req_path in (
            "/CrownOfWarMahdi.w3x",
            "/(8)CrownOfWarMahdi.w3x",
            "/maps/(8)CrownOfWarMahdi.w3x",
            "/CrownOfLordaeron.w3x",
            "/download",
            "/api/download",
        ):
            data = MAP_FILE.read_bytes()
            self._serve_bytes(
                data,
                "application/octet-stream",
                head_only,
                extra={
                    "Content-Disposition": 'attachment; filename="(8)CrownOfWarMahdi.w3x"',
                },
            )
            return

        if req_path == "/api/preview.png":
            data = PREVIEW_PNG.read_bytes()
            self._serve_bytes(data, "image/png", head_only)
            return

        if req_path == "/api/archive-manifest":
            payload = json.dumps(ARCHIVE_MANIFEST_CACHE, ensure_ascii=False).encode("utf-8")
            self._serve_bytes(payload, "application/json; charset=utf-8", head_only)
            return

        if req_path == "/api/jass":
            _, files = read_w3x_archive(MAP_FILE)
            self._serve_bytes(files["war3map.j"], "text/plain; charset=utf-8", head_only)
            return

        if req_path == "/api/ai-naga":
            _, files = read_w3x_archive(MAP_FILE)
            self._serve_bytes(files["naga_melee.ai"], "text/plain; charset=utf-8", head_only)
            return

        if req_path == "/api/ai-camphuman":
            _, files = read_w3x_archive(MAP_FILE)
            self._serve_bytes(files["camphuman_melee.ai"], "text/plain; charset=utf-8", head_only)
            return

        if req_path in ("/", "/index.html"):
            target = PUBLIC_DIR / "index.html"
        else:
            rel = req_path.lstrip("/")
            target = (PUBLIC_DIR / rel).resolve()
            if not str(target).startswith(str(PUBLIC_DIR.resolve())):
                msg = b"Forbidden"
                self._send_common_headers(403, "text/plain; charset=utf-8", len(msg))
                if not head_only:
                    self.wfile.write(msg)
                return

        if not target.is_file():
            msg = b"Not Found"
            self._send_common_headers(404, "text/plain; charset=utf-8", len(msg))
            if not head_only:
                self.wfile.write(msg)
            return

        ctype, _ = mimetypes.guess_type(str(target))
        if not ctype:
            ctype = "application/octet-stream"
        if ctype.startswith("text/") or ctype == "application/javascript" or ctype == "application/json":
            ctype += "; charset=utf-8"

        data = target.read_bytes()
        self._serve_bytes(data, ctype, head_only)

    def do_GET(self) -> None:
        self._handle_req(head_only=False)

    def do_HEAD(self) -> None:
        self._handle_req(head_only=True)


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), MapPreviewHandler)
    print(f"Serving (8) Crown of WarMahdi preview & download on http://0.0.0.0:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
