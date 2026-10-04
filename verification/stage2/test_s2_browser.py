"""Stage 2 browser checks (ledger 118-151, 174-176, 190, 192): functional flows driven through a real Chromium."""
import re
import unittest

from browser_helpers import BrowserBase, tid, PHONE, DESKTOP
from s2common import THU, SUN, FRI, fixture2, seed_res, LABELS

T = f"{THU}T19:00"
REF = re.compile(r"^[A-Z0-9]{6,12}$")


def post_attempts(state):
    return [a for a in state["attempts"]]


class Screens(BrowserBase):
    def test_L118_L133_four_routes_render_and_share_navigation(self):
        want = {"/": ["restaurant-select", "date-input", "party-size-input", "search-button"],
                "/signup": ["signup-email", "signup-password", "signup-display-name", "signup-submit"],
                "/login": ["login-email", "login-password", "login-submit"],
                "/lookup": ["lookup-reference-input", "lookup-submit"]}
        for path, ids in want.items():
            self.goto(path)
            for i in ids:
                self.assertTrue(self.visible(i), f"{i} on {path}")
            hrefs = {self.page.get_attribute(f"a >> nth={n}", "href") for n in range(self.page.locator("a").count())}
            for needed in ("/", "/lookup"):
                self.assertTrue(any(h and h.split("?")[0].rstrip("/") == needed.rstrip("/") for h in hrefs),
                                f"link to {needed} on {path}: {hrefs}")
            self.assertTrue(any(h and h.rstrip("/") in ("/login", "/signup") for h in hrefs), f"auth link on {path}")
        self.assertEqual(self.external, [], "UI requested external hosts")
        self.assertEqual(self.console_errors, [])

    def test_L118_L133_screens_reachable_through_ui_clicks(self):
        self.goto("/")
        self.page.click("a[href='/lookup']")
        self.page.wait_for_selector(tid("lookup-reference-input"))
        self.assertEqual(self.page.url.rstrip("/").split("/")[-1], "lookup")
        self.page.click("a[href='/login']")
        self.page.wait_for_selector(tid("login-email"))
        link = self.page.locator("a[href='/signup']")
        if link.count():
            link.first.click()
            self.page.wait_for_selector(tid("signup-email"))
        self.page.click("a[href='/']")
        self.page.wait_for_selector(tid("search-button"))

    def test_L134_L135_L136_L137_signup_login_logout(self):
        p = self.page
        self.goto("/signup")
        self.assertEqual(self.count("auth-error"), 0)
        p.fill(tid("signup-email"), "mia@example.com")
        p.fill(tid("signup-password"), "short")
        p.fill(tid("signup-display-name"), "Mia")
        p.click(tid("signup-submit"))
        p.wait_for_selector(tid("auth-error"), state="visible")
        self.assertTrue(self.text("auth-error"))
        self.assertEqual(self.count("current-user"), 0)
        p.fill(tid("signup-password"), "long enough pw")
        p.click(tid("signup-submit"))
        p.wait_for_selector(tid("current-user"), state="visible")
        self.assertIn("Mia", self.text("current-user"))
        self.assertEqual(self.count("auth-error"), 0, "auth-error only present when there is one")
        user = self.api.call("POST", "/auth/login", {"email": "mia@example.com", "password": "long enough pw"})
        self.assertEqual(user.status, 200)
        for path in ("/", "/lookup", "/login", "/signup"):
            self.goto(path)
            self.assertTrue(self.visible("current-user"), f"current-user on {path}")
            self.assertIn("Mia", self.text("current-user"))
            self.assertTrue(self.visible("logout-button"), path)
        self.goto("/")
        p.click(tid("logout-button"))
        p.wait_for_selector(tid("current-user"), state="detached")
        for path in ("/", "/lookup", "/login", "/signup"):
            self.goto(path)
            self.assertEqual(self.count("current-user"), 0, f"signed out on {path}")
        dump = self.storage_dump()
        self.assertNotIn("Mia", dump)

    def test_L135_L136_login_errors_and_duplicate_signup(self):
        p = self.page
        self.goto("/login")
        self.assertEqual(self.count("auth-error"), 0)
        p.fill(tid("login-email"), "ada@example.com")
        p.fill(tid("login-password"), "wrong password")
        p.click(tid("login-submit"))
        p.wait_for_selector(tid("auth-error"), state="visible")
        self.assertTrue(self.text("auth-error"))
        self.assertEqual(self.count("current-user"), 0)
        p.fill(tid("login-password"), "correct horse")
        p.click(tid("login-submit"))
        p.wait_for_selector(tid("current-user"), state="visible")
        self.assertIn("Ada", self.text("current-user"))
        self.assertEqual(self.count("auth-error"), 0)
        self.page.click(tid("logout-button"))
        self.goto("/signup")
        p.fill(tid("signup-email"), "ada@example.com")
        p.fill(tid("signup-password"), "long enough pw")
        p.fill(tid("signup-display-name"), "Other")
        p.click(tid("signup-submit"))
        p.wait_for_selector(tid("auth-error"), state="visible")
        self.assertEqual(self.count("current-user"), 0)

    def test_L137_L190_session_storage_holds_token_and_identity(self):
        self.ui_login()
        dump = self.storage_dump()
        tok = self.api.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).json["token"]
        self.assertIn("Ada", dump)
        import json
        s = json.loads(dump)["s"]
        self.assertTrue(s, "sessionStorage empty after login: the signed-in state must live in session storage")
        # the token the browser holds is a valid server token for Ada
        held = [v for v in s.values() if isinstance(v, str)]
        found = None
        for v in held:
            for cand in re.findall(r"[A-Za-z0-9_\-\.]{16,}", v):
                if self.api.call("GET", "/reservations", token=cand).status == 200:
                    found = cand
        self.assertIsNotNone(found, "no valid bearer token in session storage")
        self.assertIn("Ada", self.text("current-user"))
        self.goto("/lookup")                                                    # survives navigation within the session
        self.assertIn("Ada", self.text("current-user"))


