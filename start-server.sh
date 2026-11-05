#!/bin/sh
# Starts the real server (real accounts, passwords and two-step login). Needs Python 3.
cd "$(dirname "$0")" || exit 1
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
echo "Starting the shop server. Keep this window open. Stop it with Ctrl+C."
( sleep 2; (command -v xdg-open >/dev/null && xdg-open http://localhost:8000/admin/login.html) || (command -v open >/dev/null && open http://localhost:8000/admin/login.html) ) >/dev/null 2>&1 &
exec $PY server/server.py "$@"
