"""Export / import and state-validation checks (ledger 87-102).

Exports contain tokens and password hashes: they are kept in memory only, never written to disk.
Source is service 1, destination is an independently started service 2 (other process and port).
"""
import copy
import json
import unittest

from common import (Api, Base, THU, FRI, base_url, fixture, seed_res, clock_minute, hours, table)


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


def set_at(root, path, val):
    get_at(root, path[:-1])[path[-1]] = val


def replace_value(node, old, new):
    """Replace string values equal to `old` (and dict keys equal to old) everywhere."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            out[new if k == old else k] = replace_value(v, old, new)
        return out
    if isinstance(node, list):
        return [replace_value(v, old, new) for v in node]
    return new if node == old and isinstance(node, str) else node


def contains_value(node, val):
    return any(isinstance(n, str) and n == val for _, n in walk(node)) or \
        any(isinstance(n, dict) and val in n for _, n in walk(node))


def record_nodes(state, anchor):
    """Dict nodes (and their parent info) that hold `anchor` as a value or as a key."""
    out = []
    for path, n in walk(state):
        if isinstance(n, dict) and (
                any(isinstance(k, str) and anchor in k for k in n) or
                any(isinstance(v, str) and anchor in v for v in n.values())):
            out.append(path)
    return out


class Populated(Base):
    """Build realistic state on service 1."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dst = Api(base_url(2))

    def populate(self):
        extra = [seed_res(1, "u_bob", "r_anker", "t_1", f"{FRI}T18:00", 2, "BOBSEED1")]
        self.reset(fixture(reservations=extra))
        s = self
        s.signup = self.api.call("POST", "/auth/signup", {"email": "new@example.com", "password": "pw-12345678",
                                                           "display_name": "New"}).json
        s.t_ada = self.tok("ada@example.com")
        s.t_ada2 = self.tok("ada@example.com")
        s.t_bob = self.tok("bob@example.com")
        s.k1 = "xfer-create-1"
        body = {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": f"{THU}T19:00", "party_size": 2}
        s.create_body = body
        s.create_resp = self.api.call("POST", "/reservations", body, token=s.t_ada, key=s.k1)
        assert s.create_resp.status == 201, s.create_resp
        b = self.ok_book(s.t_ada, f"{THU}T19:00", table="t_3", key="xfer-create-2")
        c = self.ok_book(s.t_ada, f"{THU}T21:00", table="t_1", party=1, key="xfer-create-3")
        s.cancelled = self.api.call("POST", f"/reservations/{c['reference']}/cancel", token=s.t_ada).json
        s.moves_body = {"moves": [{"reference": s.create_resp.json["reference"], "table_id": "t_3"},
                                  {"reference": b["reference"], "table_id": "t_2"}]}
        s.moves_resp = self.api.call("POST", "/reservation-moves", s.moves_body, token=s.t_ada, key="xfer-moves-1")
        assert s.moves_resp.status == 201, s.moves_resp
        # later changes after the batch (replay must still return the original response)
        s.patched = self.api.call("PATCH", f"/reservations/{b['reference']}", {"starts_at_local": f"{THU}T21:00"},
                                  token=s.t_ada).json
        # failed key (4xx) stays reusable
        s.failed = self.api.call("POST", "/reservations", dict(body, table_id="nope"), token=s.t_bob, key="xfer-failed")
        assert s.failed.status == 404
        self.bobs = self.ok_book(s.t_bob, f"{THU}T19:00", table="t_1", party=2, key="xfer-bob-1", rest="r_anker")

    def snapshot_view(self, api, token_ada, token_bob):
        out = {}
        out["ada"] = api.call("GET", "/reservations", token=token_ada).json
        out["bob"] = api.call("GET", "/reservations", token=token_bob).json
        out["rest"] = api.call("GET", "/restaurants").json
        out["detail"] = api.call("GET", "/restaurants/r_anker").json
        out["avail"] = api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=1").json
        out["avail_fri"] = api.call("GET", f"/availability?restaurant_id=r_anker&date={FRI}&party_size=1").json
        return out

    def export(self, api=None):
        r = (api or self.api).call("GET", "/_test/export")
        self.assertEqual(r.status, 200, "export failed")
        return r.json


class Export(Populated):
    def test_L087_export_shape(self):
        self.populate()
        r = self.api.call("GET", "/_test/export")
        self.assertEqual(r.status, 200)
        self.assertTrue(r.ctype.lower().replace(" ", "").startswith("application/json;charset=utf-8"))
        j = r.json
        self.assertIsInstance(j, dict)
        self.assertEqual(j["track"], "tablekeeper")
        self.assertEqual(j["format_version"], 1)
        self.assertIs(type(j["format_version"]), int)
        self.assertIsInstance(j["state"], dict)
        self.assertEqual(set(j), {"track", "format_version", "state"})

    def test_L088_export_read_only_and_stable(self):
        self.populate()
        a = self.api.call("GET", "/_test/export").raw
        b = self.api.call("GET", "/_test/export").raw
        self.assertEqual(json.loads(a), json.loads(b))
        # reading does not alter observable state

    def test_L088_export_detached_from_later_writes(self):
        self.populate()
        exp = self.export()
        frozen = copy.deepcopy(exp)
        self.ok_book(self.t_ada, f"{FRI}T21:00", table="t_3", party=2)
        self.api.call("POST", "/auth/signup", {"email": "later@x.y", "password": "12345678", "display_name": "L"})
        self.assertEqual(exp, frozen)                      # my copy is of course unchanged: use import to prove it
        self.reset()
        self.assertEqual(self.api.call("POST", "/_test/import", exp).status, 204)
        self.assertEqual(len(self.api.call("GET", "/reservations", token=self.t_ada).json["reservations"]), 3)
        self.err(self.api.call("POST", "/auth/login", {"email": "later@x.y", "password": "12345678"}), 401, "unauthenticated")

    def test_L088_export_during_concurrent_writes_is_consistent(self):
        self.populate()
        calls = [lambda i=i: self.book(self.t_ada, f"{FRI}T{19 + i % 3}:00", table=("t_1", "t_2", "t_3")[i % 3],
                                       key=f"cw-{i}") for i in range(9)]
        calls += [lambda: self.api.call("GET", "/_test/export")] * 6
        outs = self.burst(calls)
        exports = [o for o in outs[9:]]
        for e in exports:
            self.assertEqual(e.status, 200)
            # every export imports cleanly (atomic snapshot -> valid, overlap-free state)
            self.assertEqual(Api(base_url(2)).call("POST", "/_test/import", e.json).status, 204)


class Transfer(Populated):
    def check_destination(self):
        d = self.dst
        r = d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json["user_id"], "u_ada")
        self.assertEqual(d.call("POST", "/auth/login", {"email": "new@example.com", "password": "pw-12345678"}).json["user_id"],
                         self.signup["user_id"])
        self.err(d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "nope"}), 401, "unauthenticated")

    def test_L089_L093_import_into_independent_service(self):
        self.populate()
        view_src = self.snapshot_view(self.api, self.t_ada, self.t_bob)
        exp = self.export()
        d = self.dst
        d.call("POST", "/_test/reset", {"users": [], "restaurants": [], "reservations": []})
        r = d.call("POST", "/_test/import", exp)
        self.assertEqual(r.status, 204, r)
        self.assertEqual(r.raw, b"")
        # existing bearer tokens (all sessions) still valid on destination
        view_dst = self.snapshot_view(d, self.t_ada, self.t_bob)
        self.assertEqual(view_dst, view_src)
        self.assertEqual(d.call("GET", "/reservations", token=self.t_ada2).status, 200)
        self.assertEqual(d.call("GET", "/reservations", token=self.signup["token"]).status, 200)
        self.check_destination()
        # identities, statuses, timestamps and references not regenerated
        got = {x["reference"]: x for x in d.call("GET", "/reservations", token=self.t_ada).json["reservations"]}
        self.assertEqual(got[self.cancelled["reference"]], self.cancelled)
        self.assertEqual(got[self.patched["reference"]], self.patched)
        # seeded fixture reservation survives
        self.assertEqual(d.call("GET", "/reservations/BOBSEED1", token=self.t_bob).json["reservation_id"], "res_s1")

    def test_L094_L111_receipts_survive_transfer(self):
        self.populate()
        exp = self.export()
        d = self.dst
        self.assertEqual(d.call("POST", "/_test/import", exp).status, 204)
        # replay create: 200, original body (even though the booking changed meanwhile)
        r = d.call("POST", "/reservations", self.create_body, token=self.t_ada, key=self.k1)
        self.assertEqual((r.status, r.json), (200, self.create_resp.json), r)
        # different body, same key -> 409
        r = d.call("POST", "/reservations", dict(self.create_body, party_size=1), token=self.t_ada, key=self.k1)
        self.err(r, 409, "idempotency_key_reuse")
        # batch replay
        r = d.call("POST", "/reservation-moves", self.moves_body, token=self.t_ada, key="xfer-moves-1")
        self.assertEqual((r.status, r.json), (200, self.moves_resp.json), r)
        self.err(d.call("POST", "/reservation-moves", {"moves": [self.moves_body["moves"][0]]}, token=self.t_ada,
                        key="xfer-moves-1"), 409, "idempotency_key_reuse")
        # failed key reusable on destination
        ok = d.call("POST", "/reservations", dict(self.create_body, table_id="t_1", party_size=1,
                                                   starts_at_local=f"{FRI}T20:00"), token=self.t_bob, key="xfer-failed")
        self.assertEqual(ok.status, 201, ok)
        # receipts keep their user scope
        other = d.call("POST", "/reservations", dict(self.create_body, table_id="t_1", party_size=1,
                                                      starts_at_local=f"{THU}T21:00"), token=self.t_bob, key=self.k1)
        self.assertEqual(other.status, 201, other)
        # occupancy preserved: patched booking still blocks its slot
        cur = self.patched                                  # B now sits on t_2 at 21:00
        blocked = dict(self.create_body, table_id=cur["table_id"], starts_at_local=cur["starts_at_local"])
        self.err(d.call("POST", "/reservations", blocked, token=self.t_bob, key="fresh-a"), 409, "table_unavailable")

    def test_L021_L093_short_password_accounts_survive_export_import(self):
        f = fixture()
        f["users"][0]["password"] = "abc"
        f["users"][1]["password"] = "x"
        self.reset(f)
        tok = self.api.call("POST", "/auth/login", {"email": "ada@example.com", "password": "abc"}).json["token"]
        exp = self.export()
        d = self.dst
        d.call("POST", "/_test/reset", {"users": [], "restaurants": [], "reservations": []})
        self.assertEqual(d.call("POST", "/_test/import", exp).status, 204)
        for email, pw in (("ada@example.com", "abc"), ("bob@example.com", "x")):
            r = d.call("POST", "/auth/login", {"email": email, "password": pw})
            self.assertEqual(r.status, 200, (email, r))
        self.err(d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "abcd"}), 401, "unauthenticated")
        self.assertEqual(d.call("GET", "/reservations", token=tok).status, 200)      # old token still valid
        self.assertNotIn('"abc"', json.dumps(exp["state"]).replace('\\"', ""), "plaintext short password in export")
        # and a second hop: export from the destination, import back into the source
        back = d.call("GET", "/_test/export").json
        self.reset()
        self.assertEqual(self.api.call("POST", "/_test/import", back).status, 204)
        self.assertEqual(self.api.call("POST", "/auth/login", {"email": "bob@example.com", "password": "x"}).status, 200)

    def test_L090_import_replaces_not_merges_and_repeats(self):
        self.populate()
        exp = self.export()
        d = self.dst
        d.call("POST", "/_test/reset", fixture(reservations=[seed_res(7, "u_ada", "r_anker", "t_1", f"{FRI}T20:00", 1, "DESTONLY")]))
        dest_tok = d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).json["token"]
        d.call("POST", "/auth/signup", {"email": "destonly@x.y", "password": "12345678", "display_name": "D"})
        for _ in range(3):
            self.assertEqual(d.call("POST", "/_test/import", exp).status, 204)
            refs = [x["reference"] for x in d.call("GET", "/reservations", token=self.t_ada).json["reservations"]]
            self.assertEqual(len(refs), len(set(refs)), refs)
            self.assertEqual(len(refs), 3)
            self.assertNotIn("DESTONLY", refs)
            self.assertEqual(len(d.call("GET", "/restaurants").json["restaurants"]), 6)
        # L095: previous destination accounts/tokens/data are gone
        self.err(d.call("GET", "/reservations", token=dest_tok), 401, "unauthenticated")
        self.err(d.call("POST", "/auth/login", {"email": "destonly@x.y", "password": "12345678"}), 401, "unauthenticated")
        self.err(d.call("GET", "/reservations/DESTONLY", token=self.t_ada), 404, "not_found")
        self.assertEqual(d.call("POST", "/auth/signup", {"email": "destonly@x.y", "password": "12345678",
                                                          "display_name": "D"}).status, 201)
        self.err(d.call("POST", "/auth/signup", {"email": "new@example.com", "password": "12345678",
                                                  "display_name": "D"}), 409, "email_taken")

    def test_L095_reset_clears_imported_state_on_destination(self):
        self.populate()
        d = self.dst
        d.call("POST", "/_test/import", self.export())
        self.assertEqual(d.call("POST", "/_test/reset", fixture()).status, 204)
        self.err(d.call("GET", "/reservations", token=self.t_ada), 401, "unauthenticated")
        self.err(d.call("POST", "/auth/login", {"email": "new@example.com", "password": "pw-12345678"}), 401,
                 "unauthenticated")
        r = d.call("POST", "/reservations", self.create_body, token=d.call("POST", "/auth/login", {
            "email": "ada@example.com", "password": "correct horse"}).json["token"], key=self.k1)
        self.assertEqual(r.status, 201)   # receipt gone -> first use

    def test_L088_L093_export_after_import_roundtrips(self):
        self.populate()
        exp = self.export()
        d = self.dst
        d.call("POST", "/_test/import", exp)
        exp2 = d.call("GET", "/_test/export").json
        self.reset()
        self.assertEqual(self.api.call("POST", "/_test/import", exp2).status, 204)
        self.assertEqual(self.api.call("GET", "/reservations", token=self.t_ada).status, 200)
        self.assertEqual(self.api.call("POST", "/reservation-moves", self.moves_body, token=self.t_ada,
                                       key="xfer-moves-1").status, 200)

    def test_L093_references_and_ids_unique_after_import(self):
        self.populate()
        d = self.dst
        d.call("POST", "/_test/import", self.export())
        old = {x["reference"] for x in d.call("GET", "/reservations", token=self.t_ada).json["reservations"]}
        old_ids = {x["reservation_id"] for x in d.call("GET", "/reservations", token=self.t_ada).json["reservations"]}
        new = []
        for i in range(5):
            new.append(self.book_on(d, self.t_ada, f"2030-02-0{i + 5}T19:00", i))
        for n in new:
            self.assertNotIn(n["reference"], old)
            self.assertNotIn(n["reservation_id"], old_ids)
        self.assertEqual(len({n["reference"] for n in new}), 5)

    def book_on(self, api, token, local, i):
        r = api.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_2",
                                               "starts_at_local": local, "party_size": 2}, token=token, key=f"post-{i}")
        self.assertEqual(r.status, 201, r)
        return r.json

    def test_L089_import_target_not_dependent_on_source_after_source_dies_or_resets(self):
        self.populate()
        exp = self.export()
        self.reset(fixture())          # source wiped completely
        d = self.dst
        self.assertEqual(d.call("POST", "/_test/import", exp).status, 204)
        self.assertEqual(len(d.call("GET", "/reservations", token=self.t_ada).json["reservations"]), 3)

    def test_L102_receipt_users_scoped_after_import(self):
        self.populate()
        d = self.dst
        d.call("POST", "/_test/import", self.export())
        # bob's replay of bob's own receipt
        r = d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_1", "starts_at_local": f"{THU}T19:00",
                                              "party_size": 2}, token=self.t_bob, key="xfer-bob-1")
        self.assertEqual((r.status, r.json), (200, self.bobs), r)


