"""Validate agreement identities, occurrence ownership and unique membership."""
from copy import deepcopy
from .validation import fields, identifier, array, require, unique
from .policies import bounded
from . import bookings


def load(state, source):
    agreements = [agreement(state, value) for value in array(source)]
    unique(agreements, 'series_id')
    refs = [o['reference'] for s in agreements for o in s['occurrences']]
    require(len(set(refs)) == len(refs), 'Multiple series membership')
    state['series'] = agreements


def agreement(state, value):
    result = fields(value, {'series_id': identifier, 'user_id': identifier,
                            'revision': bounded, 'interval_weeks': lambda v: bounded(v, 1, 4),
                            'occurrences': array})
    require(2 <= len(result['occurrences']) <= 12, 'Invalid occurrence count')
    occurrences = []
    restaurants = set()
    for index, data in enumerate(result['occurrences']):
        require(isinstance(data, dict) and set(data) == {'index', 'reference', 'exception'},
                'Invalid occurrence')
        require(type(data['index']) is int and data['index'] == index, 'Invalid occurrence index')
        require(type(data['exception']) is bool, 'Invalid exception flag')
        record = bookings.owned(state, data['reference'], result['user_id'])
        restaurants.add(record['restaurant_id'])
        occurrences.append(deepcopy(data))
    require(len(restaurants) == 1, 'Series spans restaurants')
    result['occurrences'] = occurrences
    return result
