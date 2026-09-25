#!/bin/sh
# usage: shot.sh in.html out.png  (headless Chrome, 1920x1000)
W="$(pwd -W)"
timeout 60 "/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 --window-size=1920,1000 --user-data-dir="$W/.chrome-profile" --screenshot="$W/$2" "file:///$W/$1" >/dev/null 2>&1
ls -la "$2" | awk '{print $5, $9}'
