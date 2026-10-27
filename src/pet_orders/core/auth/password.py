import secrets
import string

from fastapi.concurrency import run_in_threadpool
from pwdlib import PasswordHash

SECRET_LENGTH = 6

hasher = PasswordHash.recommended()

async def hash_password(password: str) -> str:
    return await run_in_threadpool(hasher.hash, password)


async def verify_password(password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(hasher.verify, hashed_password, password)

def generate_auth_code() -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(SECRET_LENGTH))
