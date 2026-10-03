"""HTTP transport for the Tablekeeper service."""

from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

from tablekeeper.service import Service


LOGGER = logging.getLogger("tablekeeper.http")
ERROR_BODY = {"error": {"code": "malformed_request", "message": "Malformed request."}}


class TablekeeperHTTPServer(ThreadingHTTPServer):
    """Threaded server sharing the domain service across requests."""

    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 128

    def __init__(self, address: tuple[str, int], service: Service) -> None:
        super().__init__(address, RequestHandler)
        self.service = service


class RequestHandler(BaseHTTPRequestHandler):
    """Parse HTTP inputs and serialize Service.dispatch results."""

    server: TablekeeperHTTPServer

    def do_GET(self) -> None:
        self._dispatch()

    def do_HEAD(self) -> None:
        self._dispatch()

    def do_POST(self) -> None:
        self._dispatch()

    def do_PATCH(self) -> None:
        self._dispatch()

    def do_PUT(self) -> None:
        self._dispatch()

    def do_DELETE(self) -> None:
        self._dispatch()

    def do_OPTIONS(self) -> None:
        self._dispatch()

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        """Keep BaseHTTPRequestHandler protocol errors JSON and free of 5xx."""
        if code >= 500:
            LOGGER.warning("HTTP parser error %s: %s", code, message)
            self._send_json(400, ERROR_BODY)
            return
        self._send_json(code, ERROR_BODY)

    def _dispatch(self) -> None:
        try:
            parsed = urlsplit(self.path)
            query = self._query_values(parsed.query)
            headers = {name.lower(): value for name, value in self.headers.items()}
            body = self._read_json_body(parsed.path, headers)
            if body is _BODY_ERROR:
                return

            status, value = self.server.service.dispatch(
                self.command,
                unquote(parsed.path),
                query,
                headers,
                body,
            )
            self._send_dispatch_result(status, value)
        except (ConnectionError, BrokenPipeError):
            return
        except Exception:
            LOGGER.exception("Unexpected request handling failure for %s %s", self.command, self.path)
            self._send_json(400, ERROR_BODY)

    @staticmethod
    def _query_values(raw_query: str) -> dict[str, str]:
        values = parse_qs(raw_query, keep_blank_values=True)
        return {name: entries[0] for name, entries in values.items() if entries}

    def _read_json_body(self, path: str, headers: dict[str, str]) -> object | None:
        if self.command not in {"POST", "PATCH"}:
            return None

        raw_length = headers.get("content-length", "0")
        if not raw_length.isdecimal():
            self._send_json(400, ERROR_BODY)
            return _BODY_ERROR
        length = int(raw_length)
        if length == 0 and self.command == "POST" and path.endswith("/cancel"):
            return None
        if length == 0:
            self._send_json(400, ERROR_BODY)
            return _BODY_ERROR

        try:
            value = json.loads(
                self.rfile.read(length).decode("utf-8"),
                parse_constant=self._reject_constant,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            self._send_json(400, ERROR_BODY)
            return _BODY_ERROR
        if not isinstance(value, dict):
            self._send_json(400, ERROR_BODY)
            return _BODY_ERROR
        return value

    @staticmethod
    def _reject_constant(value: str) -> None:
        raise ValueError(f"Non-finite JSON constant: {value}")

    def _send_dispatch_result(self, status: int, value: object | None) -> None:
        if not isinstance(status, int) or isinstance(status, bool) or not 100 <= status <= 599:
            LOGGER.error("Service returned invalid HTTP status: %r", status)
            self._send_json(400, ERROR_BODY)
            return
        if status >= 500:
            LOGGER.error("Service returned forbidden server error status: %s", status)
            self._send_json(400, ERROR_BODY)
            return
        if status == 204:
            self.send_response(status)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send_json(status, value)

    def _send_json(self, status: int, value: object) -> None:
        try:
            payload = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (TypeError, ValueError):
            LOGGER.exception("Service produced a non-JSON response")
            status = 400
            payload = json.dumps(ERROR_BODY, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)


_BODY_ERROR = object()


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    with TablekeeperHTTPServer(("0.0.0.0", port), Service()) as server:
        LOGGER.info("Tablekeeper listening on 0.0.0.0:%s", port)
        server.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    main()
