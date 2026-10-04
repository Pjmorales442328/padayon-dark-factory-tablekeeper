"""Stage 2 responsive / accessibility / visual-state checks at 375px and desktop width (ledger 126-133, 193).

Screenshots go to SHOT_DIR (outside the repository) as reviewable evidence.
"""
import json
import re

from axe_playwright_python.sync_playwright import Axe

from browser_helpers import BrowserBase, tid, PHONE, DESKTOP
from s2common import THU, SUN, fixture2, seed_res

T = f"{THU}T19:00"

LABEL_JS = """
() => {
  const bad = [];
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
                     return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  for (const el of document.querySelectorAll('input, select, textarea')) {
    if (el.type === 'hidden' || !vis(el)) continue;
    let ok = false;
    for (const l of (el.labels || [])) { if (vis(l) && l.innerText.trim()) ok = true; }
    const lb = el.getAttribute('aria-labelledby');
    if (!ok && lb) { for (const id of lb.split(/\\s+/)) { const t = document.getElementById(id); if (t && vis(t) && t.innerText.trim()) ok = true; } }
    if (!ok) bad.push(el.getAttribute('data-testid') || el.name || el.type);
  }
  return bad;
}
"""

STYLE_JS = """
(sel) => { const e = document.querySelector(sel); if (!e) return null; const s = getComputedStyle(e);
  return [s.backgroundColor, s.color, s.borderTopColor, s.borderTopWidth, s.borderTopStyle, s.opacity, s.textDecorationLine,
          s.fontWeight, s.boxShadow, s.outlineColor].join('|'); }
"""

FOCUS_JS = """
() => { const e = document.activeElement; if (!e || e === document.body) return null; const s = getComputedStyle(e);
  return {id: e.getAttribute('data-testid') || e.tagName, outline: s.outlineStyle + ' ' + s.outlineWidth, shadow: s.boxShadow,
          border: s.borderTopColor, bg: s.backgroundColor}; }
"""


