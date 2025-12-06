from typing import Dict


_mime_to_extension: Dict[str, str] = {
    # Documents
    "vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "pdf": "pdf",
    # Images
    "jpeg": "jpg",
    "png": "png",
    "webp": "webp",
    # Video
    "mp4": "mp4",
    # Audio
    "mpeg": "mp3",
    "mp3": "mp3",
}

# ...existing code...

_extension_to_mime: Dict[str, str] = {
    # Documents
    "docx": "application/vnd.openxmlformats-officedocument"
    + ".wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument"
    + ".spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument"
    + ".presentationml.presentation",
    "pdf": "application/pdf",
    # Images
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    # Video
    "mp4": "video/mp4",
    # Audio
    "mp3": "audio/mpeg",
}

async def get_mime_type(
    extension: str,
) -> str:
    if extension.startswith("."):
        extension = extension[1:]

    extension = extension.lower()
    return _extension_to_mime.get(extension, "application/octet-stream")


async def get_extension(
    content_type: str,
) -> str:
    if "/" in content_type:
        content_type = content_type.split("/")[1]

    return _mime_to_extension.get(content_type, "bin")
