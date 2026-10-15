"""Local loaded-source identity; no prices or credentials are read."""
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def current():
    h=hashlib.sha256()
    for p in sorted([*ROOT.glob('*.py'),*(ROOT/'q1').glob('*.py')]):
        h.update(str(p.relative_to(ROOT)).replace('\\','/').encode())
        h.update(p.read_bytes().replace(b'\r\n',b'\n'))
    return h.hexdigest()


def data_revision():
    values=[]
    for p in sorted(ROOT.glob('.runtime/boxes_*')):
        if p.is_file(): values.append((p.name,p.stat().st_size,p.stat().st_mtime_ns))
    return hashlib.sha256(repr(values).encode()).hexdigest()


if __name__=='__main__':print(current())
