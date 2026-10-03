"""Reservation field, occupancy, amendment and cancellation rules."""
import secrets
from datetime import datetime
from .validation import fields, identifier, party, text, require, timestamp
from .restaurants import restaurant, table
from .times import interval, UTC
from .identifiers import unused

CREATE_RULES = {"restaurant_id": identifier, "table_id": identifier,
                "starts_at_local": text, "party_size": party}
CHANGE_FIELDS = ("table_id", "starts_at_local", "party_size")


def values(state, body):
    result = fields(body, CREATE_RULES)
    config = restaurant(state, result["restaurant_id"])
    seat = table(config, result["table_id"])
    require(result["party_size"] <= seat["capacity"], "Party exceeds capacity", 422,
            "party_exceeds_capacity")
    result["starts_at"], result["ends_at"] = interval(config, result["starts_at_local"])
    return result


def overlaps(left, right):
    same_table = (left["restaurant_id"], left["table_id"]) == (right["restaurant_id"], right["table_id"])
    return (same_table and timestamp(left["starts_at"]) < timestamp(right["ends_at"])
            and timestamp(right["starts_at"]) < timestamp(left["ends_at"]))


def occupancy(state, candidates, excluded=()):
    occupied = [r for r in state["reservations"]
                if r["status"] == "confirmed" and r["reference"] not in excluded]
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
    config = restaurant(state, record["restaurant_id"])
    distance = (timestamp(record["starts_at"]).astimezone(UTC) - datetime.now(UTC)).total_seconds()
    require(distance > config["cancellation_cutoff_minutes"] * 60,
            "Cancellation cutoff passed", 409, "cutoff_passed")


def amendable(state, record):
    require(record["status"] != "cancelled", "Reservation is cancelled", 409,
            "reservation_cancelled")
    cutoff(state, record)


def changed(state, record, body):
    amendable(state, record)
    body_values = {k: body.get(k, record[k]) for k in CHANGE_FIELDS}
    body_values["restaurant_id"] = record["restaurant_id"]
    new = values(state, body_values)
    return {**record, **new}


def fresh(state, body, user):
    record = values(state, body)
    references = {r["reference"] for r in state["reservations"]}
    ref = unused(references, lambda: secrets.token_hex(4).upper())
    ids = {r["reservation_id"] for r in state["reservations"]}
    rid = unused(ids, lambda: secrets.token_hex(16))
    return {**record, "user_id": user, "reference": ref, "reservation_id": rid,
            "status": "confirmed", "created_at": datetime.now(UTC).isoformat()}


def create(state, body, user):
    record = fresh(state, body, user)
    occupancy(state, [record])
    state["reservations"].append(record)
    return 201, view(record)


def amend(state, body, ref, user):
    record = owned(state, ref, user)
    updated = changed(state, record, body)
    occupancy(state, [updated], [ref])
    record.update(updated)
    return 200, view(record)


def cancel(state, ref, user):
    record = owned(state, ref, user)
    if record["status"] != "cancelled":
        cutoff(state, record)
        record["status"] = "cancelled"
    return 200, view(record)
