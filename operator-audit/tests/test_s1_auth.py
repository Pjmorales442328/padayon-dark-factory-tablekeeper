"""Stage 1 §3, §5, §6: runtime contract, error shape, authentication."""
import httpx, pytest
from kit import *
pytestmark = pytest.mark.s1

def test_health_is_200_ok(base_url):
    r = httpx.get(base_url + "/health"); assert r.status_code == 200 and r.json() == {"status": "ok"}

def test_reset_replaces_everything_and_repeats(reset, api):
    world(reset, api); a = ada(api); assert book(a, date()).status_code == 201
    world(reset, api, users=[fx.BOB])
    assert_error(api().login(fx.ADA["email"], fx.ADA["password"]), 401, "unauthenticated")
    b = api().authenticate(fx.BOB["email"], fx.BOB["password"]); assert b.get("/reservations").json() == {"reservations": []}

def test_error_body_has_code_and_message(reset, api):
    world(reset, api)
    for r in (api().get("/restaurants/nope"), api().get("/reservations"), api().post("/auth/login", json={"email": "x@y.z", "password": "bad bad bad"})):
        e = r.json()["error"]; assert isinstance(e["code"], str) and isinstance(e["message"], str)

def test_signup_creates_a_usable_account(reset, api):
    world(reset, api); r = assert_status(api().signup("new@example.com", "long enough", "New"), 201).json()
    assert r["display_name"] == "New" and r["user_id"] and r["token"]
    c = api(r["token"]); assert c.get("/reservations").status_code == 200
    assert_status(api().login("new@example.com", "long enough"), 200)

@pytest.mark.parametrize("email,pw,code", [("ada@example.com", "long enough", 409), ("plain", "long enough", 422), ("a@", "long enough", 422),
                                           ("@b.c", "long enough", 422), ("ok@example.com", "short", 422), ("ok@example.com", "1234567", 422)])
def test_signup_rules(reset, api, email, pw, code):
    world(reset, api); r = api().signup(email, pw, "X")
    assert r.status_code == code, r.text
    if code == 409: assert r.json()["error"]["code"] == "email_taken"
    else: assert r.json()["error"]["code"] == "validation_failed"

def test_signup_eight_characters_is_enough(reset, api):
    world(reset, api); assert_status(api().signup("e8@example.com", "12345678", "E"), 201)

def test_signup_wrong_type_is_malformed_and_missing_is_validation(reset, api):
    world(reset, api); c = api()
    assert_error(c.post("/auth/signup", json={"email": "a@b.c", "password": 12345678, "display_name": "X"}), 400, "malformed_request")
    assert_error(c.post("/auth/signup", json={"email": "a@b.c", "display_name": "X"}), 422, "validation_failed")
    assert_error(c.post("/auth/signup", content=b"{not json"), 400, "malformed_request")

def test_login_failures_are_401_unauthenticated(reset, api):
    world(reset, api); c = api()
    assert_error(c.login(fx.ADA["email"], "wrong password"), 401, "unauthenticated")
    assert_error(c.login("nobody@example.com", "whatever pass"), 401, "unauthenticated")

def test_many_tokens_are_valid_at_once(reset, api):
    world(reset, api); t = [api().login(fx.ADA["email"], fx.ADA["password"]).json()["token"] for _ in range(3)]
    assert len(set(t)) == 3 and all(api(x).get("/reservations").status_code == 200 for x in t)

@pytest.mark.parametrize("token", [None, "Basic abc", "garbage", "Bearer"])
def test_protected_routes_need_a_real_bearer_token(reset, api, token):
    world(reset, api); c = api()
    hdr = {} if token is None else {"Authorization": token if token in ("Bearer", "Basic abc") else f"Bearer {token}"}
    for method, path in (("GET", "/reservations"), ("GET", "/reservations/ABC123"), ("POST", "/reservations/ABC123/cancel"), ("PATCH", "/reservations/ABC123")):
        assert_error(c.request(method, path, token=None, headers=hdr, json={} if method != "GET" else None), 401, "unauthenticated")

def test_public_routes_need_no_token(reset, api):
    world(reset, api); c = api(); d = date()
    assert c.get("/restaurants").status_code == 200 and c.get("/restaurants/r_anker").status_code == 200 and avail(c, d).status_code == 200

def test_unknown_body_fields_and_query_params_are_ignored(reset, api):
    world(reset, api); a = ada(api); d = date()
    assert_status(book(a, d, extra_field="x", other={"a": 1}), 201)
    assert_status(a.get("/availability", params={"restaurant_id": "r_anker", "date": d, "party_size": 2, "zzz": "1"}), 200)

def test_responses_are_json_utf8(reset, api):
    world(reset, api); r = api().get("/restaurants"); assert r.headers["content-type"].lower().startswith("application/json")
