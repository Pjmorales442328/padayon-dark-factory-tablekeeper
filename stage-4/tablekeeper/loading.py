"""Build validated detached states; never mutate live state during loading."""
from copy import deepcopy
from datetime import datetime
from .validation import (Failure, fields, array, identifier, reference, text, require,
                         timestamp, unique)
from .accounts import user_records
from .restaurants import restaurant_record
from .bookings import values, occupancy
from .receipts import record_identity
from .selections import stored_body
from .snapshots import validate_receipt
from .times import UTC
from . import policies
from .state_loading import validate_version, validate_agreement_receipts


def empty():
    return {"users": [], "restaurants": [], "reservations": [], "tokens": {}, "receipts": [],
            'policies': {}, 'histories': {}, 'series': [], 'domain_version': 4,
            'plans': [], 'closures': [], 'restaurant_revisions': {}, 'restaurant_events': {}}


def booking_record(state, data, importing=False):
    rules = {"reservation_id" if importing else "id": identifier,
             "reference": reference, "user_id": identifier}
    identity = fields(data, rules)
    if not importing:
        identity["reservation_id"] = identity.pop("id")
    require(any(u["id"] == identity["user_id"] for u in state["users"]), "Unknown user")
    body = stored_body(data) if importing else data
    config = next((r for r in state['restaurants'] if r['id'] == data.get('restaurant_id')), None)
    require(config is not None, 'Unknown restaurant')
    accepted = accepted_record(state, config, data, importing)
    record = {**values(state, body, accepted), **identity, "status": seed_status(data),
              "created_at": datetime.now(UTC).isoformat(),
              'revision': policies.bounded(data.get('revision', 1)) if importing else 1}
    if importing:
        preserve_record(record, data)
    return record


def accepted_record(state, config, data, importing):
    if importing and 'accepted_terms' in data:
        require('revision' in data, 'Missing revision')
        return policies.validate_terms(state, config, data['accepted_terms'])
    require(not importing or 'revision' not in data, 'Incomplete booking metadata')
    return policies.base_terms(config)


def seed_status(data):
    value = text(data.get("status", "confirmed"))
    require(value in ("confirmed", "cancelled"), "Invalid reservation status")
    return value


def preserve_record(record, data):
    saved = fields(data, {"status": text, "created_at": text, "starts_at": text, "ends_at": text})
    require(saved["status"] in ("confirmed", "cancelled"), "Invalid reservation status")
    timestamp(saved["created_at"])
    require(saved["starts_at"] == record["starts_at"] and saved["ends_at"] == record["ends_at"],
            "Inconsistent reservation timestamps")
    record.update(saved)


def records(state, data, importing):
    users = user_records(data['users'], importing)
    configs = [restaurant_record(r) for r in data["restaurants"]]
    unique(users, "id")
    unique(users, "email")
    unique(configs, "id")
    state.update(users=users, restaurants=configs)
    managers_record(state)
    if importing:
        policies.load(state, data.get('policies', {}))
    bookings = [booking_record(state, r, importing) for r in data["reservations"]]
    unique(bookings, "reservation_id")
    unique(bookings, "reference")
    occupancy(state, bookings)
    state["reservations"] = bookings


def managers_record(state):
    users = {u['id'] for u in state['users']}
    for config in state['restaurants']:
        require(set(config.get('manager_user_ids', [])).issubset(users), 'Unknown manager')


def tokens_record(state, tokens):
    require(isinstance(tokens, dict), "Invalid tokens")
    users = {u["id"] for u in state["users"]}
    for token, user in tokens.items():
        require(isinstance(token, str) and 0 < len(token) <= 255, "Invalid token")
        require(not any(c.isspace() for c in token), "Invalid token")
        identifier(user)
        require(user in users, "Token refers to unknown user")
    return deepcopy(tokens)


def loaded(data, importing=False):
    try:
        state = empty()
        validate_version(data, importing)
        source = fields(data, {"users": array, "restaurants": array, "reservations": array})
        records(state, {**data, **source}, importing)
        from .state_history import load as load_history
        from .state_series import load as load_series
        load_history(state, data.get('histories') if importing else None)
        load_series(state, data.get('series', []) if importing else [])
        from .state_stage4 import load as load_stage4
        load_stage4(state, data, importing)
        if importing:
            require("tokens" in data and "receipts" in data, "Incomplete imported state")
            state["tokens"] = tokens_record(state, data["tokens"])
            state["receipts"] = [validate_receipt(state, r) for r in array(data["receipts"])]
            ids = [record_identity(r) for r in state["receipts"]]
            require(len(set(ids)) == len(ids), "Duplicate receipt")
            validate_agreement_receipts(state)
        return state
    except Failure as error:
        raise Failure(message="Invalid state: " + error.message) from None


def imported(body):
    require(body.get("track") == "tablekeeper", "Wrong track")
    require(type(body.get("format_version")) is int and body["format_version"] == 1,
            "Wrong format version")
    require(isinstance(body.get("state"), dict), "State required")
    return loaded(body["state"], True)

