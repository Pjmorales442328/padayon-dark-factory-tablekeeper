"""Per-restaurant mutation counters with detached importable operation records."""
from copy import deepcopy
from datetime import datetime
from .times import UTC
from .validation import require, array, timestamp
from .policies import bounded


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
    touched = set(refs)
    for rid in state['restaurant_revisions']:
        if len(before['policies'].get(rid, [])) != len(state['policies'].get(rid, [])):
            touched.add(rid)
    touched.update(c['restaurant_id'] for c in state['closures'][len(before['closures']):])
    for rid in touched:
        seq = state['restaurant_revisions'][rid] + 1
        state['restaurant_revisions'][rid] = seq
        state['restaurant_events'][rid].append({'seq': seq, 'path': path,
            'at': next_at(state, rid), 'references': refs.get(rid, {}),
            'policy_version': len(state['policies'].get(rid, []))})


def next_at(state, rid):
    now = datetime.now(UTC)
    events = state['restaurant_events'][rid]
    if events:
        now = max(now, timestamp(events[-1]['at']))
    return now.isoformat()


def load(state, data, native):
    initialize(state)
    if not native:
        return
    counts, events = data.get('restaurant_revisions'), data.get('restaurant_events')
    require(isinstance(counts, dict) and set(counts) == set(state['restaurant_revisions']),
            'Restaurant revisions mismatch')
    require(isinstance(events, dict) and set(events) == set(counts), 'Restaurant events mismatch')
    for rid, count in counts.items():
        bounded(count, 0)
        history = array(events[rid])
        require(len(history) == count, 'Restaurant counter mismatch')
        validate_events(state, rid, history)
    state['restaurant_revisions'] = deepcopy(counts)
    state['restaurant_events'] = deepcopy(events)


def validate_events(state, rid, events):
    from .api_routes import write_path
    from .validation import timestamp
    previous = None
    for seq, event in enumerate(events, 1):
        require(isinstance(event, dict) and set(event) ==
                {'seq', 'path', 'at', 'references', 'policy_version'}, 'Invalid restaurant event')
        require(type(event['seq']) is int and event['seq'] == seq, 'Invalid revision sequence')
        require(isinstance(event['path'], str) and (write_path(event['path']) or
                event['path'].startswith('/reservations/')), 'Invalid mutation path')
        at = timestamp(event['at'])
        require(previous is None or at >= previous, 'Revision timestamp order')
        previous = at
        bounded(event['policy_version'], 0, len(state['policies'].get(rid, [])))
        validate_references(state, rid, event['references'])
        validate_target(state, rid, event['path'], event['references'])


def validate_references(state, rid, refs):
    require(isinstance(refs, dict), 'Invalid revision references')
    for ref, revision in refs.items():
        bounded(revision)
        record = next((r for r in state['reservations'] if r['reference'] == ref), None)
        require(record is not None and record['restaurant_id'] == rid, 'Mutation booking mismatch')
        require(revision <= record['revision'], 'Mutation revision beyond current booking')
        require(any(e['revision'] == revision for e in state['histories'][ref]),
                'Mutation revision missing history')


def validate_target(state, rid, path, refs):
    parts = path.strip('/').split('/')
    if parts[0] == 'restaurants':
        restaurant_target(rid, parts)
    elif len(parts) > 1 and parts[0] == 'series':
        series_target(state, parts, refs)
    elif parts[0] == 'reservations' and len(parts) > 1:
        require(parts[2:] in ([], ['cancel']) and set(refs) == {parts[1]}, 'Mutation booking path')
    else:
        require(path in ('/reservations', '/reservation-moves', '/series') and bool(refs),
                'Invalid mutation operation')


def restaurant_target(rid, parts):
    require(parts[1] == rid and parts[2] in ('policies', 'replans'), 'Mutation restaurant mismatch')


def series_target(state, parts, refs):
    from .series import membership
    agreement = next((s for s in state['series'] if s['series_id'] == parts[1]), None)
    require(agreement is not None and parts[2:] == ['amend'], 'Mutation series missing')
    require(bool(refs) and all(membership(state, ref) is agreement for ref in refs),
            'Mutation series references mismatch')
