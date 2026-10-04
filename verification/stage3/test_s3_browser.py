"""Stage 3 browser checks: the stage-2 grid and flows follow the authoritative published-policy availability (ledger 215, 291).

The whole inherited stage-2 browser suite is run against stage 3 by run_stage3.py; these add policy-specific cases.
"""
import re

from browser_helpers import BrowserBase, tid, PHONE, DESKTOP
from s3common import THU, T, fixture3, policy, hours, add_days

REF = re.compile(r"^[A-Z0-9]{6,12}$")


class PolicyBrowser(BrowserBase):
    fixture_factory = staticmethod(fixture3)

    def publish_policy(self):
        caps = {"t_1": 3, "t_2": 5, "t_3": 7}
        p = policy("2030-01-01", duration=60, slot=60, cutoff=45, opening=hours("17:00", "23:00", ["thu"]), capacities=caps)
        r = self.api.call("POST", "/restaurants/r_anker/policies", p, token=self.ada, key=self.newkey())
        self.assertEqual(r.status, 201, r)
        return caps

    def test_L215_L291_grid_follows_the_selected_policy(self):
        self.publish_policy()
        self.search("r_anker", THU, 3)
        self.assert_grid_matches("r_anker", THU, 3)
        c = self.cells()
        self.assertEqual(c["slot-t_1-17:00"], "true", "17:00 exists only under the published policy; t_1 now seats 3")
        self.assertNotIn("slot-t_1-18:30", c, "the published grid is hourly")
        self.assertEqual(c["slot-t_1+t_2-17:00"], "true")
        self.search("r_anker", "2029-01-04", 3)                                  # before the policy: fixture rules
        self.assert_grid_matches("r_anker", "2029-01-04", 3)
        self.assertEqual(self.cells()["slot-t_1-19:00"], "false")
        self.assertNotIn("slot-t_1-17:00", self.cells())

    def test_L291_booking_through_the_ui_under_a_policy_and_lookup(self):
        self.publish_policy()
        self.ui_login()
        self.search("r_anker", THU, 3)
        self.click_cell("t_1-17:00")
        self.page.wait_for_selector(tid("booking-form"))
        self.assertIn("17:00", self.text("booking-summary"))
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"))
        ref = self.text("confirmation-reference")
        self.assertRegex(ref, REF)
        b = self.api.call("GET", f"/reservations/{ref}", token=self.ada).json
        self.assertEqual((b["revision"], b["accepted_terms"]["policy_version"], b["party_size"]), (1, 1, 3))
        self.assertEqual(b["ends_at"][11:16], "18:00")
        self.goto("/lookup")
        self.page.fill(tid("lookup-reference-input"), ref)
        self.page.click(tid("lookup-submit"))
        self.page.wait_for_selector(tid("reservation-detail"))
        self.assertEqual(self.text("reservation-status"), "confirmed")
        self.assertIn("Window", self.text("reservation-tables"))
        self.page.click(tid("reservation-cancel-button"))
        self.page.wait_for_function("() => document.querySelector(\"[data-testid='reservation-status']\").innerText.trim() === 'cancelled'")
        self.assertEqual(self.api.call("GET", f"/reservations/{ref}", token=self.ada).json["revision"], 2)

    def test_L291_pair_booking_under_policy_capacities(self):
        self.publish_policy()
        self.ui_login()
        self.search("r_anker", THU, 8)
        c = self.cells()
        self.assertEqual(c["slot-t_1+t_2-18:00"], "true")                       # 3 + 5 seats
        self.click_cell("t_1+t_2-18:00")
        self.page.wait_for_selector(tid("booking-form"))
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"))
        b = self.api.call("GET", "/reservations", token=self.ada).json["reservations"][0]
        self.assertEqual((sorted(b["table_ids"]), b["accepted_terms"]["capacities"]["t_2"], b["revision"]), (["t_1", "t_2"], 5, 1))
        for s in ("Window", "Booth"):
            self.assertIn(s, self.text("confirmation-tables"))

    def test_L291_late_search_across_policy_dates_keeps_the_later_search(self):
        self.publish_policy()
        self.goto("/")
        st = self.hold_availability(2)
        self.search("r_anker", "2029-01-04", 2, wait=False)                      # A: fixture rules (held)
        self.pump(self.page, 400)
        self.page.fill(tid("date-input"), THU)
        self.page.fill(tid("party-size-input"), "3")
        self.page.click(tid("search-button"))                                    # B: the policy date
        self.page.wait_for_selector(tid("availability-grid"), state="visible")
        before = self.cells()
        self.assertIn("slot-t_1-17:00", before)
        self.release(st)
        self.assertEqual(self.cells(), before)
        self.assert_grid_matches("r_anker", THU, 3)
