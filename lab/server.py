"""Local-only, read-only prototype API and static site. Python standard library."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import importlib
import contract   # DR-LAB-SC-1.1: the semantic gate (stdlib; reads contract/build, see lab/contract.py)
import runtime_identity
START_SOURCE_REVISION=runtime_identity.current()
START_DATA_REVISION=runtime_identity.data_revision()
engine = None

ROOT = Path(__file__).resolve().parent
DATA_KIND = 'SYNTHETIC'
INTEGRATION = False


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT/'dist'), **kwargs)

    def end_headers(self):
        # the page must never run a stale copy after an update (the operator only reloads or reopens)
        if not self.path.startswith('/api/'):
            self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def log_message(self, fmt, *args):
        if len(args)>1 and str(args[1]) not in ('200','304'):
            super().log_message(fmt, *args)

    def json(self, value, status=200):
        data = json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        # every route says which profile of DR-LAB-SC-1.1 its content belongs to (legacy routes: OUTSIDE_SC11)
        self.send_header('X-DR-Lab-Contract', contract.header_for(urlparse(self.path).path))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, where):
        self.send_response(302)
        self.send_header('Location', where)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        params = {k:v[-1] for k,v in parse_qs(url.query).items()}
        try:
            if url.path == '/integration-config.js':
                import integration24
                data=('window.DR_INTEGRATION='+json.dumps(integration24.configuration(INTEGRATION),ensure_ascii=False)+';').encode('utf-8')
                self.send_response(200); self.send_header('Content-Type','application/javascript; charset=utf-8')
                self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
            if url.path in ('/api/integration/scene','/api/integration/audit'):
                if not INTEGRATION:
                    return self.json(dict(status='INTEGRATION_DISABLED'),403)
                import integration24
                date=params.get('date') or None
                if date is not None and not re.fullmatch(r'20[0-2]\d-[01]\d-[0-3]\d',date): raise ValueError('date: YYYY-MM-DD')
                packet=integration24.scene(params.get('instrument','NQ'),params.get('session','RDR'),
                    int(params['at']),date,params.get('view','auto'),params.get('scope','weekday'),
                    [k for k in params.get('trials','').split(',') if k])
                if url.path.endswith('/audit'):
                    if packet.get('status')!='OK' or params.get('context')!=packet['context']['id']:
                        return self.json(dict(status='SCENE_CHANGED'))
                    import integration_audit
                    packet=integration_audit.audit(packet,dict(instrument=params.get('instrument','NQ'),session=params.get('session','RDR'),date=date,scope=params.get('scope','weekday'),view=params.get('view','auto')))
                return self.json(packet)
            if url.path == '/api/integration/time-sd':
                if not INTEGRATION:return self.json(dict(status='INTEGRATION_DISABLED'),403)
                if START_SOURCE_REVISION!=runtime_identity.current() or START_DATA_REVISION!=runtime_identity.data_revision():
                    return self.json(dict(status='SOURCE_CHANGED',message='Сборка или история обновилась: откройте DR Lab заново'),409)
                date=params.get('date') or None
                if date is not None and not re.fullmatch(r'20[0-2]\d-[01]\d-[0-3]\d',date):raise ValueError('date: YYYY-MM-DD')
                import time_sd235
                value=time_sd235.response(dict(instrument=params.get('instrument','NQ'),session=params.get('session','RDR'),at=params.get('at','0'),
                    date=date,view=params.get('view','auto'),scope=params.get('scope','weekday'),scale=params.get('scale','1'),region=params.get('region'),link=params.get('link')))
                if START_SOURCE_REVISION!=runtime_identity.current() or START_DATA_REVISION!=runtime_identity.data_revision():
                    return self.json(dict(status='SOURCE_CHANGED',message='Во время расчёта обновились исходники или история'),409)
                return self.json(value)
            if url.path == '/api/integration/pullbacks':
                # DR-LAB-PB-0.1 (lab/pullbacks24.py): the candidate «Откаты перед обновлением экстремума» over the family on
                # screen; its own envelope from the candidate registry, never the accepted map
                if not INTEGRATION: return self.json(dict(status='INTEGRATION_DISABLED'),403)
                if START_SOURCE_REVISION!=runtime_identity.current() or START_DATA_REVISION!=runtime_identity.data_revision():
                    return self.json(dict(status='SOURCE_CHANGED',message='Сборка или история обновилась: откройте DR Lab заново'),409)
                date=params.get('date') or None
                if date is not None and not re.fullmatch(r'20[0-2]\d-[01]\d-[0-3]\d',date): raise ValueError('date: YYYY-MM-DD')
                import pullbacks24
                value=pullbacks24.response(dict(instrument=params.get('instrument','NQ'),session=params.get('session','RDR'),at=params.get('at','0'),
                                                date=date,view=params.get('view','auto'),scope=params.get('scope','weekday'),region=params.get('region')))
                if START_SOURCE_REVISION!=runtime_identity.current() or START_DATA_REVISION!=runtime_identity.data_revision():
                    return self.json(dict(status='SOURCE_CHANGED',message='Во время расчёта обновились исходники или история'),409)
                return self.json(value)
            if url.path == '/api/health':
                return self.json({'status':'ok','data_kind':DATA_KIND,'version':engine.VERSION,'integration':INTEGRATION,'workspace':str(ROOT.parent),
                                  'source_revision':START_SOURCE_REVISION,'current_source_revision':runtime_identity.current(),
                                  'data_revision':START_DATA_REVISION,'current_data_revision':runtime_identity.data_revision()})
            if url.path == '/api/query':
                return self.json(engine.query(params))
            if url.path == '/api/scene':
                value = engine.scene(params.get('id',''))
                return self.json(value or {'error':'Сцена не найдена'}, 200 if value else 404)
            if url.path in ('/api/live', '/api/live/refresh'):
                import live
                inst = params.get('instrument', 'NQ'); session = params.get('session', 'RDR')
                if url.path.endswith('/refresh'):
                    try:
                        live.fetch(inst)
                    except Exception as exc:
                        return self.json({'status': 'error', 'message': str(exc)}, 200)
                at = params.get('at')
                return self.json(live.state(inst, session, int(float(at)) if at not in (None, '') else None))
            if url.path in ('/api/day', '/api/day/refresh', '/api/cohort', '/api/family', '/api/family-v1'):
                import live, scene21
                inst = params.get('instrument', 'NQ')
                if url.path == '/api/day/refresh':
                    try:
                        live.fetch(inst)
                    except Exception as exc:
                        return self.json({'status': 'error', 'message': str(exc)}, 200)
                if url.path in ('/api/cohort', '/api/family', '/api/family-v1'):
                    at = params.get('at')
                    if url.path == '/api/cohort':
                        fn = scene21.cohort
                    elif url.path == '/api/family-v1':
                        fn = scene21.family_sem_v1
                    else:
                        fn = scene21.family
                    return self.json(fn(inst, params.get('session', 'RDR'), int(float(at)) if at not in (None, '') else None))
                return self.json(scene21.day_view(inst))
            if url.path == '/api/contract':
                # DR-LAB-SC-1.1: the compiled machine contract (registry, stamps) and its runtime status
                return self.json(contract.public_registry())
            if url.path in ('/api/d24/family', '/api/d24/now') and contract.stale():
                # a stale executable contract publishes no statistic (fail closed); the reasons are in the envelope
                return self.json(contract.stale_response(url.path, params))
            if url.path == '/api/d24/now':
                # DR-LAB-NOW-1.0 (lab/now24.py): the layer «Сейчас» of the family at the slice; never the base map
                import now24
                inst = params.get('instrument', 'NQ')
                date = params.get('date') or None
                if date is not None and not re.fullmatch(r'20[0-2]\d-[01]\d-[0-3]\d', date):
                    raise ValueError('date: YYYY-MM-DD')
                at = params.get('at')
                return self.json(contract.finalize(url.path, now24.live(inst, params.get('session', 'RDR'), int(float(at)) if at not in (None, '') else None,
                                                                        date, params.get('view', 'auto'), bool(params.get('debug')))))
            if url.path in ('/api/d24/day', '/api/d24/family', '/api/d24/dates'):
                # design 24 (lab/scene24.py): the statistical layer of DR-LAB-SEM-1.0; `date` = a trading date of
                # 2006-2025 shown as if it were today (its families use only earlier sessions), empty = the live day
                import scene24
                inst = params.get('instrument', 'NQ')
                date = params.get('date') or None
                if date is not None and not re.fullmatch(r'20[0-2]\d-[01]\d-[0-3]\d', date):
                    raise ValueError('date: YYYY-MM-DD')
                if url.path == '/api/d24/dates':
                    return self.json(contract.finalize(url.path, scene24.dates(inst)))
                if url.path == '/api/d24/day':
                    if not date and params.get('refresh'):
                        import live
                        try:
                            live.fetch(inst)
                        except Exception as exc:
                            return self.json({'status': 'error', 'message': str(exc)}, 200)
                    return self.json(contract.finalize(url.path, contract.attach_day(scene24.day_view(inst, date), dict(instrument=inst, date=date))))
                at = params.get('at')
                return self.json(contract.finalize(url.path, scene24.family(inst, params.get('session', 'RDR'), int(float(at)) if at not in (None, '') else None,
                                                                            date, params.get('view', 'auto'))))
            if url.path == '/api/spec':
                path = ROOT.parent/'docs'/'SEMANTICS.md'
                return self.json({'text':path.read_text(encoding='utf-8') if path.exists() else 'Смысловая спецификация готовится вместе с интерфейсом.'})
            if url.path.startswith('/api/'):
                return self.json({'error':'Неизвестный запрос'},404)
            # the main screen is 23.5 since 2026-10-27 (operator: «23.5 стал основным экраном»): the root opens it; screen 24
            # (the main screen from 2026-10-01 night) stays at /24/, design 22 at /22/ (its built page is /index.html);
            # the fragment of the address is kept by the browser
            if url.path == '/':
                return self.redirect('/23-5/')
            if url.path in ('/22', '/22/'):
                return self.redirect('/index.html')
            return super().do_GET()
        except (ValueError, TypeError) as exc:
            self.json({'error': str(exc)},400)
        except Exception:
            self.json({'error':'Не удалось выполнить локальный расчёт.'},500)
            raise

    def do_POST(self):
        # DR-LAB-SC-1.1: the page's own passports recomputed by the reference definitions (tests/ui_check24.js); the
        # only POST of this read-only server, it changes nothing
        url = urlparse(self.path)
        try:
            if url.path == '/api/integration/continuations':
                if not INTEGRATION: return self.json(dict(status='INTEGRATION_DISABLED'),403)
                if START_SOURCE_REVISION!=runtime_identity.current() or START_DATA_REVISION!=runtime_identity.data_revision():
                    return self.json(dict(status='SOURCE_CHANGED',message='Сборка или история обновилась: откройте DR Lab заново'),409)
                n=int(self.headers.get('Content-Length') or 0)
                if n>100_000: raise ValueError('body too large')
                req=json.loads(self.rfile.read(n).decode('utf-8') or '{}')
                import continuations24
                value=continuations24.response(req)
                if START_SOURCE_REVISION!=runtime_identity.current() or START_DATA_REVISION!=runtime_identity.data_revision():
                    return self.json(dict(status='SOURCE_CHANGED',message='Во время расчёта обновились исходники или история'),409)
                return self.json(value)
            if url.path != '/api/d24/verify':
                return self.json({'error': 'Неизвестный запрос'}, 404)
            n = int(self.headers.get('Content-Length') or 0)
            if n > 4_000_000: raise ValueError('body too large')
            req = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
            import scene24
            date = req.get('date') or None
            if date is not None and not re.fullmatch(r'20[0-2]\d-[01]\d-[0-3]\d', date):
                raise ValueError('date: YYYY-MM-DD')
            inst, session = req.get('instrument', 'NQ'), req.get('session', 'RDR')
            fam = scene24.family(inst, session, req.get('at'), date, req.get('view', 'auto'))
            if fam.get('status') != 'ok':
                return self.json({'status': fam.get('status'), 'mismatches': [], 'checked': 0})
            day = scene24.day_view(inst, date)
            bad = contract.verify_passports(fam, day.get('bars') or [], float(day.get('tick') or 0.25), req.get('passports') or [])
            return self.json({'status': 'ok', 'snapshot_id': fam['snapshot_id'], 'checked': len(req.get('passports') or []), 'mismatches': bad})
        except (ValueError, TypeError) as exc:
            self.json({'error': str(exc)}, 400)
        except Exception:
            self.json({'error': 'Не удалось выполнить локальный расчёт.'}, 500)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--data', choices=['market', 'demo'], default='market')
    parser.add_argument('--integration',action='store_true')
    args = parser.parse_args()
    if args.integration and args.data != 'market':
        parser.error('--integration requires --data market; synthetic and market scenes stay separate')
    INTEGRATION = args.integration
    engine = importlib.import_module('engine' if args.data == 'demo' else 'engine_market')
    DATA_KIND = 'SYNTHETIC' if args.data == 'demo' else 'MARKET'
    engine.initialize()
    server = ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'DR Lab ready: http://127.0.0.1:{args.port} · {DATA_KIND}',flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
