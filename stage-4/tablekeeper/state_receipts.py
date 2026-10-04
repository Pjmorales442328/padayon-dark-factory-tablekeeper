"""Original publication and adoption receipts remain immutable across transfers."""
from .validation import require, array
from .receipts import canonical
from . import policies, series
from .restaurants import restaurant
from .snapshots import snapshot_response


def validate_extra(state, receipt):
    if receipt['path'] == '/series':
        validate_series(state, receipt)
    elif receipt['path'].endswith('/amend') or '/replans' in receipt['path']:
        from .state_plan_receipts import validate
        validate(state, receipt)
    else:
        validate_policy(state, receipt)


def validate_policy(state, receipt):
    rid = receipt['path'].strip('/').split('/')[1]
    config = restaurant(state, rid)
    require(receipt['user_id'] in config.get('manager_user_ids', []), 'Policy receipt owner')
    response = receipt['response']
    parsed = policies.policy_record(receipt['body'], config)
    version = policies.bounded(response.get('policy_version'))
    expected = {**parsed, 'policy_version': version}
    require(canonical(response) == canonical(expected), 'Invalid policy receipt snapshot')
    require(any(canonical(p) == canonical(expected) for p in state['policies'].get(rid, [])),
            'Policy receipt missing published policy')


def validate_series(state, receipt):
    body = series.request(receipt['body'])
    response = receipt['response']
    require(set(response) == {'series_id', 'revision', 'interval_weeks', 'occurrences'},
            'Invalid series snapshot fields')
    agreement = series.owned(state, response['series_id'], receipt['user_id'])
    adoption_agreement(response, body, agreement)
    originals = array(response['occurrences'])
    require(len(originals) == len(agreement['occurrences']) == body['count'], 'Series count mismatch')
    snapshots = []
    for index, (original, current) in enumerate(zip(originals, agreement['occurrences'])):
        snapshots.append(adoption_occurrence(state, receipt['user_id'], index, original, current))
    require(snapshots[0]['reference'] == body['anchor_reference'], 'Anchor mismatch')
    validate_schedule(snapshots, body)
    validate_counters(state, agreement, snapshots)


def adoption_agreement(response, body, agreement):
    require(type(response['revision']) is int and response['revision'] == 1, 'Adoption revision')
    require(response['interval_weeks'] == body['interval_weeks'] == agreement['interval_weeks']
            and type(response['interval_weeks']) is int, 'Series interval mismatch')


def adoption_occurrence(state, user, index, original, current):
    require(isinstance(original, dict), 'Invalid adoption occurrence')
    require(set(original) == {'index', 'reference', 'exception', 'reservation'},
            'Invalid adoption occurrence fields')
    require(type(original['index']) is int and original['index'] == index, 'Invalid adoption index')
    require(original['exception'] is False and original['reference'] == current['reference'],
            'Invalid adoption member')
    record = snapshot_response(state, original['reservation'], user)
    require(record['reference'] == original['reference'], 'Adoption booking mismatch')
    return record


def validate_schedule(records, body):
    from datetime import timedelta
    from .validation import local
    from .selections import members
    anchor = records[0]
    start = local(anchor['starts_at_local'])
    for index, record in enumerate(records):
        expected = start + timedelta(days=index * body['interval_weeks'] * 7)
        require(record['starts_at_local'] == expected.strftime('%Y-%m-%dT%H:%M'),
                'Invalid original occurrence schedule')
        require(record['restaurant_id'] == anchor['restaurant_id'] and
                members(record) == members(anchor) and record['party_size'] == anchor['party_size'],
                'Original series fields mismatch')


def validate_counters(state, agreement, snapshots):
    events = set()
    for item, original in zip(agreement['occurrences'], snapshots):
        changes = occurrence_changes(state, agreement, item, original)
        events.update(e['at'] for e in changes)
    require(agreement['revision'] == 1 + len(events), 'Invalid series revision history')


def occurrence_changes(state, agreement, item, original):
    changes = [e for e in state['histories'][item['reference']]
               if e['revision'] > original['revision']]
    collective = set(agreement.get('collective_events', []))
    require(item['exception'] == any(e['event'] == 'changed' and e['at'] not in collective
                                     for e in changes), 'Invalid occurrence exception history')
    return changes


def publication_coverage(state):
    expected = {(rid, p['policy_version']) for rid, entries in state['policies'].items()
                for p in entries}
    actual = [(r['path'].strip('/').split('/')[1], r['response']['policy_version'])
              for r in state['receipts'] if r['path'].endswith('/policies')]
    require(set(actual) == expected and len(actual) == len(set(actual)),
            'Missing or duplicate publication receipt')
