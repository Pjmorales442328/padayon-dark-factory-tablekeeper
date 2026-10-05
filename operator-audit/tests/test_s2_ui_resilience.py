"""Stage 2 UI: out-of-order responses, lost responses, competing clients, upgrade."""
import json, httpx, re, pytest
from uikit import *
pytestmark = [pytest.mark.s2, pytest.mark.ui]


@pytest.fixture
def seeded(reset):
    reset(fx.fixture(restaurants=[rest(combinable=PAIRS)]))


def test_late_search_response_never_replaces_a_newer_one(seeded, page):
    held = []

    def handler(route):
        if not held and "/availability" in route.request.url:
            held.append(route)
        else:
            route.continue_()

    page.route("**/availability*", handler)
    d = fx.booking_date()
    page.goto("/")
    page.select_option(sel("restaurant-select"), "r_anker"); page.fill(sel("date-input"), d)
    page.fill(sel("party-size-input"), "6"); page.click(sel("search-button")); page.wait_for_timeout(300)
    assert held, "first search was not held"
    page.fill(sel("party-size-input"), "2"); page.click(sel("search-button"), force=True)
    page.wait_for_selector(sel("slot-t_1-19:00"))
    assert page.get_attribute(sel("slot-t_1-19:00"), "data-available") == "true"
    held[0].continue_(); page.wait_for_timeout(1200)
    assert page.get_attribute(sel("slot-t_1-19:00"), "data-available") == "true", "late response A restored its results"


def test_conflict_shows_error_refreshes_and_keeps_the_form(seeded, page, api):
    d = fx.booking_date()
    open_form(page, party=4, d=d); page.fill(sel("booking-party-size"), "3")
    assert_status(book(bob(api), d, "t_2", "19:00", 4), 201)
    page.click(sel("booking-submit")); page.wait_for_selector(sel("booking-error"))
    assert page.query_selector(sel("confirmation")) is None
    assert page.query_selector(sel("booking-form")) is not None and page.input_value(sel("booking-party-size")) == "3"
    page.wait_for_function("document.querySelector(\"[data-testid='slot-t_2-19:00']\").getAttribute('data-available') === 'false'")


def lost_response(page, commit):
    seen = []

    def handler(route):
        req = route.request
        if req.method == "POST" and req.url.rstrip("/").endswith("/reservations"):
            seen.append((req.headers.get("idempotency-key"), req.post_data))
            if commit:
                route.fetch()
            route.abort()
        else:
            route.continue_()

    page.route("**/*", handler)
    return seen


@pytest.mark.parametrize("commit", [True, False])
def test_lost_response_is_uncertain_then_recovers_with_same_key(seeded, page, api, commit):
    open_form(page)
    seen = lost_response(page, commit)
    page.click(sel("booking-submit")); page.wait_for_selector(sel("booking-uncertain"))
    assert page.text_content(sel("booking-uncertain")).strip()
    assert page.query_selector(sel("booking-error")) is None and page.query_selector(sel("confirmation")) is None
    page.unroute("**/*")
    retry = []
    page.on("request", lambda r: retry.append((r.headers.get("idempotency-key"), r.post_data))
            if r.method == "POST" and r.url.rstrip("/").endswith("/reservations") else None)
    page.click(sel("booking-submit")); page.wait_for_selector(sel("confirmation"))
    assert page.query_selector(sel("booking-uncertain")) is None and page.query_selector(sel("booking-error")) is None
    assert retry and retry[0][0] == seen[0][0] and json.loads(retry[0][1]) == json.loads(seen[0][1])
    rs = ada(api).get("/reservations").json()["reservations"]
    assert len(rs) == 1 and ref(page) == rs[0]["reference"]


def test_confirmed_rejection_uses_booking_error_not_uncertain(seeded, page):
    open_form(page)
    body_ = json.dumps({"error": {"code": "table_unavailable", "message": "taken"}})
    page.route("**/reservations", lambda r: r.fulfill(status=409, content_type="application/json", body=body_)
               if r.request.method == "POST" else r.continue_())
    page.click(sel("booking-submit")); page.wait_for_selector(sel("booking-error"))
    assert page.query_selector(sel("booking-uncertain")) is None and page.query_selector(sel("confirmation")) is None


def test_lost_response_for_a_combination_booking(seeded, page, api):
    sign_in(page); search(page, None, 5)
    page.click(sel("slot-t_1+t_2-19:00")); page.wait_for_selector(sel("booking-form"))
    lost_response(page, True)
    page.click(sel("booking-submit")); page.wait_for_selector(sel("booking-uncertain"))
    page.unroute("**/*"); page.click(sel("booking-submit")); page.wait_for_selector(sel("confirmation"))
    rs = ada(api).get("/reservations").json()["reservations"]
    assert len(rs) == 1 and rs[0]["table_ids"] == ["t_1", "t_2"] and ref(page) == rs[0]["reference"]


def test_pending_retry_survives_an_export_import_upgrade(seeded, page, api, base_url):
    open_form(page)
    lost_response(page, True)
    page.click(sel("booking-submit")); page.wait_for_selector(sel("booking-uncertain")); page.unroute("**/*")
    e = httpx.get(base_url + "/_test/export").json()
    assert httpx.post(base_url + "/_test/import", json=e).status_code == 204
    page.click(sel("booking-submit")); page.wait_for_selector(sel("confirmation"))
    assert page.query_selector(sel("current-user")) is not None
    rs = ada(api).get("/reservations").json()["reservations"]
    assert len(rs) == 1 and ref(page) == rs[0]["reference"]


def test_browser_stays_signed_in_after_import_and_old_reference_still_looks_up(seeded, page, api, base_url):
    sign_in(page)
    r = book(ada(api), fx.booking_date(), "t_3", "19:00", 4).json()["reference"]
    e = httpx.get(base_url + "/_test/export").json(); httpx.post(base_url + "/_test/import", json=e)
    page.goto("/lookup"); page.wait_for_selector(sel("current-user"))
    page.fill(sel("lookup-reference-input"), r); page.click(sel("lookup-submit")); page.wait_for_selector(sel("reservation-detail"))
