"""Generate collision-free identifiers without changing their caller's format."""


def unused(existing, generate):
    value = generate()
    while value in existing:
        value = generate()
    return value
