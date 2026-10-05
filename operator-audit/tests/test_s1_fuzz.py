"""Stage 1 §5: hostile input never produces a 5xx and always carries the error shape."""
import json, pytest
from kit import *
pytestmark = pytest.mark.s1

JUNK = [None, [], [1, 2], "str", 5, 1e308, -1, True, {}, {"a": {"b": [1, {"c": None}]}}, "x" * 100_000, "\u0000‮💥", {"restaurant_id": ["r_anker"]}, {"moves": "no"}, {"moves": [None]}, {"reference": {}}]
ROUTES = [("POST", "/auth/signup"), ("POST", "/auth/login"), ("POST", "/reservations"), ("POST", "/reservation-moves"), ("PATCH", "/reservations/ABC123"), ("POST", "/_test/import")]

@pytest.mark.parametrize("method,path", ROUTES)
def test_junk_bodies_never_5xx(reset, api, method, path):
    d = date(); world(reset, api); a = ada(api); k = {"idempotency_key": new_key()} if "reserv" in path and method == "POST" else {}
    for j in JUNK:
        r = a.request(method, path, json=j, **({"idempotency_key": new_key()} if k else {})) if j is not None else a.request(method, path, content=b"null", **k)
        assert r.status_code < 500, (path, str(j)[:40], r.text[:120])
        if r.status_code >= 400 and path != "/_test/import": assert "code" in r.json()["error"]

@pytest.mark.parametrize("raw_body", [b"", b"{", b"\xff\xfe", b"{\"a\":" + b"[" * 5000, b"\x00" * 1000, "{\"restaurant_id\":\"é\"}".encode("latin-1", "ignore")])
def test_raw_garbage_never_5xx(reset, api, raw_body):
    world(reset, api); a = ada(api)
    for path in ("/auth/signup", "/auth/login", "/reservations", "/reservation-moves"):
        r = a.post(path, content=raw_body, idempotency_key=new_key()); assert r.status_code < 500, (path, r.text[:100])

@pytest.mark.parametrize("path", ["/", "/nope", "/reservations/%00", "/reservations/../x", "/restaurants/" + "a" * 500, "/availability?restaurant_id[]=x&date[]=y", "/reservations?limit=-1&x=%ff"])
def test_odd_urls_never_5xx(reset, api, path):
    world(reset, api); a = ada(api); assert a.get(path).status_code < 500

def test_unicode_and_long_fields_are_handled(reset, api):
    world(reset, api); c = api()
    for dn in ("Zoë 💥", "x" * 10_000, "   "):
        assert c.signup(f"u{abs(hash(dn))}@example.com", "long enough", dn).status_code < 500
    assert c.signup("a" * 300 + "@example.com", "long enough", "L").status_code < 500
    assert c.request("GET", "/availability", params={"restaurant_id": "x" * 5000, "date": "2026-01-01", "party_size": 2}).status_code < 500

def test_every_method_on_every_route_is_clean(reset, api):
    world(reset, api); a = ada(api)
    for m in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        for p in ("/health", "/restaurants", "/availability", "/reservations", "/reservation-moves", "/auth/login", "/reservations/ABC123", "/reservations/ABC123/cancel"):
            r = a.request(m, p, idempotency_key=new_key()); assert r.status_code < 500, (m, p)
