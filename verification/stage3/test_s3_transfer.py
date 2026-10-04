"""Stage 3 version transfer and state validation (ledger 87-102, 152, 194, 261-262, 273-277, 280-287, 290).

TestUpgradeFromStage2 / TestUpgradeFromStage1 start the actual frozen service, fill it, export, KILL it and confirm the port
is closed, and only then start an independent stage-3 destination and import. Exports (tokens, hashes) stay in memory.
"""
import copy
import json
import unittest

from s3common import (Api, Base3, FROZEN_STAGE1, FROZEN_STAGE2, STAGE3_DIR, THU, FRI, T, TERMS_KEYS, add_days, fixture2, fixture3,
                      stage1_fixture, policy, seed_res, start_at, stop_process, wait_port_closed, common)
from test_e_transfer import walk, get_at, replace_value, record_nodes


def fx_terms(rest_fixture):
    return {"policy_version": 0, "slot_minutes": rest_fixture["slot_minutes"],
            "reservation_duration_minutes": rest_fixture["reservation_duration_minutes"],
            "cancellation_cutoff_minutes": rest_fixture["cancellation_cutoff_minutes"],
            "opening_hours": rest_fixture["opening_hours"], "capacities": {t["id"]: t["capacity"] for t in rest_fixture["tables"]}}