class ImportValidation(Populated):
    def setUp(self):
        super().setUp()
        self.populate()
        self.exp = self.export()
        self.dst.call("POST", "/_test/reset", fixture(reservations=[seed_res(9, "u_ada", "r_anker", "t_2", f"{THU}T20:00", 2, "KEEPME1")]))
        self.dest_token = self.dst.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).json["token"]
        self.before = self.dst.call("GET", "/_test/export").json

    def assert_dest_unchanged(self, what=""):
        self.assertEqual(self.dst.call("GET", "/_test/export").json, self.before, what)
        self.assertEqual(self.dst.call("GET", "/reservations/KEEPME1", token=self.dest_token).status, 200, what)

    def imp(self, payload=None, raw=None):
        return self.dst.call("POST", "/_test/import", payload, raw=raw)

    def test_L091_invalid_json(self):
        for raw in ("{bad", "", "[1]", "7", '"x"', "null"):
            self.err(self.imp(raw=raw), 400, "malformed_request")
        self.assert_dest_unchanged()

    def test_L091_missing_or_wrong_envelope(self):
        e = self.exp
        cases = [{}, {"track": "tablekeeper"}, {"format_version": 1}, {"state": e["state"]},
                 {"track": "tablekeeper", "format_version": 1},
                 {"track": "tablekeeper", "format_version": 1, "state": None},
                 {"track": "tablekeeper", "format_version": 1, "state": []},
                 {"track": "tablekeeper", "format_version": 1, "state": "x"},
                 {"track": "tablekeeper", "format_version": 1, "state": {}},
                 dict(e, format_version=2), dict(e, format_version=0), dict(e, format_version="1"),
                 dict(e, format_version=True), dict(e, format_version=1.5), dict(e, format_version=None),
                 dict(e, track="other"), dict(e, track=""), dict(e, track=None), dict(e, track=["tablekeeper"]),
                 dict(e, track="TABLEKEEPER")]
        for c in cases:
            r = self.imp(c)
            self.err(r, 422, "validation_failed")
            self.assert_dest_unchanged(str(c)[:80])

    def test_L092_other_track_export(self):
        for track, state in (("pocketful", {"accounts": []}), ("toy", {}), ("pocketful", self.exp["state"])):
            r = self.imp({"track": track, "format_version": 1, "state": state})
            self.err(r, 422, "validation_failed")
        self.assert_dest_unchanged()

    def test_L091_extra_envelope_fields_ignored(self):
        r = self.imp(dict(self.exp, junk=1))
        self.assertEqual(r.status, 204, r)

    def test_L096_fuzz_state_never_5xx_and_atomic(self):
        """Mutate each leaf (delete, wrong type, nonsense). Rejected imports must be 422 and change nothing;
        accepted ones may only happen if the result is still a valid state (checked by re-export import)."""
        paths = [p for p, n in walk(self.exp["state"]) if p]
        if len(paths) > 260:
            step = len(paths) / 260
            paths = [paths[int(i * step)] for i in range(260)]
        rejected = 0
        for p in paths:
            for kind in ("delete", "wrongtype", "bigint"):
                st = copy.deepcopy(self.exp["state"])
                parent = get_at(st, p[:-1])
                if kind == "delete":
                    if isinstance(parent, dict):
                        del parent[p[-1]]
                    else:
                        parent.pop(p[-1])
                elif kind == "wrongtype":
                    cur = parent[p[-1]]
                    parent[p[-1]] = {"x": 1} if isinstance(cur, (str, int, float, bool)) else "oops"
                else:
                    cur = parent[p[-1]]
                    if isinstance(cur, bool) or not isinstance(cur, (int, str)):
                        continue
                    parent[p[-1]] = -999999999999 if isinstance(cur, int) else cur + "\u0000" * 70
                r = self.imp({"track": "tablekeeper", "format_version": 1, "state": st})
                self.assertLess(r.status, 500, (p, kind, r))
                if r.status != 204:
                    rejected += 1
                    self.err(r, 422, "validation_failed")
                    self.assert_dest_unchanged(f"{p} {kind}")
                else:
                    # accepted: restore known-good baseline for next iteration
                    self.dst.call("POST", "/_test/reset", fixture(reservations=[seed_res(9, "u_ada", "r_anker", "t_2",
                                                                                         f"{THU}T20:00", 2, "KEEPME1")]))
                    self.dest_token = self.dst.call("POST", "/auth/login", {"email": "ada@example.com",
                                                                            "password": "correct horse"}).json["token"]
                    self.before = self.dst.call("GET", "/_test/export").json
        self.assertGreater(rejected, 20, "state validation appears to accept almost any corruption")

    def clone_record(self, anchor, rewrite):
        """Duplicate the record holding `anchor`, applying rewrite(old_string)->new_string on its values."""
        st = copy.deepcopy(self.exp["state"])
        for path in record_nodes(st, anchor):
            node = get_at(st, path)
            if not path:
                continue
            parent = get_at(st, path[:-1])
            clone = json.loads(json.dumps(node))
            clone = rewrite(clone)
            if isinstance(parent, list):
                parent.append(clone)
                return st
            if isinstance(parent, dict):
                key = f"dup-{path[-1]}"
                parent[key] = clone
                return st
        self.skipTest(f"anchor {anchor!r} not visible in opaque state")

    def test_L100_duplicate_reservation_identity(self):
        ref = self.patched["reference"]
        st = self.clone_record(ref, lambda c: c)
        self.err(self.imp({"track": "tablekeeper", "format_version": 1, "state": st}), 422, "validation_failed")
        self.assert_dest_unchanged()

    def test_L100_L096_overlapping_confirmed_in_import(self):
        ref, rid = self.patched["reference"], self.patched["reservation_id"]
        st = self.clone_record(ref, lambda c: replace_value(replace_value(c, ref, "DUPREF77"), rid, "res_dup_77"))
        self.err(self.imp({"track": "tablekeeper", "format_version": 1, "state": st}), 422, "validation_failed")
        self.assert_dest_unchanged()

    def test_L097_duplicate_email_and_id(self):
        uid = "u_ada"
        st = self.clone_record("ada@example.com", lambda c: replace_value(c, uid, "u_clone"))
        self.err(self.imp({"track": "tablekeeper", "format_version": 1, "state": st}), 422, "validation_failed")
        st = self.clone_record("ada@example.com", lambda c: replace_value(c, "ada@example.com", "clone@example.com"))
        self.err(self.imp({"track": "tablekeeper", "format_version": 1, "state": st}), 422, "validation_failed")
        self.assert_dest_unchanged()

    def test_L098_duplicate_restaurant_id(self):
        st = self.clone_record("r_other", lambda c: replace_value(c, "Other", "Dup"))
        self.err(self.imp({"track": "tablekeeper", "format_version": 1, "state": st}), 422, "validation_failed")
        self.assert_dest_unchanged()

    def test_L099_duplicate_table_in_restaurant_rejected_but_repeat_across_restaurants_ok(self):
        # r_anker/t_1 and r_other/t_1 coexist in the export and are accepted
        self.assertEqual(self.imp(self.exp).status, 204)
        st = copy.deepcopy(self.exp["state"])
        hits = [p for p, n in walk(st) if isinstance(n, dict) and n.get("id") == "t_2" and "capacity" in n]
        self.assertTrue(hits, "table record not found in opaque state")
        p = hits[0]
        parent = get_at(st, p[:-1])
        if isinstance(parent, list):
            parent.append(copy.deepcopy(get_at(st, p)))
            r = self.imp({"track": "tablekeeper", "format_version": 1, "state": st})
            self.err(r, 422, "validation_failed")

    @staticmethod
    def retarget(st, paths):
        st = copy.deepcopy(st)
        for p in paths:
            n = get_at(st, p)
            sub = lambda x: x.replace("u_bob", "u_missing_zz") if isinstance(x, str) else x
            new = {sub(k): sub(v) for k, v in n.items()}
            if p:
                set_at(st, p, new)
            else:
                st = new
        return st

    def test_L101_token_for_missing_user(self):
        tok = self.t_bob
        st = copy.deepcopy(self.exp["state"])
        paths = record_nodes(st, tok)
        if not paths:
            self.skipTest("token not visible in opaque state (stored hashed)")
        st = self.retarget(st, paths)
        r = self.imp({"track": "tablekeeper", "format_version": 1, "state": st})
        self.err(r, 422, "validation_failed")
        self.assert_dest_unchanged()

    def test_L102_receipt_for_missing_user(self):
        key = "xfer-bob-1"
        st = copy.deepcopy(self.exp["state"])
        paths = record_nodes(st, key)
        if not paths:
            self.skipTest("idempotency key not visible in opaque state")
        st2 = self.retarget(st, paths)
        if st2 == st:
            self.skipTest("receipt user link not discoverable")
        st = st2
        self.err(self.imp({"track": "tablekeeper", "format_version": 1, "state": st}), 422, "validation_failed")
        self.assert_dest_unchanged()

    def test_L096_reset_uses_same_booking_validation(self):
        def rej(f):
            r = self.api.call("POST", "/_test/reset", f)
            self.err(r, 422, "validation_failed")
            # untouched
            self.assertEqual(self.api.call("GET", "/restaurants").status, 200)
        good = seed_res(1, "u_ada", "r_anker", "t_2", f"{THU}T19:00", 2, "AAAAAA")
        # overlapping confirmed
        rej(fixture(reservations=[good, seed_res(2, "u_bob", "r_anker", "t_2", f"{THU}T20:00", 2, "BBBBBB")]))
        # same instant, same table id, different restaurant is fine
        ok = fixture(reservations=[good, seed_res(2, "u_bob", "r_other", "t_1", f"{THU}T19:00", 2, "BBBBBB")])
        self.assertEqual(self.api.call("POST", "/_test/reset", ok).status, 204)
        # adjacent is fine
        ok = fixture(reservations=[good, seed_res(2, "u_bob", "r_anker", "t_2", f"{THU}T20:30", 2, "BBBBBB")])
        self.assertEqual(self.api.call("POST", "/_test/reset", ok).status, 204)
        # field validity
        for mut in (lambda r: r.update(party_size=0), lambda r: r.update(party_size=True), lambda r: r.update(party_size="2"),
                    lambda r: r.update(party_size=5), lambda r: r.update(starts_at_local=f"{THU}T19:15"),
                    lambda r: r.update(starts_at_local=f"{THU}T19:00:00"), lambda r: r.update(starts_at_local=f"{THU}T23:30"),
                    lambda r: r.update(starts_at_local="2030-03-31T02:30"),
                    lambda r: r.update(table_id="zzz"), lambda r: r.update(restaurant_id="zzz"),
                    lambda r: r.update(user_id="u_nobody"), lambda r: r.update(reference="abc"),
                    lambda r: r.update(reference="TOOLONGREFERENCE1"), lambda r: r.update(reference="lower1"),
                    lambda r: r.update(reference=""), lambda r: r.update(id=""), lambda r: r.update(id="x" * 65),
                    lambda r: r.update(table_id="t_9")):
            r = seed_res(1, "u_ada", "r_anker", "t_2", f"{THU}T19:00", 2, "AAAAAA")
            mut(r)
            if r["starts_at_local"] == "2030-03-31T02:30":
                continue
            rej(fixture(reservations=[r]))
        # duplicates
        rej(fixture(reservations=[good, seed_res(1, "u_bob", "r_anker", "t_3", f"{THU}T19:00", 2, "BBBBBB")]))
        rej(fixture(reservations=[good, seed_res(2, "u_bob", "r_anker", "t_3", f"{THU}T19:00", 2, "AAAAAA")]))
        self.reset()

    def test_L097_L098_L099_fixture_duplicates(self):
        def rej(f):
            self.err(self.api.call("POST", "/_test/reset", f), 422, "validation_failed")
        f = fixture(); f["users"][1]["email"] = "ada@example.com"; rej(f)
        f = fixture(); f["users"][1]["id"] = "u_ada"; rej(f)
        for fld, v in (("email", 5), ("password", None), ("display_name", 3), ("id", 7), ("email", "noat")):
            f = fixture(); f["users"][0][fld] = v; rej(f)
        f = fixture(); f["restaurants"][1]["id"] = "r_anker"; rej(f)
        f = fixture(); f["restaurants"][0]["tables"][1]["id"] = "t_1"; rej(f)
        f = fixture(); f["restaurants"][0]["tables"].append({"id": "t_1", "label": "dup", "capacity": 2}); rej(f)
        f = fixture(); f["restaurants"][1]["tables"][0]["id"] = "t_1"        # same as r_anker/t_1: allowed
        self.assertEqual(self.api.call("POST", "/_test/reset", f).status, 204)
        for key in ("users", "restaurants", "reservations"):
            f = fixture(); del f[key]; rej(f)
        f = fixture(); f["users"] = {}; rej(f)
        self.reset()
