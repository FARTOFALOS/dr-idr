"""HTTP boundaries of the new candidate route, in a private ephemeral localhost server."""
import json,sys,threading,urllib.error,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab'))
import server as S
srv=S.ThreadingHTTPServer(('127.0.0.1',0),S.Handler)
worker=threading.Thread(target=srv.serve_forever,daemon=True);worker.start()
base='http://127.0.0.1:'+str(srv.server_port)
def get(path):
    try:r=urllib.request.urlopen(base+path,timeout=20)
    except urllib.error.HTTPError as e:r=e
    with r:return r.status,json.loads(r.read())
try:
    S.INTEGRATION=False
    code,p=get('/api/integration/time-sd')
    assert code==403 and p['status']=='INTEGRATION_DISABLED'
    print('PASS new route is disabled outside the explicit integration server')
    S.INTEGRATION=True
    S.START_SOURCE_REVISION='deliberately stale test identity'
    code,p=get('/api/integration/time-sd')
    assert code==409 and p['status']=='SOURCE_CHANGED' and 'proof' not in p
    print('PASS stale loaded source withdraws the candidate before any calculation')
    S.START_SOURCE_REVISION=S.runtime_identity.current()
    S.START_DATA_REVISION=S.runtime_identity.data_revision()
    code,p=get('/api/integration/time-sd?instrument=NQ&session=RDR&date=2026-01-01&at=670')
    assert code==200 and p['status']=='OUT_OF_SCOPE' and 'proof' not in p
    print('PASS HTTP route cannot read closed 2026 history')
    code,p=get('/api/integration/time-sd?date=2025-12-17&at=670&region=%5Btrue,1,0,1%5D')
    assert code==400 and 'error' in p
    print('PASS malformed region is rejected rather than becoming a zero')
    print('ALL GOOD 4')
finally:srv.shutdown();srv.server_close();worker.join()
