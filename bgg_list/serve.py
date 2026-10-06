"""Serve the web page, telling browsers to check for changes on every visit.

    python3 -m bgg_list.serve [--port 8000] [--directory site]
"""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# The page in a clone of the repository (or in the container)
SITE = Path(__file__).resolve().parent.parent / "site"

class NoCacheHandler(SimpleHTTPRequestHandler):
    # Without this, browsers may keep using an old app.js or style.css after the page
    # changes; with it they check first, which costs a quick 304 when nothing changed
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

def create_server(directory=SITE, port=8000):
    return ThreadingHTTPServer(("", port), partial(NoCacheHandler, directory=str(directory)))

def main(argv=None):
    parser = argparse.ArgumentParser(description="Serve the bgg-list web page.")
    parser.add_argument('--port', type=int, default=8000, help='Port to listen on (default: %(default)s)')
    parser.add_argument('--directory', default=SITE, help='Folder to serve (default: the repository\'s site folder)')
    args = parser.parse_args(argv)

    with create_server(args.directory, args.port) as server:
        print(f"Serving {args.directory} at http://localhost:{args.port}/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
