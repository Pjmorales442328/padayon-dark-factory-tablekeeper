"""Restaurant-local half-open closure intervals shared by planning and occupancy."""
from .validation import fields, identifier, timestamp, require, Failure
from .restaurants import restaurant


def instant(value):
    if isinstance(value, str) and value.endswith('Z'):
        value = value[:-1] + '+00:00'
    return timestamp(value)


def interval_record(body, config):
    try:
        result = fields(body, {'table_id': identifier, 'from': instant, 'to': instant})
    except Failure as error:
        raise Failure(message='Invalid closure interval: ' + error.message) from None
    require(result['from'] < result['to'], 'Closure interval must increase')
    require(any(t['id'] == body['table_id'] for t in config['tables']),
            'Table not found', 404, 'not_found')
    return {key: body[key] for key in ('table_id', 'from', 'to')}


def intersects(record, closure):
    return (timestamp(record['starts_at']) < instant(closure['to']) and
            instant(closure['from']) < timestamp(record['ends_at']))


def occupied(state):
    return [{'restaurant_id': c['restaurant_id'], 'table_id': c['table_id'],
             'starts_at': instant(c['from']).isoformat(), 'ends_at': instant(c['to']).isoformat()}
            for c in state.get('closures', [])]


def load(state, source):
    from .validation import array
    result = []
    for data in array(source):
        require(isinstance(data, dict), 'Invalid closure')
        config = restaurant(state, data.get('restaurant_id'))
        result.append({'restaurant_id': config['id'], **interval_record(data, config)})
    state['closures'] = result
