#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "missing python3." >&2
  exit 1
fi

#install pip and any dependencies
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

#make launchable
chmod +x launch.sh sortify.py

echo
echo "Installed. Make sure to add your client ID and callback to .env"
