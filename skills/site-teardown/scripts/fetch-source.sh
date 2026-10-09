#!/usr/bin/env bash
# fetch-source.sh <url> <outdir> — save the page HTML plus every CSS/JS file it loaded (from capture's network.json if present).
# Source is the referee for disputed values; it stays local (gitignored), never committed or redistributed.
set -euo pipefail
URL="$1"; OUT="$2"; mkdir -p "$OUT"
ORIGIN=$(python3 -c "import sys,urllib.parse as u;p=u.urlparse(sys.argv[1]);print(p.scheme+'://'+p.netloc)" "$URL")
curl -sSL --max-time 30 "$URL" -o "$OUT/index.html"
NET="$(dirname "$OUT")/network.json"
{ grep -oE '(src|href)="[^"]+\.(js|mjs|css)[^"]*"' "$OUT/index.html" | sed -E 's/^(src|href)="//; s/"$//'
  [ -f "$NET" ] && python3 -c "import json,sys;[print(r[1]) for r in json.load(open(sys.argv[1])) if r[0] in ('script','link','css') or r[1].split('?')[0].endswith(('.js','.css','.mjs'))]" "$NET"
} | sort -u | while read -r u; do
  case "$u" in http*) full="$u";; //*) full="https:$u";; /*) full="$ORIGIN$u";; *) full="$ORIGIN/$u";; esac
  f="$OUT/$(basename "${u%%\?*}")"; [ -f "$f" ] || curl -sSL --max-time 30 "$full" -o "$f" || true
done
ls "$OUT" | wc -l | xargs echo "files saved:"
