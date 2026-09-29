#!/bin/sh
# Snapshots of design 22 in its states (headless Chrome, 1920x1000) into ../snap/ (git-ignored), for looking before
# saying "done". The pictures used by meaning/ and the history page are copied from here by make_history.py.
# usage: sh shots.sh            (run from src/ after python build.py)
cd "$(dirname "$0")/.." || exit 1
W="$(pwd -W 2>/dev/null || pwd)"
mkdir -p snap
for s in "conf" "wait" "brk" "conf&hl=1" "conf&hl=3" "wait&hl=3" "conf&strip=1"; do
  n=$(echo "$s" | tr '&=:' '___')
  timeout 90 "/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=1 --window-size=1920,1000 --user-data-dir="$W/snap/.chrome" \
    --screenshot="$W/snap/$n.png" "file:///$W/built/index.html#$s" >/dev/null 2>&1
  echo "snap/$n.png"
done
rm -rf snap/.chrome
