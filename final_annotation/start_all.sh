#!/usr/bin/env bash
# Start all Label Studio instances in background (Annotator 1, Annotator 2, Annotator Expert)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "Starting Annotator 1 on port 8081..."
nohup "$DIR/annotator_1/start.sh" > "$DIR/annotator_1/label_studio.log" 2>&1 &
echo $! > "$DIR/annotator_1.pid"

echo "Starting Annotator 2 on port 8082..."
nohup "$DIR/annotator_2/start.sh" > "$DIR/annotator_2/label_studio.log" 2>&1 &
echo $! > "$DIR/annotator_2.pid"

echo "Starting Annotator Expert on port 8083..."
nohup "$DIR/annotator_expert/start.sh" > "$DIR/annotator_expert/label_studio.log" 2>&1 &
echo $! > "$DIR/annotator_expert.pid"

sleep 2

echo "Annotator 1 running at: http://localhost:8081 (PID: $(cat "$DIR/annotator_1.pid"))"
echo "Annotator 2 running at: http://localhost:8082 (PID: $(cat "$DIR/annotator_2.pid"))"
echo "Annotator Expert running at: http://localhost:8083 (PID: $(cat "$DIR/annotator_expert.pid"))"
