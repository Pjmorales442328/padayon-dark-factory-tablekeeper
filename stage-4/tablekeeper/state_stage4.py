"""Stage4 load boundary and legacy schedule/revision defaults."""
from datetime import timedelta, date
from .validation import require, array, timestamp, fields, local, identifier
from . import closures, revisions, bookings
from .receipts import canonical


def load(state, data, importing):
    native = importing and data.get('domain_version') == 4
    revisions.load(state, data, native)
    schedules(state, data, native)
    if native:
        closures.load(state, data['closures'])
        from .state_plans import load as load_plans
        load_plans(state, data['plans'])
        bookings.occupancy(state, state['reservations'], [r['reference'] for r in state['reservations']])
        repair_histories(state)


def schedules(state, data, native):
    adopted = adoptions(data)
    for agreement in state['series']:
        original = adopted.get(agreement['series_id'])
        require(original is not None, 'Missing adoption snapshot')
        original_dates = adoption_dates(original)
        scheduled_dates(agreement, original_dates, native)
        validate_schedule(agreement)
        validate_collective(state, agreement)


def scheduled_dates(agreement, original_dates, native):
    if native:
        require(agreement.get('scheduled_dates') == original_dates, 'Original schedule changed')
    else:
        agreement['scheduled_dates'] = original_dates


def adoptions(data):
    result = {}
    for receipt in array(data.get('receipts', [])):
        require(isinstance(receipt, dict), 'Invalid receipt')
        if receipt.get('path') == '/series':
            adoption_snapshot(result, receipt)
    return result


def adoption_snapshot(result, receipt):
    response = receipt.get('response')
    require(isinstance(response, dict), 'Invalid adoption snapshot')
    sid = identifier(response.get('series_id'))
    require(sid not in result, 'Duplicate adoption snapshot')
    result[sid] = response


def adoption_dates(original):
    occurrences = fields(original, {'occurrences': array})['occurrences']
    dates = []
    for item in occurrences:
        dates.append(occurrence_date(item))
    require(bool(dates), 'Missing original occurrences')
    return dates


def occurrence_date(item):
    booking = fields(item, {'reservation': scheduled_booking})
    return str(booking['reservation']['starts_at_local'].date())


def scheduled_booking(value):
    return fields(value, {'starts_at_local': local})


def validate_schedule(agreement):
    dates = agreement['scheduled_dates']
    anchor = date.fromisoformat(dates[0])
    expected = [str(anchor + timedelta(days=i * agreement['interval_weeks'] * 7))
                for i in range(len(agreement['occurrences']))]
    require(dates == expected, 'Schedule calendar mismatch')


def validate_collective(state, agreement):
    events = agreement['collective_events']
    require(all(isinstance(at, str) for at in events), 'Invalid collective event')
    require(len(events) == len(set(events)), 'Duplicate collective event')
    for at in events:
        timestamp(at)
        collective_history(state, agreement, at)


def collective_history(state, agreement, at):
    require(any(e['at'] == at and e['event'] == 'changed'
                for o in agreement['occurrences'] for e in state['histories'][o['reference']]),
            'Missing collective history')


def repair_histories(state):
    for ref, entries in state['histories'].items():
        for event in entries:
            if event['event'] != 'reassigned':
                continue
            repair_event(state, ref, event)


def repair_event(state, ref, event):
    from .replans import owned
    record = next(r for r in state['reservations'] if r['reference'] == ref)
    plan = owned(state, record['restaurant_id'], event['plan_id'])
    assignment = next((a for a in plan['assignments'] if a['reference'] == ref), None)
    require(plan['applied'] and assignment is not None and assignment['changed'],
            'Repair event missing applied plan')
    require(canonical(event['changes'][0]['to']) == canonical(assignment['table_ids']),
            'Repair plan selection mismatch')
