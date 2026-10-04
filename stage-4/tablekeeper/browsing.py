"""Detached public configuration, availability and owner booking views."""
import re
from datetime import datetime
from .validation import fields, identifier, text, decimal, require, Failure, timestamp
from .restaurants import restaurant
from .bookings import overlaps, view
from .times import slots
from .selections import selection_fields
from . import policies


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
    require('explain' not in query or query['explain'] == 'true', 'Explain must be true')
    accepted = policies.selected(state, config, parsed['date'])
    config = policies.configured(config, accepted)
    occupied = [r for r in state["reservations"] if r["status"] == "confirmed"]
    result = []
    for value, start, end in slots(config, parsed["date"]):
        candidate = {"restaurant_id": config["id"], "starts_at": start, "ends_at": end}
        options = available_options(config, candidate, parsed["party_size"], occupied)
        tables = [o["table_ids"][0] for o in options if len(o["table_ids"]) == 1]
        slot = {"starts_at_local": value, "starts_at": start, "available_table_ids": tables,
                "available_options": options}
        if 'explain' in query:
            slot['explain'] = explanations(config, candidate, parsed['party_size'], occupied,
                                            accepted['policy_version'])
        result.append(slot)
    return 200, {"restaurant_id": config["id"], "date": query["date"],
                 "timezone": config["timezone"], "slots": result}


def explanations(config, candidate, size, occupied, version):
    result = []
    for table in config['tables']:
        capacity = size <= table['capacity']
        booking = {**candidate, **selection_fields([table['id']])}
        free = not any(overlaps(booking, other) for other in occupied)
        result.append({'table_id': table['id'], 'policy_version': version,
                       'available': capacity and free,
                       'rules': [{'rule': 'capacity', 'holds': capacity},
                                 {'rule': 'no_overlap', 'holds': free}]})
    return result


def seating_options(config):
    result = [{"table_ids": [t["id"]], "capacity": t["capacity"]} for t in config["tables"]]
    capacities = {t["id"]: t["capacity"] for t in config["tables"]}
    result.extend({"table_ids": list(pair), "capacity": sum(capacities[t] for t in pair)}
                  for pair in config.get("combinable", []))
    return result


def available_options(config, candidate, size, occupied):
    result = []
    for option in seating_options(config):
        booking = {**candidate, **selection_fields(option["table_ids"])}
        if option["capacity"] >= size and not any(overlaps(booking, r) for r in occupied):
            result.append(option)
    return result


def reservations(state, user):
    owned = [r for r in state["reservations"] if r["user_id"] == user]
    owned.sort(key=lambda r: timestamp(r["starts_at"]), reverse=True)
    return 200, {"reservations": [view(r) for r in owned]}
