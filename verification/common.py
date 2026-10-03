"""Black-box helpers for the Tablekeeper stage 1 checks. HTTP only; no service imports.

Environment:
  BASE_URL / BASE_URL2   existing service(s) to test (second one is the import target)
  SERVICE_CMD            command that starts a service (reads PORT); default
                         "python -m tablekeeper.server" in REPO/stage-1
  SERVICE_CWD            working directory for SERVICE_CMD
  REPO                   repository root (default: parent of this folder)
"""
import atexit
import copy
import datetime as dt
import http.client
import json
import os
import shlex
import socket
import subprocess
import sys
import threading
import time
import unittest
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("REPO", os.path.dirname(HERE))
STAGE_DIR = os.path.join(REPO, "stage-1")

_procs = []


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def start_service(extra_env=None, wait=60):
    cmd = os.environ.get("SERVICE_CMD") or f'"{sys.executable}" -m tablekeeper.server'
    cwd = os.environ.get("SERVICE_CWD") or STAGE_DIR
    port = free_port()
    env = dict(os.environ, PORT=str(port), **(extra_env or {}))
    log = open(os.path.join(os.environ.get("CHECK_LOG_DIR", os.environ.get("TEMP", ".")),
                            f"svc_{port}.log"), "wb")
    p = subprocess.Popen(shlex.split(cmd, posix=False), cwd=cwd, env=env, stdout=log, stderr=log)
    _procs.append(p)
    base = f"http://127.0.0.1:{port}"
    t0 = time.time()
    while time.time() - t0 < wait:
        if p.poll() is not None:
            raise RuntimeError(f"service exited early with {p.returncode}")
        try:
            r = Api(base).call("GET", "/health", timeout=2)
            if r.status == 200:
                return base, p
        except Exception:
            pass
        time.sleep(0.2)
    raise RuntimeError("service did not become healthy in %ds" % wait)


@atexit.register
def _cleanup():
    for p in _procs:
        if p.poll() is None:
            p.kill()


_bases = {}


def base_url(slot=1):
    env = os.environ.get("BASE_URL" if slot == 1 else "BASE_URL2")
    if env:
        return env.rstrip("/")
    if slot not in _bases:
        _bases[slot] = start_service()[0]
    return _bases[slot]


class Resp:
    def __init__(self, status, headers, raw):
        self.status, self.headers, self.raw = status, headers, raw
        try:
            self.json = json.loads(raw.decode("utf-8")) if raw else None
        except Exception:
            self.json = None

    @property
    def ctype(self):
        return self.headers.get("content-type", "")

    def __repr__(self):
        return f"<{self.status} {self.raw[:300]!r}>"


class Api:
    def __init__(self, base):
        self.base = base
        u = urllib.parse.urlparse(base)
        self.host, self.port = u.hostname, u.port

    def call(self, method, path, body=None, token=None, key=None, headers=None, raw=None,
             timeout=15):
        h = {}
        data = None
        if raw is not None:
            data = raw if isinstance(raw, bytes) else raw.encode("utf-8")
            h["Content-Type"] = "application/json"
        elif body is not None:
            data = json.dumps(body).encode("utf-8")
            h["Content-Type"] = "application/json"
        if token is not None:
            h["Authorization"] = "Bearer " + token
        if key is not None:
            h["Idempotency-Key"] = key
        h.update(headers or {})
        c = http.client.HTTPConnection(self.host, self.port, timeout=timeout)
        try:
            c.request(method, path, body=data, headers=h)
            r = c.getresponse()
            body_raw = r.read()
            return Resp(r.status, {k.lower(): v for k, v in r.getheaders()}, body_raw)
        finally:
            c.close()


# ---------------------------------------------------------------- fixtures

def next_weekday(wd, year=2030, month=1, day=1):
    """Date of the first weekday (0=mon) on/after year-month-day."""
    d = dt.date(year, month, day)
    while d.weekday() != wd:
        d += dt.timedelta(days=1)
    return d


THU = next_weekday(3).isoformat()      # 2030-01-03, open at r_anker
FRI = next_weekday(4).isoformat()
SAT = next_weekday(5).isoformat()
SUN = next_weekday(6).isoformat()      # closed at r_anker
WD = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def hours(opens, closes, days=WD):
    return [{"weekday": d, "opens": opens, "closes": closes} for d in days]


def table(i, cap, label=None):
    return {"id": i, "label": label or i, "capacity": cap}


