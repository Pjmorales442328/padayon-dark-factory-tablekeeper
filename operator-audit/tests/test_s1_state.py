"""Stage 1 §10: export and import."""
import httpx, pytest
from kit import *
pytestmark = pytest.mark.s1

def export(base): r = httpx.get(base + "/_test/export", timeout=10); assert r.status_code == 200, r.text; return r.json()
def imp(base, obj, raw=False): return httpx.post(base + "/_test/import", json=obj, timeout=10) if not raw else httpx.post(base + "/_test/import", content=obj, headers={"content-type": "application/json"}, timeout=10)

def seeded(reset, api, base):
    d = date(); world(reset, api); a = ada(api); new = api().signup("fresh@example.com", "fresh password", "Fresh").json()
    k = new_key(); r1 = book(a, d, "t_2", "19:00", 4, key=k).json(); r2 = book(api(new["token"]), d, "t_3", "19:00", 3, key="fresh-key").json()
    failed = new_key(); book(a, d, "t_2", "19:15", key=failed)
    return d, a, new, k, r1, r2, failed

def test_export_shape(reset, api, base_url):
    world(reset, api); e = export(base_url); assert e["track"] == "tablekeeper" and e["format_version"] == 1 and isinstance(e["state"], dict)

def test_roundtrip_preserves_accounts_tokens_bookings_and_receipts(reset, api, base_url):
    d, a, new, k, r1, r2, failed = seeded(reset, api, base_url); e = export(base_url)
    CAROL = {"id": "u_c", "email": "carol@example.com", "password": "carol password", "display_name": "C"}; world(reset, api, users=[CAROL]); assert imp(base_url, e).status_code == 204
    assert api(a.token).get("/reservations").json()["reservations"][0] == r1 and api(new["token"]).get(f"/reservations/{r2['reference']}").json() == r2
    assert_status(api().login("fresh@example.com", "fresh password"), 200); assert_status(api().login(fx.ADA["email"], fx.ADA["password"]), 200)
    c = ada(api); assert book(c, d, "t_2", "19:00", 4, key=k).json() == r1 and book(c, d, "t_2", "19:00", 4, key=k).status_code == 200
    assert_error(book(c, d, "t_1", "19:00", 2, key=k), 409, "idempotency_key_reuse")
    assert api().login(CAROL["email"], CAROL["password"]).status_code == 401

def test_failed_keys_stay_reusable_after_import(reset, api, base_url):
    d, a, new, k, r1, r2, failed = seeded(reset, api, base_url); e = export(base_url); world(reset, api); imp(base_url, e)
    assert_status(book(ada(api), d, "t_1", "19:00", 2, key=failed), 201)

def test_import_is_replacement_and_repeatable(reset, api, base_url):
    d, a, new, k, r1, r2, failed = seeded(reset, api, base_url); e = export(base_url)
    book(a, d, "t_1", "21:00", 2); api().signup("later@example.com", "later password", "L")
    assert imp(base_url, e).status_code == 204 and imp(base_url, e).status_code == 204
    assert len(ada(api).get("/reservations").json()["reservations"]) == 1 and api().login("later@example.com", "later password").status_code == 401

def test_export_is_a_snapshot(reset, api, base_url):
    d, a, *_ = seeded(reset, api, base_url); e = export(base_url); book(a, d, "t_1", "21:00", 2)
    imp(base_url, e); assert len(ada(api).get("/reservations").json()["reservations"]) == 1

def test_identities_and_timestamps_survive(reset, api, base_url):
    d, a, new, k, r1, r2, failed = seeded(reset, api, base_url); before = ada(api).get(f"/reservations/{r1['reference']}").json(); e = export(base_url)
    world(reset, api); imp(base_url, e); after = ada(api).get(f"/reservations/{r1['reference']}").json()
    assert after == before and after["reservation_id"] == r1["reservation_id"] and after["created_at"] == r1["created_at"]

@pytest.mark.parametrize("mutate", [lambda e: {**e, "track": "pocketful"}, lambda e: {**e, "format_version": 2}, lambda e: {k: v for k, v in e.items() if k != "state"}, lambda e: {**e, "state": "nope"}, lambda e: {**e, "state": None}, lambda e: {}, lambda e: [e]])
def test_invalid_import_is_422_and_changes_nothing(reset, api, base_url, mutate):
    d, a, *_ = seeded(reset, api, base_url); e = export(base_url); r = imp(base_url, mutate(e)); assert r.status_code in ((422, 400) if isinstance(mutate(e), list) else (422,)), r.text; assert r.json()["error"]["code"] in ("validation_failed", "malformed_request")
    assert len(ada(api).get("/reservations").json()["reservations"]) == 1

def test_malformed_import_is_400(reset, api, base_url):
    world(reset, api); r = imp(base_url, b"{nope", raw=True); assert r.status_code == 400 and r.json()["error"]["code"] == "malformed_request"

def test_reset_clears_imported_state(reset, api, base_url):
    d, a, *_ = seeded(reset, api, base_url); e = export(base_url); world(reset, api); imp(base_url, e); world(reset, api, users=[fx.BOB])
    assert api().login("fresh@example.com", "fresh password").status_code == 401 and bob(api).get("/reservations").json() == {"reservations": []}

def test_import_with_garbage_state_keeps_the_destination(reset, api, base_url):
    d, a, *_ = seeded(reset, api, base_url); e = export(base_url); imp(base_url, {**e, "state": {"x": 1}}); assert ada(api).get("/reservations").status_code == 200 and len(ada(api).get("/reservations").json()["reservations"]) == 1


def test_batch_move_receipts_survive_import(reset, api, base_url):
    d = date(); world(reset, api); a = ada(api); r1 = book(a, d, "t_2", "19:00", 2).json()["reference"]; r2 = book(a, d, "t_3", "19:00", 2).json()["reference"]
    k = new_key(); moves = {"moves": [{"reference": r1, "table_id": "t_3"}, {"reference": r2, "table_id": "t_2"}]}; first = a.post("/reservation-moves", json=moves, idempotency_key=k).json()
    e = export(base_url); world(reset, api); assert imp(base_url, e).status_code == 204; c = ada(api)
    again = c.post("/reservation-moves", json=moves, idempotency_key=k); assert again.status_code == 200 and again.json() == first
    assert c.get(f"/reservations/{r1}").json()["table_id"] == "t_3"
