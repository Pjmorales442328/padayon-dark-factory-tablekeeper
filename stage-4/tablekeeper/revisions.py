"""Per-restaurant mutation counters with detached importable operation records."""
from datetime import datetime
from .times import UTC
from .validation import timestamp
from .state_revisions import load


def initialize(state):
    state['restaurant_revisions'] = {r['id']: 0 for r in state['restaurants']}
    state['restaurant_events'] = {r['id']: [] for r in state['restaurants']}


def changes(before, after):
    old = {r['reference']: r for r in before['reservations']}
    refs = {}
    for record in after['reservations']:
        previous = old.get(record['reference'])
        if previous is None or previous['revision'] != record['revision']:
            refs.setdefault(record['restaurant_id'], {})[record['reference']] = record['revision']
    return refs


def finish(before, state, path):
    refs = changes(before, state)
    for rid in touched_restaurants(before, state, refs):
        record_mutation(state, rid, path, refs.get(rid, {}))


def touched_restaurants(before, state, refs):
    touched = set(refs)
    for rid in state['restaurant_revisions']:
        if len(before['policies'].get(rid, [])) != len(state['policies'].get(rid, [])):
            touched.add(rid)
    touched.update(c['restaurant_id'] for c in state['closures'][len(before['closures']):])
    return touched


def record_mutation(state, rid, path, refs):
    seq = state['restaurant_revisions'][rid] + 1
    state['restaurant_revisions'][rid] = seq
    state['restaurant_events'][rid].append({'seq': seq, 'path': path,
        'at': next_at(state, rid), 'references': refs,
        'policy_version': len(state['policies'].get(rid, []))})


def next_at(state, rid):
    now = datetime.now(UTC)
    events = state['restaurant_events'][rid]
    if events:
        now = max(now, timestamp(events[-1]['at']))
    return now.isoformat()

