"""Collective recurring amendments on stable original calendar dates."""
from .validation import fields, clock, require, Failure
from .policies import bounded
from . import series, bookings
from .amendments import changed, unchanged, commit_changes


def request(body, count):
    rules = {'expected_revision': bounded, 'from_index': lambda v: bounded(v, 0, count - 1),
             'local_time': clock}
    try:
        return fields(body, rules)
    except Failure as error:
        raise Failure(message='Invalid series amendment: ' + error.message) from None


def amend(state, body, user, sid):
    agreement = series.owned(state, sid, user)
    data = request(body, len(agreement['occurrences']))
    require(data['expected_revision'] == agreement['revision'], 'Series revision changed',
            409, 'stale_revision')
    originals, candidates = prepare(state, agreement, data, user)
    bookings.occupancy(state, candidates, [r['reference'] for r in originals])
    refs = [new['reference'] for old, new in zip(originals, candidates)
            if old['revision'] != new['revision']]
    commit_changes(state, originals, candidates, exception=False)
    if refs:
        agreement['collective_events'].append(state['histories'][refs[0]][-1]['at'])
    return 201, series.view(state, agreement)


def prepare(state, agreement, data, user):
    originals, candidates = [], []
    for item, date in zip(agreement['occurrences'], agreement['scheduled_dates']):
        record = bookings.owned(state, item['reference'], user)
        if item['index'] < data['from_index'] or item['exception'] or record['status'] == 'cancelled':
            continue
        body = {'starts_at_local': date + 'T' + data['local_time'],
                'party_size': record['party_size'], 'table_ids': record['table_ids']}
        candidate = dict(record) if unchanged(record, body) else changed(state, record, body)
        originals.append(record)
        candidates.append(candidate)
    return originals, candidates
