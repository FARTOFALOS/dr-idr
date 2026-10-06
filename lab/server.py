"""Local-only, read-only prototype API and static site. Python standard library."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import importlib
engine = None

ROOT = Path(__file__).resolve().parent
DATA_KIND = 'SYNTHETIC'


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
            if url.path == '/api/health':
                return self.json({'status':'ok','data_kind':DATA_KIND,'version':engine.VERSION})
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
            if url.path == '/api/d24/now':
                # DR-LAB-NOW-1.0 (lab/now24.py): the layer «Сейчас» of the family at the slice; never the base map
                import now24
                inst = params.get('instrument', 'NQ')
                date = params.get('date') or None
                if date is not None and not re.fullmatch(r'20[0-2]\d-[01]\d-[0-3]\d', date):
                    raise ValueError('date: YYYY-MM-DD')
                at = params.get('at')
                return self.json(now24.live(inst, params.get('session', 'RDR'), int(float(at)) if at not in (None, '') else None,
                                            date, params.get('view', 'auto'), bool(params.get('debug'))))
            if url.path in ('/api/d24/day', '/api/d24/family', '/api/d24/dates'):
                # design 24 (lab/scene24.py): the statistical layer of DR-LAB-SEM-1.0; `date` = a trading date of
                # 2006-2025 shown as if it were today (its families use only earlier sessions), empty = the live day
                import scene24
                inst = params.get('instrument', 'NQ')
                date = params.get('date') or None
                if date is not None and not re.fullmatch(r'20[0-2]\d-[01]\d-[0-3]\d', date):
                    raise ValueError('date: YYYY-MM-DD')
                if url.path == '/api/d24/dates':
                    return self.json(scene24.dates(inst))
                if url.path == '/api/d24/day':
                    if not date and params.get('refresh'):
                        import live
                        try:
                            live.fetch(inst)
                        except Exception as exc:
                            return self.json({'status': 'error', 'message': str(exc)}, 200)
                    return self.json(scene24.day_view(inst, date))
                at = params.get('at')
                return self.json(scene24.family(inst, params.get('session', 'RDR'), int(float(at)) if at not in (None, '') else None,
                                                date, params.get('view', 'auto')))
            if url.path == '/api/spec':
                path = ROOT.parent/'docs'/'SEMANTICS.md'
                return self.json({'text':path.read_text(encoding='utf-8') if path.exists() else 'Смысловая спецификация готовится вместе с интерфейсом.'})
            if url.path.startswith('/api/'):
                return self.json({'error':'Неизвестный запрос'},404)
            # the working screen is design 24 since 2026-10-01 night (operator): the root opens it; design 22 stays next to
            # it at /22/ (its built page is /index.html, unchanged); the fragment of the address is kept by the browser
            if url.path == '/':
                return self.redirect('/24/')
            if url.path in ('/22', '/22/'):
                return self.redirect('/index.html')
            return super().do_GET()
        except (ValueError, TypeError) as exc:
            self.json({'error': str(exc)},400)
        except Exception:
            self.json({'error':'Не удалось выполнить локальный расчёт.'},500)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--data', choices=['market', 'demo'], default='market')
    args = parser.parse_args()
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
