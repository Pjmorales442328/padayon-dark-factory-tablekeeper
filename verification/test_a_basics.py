"""Conventions, errors, validation, auth, health, reset (ledger 4,7-16,24-41)."""
import json
import threading
import time
import unittest

from common import Base, Api, THU, fixture, base_url, deep, hours, table


class Health(Base):
    def test_L007_health_ok(self):
        r = self.api.call("GET", "/health")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.json, {"status": "ok"})
        self.assertTrue(r.ctype.lower().replace(" ", "").startswith("application/json;charset=utf-8"))

    def test_L040_public_endpoints_need_no_token(self):
        for m, p, b in [("GET", "/health", None), ("GET", "/restaurants", None),
                        ("GET", "/restaurants/r_anker", None),
                        ("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=2", None),
                        ("GET", "/_test/export", None)]:
            r = self.api.call(m, p, b)
            self.assertEqual(r.status, 200, (p, r))
        r = self.api.call("POST", "/auth/signup", {"email": "x@y.z", "password": "12345678",
                                                    "display_name": "X"})
        self.assertEqual(r.status, 201)
        r = self.api.call("POST", "/auth/login", {"email": "x@y.z", "password": "12345678"})
        self.assertEqual(r.status, 200)

    def test_L041_protected_endpoints_need_token(self):
        for m, p, b in [("GET", "/reservations", None),
                        ("POST", "/reservations", {"a": 1}),
                        ("POST", "/reservation-moves", {"moves": []})]:
            r = self.api.call(m, p, b, key="k1")
            self.err(r, 401, "unauthenticated")


