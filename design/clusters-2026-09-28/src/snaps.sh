#!/bin/sh
# Static snapshots of the artboards in several states (for visual review): ../snap/<board>_<state>.png
# usage: sh snaps.sh [filter]   (run from src/)
set -e
mkdir -p ../snap
shot() {  # board name state-json
  node render.js ../built/project/$1.dc.html "$3" ../snap/$1_$2.html >/dev/null
  (cd ../snap && sh ../src/shot.sh $1_$2.html $1_$2.png >/dev/null && echo "$1_$2.png")
}
F="${1:-}"
for b in Main Summary Projections; do
  case "$b" in *$F*) ;; *) continue ;; esac
  shot $b conf '{}'
  shot $b wait '{"scene":"wait","rp":{"sess":"RDR","at":640}}'
  shot $b brk '{"scene":"brk"}'
done
if [ "$F" = "hover" ]; then
  shot Main pick '{"pick":"blob|pull|1","hover":"blob|pull|1"}'
  shot Summary hover '{"scene":"brk","hover":"blob|cont|1"}'
  shot Projections pbin '{"hover":"col|870"}'
fi
