"""Version boundaries and mandatory receipt coverage for imported domain state."""
from .validation import require, array


def validate_version(data, importing):
    if not importing:
        return
    require(isinstance(data, dict), 'Invalid state')
    if 'domain_version' in data:
        require(type(data['domain_version']) is int and data['domain_version'] == 3,
                'Invalid domain version')
        require(all(k in data for k in ('policies', 'histories', 'series')), 'Incomplete domain state')
        require(isinstance(data['histories'], dict), 'Invalid histories')
    else:
        require(not any(k in data for k in ('policies', 'histories', 'series')),
                'Missing domain version')
        for record in array(data.get('reservations', [])):
            require(isinstance(record, dict), 'Invalid booking')
            require('revision' not in record and 'accepted_terms' not in record,
                    'Missing domain version')



def validate_agreement_receipts(state):
    snapshots = [r['response']['series_id'] for r in state['receipts'] if r['path'] == '/series']
    require(set(snapshots) == {s['series_id'] for s in state['series']}, 'Missing adoption receipt')
    require(len(snapshots) == len(set(snapshots)), 'Duplicate adoption receipt')
    from .state_receipts import publication_coverage
    publication_coverage(state)

