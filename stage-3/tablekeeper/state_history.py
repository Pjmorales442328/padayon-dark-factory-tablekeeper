"""Validate stored event order, snapshots and resulting booking state."""
from copy import deepcopy
from .validation import require, array, timestamp
from .receipts import canonical
from .selections import selection_fields, members
from .restaurants import restaurant
from . import policies, chronology, bookings


def load(state, source):
    if source is None:
        for record in state['reservations']:
            chronology.created(state, record)
        return
    require(isinstance(source, dict), 'Invalid histories')
    refs = {r['reference'] for r in state['reservations']}
    require(set(source) == refs, 'History references mismatch')
    for record in state['reservations']:
        entries = deepcopy(array(source[record['reference']]))
        validate(state, record, entries)
        state['histories'][record['reference']] = entries


def validate(state, record, entries):
    require(bool(entries), 'Missing created event')
    previous = None
    at = None
    for index, entry in enumerate(entries, 1):
        validate_identity(entry, index, at)
        at = timestamp(entry['at'])
        current = reconstruct(state, record, previous, entry)
        previous = current
    require(previous['revision'] == record['revision'], 'History revision mismatch')
    keys = ('table_ids', 'starts_at_local', 'party_size', 'accepted_terms')
    require(all(canonical(previous[k]) == canonical(record[k]) for k in keys),
            'History does not reach current booking')
    require(previous['status'] == record['status'] or (len(entries) == 1 and record['revision'] == 1),
            'History status mismatch')


def validate_identity(entry, index, previous_at):
    require(isinstance(entry, dict), 'Invalid history entry')
    require(set(entry) == {'seq', 'at', 'event', 'changes', 'revision', 'accepted_terms'},
            'Invalid history fields')
    require(type(entry['seq']) is int and entry['seq'] == index, 'Invalid history sequence')
    at = timestamp(entry['at'])
    require(previous_at is None or at >= previous_at, 'History timestamp order')
    policies.bounded(entry['revision'])


def reconstruct(state, record, previous, entry):
    event = entry['event']
    require(event in ('created', 'changed', 'cancelled'), 'Invalid event')
    require((previous is None) == (event == 'created'), 'Invalid created event order')
    require(previous is None or previous['status'] == 'confirmed', 'Event after cancellation')
    revision = 1 if previous is None else previous['revision'] + 1
    require(entry['revision'] == revision, 'Invalid event revision')
    data = apply_changes(previous, entry)
    config = restaurant(state, record['restaurant_id'])
    accepted = policies.validate_terms(state, config, entry['accepted_terms'])
    if event == 'cancelled':
        require(canonical(accepted) == canonical(previous['accepted_terms']), 'Cancel changed terms')
    body = {'restaurant_id': record['restaurant_id'], **data}
    current = bookings.values(state, body, accepted)
    current.update(revision=revision, status='cancelled' if event == 'cancelled' else 'confirmed')
    validate_delta(previous, current, entry)
    return current


def apply_changes(previous, entry):
    data = {} if previous is None else {'table_ids': members(previous),
                                       'starts_at_local': previous['starts_at_local'],
                                       'party_size': previous['party_size']}
    for change in array(entry['changes']):
        require(isinstance(change, dict) and set(change) == {'field', 'from', 'to'},
                'Invalid change')
        field = change['field']
        require(field in ('table_id', 'table_ids', 'starts_at_local', 'party_size'), 'Unknown change')
        if field in ('table_id', 'table_ids'):
            data.pop('table_ids', None)
            data.pop('table_id', None)
        data[field] = change['to']
    return data


def validate_delta(previous, current, entry):
    expected = [] if entry['event'] == 'cancelled' else chronology.changes(previous, current)
    require(canonical(expected) == canonical(entry['changes']), 'Inconsistent history changes')
    require(entry['event'] != 'changed' or bool(expected), 'Empty changed event')
