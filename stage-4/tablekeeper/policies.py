"""Immutable dated policies, publication validation and accepted terms."""
from copy import deepcopy
from datetime import date
import re
from .validation import require, fields, Failure, array, unique
from .restaurants import restaurant, hours_record

TERM_FIELDS = ('slot_minutes', 'reservation_duration_minutes',
               'cancellation_cutoff_minutes', 'opening_hours', 'capacities')


def bounded(value, minimum=1, maximum=None):
    require(type(value) is int and value >= minimum, 'Invalid integer')
    require(maximum is None or value <= maximum, 'Integer outside range')
    return value


def calendar(value):
    require(isinstance(value, str) and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value),
            'Invalid effective date')
    try:
        date.fromisoformat(value)
    except ValueError:
        raise Failure(message='Invalid calendar date') from None
    return value


def hours(value):
    result = [hours_record(h) for h in array(value)]
    unique(result, 'weekday')
    return result


def capacities(value, config):
    require(isinstance(value, dict), 'Capacities must be an object')
    require(set(value) == {t['id'] for t in config['tables']}, 'Capacity keys mismatch')
    return {key: bounded(capacity, 1, 100) for key, capacity in value.items()}


def policy_record(body, config):
    rules = {'effective_from': calendar, 'slot_minutes': lambda v: bounded(v, 1, 1440),
             'reservation_duration_minutes': lambda v: bounded(v, 1, 1440),
             'cancellation_cutoff_minutes': lambda v: bounded(v, 0, 10080),
             'opening_hours': hours, 'capacities': lambda v: capacities(v, config)}
    try:
        return fields(body, rules)
    except Failure as error:
        raise Failure(message='Invalid policy: ' + error.message) from None


def base_terms(config):
    result = {key: deepcopy(config[key]) for key in TERM_FIELDS if key != 'capacities'}
    result.update(policy_version=0, capacities={t['id']: t['capacity'] for t in config['tables']})
    return result


def terms(policy):
    return deepcopy({key: policy[key] for key in ('policy_version', *TERM_FIELDS)})


def selected(state, config, local_date):
    eligible = [p for p in state['policies'].get(config['id'], [])
                if p['effective_from'] <= str(local_date)]
    if not eligible:
        return base_terms(config)
    return terms(max(eligible, key=lambda p: (p['effective_from'], p['policy_version'])))


def configured(config, accepted):
    result = deepcopy(config)
    result.update({key: deepcopy(accepted[key]) for key in TERM_FIELDS if key != 'capacities'})
    for table in result['tables']:
        table['capacity'] = accepted['capacities'][table['id']]
    return result


def validate_terms(state, config, value):
    require(isinstance(value, dict), 'Invalid accepted terms')
    version = bounded(value.get('policy_version'), 0)
    known = [base_terms(config)] + [terms(p) for p in state['policies'].get(config['id'], [])]
    expected = next((p for p in known if p['policy_version'] == version), None)
    require(expected is not None and value == expected, 'Terms do not match immutable policy')
    # Equality alone would accept bool as int; compare typed canonical JSON as well.
    from .receipts import canonical
    require(canonical(value) == canonical(expected), 'Invalid terms types')
    return deepcopy(expected)


def publish(state, body, user, restaurant_id):
    config = restaurant(state, restaurant_id)
    require(user in config.get('manager_user_ids', []), 'Manager required', 403, 'forbidden')
    record = policy_record(body, config)
    published = state['policies'].setdefault(restaurant_id, [])
    record['policy_version'] = len(published) + 1
    published.append(record)
    return 201, deepcopy(record)


def listing(state, restaurant_id):
    restaurant(state, restaurant_id)
    return 200, {'policies': state['policies'].get(restaurant_id, [])}


def load(state, source):
    require(isinstance(source, dict), 'Invalid policies')
    for rid, entries in source.items():
        config = restaurant(state, rid)
        records = []
        for index, data in enumerate(array(entries), 1):
            record = policy_record(data, config)
            require(type(data.get('policy_version')) is int and data['policy_version'] == index,
                    'Invalid policy version')
            records.append({**record, 'policy_version': index})
        state['policies'][rid] = records
