"""Password hashing and account/session creation."""
import hashlib
import hmac
import secrets
from .validation import fields, email, password, text, identifier, require

HASH_PREFIX = "scrypt$8192$8$1"


def hash_password(value):
    salt = secrets.token_hex(16)
    digest = derive(value, salt)
    return f"{HASH_PREFIX}${salt}${digest.hex()}"


def derive(value, salt):
    return hashlib.scrypt(value.encode(), salt=bytes.fromhex(salt), n=8192, r=8, p=1, dklen=32)


def valid_hash(value):
    value = text(value)
    parts = value.split("$")
    require(len(parts) == 6, "Invalid password hash")
    require("$".join(parts[:4]) == HASH_PREFIX, "Invalid password hash")
    salt, digest = parts[-2:]
    require(len(salt) == 32 and len(digest) == 64, "Invalid password hash")
    require(all(c in "0123456789abcdef" for c in salt + digest), "Invalid password hash")
    return value


def matches(value, encoded):
    salt, digest = encoded.split("$")[-2:]
    calculated = derive(value, salt)
    return hmac.compare_digest(calculated.hex(), digest)


def user_record(data, importing=False):
    rules = {"id": identifier, "email": email, "display_name": text}
    rules["password_hash" if importing else "password"] = valid_hash if importing else password
    record = fields(data, rules)
    if not importing:
        record["password_hash"] = hash_password(record.pop("password"))
    return record


def session(state, user):
    token = secrets.token_urlsafe(32)
    while token in state["tokens"]:
        token = secrets.token_urlsafe(32)
    state["tokens"][token] = user["id"]
    return {"user_id": user["id"], "display_name": user["display_name"], "token": token}


def authenticate(state, headers, hidden=False):
    value = headers.get("authorization", "")
    pieces = value.split() if isinstance(value, str) else []
    valid = len(pieces) == 2 and pieces[0].lower() == "bearer"
    user = state["tokens"].get(pieces[1]) if valid else None
    require(user is not None, "Authentication required", 404 if hidden else 401,
            "not_found" if hidden else "unauthenticated")
    return user


def signup(state, body):
    values = fields(body, {"email": email, "password": password, "display_name": text})
    require(not any(u["email"] == values["email"] for u in state["users"]),
            "Email already registered", 409, "email_taken")
    ids = {u["id"] for u in state["users"]}
    user_id = secrets.token_hex(16)
    while user_id in ids:
        user_id = secrets.token_hex(16)
    user = user_record({**values, "id": user_id})
    state["users"].append(user)
    return 201, session(state, user)


def login(state, body):
    values = fields(body, {"email": text, "password": text})
    user = next((u for u in state["users"] if u["email"] == values["email"]), None)
    require(user is not None, "Invalid credentials", 401, "unauthenticated")
    require(matches(values["password"], user["password_hash"]), "Invalid credentials",
            401, "unauthenticated")
    return 200, session(state, user)
