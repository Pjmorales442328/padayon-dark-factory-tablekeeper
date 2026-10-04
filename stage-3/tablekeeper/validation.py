"""Small reusable field rules and public domain failures."""
import re
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class Failure(Exception):
    def __init__(self, status=422, code="validation_failed", message="Invalid value"):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)

    def response(self):
        return self.status, {"error": {"code": self.code, "message": self.message}}


def require(condition, message="Invalid value", status=422, code="validation_failed"):
    if not condition:
        raise Failure(status, code, message)


def text(value):
    require(isinstance(value, str), "Expected a string", 400, "malformed_request")
    return value


def identifier(value):
    value = text(value)
    require(0 < len(value) <= 64, "Invalid identifier")
    return value


def integer(value, minimum=1):
    require(type(value) is int, "Expected an integer", 400, "malformed_request")
    require(value >= minimum, "Integer outside range")
    return value


def party(value):
    require(type(value) is int and value > 0, "Invalid party size")
    return value


def email(value):
    value = text(value)
    require(re.fullmatch(r"[^\s@]+@[^\s@]+", value) is not None, "Invalid email")
    return value


def password(value):
    value = text(value)
    require(len(value) >= 8, "Password must have eight characters")
    return value


def zone(value):
    value = text(value)
    try:
        ZoneInfo(value)
    except (ValueError, ZoneInfoNotFoundError):
        raise Failure(message="Invalid timezone") from None
    return value


def clock(value):
    value = text(value)
    require(re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value) is not None,
            "Invalid opening time")
    return value


def local(value):
    value = text(value)
    require(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}", value)
            is not None, "Invalid local start")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        raise Failure(message="Invalid local calendar time") from None


def timestamp(value):
    value = text(value)
    require(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?[+-][0-9]{2}:[0-9]{2}", value)
            is not None, "Invalid timestamp")
    try:
        result = datetime.fromisoformat(value)
        require(result.utcoffset() is not None, "Offset required")
        return result
    except ValueError:
        raise Failure(message="Invalid timestamp") from None


def reference(value):
    value = text(value)
    require(re.fullmatch(r"[A-Z0-9]{6,12}", value) is not None, "Invalid reference")
    return value


def fields(data, rules):
    require(isinstance(data, dict), "Expected object", 400, "malformed_request")
    result = {}
    for name, rule in rules.items():
        require(name in data, "Missing " + name)
        result[name] = rule(data[name])
    return result


def array(value):
    require(isinstance(value, list), "Expected list", 400, "malformed_request")
    return value


def unique(records, field):
    values = [record[field] for record in records]
    require(len(set(values)) == len(values), "Duplicate " + field)


def decimal(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9]+", value) is not None,
            "Expected decimal digits")
    require(len(value) <= 100, "Integer too large")
    return party(int(value))
