"""A source failure must preserve cache bytes/timestamp; concurrent readers see complete JSON."""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lab'))
import live
import dr_voice

m1=[[t,1,2,0,1] for t in range(0,600,60)]
assert len(live.aggregate_m1(m1,600))==2
assert [b[0] for b in live.aggregate_m1(m1[1:],600)]==[300]
assert [b[0] for b in live.aggregate_m1([b for b in m1 if b[0]!=120],600)]==[300]
assert len(live.aggregate_m1(m1[:7],370))==2  # forming M5 is kept only from its true start
print('PASS: M1 fallback never labels partial/gapped groups as completed M5')

with tempfile.TemporaryDirectory() as folder:
    dest=Path(folder)
    old={'fetched_at':'2020-01-01T00:00:00Z','bars':[[1,1,1,1,1]]}
    cache=dest/'nq.json';cache.write_text(json.dumps(old),encoding='utf-8');before=cache.read_bytes()
    with patch.object(live,'LIVE',dest), patch.object(live,'_tv',return_value=SimpleNamespace(stdout='{"success":false,"error":"missing pane"}',stderr='')):
        try: live.fetch('NQ')
        except RuntimeError: pass
        else: raise AssertionError('missing source accepted')
    assert cache.read_bytes()==before
    good={'success':True,'interval':'5','feed':'CME_MINI:NQ1!','switched':False,'bars':[[1700000000+i*300,1,2,0,1] for i in range(300)]}
    with patch.object(live,'LIVE',dest), patch.object(live,'_tv',return_value=SimpleNamespace(stdout=json.dumps(good),stderr='')):
        value=live.fetch('NQ')
    assert json.loads(cache.read_text())==value and not value['switched']
    assert not (dest/'nq.tmp').exists()
print('PASS: failed source preserves prior cache, successful M5 refresh publishes complete JSON')

# One broken source must not block the other two or make their timestamps stale.
class StopAfterCycle:
    stopped=False
    def is_set(self): return self.stopped
    def clear(self): self.stopped=False
    def wait(self, seconds):
        assert 1 <= seconds <= 63
        self.stopped=True
class InlineThread:
    def __init__(self, target, **kwargs): self.target=target
    def start(self): self.target()
calls=[]
def source(inst):
    calls.append(inst)
    if inst=='ES': raise RuntimeError('source missing')
    return {'fetched_at':'2026-11-06T16:00:03Z'}
with tempfile.TemporaryDirectory() as folder:
    with patch.object(live,'LIVE',Path(folder)), patch.object(live,'_minute_thread',None), \
         patch.object(live,'_minute_stop',StopAfterCycle()), patch.object(live.threading,'Thread',InlineThread), \
         patch.object(live,'fetch',side_effect=source), patch.object(dr_voice,'start'), patch.object(dr_voice,'observe'):
        live.start_minute_refresh()
        status=json.loads((Path(folder)/'refresh_status.json').read_text())
        assert calls==['NQ','ES','YM']
        assert status['NQ']['ok'] and status['YM']['ok'] and not status['ES']['ok']
        assert 'fetched_at' not in status['ES']
print('PASS: minute worker visits all three instruments and isolates missing-source failures')
