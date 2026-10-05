"""Independent brute-force seating planner, written from the stage 4 text only."""
import itertools


def overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end


def options(tables, pairs):
    """Singles in fixture order, then declared pairs in declared order: [(table_ids tuple, capacity)]."""
    cap = {t["id"]: t["capacity"] for t in tables}
    return [((t["id"],), t["capacity"]) for t in tables] + [(tuple(p), cap[p[0]] + cap[p[1]]) for p in pairs]


def best_plan(tables, pairs, bookings, closure, closures=()):
    """bookings: dicts(ref, party, start, end, tables(tuple), caps(dict)) in minutes; confirmed only.
    closure/closures: (table_id, from_min, to_min). Returns (assignments, moved, unused) or None."""
    ctab, cfrom, cto = closure
    considered = sorted((b for b in bookings if overlaps(b["start"], b["end"], cfrom, cto)), key=lambda b: b["ref"])
    fixed = [b for b in bookings if not overlaps(b["start"], b["end"], cfrom, cto)]
    opts = options(tables, pairs)
    blocked = [(ctab, cfrom, cto)] + list(closures)

    def usable(b, o):
        ids, _ = o
        cap = sum(b["caps"][t] for t in ids)
        if cap < b["party"]: return None
        for tab, f, t in blocked:
            if tab in ids and overlaps(b["start"], b["end"], f, t): return None
        for x in fixed:
            if overlaps(b["start"], b["end"], x["start"], x["end"]) and set(ids) & set(x["tables"]): return None
        return cap

    per = [[(rank, ids, cap) for rank, o in enumerate(opts) if (cap := usable(b, o)) is not None for ids in [o[0]]] for b in considered]
    best, best_key = None, None
    for combo in itertools.product(*per):
        ok = True
        for i in range(len(combo)):
            for j in range(i + 1, len(combo)):
                bi, bj = considered[i], considered[j]
                if overlaps(bi["start"], bi["end"], bj["start"], bj["end"]) and set(combo[i][1]) & set(combo[j][1]): ok = False; break
            if not ok: break
        if not ok: continue
        moved = sum(1 for b, c in zip(considered, combo) if set(c[1]) != set(b["tables"]))
        unused = sum(c[2] - b["party"] for b, c in zip(considered, combo))
        key = (moved, unused, tuple(c[0] for c in combo))
        if best_key is None or key < best_key: best, best_key = combo, key
    if best is None: return None
    assignments = [(b["ref"], list(c[1]), set(c[1]) != set(b["tables"])) for b, c in zip(considered, best)]
    return assignments, best_key[0], best_key[1]
