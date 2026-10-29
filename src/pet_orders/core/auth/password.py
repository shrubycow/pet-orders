import hashlib
import hmac
import secrets
import string

from fastapi.concurrency import run_in_threadpool
from pwdlib import PasswordHash

from pet_orders.core.auth.settings import auth_settings

SECRET_LENGTH = 6

hasher = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = hasher.hash('dummy')


async def hash_password(password: str) -> str:
    return await run_in_threadpool(hasher.hash, password)


async def verify_password(password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(hasher.verify, hashed_password, password)


def generate_auth_code() -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(SECRET_LENGTH))


def hash_auth_code(code: str) -> str:
    return hmac.new(
        auth_settings.secret_key.encode(), code.encode(), hashlib.sha256
    ).hexdigest()


def verify_auth_code(code: str, hashed_code: str) -> bool:
    return hmac.compare_digest(hash_auth_code(code), hashed_code)
