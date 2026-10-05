"""Stage 2 UI: routes, auth, grid, booking, lookup."""
import re, pytest
from uikit import *
pytestmark = [pytest.mark.s2, pytest.mark.ui]

@pytest.fixture
def seeded(reset): reset(fx.fixture(restaurants=[rest(combinable=PAIRS)]))

@pytest.mark.parametrize("path", ["/", "/signup", "/login", "/lookup"])
def test_required_routes_return_html(seeded, page, path):
    r = page.goto(path); assert r.status == 200 and "text/html" in r.headers["content-type"]

def test_signup_login_logout_cycle_and_current_user_everywhere(seeded, page):
    page.goto("/signup"); page.fill(sel("signup-email"), "dee@example.com"); page.fill(sel("signup-password"), "long enough"); page.fill(sel("signup-display-name"), "Dee"); page.click(sel("signup-submit")); page.wait_for_selector(sel("current-user"))
    assert "Dee" in page.text_content(sel("current-user"))
    for path in ("/", "/lookup", "/login", "/signup"):
        page.click(f"a[href='{path}']") if page.query_selector(f"a[href='{path}']") else page.goto(path); page.wait_for_selector(sel("current-user"))
    page.click(sel("logout-button")); page.wait_for_selector(sel("current-user"), state="detached")

def test_signup_errors_use_auth_error(seeded, page):
    page.goto("/signup"); page.fill(sel("signup-email"), fx.ADA["email"]); page.fill(sel("signup-password"), "long enough"); page.fill(sel("signup-display-name"), "X"); page.click(sel("signup-submit")); page.wait_for_selector(sel("auth-error"))
    page.fill(sel("signup-email"), "ok@example.com"); page.fill(sel("signup-password"), "short"); page.click(sel("signup-submit")); page.wait_for_selector(sel("auth-error")); assert page.query_selector(sel("current-user")) is None

def test_grid_cells_match_the_api_exactly(seeded, page, api):
    d = fx.booking_date(); c = ada(api); book(c, d, "t_2", "19:00", 2); search(page, d, 3); resp = avail(api(), d, 3).json()
    for s in resp["slots"]:
        hh = s["starts_at_local"][-5:]
        for t in ("t_1", "t_2", "t_3"): assert page.get_attribute(sel(f"slot-{t}-{hh}"), "data-available") == ("true" if t in s["available_table_ids"] else "false"), (t, hh)

def test_combination_cells_exist_and_follow_availability(seeded, page, api):
    d = fx.booking_date(); search(page, d, 5)
    assert page.get_attribute(sel("slot-t_1+t_2-19:00"), "data-available") == "true" and page.get_attribute(sel("slot-t_2+t_3-19:00"), "data-available") == "true" and page.query_selector(sel("slot-t_1+t_3-19:00")) is None
    book(ada(api), d, "t_3", "19:00", 5); search(page, d, 5)
    assert page.get_attribute(sel("slot-t_1+t_2-19:00"), "data-available") == "true" and page.get_attribute(sel("slot-t_2+t_3-19:00"), "data-available") == "false"

def test_booking_a_pair_through_the_ui(seeded, page, api):
    sign_in(page); search(page, None, 5); page.click(sel("slot-t_1+t_2-19:00")); page.wait_for_selector(sel("booking-form"))
    summary = page.text_content(sel("booking-summary")); assert "1" in summary and "2" in summary and "19:00" in summary
    page.click(sel("booking-submit")); page.wait_for_selector(sel("confirmation")); r = ref(page); assert re.fullmatch(r"[A-Z0-9]{6,12}", r)
    tbl = page.text_content(sel("confirmation-tables")); assert "1" in tbl and "2" in tbl and "Zum Anker" in page.text_content(sel("confirmation-details"))
    page.goto("/lookup"); page.fill(sel("lookup-reference-input"), r); page.click(sel("lookup-submit")); page.wait_for_selector(sel("reservation-detail")); t = page.text_content(sel("reservation-tables")); assert "1" in t and "2" in t
    assert ada(api).get(f"/reservations/{r}").json()["table_ids"] == ["t_1", "t_2"]

def test_single_booking_summary_confirmation_and_prefill(seeded, page):
    open_form(page, party=3); assert page.input_value(sel("booking-party-size")) == "3"
    s = page.text_content(sel("booking-summary")); assert "2" in s and "19:00" in s
    page.click(sel("booking-submit")); page.wait_for_selector(sel("confirmation")); d = page.text_content(sel("confirmation-details")); assert "Zum Anker" in d and "19:00" in d and "2" in d
    assert re.fullmatch(r"[A-Z0-9]{6,12}", ref(page))

def test_form_stays_and_resubmit_replays(seeded, page, api):
    open_form(page); page.click(sel("booking-submit")); page.wait_for_selector(sel("confirmation")); first = ref(page)
    assert page.query_selector(sel("booking-form")) is not None
    page.click(sel("booking-submit")); page.wait_for_timeout(600); assert page.query_selector(sel("booking-error")) is None and ref(page) == first
    assert len(ada(api).get("/reservations").json()["reservations"]) == 1

def test_lookup_cancel_and_status_text(seeded, page, api):
    r = book(ada(api), fx.booking_date(), "t_2", "19:00", 2).json()["reference"]; sign_in(page); page.goto("/lookup"); page.fill(sel("lookup-reference-input"), r); page.click(sel("lookup-submit")); page.wait_for_selector(sel("reservation-detail"))
    assert page.text_content(sel("reservation-status")).strip() == "confirmed"
    page.goto("/lookup"); page.fill(sel("lookup-reference-input"), r); page.click(sel("lookup-submit")); page.click(sel("reservation-cancel-button")); page.wait_for_selector(sel("reservation-cancel-button"), state="detached")
    assert page.text_content(sel("reservation-status")).strip() == "cancelled"

def test_cancel_refused_inside_cutoff_shows_reservation_error(seeded, page, api):
    r = book(ada(api), date(-2), "t_2", "19:00", 2).json()["reference"]; sign_in(page); page.goto("/lookup"); page.fill(sel("lookup-reference-input"), r); page.click(sel("lookup-submit")); page.wait_for_selector(sel("reservation-detail"))
    page.click(sel("reservation-cancel-button")); page.wait_for_selector(sel("reservation-error")); assert page.text_content(sel("reservation-status")).strip() == "confirmed"

def test_no_slots_on_a_closed_day_and_signed_out_booking(reset, page):
    d = fx.booking_date(); reset(fx.fixture(restaurants=[rest(opening_hours=[])])); search(page, d, 2); page.wait_for_selector(sel("no-slots")); assert page.query_selector(sel("availability-grid")) is None
