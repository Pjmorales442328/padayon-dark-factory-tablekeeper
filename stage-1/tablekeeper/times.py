"""Local-time resolution with absolute duration and first-fold semantics."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from .validation import Failure, local, require
from .restaurants import opening

UTC = timezone.utc


def resolve(naive, zone):
    aware = naive.replace(tzinfo=zone, fold=0)
    roundtrip = aware.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
    require(roundtrip == naive, "Local time does not exist", 422, "invalid_local_time")
    return aware


def bounds(config, naive):
    hours = opening(config, naive)
    require(hours is not None, "Restaurant is closed", 422, "outside_opening_hours")
    date = naive.strftime("%Y-%m-%d")
    start = local(date + "T" + hours["opens"])
    close = local(date + "T" + hours["closes"])
    return start, close


def interval(config, value):
    naive = local(value)
    zone = ZoneInfo(config["timezone"])
    start = resolve(naive, zone)
    opens, closes = bounds(config, naive)
    require(opens <= naive < closes, "Outside opening hours", 422, "outside_opening_hours")
    elapsed = int((naive - opens).total_seconds() // 60)
    require(elapsed % config["slot_minutes"] == 0, "Not on slot grid", 422, "not_on_slot_grid")
    # Subtracting aware datetimes in the same zone uses wall time; move to UTC first.
    available = (resolve(closes, zone).astimezone(UTC) - start.astimezone(UTC)).total_seconds()
    duration = config["reservation_duration_minutes"]
    require(duration <= available / 60, "Ends after closing", 422, "outside_opening_hours")
    end = (start.astimezone(UTC) + timedelta(minutes=duration)).astimezone(zone)
    return start.isoformat(), end.isoformat()


def slots(config, date):
    hours = opening(config, date)
    if hours is None:
        return []
    prefix = date.strftime("%Y-%m-%dT")
    cursor = local(prefix + hours["opens"])
    closes = local(prefix + hours["closes"])
    result = []
    step = config["slot_minutes"]
    while cursor < closes:
        value = cursor.strftime("%Y-%m-%dT%H:%M")
        try:
            start, end = interval(config, value)
            result.append((value, start, end))
        except Failure:
            pass
        remaining = int((closes - cursor).total_seconds() // 60)
        if step >= remaining:
            break
        cursor += timedelta(minutes=step)
    return result
