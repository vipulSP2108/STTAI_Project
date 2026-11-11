#!/usr/bin/env bash
# Round T — export one annotator's Label Studio work to exports/<ID>.json (raw JSON export,
# exactly what Export -> JSON in the UI produces), ready to commit and push.
#
#   bash final_annotation/transcription_round/export_round_t.sh A1
#   bash final_annotation/transcription_round/export_round_t.sh A2
#
# Starts that annotator's Label Studio if it is not running, exports, and leaves it running.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ID="${1:?usage: export_round_t.sh A1|A2}"
case "$ID" in A1) PORT=8091 ;; A2) PORT=8092 ;; *) echo "use A1 or A2"; exit 2 ;; esac
LOGIN="$HERE/ls_data_$ID/login.txt"
[ -f "$LOGIN" ] || { echo "No Label Studio data for $ID on this computer ($LOGIN)"; exit 1; }
curl -s "http://localhost:$PORT/health" >/dev/null 2>&1 || bash "$HERE/start_round_t.sh" "$ID" >/dev/null
TOKEN=$(grep ^token "$LOGIN" | cut -d= -f2)
PY="$(command -v python3 || command -v python)"
mkdir -p "$HERE/exports"
"$PY" - "$PORT" "$TOKEN" "$ID" "$HERE/exports/$ID.json" <<'PY'
import json, sys, urllib.request
port, token, aid, out = sys.argv[1:]
def get(path):
    req = urllib.request.Request(f"http://localhost:{port}/api{path}", headers={"Authorization": f"Token {token}"})
    with urllib.request.urlopen(req) as r:
        return r.read()
projects = json.loads(get("/projects?page_size=50"))
projects = projects.get("results", projects)
pid = next(p["id"] for p in projects if p["title"] == f"Round T transcripts {aid}")
raw = get(f"/projects/{pid}/export?exportType=JSON")
open(out, "wb").write(raw)
tasks = json.loads(raw)
done = sum(1 for t in tasks if any(not a.get("was_cancelled") for a in t.get("annotations", [])))
print(f"Exported {aid}: {done} annotated clips -> {out}")
PY
