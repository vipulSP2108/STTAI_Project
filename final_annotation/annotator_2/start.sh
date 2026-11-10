#!/usr/bin/env bash
# Start Label Studio for Annotator 2
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_ROOT="$( cd "$DIR/../.." >/dev/null 2>&1 && pwd )"

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"
export LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
export LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="$PROJECT_ROOT"
export LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK=true
export SESSION_COOKIE_NAME=sessionid_a2

echo "Starting Label Studio Annotator 2 on port 8082..."
exec /Library/Frameworks/Python.framework/Versions/3.13/bin/label-studio start "Helpdesk Audio Annotation A2" \
  --data-dir "$DIR/data" \
  -p 8082 \
  -b \
  --username annotator2@institution.local \
  --password annotator2password

