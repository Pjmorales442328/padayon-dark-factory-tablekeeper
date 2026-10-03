"""Validate historical receipts without rewriting their original JSON values."""
from .validation import array, require
from .bookings import values, occupancy
from .receipts import receipt_record
from .selections import selected, members


def snapshot_response(state, data, user):
    from .loading import booking_record
    require(isinstance(data, dict), "Invalid response snapshot")
    require(data.get("status") == "confirmed", "Receipt must snapshot a confirmed booking")
    booking = booking_record(state, {**data, "user_id": user}, True)
    actual = next((r for r in state["reservations"]
                   if r["reservation_id"] == booking["reservation_id"]), None)
    require(actual is not None, "Receipt refers to unknown booking")
    immutable = ("user_id", "reference", "restaurant_id", "created_at")
    require(all(actual[k] == booking[k] for k in immutable), "Invalid receipt identity")
    expected = set(booking) - {"user_id"}
    if "table_ids" not in data:
        require(len(members(booking)) == 1, "Legacy snapshot must be singleton")
        expected.remove("table_ids")
    require(set(data) == expected, "Invalid snapshot fields")
    return booking


def validate_receipt(state, data):
    receipt = receipt_record(data)
    user = receipt["user_id"]
    require(any(u["id"] == user for u in state["users"]), "Receipt user missing")
    if receipt["path"] == "/reservations":
        booking = snapshot_response(state, receipt["response"], user)
        body_values = values(state, receipt["body"])
        require(all(booking[k] == v for k, v in body_values.items()),
                "Receipt body inconsistent with response")
    else:
        validate_move_receipt(state, receipt)
    return receipt


def requested_matches(item, booking):
    if "table_id" in item or "table_ids" in item:
        require(set(selected(item)) == set(members(booking)), "Batch table selection mismatch")
    requested = {k: v for k, v in item.items() if k in ("party_size", "starts_at_local")}
    require(all(type(booking[k]) is type(v) and booking[k] == v for k, v in requested.items()),
            "Batch body inconsistent with response")


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
        requested_matches(item, booking)
        bookings.append(booking)
    require(len({b["restaurant_id"] for b in bookings}) == 1, "Batch spans restaurants")
    occupancy({"reservations": []}, bookings)
