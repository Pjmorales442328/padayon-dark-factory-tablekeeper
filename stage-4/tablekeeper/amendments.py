"""Validate and commit individual or collective diner amendments."""
from .bookings import values, amendable, owned, occupancy, view, cutoff, CHANGE_FIELDS
from .selections import selected, members, retained_selector, selection_fields
from . import chronology


def changed(state, record, body):
    chronology.expected(record, body)
    amendable(state, record)
    body_values = {k: body.get(k, record[k]) for k in CHANGE_FIELDS}
    body_values["restaurant_id"] = record["restaurant_id"]
    body_values.update(retained_selector(record, body))
    if unchanged(record, body_values):
        return dict(record)
    new = values(state, body_values)
    if set(members(new)) == set(members(record)):
        new.update(selection_fields(members(record)))
    preserved = {k: v for k, v in record.items() if k not in ("table_id", "table_ids")}
    return {**preserved, **new, 'revision': record['revision'] + 1}



def unchanged(record, body):
    ids = selected(body)
    return (set(ids) == set(members(record)) and
            all(type(body[k]) is type(record[k]) and body[k] == record[k]
                for k in CHANGE_FIELDS))



def amend(state, body, ref, user):
    record = owned(state, ref, user)
    updated = changed(state, record, body)
    occupancy(state, [updated], [ref])
    commit_changes(state, [record], [updated])
    return 200, view(record)



def cancel(state, ref, user):
    record = owned(state, ref, user)
    if record["status"] != "cancelled":
        cutoff(state, record)
        record["status"] = "cancelled"
        record['revision'] += 1
        chronology.append(state, record, 'cancelled', [])
        from .series import affected
        affected(state, [record['reference']], False)
    return 200, view(record)



def commit_changes(state, originals, candidates):
    changed_refs = []
    at = chronology.next_at(state)
    for original, candidate in zip(originals, candidates):
        delta = chronology.changes(original, candidate)
        if delta:
            chronology.append(state, candidate, 'changed', delta, at)
            changed_refs.append(candidate['reference'])
        original.clear()
        original.update(candidate)
    from .series import affected
    affected(state, changed_refs, True)

