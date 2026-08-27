"""API Server with SQLite Database, Multi-Facet Filtering, FTS5 Search, and JIT Stream Resolver.

Endpoints:
  GET  /api/titles                   - Query, filter, sort and paginate titles from SQLite
  GET  /api/title/<key>              - Single anime full dossier by key
  GET  /api/filters                  - Facets (genres, studios, voiceovers, formats, statuses, years)
  GET  /api/anime.json               - Full collected database catalog (100% backward compatible)
  GET  /api/health                   - Healthcheck endpoint
  GET  /api/catalog/<shikimori_id>   - Kodik translations and episodes catalog
  GET  /api/resolve?link=<url>       - On-demand JIT stream resolver (.m3u8 URLs & skips)
"""
from __future__ import annotations

import json
import os
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "data", "anime.json")
DIST = os.path.join(ROOT, "frontend", "dist")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import (
    get_all_titles_catalog,
    get_catalog_cards,
    get_filter_facets,
    get_title_by_key,
    init_db,
    query_titles,
)
from kodik import get_kodik_catalog, resolve_kodik_stream

# Ensure database is initialized
init_db()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIST if os.path.isdir(DIST) else ROOT, **kw)

    def _send_json(self, data: dict | list, status_code: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        # 1. Full Catalog / Backward Compatibility: GET /api/anime.json
        if parsed.path == "/api/anime.json":
            try:
                db_data = get_catalog_cards(limit=2000)
                self._send_json(db_data)
                return
            except Exception as e:
                self.send_error(500, f"Error loading catalog: {e}")
                return

        # 2. Filtered Titles API: GET /api/titles
        if parsed.path == "/api/titles":
            q = qs.get("q", [""])[0] or None
            raw_genres = qs.get("genre", []) + [g for glist in qs.get("genres", []) for g in glist.split(",")]
            genres = [g.strip() for g in raw_genres if g.strip()] or None

            raw_studios = qs.get("studio", []) + [s for slist in qs.get("studios", []) for s in slist.split(",")]
            studios = [s.strip() for s in raw_studios if s.strip()] or None

            raw_vo = qs.get("voiceover", []) + [v for vlist in qs.get("voiceovers", []) for v in vlist.split(",")]
            voiceovers = [v.strip() for v in raw_vo if v.strip()] or None

            format_val = qs.get("format", [""])[0] or None
            status_val = qs.get("status", [""])[0] or None

            year_from = int(qs.get("year_from", [0])[0]) if qs.get("year_from") else None
            year_to = int(qs.get("year_to", [0])[0]) if qs.get("year_to") else None
            min_score = float(qs.get("min_score", [0])[0]) if qs.get("min_score") else None

            sort_val = qs.get("sort", ["score_desc"])[0]
            page_val = int(qs.get("page", [1])[0]) if qs.get("page") else 1
            limit_val = int(qs.get("limit", [1000])[0]) if qs.get("limit") else 1000

            result = get_catalog_cards(
                q=q,
                genres=genres,
                studios=studios,
                voiceovers=voiceovers,
                format=format_val,
                status=status_val,
                year_from=year_from,
                year_to=year_to,
                min_score=min_score,
                sort=sort_val,
                page=page_val,
                limit=limit_val,
            )
            self._send_json(result)
            return

        # 3. Single Title by Key: GET /api/title/<key>
        title_match = re.match(r"^/api/title/([a-zA-Z0-9_-]+)$", parsed.path)
        if title_match:
            key = title_match.group(1)
            item = get_title_by_key(key)
            if item:
                self._send_json(item)
            else:
                self._send_json({"error": f"Title '{key}' not found"}, 404)
            return

        # 4. Filters & Facets API: GET /api/filters
        if parsed.path == "/api/filters":
            facets = get_filter_facets()
            self._send_json(facets)
            return

        # 5. Healthcheck
        if parsed.path == "/api/health":
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"ok")
            return

        # 6. Kodik Catalog by Shikimori ID: /api/catalog/<id>
        catalog_match = re.match(r"^/api/catalog/(\d+)$", parsed.path)
        if catalog_match or parsed.path == "/api/kodik/catalog":
            shiki_id = catalog_match.group(1) if catalog_match else qs.get("shikimori_id", [""])[0]
            if not shiki_id:
                self._send_json({"error": "shikimori_id required"}, 400)
                return
            catalog = get_kodik_catalog(shiki_id, fresh=qs.get("fresh", [""])[0] == "1")
            self._send_json(catalog)
            return

        # 7. On-Demand Stream Resolver: /api/resolve?link=<iframe_url>&key=<key>&ep=<ep_num>&mal_id=<mal_id>
        if parsed.path == "/api/resolve" or parsed.path == "/api/kodik/resolve":
            link = qs.get("link", [""])[0]
            if not link:
                self._send_json({"error": "link query parameter required"}, 400)
                return
            fresh = qs.get("fresh", [""])[0] == "1"
            title_key = qs.get("key", [""])[0] or None
            ep_num = int(qs.get("ep", ["1"])[0] or 1)
            mal_id = qs.get("mal_id", [""])[0] or None

            resolved = resolve_kodik_stream(
                link,
                fresh=fresh,
                title_key=title_key,
                ep_num=ep_num,
                mal_id=mal_id,
            )
            if not resolved:
                self._send_json({"error": "Could not resolve stream for link"}, 502)
                return
            self._send_json(resolved)
            return

        # 8. Fallback to static dist files (SPA routing)
        if os.path.isdir(DIST):
            rel_path = parsed.path.lstrip("/")
            file_on_disk = os.path.join(DIST, rel_path)
            if not rel_path or not os.path.exists(file_on_disk) or os.path.isdir(file_on_disk):
                self.path = "/index.html"

        super().do_GET()

    def log_message(self, *a):
        pass


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8000))
    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"API server running on http://{host}:{port} (SQLite: data/anime.db)")
    if os.path.isdir(DIST):
        print(f"Serving frontend build from {DIST}")
    else:
        print("No frontend build yet - use 'npm run dev' in frontend/ (proxy /api -> here)")
    srv.serve_forever()


if __name__ == "__main__":
    main()