class UpgradeBase(unittest.TestCase):
    err = Base3.err
    SRC_DIR = None
    SRC_FIXTURE = staticmethod(fixture2)

    @classmethod
    def setUpClass(cls):
        cls.src_base, cls.src_proc, cls.src_port = start_at(cls.SRC_DIR)
        s = Api(cls.src_base)
        f = cls.SRC_FIXTURE(reservations=[seed_res(1, "u_bob", "r_anker", "t_1", f"{FRI}T18:00", 2, "BOBSEED1")])
        f["users"][0]["password"] = "abc"
        assert s.call("POST", "/_test/reset", f).status == 204
        cls.fx = f
        cls.tok_ada = s.call("POST", "/auth/login", {"email": "ada@example.com", "password": "abc"}).json["token"]
        cls.tok_ada2 = s.call("POST", "/auth/login", {"email": "ada@example.com", "password": "abc"}).json["token"]
        cls.tok_bob = s.call("POST", "/auth/login", {"email": "bob@example.com", "password": "battery staple"}).json["token"]
        cls.bodies = {}

        def book(key, tid, local, party, tok, **kw):
            b = {"restaurant_id": "r_anker", "starts_at_local": local, "party_size": party}
            b.update({"table_id": tid} if isinstance(tid, str) else {"table_ids": tid})
            b.update(kw)
            r = s.call("POST", "/reservations", b, token=tok, key=key)
            assert r.status == 201, r
            cls.bodies[key] = (b, tok, r.json)
            return r.json
        cls.A = book("u-A", "t_2", T, 2, cls.tok_ada)
        cls.B = book("u-B", "t_3", T, 2, cls.tok_ada)
        cls.C = book("u-C", "t_1", f"{THU}T21:00", 1, cls.tok_ada)
        cls.D = book("u-D", "t_1", T, 2, cls.tok_bob)
        if cls.SRC_DIR == FROZEN_STAGE2:
            cls.P = book("u-P", ["t_1", "t_2"], f"{add_days(THU, 7)}T19:00", 5, cls.tok_ada)
        s.call("POST", f"/reservations/{cls.C['reference']}/cancel", token=cls.tok_ada)
        cls.moves_body = {"moves": [{"reference": cls.A["reference"], "table_id": "t_3"}, {"reference": cls.B["reference"], "table_id": "t_2"}]}
        cls.moves_resp = s.call("POST", "/reservation-moves", cls.moves_body, token=cls.tok_ada, key="u-M")
        assert cls.moves_resp.status == 201
        cls.patched = s.call("PATCH", f"/reservations/{cls.B['reference']}", {"starts_at_local": f"{THU}T21:00"}, token=cls.tok_ada).json
        cls.failed = s.call("POST", "/reservations", dict(cls.bodies["u-A"][0], table_id="nope"), token=cls.tok_bob, key="u-F")
        assert cls.failed.status == 404
        cls.list_ada = s.call("GET", "/reservations", token=cls.tok_ada).json["reservations"]
        cls.list_bob = s.call("GET", "/reservations", token=cls.tok_bob).json["reservations"]
        cls.avail_src = {d: s.call("GET", f"/availability?restaurant_id=r_anker&date={d}&party_size=1").json for d in (THU, FRI)}
        cls.export = s.call("GET", "/_test/export").json                         # private: memory only
        stop_process(cls.src_proc)
        cls.stopped_before_import = wait_port_closed(cls.src_port) and cls.src_proc.poll() is not None
        cls.dst_base, cls.dst_proc, _ = start_at(STAGE3_DIR)
        cls.d = Api(cls.dst_base)
        cls.d.call("POST", "/_test/reset", fixture3(reservations=[seed_res(9, "u_ada", "r_anker", "t_2", f"{THU}T20:00", 2, "DESTONLY")]))
        cls.dest_token = cls.d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).json["token"]
        cls.import_resp = cls.d.call("POST", "/_test/import", cls.export)

    @classmethod
    def tearDownClass(cls):
        for p in (cls.src_proc, cls.dst_proc):
            if p.poll() is None:
                p.kill()

    def setUp(self):
        self.assertEqual(self.d.call("POST", "/_test/import", self.export).status, 204)

    def owners(self):
        return ((self.tok_ada, self.list_ada), (self.tok_bob, self.list_bob))

    # ------------------------------------------------------------------ the tests (shared by both sources)
    def test_L152_L194_L286_source_stopped_before_import_and_import_accepted(self):
        self.assertTrue(self.stopped_before_import, "the actual source process must be down before the import")
        self.assertEqual((self.import_resp.status, self.import_resp.raw), (204, b""))

    def test_L153_L186_tokens_logins_and_destination_data_replaced(self):
        d = self.d
        for t in (self.tok_ada, self.tok_ada2, self.tok_bob):
            self.assertEqual(d.call("GET", "/reservations", token=t).status, 200)
        self.assertEqual(d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "abc"}).json["user_id"], "u_ada")
        self.assertEqual(d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).status, 401)
        self.assertEqual(d.call("GET", "/reservations", token=self.dest_token).status, 401)
        self.assertEqual(d.call("GET", "/reservations/DESTONLY", token=self.tok_ada).status, 404)

    def test_L261_L282_imported_bookings_gain_revision_one_policy_zero_terms_and_keep_identity(self):
        d = self.d
        rest = next(r for r in self.fx["restaurants"] if r["id"] == "r_anker")
        for tok, mine in self.owners():
            for before in mine:
                r = d.call("GET", f"/reservations/{before['reference']}", token=tok)
                self.assertEqual(r.status, 200, before)
                j = r.json
                self.assertEqual((j["revision"], j["accepted_terms"]), (1, fx_terms(rest)), before["reference"])
                for k, v in before.items():
                    self.assertEqual(j[k], v, (before["reference"], k))                   # identity, status, timestamps, tables kept
                self.assertEqual(set(j) - set(before), {"revision", "accepted_terms"} | ({"table_ids"} if "table_ids" not in before else set()))
                h = d.call("GET", f"/reservations/{before['reference']}/history", token=tok)
                self.assertEqual(h.status, 200)
                ents = h.json["entries"]
                self.assertIn(len(ents), (0, 1))
                for e in ents:
                    self.assertEqual((e["seq"], e["event"], e["revision"]), (1, "created", 1))
                dec = d.call("GET", f"/reservations/{before['reference']}/decision", token=tok).json
                self.assertEqual((dec["revision"], dec["accepted_terms"]), (1, fx_terms(rest)))
        self.assertEqual(d.call("GET", "/reservations/BOBSEED1", token=self.tok_bob).json["reservation_id"], "res_s1")
        self.assertEqual(d.call("GET", f"/reservations/{self.A['reference']}/history", token=self.tok_bob).status, 404)

    def test_L233_L185_original_receipt_responses_stay_exact(self):
        d = self.d
        for key, (body, tok, original) in self.bodies.items():
            r = d.call("POST", "/reservations", body, token=tok, key=key)
            self.assertEqual((r.status, r.json), (200, original), key)
            self.assertNotIn("revision", r.json)
            self.assertNotIn("accepted_terms", r.json)
        r = d.call("POST", "/reservation-moves", self.moves_body, token=self.tok_ada, key="u-M")
        self.assertEqual((r.status, r.json), (200, self.moves_resp.json))
        self.assertTrue(all("revision" not in x for x in r.json["reservations"]))

    def test_L094_L282_L284_receipt_rules_and_failed_keys_after_the_upgrade(self):
        d = self.d
        body, tok, _ = self.bodies["u-A"]
        self.err(d.call("POST", "/reservations", dict(body, party_size=1), token=tok, key="u-A"), 409, "idempotency_key_reuse")
        ok = d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_1", "starts_at_local": f"{FRI}T20:00", "party_size": 1},
                    token=self.tok_bob, key="u-F")
        self.assertEqual(ok.status, 201, ok)                                           # failed key reusable
        self.assertEqual((ok.json["revision"], ok.json["accepted_terms"]["policy_version"]), (1, 0))
        other = d.call("POST", "/reservations", dict(body, table_id="t_1", starts_at_local=f"{FRI}T21:30", party_size=1),
                       token=self.tok_bob, key="u-A")
        self.assertEqual(other.status, 201, other)

    def test_L262_imported_booking_can_be_amended_and_adopted_into_a_series(self):
        d = self.d
        cur = d.call("GET", f"/reservations/{self.D['reference']}", token=self.tok_bob).json
        r = d.call("PATCH", f"/reservations/{self.D['reference']}", {"expected_revision": 1, "party_size": 1}, token=self.tok_bob)
        self.assertEqual((r.status, r.json["revision"]), (200, 2))
        s = d.call("POST", "/series", {"anchor_reference": self.D["reference"], "count": 3, "interval_weeks": 1}, token=self.tok_bob, key="adopt-1")
        self.assertEqual(s.status, 201, s)
        self.assertEqual(s.json["occurrences"][0]["reference"], self.D["reference"])
        self.assertEqual(s.json["occurrences"][0]["reservation"]["revision"], 2)
        self.assertEqual([o["reservation"]["starts_at_local"][:10] for o in s.json["occurrences"]], [T[:10], add_days(THU, 7), add_days(THU, 14)])
        h = d.call("GET", f"/reservations/{self.D['reference']}/history", token=self.tok_bob).json["entries"]
        self.assertEqual(h[-1]["event"], "changed")

    def test_L184_L205_stage1_and_2_configs_have_no_managers_and_policy_zero_availability(self):
        d = self.d
        for date in (THU, FRI):
            now = d.call("GET", f"/availability?restaurant_id=r_anker&date={date}&party_size=1").json
            for a, b in zip(self.avail_src[date]["slots"], now["slots"]):
                self.assertEqual(a["available_table_ids"], b["available_table_ids"])
        ex = d.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=1&explain=true").json["slots"]
        self.assertTrue(all(e["policy_version"] == 0 for s in ex for e in s["explain"]))
        self.err(d.call("POST", "/restaurants/r_anker/policies", policy(THU), token=self.tok_ada, key="pol-1"), 403, "forbidden")
        self.assertEqual(d.call("GET", "/restaurants/r_anker/policies").json, {"policies": []})

    def test_L093_L188_occupancy_preserved_and_cancelled_free(self):
        d = self.d
        cur = self.patched
        r = d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": cur["table_id"], "starts_at_local": cur["starts_at_local"],
                                              "party_size": 1}, token=self.tok_bob, key="u-occ")
        self.err(r, 409, "table_unavailable")
        r = d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_1", "starts_at_local": f"{THU}T21:00", "party_size": 1},
                   token=self.tok_bob, key="u-free")
        self.assertEqual(r.status, 201, r)

    def test_L186_new_identities_do_not_collide(self):
        d = self.d
        old = {x["reference"] for _, l in self.owners() for x in l} | {"BOBSEED1"}
        new = [d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_3", "starts_at_local": f"2030-03-0{i + 4}T19:00",
                                                 "party_size": 2}, token=self.tok_ada, key=f"u-n{i}").json for i in range(5)]
        self.assertFalse(old & {n["reference"] for n in new})
        self.assertEqual(len({n["reference"] for n in new}), 5)


