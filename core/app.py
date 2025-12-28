import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from core.middleware import JWTBearer
from core.common.token_service import TokenService

from core.api.v1.v1 import v1_router
from core.config.settings import get_settings
from core.services.elastic_sync_service import EmployeeSyncService
from core.utils.db_util import get_session
from core.utils.elastic_search_util import (
    get_elasticsearch_service,
)
from api.v1.auth import router as auth_router
from api.v1.integrations.onec import router as onec_router

router = APIRouter(prefix="/auth", tags=["Auth"])
app.include_router(onec_router)

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
        import traceback

        logger.error(traceback.format_exc())
    yield

    try:
        es_service = get_elasticsearch_service()
        es_service.es.close()
        logger.info("Elasticsearch client closed")
    except Exception as e:
        logger.warning(f"Error closing Elasticsearch: {e}")


settings = get_settings()

app = FastAPI(
    lifespan=lifespan,
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

from fastapi import FastAPI
from core.middleware import JWTBearer

app = FastAPI()

@app.get("/protected")
async def protected_route(token: str = Depends(JWTBearer())):
    user_info = TokenService.get_user_info_from_token(token)
    return {"message": "Доступ разрешён", "user": user_info}

@router.get("/me")
async def get_current_user(token: str = Depends(JWTBearer())):
    user_info = TokenService.get_user_info_from_token(token)
    return {
        "status": "success",
        "user": user_info
    }
