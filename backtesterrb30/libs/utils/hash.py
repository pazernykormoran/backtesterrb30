import hashlib


def hash_value(value: str) -> str:
    return hashlib.md5(value.encode()).hexdigest()
