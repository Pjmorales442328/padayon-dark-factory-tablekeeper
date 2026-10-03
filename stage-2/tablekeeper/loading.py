"""Build validated detached states; never mutate live state during loading."""
from copy import deepcopy
from datetime import datetime
from .validation import (Failure, fields, array, identifier, reference, text, require,
                         timestamp, unique)
from .accounts import user_record
from .restaurants import restaurant_record
from .bookings import values, occupancy
from .receipts import receipt_record, record_identity
from .times import UTC


def empty():
    return {"users": [], "restaurants": [], "reservations": [], "tokens": {}, "receipts": []}


def booking_record(state, data, importing=False):
    rules = {"reservation_id" if importing else "id": identifier,
             "reference": reference, "user_id": identifier}
    identity = fields(data, rules)
    if not importing:
        identity["reservation_id"] = identity.pop("id")
    require(any(u["id"] == identity["user_id"] for u in state["users"]), "Unknown user")
    record = {**values(state, data), **identity, "status": "confirmed",
              "created_at": datetime.now(UTC).isoformat()}
    if importing:
        preserve_record(record, data)
    return record


def preserve_record(record, data):
    saved = fields(data, {"status": text, "created_at": text, "starts_at": text, "ends_at": text})
    require(saved["status"] in ("confirmed", "cancelled"), "Invalid reservation status")
    timestamp(saved["created_at"])
    require(saved["starts_at"] == record["starts_at"] and saved["ends_at"] == record["ends_at"],
            "Inconsistent reservation timestamps")
    record.update(saved)


def records(state, data, importing):
    users = [user_record(u, importing) for u in data["users"]]
    configs = [restaurant_record(r) for r in data["restaurants"]]
    unique(users, "id")
    unique(users, "email")
    unique(configs, "id")
    state.update(users=users, restaurants=configs)
    bookings = [booking_record(state, r, importing) for r in data["reservations"]]
    unique(bookings, "reservation_id")
    unique(bookings, "reference")
    occupancy(state, bookings)
    state["reservations"] = bookings


def tokens_record(state, tokens):
    require(isinstance(tokens, dict), "Invalid tokens")
    users = {u["id"] for u in state["users"]}
    for token, user in tokens.items():
        require(isinstance(token, str) and 0 < len(token) <= 255, "Invalid token")
        require(not any(c.isspace() for c in token), "Invalid token")
        identifier(user)
        require(user in users, "Token refers to unknown user")
    return deepcopy(tokens)


def snapshot_response(state, data, user):
    require(isinstance(data, dict), "Invalid response snapshot")
    full = {**data, "user_id": user}
    require(data.get("status") == "confirmed", "Receipt must snapshot a confirmed booking")
    booking = booking_record(state, full, True)
    actual = next((r for r in state["reservations"]
                   if r["reservation_id"] == booking["reservation_id"]), None)
    require(actual is not None, "Receipt refers to unknown booking")
    immutable = ("user_id", "reference", "restaurant_id", "created_at")
    require(all(actual[k] == booking[k] for k in immutable), "Invalid receipt identity")
    require(set(data) == set(booking) - {"user_id"}, "Invalid snapshot fields")
    return booking


def validate_receipt(state, data):
    receipt = receipt_record(data)
    user = receipt["user_id"]
    require(any(u["id"] == user for u in state["users"]), "Receipt user missing")
    if receipt["path"] == "/reservations":
        snapshot_response(state, receipt["response"], user)
        body_values = values(state, receipt["body"])
        require(all(receipt["response"][k] == v for k, v in body_values.items()),
                "Receipt body inconsistent with response")
    else:
        validate_move_receipt(state, receipt)
    return receipt


def validate_move_receipt(state, receipt):
    from .moves import move_items
    items = move_items(receipt["body"])
    response = receipt["response"]
    require(set(response) == {"reservations"}, "Invalid batch snapshot")
    snapshots = array(response["reservations"])
    require(len(items) == len(snapshots), "Batch snapshot size mismatch")
    bookings = []
    for item, snapshot in zip(items, snapshots):
        booking = snapshot_response(state, snapshot, receipt["user_id"])
        require(item["reference"] == booking["reference"], "Batch reference mismatch")
        requested = {k: v for k, v in item.items() if k in ("table_id", "party_size", "starts_at_local")}
        require(all(type(booking[k]) is type(v) and booking[k] == v for k, v in requested.items()),
                "Batch body inconsistent with response")
        bookings.append(booking)
    require(len({b["restaurant_id"] for b in bookings}) == 1, "Batch spans restaurants")
    occupancy(empty(), bookings)


def loaded(data, importing=False):
    try:
        state = empty()
        source = fields(data, {"users": array, "restaurants": array, "reservations": array})
        records(state, source, importing)
        if importing:
            require("tokens" in data and "receipts" in data, "Incomplete imported state")
            state["tokens"] = tokens_record(state, data["tokens"])
            state["receipts"] = [validate_receipt(state, r) for r in array(data["receipts"])]
            ids = [record_identity(r) for r in state["receipts"]]
            require(len(set(ids)) == len(ids), "Duplicate receipt")
        return state
    except Failure as error:
        raise Failure(message="Invalid state: " + error.message) from None


def imported(body):
    require(body.get("track") == "tablekeeper", "Wrong track")
    require(type(body.get("format_version")) is int and body["format_version"] == 1,
            "Wrong format version")
    require(isinstance(body.get("state"), dict), "State required")
    return loaded(body["state"], True)
