#!/usr/bin/env bash
# Stop all Label Studio instances (Annotator 1, Annotator 2, Annotator Expert)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [ -f "$DIR/annotator_1.pid" ]; then
    PID1=$(cat "$DIR/annotator_1.pid")
    echo "Stopping Annotator 1 (PID: $PID1)..."
    kill -9 "$PID1" 2>/dev/null || true
    rm -f "$DIR/annotator_1.pid"
fi

if [ -f "$DIR/annotator_2.pid" ]; then
    PID2=$(cat "$DIR/annotator_2.pid")
    echo "Stopping Annotator 2 (PID: $PID2)..."
    kill -9 "$PID2" 2>/dev/null || true
    rm -f "$DIR/annotator_2.pid"
fi

if [ -f "$DIR/annotator_expert.pid" ]; then
    PID3=$(cat "$DIR/annotator_expert.pid")
    echo "Stopping Annotator Expert (PID: $PID3)..."
    kill -9 "$PID3" 2>/dev/null || true
    rm -f "$DIR/annotator_expert.pid"
fi

# Fallback check on ports 8081, 8082, and 8083
lsof -ti :8081 | xargs kill -9 2>/dev/null || true
lsof -ti :8082 | xargs kill -9 2>/dev/null || true
lsof -ti :8083 | xargs kill -9 2>/dev/null || true

echo "All Label Studio instances stopped."
