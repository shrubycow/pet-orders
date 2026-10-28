from typing import NoReturn

from fastapi import HTTPException


def error_response(description: str, *details: str) -> dict:
    if not details:
        return {'description': description}
    return {
        'description': description,
        'content': {
            'application/json': {
                'examples': {detail: {'value': {'detail': detail}} for detail in details},
            },
        },
    }


def raise_api_error(status_code: int, message: str, cause: BaseException | None = None) -> NoReturn:
    if cause is None:
        raise HTTPException(status_code=status_code, detail=message)
    raise HTTPException(status_code=status_code, detail=message) from cause
