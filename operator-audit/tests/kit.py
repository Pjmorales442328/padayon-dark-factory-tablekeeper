"""Shared builders and call helpers for the audit suite."""
import datetime as dt, uuid
from zoneinfo import ZoneInfo
import fixtures as fx
from harness.http import Api, assert_error, assert_status, new_key

PAIRS = [["t_1", "t_2"], ["t_2", "t_3"]]
TABLES4 = [{"id": "t_1", "label": "1", "capacity": 2}, {"id": "t_2", "label": "2", "capacity": 4},
           {"id": "t_3", "label": "3", "capacity": 6}, {"id": "t_4", "label": "4", "capacity": 2}]

def rest(rid="r_anker", *, combinable=None, managers=None, **kw):
    r = fx.restaurant(rid, **kw)
    if combinable is not None: r["combinable"] = combinable
    if managers is not None: r["manager_user_ids"] = managers
    return r

def world(reset, api, restaurants=None, reservations=None, users=None):
    f = fx.fixture(restaurants=restaurants, reservations=reservations, users=users)
    reset(f)
    return f

def ada(api): return api().authenticate(fx.ADA["email"], fx.ADA["password"])
def bob(api): return api().authenticate(fx.BOB["email"], fx.BOB["password"])
def date(lead=7, tz="Europe/Berlin"): return fx.booking_date(tz, lead)
def at(d, hhmm): return f"{d}T{hhmm}"

def body(d, table="t_2", hhmm="19:00", party=2, rid="r_anker", **extra):
    b = {"restaurant_id": rid, "starts_at_local": at(d, hhmm), "party_size": party}
    if isinstance(table, list): b["table_ids"] = table
    elif table: b["table_id"] = table
    b.update(extra); return b

def book(client, d, table="t_2", hhmm="19:00", party=2, key=None, **extra):
    return client.post("/reservations", json=body(d, table, hhmm, party, **extra), idempotency_key=key or new_key())

def avail(client, d, party=2, rid="r_anker", explain=False):
    p = {"restaurant_id": rid, "date": d, "party_size": party}
    if explain: p["explain"] = "true"
    return client.get("/availability", params=p)

def slot(resp, hhmm): return next(s for s in resp.json()["slots"] if s["starts_at_local"].endswith("T" + hhmm))

def instant(d, hour, tz="Europe/Berlin", minute=0):
    y, m, dd = map(int, d.split("-"))
    return dt.datetime(y, m, dd, hour, minute, tzinfo=ZoneInfo(tz)).isoformat()

def raw(client, method, path, **kw):
    return client.request(method, path, **kw)
