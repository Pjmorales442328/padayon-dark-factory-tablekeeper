"""Stage 4 version transfer, native roundtrip and import validation (ledger 332-343, 346; inherited upgrade lines are rerun by the
frozen suites).  TestUpgradeFromStage3/2/1 start the ACTUAL frozen service, fill it, export, KILL it, confirm the port is closed and
only then start an independent stage-4 destination and import.  Exports (tokens, hashes) stay in memory.
"""
import copy
import json
import random
import unittest

from s4common import (Api, Base4, FROZEN_STAGE1, FROZEN_STAGE2, FROZEN_STAGE3, STAGE4_DIR, THU, FRI, T, add_days, fixture2, fixture3,
                      fixture4, stage1_fixture, policy, seed_res, start_at, stop_process, wait_port_closed, inst, FAR_FROM, FAR_TO)

PW = "abc"


def walk(node, path=()):
    yield path, node
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, path + (i,))


def get_at(root, path):
    for p in path:
        root = root[p]
    return root


def login(api, email, pw):
    r = api.call("POST", "/auth/login", {"email": email, "password": pw})
    assert r.status == 200, r
    return r.json["token"]


def observe(api, toks, series_ids=()):
    """Everything readable about the state, through HTTP only."""
    out = {}
    for name, tok in toks.items():
        lst = api.call("GET", "/reservations", token=tok)
        out[(name, "list")] = (lst.status, lst.json)
        for r in (lst.json or {}).get("reservations", []):
            ref = r["reference"]
            for suffix in ("", "/history", "/decision"):
                x = api.call("GET", f"/reservations/{ref}{suffix}", token=tok)
                out[(name, ref, suffix)] = (x.status, x.json)
    for sid, tok in series_ids:
        x = api.call("GET", f"/series/{sid}", token=tok)
        out[("series", sid)] = (x.status, x.json)
    for d in (THU, FRI, add_days(THU, 7), add_days(THU, 14)):
        for party in (1, 5):
            x = api.call("GET", f"/availability?restaurant_id=r_anker&date={d}&party_size={party}&explain=true")
            out[("avail", d, party)] = (x.status, x.json)
    return out


def probe_rev(api, tok, rest="r_anker", table="t_1"):
    r = api.call("POST", f"/restaurants/{rest}/replans", {"table_id": table, "from": FAR_FROM, "to": FAR_TO}, token=tok,
                 key=f"probe-{random.random()}")
    assert r.status == 201, r
    return r.json["restaurant_revision"]


