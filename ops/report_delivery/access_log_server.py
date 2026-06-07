from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, List
from urllib.parse import parse_qs, urlsplit


class LogHandler(BaseHTTPRequestHandler):
    log_path: Path = Path("access.log")

    def do_GET(self) -> None:
        parts = urlsplit(self.path)
        params = parse_qs(parts.query)
        event = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "report_id": _get_param(params, "report_id"),
            "token_id": _get_param(params, "token_id"),
            "event": _get_param(params, "event"),
            "ip": self.client_address[0],
            "user_agent": self.headers.get("User-Agent", ""),
            "path": parts.path,
        }
        self._write_log(event)

        redirect = _get_param(params, "redirect")
        if redirect:
            self.send_response(302)
            self.send_header("Location", redirect)
            self.end_headers()
            return

        self.send_response(204)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:
        return

    def _write_log(self, event: Dict[str, str]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")


def _get_param(params: Dict[str, List[str]], name: str) -> str:
    values = params.get(name) or []
    return values[0] if values else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple access log endpoint for report delivery")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--log-path", default="ops/report_delivery/access.log")
    args = parser.parse_args()

    LogHandler.log_path = Path(args.log_path)
    server = HTTPServer((args.host, args.port), LogHandler)
    print(f"Listening on {args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
