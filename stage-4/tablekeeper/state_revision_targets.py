"""Mutation paths must name the restaurant and records they changed."""
from .validation import require


def validate_target(state, rid, path, refs):
    parts = path.strip('/').split('/')
    if parts[0] == 'restaurants':
        restaurant_target(rid, parts)
    elif len(parts) > 1 and parts[0] == 'series':
        series_target(state, parts, refs)
    elif parts[0] == 'reservations' and len(parts) > 1:
        reservation_target(parts, refs)
    else:
        require(path in ('/reservations', '/reservation-moves', '/series') and bool(refs),
                'Invalid mutation operation')


def reservation_target(parts, refs):
    require(parts[2:] in ([], ['cancel']) and set(refs) == {parts[1]}, 'Mutation booking path')


def restaurant_target(rid, parts):
    require(parts[1] == rid and parts[2] in ('policies', 'replans'), 'Mutation restaurant mismatch')


def series_target(state, parts, refs):
    from .series import membership
    agreement = next((s for s in state['series'] if s['series_id'] == parts[1]), None)
    require(agreement is not None and parts[2:] == ['amend'], 'Mutation series missing')
    require(bool(refs) and all(membership(state, ref) is agreement for ref in refs),
            'Mutation series references mismatch')
