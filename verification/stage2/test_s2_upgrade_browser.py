"""Browser upgrade continuity across a real stage-1 -> stage-2 migration (ledger 152-155, 185, 190, 192, 194).

One browser tab stays open on one origin (a small same-origin forwarding proxy owned by this test). Before the upgrade the
proxy sends API calls to the frozen stage-1 process; the UI assets always come from a stage-2 process. Then the real
migration happens: export from stage 1, STOP stage 1, start an independent stage-2 destination, import, and only then
the proxy points API calls at the destination. The tab is never reloaded. Exports stay in memory.
"""
import http.client
import http.server
import json
import re
import threading
import unittest
import urllib.parse

from playwright.sync_api import sync_playwright

from browser_helpers import launch, tid, TIMEOUT
from s2common import (Api, STAGE1_DIR, STAGE2_DIR, THU, FRI, stage1_fixture, seed_res, start_at, stop_process, port_closed, wait_port_closed)

API_PREFIXES = ("/auth/", "/restaurants", "/availability", "/reservations", "/reservation-moves", "/health", "/_test/")
HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailers", "upgrade", "proxy-authorization", "host",
       "content-length"}
T = f"{THU}T19:00"


class Proxy:
    def __init__(self, ui_port, api_port):
        self.ui_port, self.api_port = ui_port, api_port
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def handle_any(self):
                path = urllib.parse.urlparse(self.path).path
                is_api = path.startswith(API_PREFIXES) and not (path in ("/", "/login", "/signup", "/lookup"))
                port = outer.api_port if is_api else outer.ui_port
                n = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(n) if n else None
                headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
                try:
                    c = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
                    c.request(self.command, self.path, body=body, headers=headers)
                    r = c.getresponse()
                    data = r.read()
                    self.send_response(r.status)
                    for k, v in r.getheaders():
                        if k.lower() not in HOP:
                            self.send_header(k, v)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    if self.command != "HEAD":
                        self.wfile.write(data)
                except Exception:
                    self.send_response(502)
                    self.send_header("Content-Length", "0")
                    self.end_headers()

            do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = handle_any

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def stop(self):
        self.server.shutdown()


