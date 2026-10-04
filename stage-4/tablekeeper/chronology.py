"""Reservation revisions and immutable ordered history events."""
from copy import deepcopy
from datetime import datetime, timedelta
from .times import UTC
from .selections import members
from .validation import require, timestamp
from .policies import bounded


def expected(record, body):
    if 'expected_revision' in body:
        value = bounded(body['expected_revision'])
        require(value == record['revision'], 'Stale booking revision', 409, 'stale_revision')


def table_change(before, after):
    old = members(before) if before else None
    new = members(after)
    if old is not None and set(old) == set(new):
        return []
    pair = max(len(old or []), len(new)) == 2
    return [{'field': 'table_ids' if pair else 'table_id',
             'from': table_value(old, pair), 'to': table_value(new, pair)}]


def table_value(ids, pair):
    if ids is None:
        return None
    return ids if pair else ids[0]


def changes(before, after):
    result = table_change(before, after)
    for key in ('starts_at_local', 'party_size'):
        old = before[key] if before else None
        if old != after[key]:
            result.append({'field': key, 'from': old, 'to': after[key]})
    return result


def append(state, record, event, changed, at=None):
    entries = state['histories'].setdefault(record['reference'], [])
    at = at or next_at(state)
    if entries:
        at = max(timestamp(at), timestamp(entries[-1]['at'])).astimezone(UTC).isoformat()
    entries.append({'seq': len(entries) + 1, 'at': at, 'event': event,
                    'changes': deepcopy(changed), 'revision': record['revision'],
                    'accepted_terms': deepcopy(record['accepted_terms'])})


def next_at(state):
    latest = [timestamp(entries[-1]['at']) for entries in state['histories'].values() if entries]
    now = datetime.now(UTC)
    if latest and now <= max(latest):
        try:
            now = max(latest) + timedelta(microseconds=1)
        except OverflowError:
            require(False, 'History timestamp outside supported range')
    return now.astimezone(UTC).isoformat()


def created(state, record):
    append(state, record, 'created', changes(None, record))


def history(state, record):
    return 200, {'reference': record['reference'],
                 'entries': state['histories'].get(record['reference'], [])}


def decision(record):
    return 200, {key: record[key] for key in ('reference', 'revision', 'accepted_terms')}
