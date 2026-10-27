from collections.abc import NoReturn

from fastapi import HTTPException


def raise_api_error(status_code: int, message: str, cause: BaseException | None = None) -> NoReturn:
    if cause is None:
        raise HTTPException(status_code=status_code, detail=message)
    raise HTTPException(status_code=status_code, detail=message) from cause
