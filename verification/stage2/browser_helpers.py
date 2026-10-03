"""Playwright helpers for the stage 2 browser checks (run with the harness interpreter; nothing is installed)."""
import glob
import json
import os
import re
import urllib.parse

from playwright.sync_api import sync_playwright

from s2common import Base2, SHOT_DIR, THU, base_url

PHONE = {"width": 375, "height": 812}
DESKTOP = {"width": 1280, "height": 900}
TIMEOUT = 8000


def chromium_path():
    """The installed Chromium (the supplied Playwright build may not match the downloaded revision)."""
    env = os.environ.get("CHROMIUM_PATH")
    if env:
        return env
    root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or os.path.expanduser("~/AppData/Local/ms-playwright")
    found = sorted(glob.glob(os.path.join(root, "chromium-*", "chrome-win*", "chrome.exe")) +
                   glob.glob(os.path.join(root, "chromium-*", "chrome-linux*", "chrome")))
    return found[-1] if found else None


def launch(pw):
    path = chromium_path()
    try:
        return pw.chromium.launch()
    except Exception:
        if not path:
            raise
        return pw.chromium.launch(executable_path=path)


def tid(name):
    return f"[data-testid='{name}']"


def hhmm(local):
    return local[11:16]


class BrowserBase(Base2):
    pw = None
    browser = None
    viewport = DESKTOP

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base = base_url(1)
        cls.pw = sync_playwright().start()
        cls.browser = launch(cls.pw)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.browser.close()
        finally:
            cls.pw.stop()

    def setUp(self):
        super().setUp()
        self.ctx = self.browser.new_context(viewport=self.viewport)
        self.ctx.set_default_timeout(TIMEOUT)
        self.external = []
        self.console_errors = []
        self.page = self.new_page()

    def tearDown(self):
        self.ctx.close()

    def new_page(self):
        page = self.ctx.new_page()
        page.on("request", self._watch)
        page.on("pageerror", lambda e: self.console_errors.append(str(e)))
        return page

    def _watch(self, req):
        u = urllib.parse.urlparse(req.url)
        if u.scheme in ("http", "https") and u.hostname not in ("127.0.0.1", "localhost"):
            self.external.append(req.url)

    # ------------------------------------------------------------ actions
    def goto(self, path, page=None):
        page = page or self.page
        page.goto(self.base + path)
        page.wait_for_load_state("load")

    def ui_login(self, email="ada@example.com", pw="correct horse", page=None):
        page = page or self.page
        self.goto("/login", page)
        page.fill(tid("login-email"), email)
        page.fill(tid("login-password"), pw)
        page.click(tid("login-submit"))
        page.wait_for_selector(tid("current-user"), state="visible")

    def search(self, rest="r_anker", date=THU, party=2, page=None, wait=True):
        page = page or self.page
        if urllib.parse.urlparse(page.url).path != "/":
            self.goto("/", page)
        page.wait_for_selector(tid("restaurant-select"), state="visible")
        page.select_option(tid("restaurant-select"), rest)
        page.fill(tid("date-input"), date)
        page.fill(tid("party-size-input"), str(party))
        page.click(tid("search-button"))
        if wait:
            self.wait_results(page)

    def wait_results(self, page=None):
        page = page or self.page
        page.wait_for_selector(f"{tid('availability-grid')}, {tid('no-slots')}", state="visible")

    def cells(self, page=None):
        page = page or self.page
        rows = page.eval_on_selector_all("[data-testid^='slot-']",
                                         "els => els.map(e => [e.getAttribute('data-testid'), e.getAttribute('data-available')])")
        return {k: v for k, v in rows}

    def expected_cells(self, rest, date, party, with_pairs=True):
        """What the grid must show according to GET /availability for exactly these parameters."""
        j = self.avail(rest, date, party)
        r = self.api.call("GET", f"/restaurants/{rest}").json
        exp, pairs = {}, {}
        for s in j["slots"]:
            t = hhmm(s["starts_at_local"])
            for tb in r["tables"]:
                exp[f"slot-{tb['id']}-{t}"] = "true" if tb["id"] in s["available_table_ids"] else "false"
            free = {tuple(o["table_ids"]) for o in s.get("available_options", [])}
            for a, b in r.get("combinable", []):
                pairs[f"slot-{a}+{b}-{t}"] = "true" if (a, b) in free else "false"
        return exp, pairs

    def assert_grid_matches(self, rest, date, party):
        self.wait_results()
        exp, pairs = self.expected_cells(rest, date, party)
        got = self.cells()
        singles = {k: v for k, v in got.items() if "+" not in k}
        self.assertEqual(singles, exp)
        for k, v in got.items():
            if "+" in k:
                self.assertIn(k, pairs, f"unknown combination cell {k}")
                self.assertEqual(v, pairs[k], k)
        for k, v in pairs.items():
            if v == "true":
                self.assertIn(k, got, f"available combination {k} must be shown")

    def click_cell(self, ident, page=None):
        page = page or self.page
        page.click(tid(f"slot-{ident}"))

    def text(self, name, page=None):
        return (page or self.page).inner_text(tid(name)).strip()

    def count(self, name, page=None):
        return (page or self.page).locator(tid(name)).count()

    def visible(self, name, page=None):
        loc = (page or self.page).locator(tid(name))
        return loc.count() > 0 and loc.first.is_visible()

    def storage_dump(self, page=None):
        page = page or self.page
        return page.evaluate("() => JSON.stringify({s: Object.assign({}, sessionStorage), l: Object.assign({}, localStorage)})")

    def shot(self, name, page=None):
        page = page or self.page
        w = page.viewport_size["width"]
        page.screenshot(path=os.path.join(SHOT_DIR, f"{self._testMethodName}-{name}-{w}.png"), full_page=True)

    # ------------------------------------------------------------ network tricks
    def lose_booking_responses(self, page=None, mode="lose-before"):
        """Intercept POST /reservations. mode: lose-before (request dropped), lose-after (server commits, response
        lost), pass. Returns state with `attempts` [(key, body)]."""
        page = page or self.page
        state = {"mode": mode, "attempts": []}

        def handler(route):
            req = route.request
            if req.method == "POST" and urllib.parse.urlparse(req.url).path == "/reservations":
                state["attempts"].append((req.headers.get("idempotency-key"), req.post_data, state["mode"]))
                if state["mode"] == "lose-after":
                    route.fetch()
                    route.abort("failed")
                    return
                if state["mode"] == "lose-before":
                    route.abort("failed")
                    return
            route.continue_()

        page.route("**/reservations", handler)
        return state

    def hold_availability(self, hold_party, page=None):
        """Hold responses of GET /availability for the given party_size until released."""
        page = page or self.page
        state = {"held": [], "released": 0}

        def handler(route):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(route.request.url).query)
            if q.get("party_size", [""])[0] == str(hold_party) and not state.get("open"):
                state["held"].append(route)
            else:
                route.continue_()
        page.route("**/availability*", handler)
        return state

    def release(self, state, page=None):
        page = page or self.page
        state["open"] = True
        for r in state["held"]:
            r.continue_()
        state["released"] += len(state["held"])
        state["held"] = []
        page.wait_for_timeout(800)

    def pump(self, page=None, ms=300):
        (page or self.page).wait_for_timeout(ms)