def fixture(extra_reservations=(), reservations=None):
    anker_hours = hours("18:00", "23:00", ["mon", "tue", "wed", "thu", "sat"]) + \
        [{"weekday": "fri", "opens": "18:00", "closes": "23:30"}]
    f = {
        "users": [
            {"id": "u_ada", "email": "ada@example.com", "password": "correct horse",
             "display_name": "Ada"},
            {"id": "u_bob", "email": "bob@example.com", "password": "battery staple",
             "display_name": "Bob"},
        ],
        "restaurants": [
            {"id": "r_anker", "name": "Zum Anker", "timezone": "Europe/Berlin",
             "slot_minutes": 30, "reservation_duration_minutes": 90,
             "cancellation_cutoff_minutes": 120, "opening_hours": anker_hours,
             "tables": [table("t_1", 2), table("t_2", 4), table("t_3", 6)]},
            {"id": "r_other", "name": "Other", "timezone": "Europe/Berlin",
             "slot_minutes": 60, "reservation_duration_minutes": 60,
             "cancellation_cutoff_minutes": 0, "opening_hours": hours("12:00", "20:00"),
             "tables": [table("t_1", 8), table("t_9", 2)]},
            {"id": "r_dst_de", "name": "DST Berlin", "timezone": "Europe/Berlin",
             "slot_minutes": 30, "reservation_duration_minutes": 90,
             "cancellation_cutoff_minutes": 0, "opening_hours": hours("00:00", "06:00"),
             "tables": [table("t_1", 4), table("t_2", 4)]},
            {"id": "r_dst_ny", "name": "DST NY", "timezone": "America/New_York",
             "slot_minutes": 30, "reservation_duration_minutes": 90,
             "cancellation_cutoff_minutes": 0, "opening_hours": hours("00:00", "06:00"),
             "tables": [table("t_1", 4), table("t_2", 4)]},
            {"id": "r_clock", "name": "Clock", "timezone": "UTC",
             "slot_minutes": 1, "reservation_duration_minutes": 10,
             "cancellation_cutoff_minutes": 120, "opening_hours": hours("00:00", "23:59"),
             "tables": [table("t_1", 4), table("t_2", 4)]},
            {"id": "r_cut0", "name": "Cut0", "timezone": "UTC",
             "slot_minutes": 1, "reservation_duration_minutes": 5,
             "cancellation_cutoff_minutes": 0, "opening_hours": hours("00:00", "23:59"),
             "tables": [table("t_1", 4)]},
        ],
        "reservations": [] if reservations is None else reservations,
    }
    f["reservations"] += list(extra_reservations)
    return f


def seed_res(i, user, rest, tbl, local, party, ref=None):
    return {"id": f"res_s{i}", "reference": ref or f"SEED{i:02d}", "user_id": user,
            "restaurant_id": rest, "table_id": tbl, "starts_at_local": local,
            "party_size": party}


def clock_minute(offset_minutes):
    """UTC wall-clock minute `offset_minutes` from now as YYYY-MM-DDTHH:MM, avoiding 23:50+."""
    t = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0) + \
        dt.timedelta(minutes=offset_minutes)
    if t.hour == 23 and t.minute >= 50:
        t += dt.timedelta(minutes=15)
    return t.strftime("%Y-%m-%dT%H:%M")


# ---------------------------------------------------------------- base test

class Base(unittest.TestCase):
    fixture_factory = staticmethod(fixture)

    @classmethod
    def setUpClass(cls):
        cls.api = Api(base_url(1))

    def setUp(self):
        self.reset()

    def reset(self, fx=None):
        r = self.api.call("POST", "/_test/reset", fx if fx is not None else self.fixture_factory(),
                          timeout=30)
        self.assertEqual(r.status, 204, r)
        self.assertEqual(r.raw, b"")
        self._tokens = {}
        return r

    def tok(self, email="ada@example.com", pw=None, api=None):
        pw = pw or {"ada@example.com": "correct horse", "bob@example.com": "battery staple"}[email]
        r = (api or self.api).call("POST", "/auth/login", {"email": email, "password": pw})
        self.assertEqual(r.status, 200, r)
        return r.json["token"]

    @property
    def ada(self):
        return self.tok("ada@example.com")

    @property
    def bob(self):
        return self.tok("bob@example.com")

    _n = 0

    def newkey(self):
        Base._n += 1
        return f"k-{os.getpid()}-{time.time_ns()}-{Base._n}"

    def book(self, token, local, table="t_2", rest="r_anker", party=2, key=None, **kw):
        body = {"restaurant_id": rest, "table_id": table, "starts_at_local": local,
                "party_size": party}
        body.update(kw)
        return self.api.call("POST", "/reservations", body, token=token, key=key or self.newkey())

    def ok_book(self, token, local, **kw):
        r = self.book(token, local, **kw)
        self.assertEqual(r.status, 201, r)
        return r.json

    def err(self, r, status, code):
        self.assertEqual(r.status, status, r)
        self.assertTrue(r.ctype.lower().replace(" ", "").startswith("application/json;charset=utf-8"),
                        r.ctype)
        e = (r.json or {}).get("error")
        self.assertIsInstance(e, dict, r)
        self.assertEqual(e.get("code"), code, r)
        self.assertIsInstance(e.get("message"), str, r)
        self.assertTrue(e["message"].strip(), r)
        self.assertEqual(set(r.json), {"error"}, r)

    def avail(self, rest, date, party=1):
        r = self.api.call("GET", f"/availability?restaurant_id={rest}&date={date}&party_size={party}")
        self.assertEqual(r.status, 200, r)
        return r.json

    def slot_map(self, rest, date, party=1):
        return {s["starts_at_local"]: s for s in self.avail(rest, date, party)["slots"]}

    def burst(self, calls):
        """Run callables released at the same instant; returns results in order."""
        n = len(calls)
        barrier = threading.Barrier(n)
        out = [None] * n

        def run(i):
            barrier.wait()
            try:
                out[i] = calls[i]()
            except Exception as e:  # noqa
                out[i] = e

        ts = [threading.Thread(target=run, args=(i,)) for i in range(n)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        for o in out:
            self.assertNotIsInstance(o, Exception, o)
        return out


def deep(x):
    return copy.deepcopy(x)
