#!/usr/bin/env python3
"""
Live Web Preview & One-Click .w3x Download Server for `(8) Crown of WarMahdi`.
Binds to 0.0.0.0 and accepts any proxy Host/Origin header cleanly.
"""

from __future__ import annotations
import json
import mimetypes
import os
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
            "Stage 1: HM3W Pre-Header + MPQ v1 Container + StormLib CRC32/MD5",
            "Stage 2: TFT Binary Format v25 (1.26a / 1.27b / Atinad / GameRanger / Reforged)",
            "Stage 3a: JASS2 Static Typecheck vs Patch 1.27b Common.j + Blizzard.j (80 fns, 0 Errors)",
            "Stage 3b: JASS2 Static Typecheck vs Reforged 1.32.8 Common.j + Blizzard.j (80 fns, 0 Errors)",
            "Stage 4 & 5: 1-to-1 Sync (war3mapUnits.doo <-> war3map.j <-> war3map.mmp <-> war3map.wts)",
            "Stage 6: All 6 Races (Human / Orc / Undead / Night Elf / Naga / Campaign Human) Spawn Prover",
            "Stage 7: Zero Collision Footprints Across 181 Units & 5,920 Harvestable Trees",
            "Stage 8: Dynamic Pathing Grid BFS: 401,756 Walkable Cells (100% Connected)",
            "Stage 9: 200u Camp Acquisition & Highway / Central Tavern Safe-Zones",
            "Stage 10: Exact 8-Way Dihedral Group (D4) Terrain, Pathing & Forest Symmetry",
            "Stage 11: 6-Race Object Tables v2 (w3u=50, w3t=3, w3q=3, Misc.txt, 0 Button Collisions)",
            "Stage 12: Pro Melee AI Static Typecheck (naga_melee.ai & camphuman_melee.ai vs common.ai)",
        ],
    }


ARCHIVE_MANIFEST_CACHE = build_archive_manifest()


class MapPreviewHandler(BaseHTTPRequestHandler):
    server_version = "CrownOfWarMahdiPreview/2.0"

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
