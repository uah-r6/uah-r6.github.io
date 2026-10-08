"""Compatibility entry point for the structured submission browser regression."""
import argparse
import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('logical_submissions_ui',Path(__file__).with_name('verify-logical-submissions-ui.py'))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
verify=module.verify

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url');args=parser.parse_args()
    server=None
    if not args.url:
        handler=functools.partial(SimpleHTTPRequestHandler,directory=str(Path(__file__).resolve().parents[1]/'web/dist'))
        server=ThreadingHTTPServer(('127.0.0.1',0),handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        args.url=f'http://127.0.0.1:{server.server_port}/'
    try:verify(args.url)
    finally:
        if server:server.shutdown()