class Search(BrowserBase):
    def test_L138_L139_controls_and_no_slots(self):
        self.goto("/")
        opts = self.page.eval_on_selector_all(f"{tid('restaurant-select')} option", "els => els.map(e => e.value)")
        self.assertEqual(opts, [r["id"] for r in self.api.call("GET", "/restaurants").json["restaurants"]])
        self.assertEqual(self.page.get_attribute(tid("party-size-input"), "type"), "number")
        self.assertEqual(self.page.get_attribute(tid("date-input"), "type"), "date")
        self.search("r_anker", SUN, 2)
        self.assertTrue(self.visible("no-slots"))
        self.assertTrue(self.text("no-slots"))
        self.assertFalse(self.visible("availability-grid"), "no-slots replaces the grid")
        self.search("r_anker", THU, 2)
        self.assertTrue(self.visible("availability-grid"))
        self.assertFalse(self.visible("no-slots"))
        self.assertEqual(self.page.input_value(tid("date-input")), THU)

    def test_L140_grid_matches_api_for_several_party_sizes(self):
        for party in (1, 2, 5, 7, 11):
            self.search("r_anker", THU, party)
            self.assert_grid_matches("r_anker", THU, party)
        self.search("r_other", THU, 3)
        self.assert_grid_matches("r_other", THU, 3)

    def test_L140_grid_reflects_bookings_and_cancelled_seed(self):
        f = fixture2(reservations=[seed_res(1, "u_bob", "r_anker", "t_2", T, 2, "SEEDAAAA"),
                                   dict(seed_res(2, "u_bob", "r_anker", "t_3", T, 2, "SEEDBBBB"), status="cancelled"),
                                   dict(seed_res(3, "u_ada", "r_anker", "t_1", f"{THU}T21:00", 1, "SEEDCCCC"))])
        f["reservations"][2].pop("table_id")
        f["reservations"][2]["table_ids"] = ["t_1", "t_2"]
        self.reset(f)
        self.search("r_anker", THU, 1)
        self.assert_grid_matches("r_anker", THU, 1)
        c = self.cells()
        self.assertEqual(c["slot-t_2-19:00"], "false")
        self.assertEqual(c["slot-t_3-19:00"], "true")                            # cancelled seed holds nothing
        self.assertEqual(c["slot-t_1-21:00"], "false")                           # pair seed holds both members
        self.assertEqual(c["slot-t_2-21:00"], "false")

    def test_L127_L130_cells_use_human_labels_not_ids(self):
        self.search("r_anker", THU, 5)
        cell = self.page.locator(tid("slot-t_3-19:00"))
        txt = cell.inner_text()
        self.assertIn("Terrace", txt)
        grid = self.page.inner_text(tid("availability-grid"))
        self.assertNotRegex(grid, r"\bt_\d\b", "technical ids must not be the visible seating names")
        self.assertIn("19:00", grid)

    def test_L125_no_background_polling_while_idle(self):
        self.ui_login()
        self.search("r_anker", THU, 2)
        reqs = []
        self.page.on("request", lambda r: reqs.append(r.url))
        self.pump(self.page, 5000)
        self.assertEqual(reqs, [], "the UI polled the server while idle")

    def test_L141_click_available_opens_form_for_that_table_and_slot(self):
        self.ui_login()
        self.search("r_anker", THU, 3)
        self.assertEqual(self.count("booking-form"), 0)
        self.click_cell("t_2-19:00")
        self.page.wait_for_selector(tid("booking-form"), state="visible")
        summary = self.text("booking-summary")
        self.assertIn("Booth", summary)
        self.assertIn("19:00", summary)
        self.assertEqual(self.page.input_value(tid("booking-party-size")), "3")
        self.assertEqual(self.page.get_attribute(tid("booking-party-size"), "type"), "number")
        self.assertTrue(self.visible("booking-submit"))
        self.assertEqual(self.count("booking-error"), 0)
        self.assertEqual(self.count("confirmation"), 0)
        self.click_cell("t_3-20:30")
        self.pump()
        s2 = self.text("booking-summary")
        self.assertIn("Terrace", s2)
        self.assertIn("20:30", s2)
        self.assertNotIn("Booth", s2)

    def test_L141_unavailable_click_does_nothing(self):
        self.ui_login()
        self.ok_book(self.bob, T, table="t_2", party=2)
        self.search("r_anker", THU, 2)
        self.assertEqual(self.cells()["slot-t_2-19:00"], "false")
        before = self.page.url
        self.click_cell("t_2-19:00")
        self.pump(self.page, 500)
        self.assertEqual(self.count("booking-form"), 0)
        self.assertEqual(self.page.url, before)
        self.assertEqual(self.count("booking-error"), 0)
        # too-small table for the searched party is unavailable too
        self.search("r_anker", THU, 5)
        self.click_cell("t_1-19:00", self.page)
        self.pump(self.page, 300)
        self.assertEqual(self.count("booking-form"), 0)

    def test_L142_signed_out_click_asks_for_login(self):
        self.search("r_anker", THU, 2)
        self.click_cell("t_2-19:00")
        self.page.wait_for_function("() => location.pathname === '/login' || document.querySelector(\"[data-testid='auth-error']\")")
        shown = self.visible("auth-error") or self.page.url.rstrip("/").endswith("/login")
        self.assertTrue(shown)
        self.assertEqual(self.api.call("GET", "/reservations", token=self.ada).json, {"reservations": []})

    def test_L174_L175_combination_cells(self):
        self.search("r_anker", THU, 5)
        c = self.cells()
        self.assertEqual(c["slot-t_1+t_2-19:00"], "true")
        self.assertEqual(c["slot-t_2+t_3-19:00"], "true")
        self.assertEqual(c["slot-t_1-19:00"], "false")                           # 2 seats for a party of 5
        self.assertEqual(c["slot-t_3-19:00"], "true")
        self.assert_grid_matches("r_anker", THU, 5)
        txt = self.page.locator(tid("slot-t_1+t_2-19:00")).inner_text()
        self.assertIn("Window", txt)
        self.assertIn("Booth", txt)
        self.assertNotRegex(txt, r"t_\d")
        self.search("r_anker", THU, 7)
        c = self.cells()
        for k in ("slot-t_1+t_2-19:00",):
            self.assertIn(c.get(k, "false"), ("false",))                         # cap 6 < 7: absent or false
        self.assertEqual(c["slot-t_2+t_3-19:00"], "true")
        self.search("r_anker", THU, 11)
        self.assertNotIn("true", [v for k, v in self.cells().items()])
        self.ok_book(self.bob, T, table="t_2", party=2)
        self.search("r_anker", THU, 5)
        c = self.cells()
        self.assertEqual(c.get("slot-t_1+t_2-19:00", "false"), "false")
        self.assertEqual(c.get("slot-t_2+t_3-19:00", "false"), "false")
        self.assertEqual(c["slot-t_3-19:00"], "true")
        self.assertEqual(c.get("slot-t_1+t_2-20:30", "x"), "true")               # adjacent slot free again

    def test_L174_pair_cell_ids_follow_combinable_order(self):
        self.reset(fixture2(combinable=[["t_3", "t_2"], ["t_1", "t_2"]]))
        self.search("r_anker", THU, 5)
        c = self.cells()
        self.assertIn("slot-t_3+t_2-19:00", c)
        self.assertNotIn("slot-t_2+t_3-19:00", c)
        self.assertIn("slot-t_1+t_2-19:00", c)


