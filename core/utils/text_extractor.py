import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from tika import parser as tika_parser
    TIKA_AVAILABLE = True
except ImportError:
    TIKA_AVAILABLE = False
    logger.warning("tika не установлен, извлечение текста отключено")

EXTRACTABLE_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/pdf",
}


def extract_text(content: bytes, mime_type: str) -> Optional[str]:
    """Извлекает текст из файла через Apache Tika. При ошибке возвращает None."""
    if not TIKA_AVAILABLE:
        return None
    if mime_type not in EXTRACTABLE_MIME_TYPES:
        return None
    try:
        parsed = tika_parser.from_buffer(content)
        text = parsed.get("content")
        if text:
            return text.strip() or None
        return None
    except Exception as e:
        logger.warning(f"Ошибка извлечения текста через Tika: {e}")
        return None
