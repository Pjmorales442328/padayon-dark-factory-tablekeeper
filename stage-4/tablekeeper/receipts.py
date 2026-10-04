"""Type-preserving JSON comparison and immutable successful write receipts."""
import json
import math
from copy import deepcopy
from .validation import require, text, identifier, fields


def json_value(value):
    if value is None or type(value) in (bool, str, int):
        return value
    if type(value) is float:
        require(math.isfinite(value), "Non-finite JSON number")
        return value
    if isinstance(value, list):
        return [json_value(v) for v in value]
    require(isinstance(value, dict), "Invalid JSON value")
    require(all(isinstance(k, str) for k in value), "Invalid object key")
    return {k: json_value(v) for k, v in value.items()}


def canonical(body):
    return json.dumps(json_value(body), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def key_value(value):
    value = text(value)
    require(1 <= len(value) <= 255, "Invalid idempotency key")
    return value


def identity(user, method, path, key):
    return user, method, path, key


def record_identity(record):
    return identity(record["user_id"], record["method"], record["path"], record["key"])


def replay(state, user, method, path, headers, body):
    key = headers.get("idempotency-key", "")
    require(key != "", "Idempotency key required", 400, "missing_idempotency_key")
    key_value(key)
    match = identity(user, method, path, key)
    receipt = next((r for r in state["receipts"] if record_identity(r) == match), None)
    if receipt is None:
        return key, None
    require(canonical(receipt["body"]) == canonical(body), "Key already used with another body",
            409, "idempotency_key_reuse")
    return key, (200, deepcopy(receipt["response"]))


def save(state, user, method, path, key, body, response):
    state["receipts"].append({"user_id": user, "method": method, "path": path, "key": key,
                              "body": deepcopy(body), "response": deepcopy(response)})


def receipt_record(data):
    record = fields(data, {"user_id": identifier, "method": text, "path": text,
                           "key": key_value, "body": json_value, "response": json_value})
    require(record["method"] == "POST", "Invalid receipt method")
    from .service import write_path
    require(write_path(record['path']), 'Invalid receipt path')
    require(isinstance(record["body"], dict), "Invalid receipt body")
    require(isinstance(record["response"], dict), "Invalid receipt response")
    return record
