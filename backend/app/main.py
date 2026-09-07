import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import register_exception_handlers
from app.auth.router import router as auth_router

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up PhoenixML backend...")
    yield
    logger.info("Shutting down PhoenixML backend...")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan,
        debug=settings.DEBUG
    )

    register_exception_handlers(app)

    api_router = APIRouter()
    
    @api_router.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "project": settings.PROJECT_NAME}
        
    app.include_router(api_router, prefix="/api")
    
    # Register auth router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    
    # Register users router
    from app.users.router import router as users_router
    app.include_router(users_router, prefix="/api/users", tags=["users"])
    # Register models router
    from app.models.router import router as models_router
    app.include_router(models_router, prefix="/api/spam-models", tags=["spam-models"])
    
    # Register monitoring router
    from app.monitoring.router import router as monitoring_router
    app.include_router(monitoring_router, prefix="/api/spam-models", tags=["monitoring"])
    return app

app = create_app()
