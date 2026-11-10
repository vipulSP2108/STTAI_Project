#!/bin/bash
set -eu
cd /app/code/a2_part_d_deployment

command=${1:-serve}
if [ "$#" -gt 0 ]; then shift; fi
case "$command" in
    validate) exec python -m revised_release validate "$@" ;;
    smoke) exec python -m revised_api_smoke "$@" ;;
    serve)
        uvicorn revised_api:app --host 0.0.0.0 --port 8000 &
        api=$!
        streamlit run revised_ui.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true --browser.gatherUsageStats=false &
        ui=$!
        trap 'kill "$api" "$ui" 2>/dev/null || true' EXIT
        trap 'exit 0' INT TERM
        wait -n "$api" "$ui"
        ;;
    *) echo "Expected serve, validate, or smoke" >&2; exit 2 ;;
esac
