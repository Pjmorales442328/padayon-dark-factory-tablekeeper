"""Stage 3: availability explanations."""
import pytest
from kit import *
pytestmark = pytest.mark.s3
RULES = ["capacity", "no_overlap"]


def explained(c, d, party=2, hhmm="19:00"):
    return slot(avail(c, d, party, explain=True), hhmm)


def test_every_table_reports_both_rules_in_order(reset, api):
    d = date(); world(reset, api); a = ada(api); book(a, d, "t_2", "19:00", 2)
    s = explained(a, d, 3)
    assert [e["table_id"] for e in s["explain"]] == ["t_1", "t_2", "t_3"]
    for e in s["explain"]:
        assert [r["rule"] for r in e["rules"]] == RULES and e["policy_version"] == 0
        assert e["available"] == all(r["holds"] for r in e["rules"])
    by = {e["table_id"]: {r["rule"]: r["holds"] for r in e["rules"]} for e in s["explain"]}
    assert by["t_1"] == {"capacity": False, "no_overlap": True} and by["t_2"] == {"capacity": True, "no_overlap": False} and by["t_3"] == {"capacity": True, "no_overlap": True}
    assert [e["table_id"] for e in s["explain"] if e["available"]] == s["available_table_ids"] == ["t_3"]


def test_a_table_failing_both_rules_reports_both_false(reset, api):
    d = date(); world(reset, api); a = ada(api); book(a, d, "t_1", "19:00", 2)
    e = next(x for x in explained(a, d, 3)["explain"] if x["table_id"] == "t_1")
    assert e["available"] is False and [r["holds"] for r in e["rules"]] == [False, False]


def test_explain_is_opt_in_and_strict(reset, api):
    d = date(); world(reset, api); c = api()
    assert "explain" not in slot(avail(c, d, 2), "19:00")
    for bad in ("false", "1", "", "TRUE", "yes"):
        assert_error(c.get("/availability", params={"restaurant_id": "r_anker", "date": d, "party_size": 2, "explain": bad}), 422, "validation_failed")


def test_empty_slots_and_closed_days(reset, api):
    d = date(); world(reset, api, restaurants=[rest(opening_hours=[{"weekday": fx.weekday_of(d), "opens": "18:00", "closes": "23:00"}])]); c = api()
    r = avail(c, d, 99, explain=True).json()
    assert len(r["slots"]) == len(fx.expected_slots()) and all(len(s["explain"]) == 3 and s["available_table_ids"] == [] for s in r["slots"])
    assert avail(c, date(8), 2, explain=True).json()["slots"] == []


def test_explain_keeps_available_table_ids_equal_to_the_plain_query(reset, api):
    d = date(); world(reset, api); a = ada(api); book(a, d, "t_3", "20:00", 4)
    plain = avail(a, d, 3).json()["slots"]; ex = avail(a, d, 3, explain=True).json()["slots"]
    assert [(s["starts_at_local"], s["available_table_ids"]) for s in plain] == [(s["starts_at_local"], s["available_table_ids"]) for s in ex]


def test_explain_reads_the_policy_selected_for_the_date(reset, api):
    d = date(); world(reset, api, restaurants=[rest(managers=["u_ada"])]); a = ada(api)
    pol = fx.policy(d, capacities={"t_1": 6, "t_2": 4, "t_3": 6})
    assert_status(a.post("/restaurants/r_anker/policies", json=pol, idempotency_key=new_key()), 201)
    s = explained(a, d, 5)
    assert all(e["policy_version"] == 1 for e in s["explain"]) and s["available_table_ids"] == ["t_1", "t_3"]
    other = explained(a, date(-40), 5); assert all(e["policy_version"] == 0 for e in other["explain"]) and other["available_table_ids"] == ["t_3"]
