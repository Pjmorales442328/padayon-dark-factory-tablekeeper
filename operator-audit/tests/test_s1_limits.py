"""Stage 1 §2: resource limits, scale and the documented chunked-body limitation."""
import time, httpx, pytest
from harness.concurrent import burst, no_5xx
from kit import *
pytestmark = pytest.mark.s1


def users(n): return [{"id": f"u{i}", "email": f"u{i}@example.com", "password": f"password {i}", "display_name": f"U{i}"} for i in range(n)]


def test_reset_with_hundreds_of_users_fits_the_ten_second_limit(reset, api):
    t = time.time(); f = fx.fixture(users=users(300)); reset(f); assert time.time() - t < 10
    assert_status(api().login("u299@example.com", "password 299"), 200); assert_error(api().login("u299@example.com", "password 298"), 401, "unauthenticated")


def test_large_seeded_state_stays_responsive(reset, api):
    d = date(); tables = [{"id": f"t{i}", "label": str(i), "capacity": 4} for i in range(20)]
    seeded = [{"id": f"res{i}", "reference": f"S{i:05d}", "user_id": "u_ada", "restaurant_id": "r_anker", "table_id": f"t{i % 20}", "starts_at_local": at(date(i // 20 + 1), ["18:00", "20:30"][i % 2]), "party_size": 2} for i in range(1500)]
    t = time.time(); reset(fx.fixture(restaurants=[rest(tables=tables)], reservations=seeded)); assert time.time() - t < 10
    c = ada(api); t = time.time(); assert avail(c, date(5), 2).status_code == 200 and c.get("/reservations").status_code == 200; assert time.time() - t < 5
    rs = burst(lambda i: ada(api).get("/reservations") if i % 2 else avail(api(), date(1 + i % 50), 2), 50); no_5xx(rs)


def test_fifty_in_flight_requests_all_finish_inside_the_request_timeout(reset, api):
    d = date(); world(reset, api); t = time.time(); rs = burst(lambda i: avail(api(), d, 2), 50); no_5xx(rs); assert time.time() - t < 5


def test_hash_cost_does_not_stall_concurrent_signups(reset, api):
    world(reset, api); t = time.time(); rs = burst(lambda i: api().signup(f"s{i}@example.com", "long enough password", "S"), 50); no_5xx(rs); assert all(r.status_code == 201 for r in rs) and time.time() - t < 8


@pytest.mark.xfail(reason="known limitation disclosed in FACTORY.md: chunked request bodies are refused with 400", strict=False)
def test_chunked_transfer_encoding_is_accepted(reset, api, base_url):
    d = date(); world(reset, api); tok = ada(api).token
    gen = (chunk for chunk in (b'{"restaurant_id":"r_anker","table_id":"t_2",', f'"starts_at_local":"{d}T19:00","party_size":2'.encode(), b"}"))
    r = httpx.post(base_url + "/reservations", content=gen, headers={"Authorization": f"Bearer {tok}", "Idempotency-Key": new_key(), "Content-Type": "application/json"}); assert r.status_code == 201
