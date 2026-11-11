#!/usr/bin/env bash
# Round T (transcription) — start Label Studio for one annotator and load their tasks.
#
#   bash final_annotation/transcription_round/start_round_t.sh A1   # http://localhost:8091
#   bash final_annotation/transcription_round/start_round_t.sh A2   # http://localhost:8092
#   bash final_annotation/transcription_round/start_round_t.sh stop # stop both
#
# Each annotator gets an independent Label Studio database (ls_data_A1 / ls_data_A2), so neither
# can see the other's work. The first run creates the project, links the audio folder and imports
# double_100.json + single_<ID>.json; later runs just restart the server with the saved work.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
# Windows (Git Bash): Label Studio needs native C:/... paths
ROOT_NATIVE="$(cd "$ROOT" && (pwd -W 2>/dev/null || pwd))"
HERE_NATIVE="$(cd "$HERE" && (pwd -W 2>/dev/null || pwd))"
PY="$(command -v python3 || command -v python || true)"
LS="$(command -v label-studio || true)"
if [ -z "$PY" ] || [ -z "$LS" ]; then
  echo "Need Python 3 and Label Studio:  pip install label-studio==1.23.0"; exit 1
fi

if [ "${1:-}" = "stop" ]; then
  for id in A1 A2; do
    [ -f "$HERE/ls_data_$id/server.pid" ] && kill "$(cat "$HERE/ls_data_$id/server.pid")" 2>/dev/null && echo "stopped $id" || true
  done
  exit 0
fi

ID="${1:?usage: start_round_t.sh A1|A2|stop}"
case "$ID" in A1) PORT=8091 ;; A2) PORT=8092 ;; *) echo "use A1 or A2"; exit 2 ;; esac
DATA="$HERE/ls_data_$ID"; mkdir -p "$DATA" "$HERE/exports"
if [ ! -d "$ROOT/final_annotation/annotator_1/records" ]; then
  echo "Audio missing: unzip the Round T audio zip in the STTAI_Project folder so that"
  echo "  final_annotation/annotator_1/records/P1/... exists, then run this again."; exit 1
fi

# Local login for this machine only (not a real account). Created once, kept in ls_data_<ID>/login.txt.
if [ ! -f "$DATA/login.txt" ]; then
  printf 'email=%s\npassword=%s\ntoken=%s\n' "$(echo "$ID" | tr A-Z a-z)@roundt.local" \
    "$("$PY" -c 'import secrets;print(secrets.token_urlsafe(12))')" \
    "$("$PY" -c 'import secrets;print(secrets.token_hex(20))')" > "$DATA/login.txt"
fi
EMAIL=$(grep ^email "$DATA/login.txt" | cut -d= -f2); PASS=$(grep ^password "$DATA/login.txt" | cut -d= -f2)
TOKEN=$(grep ^token "$DATA/login.txt" | cut -d= -f2)

export LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
export LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="$ROOT_NATIVE"
export LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK=true
export LABEL_STUDIO_ENABLE_LEGACY_API_TOKEN=true
export SESSION_COOKIE_NAME="sessionid_roundt_$ID"

if curl -s "http://localhost:$PORT/health" >/dev/null 2>&1; then
  echo "Label Studio $ID already running on http://localhost:$PORT"
else
  echo "Starting Label Studio $ID on port $PORT (log: $DATA/server.log)"
  DATA_NATIVE="$(cd "$DATA" && (pwd -W 2>/dev/null || pwd))"
  nohup "$LS" start --data-dir "$DATA_NATIVE" -p "$PORT" --no-browser \
    --username "$EMAIL" --password "$PASS" --user-token "$TOKEN" > "$DATA/server.log" 2>&1 &
  echo $! > "$DATA/server.pid"
  for _ in $(seq 1 180); do curl -s "http://localhost:$PORT/health" >/dev/null 2>&1 && break; sleep 2; done
fi

"$PY" - "$PORT" "$TOKEN" "$ID" "$HERE_NATIVE" "$ROOT_NATIVE" <<'PY'
import json, sys, urllib.request
port, token, aid, here, root = sys.argv[1:]
base = f"http://localhost:{port}/api"
def call(method, path, body=None):
    req = urllib.request.Request(base + path, method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Token {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read() or b"{}")
projects = call("GET", "/projects?page_size=50")
projects = projects.get("results", projects)
if any(p["title"] == f"Round T transcripts {aid}" for p in projects):
    print("Project already set up; your saved work is intact.")
    sys.exit(0)
config = open(f"{here}/label_studio_config_transcript.xml").read()
p = call("POST", "/projects", {"title": f"Round T transcripts {aid}", "label_config": config,
                               "maximum_annotations": 1, "show_skip_button": False,
                               "show_collab_predictions": True, "model_version": "indic-asr-v2"})
storages_to_add = [
    ("recordings", f"{root}/final_annotation/annotator_1/records"),
    ("recordings_2", f"{root}/final_annotation/annotator_2/records"),
    ("recordings_expert", f"{root}/final_annotation/annotator_expert/records"),
    ("recordings_master", f"{root}/final_annotation/records"),
    ("recordings_root", f"{root}")
]
for stitle, spath in storages_to_add:
    try:
        call("POST", "/storages/localfiles", {"project": p["id"], "title": stitle,
                                              "path": spath, "use_blob_urls": False})
    except Exception:
        pass
tasks = json.load(open(f"{here}/double_100.json")) + json.load(open(f"{here}/single_{aid}.json"))
call("POST", f"/projects/{p['id']}/import", tasks)
print(f"Project created with {len(tasks)} tasks (100 shared + {len(tasks) - 100} only yours).")
PY

echo
echo "Open http://localhost:$PORT and log in with the email/password in:"
echo "  $DATA/login.txt"
echo "When finished: project -> Export -> JSON -> save the file unchanged as"
echo "  final_annotation/transcription_round/exports/${ID}.json"
