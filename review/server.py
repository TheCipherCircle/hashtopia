#!/usr/bin/env python3
"""
QA Portal Server

Serves the QA Portal and proxies asset requests to project directories.
"""

import http.server
import socketserver
import os
from pathlib import Path
from urllib.parse import unquote

PORT = 8888
REVIEW_DIR = Path(__file__).parent

# Map URL prefixes to actual directories
PROJECT_ROOTS = {
    '/SpellEngine/': Path('/Users/petermckernan/Projects/SpellEngine'),
    '/HashChampions/': Path('/Users/petermckernan/Projects/HashChampions'),
}

class QAPortalHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REVIEW_DIR), **kwargs)

    def translate_path(self, path):
        """Translate URL path to filesystem path, checking project roots."""
        path = unquote(path)

        # Check if path matches any project root
        for url_prefix, fs_root in PROJECT_ROOTS.items():
            if path.startswith(url_prefix):
                # Map to the project directory
                relative_path = path[len(url_prefix):]
                full_path = fs_root / relative_path
                return str(full_path)

        # Default: serve from review directory
        return super().translate_path(path)

    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def log_message(self, format, *args):
        # Cleaner logging
        path = args[0].split()[1] if args else ''
        status = args[1] if len(args) > 1 else ''
        if status == '200':
            return  # Don't log successful requests
        print(f"  {status} {path}")


def main():
    os.chdir(REVIEW_DIR)

    with socketserver.TCPServer(("", PORT), QAPortalHandler) as httpd:
        print("=" * 60)
        print("   QA PORTAL SERVER")
        print("=" * 60)
        print()
        print(f"   URL: http://localhost:{PORT}")
        print()
        print("   Serving:")
        print(f"     • Review Portal: {REVIEW_DIR}")
        for url, path in PROJECT_ROOTS.items():
            exists = "✓" if path.exists() else "✗"
            print(f"     {exists} {url} → {path}")
        print()
        print("   Press Ctrl+C to stop")
        print("=" * 60)
        print()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n   Server stopped.")


if __name__ == "__main__":
    main()
