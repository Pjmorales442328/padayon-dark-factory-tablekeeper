"""Validate detached restaurant counters and their mutation history."""
from copy import deepcopy
from .validation import require, array, timestamp
from .policies import bounded
from .state_revision_targets import validate_target


def load(state, data, native):
    from .revisions import initialize
    initialize(state)
    if not native:
        return
    counts, events = revision_maps(state, data)
    for rid, count in counts.items():
        bounded(count, 0)
        history = array(events[rid])
        require(len(history) == count, 'Restaurant counter mismatch')
        validate_events(state, rid, history)
    state['restaurant_revisions'] = deepcopy(counts)
    state['restaurant_events'] = deepcopy(events)


def revision_maps(state, data):
    counts, events = data.get('restaurant_revisions'), data.get('restaurant_events')
    require(isinstance(counts, dict) and set(counts) == set(state['restaurant_revisions']),
            'Restaurant revisions mismatch')
    require(isinstance(events, dict) and set(events) == set(counts), 'Restaurant events mismatch')
    return counts, events


def validate_events(state, rid, events):
    previous = None
    for seq, event in enumerate(events, 1):
        event_identity(event, seq)
        previous = event_time(event, previous)
        bounded(event['policy_version'], 0, len(state['policies'].get(rid, [])))
        validate_references(state, rid, event['references'])
        validate_target(state, rid, event['path'], event['references'])


def event_identity(event, seq):
    from .api_routes import write_path
    require(isinstance(event, dict) and set(event) ==
            {'seq', 'path', 'at', 'references', 'policy_version'}, 'Invalid restaurant event')
    require(type(event['seq']) is int and event['seq'] == seq, 'Invalid revision sequence')
    require(isinstance(event['path'], str) and (write_path(event['path']) or
            event['path'].startswith('/reservations/')), 'Invalid mutation path')


def event_time(event, previous):
    at = timestamp(event['at'])
    require(previous is None or at >= previous, 'Revision timestamp order')
    return at


def validate_references(state, rid, refs):
    require(isinstance(refs, dict), 'Invalid revision references')
    for ref, revision in refs.items():
        validate_reference(state, rid, ref, revision)


def validate_reference(state, rid, ref, revision):
    bounded(revision)
    record = next((r for r in state['reservations'] if r['reference'] == ref), None)
    require(record is not None and record['restaurant_id'] == rid, 'Mutation booking mismatch')
    require(revision <= record['revision'], 'Mutation revision beyond current booking')
    require(any(e['revision'] == revision for e in state['histories'][ref]),
            'Mutation revision missing history')
