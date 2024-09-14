from hashlib import sha256


def create_hashed_value(value):
    value_bytes = value.encode('utf-8')
    hash_object = sha256()
    hash_object.update(value_bytes)
    hashed_value = hash_object.hexdigest()
    return hashed_value