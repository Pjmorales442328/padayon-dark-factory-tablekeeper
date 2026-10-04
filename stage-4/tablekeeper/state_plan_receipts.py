"""Validate immutable preview/application and collective-amendment receipts."""
from .validation import require, array
from .receipts import canonical
from .snapshots import snapshot_response
from . import replans, series, series_amend
from .state_plans import public


def validate(state, receipt):
    parts = receipt['path'].strip('/').split('/')
    if parts[0] == 'series':
        validate_amend(state, receipt, parts[1])
        return
    plan = replans.owned(state, parts[1], receipt['response'].get('plan_id'))
    replans.manager(state, parts[1], receipt['user_id'])
    if len(parts) == 3:
        require(canonical(receipt['response']) == canonical(public(plan)), 'Preview snapshot mismatch')
        from .closures import interval_record
        config = replans.manager(state, parts[1], receipt['user_id'])
        require(canonical(interval_record(receipt['body'], config)) == canonical(plan['closure']),
                'Preview request mismatch')
        return
    validate_apply(state, receipt, plan, parts[3])


def validate_apply(state, receipt, plan, pid):
    response = receipt['response']
    require(plan['applied'] and pid == plan['plan_id'], 'Application plan mismatch')
    require(set(response) == {'plan_id', 'restaurant_revision', 'reservations'}, 'Apply fields')
    require(type(response['restaurant_revision']) is int and
            response['restaurant_revision'] == plan['restaurant_revision'] + 1, 'Apply revision')
    records = array(response['reservations'])
    require(len(records) == len(plan['snapshot']), 'Application count')
    for saved, original, assignment in zip(records, plan['snapshot'], plan['assignments']):
        record = snapshot_response(state, saved, original['user_id'])
        require(record['reference'] == assignment['reference'] and
                record['table_ids'] == assignment['table_ids'], 'Application assignment mismatch')
        expected = original['revision'] + int(assignment['changed'])
        require(record['revision'] == expected, 'Application booking revision')
        retained = ('reservation_id', 'restaurant_id', 'user_id', 'party_size', 'status',
                    'starts_at_local', 'starts_at', 'ends_at', 'created_at', 'accepted_terms')
        require(all(record[key] == original[key] for key in retained), 'Repair changed accepted booking')


def validate_amend(state, receipt, sid):
    agreement = series.owned(state, sid, receipt['user_id'])
    data = series_amend.request(receipt['body'], len(agreement['occurrences']))
    response = receipt['response']
    require(set(response) == {'series_id', 'revision', 'interval_weeks', 'occurrences'}, 'Amend fields')
    require(response['series_id'] == sid and type(response['revision']) is int and
            response['revision'] in (data['expected_revision'], data['expected_revision'] + 1),
            'Amend series revision')
    require(response['revision'] <= agreement['revision'], 'Amend revision beyond current series')
    require(response['interval_weeks'] == agreement['interval_weeks'] and
            type(response['interval_weeks']) is int, 'Amend interval')
    occurrences = array(response['occurrences'])
    require(len(occurrences) == len(agreement['occurrences']), 'Amend count')
    for index, (saved, item) in enumerate(zip(occurrences, agreement['occurrences'])):
        require(isinstance(saved, dict), 'Invalid amendment occurrence')
        require(set(saved) == {'index', 'reference', 'exception', 'reservation'}, 'Amend occurrence fields')
        require(type(saved['index']) is int and saved['index'] == index and
                saved['reference'] == item['reference'] and type(saved['exception']) is bool,
                'Amend occurrence mismatch')
        record = snapshot_response(state, saved['reservation'], receipt['user_id'], False)
        require(record['reference'] == item['reference'], 'Amend booking mismatch')


def coverage(state):
    previews = [r['response']['plan_id'] for r in state['receipts']
                if r['path'].endswith('/replans')]
    require(set(previews) == {p['plan_id'] for p in state['plans']} and len(previews) == len(set(previews)),
            'Preview receipt coverage')
    application_coverage(state)
    collective_coverage(state)


def application_coverage(state):
    applies = [r['response']['plan_id'] for r in state['receipts']
               if r['path'].endswith('/apply')]
    require(set(applies) == {p['plan_id'] for p in state['plans'] if p['applied']} and
            len(applies) == len(set(applies)), 'Application receipt coverage')


def collective_coverage(state):
    for agreement in state['series']:
        path = '/series/' + agreement['series_id'] + '/amend'
        changed = [r for r in state['receipts'] if r['path'] == path and
                   r['response']['revision'] == r['body']['expected_revision'] + 1]
        require(len(changed) == len(agreement['collective_events']), 'Collective receipt coverage')
        for at in agreement['collective_events']:
            require(any(contains_event(state, receipt, at) for receipt in changed),
                    'Collective event missing receipt')


def contains_event(state, receipt, at):
    for item in receipt['response']['occurrences']:
        saved = item['reservation']
        entries = state['histories'][item['reference']]
        if any(e['at'] == at and e['revision'] == saved['revision'] and e['event'] == 'changed'
               for e in entries):
            return True
    return False
