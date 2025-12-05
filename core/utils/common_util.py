from functools import wraps
from fastapi import HTTPException
from core.common.common_exc import IntervalServerErrorHttpException


def exception_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e

            raise IntervalServerErrorHttpException(msg=str(e))

    return wrapper
