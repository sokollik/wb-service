import asyncio
import logging
import traceback

from core.config.settings import get_settings
from core.repositories.news_repo import NewsRepository
from core.utils.db_util import get_session

logger = logging.getLogger(__name__)


async def scheduled_news_publisher(stop_event: asyncio.Event):
    settings = get_settings()
    interval = settings.SCHEDULED_NEWS_CHECK_INTERVAL

    while not stop_event.is_set():
        try:
            async with get_session() as session:
                news_repo = NewsRepository(session=session)
                published = await news_repo.publish_scheduled_news()
                if published:
                    logger.info(f"Scheduled publish: {published} news published")
        except Exception as e:
            logger.error(f"Error in scheduled news publisher: {e}")
            logger.error(traceback.format_exc())

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass
