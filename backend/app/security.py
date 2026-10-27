import hashlib
import secrets

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher


_password_hasher = PasswordHash((Argon2Hasher(), BcryptHasher()))


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _password_hasher.verify(plain_password, password_hash)


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
