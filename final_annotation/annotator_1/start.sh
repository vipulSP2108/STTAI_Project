#!/usr/bin/env bash
# Start Label Studio for Annotator 1
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_ROOT="$( cd "$DIR/../.." >/dev/null 2>&1 && pwd )"

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"
export LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
export LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="$PROJECT_ROOT"
export LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK=true
export SESSION_COOKIE_NAME=sessionid_a1

echo "Starting Label Studio Annotator 1 on port 8081..."
exec /Library/Frameworks/Python.framework/Versions/3.13/bin/label-studio start "Helpdesk Audio Annotation A1" \
  --data-dir "$DIR/data" \
  -p 8081 \
  -b \
  --username annotator1@institution.local \
  --password annotator1password

