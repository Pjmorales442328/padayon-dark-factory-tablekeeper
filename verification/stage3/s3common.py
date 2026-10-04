"""Stage 3 black-box helpers. Reuses the frozen stage 1/2 helper modules (never edited), pointed at stage-3.

Env: S3_DIR (stage-3 service folder, default REPO/stage-3), FROZEN_STAGE1 / FROZEN_STAGE2 (frozen services used as migration
sources), SHOT_DIR, CHECK_LOG_DIR, SERVICE_CMD, KICKOFF, HARNESS_OUT, BASE_URL/BASE_URL2 (running stage-3 services).
"""
import copy
import datetime as dt
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.dirname(HERE)                      # verification
V2 = os.path.join(V1, "stage2")
for p in (V1, V2, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

_REPO = os.environ.get("REPO", os.path.dirname(V1))
STAGE3_DIR = os.environ.get("S3_DIR", os.path.join(_REPO, "stage-3"))
FROZEN_STAGE1 = os.environ.get("FROZEN_STAGE1", os.path.join(_REPO, "stage-1"))
FROZEN_STAGE2 = os.environ.get("FROZEN_STAGE2", os.path.join(_REPO, "stage-2"))
# the stage 2 helpers (and therefore the inherited stage 2 tests) will start the stage-3 service as "stage 2"
os.environ["S2_DIR"] = STAGE3_DIR
os.environ["FROZEN_STAGE1"] = FROZEN_STAGE1

import s2common  # noqa: E402
import common  # noqa: E402

common.STAGE_DIR = STAGE3_DIR
REPO = common.REPO
from s2common import (Api, Base2, THU, FRI, SAT, SUN, WD, SHOT_DIR, LABELS, base_url, fixture2, stage1_fixture,  # noqa: E402,F401
                      seed_res, hours, table, clock_minute, next_weekday, start_at, stop_process, port_closed,
                      wait_port_closed, start_service)

T = f"{THU}T19:00"
POLICY_FIELDS = ("slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes", "opening_hours", "capacities")
TERMS_KEYS = {"policy_version", "slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes",
              "opening_hours", "capacities"}


def add_days(date_s, n):
    return (dt.date.fromisoformat(date_s) + dt.timedelta(days=n)).isoformat()


def fixture3(reservations=None, managers=None, combinable=None):
    """Stage 2 fixture plus `manager_user_ids`: u_ada manages r_anker and r_clock, u_bob manages r_other."""
    f = fixture2(reservations=reservations, combinable=combinable)
    m = {"r_anker": ["u_ada"], "r_other": ["u_bob"], "r_clock": ["u_ada"], "r_dst_de": ["u_ada"], "r_dst_ny": ["u_ada"],
         "r_cut0": ["u_ada"]}
    if managers is not None:
        m.update(managers)
    for r in f["restaurants"]:
        r["manager_user_ids"] = list(m.get(r["id"], []))
    return f


def policy(effective_from, duration=90, slot=30, cutoff=120, opening=None, capacities=None, rest="r_anker"):
    caps = capacities or {"r_anker": {"t_1": 2, "t_2": 4, "t_3": 6}, "r_other": {"t_1": 8, "t_9": 2},
                          "r_clock": {"t_1": 4, "t_2": 4}, "r_dst_de": {"t_1": 4, "t_2": 4},
                          "r_dst_ny": {"t_1": 4, "t_2": 4}, "r_cut0": {"t_1": 4}}[rest]
    op = opening
    if op is None:
        op = hours("18:00", "23:00", ["mon", "tue", "wed", "thu", "fri", "sat"]) if rest == "r_anker" else hours("00:00", "23:59")
    return {"effective_from": effective_from, "slot_minutes": slot, "reservation_duration_minutes": duration,
            "cancellation_cutoff_minutes": cutoff, "opening_hours": op, "capacities": caps}


class Base3(Base2):
    fixture_factory = staticmethod(fixture3)

    def publish(self, token, pol, rest="r_anker", key=None, **kw):
        return self.api.call("POST", f"/restaurants/{rest}/policies", pol, token=token, key=key or self.newkey(), **kw)

    def ok_publish(self, pol, rest="r_anker", token=None):
        r = self.publish(token or self.ada, pol, rest)
        self.assertEqual(r.status, 201, r)
        return r.json

    def history(self, ref, token=None):
        r = self.api.call("GET", f"/reservations/{ref}/history", token=token or self.ada)
        self.assertEqual(r.status, 200, r)
        return r.json

    def decision(self, ref, token=None):
        r = self.api.call("GET", f"/reservations/{ref}/decision", token=token or self.ada)
        self.assertEqual(r.status, 200, r)
        return r.json

    def patch(self, ref, body, token=None):
        return self.api.call("PATCH", f"/reservations/{ref}", body, token=token or self.ada)

    def get_res(self, ref, token=None):
        r = self.api.call("GET", f"/reservations/{ref}", token=token or self.ada)
        self.assertEqual(r.status, 200, r)
        return r.json

    def adopt(self, anchor, count=4, interval=1, token=None, key=None):
        return self.api.call("POST", "/series", {"anchor_reference": anchor, "count": count, "interval_weeks": interval},
                             token=token or self.ada, key=key or self.newkey())

    def ok_adopt(self, anchor, count=4, interval=1, token=None):
        r = self.adopt(anchor, count, interval, token)
        self.assertEqual(r.status, 201, r)
        return r.json

    def get_series(self, sid, token=None):
        r = self.api.call("GET", f"/series/{sid}", token=token or self.ada)
        self.assertEqual(r.status, 200, r)
        return r.json

    def moves(self, moves, token=None, key=None):
        return self.api.call("POST", "/reservation-moves", {"moves": moves}, token=token or self.ada, key=key or self.newkey())

    def explain(self, rest, date, party=1, extra=""):
        r = self.api.call("GET", f"/availability?restaurant_id={rest}&date={date}&party_size={party}&explain=true{extra}")
        self.assertEqual(r.status, 200, r)
        return {s["starts_at_local"]: s for s in r.json["slots"]}

    def assert_terms(self, terms, version, **fields):
        self.assertEqual(set(terms), TERMS_KEYS, terms)
        self.assertEqual(terms["policy_version"], version)
        for k, v in fields.items():
            self.assertEqual(terms[k], v, k)
