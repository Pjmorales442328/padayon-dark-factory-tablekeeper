"""Atomic local-calendar recurring agreements and occurrence mutation counters."""
import secrets
from datetime import timedelta
from .validation import fields, identifier, local, require, Failure
from .policies import bounded
from .identifiers import unused
from .selections import members
from . import bookings, chronology


def owned(state, series_id, user):
    found = next((s for s in state['series']
                  if s['series_id'] == series_id and s['user_id'] == user), None)
    require(found is not None, 'Series not found', 404, 'not_found')
    return found


def view(state, agreement):
    result = {key: agreement[key] for key in ('series_id', 'revision', 'interval_weeks')}
    result['occurrences'] = [{**item, 'reservation': bookings.view(bookings.owned(
        state, item['reference'], agreement['user_id']))} for item in agreement['occurrences']]
    return result


def membership(state, reference):
    return next((s for s in state['series']
                 if any(o['reference'] == reference for o in s['occurrences'])), None)


def affected(state, references, exception):
    refs = set(references)
    for agreement in state['series']:
        changed = [o for o in agreement['occurrences'] if o['reference'] in refs]
        if changed:
            agreement['revision'] += 1
        if exception:
            for item in changed:
                item['exception'] = True


def request(body):
    return fields(body, {'anchor_reference': identifier,
                         'count': lambda v: bounded(v, 2, 12),
                         'interval_weeks': lambda v: bounded(v, 1, 4)})


def create(state, body, user):
    data = request(body)
    anchor = bookings.owned(state, data['anchor_reference'], user)
    bookings.amendable(state, anchor)
    require(membership(state, anchor['reference']) is None, 'Anchor already adopted',
            409, 'already_in_series')
    candidates = generated(state, anchor, data, user)
    sid = unused({s['series_id'] for s in state['series']}, lambda: secrets.token_hex(16))
    agreement = {'series_id': sid, 'user_id': user, 'revision': 1,
                 'interval_weeks': data['interval_weeks'],
                 'occurrences': [{'index': i, 'reference': r['reference'], 'exception': False}
                                 for i, r in enumerate([anchor, *candidates])]}
    agreement['scheduled_dates'] = [r['starts_at_local'][:10] for r in [anchor, *candidates]]
    agreement['collective_events'] = []
    for record in candidates:
        state['reservations'].append(record)
        chronology.created(state, record)
    state['series'].append(agreement)
    return 201, view(state, agreement)


def generated(state, anchor, data, user):
    from copy import deepcopy
    working = deepcopy(state)
    start = local(anchor['starts_at_local'])
    result = []
    for index in range(1, data['count']):
        date = occurrence_date(start, index, data['interval_weeks'])
        body = {'restaurant_id': anchor['restaurant_id'], 'table_ids': members(anchor),
                'party_size': anchor['party_size'], 'starts_at_local': date.strftime('%Y-%m-%dT%H:%M')}
        record = bookings.fresh(working, body, user)
        bookings.occupancy(working, [record])
        working['reservations'].append(record)
        result.append(record)
    return result


def occurrence_date(start, index, interval):
    try:
        return start + timedelta(days=index * interval * 7)
    except OverflowError:
        raise Failure(message='Occurrence date outside calendar range') from None
