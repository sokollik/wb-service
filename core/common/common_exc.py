from fastapi import HTTPException


class NotFoundHttpException(HTTPException):
    def __init__(
        self,
        lang="en",
        name="поле",
        name_en=None,
    ):
        if name_en is None:
            if name == "поле":
                name_en = "propery"
            else:
                name_en = name

        message = f'object "{name_en}" not found'
        if lang == "ru":
            message = f'объект "{name}" не найден'
        super().__init__(status_code=404, detail=message)


class InvalidHttpException(HTTPException):
    def __init__(
        self,
        lang="en",
        name=None,
        name_en=None,
    ):
        if name_en is None:
            name_en = name

        message = f"{name_en} invalid" if name_en else "invalid"
        if lang == "ru":
            message = f"{name} неверный" if name else "неверный"
        super().__init__(status_code=403, detail=message)


class ShouldntBeNullHttpException(HTTPException):
    def __init__(
        self,
        lang="en",
        name="поле",
        name_en=None,
    ):
        if name_en is None:
            if name == "поле":
                name_en = "propery"
            else:
                name_en = name

        message = f"{name_en} shouldn't be null"
        if lang == "ru":
            message = f"{name} не должен быть null"
        super().__init__(status_code=400, detail=message)


class NotAllowedHttpException(HTTPException):
    def __init__(
        self,
        lang="en",
        name=None,
        name_en=None,
    ):
        if name_en is None:
            name_en = name

        message = (
            f'object "{name_en}" not allowed' if name_en else "not allowed"
        )
        if lang == "ru":
            message = (
                f'объект "{name}" не разрешен' if name else "не разрешено"
            )
        super().__init__(status_code=403, detail=message)


class AlreadyExistsHttpException(HTTPException):
    def __init__(
        self,
        lang="en",
        name="поле",
        name_en=None,
    ):
        if name_en is None:
            if name == "поле":
                name_en = "propery"
            else:
                name_en = name

        message = f"{name_en} already exists"
        if lang == "ru":
            message = f"{name} уже существует"
        super().__init__(status_code=400, detail=message)


class WrongParametersHttpException(HTTPException):
    def __init__(
        self,
        params: str = None,
        lang="en",
    ):
        message = "wrong parameters"
        if lang == "ru":
            message = "неверные параметры"
        super().__init__(
            status_code=400,
            detail=message + (f": {params}" if params else ""),
        )


class InfoHttpException(HTTPException):
    def __init__(
        self,
        msg: str | None = None,
        msg_en: str | None = None,
        lang="en",
    ):
        if msg_en is not None and lang == "en":
            msg = msg_en

        msg = msg or ""

        super().__init__(
            status_code=400,
            detail=msg,
        )


class IntervalServerErrorHttpException(HTTPException):
    def __init__(
        self,
        msg: str = "",
        lang="en",
    ):
        if msg in [None, ""]:
            msg = "internal server error"
        super().__init__(status_code=500, detail=msg)