class VisualChecks:
    def audit(self, name, axe=True):
        p = self.page
        self.shot(name)
        w = p.viewport_size["width"]
        sw = p.evaluate("() => Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0)")
        self.assertLessEqual(sw, w + 1, f"horizontal scroll at {w}px in state {name}: scrollWidth {sw}")
        self.assertEqual(p.evaluate(LABEL_JS), [], f"inputs without visible labels in {name}")
        if axe:
            res = Axe().run(p).response["violations"]
            bad = [(v["id"], v["impact"], len(v["nodes"])) for v in res if v["impact"] in ("serious", "critical")]
            self.assertEqual(bad, [], f"axe serious/critical violations in {name}")
        self.assertEqual(self.external, [])

    # ------------------------------------------------------------------ states
    def test_L131_L132_L133_L193_every_route_empty_state(self):
        for path in ("/", "/signup", "/login", "/lookup"):
            self.goto(path)
            self.audit("route" + path.replace("/", "_"))
            self.assertTrue(self.page.title().strip(), f"title on {path}")
            self.assertGreaterEqual(self.page.locator("h1, h2, [role=heading]").count(), 1, f"heading on {path}")
            self.assertEqual(self.page.locator("main, [role=main]").count() >= 1, True, f"main landmark on {path}")

    def test_L131_L193_search_grid_and_form_states(self):
        self.ui_login()
        self.search("r_anker", THU, 5)
        self.audit("grid")
        self.click_cell("t_1+t_2-19:00")
        self.page.wait_for_selector(tid("booking-form"))
        self.audit("form-pair")
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"))
        self.audit("confirmation")
        self.search("r_anker", SUN, 2)
        self.audit("no-slots")
        self.assertTrue(self.visible("no-slots"))

    def test_L129_available_unavailable_selected_states_look_different(self):
        self.ui_login()
        self.ok_book(self.bob, T, table="t_2", party=2)
        self.search("r_anker", THU, 2)
        free = self.page.evaluate(STYLE_JS, tid("slot-t_3-19:00"))
        busy = self.page.evaluate(STYLE_JS, tid("slot-t_2-19:00"))
        self.assertNotEqual(free, busy, "available and unavailable cells must be visually distinct")
        self.click_cell("t_3-19:00")
        self.page.wait_for_selector(tid("booking-form"))
        self.pump()
        selected = self.page.evaluate(STYLE_JS, tid("slot-t_3-19:00"))
        other = self.page.evaluate(STYLE_JS, tid("slot-t_3-20:30"))
        self.assertNotEqual(selected, other, "the selected cell must stand out from other available cells")
        self.assertNotEqual(selected, busy)
        self.audit("selected")

    def test_L129_L133_loading_state_is_visible_and_distinct(self):
        self.goto("/")
        st = self.hold_availability(2)
        self.search("r_anker", THU, 2, wait=False)
        self.pump(self.page, 500)
        found = self.page.evaluate("""() => {
            const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
            const busy = [...document.querySelectorAll('[aria-busy=true], [role=status], [role=progressbar], [data-loading], .loading, .spinner')].some(vis);
            const txt = [...document.querySelectorAll('body *')].some(e => vis(e) && e.children.length === 0 && /load|search|finding|checking|looking|wait/i.test(e.innerText || ''));
            return busy || txt; }""")
        self.assertTrue(found, "no visible loading indicator while the availability request is pending")
        self.shot("loading")
        self.release(st)
        self.wait_results()
        self.audit("after-loading")

    def test_L129_L133_conflict_uncertain_and_confirmation_are_three_different_looks(self):
        self.ui_login()
        self.search("r_anker", THU, 2)
        self.click_cell("t_2-19:00")
        self.page.wait_for_selector(tid("booking-form"))
        st = self.lose_booking_responses(mode="lose-before")
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("booking-uncertain"))
        uncertain = self.page.evaluate(STYLE_JS, tid("booking-uncertain"))
        self.audit("uncertain")
        st["mode"] = "pass"
        self.ok_book(self.bob, T, table="t_2", party=2)
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("booking-error"))
        error = self.page.evaluate(STYLE_JS, tid("booking-error"))
        self.audit("refused")
        self.click_cell("t_3-19:00")
        self.page.click(tid("booking-submit"))
        self.page.wait_for_selector(tid("confirmation"))
        ok = self.page.evaluate(STYLE_JS, tid("confirmation"))
        self.audit("success")
        self.assertEqual(len({uncertain, error, ok}), 3, "uncertain / refused / success must each look different")

    def test_L133_search_failure_shows_an_error_state(self):
        self.goto("/")
        marker = "Search service refused marker-7731"
        self.page.route("**/availability*", lambda r: r.fulfill(status=500, content_type="application/json",
                                                                 body='{"error":{"code":"x","message":"%s"}}' % marker))
        self.search("r_anker", THU, 2, wait=False)
        self.pump(self.page, 800)
        self.assertFalse(self.visible("availability-grid"))
        body = self.page.inner_text("body")
        alert = self.page.locator("[role=alert], [role=status]:visible, [data-testid*=error]:visible").count()
        # an error state means the diner is told: either the server's message is shown or a visible alert region exists
        self.assertTrue("marker-7731" in body or alert > 0, "search failure is silent: " + body[-200:])
        self.assertFalse(self.visible("no-slots") and "marker-7731" not in body and alert == 0,
                         "a failed search must not look like an empty day")
        self.audit("search-error", axe=False)

    def test_L133_lookup_states(self):
        a = self.ok_book(self.ada, T, table="t_2", party=2)
        self.ui_login()
        self.goto("/lookup")
        self.page.fill(tid("lookup-reference-input"), a["reference"])
        self.page.click(tid("lookup-submit"))
        self.page.wait_for_selector(tid("reservation-detail"))
        self.audit("lookup-found")
        self.page.fill(tid("lookup-reference-input"), "NOPE1234")
        self.page.click(tid("lookup-submit"))
        self.page.wait_for_selector(tid("reservation-error"))
        self.audit("lookup-error")

    def test_L132_L133_auth_error_states(self):
        self.goto("/login")
        self.page.fill(tid("login-email"), "ada@example.com")
        self.page.fill(tid("login-password"), "nope nope")
        self.page.click(tid("login-submit"))
        self.page.wait_for_selector(tid("auth-error"))
        self.audit("login-error")
        self.goto("/signup")
        self.page.fill(tid("signup-email"), "x@y.z")
        self.page.fill(tid("signup-password"), "short")
        self.page.fill(tid("signup-display-name"), "X")
        self.page.click(tid("signup-submit"))
        self.page.wait_for_selector(tid("auth-error"))
        self.audit("signup-error")

    def test_L132_keyboard_focus_is_visible_on_every_control(self):
        for path in ("/", "/login", "/lookup", "/signup"):
            self.goto(path)
            seen = 0
            for _ in range(14):
                self.page.keyboard.press("Tab")
                f = self.page.evaluate(FOCUS_JS)
                if not f:
                    continue
                seen += 1
                visible = ((f["outline"].split()[0] not in ("none", "hidden") and f["outline"].split()[1] != "0px")
                           or f["shadow"] != "none")
                self.assertTrue(visible, f"no visible focus indicator on {f['id']} at {path}: {f}")
            self.assertGreater(seen, 3, f"too few focusable controls reachable by keyboard on {path}")
        self.ui_login()
        self.search("r_anker", THU, 2)
        self.page.focus(tid("slot-t_2-19:00"))
        f = self.page.evaluate(FOCUS_JS)
        self.assertIsNotNone(f, "availability cells must be reachable by keyboard")

    def test_L126_L128_consistent_visual_system(self):
        self.ui_login()
        self.search("r_anker", THU, 2)
        info = self.page.evaluate("""() => {
          const fam = e => getComputedStyle(e).fontFamily;
          const btns = [...document.querySelectorAll('button')].filter(b => b.getBoundingClientRect().width > 0);
          const inputs = [...document.querySelectorAll('input, select')].filter(b => b.getBoundingClientRect().width > 0);
          const h = document.querySelector('h1, h2');
          return {body: fam(document.body), btn: [...new Set(btns.map(fam))], inp: [...new Set(inputs.map(fam))],
                  h: h ? fam(h) : null, bg: getComputedStyle(document.body).backgroundColor,
                  btnbg: [...new Set(btns.map(b => getComputedStyle(b).backgroundColor))],
                  minBtn: Math.min(...btns.map(b => b.getBoundingClientRect().height))}; }""")
        print("[measure] visual system", json.dumps(info), file=__import__("sys").stderr)
        self.assertNotRegex(info["body"].lower(), r"^(\"?times new roman\"?|serif)$", "default serif body font")
        self.assertEqual(len(info["btn"]), 1, "all buttons share one font family")
        self.assertEqual(info["btn"][0], info["body"], "buttons inherit the page typography")
        self.assertEqual(len(info["inp"]), 1, "inputs share one font family")
        self.assertNotEqual(info["btnbg"], ["rgb(239, 239, 239)"], "buttons are unstyled browser defaults")
        self.assertGreaterEqual(info["minBtn"], 32, "touch targets too small")
        self.assertIsNotNone(info["h"])
        self.audit("visual-system")


class Phone(VisualChecks, BrowserBase):
    viewport = PHONE


class Desktop(VisualChecks, BrowserBase):
    viewport = DESKTOP