class TestUpgradeFromStage2(UpgradeBase):
    SRC_DIR = FROZEN_STAGE2

    def test_L184_L152_stage2_pair_bookings_and_receipts_survive(self):
        d = self.d
        r = d.call("GET", f"/reservations/{self.P['reference']}", token=self.tok_ada).json
        self.assertEqual((sorted(r["table_ids"]), "table_id" in r, r["revision"]), (["t_1", "t_2"], False, 1))
        self.assertEqual(r["accepted_terms"]["capacities"], {"t_1": 2, "t_2": 4, "t_3": 6})
        body, tok, original = self.bodies["u-P"]
        again = d.call("POST", "/reservations", body, token=tok, key="u-P")
        self.assertEqual((again.status, again.json), (200, original))
        self.assertEqual(d.call("GET", "/restaurants/r_anker").json["combinable"], [["t_1", "t_2"], ["t_2", "t_3"]])
        h = d.call("GET", f"/reservations/{self.P['reference']}/history", token=self.tok_ada).json["entries"]
        self.assertIn(len(h), (0, 1))
        if h:
            self.assertEqual(h[0]["changes"][0]["field"], "table_ids")
        # an imported pair keeps occupying both members and can be amended with stage 3 history rules
        pd = f"{add_days(THU, 7)}T19:00"
        self.err(d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": pd, "party_size": 1},
                        token=self.tok_bob, key="u-pp"), 409, "table_unavailable")
        r = d.call("PATCH", f"/reservations/{self.P['reference']}", {"table_ids": ["t_3"], "party_size": 5}, token=self.tok_ada)
        self.assertEqual((r.status, r.json["revision"], r.json["table_id"]), (200, 2, "t_3"))
        h = d.call("GET", f"/reservations/{self.P['reference']}/history", token=self.tok_ada).json["entries"][-1]
        self.assertEqual(h["changes"][0], {"field": "table_ids", "from": ["t_1", "t_2"], "to": ["t_3"]})