class Booking(BrowserBase):
    def open_form(self, ident, party=2, rest="r_anker", date=THU, login=True):
        if login:
            self.ui_login()
        self.search(rest, date, party)
        self.click_cell(ident)
        self.page.wait_for_selector(tid("booking-form"), state="visible")

    def reservations(self, token=None):
        return self.api.call("GET", "/reservations", token=token or self.ada).json["reservations"]

    def test_L143_L144_L145_L146_L147_L148_single_booking_flow(self):
        self.open_form("t_2-19:00", 3)
        reqs = []
        self.page.on("request", lambda r: reqs.append((r.method, r.url, r.headers.get("idempotency-key"), r.post_data))
                     if r.method == "POST" and r.url.endswith("/reservations") else None)
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"), state="visible")
        ref = self.text("confirmation-reference")
        self.assertRegex(ref, REF)
        got = self.reservations()
        self.assertEqual([g["reference"] for g in got], [ref])
        b = got[0]
        self.assertEqual((b["table_ids"], b["party_size"], b["starts_at_local"]), (["t_2"], 3, T))
        self.assertEqual(self.text("confirmation-reference"), ref)
        det = self.text("confirmation-details")
        for s in ("Zum Anker", "Booth", "19:00"):
            self.assertIn(s, det)
        self.assertIn("Booth", self.text("confirmation-tables"))
        self.assertTrue(self.visible("booking-form"), "form stays on screen after success")
        self.assertEqual(self.count("booking-error"), 0)
        # unchanged resubmission: same reference, no second booking, no error
        self.page.click(tid("booking-submit"))
        self.pump(self.page, 800)
        self.assertEqual(self.text("confirmation-reference"), ref)
        self.assertEqual(self.count("booking-error"), 0)
        self.assertEqual(len(self.reservations()), 1)
        if len(reqs) > 1:
            self.assertEqual(reqs[1][2], reqs[0][2], "retry must reuse the idempotency key")
            self.assertEqual(reqs[1][3], reqs[0][3], "retry must reuse the body")
        self.assertTrue(reqs and reqs[0][2], "first booking request carries an Idempotency-Key")
        self.assertEqual(self.external, [])

    def test_L146_changed_field_is_a_new_request_with_a_new_key(self):
        self.open_form("t_2-19:00", 3)
        reqs = []
        self.page.on("request", lambda r: reqs.append((r.headers.get("idempotency-key"), r.post_data))
                     if r.method == "POST" and r.url.endswith("/reservations") else None)
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"))
        ref1 = self.text("confirmation-reference")
        self.page.fill(tid("booking-party-size"), "4")
        self.page.click(tid("booking-submit"))
        self.pump(self.page, 800)
        self.assertGreaterEqual(len(reqs), 2)
        self.assertNotEqual(reqs[0][0], reqs[-1][0], "a changed field needs a new idempotency key")
        import json
        self.assertEqual(json.loads(reqs[-1][1])["party_size"], 4)
        # server: the table is taken by the first booking, so the new request is refused, nothing duplicated
        self.assertEqual(len(self.reservations()), 1)
        self.assertTrue(self.visible("booking-error"))

    def test_L134_L144_party_size_and_error_absent_until_refusal(self):
        self.open_form("t_3-19:00", 4)
        self.assertEqual(self.page.input_value(tid("booking-party-size")), "4")
        self.assertEqual(self.count("booking-error"), 0)

    def test_L119_L148_L151_combined_booking_flow_and_lookup(self):
        self.open_form("t_1+t_2-19:00", 5)
        summary = self.text("booking-summary")
        for s in ("Window", "Booth", "19:00"):
            self.assertIn(s, summary)
        self.assertNotRegex(summary, r"t_\d")
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"), state="visible")
        ref = self.text("confirmation-reference")
        self.assertRegex(ref, REF)
        for s in ("Window", "Booth"):
            self.assertIn(s, self.text("confirmation-tables"))
            self.assertIn(s, self.text("confirmation-details"))
        b = self.reservations()[0]
        self.assertEqual((sorted(b["table_ids"]), b["party_size"], b["reference"]), (["t_1", "t_2"], 5, ref))
        self.assertNotIn("table_id", b)
        self.search("r_anker", THU, 1)
        c = self.cells()
        for k in ("slot-t_1-19:00", "slot-t_2-19:00", "slot-t_1+t_2-19:00", "slot-t_2+t_3-19:00"):
            self.assertEqual(c.get(k, "false"), "false", k)
        self.assertEqual(c["slot-t_3-19:00"], "true")
        self.goto("/lookup")
        self.page.fill(tid("lookup-reference-input"), ref)
        self.page.click(tid("lookup-submit"))
        self.page.wait_for_selector(tid("reservation-detail"), state="visible")
        self.assertEqual(self.text("reservation-status"), "confirmed")
        for s in ("Window", "Booth"):
            self.assertIn(s, self.text("reservation-tables"))
        self.page.click(tid("reservation-cancel-button"))
        self.page.wait_for_function("() => document.querySelector(\"[data-testid='reservation-status']\").innerText.trim() === 'cancelled'")
        self.assertEqual(self.count("reservation-cancel-button"), 0)
        self.assertEqual(self.api.call("GET", f"/reservations/{ref}", token=self.ada).json["status"], "cancelled")
        self.assertEqual(self.avail("r_anker", THU, 1)["slots"][2]["available_table_ids"], ["t_1", "t_2", "t_3"])

    def test_L176_single_table_ids_and_cells_unchanged(self):
        self.open_form("t_3-21:00", 2)
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"))
        self.assertIn("Terrace", self.text("confirmation-tables"))
        b = self.reservations()[0]
        self.assertEqual((b["table_id"], b["table_ids"]), ("t_3", ["t_3"]))

    # ---------------------------------------------------------------- 409 recovery
    def test_L121_conflict_shows_error_refreshes_and_preserves_form(self):
        self.open_form("t_2-19:00", 3)
        self.ok_book(self.bob, T, table="t_2", party=2)                       # another client takes it
        self.page.fill(tid("booking-party-size"), "4")
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("booking-error"), state="visible")
        self.assertTrue(self.text("booking-error"))
        self.assertEqual(self.count("confirmation"), 0)
        self.assertEqual(self.count("booking-uncertain"), 0)
        self.assertTrue(self.visible("booking-form"))
        self.assertEqual(self.page.input_value(tid("booking-party-size")), "4", "inputs preserved")
        self.assertIn("Booth", self.text("booking-summary"))
        self.assertEqual(self.reservations(), [])
        # availability was refreshed: the cell is now unavailable without a new search
        self.page.wait_for_function("() => { const e = document.querySelector(\"[data-testid='slot-t_2-19:00']\");"
                                    " return e && e.getAttribute('data-available') === 'false'; }")
        # the diner can change their choice
        self.click_cell("t_3-19:00")
        self.pump()
        self.assertIn("Terrace", self.text("booking-summary"))

    def test_L121_L124_conflict_on_one_member_of_a_pair(self):
        self.open_form("t_1+t_2-19:00", 5)
        self.ok_book(self.bob, f"{THU}T19:30", table="t_2", party=2)          # overlaps one member only
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("booking-error"), state="visible")
        self.assertEqual(self.count("confirmation"), 0)
        self.assertEqual(self.reservations(), [])
        self.assertIn("Window", self.text("booking-summary"))
        self.assertIn("Booth", self.text("booking-summary"))
        self.assertEqual(self.page.input_value(tid("booking-party-size")), "5")
        self.page.wait_for_function("() => { const e = document.querySelector(\"[data-testid='slot-t_1+t_2-19:00']\");"
                                    " return !e || e.getAttribute('data-available') === 'false'; }")
        self.assertEqual(self.cells().get("slot-t_3-19:00"), "true")           # t_3 (6 seats) is untouched
        self.assertEqual(self.cells().get("slot-t_1-19:00"), "false")          # t_1 is free but too small for 5

    # ---------------------------------------------------------------- lost responses
    def lost_flow(self, ident, party, mode):
        self.open_form(ident, party)
        st = self.lose_booking_responses(mode=mode)
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("booking-uncertain"), state="visible")
        return st

    def check_uncertain_state(self):
        self.assertTrue(self.text("booking-uncertain"))
        self.assertEqual(self.count("booking-error"), 0)
        self.assertEqual(self.count("confirmation"), 0)
        self.assertTrue(self.visible("booking-form"))
        self.assertTrue(self.visible("booking-submit"))

    def test_L122_L123_lost_before_commit_then_retry_same_key_and_body(self):
        st = self.lost_flow("t_2-19:00", 3, "lose-before")
        self.check_uncertain_state()
        self.assertEqual(self.reservations(), [])
        key, body, _ = st["attempts"][0]
        self.assertTrue(key)
        st["mode"] = "pass"
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"), state="visible")
        self.assertEqual(st["attempts"][-1][:2], (key, body), "retry must reuse the same key and body")
        self.assertEqual(self.count("booking-uncertain"), 0)
        self.assertEqual(self.count("booking-error"), 0)
        got = self.reservations()
        self.assertEqual(len(got), 1)
        self.assertEqual(self.text("confirmation-reference"), got[0]["reference"])

    def test_L122_L123_lost_after_commit_retry_recovers_original_reference(self):
        st = self.lost_flow("t_2-19:00", 3, "lose-after")
        self.check_uncertain_state()
        committed = self.reservations()
        self.assertEqual(len(committed), 1, "the lost request did commit on the server")
        key, body, _ = st["attempts"][0]
        st["mode"] = "pass"
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"), state="visible")
        self.assertEqual(st["attempts"][-1][:2], (key, body))
        self.assertEqual(self.text("confirmation-reference"), committed[0]["reference"])
        self.assertEqual(self.count("booking-uncertain") + self.count("booking-error"), 0)
        self.assertEqual(len(self.reservations()), 1, "retry must not create a second booking")
        self.assertIn("Booth", self.text("confirmation-tables"))

    def test_L123_L190_pending_identity_in_session_storage(self):
        st = self.lost_flow("t_2-19:00", 3, "lose-after")
        key = st["attempts"][0][0]
        self.assertIn(key, self.storage_dump(), "pending idempotency key must be held in session storage")

    def test_L124_lost_responses_for_combined_booking(self):
        for mode in ("lose-before", "lose-after"):
            self.reset()
            self.ctx.clear_cookies()
            st = self.lost_flow("t_1+t_2-19:00", 5, mode)
            self.check_uncertain_state()
            self.assertIn("Window", self.text("booking-summary"))
            self.assertIn("Booth", self.text("booking-summary"))
            committed = self.reservations()
            self.assertEqual(len(committed), 1 if mode == "lose-after" else 0, st.get("fetched"))
            key, body, _ = st["attempts"][0]
            self.assertIn("table_ids", body)
            st["mode"] = "pass"
            self.page.click(tid("booking-submit"))
            self.page.wait_for_selector(tid("confirmation"), state="visible")
            self.assertEqual(st["attempts"][-1][:2], (key, body))
            got = self.reservations()
            self.assertEqual(len(got), 1, mode)
            self.assertEqual(sorted(got[0]["table_ids"]), ["t_1", "t_2"])
            self.assertEqual(self.text("confirmation-reference"), got[0]["reference"])
            for s in ("Window", "Booth"):
                self.assertIn(s, self.text("confirmation-tables"))
            self.assertEqual(self.count("booking-uncertain") + self.count("booking-error"), 0)

    def test_L123_retry_rejected_after_loss_uses_booking_error(self):
        st = self.lost_flow("t_2-19:00", 3, "lose-before")
        self.ok_book(self.bob, T, table="t_2", party=2)
        st["mode"] = "pass"
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("booking-error"), state="visible")
        self.assertEqual(self.count("confirmation"), 0)
        self.assertEqual(self.count("booking-uncertain"), 0, "a confirmed rejection resolves the uncertainty")
        self.assertEqual(self.reservations(), [])

    def test_L146_changing_form_after_uncertainty_gets_new_key(self):
        st = self.lost_flow("t_2-19:00", 3, "lose-before")
        first_key = st["attempts"][0][0]
        st["mode"] = "pass"
        self.page.fill(tid("booking-party-size"), "2")
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"), state="visible")
        self.assertNotEqual(st["attempts"][-1][0], first_key)
        self.assertEqual(len(self.reservations()), 1)
        self.assertEqual(self.reservations()[0]["party_size"], 2)

    def test_L122_server_error_is_not_a_success(self):
        self.open_form("t_2-19:00", 3)

        def h(route):
            route.fulfill(status=500, content_type="application/json",
                          body='{"error":{"code":"internal","message":"boom"}}')
        self.page.route("**/reservations", lambda r: h(r) if r.request.method == "POST" else r.continue_())
        self.page.click(tid("booking-submit"))
        self.pump(self.page, 800)
        self.assertEqual(self.count("confirmation"), 0)
        self.assertTrue(self.visible("booking-error") or self.visible("booking-uncertain"))
        self.assertEqual(self.reservations(), [])

    # ---------------------------------------------------------------- out of order
    def test_L120_late_search_never_restores_old_grid(self):
        self.goto("/")
        st = self.hold_availability(2)
        self.search("r_anker", THU, 2, wait=False)            # A (held)
        self.page.wait_for_function("() => true")
        self.pump(self.page, 400)
        self.page.fill(tid("party-size-input"), "5")
        self.page.click(tid("search-button"))                  # B finishes first
        self.page.wait_for_selector(tid("availability-grid"), state="visible")
        self.assert_grid_matches("r_anker", THU, 5)
        before = self.cells()
        self.release(st)                                       # A arrives late
        self.assertEqual(self.cells(), before, "late response restored stale results")
        self.assert_grid_matches("r_anker", THU, 5)
        self.assertEqual(self.cells()["slot-t_1-19:00"], "false")

    def test_L120_late_search_for_other_restaurant_keeps_labels_and_form(self):
        self.ui_login()
        self.goto("/")
        st = self.hold_availability(3)
        self.search("r_other", THU, 3, wait=False)             # A: other restaurant (held)
        self.pump(self.page, 400)
        self.page.select_option(tid("restaurant-select"), "r_anker")
        self.page.fill(tid("party-size-input"), "2")
        self.page.click(tid("search-button"))                  # B
        self.page.wait_for_selector(tid("availability-grid"), state="visible")
        self.click_cell("t_2-19:00")
        self.page.wait_for_selector(tid("booking-form"))
        summary = self.text("booking-summary")
        self.release(st)
        self.assertEqual(self.text("booking-summary"), summary)
        self.assertEqual(self.page.input_value(tid("booking-party-size")), "2")
        grid = self.page.inner_text(tid("availability-grid"))
        for stale in ("Garden", "Bar"):
            self.assertNotIn(stale, grid)
        self.assertEqual(self.count("slot-t_9-12:00"), 0)
        self.assert_grid_matches("r_anker", THU, 2)
        self.assertEqual(self.page.input_value(tid("restaurant-select")), "r_anker")
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"))
        self.assertEqual(self.reservations()[0]["restaurant_id"], "r_anker")

    def test_L124_late_search_with_combination_cells(self):
        self.goto("/")
        st = self.hold_availability(1)
        self.search("r_anker", THU, 1, wait=False)            # A: everything incl. both pairs bookable
        self.pump(self.page, 400)
        self.page.fill(tid("party-size-input"), "8")
        self.page.click(tid("search-button"))                  # B: only t_2+t_3 (10 seats)
        self.page.wait_for_selector(tid("availability-grid"), state="visible")
        before = self.cells()
        self.assertEqual(before.get("slot-t_2+t_3-19:00"), "true")
        self.assertEqual(before.get("slot-t_1+t_2-19:00", "false"), "false")
        self.release(st)
        self.assertEqual(self.cells(), before)

    def test_L120_late_search_error_is_ignored(self):
        self.goto("/")
        st = self.hold_availability(2)
        self.search("r_anker", THU, 2, wait=False)
        self.pump(self.page, 300)
        self.page.fill(tid("party-size-input"), "4")
        self.page.click(tid("search-button"))
        self.page.wait_for_selector(tid("availability-grid"), state="visible")
        before = self.cells()
        for r in st["held"]:
            r.fulfill(status=500, content_type="application/json", body='{"error":{"code":"x","message":"late failure"}}')
        st["held"] = []
        self.pump(self.page, 800)
        self.assertEqual(self.cells(), before)
        self.assertTrue(self.visible("availability-grid"))


