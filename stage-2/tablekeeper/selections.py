"""Typed selectors and restaurant-local approved member sets."""
from .validation import array, identifier, require
from .restaurants import table


def members(record):
    if "table_ids" in record:
        return record["table_ids"]
    return [record["table_id"]]


def selected(body):
    require(not ("table_id" in body and "table_ids" in body), "Use one table selector")
    require("table_id" in body or "table_ids" in body, "Missing table selection")
    if "table_id" in body:
        return [identifier(body["table_id"])]
    ids = [identifier(value) for value in array(body["table_ids"])]
    require(len(ids) > 0, "Empty table selection")
    require(len(ids) <= 2, "Only pairs may be combined", 422, "combination_not_allowed")
    require(len(set(ids)) == len(ids), "Duplicate selected table")
    return ids


def selection_fields(ids):
    result = {"table_ids": list(ids)}
    if len(ids) == 1:
        result["table_id"] = ids[0]
    return result


def approved(config, ids):
    seats = [table(config, value) for value in ids]
    if len(ids) == 2:
        declaration = next((pair for pair in config.get("combinable", [])
                            if set(pair) == set(ids)), None)
        require(declaration is not None, "Pair is not declared", 422, "combination_not_allowed")
        ids = declaration
    return selection_fields(ids), sum(seat["capacity"] for seat in seats)


def retained_selector(record, body):
    if "table_id" in body or "table_ids" in body:
        return {k: body[k] for k in ("table_id", "table_ids") if k in body}
    return {"table_ids": list(members(record))}


def stored_body(data):
    result = dict(data)
    if "table_id" in result and "table_ids" in result:
        ids = selected({"table_ids": result["table_ids"]})
        require(len(ids) == 1 and identifier(result["table_id"]) == ids[0],
                "Stored selectors disagree")
        result.pop("table_id")
    return result
