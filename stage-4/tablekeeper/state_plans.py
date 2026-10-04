"""Detached historic plans are validated against their original planning environment."""
from copy import deepcopy
from .validation import fields, identifier, array, require, unique
from .policies import bounded
from .restaurants import restaurant
from .receipts import canonical
from . import closures, planning

PUBLIC_FIELDS = ('plan_id', 'restaurant_revision', 'closure', 'assignments', 'moved_count', 'unused_seats')


def public(plan):
    return {k: deepcopy(plan[k]) for k in PUBLIC_FIELDS}


def load(state, source):
    plans = [record(state, value) for value in array(source)]
    unique(plans, 'plan_id')
    state['plans'] = plans
    applied_closures(state, plans)


def applied_closures(state, plans):
    expected = [canonical({'restaurant_id': p['restaurant_id'], **p['closure']})
                for p in plans if p['applied']]
    require(sorted(expected) == sorted(canonical(c) for c in state['closures']),
            'Applied closures mismatch')


def record(state, value):
    result = plan_fields(value)
    config = restaurant(state, result['restaurant_id'])
    result['closure'] = closures.interval_record(result['closure'], config)
    require(result['restaurant_revision'] <= state['restaurant_revisions'][config['id']],
            'Plan revision beyond restaurant')
    originals = snapshots(state, result['snapshot'], config['id'])
    fixed = snapshots(state, result['fixed'], config['id'])
    distinct_bookings(originals, fixed)
    preview_environment(state, config, result, originals, fixed)
    return deepcopy(result)


def plan_fields(value):
    return fields(value, {'plan_id': identifier, 'restaurant_id': identifier,
        'restaurant_revision': lambda v: bounded(v, 0), 'closure': lambda v: v,
        'assignments': array, 'moved_count': lambda v: bounded(v, 0),
        'unused_seats': lambda v: bounded(v, 0), 'snapshot': array, 'fixed': array,
        'prior_closures': array, 'applied': boolean})


def distinct_bookings(originals, fixed):
    refs = [r['reference'] for r in originals + fixed]
    require(len(refs) == len(set(refs)), 'Duplicate planning booking')


def boolean(value):
    require(type(value) is bool, 'Expected boolean')
    return value


def snapshots(state, entries, rid):
    return [booking_snapshot(state, value, rid) for value in entries]


def booking_snapshot(state, value, rid):
    from .snapshots import snapshot_response
    require(isinstance(value, dict), 'Invalid planning booking')
    user = identifier(value.get('user_id'))
    record = snapshot_response(state, {k: v for k, v in value.items() if k != 'user_id'}, user)
    require(record['restaurant_id'] == rid, 'Planning booking restaurant mismatch')
    return record


def preview_environment(state, config, plan, originals, fixed):
    for item in plan['prior_closures']:
        prior_closure(state, config, item)
    booking_partition(config, plan, originals, fixed)
    obstacles = fixed + closures.occupied({'closures': plan['prior_closures'] +
                       [{'restaurant_id': config['id'], **plan['closure']}]})
    candidates, score = planning.solve(config, originals, obstacles)
    optimal_assignments(plan, originals, candidates, score)


def prior_closure(state, config, item):
    require(isinstance(item, dict), 'Invalid prior closure')
    require(item.get('restaurant_id') == config['id'], 'Closure restaurant mismatch')
    closures.interval_record(item, config)
    require(any(canonical(item) == canonical(c) for c in state['closures']), 'Unknown prior closure')


def booking_partition(config, plan, originals, fixed):
    environment = {'reservations': originals + fixed}
    expected_originals, expected_fixed = planning.considered(environment, config, plan['closure'])
    require([r['reference'] for r in originals] == [r['reference'] for r in expected_originals],
            'Plan considered booking order mismatch')
    require(len(expected_fixed) == len(fixed), 'Invalid fixed bookings')


def optimal_assignments(plan, originals, candidates, score):
    require(canonical(plan['assignments']) == canonical(planning.assignments(originals, candidates)),
            'Invalid optimal assignments')
    require((plan['moved_count'], plan['unused_seats']) == score, 'Planning objective mismatch')
