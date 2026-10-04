"""Thread-safe routing over the validated in-memory domain state."""
from copy import deepcopy
from threading import RLock
from .validation import Failure, require
from . import accounts, bookings, browsing, loading, moves, receipts, restaurants


class Service:
    def __init__(self):
        self._lock = RLock()
        self._state = loading.empty()

    def dispatch(self, method, path, query, headers, body):
        try:
            with self._lock:
                self.validate_body(method, path, body)
                result = self.route(method, path, query, headers, body)
                return result[0], deepcopy(result[1])
        except Failure as error:
            return error.response()
        except (ValueError, TypeError, OverflowError, RecursionError):
            return Failure(400, "malformed_request", "Invalid request value").response()

    @staticmethod
    def validate_body(method, path, body):
        if method not in ("POST", "PATCH"):
            return
        if method == "POST" and path.endswith("/cancel") and body is None:
            return
        require(isinstance(body, dict), "Expected JSON object", 400, "malformed_request")
        receipts.json_value(body)

    def route(self, method, path, query, headers, body):
        public = {("GET", "/health"): lambda: (200, {"status": "ok"}),
                  ("POST", "/_test/reset"): lambda: self.replace(loading.loaded(body)),
                  ("POST", "/_test/import"): lambda: self.replace(loading.imported(body)),
                  ("GET", "/_test/export"): self.export,
                  ("POST", "/auth/signup"): lambda: accounts.signup(self._state, body),
                  ("POST", "/auth/login"): lambda: accounts.login(self._state, body),
                  ("GET", "/restaurants"): self.restaurant_list,
                  ("GET", "/availability"): lambda: browsing.availability(self._state, query)}
        handler = public.get((method, path))
        if handler is not None:
            return handler()
        parts = path.strip("/").split("/")
        if method == "GET" and len(parts) == 2 and parts[0] == "restaurants":
            return 200, restaurants.restaurant(self._state, parts[1])
        return self.private(method, path, parts, headers, body)

    def replace(self, state):
        self._state = state
        return 204, None

    def export(self):
        return 200, {"track": "tablekeeper", "format_version": 1, "state": self._state}

    def restaurant_list(self):
        return 200, {"restaurants": [{k: r[k] for k in ("id", "name", "timezone")}
                                    for r in self._state["restaurants"]]}

    def private(self, method, path, parts, headers, body):
        require(parts[0] in ("reservations", "reservation-moves"), "Route not found", 404, "not_found")
        hidden = self.existing_reference(parts)
        user = accounts.authenticate(self._state, headers, hidden)
        if method == "POST" and path in ("/reservations", "/reservation-moves"):
            return self.idempotent(user, method, path, headers, body)
        if method == "GET" and path == "/reservations":
            return browsing.reservations(self._state, user)
        return self.single(method, parts, body, user)

    def existing_reference(self, parts):
        if len(parts) < 2 or parts[0] != "reservations":
            return False
        return any(r["reference"] == parts[1] for r in self._state["reservations"])

    def idempotent(self, user, method, path, headers, body):
        key, replay = receipts.replay(self._state, user, method, path, headers, body)
        if replay is not None:
            return replay
        operation = bookings.create if path == "/reservations" else moves.move
        # Build receipt before publishing state to keep all write components atomic.
        working = deepcopy(self._state)
        status, response = operation(working, body, user)
        receipts.save(working, user, method, path, key, body, response)
        self._state = working
        return status, response

    def single(self, method, parts, body, user):
        require(len(parts) in (2, 3) and parts[0] == "reservations", "Route not found", 404, "not_found")
        ref = parts[1]
        if len(parts) == 2 and method == "GET":
            return 200, bookings.view(bookings.owned(self._state, ref, user))
        if len(parts) == 2 and method == "PATCH":
            return bookings.amend(self._state, body, ref, user)
        if len(parts) == 3 and parts[2] == "cancel" and method == "POST":
            return bookings.cancel(self._state, ref, user)
        raise Failure(404, "not_found", "Route not found")