class Lookup(BrowserBase):
    def lookup(self, ref):
        self.goto("/lookup")
        self.page.fill(tid("lookup-reference-input"), ref)
        self.page.click(tid("lookup-submit"))

    def test_L149_L150_L151_lookup_found_cancel_and_errors(self):
        a = self.ok_book(self.ada, T, table="t_2", party=2)
        self.ui_login()
        self.lookup(a["reference"])
        self.page.wait_for_selector(tid("reservation-detail"), state="visible")
        self.assertEqual(self.text("reservation-status"), "confirmed")
        self.assertIn("Booth", self.text("reservation-tables"))
        self.assertEqual(self.count("reservation-error"), 0)
        self.assertTrue(self.visible("reservation-cancel-button"))
        self.page.click(tid("reservation-cancel-button"))
        self.page.wait_for_function("() => document.querySelector(\"[data-testid='reservation-status']\").innerText.trim() === 'cancelled'")
        self.assertEqual(self.count("reservation-cancel-button"), 0)
        self.assertEqual(self.api.call("GET", f"/reservations/{a['reference']}", token=self.ada).json["status"], "cancelled")
        # cancelled booking looked up again: no cancel button
        self.lookup(a["reference"])
        self.page.wait_for_selector(tid("reservation-detail"))
        self.assertEqual(self.text("reservation-status"), "cancelled")
        self.assertEqual(self.count("reservation-cancel-button"), 0)

    def test_L150_not_found_and_other_users_booking(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        self.ui_login()
        self.lookup("NOSUCH99")
        self.page.wait_for_selector(tid("reservation-error"), state="visible")
        self.assertTrue(self.text("reservation-error"))
        self.assertEqual(self.count("reservation-detail"), 0)
        self.lookup(a["reference"])
        self.page.wait_for_selector(tid("reservation-error"), state="visible")
        self.assertEqual(self.count("reservation-detail"), 0)
        self.assertNotIn("Booth", self.page.content().replace("data-testid", ""))

    def test_L150_cancel_refused_after_cutoff_shows_error(self):
        self.reset(fixture2(reservations=[seed_res(1, "u_ada", "r_anker", "t_2", "2020-01-02T19:00", 2, "PASTBOOK")]))
        self.ui_login()
        self.lookup("PASTBOOK")
        self.page.wait_for_selector(tid("reservation-detail"))
        self.page.click(tid("reservation-cancel-button"))
        self.page.wait_for_selector(tid("reservation-error"), state="visible")
        self.assertEqual(self.text("reservation-status"), "confirmed")
        self.assertEqual(self.api.call("GET", "/reservations/PASTBOOK", token=self.ada).json["status"], "confirmed")

    def test_L149_lookup_when_signed_out_shows_error_not_booking(self):
        a = self.ok_book(self.ada, T, table="t_2", party=2)
        self.lookup(a["reference"])
        self.page.wait_for_selector(f"{tid('reservation-error')}, {tid('reservation-detail')}")
        self.assertEqual(self.count("reservation-detail"), 0, "a signed-out visitor must not see someone's booking")
        self.assertTrue(self.visible("reservation-error"))

    def test_L149_L151_seeded_pair_and_cancelled_lookup(self):
        pair = dict(seed_res(1, "u_ada", "r_anker", "t_1", T, 5, "PAIRSEED1"), table_ids=["t_2", "t_3"])
        pair.pop("table_id")
        cancelled = dict(seed_res(2, "u_ada", "r_anker", "t_1", f"{THU}T21:00", 2, "CNCLSEED1"), status="cancelled")
        self.reset(fixture2(reservations=[pair, cancelled]))
        self.ui_login()
        self.lookup("PAIRSEED1")
        self.page.wait_for_selector(tid("reservation-detail"))
        for s in ("Booth", "Terrace"):
            self.assertIn(s, self.text("reservation-tables"))
        self.assertEqual(self.text("reservation-status"), "confirmed")
        self.lookup("CNCLSEED1")
        self.page.wait_for_selector(tid("reservation-detail"))
        self.assertEqual(self.text("reservation-status"), "cancelled")
        self.assertEqual(self.count("reservation-cancel-button"), 0)
        self.assertIn("Window", self.text("reservation-tables"))
