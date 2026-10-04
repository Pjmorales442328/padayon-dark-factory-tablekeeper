"""Validate every move before checking resulting occupancy or committing."""
from .validation import require
from .bookings import owned, changed, occupancy, view, commit_changes


def move_items(body):
    items = body.get("moves")
    require(isinstance(items, list) and 1 <= len(items) <= 8, "Expected one to eight moves")
    refs = []
    for item in items:
        require(isinstance(item, dict), "Move must be an object")
        ref = item.get("reference")
        require(isinstance(ref, str) and 0 < len(ref) <= 64, "Invalid move reference")
        refs.append(ref)
    require(len(set(refs)) == len(refs), "Duplicate move reference")
    return items


def move(state, body, user):
    items = move_items(body)
    originals, candidates = [], []
    restaurant_id = None
    for item in items:
        original = owned(state, item["reference"], user)
        if restaurant_id is None:
            restaurant_id = original["restaurant_id"]
        require(original["restaurant_id"] == restaurant_id, "Moves span restaurants")
        candidate = changed(state, original, item)
        originals.append(original)
        candidates.append(candidate)
    occupancy(state, candidates, [r["reference"] for r in originals])
    commit_changes(state, originals, candidates)
    return 201, {"reservations": [view(r) for r in candidates]}