# ======================================================================================== native roundtrip (346, 339, 340)
class Native(Base4):
    """Populate a stage-4 service, export, import into a second independent stage-4 process and compare everything."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dst_base, cls.dst_proc, cls.dst_port = start_at(STAGE4_DIR)
        cls.d = Api(cls.dst_base)

    @classmethod
    def tearDownClass(cls):
        if cls.dst_proc.poll() is None:
            cls.dst_proc.kill()
        super().tearDownClass()

    _tk = None

    @property
    def ada(self):
        """The token captured by populate() (tokens survive an export; a fresh login after it would not)."""
        return self._tk["ada"] if self._tk else super().ada

    @property
    def bob(self):
        return self._tk["bob"] if self._tk else super().bob

    def reset(self, fx=None):
        self._tk = None                                     # a reset invalidates every earlier token
        return super().reset(fx)

    def populate(self):
        f = fixture4(reservations=[seed_res(1, "u_bob", "r_anker", "t_1", f"{FRI}T18:00", 2, "BOBSEED1")])
        f["users"][0]["password"] = PW
        self.reset(f)
        self._tk = {"ada": login(self.api, "ada@example.com", PW), "bob": login(self.api, "bob@example.com", "battery staple")}
        self.calls = []

        def rec(method, path, body, tok, key):
            r = self.api.call(method, path, body, token=tok, key=key)
            self.calls.append((method, path, body, tok, key, r.status, r.json))
            return r
        self.rec = rec
        a = rec("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": T, "party_size": 3}, self.bob, "n-a").json
        s = rec("POST", "/series", {"anchor_reference": a["reference"], "count": 4, "interval_weeks": 1}, self.bob, "n-s").json
        refs = [o["reference"] for o in s["occurrences"]]
        self.api.call("PATCH", f"/reservations/{refs[2]}", {"starts_at_local": f"{add_days(THU, 14)}T20:30"}, token=self.bob)
        self.api.call("POST", f"/reservations/{refs[3]}/cancel", token=self.bob)
        pr = rec("POST", "/reservations", {"restaurant_id": "r_anker", "table_ids": ["t_2", "t_3"], "starts_at_local": f"{FRI}T20:00",
                                         "party_size": 8}, self.bob, "n-pair")
        b = rec("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_1", "starts_at_local": f"{THU}T21:00", "party_size": 2},
                self.ada, "n-b").json
        rec("POST", "/restaurants/r_anker/policies", policy(add_days(THU, 14), duration=60, capacities={"t_1": 2, "t_2": 4, "t_3": 6}), self.ada, "n-pol")
        p1 = rec("POST", "/restaurants/r_anker/replans", {"table_id": "t_2", "from": inst(THU, "18:00"), "to": inst(THU, "20:00")}, self.ada, "n-p1")
        self.assertEqual(p1.status, 201, p1)
        self.ap1 = rec("POST", f"/restaurants/r_anker/replans/{p1.json['plan_id']}/apply", {}, self.ada, "n-ap1")
        self.assertEqual(self.ap1.status, 201, self.ap1)
        self.p1 = p1.json
        sr = self.get_series(s["series_id"], self.bob)
        rec("POST", f"/series/{s['series_id']}/amend", {"expected_revision": sr["revision"], "from_index": 1, "local_time": "20:00"}, self.bob, "n-am")
        self.p2 = rec("POST", "/restaurants/r_anker/replans", {"table_id": "t_3", "from": inst(FRI, "00:00"), "to": inst(FRI, "23:59")}, self.ada, "n-p2").json
        self.p3 = rec("POST", "/restaurants/r_anker/replans", {"table_id": "t_1", "from": inst(THU, "20:30"), "to": inst(THU, "23:00")}, self.ada, "n-p3").json
        rec("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_3", "starts_at_local": f"{add_days(THU, 21)}T22:00", "party_size": 2},
            self.ada, "n-stale")                                                     # p2 and p3 are now stale
        self.p4 = rec("POST", "/restaurants/r_anker/replans", {"table_id": "t_1", "from": inst(THU, "20:30"), "to": inst(THU, "23:00")}, self.ada, "n-p4").json
        self.series_ids = [(s["series_id"], self.bob)]
        self.toks = {"ada": self.ada, "bob": self.bob}

    def test_L339_L346_roundtrip_preserves_everything_and_replays(self):
        self.populate()
        before = observe(self.api, self.toks, self.series_ids)
        rev_src = probe_rev(self.api, self.ada)
        export = self.api.call("GET", "/_test/export").json                             # private: memory only
        self.assertEqual(self.api.call("GET", "/_test/export").json, export, "export is a detached, repeatable read")
        self.d.call("POST", "/_test/reset", fixture4())
        r = self.d.call("POST", "/_test/import", export)
        self.assertEqual((r.status, r.raw), (204, b""))
        after = observe(self.d, self.toks, self.series_ids)
        self.assertEqual(after, before, "reads are identical after the move")
        self.assertEqual(probe_rev(self.d, self.ada), rev_src, "the restaurant revision is carried over")
        # recorded requests replay with the original response
        for method, path, body, tok, key, status, js in self.calls:
            rr = self.d.call(method, path, body, token=tok, key=key)
            if status == 201:
                self.assertEqual((rr.status, rr.json), (200, js), (path, key))
            else:
                self.assertEqual(rr.status, status, (path, key))
        # the applied plan stays applied; another key is refused, the original key replays
        pid = self.p1["plan_id"]
        self.err(self.d.call("POST", f"/restaurants/r_anker/replans/{pid}/apply", {}, token=self.ada, key="other-key"), 409, "plan_already_applied")
        rr = self.d.call("POST", f"/restaurants/r_anker/replans/{pid}/apply", {}, token=self.ada, key="n-ap1")
        self.assertEqual((rr.status, rr.json), (200, self.ap1.json))
        # the stale plans stay stale, the fresh plan stays applicable (identically on both sides)
        for plan in (self.p2, self.p3):
            self.err(self.d.call("POST", f"/restaurants/r_anker/replans/{plan['plan_id']}/apply", {}, token=self.ada, key="s-" + plan["plan_id"]),
                     409, "stale_plan")
            self.err(self.api.call("POST", f"/restaurants/r_anker/replans/{plan['plan_id']}/apply", {}, token=self.ada, key="s-" + plan["plan_id"]),
                     409, "stale_plan")
        dd = self.d.call("POST", f"/restaurants/r_anker/replans/{self.p4['plan_id']}/apply", {}, token=self.ada, key="fresh")
        ss = self.api.call("POST", f"/restaurants/r_anker/replans/{self.p4['plan_id']}/apply", {}, token=self.ada, key="fresh")
        self.assertEqual((dd.status, ss.status), (201, 201), (dd, ss))
        norm = lambda j: [(x["reference"], x["table_ids"] if "table_ids" in x else None) for x in j["assignments"]] if "assignments" in j else \
            [(x["reference"], self.tids(x), x["revision"]) for x in j["reservations"]]
        self.assertEqual(norm(dd.json), norm(ss.json))
        self.assertEqual(probe_rev(self.d, self.ada), probe_rev(self.api, self.ada))
        # closures persist: the closed window rejects bookings on both
        for api in (self.d, self.api):
            self.err(api.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": f"{THU}T19:00",
                                                         "party_size": 2}, token=self.bob, key="cl-chk"), 409, "table_unavailable")

    def test_L340_bad_imports_are_422_atomic_and_never_5xx(self):
        self.populate()
        export = self.api.call("GET", "/_test/export").json
        self.d.call("POST", "/_test/reset", fixture4())
        base = observe(self.d, {}, [])
        marker_before = self.d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"})
        self.assertEqual(marker_before.status, 200)
        statuses = {}
        rng = random.Random(77)
        cands = [(p, n) for p, n in walk(export) if p and not isinstance(n, (dict, list))]
        # targeted: revision-like numbers and flags
        muts = []
        for p, n in cands:
            k = str(p[-1])
            if "revision" in k or k in ("moved_count", "unused_seats", "index", "seq", "count", "interval_weeks"):
                for bad in (-1, True, "1", 1.5, None):
                    muts.append((p, bad, "number"))
            if k in ("changed", "applied", "exception"):
                for bad in (1, "true", None, 0):
                    muts.append((p, bad, "flag"))
        rng.shuffle(muts)
        for p, bad, kind in muts[:60]:
            doc = copy.deepcopy(export)
            get_at(doc, p[:-1])[p[-1]] = bad
            r = self.d.call("POST", "/_test/import", doc)
            statuses[(p, kind)] = r.status
            self.assertLess(r.status, 500, (p, bad, r))
            self.assertIn(r.status, (204, 400, 422), (p, bad, r))
            if r.status != 204:
                self.assertEqual(r.status, 422 if r.status != 400 else 400, (p, bad, r))
                self.assertEqual(self.d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).status, 200,
                                 "a rejected import leaves the previous state in place")
            else:
                self.d.call("POST", "/_test/reset", fixture4())
        rejected = sum(1 for v in statuses.values() if v == 422)
        self.assertGreater(rejected, 0, "at least some wrong-typed counters must be refused")
        # structure: dropping or retyping whole nodes with plan/closure/receipt in the path
        nodes = [(p, n) for p, n in walk(export) if p and isinstance(n, (dict, list)) and any(w in str(p[-1]) for w in ("plan", "closure", "receipt", "series"))]
        self.assertTrue(nodes, "the export names plans, closures or receipts")
        for p, n in nodes[:30]:
            for bad in ("x", 7, [], None, True):
                doc = copy.deepcopy(export)
                get_at(doc, p[:-1])[p[-1]] = bad
                r = self.d.call("POST", "/_test/import", doc)
                self.assertLess(r.status, 500, (p, bad, r))
                self.assertIn(r.status, (204, 400, 422), (p, bad, r))
                if r.status == 204:
                    self.d.call("POST", "/_test/reset", fixture4())
        for raw in ("{", "[]", "null", '"x"', "123", ""):
            r = self.d.call("POST", "/_test/import", raw=raw)
            self.assertIn(r.status, (400, 422), (raw, r))
        self.d.call("POST", "/_test/reset", fixture4())
        self.assertEqual(self.d.call("POST", "/_test/import", export).status, 204, "the genuine export still imports")

    def test_L333_L335_L336_L338_targeted_relations(self):
        self.populate()
        export = self.api.call("GET", "/_test/export").json
        self.d.call("POST", "/_test/reset", fixture4())

        def imp(doc):
            r = self.d.call("POST", "/_test/import", doc)
            self.assertLess(r.status, 500, r)
            return r

        # find a plan snapshot (contains assignments), a closure (contains table_id+from+to) and a receipt (contains key)
        plans = [p for p, n in walk(export) if isinstance(n, dict) and "assignments" in n and "plan_id" in n]
        self.assertTrue(plans, "plan snapshots are exported")
        closures = [p for p, n in walk(export) if isinstance(n, dict) and {"table_id", "from", "to"} <= set(n)]
        self.assertTrue(closures, "closures are exported")
        for p in closures[:4]:
            c = get_at(export, p)
            for field, bad in (("from", c["to"]), ("to", c["from"]), ("from", "nonsense"), ("to", "2030-01-03T20:00:00"), ("table_id", "t_404"),
                               ("table_id", 5), ("from", None)):
                doc = copy.deepcopy(export)
                get_at(doc, p)[field] = bad
                r = imp(doc)
                self.assertIn(r.status, (422, 400), (p, field, bad, r))
        for p in plans[:4]:
            n = get_at(export, p)
            muts = [("plan_id", ""), ("plan_id", 5), ("plan_id", "x" * 65), ("assignments", "x"), ("assignments", {})]
            for field, bad in muts:
                doc = copy.deepcopy(export)
                get_at(doc, p)[field] = bad
                r = imp(doc)
                self.assertIn(r.status, (422, 400), (p, field, bad, r))
            if n["assignments"]:
                for edit in (lambda a: a.append(copy.deepcopy(a[0])),                               # duplicate reference
                             lambda a: a[0].__setitem__("reference", "NOSUCHREF"),
                             lambda a: a[0].__setitem__("table_ids", ["t_404"]),
                             lambda a: a[0].__setitem__("table_ids", []),
                             lambda a: a[0].__setitem__("table_ids", ["t_1", "t_3"]),               # not a declared pair
                             lambda a: a[0].__setitem__("changed", "yes")):
                    doc = copy.deepcopy(export)
                    edit(get_at(doc, p)["assignments"])
                    r = imp(doc)
                    self.assertIn(r.status, (422, 400), (p, r))
        # two plans with the same id
        if len(plans) >= 2:
            doc = copy.deepcopy(export)
            a, b = get_at(doc, plans[0]), get_at(doc, plans[1])
            b["plan_id"] = a["plan_id"]
            r = imp(doc)
            if a != b:
                self.assertIn(r.status, (422, 400), r)
        # the genuine export still loads afterwards and an applied plan keeps refusing a second application
        self.assertEqual(imp(export).status, 204)
        self.err(self.d.call("POST", f"/restaurants/r_anker/replans/{self.p1['plan_id']}/apply", {}, token=self.ada, key="again"), 409, "plan_already_applied")

    def test_L333_L340_malformed_json_and_wrong_top_level_types(self):
        for raw in ("{", "[1,2", "", "{'a': 1}"):
            r = self.api.call("POST", "/_test/import", raw=raw)
            self.assertEqual(r.status, 400, (raw, r))
        before = self.rev()
        for doc in ([], None, 7, "x", True):
            r = self.api.call("POST", "/_test/import", doc)
            self.assertIn(r.status, (400, 422), (doc, r))
        self.assertEqual(self.rev(), before)

    def test_L332_reset_clears_closures_plans_receipts_and_revision(self):
        self.populate()
        self.assertGreater(self.rev(), 0)
        pid = self.p4["plan_id"]
        self.reset()
        self.assertEqual(self.rev(), 0)
        ada = self.ada
        self.err(self.apply(ada, pid), 404, "not_found")
        self.assertEqual(self.book(self.ada, f"{THU}T19:00", table="t_2", party=2, key="n-a").status, 201, "reset receipts: a reused key is new")
        self.assertEqual(self.book(self.bob, f"{THU}T19:00", table="t_2", party=2, key="n-a").status, 409)
        self.reset()
        self.assertEqual(self.slot_map("r_anker", THU, 1)["2030-01-03T19:00"]["available_table_ids"], ["t_1", "t_2", "t_3"])
        self.assertEqual(self.all_res(self.bob), [], "reset removed every imported/earlier booking")


# ====================================================================================== upgrade from earlier stages (343, 341, 342)
class UpgradeBase:
    err = Base4.err
    SRC_DIR = None
    SRC_FIXTURE = staticmethod(fixture3)
    LEVEL = 3

    @classmethod
    def setUpClass(cls):
        cls.src_base, cls.src_proc, cls.src_port = start_at(cls.SRC_DIR)
        s = Api(cls.src_base)
        f = cls.SRC_FIXTURE(reservations=[seed_res(1, "u_bob", "r_anker", "t_1", f"{FRI}T18:00", 2, "BOBSEED1")])
        f["users"][0]["password"] = PW
        assert s.call("POST", "/_test/reset", f).status == 204
        cls.tok_ada = login(s, "ada@example.com", PW)
        cls.tok_ada2 = login(s, "ada@example.com", PW)
        cls.tok_bob = login(s, "bob@example.com", "battery staple")
        cls.calls = []

        def call(method, path, body, tok, key, expect=None):
            r = s.call(method, path, body, token=tok, key=key)
            cls.calls.append((method, path, body, tok, key, r.status, r.json))
            if expect:
                assert r.status == expect, r
            return r
        bk = lambda k, tid, local, party, tok, **kw: call("POST", "/reservations", dict(
            {"restaurant_id": "r_anker", "starts_at_local": local, "party_size": party},
            **({"table_id": tid} if isinstance(tid, str) else {"table_ids": tid}), **kw), tok, k, 201).json
        cls.A = bk("u-A", "t_2", T, 2, cls.tok_bob)
        cls.B = bk("u-B", "t_3", T, 2, cls.tok_ada)
        cls.C = bk("u-C", "t_1", f"{THU}T21:00", 1, cls.tok_ada)
        cls.D = bk("u-D", "t_1", T, 2, cls.tok_bob)
        if cls.LEVEL >= 2:
            cls.P = bk("u-P", ["t_1", "t_2"], f"{add_days(THU, 8)}T19:00", 5, cls.tok_ada)       # off the weekly t_2 series dates
        s.call("POST", f"/reservations/{cls.C['reference']}/cancel", token=cls.tok_ada)
        cls.series_ids = []
        if cls.LEVEL >= 3:
            call("POST", "/restaurants/r_anker/policies", policy(add_days(THU, 21), duration=60, capacities={"t_1": 2, "t_2": 4, "t_3": 6}),
                 cls.tok_ada, "u-pol", 201)
            sr = call("POST", "/series", {"anchor_reference": cls.A["reference"], "count": 5, "interval_weeks": 1}, cls.tok_bob, "u-ser", 201).json
            refs = [o["reference"] for o in sr["occurrences"]]
            s.call("PATCH", f"/reservations/{refs[1]}", {"party_size": 3}, token=cls.tok_bob)
            s.call("PATCH", f"/reservations/{refs[2]}", {"starts_at_local": f"{add_days(THU, 14)}T20:30"}, token=cls.tok_bob)        # exception
            s.call("POST", f"/reservations/{refs[3]}/cancel", token=cls.tok_bob)
            call("POST", "/reservation-moves", {"moves": [{"reference": refs[4], "table_id": "t_3"}]}, cls.tok_bob, "u-mv")
            cls.series_ids = [(sr["series_id"], cls.tok_bob)]
            cls.refs = refs
        cls.failed = call("POST", "/reservations", dict({"restaurant_id": "r_anker", "starts_at_local": T, "party_size": 2}, table_id="nope"),
                          cls.tok_bob, "u-F", 404)
        cls.toks = {"ada": cls.tok_ada, "bob": cls.tok_bob}
        cls.before = observe(s, cls.toks, cls.series_ids)
        cls.export = s.call("GET", "/_test/export").json                            # private: memory only
        stop_process(cls.src_proc)
        cls.stopped_before_import = wait_port_closed(cls.src_port) and cls.src_proc.poll() is not None
        cls.dst_base, cls.dst_proc, _ = start_at(STAGE4_DIR)
        cls.d = Api(cls.dst_base)
        cls.d.call("POST", "/_test/reset", fixture4(reservations=[seed_res(9, "u_ada", "r_anker", "t_2", f"{THU}T20:00", 2, "DESTONLY")]))
        cls.dest_token = login(cls.d, "ada@example.com", "correct horse")
        cls.import_resp = cls.d.call("POST", "/_test/import", cls.export)

    @classmethod
    def tearDownClass(cls):
        for p in (cls.src_proc, cls.dst_proc):
            if p.poll() is None:
                p.kill()

    def setUp(self):
        self.assertEqual(self.d.call("POST", "/_test/import", self.export).status, 204)

    def test_L343_source_actually_stopped_before_independent_import(self):
        self.assertTrue(self.stopped_before_import, "the actual frozen source process must be down and its port closed before the import")
        self.assertNotEqual(self.src_base, self.dst_base)
        self.assertEqual((self.import_resp.status, self.import_resp.raw), (204, b""))

    def test_L341_old_tokens_logins_and_destination_data_replaced(self):
        for t in (self.tok_ada, self.tok_ada2, self.tok_bob):
            self.assertEqual(self.d.call("GET", "/reservations", token=t).status, 200)
        self.assertEqual(self.d.call("POST", "/auth/login", {"email": "ada@example.com", "password": PW}).status, 200)
        self.assertEqual(self.d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).status, 401)
        self.assertEqual(self.d.call("GET", "/reservations", token=self.dest_token).status, 401)
        self.assertEqual(self.d.call("GET", "/reservations/DESTONLY", token=self.tok_ada).status, 404)

    def test_L341_reservations_history_decisions_and_availability_survive(self):
        after = observe(self.d, self.toks, self.series_ids)
        if self.LEVEL >= 3:
            self.assertEqual(after, self.before, "stage 3 to stage 4 is the identity on everything readable")
            return
        for key, (status, js) in self.before.items():
            if key[0] == "avail":
                self.assertEqual(after[key][0], status)
                continue
            if key[-1] in ("/history", "/decision") and status == 404:
                # the old stage lacked these endpoints; after migration the owner reads them (stage 3 requirement 206/241, ledger 261)
                self.assertEqual(after[key][0], 200, (key, "an endpoint the old stage lacked is served to the owner after migration"))
                continue
            self.assertEqual(after[key][0], status, key)
            if key[-1] == "":
                for k, v in js.items():
                    self.assertEqual(after[key][1][k], v, (key, k))
                self.assertEqual((after[key][1]["revision"], after[key][1]["accepted_terms"]["policy_version"]), (1, 0))

    def test_L341_receipts_replay_originals_and_failed_keys_stay_failed(self):
        for method, path, body, tok, key, status, js in self.calls:
            r = self.d.call(method, path, body, token=tok, key=key)
            if status == 201:
                self.assertEqual((r.status, r.json), (200, js), (path, key))
            else:
                self.assertEqual(r.status, status, (path, key))
        r = self.d.call("POST", "/reservations", dict(self.calls[0][2], party_size=1), token=self.tok_bob, key="u-A")
        self.err(r, 409, "idempotency_key_reuse")

    def test_L341_restaurant_revision_is_well_defined_after_import(self):
        if self.LEVEL < 3:
            # stage 1/2 fixtures declare no manager_user_ids (stage 3 default []), so nobody may plan after the import
            self.err(self.d.call("POST", "/restaurants/r_anker/replans", {"table_id": "t_1", "from": FAR_FROM, "to": FAR_TO},
                                 token=self.tok_ada, key="no-mgr"), 403, "forbidden")
            return
        a = probe_rev(self.d, self.tok_ada)
        self.assertIs(type(a), int)
        self.assertGreaterEqual(a, 0)
        self.assertEqual(probe_rev(self.d, self.tok_ada), a, "previews do not move it")
        before = observe(self.d, self.toks, self.series_ids)
        r = self.d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_3", "starts_at_local": f"{add_days(THU, 28)}T20:00",
                                                   "party_size": 2}, token=self.tok_ada, key="post-imp")
        self.assertEqual(r.status, 201, r)
        self.assertEqual(probe_rev(self.d, self.tok_ada), a + 1)
        self.assertNotEqual(observe(self.d, self.toks, self.series_ids), before)

    def test_L341_replans_work_on_imported_bookings(self):
        if self.LEVEL < 3:
            self.err(self.d.call("POST", "/restaurants/r_anker/replans", {"table_id": "t_2", "from": inst(THU, "18:00"), "to": inst(THU, "23:00")},
                                 token=self.tok_ada, key="imp-p"), 403, "forbidden")
            return
        p = self.d.call("POST", "/restaurants/r_anker/replans", {"table_id": "t_2", "from": inst(THU, "18:00"), "to": inst(THU, "23:00")},
                        token=self.tok_ada, key="imp-p")
        self.assertIn(p.status, (201, 409), p)
        if p.status == 201:
            ap = self.d.call("POST", f"/restaurants/r_anker/replans/{p.json['plan_id']}/apply", {}, token=self.tok_ada, key="imp-ap")
            self.assertEqual(ap.status, 201, ap)
            for res in ap.json["reservations"]:
                self.assertIn(res["revision"], range(1, 20))
        else:
            self.assertEqual(p.json["error"]["code"], "no_feasible_plan")

    def test_L342_imported_series_support_amend_and_repair(self):
        if self.LEVEL < 3:
            # an imported legacy anchor is adopted (stage 3 requirement 262), then amended with stage-4 semantics
            d = self.d
            ad = d.call("POST", "/series", {"anchor_reference": self.A["reference"], "count": 3, "interval_weeks": 1}, token=self.tok_bob,
                        key="leg-ser")
            self.assertEqual(ad.status, 201, ad)
            sid = ad.json["series_id"]
            r = d.call("POST", f"/series/{sid}/amend", {"expected_revision": ad.json["revision"], "from_index": 1, "local_time": "20:00"},
                       token=self.tok_bob, key="leg-am")
            self.assertEqual(r.status, 201, r)
            self.assertEqual([o["reservation"]["starts_at_local"][11:16] for o in r.json["occurrences"]], [T[11:], "20:00", "20:00"])
            self.assertEqual(r.json["revision"], ad.json["revision"] + 1)
            self.assertEqual(d.call("POST", f"/series/{sid}/amend", {"expected_revision": ad.json["revision"], "from_index": 1,
                                                                      "local_time": "20:00"}, token=self.tok_bob, key="leg-am").json, r.json)
            self.err(d.call("POST", f"/series/{sid}/amend", {"expected_revision": ad.json["revision"], "from_index": 0, "local_time": "20:00"},
                            token=self.tok_bob, key="leg-stale"), 409, "stale_revision")
            return
        sid, tok = self.series_ids[0]
        d = self.d
        cur = d.call("GET", f"/series/{sid}", token=tok).json
        ex = [o["exception"] for o in cur["occurrences"]]
        self.assertEqual(ex, [False, False, True, False, False])
        sched = [o["reservation"]["starts_at_local"][:10] for o in cur["occurrences"]]
        r = d.call("POST", f"/series/{sid}/amend", {"expected_revision": cur["revision"], "from_index": 0, "local_time": "20:00"}, token=tok, key="imp-am")
        self.assertEqual(r.status, 201, r)
        n = r.json
        self.assertEqual([o["exception"] for o in n["occurrences"]], ex)
        self.assertEqual([o["reservation"]["starts_at_local"][:10] for o in n["occurrences"]], sched)
        self.assertEqual(n["revision"], cur["revision"] + 1)
        t = [o["reservation"]["starts_at_local"][11:16] for o in n["occurrences"]]
        self.assertEqual((t[0], t[1], t[3], t[4]), ("20:00", "20:00", cur["occurrences"][3]["reservation"]["starts_at_local"][11:16], "20:00"))
        self.assertEqual(t[2], "20:30", "the imported exception keeps its own time")
        self.assertEqual(n["occurrences"][3], cur["occurrences"][3], "the cancelled occurrence is untouched")
        # a repair that moves members keeps scheduled dates and exception flags
        cur = d.call("GET", f"/series/{sid}", token=tok).json
        tb = self.tids_of(cur["occurrences"][0]["reservation"])
        pl = d.call("POST", "/restaurants/r_anker/replans", {"table_id": tb[0], "from": inst(THU, "00:00"), "to": inst(add_days(THU, 70), "00:00")},
                    token=self.tok_ada, key="imp-rp")
        if pl.status == 201:
            ap = d.call("POST", f"/restaurants/r_anker/replans/{pl.json['plan_id']}/apply", {}, token=self.tok_ada, key="imp-rpa")
            self.assertEqual(ap.status, 201, ap)
            after = d.call("GET", f"/series/{sid}", token=tok).json
            self.assertEqual([o["exception"] for o in after["occurrences"]], ex)
            self.assertEqual([o["reservation"]["starts_at_local"][:10] for o in after["occurrences"]], sched)
            if any(x["changed"] for x in pl.json["assignments"] if x["reference"] in {o["reference"] for o in cur["occurrences"]}):
                self.assertEqual(after["revision"], cur["revision"] + 1)
        else:
            self.assertEqual(pl.json["error"]["code"], "no_feasible_plan")

    @staticmethod
    def tids_of(res):
        return res.get("table_ids") or [res["table_id"]]


class TestUpgradeFromStage3(UpgradeBase, unittest.TestCase):
    SRC_DIR = FROZEN_STAGE3
    SRC_FIXTURE = staticmethod(fixture3)
    LEVEL = 3


class TestUpgradeFromStage2(UpgradeBase, unittest.TestCase):
    SRC_DIR = FROZEN_STAGE2
    SRC_FIXTURE = staticmethod(fixture2)
    LEVEL = 2


class TestUpgradeFromStage1(UpgradeBase, unittest.TestCase):
    SRC_DIR = FROZEN_STAGE1
    SRC_FIXTURE = staticmethod(stage1_fixture)
    LEVEL = 1