class UpgradeBrowser(unittest.TestCase):
    def test_L152_L153_L154_L155_L190_L192_L194_browser_survives_real_upgrade(self):
        s1_base, s1_proc, s1_port = start_at(STAGE1_DIR)
        ui_base, ui_proc, ui_port = start_at(STAGE2_DIR)
        s1 = Api(s1_base)
        f = stage1_fixture(reservations=[seed_res(1, "u_bob", "r_anker", "t_1", f"{FRI}T18:00", 2, "BOBSEED1")])
        self.assertEqual(s1.call("POST", "/_test/reset", f).status, 204)
        proxy = Proxy(ui_port, s1_port)
        pbase = f"http://127.0.0.1:{proxy.port}"
        procs = [s1_proc, ui_proc]
        pw = sync_playwright().start()
        try:
            browser = launch(pw)
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            ctx.set_default_timeout(TIMEOUT)
            page = ctx.new_page()
            external = []
            page.on("request", lambda r: external.append(r.url) if urllib.parse.urlparse(r.url).hostname not in
                    ("127.0.0.1", "localhost") else None)
            # ---- pre-upgrade life with the stage-1 API behind the tab
            page.goto(pbase + "/login")
            page.fill(tid("login-email"), "ada@example.com")
            page.fill(tid("login-password"), "correct horse")
            page.click(tid("login-submit"))
            page.wait_for_selector(tid("current-user"))
            self.assertIn("Ada", page.inner_text(tid("current-user")))
            sess = json.loads(page.evaluate("() => JSON.stringify(Object.assign({}, sessionStorage))"))
            self.assertTrue(sess, "signed-in state must live in session storage")
            token = None
            for v in sess.values():
                for cand in re.findall(r"[A-Za-z0-9_\-\.]{16,}", str(v)):
                    if s1.call("GET", "/reservations", token=cand).status == 200:
                        token = cand
            self.assertIsNotNone(token, "browser holds no valid stage-1 token")

            # a booking made through the UI (retained reference)
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
            seen = {}

            def on_resp(resp):
                if resp.request.method == "POST" and urllib.parse.urlparse(resp.url).path == "/reservations":
                    seen.setdefault("responses", []).append((resp.request.headers.get("idempotency-key"), resp.status,
                                                             resp.request.post_data, resp.body()))
            page.on("response", on_resp)
            page.click(tid("booking-submit"))
            page.wait_for_selector(tid("confirmation"))
            retained_ref = page.inner_text(tid("confirmation-reference")).strip()
            self.assertRegex(retained_ref, r"^[A-Z0-9]{6,12}$")
            key1, status1, body1, resp1 = seen["responses"][-1]
            self.assertEqual(status1, 201)
            legacy_original = json.loads(resp1)
            self.assertNotIn("table_ids", legacy_original, "stage-1 backend answered with legacy shape")

            # a second booking whose response is lost AFTER the stage-1 server committed it
            open_form("t_2-19:00", 2)
            lost = {"attempts": [], "mode": "lose-after"}

            def lose(route):
                req = route.request
                if req.method == "POST" and urllib.parse.urlparse(req.url).path == "/reservations":
                    lost["attempts"].append((req.headers.get("idempotency-key"), req.post_data, lost["mode"]))
                    if lost["mode"] == "lose-after":
                        route.fetch()
                        route.abort("failed")
                        return
                route.continue_()
            page.route("**/reservations", lose)
            page.click(tid("booking-submit"))
            page.wait_for_selector(tid("booking-uncertain"))
            self.assertEqual(page.locator(tid("booking-error")).count(), 0)
            pend_key, pend_body, _ = lost["attempts"][0]
            self.assertIn(pend_key, page.evaluate("() => JSON.stringify(Object.assign({}, sessionStorage))"),
                          "pending retry identity must be in session storage")
            lost["mode"] = "pass"
            before_url = page.url
            form_party = page.input_value(tid("booking-party-size"))
            summary = page.inner_text(tid("booking-summary"))

            # stage-1 only side data: a direct create receipt and a batch receipt through the stage-1 API
            ada2 = s1.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).json["token"]
            cb = {"restaurant_id": "r_anker", "table_id": "t_1", "starts_at_local": f"{THU}T21:00", "party_size": 1}
            cr = s1.call("POST", "/reservations", cb, token=ada2, key="direct-create")
            cb2 = dict(cb, table_id="t_2")
            cr2 = s1.call("POST", "/reservations", cb2, token=ada2, key="direct-create-2")
            moves = {"moves": [{"reference": cr.json["reference"], "table_id": "t_2"}, {"reference": cr2.json["reference"], "table_id": "t_1"}]}
            batch = s1.call("POST", "/reservation-moves", moves, token=ada2, key="direct-moves")
            self.assertEqual((cr.status, cr2.status, batch.status), (201, 201, 201))
            export = s1.call("GET", "/_test/export").json                       # private, memory only

            # ---- the real migration: stop the source BEFORE importing
            stop_process(s1_proc)
            self.assertTrue(wait_port_closed(s1_port) and s1_proc.poll() is not None, "source must be stopped before import")
            dst_base, dst_proc, dst_port = start_at(STAGE2_DIR)
            procs.append(dst_proc)
            d = Api(dst_base)
            self.assertEqual(d.call("POST", "/_test/import", export).status, 204)
            proxy.api_port = dst_port                                            # same tab, same origin, new backend

            # ---- the tab, never reloaded
            self.assertEqual(page.url, before_url)
            self.assertTrue(page.is_visible(tid("booking-form")))
            self.assertEqual(page.input_value(tid("booking-party-size")), form_party)
            self.assertEqual(page.inner_text(tid("booking-summary")), summary)
            self.assertIn("Ada", page.inner_text(tid("current-user")))
            self.assertEqual(d.call("GET", "/reservations", token=token).status, 200, "pre-upgrade token still valid")
            committed = [x for x in d.call("GET", "/reservations", token=token).json["reservations"]
                         if x["starts_at_local"] == T and x["table_id"] == "t_2"]
            self.assertEqual(len(committed), 1, "the lost-response booking exists exactly once after import")
            page.click(tid("booking-submit"))                                    # retry: same unchanged form
            page.wait_for_selector(tid("confirmation"))
            self.assertEqual(lost["attempts"][-1][:2], (pend_key, pend_body), "retry must use the same key and body")
            self.assertEqual(page.inner_text(tid("confirmation-reference")).strip(), committed[0]["reference"])
            self.assertEqual(page.locator(tid("booking-uncertain")).count() + page.locator(tid("booking-error")).count(), 0)
            self.assertIn("Booth", page.inner_text(tid("confirmation-tables")))
            self.assertEqual(len([x for x in d.call("GET", "/reservations", token=token).json["reservations"]
                                  if x["starts_at_local"] == T and x["table_id"] == "t_2"]), 1, "no duplicate booking")
            self.assertIn("Ada", page.inner_text(tid("current-user")))          # still signed in

            # still signed in on other screens, a retained reference works in lookup
            page.goto(pbase + "/lookup")
            self.assertIn("Ada", page.inner_text(tid("current-user")))
            page.fill(tid("lookup-reference-input"), retained_ref)
            page.click(tid("lookup-submit"))
            page.wait_for_selector(tid("reservation-detail"))
            self.assertEqual(page.inner_text(tid("reservation-status")).strip(), "confirmed")
            self.assertIn("Terrace", page.inner_text(tid("reservation-tables")))
            # new searches and bookings work against the destination (pairs not declared in imported stage-1 config)
            page.goto(pbase + "/")
            page.select_option(tid("restaurant-select"), "r_anker")
            page.fill(tid("date-input"), THU)
            page.fill(tid("party-size-input"), "2")
            page.click(tid("search-button"))
            page.wait_for_selector(tid("availability-grid"))
            self.assertEqual(page.locator("[data-testid*='+']").count(), 0, "imported stage-1 restaurants have no pairs")
            self.assertEqual(page.locator(tid("slot-t_3-19:00")).get_attribute("data-available"), "false")
            self.assertEqual(external, [])

            # ---- receipts: original JSON preserved exactly (no regenerated table_ids)
            r = d.call("POST", "/reservations", json.loads(body1), token=token, key=key1)
            self.assertEqual(r.status, 200)
            self.assertEqual(r.json, legacy_original)
            r = d.call("POST", "/reservations", cb, token=ada2, key="direct-create")
            self.assertEqual((r.status, r.json), (200, cr.json))
            self.assertNotIn("table_ids", r.json)
            r = d.call("POST", "/reservation-moves", moves, token=ada2, key="direct-moves")
            self.assertEqual((r.status, r.json), (200, batch.json))
            self.assertTrue(all("table_ids" not in x for x in r.json["reservations"]))
            ctx.close()
            browser.close()
        finally:
            pw.stop()
            proxy.stop()
            for p in procs:
                if p.poll() is None:
                    p.kill()
