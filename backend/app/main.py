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

    @app.get("/health", tags=["health"], include_in_schema=False)
    def root_health_check() -> dict[str, str]:
        return {"status": "ok", "project": settings.PROJECT_NAME}
    
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

    # Register decisions router
    from app.decisions.router import router as decisions_router
    app.include_router(decisions_router, prefix="/api/spam-models", tags=["decisions"])

    # Register dashboard router
    from app.dashboard.router import router as dashboard_router
    app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])

    # Configure CORS for local development and frontend clients
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount operator frontend UI if present
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import RedirectResponse

    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    if frontend_dir.is_dir():
        app.mount("/ui", StaticFiles(directory=str(frontend_dir), html=True), name="ui")

        @app.get("/", include_in_schema=False)
        def root_redirect():
            return RedirectResponse(url="/ui/")

    return app

app = create_app()
