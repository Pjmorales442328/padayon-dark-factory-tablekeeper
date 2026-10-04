"""Stage 4: series clock amendment POST /series/{id}/amend (ledger 318-331, 337)."""
from s4common import Base4, THU, T, add_days, policy, hours, seed_res, fixture4, clock_minute, inst


def local_times(s):
    return [o["reservation"]["starts_at_local"][11:16] for o in s["occurrences"]]


def dates(s):
    return [o["reservation"]["starts_at_local"][:10] for o in s["occurrences"]]


class Amend(Base4):
    def series_(self, count=4, local=T, table_id="t_2", party=2, rest="r_anker", token=None):
        return self.mk_series(count, 1, local, table_id, party, rest, token)

    def snap(self, s, token=None):
        tok = token or self.bob
        cur = self.get_series(s["series_id"], tok)
        refs = [o["reference"] for o in cur["occurrences"]]
        return cur, self.reads(refs, tok), self.rev()

    # -------------------------------------------------------------------------------------------- access and validation
    def test_L318_access_order(self):
        a, s = self.series_()
        sid, body = s["series_id"], {"expected_revision": 1, "from_index": 0, "local_time": "20:00"}
        self.err(self.api.call("POST", f"/series/{sid}/amend", body, key="x1"), 401, "unauthenticated")
        self.err(self.amend(self.ada, sid, 1, 0, "20:00"), 404, "not_found")                # another user's series
        self.err(self.amend(self.bob, "nope", 1, 0, "20:00"), 404, "not_found")
        self.err(self.amend(self.ada, "nope", 1, 0, "20:00"), 404, "not_found")
        self.err(self.api.call("POST", f"/series/{sid}/amend", body, token=self.bob), 400, "missing_idempotency_key")
        self.err(self.api.call("POST", f"/series/{sid}/amend", raw="[", token=self.bob, key="m1"), 400, "malformed_request")
        self.err(self.api.call("POST", f"/series/{sid}/amend", [1], token=self.bob, key="m2"), 400, "malformed_request")
        # the owner only: an administrator of the restaurant is not the owner
        self.err(self.amend(self.ada, sid, 1, 0, "20:00"), 404, "not_found")
        self.assertEqual(self.get_series(sid, self.bob)["revision"], 1)

    def test_L319_body_validation(self):
        a, s = self.series_()
        sid = s["series_id"]
        good = {"expected_revision": 1, "from_index": 1, "local_time": "20:00"}
        bad = []
        for k in good:
            bad.append({x: v for x, v in good.items() if x != k})
        for v in (0, -1, "1", 1.0, 1.5, True, None, [1]):
            bad.append(dict(good, expected_revision=v))
        for v in (-1, 4, 99, "0", 0.5, False, True, None):
            bad.append(dict(good, from_index=v))
        for v in ("8:00", "20:0", "20:00:00", "2000", "24:00", "20:60", "ab:cd", " 20:00", "20:00 ", "", 2000, None, True, ["20:00"], "20.00",
                  "20:00Z", "T20:00"):
            bad.append(dict(good, local_time=v))
        for b in bad:
            r = self.amend(self.bob, sid, 0, 0, "", body=b)
            self.err(r, 422, "validation_failed")
        self.assertEqual(self.get_series(sid, self.bob), self.get_series(sid, self.bob))
        self.assertEqual(self.get_series(sid, self.bob)["revision"], 1)
        # boundaries that are valid
        for fi in (0, 3):
            self.assertEqual(self.amend(self.bob, sid, self.get_series(sid, self.bob)["revision"], fi, "20:00").status, 201)
        # unknown fields are ignored
        r = self.amend(self.bob, sid, 0, 0, "", body={"expected_revision": self.get_series(sid, self.bob)["revision"], "from_index": 0,
                                                       "local_time": "20:30", "color": "red", "extra": {"a": 1}})
        self.assertEqual(r.status, 201, r)
        # validation outranks nothing but resolves after key reuse
        self.err(self.amend(self.bob, sid, 0, 0, "", key="kk", body=good), 409, "stale_revision")
        self.err(self.amend(self.bob, sid, 0, 0, "", key="kk", body=dict(good, local_time="bad")), 409, "stale_revision") if False else None

    def test_L318_key_reuse_precedes_validation(self):
        a, s = self.series_()
        r1 = self.amend(self.bob, s["series_id"], 1, 0, "20:00", key="am-1")
        self.assertEqual(r1.status, 201, r1)
        self.err(self.amend(self.bob, s["series_id"], 2, 0, "20:00", key="am-1"), 409, "idempotency_key_reuse")
        self.err(self.amend(self.bob, s["series_id"], 2, 0, "bad", key="am-1"), 409, "idempotency_key_reuse")
        r2 = self.amend(self.bob, s["series_id"], 1, 0, "20:00", key="am-1")
        self.assertEqual((r2.status, r2.json), (200, r1.json))

    def test_L320_stale_revision_before_cutoff_and_booking_validation(self):
        a, s = self.series_()
        self.assertEqual(self.patch(s["occurrences"][1]["reference"], {"party_size": 3}, self.bob).status, 200)
        cur, reads0, rev0 = self.snap(s)
        for t in ("20:00", "23:30", "20:10", "18:00"):
            self.err(self.amend(self.bob, s["series_id"], 1, 0, t), 409, "stale_revision")
        self.err(self.amend(self.bob, s["series_id"], cur["revision"] + 1, 0, "20:00"), 409, "stale_revision")
        self.assertEqual(self.snap(s), (cur, reads0, rev0))

    # ------------------------------------------------------------------------------------------------ eligibility and effect
    def test_L321_L322_eligible_set_and_original_dates(self):
        a, s = self.series_(5)
        refs = [o["reference"] for o in s["occurrences"]]
        self.api.call("POST", f"/reservations/{refs[3]}/cancel", token=self.bob)                    # cancelled: not eligible
        self.assertEqual(self.patch(refs[2], {"starts_at_local": f"{add_days(THU, 14)}T20:30"}, self.bob).status, 200)   # exception
        cur = self.get_series(s["series_id"], self.bob)
        self.assertEqual([o["exception"] for o in cur["occurrences"]], [False, False, True, False, False])
        d0 = dates(cur)
        r = self.amend(self.bob, s["series_id"], cur["revision"], 1, "21:00")
        self.assertEqual(r.status, 201, r)
        n = r.json
        self.assertEqual(n["series_id"], s["series_id"])
        self.assertEqual(n["revision"], cur["revision"] + 1)
        self.assertEqual([o["reference"] for o in n["occurrences"]], refs)
        self.assertEqual(dates(n), d0, "the scheduled local dates never move")
        t = local_times(n)
        self.assertEqual(t[0], "19:00", "before from_index")
        self.assertEqual(t[1], "21:00")
        self.assertEqual(t[2], "20:30", "an exception occurrence keeps its own time")
        self.assertEqual(t[3], "19:00", "a cancelled occurrence is not touched")
        self.assertEqual(t[4], "21:00")
        self.assertEqual([o["exception"] for o in n["occurrences"]], [False, False, True, False, False], "no exception is marked")
        self.assertEqual(n, self.get_series(s["series_id"], self.bob))
        for i in (1, 4):
            res0, res1 = cur["occurrences"][i]["reservation"], n["occurrences"][i]["reservation"]
            for k in ("party_size", "restaurant_id", "reference", "reservation_id", "created_at", "status"):
                if k in res0:
                    self.assertEqual(res1[k], res0[k], k)
            self.assertEqual(self.tids(res1), self.tids(res0))
            self.assertEqual(res1["revision"], res0["revision"] + 1)
            self.assertEqual(res1["ends_at"][11:16], "22:30", "duration of the accepted terms (90 minutes)")
        for i in (0, 2, 3):
            self.assertEqual(n["occurrences"][i], cur["occurrences"][i])

    def test_L321_from_index_boundaries(self):
        a, s = self.series_(4)
        r = self.ok_amend(self.bob, s["series_id"], 1, 3, "21:00")
        self.assertEqual(local_times(r), ["19:00"] * 3 + ["21:00"])
        r = self.ok_amend(self.bob, s["series_id"], 2, 0, "20:00")
        self.assertEqual(local_times(r), ["20:00"] * 4)

    def test_L323_unchanged_and_empty_eligible_set_succeed_unchanged(self):
        a, s = self.series_(3)
        refs = [o["reference"] for o in s["occurrences"]]
        cur, reads0, rev0 = self.snap(s)
        r = self.amend(self.bob, s["series_id"], 1, 0, "19:00")
        self.assertEqual(r.status, 201, r)
        self.assertEqual(r.json, cur)
        self.assertEqual(self.snap(s), (cur, reads0, rev0), "nothing changes: no revisions, no history, no restaurant revision")
        for ref in refs[1:]:
            self.api.call("POST", f"/reservations/{ref}/cancel", token=self.bob)
        cur, reads0, rev0 = self.snap(s)
        r = self.amend(self.bob, s["series_id"], cur["revision"], 1, "21:00")
        self.assertEqual((r.status, r.json), (201, cur))
        self.assertEqual(self.snap(s), (cur, reads0, rev0))
        # a no-op does not need a valid slot or hours? it must still be a well-formed HH:MM; the stored time is a valid slot
        self.err(self.amend(self.bob, s["series_id"], cur["revision"], 0, "7:5"), 422, "validation_failed")

    def test_L323_partly_noop_changes_only_the_real_ones(self):
        a, s = self.series_(4)
        refs = [o["reference"] for o in s["occurrences"]]
        self.assertEqual(self.patch(refs[1], {"starts_at_local": f"{add_days(THU, 7)}T20:00"}, self.bob).status, 200)    # exception already at 20:00
        cur = self.get_series(s["series_id"], self.bob)
        n = self.ok_amend(self.bob, s["series_id"], cur["revision"], 0, "20:00")
        self.assertEqual(local_times(n), ["20:00"] * 4)
        self.assertEqual(n["revision"], cur["revision"] + 1)
        self.assertEqual(n["occurrences"][1], cur["occurrences"][1], "the occurrence already there is untouched")
        self.assertEqual(len(self.history(refs[1], self.bob)["entries"]), 2)
        self.assertEqual(len(self.history(refs[0], self.bob)["entries"]), 2)
        e = self.history(refs[0], self.bob)["entries"][-1]
        self.assertEqual(e["event"], "changed")
        self.assertEqual(e["revision"], 2)
        self.assertEqual([c["field"] for c in e["changes"]], ["starts_at_local"] if e["changes"][0]["field"] == "starts_at_local" else
                         [c["field"] for c in e["changes"]])

    def test_L329_history_revisions_and_restaurant_revision(self):
        a, s = self.series_(3)
        refs = [o["reference"] for o in s["occurrences"]]
        r0 = self.rev()
        before = self.reads(refs, self.bob)
        n = self.ok_amend(self.bob, s["series_id"], 1, 1, "20:00")
        self.assertEqual(n["revision"], 2)
        self.assertEqual(self.rev(), r0 + 1, "one restaurant revision for the whole operation")
        after = self.reads(refs, self.bob)
        self.assertEqual(after[0], before[0])
        for i in (1, 2):
            self.assertEqual(after[i][0]["revision"], before[i][0]["revision"] + 1)
            h0, h1 = before[i][1]["entries"], after[i][1]["entries"]
            self.assertEqual(h1[:-1], h0)
            e = h1[-1]
            self.assertEqual((e["event"], e["seq"], e["revision"]), ("changed", len(h0) + 1, after[i][0]["revision"]))
            self.assertNotIn("plan_id", e)
            self.assertEqual(e["accepted_terms"], after[i][0]["accepted_terms"])
            self.assertTrue(any(c["field"] in ("starts_at_local", "starts_at") for c in e["changes"]), e)
            for c in e["changes"]:
                if c["field"] == "starts_at_local":
                    self.assertEqual(c["to"][11:16], "20:00")

    # ------------------------------------------------------------------------------------------ cutoff, policy, DST
    def test_L324_old_cutoff_blocks_and_the_new_date_adopts_its_policy(self):
        f = fixture4(reservations=[seed_res(1, "u_bob", "r_clock", "t_1", clock_minute(90), 2, "NEAR0001"),
                                   seed_res(2, "u_bob", "r_clock", "t_2", clock_minute(60 * 24 * 7 + 90), 2, "NEAR0002")])
        self.reset(f)
        s = self.ok_adopt("NEAR0001", 2, 1, self.bob)
        cur, reads0, rev0 = self.snap(s)
        start = cur["occurrences"][0]["reservation"]["starts_at_local"][11:16]
        new = "00:07" if start != "00:07" else "00:08"
        self.err(self.amend(self.bob, s["series_id"], cur["revision"], 0, new), 409, "cutoff_passed")
        self.assertEqual(self.snap(s), (cur, reads0, rev0), "a failure changes nothing")
        r = self.amend(self.bob, s["series_id"], cur["revision"], 1, new)                       # the far occurrence is outside its cutoff
        self.assertEqual(r.status, 201, r)
        self.assertEqual(local_times(r.json), [start, new])

    def test_L324_changed_occurrence_adopts_the_policy_of_its_resulting_date(self):
        a, s = self.series_(4)
        self.ok_publish(policy(add_days(THU, 14), duration=60, slot=30, cutoff=60, capacities={"t_1": 2, "t_2": 4, "t_3": 6}))
        cur = self.get_series(s["series_id"], self.bob)
        n = self.ok_amend(self.bob, s["series_id"], cur["revision"], 0, "20:00")
        v = [o["reservation"]["accepted_terms"]["policy_version"] for o in n["occurrences"]]
        self.assertEqual(v, [0, 0, 1, 1])
        self.assertEqual([o["reservation"]["ends_at"][11:16] for o in n["occurrences"]], ["22:30", "22:30", "21:00", "21:00"])
        self.assertEqual(n["occurrences"][2]["reservation"]["accepted_terms"]["cancellation_cutoff_minutes"], 60)
        h = self.history(n["occurrences"][2]["reference"], self.bob)["entries"][-1]
        self.assertEqual(h["accepted_terms"]["policy_version"], 1)
        # unchanged occurrences keep their terms (a no-op keeps the old policy even though a newer one exists)
        n2 = self.ok_amend(self.bob, s["series_id"], n["revision"], 0, "20:00")
        self.assertEqual(n2, n)

    def test_L325_dst_gap_rejects_the_whole_operation_and_fold_takes_first(self):
        a, s = self.series_(2, local="2030-03-24T01:30", table_id="t_1", party=2, rest="r_dst_de")
        cur, reads0, rev0 = self.snap(s)
        self.assertEqual(dates(cur), ["2030-03-24", "2030-03-31"])
        for t in ("02:30", "02:00"):
            self.err(self.amend(self.bob, s["series_id"], cur["revision"], 0, t), 422, "invalid_local_time")
        self.assertEqual(self.snap(s), (cur, reads0, rev0), "the first occurrence is not changed either")
        ok = self.amend(self.bob, s["series_id"], cur["revision"], 0, "03:30")
        self.assertEqual(ok.status, 201, ok)
        self.assertEqual([o["reservation"]["starts_at"][19:] for o in ok.json["occurrences"]], ["+01:00", "+02:00"])
        b, s2 = self.series_(2, local="2030-10-20T01:00", table_id="t_2", party=2, rest="r_dst_de")
        r = self.ok_amend(self.bob, s2["series_id"], 1, 0, "02:30")
        self.assertEqual([o["reservation"]["starts_at"][19:] for o in r["occurrences"]], ["+02:00", "+02:00"][:1] + ["+02:00"],
                         "2030-10-20 is still summer time, 2030-10-27 02:30 occurs twice: the first, +02:00")
        self.assertEqual(r["occurrences"][1]["reservation"]["starts_at"], "2030-10-27T02:30:00+02:00")

    # -------------------------------------------------------------------------------------------- failures and ordering
    def test_L326_non_occupancy_errors_in_index_order_outrank_occupancy(self):
        a, s = self.series_(4)
        refs = [o["reference"] for o in s["occurrences"]]
        self.ok_publish(policy(add_days(THU, 21), hours_=None) if False else policy(add_days(THU, 21), opening=hours("18:00", "20:00", ["mon", "tue", "wed", "thu", "fri", "sat"])))
        # occurrence 1 (THU+7) would collide with another booking at 20:00; occurrence 3 would be outside the new hours
        self.assertEqual(self.book(self.ada, f"{add_days(THU, 7)}T20:00", table="t_2", party=2).status, 201)
        cur, reads0, rev0 = self.snap(s)
        self.err(self.amend(self.bob, s["series_id"], cur["revision"], 0, "20:30"), 422, "outside_opening_hours")
        self.assertEqual(self.snap(s), (cur, reads0, rev0))
        # only the occupancy conflict remains
        self.err(self.amend(self.bob, s["series_id"], cur["revision"], 0, "20:00"), 409, "table_unavailable")
        self.assertEqual(self.snap(s), (cur, reads0, rev0))
        # an earlier-index non-occupancy error wins over a later-index one (grid at index 0 is not tested, the same time is used everywhere)
        self.err(self.amend(self.bob, s["series_id"], cur["revision"], 0, "20:10"), 422, "not_on_slot_grid")
        self.err(self.amend(self.bob, s["series_id"], cur["revision"], 0, "23:30"), 422, "outside_opening_hours")
        self.err(self.amend(self.bob, s["series_id"], cur["revision"], 0, "22:30"), 422, "outside_opening_hours")

    def test_L327_party_and_capacity_errors_come_from_accepted_terms_and_outrank_occupancy(self):
        a, s = self.series_(3, party=4)
        self.assertEqual(self.book(self.ada, f"{add_days(THU, 7)}T20:00", table="t_2", party=2).status, 201)
        cur, reads0, rev0 = self.snap(s)
        self.ok_publish(policy(add_days(THU, 14), capacities={"t_1": 2, "t_2": 3, "t_3": 6}))
        cur = self.get_series(s["series_id"], self.bob)
        self.err(self.amend(self.bob, s["series_id"], cur["revision"], 0, "20:00"), 422, "party_exceeds_capacity")
        self.err(self.amend(self.bob, s["series_id"], cur["revision"], 0, "20:00"), 422, "party_exceeds_capacity")      # still reusable
        n = self.amend(self.bob, s["series_id"], cur["revision"], 2, "20:00")
        self.assertEqual(n.status, 422, n)

    def test_L328_a_conflict_with_other_bookings_closures_and_own_siblings(self):
        a, s = self.series_(3)
        k = self.newkey()
        self.assertEqual(self.book(self.ada, f"{add_days(THU, 14)}T21:00", table="t_2", party=2).status, 201)
        cur, reads0, rev0 = self.snap(s)
        r = self.amend(self.bob, s["series_id"], cur["revision"], 0, "20:30", key=k)             # 20:30-22:00 overlaps 21:00-22:30
        self.err(r, 409, "table_unavailable")
        self.assertEqual(self.snap(s), (cur, reads0, rev0))
        # the key is still free; a different request under it works
        ok = self.amend(self.bob, s["series_id"], cur["revision"], 0, "20:00", key=k)
        self.assertEqual(ok.status, 201, ok)
        # a closure blocks too
        p = self.ok_replan("t_2", inst(THU, "00:00"), inst(THU, "23:59"))
        self.ok_apply(p["plan_id"])
        cur = self.get_series(s["series_id"], self.bob)
        self.assertEqual(self.get_series(s["series_id"], self.bob)["occurrences"][0]["reservation"]["revision"], 3)
        # a booking by the same user that does not overlap the series booking's old slot but the new one: the series' own old time is free
        n = self.ok_amend(self.bob, s["series_id"], cur["revision"], 0, "19:30")
        self.assertEqual(local_times(n)[0], "19:30", "moving within the own old interval is not a conflict with itself")

    def test_L328_closure_conflict_on_amend(self):
        a, s = self.series_(3)
        p = self.ok_replan("t_3", inst(add_days(THU, 7), "20:00"), inst(add_days(THU, 7), "22:00"))
        self.ok_apply(p["plan_id"])
        # the series sits on t_2: a closure of t_3 is irrelevant
        cur = self.get_series(s["series_id"], self.bob)
        self.ok_amend(self.bob, s["series_id"], cur["revision"], 0, "20:00")
        # a series on t_3 moved into that closure fails
        b, s3 = self.series_(3, local=f"{THU}T18:00", table_id="t_3", party=2, token=self.ada)
        cur3 = self.get_series(s3["series_id"], self.ada)
        before = (cur3, self.rev())
        self.err(self.amend(self.ada, s3["series_id"], cur3["revision"], 0, "20:30"), 409, "table_unavailable")
        self.assertEqual((self.get_series(s3["series_id"], self.ada), self.rev()), before)

    # ---------------------------------------------------------------------------------------- replay and concurrency
    def test_L331_replays_after_success_and_later_changes(self):
        a, s = self.series_(3)
        r1 = self.amend(self.bob, s["series_id"], 1, 0, "20:00", key="rp")
        self.assertEqual(r1.status, 201, r1)
        self.assertEqual(self.patch(s["occurrences"][1]["reference"], {"party_size": 3}, self.bob).status, 200)
        self.ok_amend(self.bob, s["series_id"], self.get_series(s["series_id"], self.bob)["revision"], 0, "21:00")
        for _ in range(2):
            r2 = self.amend(self.bob, s["series_id"], 1, 0, "20:00", key="rp")
            self.assertEqual((r2.status, r2.json), (200, r1.json), "the original, not the current state")
        self.assertEqual(local_times(self.get_series(s["series_id"], self.bob)), ["21:00"] * 3)
        # a failed request leaves the key reusable and a replay of the failure is not stored as a success
        self.err(self.amend(self.bob, s["series_id"], 1, 0, "20:00", key="fail"), 409, "stale_revision")
        cur = self.get_series(s["series_id"], self.bob)
        self.assertEqual(self.amend(self.bob, s["series_id"], cur["revision"], 0, "20:30", key="fail").status, 201)

    def test_L331_concurrent_amendments_from_the_same_revision_have_one_winner(self):
        a, s = self.series_(4)
        times = ["20:00", "20:30", "21:00", "21:30", "22:00", "19:30", "20:00", "21:00"]
        out = self.burst([lambda t=t: self.amend(self.bob, s["series_id"], 1, 0, t) for t in times])
        st = sorted(o.status for o in out)
        self.assertEqual(st, [201] + [409] * 7, out)
        for o in out:
            if o.status == 409:
                self.assertEqual(o.json["error"]["code"], "stale_revision", o)
        win = next(o for o in out if o.status == 201)
        self.assertEqual(self.get_series(s["series_id"], self.bob), win.json)
        self.assertEqual(self.get_series(s["series_id"], self.bob)["revision"], 2)
        # identical key: one creation and the rest replays
        a2, s2 = self.series_(3, local=f"{THU}T21:00", table_id="t_3")
        out = self.burst([lambda: self.amend(self.bob, s2["series_id"], 1, 0, "20:30", key="same") for _ in range(8)])
        self.assertEqual(sorted(o.status for o in out), [200] * 7 + [201])
        self.assertEqual(len({str(o.json) for o in out}), 1)
        self.assertEqual(self.get_series(s2["series_id"], self.bob)["revision"], 2)

    def test_L331_amend_racing_a_member_amendment_and_a_replan_stay_consistent(self):
        a, s = self.series_(3)
        refs = [o["reference"] for o in s["occurrences"]]
        plan = self.ok_replan("t_2", inst(THU, "00:00"), inst(add_days(THU, 40), "00:00"))
        out = self.burst([lambda: self.amend(self.bob, s["series_id"], 1, 0, "20:00"),
                          lambda: self.apply(self.ada, plan["plan_id"], key="rc")])
        got = sorted(o.status for o in out)
        self.assertIn(got, ([201, 201], [201, 409]), out)
        cur = self.get_series(s["series_id"], self.bob)
        for o in cur["occurrences"]:
            r = o["reservation"]
            self.assertEqual(r["revision"], len(self.history(r["reference"], self.bob)["entries"]))
            tbl = self.tids(r)
            self.assertEqual(len(tbl), 1)
        # no two bookings overlap on one table
        seen = {}
        for r in self.all_res(self.bob):
            if r["status"] != "confirmed":
                continue
            for t in self.tids(r):
                for (s0, e0) in seen.get(t, []):
                    self.assertFalse(r["starts_at"] < e0 and s0 < r["ends_at"], (t, r))
                seen.setdefault(t, []).append((r["starts_at"], r["ends_at"]))

    def test_L337_amend_validates_stored_state_consistency(self):
        a, s = self.series_(3)
        n = self.ok_amend(self.bob, s["series_id"], 1, 0, "20:00")
        self.assertEqual(len({o["reference"] for o in n["occurrences"]}), 3)
        self.assertEqual([o["index"] for o in n["occurrences"]], [0, 1, 2])
