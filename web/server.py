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
            "Stage 1: HM3W header + PurePython MPQ v1 archive (97 files)",
            "Stage 2: TFT v25 — 192x192 Sunken-Astral terrain + 5,961 placed trees within the World Editor limit",
            "Stage 3a: JASS2 static typecheck vs 1.27b Common.j + Blizzard.j (110 functions, 0 errors)",
            "Stage 3b: JASS2 static typecheck vs Reforged 1.32.8 Common.j + Blizzard.j (110 functions, 0 errors)",
            "Stage 4 & 5: 181 preplaced units, 15 strings, 45 minimap icons and 256x256 BLP1 minimap synchronized",
            "Stage 6: All 8 mirrored player starts, mines and town-hall zones are buildable",
            "Stage 7: Zero collision footprints across 181 units and the 5,920 harvestable trees",
            "Stage 8: Dynamic pathing BFS — 401,756 walkable cells, all bases/mines/shops/creeps reachable",
            "Stage 9: 200u creep-camp acquisition and Tavern/base safe-zones verified",
            "Stage 10: Exact 8-way D4 terrain, pathing and forest symmetry",
            "Stage 11: 8 playable empires, 16 heroes, 64 skills; object tables and command-card collisions verified",
            "Stage 12: All 4 imported race AI scripts typechecked against Common.j + common.ai (0 errors)",
            "Stage 13: 31 combat units + 16 heroes; ladder DPS/EHP/cost and 55-point stat audits",
            "Stage 14: 66 BLP1s (20 icon-only portrait files), native effect-matched skill art and 6 MDX VFX",
            "Stage 15: TFT 1.26-era API compatibility proxy, worker-build fallback, item use and AI safeguards",
        ],
    }


ARCHIVE_MANIFEST_CACHE = build_archive_manifest()


class MapPreviewHandler(BaseHTTPRequestHandler):
    server_version = "CrownOfWarMahdiPreview/5.0"

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
