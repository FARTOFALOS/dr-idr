"""Build design 23 SEM-1.0 prototype into lab/dist/sem-v1 without touching working design 22."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
OUT=REPO/"lab"/"dist"/"sem-v1"
OUT.mkdir(parents=True,exist_ok=True)
for name in ("index.html","app.js","style.css"):
    (OUT/name).write_text((HERE/name).read_text(encoding="utf-8"),encoding="utf-8")
print("built", OUT)
