"""Browser helpers: everything is found by data-testid only."""
from kit import *

def sel(n): return f"[data-testid='{n}']"
def sign_in(page, email=None, password="correct horse"):
    page.goto("/login"); page.fill(sel("login-email"), email or fx.ADA["email"]); page.fill(sel("login-password"), password); page.click(sel("login-submit")); page.wait_for_selector(sel("current-user"))
def search(page, d=None, party=4, rid="r_anker"):
    page.goto("/") if page.url.rstrip("/").endswith(("signup", "login", "lookup")) or "/" not in page.url.split("//", 1)[-1] else None
    if page.query_selector(sel("search-button")) is None: page.goto("/")
    page.select_option(sel("restaurant-select"), rid); page.fill(sel("date-input"), d or fx.booking_date()); page.fill(sel("party-size-input"), str(party)); page.click(sel("search-button"))
    page.wait_for_selector(f"{sel('availability-grid')}, {sel('no-slots')}")
def open_form(page, cell="slot-t_2-19:00", party=4, d=None):
    sign_in(page); search(page, d, party); page.click(sel(cell)); page.wait_for_selector(sel("booking-form"))
def ref(page): return page.text_content(sel("confirmation-reference")).strip()
