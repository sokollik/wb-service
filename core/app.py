import asyncio
import logging
import sys
import traceback
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.api.v1.v1 import v1_router
from core.config.settings import get_settings
from core.services.elastic_sync_service import EmployeeSyncService
from core.utils.db_util import get_session
from core.utils.elastic_search_util import get_document_es_service, get_elasticsearch_service
from core.utils.scheduler import scheduled_news_publisher

router = APIRouter(prefix="/auth", tags=["Auth"])

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        es_service = get_elasticsearch_service()
        es_service.create_index()

        doc_es_service = get_document_es_service()
        doc_es_service.create_index()
        try:
            async with get_session() as db_session:
                sync_service = EmployeeSyncService(db_session, es_service)
                synced_count = await sync_service.sync_if_empty()

                if synced_count > 0:
                    logger.info(
                        f"Auto-sync completed: {synced_count} employees"
                    )
                else:
                    logger.info(
                        "Index is empty or no employees in database"
                    )

        except Exception as e:
            logger.error(f"Error auto-sync: {e}")
            logger.error(traceback.format_exc())

    except Exception as e:
        logger.error(f"Error during Elasticsearch setup: {e}")
        logger.error(traceback.format_exc())

    stop_event = asyncio.Event()
    publisher_task = asyncio.create_task(scheduled_news_publisher(stop_event))
    logger.info("Scheduled news publisher started")

    yield

    stop_event.set()
    publisher_task.cancel()
    try:
        await publisher_task
    except asyncio.CancelledError:
        pass
    logger.info("Scheduled news publisher stopped")

    try:
        es_service = get_elasticsearch_service()
        es_service.es.close()
        logger.info("Elasticsearch client closed")
    except Exception as e:
        logger.warning(f"Error closing Elasticsearch: {e}")


settings = get_settings()

app = FastAPI(
    lifespan=lifespan,
    title="WB Service API",
    description="API для корпоративного портала: уведомления, новости, профиль сотрудника",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.include_router(v1_router)

# from fastapi import FastAPI

# from core.middleware import JWTBearer

# app = FastAPI()

# @app.get("/protected")
# async def protected_route(token: str = Depends(JWTBearer())):
#     user_info = TokenService.get_user_info_from_token(token)
#     return {"message": "Доступ разрешён", "user": user_info}

# @router.get("/me")
# async def get_current_user(token: str = Depends(JWTBearer())):
#     user_info = TokenService.get_user_info_from_token(token)
#     return {
#         "status": "success",
#         "user": user_info
#     }
