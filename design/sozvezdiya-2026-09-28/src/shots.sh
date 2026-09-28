#!/bin/sh
# Snapshots of design 20 in its states (headless Chrome, 1920x1000) into ../snap/, for looking before saying "done".
# usage: sh shots.sh            (run from src/ after python build.py)
cd "$(dirname "$0")/.." || exit 1
W="$(pwd -W 2>/dev/null || pwd)"
mkdir -p snap
for s in "conf" "wait" "brk" "conf&pin=pull:1&strip=1" "conf&pin=pull:1&slice=14:00" "brk&pin=cont:1" "conf&band=pull:max" "conf&band=cont:max"; do
  n=$(echo "$s" | tr '&=:' '___')
  timeout 90 "/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=1 --window-size=1920,1000 --user-data-dir="$W/snap/.chrome" \
    --screenshot="$W/snap/$n.png" "file:///$W/built/index.html#$s" >/dev/null 2>&1
  echo "snap/$n.png"
done
rm -rf snap/.chrome
