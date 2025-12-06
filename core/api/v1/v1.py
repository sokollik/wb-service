from fastapi import APIRouter

from core.api.v1.birthday_controller import birthday_controller
from core.api.v1.profile_controller import profile_controller
from core.api.v1.static_controller import static_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(profile_controller, prefix="/profile")
v1_router.include_router(birthday_controller, prefix="/birthday")
v1_router.include_router(static_router, prefix="/static")