class TestUpgradeFromStage1(UpgradeBase):
    SRC_DIR = FROZEN_STAGE1
    SRC_FIXTURE = staticmethod(stage1_fixture)

    def test_L152_stage1_exports_get_table_ids_and_no_pairs(self):
        d = self.d
        r = d.call("GET", f"/reservations/{self.A['reference']}", token=self.tok_ada).json
        self.assertEqual(r["table_ids"], [r["table_id"]])
        self.err(d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_ids": ["t_1", "t_2"], "starts_at_local": f"{THU}T18:00",
                                                  "party_size": 3}, token=self.tok_ada, key="u-np"), 422, "combination_not_allowed")


class Stage3Roundtrip(Base3):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dbase, cls.dproc, _ = start_at(STAGE3_DIR)
        cls.dst = Api(cls.dbase)

    @classmethod
    def tearDownClass(cls):
        cls.dproc.kill()

    def populate(self):
        ada, bob = self.ada, self.bob
        self.ada_t, self.bob_t = ada, bob
        self.reqs = []                                           # (method, path, body, token, key, original response)

        def rec(method, path, body, tok, key):
            r = self.api.call(method, path, body, token=tok, key=key)
            self.reqs.append((method, path, body, tok, key, r))
            return r
        rec("POST", "/restaurants/r_anker/policies", policy("2030-01-15", duration=60, cutoff=30), ada, "s3-pol-1")
        rec("POST", "/restaurants/r_anker/policies", policy("2030-01-15", duration=75, cutoff=20), ada, "s3-pol-2")
        self.assertEqual(self.publish(ada, {"effective_from": "bad"}, key="s3-badpol").status, 422)
        a = rec("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": T, "party_size": 2}, bob, "s3-a")
        p = rec("POST", "/reservations", {"restaurant_id": "r_anker", "table_ids": ["t_1", "t_2"], "starts_at_local": f"{THU}T21:00", "party_size": 6},
                bob, "s3-p")
        x = rec("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_3", "starts_at_local": T, "party_size": 3}, bob, "s3-x")
        self.assertEqual((a.status, p.status, x.status), (201,) * 3)
        self.patch(a.json["reference"], {"starts_at_local": f"{add_days(THU, 14)}T19:00", "party_size": 3}, bob)
        self.patch(a.json["reference"], {"table_ids": ["t_1", "t_2"], "party_size": 5}, bob)
        s = rec("POST", "/series", {"anchor_reference": x.json["reference"], "count": 4, "interval_weeks": 1}, bob, "s3-ser")
        self.assertEqual(s.status, 201, s)
        self.series = s.json
        refs = [o["reference"] for o in s.json["occurrences"]]
        self.patch(refs[2], {"party_size": 4}, bob)
        self.api.call("POST", f"/reservations/{refs[3]}/cancel", token=bob)
        m = rec("POST", "/reservation-moves", {"moves": [{"reference": refs[1], "party_size": 2}, {"reference": refs[2], "party_size": 2}]}, bob, "s3-mv")
        self.assertEqual(m.status, 201, m)
        self.err(self.adopt(x.json["reference"], 3, 1, bob, key="s3-already"), 409, "already_in_series")
        self.refs = [a.json["reference"], p.json["reference"]] + refs
        self.api.call("POST", f"/reservations/{p.json['reference']}/cancel", token=bob)

    def views(self, api, ada, bob):
        out = {"ada": api.call("GET", "/reservations", token=ada).json, "bob": api.call("GET", "/reservations", token=bob).json,
               "policies": api.call("GET", "/restaurants/r_anker/policies").json,
               "series": api.call("GET", f"/series/{self.series['series_id']}", token=bob).json}
        for ref in self.refs:
            out["h" + ref] = api.call("GET", f"/reservations/{ref}/history", token=bob).json
            out["d" + ref] = api.call("GET", f"/reservations/{ref}/decision", token=bob).json
        for d in (THU, add_days(THU, 14), "2030-02-01"):
            out["e" + d] = api.call("GET", f"/availability?restaurant_id=r_anker&date={d}&party_size=2&explain=true").json
        return out

    def test_L287_roundtrip_carries_every_new_kind_of_state_and_receipt(self):
        self.populate()
        view = self.views(self.api, self.ada_t, self.bob_t)
        exp = self.api.call("GET", "/_test/export").json
        d = self.dst
        self.assertEqual(d.call("POST", "/_test/import", exp).status, 204)
        self.assertEqual(self.views(d, self.ada_t, self.bob_t), view)
        for method, path, body, tok, key, original in self.reqs:
            r = d.call(method, path, body, token=tok, key=key)
            self.assertEqual((r.status, r.json), (200, original.json), (path, key))
        self.assertEqual(self.views(d, self.ada_t, self.bob_t), view, "replays changed nothing")
        # counters continue where they were
        self.assertEqual(d.call("POST", "/restaurants/r_anker/policies", policy("2030-05-01"), token=self.ada_t, key="s3-next").json["policy_version"], 3)
        ref0 = self.refs[0]
        cur = d.call("GET", f"/reservations/{ref0}/decision", token=self.bob_t).json["revision"]
        r = d.call("PATCH", f"/reservations/{ref0}", {"expected_revision": cur, "party_size": 4}, token=self.bob_t)
        self.assertEqual((r.status, r.json["revision"]), (200, cur + 1))
        s0 = view["series"]["revision"]
        o1 = self.series["occurrences"][1]["reference"]
        self.assertEqual(d.call("PATCH", f"/reservations/{o1}", {"party_size": 1}, token=self.bob_t).status, 200)    # a real change
        g = d.call("GET", f"/series/{self.series['series_id']}", token=self.bob_t).json
        self.assertEqual((g["revision"], g["occurrences"][1]["exception"]), (s0 + 1, True))
        self.err(d.call("PATCH", f"/reservations/{ref0}", {"expected_revision": cur, "party_size": 2}, token=self.bob_t), 409, "stale_revision")

    def test_L283_export_is_a_detached_snapshot_across_the_new_state(self):
        self.populate()
        view = self.views(self.api, self.ada_t, self.bob_t)
        exp = self.api.call("GET", "/_test/export").json
        self.ok_publish(policy("2031-01-01"))
        self.patch(self.refs[0], {"party_size": 2}, self.bob_t)
        self.adopt(self.ok_book(self.bob_t, f"{THU}T18:00", table="t_1", party=1)["reference"], 2, 1, self.bob_t)
        self.assertEqual(self.dst.call("POST", "/_test/import", exp).status, 204)
        self.assertEqual(self.views(self.dst, self.ada_t, self.bob_t), view)

    def test_L090_repeated_import_restores_exactly_and_replaces(self):
        self.populate()
        exp = self.api.call("GET", "/_test/export").json
        view = self.views(self.api, self.ada_t, self.bob_t)
        d = self.dst
        d.call("POST", "/_test/reset", fixture3(reservations=[seed_res(9, "u_ada", "r_anker", "t_2", f"{THU}T20:00", 2, "DESTONLY")]))
        for _ in range(3):
            self.assertEqual(d.call("POST", "/_test/import", exp).status, 204)
            self.assertEqual(self.views(d, self.ada_t, self.bob_t), view)
        self.assertEqual(d.call("GET", "/reservations/DESTONLY", token=self.ada_t).status, 404)

    def test_L279_reset_clears_new_state_and_old_tokens(self):
        self.populate()
        self.reset()
        self.err(self.api.call("GET", "/reservations", token=self.bob_t), 401, "unauthenticated")
        self.assertEqual(self.api.call("GET", "/restaurants/r_anker/policies").json, {"policies": []})
        self.err(self.api.call("GET", f"/series/{self.series['series_id']}", token=self.bob), 404, "not_found")
        self.assertEqual(self.ok_publish(policy(THU))["policy_version"], 1)
        self.assertEqual(self.ok_book(self.bob, T, table="t_2", party=2)["revision"], 1)


