"""Detached public configuration, availability and owner booking views."""
import re
from datetime import datetime
from .validation import fields, identifier, text, decimal, require, Failure, timestamp
from .restaurants import restaurant
from .bookings import overlaps, view
from .times import slots


def date_value(value):
    value = text(value)
    require(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is not None, "Invalid date")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise Failure(message="Invalid calendar date") from None


def availability(state, query):
    parsed = fields(query, {"restaurant_id": identifier, "date": date_value, "party_size": decimal})
    config = restaurant(state, parsed["restaurant_id"])
    occupied = [r for r in state["reservations"] if r["status"] == "confirmed"]
    result = []
    for value, start, end in slots(config, parsed["date"]):
        candidate = {"restaurant_id": config["id"], "starts_at": start, "ends_at": end}
        tables = available_tables(config, candidate, parsed["party_size"], occupied)
        result.append({"starts_at_local": value, "starts_at": start, "available_table_ids": tables})
    return 200, {"restaurant_id": config["id"], "date": query["date"],
                 "timezone": config["timezone"], "slots": result}


def available_tables(config, candidate, size, occupied):
    result = []
    for table in config["tables"]:
        booking = {**candidate, "table_id": table["id"]}
        if table["capacity"] >= size and not any(overlaps(booking, r) for r in occupied):
            result.append(table["id"])
    return result


def reservations(state, user):
    owned = [r for r in state["reservations"] if r["user_id"] == user]
    owned.sort(key=lambda r: timestamp(r["starts_at"]), reverse=True)
    return 200, {"reservations": [view(r) for r in owned]}
