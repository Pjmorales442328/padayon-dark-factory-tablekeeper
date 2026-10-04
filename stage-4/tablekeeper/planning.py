"""Bounded exact lexicographic seating search over accepted booking capacities."""
from copy import deepcopy
from .validation import require
from .selections import members, selection_fields
from .bookings import overlaps
from .browsing import seating_options
from .policies import configured
from . import closures


def considered(state, config, closure):
    confirmed = confirmed_bookings(state, config['id'])
    selected = sorted((r for r in confirmed if closures.intersects(r, closure)),
                      key=lambda r: r['reference'])
    fixed = [r for r in confirmed if not closures.intersects(r, closure)]
    require(len(config['tables']) <= 6 and len(config.get('combinable', [])) <= 4 and
            len(selected) <= 6, 'Planning limits exceeded', 422, 'planning_limit')
    return deepcopy(selected), deepcopy(fixed)


def confirmed_bookings(state, rid):
    return [r for r in state['reservations']
            if r['restaurant_id'] == rid and r['status'] == 'confirmed']


def choices(config, record, obstacles):
    result = []
    for rank, option in enumerate(seating_options(configured(config, record['accepted_terms']))):
        candidate = {**record, **selection_fields(option['table_ids'])}
        if len(option['table_ids']) == 2:
            candidate.pop('table_id', None)
        if option['capacity'] >= record['party_size'] and not any(
                overlaps(candidate, other) for other in obstacles):
            result.append((candidate, option['capacity'] - record['party_size'], rank))
    return result


def solve(config, selected, obstacles):
    domains = [choices(config, record, obstacles) for record in selected]
    best = [None, None]
    search(selected, domains, [], 0, 0, [], best)
    require(best[1] is not None, 'No feasible seating plan', 409, 'no_feasible_plan')
    return best[1], best[0][:2]


def search(originals, domains, assigned, moved, unused, ranks, best):
    if best[0] is not None and (moved, unused) > best[0][:2]:
        return
    index = len(assigned)
    if index == len(domains):
        score = (moved, unused, tuple(ranks))
        if best[0] is None or score < best[0]:
            best[:] = [score, deepcopy(assigned)]
        return
    for candidate, waste, rank in domains[index]:
        if not any(overlaps(candidate, other) for other in assigned):
            change = set(members(candidate)) != set(members(originals[index]))
            search(originals, domains, assigned + [candidate], moved + change,
                   unused + waste, ranks + [rank], best)


def assignments(originals, candidates):
    return [{'reference': new['reference'], 'table_ids': members(new),
             'changed': set(members(old)) != set(members(new))}
            for old, new in zip(originals, candidates)]