class ImportValidation3(Base3):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dbase, cls.dproc, _ = start_at(STAGE3_DIR)
        cls.dst = Api(cls.dbase)

    @classmethod
    def tearDownClass(cls):
        cls.dproc.kill()

    def setUp(self):
        super().setUp()
        self.ok_publish(policy("2030-01-15", duration=60))
        self.ok_publish(policy("2030-01-20", duration=75))
        self.a = self.ok_book(self.bob, T, table="t_2", party=2)
        self.patch(self.a["reference"], {"party_size": 3}, self.bob)
        self.patch(self.a["reference"], {"starts_at_local": "2030-01-17T19:00"}, self.bob)
        self.s = self.ok_adopt(self.ok_book(self.bob, f"{THU}T21:00", table="t_3", party=2)["reference"], 3, 1, self.bob)
        self.moves([{"reference": self.s["occurrences"][1]["reference"], "party_size": 3}], self.bob, key="iv-m")
        self.exp = self.api.call("GET", "/_test/export").json
        self.restore()

    def restore(self):
        self.dst.call("POST", "/_test/reset", fixture3(reservations=[seed_res(9, "u_ada", "r_anker", "t_2", f"{THU}T20:00", 2, "KEEPME1")]))
        self.keep = self.dst.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).json["token"]
        self.before = self.dst.call("GET", "/_test/export").json

    def unchanged(self, what=""):
        self.assertEqual(self.dst.call("GET", "/_test/export").json, self.before, what)
        self.assertEqual(self.dst.call("GET", "/reservations/KEEPME1", token=self.keep).status, 200, what)
        self.assertEqual(self.dst.call("GET", "/restaurants/r_anker/policies").json, {"policies": []}, what)

    def imp(self, state):
        return self.dst.call("POST", "/_test/import", {"track": "tablekeeper", "format_version": 1, "state": state})

    def mutate(self, predicate, replacements, what):
        st0 = self.exp["state"]
        found = [p for p, n in walk(st0) if p and predicate(p, n)]
        if not found:
            self.skipTest(f"{what}: not visible in the opaque state")
        for p in found[:6]:
            for rep in replacements:
                st = copy.deepcopy(st0)
                get_at(st, p[:-1])[p[-1]] = rep
                r = self.imp(st)
                self.assertLess(r.status, 500, (p, rep, r))
                self.err(r, 422, "validation_failed")
                self.unchanged(f"{what} {p} {rep}")

    def test_L281_bad_counters_are_rejected_atomically(self):
        for key, bad in (("revision", [0, -1, True, "2", 1.5, None]), ("policy_version", [-1, True, "1", 1.5, None]),
                         ("seq", [0, -1, True, "1", 1.5, None]), ("interval_weeks", [0, 5, True, "1", None]),
                         ("exception", ["yes", 1, None, 0])):
            self.mutate(lambda p, n, key=key: p[-1] == key and not isinstance(n, (dict, list)), bad, key)

    def test_L281_L273_terms_and_policy_fields_are_validated(self):
        for key, bad in (("slot_minutes", [0, 1441, True, "30", 1.5, None]), ("reservation_duration_minutes", [0, 1441, True, None]),
                         ("cancellation_cutoff_minutes", [-1, 10081, True, None]), ("effective_from", ["2030-02-30", 5, None, True]),
                         ("capacities", [{}, [], "x", {"t_1": 0}, {"t_1": True, "t_2": 4, "t_3": 6}, None])):
            self.mutate(lambda p, n, key=key: p[-1] == key, bad, key)

    def test_L281_L272_history_sequence_and_events_are_validated(self):
        st0 = self.exp["state"]
        lists = [(p, n) for p, n in walk(st0) if isinstance(n, list) and n and all(isinstance(e, dict) and "seq" in e for e in n)]
        if not lists:
            self.skipTest("history lists not visible in the opaque state")
        p, n = max(lists, key=lambda x: len(x[1]))
        self.assertGreaterEqual(len(n), 2)
        variants = []
        v = copy.deepcopy(n); v[0], v[1] = v[1], v[0]; variants.append(v)                      # out of seq order
        v = copy.deepcopy(n); v[1]["seq"] = v[0]["seq"]; variants.append(v)                    # duplicate seq
        v = copy.deepcopy(n); v[1]["seq"] = 7; variants.append(v)                              # gap
        v = copy.deepcopy(n); v[1]["event"] = "exploded"; variants.append(v)
        v = copy.deepcopy(n); v[0]["event"] = "changed"; variants.append(v)                    # history must start with creation
        v = copy.deepcopy(n); del v[0]; variants.append(v)
        v = copy.deepcopy(n); v[1]["revision"] = v[0]["revision"] + 5; variants.append(v)
        v = copy.deepcopy(n); v[1]["changes"] = "x"; variants.append(v)
        for rep in variants:
            st = copy.deepcopy(st0)
            get_at(st, p[:-1])[p[-1]] = rep
            r = self.imp(st)
            self.assertLess(r.status, 500)
            self.err(r, 422, "validation_failed")
            self.unchanged(str(rep)[:80])

    def test_L274_L276_series_membership_is_validated(self):
        st0 = self.exp["state"]
        occ = [(p, n) for p, n in walk(st0) if isinstance(n, list) and len(n) == 3 and all(isinstance(e, dict) and "index" in e for e in n)]
        if not occ:
            self.skipTest("series occurrences not visible in the opaque state")
        p, n = occ[0]
        variants = []
        v = copy.deepcopy(n); v[1]["index"] = 0; variants.append(v)                              # duplicate index
        v = copy.deepcopy(n); v[2]["index"] = 5; variants.append(v)                              # gap
        v = copy.deepcopy(n); v.pop(); variants.append(v)                                        # shorter than count / index sequence
        v = copy.deepcopy(n)
        for k in v[1]:
            if isinstance(v[1][k], str) and v[1][k] == n[0].get(k) and k != "index":
                break
        refk = next((k for k in n[0] if isinstance(n[0][k], str) and k.startswith("ref")), None)
        if refk:
            v = copy.deepcopy(n); v[1][refk] = v[0][refk]; variants.append(v)                     # one reservation twice
            v = copy.deepcopy(n); v[1][refk] = "NOSUCHREF"; variants.append(v)                     # unknown reservation
        for rep in variants:
            st = copy.deepcopy(st0)
            get_at(st, p[:-1])[p[-1]] = rep
            r = self.imp(st)
            self.assertLess(r.status, 500)
            self.err(r, 422, "validation_failed")
            self.unchanged(str(rep)[:80])

    def test_L280_manager_and_owner_relations_are_validated(self):
        st0 = self.exp["state"]
        uid = "u_ada"
        found = [p for p, n in walk(st0) if p and n == [uid] and "manager" in str(p[-1])]
        if not found:
            self.skipTest("manager lists not visible in the opaque state")
        for rep in (["u_nobody"], [uid, uid], "u_ada", [1], [True]):
            st = copy.deepcopy(st0)
            get_at(st, found[0][:-1])[found[0][-1]] = rep
            r = self.imp(st)
            self.assertLess(r.status, 500)
            self.err(r, 422, "validation_failed")
            self.unchanged(str(rep))

    def test_L281_fuzz_never_5xx_and_rejections_are_atomic(self):
        paths = [p for p, n in walk(self.exp["state"]) if p]
        step = max(1, len(paths) // 220)
        rejected = 0
        for p in paths[::step]:
            for kind in ("delete", "wrongtype"):
                st = copy.deepcopy(self.exp["state"])
                parent = get_at(st, p[:-1])
                if kind == "delete":
                    if isinstance(parent, dict):
                        del parent[p[-1]]
                    else:
                        parent.pop(p[-1])
                else:
                    cur = parent[p[-1]]
                    parent[p[-1]] = {"x": 1} if isinstance(cur, (str, int, float, bool)) else "oops"
                r = self.imp(st)
                self.assertLess(r.status, 500, (p, kind, r))
                if r.status == 204:
                    self.restore()
                else:
                    rejected += 1
                    self.err(r, 422, "validation_failed")
                    self.unchanged(f"{p} {kind}")
        self.assertGreater(rejected, 40)

    def test_L282_envelope_failures(self):
        e = self.exp
        for c in ({}, dict(e, track="pocketful"), dict(e, format_version=2), dict(e, format_version="1"), dict(e, state=[]), dict(e, state=None),
                  {"track": "tablekeeper", "format_version": 1}):
            self.err(self.dst.call("POST", "/_test/import", c), 422, "validation_failed")
            self.unchanged()
        for raw in ("{x", "", "[]"):
            self.err(self.dst.call("POST", "/_test/import", raw=raw), 400, "malformed_request")
        self.unchanged()
