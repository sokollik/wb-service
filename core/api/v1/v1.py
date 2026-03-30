from fastapi import APIRouter

from core.api.v1.birthday_controller import birthday_controller
from core.api.v1.comment_controller import comment_controller
from core.api.v1.document_ack_controller import document_ack_router
from core.api.v1.integration_controller import integration_router
from core.api.v1.news_controller import news_router
from core.api.v1.notification_controller import notification_router
from core.api.v1.org_structure_controller import org_structure_controller
from core.api.v1.profile_controller import profile_controller
from core.api.v1.rbac_controller import rbac_router
from core.api.v1.static_controller import static_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(
    profile_controller, prefix="/profile", tags=["Profile"]
)
v1_router.include_router(
    birthday_controller, prefix="/birthday", tags=["Birthday"]
)
v1_router.include_router(static_router, prefix="/static")
v1_router.include_router(
    org_structure_controller, prefix="/orgstructure", tags=["Org"]
)
v1_router.include_router(
    comment_controller, prefix="/comments", tags=["Comments"]
)
v1_router.include_router(
    news_router, prefix="/news", tags=["News"]
)
v1_router.include_router(
    notification_router, prefix="/notifications", tags=["Notifications"]
)
v1_router.include_router(
    rbac_router, prefix="/rbac", tags=["RBAC"]
)
v1_router.include_router(
    document_ack_router, tags=["Document Acknowledgments"]
)
v1_router.include_router(
    integration_router, tags=["Integrations"]
)