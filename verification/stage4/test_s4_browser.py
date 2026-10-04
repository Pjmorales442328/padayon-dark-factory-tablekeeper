"""Stage 4 browser checks (ledger 345): after a replan is applied through the API the UI reflects it, at phone and desktop widths.

The inherited stage-2/3 browser suites run unchanged against stage 4 (run_stage4.py); these add closure/applied-plan cases.
"""
import re

from browser_helpers import BrowserBase, tid, PHONE, DESKTOP
from s4common import THU, T, fixture4, inst

REF = re.compile(r"^[A-Z0-9]{6,12}$")


class AppliedPlan(BrowserBase):
    fixture_factory = staticmethod(fixture4)

    def scenario(self):
        """A booking on t_2 at 19:00; the manager closes t_2 for the evening, which moves the booking to another table."""
        b = self.ok_book(self.ada, T, table="t_2", party=2)
        p = self.api.call("POST", "/restaurants/r_anker/replans", {"table_id": "t_2", "from": inst(THU, "18:00"), "to": inst(THU, "23:00")},
                          token=self.ada, key=self.newkey())
        self.assertEqual(p.status, 201, p)
        a = self.api.call("POST", f"/restaurants/r_anker/replans/{p.json['plan_id']}/apply", {}, token=self.ada, key=self.newkey())
        self.assertEqual(a.status, 201, a)
        moved = [x for x in a.json["reservations"] if x["reference"] == b["reference"]][0]
        self.assertNotEqual(sorted(moved.get("table_ids") or [moved["table_id"]]), ["t_2"])
        return b["reference"], moved

    def check_ui(self):
        ref, moved = self.scenario()
        self.search("r_anker", THU, 2)
        self.assert_grid_matches("r_anker", THU, 2)
        c = self.cells()
        for k, v in c.items():
            if k.startswith("slot-t_2-") and re.search(r"-(1[89]|2[0-2]):", k):
                self.assertEqual(v, "false", f"{k}: the closed table is not offered during the closure")
        self.assertFalse(any(v == "true" and "t_2" in k.split("-")[1].split("+") and re.search(r"-(1[89]|2[0-2]):", k) for k, v in c.items()),
                         "no pair containing the closed table is offered")
        self.goto("/lookup")
        self.ui_login()
        self.goto("/lookup")
        self.page.fill(tid("lookup-reference-input"), ref)
        self.page.click(tid("lookup-submit"))
        self.page.wait_for_selector(tid("reservation-detail"))
        self.assertEqual(self.text("reservation-status"), "confirmed")
        names = {"t_1": "Terrace", "t_2": "Booth", "t_3": "Window"}
        shown = self.text("reservation-tables")
        for t in (moved.get("table_ids") or [moved["table_id"]]):
            self.assertIn(names[t], shown, "lookup shows the table the plan moved the booking to")
        self.assertNotIn("Booth", shown)
        self.shot("s4-lookup-applied-%d" % self.viewport["width"])
        w = self.page.evaluate("() => [document.documentElement.scrollWidth, window.innerWidth]")
        self.assertLessEqual(w[0], w[1] + 1, "no horizontal overflow")

    def check_booking_blocked(self):
        self.scenario()
        self.ui_login()
        self.search("r_anker", THU, 2)
        self.assertEqual(self.cells().get("slot-t_2-19:00"), "false")
        self.assertEqual(self.external, [])
        self.assertEqual(self.console_errors, [])


class AppliedPlanPhone(AppliedPlan):
    viewport = PHONE

    def test_L345_phone_ui_reflects_applied_plan(self):
        self.check_ui()

    def test_L345_phone_closed_table_is_not_bookable(self):
        self.check_booking_blocked()


class AppliedPlanDesktop(AppliedPlan):
    viewport = DESKTOP

    def test_L345_desktop_ui_reflects_applied_plan(self):
        self.check_ui()

    def test_L345_desktop_closed_table_is_not_bookable(self):
        self.check_booking_blocked()

    def test_L345_ui_booking_after_closure_lands_on_an_open_table(self):
        self.scenario()
        self.ui_login()
        self.search("r_anker", THU, 2)
        open_cells = [k for k, v in self.cells().items() if v == "true" and k.endswith("-20:00") and "+" not in k]
        self.assertTrue(open_cells, "some table is still bookable")
        self.click_cell(open_cells[0][len("slot-"):])
        self.page.wait_for_selector(tid("booking-form"))
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"))
        ref = self.text("confirmation-reference")
        self.assertRegex(ref, REF)
        got = self.api.call("GET", f"/reservations/{ref}", token=self.ada).json
        self.assertNotIn("t_2", got.get("table_ids") or [got["table_id"]])
