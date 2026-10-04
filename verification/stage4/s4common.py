"""Stage 4 black-box helpers (HTTP only). Reuses the frozen stage 1-3 helper modules (never edited), pointed at stage-4.

Env: S4_DIR (stage-4 service folder, default REPO/stage-4), FROZEN_STAGE1/2/3 (frozen services used as migration sources),
SHOT_DIR, CHECK_LOG_DIR, SERVICE_CMD, HARNESS_OUT, BASE_URL/BASE_URL2 (running stage-4 services).
Exports (tokens, hashes) stay in memory.
"""
import datetime as dt
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.dirname(HERE)
V3 = os.path.join(V1, "stage3")
_REPO = os.environ.get("REPO", os.path.dirname(V1))
STAGE4_DIR = os.environ.get("S4_DIR", os.path.join(_REPO, "stage-4"))
FROZEN_STAGE3 = os.environ.get("FROZEN_STAGE3", os.path.join(_REPO, "stage-3"))
os.environ["S3_DIR"] = STAGE4_DIR            # the stage 3 helpers (and inherited tests) now start the stage-4 service
os.environ.setdefault("FROZEN_STAGE3", FROZEN_STAGE3)
for p in (V3, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import s3common  # noqa: E402
from s3common import (Api, Base3, THU, FRI, SAT, SUN, T, TERMS_KEYS, add_days, fixture2, fixture3, stage1_fixture,  # noqa: E402,F401
                      policy, hours, table, seed_res, clock_minute, start_at, stop_process, port_closed, wait_port_closed,
                      FROZEN_STAGE1, FROZEN_STAGE2, common)

TZ = "+01:00"                                   # Europe/Berlin in January 2030
PLAN_KEYS = {"plan_id", "restaurant_revision", "closure", "assignments", "moved_count", "unused_seats"}
APPLY_KEYS = {"plan_id", "restaurant_revision", "reservations"}
FAR_FROM, FAR_TO = "2040-06-01T10:00:00+02:00", "2040-06-01T11:00:00+02:00"      # overlaps nothing: a pure revision probe


def inst(date_s, hhmm, off=TZ):
    return f"{date_s}T{hhmm}:00{off}"


def parse(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def fixture4(reservations=None, managers=None, combinable=None):
    return fixture3(reservations=reservations, managers=managers, combinable=combinable)


def stage3_fixture(reservations=None):
    return fixture3(reservations=reservations)


# ---------------------------------------------------------------------------------- independent planning oracle
def oracle(tables, pairs, bookings, fixed, closures, closure):
    """Brute-force optimum. tables: ids in fixture order; pairs: declared lists; bookings: dicts (reference, party, start, end,
    caps -> {table: capacity under the booking's OWN terms}); fixed: [(table_ids, start, end)] occupied by bookings that keep
    their assignment; closures: [(table, from, to)] applied; closure: (table, from, to) proposed.  Instants are datetimes.
    Returns (assignments {reference: [tables]}, moved_count_key, unused) or None. Objective: (#changed sets, unused, ranks)."""
    options = [[t] for t in tables] + [list(p) for p in pairs]
    allc = list(closures) + [closure]
    refs = sorted(bookings, key=lambda b: b["reference"])

    def blocked_by_closure(opt, b):
        return any(c[0] in opt and b["start"] < c[2] and c[1] < b["end"] for c in allc)

    def blocked_by_fixed(opt, b):
        return any(set(f[0]) & set(opt) and b["start"] < f[2] and f[1] < b["end"] for f in fixed)

    feas = []
    for b in refs:
        fo = []
        for rank, opt in enumerate(options):
            if sum(b["caps"][t] for t in opt) < b["party"] or blocked_by_closure(opt, b) or blocked_by_fixed(opt, b):
                continue
            fo.append((rank, opt))
        if not fo:
            return None
        feas.append(fo)
    best = [None]

    def rec(i, chosen):
        if i == len(refs):
            changed = sum(1 for b, (r, o) in zip(refs, chosen) if sorted(o) != sorted(b["current"]))
            unused = sum(sum(b["caps"][t] for t in o) - b["party"] for b, (r, o) in zip(refs, chosen))
            key = (changed, unused, tuple(r for r, o in chosen))
            if best[0] is None or key < best[0][0]:
                best[0] = (key, list(chosen))
            return
        b = refs[i]
        for r, o in feas[i]:
            if any(set(o) & set(po) and b["start"] < pb["end"] and pb["start"] < b["end"]
                   for pb, (pr, po) in zip(refs[:i], chosen)):
                continue
            rec(i + 1, chosen + [(r, o)])
    rec(0, [])
    if best[0] is None:
        return None
    key, chosen = best[0]
    return {b["reference"]: o for b, (r, o) in zip(refs, chosen)}, key[0], key[1]


class Base4(Base3):
    fixture_factory = staticmethod(fixture4)
    PAIRS = [["t_1", "t_2"], ["t_2", "t_3"]]
    TABLES = ["t_1", "t_2", "t_3"]

    @property
    def ta(self):
        """Ada's token from a login made now (a reset invalidates every earlier token)."""
        return self.ada

    @property
    def tb(self):
        return self.bob

    # --- replans
    def replan(self, token, table_id="t_2", frm=None, to=None, rest="r_anker", key=None, body=None):
        b = body if body is not None else {"table_id": table_id, "from": frm or inst(THU, "18:00"), "to": to or inst(THU, "23:00")}
        return self.api.call("POST", f"/restaurants/{rest}/replans", b, token=token, key=key or self.newkey())

    def ok_replan(self, table_id="t_2", frm=None, to=None, rest="r_anker", token=None):
        r = self.replan(token or self.ada, table_id, frm, to, rest)
        self.assertEqual(r.status, 201, r)
        self.assertEqual(set(r.json), PLAN_KEYS, r)
        return r.json

    def apply(self, token, plan_id, rest="r_anker", key=None, body=None):
        return self.api.call("POST", f"/restaurants/{rest}/replans/{plan_id}/apply", {} if body is None else body, token=token,
                             key=key or self.newkey())

    def ok_apply(self, plan_id, rest="r_anker", token=None, key=None):
        r = self.apply(token or self.ada, plan_id, rest, key)
        self.assertEqual(r.status, 201, r)
        self.assertEqual(set(r.json), APPLY_KEYS, r)
        return r.json

    def rev(self, rest="r_anker", token=None):
        """Restaurant revision observed through a preview that overlaps no booking (stores only a plan)."""
        r = self.replan(token or self.ada, "t_1", FAR_FROM, FAR_TO, rest)
        self.assertEqual(r.status, 201, r)
        return r.json["restaurant_revision"]

    # --- series amend
    def amend(self, token, sid, expected, from_index, local_time, key=None, body=None):
        b = body if body is not None else {"expected_revision": expected, "from_index": from_index, "local_time": local_time}
        return self.api.call("POST", f"/series/{sid}/amend", b, token=token, key=key or self.newkey())

    def ok_amend(self, token, sid, expected, from_index, local_time, key=None):
        r = self.amend(token, sid, expected, from_index, local_time, key)
        self.assertEqual(r.status, 201, r)
        return r.json

    def mk_series(self, count=4, interval=1, local=T, table_id="t_2", party=2, rest="r_anker", token=None):
        tok = token or self.bob
        a = self.ok_book(tok, local, table=table_id, party=party, rest=rest)
        return a, self.ok_adopt(a["reference"], count, interval, tok)

    def all_res(self, token):
        return self.api.call("GET", "/reservations", token=token).json["reservations"]

    def reads(self, refs, token):
        """Everything observable about some reservations."""
        return [(self.get_res(r, token), self.history(r, token)) for r in refs]

    def tids(self, res):
        return res.get("table_ids") or [res["table_id"]]

    def oracle_input(self, token_of, refs, rest="r_anker"):
        out = []
        for ref, tok in refs:
            r = self.get_res(ref, tok)
            out.append({"reference": ref, "party": r["party_size"], "start": parse(r["starts_at"]), "end": parse(r["ends_at"]),
                        "caps": r["accepted_terms"]["capacities"], "current": self.tids(r), "status": r["status"]})
        return out
