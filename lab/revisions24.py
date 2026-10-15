"""Content witnesses for consumers of full paths. BASE family/snapshot identities and measurements are unchanged."""
import hashlib
import json

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def path_revision(fam):
    return digest([fam.get('view'),fam.get('grid'),
                   [[m['id'],m['act'],m['w'],m.get('oppv'),m['path']] for m in fam.get('members',[])]])

def prefix_revision(bars,cut,tick):
    return digest([[int(b[0])+5,*[int(round(float(p)/tick)) for p in b[1:5]]]
                   for b in bars if int(b[0])+5<=cut])
