"""Serve the bundled browser shell and assets before JSON API dispatch."""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from urllib.parse import unquote


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
STATIC_ROOT = (PACKAGE_ROOT / "static").resolve()
TEMPLATE_ROOT = (PACKAGE_ROOT / "templates").resolve()
SCREEN_PATHS = {"/", "/signup", "/login", "/lookup"}


def serve(handler, method: str, path: str) -> bool:
    """Write a browser response for an owned route; return False for API paths."""
    if method != "GET":
        return False
    if path in SCREEN_PATHS:
        return _send_file(handler, TEMPLATE_ROOT / "index.html", "text/html; charset=utf-8")
    if path.startswith("/static/"):
        asset = _static_path(path)
        if asset is None:
            body = json.dumps({"error": {"code": "not_found", "message": "Asset not found."}}).encode("utf-8")
            _send_bytes(handler, 404, body, "application/json; charset=utf-8")
            return True
        content_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
        if content_type.startswith(("text/", "application/javascript")):
            content_type += "; charset=utf-8"
        return _send_file(handler, asset, content_type)
    return False


def _static_path(path: str) -> Path | None:
    relative = unquote(path.removeprefix("/static/"))
    target = (STATIC_ROOT / relative).resolve()
    try:
        target.relative_to(STATIC_ROOT)
    except ValueError:
        return None
    return target if target.is_file() else None


def _send_file(handler, path: Path, content_type: str) -> bool:
    try:
        payload = path.read_bytes()
    except OSError:
        body = json.dumps({"error": {"code": "not_found", "message": "Page not found."}}).encode("utf-8")
        _send_bytes(handler, 404, body, "application/json; charset=utf-8")
        return True
    _send_bytes(handler, 200, payload, content_type)
    return True


def _send_bytes(handler, status: int, payload: bytes, content_type: str) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    if handler.command != "HEAD":
        handler.wfile.write(payload)
