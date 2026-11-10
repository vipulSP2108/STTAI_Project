#!/usr/bin/env bash
# Start Label Studio for Expert Annotator with Fatigue & Reliability telemetry
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_ROOT="$( cd "$DIR/../.." >/dev/null 2>&1 && pwd )"

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"
export LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
export LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="$PROJECT_ROOT"
export LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK=true
export SESSION_COOKIE_NAME=sessionid_expert

echo "Starting Label Studio Annotator Expert on port 8083..."
exec /Library/Frameworks/Python.framework/Versions/3.13/bin/label-studio start "Helpdesk Audio Annotation - Expert Adjudication" \
  --data-dir "$DIR/data" \
  -p 8083 \
  -b \
  --username expert@institution.local \
  --password expertpassword
