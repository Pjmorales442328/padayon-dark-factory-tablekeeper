"""Stage 2 UI: 375 px layout, labels, focus, accessibility scan."""
import pytest
from uikit import *
pytestmark = [pytest.mark.s2, pytest.mark.ui]
ROUTES = ["/", "/login", "/signup", "/lookup"]
UNLABELLED = """[...document.querySelectorAll('input,select,textarea')].filter(e => e.type !== 'hidden').filter(e => {
  const l = e.id && document.querySelector('label[for="' + CSS.escape(e.id) + '"]'); const w = e.closest('label');
  const a = e.getAttribute('aria-label') || e.getAttribute('aria-labelledby');
  return !((l && l.innerText.trim()) || (w && w.innerText.trim()) || a) }).map(e => e.outerHTML.slice(0, 80))"""


@pytest.fixture
def seeded(reset):
    reset(fx.fixture(restaurants=[rest(combinable=PAIRS)]))


@pytest.mark.parametrize("w", [375, 1280])
def test_no_horizontal_scroll_on_any_route_or_after_search(seeded, browser, base_url, w):
    ctx = browser.new_context(base_url=base_url, viewport={"width": w, "height": 800}); p = ctx.new_page()
    for r in ROUTES:
        p.goto(r); p.wait_for_load_state("networkidle")
        assert p.evaluate("document.documentElement.scrollWidth") <= w, (r, w)
    sign_in(p); search(p, None, 5)
    assert p.evaluate("document.documentElement.scrollWidth") <= w
    p.click(sel("slot-t_1+t_2-19:00")); p.wait_for_selector(sel("booking-form"))
    assert p.evaluate("document.documentElement.scrollWidth") <= w
    ctx.close()


def test_every_input_has_a_visible_label(seeded, page):
    for r in ROUTES:
        page.goto(r)
        assert not page.evaluate(UNLABELLED), r


def test_keyboard_focus_is_visible(seeded, page):
    page.goto("/login")
    for _ in range(3):
        page.keyboard.press("Tab")
    st = page.evaluate("(() => { const e = document.activeElement; const s = getComputedStyle(e); return {tag: e.tagName, outline: s.outlineStyle + ' ' + s.outlineWidth, shadow: s.boxShadow}; })()")
    assert st["tag"] != "BODY" and (not st["outline"].startswith("none") or st["shadow"] != "none"), st


@pytest.mark.parametrize("w", [375, 1280])
def test_no_serious_accessibility_findings(seeded, browser, base_url, w):
    from axe_playwright_python.sync_playwright import Axe
    ctx = browser.new_context(base_url=base_url, viewport={"width": w, "height": 800}); p = ctx.new_page(); bad = []

    def scan(name):
        res = Axe().run(p)
        bad.extend((name, v["id"], v["impact"]) for v in res.response["violations"] if v["impact"] in ("serious", "critical"))

    for r in ROUTES:
        p.goto(r); p.wait_for_load_state("networkidle"); scan(r)
    sign_in(p); search(p, None, 5); scan("grid")
    p.click(sel("slot-t_3-19:00")); p.wait_for_selector(sel("booking-form")); scan("form")
    p.click(sel("booking-submit")); p.wait_for_selector(sel("confirmation")); scan("confirmation")
    ctx.close()
    assert not bad, bad


def test_available_and_unavailable_cells_look_different(seeded, page, api):
    d = fx.booking_date(); book(ada(api), d, "t_2", "19:00", 2); search(page, d, 2)
    probe = "(() => { const e = document.querySelector(\"[data-testid='slot-%s-19:00']\"); const s = getComputedStyle(e); return [s.backgroundColor, s.color, s.opacity, s.textDecorationLine].join('|'); })()"
    assert page.evaluate(probe % "t_1") != page.evaluate(probe % "t_2")
