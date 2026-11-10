import sys
import queue
import tempfile
from pathlib import Path
from unittest.mock import patch
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'lab'))
import dr_voice as voice

day=pd.Timestamp('2026-11-06',tz='America/New_York')
def raw(now=645, missing=None, close=111, high=111, low=89, extra=()):
    rows=[[t,92,110,90,108] for t in range(570,630,5)]
    rows += [[630,108,120,99,110],[635,110,125,99,109],[640,109,high,low,close]]
    rows += list(extra)
    return dict(fetched_at=(day+pd.Timedelta(minutes=now)).isoformat(),
                bars=[[(day+pd.Timedelta(minutes=b[0])).timestamp(),*b[1:]] for b in rows if b[0]!=missing])

assert voice.session_events('NQ',raw(644.99))==[]  # forming bar/wicks/equality do not confirm
events=voice.session_events('NQ',raw())
assert len(events)==1 and events[0]['session']=='RDR'
assert events[0]['closed_at']==(day+pd.Timedelta(minutes=645)).timestamp()
assert len(voice.session_events('YM',raw(close=89)))==1
assert voice.session_events('NQ',raw(missing=635))==[]  # cannot know the FIRST close through a gap
assert voice.session_events('NQ',raw(missing=625))==[]
assert voice.session_events('NQ',raw(now=964))==[]  # no late-session/replay narration

def sd_events(inst, sample):
    return [event for event in voice.session_events(inst, sample) if 'sd' in event]

# IDR = [92,108]. The first extension is 116/124 for longs and 84/76 for shorts.
assert sd_events('NQ',raw(649.99,extra=[[645,111,124,108,112]]))==[]
sample=raw(655,extra=[[645,111,116,108,112],[650,112,124,111,114]])
reaches=sd_events('NQ',sample)
assert [(e['sd'],e['closed_at']) for e in reaches]==[
    (0.5,(day+pd.Timedelta(minutes=650)).timestamp()),
    (1,(day+pd.Timedelta(minutes=655)).timestamp())]
assert [e['sd'] for e in sd_events('ES',raw(high=124))]==[0.5,1]
assert [e['sd'] for e in sd_events('YM',raw(close=89,low=76))]==[0.5,1]
assert sd_events('NQ',raw(655,extra=[[650,112,124,111,114]]))==[]  # gap after confirmation
assert sd_events('NQ',raw(650,extra=[[645,111,124,89,89]]))==[]  # no claim on the break candle
late_bars=[[t,111,112,108,111] for t in range(645,955,5)]+[[955,111,116,108,112]]
assert [e['sd'] for e in sd_events('NQ',raw(960.05,extra=late_bars))]==[0.5]

event=events[0]; stamp=event['closed_at']
with tempfile.TemporaryDirectory() as folder:
    q=queue.Queue()
    with patch.object(voice,'RUNTIME',Path(folder)), patch.object(voice,'_queue',q), \
         patch.object(voice,'_started',stamp-60), patch.object(voice.time,'time',return_value=stamp+4):
        voice.observe('NQ',raw());voice.observe('NQ',raw())
        assert q.qsize()==1
        voice.observe('ES',raw());voice.observe('YM',raw())
        assert q.qsize()==3
    with patch.object(voice,'_queue',q), patch.object(voice,'_started',stamp+1):
        voice.observe('NQ',raw())
        assert q.qsize()==3
    level_queue=queue.Queue()
    with patch.object(voice,'RUNTIME',Path(folder)), patch.object(voice,'_queue',level_queue), \
         patch.object(voice,'_started',stamp+1), patch.object(voice.time,'time',return_value=reaches[-1]['closed_at']+4):
        voice.observe('NQ',sample)
        voice.observe('NQ',sample)
        assert level_queue.qsize()==1  # only +1 SD was reached on a full M5 after startup
        assert level_queue.get_nowait()['sd']==1
    with patch.object(voice,'_queue',level_queue), patch.object(voice,'_started',stamp-301), \
         patch.object(voice.time,'time',return_value=reaches[-1]['closed_at']+181):
        voice.observe('YM',sample)
        assert level_queue.empty()  # old observations cannot turn into fresh announcements
print('PASS: closed-M5 activation and SD reaches, long/short, all instruments, gaps, break, startup, dedup')
