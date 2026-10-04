"""Same-tab upgrade across a real stage-3 -> stage-4 migration (ledger 344, 343, 341).

One browser tab stays open on one origin (a same-origin forwarding proxy owned by this test). Before the upgrade the proxy
sends API calls to the ACTUAL frozen stage-3 process; UI assets come from a stage-4 process. Then: export from stage 3, STOP
stage 3 (port closed), start an independent stage-4 destination, import, and only then point the proxy at it. The tab is never
reloaded. Exports stay in memory.
"""
import json
import re
import urllib.parse
import unittest

from playwright.sync_api import sync_playwright

from browser_helpers import launch, tid, TIMEOUT
from s4common import (Api, FROZEN_STAGE3, STAGE4_DIR, THU, T, fixture3, start_at, stop_process, wait_port_closed, inst)
from test_s3_upgrade_browser import Proxy
import test_s3_upgrade_browser as base

base.API_PREFIXES = base.API_PREFIXES + ("/series",)


class UpgradeBrowser4(unittest.TestCase):
    def test_L344_L343_L341_browser_survives_real_stage3_to_stage4_upgrade(self):
        s3_base, s3_proc, s3_port = start_at(FROZEN_STAGE3)
        ui_base, ui_proc, ui_port = start_at(STAGE4_DIR)
        s3 = Api(s3_base)
        self.assertEqual(s3.call("POST", "/_test/reset", fixture3()).status, 204)
        proxy = Proxy(ui_port, s3_port)
        pbase = f"http://127.0.0.1:{proxy.port}"
        procs = [s3_proc, ui_proc]
        pw = sync_playwright().start()
        try:
            browser = launch(pw)
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            ctx.set_default_timeout(TIMEOUT)
            page = ctx.new_page()
            external = []
            page.on("request", lambda r: external.append(r.url) if urllib.parse.urlparse(r.url).hostname not in ("127.0.0.1", "localhost") else None)
            page.goto(pbase + "/login")
            page.fill(tid("login-email"), "ada@example.com")
            page.fill(tid("login-password"), "correct horse")
            page.click(tid("login-submit"))
            page.wait_for_selector(tid("current-user"))
            sess = json.loads(page.evaluate("() => JSON.stringify(Object.assign({}, sessionStorage))"))
            token = None
            for v in sess.values():
                for cand in re.findall(r"[A-Za-z0-9_\-\.]{16,}", str(v)):
                    if s3.call("GET", "/reservations", token=cand).status == 200:
                        token = cand
            self.assertIsNotNone(token, "browser holds no valid stage-3 token")

            def open_form(ident, party):
                page.goto(pbase + "/")
                page.select_option(tid("restaurant-select"), "r_anker")
                page.fill(tid("date-input"), THU)
                page.fill(tid("party-size-input"), str(party))
                page.click(tid("search-button"))
                page.wait_for_selector(tid("availability-grid"))
                page.click(tid(f"slot-{ident}"))
                page.wait_for_selector(tid("booking-form"))
            open_form("t_3-19:00", 3)
            seen = []
            page.on("response", lambda resp: seen.append((resp.request.headers.get("idempotency-key"), resp.status, resp.body(), resp.request.post_data))
                    if resp.request.method == "POST" and urllib.parse.urlparse(resp.url).path == "/reservations" else None)
            page.click(tid("booking-submit"))
            page.wait_for_selector(tid("confirmation"))
            ref = page.inner_text(tid("confirmation-reference")).strip()
            key1, status1, body1, post1 = seen[-1]
            self.assertEqual(status1, 201)
            original = json.loads(body1)

            # a second booking whose response is lost AFTER stage 3 committed it
            open_form("t_2-19:00", 2)
            lost = {"attempts": [], "mode": "lose-after"}

            def lose(route):
                req = route.request
                if req.method == "POST" and urllib.parse.urlparse(req.url).path == "/reservations":
                    lost["attempts"].append((req.headers.get("idempotency-key"), req.post_data))
                    if lost["mode"] == "lose-after":
                        route.fetch()
                        route.abort("failed")
                        return
                route.continue_()
            page.route("**/reservations", lose)
            page.click(tid("booking-submit"))
            page.wait_for_selector(tid("booking-uncertain"))
            pend_key, pend_body = lost["attempts"][0]
            lost["mode"] = "pass"
            before_url = page.url
            summary = page.inner_text(tid("booking-summary"))

            # stage-3 state: a series with a cancelled member and a published policy, all made directly through the API
            bob = s3.call("POST", "/auth/login", {"email": "bob@example.com", "password": "battery staple"}).json["token"]
            first = s3.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_1", "starts_at_local": f"{THU}T20:00",
                                                       "party_size": 2}, token=bob, key="s3-series-first")
            self.assertEqual(first.status, 201, first.raw)
            series = s3.call("POST", f"/reservations/{first.json['reference']}/series", {"count": 3, "interval_weeks": 1}, token=bob,
                             key="s3-series-adopt")
            self.assertEqual(series.status, 201, series.raw)
            export = s3.call("GET", "/_test/export").json                       # private, memory only

            stop_process(s3_proc)
            self.assertTrue(wait_port_closed(s3_port) and s3_proc.poll() is not None, "frozen stage 3 must be stopped before import")
            dst_base, dst_proc, dst_port = start_at(STAGE4_DIR)
            procs.append(dst_proc)
            d = Api(dst_base)
            self.assertEqual(d.call("POST", "/_test/import", export).status, 204)
            proxy.api_port = dst_port                                           # same tab, same origin, new backend

            self.assertEqual(page.url, before_url)
            self.assertTrue(page.is_visible(tid("booking-form")))
            self.assertEqual(page.inner_text(tid("booking-summary")), summary)
            self.assertIn("Ada", page.inner_text(tid("current-user")))
            self.assertEqual(d.call("GET", "/reservations", token=token).status, 200, "pre-upgrade token still valid")
            committed = [x for x in d.call("GET", "/reservations", token=token).json["reservations"]
                         if x["starts_at_local"] == T and x.get("table_id", (x.get("table_ids") or [None])[0]) == "t_2"]
            self.assertEqual(len(committed), 1, "the lost-response booking exists exactly once after import")
            page.click(tid("booking-submit"))                                   # retry: same key and body
            page.wait_for_selector(tid("confirmation"))
            self.assertEqual(lost["attempts"][-1], (pend_key, pend_body))
            self.assertEqual(page.inner_text(tid("confirmation-reference")).strip(), committed[0]["reference"])
            self.assertEqual(len([x for x in d.call("GET", "/reservations", token=token).json["reservations"] if x["starts_at_local"] == T
                                  and x["reference"] != ref and x["restaurant_id"] == "r_anker" and "t_2" in (x.get("table_ids") or [x.get("table_id")])]), 1)

            page.goto(pbase + "/lookup")
            self.assertIn("Ada", page.inner_text(tid("current-user")))
            page.fill(tid("lookup-reference-input"), ref)
            page.click(tid("lookup-submit"))
            page.wait_for_selector(tid("reservation-detail"))
            self.assertEqual(page.inner_text(tid("reservation-status")).strip(), "confirmed")
            self.assertEqual(external, [])

            # receipts and the series replay exactly; the old stage-3 reservation JSON is unchanged
            r = d.call("POST", "/reservations", json.loads(post1), token=token, key=key1)
            self.assertEqual((r.status, r.json), (200, original))
            r = d.call("POST", f"/reservations/{first.json['reference']}/series", {"count": 3, "interval_weeks": 1}, token=bob, key="s3-series-adopt")
            self.assertEqual((r.status, r.json), (200, series.json))
            # stage-4 behaviour on the imported state: preview and amend work through the new backend
            p = d.call("POST", "/restaurants/r_anker/replans", {"table_id": "t_2", "from": inst(THU, "18:00"), "to": inst(THU, "23:00")},
                       token=token, key="s4-first-plan")
            self.assertEqual(p.status, 201, p.raw)
            am = d.call("POST", f"/series/{series.json['series_id']}/amend",
                        {"expected_revision": series.json["revision"], "from_index": 1, "local_time": "21:00"}, token=bob, key="s4-first-amend")
            self.assertEqual(am.status, 201, am.raw)
            ctx.close()
            browser.close()
        finally:
            pw.stop()
            proxy.stop()
            for p in procs:
                if p.poll() is None:
                    p.kill()