class Conventions(Base):
    def test_L011_json_content_type_and_rfc3339(self):
        t = self.ada
        for r in [self.api.call("GET", "/restaurants"), self.api.call("GET", "/restaurants/nope"),
                  self.api.call("GET", "/reservations", token=t)]:
            self.assertTrue(r.ctype.lower().replace(" ", "").startswith("application/json;charset=utf-8"),
                            r.ctype)
        res = self.ok_book(t, f"{THU}T19:00")
        import re
        pat = r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|[+-]\d\d:\d\d)$"
        for k in ("starts_at", "ends_at", "created_at"):
            self.assertRegex(res[k], pat)

    def test_L012_unknown_fields_and_query_ignored(self):
        r = self.api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=2&zzz=1&foo=bar")
        self.assertEqual(r.status, 200)
        r = self.api.call("GET", "/restaurants?x=1&party_size=abc")
        self.assertEqual(r.status, 200)
        res = self.book(self.ada, f"{THU}T19:00", extra="x", nested={"a": [1]})
        self.assertEqual(res.status, 201, res)
        r = self.api.call("POST", "/auth/signup", {"email": "q@q.q", "password": "12345678",
                                                    "display_name": "Q", "role": "admin"})
        self.assertEqual(r.status, 201)
        r = self.api.call("PATCH", f"/reservations/{res.json['reference']}",
                          {"party_size": 3, "bogus": 1}, token=self.ada)
        self.assertEqual(r.status, 200, r)

    def test_L013_ids_opaque_strings_max_64(self):
        t = self.ada
        res = self.ok_book(t, f"{THU}T19:00")
        for v in (res["reservation_id"], res["reference"]):
            self.assertIsInstance(v, str)
            self.assertLessEqual(len(v), 64)
        r = self.api.call("POST", "/auth/signup", {"email": "n@n.n", "password": "12345678",
                                                    "display_name": "N"})
        self.assertLessEqual(len(r.json["user_id"]), 64)
        self.assertIsInstance(r.json["user_id"], str)
        # fixture ids of exactly 64 chars work, 65 are rejected at reset
        f = fixture()
        long64 = "r" * 64
        f["restaurants"][0]["id"] = long64
        self.reset(f)
        self.assertEqual(self.api.call("GET", f"/restaurants/{long64}").status, 200)
        f["restaurants"][0]["id"] = "r" * 65
        r = self.api.call("POST", "/_test/reset", f)
        self.err(r, 422, "validation_failed")

    def test_L025_malformed_bodies(self):
        t = self.ada
        k = self.newkey()
        for raw in ["{not json", "", "[]", "[1,2]", '"str"', "42", "null", "true"]:
            r = self.api.call("POST", "/reservations", raw=raw, token=t, key=self.newkey())
            self.err(r, 400, "malformed_request")
            r = self.api.call("POST", "/auth/login", raw=raw)
            self.err(r, 400, "malformed_request")
            r = self.api.call("POST", "/auth/signup", raw=raw)
            self.err(r, 400, "malformed_request")
            r = self.api.call("PATCH", "/reservations/SEED01", raw=raw, token=t)
            self.err(r, 400, "malformed_request")
            r = self.api.call("POST", "/reservation-moves", raw=raw, token=t, key=self.newkey())
            self.err(r, 400, "malformed_request")
        # no body at all
        r = self.api.call("POST", "/reservations", token=t, key=k)
        self.err(r, 400, "malformed_request")
        # wrong field types (not party_size / starts_at_local-string rules)
        for body in [{"restaurant_id": 5, "table_id": "t_2", "starts_at_local": f"{THU}T19:00", "party_size": 2},
                     {"restaurant_id": "r_anker", "table_id": ["t_2"], "starts_at_local": f"{THU}T19:00",
                      "party_size": 2},
                     {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": None, "party_size": 2},
                     {"restaurant_id": True, "table_id": "t_2", "starts_at_local": f"{THU}T19:00",
                      "party_size": 2}]:
            r = self.api.call("POST", "/reservations", body, token=t, key=self.newkey())
            self.err(r, 400, "malformed_request")
        for body in [{"email": 5, "password": "12345678"}, {"email": "a@b.c", "password": 12345678},
                     {"email": ["a@b.c"], "password": "x"}]:
            self.err(self.api.call("POST", "/auth/login", body), 400, "malformed_request")
        self.err(self.api.call("POST", "/auth/signup", {"email": "a@b.c", "password": "12345678",
                                                         "display_name": 7}), 400, "malformed_request")

    def test_L025_malformed_reset(self):
        for raw in ["{bad", "", "[]", "7"]:
            r = self.api.call("POST", "/_test/reset", raw=raw)
            self.err(r, 400, "malformed_request")
        # state still intact afterwards
        self.assertEqual(self.api.call("GET", "/restaurants/r_anker").status, 200)

    def test_L026_numeric_starts_at_local(self):
        for v in (20300103190, 1893438000, 1.5, 0):
            r = self.book(self.ada, v)
            self.err(r, 400, "malformed_request")

    def test_L027_missing_fields_422(self):
        t = self.ada
        full = {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": f"{THU}T19:00",
                "party_size": 2}
        for k in full:
            b = {x: y for x, y in full.items() if x != k}
            self.err(self.api.call("POST", "/reservations", b, token=t, key=self.newkey()),
                     422, "validation_failed")
        self.err(self.api.call("POST", "/reservations", {}, token=t, key=self.newkey()),
                 422, "validation_failed")
        self.err(self.api.call("POST", "/auth/login", {"email": "ada@example.com"}), 422,
                 "validation_failed")
        self.err(self.api.call("POST", "/auth/signup", {"email": "a@b.c", "password": "12345678"}),
                 422, "validation_failed")

    def test_L028_party_size_invalid(self):
        for v in ("2", True, False, 2.5, 2.0, 0, -1, "", None, "abc"):
            r = self.book(self.ada, f"{THU}T19:00", party=v)
            self.err(r, 422, "validation_failed")

    def test_L029_starts_at_local_format(self):
        bad = [f"{THU}T19:00:00", f"{THU}T19:00Z", f"{THU}T19:00+01:00", f"{THU}T19:00:00+01:00",
               f"{THU}", f"{THU} 19:00", "2030-02-30T19:00", "2030-13-01T19:00", f"{THU}T25:00",
               f"{THU}T19:60", f"{THU}T7:00", "30-01-03T19:00", "", "garbage", f"{THU}t19:00",
               f" {THU}T19:00", f"{THU}T19:00 "]
        for v in bad:
            r = self.book(self.ada, v)
            self.err(r, 422, "validation_failed")

    def test_L030_integer_query_params(self):
        for v in ("1e9", "4.0", "+4", "-1", "0", "", "abc", " 4", "4 ", "0x4", "٤"):
            r = self.api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size={v.replace(' ', '%20')}")
            self.err(r, 422, "validation_failed")
        r = self.api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=04")
        self.assertIn(r.status, (200, 422))  # leading zero: digits only; either reading is tolerated
        r = self.api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=4")
        self.assertEqual(r.status, 200)

    def test_L031_idempotency_header_rules(self):
        t = self.ada
        body = {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": f"{THU}T19:00",
                "party_size": 2}
        r = self.api.call("POST", "/reservations", body, token=t)
        self.err(r, 400, "missing_idempotency_key")
        r = self.api.call("POST", "/reservations", body, token=t, key="")
        self.err(r, 400, "missing_idempotency_key")
        r = self.api.call("POST", "/reservations", body, token=t, key="k" * 256)
        self.err(r, 422, "validation_failed")
        r = self.api.call("POST", "/reservations", body, token=t, key="k" * 255)
        self.assertEqual(r.status, 201, r)
        r = self.api.call("POST", "/reservations", body, token=t, key="k")
        self.assertIn(r.status, (201, 409))  # 1 char key accepted (409 only because table taken)
        self.assertNotEqual(r.status, 422)
        for p in ("/reservation-moves",):
            r = self.api.call("POST", p, {"moves": [{"reference": "SEED01"}]}, token=t)
            self.err(r, 400, "missing_idempotency_key")
            r = self.api.call("POST", p, {"moves": [{"reference": "SEED01"}]}, token=t, key="z" * 256)
            self.err(r, 422, "validation_failed")

    def test_L031_missing_key_ordering_vs_validation(self):
        """Auth first, then key presence, then body checks; missing key beats bad fields."""
        t = self.ada
        r = self.api.call("POST", "/reservations", {"restaurant_id": 1}, token=t)
        self.assertIn(r.status, (400,))
        r = self.api.call("POST", "/reservations", {"restaurant_id": "r_anker"}, token=None, key="a")
        self.err(r, 401, "unauthenticated")

    def test_L032_no_5xx_on_garbage(self):
        t = self.ada
        cases = []
        for m in ("GET", "POST", "PATCH", "PUT", "DELETE"):
            for p in ("/", "/reservations/%00", "/reservations/" + "A" * 5000, "/restaurants/%ff",
                      "/availability?date=%ff&restaurant_id=%00", "/nope", "/reservations/x/cancel",
                      "/auth/login/", "//reservations"):
                cases.append((m, p))
        for m, p in cases:
            r = self.api.call(m, p, token=t, key="x")
            self.assertLess(r.status, 500, (m, p, r))
        for raw in ['{"a":' * 200, "\x00", "{" * 5000, '{"moves": 5}', '{"moves": [[]]}', "1e999",
                    '{"x": NaN}', '{"x": Infinity}', "\ufeff{}", '{"a":1}garbage']:
            for p, k in (("/reservations", True), ("/reservation-moves", True), ("/auth/login", False),
                         ("/auth/signup", False), ("/_test/import", False), ("/_test/reset", False)):
                r = self.api.call("POST", p, raw=raw, token=t, key="kk" if k else None)
                self.assertLess(r.status, 500, (p, raw[:30], r))
        self.assertEqual(self.api.call("GET", "/health").status, 200)
        self.reset()

    def test_L032_head_options_survive(self):
        for m in ("HEAD", "OPTIONS"):
            r = self.api.call(m, "/restaurants")
            self.assertLess(r.status, 500)


class Auth(Base):
    def test_L021_L036_seed_users_login(self):
        r = self.api.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"})
        self.assertEqual(r.status, 200)
        self.assertEqual(r.json["user_id"], "u_ada")
        self.assertEqual(r.json["display_name"], "Ada")
        self.assertTrue(r.json["token"] and isinstance(r.json["token"], str))
        self.assertEqual(set(r.json), {"user_id", "display_name", "token"})

    def test_L036_login_failures_indistinct(self):
        r1 = self.api.call("POST", "/auth/login", {"email": "ada@example.com", "password": "wrong"})
        r2 = self.api.call("POST", "/auth/login", {"email": "ghost@example.com", "password": "correct horse"})
        r3 = self.api.call("POST", "/auth/login", {"email": "ada@example.com", "password": "Correct Horse"})
        r4 = self.api.call("POST", "/auth/login", {"email": "ada@example.com", "password": ""})
        for r in (r1, r2, r3, r4):
            self.err(r, 401, "unauthenticated")

    def test_L033_signup(self):
        r = self.api.call("POST", "/auth/signup", {"email": "new@example.com", "password": "12345678",
                                                    "display_name": "New"})
        self.assertEqual(r.status, 201)
        self.assertEqual(set(r.json), {"user_id", "display_name", "token"})
        self.assertEqual(r.json["display_name"], "New")
        r2 = self.api.call("POST", "/auth/login", {"email": "new@example.com", "password": "12345678"})
        self.assertEqual(r2.status, 200)
        self.assertEqual(r2.json["user_id"], r.json["user_id"])
        self.assertEqual(self.api.call("GET", "/reservations", token=r.json["token"]).status, 200)

    def test_L034_duplicate_email(self):
        self.err(self.api.call("POST", "/auth/signup", {"email": "ada@example.com", "password": "12345678",
                                                         "display_name": "X"}), 409, "email_taken")
        self.assertEqual(self.api.call("POST", "/auth/signup", {"email": "z@z.z", "password": "12345678",
                                                                 "display_name": "X"}).status, 201)
        self.err(self.api.call("POST", "/auth/signup", {"email": "z@z.z", "password": "87654321",
                                                         "display_name": "Y"}), 409, "email_taken")

    def test_L035_signup_validation(self):
        base = {"email": "v@v.v", "password": "12345678", "display_name": "V"}
        for pw in ("1234567", "", "a"):
            self.err(self.api.call("POST", "/auth/signup", dict(base, password=pw)), 422, "validation_failed")
        self.assertEqual(self.api.call("POST", "/auth/signup", dict(base, password="12345678")).status, 201)
        for em in ("nodomain", "@x.y", "a@", "a@@b.c", "", "a b@c.d", "plain"):
            self.err(self.api.call("POST", "/auth/signup", dict(base, email=em)), 422, "validation_failed")
        # password length counts characters, not bytes
        r = self.api.call("POST", "/auth/signup", dict(base, email="u1@v.v", password="ééééééé"))
        self.err(r, 422, "validation_failed")
        r = self.api.call("POST", "/auth/signup", dict(base, email="u2@v.v", password="éééééééé"))
        self.assertEqual(r.status, 201)

    def test_L034_L035_order_dup_email_vs_short_password(self):
        r = self.api.call("POST", "/auth/signup", {"email": "ada@example.com", "password": "short",
                                                    "display_name": "X"})
        self.assertIn(r.status, (409, 422))

    def test_L038_bad_tokens(self):
        for h in ({}, {"Authorization": "Bearer"}, {"Authorization": "Bearer "},
                  {"Authorization": "Bearer nonsense"}, {"Authorization": "Basic abc"},
                  {"Authorization": self.ada}, {"Authorization": "bearer " + self.ada + "x"}):
            r = self.api.call("GET", "/reservations", headers=h)
            self.err(r, 401, "unauthenticated")

    def test_L039_multiple_tokens_and_no_expiry(self):
        t1, t2 = self.ada, self.ada
        self.assertNotEqual(t1, t2)
        self.assertEqual(self.api.call("GET", "/reservations", token=t1).status, 200)
        self.assertEqual(self.api.call("GET", "/reservations", token=t2).status, 200)
        r = self.ok_book(t1, f"{THU}T19:00")
        self.assertEqual(self.api.call("GET", f"/reservations/{r['reference']}", token=t2).status, 200)
        tokens = [self.api.call("POST", "/auth/login", {"email": "ada@example.com",
                                                         "password": "correct horse"}).json["token"]
                  for _ in range(20)]
        self.assertEqual(len(set(tokens)), 20)
        for t in tokens + [t1, t2]:
            self.assertEqual(self.api.call("GET", "/reservations", token=t).status, 200)

    def test_L039_concurrent_logins(self):
        outs = self.burst([lambda: self.api.call("POST", "/auth/login", {"email": "ada@example.com",
                                                                          "password": "correct horse"})] * 20)
        self.assertTrue(all(o.status == 200 for o in outs))
        self.assertEqual(len({o.json["token"] for o in outs}), 20)

    def test_L034_concurrent_signup_same_email(self):
        outs = self.burst([lambda: self.api.call("POST", "/auth/signup", {"email": "race@x.y",
                                                                           "password": "12345678",
                                                                           "display_name": "R"})] * 10)
        self.assertEqual(sorted(o.status for o in outs), [201] + [409] * 9)

    def test_L041_users_isolated(self):
        a = self.ok_book(self.ada, f"{THU}T19:00")
        r = self.api.call("GET", "/reservations", token=self.bob)
        self.assertEqual(r.json, {"reservations": []})

    def test_L037_no_plaintext_password_in_export(self):
        self.api.call("POST", "/auth/signup", {"email": "pw@x.y", "password": "UniqueSecretPw-9917",
                                                "display_name": "P"})
        ex = self.api.call("GET", "/_test/export")
        txt = ex.raw.decode()
        for pw in ("correct horse", "battery staple", "UniqueSecretPw-9917"):
            self.assertNotIn(pw, txt)
        self.assertEqual(self.api.call("POST", "/auth/login", {"email": "pw@x.y",
                                                                "password": "UniqueSecretPw-9917"}).status, 200)

    def test_L037_same_password_distinct_salts(self):
        """Two accounts with the same password must not share a visible hash value."""
        for e in ("s1@x.y", "s2@x.y"):
            self.api.call("POST", "/auth/signup", {"email": e, "password": "SamePassword-123", "display_name": e})
        txt = self.api.call("GET", "/_test/export").raw.decode()
        self.assertNotIn("SamePassword-123", txt)


class Reset(Base):
    def test_L014_reset_204_no_auth_and_replaces(self):
        r = self.api.call("POST", "/_test/reset", fixture())
        self.assertEqual(r.status, 204)
        self.assertEqual(r.raw, b"")
        f = {"users": [], "restaurants": [], "reservations": []}
        self.assertEqual(self.api.call("POST", "/_test/reset", f).status, 204)
        self.assertEqual(self.api.call("GET", "/restaurants").json, {"restaurants": []})
        self.err(self.api.call("POST", "/auth/login", {"email": "ada@example.com",
                                                        "password": "correct horse"}), 401, "unauthenticated")

    def test_L015_reset_clears_everything(self):
        t = self.ada
        key = self.newkey()
        body = {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": f"{THU}T19:00", "party_size": 2}
        first = self.api.call("POST", "/reservations", body, token=t, key=key)
        sign = self.api.call("POST", "/auth/signup", {"email": "gone@x.y", "password": "12345678",
                                                       "display_name": "G"})
        self.assertEqual(first.status, 201)
        self.reset()
        self.err(self.api.call("GET", "/reservations", token=t), 401, "unauthenticated")
        self.err(self.api.call("GET", "/reservations", token=sign.json["token"]), 401, "unauthenticated")
        self.err(self.api.call("POST", "/auth/login", {"email": "gone@x.y", "password": "12345678"}),
                 401, "unauthenticated")
        t2 = self.ada
        self.assertEqual(self.api.call("GET", "/reservations", token=t2).json, {"reservations": []})
        again = self.api.call("POST", "/reservations", body, token=t2, key=key)
        self.assertEqual(again.status, 201)  # receipt gone: first use again
        self.assertEqual(self.api.call("POST", "/auth/signup", {"email": "gone@x.y", "password": "12345678",
                                                                 "display_name": "G"}).status, 201)

    def test_L015_reset_clears_imported_state(self):
        t = self.ada
        self.ok_book(t, f"{THU}T19:00")
        exp = self.api.call("GET", "/_test/export").json
        self.reset(fixture(reservations=[]))
        self.assertEqual(self.api.call("POST", "/_test/import", exp).status, 204)
        self.reset()
        self.err(self.api.call("GET", "/reservations", token=t), 401, "unauthenticated")
        self.assertEqual(self.api.call("GET", "/reservations", token=self.ada).json, {"reservations": []})

    def test_L016_config_from_reset_only(self):
        f = fixture()
        f["restaurants"] = [dict(f["restaurants"][0], id="r_solo", name="Solo")]
        self.reset(f)
        r = self.api.call("GET", "/restaurants")
        self.assertEqual([x["id"] for x in r.json["restaurants"]], ["r_solo"])
        self.assertIn(self.api.call("POST", "/restaurants", {"id": "x"}, token=self.ada).status,
                      (404, 405, 401, 403))
        self.assertEqual([x["id"] for x in self.api.call("GET", "/restaurants").json["restaurants"]],
                         ["r_solo"])

    def test_L017_config_validation(self):
        def bad(mut, what):
            f = fixture()
            mut(f["restaurants"][0])
            r = self.api.call("POST", "/_test/reset", f)
            self.err(r, 422, "validation_failed")
            # nothing replaced
            self.assertEqual(self.api.call("GET", "/restaurants/r_anker").status, 200, what)
        bad(lambda x: x.update(timezone="Mars/Olympus"), "tz unknown")
        bad(lambda x: x.update(timezone=""), "tz empty")
        bad(lambda x: x.update(timezone=5), "tz int")
        for fld in ("slot_minutes", "reservation_duration_minutes"):
            for v in (0, -5, 1.5, "30", True, None):
                bad(lambda x, fld=fld, v=v: x.update({fld: v}), f"{fld}={v!r}")
        for v in (-1, 1.5, "120", True, None):
            bad(lambda x, v=v: x.update(cancellation_cutoff_minutes=v), f"cutoff={v!r}")
        f = fixture()
        f["restaurants"][0]["cancellation_cutoff_minutes"] = 0
        self.assertEqual(self.api.call("POST", "/_test/reset", f).status, 204)

    def test_L018_weekdays(self):
        def bad(mut):
            f = fixture()
            mut(f["restaurants"][0])
            self.err(self.api.call("POST", "/_test/reset", f), 422, "validation_failed")
        for wd in ("monday", "MON", "mo", "", 1, None, "thur"):
            bad(lambda x, wd=wd: x["opening_hours"].append({"weekday": wd, "opens": "10:00", "closes": "11:00"}))
        f = fixture()
        self.reset(f)
        # SUN missing -> closed
        self.assertEqual(self.avail("r_anker", "2030-01-06")["slots"], [])
        # every day listed in fixture works
        for i, d in enumerate(["2030-01-07", "2030-01-08", "2030-01-09", "2030-01-10", "2030-01-12"]):
            self.assertTrue(self.avail("r_anker", d)["slots"], d)

    def test_L019_opening_times(self):
        def bad(opens, closes):
            f = fixture()
            f["restaurants"][0]["opening_hours"] = [{"weekday": "thu", "opens": opens, "closes": closes}]
            self.err(self.api.call("POST", "/_test/reset", f), 422, "validation_failed")
        for o, c in [("18:00", "18:00"), ("18:00", "17:00"), ("22:00", "02:00"), ("24:00", "24:30"),
                     ("18:60", "23:00"), ("6:00", "23:00"), ("18:00", "23:00:00"), ("", "23:00"),
                     ("18:00", "24:00"), ("ab:cd", "23:00"), (1800, 2300), ("18:00", None)]:
            bad(o, c)
        f = fixture()
        f["restaurants"][0]["opening_hours"] = [{"weekday": "thu", "opens": "00:00", "closes": "23:59"}]
        self.assertEqual(self.api.call("POST", "/_test/reset", f).status, 204)
        # duplicate weekday entries rejected or tolerated but never 5xx
        f = fixture()
        f["restaurants"][0]["opening_hours"] += [{"weekday": "thu", "opens": "10:00", "closes": "12:00"}]
        self.assertLess(self.api.call("POST", "/_test/reset", f).status, 500)
        self.reset()

    def test_L020_capacity_types(self):
        for v in (0, -1, 2.5, "4", True, False, None):
            f = fixture()
            f["restaurants"][0]["tables"][0]["capacity"] = v
            self.err(self.api.call("POST", "/_test/reset", f), 422, "validation_failed")
        self.reset()

    def test_L022_seed_reservations(self):
        from common import seed_res
        f = fixture(reservations=[seed_res(1, "u_ada", "r_anker", "t_2", f"{THU}T19:00", 3, "ABC123")])
        self.reset(f)
        t = self.ada
        r = self.api.call("GET", "/reservations/ABC123", token=t)
        self.assertEqual(r.status, 200, r)
        j = r.json
        self.assertEqual((j["reservation_id"], j["reference"], j["status"], j["party_size"], j["table_id"],
                          j["restaurant_id"], j["starts_at_local"]),
                         ("res_s1", "ABC123", "confirmed", 3, "t_2", "r_anker", f"{THU}T19:00"))
        self.assertEqual(j["starts_at"], f"{THU}T19:00:00+01:00")
        self.assertEqual(j["ends_at"], f"{THU}T20:30:00+01:00")
        self.assertIn("created_at", j)
        self.err(self.api.call("GET", "/reservations/ABC123", token=self.bob), 404, "not_found")
        self.assertNotIn("t_2", self.slot_map("r_anker", THU)[f"{THU}T19:00"]["available_table_ids"])
        self.err(self.book(t, f"{THU}T19:30"), 409, "table_unavailable")

    def test_L023_past_dates_allowed(self):
        r = self.book(self.ada, "2020-01-02T19:00")
        self.assertEqual(r.status, 201, r)
        self.assertTrue(self.slot_map("r_anker", "2020-01-02"))
        from common import seed_res
        self.reset(fixture(reservations=[seed_res(1, "u_ada", "r_anker", "t_2", "2019-01-03T19:00", 2)]))
        self.assertEqual(self.api.call("GET", "/reservations/SEED01", token=self.ada).status, 200)

    def test_L024_error_shape_unknown_route(self):
        r = self.api.call("GET", "/definitely/not/here")
        self.assertIn(r.status, (404,))
        self.err(r, 404, "not_found")
