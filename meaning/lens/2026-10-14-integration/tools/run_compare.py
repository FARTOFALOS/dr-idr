"""Run two frozen local backends and the shared headless comparison collector; always stop owned processes."""
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PACKAGE=ROOT/'meaning/lens/2026-10-14-integration'
LOCAL=ROOT/'lab/.runtime/integration-spec'

def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        port=s.getsockname()[1]
    if port in (8767,8771,8772): return free_port()
    return port

def main():
    procs=[]; logs=[]; urls=[]
    env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    tmp=LOCAL/'tmp'; tmp.mkdir(parents=True,exist_ok=True)
    env['TEMP']=env['TMP']=str(tmp)
    try:
        for variant in ('accepted','candidate'):
            folder=LOCAL/variant; port=free_port(); url=f'http://127.0.0.1:{port}'
            log=(LOCAL/(variant+'.log')).open('w',encoding='utf-8'); logs.append(log)
            proc=subprocess.Popen([sys.executable,'-B',str(folder/'lab/server.py'),'--port',str(port)],cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT)
            procs.append(proc); urls.append(url)
            for _ in range(180):
                if proc.poll() is not None: raise RuntimeError(variant+' exited; inspect its local log')
                try:
                    with urllib.request.urlopen(url+'/24/',timeout=2) as r:
                        if r.status==200: break
                except (OSError,TimeoutError): time.sleep(.5)
            else: raise TimeoutError(variant+' did not start')
            print('READY '+variant+' on isolated loopback port',flush=True)
        collector='checks.mjs' if '--checks' in sys.argv else 'compare.mjs'
        subprocess.run(['C:/Program Files/nodejs/node.exe',str(PACKAGE/'tools'/collector),*urls],cwd=ROOT,env=env,check=True,timeout=900)
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=10)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=10)
        for log in logs: log.close()

if __name__=='__main__': main()
