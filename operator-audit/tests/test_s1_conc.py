"""Stage 1 §1, §5: concurrency and no-5xx under load."""
import pytest
from harness.concurrent import burst, no_5xx, tally
from kit import *
pytestmark = pytest.mark.s1

def test_fifty_racers_one_table_one_winner(reset, api):
    d = date(); world(reset, api); rs = burst(lambda i: ada(api).post("/reservations", json=body(d), idempotency_key=new_key()), 50)
    no_5xx(rs); t = tally(rs); assert t == {201: 1, 409: 49}, t
    assert len(ada(api).get("/reservations").json()["reservations"]) == 1

def test_fifty_independent_bookings_all_succeed(reset, api):
    d = date(); world(reset, api, restaurants=[rest(tables=[{"id": f"t{i}", "label": str(i), "capacity": 4} for i in range(25)])])
    rs = burst(lambda i: ada(api).post("/reservations", json=body(d, f"t{i % 25}", "19:00" if i < 25 else "21:00", 2), idempotency_key=new_key()), 50)
    no_5xx(rs); assert tally(rs) == {201: 50}

def test_racing_amendments_to_one_slot(reset, api):
    d = date(); world(reset, api, restaurants=[rest(tables=[{"id": f"t{i}", "label": str(i), "capacity": 4} for i in range(8)])]); a = ada(api)
    refs = [book(a, d, f"t{i}", "19:00").json()["reference"] for i in range(1, 8)]
    rs = burst(lambda i: a.patch(f"/reservations/{refs[i]}", json={"table_id": "t0"}), 7); no_5xx(rs); assert tally(rs) == {200: 1, 409: 6}
    assert sum(1 for r in a.get("/reservations").json()["reservations"] if r["table_id"] == "t0") == 1

def test_cancel_then_rebook_races_never_double_book(reset, api):
    d = date(); world(reset, api); a = ada(api); ref = book(a, d).json()["reference"]; a.post(f"/reservations/{ref}/cancel")
    rs = burst(lambda i: bob(api).post("/reservations", json=body(d), idempotency_key=new_key()), 20); no_5xx(rs); assert tally(rs) == {201: 1, 409: 19}

def test_racing_signups_for_one_email(reset, api):
    world(reset, api); rs = burst(lambda i: api().signup("same@example.com", "long enough", "S"), 15); no_5xx(rs); assert tally(rs) == {201: 1, 409: 14}

def test_mixed_load_stays_fast_and_clean(reset, api):
    import time
    d = date(); world(reset, api); a = ada(api); t0 = time.time()
    def op(i):
        c = ada(api)
        return [lambda: avail(c, d, 2), lambda: c.get("/reservations"), lambda: c.post("/reservations", json=body(d, ["t_1", "t_2", "t_3"][i % 3], ["19:00", "21:00"][i % 2], 2), idempotency_key=new_key()), lambda: api().get("/restaurants")][i % 4]()
    rs = burst(op, 50); no_5xx(rs); assert time.time() - t0 < 10
    assert all(r.status_code in (200, 201, 409) for r in rs)

def test_reset_during_traffic_is_safe(reset, api):
    d = date(); world(reset, api); import threading
    stop = threading.Event()
    def spam():
        c = ada(api)
        while not stop.is_set(): c.get("/reservations")
    th = threading.Thread(target=spam); th.start()
    try:
        for _ in range(5): world(reset, api)
    finally: stop.set(); th.join()
    assert ada(api).get("/reservations").json() == {"reservations": []}
