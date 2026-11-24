from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.health import router as health_router
from app.api.v1.interventions import router as interventions_router
from app.api.v1.model import router as model_router
from app.api.v1.recovery import router as recovery_router
from app.api.v1.simulate import router as simulate_router
from app.api.v1.students import router as students_router
from app.api.v1.upload import router as upload_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(dashboard_router)
api_router.include_router(simulate_router)
api_router.include_router(recovery_router)
api_router.include_router(interventions_router)
api_router.include_router(model_router)
api_router.include_router(upload_router)
api_router.include_router(admin_router)
