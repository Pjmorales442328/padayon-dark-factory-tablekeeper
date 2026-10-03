"""Stage 2 black-box helpers. Imports the frozen stage 1 helper module (never edited) and points it at stage-2.

Environment (in addition to the stage 1 ones): S2_BASE_URL / S2_BASE_URL2 existing stage-2 services,
SERVICE_CMD/SERVICE_CWD as before, CHECK_LOG_DIR (logs), SHOT_DIR (screenshots, outside the repo),
FROZEN_STAGE1 (directory of the frozen stage-1 service, default REPO/stage-1).
"""
import copy
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.dirname(HERE)
if V1 not in sys.path:
    sys.path.insert(0, V1)

import common  # noqa: E402  (frozen stage 1 helpers)

REPO = common.REPO
STAGE2_DIR = os.environ.get("S2_DIR", os.path.join(REPO, "stage-2"))
STAGE1_DIR = os.environ.get("FROZEN_STAGE1", os.path.join(REPO, "stage-1"))
common.STAGE_DIR = STAGE2_DIR                       # default service folder is now stage-2
if os.environ.get("S2_BASE_URL"):
    os.environ.setdefault("BASE_URL", os.environ["S2_BASE_URL"])
if os.environ.get("S2_BASE_URL2"):
    os.environ.setdefault("BASE_URL2", os.environ["S2_BASE_URL2"])

from common import (Api, Base, Resp, THU, FRI, SAT, SUN, WD, base_url, free_port, hours, table,  # noqa: E402,F401
                    seed_res, clock_minute, next_weekday, start_service)

SHOT_DIR = os.environ.get("SHOT_DIR", os.path.join(os.environ.get("TEMP", "."), "tk_shots"))
os.makedirs(SHOT_DIR, exist_ok=True)

LABELS = {"t_1": "Window", "t_2": "Booth", "t_3": "Terrace"}


def fixture2(reservations=None, combinable=None):
    """Stage 1 fixture plus labels and `combinable` pairs on r_anker (t_1:2, t_2:4, t_3:6 seats)."""
    f = common.fixture(reservations=reservations)
    anker = f["restaurants"][0]
    anker["tables"] = [table("t_1", 2, "Window"), table("t_2", 4, "Booth"), table("t_3", 6, "Terrace")]
    anker["combinable"] = [["t_1", "t_2"], ["t_2", "t_3"]] if combinable is None else combinable
    other = f["restaurants"][1]
    other["tables"] = [table("t_1", 8, "Garden"), table("t_9", 2, "Bar")]
    other["combinable"] = [["t_1", "t_9"]]
    return f


def stage1_fixture(reservations=None):
    """A fixture the frozen stage-1 service accepts (no combinable) with the same labels."""
    f = fixture2(reservations=reservations)
    for r in f["restaurants"]:
        r.pop("combinable", None)
    return f


class Base2(Base):
    fixture_factory = staticmethod(fixture2)

    def pair_book(self, token, local, ids, party, rest="r_anker", key=None, **kw):
        body = {"restaurant_id": rest, "table_ids": ids, "starts_at_local": local, "party_size": party}
        body.update(kw)
        return self.api.call("POST", "/reservations", body, token=token, key=key or self.newkey())

    def ok_pair(self, token, local, ids, party, **kw):
        r = self.pair_book(token, local, ids, party, **kw)
        self.assertEqual(r.status, 201, r)
        return r.json

    def options(self, rest, date, party=1):
        return {s["starts_at_local"]: s for s in self.avail(rest, date, party)["slots"]}

    def opt_ids(self, rest, date, local, party=1):
        s = self.options(rest, date, party)[local]
        return [o["table_ids"] for o in s["available_options"]]


def stop_process(p, wait=10):
    p.kill()
    p.wait(timeout=wait)


def wait_port_closed(port, seconds=15):
    t0 = time.time()
    while time.time() - t0 < seconds:
        if port_closed(port):
            return True
        time.sleep(0.2)
    return False


def port_closed(port):
    import socket
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect(("127.0.0.1", port))
        return False
    except OSError:
        return True
    finally:
        s.close()


def start_at(cwd, extra_env=None):
    """Start a service from `cwd` (own PORT); returns (base_url, process, port)."""
    old = os.environ.get("SERVICE_CWD")
    os.environ["SERVICE_CWD"] = cwd
    try:
        base, p = start_service(extra_env)
    finally:
        if old is None:
            os.environ.pop("SERVICE_CWD", None)
        else:
            os.environ["SERVICE_CWD"] = old
    return base, p, int(base.rsplit(":", 1)[1])
