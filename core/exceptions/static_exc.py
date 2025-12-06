from fastapi import HTTPException


class UploadingFileTooBigHttpException(HTTPException):
    def __init__(self, lang="en"):
        message = "uploaded file is too big"
        if lang == "ru":
            message = "загруженный файл слишком большой"
        super().__init__(status_code=413, detail=message)


class IncorrectFileTypeHttpException(HTTPException):
    def __init__(
        self,
        allowed_types: list[str],
        lang="en",
    ):
        message = "incorrect file type"
        if lang == "ru":
            message = "неверный тип файла"
            allowed_types = [f"'{x}'" for x in allowed_types]
        super().__init__(
            status_code=400,
            detail=message
            + (
                f", allowed types: {', '.join(allowed_types)}"
                if allowed_types
                else ""
            ),
        )
