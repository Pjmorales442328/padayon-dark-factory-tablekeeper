"""Manager previews and atomic operator seating repairs."""
import secrets
from copy import deepcopy
from .restaurants import restaurant
from .validation import require
from .identifiers import unused
from .selections import members, selection_fields
from . import planning, closures, chronology, bookings, series


def manager(state, rid, user):
    config = restaurant(state, rid)
    require(user in config.get('manager_user_ids', []), 'Manager required', 403, 'forbidden')
    return config


def preview(state, body, user, rid):
    config = manager(state, rid, user)
    closure = closures.interval_record(body, config)
    selected, fixed = planning.considered(state, config, closure)
    prior = [c for c in state['closures'] if c['restaurant_id'] == rid]
    obstacles = fixed + closures.occupied({'closures': prior + [{'restaurant_id': rid, **closure}]})
    candidates, score = planning.solve(config, selected, obstacles)
    pid = unused({p['plan_id'] for p in state['plans']}, lambda: secrets.token_hex(16))
    response = {'plan_id': pid, 'restaurant_revision': state['restaurant_revisions'][rid],
                'closure': closure, 'assignments': planning.assignments(selected, candidates),
                'moved_count': score[0], 'unused_seats': score[1]}
    state['plans'].append({**deepcopy(response), 'restaurant_id': rid, 'applied': False,
                           'snapshot': selected, 'fixed': fixed, 'prior_closures': deepcopy(prior)})
    return 201, response


def owned(state, rid, pid):
    plan = next((p for p in state['plans'] if p['plan_id'] == pid and p['restaurant_id'] == rid), None)
    require(plan is not None, 'Plan not found', 404, 'not_found')
    return plan


def apply(state, body, user, rid, pid):
    manager(state, rid, user)
    plan = owned(state, rid, pid)
    require(not plan['applied'], 'Plan already applied', 409, 'plan_already_applied')
    require(state['restaurant_revisions'][rid] == plan['restaurant_revision'],
            'Restaurant changed since preview', 409, 'stale_plan')
    at = chronology.next_at(state)
    moved = []
    records = []
    for assignment in plan['assignments']:
        record = next(r for r in state['reservations'] if r['reference'] == assignment['reference'])
        if assignment['changed']:
            reassign(state, record, assignment['table_ids'], pid, at)
            moved.append(record['reference'])
        records.append(bookings.view(record))
    state['closures'].append({'restaurant_id': rid, **deepcopy(plan['closure'])})
    series.affected(state, moved, False)
    plan['applied'] = True
    return 201, {'plan_id': pid, 'restaurant_revision': plan['restaurant_revision'] + 1,
                 'reservations': records}


def reassign(state, record, ids, pid, at):
    change = {'field': 'table_ids', 'from': members(record), 'to': list(ids)}
    record.pop('table_id', None)
    record.update(selection_fields(ids))
    record['revision'] += 1
    chronology.append(state, record, 'reassigned', [change], at)
    state['histories'][record['reference']][-1]['plan_id'] = pid
