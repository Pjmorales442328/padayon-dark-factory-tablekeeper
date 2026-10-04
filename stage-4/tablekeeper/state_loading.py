"""Version boundaries and mandatory receipt coverage for imported domain state."""
from .validation import require, array


def validate_version(data, importing):
    if not importing:
        return
    require(isinstance(data, dict), 'Invalid state')
    if 'domain_version' in data:
        native_version(data)
    else:
        legacy_version(data)


def native_version(data):
    require(type(data['domain_version']) is int and data['domain_version'] in (3, 4),
            'Invalid domain version')
    require(all(k in data for k in ('policies', 'histories', 'series')), 'Incomplete domain state')
    require(isinstance(data['histories'], dict), 'Invalid histories')
    extra = ('plans', 'closures', 'restaurant_revisions', 'restaurant_events')
    if data['domain_version'] == 4:
        require(all(k in data for k in extra), 'Incomplete Stage4 state')
    else:
        require(not any(k in data for k in extra), 'Missing Stage4 version')


def legacy_version(data):
    require(not any(k in data for k in ('policies', 'histories', 'series', 'plans', 'closures',
                                      'restaurant_revisions', 'restaurant_events')),
            'Missing domain version')
    for record in array(data.get('reservations', [])):
        require(isinstance(record, dict), 'Invalid booking')
        require('revision' not in record and 'accepted_terms' not in record, 'Missing domain version')



def validate_agreement_receipts(state):
    snapshots = [r['response']['series_id'] for r in state['receipts'] if r['path'] == '/series']
    require(set(snapshots) == {s['series_id'] for s in state['series']}, 'Missing adoption receipt')
    require(len(snapshots) == len(set(snapshots)), 'Duplicate adoption receipt')
    from .state_receipts import publication_coverage
    publication_coverage(state)
    from .state_plan_receipts import coverage
    coverage(state)

