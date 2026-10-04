"""Reservation field, occupancy, amendment and cancellation rules."""
import secrets
from datetime import datetime
from .validation import fields, identifier, party, text, require, timestamp
from .restaurants import restaurant
from .times import interval, UTC
from .identifiers import unused
from .selections import selected, approved, members, retained_selector, selection_fields
from . import policies, chronology

CREATE_RULES = {"restaurant_id": identifier,
                "starts_at_local": text, "party_size": party}
CHANGE_FIELDS = ("starts_at_local", "party_size")


def values(state, body, accepted=None):
    result = fields(body, CREATE_RULES)
    ids = selected(body)
    config = restaurant(state, result["restaurant_id"])
    from .validation import local
    date = local(result['starts_at_local']).date()
    accepted = accepted or policies.selected(state, config, date)
    config = policies.configured(config, accepted)
    selection, capacity = approved(config, ids)
    result.update(selection)
    require(result["party_size"] <= capacity, "Party exceeds capacity", 422,
            "party_exceeds_capacity")
    result["starts_at"], result["ends_at"] = interval(config, result["starts_at_local"])
    result['accepted_terms'] = accepted
    return result


def overlaps(left, right):
    same_table = (left["restaurant_id"] == right["restaurant_id"]
                  and not set(members(left)).isdisjoint(members(right)))
    return (same_table and timestamp(left["starts_at"]) < timestamp(right["ends_at"])
            and timestamp(right["starts_at"]) < timestamp(left["ends_at"]))


def occupancy(state, candidates, excluded=()):
    occupied = [r for r in state["reservations"]
                if r["status"] == "confirmed" and r["reference"] not in excluded]
    from .closures import occupied as closed
    occupied.extend(closed(state))
    for candidate in candidates:
        if candidate["status"] != "confirmed":
            continue
        require(not any(overlaps(candidate, other) for other in occupied),
                "Table is occupied", 409, "table_unavailable")
        occupied.append(candidate)


def view(record):
    return {k: v for k, v in record.items() if k != "user_id"}


def owned(state, reference, user):
    found = next((r for r in state["reservations"]
                  if r["reference"] == reference and r["user_id"] == user), None)
    require(found is not None, "Reservation not found", 404, "not_found")
    return found


def cutoff(state, record):
    config = record['accepted_terms']
    distance = (timestamp(record["starts_at"]).astimezone(UTC) - datetime.now(UTC)).total_seconds()
    require(distance > config["cancellation_cutoff_minutes"] * 60,
            "Cancellation cutoff passed", 409, "cutoff_passed")


def amendable(state, record):
    require(record["status"] != "cancelled", "Reservation is cancelled", 409,
            "reservation_cancelled")
    cutoff(state, record)


def fresh(state, body, user):
    record = values(state, body)
    references = {r["reference"] for r in state["reservations"]}
    ref = unused(references, lambda: secrets.token_hex(4).upper())
    ids = {r["reservation_id"] for r in state["reservations"]}
    rid = unused(ids, lambda: secrets.token_hex(16))
    return {**record, "user_id": user, "reference": ref, "reservation_id": rid,
            "status": "confirmed", "created_at": datetime.now(UTC).isoformat(), 'revision': 1}


def create(state, body, user):
    record = fresh(state, body, user)
    occupancy(state, [record])
    state["reservations"].append(record)
    chronology.created(state, record)
    return 201, view(record)

from .amendments import changed, amend, cancel, commit_changes
