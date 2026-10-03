"""Configuration validation and scoped restaurant/table lookup."""
from .validation import fields, identifier, text, zone, integer, clock, array, unique, require

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def weekday(value):
    value = text(value)
    require(value in WEEKDAYS, "Invalid weekday")
    return value


def hours_record(data):
    result = fields(data, {"weekday": weekday, "opens": clock, "closes": clock})
    require(result["closes"] > result["opens"], "Closing must follow opening")
    return result


def table_record(data):
    return fields(data, {"id": identifier, "label": text, "capacity": integer})


def restaurant_record(data):
    result = fields(data, {"id": identifier, "name": text, "timezone": zone,
                          "slot_minutes": integer, "reservation_duration_minutes": integer,
                          "cancellation_cutoff_minutes": lambda v: integer(v, 0),
                          "opening_hours": array, "tables": array})
    result["opening_hours"] = [hours_record(h) for h in result["opening_hours"]]
    result["tables"] = [table_record(t) for t in result["tables"]]
    unique(result["opening_hours"], "weekday")
    unique(result["tables"], "id")
    if "combinable" in data:
        result["combinable"] = combinations(data["combinable"], result)
    return result


def combinations(value, config):
    result = []
    seen = set()
    for entry in array(value):
        pair = [identifier(member) for member in array(entry)]
        require(len(pair) == 2 and len(set(pair)) == 2, "Expected distinct pair members")
        for member in pair:
            table(config, member)
        identity = frozenset(pair)
        require(identity not in seen, "Duplicate unordered pair")
        seen.add(identity)
        result.append(pair)
    return result


def restaurant(state, restaurant_id):
    found = next((r for r in state["restaurants"] if r["id"] == restaurant_id), None)
    require(found is not None, "Restaurant not found", 404, "not_found")
    return found


def table(config, table_id):
    found = next((t for t in config["tables"] if t["id"] == table_id), None)
    require(found is not None, "Table not found", 404, "not_found")
    return found


def opening(config, date):
    day = WEEKDAYS[date.weekday()]
    return next((h for h in config["opening_hours"] if h["weekday"] == day), None)
