"""Small route predicates and domain operation dispatch independent of transport."""
from .validation import Failure, require
from . import bookings, moves, policies, chronology, series, replans, series_amend


def private_read(parts, method):
    return method == 'GET' and (parts[0] == 'series' or
                               (len(parts) == 3 and parts[2] in ('history', 'decision')))



def write_path(path):
    parts = path.strip('/').split('/')
    return path in ('/reservations', '/reservation-moves', '/series') or restaurant_write(parts) or (
        len(parts) == 3 and parts[0] == 'series' and parts[2] == 'amend')


def restaurant_write(parts):
    if len(parts) == 3 and parts[0] == 'restaurants':
        return parts[2] in ('policies', 'replans')
    return len(parts) == 5 and parts[0] == 'restaurants' and parts[2] == 'replans' and parts[4] == 'apply'



def operate(state, path, body, user):
    operations = {'/reservations': bookings.create, '/reservation-moves': moves.move,
                  '/series': series.create}
    if path in operations:
        return operations[path](state, body, user)
    parts = path.strip('/').split('/')
    if parts[0] == 'series':
        return series_amend.amend(state, body, user, parts[1])
    if parts[2] == 'policies':
        return policies.publish(state, body, user, parts[1])
    if len(parts) == 3:
        return replans.preview(state, body, user, parts[1])
    return replans.apply(state, body, user, parts[1], parts[3])



def inspect_booking(state, kind, record):
    if kind == 'history':
        return chronology.history(state, record)
    require(kind == 'decision', 'Route not found', 404, 'not_found')
    return chronology.decision(record)



def booking_read(state, parts, record):
    if len(parts) == 2:
        return 200, bookings.view(record)
    return inspect_booking(state, parts[2], record)



def booking_write(state, method, parts, body, user):
    if len(parts) == 2 and method == 'PATCH':
        return bookings.amend(state, body, parts[1], user)
    if len(parts) == 3 and parts[2] == 'cancel' and method == 'POST':
        return bookings.cancel(state, parts[1], user)
    raise Failure(404, 'not_found', 'Route not found')

